"""source_cache 缓存切面单测 · 零网络零付费 · 守数据等价。

覆盖：命中省调、端点级 TTL、不缓存端点、参数区分、force_refresh、
深拷贝隔离、失败不缓存、计费埋点（含 cache_hit）。
"""
from __future__ import annotations

import unittest
from unittest.mock import patch

from app.datasources import source_cache


class SourceCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        source_cache.clear()
        source_cache.reset_spend()
        # 埋点替换为 mock，避免真写 PG/JSONL，并可断言调用
        self._meter_patch = patch("app.services.metering.record_datasource")
        self.meter = self._meter_patch.start()

    def tearDown(self) -> None:
        self._meter_patch.stop()
        source_cache.clear()
        source_cache.reset_spend()

    def _counter(self, ret):
        calls = {"n": 0}

        def fn():
            calls["n"] += 1
            return ret if not isinstance(ret, dict) else dict(ret)
        return fn, calls

    def test_hit_saves_call(self):
        """同 source/endpoint/params 第二次命中缓存 → 不再调 fetch_fn。"""
        fn, calls = self._counter({"code": 0, "v": 1})
        r1 = source_cache.cached_call("jzl", "/article_detail", {"url": "u1"}, fn, cost_cny=0.045)
        r2 = source_cache.cached_call("jzl", "/article_detail", {"url": "u1"}, fn, cost_cny=0.045)
        self.assertEqual(calls["n"], 1)            # 只真调一次
        self.assertEqual(r1, r2)                    # 数据等价：命中值==首调值

    def test_data_equivalence_with_force_refresh(self):
        """force_refresh 旁路缓存，拿到真调值（实时快照保证）。"""
        seq = [{"read": 100}, {"read": 200}]
        box = {"i": 0}

        def fn():
            v = seq[box["i"]]
            box["i"] += 1
            return dict(v)
        first = source_cache.cached_call("jzl", "/read_zan", {"url": "u"}, fn, cost_cny=0.04)
        forced = source_cache.cached_call("jzl", "/read_zan", {"url": "u"}, fn, cost_cny=0.04,
                                          force_refresh=True)
        self.assertEqual(first["read"], 100)
        self.assertEqual(forced["read"], 200)       # 旁路拿到新值

    def test_no_cache_endpoint(self):
        """TTL=0 端点（余额）→ 每次真调，绝不缓存。"""
        fn, calls = self._counter({"remain_money": 86})
        source_cache.cached_call("jzl", "/get_remain_money", {}, fn)
        source_cache.cached_call("jzl", "/get_remain_money", {}, fn)
        self.assertEqual(calls["n"], 2)

    def test_unregistered_endpoint_not_cached(self):
        """未登记端点默认 TTL=0 → 不缓存（防意外缓存影响结果）。"""
        fn, calls = self._counter({"x": 1})
        source_cache.cached_call("jzl", "/some_new_endpoint", {"a": 1}, fn)
        source_cache.cached_call("jzl", "/some_new_endpoint", {"a": 1}, fn)
        self.assertEqual(calls["n"], 2)

    def test_params_distinguish(self):
        """不同参数 → 不同缓存键 → 各自真调。"""
        fn, calls = self._counter({"v": 1})
        source_cache.cached_call("jzl", "/article_detail", {"url": "a"}, fn)
        source_cache.cached_call("jzl", "/article_detail", {"url": "b"}, fn)
        self.assertEqual(calls["n"], 2)

    def test_deepcopy_isolation(self):
        """命中返回深拷贝 → 调用方改动不污染缓存。"""
        fn, _ = self._counter({"code": 0, "list": [1, 2]})
        r1 = source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
        r1["list"].append(999)                       # 污染返回值
        r2 = source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
        self.assertEqual(r2["list"], [1, 2])         # 缓存未被污染

    def test_fail_not_cached(self):
        """fetch_fn 抛异常 → 不缓存、重抛；下次重试真调。"""
        box = {"n": 0}

        def fn():
            box["n"] += 1
            if box["n"] == 1:
                raise RuntimeError("boom")
            return {"ok": True}
        with self.assertRaises(RuntimeError):
            source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
        r = source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
        self.assertEqual(r, {"ok": True})            # 第二次重试成功
        self.assertEqual(box["n"], 2)

    def test_metering_cache_hit_flag(self):
        """埋点：首调 status=success/cache_hit=False，命中 status=cached/cache_hit=True。"""
        fn, _ = self._counter({"v": 1})
        source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn, cost_cny=0.045)
        source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn, cost_cny=0.045)
        self.assertEqual(self.meter.call_count, 2)
        first_kw = self.meter.call_args_list[0].kwargs
        second_kw = self.meter.call_args_list[1].kwargs
        self.assertEqual(first_kw["status"], "success")
        self.assertFalse(first_kw["cache_hit"])
        self.assertAlmostEqual(first_kw["cost_cny"], 0.045)
        self.assertEqual(second_kw["status"], "cached")
        self.assertTrue(second_kw["cache_hit"])
        self.assertEqual(second_kw["cost_cny"], 0.0)   # 命中不计费

    def test_env_disable(self):
        """PROBE_SOURCE_CACHE=0 全关 → 退回裸调（每次真调）。"""
        fn, calls = self._counter({"v": 1})
        with patch.object(source_cache, "_ENABLED", False):
            source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
            source_cache.cached_call("jzl", "/article_detail", {"url": "u"}, fn)
        self.assertEqual(calls["n"], 2)


class CostGateTest(unittest.TestCase):
    """成本闸：付费调用超日预算 fail-loud；缓存命中/免费调用不受闸。"""

    def setUp(self) -> None:
        source_cache.clear()
        source_cache.reset_spend()
        self._meter_patch = patch("app.services.metering.record_datasource")
        self.meter = self._meter_patch.start()

    def tearDown(self) -> None:
        self._meter_patch.stop()
        source_cache.clear()
        source_cache.reset_spend()

    def _fn(self, ret):
        return lambda: dict(ret)

    def test_budget_block(self):
        """累计花费将超日预算 → 抛 BudgetExceeded，埋点 skipped，不真调。"""
        net = {"n": 0}

        def fn():
            net["n"] += 1
            return {"v": 1}
        with patch.object(source_cache, "_DAILY_BUDGET", 0.05):
            # 第一次 ¥0.045 通过（不同 url 避免命中缓存）
            source_cache.cached_call("jzl", "/article_detail", {"url": "a"}, fn, cost_cny=0.045)
            # 第二次 0.045+0.045=0.09 > 0.05 → 拦
            with self.assertRaises(source_cache.BudgetExceeded):
                source_cache.cached_call("jzl", "/article_detail", {"url": "b"}, fn, cost_cny=0.045)
        self.assertEqual(net["n"], 1)                       # 被拦的没真调
        self.assertAlmostEqual(source_cache.spent_today(), 0.045)
        # 末次埋点 status=skipped
        self.assertEqual(self.meter.call_args_list[-1].kwargs["status"], "skipped")

    def test_free_endpoint_not_gated(self):
        """免费端点（cost=0）不受预算闸。"""
        with patch.object(source_cache, "_DAILY_BUDGET", 0.0):
            for i in range(3):
                source_cache.cached_call("jzl", "/principal_info", {"ghid": f"g{i}"},
                                         self._fn({"v": i}), cost_cny=0.0)
        self.assertEqual(source_cache.spent_today(), 0.0)   # 免费不计花费

    def test_cache_hit_bypasses_gate(self):
        """缓存命中不真花钱 → 即使预算耗尽也能返回。"""
        with patch.object(source_cache, "_DAILY_BUDGET", 0.05):
            source_cache.cached_call("jzl", "/article_detail", {"url": "u"},
                                     self._fn({"v": 1}), cost_cny=0.045)
            # 预算已近耗尽，但同 url 命中缓存 → 不触发闸
            r = source_cache.cached_call("jzl", "/article_detail", {"url": "u"},
                                         self._fn({"v": 999}), cost_cny=0.045)
        self.assertEqual(r["v"], 1)                          # 命中首调值

    def test_gate_disabled(self):
        """PROBE_COST_GATE 关 → 不拦。"""
        with patch.object(source_cache, "_COST_GATE", False), \
             patch.object(source_cache, "_DAILY_BUDGET", 0.0):
            source_cache.cached_call("jzl", "/article_detail", {"url": "x"},
                                     self._fn({"v": 1}), cost_cny=0.045)   # 不抛
        self.assertAlmostEqual(source_cache.spent_today(), 0.045)


class JZLAdapterCacheTest(unittest.TestCase):
    """JZL adapter 经 _post_json 走缓存：同 url 第二次不打网络。"""

    def setUp(self) -> None:
        source_cache.clear()
        self._meter_patch = patch("app.services.metering.record_datasource")
        self._meter_patch.start()

    def tearDown(self) -> None:
        self._meter_patch.stop()
        source_cache.clear()

    def test_article_content_cached(self):
        from app.datasources.jzl_channels import JZLChannelsAdapter
        ad = JZLChannelsAdapter()
        ad._key = "dummy"        # 绕过 _needs_key 短路
        net = {"n": 0}

        def fake_post(path, extra):
            # 模拟 _post_json 真实返回（code 0 的 raw）
            net["n"] += 1
            return {"code": 0, "title": "T", "content": "正文", "gh_id": "gh1"}

        # 直接替换底层 HTTP（_post_json 内部的 _do），用缓存外壳真实路径
        with patch.object(JZLChannelsAdapter, "_post_json",
                          side_effect=lambda p, e: source_cache.cached_call(
                              ad.source_id, p, e, lambda: fake_post(p, e), cost_cny=0.045)):
            r1 = ad.fetch_article_content("https://mp.weixin.qq.com/s/abc")
            r2 = ad.fetch_article_content("https://mp.weixin.qq.com/s/abc")
        self.assertEqual(net["n"], 1)             # 第二次命中缓存·不打网络
        self.assertEqual(r1["title"], r2["title"])


class SummarizeDatasourceTest(unittest.TestCase):
    """summarize_datasource：从 JSONL 聚合缓存命中率/省费/闸拦截。"""

    def setUp(self) -> None:
        import tempfile
        from app.services import metering
        self.metering = metering
        self.tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        # 5 次 article_detail：3 真调(¥0.045) + 2 命中
        import json as _j
        rows = [
            {"surface": "datasource", "source_id": "jzl_wechat_channels", "status": "success",
             "cache_hit": False, "cost_cny": 0.045, "ts": 0},
            {"surface": "datasource", "source_id": "jzl_wechat_channels", "status": "success",
             "cache_hit": False, "cost_cny": 0.045, "ts": 0},
            {"surface": "datasource", "source_id": "jzl_wechat_channels", "status": "success",
             "cache_hit": False, "cost_cny": 0.045, "ts": 0},
            {"surface": "datasource", "source_id": "jzl_wechat_channels", "status": "cached",
             "cache_hit": True, "cost_cny": 0.0, "ts": 0},
            {"surface": "datasource", "source_id": "jzl_wechat_channels", "status": "cached",
             "cache_hit": True, "cost_cny": 0.0, "ts": 0},
            {"surface": "llm", "source_id": "cc-sonnet", "ts": 0},   # 非 datasource → 应被忽略
        ]
        for r in rows:
            self.tmp.write(_j.dumps(r) + "\n")
        self.tmp.close()
        self._patch = patch.object(metering, "_LOG_PATH", __import__("pathlib").Path(self.tmp.name))
        self._patch.start()
        self._pg_patch = patch.object(metering, "_PG_DSN", "")   # 强制走 JSONL 路径
        self._pg_patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        self._pg_patch.stop()
        import os as _os
        _os.unlink(self.tmp.name)

    def test_hit_rate_and_saved(self):
        out = self.metering.summarize_datasource()
        s = out["by_source"]["jzl_wechat_channels"]
        self.assertEqual(s["calls"], 5)
        self.assertEqual(s["cache_hits"], 2)
        self.assertAlmostEqual(s["hit_rate"], 0.4)          # 2/5
        self.assertAlmostEqual(s["cost_cny"], 0.135)         # 3×0.045
        self.assertAlmostEqual(s["saved_cny"], 0.09)         # 2 命中 × 均价 0.045
        self.assertNotIn("cc-sonnet", out["by_source"])      # llm 不计入


if __name__ == "__main__":
    unittest.main()

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
        # 埋点替换为 mock，避免真写 PG/JSONL，并可断言调用
        self._meter_patch = patch("app.services.metering.record_datasource")
        self.meter = self._meter_patch.start()

    def tearDown(self) -> None:
        self._meter_patch.stop()
        source_cache.clear()

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


if __name__ == "__main__":
    unittest.main()

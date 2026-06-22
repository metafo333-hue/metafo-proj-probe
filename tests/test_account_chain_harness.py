"""接线1: _harness_collect 适配层测试(离线·mock·0 网络)。

验证 harness 并发采集 → AccountProbe.to_dict 契约格式 + 失败回退降级。
"""
import unittest
from unittest.mock import patch

from app.services import account_chain

_PROFILE_DATA = {"user": {"nickname": "测试号", "follower_count": 1000,
                          "aweme_count": 5, "max_follower_count": 1200}}
_POSTS_DATA = {"aweme_list": [
    {"desc": "#美食 好吃", "create_time": 1000,
     "statistics": {"digg_count": 100, "comment_count": 5, "collect_count": 10, "share_count": 2}},
    {"desc": "#美食 探店", "create_time": 90000,
     "statistics": {"digg_count": 300, "comment_count": 8, "collect_count": 30, "share_count": 5}},
]}


class TestHarnessCollect(unittest.TestCase):
    def test_harness_path_yields_contract(self):
        async def fake_fetch(specs, key, cache=None, **kw):
            return {"profile": {"status": 200, "data": _PROFILE_DATA, "from_cache": False},
                    "posts": {"status": 200, "data": _POSTS_DATA, "from_cache": False}}

        with patch("combo_deep_probe.harness.fetch_endpoints_async", fake_fetch):
            rd = account_chain._harness_collect("sec_x", "key")

        # to_dict 契约 4 键(account_chain line ~250 _CONTRACT_FIELDS)
        self.assertTrue({"profile", "diagnosis", "works_sample", "works_analyzed"}.issubset(rd))
        self.assertEqual(rd["meta"]["via"], "harness")          # 走了 harness 非降级
        self.assertEqual(rd["profile"]["nickname"], "测试号")
        self.assertEqual(rd["works_analyzed"], 2)
        self.assertIn("burst_ratio", rd["diagnosis"])           # diagnose 真算了
        self.assertIn("follower_drawdown", rd["diagnosis"])     # max_follower_count→掉粉(组合矩阵)

    def test_degrade_to_accountprobe_on_harness_fail(self):
        async def boom(*a, **kw):
            raise RuntimeError("harness down")

        class _FakeRep:
            def to_dict(self):
                return {"profile": {"nickname": "降级号"}, "diagnosis": {},
                        "works_sample": [], "works_analyzed": 0, "meta": {"via": "accountprobe"}}

        class _FakeProbe:
            def analyze(self, **kw):
                return _FakeRep()

        with patch("combo_deep_probe.harness.fetch_endpoints_async", boom), \
             patch("combo_deep_probe.build_account_probe", lambda **kw: _FakeProbe()):
            rd = account_chain._harness_collect("sec_x", "key")

        self.assertEqual(rd["profile"]["nickname"], "降级号")    # 回退 AccountProbe
        self.assertEqual(rd["meta"]["via"], "accountprobe")

    def test_degrade_on_empty_data(self):
        # harness 返回但 data 为空(WAF/风控) → 也回退
        async def empty(specs, key, cache=None, **kw):
            return {"profile": {"status": -3, "data": None, "from_cache": False},
                    "posts": {"status": 200, "data": _POSTS_DATA, "from_cache": False}}

        class _FakeProbe:
            def analyze(self, **kw):
                class R:
                    def to_dict(self):
                        return {"profile": {}, "diagnosis": {}, "works_sample": [],
                                "works_analyzed": 0, "meta": {"via": "accountprobe"}}
                return R()

        with patch("combo_deep_probe.harness.fetch_endpoints_async", empty), \
             patch("combo_deep_probe.build_account_probe", lambda **kw: _FakeProbe()):
            rd = account_chain._harness_collect("sec_x", "key")
        self.assertEqual(rd["meta"]["via"], "accountprobe")     # 空数据回退


if __name__ == "__main__":
    unittest.main()

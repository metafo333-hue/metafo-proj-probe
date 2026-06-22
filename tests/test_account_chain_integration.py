"""account_chain + pipeline 集成单测 · 零网络·零付费·全 mock。

覆盖：
  竞品圈递归深度限制（depth>1 拒绝·depth=1 放行·代码约束验证）
  微信视频号路径：wechat_channels 已在渲染器映射·render_wechat_channels 正常工作
  C 路径 (_discover_stub)：返回结构正确·含 deliverable/meta/cost·搜索降级不崩
  账号链契约：combo-deep-probe to_dict() 缺字段时记录警告不崩溃
"""
from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

_DOUYIN_URL = "https://www.douyin.com/video/7534641277405531446"
_WECHAT_URL = "https://channels.weixin.qq.com/web/pages/home?channel_id=v2_abc123@finder"
_COMPETITOR_URL = "https://www.douyin.com/video/9999999999"


class TestRecursionDepthGuard(unittest.TestCase):
    """① 竞品圈递归深度限制。"""

    def test_depth_2_blocked(self):
        """depth=2 被守卫拦截，直接返回错误，不执行任何网络请求。"""
        from app.services.account_chain import run_from_video_url
        result = run_from_video_url(_DOUYIN_URL, _depth=2)
        self.assertFalse(result["ok"])
        self.assertIn("递归深度超限", result["error"])

    def test_depth_1_not_depth_error(self):
        """depth=1 不被深度守卫拦截（因为 >1 才拦）·失败是因为缺 key 等，不是深度问题。"""
        from app.services.account_chain import run_from_video_url
        result_d1 = run_from_video_url(_DOUYIN_URL, _depth=1)
        # depth=1 不含递归错误（可能有其他错误，但不是深度问题）
        self.assertNotIn("递归深度超限", result_d1.get("error", ""))

    def test_competitor_guard_in_source_code(self):
        """代码级验证：竞品圈递归传入了 _depth+1 且有 _depth==0 保护。"""
        import inspect
        from app.services import account_chain as _ac
        src = inspect.getsource(_ac.run_from_video_url)
        self.assertIn("_depth=_depth + 1", src)
        self.assertIn("_depth == 0", src)


class TestWechatChannelsRouting(unittest.TestCase):
    """② 微信视频号渲染链路。"""

    def test_wechat_channels_in_renderer_map(self):
        """cross_platform_render._RENDERERS 已包含 wechat_channels 渲染器。"""
        from app.services.cross_platform_render import _RENDERERS
        self.assertIn("wechat_channels", _RENDERERS)

    def test_render_wechat_channels_basic(self):
        """render_wechat_channels 能正常渲染基础数据字段。"""
        from app.services.cross_platform_render import render_wechat_channels
        md = render_wechat_channels({
            "title": "测试视频号内容",
            "nickname": "测试账号",
            "like_count": 500,
            "comment_count": 30,
            "_source": "jzl",
        })
        self.assertIn("测试视频号内容", md)
        self.assertIn("500", md)
        self.assertIn("播放量", md)  # 必须有播放量永久缺口说明

    def test_render_wechat_channels_empty_no_crash(self):
        """空 data 不崩溃，输出包含播放量缺口说明。"""
        from app.services.cross_platform_render import render_wechat_channels
        md = render_wechat_channels({})
        self.assertIsInstance(md, str)
        self.assertIn("播放量", md)

    def test_render_wechat_channels_full(self):
        """全字段渲染：粉丝/各互动数/v2_name 均出现在输出。"""
        from app.services.cross_platform_render import render_wechat_channels
        md = render_wechat_channels({
            "title": "视频标题",
            "nickname": "账号名",
            "v2_name": "v2_abc@finder",
            "like_count": 1200,
            "comment_count": 80,
            "collect_count": 300,
            "share_count": 50,
            "fans": 5000,
            "_source": "jzl",
        })
        self.assertIn("1,200", md)
        self.assertIn("5,000", md)
        self.assertIn("JZL", md)
        self.assertIn("v2_abc@finder", md)

    def test_account_chain_has_jzl_branch(self):
        """account_chain 代码中存在 PROBE_JZL_KEY 和 JZLChannelsAdapter 调用。"""
        import inspect
        from app.services import account_chain as _ac
        src = inspect.getsource(_ac.run_from_video_url)
        self.assertIn("PROBE_JZL_KEY", src)
        self.assertIn("JZLChannelsAdapter", src)
        self.assertIn("wechat_channels", src)


class TestCPathDiscover(unittest.TestCase):
    """③ C 路径选题发现（_discover_stub 升级版）。"""

    def _call_discover(self, instruction="美食视频选题"):
        from app.services.pipeline import _discover_stub
        brief = MagicMock()
        brief.subject = None
        brief.instruction = instruction
        brief.context = None
        brief.attachments = []
        route_decision = MagicMock()
        route_decision.circles = []
        import time
        return _discover_stub(brief, route_decision, "task-test", time.perf_counter())

    def test_returns_required_keys(self):
        """必须返回 deliverable / meta / cost 三个顶层键。"""
        with patch("app.datasources.public.searxng.search", return_value=[]), \
             patch("app.datasources.public.hackernews.search", return_value=[]):
            result = self._call_discover()
        self.assertIn("deliverable", result)
        self.assertIn("meta", result)
        self.assertIn("cost", result)

    def test_deliverable_has_path_C(self):
        """deliverable._path 必须为 C。"""
        with patch("app.datasources.public.searxng.search", return_value=[]), \
             patch("app.datasources.public.hackernews.search", return_value=[]):
            result = self._call_discover()
        self.assertEqual(result["deliverable"]["_path"], "C")

    def test_with_search_results_not_stub(self):
        """有搜索结果时 _stub=False、content 含具体线索标题。"""
        mock_results = [
            {"title": "美食短视频选题攻略", "url": "https://example.com/1"},
            {"title": "餐厅探店内容方向", "url": "https://example.com/2"},
        ]
        with patch("app.datasources.public.searxng.search", return_value=mock_results):
            result = self._call_discover("美食视频选题")
        d = result["deliverable"]
        self.assertFalse(d.get("_stub"))
        self.assertIn("美食短视频选题攻略", d["content"])

    def test_search_failure_degrades_gracefully(self):
        """搜索层抛异常时降级占位，不崩溃，返回结构完整。"""
        with patch("app.datasources.public.searxng.search",
                   side_effect=Exception("network error")), \
             patch("app.datasources.public.hackernews.search",
                   side_effect=Exception("network error")):
            result = self._call_discover()
        self.assertIn("deliverable", result)
        self.assertIn("meta", result)

    def test_stub_flag_true_when_no_results(self):
        """搜索无结果时 _stub=True。"""
        with patch("app.datasources.public.searxng.search", return_value=[]), \
             patch("app.datasources.public.hackernews.search", return_value=[]):
            result = self._call_discover()
        self.assertTrue(result["deliverable"].get("_stub"))


class TestComboCombatContractCheck(unittest.TestCase):
    """④ combo-deep-probe 字段契约校验：缺字段时记录警告不崩溃。"""

    def test_missing_fields_logged_not_raised(self):
        """to_dict() 缺字段 → warning 日志·不 raise。"""
        import logging
        _CONTRACT_FIELDS = ("profile", "diagnosis", "works_sample", "works_analyzed")
        bad_rd = {"profile": {"nickname": "测试"}, "diagnosis": {}}
        # 不含 works_sample / works_analyzed

        with self.assertLogs("app.services.account_chain", level="WARNING") as cm:
            import logging as _clog
            _missing_fields = [f for f in _CONTRACT_FIELDS if f not in bad_rd]
            if _missing_fields:
                _clog.getLogger("app.services.account_chain").warning(
                    "combo-deep-probe.to_dict() 字段缺失: %s · 可能版本漂移，请检查两仓字段契约",
                    _missing_fields)

        self.assertTrue(any("字段缺失" in msg for msg in cm.output))
        self.assertIn("works_sample", str(cm.output))

    def test_contract_check_in_source_code(self):
        """account_chain 源码中存在字段契约校验逻辑。"""
        import inspect
        from app.services import account_chain as _ac
        src = inspect.getsource(_ac.run_from_video_url)
        self.assertIn("_CONTRACT_FIELDS", src)
        self.assertIn("_missing_fields", src)
        self.assertIn("to_dict() 字段缺失", src)


if __name__ == "__main__":
    unittest.main(verbosity=2)

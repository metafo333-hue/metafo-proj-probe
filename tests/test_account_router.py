"""account router 单元测试 · TestClient + mock · 不调网络/不付费。

依赖 fastapi 存在才跑；无 fastapi 时 skip（与 test_selftest 同约定）。
"""
from __future__ import annotations

import unittest

try:
    from unittest.mock import patch

    from fastapi.testclient import TestClient

    from app.main import app

    _HAS_FASTAPI = True
except ImportError:
    _HAS_FASTAPI = False

_MOCK_SUCCESS = {
    "ok": True,
    "report_md": "# 账号报告\n测试内容",
    "video": {"title": "测试视频", "like": 1000, "comment": 50, "share": 20,
              "collect": 30, "duration_s": 60},
    "account": {"nickname": "测试账号", "follower": 50000, "aweme_count": 100,
                 "works_analyzed": 20, "signature": "测试签名",
                 "avg_like": 800.0, "max_like": 5000, "burst_ratio": 0.3,
                 "vertical_score": 0.85, "hashtags": ["美食", "生活"]},
    "audit": {"source_reliability": "高", "confidence_level": "高",
              "evidence_strength": "强"},
    "works": [{"title": "作品1", "like": 1000}],
    "six_layer": None,
}

_MOCK_FAILURE = {
    "ok": False,
    "error": "缺 TIKHUB_API_KEY/PROBE_TIKHUB_KEY(走 vault)",
}

_MOCK_PLATFORM_ERR = {
    "ok": False,
    "platform": "unknown",
    "error": "暂仅支持抖音链路（TikHub 抖音源）",
}

_MODULE = "app.services.account_chain.run_from_video_url"


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed — skipping account router tests")
class TestAccountRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # ── 正常路径 ──────────────────────────────────────────────────────────

    def test_analyze_success(self):
        """正常返回：code=0，data 含 ok/report_md/account/six_layer，不含 works/video/audit。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as mock_fn:
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["msg"], "ok")
        data = body["data"]
        self.assertTrue(data["ok"])
        self.assertIn("report_md", data)
        self.assertIn("account", data)
        self.assertIn("six_layer", data)
        # works/video/audit 不暴露
        self.assertNotIn("works", data)
        self.assertNotIn("video", data)
        self.assertNotIn("audit", data)
        # 确认传参正确
        mock_fn.assert_called_once()
        args, kwargs = mock_fn.call_args
        self.assertEqual(args[0], "https://www.douyin.com/video/12345")
        self.assertTrue(kwargs.get("with_audiovisual", True))
        self.assertIsNone(kwargs.get("competitor_urls"))

    def test_analyze_with_competitor_urls(self):
        """competitor_urls 正确透传给 run_from_video_url。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as mock_fn:
            r = self.client.post("/api/v1/account/analyze", json={
                "video_url": "https://www.douyin.com/video/12345",
                "competitor_urls": ["https://www.douyin.com/video/99999"],
                "with_audiovisual": False,
            })
        self.assertEqual(r.json()["code"], 0)
        _, kwargs = mock_fn.call_args
        self.assertEqual(kwargs["competitor_urls"],
                         ["https://www.douyin.com/video/99999"])
        self.assertFalse(kwargs["with_audiovisual"])

    # ── 错误路径 ──────────────────────────────────────────────────────────

    def test_analyze_missing_url(self):
        """缺 video_url → code=4001，不调 run_from_video_url。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as mock_fn:
            r = self.client.post("/api/v1/account/analyze", json={})
        self.assertEqual(r.json()["code"], 4001)
        mock_fn.assert_not_called()

    def test_analyze_empty_url(self):
        """空字符串 video_url → code=4001。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as mock_fn:
            r = self.client.post("/api/v1/account/analyze", json={"video_url": ""})
        self.assertEqual(r.json()["code"], 4001)
        mock_fn.assert_not_called()

    def test_analyze_run_returns_ok_false(self):
        """run_from_video_url 返回 ok=False（如缺 key）→ code=5002。"""
        with patch(_MODULE, return_value=_MOCK_FAILURE):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
        body = r.json()
        self.assertEqual(body["code"], 5002)
        self.assertIsNone(body["data"])
        self.assertIn("TIKHUB", body["msg"])

    def test_analyze_platform_not_supported(self):
        """非抖音链接 → run 返回 ok=False + error → code=5002。"""
        with patch(_MODULE, return_value=_MOCK_PLATFORM_ERR):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://weixin.qq.com/sph/abc"})
        body = r.json()
        self.assertEqual(body["code"], 5002)
        self.assertIsNone(body["data"])

    def test_analyze_exception_returns_5001(self):
        """run_from_video_url 抛异常 → code=5001，不 500。"""
        with patch(_MODULE, side_effect=RuntimeError("网络超时")):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["code"], 5001)
        self.assertIn("RuntimeError", body["msg"])
        self.assertIsNone(body["data"])

    # ── 路由注册验证 ──────────────────────────────────────────────────────

    def test_router_registered_in_app(self):
        """端点已注册在 FastAPI app 路由表中。"""
        routes = [r.path for r in app.routes]
        self.assertIn("/api/v1/account/analyze", routes)


if __name__ == "__main__":
    unittest.main()

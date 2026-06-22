"""account router 异步版单元测试 · TestClient + mock · 不调网络/不付费。

默认异步(提交 task_id·复用 core/tasks 长任务机制)·sync=true 同步。
无 fastapi 时 skip（与 test_selftest 同约定）。
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
    "account": {"nickname": "测试账号", "follower": 50000},
    "six_layer": None,
    "works": [{"title": "作品1", "like": 1000}],   # 不应出现在返回里
    "video": {"title": "x"},                        # 不应出现
    "audit": {"source_reliability": "高"},          # 不应出现
}
_MOCK_FAILURE = {"ok": False, "error": "缺 TIKHUB_API_KEY/PROBE_TIKHUB_KEY(走 vault)"}
_MODULE = "app.services.account_chain.run_from_video_url"


@unittest.skipUnless(_HAS_FASTAPI, "fastapi not installed — skipping account router tests")
class TestAccountRouter(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    # ── 异步(默认·复用 task 机制防超时) ──────────────────────────────────
    def test_async_returns_task_id(self):
        """默认 POST → code=0·data 含 task_id + status_url（秒级返回·不阻塞）。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
        body = r.json()
        self.assertEqual(body["code"], 0)
        self.assertIn("task_id", body["data"])
        self.assertIn("status_url", body["data"])
        self.assertTrue(body["data"]["status_url"].startswith("/api/v1/task/"))

    def test_async_then_poll_done(self):
        """提交 → 轮询 GET task → done + deliverable（TestClient 会执行 BackgroundTasks）。"""
        with patch(_MODULE, return_value=_MOCK_SUCCESS):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
            tid = r.json()["data"]["task_id"]
            poll = self.client.get(f"/api/v1/task/{tid}")
        t = poll.json()["data"]
        self.assertEqual(t["status"], "done")
        self.assertIn("report_md", t["deliverable"])
        # 裁剪：works/video/audit 不进 deliverable
        self.assertNotIn("works", t["deliverable"])

    def test_async_failure_task_failed(self):
        """run 返回 ok=False → 后台 task=failed（不扣费·不 HTTP 错误）。"""
        with patch(_MODULE, return_value=_MOCK_FAILURE):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345"})
            tid = r.json()["data"]["task_id"]
            poll = self.client.get(f"/api/v1/task/{tid}")
        t = poll.json()["data"]
        self.assertEqual(t["status"], "failed")
        self.assertIsNone(t["cost"])         # 失败不扣费

    # ── 同步(sync=true·调试/短任务) ──────────────────────────────────────
    def test_sync_returns_report(self):
        with patch(_MODULE, return_value=_MOCK_SUCCESS):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345", "sync": True})
        data = r.json()["data"]
        self.assertTrue(data["ok"])
        self.assertIn("report_md", data)
        self.assertNotIn("works", data)     # 裁剪

    def test_sync_competitor_passthrough(self):
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as m:
            self.client.post("/api/v1/account/analyze", json={
                "video_url": "https://www.douyin.com/video/12345",
                "competitor_urls": ["https://www.douyin.com/video/99999"],
                "with_audiovisual": False, "sync": True})
        _, kw = m.call_args
        self.assertEqual(kw["competitor_urls"], ["https://www.douyin.com/video/99999"])
        self.assertFalse(kw["with_audiovisual"])

    def test_sync_ok_false_5002(self):
        with patch(_MODULE, return_value=_MOCK_FAILURE):
            r = self.client.post("/api/v1/account/analyze",
                                 json={"video_url": "https://www.douyin.com/video/12345", "sync": True})
        self.assertEqual(r.json()["code"], 5002)

    # ── 通用 ──────────────────────────────────────────────────────────────
    def test_missing_url_4001(self):
        with patch(_MODULE, return_value=_MOCK_SUCCESS) as m:
            r = self.client.post("/api/v1/account/analyze", json={})
        self.assertEqual(r.json()["code"], 4001)
        m.assert_not_called()

    def test_router_registered(self):
        routes = [r.path for r in app.routes]
        self.assertIn("/api/v1/account/analyze", routes)


if __name__ == "__main__":
    unittest.main()

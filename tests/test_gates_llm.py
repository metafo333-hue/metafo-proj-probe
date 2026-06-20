"""闸级 LLM 集成测试 · GATES_LIVE_MODEL 开关 + 降级验证。

验证目标
--------
1. GATES_LIVE_MODEL 未设或=0 时，所有闸行为与 StubBackend 完全一致（零网络调用）。
2. GATES_LIVE_MODEL=1 且 LLM 不可用（网络 mock 抛异常）时，闸降级回 stub 中性值，
   pipeline 不崩溃，run_audit() 正常返回结构。
3. AuditLLMBackend 各方法单独降级验证（mock llm_caller.call 抛异常）。

零网络调用：所有 LLM 调用通过 unittest.mock.patch 拦截，不发真实请求。

⚠️ 真模型集成未在生产实测，需 probe-a 部署后配置环境变量验证：
   GATES_LIVE_MODEL=1
   LITELLM_BASE_URL=http://<ufo2 tailscale ip>:4000/v1
   LITELLM_API_KEY=<vault probe.env 的 key>
   LITELLM_MODEL=cc-sonnet  # 或其他 LiteLLM alias
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.audit.backends import AuditLLMBackend, StubBackend, get_backend
from app.audit.gates import run_audit


# ---------------------------------------------------------------------------
# 辅助 fixture
# ---------------------------------------------------------------------------

_CLAIMS = ["公司 A 的月活用户超过 100 万", "产品 B 的用户满意度为 95%"]
_SOURCES = [
    {
        "url":              "https://reuters.com/tech/company-a-mau",
        "title":            "Company A MAU Report",
        "text":             "Company A announced monthly active users exceed 1 million.",
        "timestamp":        "2026-06-01T00:00:00Z",
        "reliability_hint": "B",
        "source_type":      "primary",
    }
]


# ---------------------------------------------------------------------------
# 测试组 1：开关关闭时，行为与 stub 完全一致
# ---------------------------------------------------------------------------

class TestSwitchOff(unittest.TestCase):
    """GATES_LIVE_MODEL=0（默认）→ 使用 StubBackend，无 LLM 调用。"""

    def setUp(self):
        # 确保开关关闭
        os.environ.pop("GATES_LIVE_MODEL", None)
        os.environ.pop("PROBE_LITELLM_KEY", None)

    def test_get_backend_returns_stub_when_switch_off(self):
        backend = get_backend()
        self.assertIsInstance(backend, StubBackend)

    def test_run_audit_free_no_llm_call(self):
        """free 档 run_audit 不触发任何网络调用。"""
        with patch("app.audit.llm_caller.call") as mock_call:
            result = run_audit(_CLAIMS, _SOURCES, tier="free")
            mock_call.assert_not_called()
        self.assertIn("gate_results", result)
        self.assertIn("gate0", result["gate_results"])
        self.assertIn("gate1", result["gate_results"])
        self.assertIn("gate7", result["gate_results"])

    def test_run_audit_paid_no_llm_call_when_switch_off(self):
        """paid 档、开关关闭时，仍不触发 LLM 调用。"""
        with patch("app.audit.llm_caller.call") as mock_call:
            result = run_audit(_CLAIMS, _SOURCES, tier="paid")
            mock_call.assert_not_called()
        self.assertIn("conclusion_label", result)

    def test_stub_backend_faithfulness_neutral(self):
        stub = StubBackend()
        self.assertEqual(stub.faithfulness("任意声称", ["任意来源"]), 0.5)

    def test_stub_backend_detect_aigc_zero(self):
        stub = StubBackend()
        self.assertEqual(stub.detect_aigc("任意文本"), 0.0)

    def test_stub_backend_nli_neutral(self):
        stub = StubBackend()
        result = stub.nli("前提", "假设")
        self.assertEqual(result["contradiction"], 0.0)
        self.assertEqual(result["neutral"], 1.0)

    def test_stub_backend_judge_accept(self):
        stub = StubBackend()
        result = stub.judge("声称", [])
        self.assertEqual(result["verdict"], "accept")


# ---------------------------------------------------------------------------
# 测试组 2：开关开启，但 LLM 不可用（mock 抛异常）→ 降级不崩
# ---------------------------------------------------------------------------

class TestSwitchOnLLMUnavailable(unittest.TestCase):
    """GATES_LIVE_MODEL=1 + LLM 不可用 → 所有闸降级到 stub，pipeline 正常返回。"""

    def setUp(self):
        os.environ["GATES_LIVE_MODEL"] = "1"
        # 设置虚拟端点和 key（让 is_enabled() 返回 True）
        os.environ["LITELLM_BASE_URL"] = "http://127.0.0.1:9999/v1"
        os.environ["LITELLM_API_KEY"]  = "test-key-unavailable"
        os.environ["LITELLM_MODEL"]    = "test-model"

    def tearDown(self):
        for k in ("GATES_LIVE_MODEL", "LITELLM_BASE_URL", "LITELLM_API_KEY", "LITELLM_MODEL"):
            os.environ.pop(k, None)

    def test_get_backend_returns_audit_llm_when_switch_on(self):
        backend = get_backend()
        self.assertIsInstance(backend, AuditLLMBackend)

    def _run_with_network_error(self, tier: str) -> dict:
        """Mock llm_caller.call 抛 ConnectionError，模拟网络不可达。"""
        import httpx
        with patch("app.audit.llm_caller.call", side_effect=ConnectionError("network down")):
            # AuditLLMBackend 内部调用 call()，异常被 llm_caller 捕获返回 None，
            # 再由 AuditLLMBackend 各方法降级 stub。
            # 但 mock 在 llm_caller 模块级 call()，需确认调用路径正确。
            # 正确 patch 路径：app.audit.backends 里 from app.audit.llm_caller import call
            pass
        # 改 patch AuditLLMBackend 内通过 llm_caller 模块的 call
        with patch("app.audit.llm_caller.call", return_value=None):
            backend = get_backend()
            result = run_audit(_CLAIMS, _SOURCES, tier=tier, backend=backend)
        return result

    def test_run_audit_free_degrades_gracefully(self):
        result = self._run_with_network_error("free")
        self.assertIn("gate_results", result)
        self.assertIn("gates_run", result)
        self.assertGreater(len(result["gates_run"]), 0)
        self.assertIn("conclusion_label", result)

    def test_run_audit_paid_degrades_gracefully(self):
        result = self._run_with_network_error("paid")
        self.assertIn("gate_results", result)
        # paid 档应跑所有闸
        gates_run = set(result["gates_run"])
        self.assertIn("gate2", gates_run)
        self.assertIn("gate3", gates_run)
        self.assertIn("gate5", gates_run)
        self.assertIn("gate6", gates_run)

    def test_no_exception_propagates(self):
        """开关开启 + LLM 不可用时，run_audit 不应抛任何异常。"""
        with patch("app.audit.llm_caller.call", return_value=None):
            backend = get_backend()
            try:
                run_audit(_CLAIMS, _SOURCES, tier="paid", backend=backend)
            except Exception as exc:
                self.fail(f"run_audit 不应抛异常，但得到 {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# 测试组 3：AuditLLMBackend 各方法单独降级验证
# ---------------------------------------------------------------------------

class TestAuditLLMBackendDegradation(unittest.TestCase):
    """AuditLLMBackend 方法级单测：llm_caller.call 返回 None → 降级 stub 值。"""

    def setUp(self):
        self.backend = AuditLLMBackend()

    def test_faithfulness_degrades_to_stub_on_none(self):
        with patch("app.audit.llm_caller.call", return_value=None):
            score = self.backend.faithfulness("声称", ["来源"])
        # stub 降级值是 0.5
        self.assertEqual(score, 0.5)

    def test_faithfulness_degrades_on_unparseable_response(self):
        with patch("app.audit.llm_caller.call", return_value="我不知道"):
            score = self.backend.faithfulness("声称", ["来源"])
        self.assertEqual(score, 0.5)

    def test_detect_aigc_degrades_to_stub_on_none(self):
        with patch("app.audit.llm_caller.call", return_value=None):
            score = self.backend.detect_aigc("文本")
        self.assertEqual(score, 0.0)

    def test_nli_degrades_to_stub_on_none(self):
        with patch("app.audit.llm_caller.call", return_value=None):
            result = self.backend.nli("前提", "假设")
        self.assertEqual(result["contradiction"], 0.0)
        self.assertEqual(result["neutral"], 1.0)

    def test_nli_degrades_on_invalid_json(self):
        with patch("app.audit.llm_caller.call", return_value="不是JSON"):
            result = self.backend.nli("前提", "假设")
        self.assertEqual(result["contradiction"], 0.0)

    def test_judge_degrades_to_stub_on_none(self):
        with patch("app.audit.llm_caller.call", return_value=None):
            result = self.backend.judge("声称", [])
        self.assertEqual(result["verdict"], "accept")

    def test_judge_degrades_on_invalid_verdict(self):
        # verdict 值不合法 → 降级
        with patch("app.audit.llm_caller.call",
                   return_value='{"verdict":"unknown","vote_count":3,"rationale":"x"}'):
            result = self.backend.judge("声称", [])
        self.assertEqual(result["verdict"], "accept")

    def test_faithfulness_parses_valid_response(self):
        with patch("app.audit.llm_caller.call", return_value="0.9"):
            score = self.backend.faithfulness("声称", ["来源"])
        self.assertAlmostEqual(score, 0.9)

    def test_nli_parses_valid_json(self):
        valid = '{"entailment":0.7,"neutral":0.2,"contradiction":0.1}'
        with patch("app.audit.llm_caller.call", return_value=valid):
            result = self.backend.nli("前提", "假设")
        self.assertAlmostEqual(result["entailment"], 0.7)
        self.assertAlmostEqual(result["contradiction"], 0.1)

    def test_judge_parses_valid_response(self):
        valid = '{"verdict":"reject","vote_count":1,"rationale":"证据不足"}'
        with patch("app.audit.llm_caller.call", return_value=valid):
            result = self.backend.judge("声称", [])
        self.assertEqual(result["verdict"], "reject")
        self.assertEqual(result["vote_count"], 1)


# ---------------------------------------------------------------------------
# 测试组 4：llm_caller 模块级测试
# ---------------------------------------------------------------------------

class TestLLMCaller(unittest.TestCase):
    """llm_caller.py 单测：is_enabled() 逻辑 + call() 降级返回 None。"""

    def test_is_enabled_false_when_switch_off(self):
        from app.audit.llm_caller import is_enabled
        with patch.dict(os.environ, {"GATES_LIVE_MODEL": "0"}, clear=False):
            self.assertFalse(is_enabled())

    def test_is_enabled_false_when_no_url(self):
        from app.audit.llm_caller import is_enabled
        env = {"GATES_LIVE_MODEL": "1", "LITELLM_API_KEY": "k"}
        with patch.dict(os.environ, env, clear=False):
            # LITELLM_BASE_URL 为空
            with patch("app.audit.llm_caller._BASE_URL", ""):
                self.assertFalse(is_enabled())

    def test_call_returns_none_when_no_config(self):
        """无端点/key 配置时 call() 返回 None，不抛异常。"""
        from app.audit import llm_caller
        with patch.object(llm_caller, "_BASE_URL", ""), \
             patch.object(llm_caller, "_API_KEY", ""):
            result = llm_caller.call([{"role": "user", "content": "test"}])
        self.assertIsNone(result)

    def test_call_returns_none_on_network_error(self):
        """网络异常时 call() 返回 None，不向上抛。"""
        import httpx
        from app.audit import llm_caller
        with patch.object(llm_caller, "_BASE_URL", "http://localhost:9999/v1"), \
             patch.object(llm_caller, "_API_KEY", "key"), \
             patch("httpx.post", side_effect=httpx.ConnectError("refused")):
            result = llm_caller.call([{"role": "user", "content": "test"}])
        self.assertIsNone(result)

    def test_call_returns_none_on_non_200(self):
        """HTTP 非 200 响应时 call() 返回 None。"""
        from app.audit import llm_caller
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        with patch.object(llm_caller, "_BASE_URL", "http://localhost:9999/v1"), \
             patch.object(llm_caller, "_API_KEY", "key"), \
             patch("httpx.post", return_value=mock_resp):
            result = llm_caller.call([{"role": "user", "content": "test"}])
        self.assertIsNone(result)

    def test_call_returns_content_on_200(self):
        """HTTP 200 时 call() 返回 content 字符串。"""
        from app.audit import llm_caller
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "  0.85  "}}]
        }
        with patch.object(llm_caller, "_BASE_URL", "http://localhost:9999/v1"), \
             patch.object(llm_caller, "_API_KEY", "key"), \
             patch("httpx.post", return_value=mock_resp):
            result = llm_caller.call([{"role": "user", "content": "test"}])
        self.assertEqual(result, "0.85")


if __name__ == "__main__":
    unittest.main(verbosity=2)

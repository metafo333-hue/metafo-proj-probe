"""八闸真模型接线回归测试（P0-b·离线确定性）。

目的：防止「八闸静默退回 StubBackend」回归。
- 验证 get_backend() 按 env 正确选型（stub / litellm / audit_llm）
- 验证真 backend 的判定能贯穿 run_audit 全流水线（对抗证伪 D3-Judge 用真裁决）
不依赖网络：用 FakeLiveBackend 注入确定性非中性值。
"""
from __future__ import annotations

from typing import Any

import pytest

from app.audit.gates import run_audit
from app.audit.backends import get_backend, StubBackend, ModelBackend, LiteLLMBackend


class FakeLiveBackend(ModelBackend):
    """模拟真模型：返回会触发各闸阈值的非中性值（vs Stub 中性）。"""
    name = "fake_live"

    def faithfulness(self, claim: str, sources: list[str]) -> float:
        return 0.95                       # 高忠实（vs stub 0.5）

    def detect_aigc(self, text: str) -> float:
        return 0.85                       # 触发 AIGC 标记（vs stub 0.0）

    def nli(self, premise: str, hypothesis: str) -> dict[str, float]:
        return {"entailment": 0.05, "neutral": 0.05, "contradiction": 0.90}  # 触发矛盾

    def judge(self, claim: str, perspectives: list[dict[str, Any]]) -> dict[str, Any]:
        return {"verdict": "reject", "vote_count": 2,
                "rationale": "FAKE_LIVE_REJECT 对抗证伪真裁决"}


_CLAIMS = ["该账号粉丝数为 4645，主营魔芋源头直供。"]
_SOURCES = [{"url": "https://www.douyin.com/user/x", "title": "主页",
             "text": "北川魔芋姐 粉丝 4645 源头直供魔芋", "timestamp": "2026-06-22",
             "reliability_hint": "B", "source_type": "platform_official"}]


# ── get_backend 选型 ─────────────────────────────────────────────
def test_get_backend_default_is_stub(monkeypatch):
    monkeypatch.delenv("GATES_LIVE_MODEL", raising=False)
    monkeypatch.delenv("PROBE_LITELLM_KEY", raising=False)
    assert get_backend().name == "stub"


def test_get_backend_litellm_when_probe_key(monkeypatch):
    monkeypatch.delenv("GATES_LIVE_MODEL", raising=False)
    monkeypatch.setenv("PROBE_LITELLM_KEY", "x")
    assert get_backend().name == "litellm"


def test_get_backend_audit_llm_when_live_flag(monkeypatch):
    monkeypatch.setenv("GATES_LIVE_MODEL", "1")
    assert get_backend().name == "audit_llm"


# ── 真 backend 贯穿全流水线 ──────────────────────────────────────
def test_live_backend_changes_audit_outcome():
    """真 backend 的对抗证伪裁决必须贯穿到最终结论（vs stub 中性）。"""
    stub_res = run_audit(_CLAIMS, _SOURCES, tier="paid", backend=StubBackend())
    live_res = run_audit(_CLAIMS, _SOURCES, tier="paid", backend=FakeLiveBackend())

    # 闸6 对抗证伪：真裁决 rationale 必须出现在结果里（证明 backend 贯穿）
    g6 = live_res["gate_results"].get("gate6", {})
    g6_blob = str(g6)
    assert "FAKE_LIVE_REJECT" in g6_blob, "真 backend 的 judge 裁决未贯穿到 gate6"

    # stub 与 live 的审计结论应不同（中性 vs 触发阈值）
    assert stub_res["conclusion_label"] != live_res["conclusion_label"], \
        "真模型应改变审计结论，不应与 stub 中性结果一致"


def test_litellm_backend_falls_back_to_stub_on_no_model(monkeypatch):
    """LiteLLMBackend 在 _chat 返回 None（无 key）时降级 stub 中性值，不抛异常。"""
    monkeypatch.setattr("app.services.llm._chat", lambda *a, **k: None)
    be = LiteLLMBackend()
    assert be.faithfulness("c", ["s"]) == 0.5      # 降级回 stub 中性
    assert be.detect_aigc("t") == 0.0

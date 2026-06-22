"""P3-d 八闸生产默认 live 策略 + 可观测测试（离线·monkeypatch env）。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.audit.backends import get_backend, backend_status
from app.main import app


def _clear(mp):
    for k in ("GATES_LIVE_MODEL", "PROBE_LITELLM_KEY",
              "PROBE_AUDIT_DEFAULT_LIVE", "DEEPSEEK_API_KEY", "BAILIAN_API_KEY"):
        mp.delenv(k, raising=False)


def test_default_live_with_guokey(monkeypatch):
    """PROBE_AUDIT_DEFAULT_LIVE=1 + 国产 key → 走 litellm 真跑（无 ufo2 proxy 也行）。"""
    _clear(monkeypatch)
    monkeypatch.setenv("PROBE_AUDIT_DEFAULT_LIVE", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-x")
    assert get_backend().name == "litellm"


def test_default_live_off_without_flag(monkeypatch):
    """只有国产 key 但没开 flag → 仍 stub（不擅自花钱·尊重 opt-in）。"""
    _clear(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-x")
    assert get_backend().name == "stub"


def test_default_live_needs_key(monkeypatch):
    """开了 flag 但无任何国产 key → stub（fail-safe）。"""
    _clear(monkeypatch)
    monkeypatch.setenv("PROBE_AUDIT_DEFAULT_LIVE", "1")
    assert get_backend().name == "stub"


def test_explicit_switches_still_win(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("GATES_LIVE_MODEL", "1")
    assert get_backend().name == "audit_llm"
    _clear(monkeypatch)
    monkeypatch.setenv("PROBE_LITELLM_KEY", "k")
    assert get_backend().name == "litellm"


def test_backend_status_observability(monkeypatch):
    _clear(monkeypatch)
    st = backend_status()
    assert st["backend"] == "stub" and st["live"] is False and st["hint"]


def test_health_exposes_audit_backend():
    r = TestClient(app).get("/api/v1/health")
    body = r.json()
    assert body["code"] == 0
    assert "audit_backend" in body["data"]
    assert {"backend", "live", "reason"} <= set(body["data"]["audit_backend"])

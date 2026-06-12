"""probe L1 契约自检 + 端到端冒烟（TestClient · 不依赖外网）。"""
from fastapi.testclient import TestClient

from app.core import billing
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["code"] == 0
    assert r.json()["data"]["subdomain"] == "probe"


def test_manifest_three_dim():
    d = client.get("/api/v1/manifest").json()["data"]
    assert d["subdomain"] == "probe"
    assert "自媒体" in d["industry"]
    assert "链接分析" in d["angle"]
    assert d["pricing_tier"] == "免费+付费"
    assert d["version"] == "1"


def test_selftest_all_pass():
    d = client.post("/api/v1/selftest").json()["data"]
    assert d["ok"] is True, [c for c in d["checks"] if not c["ok"]]
    assert d["contract_ready"] is True


def test_double_helix_admission():
    """正常态：双螺旋门两轴 🟢 → 🟢🟢 准入。"""
    d = client.post("/api/v1/selftest").json()["data"]
    h = d["double_helix"]
    assert h["scale"]["verdict"] == "🟢"
    assert h["trust"]["verdict"] == "🟢"
    assert h["gate"].startswith("🟢🟢")


def test_double_helix_not_hardcoded(monkeypatch):
    """双螺旋 verdict 非硬编码：破坏「未付费不暗扣 premium」→ 信任轴 🔴 → 门否决。"""
    monkeypatch.setattr(billing, "cost_deep",
                        lambda authed_paid: {"base": 0.002, "premium_data": 9.9})
    d = client.post("/api/v1/selftest").json()["data"]
    assert d["double_helix"]["trust"]["verdict"] == "🔴"
    assert d["double_helix"]["gate"].startswith("🔴")
    assert d["ok"] is False


def test_invoke_async_returns_task():
    r = client.post("/api/v1/invoke",
                    json={"instruction": "提取", "context": {"url": "https://example.com"}})
    d = r.json()
    assert d["code"] == 0
    assert d["data"]["task_id"].startswith("t_")
    assert d["data"]["status_url"].startswith("/api/v1/task/")


def test_invoke_missing_link():
    r = client.post("/api/v1/invoke", json={"instruction": "你好"})
    assert r.json()["code"] == 4001


def test_task_not_found():
    r = client.get("/api/v1/task/t_nonexistent")
    assert r.json()["code"] == 4004

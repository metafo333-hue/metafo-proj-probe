"""scenario router HTTP 测试（P2-b·FastAPI TestClient·D2 走真适配器短超时）。"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_list_scenarios():
    r = client.get("/api/v1/scenario")
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    keys = {s["key"] for s in body["data"]["scenarios"]}
    assert {"B1", "C5", "D2", "E3"} <= keys      # 含 4 详细场景
    assert len(keys) == 13                        # 扩至 13 多源场景


def test_unknown_scenario():
    r = client.post("/api/v1/scenario/Z9", json={"query": "x"})
    assert r.json()["code"] == 4040


def test_missing_query():
    r = client.post("/api/v1/scenario/B1", json={})
    assert r.json()["code"] == 4001


def test_run_d2_real_adapters():
    """D2 走真 GitHub+OSV·返回情报包带可信度三标签。"""
    r = client.post("/api/v1/scenario/D2",
                    json={"query": "psf/requests", "audit": True})
    assert r.status_code == 200
    body = r.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["scenario"].startswith("D2")
    assert "conclusion_label" in data        # 护城河：带可信度的结论
    assert "sources" in data and "credibility_note" in data


def test_run_audit_skip_flag():
    """audit=False → 不出 conclusion_label（省成本）·走真适配器。"""
    r = client.post("/api/v1/scenario/D2",
                    json={"query": "psf/requests", "audit": False})
    data = r.json()["data"]
    assert "conclusion_label" not in data

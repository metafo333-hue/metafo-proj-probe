"""回归:本会话 2 生产 bug(invoke @property 误调 / deep structure KeyError)。"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_invoke_anonymous_not_500():
    r = client.post("/api/v1/invoke", json={
        "request": {"instruction": "分析这篇", "context": {"url": "https://example.com/x"}}})
    assert r.status_code == 200, r.text
    assert r.json().get("data", {}).get("task_id")


def test_invoke_no_url_4001():
    r = client.post("/api/v1/invoke", json={"request": {"instruction": "你好"}})
    assert r.json().get("code") == 4001


def test_pipeline_no_structure_keyaccess():
    import pathlib, app.services.pipeline as P
    src = pathlib.Path(P.__file__).read_text()
    assert 'report["structure"]' not in src
    assert "structure_formula" in src

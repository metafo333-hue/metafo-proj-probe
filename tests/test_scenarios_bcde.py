"""B/C/D/E 四赛道 MVP 场景回归测试（离线·注入 fake 适配器·无网络）。

验证：27 场景里 B/C/D/E 各 1 个从「纯设计」变「可跑通的多源情报包」。
"""
from __future__ import annotations

from app.services import scenarios as sc


def test_b1_company_multisource():
    out = sc.scenario_b1_company(
        "Acme Inc",
        _oc=lambda q: [{"name": q, "status": "active"}],
        _edgar=lambda q: [{"filing": "10-K"}],
        _wiki=lambda q: [{"title": q}],
    )
    assert out["scenario"].startswith("B1")
    assert out["ok"] and out["partial"] is False
    assert out["sources"]["ok"] == 3
    assert {f["source"] for f in out["findings"]} == {"opencorporates", "edgar", "wikipedia"}
    assert "交叉印证" in out["credibility_note"]


def test_c5_compliance_sanction_hit():
    """OFAC 命中 → 高风险红旗。"""
    hit = sc.scenario_c5_compliance(
        "Bad Entity",
        _ofac=lambda q: [{"sdn_name": q, "program": "SDGT"}],   # 命中
        _oc=lambda q: [{"name": q}],
    )
    assert "🔴" in hit["risk_flag"]

    clean = sc.scenario_c5_compliance(
        "Good Corp",
        _ofac=lambda q: [],                                     # 未命中
        _oc=lambda q: [{"name": q}],
    )
    assert "🟢" in clean["risk_flag"]


def test_d2_tech_repo_and_cve():
    out = sc.scenario_d2_tech(
        "psf/requests",
        _gh=lambda r: {"stars": 50000, "archived": False},
        _osv=lambda pkg: [{"id": "GHSA-xxxx", "summary": "demo cve"}],
    )
    assert out["scenario"].startswith("D2")
    assert out["sources"]["ok"] == 2
    gh = [f for f in out["findings"] if f["source"] == "github"][0]
    assert gh["data"]["stars"] == 50000


def test_e3_source_partial_when_one_fails():
    """一个源抛错 → partial=True，其余源照常出（OS1 隔离贯穿到场景层）。"""
    out = sc.scenario_e3_source(
        "konjac health",
        _wiki=lambda q: [{"title": q}],
        _gdelt=lambda q: (_ for _ in ()).throw(RuntimeError("gdelt down")),  # 抛错
        _openalex=lambda q: [{"work": "paper1"}],
    )
    assert out["partial"] is True
    assert out["sources"]["ok"] == 2
    assert out["sources"]["error"] == 1
    assert any("gdelt" in s for s in out["sources"]["sources_failed"])


def test_registry_complete():
    assert set(sc.REGISTRY) == {"B1", "C5", "D2", "E3"}
    for fn in sc.REGISTRY.values():
        assert callable(fn)


# ── P2-a: 场景过八闸出可信度三标签（护城河）────────────────────
def test_scenario_carries_conclusion_label():
    """每个情报包必须带可信度三标签（probe 价值：带可信度的结论·非裸数据）。"""
    out = sc.scenario_b1_company(
        "Acme Inc",
        _oc=lambda q: [{"name": q, "status": "active"}],
        _edgar=lambda q: [{"filing": "10-K"}],
        _wiki=lambda q: [{"title": q}],
    )
    cl = out["conclusion_label"]
    assert set(cl) >= {"source_reliability", "confidence_level", "evidence_strength"}
    assert cl["confidence_level"]                       # 非空
    assert "trace_id" in cl                             # 可回放溯源


def test_enrich_audit_no_sources():
    """无可用源 → 标「不可出」，不伪造可信度。"""
    pkt = {"query": "x", "scenario": "T", "partial": True, "findings": []}
    out = sc.enrich_with_audit(pkt)
    assert out["conclusion_label"]["confidence_level"] == "无源·不可出"


def test_scenario_audit_can_be_skipped():
    """audit=False（_assemble 直传）时不过八闸，省成本。"""
    from app.datasources.orchestrator import SourceSpec, fan_out
    out = fan_out([SourceSpec("s", lambda q: [1], ("q",))])
    pkt = sc._assemble("T", "q", ["D1"], out, audit=False)
    assert "conclusion_label" not in pkt

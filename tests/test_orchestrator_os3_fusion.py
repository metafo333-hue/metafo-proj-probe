"""OS3 多源融合·真值发现回归测试（离线确定性）。

覆盖：源加权投票胜出、冲突检测、佐证度、置信度、FanOut→融合→audit claims 桥接。
"""
from __future__ import annotations

from app.datasources.orchestrator import SourceSpec, fan_out
from app.datasources.orchestrator.fusion import (
    Claim, fuse_claims, fuse_fanout, to_audit_claims, reliability_weight,
)


def test_weighted_truth_discovery_beats_majority():
    """2 个低权 C 源说 100，1 个高权 A 源说 200 → A 加权胜出（非多数票）。"""
    claims = [
        Claim("follower", 100, "wikipedia", reliability_weight("C")),  # 0.4
        Claim("follower", 100, "gdelt", reliability_weight("C")),      # 0.4
        Claim("follower", 200, "edgar", reliability_weight("A")),      # 1.0
    ]
    fused = {f.key: f for f in fuse_claims(claims)}
    f = fused["follower"]
    assert f.value == 200, "高权威源应加权胜出，而非低权多数票"
    assert f.conflict is True
    assert f.sources == ["edgar"]
    assert any(a["value"] == 100 for a in f.alternatives)


def test_corroboration_and_confidence():
    """3 源一致 → 佐证 3·置信 1.0·无冲突。"""
    claims = [Claim("status", "active", s, 0.7) for s in ("oc", "edgar", "wiki")]
    f = fuse_claims(claims)[0]
    assert f.corroboration == 3
    assert f.confidence == 1.0
    assert f.conflict is False


def test_fuse_fanout_with_reliability():
    def _src_a(q):
        return [{"name": "Acme", "country": "US"}]

    def _src_b(q):
        return [{"name": "Acme", "country": "UK"}]   # country 冲突

    out = fan_out([
        SourceSpec("edgar", _src_a, ("q",)),
        SourceSpec("wikipedia", _src_b, ("q",)),
    ])
    fused = fuse_fanout(out, reliability={"edgar": "A", "wikipedia": "C"})
    by = {f.key: f for f in fused}
    assert by["name"].conflict is False and by["name"].corroboration == 2
    assert by["country"].value == "US"      # edgar(A·1.0) 胜过 wikipedia(C·0.4)
    assert by["country"].conflict is True


def test_to_audit_claims_bridge():
    claims = [
        Claim("a", 1, "s1", 1.0), Claim("a", 1, "s2", 1.0),   # 一致
        Claim("b", "x", "s1", 1.0), Claim("b", "y", "s2", 1.0),  # 冲突
    ]
    fused = fuse_claims(claims)
    good, conflicts = to_audit_claims(fused)
    assert any("a = 1" in g for g in good)
    assert any("b 多源冲突" in c for c in conflicts)

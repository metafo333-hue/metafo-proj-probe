"""probe 审核栈 Wave 2 · 双审 8 闸 + Admiralty 标准 + 强度分档。

子模块
-------
standards   Admiralty 双轴枚举 + 证据强度 + ConclusionLabel 强制元数据
trace       闸0 过程留痕：append-only 事件 + SHA-256 哈希链 + run_snapshot
gates       8 闸 pipeline + run_audit(claims, sources, tier)
backends    可插拔 model backend 接口 + StubBackend 默认实现

快速用法
-------
    from app.audit.gates import run_audit
    result = run_audit(claims=[...], sources=[...], tier="free")
"""
from app.audit.standards import (
    SourceReliability,
    InfoCredibility,
    EvidenceStrength,
    ConfidenceLevel,
    ConclusionLabel,
)
from app.audit.gates import run_audit
from app.audit.trace import AuditTrace
from app.audit.backends import StubBackend

__all__ = [
    "SourceReliability",
    "InfoCredibility",
    "EvidenceStrength",
    "ConfidenceLevel",
    "ConclusionLabel",
    "run_audit",
    "AuditTrace",
    "StubBackend",
]

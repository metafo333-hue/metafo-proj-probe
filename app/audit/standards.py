"""Admiralty 双轴 + 证据强度 + ConclusionLabel · probe 审核标准框架。

设计依据：probe-audit-system-v1.md § 三（专业标准框架）

铁律
----
- 源可靠性与信息可信度物理隔离独立评分（防 87% 对角线偏差陷阱）。
- High 置信需 ≥2 独立源 + A/B 级源可靠性。
- 每条发布结论必须携带完整 ConclusionLabel。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Admiralty Code 双轴（源可靠性 A-F × 信息可信度 1-6）
# ---------------------------------------------------------------------------

class SourceReliability(str, Enum):
    """Admiralty 源可靠性六级（A=完全可靠 → F=无法判断）。

    评分规则：先评源，独立于信息内容评分，物理隔离。
    A/B 级：多次核实可信的一手权威源。
    C 级：通常可靠但有时出错。
    D 级：曾提供不准确信息。
    E 级：不可靠，多次不准确。
    F 级：无历史可参考，无法判断。
    """
    A = "A"  # 完全可靠（Completely Reliable）
    B = "B"  # 通常可靠（Usually Reliable）
    C = "C"  # 基本可靠（Fairly Reliable）
    D = "D"  # 通常不可靠（Not Usually Reliable）
    E = "E"  # 不可靠（Unreliable）
    F = "F"  # 无法判断（Reliability Cannot Be Judged）

    # 自动拦截阈值：D/E/F 级源触发降级警告
    @property
    def auto_downgrade(self) -> bool:
        return self in (self.E, self.F)

    @property
    def rank(self) -> int:
        """数值越低越可靠（A=1, F=6）。"""
        return {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6}[self.value]


class InfoCredibility(str, Enum):
    """Admiralty 信息可信度六级（1=经多源确认 → 6=无法判断）。

    评分规则：独立于源可靠性评分，仅看信息本身。
    1：经多个独立来源确认。
    2：可能为真（已知信息逻辑一致，单源）。
    3：可能为真（弱，逻辑合理但未确认）。
    4：存疑（与已知信息矛盾，但不排除）。
    5：不可能（大量证据相反）。
    6：无法判断（信息新颖，无参照物）。
    """
    ONE   = "1"  # 经多源确认
    TWO   = "2"  # 可能为真
    THREE = "3"  # 可能为真（弱）
    FOUR  = "4"  # 存疑
    FIVE  = "5"  # 不可能
    SIX   = "6"  # 无法判断

    @property
    def rank(self) -> int:
        """数值越低越可信（1=最可信, 6=无法判断）。"""
        return int(self.value)


# ---------------------------------------------------------------------------
# 证据强度（情报界三级）
# ---------------------------------------------------------------------------

class EvidenceStrength(str, Enum):
    """证据强度三级 + Contested。

    Strong    : ≥2 独立高质量源（A/B级）+ 信息可信度 1/2，互相印证。
    Moderate  : 单高质量源 或 多中质量源（C级），信息可信度 2/3。
    Weak      : 碎片化/存疑，单源或低质量，信息可信度 4/5/6。
    Contested : 存在明确矛盾来源，需对抗证伪（闸6）处理。
    """
    STRONG    = "Strong"
    MODERATE  = "Moderate"
    WEAK      = "Weak"
    CONTESTED = "Contested"


# ---------------------------------------------------------------------------
# 三级置信
# ---------------------------------------------------------------------------

class ConfidenceLevel(str, Enum):
    """三级置信度（情报界标准）。

    High     : 多独立源 + A/B 级源可靠性 + 交叉印证（闸2通过）。
    Moderate : 单高质量源 或 多中质量源，无明显矛盾。
    Low      : 碎片化/存疑/单源/未经核查。
    """
    HIGH     = "High"
    MODERATE = "Moderate"
    LOW      = "Low"


# ---------------------------------------------------------------------------
# ConclusionLabel：每条结论的强制元数据标签
# ---------------------------------------------------------------------------

@dataclass
class ConclusionLabel:
    """每条发布结论必须携带的强制元数据标签。

    两轴物理隔离：source_reliability 与 info_credibility 独立评分。
    High 置信约束：confidence_level=High 时，source_count≥2 且
        source_reliability 必须为 A 或 B，否则自动降为 Moderate。

    字段说明
    --------
    source_reliability  : Admiralty 源可靠性（A-F），按最弱源评
    info_credibility    : Admiralty 信息可信度（1-6），独立于源评
    confidence_level    : 三级置信度（High/Moderate/Low）
    source_count        : 参与本条结论的独立来源数量
    source_types        : 来源类型列表（primary/secondary/tertiary）
    evidence_strength   : 证据强度分级（Strong/Moderate/Weak/Contested）
    verification_methods: 使用的审核闸列表（如 ["gate1", "gate2", "gate6"]）
    reviewer_count      : 独立审核者数（四眼原则要求 ≥2 才算 High）
    aigc_flag           : 是否检测到 AI 生成内容（闸3）
    last_verified       : 最后核查时间（ISO 8601 UTC）
    trace_id            : 贯穿全流水线的 trace ID（闸0 生成）
    gate_results        : 各闸原始结果摘要（调试/溯源用）
    """
    source_reliability:   SourceReliability = SourceReliability.F
    info_credibility:     InfoCredibility   = InfoCredibility.SIX
    confidence_level:     ConfidenceLevel   = ConfidenceLevel.LOW
    source_count:         int               = 0
    source_types:         list              = field(default_factory=list)
    evidence_strength:    EvidenceStrength  = EvidenceStrength.WEAK
    verification_methods: list              = field(default_factory=list)
    reviewer_count:       int               = 0
    aigc_flag:            bool              = False
    last_verified:        str               = ""
    trace_id:             str               = ""
    gate_results:         dict              = field(default_factory=dict)

    def __post_init__(self) -> None:
        """自动约束：High 置信需 ≥2 独立源 + A/B 级可靠性。"""
        if not self.last_verified:
            self.last_verified = datetime.now(timezone.utc).isoformat()
        self._enforce_high_confidence_constraint()

    def _enforce_high_confidence_constraint(self) -> None:
        """High 置信的硬约束：不满足则自动降为 Moderate。"""
        if self.confidence_level == ConfidenceLevel.HIGH:
            if self.source_count < 2:
                self.confidence_level = ConfidenceLevel.MODERATE
            elif self.source_reliability not in (SourceReliability.A, SourceReliability.B):
                self.confidence_level = ConfidenceLevel.MODERATE

    def to_dict(self) -> dict:
        """输出标准 JSON 兼容字典（用于七段报告输出）。"""
        return {
            "source_reliability":   self.source_reliability.value,
            "info_credibility":     self.info_credibility.value,
            "confidence_level":     self.confidence_level.value,
            "source_count":         self.source_count,
            "source_types":         self.source_types,
            "evidence_strength":    self.evidence_strength.value,
            "verification_methods": self.verification_methods,
            "reviewer_count":       self.reviewer_count,
            "aigc_flag":            self.aigc_flag,
            "last_verified":        self.last_verified,
            "trace_id":             self.trace_id,
            "gate_results":         self.gate_results,
        }

    @classmethod
    def stub(cls, trace_id: str = "") -> "ConclusionLabel":
        """返回一个中性 stub label，用于 StubBackend / 测试。"""
        return cls(
            source_reliability   = SourceReliability.F,
            info_credibility     = InfoCredibility.SIX,
            confidence_level     = ConfidenceLevel.LOW,
            source_count         = 0,
            source_types         = [],
            evidence_strength    = EvidenceStrength.WEAK,
            verification_methods = [],
            reviewer_count       = 0,
            aigc_flag            = False,
            trace_id             = trace_id,
        )

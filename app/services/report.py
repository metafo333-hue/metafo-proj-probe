"""七段报告 builder · Wave 2 交付层。

硬约束（对齐核查 C-1）：
  ① 首屏速判   A/B/C/D 综合评级 + 15 秒拍板 + 三步行动
  ② 真相核查   D1 verdict + 置信度
  ③ 内容拆解   D2 结构公式 + 节奏拐点
  ④ 竞品横评   (paid only)
  ⑤ 二创方案   借/换/串三路（paid: 完整；preview: 仅1条简版；public: 裁掉）
  ⑥ 风险合规   D8 合规评估
  ⑦ 完整明细   原始维度数据摘要（不透传原始 JSON · C-8）

评级规则（C-1 注：非字数判，综合 D1/D2/D8 结论）：
  A: D1 低风险 + 结构完整 + D8 合规无风险
  B: D1 中风险 或 结构有缺陷 或 轻微合规提示
  C: D1 高风险 或 明显结构问题 或 合规风险
  D: D1 失实/高风险 + 结构严重缺陷 + 合规高风险（≥2 项重度）
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal

from app.services import llm as llm_service

RatingLiteral = Literal["A", "B", "C", "D"]


# ─────────────────── 七段 dataclass ───────────────────

@dataclass
class Section1FirstScreen:
    """① 首屏速判 · 最重要的 15 秒拍板区。"""
    rating: RatingLiteral             # A/B/C/D 综合评级
    headline: str                     # 一句话结论（≤30 字）
    decision_tip: str                 # 15 秒拍板语（≤50 字）
    action_steps: list[str]           # 三步行动（长度 == 3）
    aigc_flag: bool = False


@dataclass
class Section2FactCheck:
    """② 真相核查 · D1 维度。"""
    overall_credibility: str          # 低风险/中风险/高风险/未评估
    claims_summary: list[dict]        # [{claim, verdict, reason}] 脱敏摘要（禁透传原始）
    aigc_flag: bool = False
    _stub: bool = False


@dataclass
class Section3ContentBreakdown:
    """③ 内容拆解 · D2 结构维度。"""
    structure_formula: str
    hook_summary: str
    reuse_tags: list[str]
    aigc_flag: bool = False
    _stub: bool = False


@dataclass
class Section4CompetitorMatrix:
    """④ 竞品横评 · paid only（preview/public 置 None）。"""
    items: list[dict] | None = None   # [{name, score, note}]
    locked: bool = True
    aigc_flag: bool = False


@dataclass
class Section5RecreationPaths:
    """⑤ 二创方案 · 三层裁剪（C-2）。"""
    priority: str | None = None
    priority_reason: str | None = None
    borrow: dict | None = None
    adapt: dict | None = None
    remix: dict | None = None
    preview_hint: str | None = None   # preview 层仅露 1 条简版文字
    locked: bool = False
    aigc_flag: bool = False
    _stub: bool = False


@dataclass
class Section6RiskCompliance:
    """⑥ 风险合规 · D8 维度。"""
    compliance_note: str
    risk_level: str                   # 低/中/高
    aigc_flag: bool = False


@dataclass
class Section7FullDetail:
    """⑦ 完整明细 · 原始维度摘要（不透传第三方原始 JSON · C-8）。"""
    kind: str
    title: str
    source_hint: str                  # 来源说明（URL 脱敏后的域名摘要）
    word_count_hint: int
    dimensions_summary: dict          # 已加工摘要，禁原始字段透传
    aigc_flag: bool = False


@dataclass
class SevenSectionReport:
    """七段报告结构体（对应 C-1 精确骨架）。"""
    s1_first_screen: Section1FirstScreen
    s2_fact_check: Section2FactCheck
    s3_content_breakdown: Section3ContentBreakdown
    s4_competitor_matrix: Section4CompetitorMatrix
    s5_recreation_paths: Section5RecreationPaths
    s6_risk_compliance: Section6RiskCompliance
    s7_full_detail: Section7FullDetail
    aigc_flag: bool = False
    _stub: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ─────────────────── 评级逻辑 ───────────────────

def _compute_rating(
    credibility: str,
    structure_formula: str,
    risk_level: str,
) -> RatingLiteral:
    """综合 D1/D2/D8 输出 A/B/C/D 评级（C-1 注：非字数判）。"""
    # 各维度得分 (0=好, 1=中, 2=差)
    d1_score = {"低风险": 0, "未评估": 1, "中风险": 1, "高风险": 2}.get(credibility, 1)
    # D2：结构公式是否有实质内容
    d2_score = 0 if (structure_formula and "待 LLM" not in structure_formula
                     and len(structure_formula) > 8) else 1
    d8_score = {"低": 0, "中": 1, "高": 2}.get(risk_level, 1)

    total = d1_score + d2_score + d8_score
    if total == 0:
        return "A"
    elif total <= 2:
        return "B"
    elif total <= 4:
        return "C"
    else:
        return "D"


def _rating_headline(rating: RatingLiteral, kind: str, title: str) -> tuple[str, str, list[str]]:
    """根据评级生成 headline / decision_tip / action_steps。"""
    short_title = (title or kind or "该内容")[:15]
    templates: dict[str, tuple[str, str, list[str]]] = {
        "A": (
            f"{short_title}：高质量·可参考",
            "内容可信度高，结构清晰，合规无大风险，可直接作为参考标杆。",
            ["直接收录为标杆案例", "提取结构公式复用", "评估二创可行性"],
        ),
        "B": (
            f"{short_title}：质量中上·审慎参考",
            "内容整体可信，但存在局部瑕疵，建议重点核查标记条目后参考。",
            ["核查标记疑点条目", "借鉴结构公式（回避有问题节点）", "二创前评估版权风险"],
        ),
        "C": (
            f"{short_title}：质量存疑·谨慎使用",
            "发现较明显问题（真实性/结构/合规），不建议直接参考，需进一步核查。",
            ["先核实主要疑点再决策", "谨慎参考结构，规避高风险段", "二创前务必过合规门"],
        ),
        "D": (
            f"{short_title}：风险高·不建议参考",
            "多维度重度问题，不建议作为参考或二创素材，规避风险。",
            ["暂不参考该内容", "记录风险点供后续对比", "如需用须人工深度审核"],
        ),
    }
    return templates[rating]


# ─────────────────── 主 builder ───────────────────

def build_seven_section_report(
    audit_result: dict[str, Any],
    kind: str = "article",
) -> SevenSectionReport:
    """从 audit_result 构建七段报告（C-1 骨架）。

    audit_result 期望字段（可缺失，缺失走降级桩）：
      - title: str
      - text: str
      - url: str
      - fact_check: dict        ← llm.fact_check 结果
      - structure: dict         ← llm.analyze_structure 结果
      - recreation: dict        ← llm.generate_recreation_paths 结果
      - compliance_note: str
      - risk_level: str
    """
    title = audit_result.get("title", "")
    text = audit_result.get("text", "")
    url = audit_result.get("url", "")
    is_stub = audit_result.get("_stub", False)

    # ── D1 真相核查 ──
    fact_check_raw = audit_result.get("fact_check")
    if fact_check_raw is None:
        fact_check_raw = llm_service.fact_check(text)
    credibility = fact_check_raw.get("overall_credibility", "未评估")
    # 脱敏摘要：只取 claim/verdict/reason，禁止透传 source_url 等原始字段（C-8）
    claims_summary = [
        {"claim": c.get("claim", "")[:80], "verdict": c.get("verdict", "❓"),
         "reason": c.get("reason", "")[:100]}
        for c in fact_check_raw.get("claims", [])[:5]
    ]

    # ── D2 内容拆解 ──
    structure_raw = audit_result.get("structure")
    if structure_raw is None:
        structure_raw = llm_service.analyze_structure(text, title)
    structure_formula = structure_raw.get("structure_formula", "未分析")
    hook_summary = ""
    hook = structure_raw.get("hook", {})
    if isinstance(hook, dict):
        hook_summary = f"{hook.get('type', '')}·{hook.get('text', '')[:30]}"
    reuse_tags = structure_raw.get("reuse_tags", [])

    # ── D8 合规 ──
    compliance_note = audit_result.get("compliance_note", "未评估")
    risk_level = audit_result.get("risk_level", "中")

    # ── 综合评级（C-1：非字数判） ──
    rating: RatingLiteral = _compute_rating(credibility, structure_formula, risk_level)
    headline, decision_tip, action_steps = _rating_headline(rating, kind, title)

    # ── D7 二创 ──
    recreation_raw = audit_result.get("recreation")
    if recreation_raw is None:
        recreation_raw = llm_service.generate_recreation_paths(
            structure_raw, title, rating, compliance_note)
    rec_stub = recreation_raw.get("_stub", False)

    # ── 组装七段 ──
    s1 = Section1FirstScreen(
        rating=rating,
        headline=headline,
        decision_tip=decision_tip,
        action_steps=action_steps,
        aigc_flag=fact_check_raw.get("aigc_flag", False)
                  or structure_raw.get("aigc_flag", False),
    )

    s2 = Section2FactCheck(
        overall_credibility=credibility,
        claims_summary=claims_summary,
        aigc_flag=fact_check_raw.get("aigc_flag", False),
        _stub=fact_check_raw.get("_stub", False),
    )

    s3 = Section3ContentBreakdown(
        structure_formula=structure_formula,
        hook_summary=hook_summary,
        reuse_tags=reuse_tags,
        aigc_flag=structure_raw.get("aigc_flag", False),
        _stub=structure_raw.get("_stub", False),
    )

    # ④ 竞品横评：builder 层保留占位，三层裁剪由 guards.redact_by_tier 控制
    s4 = Section4CompetitorMatrix(
        items=audit_result.get("competitor_matrix"),
        locked=audit_result.get("competitor_matrix") is None,
        aigc_flag=False,
    )

    s5 = Section5RecreationPaths(
        priority=recreation_raw.get("priority"),
        priority_reason=recreation_raw.get("priority_reason"),
        borrow=recreation_raw.get("borrow"),
        adapt=recreation_raw.get("adapt"),
        remix=recreation_raw.get("remix"),
        locked=False,
        aigc_flag=recreation_raw.get("aigc_flag", False),
        _stub=rec_stub,
    )

    s6 = Section6RiskCompliance(
        compliance_note=compliance_note,
        risk_level=risk_level,
        aigc_flag=False,
    )

    # ⑦ 完整明细：只存摘要，禁透传原始 JSON（C-8）
    import urllib.parse as _up
    try:
        domain_hint = _up.urlparse(url).netloc or "未知来源"
    except Exception:
        domain_hint = "未知来源"

    s7 = Section7FullDetail(
        kind=kind,
        title=title[:80],
        source_hint=domain_hint,
        word_count_hint=len(text),
        dimensions_summary={
            "d1_credibility": credibility,
            "d2_structure_formula": structure_formula[:60],
            "d8_risk": risk_level,
            "tags_count": len(reuse_tags),
            "claims_checked": len(claims_summary),
        },
        aigc_flag=s1.aigc_flag or s2.aigc_flag or s3.aigc_flag,
    )

    return SevenSectionReport(
        s1_first_screen=s1,
        s2_fact_check=s2,
        s3_content_breakdown=s3,
        s4_competitor_matrix=s4,
        s5_recreation_paths=s5,
        s6_risk_compliance=s6,
        s7_full_detail=s7,
        aigc_flag=s1.aigc_flag,
        _stub=is_stub or rec_stub or s2._stub or s3._stub,
    )

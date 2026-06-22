"""RouteDecider · 脊髓：ProbeBrief → RouteDecision（裁哪几层/拉几圈/开哪几段）。

decision 反向定采集预算（go_no_go 无裸数字铁律 → 必拉竞品圈）。
替代 pipeline._is_deep 关键词二分（旧路径保留作向后兼容降级）。
裁剪逻辑真源：运营报告/probe-ask-first-upgrade-design-v2.2.md §四/五/六。

首版边界（诚实标注）：
- layers（九层数字编号）首版占位空 → W5 与 probe 九层组件实际编号对齐后填实。
- fusion_weights 首版空 → L5 融合在 W5 接。
本文件只定"路径→圈/验证面/七段/采集预算"裁剪（v2.2 §五裁剪表完整·可直接写）。
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

from app.schemas.brief import ProbeBrief
from app.schemas.probe_intent_enum import PathEnum, DecisionEnum


@dataclass
class RouteDecision:
    path: PathEnum
    circles: list = field(default_factory=list)        # target/account/sibling/competitor/discover
    account_crosseval: bool = False                    # T17 账号横评
    verify_face: list = field(default_factory=list)    # text_gates/lineage_quant/dedup_original
    report_sections: dict = field(default_factory=dict)  # s1-s7 + beyond 开关
    depth: str = "standard"                            # light/standard/deep
    stop_cond: str = ""
    layers: list = field(default_factory=list)         # 首版占位·W5 与九层编号对齐
    fusion_weights: dict = field(default_factory=dict)  # 首版空·L5 融合 W5 接

    def to_dict(self) -> dict:
        d = asdict(self)
        d["path"] = self.path.value
        return d


def _resolve_circles(decision: DecisionEnum, is_paid: bool) -> list:
    """decision 反向定采集圈数（§六：决策需要什么参照系，就采多大范围）。"""
    if decision == DecisionEnum.go_no_go:
        # 高 blast：判断合作需外部参照系 → 竞品圈（付费才拉，但 go_no_go 铁律下见 decide 兜底）
        return ["target", "account", "sibling"] + (["competitor"] if is_paid else [])
    if decision == DecisionEnum.self_review:
        # 低 blast：只需自身纵向对比
        return ["account", "sibling"]
    # create / find_target → 目标尚不存在 → 触发 L2 发现层
    return ["discover"]


def _all_sections(beyond: bool = True) -> dict:
    s = {f"s{i}": True for i in range(1, 8)}
    s["beyond"] = beyond
    return s


def decide(brief: ProbeBrief, principal=None) -> RouteDecision:
    """ProbeBrief → RouteDecision。按 4 路径裁剪 + decision 反向定圈。"""
    is_paid = bool(principal and getattr(principal, "tier", "free") in ("paid", "member"))
    rd = RouteDecision(path=brief.path)
    rd.circles = _resolve_circles(brief.decision, is_paid)
    rd.account_crosseval = True   # 四路径都开账号横评（T17·L2+L3 粒度）

    if brief.path == PathEnum.D:        # 对标诊断（go_no_go/self_review）
        rd.verify_face = ["text_gates", "lineage_quant", "dedup_original"]
        rd.report_sections = _all_sections()
        rd.depth = "deep" if is_paid else "standard"
    elif brief.path == PathEnum.B:      # 二创借鉴
        rd.verify_face = ["text_gates", "dedup_original"]  # L4 原创性去重·标搬运链
        rd.report_sections = _all_sections()
        if is_paid and "competitor" not in rd.circles:
            rd.circles.append("competitor")   # 二创付费必拉竞品（借鉴核心）
    elif brief.path == PathEnum.C:      # 选题灵感（常无 subject）
        rd.circles = ["discover"]          # L2 发现漏斗
        rd.verify_face = ["lineage_quant"]
        rd.report_sections = _all_sections(beyond=True)  # 前瞻段=选题核心
    else:                               # A 原创放大
        rd.verify_face = ["text_gates", "dedup_original"]  # 护你原创
        rd.report_sections = _all_sections()

    # go_no_go 无裸数字铁律：竞品圈必须（即便免费档·判断合作离不开外部参照系）
    if brief.decision == DecisionEnum.go_no_go and "competitor" not in rd.circles:
        rd.circles.append("competitor")

    rd.stop_cond = f"圈={rd.circles} 满采 或 连续2轮无新增"
    return rd

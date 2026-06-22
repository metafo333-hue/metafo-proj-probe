"""L1 §7 guards 硬约束 · 每次出口校验（C4 穿透）。

1 aigc_flag 必填且为 bool
2 禁直吐第三方原始数据（meta.raw_passthrough=True 即拒）
3 AI 生成内容双标识（meta.aigc_flag + deliverable 隐式 _aigc_notice）
4 公开/付费三层深度线：公开结论 / 免费预览 / 付费深度，不泄露付费价值
"""
from __future__ import annotations

from typing import Any


class GuardError(Exception):
    """出口契约违规。"""


DEPTH_PUBLIC = "public"     # 公开结论（匿名可见）
DEPTH_PREVIEW = "preview"   # 免费预览（登录免费档）
DEPTH_PAID = "paid"         # 付费深度（paid/member）

# 个保法最小必要红线（仅公开元数据·不建个人档案 · probe 数据来源铁律 第5条）
PIPL_GENERAL_LIMIT = 5000    # 普通个人信息入刑红线（条）
PIPL_SENSITIVE_LIMIT = 500   # 敏感个人信息入刑红线（条）


def check_response(resp: dict[str, Any]) -> None:
    """出口硬校验（aigc_flag + 禁直吐）。"""
    meta = resp.get("meta")
    if not isinstance(meta, dict):
        raise GuardError("出口缺 meta")
    if "aigc_flag" not in meta or not isinstance(meta["aigc_flag"], bool):
        raise GuardError("aigc_flag 必填且为 bool（02-api §7.1）")
    if meta.get("raw_passthrough") is True:
        raise GuardError("C4: 禁直吐第三方原始数据（02-api §7.2）")


# ─────────────────── C-2 三层裁剪（七段报告·唯一裁剪函数） ───────────────────
# 注：旧 apply_depth_line（扁平版）已于 2026-06-13 按 D2 裁定删除，
#     全局统一走下方 redact_by_tier（七段 s1-s7·更精确）。

def redact_by_tier(report: "dict[str, Any]", tier: str) -> "dict[str, Any]":
    """按 public/preview/paid 对七段报告执行三层深度线裁剪（C-2 硬约束）。

    裁剪规则（来自对齐核查 C-2）：
      public  → 仅保留 s1 评级 + 一句话 headline；禁显 s3 结构/s4 竞品/s5 二创/s6 合规明细
      preview → + s3 结构骨架 + s5 仅 1 条二创简版（priority + priority_reason）；锁 s4/s6 详情
      paid    → 完整七段全开

    C-8 保证：无论哪档，均不透传第三方原始 JSON。
    """
    import copy
    r = copy.deepcopy(report)

    if tier in ("paid", "member"):
        r["depth"] = DEPTH_PAID
        return r

    if tier == "free":
        # preview：开 s1 + s3 骨架 + s5 一条简版，锁 s4/s6 完整内容
        r["depth"] = DEPTH_PREVIEW
        # s3：只留 structure_formula，去掉 hook_summary/reuse_tags
        if "s3_content_breakdown" in r:
            s3 = r["s3_content_breakdown"]
            r["s3_content_breakdown"] = {
                "structure_formula": s3.get("structure_formula", ""),
                "aigc_flag": s3.get("aigc_flag", False),
                "_preview": True,
            }
        # s4：全锁
        r["s4_competitor_matrix"] = {
            "locked": True,
            "unlock_hint": "竞品横评需付费档解锁",
        }
        # s5：仅露 priority + priority_reason 一条简版
        if "s5_recreation_paths" in r:
            s5 = r["s5_recreation_paths"]
            r["s5_recreation_paths"] = {
                "preview_hint": f"{s5.get('priority', '借路')}：{s5.get('priority_reason', '')}",
                "locked": True,
                "unlock_hint": "完整借/换/串三路方案需付费档解锁",
                "aigc_flag": s5.get("aigc_flag", False),
                "_preview": True,
            }
        # s6：只留 risk_level，锁合规详情
        if "s6_risk_compliance" in r:
            s6 = r["s6_risk_compliance"]
            r["s6_risk_compliance"] = {
                "risk_level": s6.get("risk_level", "中"),
                "locked": True,
                "unlock_hint": "合规详情需付费档解锁",
            }
        r["locked_sections"] = ["s4_competitor_matrix", "s5_recreation_full", "s6_compliance_detail"]
        r["unlock_hint"] = "付费档解锁完整竞品横评 / 三路二创 / 合规明细"
        return r

    # public（匿名）：只留评级 + headline + 一句话 decision_tip
    s1 = r.get("s1_first_screen", {})
    return {
        "depth": DEPTH_PUBLIC,
        "rating": s1.get("rating"),
        "headline": s1.get("headline", ""),
        "decision_tip": s1.get("decision_tip", ""),
        "locked_sections": ["s3_content_breakdown", "s4_competitor_matrix",
                             "s5_recreation_paths", "s6_risk_compliance", "s7_full_detail"],
        "unlock_hint": "登录看结构预览，付费档解锁完整七段深度报告",
    }

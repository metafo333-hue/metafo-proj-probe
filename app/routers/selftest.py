"""POST /api/v1/selftest · 准入自检（02-api §5 · 过 C2 + 双螺旋门）。

校验 probe 对 L1 契约的实现合规（不依赖外网，稳定可重复）：
契约结构 / guards / 三层深度线 / 计费档位 / L0 可加载。

双螺旋门（标准 18 · 卡1 上架工具）：两轴 verdict 由真实可证伪信号派生（非硬编码）——
任一关键 check 失败 → 该轴 🔴 → 门否决。母体侧 C2 评分卡（完成度/准确/省力/盲评）另行评定。
真理源：docs/standards/double-helix-gate.md
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core import billing, guards
from app.routers.manifest import manifest_data

router = APIRouter(prefix="/api/v1", tags=["selftest"])


def _rejects(resp: dict) -> bool:
    """guards 应拒绝该响应（返回 True 表示正确拒绝）。"""
    try:
        guards.check_response(resp)
        return False
    except guards.GuardError:
        return True


def _signals() -> dict:
    """派生双螺旋 verdict 与契约检查的同源真实信号。"""
    md = manifest_data()
    try:
        from app import l0
        l0_ok = hasattr(l0, "extract_public") and hasattr(l0, "classify")
    except Exception:
        l0_ok = False
    try:
        from app import l0 as _l0
        wechat_channels_classify = _l0.classify(
            "https://channels.weixin.qq.com/sns/appmsg/video?v=v2_test123@finder"
        ) == "wechat_channels"
    except Exception:
        wechat_channels_classify = False
    try:
        guards.check_response({"deliverable": {}, "meta": {"aigc_flag": False}, "cost": {"base": 0.002}})
        legal_passes = True
    except guards.GuardError:
        legal_passes = False
    # 七段报告 schema · 走唯一裁剪函数 redact_by_tier（D2 裁定·apply_depth_line 已废弃删除）
    full = {
        "s1_first_screen":     {"rating": "B", "headline": "h", "decision_tip": "tip"},
        "s3_content_breakdown": {"structure_formula": "s", "aigc_flag": False},
        "s4_competitor_matrix": {"competitors": "c"},
        "s5_recreation_paths":  {"priority": "借路", "priority_reason": "r", "aigc_flag": False},
        "s6_risk_compliance":   {"risk_level": "中", "detail": "d"},
    }
    anon = guards.redact_by_tier(full, "anon")
    free = guards.redact_by_tier(full, "free")
    paid = guards.redact_by_tier(full, "paid")
    return {
        "manifest_complete": all(md.get(k) for k in
                                 ("name", "subdomain", "industry", "angle", "pricing_tier", "solves")),
        "l0_loads": l0_ok,
        "legal_passes": legal_passes,
        "aigc_type_guard": _rejects({"deliverable": {}, "meta": {"aigc_flag": "yes"}, "cost": {"base": 0}}),
        "c4_no_passthrough": _rejects({"deliverable": {}, "meta": {"aigc_flag": True, "raw_passthrough": True},
                                       "cost": {"base": 0}}),
        "depth_anon_safe": "s4_competitor_matrix" not in anon and "locked_sections" in anon,
        "depth_free_safe": bool(free.get("s3_content_breakdown", {}).get("structure_formula"))
                           and free.get("s4_competitor_matrix", {}).get("locked") is True,
        "depth_paid_full": paid.get("s4_competitor_matrix", {}).get("competitors") == "c",
        "billing_public_free": billing.cost_public()["premium_data"] == 0.0,
        "billing_deep_paid": billing.cost_deep(True)["premium_data"] > 0,
        "billing_no_silent": billing.cost_deep(False)["premium_data"] == 0.0,
        "wechat_channels_classify": wechat_channels_classify,
    }


def _contract_checks(sig: dict) -> list[tuple[str, bool]]:
    return [
        ("manifest 三维标签完整", sig["manifest_complete"]),
        ("L0 提取器加载", sig["l0_loads"]),
        ("合法出口通过 guards", sig["legal_passes"]),
        ("aigc_flag 类型 guard", sig["aigc_type_guard"]),
        ("C4 禁直吐 guard", sig["c4_no_passthrough"]),
        ("匿名层不泄露竞品/二创", sig["depth_anon_safe"]),
        ("免费层有结构无竞品", sig["depth_free_safe"]),
        ("付费层完整", sig["depth_paid_full"]),
        ("免费档 premium=0", sig["billing_public_free"]),
        ("付费深探 premium>0", sig["billing_deep_paid"]),
        ("未付费深探不收 premium", sig["billing_no_silent"]),
        ("视频号 URL classify→wechat_channels", sig["wechat_channels_classify"]),
    ]


def _double_helix(sig: dict, contract_ready: bool) -> dict:
    """双螺旋门 · 卡1 上架工具二维判据（verdict 由真实信号派生 · 非硬编码）。"""
    # 🌀 规模递增：复用母体 L0/契约/网关/存储 + 自动化（绑定 contract_ready 机检）
    scale_ok = contract_ready
    scale = {
        "axis": "🌀 规模递增（越用越便宜）",
        "evidence": ["复用母体 L0 提取器零改动 + L1 契约 + LLM 网关 + 对象存储，不另起炉灶",
                     "一次抓取 → 结构化结论可被 AI 引用 / 批量复用，人工介入趋 0",
                     "公开层边际成本极低（premium=0）；付费深探按量计费，量大单价↓"],
        "verdict": "🟢" if scale_ok else "🔴",
    }
    # 🤝 信任复利：诚实分层(深度线) + 结论化(C4禁直吐) + 计费透明(不暗扣) + 出口合规 + 账号0接管
    trust_mech_ok = all([sig["legal_passes"], sig["aigc_type_guard"], sig["c4_no_passthrough"],
                         sig["depth_anon_safe"], sig["depth_free_safe"], sig["depth_paid_full"],
                         sig["billing_no_silent"]])
    trust = {
        "axis": "🤝 信任复利（越做越被信）",
        "evidence": ["三层深度线：匿名/免费层不泄露竞品·二创付费价值（诚实分层·不诱导）",
                     "C4 禁直吐：原料进结论出，不裸搬第三方数据",
                     "计费透明：未付费不暗扣 premium",
                     "账号 0 接管：只认母体短时 token，不存用户平台凭据",
                     "出口过 guards（类型 / 合规校验）"],
        "verdict": "🟢" if trust_mech_ok else "🔴",
    }
    if "🔴" in (scale["verdict"], trust["verdict"]):
        gate = "🔴 否决"
    elif "🟡" in (scale["verdict"], trust["verdict"]):
        gate = "🟡 整改后准入"
    else:
        gate = "🟢🟢 准入"
    return {"scale": scale, "trust": trust, "gate": gate, "rule": "短板决定·任一🔴否决·🟡整改后准入"}


@router.post("/selftest")
def selftest() -> dict:
    sig = _signals()
    checks = _contract_checks(sig)
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    contract_ready = passed == total
    helix = _double_helix(sig, contract_ready)
    admission = contract_ready and helix["gate"].startswith("🟢🟢")
    return {
        "code": 0,
        "data": {
            "ok": admission,                    # 准入 = 契约就绪 + 双螺旋 🟢🟢
            "contract_ready": contract_ready,   # 契约实现就绪（与上线准入分离）
            "passed": passed, "total": total,
            "checks": [{"name": n, "ok": o} for n, o in checks],
            "double_helix": helix,
            "c2_scorecard": {
                "note": "C2 评分卡（完成度≥80%/准确≥20pct/省力≥3×/盲评胜率≥70%）由母体侧实评，此处不自过",
            },
            "blockers": [] if admission else [f"契约检查未过: {n}" for n, ok in checks if not ok],
        },
        "msg": "准入就绪" if admission else "selftest 未全过",
    }

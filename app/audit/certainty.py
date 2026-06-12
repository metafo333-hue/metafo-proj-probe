"""信号 C · 确定性自评 · 极速版跑完决定「直接交付」or「建议升级深度版」。

speed-depth-tiering-v1.0 §三 信号C 的代码落地（该方案点名"唯一新增核心组件"）：
极速版跑完验证层（run_audit）→ 用 conclusion_label 算确定性分数：
  - 高确定（多源一致/高权威/无矛盾）→ 直接交付（标⚡极速版·已轻验）
  - 低确定（单源未证实/源冲突/AIGC嫌疑）→ 建议升级深度分析版（8闸全验+对抗证伪）

输入 = run_audit() 的返回（conclusion_label + flags）；不新依赖、零模型，纯规则可跑。
"""
from __future__ import annotations

from typing import Any

# 确定性分数各因子权重（合计上限 1.0）
_CONF = {"high": 0.40, "moderate": 0.25, "low": 0.10}
_EVID = {"strong": 0.30, "moderate": 0.20, "weak": 0.05, "contested": 0.0}
_SUFFICIENT_THRESHOLD = 0.5


def assess(audit_result: dict[str, Any]) -> dict[str, Any]:
    """确定性自评。

    Parameters
    ----------
    audit_result : run_audit() 返回（含 conclusion_label / flags）

    Returns
    -------
    {certainty_score, sufficient, uncertain_dims, recommendation}
    """
    label = audit_result.get("conclusion_label", {}) or {}
    flags = audit_result.get("flags", []) or []

    conf = str(label.get("confidence_level", "low")).lower()
    evid = str(label.get("evidence_strength", "weak")).lower()
    src_count = int(label.get("source_count", 0) or 0)
    aigc = bool(label.get("aigc_flag", False))

    score = _CONF.get(conf, 0.10) + _EVID.get(evid, 0.05) + min(src_count * 0.10, 0.20)
    if aigc:
        score -= 0.15
    if any(("矛盾" in f) or ("🔴" in f) for f in flags):
        score -= 0.20
    score = max(0.0, min(1.0, round(score, 3)))

    uncertain: list[str] = []
    if conf == "low":
        uncertain.append("置信度低")
    if evid in ("weak", "contested"):
        uncertain.append("证据弱/有冲突")
    if src_count < 2:
        uncertain.append("单源未交叉")
    if aigc:
        uncertain.append("AIGC 嫌疑")

    sufficient = score >= _SUFFICIENT_THRESHOLD and not uncertain
    return {
        "certainty_score": score,
        "sufficient": sufficient,
        "uncertain_dims": uncertain,
        "recommendation": (
            "极速版可直接交付（已轻验）" if sufficient
            else "建议升级深度分析版（8闸全验 + 对抗证伪）"
        ),
    }

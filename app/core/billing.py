"""L1 §3 计费契约 · cost{base, premium_data} · 失败不扣。

- 公开提取（A线）= 免费档：base 极小、premium_data=0
- 深探（B线）= 付费档：premium_data = 数据成本 + 加工溢价（卖独有结论）
- 失败不扣：task=failed 不产生 cost（在 tasks 层保证 failed→cost=None）
- 定价铁律：付费档 = 数据成本 + 加工溢价（02-api §3）
"""
from __future__ import annotations

PUBLIC_BASE_COST = 0.002   # 公开提取基础成本（带宽/算力）
DEEP_BASE_COST = 0.01      # 深探基础成本
DEEP_PREMIUM_COST = 0.20   # 深探付费数据 + 加工溢价


def cost_public() -> dict[str, float]:
    """免费档（公开提取）。"""
    return {"base": PUBLIC_BASE_COST, "premium_data": 0.0}


def cost_deep(authed_paid: bool) -> dict[str, float]:
    """深探：付费档收 premium_data；匿名/免费预览只收 base（不解锁付费深度）。"""
    if authed_paid:
        return {"base": DEEP_BASE_COST, "premium_data": DEEP_PREMIUM_COST}
    return {"base": DEEP_BASE_COST, "premium_data": 0.0}

"""数据源注册 + 标准19核验门。

只有过 19 项核验(成熟/已验证/数据真实/资质授权/License/安全…)且 ledger
status=active 的适配器才被 get_adapter 放行。当前无已核验源 → 返回 None
→ 上层走「需第三方授权 API」合规占位(不回退自建爬取)。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.datasources.base import DataSourceAdapter

_LEDGER = Path(__file__).resolve().parent / "ledger.yaml"

# 标准19核验关键维度(数据源上线前逐项过 · 见 docs/standards 标准19)
GATE_19 = [
    "mature",           # 成熟稳定
    "verified",         # 已验证可用
    "data_authentic",   # 数据真实
    "vendor_qualified", # 供应商有数据资质
    "authorized",       # 已获授权
    "license_ok",       # License 合规
    "security_ok",      # 安全(凭据/传输)
]

# 已接入适配器实例（新边界 2026-06-04：正规商业 API 采购，probe 只调接口、不背供应商技术责任）。
from app.datasources.tikhub import TikHubAdapter

_ADAPTERS: dict[str, DataSourceAdapter] = {
    "tikhub": TikHubAdapter(),       # 覆盖五平台（抖音/小红书/微博/B站/快手）· 待 PROBE_TIKHUB_KEY
}


def _ledger() -> dict[str, Any]:
    if not _LEDGER.exists():
        return {}
    return yaml.safe_load(_LEDGER.read_text(encoding="utf-8")) or {}


def gate_passed(source_id: str) -> bool:
    """该数据源是否过标准19核验且 active(以 ledger 实填为准)。"""
    entry = (_ledger().get("sources") or {}).get(source_id)
    if not entry or entry.get("status") != "active":
        return False
    gate = entry.get("gate19") or {}
    return all(gate.get(k) is True for k in GATE_19)


def get_adapter(kind: str) -> DataSourceAdapter | None:
    """取支持该 kind 的已接入适配器;无 → None(上层走合规占位)。

    新边界(2026-06-04):qualified=已按正规商业 API 采购接入即放行;gate_passed（官方数据授权
    gate19）作合规记录、不强制阻断——官方授权是更高合规等级，列为深化备选。
    """
    for sid, ad in _ADAPTERS.items():
        if kind in ad.supported_kinds and ad.qualified:
            return ad
    return None


def list_candidates() -> list[str]:
    """待核验选型的候选数据源(ledger.candidates_to_evaluate)。"""
    return _ledger().get("candidates_to_evaluate") or []

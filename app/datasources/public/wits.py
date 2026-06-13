"""World Bank WITS · 关税与贸易统计 API · 无需 key · 免费 · CC BY 4.0。

WITS = World Integrated Trade Solution，整合 UNCTAD TRAINS（关税）+ UN Comtrade（贸易流）。
probe 用途：跨境外贸赛道关税成本核算 —— 这是 probe 此前**完全缺失**的关税数据能力（D14）。

端点（TradeStats-Tariff · SDMX-JSON · 实测 200 真数据 2026-06-13）：
  GET https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-tariff/
      reporter/{rep}/year/{yr}/partner/{par}/product/{prod}/indicator/{ind}?format=JSON
  reporter/partner: ISO3 小写（usa/chn/...）或 wld（世界）
  indicator: AHS-SMPL-AVRG（实施简单平均%）/ MFN-SMPL-AVRG（最惠国简单平均%）/
             AHS-WGHTD-AVRG（加权平均）等
合规：WITS Open Data，CC BY 4.0，官方明确允许商业使用。须带合理 User-Agent。
注意：WITS 服务较慢，timeout 设 60s；失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "wits",
    "domain": ["D14", "D11"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["tariff", "trade"],
}

_API_BASE = "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-tariff"
_TIMEOUT = 60
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def _series_dim_values(structure: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """取 series 各维度的取值列表（用于把 "0:0:0:0:0" 索引映射回真名）。"""
    dims = (structure.get("dimensions") or {}).get("series") or []
    return [dm.get("values") or [] for dm in dims]


def tariff(
    reporter: str,
    year: int,
    partner: str = "wld",
    product: str = "all",
    indicator: str = "AHS-SMPL-AVRG",
) -> list[dict[str, Any]]:
    """查询某经济体某年的关税水平（按产品组拆分）。

    Args:
        reporter:  申报经济体 ISO3 小写，如 "chn" / "usa" / "jpn"
        year:      年份，如 2019
        partner:   伙伴方，默认 "wld"（世界），或 ISO3 小写
        product:   "all"（全部产品组，约 29 组）或 HS 产品码
        indicator: 关税指标 —— "AHS-SMPL-AVRG"（实施关税简单平均%）/
                   "MFN-SMPL-AVRG"（最惠国关税简单平均%）/ "AHS-WGHTD-AVRG"（加权平均）

    Returns:
        [{"reporter", "reporter_name", "partner", "product", "product_name",
          "indicator", "indicator_name", "year", "value", "source_id"}] 或空列表。
    """
    url = (
        f"{_API_BASE}/reporter/{reporter}/year/{year}"
        f"/partner/{partner}/product/{product}/indicator/{indicator}"
    )
    try:
        r = httpx.get(url, params={"format": "JSON"}, headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception:
        return []

    try:
        structure = data.get("structure") or {}
        dim_vals = _series_dim_values(structure)
        # series 维度顺序：FREQ:REPORTER:PARTNER:PRODUCTCODE:INDICATOR
        obs_dims = (structure.get("dimensions") or {}).get("observation") or []
        time_vals = obs_dims[0].get("values") if obs_dims else []

        datasets = data.get("dataSets") or []
        if not datasets:
            return []
        series = datasets[0].get("series") or {}

        out: list[dict[str, Any]] = []
        for skey, sval in series.items():
            idx = [int(p) for p in skey.split(":")]

            def _name(dim: int, default: str = "") -> tuple[str, str]:
                vals = dim_vals[dim] if dim < len(dim_vals) else []
                pos = idx[dim] if dim < len(idx) else -1
                if 0 <= pos < len(vals):
                    return vals[pos].get("id", default), vals[pos].get("name", "")
                return default, ""

            rep_id, rep_name = _name(1)
            par_id, _ = _name(2)
            prod_id, prod_name = _name(3)
            ind_id, ind_name = _name(4)

            for tkey, obs in (sval.get("observations") or {}).items():
                tpos = int(tkey)
                yr = time_vals[tpos].get("id", str(year)) if tpos < len(time_vals) else str(year)
                value = obs[0] if obs else None
                out.append({
                    "reporter": rep_id,
                    "reporter_name": rep_name,
                    "partner": par_id,
                    "product": prod_id,
                    "product_name": prod_name,
                    "indicator": ind_id,
                    "indicator_name": ind_name,
                    "year": yr,
                    "value": value,
                    "source_id": META["id"],
                })
        return out
    except Exception:
        return []

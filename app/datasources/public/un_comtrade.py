"""UN Comtrade · 联合国国际贸易统计 · keyless preview 端点 · 免费 · CC BY 4.0。

UN Comtrade = 联合国统计署官方国际贸易数据库，200+ 国双边货物贸易流。
probe 用途：跨境外贸赛道双边贸易流（出口/进口/伙伴国/HS 商品），
是 WITS 之外贸易流的第二独立源 —— 满足验证层闸2「一论断 ≥2 独立源印证」。

端点（public preview · 无需 key · 实测 200 真数据 2026-06-13）：
  GET https://comtradeapi.un.org/public/v1/preview/{type}/{freq}/{cl}
      ?reporterCode={M49}&period={year}&flowCode=X,M&cmdCode=TOTAL&partnerCode={M49}
  type=C(货物) freq=A(年)/M(月) cl=HS
  reporterCode/partnerCode: UN M49 数字码（156=中国 842=美国 0=世界）
  flowCode: X=出口 M=进口（可逗号组合）
合规：UN Comtrade 官方开放数据，CC BY 4.0，允许商业使用。
限制：preview 端点免 key 但单次最多 500 条；超出需注册 subscription key（升级 P1）。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "un_comtrade",
    "domain": ["D11", "D14"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["trade", "customs"],
}

_API_BASE = "https://comtradeapi.un.org/public/v1/preview"
_TIMEOUT = 40
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """preview 端点无需 key，恒返回 True。"""
    return True


def trade(
    reporter: int | str,
    year: int | str,
    flow: str = "X,M",
    partner: int | str | None = None,
    cmd: str = "TOTAL",
    freq: str = "A",
) -> list[dict[str, Any]]:
    """查询某经济体某年的双边货物贸易流。

    Args:
        reporter: 申报国 UN M49 数字码，如 156(中国) / 842(美国) / 392(日本)
        year:     年份，如 2022（freq=M 时用 "202201" 月份格式）
        flow:     "X"=出口 / "M"=进口 / "X,M"=两者
        partner:  伙伴国 M49 码；None=全部伙伴（含 0=世界汇总）
        cmd:      HS 商品码，"TOTAL"=全部商品汇总，或具体 HS 码如 "85"
        freq:     "A"=年度 / "M"=月度

    Returns:
        [{"reporter", "partner", "partner_desc", "flow", "cmd", "cmd_desc",
          "year", "value_usd", "net_weight", "qty", "source_id"}] 或空列表。
        注：preview 单次最多 500 条；value_usd = primaryValue（美元）。
    """
    params: dict[str, str] = {
        "reporterCode": str(reporter),
        "period": str(year),
        "flowCode": flow,
        "cmdCode": cmd,
    }
    if partner is not None:
        params["partnerCode"] = str(partner)
    url = f"{_API_BASE}/C/{freq}/HS"
    try:
        r = httpx.get(url, params=params, headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception:
        return []

    try:
        out: list[dict[str, Any]] = []
        for rec in data.get("data") or []:
            out.append({
                "reporter": rec.get("reporterCode"),
                "partner": rec.get("partnerCode"),
                "partner_desc": rec.get("partnerDesc"),
                "flow": rec.get("flowCode"),
                "cmd": rec.get("cmdCode"),
                "cmd_desc": rec.get("cmdDesc"),
                "year": rec.get("refYear"),
                "value_usd": rec.get("primaryValue"),
                "net_weight": rec.get("netWgt"),
                "qty": rec.get("qty"),
                "source_id": META["id"],
            })
        return out
    except Exception:
        return []

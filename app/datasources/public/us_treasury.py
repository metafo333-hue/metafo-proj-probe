"""US Treasury · 美国国债收益率 & 财政数据 API · 无需 key · 公有领域。

端点（Fiscal Data API）：
  avg_interest  GET https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates
  debt_to_penny GET https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_to_penny
  yield_curve   GET https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/{month}/...
合规：美国联邦政府数据，公有领域（U.S. Government Works），fiscaldata.treasury.gov 官方 API。
须带合理 User-Agent。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "us_treasury",
    "domain": ["D13", "D14"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["rate", "yield", "debt"],
}

_FISCAL_BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def avg_interest_rates(
    security_type: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """取美国国债平均利率（各类型证券）。

    Args:
        security_type: 证券类型过滤，如 "Treasury Bills" / "Treasury Notes"
                       / "Treasury Bonds" / "Total Marketable"；空 = 不过滤
        limit:         最多返回条数（1-100）

    Returns:
        [{"record_date", "security_type", "security_desc", "avg_interest_rate_amt", "source_id"}]
        或空列表。
    """
    url = f"{_FISCAL_BASE}/v2/accounting/od/avg_interest_rates"
    params: dict[str, Any] = {
        "sort": "-record_date",
        "page[size]": str(max(1, min(limit, 100))),
        "format": "json",
    }
    if security_type:
        params["filter"] = f"security_type_desc:eq:{security_type}"
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        records = (data.get("data") or [])
        results: list[dict[str, Any]] = []
        for rec in records:
            results.append({
                "record_date": rec.get("record_date", ""),
                "security_type": rec.get("security_type_desc", ""),
                "security_desc": rec.get("security_desc", ""),
                "avg_interest_rate_amt": rec.get("avg_interest_rate_amt"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def debt_to_penny(limit: int = 5) -> list[dict[str, Any]]:
    """取美国联邦总债务（精确到美分）最近数据。

    Args:
        limit: 最多返回条数

    Returns:
        [{"record_date", "debt_held_public_amt", "intragov_holdings_amt",
          "tot_pub_debt_out_amt", "source_id"}] 或空列表。
    """
    url = f"{_FISCAL_BASE}/v2/accounting/od/debt_to_penny"
    params: dict[str, Any] = {
        "sort": "-record_date",
        "page[size]": str(max(1, min(limit, 50))),
        "format": "json",
    }
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        records = data.get("data") or []
        results: list[dict[str, Any]] = []
        for rec in records:
            results.append({
                "record_date": rec.get("record_date", ""),
                "debt_held_public_amt": rec.get("debt_held_public_amt"),
                "intragov_holdings_amt": rec.get("intragov_holdings_amt"),
                "tot_pub_debt_out_amt": rec.get("tot_pub_debt_out_amt"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def exchange_rates(currency: str = "", limit: int = 10) -> list[dict[str, Any]]:
    """取美国财政部公布的外汇汇率（季度更新）。

    Args:
        currency: 货币过滤，如 "Euro" / "China-Renminbi"；空 = 不过滤
        limit:    最多返回条数

    Returns:
        [{"record_date", "country", "currency", "exchange_rate", "effective_date", "source_id"}]
        或空列表。
    """
    url = f"{_FISCAL_BASE}/v1/accounting/od/rates_of_exchange"
    params: dict[str, Any] = {
        "sort": "-record_date",
        "page[size]": str(max(1, min(limit, 100))),
        "format": "json",
    }
    if currency:
        params["filter"] = f"currency:eq:{currency}"
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        records = data.get("data") or []
        results: list[dict[str, Any]] = []
        for rec in records:
            results.append({
                "record_date": rec.get("record_date", ""),
                "country": rec.get("country", ""),
                "currency": rec.get("currency", ""),
                "exchange_rate": rec.get("exchange_rate"),
                "effective_date": rec.get("effective_date", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []

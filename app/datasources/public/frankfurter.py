"""Frankfurter · ECB 实时/历史汇率 API · 无需 key · 免费 · 明示允许商用。

端点：
  latest  GET https://api.frankfurter.app/latest?from=USD
  convert GET https://api.frankfurter.app/latest?from=USD&to=CNY&amount=100
  history GET https://api.frankfurter.app/{date}?from=USD
  series  GET https://api.frankfurter.app/{start}..{end}?from=USD&to=CNY
合规：https://www.frankfurter.app/ 明示"free to use for any purpose"，数据来源 ECB，公共领域。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "frankfurter",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["fx", "rate"],
}

_API_BASE = "https://api.frankfurter.app"
_TIMEOUT = 15
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def latest(
    base: str = "USD",
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """取最新 ECB 汇率（工作日每日更新，约 16:00 CET）。

    Args:
        base:    基准货币（ISO-4217，如 "USD" / "EUR" / "CNY"）
        targets: 目标货币列表，如 ["CNY", "JPY", "EUR"]；空列表 = 取全部

    Returns:
        {"base", "date", "rates": {currency: rate}, "source_id"} 或空 dict。
    """
    params: dict[str, str] = {"from": base}
    if targets:
        params["to"] = ",".join(targets)
    try:
        r = httpx.get(f"{_API_BASE}/latest", params=params, headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "base": data.get("base", base),
            "date": data.get("date", ""),
            "rates": data.get("rates", {}),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict[str, Any]:
    """货币换算（当日汇率）。

    Args:
        amount:        金额
        from_currency: 来源货币，如 "USD"
        to_currency:   目标货币，如 "CNY"

    Returns:
        {"from", "to", "amount", "result", "date", "rate", "source_id"} 或空 dict。
    """
    params = {
        "from": from_currency,
        "to": to_currency,
        "amount": str(amount),
    }
    try:
        r = httpx.get(f"{_API_BASE}/latest", params=params, headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        rates = data.get("rates", {})
        result_rate = rates.get(to_currency)
        return {
            "from": from_currency,
            "to": to_currency,
            "amount": amount,
            "result": result_rate,
            "date": data.get("date", ""),
            "rate": result_rate / amount if (result_rate and amount) else None,
            "source_id": META["id"],
        }
    except Exception:
        return {}


def historical(
    date: str,
    base: str = "USD",
    targets: list[str] | None = None,
) -> dict[str, Any]:
    """取历史某日汇率。

    Args:
        date:    日期字符串，格式 "YYYY-MM-DD"，最早 1999-01-04
        base:    基准货币
        targets: 目标货币列表，空 = 取全部

    Returns:
        {"base", "date", "rates", "source_id"} 或空 dict。
    """
    params: dict[str, str] = {"from": base}
    if targets:
        params["to"] = ",".join(targets)
    try:
        r = httpx.get(f"{_API_BASE}/{date}", params=params, headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "base": data.get("base", base),
            "date": data.get("date", date),
            "rates": data.get("rates", {}),
            "source_id": META["id"],
        }
    except Exception:
        return {}

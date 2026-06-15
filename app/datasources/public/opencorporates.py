"""OpenCorporates API · 可选 OPENCORPORATES_TOKEN env · 免费（有限额度）· ODbl。

端点：
  search  https://api.opencorporates.com/v0.4/companies/search?q=...
合规：OpenCorporates 官方 API，无 token 时有限频调用，有 token 更高限额。
失败返回空，不抛出。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "opencorporates",
    "domain": ["D11", "D4"],
    "access_type": "free_with_key",
    "method": ["O"],
    "kinds": ["company", "search"],
    "needs_key": True,
    "key_env": "OPENCORPORATES_TOKEN",
}

_API_BASE = "https://api.opencorporates.com/v0.4"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def _get_token() -> str:
    """从环境变量读取 token，未配置返回空字符串。"""
    return os.environ.get("OPENCORPORATES_TOKEN", "").strip()


def search_company(
    name: str,
    jurisdiction_code: str = "",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """按公司名搜索 OpenCorporates 注册信息。

    Args:
        name:              公司名称关键词
        jurisdiction_code: 限定注册地，如 "us_ca" / "gb" / "cn"，空字符串不限
        max_results:       返回条数，最大 100

    Returns:
        列表，每条包含 {name, company_number, jurisdiction_code, status, url, source_id}。
        失败返回空列表。
    """
    max_results = min(max(1, max_results), 100)
    params: dict[str, Any] = {
        "q": name,
        "per_page": str(max_results),
        "format": "json",
    }
    token = _get_token()
    if token:
        params["api_token"] = token
    if jurisdiction_code:
        params["jurisdiction_code"] = jurisdiction_code

    try:
        r = httpx.get(
            f"{_API_BASE}/companies/search",
            params=params,
            timeout=_TIMEOUT,
            headers=_HEADERS,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        companies = (
            (data.get("results") or {}).get("companies") or []
        )
        results: list[dict[str, Any]] = []
        for item in companies:
            c = item.get("company") or {}
            results.append({
                "name": c.get("name", ""),
                "company_number": c.get("company_number", ""),
                "jurisdiction_code": c.get("jurisdiction_code", ""),
                "status": c.get("current_status", ""),
                "incorporation_date": c.get("incorporation_date", ""),
                "company_type": c.get("company_type", ""),
                "url": c.get("opencorporates_url", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def get_company(
    jurisdiction_code: str,
    company_number: str,
) -> dict[str, Any]:
    """取单一公司详情。

    Args:
        jurisdiction_code: 注册地代码，如 "us_de"
        company_number:    公司注册号

    Returns:
        公司详情 dict，失败返回空字典。
    """
    params: dict[str, str] = {}
    token = _get_token()
    if token:
        params["api_token"] = token
    try:
        r = httpx.get(
            f"{_API_BASE}/companies/{jurisdiction_code}/{company_number}",
            params=params,
            timeout=_TIMEOUT,
            headers=_HEADERS,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        c = (data.get("results") or {}).get("company") or {}
        return {
            "name": c.get("name", ""),
            "company_number": c.get("company_number", ""),
            "jurisdiction_code": c.get("jurisdiction_code", ""),
            "status": c.get("current_status", ""),
            "incorporation_date": c.get("incorporation_date", ""),
            "company_type": c.get("company_type", ""),
            "registered_address": c.get("registered_address_in_full", ""),
            "url": c.get("opencorporates_url", ""),
            "source_id": META["id"],
        }
    except Exception:
        return {}

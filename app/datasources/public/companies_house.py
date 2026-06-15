"""UK Companies House · 英国官方企业注册 REST API · 需 COMPANIES_HOUSE_API_KEY · 免费。

英国公司全量注册局官方 API：公司注册信息/状态、董事、PSC(实控人)、申报文件。
probe 用途：跨境/法风控赛道海外企业背调 —— 是 GLEIF 之外海外企业的第二独立源
（满足验证层闸2「≥2 独立源印证」），数据近实时（申报即更新）。

端点（HTTP Basic 认证：API key 作用户名·密码空 · 实测 200 真数据 2026-06-13）：
  search   GET https://api.company-information.service.gov.uk/search/companies?q={q}
  profile  GET https://api.company-information.service.gov.uk/company/{number}
  officers GET https://api.company-information.service.gov.uk/company/{number}/officers
合规：Open Government Licence v3.0，官方明确允许商业使用。
未配置 COMPANIES_HOUSE_API_KEY 时所有函数返回空，不报错。失败返回空，不抛出。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "companies_house",
    "domain": ["D11"],
    "access_type": "free_with_key",
    "method": ["O"],
    "kinds": ["company", "officers", "registry"],
    "needs_key": True,
    "key_env": "COMPANIES_HOUSE_API_KEY",
}

_API_BASE = "https://api.company-information.service.gov.uk"
_TIMEOUT = 20
_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
}


def _get_key() -> str:
    """从环境变量读取 API key，未配置返回空字符串。"""
    return os.environ.get("COMPANIES_HOUSE_API_KEY", "").strip()


def configured() -> bool:
    """是否已配置 API key。"""
    return bool(_get_key())


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    key = _get_key()
    if not key:
        return {}
    try:
        r = httpx.get(f"{_API_BASE}{path}", params=params or {}, headers=_HEADERS,
                      auth=(key, ""), timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        return r.json()
    except Exception:
        return {}


def search_companies(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """按名称/编号搜索英国公司。

    Returns:
        [{"company_number", "title", "company_status", "company_type",
          "address_snippet", "date_of_creation", "source_id"}] 或空列表。
    """
    data = _get("/search/companies", {"q": query, "items_per_page": limit})
    out: list[dict[str, Any]] = []
    for it in data.get("items", []) or []:
        out.append({
            "company_number": it.get("company_number"),
            "title": it.get("title"),
            "company_status": it.get("company_status"),
            "company_type": it.get("company_type"),
            "address_snippet": it.get("address_snippet"),
            "date_of_creation": it.get("date_of_creation"),
            "source_id": META["id"],
        })
    return out


def company_profile(company_number: str) -> dict[str, Any]:
    """取某公司完整注册档案。

    Returns:
        {"company_number", "company_name", "company_status", "type",
         "date_of_creation", "registered_office_address", "sic_codes",
         "accounts", "source_id"} 或空 dict。
    """
    data = _get(f"/company/{company_number}")
    if not data:
        return {}
    return {
        "company_number": data.get("company_number"),
        "company_name": data.get("company_name"),
        "company_status": data.get("company_status"),
        "type": data.get("type"),
        "date_of_creation": data.get("date_of_creation"),
        "registered_office_address": data.get("registered_office_address"),
        "sic_codes": data.get("sic_codes"),
        "accounts": data.get("accounts"),
        "source_id": META["id"],
    }


def officers(company_number: str, limit: int = 35) -> list[dict[str, Any]]:
    """取某公司董事/管理人员列表。

    Returns:
        [{"name", "officer_role", "appointed_on", "resigned_on",
          "nationality", "occupation", "source_id"}] 或空列表。
    """
    data = _get(f"/company/{company_number}/officers", {"items_per_page": limit})
    out: list[dict[str, Any]] = []
    for it in data.get("items", []) or []:
        out.append({
            "name": it.get("name"),
            "officer_role": it.get("officer_role"),
            "appointed_on": it.get("appointed_on"),
            "resigned_on": it.get("resigned_on"),
            "nationality": it.get("nationality"),
            "occupation": it.get("occupation"),
            "source_id": META["id"],
        })
    return out

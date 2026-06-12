"""World Bank · 宏观经济指标 API · 无需 key · 免费 · 公有领域。

端点：
  country_indicator  GET https://api.worldbank.org/v2/country/{cc}/indicator/{ind}?format=json
  indicator_search   GET https://api.worldbank.org/v2/indicator?format=json&source=2&per_page=50
合规：World Bank Open Data API，CC BY 4.0，官方明确允许商业使用。
须带合理 User-Agent（礼貌实践）。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "worldbank",
    "domain": ["D14", "D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["macro", "indicator"],
}

_API_BASE = "https://api.worldbank.org/v2"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def country_indicator(
    country_code: str,
    indicator: str,
    mrv: int = 5,
) -> list[dict[str, Any]]:
    """查询某国家的宏观指标时间序列数据。

    Args:
        country_code: ISO-2 国家码，如 "CN" / "US" / "JP"，或 "all" 查全球
        indicator:    世行指标 ID，如 "NY.GDP.MKTP.CD"（GDP）/ "FP.CPI.TOTL"（CPI）
                      / "SP.POP.TOTL"（人口）/ "BX.KLT.DINV.CD.WD"（FDI）
        mrv:          最近 N 期数据（1-50）

    Returns:
        [{"country_code", "country_name", "indicator_id", "indicator_name",
          "year", "value", "source_id"}] 或空列表。
    """
    url = f"{_API_BASE}/country/{country_code}/indicator/{indicator}"
    params: dict[str, str] = {
        "format": "json",
        "mrv": str(max(1, min(mrv, 50))),
        "per_page": "50",
    }
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        # World Bank 返回 [meta_dict, data_list]
        if not isinstance(data, list) or len(data) < 2:
            return []
        records = data[1]
        if not isinstance(records, list):
            return []
        results: list[dict[str, Any]] = []
        for rec in records:
            if rec is None or not isinstance(rec, dict):
                continue
            results.append(_normalize(rec))
        return results
    except Exception:
        return []


def indicators_search(
    query: str = "",
    topic_id: int = 0,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """搜索世行指标定义（按关键词或主题）。

    Args:
        query:    指标名关键词（大小写不敏感）
        topic_id: 主题 ID（0 = 不限主题；常见主题：3=经济 / 6=科技 / 8=环境）
        per_page: 返回条数（1-100）

    Returns:
        [{"id", "name", "unit", "source_note", "source_id"}] 或空列表。
    """
    url = f"{_API_BASE}/indicator"
    params: dict[str, str] = {
        "format": "json",
        "per_page": str(max(1, min(per_page, 100))),
    }
    if topic_id:
        url = f"{_API_BASE}/topic/{topic_id}/indicator"
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list) or len(data) < 2:
            return []
        items = data[1] or []
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "")
            # 若有 query 关键词则过滤
            if query and query.lower() not in name.lower():
                continue
            results.append({
                "id": item.get("id", ""),
                "name": name[:200],
                "unit": item.get("unit", ""),
                "source_note": (item.get("sourceNote") or "")[:300],
                "source_id": META["id"],
            })
        return results[:per_page]
    except Exception:
        return []


def _normalize(rec: dict[str, Any]) -> dict[str, Any]:
    country = rec.get("country") or {}
    indicator = rec.get("indicator") or {}
    return {
        "country_code": rec.get("countryiso3code", ""),
        "country_name": country.get("value", ""),
        "indicator_id": indicator.get("id", ""),
        "indicator_name": (indicator.get("value") or "")[:200],
        "year": rec.get("date", ""),
        "value": rec.get("value"),
        "decimal": rec.get("decimal"),
        "source_id": META["id"],
    }

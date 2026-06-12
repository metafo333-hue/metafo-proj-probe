"""Eurostat · 欧盟统计局官方数据 API · 无需 key · 免费 · 公有领域。

端点：
  dataset        GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset}
  search         GET https://ec.europa.eu/eurostat/api/dissemination/catalogue/1.0/eurobase/tables/table
合规：Eurostat 官方 REST API，数据 CC BY 4.0，商业使用合法。
失败返回空，不抛出。

常用数据集（dataset code）：
  nama_10_gdp      - GDP 国民账户
  prc_hicp_manr    - 欧元区 HICP 通胀（月）
  une_rt_m         - 失业率（月）
  irt_st_m         - 短期利率
  bop_c6_q         - 国际收支（季）
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "eurostat",
    "domain": ["D14", "D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["macro", "indicator", "rate"],
}

_API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
_CAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/catalogue/1.0"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def get_dataset(
    dataset: str,
    filters: dict[str, str] | None = None,
    lang: str = "EN",
    since_time_period: str = "",
) -> dict[str, Any]:
    """获取 Eurostat 数据集（JSON-stat 格式）。

    Args:
        dataset:          数据集代码，如 "prc_hicp_manr"
        filters:          维度过滤，如 {"geo": "DE", "coicop": "CP00"}
        lang:             语言 "EN" / "DE" / "FR"
        since_time_period: 起始时期，如 "2020-01"（可选）

    Returns:
        {"id", "size", "dimension", "value", "source_id"} 原始 JSON-stat 结构或空 dict。
    """
    url = f"{_API_BASE}/{dataset}"
    params: dict[str, str] = {
        "format": "JSON",
        "lang": lang,
    }
    if since_time_period:
        params["sinceTimePeriod"] = since_time_period
    if filters:
        params.update(filters)
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        data = r.json()
        data["source_id"] = META["id"]
        return data
    except Exception:
        return {}


def get_observations(
    dataset: str,
    filters: dict[str, str] | None = None,
    since_time_period: str = "",
    max_obs: int = 200,
) -> list[dict[str, Any]]:
    """获取 Eurostat 数据集并展平为观测值列表。

    Args:
        dataset:          数据集代码
        filters:          维度过滤，如 {"geo": "DE", "unit": "RCH_A_AVG"}
        since_time_period: 起始时期，如 "2020"
        max_obs:          最多返回条数（防大数据集）

    Returns:
        [{"time", "geo", "unit", "value", "dataset", "source_id"}] 或空列表。
    """
    raw = get_dataset(dataset, filters, since_time_period=since_time_period)
    if not raw:
        return []
    try:
        dims = raw.get("id", [])            # 维度列表，如 ["freq","unit","geo","time"]
        sizes = raw.get("size", [])
        dimension = raw.get("dimension", {})
        values = raw.get("value", {})

        if not dims or not values:
            return []

        # 构建每个维度的 label 映射（index→label）
        dim_labels: list[list[str]] = []
        for d in dims:
            cat = dimension.get(d, {}).get("category", {})
            index_map = cat.get("index", {})
            label_map = cat.get("label", {})
            # index_map: {label_key: position_int}
            labels_by_pos: list[str] = [""] * (len(index_map) or 1)
            for k, pos in index_map.items():
                labels_by_pos[int(pos)] = label_map.get(k, k)
            dim_labels.append(labels_by_pos)

        # 展平 values（flat index → value）
        results: list[dict[str, Any]] = []
        for flat_idx_str, val in values.items():
            flat_idx = int(flat_idx_str)
            # 反向解码 multi-dim index
            indices: list[int] = []
            remainder = flat_idx
            for sz in reversed(sizes):
                indices.insert(0, remainder % sz)
                remainder //= sz
            obs: dict[str, Any] = {"dataset": dataset, "source_id": META["id"]}
            for i, (d, idx) in enumerate(zip(dims, indices)):
                labels = dim_labels[i]
                obs[d] = labels[idx] if idx < len(labels) else str(idx)
            obs["value"] = val
            results.append(obs)
            if len(results) >= max_obs:
                break
        return results
    except Exception:
        return []


def search_tables(query: str, lang: str = "EN", max_results: int = 20) -> list[dict[str, Any]]:
    """在 Eurostat 目录中搜索数据集。

    Args:
        query:       搜索关键词，如 "inflation" / "GDP"
        lang:        界面语言
        max_results: 最多返回条数

    Returns:
        [{"code", "title", "source_id"}] 或空列表。
    """
    url = f"{_CAT_BASE}/eurobase/tables/table"
    params = {
        "lang": lang,
        "type": "dataset",
        "searchText": query,
        "pageSize": str(max_results),
        "pageNum": "1",
    }
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("results", {}).get("items", [])
        if not isinstance(items, list):
            return []
        results: list[dict[str, Any]] = []
        for item in items[:max_results]:
            if not isinstance(item, dict):
                continue
            results.append({
                "code": item.get("code", ""),
                "title": item.get("title", "")[:200],
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []

"""DBnomics · 宏观经济数据聚合平台 API · 无需 key · 免费 · 开放数据。

端点：
  providers  GET https://api.db.nomics.world/v22/providers?format=json&limit=100
  datasets   GET https://api.db.nomics.world/v22/datasets/{provider_code}?format=json
  series     GET https://api.db.nomics.world/v22/series/{provider_code}/{dataset_code}/{series_code}?format=json
  search     GET https://api.db.nomics.world/v22/series?q={query}&format=json&limit=20

常用 provider：
  IMF   — 国际货币基金组织
  ECB   — 欧洲中央银行
  WB    — World Bank（世界银行）
  OECD  — 经合组织
  Eurostat — 欧盟统计局
  INSEE — 法国国家统计局
  FRED  — 美联储经济数据（圣路易斯联储）

合规：DBnomics 官方公开 API（https://api.db.nomics.world/v22/），无需注册，免费。
数据版权归各原始来源机构。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "dbnomics",
    "domain": ["D14"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["macro", "indicator", "time_series"],
}

_API_BASE = "https://api.db.nomics.world/v22"
_TIMEOUT = 25
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    query: str,
    provider_code: str = "",
    dataset_code: str = "",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """搜索 DBnomics provider/dataset 内的时间序列（精确路径搜索，避免全局超时）。

    推荐用法：指定 provider_code + dataset_code 缩小范围，如 provider_code="IMF", dataset_code="IFS"。
    若只给 query 且不指定 provider/dataset，会较慢（全局搜索数据量大）。

    Args:
        query:         关键词（provider+dataset 内过滤，空=取全部）
        provider_code: 数据提供方代码，如 "IMF" / "ECB" / "WB" / "FRED"
        dataset_code:  数据集代码，如 "IFS" / "WDI" / "DOT"
        limit:         返回条数（1-100）

    Returns:
        [{"series_id", "name", "provider", "dataset", "frequency",
          "last_updated", "source_id"}] 或空列表。
    """
    if not provider_code or not dataset_code:
        # 无路径时无法安全全局搜索（超时），返回空并给出提示
        return []
    try:
        r = httpx.get(
            f"{_API_BASE}/series/{provider_code}/{dataset_code}",
            params={"q": query, "limit": max(1, min(limit, 100))},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        series_list = data.get("series", {}).get("docs", [])
        if not isinstance(series_list, list):
            return []
        results: list[dict[str, Any]] = []
        for s in series_list:
            results.append({
                "series_id": s.get("series_id", ""),
                "name": (s.get("series_name") or "")[:200],
                "provider": s.get("provider_code", ""),
                "dataset": s.get("dataset_code", ""),
                "frequency": s.get("@frequency", ""),
                "last_updated": s.get("indexed_at", "")[:10],
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def series(
    provider_code: str,
    dataset_code: str,
    series_code: str,
    observations: bool = True,
    limit: int = 60,
) -> dict[str, Any]:
    """拉取单条时间序列及观测值。

    Args:
        provider_code: 数据提供方代码，如 "IMF" / "ECB" / "WB" / "FRED"
        dataset_code:  数据集代码，如 "IFS" / "WEO" / "WDI"
        series_code:   序列代码，如 "CN.NGDP_RPCH"
        observations:  是否拉取观测值（True）或只取元数据（False）
        limit:         最近 N 期观测值

    Returns:
        {"series_id", "name", "provider", "dataset", "frequency",
         "unit", "observations": [{"period", "value"}], "source_id"} 或空 dict。
    """
    params: dict[str, Any] = {
        "observations": 1 if observations else 0,
        "limit": max(1, min(limit, 1000)),
    }
    try:
        url = f"{_API_BASE}/series/{provider_code}/{dataset_code}/{series_code}"
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        series_data = data.get("series", {}).get("docs", [{}])
        if not series_data:
            return {}
        s = series_data[0]
        obs_periods = s.get("period", [])
        obs_values = s.get("value", [])
        obs_list = [
            {"period": p, "value": v}
            for p, v in zip(obs_periods, obs_values)
        ]
        # 只取最近 limit 期
        if len(obs_list) > limit:
            obs_list = obs_list[-limit:]
        return {
            "series_id": s.get("series_id", f"{provider_code}/{dataset_code}/{series_code}"),
            "name": (s.get("series_name") or s.get("name") or "")[:200],
            "provider": provider_code,
            "dataset": dataset_code,
            "frequency": s.get("@frequency", ""),
            "unit": (s.get("unit") or "")[:100],
            "observations": obs_list,
            "source_id": META["id"],
        }
    except Exception:
        return {}


def providers(limit: int = 50) -> list[dict[str, Any]]:
    """列出 DBnomics 数据提供方。

    Returns:
        [{"code", "name", "region", "datasets_count", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/providers",
            params={"limit": min(limit, 200)},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        provider_list = data.get("providers", {}).get("docs", [])
        return [
            {
                "code": p.get("code", ""),
                "name": (p.get("name") or "")[:200],
                "region": (p.get("region") or "")[:100],
                "datasets_count": p.get("datasets_count", 0),
                "source_id": META["id"],
            }
            for p in provider_list
            if isinstance(p, dict)
        ]
    except Exception:
        return []

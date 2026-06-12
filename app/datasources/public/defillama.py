"""DeFi Llama · DeFi TVL 与链上数据 · 无需 key · 完全免费 · 开放数据。

端点：
  protocols  GET https://api.llama.fi/protocols         — 所有协议 TVL 列表
  protocol   GET https://api.llama.fi/protocol/{slug}   — 单协议历史 TVL
  chains     GET https://api.llama.fi/v2/chains         — 各链 TVL 汇总
  tvl        GET https://api.llama.fi/tvl/{protocol}    — 单协议当前 TVL（数字）
合规：DeFi Llama 官方公开 API，无 ToS 限制，完全免费，开源项目数据。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "defillama",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["defi", "tvl", "chain"],
}

_API_BASE = "https://api.llama.fi"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def protocols(top_n: int = 50) -> list[dict[str, Any]]:
    """取 DeFi 协议列表（按 TVL 降序）。

    Args:
        top_n: 取前 N 条（1-500）

    Returns:
        [{"name", "slug", "tvl", "chain", "category", "change_1d", "change_7d", "source_id"}]
        或空列表。
    """
    try:
        r = httpx.get(f"{_API_BASE}/protocols", headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        # 已按 TVL 降序
        results: list[dict[str, Any]] = []
        for item in data[:max(1, min(top_n, 500))]:
            results.append(_normalize_protocol(item))
        return results
    except Exception:
        return []


def protocol_detail(slug: str) -> dict[str, Any]:
    """取单协议完整历史 TVL 数据。

    Args:
        slug: 协议 slug，如 "aave" / "uniswap" / "makerdao"

    Returns:
        {"name", "slug", "tvl_current", "tvl_history": [{date, totalLiquidityUSD}],
         "chains", "category", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(f"{_API_BASE}/protocol/{slug}", headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        tvl_history = data.get("tvl") or []
        # 只取最近 30 期
        recent_tvl = [
            {"date": t.get("date"), "usd": t.get("totalLiquidityUSD")}
            for t in (tvl_history[-30:] if len(tvl_history) > 30 else tvl_history)
        ]
        return {
            "name": data.get("name", ""),
            "slug": slug,
            "tvl_current": data.get("currentChainTvls"),
            "tvl_history": recent_tvl,
            "chains": list((data.get("currentChainTvls") or {}).keys()),
            "category": data.get("category", ""),
            "description": (data.get("description") or "")[:300],
            "source_id": META["id"],
        }
    except Exception:
        return {}


def chains(top_n: int = 30) -> list[dict[str, Any]]:
    """取各区块链 TVL 排名。

    Args:
        top_n: 取前 N 条

    Returns:
        [{"name", "tvl", "tokenSymbol", "gecko_id", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(f"{_API_BASE}/v2/chains", headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        results: list[dict[str, Any]] = []
        for chain in data[:max(1, min(top_n, 200))]:
            results.append({
                "name": chain.get("name", ""),
                "tvl": chain.get("tvl"),
                "tokenSymbol": chain.get("tokenSymbol", ""),
                "gecko_id": chain.get("gecko_id", ""),
                "cmc_id": chain.get("cmcId", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def _normalize_protocol(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": item.get("name", ""),
        "slug": item.get("slug", ""),
        "tvl": item.get("tvl"),
        "chain": item.get("chain", ""),
        "chains": item.get("chains", []),
        "category": item.get("category", ""),
        "symbol": item.get("symbol", ""),
        "change_1d": item.get("change_1d"),
        "change_7d": item.get("change_7d"),
        "change_1m": item.get("change_1m"),
        "mcap": item.get("mcap"),
        "source_id": META["id"],
    }

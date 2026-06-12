"""上海黄金交易所 · 官方延时行情 · 无需 key · 免费 · 官方公开数据。

端点（SGE 官网公开 JSON）：
  实时价格  GET https://www.sge.com.cn/staticfiles/SGE/js/gis.js  (JS 变量内嵌)
  行情汇总  GET https://www.sge.com.cn/sjzx/yshqxx  (HTML 含 JSON，延时 15min)
  品种信息  GET https://www.sge.com.cn/api/market/quotation/getQuotation (官方 API)

说明：SGE 官网行情为延时 15 分钟公开数据，无 key 要求。
合规：上海黄金交易所官方公示数据，公开无版权限制。
Mac 直连可达。失败返回空，不抛出。
"""
from __future__ import annotations

import re
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "sge_gold",
    "domain": ["D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["gold", "commodity", "rate"],
}

_BASE = "https://www.sge.com.cn"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sge.com.cn/sjzx/yshqxx",
}

# SGE 主力品种代码
_MAIN_SYMBOLS = ["Au99.99", "Au99.95", "Au(T+D)", "mAu(T+D)", "Au50g", "Ag99.99", "Ag(T+D)"]


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def quotation() -> list[dict[str, Any]]:
    """获取 SGE 延时行情（官方公开 API）。

    Returns:
        [{"symbol", "price", "change", "change_pct", "high", "low",
          "volume", "currency", "updated", "source_id"}] 或空列表。
    """
    try:
        r = httpx.get(
            f"{_BASE}/api/market/quotation/getQuotation",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return _fallback_quotation()
        data = r.json()
        items = data.get("data") or data.get("list") or []
        if not isinstance(items, list) or not items:
            return _fallback_quotation()
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append({
                "symbol": item.get("varietyCode") or item.get("symbol", ""),
                "price": item.get("latestPrice") or item.get("price"),
                "change": item.get("priceChange") or item.get("change"),
                "change_pct": item.get("changePercent") or item.get("change_pct"),
                "high": item.get("highPrice") or item.get("high"),
                "low": item.get("lowPrice") or item.get("low"),
                "volume": item.get("volume") or item.get("tradingVolume"),
                "currency": "CNY",
                "updated": item.get("updateTime") or item.get("time", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return _fallback_quotation()


def _fallback_quotation() -> list[dict[str, Any]]:
    """备用：从 SGE 官网 JS 文件解析延时价格数据。"""
    try:
        r = httpx.get(
            f"{_BASE}/staticfiles/SGE/js/gis.js",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        text = r.text
        # 匹配 var gisData = {...} 或 JSON 格式价格数据
        match = re.search(r"var\s+gisData\s*=\s*(\{.*?\})\s*;", text, re.DOTALL)
        if not match:
            return []
        import json
        raw = json.loads(match.group(1))
        results: list[dict[str, Any]] = []
        for k, v in raw.items():
            if isinstance(v, dict):
                results.append({
                    "symbol": k,
                    "price": v.get("price") or v.get("closePrice"),
                    "change": v.get("change"),
                    "change_pct": v.get("changePct"),
                    "high": v.get("high"),
                    "low": v.get("low"),
                    "volume": v.get("volume"),
                    "currency": "CNY",
                    "updated": v.get("time", ""),
                    "source_id": META["id"],
                })
        return results
    except Exception:
        return []


def gold_price(symbol: str = "Au99.99") -> dict[str, Any]:
    """获取 SGE 单一黄金品种延时行情。

    Args:
        symbol: 品种代码，如 "Au99.99"（足金）/ "Au(T+D)"（延期合约）

    Returns:
        {"symbol", "price", "change", "high", "low", "currency", "source_id"} 或空 dict。
    """
    all_quotes = quotation()
    for q in all_quotes:
        if q.get("symbol", "") == symbol:
            return q
    return {}

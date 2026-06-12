"""中国理财网 · 银行理财产品官方查询 · 无需 key · 免费 · 官方公开数据。

端点（中国理财网官方公开 API）：
  产品搜索  POST https://www.chinawealth.com.cn/zzlc/fhInfo/queryFhInfo.go
  产品详情  GET  https://www.chinawealth.com.cn/zzlc/jsp/lccp.do?cpbm={code}
  收益公告  POST https://www.chinawealth.com.cn/zzlc/fhInfo/queryNetValueInfo.go

合规：中国理财网（chinawealth.com.cn）为银行业理财登记托管中心运营的官方信息披露平台，
数据属公开监管信息，无版权限制，无需授权。
Mac 直连可达（HTTPS）。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "chinawealth",
    "domain": ["D11", "D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["wealth_product", "bank_finance", "rate"],
}

_BASE = "https://www.chinawealth.com.cn"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://www.chinawealth.com.cn/zzlc/html/lccp.shtml",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search_products(
    product_name: str = "",
    bank_name: str = "",
    risk_level: str = "",
    page: int = 1,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """搜索银行理财产品（中国理财网官方接口）。

    Args:
        product_name: 产品名称关键词（空=不限）
        bank_name:    发行银行名称（空=不限）
        risk_level:   风险等级，"1"~"5" 对应 R1~R5（空=不限）
        page:         页码（从 1 起）
        per_page:     每页条数（最大 20）

    Returns:
        [{"code", "name", "bank", "risk_level", "term", "expected_return",
          "currency", "min_amount", "source_id"}] 或空列表。
    """
    payload = {
        "pageSize": str(min(per_page, 20)),
        "pageIndex": str(page),
        "cpmc": product_name,
        "jgmc": bank_name,
        "riskRating": risk_level,
        "shzt": "1",  # 在售状态
    }
    try:
        r = httpx.post(
            f"{_BASE}/zzlc/fhInfo/queryFhInfo.go",
            data=payload,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or data.get("list") or []
        if not isinstance(items, list):
            return []
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append({
                "code": item.get("cpbm", ""),
                "name": (item.get("cpmc") or "")[:200],
                "bank": item.get("jgmc", ""),
                "risk_level": item.get("riskRating", ""),
                "term": item.get("qxms", ""),
                "expected_return": item.get("qjsyl") or item.get("expectedYield"),
                "currency": item.get("bzms", "RMB"),
                "min_amount": item.get("qgse"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def net_value(
    product_code: str,
    page: int = 1,
    per_page: int = 10,
) -> list[dict[str, Any]]:
    """查询理财产品净值/收益公告。

    Args:
        product_code: 产品登记编码，如 "C1111000001"
        page:         页码
        per_page:     每页条数

    Returns:
        [{"date", "net_value", "cumulative_return", "source_id"}] 或空列表。
    """
    payload = {
        "pageSize": str(min(per_page, 20)),
        "pageIndex": str(page),
        "cpbm": product_code,
    }
    try:
        r = httpx.post(
            f"{_BASE}/zzlc/fhInfo/queryNetValueInfo.go",
            data=payload,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or data.get("list") or []
        if not isinstance(items, list):
            return []
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append({
                "date": item.get("jzrq", ""),
                "net_value": item.get("dwjz") or item.get("netValue"),
                "cumulative_return": item.get("ljjz") or item.get("cumulativeReturn"),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []

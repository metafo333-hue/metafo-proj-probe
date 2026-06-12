"""中国基金业协会 AMAC · 基金/私募公示查询 · 官方公开端点 · 免费 · 无需 key。

端点（AMAC 官方公示查询）：
  公募基金列表  GET https://www.amac.org.cn/publicInformation/queryPublicFundInfo.json
  私募基金管理人 GET https://gs.amac.org.cn/amac-infodisc/api/pof/manager/query
  基金产品查询  GET https://gs.amac.org.cn/amac-infodisc/api/pof/fund/query

合规：中国基金业协会（amac.org.cn）官方信息披露系统，属公开监管数据，
数据按《私募投资基金信息披露管理办法》公示，无版权限制。
Mac 直连可达。失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "amac",
    "domain": ["D11", "D8"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["fund", "private_equity", "compliance"],
}

_BASE = "https://www.amac.org.cn"
_GS_BASE = "https://gs.amac.org.cn/amac-infodisc/api"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "Mozilla/5.0 probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://gs.amac.org.cn/amac-infodisc/res/pof/fund/index.html",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def public_fund_list(
    fund_name: str = "",
    page: int = 1,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """查询公募基金信息（AMAC 官方公示）。

    Args:
        fund_name: 基金名称关键词（空=不限）
        page:      页码（从 1 起）
        per_page:  每页条数

    Returns:
        [{"code", "name", "manager", "trustee", "type", "establish_date",
          "source_id"}] 或空列表。
    """
    params: dict[str, Any] = {
        "fundName": fund_name,
        "pageNum": page,
        "pageSize": min(per_page, 50),
    }
    try:
        r = httpx.get(
            f"{_BASE}/publicInformation/queryPublicFundInfo.json",
            params=params,
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
                "code": item.get("fundCode", ""),
                "name": (item.get("fundName") or "")[:200],
                "manager": item.get("fundManager", ""),
                "trustee": item.get("trustee", ""),
                "type": item.get("fundType", ""),
                "establish_date": item.get("establishDate", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def private_fund_manager(
    manager_name: str = "",
    page: int = 0,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """查询私募基金管理人公示信息。

    Args:
        manager_name: 管理人名称关键词（空=不限）
        page:         页码（从 0 起）
        per_page:     每页条数（最大 100）

    Returns:
        [{"id", "name", "type", "register_date", "status",
          "fund_count", "source_id"}] 或空列表。
    """
    payload = {
        "managerName": manager_name,
        "page": page,
        "size": min(per_page, 100),
    }
    try:
        r = httpx.post(
            f"{_GS_BASE}/pof/manager/query",
            json=payload,
            headers={**_HEADERS, "Content-Type": "application/json"},
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or data.get("content") or []
        if not isinstance(items, list):
            return []
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append({
                "id": item.get("id", ""),
                "name": (item.get("managerName") or "")[:200],
                "type": item.get("orgType", ""),
                "register_date": item.get("registerDate", ""),
                "status": item.get("abnormalOrNot", ""),
                "fund_count": item.get("fundCount", 0),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def private_fund_query(
    fund_name: str = "",
    manager_id: str = "",
    page: int = 0,
    per_page: int = 20,
) -> list[dict[str, Any]]:
    """查询私募基金产品公示信息。

    Args:
        fund_name:  基金名称关键词（空=不限）
        manager_id: 管理人 ID（空=不限）
        page:       页码（从 0 起）
        per_page:   每页条数（最大 100）

    Returns:
        [{"id", "name", "manager", "type", "register_date",
          "status", "source_id"}] 或空列表。
    """
    payload = {
        "fundName": fund_name,
        "managerId": manager_id,
        "page": page,
        "size": min(per_page, 100),
    }
    try:
        r = httpx.post(
            f"{_GS_BASE}/pof/fund/query",
            json=payload,
            headers={**_HEADERS, "Content-Type": "application/json"},
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("data") or data.get("content") or []
        if not isinstance(items, list):
            return []
        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            results.append({
                "id": item.get("id", ""),
                "name": (item.get("fundName") or "")[:200],
                "manager": item.get("managerName", ""),
                "type": item.get("fundType", ""),
                "register_date": item.get("registerDate", ""),
                "status": item.get("fundStatus", ""),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []

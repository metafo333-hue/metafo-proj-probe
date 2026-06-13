"""GLEIF · Global LEI Foundation · 全球法人识别符数据库 · 免费开放 · 无需 key。

端点：
  search_by_name    GET .../lei-records?filter[entity.legalName]=...        — 按法人名搜索
  get_by_lei        GET .../lei-records/{lei}                               — 按 LEI 取详情
  get_relationships GET .../lei-records/{lei}/{direct|ultimate}-parent      — 母子公司关系（Level 2）
                    GET .../lei-records/{lei}/{direct|ultimate}-children
合规：GLEIF 是 G20 授权的全球法人识别符基金会，API 免费公开（CC0），数据来源为全球 LOUs 官方上报，
权威度极高（D11 企业/财务情报主力来源之一）。失败返回空，不抛出。

母子公司关系（get_relationships）免费替代 OpenCorporates 付费的公司层级能力：
覆盖「母公司本身持 LEI 且实体已报告关系记录」的会计合并口径；无关系报告时端点返 404（合法空，非错误）。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "gleif",
    "domain": ["D11"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["company", "lei", "relationship", "parent", "children"],
}

_API_BASE = "https://api.gleif.org/api/v1"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/vnd.api+json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search_by_name(
    legal_name: str,
    page_size: int = 10,
    fuzzy: bool = True,
) -> list[dict[str, Any]]:
    """按法人名称搜索 LEI 记录。

    Args:
        legal_name: 法人名称，如 "Apple Inc" / "阿里巴巴集团"
        page_size:  返回条数（1-50）
        fuzzy:      是否启用模糊匹配（True = filter[entity.legalName] 含匹配）

    Returns:
        [{"lei", "legal_name", "jurisdiction", "status", "registered_as",
          "legal_address_country", "registered_at_id", "source_id"}] 或空列表。
    """
    params: dict[str, Any] = {
        "page[size]": str(max(1, min(page_size, 50))),
        "page[number]": "1",
    }
    if fuzzy:
        params["filter[entity.legalName]"] = legal_name
    else:
        params["filter[entity.legalName]"] = legal_name
    try:
        r = httpx.get(
            f"{_API_BASE}/lei-records",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json().get("data") or []
        return [_normalize(item) for item in data]
    except Exception:
        return []


def get_by_lei(lei: str) -> dict[str, Any]:
    """按 LEI（20位字母数字编码）取法人详情。

    Args:
        lei: 20位 LEI，如 "7H6GLXDRUGQFU57RNE97"

    Returns:
        标准化法人详情 dict，失败返回空 dict。
    """
    lei = lei.strip().upper()
    if not lei:
        return {}
    try:
        r = httpx.get(
            f"{_API_BASE}/lei-records/{lei}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code == 200:
            data = r.json().get("data")
            if data:
                return _normalize(data)
    except Exception:
        pass
    return {}


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    """标准化 GLEIF LEI 记录（JSON:API 格式）。"""
    attrs = item.get("attributes") or {}
    entity = attrs.get("entity") or {}
    reg = attrs.get("registration") or {}
    legal_name_obj = entity.get("legalName") or {}
    legal_address = entity.get("legalAddress") or {}
    registered_at = entity.get("registeredAt") or {}
    return {
        "lei": attrs.get("lei", item.get("id", "")),
        "legal_name": legal_name_obj.get("name", "")[:200],
        "jurisdiction": entity.get("jurisdiction", ""),
        "status": entity.get("status", ""),
        "registered_as": entity.get("registeredAs", ""),
        "legal_address_country": legal_address.get("country", ""),
        "registered_at_id": registered_at.get("id", ""),
        "registration_status": reg.get("status", ""),
        "next_renewal": reg.get("nextRenewalDate", ""),
        "source_id": META["id"],
    }


# ── 母子公司关系（Level 2）· 免费替代 OpenCorporates 公司层级能力 ──────────────

def _fetch_relation_single(lei: str, relation: str) -> dict[str, Any]:
    """取单条关系端点（direct-parent / ultimate-parent）的标准化结果。

    无关系报告时端点返 404（合法空），统一映射为 {}；不抛出。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/lei-records/{lei}/{relation}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json().get("data")
        if isinstance(data, dict) and data:
            return _normalize(data)
    except Exception:
        pass
    return {}


def get_parents(lei: str) -> dict[str, Any]:
    """取法人的直接母公司与最终母公司（GLEIF Level 2 关系）。

    Returns:
        {"direct_parent": {...}|{}, "ultimate_parent": {...}|{}}。
        无母公司报告（404）时对应值为空 dict。
    """
    lei = lei.strip().upper()
    if not lei:
        return {"direct_parent": {}, "ultimate_parent": {}}
    return {
        "direct_parent": _fetch_relation_single(lei, "direct-parent"),
        "ultimate_parent": _fetch_relation_single(lei, "ultimate-parent"),
    }


def get_children(
    lei: str,
    page_size: int = 20,
    ultimate: bool = False,
) -> list[dict[str, Any]]:
    """取法人的直接（或最终）子公司列表（GLEIF Level 2 关系）。

    Args:
        lei:       母公司 LEI
        page_size: 返回条数（1-200，仅取首页）
        ultimate:  True=最终子公司链 / False=直接子公司

    Returns:
        子公司 LEI 记录列表（标准化），无子公司返空列表。
    """
    lei = lei.strip().upper()
    if not lei:
        return []
    relation = "ultimate-children" if ultimate else "direct-children"
    try:
        r = httpx.get(
            f"{_API_BASE}/lei-records/{lei}/{relation}",
            params={
                "page[size]": str(max(1, min(page_size, 200))),
                "page[number]": "1",
            },
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json().get("data") or []
        return [_normalize(item) for item in data]
    except Exception:
        return []


def get_relationships(lei: str, children_page_size: int = 20) -> dict[str, Any]:
    """一次性取法人完整母子公司图谱（免费替代 OpenCorporates 付费的公司层级能力）。

    Args:
        lei:                法人 LEI（20 位）
        children_page_size: 直接子公司返回条数（1-200）

    Returns:
        {"lei", "direct_parent", "ultimate_parent", "direct_children": [...], "source_id"}。
        无任何关系报告时各字段为空 dict / 空列表（合法，非错误）。
    """
    lei = lei.strip().upper()
    parents = get_parents(lei)
    return {
        "lei": lei,
        "direct_parent": parents["direct_parent"],
        "ultimate_parent": parents["ultimate_parent"],
        "direct_children": get_children(lei, page_size=children_page_size),
        "source_id": META["id"],
    }

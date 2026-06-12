"""crt.sh · 证书透明日志查询 · 无需 key · 完全免费。

端点：GET https://crt.sh/?q=<domain>&output=json
参数：
  q       — 域名查询（支持通配 %.example.com）
  output  — 必须是 "json"
  deduplicate — "Y" 去重（推荐）

合规：crt.sh 是 Sectigo（原 Comodo CA）维护的公开证书透明查询服务，
      数据来源为 Certificate Transparency logs（RFC 6962），属于公开基础设施数据。
      官网：https://crt.sh/ — 无 ToS 限制，明确为公共服务。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "crt_sh",
    "domain": ["D8"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["certificate", "domain", "ssl", "ct_log"],
}

_API_BASE = "https://crt.sh"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; ct-research)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search(
    domain: str,
    deduplicate: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """查询域名的证书透明记录（颁发历史）。

    Args:
        domain:      域名，如 "example.com" 或通配 "%.example.com"
        deduplicate: 是否去重（去除重复证书，推荐 True）
        limit:       最多返回条数（1-2000）

    Returns:
        [{"id", "issuer_ca_id", "issuer_name", "common_name", "name_value",
          "not_before", "not_after", "serial_number", "source_id"}]
        或空列表。
    """
    params: dict[str, str] = {
        "q": domain,
        "output": "json",
    }
    if deduplicate:
        params["deduplicate"] = "Y"
    try:
        r = httpx.get(
            _API_BASE,
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        results: list[dict[str, Any]] = []
        for item in data[:max(1, min(limit, 2000))]:
            results.append(_normalize_cert(item))
        return results
    except Exception:
        return []


def wildcard_search(
    apex_domain: str,
    deduplicate: bool = True,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """通配查询：取顶级域名下所有子域名的证书记录。

    Args:
        apex_domain: 顶级域名，如 "metafoclaw.com"（自动转换为 %.metafoclaw.com）
        deduplicate: 是否去重
        limit:       最多返回条数

    Returns:
        同 search()。
    """
    return search(f"%.{apex_domain.lstrip('.')}", deduplicate=deduplicate, limit=limit)


def cert_detail(cert_id: int) -> dict[str, Any]:
    """取单个证书详情（通过 crt.sh 内部 ID）。

    Args:
        cert_id: crt.sh 内部证书 ID（由 search() 返回的 id 字段）

    Returns:
        同 _normalize_cert() 结构（更完整），或空 dict。
    """
    try:
        r = httpx.get(
            _API_BASE,
            params={"id": str(cert_id), "output": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if isinstance(data, list) and data:
            return _normalize_cert(data[0])
        if isinstance(data, dict):
            return _normalize_cert(data)
        return {}
    except Exception:
        return {}


def _normalize_cert(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "issuer_ca_id": item.get("issuer_ca_id"),
        "issuer_name": item.get("issuer_name", ""),
        "common_name": item.get("common_name", ""),
        "name_value": item.get("name_value", ""),
        "not_before": item.get("not_before", ""),
        "not_after": item.get("not_after", ""),
        "serial_number": item.get("serial_number", ""),
        "source_id": META["id"],
    }

"""RDAP ICANN · 域名注册信息查询（Registration Data Access Protocol）。

端点：
  GET https://rdap.org/domain/<domain>       — 域名 RDAP（rdap.org 统一入口）
  GET https://rdap.org/ip/<ip>               — IP 段 RDAP
  GET https://rdap.org/autnum/<asn>          — ASN RDAP

合规：RDAP 是 ICANN 定义的标准协议（RFC 7482/7483），取代旧版 WHOIS。
      rdap.org 是公开聚合入口，由 ARIN 维护，完全免费，数据来源各注册局官方。
      数据属于公开注册数据，属于合规信息调查范畴。
      注意：部分注册数据受 GDPR 保护（欧洲注册人姓名/邮箱可能被屏蔽）。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "rdap_icann",
    "domain": ["D4", "D8"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["domain", "whois", "registrar", "ip", "asn"],
}

_RDAP_BASE = "https://rdap.org"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; domain-research)",
    "Accept": "application/rdap+json, application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def domain_lookup(domain: str) -> dict[str, Any]:
    """查询域名注册信息（RDAP）。

    Args:
        domain: 域名，如 "example.com"（不带 http://）

    Returns:
        {"ldhName", "handle", "status", "registrar", "nameservers",
         "created", "updated", "expires", "source_id"}
        失败返回空 dict。
    """
    clean = domain.strip().lstrip("http://").lstrip("https://").split("/")[0].lower()
    try:
        r = httpx.get(
            f"{_RDAP_BASE}/domain/{clean}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return _normalize_domain(data)
    except Exception:
        return {}


def ip_lookup(ip: str) -> dict[str, Any]:
    """查询 IP 段注册信息。

    Args:
        ip: IPv4 或 IPv6 地址，如 "8.8.8.8" / "2001:4860:4860::8888"

    Returns:
        {"startAddress", "endAddress", "name", "type", "country",
         "handle", "registrant_org", "source_id"} 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_RDAP_BASE}/ip/{ip}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return _normalize_ip(data)
    except Exception:
        return {}


def asn_lookup(asn: int | str) -> dict[str, Any]:
    """查询 ASN（Autonomous System Number）信息。

    Args:
        asn: ASN 号，如 15169（Google）；可含 "AS" 前缀

    Returns:
        {"startAutnum", "endAutnum", "name", "handle", "country", "source_id"} 或空 dict。
    """
    asn_str = str(asn).lstrip("ASas")
    try:
        r = httpx.get(
            f"{_RDAP_BASE}/autnum/{asn_str}",
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return {
            "startAutnum": data.get("startAutnum"),
            "endAutnum": data.get("endAutnum"),
            "name": data.get("name", ""),
            "handle": data.get("handle", ""),
            "country": data.get("country", ""),
            "status": data.get("status", []),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def _normalize_domain(data: dict[str, Any]) -> dict[str, Any]:
    # events → created/updated/expires
    events: dict[str, str] = {}
    for ev in (data.get("events") or []):
        action = ev.get("eventAction", "")
        date = ev.get("eventDate", "")
        if "registration" in action:
            events["created"] = date
        elif "last changed" in action or "updated" in action:
            events["updated"] = date
        elif "expiration" in action:
            events["expires"] = date

    # registrar from entities
    registrar = ""
    for ent in (data.get("entities") or []):
        roles = ent.get("roles") or []
        if "registrar" in roles:
            vcard = ent.get("vcardArray") or []
            if len(vcard) >= 2:
                for prop in vcard[1]:
                    if prop[0] == "fn":
                        registrar = prop[3]
                        break
            if not registrar:
                registrar = ent.get("handle", "")
            break

    nameservers = [
        ns.get("ldhName", "") for ns in (data.get("nameservers") or [])
    ]

    return {
        "ldhName": data.get("ldhName", ""),
        "handle": data.get("handle", ""),
        "status": data.get("status", []),
        "registrar": registrar,
        "nameservers": nameservers,
        "created": events.get("created", ""),
        "updated": events.get("updated", ""),
        "expires": events.get("expires", ""),
        "source_id": META["id"],
    }


def _normalize_ip(data: dict[str, Any]) -> dict[str, Any]:
    org = ""
    for ent in (data.get("entities") or []):
        roles = ent.get("roles") or []
        if "registrant" in roles or "administrative" in roles:
            vcard = ent.get("vcardArray") or []
            if len(vcard) >= 2:
                for prop in vcard[1]:
                    if prop[0] == "fn":
                        org = prop[3]
                        break
            break
    return {
        "startAddress": data.get("startAddress", ""),
        "endAddress": data.get("endAddress", ""),
        "name": data.get("name", ""),
        "type": data.get("type", ""),
        "country": data.get("country", ""),
        "handle": data.get("handle", ""),
        "registrant_org": org,
        "source_id": META["id"],
    }

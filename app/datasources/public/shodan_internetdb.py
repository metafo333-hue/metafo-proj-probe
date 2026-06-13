"""Shodan InternetDB · 免费暴露资产快查 · 无需 key · 免费层。

InternetDB = Shodan 的免费轻量端点，按 IP 返回暴露端口/漏洞/主机名/CPE/标签。
probe 用途：法风控/尽调赛道「资产·技术侧风险」—— 供应商技术尽调时快查对方
暴露面（开放端口、已知 CVE），配合 crt_sh/rdap/urlscan 构成 ≥2 源资产侦察。

端点（实测 200 真数据 2026-06-13）：
  GET https://internetdb.shodan.io/{ip}
  返回 {ip, hostnames, ports, vulns, cpes, tags}
合规：Shodan 官方免费端点，仅返回被动扫描的公开暴露信息，不做主动探测。
注意：InternetDB 仅支持 IPv4，不支持域名（本模块提供 lookup_domain 先做 DNS 解析）。
深度扫描（服务 banner/历史/搜索）需 Shodan 完整版付费 key（→ P3 R1）。
失败返回空，不抛出。
"""
from __future__ import annotations

import socket
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "shodan_internetdb",
    "domain": ["D8", "D12"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["asset", "exposure", "security"],
}

_API_BASE = "https://internetdb.shodan.io"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """免费端点无需 key，恒返回 True。"""
    return True


def lookup_ip(ip: str) -> dict[str, Any]:
    """查询某 IPv4 的暴露资产信息。

    Args:
        ip: IPv4 地址，如 "8.8.8.8"

    Returns:
        {"ip", "hostnames", "ports", "vulns", "cpes", "tags", "source_id"} 或空 dict。
        vulns = 已知 CVE 列表（空表示无已知漏洞）；ports = 开放端口。
    """
    try:
        r = httpx.get(f"{_API_BASE}/{ip}", headers=_HEADERS,
                      timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        return {
            "ip": data.get("ip", ip),
            "hostnames": data.get("hostnames", []),
            "ports": data.get("ports", []),
            "vulns": data.get("vulns", []),
            "cpes": data.get("cpes", []),
            "tags": data.get("tags", []),
            "source_id": META["id"],
        }
    except Exception:
        return {}


def lookup_domain(domain: str) -> dict[str, Any]:
    """先 DNS 解析域名为 IP，再查暴露资产。

    Args:
        domain: 域名，如 "example.com"

    Returns:
        lookup_ip 结果，附加 "domain" 字段；解析失败返回空 dict。
    """
    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        return {}
    result = lookup_ip(ip)
    if result:
        result["domain"] = domain
    return result

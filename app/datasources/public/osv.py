"""OSV.dev · Open Source Vulnerabilities API · Google · 无需 key · 免费 · Apache-2.0。

端点：
  query    POST https://api.osv.dev/v1/query  — 按 package 或 commit 查漏洞
  by_id    GET  https://api.osv.dev/v1/vulns/{id}  — 按 OSV/CVE id 取详情
合规：OSV 是 Google 维护的公共安全数据库，官方 API 无速率限制文档要求，免费使用。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "osv",
    "domain": ["D8", "D12"],
    "access_type": "free",
    "kinds": ["vuln", "search"],
}

_API_BASE = "https://api.osv.dev/v1"
_TIMEOUT = 15
_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
}


def query_package(name: str, ecosystem: str, version: str = "") -> list[dict[str, Any]]:
    """查询某 package 的已知漏洞列表。

    Args:
        name:       包名，如 "requests"
        ecosystem:  如 "PyPI" / "npm" / "Go" / "Maven"
        version:    可选，指定版本号

    返回 [{id, summary, severity, published, aliases}] 或空列表。
    """
    pkg: dict[str, Any] = {"name": name, "ecosystem": ecosystem}
    if version:
        pkg["version"] = version
    payload: dict[str, Any] = {"package": pkg}
    try:
        r = httpx.post(f"{_API_BASE}/query", json=payload, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code == 200:
            vulns = r.json().get("vulns", [])
            return [_normalize(v) for v in vulns[:20]]
    except Exception:
        pass
    return []


def by_id(vuln_id: str) -> dict[str, Any]:
    """按 OSV id（如 "OSV-2021-111"）或 CVE id 取漏洞详情。失败返回空 dict。"""
    try:
        r = httpx.get(
            f"{_API_BASE}/vulns/{vuln_id}",
            headers={"User-Agent": _HEADERS["User-Agent"]},
            timeout=_TIMEOUT,
        )
        if r.status_code == 200:
            return _normalize(r.json())
    except Exception:
        pass
    return {}


def _normalize(v: dict[str, Any]) -> dict[str, Any]:
    """标准化漏洞元数据（原料进结论出：只取摘要字段）。"""
    severity = ""
    db_sevs = v.get("database_specific", {}).get("severity", "")
    if db_sevs:
        severity = db_sevs
    elif v.get("severity"):
        # CVSS 评分列表
        sev_list = v["severity"]
        if isinstance(sev_list, list) and sev_list:
            severity = sev_list[0].get("score", "")
    return {
        "id": v.get("id", ""),
        "summary": (v.get("summary") or "")[:300],
        "details": (v.get("details") or "")[:500],
        "severity": severity,
        "published": v.get("published", ""),
        "modified": v.get("modified", ""),
        "aliases": v.get("aliases", [])[:5],
        "source_id": META["id"],
    }

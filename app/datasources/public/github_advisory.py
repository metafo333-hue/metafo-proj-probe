"""GitHub Advisory Database · 安全公告 · 免费 · 无需 key（公开端点）· D8/D12。

端点（GitHub REST API v3）：
  list_advisories  GET https://api.github.com/advisories
  get_advisory     GET https://api.github.com/advisories/{ghsa_id}
合规：GitHub Security Advisories 公开 REST API，无需 token（公开端点每小时 60 次），
      数据为 CC0/公有领域，官方明确开放给工具链使用。
      若配置 GITHUB_TOKEN 则速率提升至 5000/hr（环境变量可选）。
失败返回空，不抛出。
"""
from __future__ import annotations

import os
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "github_advisory",
    "domain": ["D8", "D12"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["advisory", "cve", "security"],
}

_API_BASE = "https://api.github.com"
_TIMEOUT = 20
_ACCEPT = "application/vnd.github+json"
_API_VERSION = "2022-11-28"

# 支持的 CVSS 严重等级
SEVERITIES = ("critical", "high", "medium", "low", "unknown")


def configured() -> bool:
    """无 token 也可用（仅速率较低），恒返回 True。"""
    return True


def _headers() -> dict[str, str]:
    h = {
        "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
        "Accept": _ACCEPT,
        "X-GitHub-Api-Version": _API_VERSION,
    }
    token = os.getenv("GITHUB_TOKEN", "")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def list_advisories(
    severity: str = "",
    ecosystem: str = "",
    cve_id: str = "",
    ghsa_id: str = "",
    per_page: int = 20,
    page: int = 1,
) -> list[dict[str, Any]]:
    """列出 GitHub Security Advisories（支持多维过滤）。

    Args:
        severity:  CVSS 严重等级过滤，如 "critical" / "high" / "medium" / "low"
        ecosystem: 包生态系统过滤，如 "npm" / "pypi" / "go" / "maven" / "cargo"
        cve_id:    按 CVE ID 精确查询，如 "CVE-2024-12345"
        ghsa_id:   按 GHSA ID 精确查询，如 "GHSA-xxxx-xxxx-xxxx"
        per_page:  每页条数（1-100）
        page:      页码（从 1 开始）

    Returns:
        [{"ghsa_id", "cve_id", "severity", "summary", "ecosystems",
          "published_at", "updated_at", "cvss_score", "cwe_ids", "html_url", "source_id"}]
        或空列表。
    """
    params: dict[str, str] = {
        "per_page": str(min(max(1, per_page), 100)),
        "page": str(max(1, page)),
    }
    if severity and severity in SEVERITIES:
        params["severity"] = severity
    if ecosystem:
        params["ecosystem"] = ecosystem
    if cve_id:
        params["cve_id"] = cve_id
    if ghsa_id:
        params["ghsa_id"] = ghsa_id
    try:
        r = httpx.get(
            f"{_API_BASE}/advisories",
            params=params,
            headers=_headers(),
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        if not isinstance(data, list):
            return []
        return [_normalize(adv) for adv in data]
    except Exception:
        return []


def get_advisory(ghsa_id: str) -> dict[str, Any]:
    """按 GHSA ID 获取单条公告详情。

    Args:
        ghsa_id: GitHub Security Advisory ID，如 "GHSA-xxxx-xxxx-xxxx"

    Returns:
        单条公告 dict 或空 dict。
    """
    try:
        r = httpx.get(
            f"{_API_BASE}/advisories/{ghsa_id}",
            headers=_headers(),
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return _normalize(data)
    except Exception:
        return {}


def _normalize(adv: dict[str, Any]) -> dict[str, Any]:
    cvss = adv.get("cvss") or {}
    cwes = adv.get("cwes") or []
    vulns = adv.get("vulnerabilities") or []
    ecosystems = list({
        v.get("package", {}).get("ecosystem", "")
        for v in vulns
        if isinstance(v, dict) and v.get("package")
    })
    return {
        "ghsa_id": adv.get("ghsa_id", ""),
        "cve_id": adv.get("cve_id", ""),
        "severity": adv.get("severity", ""),
        "summary": (adv.get("summary") or "")[:500],
        "description": (adv.get("description") or "")[:1000],
        "ecosystems": ecosystems,
        "published_at": adv.get("published_at", ""),
        "updated_at": adv.get("updated_at", ""),
        "withdrawn_at": adv.get("withdrawn_at", ""),
        "cvss_score": cvss.get("score"),
        "cvss_vector": (cvss.get("vector_string") or "")[:100],
        "cwe_ids": [c.get("cwe_id", "") for c in cwes[:5]],
        "html_url": adv.get("html_url", ""),
        "source_id": META["id"],
    }

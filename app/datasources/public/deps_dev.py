"""deps.dev (Google) · 开源包依赖图 API · 免费 · 无需 key · D12。

端点（Open Source Insights REST API v3alpha）：
  package_info  GET https://api.deps.dev/v3alpha/systems/{system}/packages/{name}
  version_info  GET https://api.deps.dev/v3alpha/systems/{system}/packages/{name}/versions/{version}
  dependencies  GET https://api.deps.dev/v3alpha/query?versionKey.system=...&versionKey.name=...&versionKey.version=...
合规：Google Open Source Insights 官方公开 API，无 ToS 限制，数据属公共域，
      允许分析与研究使用。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

META: dict[str, Any] = {
    "id": "deps_dev",
    "domain": ["D12"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["package", "dependency", "version"],
}

_API_BASE = "https://api.deps.dev/v3alpha"
_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}

# 支持的包管理系统
SYSTEMS = ("npm", "pypi", "go", "maven", "cargo", "nuget")


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def package_info(system: str, name: str) -> dict[str, Any]:
    """查询包基本信息（最新版本列表、发布时间等）。

    Args:
        system: 包管理系统，如 "npm" / "pypi" / "go" / "maven" / "cargo" / "nuget"
        name:   包名，如 "express" / "requests" / "github.com/gin-gonic/gin"

    Returns:
        {"system", "name", "default_version", "versions_count", "versions", "source_id"}
        或空 dict。
    """
    url = f"{_API_BASE}/systems/{system}/packages/{quote(name, safe='')}"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        pkg = data.get("packageKey", {})
        versions = data.get("versions", [])
        # 找 default version
        default_ver = ""
        for v in versions:
            if v.get("isDefault"):
                default_ver = v.get("versionKey", {}).get("version", "")
                break
        return {
            "system": pkg.get("system", system).lower(),
            "name": pkg.get("name", name),
            "default_version": default_ver,
            "versions_count": len(versions),
            "versions": [
                {
                    "version": v.get("versionKey", {}).get("version", ""),
                    "published_at": v.get("publishedAt", ""),
                    "is_default": v.get("isDefault", False),
                }
                for v in versions[:20]
            ],
            "source_id": META["id"],
        }
    except Exception:
        return {}


def version_info(system: str, name: str, version: str) -> dict[str, Any]:
    """查询特定版本的元数据（依赖数、许可证、CVE 等）。

    Args:
        system:  包管理系统
        name:    包名
        version: 版本号，如 "4.18.2"

    Returns:
        {"system", "name", "version", "published_at", "licenses",
         "dependencies_count", "advisories_count", "is_deprecated", "source_id"}
        或空 dict。
    """
    url = (
        f"{_API_BASE}/systems/{system}/packages/{quote(name, safe='')}"
        f"/versions/{quote(version, safe='')}"
    )
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        vk = data.get("versionKey", {})
        links = data.get("links", [])
        advisories = data.get("advisoryKeys", [])
        # licenses 字段是字符串列表（如 ["MIT"]），不是对象列表
        raw_licenses = data.get("licenses") or []
        licenses = [lic if isinstance(lic, str) else lic.get("license", "") for lic in raw_licenses]
        return {
            "system": vk.get("system", system).lower(),
            "name": vk.get("name", name),
            "version": vk.get("version", version),
            "published_at": data.get("publishedAt", ""),
            "is_default": data.get("isDefault", False),
            "is_deprecated": data.get("isDeprecated", False),
            "licenses": licenses,
            "advisories_count": len(advisories),
            "advisories": [a.get("id", "") for a in advisories[:10]],
            "links": [lk.get("url", "") for lk in links[:5]],
            "source_id": META["id"],
        }
    except Exception:
        return {}


def dependencies(system: str, name: str, version: str) -> list[dict[str, Any]]:
    """查询特定版本的直接依赖（及其版本要求）。

    Args:
        system:  包管理系统
        name:    包名
        version: 版本号

    Returns:
        [{"system", "name", "version", "relation"}] 或空列表。
    """
    params = {
        "versionKey.system": system.upper() if system.upper() in [s.upper() for s in SYSTEMS] else system,
        "versionKey.name": name,
        "versionKey.version": version,
    }
    try:
        r = httpx.get(
            f"{_API_BASE}/query",
            params=params,
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        results_raw = data.get("results", [])
        results: list[dict[str, Any]] = []
        for item in results_raw:
            ver = item.get("version", {})
            vk = ver.get("versionKey", {})
            deps = ver.get("dependencies", [])
            for dep in deps:
                dk = dep.get("versionKey", {})
                results.append({
                    "system": dk.get("system", "").lower(),
                    "name": dk.get("name", ""),
                    "version": dk.get("version", ""),
                    "relation": dep.get("relation", "DIRECT"),
                    "source_id": META["id"],
                })
        return results
    except Exception:
        return []

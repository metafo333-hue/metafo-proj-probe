"""VirusTotal API v3 · 需 VIRUSTOTAL_KEY env · 免费层（500 req/day）。

端点：
  url lookup     https://www.virustotal.com/api/v3/urls/{id}
  domain report  https://www.virustotal.com/api/v3/domains/{domain}
合规：VirusTotal 官方 API，需注册免费 key，公共威胁情报开放使用。
未配置 VIRUSTOTAL_KEY 时所有函数返回空，不报错。
失败返回空，不抛出。
"""
from __future__ import annotations

import base64
import os
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "virustotal",
    "domain": ["D8", "D1"],
    "access_type": "free_with_key",
    "method": ["O"],
    "kinds": ["url_report", "domain_report", "security"],
    "needs_key": True,
    "key_env": "VIRUSTOTAL_KEY",
}

_API_BASE = "https://www.virustotal.com/api/v3"
_TIMEOUT = 20


def _get_key() -> str:
    """从环境变量读取 API key，未配置返回空字符串。"""
    return os.environ.get("VIRUSTOTAL_KEY", "").strip()


def _headers(key: str) -> dict[str, str]:
    return {
        "x-apikey": key,
        "Accept": "application/json",
        "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    }


def _parse_stats(stats: dict[str, Any]) -> dict[str, int]:
    """提取检测统计 {malicious, suspicious, harmless, undetected}。"""
    return {
        "malicious": stats.get("malicious", 0),
        "suspicious": stats.get("suspicious", 0),
        "harmless": stats.get("harmless", 0),
        "undetected": stats.get("undetected", 0),
    }


def lookup_url(url: str) -> dict[str, Any]:
    """查询 URL 的 VirusTotal 检测报告。

    Args:
        url: 要查询的 URL（http/https）

    Returns:
        {
          "url": "...",
          "stats": {malicious, suspicious, harmless, undetected},
          "reputation": int,
          "last_analysis_date": "YYYY-MM-DD",
          "source_id": "virustotal"
        }
        未配置 key 或失败返回空字典。
    """
    key = _get_key()
    if not key:
        return {}
    # VirusTotal URL lookup 需要 base64url 编码（无填充）
    url_id = base64.urlsafe_b64encode(url.encode()).rstrip(b"=").decode()
    try:
        r = httpx.get(
            f"{_API_BASE}/urls/{url_id}",
            timeout=_TIMEOUT,
            headers=_headers(key),
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        attrs = (data.get("data") or {}).get("attributes") or {}
        stats = _parse_stats(attrs.get("last_analysis_stats") or {})
        # 时间戳转日期
        ts = attrs.get("last_analysis_date", 0)
        date_str = ""
        if ts:
            import datetime
            date_str = datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        return {
            "url": attrs.get("url", url),
            "stats": stats,
            "reputation": attrs.get("reputation", 0),
            "last_analysis_date": date_str,
            "categories": attrs.get("categories") or {},
            "source_id": META["id"],
        }
    except Exception:
        return {}


def lookup_domain(domain: str) -> dict[str, Any]:
    """查询域名的 VirusTotal 检测报告。

    Args:
        domain: 纯域名，如 "example.com"（不含协议）

    Returns:
        {
          "domain": "...",
          "stats": {malicious, suspicious, harmless, undetected},
          "reputation": int,
          "registrar": "...",
          "creation_date": "...",
          "source_id": "virustotal"
        }
        未配置 key 或失败返回空字典。
    """
    key = _get_key()
    if not key:
        return {}
    # 清理域名：去掉协议和路径
    clean = domain.strip().lower()
    for prefix in ("https://", "http://", "www."):
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
    clean = clean.split("/")[0].split("?")[0]
    if not clean:
        return {}
    try:
        r = httpx.get(
            f"{_API_BASE}/domains/{clean}",
            timeout=_TIMEOUT,
            headers=_headers(key),
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        attrs = (data.get("data") or {}).get("attributes") or {}
        stats = _parse_stats(attrs.get("last_analysis_stats") or {})
        return {
            "domain": clean,
            "stats": stats,
            "reputation": attrs.get("reputation", 0),
            "registrar": attrs.get("registrar", ""),
            "creation_date": attrs.get("creation_date", ""),
            "categories": attrs.get("categories") or {},
            "source_id": META["id"],
        }
    except Exception:
        return {}


def lookup(target: str) -> dict[str, Any]:
    """统一入口：自动判断 target 是 URL 还是域名并调用对应函数。

    未配置 key 时返回空字典，不报错。
    """
    key = _get_key()
    if not key:
        return {}
    t = target.strip()
    if t.startswith("http://") or t.startswith("https://"):
        return lookup_url(t)
    return lookup_domain(t)

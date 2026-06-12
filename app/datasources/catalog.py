"""数据源仓库 catalog · 加载 ledger.yaml 多域分类 + 元数据查询。

不破坏现有 registry.py（独立模块）。

用法：
    from app.datasources import catalog

    # 查所有 live 源
    catalog.list_sources(status="live")

    # 按域查
    catalog.list_sources(domain="D1")

    # 按 access_type 查
    catalog.list_sources(access_type="free")

    # 取单源详情
    catalog.get_source("wikipedia")

    # 域描述
    catalog.domain_label("D1")  # → "真相核查 / 事实核验"
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_LEDGER = Path(__file__).resolve().parent / "ledger.yaml"

# ── 内部缓存（单进程生命周期）──────────────────────────────────────────────
_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is None:
        if not _LEDGER.exists():
            _cache = {}
        else:
            _cache = yaml.safe_load(_LEDGER.read_text(encoding="utf-8")) or {}
    return _cache


def reload() -> None:
    """强制重新加载（测试 / 热更新用）。"""
    global _cache
    _cache = None


# ── 公共 API ──────────────────────────────────────────────────────────────

def get_source(source_id: str) -> dict[str, Any] | None:
    """取单一数据源完整元数据。不存在返回 None。"""
    return (_load().get("sources") or {}).get(source_id)


def list_sources(
    domain: str | None = None,
    access_type: str | None = None,
    method: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """按条件过滤数据源列表，返回带 id 字段的 dict 列表。

    Args:
        domain:      信息域代码，如 "D1"（模糊匹配，源的 domain 列表中含该值即命中）
        access_type: "free" / "paid" / "free_with_key" / "paid_with_key"
        method:      "L" / "S" / "W" / "O" / "D"（源的 method 列表中含该值即命中）
        status:      "live" / "pending" / "cataloged" / "rejected"

    所有条件为 AND 关系；未传则不过滤该维度。
    """
    sources = _load().get("sources") or {}
    result: list[dict[str, Any]] = []
    for sid, entry in sources.items():
        if domain is not None:
            domains = entry.get("domain") or []
            if domain not in domains:
                continue
        if access_type is not None:
            if entry.get("access_type") != access_type:
                continue
        if method is not None:
            methods = entry.get("method") or []
            if method not in methods:
                continue
        if status is not None:
            if entry.get("status") != status:
                continue
        result.append({"id": sid, **entry})
    return result


def domain_label(domain_code: str) -> str:
    """返回域的中文描述，如 domain_label("D1") → "真相核查 / 事实核验"。未知域返回空字符串。"""
    return (_load().get("domains") or {}).get(domain_code, "")


def list_domains() -> dict[str, str]:
    """返回所有域代码 → 描述的映射 dict。"""
    return dict((_load().get("domains") or {}))


def ledger_version() -> int:
    """返回 ledger 版本号。"""
    return int(_load().get("version", 1))


def all_source_ids() -> list[str]:
    """返回所有已登记的数据源 id 列表（不过滤 status）。"""
    return list((_load().get("sources") or {}).keys())

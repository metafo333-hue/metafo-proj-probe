"""GitHub Intel RSS · AI 免费额度聚合 · D17 · 无需 key · 免费。

数据源（均经实测 HTTP 200·2026-06-12）：
  fetch_registry   mnfst/awesome-free-llm-apis data.json  — AI LLM 免费 API 额度聚合（CC0·24家·机器可读）
  fetch_mlcontests mlcontests.github.io competitions.json — ML 竞赛列表（GPL-3.0·350条·多平台）

选源依据（见 docs/4-research/datasource-aideal-source-registry-v1.md §I1/I6）：
- mnfst/awesome-free-llm-apis：CC0，data.json 直接机器可读，每次 commit 自动刷新，首选入自动管线。
- mlcontests：免认证，master branch JSON，341 条多平台竞赛，tag 可过滤 AI。
- cheahjs/free-llm-api-resources：license 未明确（⚠️），暂不入管线（待 license 确认升主力）。

合规铁律：永不代爬，仅调 raw.githubusercontent.com / GitHub Pages 机器可读 JSON。
失败返回空，不抛出。
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "github_intel_rss",
    "domain": ["D17", "D12"],
    "access_type": "free",
    "method": ["O", "W"],
    "kinds": ["ai_deal", "competition", "llm_api"],
}

# mnfst/awesome-free-llm-apis — CC0，machine-readable JSON
_MNFST_URL = "https://raw.githubusercontent.com/mnfst/awesome-free-llm-apis/main/data.json"

# mlcontests.github.io — GPL-3.0，免认证，master branch 含实际数据
_MLCONTESTS_URL = "https://raw.githubusercontent.com/mlcontests/mlcontests.github.io/master/competitions.json"

_TIMEOUT = 30  # 原始文件较大
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
    "Accept": "application/json",
}

# 模块级缓存（会话内生命周期）
_mnfst_cache: list[dict[str, Any]] | None = None
_mlcontests_cache: list[dict[str, Any]] | None = None


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def fetch_registry(
    force_reload: bool = False,
    keyword: str = "",
) -> list[dict[str, Any]]:
    """拉取 mnfst/awesome-free-llm-apis 的 LLM 免费 API 额度列表。

    Args:
        force_reload: True = 强制重新下载（忽略缓存）
        keyword:      可选，按 provider 名称或描述过滤（大小写不敏感）

    Returns:
        [{"provider", "category", "country", "url", "description",
          "models_count", "source_id"}] 或空列表。
    """
    global _mnfst_cache
    if _mnfst_cache is None or force_reload:
        try:
            r = httpx.get(_MNFST_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
            if r.status_code != 200:
                return []
            raw = r.json()
            providers = raw.get("providers") or []
            _mnfst_cache = [_normalize_provider(p) for p in providers]
        except Exception:
            return []

    results = _mnfst_cache
    if keyword:
        kw = keyword.lower()
        results = [
            p for p in results
            if kw in p.get("provider", "").lower()
            or kw in p.get("description", "").lower()
        ]
    return results


def fetch_mlcontests(
    force_reload: bool = False,
    tag: str = "",
    platform: str = "",
    top_n: int = 50,
) -> list[dict[str, Any]]:
    """拉取 mlcontests 竞赛列表（机器学习/AI 竞赛）。

    Args:
        force_reload: True = 强制重新下载
        tag:          按 tag 过滤，如 "nlp" / "ai" / "supervised"（含匹配）
        platform:     按平台过滤，如 "Kaggle" / "CrunchDAO"（精确匹配）
        top_n:        最多返回条数（1-500）

    Returns:
        [{"name", "url", "tags", "launched", "deadline", "prize",
          "platform", "sponsor", "source_id"}] 或空列表。
    """
    global _mlcontests_cache
    if _mlcontests_cache is None or force_reload:
        try:
            r = httpx.get(_MLCONTESTS_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
            if r.status_code != 200:
                return []
            raw = r.json()
            # 格式可能是 {"data": [...]} 或直接 [...]
            items = raw.get("data", raw) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                return []
            _mlcontests_cache = [_normalize_competition(c) for c in items]
        except Exception:
            return []

    results = _mlcontests_cache
    if tag:
        tag_lower = tag.lower()
        results = [c for c in results if tag_lower in [t.lower() for t in (c.get("tags") or [])]]
    if platform:
        results = [c for c in results if c.get("platform", "") == platform]
    return results[:max(1, min(top_n, 500))]


def _normalize_provider(p: dict[str, Any]) -> dict[str, Any]:
    """标准化 mnfst provider 条目。"""
    models = p.get("models") or []
    return {
        "provider": (p.get("name") or "")[:150],
        "category": p.get("category", ""),
        "country": p.get("country", ""),
        "url": p.get("url", ""),
        "base_url": p.get("baseUrl", ""),
        "description": (p.get("description") or "")[:400],
        "models_count": len(models),
        "model_ids": [m.get("id", "") for m in models[:5]],
        "source_id": META["id"],
    }


def _normalize_competition(c: dict[str, Any]) -> dict[str, Any]:
    """标准化 mlcontests 竞赛条目。"""
    return {
        "name": (c.get("name") or "")[:200],
        "url": c.get("url", ""),
        "tags": c.get("tags") or [],
        "launched": c.get("launched", ""),
        "deadline": c.get("deadline", ""),
        "registration_deadline": c.get("registration-deadline", ""),
        "prize": c.get("prize", ""),
        "platform": c.get("platform", ""),
        "sponsor": (c.get("sponsor") or "")[:150],
        "conference": c.get("conference", ""),
        "source_id": META["id"],
    }

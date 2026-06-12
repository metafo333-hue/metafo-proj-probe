"""governor · 统一取数入口（S1 施工件）。

所有外部取数请求必须经此入口，实现：
  - kind 自动检测（article / document / api）
  - 路由到对应 datasource 模块的 module-level 函数
  - 统一输出 schema：{kind, title, text, url, extractor, cost_hint, ...}
  - 合规占位：datasource key 未就绪时返回 needs_authorized_api=True（不自建爬取）

调用方（pipeline 等）改用 governor.fetch_one(url, kind_hint) 替代直接 import l0。
"""
from __future__ import annotations

import os
import re
from typing import Any

# 已批量合规激活的 datasource 适配器（公开 API · 无需 R1）
_PUBLIC_DOMAINS: dict[str, str] = {
    "wikipedia.org":      "wikipedia",
    "arxiv.org":          "arxiv",
    "archive.org":        "webarchive",
    "web.archive.org":    "webarchive",
    "github.com":         "github_src",
    "edgar.sec.gov":      "edgar",
    "efts.sec.gov":       "edgar",
    "opencorporates.com": "opencorporates",
    "virustotal.com":     "virustotal",
    "osv.dev":            "osv",
}

_DOC_EXTS = (".pdf", ".docx", ".pptx", ".xlsx", ".doc", ".ppt", ".xls")


def _detect_kind(url: str) -> str:
    """根据 URL 推断资源类型。"""
    low = url.lower().split("?")[0]
    if any(low.endswith(ext) for ext in _DOC_EXTS):
        return "document"
    for domain in _PUBLIC_DOMAINS:
        if domain in low:
            return "api"
    return "article"


def _domain_key(url: str) -> str | None:
    """从 URL 提取匹配 _PUBLIC_DOMAINS 的 domain 键。"""
    low = url.lower()
    for domain in _PUBLIC_DOMAINS:
        if domain in low:
            return domain
    return None


def fetch_one(url: str, kind_hint: str | None = None) -> dict[str, Any]:
    """统一取数入口。

    Parameters
    ----------
    url       : 目标 URL
    kind_hint : 可选强制指定 kind（article / document / api）

    Returns
    -------
    标准结果 dict：
      {kind, title, text, url, extractor, ...}
      或 {kind, needs_authorized_api: True, ...}（合规占位）
      或 {kind, failed: True, error: str}
    """
    kind = kind_hint or _detect_kind(url)
    domain_key = _domain_key(url)

    # ── api 路径：走 datasource 模块 ──────────────────────────────────────
    if kind == "api" and domain_key:
        src_id = _PUBLIC_DOMAINS[domain_key]
        return _fetch_via_datasource(url, src_id, kind)

    # ── document 路径 ─────────────────────────────────────────────────────
    if kind == "document":
        try:
            from app.extractors.document import extract as extract_doc
            data = extract_doc(url)
            return _normalize(data, kind, url, "doc-extractor")
        except Exception as e:
            return {"kind": kind, "failed": True, "error": str(e), "url": url}

    # ── article 路径（含降级 article 的 api fallback）─────────────────────
    try:
        from app.extractors.article import extract as extract_art
        data = extract_art(url)
        return _normalize(data, kind, url, "article-extractor")
    except Exception as e:
        return {"kind": kind, "failed": True, "error": str(e), "url": url}


def _fetch_via_datasource(url: str, src_id: str, kind: str) -> dict[str, Any]:
    """走 datasource 模块取数，key 未就绪时返回合规占位。"""
    try:
        import importlib
        mod = importlib.import_module(f"app.datasources.public.{src_id}")

        # 检查 key 是否就绪（有 key_env 的模块必须有 key）
        meta = getattr(mod, "META", {})
        key_env = meta.get("key_env", "")
        if key_env and not os.getenv(key_env, "").strip():
            return {
                "kind": kind, "url": url,
                "needs_authorized_api": True,
                "src_id": src_id,
                "_compliance": f"环境变量 {key_env} 未配置（ledger gate19 待授权）",
            }

        # 路由到对应模块函数
        result = _dispatch(mod, src_id, url)
        if result is None:
            return {
                "kind": kind, "url": url,
                "needs_authorized_api": True,
                "src_id": src_id,
                "_error": "dispatch returned None",
            }
        if isinstance(result, list):
            result = result[0] if result else {}
        if not result:
            return {"kind": kind, "url": url, "failed": True, "src_id": src_id,
                    "error": "empty result from adapter"}

        return _normalize(result, kind, url, src_id)

    except Exception as e:
        return {
            "kind": kind, "url": url,
            "needs_authorized_api": True,
            "src_id": src_id,
            "_error": str(e),
            "_compliance": "适配器异常 · 合规占位（不自建爬取）",
        }


def _dispatch(mod: Any, src_id: str, url: str) -> Any:
    """按 src_id 将 URL 路由到模块内具体函数。"""
    if src_id == "github_src":
        return mod.repo_info(url)

    if src_id == "wikipedia":
        m = re.search(r"/wiki/([^?#]+)", url)
        title = m.group(1).replace("_", " ") if m else url
        return mod.summary(title)

    if src_id == "arxiv":
        m = re.search(r"/abs/([0-9.]+)", url)
        query = m.group(1) if m else url
        results = mod.search(query, max_results=1)
        return results[0] if results else {}

    if src_id == "webarchive":
        return mod.availability(url)

    if src_id == "edgar":
        m = re.search(r"CIK[=/](\d+)", url, re.IGNORECASE)
        if not m:
            m = re.search(r"/(\d{10})/", url)
        cik = m.group(1) if m else ""
        if not cik:
            return None
        result = mod.company_filings(cik)
        return result

    if src_id == "opencorporates":
        return mod.get_company(url)

    if src_id == "virustotal":
        return mod.lookup_url(url)

    if src_id == "osv":
        if "/vuln/" in url:
            vuln_id = url.rstrip("/").rsplit("/", 1)[-1]
            return mod.by_id(vuln_id)
        return None

    return None


def _normalize(data: dict, kind: str, url: str, extractor: str) -> dict[str, Any]:
    """把各 extractor 输出统一成 governor 标准 schema。"""
    return {
        "kind":      kind,
        "url":       url,
        "title":     data.get("title", ""),
        "text":      data.get("text", data.get("content", data.get("description", ""))),
        "extractor": extractor,
        "cost_hint": data.get("cost_hint", {}),
        "_raw_keys": list(data.keys()),
    }

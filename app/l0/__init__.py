"""L0 自有链路包装 · 链接归类 + 走 datasources 合规层取数。

⚠️ 数据来源铁律(2026-06-03 合规整改):
- 禁自建爬虫/绕反爬。原 scripts(trafilatura/yt-dlp/Playwright/MediaCrawler)已停用,
  移至 `_deprecated/scripts/` 仅留参考,**不再 import**。
- 取数只走 `app.datasources` 第三方授权 API 适配层(过标准19核验)。
- 当前无已核验合规源 → extract_public 返回 needs_authorized_api 合规占位。
- 原料进结论出:适配器只取标准化元数据,加工成结论由 deep_probe 负责。
"""
from __future__ import annotations

import re
from typing import Any

from app.datasources import registry

# 链接归类正则(纯 URL 判别 · 不发请求、不爬取)
_VIDEO = re.compile(r"(douyin\.com|iesdouyin\.com|bilibili\.com|b23\.tv|"
                    r"youtube\.com|youtu\.be|kuaishou\.com)")
_SOCIAL = re.compile(r"(xiaohongshu\.com|xhslink\.com|weibo\.(com|cn)|m\.weibo\.cn|twitter\.com|x\.com)")
_DOC = re.compile(r"(\.pdf($|\?)|github\.com|arxiv\.org|readthedocs)")
# 直链公开音频/图片（非平台·非反爬）→ 走 extractors 本地 ASR/OCR（合规：等同抓公开网页文件）
_AUDIO = re.compile(r"\.(mp3|wav|m4a|aac|flac|ogg|opus)($|\?)")
_IMAGE = re.compile(r"\.(jpe?g|png|webp|bmp|tiff?|gif)($|\?)")
_URL_RE = re.compile(r"https?://[^\s一-鿿]+")


def find_url(instruction: str | None, context: dict | None,
             attachments: list | None) -> str | None:
    """从 context.url / attachments / instruction 三处取链接(纯解析)。"""
    if context and context.get("url"):
        return context["url"]
    for a in attachments or []:
        if isinstance(a, str) and a.startswith("http"):
            return a
    m = _URL_RE.search(instruction or "")
    return m.group(0) if m else None


def classify(url: str) -> str:
    """链接归类 article/doc/video/social/audio/image(纯正则 · 不爬取)。

    平台域名优先(video/social→datasources)；其后才判直链文件后缀(audio/image/doc→extractors)，
    确保"抖音视频链接"不会因含 .mp4 误入本地提取层(平台数据须走授权 API)。
    """
    u = (url or "").lower()
    if _VIDEO.search(u):
        return "video"
    if _SOCIAL.search(u):
        return "social"
    if _AUDIO.search(u):
        return "audio"
    if _IMAGE.search(u):
        return "image"
    if _DOC.search(u):
        return "doc"
    return "article"


def extract_public(url: str) -> dict[str, Any]:
    """A 线取数 · 分两条合规路径：

    - article/doc（公开网页/文档）→ extractors 技术合规开源库直接嵌入（铁律③），真出数据；
    - video/social（五平台）→ datasources 第三方授权 API；无已核验源 → needs_authorized_api 占位。
    """
    kind = classify(url)

    # 路径①：技术合规开源库直接嵌入（公开内容 · 含直链音频/图片本地 ASR/OCR）
    if kind in ("article", "doc", "audio", "image"):
        from app.extractors import get_extractor
        ex = get_extractor(kind)
        if ex is not None:
            d = ex.extract(url)
            if d.get("failed"):
                return {"kind": kind, "failed": True,
                        "extractor": ex.lib, "reason": d.get("reason", "")}
            return {"kind": kind, "title": d.get("title", ""), "text": d["text"],
                    "extractor": d.get("extractor", ex.lib), "sources": [url]}

    # 路径②：五平台数据走第三方商业 API（probe 只调接口·不主动爬取）
    adapter = registry.get_adapter(kind)
    if adapter is None:
        return {"kind": kind, "needs_authorized_api": True}
    data = adapter.fetch_metadata(url, kind)
    if data.get("_needs_key"):
        return {"kind": kind, "needs_authorized_api": True, "adapter": adapter.source_id,
                "note": f"已接 {adapter.source_id} 适配器(覆盖五平台)·待配 API key(R8 注册 + R1 付费授权)"}
    if data.get("_error"):
        return {"kind": kind, "failed": True,
                "extractor": adapter.source_id, "reason": data["_error"]}
    if not data or not data.get("text"):
        return {"kind": kind, "failed": True, "extractor": adapter.source_id}
    return {
        "kind": kind,
        "title": data.get("title", ""),
        "text": data.get("text", ""),        # 标准化元数据(非原始全文直吐)
        "extractor": adapter.source_id,
        "sources": [url],
        "metadata": data.get("metadata"),
        "cost_hint": adapter.cost_hint(),
    }


def deep_probe(url: str, public: dict) -> dict[str, Any]:
    """B 线深探 · 原料进结论出 · D1真相核查 + D2结构拆解 + D7二创路径。

    数据层：trafilatura 正文(已有) + AnySearch 联网核查(免费1000次/天)
    分析层：LLM(DeepSeek/Qwen) 运行 D1/D2/D7
    结论层：A-D 评级 + 三步行动 + 借换串二创方案
    供 guards 三层深度线裁剪（public评级/preview+结构/paid完整）
    """
    from app.services import llm
    from app.datasources import anysearch as asearch

    text = public.get("text", "")
    title = public.get("title", "") or url
    wordcount = len(text)
    llm_ok = llm.is_available()

    # ── D1 真相核查（AnySearch联网，免费）──────────────────
    fact_results: list[dict] = []
    d1: dict[str, Any] = {}
    if len(text) >= 200:
        # 用标题+首句搜索权威来源
        first_sentence = text[:80].split("。")[0]
        search_q = f"{title} {first_sentence}"
        fact_results = asearch.search(search_q, max_results=4)
        d1 = llm.fact_check(text, fact_results) if llm_ok else {
            "claims": [], "overall_credibility": "未评估（LLM 未接入）",
            "aigc_flag": False, "_stub": True
        }

    # ── D2 结构拆解（LLM）────────────────────────────────
    d2 = llm.analyze_structure(text, title) if llm_ok else llm._stub_structure(title, text)

    # ── D7 二创路径（LLM，基于D2结论）───────────────────
    d7 = llm.generate_recreation_paths(d2, title, _rate(d2, wordcount)) if llm_ok else llm._stub_recreation()

    # ── 综合评级（A/B/C/D）───────────────────────────────
    rating = _rate(d2, wordcount, d1)
    is_stub = d2.get("_stub", False) and d7.get("_stub", False)

    return {
        "rating": rating,
        "_stub": is_stub,
        "_llm": llm_ok,
        "headline": f"{title[:40] or '该链接'} · 初评 {rating}",
        # D2 结构
        "structure_formula": d2.get("structure_formula", ""),
        "hook": d2.get("hook", {}),
        "body_nodes": d2.get("body_nodes", []),
        "cta": d2.get("cta", {}),
        "reuse_tags": d2.get("reuse_tags", []),
        # D7 二创
        "recreation": d7,
        # D1 真相核查
        "fact_check": d1,
        "fact_sources": [{"title": r.get("title"), "url": r.get("url")} for r in fact_results[:3]],
        # D5/D6 占位（需 TikHub key）
        "competitors": "竞品横评（待 TikHub key 接入五平台数据）",
        "publisher": "发布者画像（待 TikHub key 接入账号数据）",
        "_wordcount": wordcount,
    }


def _rate(d2: dict, wordcount: int, d1: dict | None = None) -> str:
    """综合 D1/D2 出 A/B/C/D 评级。"""
    # 有失实声称 → 不超过 C
    if d1:
        failed = [c for c in d1.get("claims", []) if c.get("verdict") == "❌"]
        risk = d1.get("overall_credibility", "")
        if risk == "高风险" or len(failed) >= 2:
            return "C"
    # 有清晰结构公式且字数充足 → B 以上
    has_formula = bool(d2.get("structure_formula") and "待" not in d2.get("structure_formula", ""))
    if has_formula and wordcount > 1000:
        return "A"
    if has_formula or wordcount > 500:
        return "B"
    return "C"

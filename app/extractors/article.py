"""公开网页文章正文提取 · trafilatura（主选，F≈0.95 梯队最高）。

技术合规（铁律③）：仅提取公开网页正文，不绕反爬、不碰五平台。
降级备选 newspaper4k（MIT）可后续加（datasource-selection-v1 报告推荐）。
注：后续可加 robots.txt 尊重；当前仅处理 classify 判为 article 的非五平台公开网页。
"""
from __future__ import annotations

import json
from typing import Any

from app.extractors.base import Extractor


class ArticleExtractor(Extractor):
    kind = "article"
    lib = "trafilatura"

    def extract(self, url: str) -> dict[str, Any]:
        try:
            import trafilatura
        except ImportError:
            return {"failed": True, "reason": "trafilatura 未安装"}
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {"failed": True, "reason": "fetch_url 返回空（反爬/无网/404）"}
        data = trafilatura.extract(downloaded, output_format="json", with_metadata=True)
        if not data:
            return {"failed": True, "reason": "trafilatura 提取空"}
        d = json.loads(data)
        text = d.get("text", "")
        if len(text) < 200:
            return {"failed": True, "reason": f"正文过短（{len(text)} 字）"}
        return {"title": d.get("title", ""), "text": text, "extractor": "trafilatura"}

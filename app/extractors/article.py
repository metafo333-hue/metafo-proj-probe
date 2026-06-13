"""公开网页文章正文提取 · trafilatura（主选，F≈0.95 梯队最高）。

技术合规（铁律③）：仅提取公开网页正文，不绕反爬、不碰五平台。
降级备选 newspaper4k（MIT）可后续加（datasource-selection-v1 报告推荐）。
注：后续可加 robots.txt 尊重；当前仅处理 classify 判为 article 的非五平台公开网页。
"""
from __future__ import annotations

import json
import os
from typing import Any

from app.extractors.base import Extractor

# 抓取超时（秒）：海外/不可达站点快速失败,不挂死 task（默认 12s·可 env 调）
_FETCH_TIMEOUT = int(os.getenv("PROBE_FETCH_TIMEOUT", "12"))
# 出境代理（probe-a mihomo·海外站经此·未配则直连·境内站无需）
_HTTP_PROXY = os.getenv("PROBE_FETCH_PROXY", "")


class ArticleExtractor(Extractor):
    kind = "article"
    lib = "trafilatura"

    def extract(self, url: str) -> dict[str, Any]:
        try:
            import trafilatura
        except ImportError:
            return {"failed": True, "reason": "trafilatura 未安装"}
        # 抓取/解析解耦：httpx 抓 HTML（原生支持代理+超时·trafilatura 自身 urllib3 不读 proxy env）,
        # 再交 trafilatura.extract 纯解析（无网络）。海外站经 mihomo 代理·境内 mihomo 自动直连。
        try:
            import httpx
            headers = {"User-Agent": "Mozilla/5.0 (compatible; probe-intel/1.0; +https://metafoclaw.com)"}
            client_kw: dict[str, Any] = {"timeout": _FETCH_TIMEOUT, "follow_redirects": True, "headers": headers}
            if _HTTP_PROXY:
                client_kw["proxy"] = _HTTP_PROXY
            with httpx.Client(**client_kw) as c:
                resp = c.get(url)
                if resp.status_code >= 400:
                    return {"failed": True, "reason": f"HTTP {resp.status_code}"}
                downloaded = resp.text
        except Exception as e:
            return {"failed": True, "reason": f"抓取失败（{type(e).__name__}·超时/反爬/无网）"}
        if not downloaded:
            return {"failed": True, "reason": "抓取返回空（反爬/无网/404/超时）"}
        data = trafilatura.extract(downloaded, output_format="json", with_metadata=True)
        if not data:
            return {"failed": True, "reason": "trafilatura 提取空"}
        d = json.loads(data)
        text = d.get("text", "")
        if len(text) < 200:
            return {"failed": True, "reason": f"正文过短（{len(text)} 字）"}
        return {"title": d.get("title", ""), "text": text, "extractor": "trafilatura"}

"""字幕文件 → 纯文本 · .srt / .vtt（零依赖·D-Use 媒体补全 2026-06-14）。

技术合规（铁律③）：仅解析「直链公开字幕 / 用户上传字幕」。纯文本解析、无网络爬取、无 ML。
轻量本地（prefer_remote=False）——不走 ufo 提取服务。
"""
from __future__ import annotations

import os
import re
from typing import Any

from app.extractors.base import Extractor

_FETCH_TIMEOUT = int(os.getenv("PROBE_FETCH_TIMEOUT", "15"))
_HTTP_PROXY = os.getenv("PROBE_FETCH_PROXY", "")
# 时间轴行：SRT "00:00:01,000 --> 00:00:04,000" / VTT 用 "."
_TS_LINE = re.compile(r"^\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}\s*-->")
_SEQ_LINE = re.compile(r"^\d+$")           # SRT 序号行
_TAG = re.compile(r"<[^>]+>")               # VTT 内联标签 <c>/<i> 等


class SubtitleExtractor(Extractor):
    kind = "subtitle"
    lib = "(stdlib)"
    import_name = ""          # 无外部依赖
    license = "—"

    def extract(self, url: str) -> dict[str, Any]:
        raw = self._read(url)
        if isinstance(raw, dict):
            return raw
        text = self._parse(raw)
        if len(text.strip()) < 1:
            return {"failed": True, "reason": "字幕解析为空"}
        return {"title": "", "text": text, "extractor": "subtitle"}

    def _parse(self, raw: str) -> str:
        lines_out: list[str] = []
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.upper() == "WEBVTT" or s.startswith("NOTE"):
                continue
            if _TS_LINE.match(s) or _SEQ_LINE.match(s):
                continue
            s = _TAG.sub("", s)              # 去 VTT 内联标签
            if s:
                lines_out.append(s)
        # 去相邻重复（滚动字幕常重复同句）
        deduped: list[str] = []
        for s in lines_out:
            if not deduped or deduped[-1] != s:
                deduped.append(s)
        return "\n".join(deduped)

    def _read(self, url: str):
        if os.path.isfile(url):
            try:
                with open(url, encoding="utf-8", errors="replace") as f:
                    return f.read()
            except OSError as e:
                return {"failed": True, "reason": f"读字幕文件失败：{e}"}
        try:
            import httpx
        except ImportError:
            return {"failed": True, "reason": "httpx 未安装"}
        kw: dict[str, Any] = {"timeout": _FETCH_TIMEOUT, "follow_redirects": True}
        if _HTTP_PROXY:
            kw["proxy"] = _HTTP_PROXY
        try:
            r = httpx.get(url, **kw)
            r.raise_for_status()
            return r.text
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"抓取字幕失败：{e}"}

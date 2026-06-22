"""文档/PDF/Office → Markdown · markitdown(轻量主选) + Docling(高精度可选·D-Use)。

技术合规（铁律③）：公开文档转换。GitHub 仓库走 raw README 快路径（无需渲染）。
高精度（复杂表格/公式/版面）走 Docling(MIT·61k★·内置 ASR)，env `PROBE_DOC_BACKEND=docling`
开启（默认 markitdown 不变·保持现行为·切换可回滚）。两者皆 MIT，无许可证陷阱。
"""
from __future__ import annotations

import os
import subprocess
from typing import Any

from app.extractors.base import Extractor

# 文档后端：markitdown(默认·轻量) | docling(高精度·重依赖·须先装)
_DOC_BACKEND = os.getenv("PROBE_DOC_BACKEND", "markitdown").lower()


class DocumentExtractor(Extractor):
    kind = "doc"
    lib = "markitdown"
    import_name = "markitdown"
    license = "MIT"

    def extract(self, url: str) -> dict[str, Any]:
        # GitHub 仓库主页 → raw README 快路径（与后端无关）
        if "github.com" in url and "/blob/" not in url and url.count("/") <= 4:
            raw = url.rstrip("/") + "/raw/HEAD/README.md"
            r = subprocess.run(["curl", "-sL", "--max-time", "30", raw],
                               capture_output=True, text=True)
            if r.returncode == 0 and len(r.stdout.strip()) >= 100:
                return {"title": "", "text": r.stdout, "extractor": "github-raw"}

        # 高精度后端（opt-in）→ Docling；失败回落 markitdown
        if _DOC_BACKEND == "docling":
            d = self._docling(url)
            if not d.get("failed"):
                return d
            # Docling 失败 → 回落 markitdown（不直接报错,留降级链）

        return self._markitdown(url)

    def _markitdown(self, url: str) -> dict[str, Any]:
        try:
            from markitdown import MarkItDown
        except ImportError:
            return {"failed": True, "reason": "markitdown 未安装"}
        try:
            result = MarkItDown().convert(url)
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"markitdown 转换失败：{e}"}
        text = getattr(result, "text_content", "") or ""
        if len(text) < 100:
            return {"failed": True, "reason": "转换内容过短"}
        return {"title": getattr(result, "title", "") or "", "text": text,
                "extractor": "markitdown"}

    def _docling(self, url: str) -> dict[str, Any]:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError:
            return {"failed": True, "reason": "docling 未安装"}
        try:
            result = DocumentConverter().convert(url)
            text = result.document.export_to_markdown()
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"docling 转换失败：{e}"}
        if len(text) < 100:
            return {"failed": True, "reason": "docling 内容过短"}
        return {"title": "", "text": text, "extractor": "docling"}

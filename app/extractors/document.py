"""文档/PDF/Office → Markdown · markitdown（MIT，微软，轻量主选）。

技术合规（铁律③）：公开文档转换。GitHub 仓库走 raw README 快路径（无需渲染）。
高精度场景（复杂表格/公式/版面）可后续加 Docling（MIT，重依赖），见 datasource-selection-v1 报告。
"""
from __future__ import annotations

import subprocess
from typing import Any

from app.extractors.base import Extractor


class DocumentExtractor(Extractor):
    kind = "doc"
    lib = "markitdown"

    def extract(self, url: str) -> dict[str, Any]:
        # GitHub 仓库主页 → raw README 快路径
        if "github.com" in url and "/blob/" not in url and url.count("/") <= 4:
            raw = url.rstrip("/") + "/raw/HEAD/README.md"
            r = subprocess.run(["curl", "-sL", "--max-time", "30", raw],
                               capture_output=True, text=True)
            if r.returncode == 0 and len(r.stdout.strip()) >= 100:
                return {"title": "", "text": r.stdout, "extractor": "github-raw"}
        # 通用文档（PDF/Office/HTML）→ markitdown
        try:
            from markitdown import MarkItDown
        except ImportError:
            return {"failed": True, "reason": "markitdown 未安装"}
        try:
            result = MarkItDown().convert(url)
        except Exception as e:
            return {"failed": True, "reason": f"markitdown 转换失败：{e}"}
        text = getattr(result, "text_content", "") or ""
        if len(text) < 100:
            return {"failed": True, "reason": "转换内容过短"}
        return {"title": getattr(result, "title", "") or "", "text": text,
                "extractor": "markitdown"}

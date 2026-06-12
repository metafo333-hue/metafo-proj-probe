"""技术合规提取器（铁律③）· 处理公开内容/自有授权素材的开源库，可直接嵌入。

与 datasources 的区别：
- datasources = 第三方授权 API（五平台反爬数据，须过标准19核验，当前无源 → 占位）
- extractors = 技术「非违法」开源库（公开网页正文提取 / 文档转换 / 授权音频 ASR），直接嵌入无须授权

合规边界：只处理「公开网页文章 / 公开文档 / 自有或授权音频」。不得用于五平台（抖音/小红书/微博/B站/快手——
classify 已将其归 video/social → 走 datasources 占位，不进本层）。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Extractor(ABC):
    kind: str = ""        # article / doc / asr
    lib: str = ""         # 所用开源库

    @abstractmethod
    def extract(self, url: str) -> dict[str, Any]:
        """→ {title, text, extractor} 或 {failed: True, reason}。"""
        raise NotImplementedError

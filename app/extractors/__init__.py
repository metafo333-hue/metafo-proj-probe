"""技术合规提取层 · 自动发现（D-Ext 2026-06-14）。

铁律③「技术非违法开源库可直接嵌入」——处理公开网页/文档/授权音频，无须第三方授权。
五平台数据不走本层（见 base 合规边界 + datasources 占位）。

在役提取器由 _registry.autodiscover() 扫包自动注册：
- article (trafilatura) / doc (markitdown)
- 新增 audio/image 等 = 新建模块写 Extractor 子类即自动入册，无需改本文件。
"""
from app.extractors._registry import (
    get_extractor,
    health_report,
    list_extractors,
)

__all__ = ["get_extractor", "list_extractors", "health_report"]

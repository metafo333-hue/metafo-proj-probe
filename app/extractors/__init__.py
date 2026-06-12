"""技术合规提取层 · article(trafilatura) / doc(markitdown)。

铁律③「技术非违法开源库可直接嵌入」——处理公开网页/文档/授权音频，无须第三方授权。
五平台数据不走本层（见 base 合规边界 + datasources 占位）。
"""
from app.extractors.article import ArticleExtractor
from app.extractors.document import DocumentExtractor

_EXTRACTORS = {
    "article": ArticleExtractor(),
    "doc": DocumentExtractor(),
}


def get_extractor(kind: str):
    """取技术合规提取器；kind 不在 article/doc 则 None（交 datasources）。"""
    return _EXTRACTORS.get(kind)

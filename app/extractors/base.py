"""技术合规提取器（铁律③）· 处理公开内容/自有授权素材的开源库，可直接嵌入。

与 datasources 的区别：
- datasources = 第三方授权 API（五平台反爬数据，须过标准19核验，当前无源 → 占位）
- extractors = 技术「非违法」开源库（公开网页正文提取 / 文档转换 / 授权音频 ASR），直接嵌入无须授权

合规边界：只处理「公开网页文章 / 公开文档 / 自有或授权音频」。不得用于五平台（抖音/小红书/微博/B站/快手——
classify 已将其归 video/social → 走 datasources 占位，不进本层）。
"""
from __future__ import annotations

import importlib
from abc import ABC, abstractmethod
from typing import Any


class Extractor(ABC):
    """技术合规提取器基类 · 类级 manifest（D-Ext 扩展性地基 2026-06-14）。

    加新提取器 = 新建 <kind>.py 写 Extractor 子类、填 kind/lib/license，
    由 _registry.autodiscover() 自动注册——无需改 __init__.py 或注册表（"加件不改架构"）。
    """

    # ── 路由 ──────────────────────────────────────────────────────────────
    kind: str = ""            # article / doc / audio / image — 路由键(对应 classify 输出)
    lib: str = ""             # 所用开源库(显示用)

    # ── 类级 manifest（供健康看板 / MetaFlow 能力过滤 / CI 合规扫）────────────
    import_name: str = ""     # 健康检查用的 import 名(留空则取 lib);多库用主库名
    license: str = ""         # 库许可证(商用合规可查·如 Apache-2.0 / MIT)
    requires_gpu: bool = False # 是否需 GPU(audio/image 提取器→True·调度到 ufo)
    version: str = "1.0.0"
    _WORKING: bool = True      # False = 停用不删代码(yt-dlp 范式·保留可 grep)

    @classmethod
    def handles(cls, kind: str) -> bool:
        """本提取器是否处理该 kind（且在役）。"""
        return cls._WORKING and bool(cls.kind) and cls.kind == kind

    @abstractmethod
    def extract(self, url: str) -> dict[str, Any]:
        """→ {title, text, extractor} 或 {failed: True, reason}。"""
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        """默认健康检查：依赖库可 import 即 ok。子类可覆盖做更深探活。"""
        name = self.import_name or self.lib
        if not name:
            return {"kind": self.kind, "ok": True, "lib": self.lib, "note": "无外部库依赖"}
        try:
            importlib.import_module(name)
            return {"kind": self.kind, "ok": True, "lib": self.lib}
        except Exception as e:  # noqa: BLE001 — 健康检查须吞所有异常,只报状态
            return {"kind": self.kind, "ok": False, "lib": self.lib, "error": str(e)}

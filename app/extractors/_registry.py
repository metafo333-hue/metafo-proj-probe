"""提取器自动发现注册 · D-Ext 扩展性地基（2026-06-14）。

扫 app.extractors 包内每个模块的 Extractor 子类（_WORKING=True），按 kind 注册实例。
加新提取器 = 新建 <kind>.py 写子类填 kind/lib，跑起来即被发现——无需改本文件或 __init__.py。

安全（D2 反例警示）：仅 iter_modules 扫包内一处，**不**扫 PYTHONPATH / 用户目录 / zip，
防 probe-a（有公网 EIP）被任意文件注入提取器代码。
"""
from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.extractors.base import Extractor

# 单进程缓存（发现一次）。kind → Extractor 实例。
_registry: dict[str, "Extractor"] = {}
_discovered = False


def _discover() -> dict[str, "Extractor"]:
    global _discovered
    if _discovered:
        return _registry

    from app.extractors.base import Extractor

    import app.extractors as _pkg

    for _finder, modname, _ispkg in pkgutil.iter_modules(_pkg.__path__):
        # 跳过基类 / 私有模块（_registry 自身、__init__）
        if modname == "base" or modname.startswith("_"):
            continue
        mod = importlib.import_module(f"app.extractors.{modname}")
        for attr in vars(mod).values():
            if (isinstance(attr, type)
                    and issubclass(attr, Extractor)
                    and attr is not Extractor
                    and getattr(attr, "_WORKING", True)):
                inst = attr()
                if inst.kind:
                    _registry[inst.kind] = inst  # 同 kind 后发现者覆盖(插件优先·yt-dlp 范式)

    _discovered = True
    return _registry


def get_extractor(kind: str) -> "Extractor | None":
    """取处理该 kind 的在役提取器；无则 None（上层交 datasources）。"""
    return _discover().get(kind)


def list_extractors() -> dict[str, "Extractor"]:
    """全部在役提取器（kind → 实例）· 供健康看板 / 能力过滤。"""
    return dict(_discover())


def health_report() -> list[dict]:
    """各提取器依赖健康一览 · 供 selftest / 运维看板。"""
    return [ex.health_check() for ex in _discover().values()]

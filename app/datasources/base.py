"""数据源适配器抽象 · 第三方授权 API 统一接口。

每个子类适配一个合规数据供应商(如 TikHub)。接入前必须:
1. 供应商有数据资质/授权(留台账 ledger.yaml)
2. 走官方授权 API,禁逆向/抓包/模拟登录/群控
3. 过标准19核验,ledger status=active 才被 registry 放行
4. R1: API 付费 → 报价 + 元东方密码授权后才接
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataSourceAdapter(ABC):
    """第三方授权数据源适配器基类。"""

    source_id: str = ""                       # 台账唯一 id(对应 ledger.sources.<id>)
    vendor: str = ""                          # 供应商名
    qualified: bool = False                   # 过标准19 + R1 授权后置 True
    supported_kinds: tuple[str, ...] = ()     # article / doc / video / social

    @abstractmethod
    def fetch_metadata(self, url: str, kind: str) -> dict[str, Any]:
        """调第三方授权 API 取**公开元数据**(标准化)。

        返回 {title, text(标准化摘要/元数据·非原始全文直吐), source_id, ...}。
        禁:返回第三方原始全文/封面二进制(原料进结论出 由上层加工)。
        """
        raise NotImplementedError

    def cost_hint(self) -> dict[str, float]:
        """本次调用的数据成本(喂 billing.premium_data)。"""
        return {"premium_data": 0.0}

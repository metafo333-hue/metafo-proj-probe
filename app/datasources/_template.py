"""第三方授权 API 适配器模板 · 复制改名实现(如 tikhub.py)后在 registry._ADAPTERS 注册。

接入前必须(probe 数据来源铁律 + 标准19):
1. 供应商有数据资质/授权(留台账 ledger.yaml)
2. 走官方授权 API,禁逆向/抓包/模拟登录/群控/换代理对抗
3. 过标准19核验,ledger status=active
4. R1: API 付费 → 报价 + 元东方密码授权后才接
"""
from __future__ import annotations

from typing import Any

from app.datasources.base import DataSourceAdapter


class TemplateAdapter(DataSourceAdapter):
    source_id = "template"
    vendor = "待选型(TikHub / 新榜 / 飞瓜)"
    qualified = False                 # 过标准19 + R1 授权后置 True
    supported_kinds = ()              # 如 ("video", "social")

    def fetch_metadata(self, url: str, kind: str) -> dict[str, Any]:
        raise NotImplementedError(
            "第三方授权 API 未接入(需选型 + R1 付费授权 + 标准19核验)")

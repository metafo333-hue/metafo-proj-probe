"""probe 数据源适配层 · 只接第三方授权 API(不自建爬取/不绕反爬)。

铁律(probe 数据来源铁律 2026-06-03):
- 禁自建爬虫、禁 Selenium/抓包/逆向签名/模拟登录。
- 只用过标准19核验的第三方合规授权 API(TikHub/新榜/飞瓜等),留台账 ledger.yaml。
- 原料进结论出:适配器只取标准化元数据,加工成结论由上层负责。

见 base(抽象)/ registry(核验门)/ ledger.yaml(台账)/ catalog(多域查询)。
"""
from app.datasources.registry import GATE_19, gate_passed, get_adapter  # noqa: F401
from app.datasources import catalog  # noqa: F401

# probe 数据来源合规整改 · HANDOFF（上报母体合规官）

> 日期：2026-06-03 · 触发：母体下发 probe 数据来源合规铁律
> 依据红线第 8 条「自己爬/逆向/绕反爬 → 拒绝、写 handoff、上报合规官、改第三方授权 API」

## 一、发现的违规（整改前）

probe 原 L0（迁自 link-intel skill）= **纯自建爬取/绕反爬，零第三方合规 API**：

| 原实现 | 违反铁律 |
|--------|---------|
| `extract.py` trafilatura/crawl4ai/jina 爬正文 | 第1条 不爬取 |
| `subtitle.py` yt-dlp 下视频/字幕 | 第3条 + 爬视频平台 |
| README Playwright 拦截抖音 CDN | 第3条 严禁 Selenium/抓包/逆向签名 |
| `extract.py` MediaCrawler 小红书/微博 | 第1条 robots/ToS 禁 + 反爬 |

## 二、已整改（本轮 · 停违规 + 搭合规骨架）

- ✅ 违规脚本全停用隔离 → `app/l0/_deprecated/scripts/`（留参考，不再 import）
- ✅ 新建 `app/datasources/` 第三方授权 API 适配层：`base`（抽象）+ `registry`（标准19核验门）+ `ledger.yaml`（台账）+ `_template`
- ✅ `app/l0/__init__.py` 重写：归类用纯正则（不发请求），取数走 datasources；无已核验源 → 返回 `needs_authorized_api` 合规占位（**不回退自建爬取**）
- ✅ guards 补个保法红线常量（普通≥5000/敏感≥500）；manifest 补 `data_policy` 合规声明
- ✅ 实测：pytest **6/6** + selftest **11/11** + 停爬取验证（article/video/social 全返合规占位）

## 三、合规边界落地对照

| 铁律 | 落地 |
|------|------|
| 不自建爬虫/不爬取 | ✅ 自建爬取已停用隔离 |
| 只用第三方授权 API + 标准19核验 + 台账 | ✅ 适配层 + 核验门 + ledger 就绪（待填实源） |
| 严禁模拟登录/抓包/逆向/Selenium | ✅ Playwright/MediaCrawler 已停 |
| 原料进结论出 | ✅ 适配器只取标准化元数据；guards 禁直吐 + 三层深度线 |
| 个保法最小必要（≥5000/≥500） | ✅ 红线常量 + manifest 声明（仅公开元数据·不建档） |
| aigc_flag 必填 | ✅ guards 强校验 |
| 账号 0 接管 | ✅ 不持用户账号凭据（仅母体 user_token） |
| 频率/降级不对抗 | ✅ 写入 datasources/README 铁律 |

## 四、待办（需元东方/合规官决策 · probe 已就绪等输入）

1. **第三方数据源选型**：TikHub / 新榜 / 飞瓜 对比（覆盖/价格/资质/License/成熟度）→ 标准19核验
2. **R1 付费授权**：选定 API 付费 → 报价 + 元东方密码确认
3. **填台账**：`ledger.yaml` gate19 逐项核验 + status=active
4. **实接适配器**：复制 `_template.py` 实现，registry 注册
5. 完成后 probe 才能真正交付数据价值（当前为合规占位，契约/铁轨已验证）

> 现状：probe 契约层（4 暗号 + selftest 11/11）已过线，可作铁轨打通样本；**数据获取需第三方授权 API 接入后开通**。

# app/datasources — 第三方授权数据源适配层

> 2026-06-03 合规整改新增。probe **不自建爬虫、不绕反爬**，取数只走过标准19核验的第三方授权 API。

## 为什么有这层

原 L0（`_deprecated/scripts/`：trafilatura/yt-dlp/Playwright 抖音/MediaCrawler）= 自建爬取，违反数据来源铁律（五平台 robots/ToS 禁爬、禁逆向/抓包/模拟登录）。已**全部停用隔离**，改由本层对接第三方合规授权 API。

## 结构

| 文件 | 作用 |
|------|------|
| `base.py` | `DataSourceAdapter` 抽象（每供应商一子类） |
| `registry.py` | 标准19核验门 + `get_adapter(kind)`；无已核验源 → None |
| `ledger.yaml` | 数据源台账（资质/License/定价/gate19/status） |
| `_template.py` | 适配器模板（复制实现 tikhub.py 等） |

## 接入一个数据源（5 步）

1. 选型：候选 TikHub / 新榜 / 飞瓜（`candidates_to_evaluate`）
2. **R1 付费授权**：API 付费 → 报价 + 元东方密码确认
3. **标准19核验**：成熟/已验证/数据真实/资质/授权/License/安全 → 填 `ledger.yaml` gate19
4. 实现：复制 `_template.py` → `tikhub.py`，实现 `fetch_metadata`（只取公开元数据，不直吐原料）
5. 注册：`registry._ADAPTERS` 注册实例 + ledger `status: active`

## 铁律

- 原料进结论出：适配器只返标准化元数据，加工成结论由 `l0.deep_probe` 负责。
- 账号 0 接管：不持用户账号凭据。
- 频率/降级：守 API 配额，限流即停 + 通知运营，**不换代理对抗**。
- 个保法最小必要：仅公开元数据，不建个人档案（普通≥5000/敏感≥500 条入刑红线）。

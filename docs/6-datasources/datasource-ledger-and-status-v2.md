# probe 数据源台账与状态 v2.0

> v2.0（2026-06-22）：合并 activation-log v1.0 + integration-schedule v1.1，消除重复。
> **状态真源唯一**：`app/datasources/ledger.yaml`（代码侧）。本文补充"为什么"和历史背景，**不重定义 status**。
> 原两份文档（activation-log/integration-schedule）保留为只读历史参考，不再维护。

---

## 合规架构声明（必读）

probe 数据源分两类：

| 类别 | 定义 | 台账标记 |
|------|------|---------|
| **✅ 官方/开放授权** | 官方 API / 公开 oEmbed / CC 协议数据 | `access_type: free` 或 `free_with_key` |
| **⚠️ 合规债（第三方授权）** | 无官方 API 替代时，采购持牌第三方（TikHub 等） | `access_type: paid` + `compliance_debt: true` |

**国内社媒平台（抖音/快手/B站/小红书/微博）**：官方开放平台只给自有账号数据，任意达人竞品情报**官方零供给**。probe 以 TikHub 付费 API 担责，这是已知的合规债，由供应商担责"如何取数"，probe 只对"调用行为"负责。详见 [datasource-selfmedia-track-a-v1.md](../4-research/datasource-selfmedia-track-a-v1.md) §六。

---

## 一、当前总盘点

> 状态以 ledger.yaml 为准，本表为摘要快照（2026-06-22）。

| 分类 | 数量 | 说明 |
|------|------|------|
| ✅ **live** | ~50 外部源 + 3 内部 LLM | 代码 + 凭据（若需）+ 实测通过 |
| ⏳ **pending** | 2 | TikHub（已 key，待 probe-a 稳定）· JZL（已 key，微信视频号）|
| 🟡 **cataloged** | ~7 | 代码完整但需 probe-a 代理（Mac 直连受限）|
| ❌ **rejected** | ~55 | 逆向/违法/license 禁商用（永久拒用）|

---

## 二、关键数据源激活记录（历史·已稳定）

| 数据源 | 激活日期 | key 位置 | 备注 |
|--------|---------|---------|------|
| GitHub API | 2026-06-12 | `~/vault/credentials/github-pat.txt` | Bearer token |
| SearXNG（自部署）| 2026-06-12 | `PROBE_SEARXNG_BASE=http://100.64.0.8:8080` | ufo Docker |
| Edgar (SEC) | 2026-06-12 | 无需 key（User-Agent 已配）| 美股公司公告 |
| LiteLLM proxy | 2026-06-12 | `PROBE_LITELLM_KEY` in vault probe.env | ufo2:4000 |
| AlphaVantage | 2026-06-12 | `ALPHAVANTAGE_API_KEY` | 美股实时报价 |
| Finnhub | 2026-06-12 | `FINNHUB_API_KEY` | 40 位 key，从 dashboard 取 |
| FRED | 2026-06-12 | `FRED_API_KEY` | 元东方手动注册 |
| BLS | 2026-06-12 | `BLS_API_KEY` | 元东方手动注册+激活 |
| HuggingFace | 2026-06-12 | `HF_TOKEN` | 元东方手动注册 |
| VirusTotal | 2026-06-12 | `VIRUSTOTAL_KEY` | ledger=live，key 已配 |
| urlscan.io | 2026-06-12 | `URLSCAN_API_KEY` | reCAPTCHA 音频管线激活 |
| AbuseIPDB | 2026-06-12 | `ABUSEIPDB_API_KEY` | 已写入 probe-a |
| NVD CVE | 2026-06-12 | `NVD_API_KEY` | 已写入 probe-a |
| **TikHub** | **2026-06-14** | `PROBE_TIKHUB_KEY` in vault/api/datasource/social/ | 自媒体五平台·合规债·已接统计端点（抖音 play_count 修复 2026-06-22）|
| **JZL（微信视频号）**| **2026-06-20** | `PROBE_JZL_KEY` in vault/api/jzl-api-key.txt | 13 字段·play_count 永久缺口 |

---

## 三、待办队列（P1-P3）

### P1 · 需手动注册/配置
| 源 | 障碍 | 行动 |
|----|------|------|
| Pulsedive | Gmail 预抓取 token 消耗 | 个人浏览器手动注册 https://pulsedive.com/login |
| OpenCorporates | 免费 API 层取消（£2,250/年）| 待元东方拍板：公益申请/付费/搁置 |
| Semantic Scholar | 拒绝 Gmail 邮箱 | 需学术/企业邮箱，暂搁置 |

### P2 · 需自托管（按需）
| 源 | 部署 | 价值 |
|----|------|------|
| OpenSanctions + Yente | ufo Docker | 制裁数据（非商业免费）|
| SpiderFoot（**禁人物模式**）| ufo Docker | 资产侦察·限企业主体 |

### P3 · 付费·待元东方 R1 密码授权
| 优先 | 源 | 月成本 | 价值 |
|------|----|-------|------|
| ★1 | 天眼查/企查查 API | ¥按量 | 国内企业风险全维 |
| ★2 | Shodan 完整版 | $49 一次性 | 性价比高 |
| ★3 | AlphaVantage Premium | $30 | 美股深度 |
| ★4 | 蜻蜓/喜马拉雅 RSS | 待议 | 播客数据 |

---

## 四、凭据地图

所有 key 存放：`~/vault/credentials/api/probe.env`（chmod 600）

| 凭据 | 状态 |
|------|------|
| GITHUB_TOKEN | ✅ 已配 |
| PROBE_LITELLM_BASE/KEY | ✅ 已配 |
| PROBE_SEARXNG_BASE | ✅ 已配 |
| DEEPSEEK_API_KEY / BAILIAN_API_KEY | ✅ 已配 |
| ALPHAVANTAGE / FINNHUB / USDA_NASS / EIA | ✅ 已配 |
| FRED / BLS / HF_TOKEN | ✅ 已配 |
| VIRUSTOTAL_KEY / URLSCAN_API_KEY / ABUSEIPDB / NVD | ✅ 已配 |
| PROBE_TIKHUB_KEY | ✅ 已配（vault/api/datasource/social/）|
| PROBE_JZL_KEY | ✅ 已配（vault/api/jzl-api-key.txt）|
| OPENCORPORATES_TOKEN / PULSEDIVE | ⚠️ PLACEHOLDER |

---

## 五、永久拒用红线（节选）

| 类 | 代表源 | 原因 |
|----|--------|------|
| 逆向签名 | TikTok-Api · MediaCrawler · snscrape | 破平台安全机制 |
| 违法判例 | 蝉妈妈（2025 赔 490 万）· bilibili-API-collect（2026 律师函）| 已判违法 |
| 数据非法 | akshare / yfinance · 东财逆向 | 爬网页破反爬 |
| PIPL 红线 | Sherlock/Maigret / 社工库 | 人物画像·刑 253 |
| license 禁商 | DeepfakeBench(CC-BY-NC) / OpenBB(AGPL) | 商业明禁 |

完整 55 条见 [datasource-selfmedia-track-a-v1.md §五](../4-research/datasource-selfmedia-track-a-v1.md)。

---

> 状态真源：[ledger.yaml](../../app/datasources/ledger.yaml)
> 历史记录：[activation-log（只读）](probe-datasource-activation-log-v1.0.md) · [integration-schedule（只读）](probe-api-integration-schedule-v1.0.md)
> 自媒体赛道合规详析：[datasource-selfmedia-track-a-v1.md](../4-research/datasource-selfmedia-track-a-v1.md)

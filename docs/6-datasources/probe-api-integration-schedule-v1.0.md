# probe API 对接 · 登记排序 + 轻重缓急排期表 v1.1

> 编写：2026-06-12 · v1.1 同日更新(P0 wave 落地)：live 源 24→**48**，新增 4 个可用免费 key。
> 单一真源(SSOT)：本文件 + `app/datasources/ledger.yaml`(代码侧·v8) + `probe-datasource-activation-log-v1.0.md`(激活台账)
> 口径：**对接 = 拿到凭据(若需) + 写 adapter + 实测取到真数据 + ledger status=live**。
> 合规铁律：只接官方授权/开放许可源；逆向/破反爬/违法判例源一律 ❌ 永久拒用(见 §5)。
> 付费源一律 P3，须元东方密码确认(P0 R1)，本表只登记不开通。

---

## 一、总盘点(去重后)

| 分类 | 数量 | 说明 |
|------|------|------|
| ✅ **已 live(可调用)** | **48** 外部源 + 3 内部 LLM | 既往 11 + 本轮 +37 adapter；ledger v8 · selftest 8 passed |
| ✅ **可用免费 key** | 4 | AlphaVantage·Finnhub·USDA_NASS·EIA(均实测有效) |
| 🟡 **cataloged-live 待代理验证** | 7 | 中国官方/🌐源 Mac 直连受限·部署 probe-a 后转 live |
| ⚠️ **pending(账号/key 需手动)** | 9 | FRED/BLS/HuggingFace/VirusTotal/urlscan/AbuseIPDB/NVD/Pulsedive/SemScholar |
| 📋 **cataloged(已登记·待接)** | ~100 | 调研已确认合规·按本表 P1-P3 排期 |
| ❌ **rejected(永久拒用)** | ~55 | 逆向/违法/license 禁商用(§5) |

---

## 二、✅ 本轮已完成对接(2026-06-12)

### 2.1 新增 live adapter(13 个·全部 keyless 免费·已实测真数据)

| 源 | 域 | 赛道 | 实测验证 |
|----|----|------|---------|
| worldbank | D14 | F/D | 中国 GDP 2024=$18.74T ✅ |
| frankfurter(ECB 汇率) | D13 | F | USD→CNY=6.7774 ✅ |
| defillama | D13 | F | Binance CEX TVL=$139.6B ✅ |
| us_treasury | D13/D14 | F | 联邦总债务 $39.21T ✅ |
| coingecko | D13 | F | BTC 实时价 ✅ |
| tiktok_oembed(官方) | D6 | A | 接口校验 ✅ |
| mastodon | D6 | A | fosstodon 公开时间线 ✅ |
| yc_oss | D17/D11 | I | YC W24 AI 公司 ✅ |
| ossinsight | D12 | I | vuejs/vue 209k★ ✅ |
| openalex | D10/D5 | D | LLM 论文检索 ✅ |
| hackernews(Algolia) | D12/D6 | D | HN 热帖 ✅ |
| gleif(LEI) | D11 | B/C/F | Apple LEI ✅ |
| github_intel_rss | D17/D12 | I | 24 家 LLM 免费额度商 ✅ |

> ledger.yaml：version 5 → 7 · live 源 10 → 24 · selftest 8 passed(无回归)

### 2.2 新增凭据(免费 key)

| 源 | 域 | 状态 | key 位置 |
|----|----|------|---------|
| **AlphaVantage** | D13 美股 | ✅ 实测有效(IBM 实时报价 200) | `~/vault/credentials/api/probe.env` `ALPHAVANTAGE_API_KEY` |
| Finnhub | D13 | ⚠️ 账号已注册+邮箱已验证·捕获的 key 无效(401)·需从 dashboard 重取 | 同上(待修正) |

> 账号邮箱 metafo333@gmail.com(R8 授权)。

### 2.3 第二轮 P0 wave(多 agent 并发 · 同日落地)

**+32 个 adapter**(25 live / 7 cataloged-待代理)，ledger v7→v8，全部 import 通过，selftest 8 passed：

| 域 | live 源 |
|----|--------|
| 金融 F | eurostat·oecd·dbnomics·amac·cbank_rss·ccxt_src·hyperliquid·alt_fng·cninfo |
| 风控 C/E | ofac_sls·sanctions_network·crt_sh·rdap_icann |
| 调研 D | deps_dev·gh_archive·github_advisory·crossref·itunes_search·youtube_oembed |
| AI优惠 I / 省钱 G | gpuhunt_src·ai_vendor_rss·cloudcredits·startup_credits·holiday_cn·appstore_discounts |

7 个 **cataloged-待 probe-a 代理验证**(Mac 直连受限)：imf_sdmx·chinamoney_lpr·sge_gold·chinawealth·reddit_rss·exchange_deriv·wikidata_sparql。

**+3 个可用免费 key**(实测有效)：Finnhub(已修正 40 位)·USDA_NASS·EIA → `probe.env`。

---

## 三、📋 排期表(轻重缓急)

> 排序原则：**免费 keyless > 免费可自助注册 key > 免费需自托管 > 付费(R1)**；同档内按赛道权重 F(90)/G(85)/I(82)/H(80)/C(55)/A(50) 排。
> 「网络」列：🌐=需 probe-a 出口/mihomo 代理访问境外源。

### P0 · 本周即接(免费 keyless · 零注册)— 约 30 源 ✅ **本轮已基本落地**

> 状态：25 源已 live、7 源 cataloged-待 probe-a 代理验证(见 §2.3)。下表为完整清单，余下少量(解析库类/未覆盖)随 P1 补。

| 源 | 赛道 | 域 | 网络 | 端点要点 |
|----|------|----|----|---------|
| IMF SDMX / Eurostat / OECD / dbnomics | F/D | D14 | — | 国际宏观 SDMX |
| 央行 RSS(Fed/ECB/PBoC) | F | D14 | 部分🌐 | 政策公告 |
| cninfo 巨潮(官方 JSON 端点) | F | D11 | — | A 股年报/IPO·**只用官方端点禁爬虫** |
| chinamoney LPR / sge 上海金 / chinawealth / amac | F | D11/D13 | — | 央行/官方披露 |
| CCXT(100+CEX) | F | D13 | 🌐 | **仅内部决策·禁对外分发** |
| 交易所衍生品端点(Binance/Bybit/OKX 资金费率/OI) | F | D13 | 🌐 | 官方 REST |
| Hyperliquid Info / Alternative.me 恐慌贪婪 | F | D13 | 🌐 | 链上 perp / 情绪 |
| Etherscan V2(免费档·需 key·归 P1) | F | D13 | 🌐 | — |
| OFAC SLS / sanctions.network / crt.sh / RDAP-ICANN / Wikidata SPARQL | C/E | D8/D11 | — | 制裁/证书/工商 |
| deps.dev / GH Archive / GitHub Advisory / Crossref | D | D12/D10 | 部分🌐 | 依赖/漏洞/学术 |
| trafilatura / docling / MarkItDown / unstructured / pdfplumber | D | D2 | — | 文档解析库(本地) |
| Reddit .rss+.json / iTunes Search / 播客 RSS / YouTube oEmbed / RSSHub / feedparser | A | D6/D2 | 部分🌐 | 自媒体官方/开放 |
| edgartools / Common Crawl / asyncwhois+dnspython / waybackpy | B | D11/D4 | — | 商业情报库 |
| gpuhunt / Olshansk-RSS / 各 AI 厂商官方 RSS / cloudcredits / awesome-startup-credits / mnfst-data.json | I | D17 | 部分🌐 | AI 优惠 GitHub-First |
| holiday-cn / chinese-days / appstore-discounts | G | D15 | — | 节假日/限免底座 |

### P1 · 本周-下周(免费需 key · 可自助注册)— 约 20 源

我可用 Playwright+Gmail 自动注册的免费 key 源(部分站点 bot 拦截需元东方手动，已标 🖐)：

| 源 | 赛道 | 域 | 注册难度 |
|----|------|----|---------|
| **EIA(能源) / USDA NASS(农业)** | F | D13/D14 | ✅ 本轮已注册·实测有效 |
| urlscan.io / AbuseIPDB / Pulsedive | C/E | D8 | 🖐 本轮受阻(reCAPTCHA/bot/激活链接)·需手动 |
| NVD CVE / Semantic Scholar | D | D8/D10 | 🖐 本轮受阻(Cloudflare/审核)·需手动 |
| Libraries.io / PubMed-NCBI / Shodan InternetDB / Companies House | B/C/D | D11/D12 | 待接·易-中 |
| PageSpeed Insights / Google Fact Check / Data Commons / Etherscan V2 | B/E/F | D5/D1/D13 | 待接·Google/简单 |
| **FRED**(美联储宏观·高价值) | F/D | D13/D14 | 🖐 本轮受阻(隐藏 CSRF)·需手动 |
| **US BLS**(劳工统计) | F | D14 | 🖐 本轮受阻(扭曲验证码)·需手动 |
| **HuggingFace token**(90 万模型) | I | D12/D17 | 🖐 本轮受阻(CloudFront 403)·需手动或换 IP |
| **VirusTotal**(已 cataloged·adapter 就绪) | C/E | D8 | 🖐 既往受阻·需手动 |
| **Finnhub**(已注册·key 无效) | F | D13 | 🖐 dashboard 重取 key |
| Kaggle / Reddit OAuth App / YouTube Data API v3 / Spotify | A/H/I | D6/D16 | 中·OAuth |

### P2 · 按需(免费·需自托管/重部署)— 约 8 源

| 源 | 赛道 | 部署 |
|----|------|------|
| SpiderFoot(资产被动侦察·**禁人物模式**) | B/C | Docker 自托管 |
| OpenSanctions + Yente(制裁) | C | 自托管·非商业免费 |
| Maltrail / GROBID / The Graph node / 自建 RSSHub 实例 | E/D/F | 自托管 |

> 自托管建议落 ufo(算力机)或 probe-a，按 server-roles 边界；probe 采集数据只入 probe-a 本机 PG。

### P3 · 待元东方拍板(付费 · P0 R1 红线 · 仅登记不开通)— 约 60 源

按价值/成本排序的关键付费源(完整 60 源见 ledger + 调研文档)：

| 优先 | 源 | 赛道 | 月成本估 | 价值 |
|------|----|------|---------|------|
| ★P3-1 | TikHub | A | $20-300/量 | 国内 5 平台(抖音/小红书/B站/微博/快手)唯一合规路径·compliance_debt 已知接受 |
| ★P3-2 | 天眼查/企查查 API | C/F | ¥按量·企业资质 | 中国企业风险唯一全维 |
| ★P3-3 | Shodan 完整版 | C | $49 一次性 | 性价比极高·强烈推荐 |
| P3-4 | AlphaVantage Premium / Polygon.io | F | $30-50 | 美股深度(免费档已先用) |
| P3-5 | 大淘客/拼多多 DDK/穿山甲(CPS) | G/H | 抽佣·个人可注册 | 省钱/搞钱变现入口 |
| P3-6 | Sightengine/Copyleaks/GPTZero(AI 检测) | E | $8-179 | 商业核查必需 |
| P3-7 | Crunchbase / tushare / Trading Economics | B/F | $17-49 | 融资/A股/经济日历 |
| … | (其余 50+ 见 ledger cataloged·access_type=paid) | — | — | 按业务触发再评估 |

---

## 四、凭据记录(本轮更新)

| 凭据 | 位置 | 状态 |
|------|------|------|
| ALPHAVANTAGE / FINNHUB / USDA_NASS / EIA | `~/vault/credentials/api/probe.env`(chmod 600) | ✅ 实测有效(4 个) |
| FRED/BLS/HF/VIRUSTOTAL/URLSCAN/ABUSEIPDB/NVD/PULSEDIVE/SEMANTIC_SCHOLAR/OPENCORPORATES | 同上 = PLACEHOLDER | ⚠️ 待手动(风控拦截) |
| 既有(GITHUB/LiteLLM/DeepSeek/Bailian/SearXNG) | 同上 | ✅ 既往已配 |

> 注册账号统一邮箱 metafo333@gmail.com(元东方 R8 授权) · 账号密码记 probe.env 注释区 chmod 600 · 仓内 .env.example 仅 PLACEHOLDER。
> vault 总册 `~/vault/credentials/INDEX.md` 第 2 节已登记 probe 数据源 key 指针。

---

## 五、❌ 永久拒用红线(节选·完整 55 源见调研文档)

| 类 | 代表源 | 拒用理由 |
|----|--------|---------|
| 逆向签名 | TikTok-Api / Douyin 逆向 / X-Bogus 库 / MediaCrawler / snscrape | 破平台安全机制·铁律① |
| 违法判例 | 蝉妈妈(2025 厦门判赔 490 万) / bilibili-API-collect(2026 律师函清空) | 已判违法 |
| 数据非法 | akshare 全系 / yfinance / 东财天天基金逆向 | 爬网页破反爬·MIT 代码≠数据合规 |
| PIPL 红线 | Sherlock/Maigret / SpiderFoot 人物模式 / 任何社工库 | 拼装人物画像·刑 253 |
| license 禁商用 | DeepfakeBench(CC-BY-NC) / OpenBB(AGPL 传染) / marker-pdf | 商业明确禁止 |
| key 倒卖 | alistaitsacle/free-llm-api-keys | 违 ToS |

---

## 六、下一步(队列就绪)

1. **P0 wave** — 多 agent 并发写 ~30 个 keyless adapter(同本轮模式) → 一轮可大批 live。
2. **P1 自助注册** — urlscan/AbuseIPDB/NVD/EIA 等易注册源批量拿 key。
3. **元东方手动补 5 个** — FRED / BLS / HuggingFace / VirusTotal(真浏览器) + Finnhub(dashboard 重取 key)。
4. **P3 付费** — 按 ★ 优先级出报价单待密码确认。

> 关联：[ledger.yaml](../../app/datasources/ledger.yaml) · [激活台账](probe-datasource-activation-log-v1.0.md) · [总导航](../3-build/) · 各赛道调研 [docs/4-research/](../4-research/)

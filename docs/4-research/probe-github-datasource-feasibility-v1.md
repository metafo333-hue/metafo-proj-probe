# probe 情报引擎 · GitHub 数据源调研 + 可行性 + 实施方案 v1.0

> 日期：2026-06-06 · 方法：6 路扇出调研（5 业务域 + 公共资源层）· 全部真实 GitHub/官方文档查证 + 对抗核查
> 框架对齐：本报告是 [probe-intelligence-engine-design-v1.md](../3-build/probe-intelligence-engine-design-v1.md) §2 数据源仓库的**落地调研**，框架不变
> 合规基准：**不自己爬数据**（不自建爬虫、不模拟登录；绕反爬由第三方供应商担责）；只接受 L/S/W/O/D 五类实现方式
> 数据源原始报告：6 路调研详表见本会话 agent 输出（如需可回溯 agentId）

---

## 1. GitHub 实现数据源的「6 种范式」（方法论总览）

你问的「在 GitHub 上实现数据源的方式是什么、有哪些」——系统答案是 **5 类实现 + 1 类发现**：

| 代号 | 范式 | 定义 | 优点 | 缺点 | 代表 |
|------|------|------|------|------|------|
| **L** | 开源库本地嵌入 | pip/npm 装进项目直接调，无独立服务 | 零延迟·无配额·离线 | 静态快照·占磁盘 | Docling · whisperX · imagehash · dnspython |
| **S** | 可自托管开源服务 | 部署开源软件到自有服务器，对内提供 API | 数据自控·无配额·可定制 | 运维负担·部署门槛 | SearXNG · RSSHub · SpiderFoot · Yente |
| **W** | 开源官方 API 客户端 SDK | 用平台官方维护的开源 SDK 调其 API | 官方跟进·文档全 | 受平台配额/付费约束 | PyGithub · arXiv.py · vt-py · PyAlex |
| **O** | 官方开放 API（需 key/付费） | 直调平台官方授权 API | 权威·授权清晰 | 配额/付费/审核门槛 | OpenCorporates · Lens.org · YouTube Data |
| **D** | 开源数据集/批量 | 用整理好的结构化数据集，定期下载本地处理 | 量大·历史全·离线 | 实时性差·存储成本 | OpenSanctions · GDELT · AllSides CSV |
| **★源的源** | API 目录/Awesome 清单 | 不采数据，而是从元目录持续**发现**新源 | 扩源效率最高 | 需二次核验各源合规 | public-apis(440k★) · awesome-osint(26.7k★) · APIs.guru |

**关键方法论**：probe 持续扩源的最高效渠道是「★源的源」。建议把 `public-apis/public-apis`、`jivoi/awesome-osint`、`APIs.guru 机器 API（api.apis.guru/v2/list.json）` 纳入季度自动扫描——新源第一落地地，不靠人工拍脑袋。

---

## 2. 公共资源默认底座（全面覆盖的共同组成 · 你点名的补充）

> 你要求的「自媒体权威信息补充 + GitHub 真实信息补充」= 把一批**零成本、高权威、合规**的源设为**每次任务都默认调用**的共同底座（不分业务域）。这是 probe 的「全面覆盖」基本盘。

| 优先级 | 源 | 方式 | 补充的「真实信息」 | 接入 |
|-------|----|----|------|------|
| **P0 必选** | SearXNG（自托管） | S | 一次查 70+ 搜索引擎，通用检索底座 | 免费自托管 |
| **P0 必选** | Wikimedia REST API | O | 通用知识权威源（多语言） | 免费无 key |
| **P0 必选** | Wikidata SPARQL | O | 结构化实体关系/知识图谱 | 免费无 key |
| **P0 必选** | GitHub REST API（PyGithub） | W | **GitHub 真实信息**：repo/user/code/活跃度/趋势 | 免费 PAT·5000/h |
| **P0 必选** | GDELT | W/D | 全球新闻事件库·15 分钟实时 | 免费无 key |
| **P1 推荐** | Open-Meteo | S/O | 气象（1940 起历史+16 天预报） | 非商业免费 |
| **P1 推荐** | fawazahmed0/exchange-api | O | 汇率·200+ 币种·无限速 | 完全免费 |
| **P1 推荐** | SpiderFoot（自托管） | S | OSINT 深度探查后端·200+ 模块 | 免费自托管 |
| **自媒体权威补充** | YouTube Data API + 各平台官方 oEmbed + RSSHub 热榜路由 + TikHub 等第三方聚合 API（video/social 数据均走第三方 API，**禁 probe 自己 yt-dlp 下载/字幕**） | W/O/S | **自媒体权威信息**：合规范围内的官方视频数据/内容元数据/公开热榜 | YouTube 免费额度 / oEmbed 免费 / RSSHub 自托管 / TikHub 按计划付费 |

> 落地建议：把上述 P0 做成 probe 的「默认源集」，任何场景任务先打底座再叠加业务域专源。**自媒体权威信息**走官方 API + 公开热榜路由（不碰代爬）；**GitHub 真实信息**走 GitHub 官方 API（技术情报域天然权威）。

---

## 3. 五业务域数据源精选（每域 Top 合规源）

> 完整对比表（含 stars/license/活跃度/弃用项）见 6 路调研原始输出。下表为**汇总精选**。✅ 可立即接 · ⚠️ 需 key/付费/资质 · ❌ 弃用

### A · 自媒体/内容创作
| 赛道 | 首选 | 方式 | 接入 |
|------|------|------|------|
| 字幕/转写 | whisperX（+ faster-whisper） | L | ✅ 免费本地 |
| RSS/热榜 | RSSHub + Miniflux + feedparser | S/L | ✅ 免费自托管 |
| 平台数据 | YouTube→google-api-python-client；抖音/TikTok→官方开放平台 | W/O | ⚠️ 免费额度/需申请 |
| BGM 版权 | pyacoustid（识别）+ Jamendo API（找曲） | L/O | ✅/⚠️ |
| 内容元数据 | 各平台官方 oEmbed + iframely 自托管 | O/S | ✅ 免费 |
| ❌ 弃用 | bilibili-api(逆向·律师函) · 小红书逆向（probe 自己嵌入的逆向库）· TikHub captcha 破解工具（TikHub 纯数据 API 本身可用，见 §4） | — | ❌ |
| video/social 数据 | TikHub 等第三方 API 聚合（走第三方 API，禁 probe 自己 yt-dlp 下载） | W/O | ✅ 可用（供应商担责） |

### B · 商业/市场/竞品
| 赛道 | 首选 | 方式 | 接入 |
|------|------|------|------|
| 网络资产 | asyncwhois + dnspython + subfinder + waybackpy | L | ✅ 免费 |
| 技术栈识别 | wappalyzergo（ProjectDiscovery·Go） | L | ✅ 免费 |
| 流量/SEO | DataForSEO（pay-as-you-go）+ open-seo 前端 | W/O | ⚠️ $50 起充 |
| 电商价格 | python-amazon-paapi（Creators API）+ Keepa | W/O | ⚠️ 需联盟/付费 |
| App 榜单 | SerpAPI Google Play（合规唯一）| W/O | ⚠️ 付费 |
| 公司/融资 | OpenCorporates + edgartools(SEC) + pygleif(LEI) | O/L/W | ✅ 免费层 / ⚠️ Crunchbase 付费 |

### C · 尽调/背调/风控
| 赛道 | 首选 | 方式 | 接入 |
|------|------|------|------|
| 工商企业 | OpenCorporates(国际) + edgartools(美股) + 天眼查(中国) | O/L | ✅免费 / ⚠️天眼查需企业资质 |
| 制裁/PEP | OpenSanctions(数据) + Yente(自托管 API) | D/S | ✅ 非商业免费 / ⚠️ 商业需 bulk license |
| 域名/资产风险 | vt-py(VirusTotal) + URLhaus + Shodan | W/D | ✅免费层 / ⚠️Shodan $49 |
| 人物 OSINT | Sherlock（仅即时单次查询） | L | ⚠️🔴 个保法红线·禁批量落库 |
| 司法/经营异常 | 天眼查 API（裁判文书网 2023 已关闭公众检索） | O | ⚠️ 需企业资质 |

### D · 调研/知识/技术
| 赛道 | 首选 | 方式 | 接入 |
|------|------|------|------|
| 通用搜索 | SearXNG（+ Tavily 付费增强） | S/W | ✅ 免费自托管 |
| 学术 | arXiv.py + PyAlex(OpenAlex) + habanero(Crossref) | W | ✅ 免费 |
| 专利 | Lens.org API + Google Patents BigQuery | O/D | ⚠️ 免费注册/BigQuery 配额 |
| 新闻舆情 | GDELT + feedparser | W/L | ✅ 免费 |
| 文档解析 | Docling(主) + MarkItDown(轻) + faster-whisper(音视频) | L | ✅ 免费本地 |
| GitHub 技术情报 | OSV-Scanner + OSV.dev + deps.dev + PyGithub | L/O/W | ✅ 免费 |

### E · 真伪/溯源/核查（验证层对外）
| 赛道 | 首选 | 方式 | 接入 |
|------|------|------|------|
| 反向图搜 | imagehash(本地)→ TinEye/Google Vision(精确) | L/W/O | ✅免费本地 / ⚠️付费精确 |
| AIGC 检测 | Binoculars(文本·BSD) + DeepfakeBench(图像·⚠️非商用) | L | ✅文本 / ⚠️图像许可 |
| 事实核查 | Google Fact Check API + Data Commons 数据集 | W/D | ✅ 免费 key |
| URL/钓鱼 | VirusTotal + urlscan.io + PhishTank + OpenPhish | W/O/D | ✅ 免费层 |
| 内容溯源 | c2pa-python(C2PA) + ExifTool(CLI) | L | ✅ 免费本地 |
| 媒体可信度 | AllSides CSV 导入（无 API·静态） | D | ✅ 免费导入 |

---

## 4. 可行性分析报表（综合评分 · 决定接入优先级）

> 评分维度：价值(对场景的不可替代性) · 成本(R1) · 合规 · 接入难度 · 综合优先级
> 优先级：🟢P0 立即接（免费+合规+易接）· 🟡P1 按场景授权（需 key/付费但可控）· 🔴P2 高价值高成本 · ⛔弃用

| 数据源 | 域 | 价值 | 成本 | 合规 | 接入难度 | 优先级 |
|--------|----|----|----|----|--------|--------|
| SearXNG / Wikimedia / Wikidata / GitHub API / GDELT | 公共底座 | 高 | 0 | ✅ | 低 | 🟢 P0 |
| Docling / MarkItDown / faster-whisper / whisperX | A/D | 高 | 0 | ✅ | 低 | 🟢 P0 |
| asyncwhois / dnspython / subfinder / waybackpy / wappalyzergo | B | 高 | 0 | ✅ | 低 | 🟢 P0 |
| edgartools / OpenCorporates / pygleif | B/C | 高 | 0~低 | ✅ | 低 | 🟢 P0 |
| arXiv.py / PyAlex / habanero / OSV / deps.dev | D | 高 | 0 | ✅ | 低 | 🟢 P0 |
| imagehash / Binoculars / c2pa-python / ExifTool | E | 高 | 0 | ✅ | 低 | 🟢 P0 |
| OpenSanctions + Yente | C | 高 | 0(非商) | ✅ | 中(自托管) | 🟢 P0 |
| VirusTotal / urlscan / URLhaus / PhishTank | C/E | 高 | 0(免费层) | ✅ | 低 | 🟢 P0 |
| RSSHub / Miniflux / SpiderFoot | A/公共 | 中高 | 0 | ✅ | 中(自托管) | 🟢 P0 |
| YouTube Data API / 各平台 oEmbed | A | 高 | 0(额度) | ✅ | 低 | 🟢 P0 |
| Google Fact Check API / Lens.org | E/D | 中高 | 0(注册) | ✅ | 低 | 🟡 P1 |
| DataForSEO（流量/SEO/SERP） | B | 高 | $50 起充 | ✅(官方) | 低 | 🟡 P1 |
| Keepa / python-amazon-paapi | B | 中高 | 付费/联盟 | ✅ | 中 | 🟡 P1 |
| Tavily / SerpAPI / Brave / Exa（搜索增强） | D/公共 | 中 | 付费层 | ✅ | 低 | 🟡 P1 |
| TinEye / Google Vision / Sightengine / GPTZero | E | 中高 | 付费 | ✅ | 低 | 🟡 P1 |
| 天眼查 / 企查查（中国工商司法） | C | 高 | 付费+资质 | ⚠️PIPL | 中(企业认证) | 🟡 P1 |
| Crunchbase / Sensor Tower | B | 中 | $49+/月 | ✅ | 低 | 🔴 P2 |
| Sherlock / Maigret（人物 OSINT） | C | 中 | 0 | 🔴PIPL | 低 | 🔴 P2(限即时查询·禁落库) |
| TikHub（纯数据 API · 不调其 captcha 工具） | A/D8 | 中高 | 付费 | ✅ 可用（供应商担责） | 低 | 🟡 P1 |
| bilibili-api（逆向·律师函）/ 小红书逆向 / 裁判文书爬虫（probe 自己嵌入的逆向库） | — | — | ⛔ probe 自己爬 | — | ⛔ 弃用 |
| SimilarWeb 非官方 / pytrends-Camoufox（probe 直连未授权内部 API） | — | — | ⛔ probe 自己绕 | — | ⛔ 弃用 |
| 蝉妈妈（已被司法判违法） | — | — | ⛔ 违法供应商 | — | ⛔ 弃用 |

---

## 5. 合规缺口与红线清单（硬约束 · 必须记录）

### 红线口径（最终版 · 单条）

**「不自己爬」** = probe 自身不实施任何爬取（自写爬虫/抓取平台数据/模拟登录/抓包/逆向签名）。
**可用**任何第三方付费/免费 API 或全自动化数据提供方（第三方如何取数由其自行担责，probe 只作调用方）；弃已被司法判违法供应商（蝉妈妈）。
**独立保留**（不被此单条吃掉）：个保法最小必要 / aigc_flag / 原料进结论出。

> 判定要点：TikHub 等第三方 API 聚合 = **✅ 可用**（probe 只调数据接口，不调其 captcha 工具，供应商担责）。仍 ❌ 弃用：probe 自己嵌入的逆向库（bilibili-api/小红书逆向/裁判文书爬虫）· probe 直连未授权内部 API（SimilarWeb 非官方/pytrends-Camoufox）· 蝉妈妈（已判违法）。

### 调用方责任边界（2026-06-08 补 · 「供应商担责」担不了的三处 · probe 自责）

「probe 只作调用方·供应商担责」对**数据采集层**成立，但下列三处责任在 probe 自己，第三方挡不住，必须 probe 自建合规判定层拦截：

| # | 场景 | 为什么供应商担不了 | probe 自责动作 |
|---|------|------------------|---------------|
| 1 | **数据出境** | probe 调海外 API 传中国用户数据时，probe 自身即「出境方」（PIPL 第 38-39 条） | 出境拦截：中国个人数据禁发境外 API；跨境前评估 + 最小化 |
| 2 | **二次分发/白标** | 转售/再分发第三方数据可能违反该 API 的 ToS，「再分发」是 probe 的行为非供应商的 | 再分发授权核验：白标/可商用前逐源核 ToS 是否许可转售 |
| 3 | **敏感拼装** | 即便每源都合规，probe 把碎片**拼成人物背调**这一「处理」动作本身可能违法（PIPL/刑法 253 之一） | 敏感拼装阻断：人物类拼装走 §C 即时不落库 + 合法依据门 |

> 结论：红线口径的「调用方无责」只覆盖**采集层**；**出境/再分发/拼装**是 probe 应用层的自有合规责任，不可外包。详见 [bizmodel review §7②](../records/probe-value-presentation-and-bizmodel-review-v1.md)。

---

| 缺口/红线 | 现状 | probe 对策 |
|----------|------|-----------|
| 微信公众号 | 无官方 RSS/API，第三方均逆向 | ❌ 无合规路径，暂不覆盖 |
| B 站 | 官方无第三方开放 API，社区库逆向（2026-01 律师函） | 仅 RSSHub 公开 RSS 路由（无用户数据） |
| 小红书 | 官方开放平台需企业认证+审核，能力有限 | 仅官方平台申请（不碰逆向） |
| 中国裁判文书 | 文书网 2023 关闭公众检索 | 仅天眼查聚合（滞后 1-3 月·非全量） |
| 流量估算（类 SimilarWeb） | 无免费合规方案 | 仅 DataForSEO 付费（pay-as-you-go） |
| App 榜单/下载 | App Store/Google Play 无开放榜单 API | 仅 SerpAPI 付费（开源库全为非授权爬取） |
| 媒体可信度评级 | MBFC/Ad Fontes 无 API | 仅静态 CSV 周期导入（AllSides/Qbias） |
| 人物 OSINT | Sherlock/Maigret 聚合能力强 | 🔴 即时单次查询·不落库·日志脱敏·留合法依据（PIPL 第 53 条+刑法 253 之一：普通≥5000/敏感≥500 条入刑） |
| AIGC 图像检测 | DeepfakeBench 最成熟但 CC BY-NC 非商用 | 短期原型/接商业 API；长期找 Apache-2.0 模型 |
| MinerU 许可 | Apache 2.0 + 附加条款 | 优先 Docling（纯 MIT）；MinerU 待法务确认 |

---

## 6. 实施方案（落地路线）

### 6.1 适配器接入顺序（沿用现有 registry/ledger/标准19 机制）

**Sprint 1 · 公共底座 + 零成本本地库（全免费·零 R1）**
1. 升级 `ledger.yaml` → 多域 catalog（按 §2.4 元数据 schema，加 domain/access_type/authority_score 字段）
2. 接入默认底座适配器：SearXNG · Wikimedia · Wikidata · GitHub API(PyGithub) · GDELT
3. 本地库适配器：Docling · MarkItDown · faster-whisper · imagehash · ExifTool · c2pa-python · Binoculars
4. 网络资产适配器：asyncwhois · dnspython · subfinder · waybackpy · wappalyzergo
5. 学术/技术适配器：arXiv.py · PyAlex · OSV.dev · deps.dev · edgartools

**Sprint 2 · 自托管服务 + 免费层 API**
6. 自托管：RSSHub · Miniflux · SpiderFoot · Yente(+OpenSanctions 数据)
7. 免费层 API：VirusTotal · urlscan.io · URLhaus · PhishTank · YouTube Data · 各平台 oEmbed · OpenCorporates · pygleif · Google Fact Check · Lens.org

**Sprint 3 · 验证层 engine（双审 8 闸，见 audit-system-v1）**
8. 闸0 过程留痕 + 闸1/2 溯源+交叉印证 + 闸6 对抗证伪先落地（这是不可替代性所在，与数据源并重）

**Sprint 4 · 付费源（R1 逐个授权 · 按场景 ROI）**
9. 按真实场景需求排序授权：DataForSEO（流量）→ 天眼查（中国工商/司法）→ Keepa（Amazon 价格）→ Tavily/SerpAPI（搜索增强）→ TinEye/Sightengine（图像/AIGC）→ Crunchbase（融资）

### 6.2 每个适配器的接入门（不变）
R1 付费授权（付费源）→ 标准19 核验 → 实现 `DataSourceAdapter`（只返标准化元数据，不直吐原料）→ ledger `status: active` → registry 放行。

### 6.3 解耦保证
所有适配器实现统一 `DataSourceAdapter` 契约；采集层/验证层/整合层源无关。新增/替换一个源 = 加/换一个适配器，**对流程零影响**，只改变数据质量。

---

## 7. 待元东方拍板（R1 付费源授权清单）

Sprint 1-3 全程**零 R1 成本**（免费源 + 本地库 + 自托管），可直接开工。仅 Sprint 4 付费源需逐个授权，建议按此 ROI 顺序：

| 序 | 付费源 | 用途 | 成本量级 | 建议 |
|----|-------|------|---------|------|
| 1 | DataForSEO | 流量/SEO/SERP（B 域刚需） | $50 起充·按量 | 优先 |
| 2 | 天眼查/企查查 开放平台 | 中国工商/司法/尽调（C 域刚需） | 付费+企业资质 | 优先（需公司资质走 R1+R4） |
| 3 | Keepa | Amazon 价格历史（B 域电商） | 订阅 | 按需 |
| 4 | Tavily / SerpAPI | 搜索/App 榜单增强 | 付费层 | 按需 |
| 5 | TinEye / Sightengine / GPTZero | 反图搜/AIGC 检测（E 域变现） | $29-200/月 | 按变现节奏 |
| 6 | Crunchbase | 全球融资（B/C 域高客单） | $49+/月 | 中大 B 场景再接 |

> 问题：Sprint 1-3 零成本部分**是否即可开工**（我直接升级 ledger 多域 catalog + 起首批适配器骨架）？Sprint 4 付费源是否同意按上表 ROI 顺序、需要时逐个走 R1 授权？

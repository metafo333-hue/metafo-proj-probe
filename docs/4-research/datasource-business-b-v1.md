# probe · B商业市场竞品域 数据源调研报告 v1.0

> 日期：2026-06-10 · 性质：调研证据层（6子场景×三层优先级+四闸审核）
> 方法：开源API > 综合服务 > 权威官方 三层 · 永不代爬 · 见 [调研方法论v1.1](datasource-research-methodology-v1.0.md)
> 上游：[赛道注册表架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) B-business · [feasibility-v1](probe-github-datasource-feasibility-v1.md) §B
> 状态口径：✅ 采纳（可立即用） · ⚠️ 待授权（R1付费/R4资质） · ❌ 弃（合规/ROI）

---

## 一、综述

### 三层覆盖总评表

| 子场景 | L1 开源/免费可用数 | L2 商业服务数 | L3 权威官方数 | 整体覆盖评级 | 核心缺口 |
|--------|------------------|-------------|-------------|------------|---------|
| B1 竞品全景 | 3（edgartools / SpiderFoot / GLEIF+Companies House） | 3待授权（Crunchbase / OpenCorporates商业 / Dealroom） | 2（SEC EDGAR / GLEIF官方） | 🟡 中等 | 中国未上市企业·私有市场深度 |
| B2 网站诊断 | 5（wappalyzergo / sitespeed.io / asyncwhois / waybackpy / PageSpeed Insights） | 3待授权（DataForSEO / Moz / BuiltWith） | 2（Internet Archive / Common Crawl） | 🟢 良好 | 实时精准流量（SimilarWeb级）太贵 |
| B3 行业赛道扫描 | 6（SearXNG / GDELT / OSSInsight / GitHub API / World Bank / OECD / OEC） | 3待授权（Crunchbase / Dealroom / Tracxn） | 2（World Bank / OECD官方） | 🟢 良好 | CB Insights/Statista无公开API·中国行业协会无机器可读API |
| B4 电商价格销量 | 2（keepa SDK壳 / DataForSEO Amazon Merchant） | 3待授权（Keepa API / Jungle Scout / 后端Keepa） | 1（Amazon SP-API自有） | 🔴 弱 | 跨境非Amazon电商无合规API·真实销量数据封锁 |
| B5 App情报 | 2（RSSHub版本监控 / App Store Connect自有） | 2待授权（SerpAPI Google Play / AppTweak） | 2（App Store Connect / Google Play Developer API自有） | 🔴 弱 | 真实下载量只平台持有·中国应用市场无API |
| B6 品牌舆情 | 4（GDELT / RSSHub / PRAW / feedparser / NewsCatcher免费层） | 3待授权（Brand24 / BrandMentions / Twitter/X API） | 0 | 🟡 中等 | 微信生态无API·中文情感分析需本地补充 |

### 核心结论（5条）

1. **L1层覆盖最厚的是B2和B3**：网站诊断和行业赛道扫描均有5-6个可立即接入的开源/免费方案，MVP阶段无需付费即可运转。

2. **B4电商和B5 App是最薄弱的两个子场景**：真实销量数据和App下载量数据是平台级私有资产，合规路径只有付费商业API（Keepa / SerpAPI / AppTweak）或自有开发者账号，无法绕过。

3. **中国本土商业数据存在结构性缺口**：未上市中国企业、国内应用市场、微信生态、中文行业协会数据均无合规API，B域所有中国深度情报实际依赖天眼查（待授权R1）或人工研判。

4. **B1和B6在付费授权到位前可以"半跑"**：用SEC EDGAR + edgartools做美股，GDELT + RSSHub + NewsCatcher免费层做舆情，覆盖英文/美股/欧洲上市公司范围已够MVP验证。

5. **NewsCatcher是B6性价比最高的立即行动项**：免费层100次/日·Starter $50/月，内置多语言NLP情感，可以在R1授权前先用免费层验证效果，建议列为下一批接入P0。

---

## 二、6子场景源卡明细

### B1 · 竞品全景

#### L1 · 开源/免费层

**edgartools**
- URL：https://github.com/dgunning/edgartools
- License：MIT
- 能力：Python库·解析SEC EDGAR 20+表单（10-K/10-Q/8-K等）·财务报表结构化提取·融资/股权/高管变动
- 接入成本：`pip install edgartools`·零成本
- 合规：MIT·SEC EDGAR数据CC0公共领域
- **裁决：✅ 采纳 P0**（美股上市竞品财务/融资数据首选）

**SpiderFoot**
- URL：https://github.com/smicallef/spiderfoot
- License：MIT
- 能力：200+OSINT模块·竞品域名/IP/技术资产/证书/子域名/社交关联探测·自托管
- 接入成本：自托管Docker·零授权成本
- 合规：MIT·主动扫描需确认目标无反扫描条款
- **裁决：✅ 采纳**（竞品技术资产/数字足迹探测·配合B2网站诊断）

**GLEIF + pygleif / Companies House API**
- GLEIF URL：https://www.gleif.org/en/lei-data/gleif-api
- Companies House URL：https://developer.company-information.service.gov.uk
- License：GLEIF开放数据·Companies House开放API
- 能力：GLEIF覆盖全球LEI法人识别符·Companies House覆盖英国工商注册·股权结构/注册地址/董事
- 接入成本：免费·需注册key（Companies House）
- 合规：官方开放数据·无商业限制
- **裁决：✅ 采纳**（欧洲/全球法人识别补充·补OpenCorporates缺口）

#### L2 · 商业服务层

**OpenCorporates API**
- URL：https://api.opencorporates.com
- 能力：230M家公司·145+辖区工商数据·公司状态/注册信息/董事/关联关系
- 接入成本：免费层200次/月·50次/日；商业版£2250/年起
- 合规：开放层CC-BY·商业层合同授权
- **裁决：⚠️ 待授权 R1**（免费层做原型·商业场景需付费授权）

**Crunchbase API**
- URL：https://about.crunchbase.com/products/crunchbase-api
- 能力：融资轮次/投资方/估值/创始团队/竞品关系图谱
- 接入成本：2026年已取消免费层·$49/月起（Basic）
- 合规：商业API合同·数据来源公开披露
- **裁决：⚠️ 待授权 R1**（B1融资情报首选·MVP后优先授权）

**Dealroom**
- URL：https://dealroom.co
- 能力：欧洲生态最强·初创公司/融资/投资方/生态地图·API访问
- 接入成本：€12,500/年起
- 合规：商业合同
- **裁决：⚠️ 待授权 R1**（欧洲专项场景·非全球MVP阶段可暂缓）

**PitchBook**
- 成本：$12,000–$70,000/年
- **裁决：❌ 弃**（成本严重超ROI·Crunchbase覆盖80%融资数据·性价比不成立）

**Harmonic.ai**
- 成本：$25,000/年起
- **裁决：❌ 弃**（超高成本·无公开self-serve·与目标不符）

#### L3 · 权威官方层

**SEC EDGAR API**
- URL：https://data.sec.gov
- 能力：美国上市公司全量财报·10-K/10-Q/8-K·RESTful JSON API
- 接入成本：免费·无需key·限速10 req/s
- 合规：CC0·美国公共数据
- **裁决：✅ 采纳**（经edgartools解析·B1美股财务数据权威底座）

---

### B2 · 网站诊断

#### L1 · 开源/免费层

**wappalyzergo**
- URL：https://github.com/projectdiscovery/wappalyzergo
- License：MIT（注：依赖的Wappalyzer指纹库为GPL-3.0·**需法务确认商业使用**）
- 能力：技术栈检测·CMS/框架/CDN/分析工具识别·Go语言高性能
- 接入成本：`go get`·零成本
- 合规：MIT壳可用·GPL-3.0指纹库商业化需法务核查
- **裁决：✅ 采纳**（技术栈核心检测·法务确认前仅内部使用）

**sitespeed.io**
- URL：https://github.com/sitespeedio/sitespeed.io
- License：MIT
- 能力：Lighthouse集成·Core Web Vitals·SEO评分·性能预算·Docker化部署
- 接入成本：Docker自托管·零授权成本
- 合规：MIT
- **裁决：✅ 采纳**（性能+SEO完整方案·配合ufo Docker算力机）

**asyncwhois + dnspython**
- asyncwhois URL：https://github.com/pogzyb/asyncwhois
- License：MIT
- 能力：异步WHOIS/RDAP查询·域名注册时间/注册商/到期日·DNS记录解析
- 接入成本：`pip install asyncwhois dnspython`·零成本
- 合规：MIT·WHOIS公开协议
- **裁决：✅ 采纳**（域名/注册信息底座）

**waybackpy**
- URL：https://github.com/akamhy/waybackpy
- License：MIT
- 能力：Wayback Machine历史快照检索·改版时间线·页面存档URL批量获取
- 接入成本：`pip install waybackpy`·零成本
- 合规：MIT·Wayback Machine公开API
- **裁决：✅ 采纳**（竞品改版历史/品牌演变追踪）

**PageSpeed Insights API**
- URL：https://developers.google.com/speed/docs/insights/v5/get-started
- 能力：Core Web Vitals（LCP/FID/CLS）·移动端/桌面SEO评分·Google官方权威
- 接入成本：免费·有key 25,000次/日·无key也可用（限速）
- 合规：Google官方API·ToS允许商业使用
- **裁决：✅ 采纳**（SEO+性能权威免费首选·列P0接入）

#### L2 · 商业服务层

**DataForSEO**
- URL：https://dataforseo.com
- 能力：域名流量估算/关键词排名/反链/SERP数据·$0.001/任务起·充值制
- 接入成本：$50起充
- 合规：商业API合同·代为抓取·平台担责
- **裁决：⚠️ 待授权 R1**（流量估算B2首选·DataForSEO是SimilarWeb底层供应商·更划算）

**Moz API**
- URL：https://moz.com/products/api
- 能力：Domain Authority（DA）/ Page Authority（PA）·反链数据
- 接入成本：$49/月
- 合规：商业API
- **裁决：⚠️ 待授权 R1**（按需·有DataForSEO后可降优先级）

**BuiltWith API**
- URL：https://api.builtwith.com
- 能力：技术栈历史追踪·竞品技术演变时间线·$144/年起
- 接入成本：$144/年起（Basic）
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（技术历史追踪·wappalyzergo只有当前快照·需历史时补充）

**SimilarWeb / Ahrefs / SEMrush**
- **裁决：❌ 弃**（成本极高·DataForSEO是其底层供应商且价格更优·ROI不成立）

#### L3 · 权威官方层

**Internet Archive Wayback Machine**
- URL：https://archive.org/help/wayback_api.php
- 能力：公开API·页面历史快照·CDX Server API批量查询
- 接入成本：免费
- 合规：互联网公共档案·无商业限制
- **裁决：✅ 采纳**（waybackpy底层·历史快照权威来源）

**Common Crawl**
- URL：https://commoncrawl.org
- License：CC0
- 能力：250B+页面爬取数据·离线批量分析
- 接入成本：免费·AWS S3直接访问
- 合规：CC0·完全开放
- **裁决：✅ 采纳（B3场景）**（B2实时诊断不适合·B3离线赛道词频/技术趋势分析可用·需ufo GPU算力）

---

### B3 · 行业赛道扫描

#### L1 · 开源/免费层

**SearXNG**
- URL：https://github.com/searxng/searxng
- License：MIT
- 能力：聚合70+搜索引擎·隐私保护·已部署在probe底座
- 接入成本：已在役·零额外成本
- 合规：MIT
- **裁决：✅ 采纳**（已底座·检索层标配）

**GDELT**
- URL：https://www.gdeltproject.org
- 能力：全球新闻事件数据库·行业趋势/危机信号·BigQuery免费查询·15分钟更新
- 接入成本：免费·BigQuery按量（免费层1TB/月）
- 合规：开放数据集·免费商业使用
- **裁决：✅ 采纳**（已底座·行业新闻趋势赛道扫描）

**OSSInsight**
- URL：https://ossinsight.io
- License：Apache-2.0
- 能力：GitHub生态地图·技术赛道玩家分布·开发者趋势·Star增长曲线
- 接入成本：免费API
- 合规：Apache-2.0
- **裁决：✅ 采纳**（技术赛道竞品生态洞察）

**GitHub API / PyGithub**
- GitHub API URL：https://docs.github.com/en/rest
- PyGithub URL：https://github.com/PyGithub/PyGithub
- License：LGPL-3.0（PyGithub）
- 能力：仓库Star/Fork/提交/Issue·技术赛道生态·5,000 req/h（认证）
- 接入成本：免费·需token
- 合规：官方API·ToS允许研究用途
- **裁决：✅ 采纳**（技术赛道竞品开源生态必查）

**World Bank API**
- URL：https://data.worldbank.org/developers
- 能力：全球GDP/行业规模/贸易数据·宏观行业背景
- 接入成本：免费·CC-BY授权
- 合规：CC-BY·世界银行官方开放数据
- **裁决：✅ 采纳**（宏观行业规模锚点·权威免费）

**OECD API**
- URL：https://data.oecd.org/api/
- 能力：SDMX格式·OECD成员国行业统计·经济指标
- 接入成本：免费
- 合规：官方开放数据
- **裁决：✅ 采纳**（OECD成员国行业数据补充）

**OEC（Observatory of Economic Complexity）**
- URL：https://oec.world
- 能力：MIT Media Lab出品·全球贸易流向·产品/行业出口数据·跨境赛道分析
- 接入成本：免费API（有限制）
- 合规：MIT Media Lab开放数据
- **裁决：✅ 采纳**（跨境行业贸易视角·B3补充）

#### L2 · 商业服务层

**Crunchbase**
- 同B1描述·行业标签+融资轮次
- **裁决：⚠️ 待授权 R1**（与B1共用同一授权·B3行业赛道融资地图）

**Dealroom**
- 同B1描述·欧洲赛道细分最强
- **裁决：⚠️ 待授权 R1**（欧洲赛道专项·可与B1合并授权谈判）

**Tracxn**
- URL：https://tracxn.com
- 能力：细分赛道玩家最细·行业报告·有API·$500–$1,000/年
- 接入成本：$500–$1,000/年
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（B3性价比最高的商业源·细分赛道深度覆盖·优先于Dealroom）

#### L3 · 权威官方层

以上World Bank API和OECD API已计入L1/L3。Common Crawl（CC0·离线赛道技术词趋势·配合ufo GPU）：**✅ 采纳**。

---

### B4 · 电商价格销量（商业/选品视角·与G元惠消费者省钱视角不同）

#### L1 · 开源/免费层

**keepa Python SDK**
- URL：https://github.com/akaszynski/keepa
- License：MIT（SDK壳）
- 能力：Python封装层·调用Keepa后端API·Amazon价格历史/BSR排名/产品数据
- 接入成本：SDK本身MIT免费·**后端Keepa API需付费**
- 合规：MIT壳·后端需R1授权
- **裁决：✅ 采纳SDK层 · ⚠️ 后端R1**（接入层直接用·后端授权后即可启用）

**DataForSEO Amazon Merchant**
- URL：https://dataforseo.com/apis/amazon-api
- 能力：Amazon产品销量信号（bought_past_month）·is_best_seller·价格·评分·$0.001/task
- 接入成本：$50起充·按量付费
- 合规：商业API·平台担责
- **裁决：✅ 采纳**（B4首选低成本路径·DataForSEO已在B2待授权·合并授权可复用）

**开源价格追踪器（PriceGhost等自托管方案）**
- **裁决：❌ 弃**（自托管=probe自己爬目标电商页面·违反铁律"永不代爬"）

#### L2 · 商业服务层

**Keepa API**
- URL：https://keepa.com/#!api
- 能力：Amazon全品类价格历史·BSR时间线·售价/历史低价/折扣频率·~$19–$79/月
- 接入成本：约$19–$79/月（按token）
- 合规：商业API合同·Keepa官方
- **裁决：⚠️ 待授权 R1**（B4核心·Amazon价格历史深度数据唯一合规路径）

**Jungle Scout API**
- URL：https://www.junglescout.com/solutions/jungle-scout-api
- 能力：Amazon销量估算·关键词需求·市场份额·$79/月起
- 接入成本：$79/月起
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（Keepa授权后补充销量估算·可延后）

**Amazon Associates Product Advertising API（Creators API）**
- URL：https://affiliate-program.amazon.com/help/node/topic/GP38PJ6EUR6PFBEC
- 能力：产品信息/价格/评分/类目·免费·需Associates资质（30天内达成10笔销售）
- 接入成本：免费·需Associates账号资质
- 合规：官方API·**明确禁止建立独立比价服务**（条款限制）
- **裁决：✅ 采纳（有条件）**（自有内容站场景可用·禁用于独立比价竞品分析·使用前确认场景合规）

#### L3 · 权威官方层

**Amazon Selling Partner API（SP-API）**
- URL：https://developer-docs.amazon.com/sp-api
- 能力：卖家自有订单/库存/销售数据·免费·需卖家账号
- 接入成本：免费·需SP-API开发者资质
- 合规：官方API·**仅自有卖家数据·非竞品数据**
- **裁决：✅ 采纳（限自有场景）**（自有品牌卖家监控用·无法获取竞品真实销量）

---

### B5 · App情报

#### L1 · 开源/免费层

**RSSHub（App版本更新路由）**
- URL：https://github.com/DIYgod/RSSHub
- License：MIT
- 能力：部分路由支持App Store版本更新推送·版本迭代监控
- 接入成本：MIT·已底座或自托管
- 合规：MIT·基于官方公开信息
- **裁决：✅ 采纳**（App版本迭代监控·**不覆盖下载量/榜单排名**）

**google-play-scraper / app-store-scraper（npm·facundoolano）**
- **裁决：❌ 弃**（probe自跑=自己爬应用商店页面·违反ToS铁律·即使是第三方库也不可接受probe自调·若需榜单数据走SerpAPI等托管服务）

#### L2 · 商业服务层

**SerpAPI Google Play API**
- URL：https://serpapi.com/google-play-api
- 能力：Google Play榜单/评分/下载区间/评论·SerpAPI作为供应商担责·$75/月起
- 接入成本：$75/月起（Basic计划）
- 合规：SerpAPI商业合同·平台担责·probe不直接爬
- **裁决：⚠️ 待授权 R1**（Google Play竞品情报目前唯一合规路径·高优先）

**AppTweak API**
- URL：https://www.apptweak.com/app-store-marketing-tool/aso-api
- 能力：App Store + Google Play双平台·下载量/收入ML估算·ASO关键词·$69/月起
- 接入成本：$69/月起
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（双平台覆盖·精准下载估算·性价比高于Sensor Tower）

**Sensor Tower / data.ai（App Annie）**
- 成本：$30,000–$150,000/年·无self-serve
- **裁决：❌ 弃**（成本极高·大B专项预算才评估·data.ai已被Sensor Tower收购）

#### L3 · 权威官方层

**App Store Connect API**
- URL：https://developer.apple.com/app-store-connect/api/
- 能力：自有App下载量/收入/崩溃率/评分·免费
- 接入成本：免费·需Apple开发者账号
- 合规：Apple官方API·**仅自有App数据**
- **裁决：✅ 采纳（限自有场景）**（自有App监控·无法获取竞品数据）

**Google Play Developer API**
- URL：https://developers.google.com/android-publisher
- 能力：自有App下载/评论/评分/崩溃·免费
- 接入成本：免费·需Google Play开发者账号
- 合规：Google官方API·**仅自有App数据**
- **裁决：✅ 采纳（限自有场景）**（自有App监控·竞品数据需SerpAPI/AppTweak）

---

### B6 · 品牌舆情

#### L1 · 开源/免费层

**GDELT**
- URL：https://www.gdeltproject.org
- 能力：全球新闻情感分析（GCAM 2,200维情绪维度）·15分钟频率·已底座
- 接入成本：免费（BigQuery免费层）
- 合规：开放数据集
- **裁决：✅ 采纳**（B6层1首选·英文媒体危机预警·实时性强·中文覆盖弱）

**RSSHub**
- URL：https://github.com/DIYgod/RSSHub
- License：MIT
- 能力：微博话题/Reddit subreddit/新闻站点订阅·部分路由需平台API key
- 接入成本：MIT自托管·零成本·部分key需申请
- 合规：MIT·基于公开RSS/官方接口
- **裁决：✅ 采纳**（多渠道声量聚合·补GDELT平台盲区）

**PRAW（Python Reddit API Wrapper）**
- URL：https://github.com/praw-dev/praw
- License：BSD-2-Clause
- 能力：Reddit全量API·帖子/评论/subreddit订阅·100 req/min免费
- 接入成本：免费·需Reddit OAuth app注册·**商业大量使用需Reddit企业授权**
- 合规：BSD-2·小规模研究免费·大量商业需合同
- **裁决：✅ 采纳（小规模）**（Reddit舆情监控·注意用量边界）

**feedparser**
- URL：https://github.com/kurtmckee/feedparser
- License：MIT
- 能力：RSS/Atom/RDF解析·新闻源聚合·底座通用组件
- 接入成本：`pip install feedparser`·零成本
- 合规：MIT
- **裁决：✅ 采纳**（新闻RSS底座·B6检索管线标配）

**NewsCatcher API**
- URL：https://www.newscatcherapi.com
- 能力：90,000+新闻源·内置NLP情感分析·多语言·免费层100次/日·Starter $50/月
- 接入成本：免费层立即可用·Starter $50/月
- 合规：商业API（免费层有限制）
- **裁决：✅ 采纳**（B6性价比最高·**建议立即用免费层验证·是下一批接入P0候选**）

#### L2 · 商业服务层

**Brand24**
- URL：https://brand24.com
- 能力：实时社交/新闻监控·多语言AI情感分析·**提供MCP接口（独特价值）**·$249/月起
- 接入成本：$249/月起（Individual计划）
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（MCP接口使probe可直接集成·独特价值·优先级高）

**BrandMentions**
- URL：https://brandmentions.com
- 能力：全平台+10年历史舆情·$99/月起·功能与Brand24接近
- 接入成本：$99/月起
- 合规：商业API合同
- **裁决：⚠️ 待授权 R1**（比Brand24便宜60%·功能相近·二选一·建议先评估Brand24 MCP价值）

**Mention**
- URL：https://mention.com
- 成本：$599/月年付
- **裁决：❌ 弃**（性价比低·BrandMentions/$99已覆盖核心需求）

**Brandwatch / Meltwater**
- 成本：$25,000–$50,000/年
- **裁决：❌ 弃**（大B企业专项预算才评估·当前阶段ROI不成立）

#### L3 · 权威官方层

**Twitter/X API**
- URL：https://developer.x.com
- 能力：实时推文流·声量监控·关键词搜索·Basic $100/月（500K tweet/月）
- 接入成本：$100/月（Basic）
- 合规：官方API·付费层允许商业使用
- **裁决：⚠️ 待授权 R1**（实时声量不可替代·无其他合规路径覆盖X舆情）

**snownlp（本地中文情感）**
- URL：https://github.com/isnowfy/snownlp
- License：MIT
- 能力：中文情感分析·本地运行·无API调用成本
- 接入成本：`pip install snownlp`·零成本
- 合规：MIT·无数据出境风险
- **裁决：✅ 采纳**（补GDELT中文情感弱点·本地化中文舆情分析底座）

---

## 三、推荐首选源汇总表

| 子场景 | L1首选（立即可用） | L2首选（待授权） | L3权威 | MVP最小集 |
|--------|-----------------|---------------|--------|---------|
| B1 竞品全景 | edgartools（美股财务） + SpiderFoot（技术资产） | Crunchbase（融资情报） | SEC EDGAR API | edgartools + SEC EDGAR |
| B2 网站诊断 | PageSpeed Insights + sitespeed.io + asyncwhois | DataForSEO（流量估算） | Internet Archive | PageSpeed Insights + asyncwhois + waybackpy |
| B3 行业赛道 | SearXNG + GDELT + GitHub API | Tracxn（细分赛道） | World Bank + OECD API | SearXNG + GDELT + GitHub API + World Bank |
| B4 电商价格 | DataForSEO Amazon Merchant | Keepa API | Amazon SP-API（自有） | DataForSEO Amazon Merchant |
| B5 App情报 | RSSHub（版本监控） | SerpAPI Google Play | App Store Connect（自有） | SerpAPI Google Play（唯一覆盖路径） |
| B6 品牌舆情 | GDELT + NewsCatcher免费层 + feedparser | Brand24（MCP）或BrandMentions | Twitter/X API | GDELT + NewsCatcher + RSSHub + snownlp |

---

## 四、待授权清单

| 源 | 授权类型 | 子场景 | 成本 | 优先级 | 备注 |
|----|---------|--------|------|--------|------|
| **Crunchbase API** | R1商业付费 | B1·B3（共用） | $49/月起 | P0 | 融资/行业赛道首选·两场景共用授权 |
| **DataForSEO** | R1商业付费 | B2·B4（共用） | $50起充·按量 | P0 | 流量估算+Amazon商品·B2/B4共用·立即接入 |
| **SerpAPI Google Play** | R1商业付费 | B5 | $75/月起 | P0 | Google Play唯一合规路径 |
| **NewsCatcher Starter** | R1商业付费 | B6 | $50/月 | P1（先用免费层验证） | 免费层100次/日先验证·验证后升级 |
| **Brand24** | R1商业付费 | B6 | $249/月起 | P1 | MCP接口独特价值·评估后与BrandMentions二选一 |
| **BrandMentions** | R1商业付费 | B6 | $99/月起 | P1 | Brand24替代·若MCP不是必需则优先此 |
| **Keepa API** | R1商业付费 | B4 | $19–$79/月 | P1 | Amazon价格历史深度·DataForSEO接入后补充 |
| **Twitter/X API Basic** | R1商业付费 | B6 | $100/月 | P1 | 实时声量不可替代·无其他路径 |
| **OpenCorporates商业版** | R1商业付费 | B1 | £2,250/年 | P2 | 免费层先用·规模化后升级 |
| **AppTweak API** | R1商业付费 | B5 | $69/月起 | P2 | 双平台精准估算·SerpAPI接入后补充 |
| **Dealroom** | R1商业付费 | B1·B3 | €12,500/年 | P3 | 欧洲专项·非全球MVP不急 |
| **Moz API** | R1商业付费 | B2 | $49/月 | P3 | DA/PA·有DataForSEO后按需评估 |
| **BuiltWith API** | R1商业付费 | B2 | $144/年起 | P3 | 技术历史追踪·wappalyzergo够MVP |
| **Jungle Scout API** | R1商业付费 | B4 | $79/月起 | P3 | Keepa授权后再补 |

---

## 五、覆盖缺口与对策

### 结构性缺口（无合规替代路径）

| 缺口 | 子场景 | 性质 | 对策 |
|------|--------|------|------|
| **中国未上市企业工商数据** | B1 | 结构性·天眼查无公开API | R1授权天眼查企业API（Sprint4按ROI评估）·暂用GLEIF/Companies House覆盖境外主体 |
| **私有市场深度估值/融资** | B1 | 结构性·Crunchbase/Dealroom数据截止最后一轮 | 明示覆盖边界·Crunchbase授权后做到L2最优 |
| **创始人/高管LinkedIn数据** | B1 | 合规红线·LinkedIn无公开API且禁爬 | ❌永久缺口·明示不覆盖·人工检索兜底 |
| **真实App下载量** | B5 | 结构性·仅Apple/Google持有 | 只能用ML估算（AppTweak/SerpAPI）·报告明示"估算值" |
| **中国应用市场（华为/小米/OPPO）** | B5 | 结构性·无公开API | 暂不覆盖·报告明示中国Android市场盲区 |
| **微信小程序榜单/数据** | B5·B6 | 合规·微信封闭生态 | 暂不覆盖·人工周报补充 |
| **微信公众号/朋友圈舆情** | B6 | 合规·封闭生态无第三方API | 暂不覆盖·考虑新榜/清博指数（均为灰区·需法务确认） |
| **微博官方舆情API** | B6 | 需企业资质认证 | R4资质门·暂用RSSHub微博话题路由兜底 |
| **中国行业协会数据** | B3 | 结构性·无机器可读API | 人工PDF解析+定期手动更新 |
| **实时精准流量（SimilarWeb级）** | B2 | 成本问题·非技术限制 | DataForSEO作最优性价比替代·覆盖80%需求 |
| **跨境非Amazon电商（淘宝/拼多多/1688）** | B4 | 合规·无官方API | 暂不覆盖·明示Amazon-only范围 |
| **转化率/真实GMV** | B4 | 结构性·属卖家私有数据 | 仅能用SP-API看自有·竞品永远缺口 |

### 缺口补偿策略

1. **snownlp本地部署**（已列采纳）：补GDELT中文情感分析弱点，无API调用成本，B6中文舆情即时可用。
2. **wappalyzergo + GPL法务确认**：在法务确认前限内部使用，确认后可对外服务；同时备BuiltWith API作商业化保险。
3. **Common Crawl离线分析**（配ufo GPU）：B3赛道离线词频/技术趋势批处理，覆盖实时API无法规模化扫描的场景。
4. **OpenCorporates免费层先跑**：200次/月够小规模原型验证，商业规模化时升级。

---

## 六、对接批次建议

### Batch 1（立即接入·零成本·MVP地基）

| 源 | 子场景 | 接入方式 | 预计工时 |
|----|--------|---------|---------|
| edgartools | B1 | `pip install edgartools` | 0.5天 |
| PageSpeed Insights API | B2 | 官方API·申请免费key | 0.5天 |
| asyncwhois + dnspython | B2 | `pip install` | 0.5天 |
| waybackpy | B2 | `pip install` | 0.5天 |
| sitespeed.io | B2 | Docker部署·ufo机 | 1天 |
| GitHub API + PyGithub | B3 | 已有token·直接配 | 0.5天 |
| World Bank API + OECD API | B3 | 免费·注册key | 0.5天 |
| NewsCatcher免费层 | B6 | 注册key·100次/日开始验证 | 0.5天 |
| snownlp | B6 | `pip install snownlp` | 0.5天 |
| RSSHub（B6路由补充） | B6 | 复用底座·配路由 | 0.5天 |

**Batch 1合计**：~6天工程量·零授权成本·覆盖B1/B2/B3/B6基础层

### Batch 2（低成本授权·关键缺口补全）

| 源 | 子场景 | 成本 | 前置条件 |
|----|--------|------|---------|
| DataForSEO | B2·B4（共用） | $50起充 | R1授权·共用 |
| Crunchbase API | B1·B3（共用） | $49/月 | R1授权·共用 |
| SerpAPI Google Play | B5 | $75/月 | R1授权 |
| Keepa SDK接入（后端先mock） | B4 | SDK免费 | 先跑通接入层·后端等Keepa授权 |

**Batch 2合计**：约$174/月·覆盖B4/B5关键缺口·需R1授权启动

### Batch 3（提升层·按ROI决策）

| 源 | 子场景 | 成本 | 决策依据 |
|----|--------|------|---------|
| Keepa API真实后端 | B4 | $19–$79/月 | B4使用量验证后再升级 |
| Brand24 或 BrandMentions | B6 | $99–$249/月 | MCP接口价值验证后二选一 |
| Twitter/X API Basic | B6 | $100/月 | X舆情需求频率验证后授权 |
| AppTweak API | B5 | $69/月 | SerpAPI跑稳后补精准估算 |

### Batch 4（大B专项·按规模评估）

- Dealroom（€12,500/年）：欧洲赛道规模化专项
- 天眼查企业API：中国本土商业情报规模化
- Tracxn（$500–$1,000/年）：细分赛道深度覆盖

---

> 本文件为调研证据层 · 仅记录数据源可行性结论
> 架构决策和实现规范见上游文档：[赛道注册表架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md)
> 下一步：[对接批次实施计划](datasource-research-onboarding-batch-plan-v1.0.md)

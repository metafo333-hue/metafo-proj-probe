# probe · 数据源接入核验（标准19）+ 源的源去重图谱 v1.0

> 日期：2026-06-08 · 补 B8/B9 两项盲点 · 配套金融F+自媒体A 5 份数据源清单
> 性质：**接入前工程交付物**（非调研）· 基于已有调研事实整理
> 🔴 诚实标注：gate19 的 `verified`（已验证可用）项**必须真接入实测才能确认**，未接入源一律标「待S1实测」，不假装核验通过。仅 rejected 源不核验（已拒）。

---

## 第一部分 · B8 · 标准19（gate19）逐源核验

### 核验七项（来自 registry.py `GATE_19`）
M=mature成熟 · V=verified已验证可用 · A=data_authentic数据真实 · Q=vendor_qualified供应商资质 · Au=authorized已获授权 · L=license_ok许可合规 · S=security_ok安全
> 放行规则：七项全 ✓ 且 ledger status=active 才被 registry 放行。当前**无源 status=active**（registry.py 实况），下表为接入前预核验，最后一列给"放行裁定"。

### 1.1 金融 F · ✅ 免费/开源源（建议 S1-S2 接入）

| 源 | M | V | A | Q | Au | L | S | 放行裁定 |
|----|---|---|---|---|----|---|---|---------|
| **edgartools**(SEC封装) | ✓ | 待测 | ✓ | ✓ | ✓ | ✓MIT | ✓ | S1可放行（实测后）|
| **SDMX-client**(IMF/OECD/ECB/Eurostat/BIS/WB) | ✓ | 待测 | ✓ | ✓ | ✓ | ✓Apache2 | ✓ | S1可放行 |
| **FRED** | ✓ | 待测 | ✓ | ✓ | ✓ | ⚠️再分发限制 | ✓ | S1可放行+加免责声明 |
| **World Bank**(wbgapi) | ✓ | 待测 | ✓ | ✓ | ✓ | ✓CC-BY-4.0 | ✓ | S1可放行 |
| **US BLS / BEA / Treasury** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓公有领域 | ✓ | S1可放行 |
| **Frankfurter**(外汇) | ✓ | 待测 | ✓ | ✓ | ✓ | ✓明示可商用 | ✓ | S1可放行（最干净）|
| **CCXT**(加密) | ✓ | 待测 | ✓ | ✓ | ⚠️逐CES核ToS | ✓MIT | ✓ | S1可放行+标redistribute:false |
| **交易所官方衍生品端点**(Binance/Bybit/OKX) | ✓ | 待测 | ✓ | ✓ | ⚠️行情ToS | ✓ | ✓ | S1可放行（仅自用决策）|
| **Hyperliquid Info API** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓公开 | ✓ | S1可放行 |
| **DeFiLlama** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓公开 | ✓ | S1可放行 |
| **Alternative.me Fear&Greed** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓免费可商用 | ✓ | S1可放行 |
| **Etherscan API V2** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓商用允许 | ✓需key | S1可放行（免费档）|
| **The Graph 自托管** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓MIT+Apache2 | ✓ | S2（需算力起索引器）|
| **Fed/ECB 官方RSS** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓公开 | ✓ | S1可放行 |
| **gdelt-doc-api** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓MIT | ✓ | S1可放行 |
| **Companies House**(英) | ✓ | 待测 | ✓ | ✓ | ✓ | ✓UK Open Gov | ✓需key | S2可放行 |
| **cninfo 巨潮** | ✓ | 待测 | ✓ | ✓官方披露 | ✓ | ✓证监会指定 | ✓ | S2可放行（官方端点）|
| **PatentsView / Lens.org** | ✓ | 待测 | ✓ | ✓ | ✓ | ✓CC-BY/学术免费 | ✓ | S2可放行 |
| **富途 Futu OpenAPI**(A股LV1) | ✓ | 待测 | ✓ | ✓持牌券商 | ✓ | ✓正规分发 | ✓需账户 | S3可放行（A股底座）|
| **pbc-LPR / NBS / chinawealth / amac / sge** | ✓ | 待测 | ✓ | ✓官方 | ⚠️控频 | ✓官方公开 | ✓ | S2-S3（需自写解析+控频）|
| **EIA / USDA / LME免费档** | ✓ | 待测 | ✓ | ✓官方 | ✓ | ✓公有领域/官方 | ✓ | S2可放行 |
| **国内期货 CTP**(tqsdk) | ✓ | 待测 | ✓ | ✓持牌期货公司 | ✓ | ✓开户授权 | ✓需账户 | S3（开户拿一档）|

> 共性：免费官方/开源源 6 项基本 ✓，**唯一卡点是 V（verified）必须真接入实测**——这印证了"现在空填意义不大、必须 S1 接入时逐源跑通"。

### 1.2 金融 F · ⚠️ 付费源（待 R1 授权 + 实测）

| 源 | M | V | A | Q | Au | L | S | 放行裁定 |
|----|---|---|---|---|----|---|---|---------|
| **天眼查 / 企查查 API** | ✓ | 待测 | ✓ | ✓官方商业 | ⚠️R1付费 | ✓商业授权 | ✓需key | 待R1+人物字段不落库 |
| **Alpha Vantage** | ✓ | 待测 | ✓ | ✓NASDAQ授权 | ⚠️R1(商用) | ✓持牌再分发 | ✓需key | 待R1（真上美股行情时）|
| **tushare Pro** | ✓ | 待测 | ⚠️仅Pro | ✓自建库 | ⚠️积分/付费 | ⚠️核条款 | ✓需token | 待R8攒积分·禁旧org接口 |
| **Trading Economics** | ✓ | 待测 | ✓ | ✓ | 🔴试用自动扣费 | ✓商业 | ✓需key | **必走R1·禁默认试用** |
| **Finnhub / Twelve Data** | ✓ | 待测 | ✓ | ✓ | ⚠️R1 | ⚠️多为内部用 | ✓需key | 待R1·再分发需谈 |
| **CoinGecko** | ✓ | 待测 | ✓ | ✓ | ⚠️R1 | ✓商用需署名 | ✓需key | 待R1·禁白标 |
| **Polygon.io / Nasdaq Data Link** | ✓ | 待测 | ✓ | ✓ | ⚠️R1 | ⚠️按数据集 | ✓需key | 待R1·ROI待评 |
| **Coinglass**(清算热图) | ✓ | 待测 | ✓ | ✓ | ⚠️R1($299商用) | ⚠️禁再分发 | ✓需key | 先用免费端点验证再升档 |
| **Glassnode/CryptoQuant/Nansen/MistTrack** | ✓ | 待测 | ✓ | ✓ | ⚠️R1 | ⚠️标签禁再分发 | ✓需key | 仅内部决策·禁再分发 |

### 1.3 自媒体 A · 源核验

| 源 | M | V | A | Q | Au | L | S | 放行裁定 |
|----|---|---|---|---|----|---|---|---------|
| **YouTube Data API v3** | ✓ | 待测 | ✓ | ✓Google官方 | ✓ | ✓ | ✓需key | S1可放行（替代tikhub的YT）|
| **YouTube/TikTok/X/IG 官方oEmbed** | ✓ | 待测 | ✓ | ✓官方 | ✓ | ✓ | ✓ | S1可放行（免key）|
| **Reddit API + .rss** | ✓ | 待测 | ✓ | ✓官方 | ✓ | ✓ | ✓OAuth | S1可放行 |
| **Mastodon API** | ✓ | 待测 | ✓ | ✓联邦官方 | ✓ | ✓MIT | ✓ | S1可放行（纯增量）|
| **Threads API** | ✓ | 待测 | ✓ | ✓Meta官方 | ✓ | ✓ | ✓token | S1可放行（舆情蓝海）|
| **iTunes API + 播客RSS** | ✓ | 待测 | ✓ | ✓Apple/公开 | ✓ | ✓ | ✓ | S1可放行（合规✅✅最高）|
| **巨量算数** | ✓ | 待测 | ✓ | ✓字节官方 | ⚠️受控读取 | ✓ | ✓ | S2（禁爬榜单页）|
| **roberta开源检测** | ⚠️老旧 | 待测 | ⚠️对新模型弱 | ✓ | ✓ | ✓MIT | ✓自托管 | S2兜底（粗筛）|
| **tikhub** | ✓ | 待测 | ⚠️逆向封装 | ⚠️授权第三方 | ⚠️R1+R8 | ⚠️合规债 | ✓需key | 待R1·标compliance_debt |
| **微博商业数据API** | ✓ | 待测 | ✓ | ✓官方 | ⚠️企业资质+付费 | ✓ | ✓需key | 待R1+资质 |
| **Copyleaks / Originality** | ✓ | 待测 | ✓ | ✓ | ⚠️R1 | ✓商业 | ✓需key | 待R1（AI检测）|
| **EnsembleData / 新榜 / 飞瓜 / twitterapi.io / Spotify / 喜马拉雅 / 蒲公英** | ✓ | 待测 | ⚠️部分含自爬 | ⚠️ | ⚠️R1/资质 | ⚠️逐家核 | ✓需key | 待R1·按需 |

> 自媒体 gate19 关键分野：**官方源（YouTube/Reddit/Mastodon/Threads/oEmbed/播客RSS）的 A（数据真实）+Au（授权）干净**；**第三方授权源（tikhub/新榜/飞瓜）的 A 项打⚠️（含逆向/自爬成分）**——这正是合规债所在。

---

## 第二部分 · B9 · "源的源"去重图谱

> 目的：避免重复接入同一底层数据。多个库/源底层读同一数据时，**只接最干净的一个入口**，其余标注"同源"避免冗余。

### 2.1 底层数据源 → 上层接入入口 映射

```
【底层真实数据源】              【上层接入入口】                    【去重裁定】
─────────────────────────────────────────────────────────────────────────
SEC EDGAR(美政府)        ┌─ edgar(裸submissions端点·已接)
                         └─ edgartools(MIT封装·XBRL/13F)      → 接 edgartools 为主，edgar 端点保留兜底（同源·能力互补不算重复）

东方财富/新浪/同花顺网页  ┌─ akshare(_em/_sina 爬取) ❌
                         ├─ tushare旧org版(爬) ❌
                         └─ 东财Choice官方API(¥5000/年) ✅     → 全部同源(东财)·爬取入口 rejected·要东财数据走官方 Choice

Yahoo Finance 非公开端点  └─ yfinance(抓取) ❌                  → 单一来源·rejected·海外行情走 Frankfurter/FRED/官方

SDMX 协议(国际机构)       └─ sdmx1/pandaSDMX 一库接 6 机构      → IMF/OECD/Eurostat/ECB/BIS/WorldBank 同协议·一个 client 全覆盖·勿逐个写

各 CEX 行情(交易所)       ┌─ CCXT(聚合100+所·现货为主)
                         └─ 交易所官方衍生品端点(资金费率/OI/清算) → CCXT 补现货，官方端点补衍生品深度·互补不重复(同源但维度不同)

链上数据(公链·本身公开)   ┌─ DeFiLlama(TVL/费率聚合)
                         ├─ Etherscan(地址/合约事件)
                         ├─ The Graph(DEX swap)
                         └─ Covalent/Blockchair/Alchemy(多链)  → 同底层(链上)·按维度分工·避免 Covalent+Blockchair+Alchemy 三个多链浏览器重复接(选1个)

中国企业工商(国家公示系统) ┌─ 天眼查 API(官方授权)
                         ├─ 企查查 API(官方授权·备选)
                         └─ businessInfo-api(爬gsxt) ❌        → 天眼查/企查查同底层(公示系统)·接1个为主1个备份·爬取入口rejected

A股行情(交易所)          ┌─ 富途/老虎 OpenAPI(券商分发·免费LV1)
                         ├─ 东财Choice(机构¥5000)
                         └─ Wind/iFinD(机构数万) ❌成本         → 同底层(交易所行情)·按成本选富途免费LV1为主入口

巨潮/证监会披露          ┌─ cninfo 官方端点 ✅
                         └─ cninfo Scrapy爬虫类repo ❌         → 同源·官方端点放行·爬虫repo rejected

播客内容(发布方RSS)      ┌─ iTunes API(发现feedUrl)
                         └─ 播客RSS(直读)                     → iTunes 做发现→直读RSS·同链路·非重复(发现层+数据层)

多平台自媒体(各平台)      ┌─ tikhub(逆向聚合·全平台)
                         ├─ YouTube官方API(YT)
                         ├─ Reddit官方(Reddit)
                         └─ Mastodon/Threads官方             → tikhub 与官方源对同一平台时(如YT)·优先官方·tikhub从YT撤出收窄到国内任意达人+B站
```

### 2.2 去重裁定汇总（避免重复接入）

| 底层数据 | 选定主入口 | 撤掉/备份的冗余入口 |
|---------|-----------|-------------------|
| SEC EDGAR | edgartools（能力最全）| edgar 裸端点降为兜底 |
| 国际宏观 | SDMX 单 client | 勿对 IMF/OECD/ECB 逐个写 connector |
| 东财数据 | 东财 Choice 官方（需要时）| akshare/tushare旧版/东财逆向 全 rejected |
| 海外行情 | Frankfurter/FRED/官方 | yfinance rejected |
| 加密多链浏览器 | 选 1 个（Etherscan 或 Covalent）| 勿同时接 Covalent+Blockchair+Alchemy 三个 |
| 中国工商 | 天眼查 API（主）| 企查查（备份·勿双接）· businessInfo-api rejected |
| A股行情 | 富途 OpenAPI（免费LV1）| Wind/iFinD 成本 reject · Choice 仅全市场LV2时 |
| YouTube | 官方 Data API | tikhub 从 YT 撤出 |
| 巨潮披露 | cninfo 官方端点 | 所有 cninfo 爬虫 repo rejected |

### 2.3 关键结论
- **同源去重省 3 处冗余**：① SDMX 一库替代 6 个 connector ② 加密多链浏览器选 1 不选 3 ③ 工商天眼查/企查查接 1 备 1。
- **同底层不同维度不算重复**：CCXT(现货)+交易所官方端点(衍生品)、edgar+edgartools、iTunes(发现)+RSS(数据)——这些是互补分工，全接。
- **爬取入口与官方入口同源时**：一律走官方、爬取入口 rejected（akshare/tushare旧版/cninfo爬虫/businessInfo-api 全是这个模式）。

---

## 落地提示
- B8 的 `verified` 项是**唯一无法预填的硬项**——S1 接入每个源时跑通一次真实调用，回填 ledger.yaml 的 gate19.verified=true，status 才能转 active。
- B9 去重图谱应在 S1 写 registry 适配器前对照，避免重复实现同源 connector。
- 两项均已从"调研盲点"转为"S1 接入执行清单"，盲点清零。

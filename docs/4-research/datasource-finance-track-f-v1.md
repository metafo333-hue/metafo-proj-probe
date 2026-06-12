# probe · 金融赛道 F · 数据源完整清单 v1.0（含 v1.1 盲点补充合并）

> 日期：2026-06-08 · 方法：先整理分类框架 → 合规清洗 → GitHub 4 子域扇出调研（opus×4）+ 主代理去重证伪
> 合规框架：probe 数据来源铁律（**核心红线：不自己爬数据**——不自建爬虫/不模拟登录；只走官方 API 或官方授权第三方或开源自托管或公开数据集；个保法最小必要；绕反爬由第三方供应商担责）
> 状态口径：✅ live 可接（官方/开源干净·零或可控成本） · ⚠️ pending（待 key / R1 付费 / 核条款） · ❌ rejected（合规红线或 ROI 不成立）

---

## 一、赛道定位与子域拆解

金融赛道 F = probe 前期两大主攻行业之一（与自媒体 A 并列）。现有台账金融几乎空白（仅 edgar/opencorporates/gdelt 沾边，且 edgar/opencorporates 误标 D4），本清单为**从零建栈**。

| 子域 | 范围 | 现状 |
|------|------|------|
| **F①·行情与交易** | 证券/加密/外汇/大宗/债券·K线/盘口/链上/衍生品·与 boss8001 契合 | 完全空白 |
| **F②·宏观与政策舆情** | 经济指标/央行/政策法规/监管处罚/金融新闻/经济日历 | gdelt 部分覆盖舆情 |
| **F③·企业与一级市场** | 工商/财报/投融资/司法风险/专利/评级·海内外双主体 | edgar/opencorporates 沾边(归类错) |
| **F④·个人理财与产品** | 基金/理财/保险/存贷利率/贵金属零售·C 端比价 | 完全空白 |

---

## 二、信息域映射与扩域建议

现有 D11「企业/财务情报」一域装不下金融全栈（行情/利率/汇率/基金 ≠ 企业财务）。**建议任务 2 设计阶段扩域**：

| 域 | 现状 | 建议 |
|----|------|------|
| **D11 企业/财务情报** | 已有（但 edgar/opencorporates 误标 D4） | 保留装企业工商/财报/投融资·**修正 edgar/opencorporates → D11** |
| **D13 金融行情/市场数据（新增）** | 无 | 装行情/K线/汇率/利率/链上/衍生品/基金净值 |
| **D14 宏观/政策/监管（新增）** | 无 | 装宏观指标/央行/政策法规/监管处罚/经济日历 |

> 归类修正（明确 bug）：`ledger.yaml:177` edgar、`:192` opencorporates 现标 `domain: [D4]`，应改主域 `[D11]`（edgar 可留 D4 次标签）。任务 2 落地时一并改。

---

## 三、🔴 主代理证伪裁定（三路 agent 判定冲突的源）

子域① / ③ / ④ 对以下三个高人气中国/聚合数据库给出**互相矛盾**的合规判定，主代理基于证据统一裁定：

| 源 | 子域①判 | 子域③判 | 子域④判 | **统一裁定** | 依据 |
|----|--------|--------|--------|-----------|------|
| **akshare**（20k★ MIT） | ❌爬东财/新浪 | ✅聚合官方公开接口 | ❌逆向爬网页 | **❌ rejected** | 多路一致核实其 `_em`/`_sina` 后缀接口本质=抓东方财富/新浪网页（东财 ToS 禁爬+有反爬），代码 MIT≠数据合规。整库混杂难逐接口治理→作为「库」判 ❌。若确需其中某个真属官方公开 API 的接口，**直接对接该官方源**，不经 akshare |
| **tushare**（13k★） | ❌ToS禁商用 | ✅Pro自建库 | ✅Pro自建库 | **⚠️ pending（仅 Pro·非旧 org 版）** | tushare **Pro**（2018 后）是平台自有数据库服务（非实时爬网页），合规底子可；但有积分门槛+商用条款。子域①"禁商用"过绝对——Pro 商业版是付费授权可商用。**只用 tushare.pro 接口，禁旧 tushare.org 爬虫接口** |
| **yfinance**（24k★ Apache2） | ❌Yahoo ToS | — | ⚠️仅研究 | **❌ rejected（商用）** | 抓 Yahoo 非公开端点，Yahoo ToS 明文 personal-use-only，作者自述灰色地带。可作本地研究锚点，**禁进 probe 生产/商用链路**。海外基金/ETF 走 Frankfurter/FRED/官方 feed 替代 |

**通用原则**：开源库的**代码许可证（MIT/Apache）≠ 数据使用权**。数据权由上游源 ToS 决定。同一库接 A 源合规、接 B 源可能违规——必须逐上游源核 ToS。

---

## 四、✅ 建议优先接入清单（官方/开源干净 · 零或可控成本）

> **源数口径**：本主表 19 源（首轮优先接入）+ 附录补充（加密链上/A股/大宗等，见下「增补后的 F 赛道总览」）= **合计 27+ 源**。各处引用「27+源」即指此合计。

| # | 源名 | 子域 | 厂商/repo | 接入方式 | 许可证 | 成本 | 权威 | 信息域 | 备注 |
|---|------|------|----------|---------|--------|------|------|--------|------|
| 1 | **edgartools** | F③ | dgunning/edgartools 2.3k★活跃 | 开源SDK封装SEC EDGAR | MIT | 免费无key | 10 | D11 | 补强现有 edgar(裸端点)·XBRL财报/13F/内部人交易·**最高ROI** |
| 2 | **SDMX 统一client** | F② | khaeru/sdmx · pandaSDMX 1.6k★ | 开源·一库接IMF/OECD/Eurostat/ECB/BIS/WorldBank | Apache-2.0 | 免费 | 9 | D14 | **一鱼多吃·6+国际机构·ROI最高** |
| 3 | **FRED** | F①② | mortada/fredapi | 官方API免费key | 数据ToS限再分发 | 免费 | 10 | D13/D14 | 84万经济序列·**须加"非联储背书"免责声明**·内部分析可/对外再分发原序列逐序列核版权 |
| 4 | **World Bank** | F② | tgherzog/wbgapi | 官方API无需key | client MIT·数据CC-BY-4.0 | 免费 | 9 | D14 | 合规最干净宏观源·明确可商用 |
| 5 | **US BLS / BEA** | F② | OliverSherouse/bls · us-bea/beaapi | 官方API | 美政府公有领域 | 免费 | 10 | D14 | 就业/CPI/GDP·可商用 |
| 6 | **US Treasury Fiscal Data** | F① | fiscaldata.treasury.gov | 官方API免key | 公有领域 | 免费 | 10 | D13 | 国债收益率曲线CMT |
| 7 | **Frankfurter** | F① | lineofflight/frankfurter | 官方API(源ECB+84央行) | 开源·**明示可商用** | 免费无key | 9 | D13 | 外汇维度首选·少数白纸黑字允许商用再分发 |
| 8 | **CCXT** | F① | ccxt/ccxt 42.8k★ | 开源聚合100+CEX | MIT(代码) | 免费 | 9 | D13 | 加密行情标配·**仅boss8001内部决策·禁对外行情分发**(守各CEX ToS)·标注 redistribute:false |
| 9 | **DeFiLlama** | F① | DefiLlama / py wrapper | 官方公开API免key免限流 | 公开免费 | 免费 | 8 | D13 | 链上/DeFi/TVL/资金费率·链上数据本身公开·零合规负担 |
| 10 | **Fed/ECB 官方 RSS** | F② | 官方RSS | 公开RSS | 公开 | 免费 | 10 | D14 | 央行政策即时公告·零风险 |
| 11 | **gdelt-doc-api** | F② | alex9smith/gdelt-doc-api 219★ | 开源(现有gdelt增强) | MIT | 免费 | 7 | D14 | 宏观主题情感timeline·复用已有gdelt基座 |
| 12 | **Companies House** | F③ | UK Gov官方 | 官方API免费key | UK Open Gov | 免费 | 10 | D11 | 英国工商/股权/filing·补强opencorporates |
| 13 | **cninfo 巨潮** | F③④ | 官方hisAnnouncement端点 | 官方公开JSON端点 | 证监会指定披露 | 免费 | 10 | D11 | A股年报/IPO/基金披露·**只用官方端点·禁GitHub上Scrapy/Selenium爬虫repo** |
| 14 | **PatentsView / Lens.org** | F③ | USPTO官方 · Cambia | 官方API | CC-BY-4.0 / 学术免费 | 免费 | 9-10 | D11/D12 | 专利·中美覆盖 |
| 15 | **pbc/chinamoney LPR** | F④ | 央行/CFETS官方 | 官方公开 | 官方公开 | 免费 | 10 | D13 | LPR 1Y/5Y权威值·贷款比价锚点 |
| 16 | **chinawealth 中国理财网** | F④ | 金融监管总局指定·理财登记中心 | 官方公开查询页(自写解析) | 官方披露 | 免费 | 10 | D11 | 银行理财产品唯一官方底座 |
| 17 | **amac 基金业协会** | F④ | 基金业协会官方公示 | 官方公示页 | 官方公示 | 免费 | 10 | D11/D8 | 私募管理人/备案状态 |
| 18 | **sge 上海黄金交易所** | F④ | 上金所官方 | 官方延时行情 | 交易所官方(延时) | 免费 | 9 | D13 | 上海金基准价/AU9999 |
| 19 | **国家统计局 NBS** | F②④ | data.stats.gov.cn V2.0无鉴权 | 官方接口 | 官方公开 | 免费 | 10 | D14 | 中国宏观·⚠️控频+核官网声明 |

> 中国官方公开源（#13/15/16/17/18/19）合规依据=查询官方公开披露平台（非逆向），但多无标准 API、须自写解析 + 严格控频 + 不触动态反爬接口；监管处罚（CSRC/NFRA/PBOC）只走官方公开页/RSS。

---

## 五、⚠️ pending 清单（待 key / R1 付费 / 核条款）

| 源 | 子域 | 接入 | 成本 | 合规要点 | 优先级 |
|----|------|------|------|---------|--------|
| **天眼查 API** | F③ | 官方授权第三方API | ¥0.05/次起·免费500/日 | 官方商业API·声明只采公开数据·非爬虫·**中国企业风险维度唯一全维路径**·人物字段不落库 | 高(R1) |
| **企查查 API** | F③ | 官方授权第三方API | 免费100/日·超付费 | 天眼查备选·同合规等级 | 中(R1) |
| **Alpha Vantage** | F① | 官方API | 免费25/日·商用付费 | **唯一NASDAQ正式授权再分发的持牌美股源**·合法上美股实时行情正路(替yfinance灰产) | 高(真上证券行情时) |
| **tushare Pro** | F④ | 官方平台API | 积分门槛·商用付费 | 仅Pro接口·基金净值/A股·非旧org爬虫版 | 中(R8注册攒积分) |
| **Trading Economics** | F② | 官方授权第三方 | 付费·**试用自动转付** | 经济日历行业标准·**禁默认开试用·必走R1报价确认** | 中(R1) |
| **Finnhub / Twelve Data** | F① | 官方API | 免费层有限 | 海外股票基本面·授权多为"仅内部用"·再分发需谈 | 中 |
| **CoinGecko** | F① | 官方API | 免费10k/月·须署名 | 加密聚合·免费层可商用须"Powered by CoinGecko"·禁白标 | 中 |
| **Polygon.io / Nasdaq Data Link** | F① | 官方API | $99+/mo / 免费40集 | 持牌实时美股深度·高成本·按数据集核授权 | 低(ROI待评) |
| **IT桔子** | F③ | 官方API需商务 | 未公开·需报价 | 中国创投/投融资·待商务对接 | 低 |

---

## 六、❌ rejected 清单（合规红线 / ROI 不成立）

| 源 | 判定理由 | 触犯 |
|----|---------|------|
| **akshare 全系** | 底层抓东财/新浪/同花顺网页+破反爬 | 铁律①② |
| **tushare 旧 org 版爬虫接口** | 部分接口仍爬网页 | 铁律① |
| **yfinance** | 抓Yahoo非公开端点·ToS personal-only | 铁律①+再分发版权 |
| **东财/天天基金 民间逆向API** | 逆向 fund.eastmoney 网页 | 铁律① |
| **businessInfo-api**(Litre-WU 120★) | 爬天眼查/企查查/gsxt+proxy轮换绕反爬 | 铁律①② |
| **cninfo Scrapy/Selenium 爬虫类 repo** | 自建爬虫抓巨潮(有官方端点替代) | 铁律① |
| **juhe/jisuapi/nowapi 聚合** | 数据源不透明(可能二次爬)·官方源已覆盖 | 数据真实性存疑 |
| **OpenBB（嵌入产品）** | AGPLv3 传染·作网络服务须开源全部代码 | 商业产品化污染红线·**仅本地调研参考·禁import进产品** |
| **Crunchbase API** | 2026取消免费层·全量需Enterprise $50k+/年 | ROI不成立(合规✅但成本) |
| **morningstar 晨星** | 无开放API+$99-545/年(R1)·暂缓 | 评级维度先用cninfo/tushare替代 |
| **任何"天眼查/企查查数据"第三方代爬包** | 非官方授权·本质代爬(涉企业+人物) | 铁律①+个保法 |

**🔴 硬红线**：人物背调/法人/股东个人信息——天眼查/企查查 API 涉个人字段**只即时查不落库**（个保法最小必要·普通≥5000/敏感≥500 条入刑）。

---

## 七、与现有 12 源关系 + 接入优先级

- **纯新增**：F 赛道全部为增量，不替代任何现有源。现有 12 源（见 ledger.yaml）无一覆盖行情/利率/汇率/基金/宏观指标。
- **补强**：edgartools 封装现有 edgar（能力远超裸端点）；Companies House + 天眼查补强 opencorporates 成"全球/英国/中国"三层工商；FRED/Treasury 与 gdelt 互为印证（硬指标 vs 事件信号）。
- **与 boss8001 协同**：CCXT + DeFiLlama 服务交易决策，但守职能隔离 T3——probe 调研数据落 metafoclaw 业务库，交易实时数据走 boss8001-a 自有 PG，不混库。

### 建议 Sprint 排期（零 R1 优先）
- **Sprint 1（零成本·即接）**：edgartools / SDMX-client / FRED / WorldBank / BLS / BEA / Treasury / Frankfurter / DeFiLlama / CCXT / Fed-ECB-RSS / gdelt-doc — 12 个 ✅ 源，纯官方/开源，零付费红线。
- **Sprint 2（中国官方公开源·需自写解析+控频）**：cninfo / pbc-LPR / amac / chinawealth / sge / NBS / PatentsView。
- **Sprint 3（R1 付费授权·按 ROI 报价确认）**：天眼查 → Alpha Vantage → Trading Economics → tushare Pro → CoinGecko。
- **暂缓**：Polygon / Crunchbase / morningstar（高成本 ROI 待评）。

---

## 八、关键依据信源（节选）
ccxt.com · alphavantage.co/realtime_data_policy · developers.binance.com PROD-TERMS · fred.stlouisfed.org/docs/api/terms_of_use · frankfurter.dev · fiscaldata.treasury.gov · github.com/dgunning/edgartools · github.com/khaeru/sdmx · open.tianyancha.com · openapi.qcc.com · github.com/akfamily/akshare(rejected依据) · github.com/Litre-WU/businessInfo-api(rejected) · tradingeconomics.com/api/pricing · api-docs.defillama.com


---

# 附 · v1.1 盲点补充合并（加密链上衍生品 / A股真空 / 大宗能源 / 合规红线 / 成本总账）

> 2026-06-08 并入 · 原为 datasource-finance-track-f-v1.1-addendum.md（已合并删除）
## A · 加密链上与衍生品深度（首轮只接 CCXT+DeFiLlama，这里补深度）

**核心发现**：交易决策最值钱的**衍生品三件套（资金费率/未平仓 OI/清算流）在交易所官方 API 就免费提供**，首轮因只接 CCXT（现货为主）遗漏。两条轨：链上原始数据多数公开免费 ✅，聚合分析服务多数商业付费 ⚠️。

### ✅ 建议立即接（全零成本）

| # | 源 | 接入 | 数据 | 合规 | 备注 |
|---|----|------|------|------|------|
| 1 | **交易所官方衍生品端点**(Binance/Bybit/OKX) | 官方REST/WS免key | **资金费率历史/OI/标记价/清算流** | ✅行情可商用 | 首轮最大遗漏·第一手·对 boss8001 套利/清算预判直接喂决策 |
| 2 | **Hyperliquid Info API** | 无key无签名 | 链上perp资金费率/OI | ✅公开 | 最大链上永续DEX·与CEX交叉验证 |
| 3 | **Alternative.me Fear&Greed** | 公开API免key | 恐惧贪婪指数 | ✅免费可商用 | 宏观情绪择时输入 |
| 4 | **The Graph 自托管 graph-node** | 自托管GraphQL | DEX swap/流动性/合约事件 | ✅MIT+Apache2 | 数据归属自有·符合"开源自托管"铁律·需 ufo 算力起索引器 |
| 5 | **Etherscan API V2 + DefiLlama 扩端点** | 官方API免费档 | 多链地址/合约事件 + 资金费率/稳定币 | ✅商用允许 | Etherscan 免费档2025缩水(90%链·10万/日)·DefiLlama已接补端点零成本 |

### ⚠️ cataloged 可选付费（聚合分析服务·标签禁再分发）

Blockchair/Covalent/Alchemy/Infura（多链/RPC·免费档够用）· Dune（SQL导出·须署名）· **Coinglass 清算热图**（$299/mo commercial·唯一值得付费·但基础清算流官方端点已免费拿，验证ROI后再升档）· Glassnode/CryptoQuant/Santiment/Nansen/Whale Alert（链上分析·商业档·boss8001内部决策用，禁再分发）· **MistTrack慢雾**（AML地址风险·归D14·试用足够）

### ❌ rejected
Chainalysis/TRM Labs（机构级合同·boss8001体量未到）· Laevitas/Amberdata（期权机构级·暂无期权策略）· Lookonchain（无可编程API）· **任何聚合服务的标签/实体归属/热图再分发**（ToS普禁·同 CCXT 仅内部决策红线）

> **对 boss8001 最高价值 3 源**：① 交易所官方衍生品端点（资金费率+OI+清算·零成本第一手）② Hyperliquid（链上perp独立信号）③ Coinglass 跨所清算热图（唯一值得付费·先用免费端点验证再升 $299）

---

## B · 🔴 A股实时行情真空——最终裁定（首轮裁掉 akshare/tushare/yfinance 后的解）

**结论：有平价合规路，但只有一条主路——持牌券商官方 OpenAPI。**

| 路径 | 能拿什么 | 成本 | 合规 | 裁定 |
|------|---------|------|------|------|
| **🟢 富途 Futu OpenAPI**（首选） | **内地IP个人客户免费拿 A股 LV1 实时**(港股LV2)·Python SDK `FutunnOpen/py-futu-api` | **A股LV1免费**·LV2行情卡小额 | ✅持牌券商正规分发 | **A股实时行情底座·优先接** |
| 🟢 老虎 Tiger Open API | A股LV1/部分行情随账户 | 开户·部分免费 | ✅ | 富途平行备份 |
| 🟡 东财 Choice API | 全市场LV2/历史 | **≤5,000元/台/年**(持牌源最便宜) | ✅ | 需全市场LV2时中期评 |
| 🟡 IBKR(盈透)API | 仅沪深港通标的LV1 | 月费数美元级 | ✅但覆盖窄 | 补充 |
| ❌ Wind/同花顺iFinD | 全市场实时 | Wind 39,800/年·iFinD 8,800-20,000/年 | ✅但平价不可行 | rejected(成本) |
| ❌ Tushare realtime_quote / 新浪腾讯财经"API" | 实时报价 | 免费 | ❌官方自述爬虫接口/无授权逆向 | rejected(铁律) |

**诚实退路**：若拒绝任何券商绑定 → A股只能做"官方披露(cninfo/巨潮)+ 交易所官方延时 + 非实时"。实时全市场行情在不开券商、不付机构费、不爬虫前提下确无平价合规源。**裁定：优先富途 OpenAPI（免费 LV1），这是唯一平价合规真路。**

---

## C · 大宗商品 / 能源细分（首轮只有上金所黄金）

### ✅ 推荐 Top 3（全官方免费）
1. **EIA Open Data API**（美能源署·官方免费key）— 原油/天然气/电力/库存/产量·public domain·能源信息域基石
2. **USDA NASS QuickStats**（美农业部·官方免费key）— 农产品全口径
3. **LME 免费次日档**（官方·免费 T+1）— 金属基准(Officials/收盘/库存)·需延时全量再上 $2,490/年 XML feed

### 🟢 国内商品期货补充
**经持牌期货公司 CTP 开户即免费拿实时"一档"行情**（`tqsdk` 开源SDK封装）——合规平价，补上期所/大商所/郑商所缺口。Level2/逐笔/历史才需向行情商付费。

### ⚠️ 取数纪律
OPEC/CME 取**官方公布值/官网延时**，不取第三方爬虫聚合API（commodities-api/oilpriceapi 等权威性合规性存疑，仅作交叉验证）。

---

## D · 🔴 金融数据合规红线清单（6 条·法条可核）

| # | 红线 | 法条 | probe 动作 |
|---|------|------|-----------|
| 1 | **个人征信=持牌专营禁区** | 《征信业管理条例》+《征信业务管理办法》·全国仅3张个人征信牌照·央行"断直连" | ❌ 个人银行流水/信贷/还款/征信报告/账户明细**无论自用对外一律不碰**(无牌即非法)·"信用替代数据"做个人评分也属持牌范围·probe金融只做企业/市场/公开层 |
| 2 | **企业可采 vs 个人金融禁区分界** | 《证券法》披露制度 + 征信条例 | ✅企业工商/财报/公告/涉诉公开层(走天眼查持牌通道)·❌个人金融账户/征信/身份金融关联·口诀"企业层公开可采·个人金融层持牌红线" |
| 3 | **金融数据出境限制** | 《数据安全法》+《数据出境安全评估办法》+2024-03跨境新规 | probe拉境外API=数据"入境"压力小·⚠️**禁把含中国个人/客户金融数据的请求发往境外接口**(=出境触发评估)·境外行情/宏观/公司数据自由入境用于决策无碍 |
| 4 | **行情数据再分发版权** | 交易所行情授权服务商制度·SEC/FINRA redistribution license | ✅自用决策(内部分析)风险低·❌对外提供(原样转发/对外行情展示页)触再分发红线·选型区分license(CoinGecko付费档可商用需署名·交易所实时对外必走授权商) |
| 5 | **投资建议=持牌红线(只做信息不做建议)** | 《证券法》120/160·投资咨询暂行办法·越界涉《刑法》225非法经营罪 | ✅聚合公开情报/客观数据/事实陈述·❌荐股/买卖建议/预测特定标的/个性化方案·输出层加"仅供信息参考不构成投资建议"免责·产品停在信息聚合不跨咨询 |
| 6 | **反不正当竞争/爬虫判例** | 《反不正当竞争法》第二/十二条·判例标尺300-528万(蝉妈妈490万/微博528万/淘宝500万) | ❌禁绕技术保护(换IP/UA/破验证)爬金融数据·金融数据走官方API+授权商·个人OSINT即时查不落库 |

---

## E · pending 源成本总账（官方定价页实测）

### 成本汇总
- **Sprint3 最小集（免费档先跑 + 1核心付费）≈ ¥225/月**（tushare ¥17 + Polygon $29 或 AV $49.99）
- **全接（所有 pending 上最低档）≈ ¥5,200/月（$720）**

### 付费优先级（先接性价比高·零自动扣费雷）
| 优先级 | 源 | 月成本 | 理由 |
|-------|----|-------|------|
| **P1** | tushare Pro | ¥17/月 | A股全量·极致性价比·零R1风险 |
| **P1** | Polygon.io Starter | $29/月 | 美股无限调用·固定低价·无overage |
| **P2** | CoinGecko Basic | $35/月 | 加密全覆盖·含商用license |
| **P2** | Alpha Vantage / Finnhub | $50/月 | 美股+宏观·二选一(功能重叠) |
| **P3** | 天眼查/企查查 按量 | ~¥100/月 | 企业工商核心·按量·先免费档500/日 |
| **P3** | TikHub/twitterapi.io | 按量 | 预充值无月费门槛 |
| **P4慎** | Twelve Data $79 / EnsembleData $100 | — | 功能重叠·ROI待验 |
| **P5报价后定** | Trading Economics/新榜/飞瓜/Nasdaq premium | 报价制 | 须销售报价·多含自动续费雷 |

### 🔴 R1 自动扣费雷（接入前必查）
- **Trading Economics = 最危险**：试用不退款·到期未取消自动扣卡 → 必先走 R1 确认
- **EnsembleData/新榜/飞瓜**：订阅自动续 → 按月勿按年首充
- **✅ 安全（预充值·用完即停）**：天眼查/企查查/tushare/TikHub/twitterapi.io → 优先选

> R1 执行：任何付费接入前出报价清单 → 元东方密码确认 → 执行。预充值类可小额试水，订阅/试用类（尤其 Trading Economics）必先 R1。

---

## 增补后的 F 赛道总览（首轮 + 本增补）
- ✅ 可立即接（零成本）：首轮 19 + 加密 5 + A股富途免费LV1 + 大宗 EIA/USDA/LME/国内期货CTP ≈ **27+ 个零成本/低成本源**
- ⚠️ pending 付费：首轮 9 + 加密聚合服务若干（成本总账见 E）
- ❌ rejected：首轮 11 类 + 加密机构级 4 类 + A股爬虫接口
- 🔴 合规红线：6 条（个人征信禁区为最硬）

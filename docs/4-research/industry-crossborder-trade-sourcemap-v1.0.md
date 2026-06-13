# 跨境外贸行业免费官方源地图 v1.0

> probe 情报引擎 · 跨境外贸赛道 · 数据源调研文档
> 日期：2026-06-13
> 合规口径：D2 裁定——probe 自身绝不爬数据，只调 官方/授权 API。已判违法/逆向源永久拒用。

---

## 一、免费官方源总表

> 标注说明：P0 = keyless 免费立即可接；P1 = 需注册免费 key；P3 = 付费须授权；"已有" = probe ledger 已 live/cataloged

| # | 源名 | 类别 | access_type | 核心数据 | 接入档 | Mac直连 |
|---|------|------|-------------|----------|--------|---------|
| 1 | UN Comtrade (comtradeplus) | 1-贸易流 | free_with_key | HS全粒度进出口流向·200+国·月/年 | P1 | ✅ (需key) |
| 2 | US Census Bureau Trade API | 1-贸易流 | free_with_key | 美国进出口 HS/NAICS·2010-now·月度 | P1 | ✅ |
| 3 | Eurostat Comext API | 1-贸易流 | free | EU 27国进出口·CN8位·月/年 | P0† | ✅ |
| 4 | World Bank WITS API | 1贸易流+4关税 | free | 关税(MFN/优惠)·贸易流·HS6位·SDMX | P0 | ✅ |
| 5 | WTO Timeseries API | 4-关税/指标 | free_with_key | 关税(Bound/MFN/优惠)·贸易统计·非关税壁垒 | P1 | ✅ |
| 6 | IMF DOTS API | 4-宏观 | free | 双边贸易流向·时序·SDMX 3.0 | P0 | ✅ |
| 7 | GLEIF API | 2-企业背调 | free | 全球250万+法人LEI·层级·状态 | P0 | ✅ |（已有ledger live）|
| 8 | UK Companies House API | 2-企业注册 | free_with_key | 英国全量公司注册·董事·PSC·申报文件 | P1 | ✅ |
| 9 | OpenCorporates API | 2-企业注册 | free_with_key | 140+国家企业注册聚合·200次/月(免费层) | P1⁽商用需付费⁾ | ✅ |（已有ledger cataloged）|
| 10 | OFAC SDN 官方下载 (SLS) | 3-制裁合规 | free | 美国SDN+综合制裁清单·XML/CSV·实时 | P0 | ✅ |
| 11 | OpenSanctions 自托管 | 3-制裁合规 | free_with_license | 多国制裁/政治人物/执法·yente自托管 | P1⁽商用须license⁾ | probe-a |（已有ledger cataloged）|
| 12 | World Bank Indicators API | 4-宏观 | free | GDP/贸易占比/外汇储备·200+经济体 | P0 | ✅ |（已有ledger live）|
| 13 | IMF DataMapper API | 4-宏观 | free | WEO·IFS·DOT·SDMX·10次/5s | P0 | ✅ |（已有ledger live）|
| 14 | frankfurter (ECB汇率) | 4-汇率 | free | 170+货币对·ECB官方·keyless | P0 | ✅ |（已有ledger live）|
| 15 | EU TARIC 数据集 | 4-关税 | free | EU关税措施·CN8位·Excel/XML官方下载 | P0† | ✅ |
| 16 | aisstream.io | 5-航运 | free_with_key | 全球AIS实时船位·WebSocket流·Beta | P1 | probe-a推荐 |
| 17 | AISHub | 5-航运 | free_with_key | 实时船位·共享网络·AIS | P1 | probe-a推荐 |
| 18 | ShipsGo 集装箱追踪 API | 5-物流 | paid (pay-as-go) | 160+船公司集装箱追踪·Webhook | P3 | ✅ |

> †：P0 指可直接下载/查询公开端点，无需 key；实际高频调用建议登记账户以获稳定 SLA。

---

## 二、六类逐项核实

### 类别 1：国际贸易流 / 海关进出口数据

#### 1.1 UN Comtrade (comtradeplus.un.org)

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://comtradeplus.un.org/` + 开发者门户 `https://comtradedeveloper.un.org/`
- **数据端点**：`/data/v1/get/C/A/HS`（商品/年度/HS分类）
- **免费额度**：500次/天，每次最多 100K 条记录，注册后自动审批
- **HS 粒度**：支持 HS1992~HS2022 全版本，6位及以下细分
- **覆盖**：200+ 申报国，双边流向，进口/出口/再出口
- **需 key**：是，需在 comtradedeveloper.un.org 注册，选 `comtrade-v1` 免费产品
- **时效**：月度更新，数据延迟约 6-12 个月
- **license**：CC BY 4.0
- **Mac 直连**：✅
- **接入档**：P1（免费 key）
- **证据 URL**：https://unstats.un.org/wiki/display/comtrade/Free+Access+to+UN+Comtrade

#### 1.2 US Census Bureau International Trade API

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://api.census.gov/data/timeseries/intltrade/`
- **子端点示例**：`/exports/hs`（按 HS 出口）、`/imports/enduse`（按终端用途进口）
- **免费额度**：需免费注册 key，无公开频率上限说明
- **覆盖**：美国进出口，2010 年至今，月度，按州/港口/国家/HS/NAICS 过滤
- **需 key**：是，免费注册后激活
- **时效**：月度，T+1 个月
- **license**：公共数据
- **Mac 直连**：✅
- **接入档**：P1（免费 key）
- **证据 URL**：https://www.census.gov/data/developers/data-sets/international-trade.html

#### 1.3 Eurostat Comext API

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://ec.europa.eu/eurostat/api/comext/dissemination`
- **数据流发现**：`/sdmx/2.1/dataflow/ESTAT/all`
- **免费**：是，REST 公开无 key
- **数据内容**：EU 成员国进出口，Combined Nomenclature (CN8 位)，月度+年度
- **限制**：不支持完整数据集无过滤下载（须加过滤参数）
- **时效**：月度，T+6 周左右
- **license**：Eurostat CC BY 4.0
- **Mac 直连**：✅
- **接入档**：P0（keyless 公开 REST）
- **证据 URL**：https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/comext-database

#### 1.4 World Bank WITS API

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://wits.worldbank.org/API/V1`
- **SDMX 基地址**：`https://wits.worldbank.org/API/V1/SDMX/V21/`
- **免费**：是，无需 key
- **数据内容**：UNCTAD TRAINS 关税数据（MFN/优惠）+ 贸易流 + 发展指标，HS 6位
- **格式**：XML/JSON（加 `?format=JSON`）
- **license**：World Bank CC BY 4.0
- **Mac 直连**：✅
- **接入档**：P0（keyless）
- **证据 URL**：https://wits.worldbank.org/witsapiintro.aspx?lang=en

---

### 类别 2：海外企业注册 / 资质背调

#### 2.1 GLEIF API（已 live）

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://api.gleif.org/api/v1/`
- **免费且无需 key**：是，公开，60 次/分钟
- **覆盖**：250万+ 全球法人实体，包含法人名称、地址、注册状态、层级结构、BIC/SWIFT 映射
- **对跨境外贸用途**：验证对手方公司法律身份，查母子公司结构，识别壳公司
- **时效**：每日更新
- **license**：CC0 / 公共领域
- **Mac 直连**：✅（已 live，本条目仅做跨境赛道重标注）

#### 2.2 UK Companies House API

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://api.company-information.service.gov.uk`
- **注册地址**：`https://developer.company-information.service.gov.uk/`
- **免费 key**：是，注册后免费获取
- **覆盖**：英国全量公司信息（注册名、编号、状态）、董事（identity_verification_status 2025新增）、PSC 实控人、申报文件历史
- **时效**：近实时（文件提交即更新）
- **license**：Open Government Licence v3.0
- **Mac 直连**：✅
- **接入档**：P1（免费 key）
- **证据 URL**：https://www.thecompanywarehouse.co.uk/blog/companies-house-api

#### 2.3 OpenCorporates API（已 cataloged）

**核实状态**：✅ 已验证（当前定价核实）

- **免费层**：200次/月（50次/天），适用于开放数据项目
- **商用**：需付费，起价 £2,250/年（三档 self-serve + Enterprise）
- **覆盖**：140+ 国家注册信息聚合
- **结论**：免费层仅供研发测试；**商业生产部署需 P3 付费授权**（触发 R1，须元东方批准）
- **接入档**：P1（开发测试）/ P3（生产商用）
- **证据 URL**：https://api.opencorporates.com/documentation/API-Reference

---

### 类别 3：全球制裁 / 出口管制 / 合规清单

#### 3.1 OFAC SDN 官方下载（SLS）

**核实状态**：✅ 已验证

- **官方 API 端点**：`https://sanctionslistservice.ofac.treas.gov/api/download/{filename}`
- **可用文件清单**：`GET /sanctions-lists`（动态获取，不硬编码文件名）
- **主要文件**：`SDN_ADVANCED.XML`、`SDN.CSV`、`CONS_ADVANCED.XML`、`CONS_PRIM.CSV`
- **免费且无 key**：是，需加 `User-Agent` header，否则 403
- **更新频率**：OFAC 工作日及突发时更新，约每日
- **性质**：文件下载服务，无内建模糊匹配——需自行构建解析/匹配层
- **license**：US Government 公共数据
- **Mac 直连**：✅
- **接入档**：P0（keyless，需 User-Agent）
- **证据 URL**：https://ofac.treasury.gov/sanctions-list-service

#### 3.2 OpenSanctions 自托管 yente（已 cataloged）

**核实状态**：✅ 已验证

- **自托管软件**：开源，Docker 两容器（yente + ElasticSearch），最低 8GB RAM + 60GB 存储
- **数据集费用**：非商业免费；**商业使用须获数据 license**（内部使用/金融服务/转售三档，联系报价）
- **端点**：Matching API + Entities API + Search API（含模糊匹配）
- **优势**：本地隐私保护、可导入自定义黑名单、无限查询量、自动每日更新
- **对绵阳零元（非金融主体）**：如只做内部客户/供应商筛查，走"内部使用"档，较金融档便宜
- **Mac 直连**：建议 probe-a 部署（内存/存储要求高）
- **接入档**：P1（非商业）/ P3（商用需 license 授权）
- **证据 URL**：https://www.opensanctions.org/docs/self-hosted/

---

### 类别 4：汇率 / 关税 / 宏观贸易指标

#### 4.1 frankfurter / ECB 汇率（已 live）

已覆盖，170+ 货币对，P0 keyless。跨境外贸直接复用，无需补充。

#### 4.2 WTO Timeseries API

**核实状态**：✅ 已验证

- **开发者门户**：`https://apiportal.wto.org/`
- **旗舰端点**：WTO Timeseries API（具体路径需注册后查文档）
- **免费 key**：是，注册后免费
- **数据内容**：
  - 关税：Bound（CTS）/ MFN Applied / 优惠关税
  - 贸易统计：货物贸易 + 服务贸易（年/季/月）
  - 非关税措施（NTM）信息
  - 市场准入指标
- **注**：TAO（关税分析在线）已于 2025 年 6 月末停用，迁至 ttd.wto.org
- **时效**：年度/季度/月度，依指标而异
- **license**：WTO 公开数据，需标注来源
- **Mac 直连**：✅
- **接入档**：P1（免费 key）
- **证据 URL**：https://apiportal.wto.org/

#### 4.3 IMF DOTS API（已 live + 补充说明）

- **端点**：`https://api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/DOT/{version}/{key}`
- **2025 迁移**：IMF 已切换至 SDMX 3.0，旧 JSON REST 端点停用，需用新端点
- **限速**：10 次/5 秒
- **对跨境外贸**：双边贸易流向（Direction of Trade），补充 Comtrade 的快捷视角
- **接入档**：P0（已 live，此处补 SDMX 3.0 新端点说明）

#### 4.4 EU TARIC 数据集

**核实状态**：⚠️ 部分核实（无官方 REST API，仅批量下载）

- **官方渠道**：`https://taxation-customs.ec.europa.eu/customs/calculation-customs-duties/customs-tariff/eu-customs-tariff-taric_en`
- **可获取形式**：Excel 格式免费下载（CIRCABC 平台），无官方 REST API
- **数据内容**：EU 关税措施（税率、配额、反倾销）CN8 位，每日更新
- **probe 接入方式**：定期下载 → ETL 入 probe PG，非实时 API；或通过 WITS 获取 EU MFN 数据（已有 P0）
- **接入档**：P0（批量下载）
- **建议**：优先用 WITS（P0 REST API）覆盖 EU 关税，TARIC 精细措施数据作辅助批量导入

---

### 类别 5：物流 / 航运追踪

#### 5.1 aisstream.io

**核实状态**：✅ 已验证

- **端点**：`wss://stream.aisstream.io/v0/stream`（WebSocket）
- **免费 key**：是，注册获取，当前 Beta 阶段
- **数据内容**：实时全球船位/船名/船型/港口停靠/搜救/航行警告，28 种 AIS 消息类型
- **处理要求**：全球订阅约 300 条/秒，需足够 CPU/内存
- **注意**：Beta 服务，无 SLA 保障
- **Mac 直连**：可，但建议 probe-a 后台常驻消费（高带宽需求）
- **接入档**：P1（免费 key，Beta）
- **证据 URL**：https://aisstream.io/

#### 5.2 ShipsGo 集装箱追踪 API

**核实状态**：✅ 已验证

- **API 文档**：`https://api.shipsgo.com/docs/v2/`
- **免费层**：API 调用本身不限次，但**追踪信用点付费**（$20 起 / 10 次追踪）
- **数据内容**：160+ 船公司集装箱里程碑、船位、ETA、CO₂ 排放、Webhook 推送
- **空运**：Air Cargo Tracking API，同样 API 调用不限次 + 信用点按量付费
- **结论**：无真正免费层，P3 按量付费，ROI 需评估
- **接入档**：P3（须 R1 授权方可开通）

---

### 类别 6：海外舆情 / 买家线索

**核实状态**：⚠️ 官方免费源较少，此类数据官方渠道薄弱

- **Panjiva / ImportGenius / Volza**：付费订阅，无免费 API 层，均为 P3
- **US Customs 公开 BL 数据**：美国进口报关单（Bill of Lading）数据部分公开，ImportYeti 做了聚合但无官方 API
- **WTO 贸易指标**：可通过 WTO API 获取各国贸易伙伴结构，作为买家市场线索的宏观层支撑
- **ITC Trade Map**：国际贸易中心（ITC / WTO + UNCTAD 联合机构）提供免费贸易流数据查询，无批量 API，只有网页工具
- **结论**：类别 6 暂无零 R1 的高质量免费官方 API 层，建议以 UN Comtrade + WTO 贸易流数据替代（贸易规模反推买家市场），精确买家线索数据属付费赛道

---

## 三、需 probe-a 代理的源清单

> probe-a 部署于腾讯云东京/上海，独立出口 EIP，mihomo 自动分流

| 源 | 原因 | 代理必要性 |
|----|------|-----------|
| OpenSanctions yente 自托管 | 自托管服务部署在 probe-a，需本地资源（8GB RAM + ElasticSearch） | 必须在 probe-a 部署 |
| aisstream.io WebSocket | 高带宽流式数据（300条/秒全球订阅），Mac 不宜常驻消费 | 强烈建议 probe-a 后台消费 |
| AISHub | 同上，实时流式数据 | 建议 probe-a |
| UN Comtrade（大批量拉取） | 境外 API，Mac 直连可用；高频批量拉取时建议走 probe-a 出口避免 IP 限制 | 可选，视用量决定 |
| UK Companies House API | 英国 API，部分情况境内访问偶有超时 | 推荐 probe-a |

**Mac 直连可用、无需代理的源**（占多数）：OFAC SLS、GLEIF、Census Bureau、WITS、Eurostat Comext、WTO API、IMF API、frankfurter、OpenCorporates

---

## 四、验证冗余评估（闸 2 要求）

### 4.1 海关贸易流 ——能否凑齐 ≥2 独立源？

| 源 | 独立性 | 覆盖 |
|----|--------|------|
| UN Comtrade | 联合国统计署官方，200+国申报 | 全球最广 |
| US Census Trade API | 美国商务部独立发布 | 美国进出口精确 |
| Eurostat Comext | 欧盟统计局独立发布 | EU 27国精确 |
| World Bank WITS | 世界银行整合 UNCTAD TRAINS + UN Comtrade | 有重叠但独立汇总层 |

**结论**：✅ 轻松凑齐 ≥2 完全独立源（UN Comtrade + Eurostat 已构成双重印证；加 US Census 形成三角验证）。

### 4.2 海外企业注册 ——能否凑齐 ≥2 独立源？

| 源 | 独立性 | 覆盖 |
|----|--------|------|
| GLEIF | ISO 20275 LEI，全球权威法人标识 | 250万+注册法人 |
| UK Companies House | 英国政府官方注册局 | 英国全量（对英贸易） |
| OpenCorporates | 140+国家聚合（第三方，非官方） | 最宽但非官方 |

**结论**：✅ GLEIF + UK Companies House 已达双源印证；OpenCorporates 作第三交叉。  
**缺口**：中国、印度、东南亚国家无等量级的官方免费 API（工商局无公开 API）——此类市场需依赖 GLEIF（LEI 覆盖有限）+ 付费数据源（OpenCorporates 商用/Dun & Bradstreet）。

### 4.3 全球制裁 ——能否凑齐 ≥2 独立源？

| 源 | 独立性 | 覆盖 |
|----|--------|------|
| OFAC SDN（美国财政部） | 美国政府官方 | 美国制裁（最核心） |
| OpenSanctions yente | 多国/多机构合并（含 EU、UN、英国 OFSI、FATF 等） | 40+ 司法管辖区制裁列表 |

**结论**：✅ 双源均可独立运行，且互补性强（OFAC = 单一权威原始源；OpenSanctions = 多国汇总+模糊匹配）。OFAC P0 无 key，OpenSanctions 商用须 license（P3 R1 门）。  
**临时方案**：在商用 license 授权前，可用 OFAC SLS P0（自行解析 XML）作单源生产，OpenSanctions 作开发测试参比。

---

## 五、接入排期

### P0 档 —— keyless 免费，立即可接（共 5 个）

| 优先级 | 源 | 端点 | 价值 |
|--------|----|----- |------|
| ★★★ | Eurostat Comext API | `ec.europa.eu/eurostat/api/comext/dissemination` | EU贸易流·CN8位·月度 |
| ★★★ | World Bank WITS API | `wits.worldbank.org/API/V1` | 关税(MFN/优惠)·贸易流·免费keyless |
| ★★★ | OFAC SDN SLS | `sanctionslistservice.ofac.treas.gov/api/download/` | 制裁名单·零R1·P0 |
| ★★ | IMF DOTS (SDMX 3.0) | `api.imf.org/external/sdmx/3.0/data/dataflow/IMF.STA/DOT/` | 双边贸易流向·补充视角 |
| ★★ | EU TARIC 批量下载 | CIRCABC Excel | EU关税措施·ETL入库 |

### P1 档 —— 需注册免费 key（共 4 个，建议本季度完成注册）

| 源 | 注册地址 | 等待审批 | 优先级 |
|----|---------|---------|--------|
| UN Comtrade v1 | comtradedeveloper.un.org | 自动批准 | ★★★ |
| WTO Timeseries API | apiportal.wto.org | 自动批准 | ★★★ |
| US Census Trade API | census.gov/developers | 邮件激活 | ★★ |
| UK Companies House | developer.company-information.service.gov.uk | 即时 | ★★ |
| aisstream.io | aisstream.io | 即时(Beta) | ★ |

### P3 档 —— 付费，需元东方 R1 授权（登记备用）

| 源 | 用途 | 预估成本 | 触发条件 |
|----|------|---------|---------|
| OpenSanctions 商用 license | 生产级制裁筛查 | 联系报价（startup 折扣可申请） | 有商业客户合规需求时 |
| OpenCorporates 商用 API | 生产级 140+国企业查询 | £2,250/年起 | 有买方/供应商背调产品时 |
| ShipsGo 集装箱追踪 | 精确货物追踪 | $20 起按量 | 有物流可视化产品需求时 |
| Panjiva / ImportGenius | 批量采购商线索 | 高价订阅 | 有销售情报产品需求时 |

---

## 六、值得登记的付费源（P3 优先级排序）

| 源 | 类别 | 价值点 | 替代方案 |
|----|------|--------|---------|
| **OpenSanctions 商用** | 制裁合规 | 生产级多国制裁 + 模糊匹配 + 每日更新 | OFAC SLS P0（仅美国制裁） |
| **OpenCorporates 商用** | 企业背调 | 140+国家统一查询接口 | GLEIF P0（LEI 覆盖较窄）+ Companies House P1 |
| **Dun & Bradstreet API** | 企业信用 | 全球企业信用评级、D-U-N-S 号 | 无直接免费替代 |
| **ShipsGo Container Tracking** | 物流追踪 | 160+船公司集装箱端到端追踪 | aisstream.io（船位，非集装箱里程碑） |
| **ITC Trade Map 数据** | 买家市场 | 产品级进出口市场份额 | UN Comtrade（自行聚合） |
| **Panjiva/ImportGenius** | 买家线索 | BL 级别采购商具体采购记录 | 无官方免费替代 |

---

## 七、决策闭环评估

```
┌──────────────────────────────────────────────────────────────┐
│  跨境外贸决策闭环（六类）      免费官方源覆盖度评估           │
├──────────┬───────────────────────┬───────────────────────────┤
│ 类别     │ 覆盖状态               │ 说明                       │
├──────────┼───────────────────────┼───────────────────────────┤
│ 1-贸易流 │ ✅ 强覆盖（P0/P1×3）  │ Comtrade+Census+Eurostat   │
│ 2-企业背 │ ✅ 基础覆盖（P0/P1）  │ GLEIF+Companies House      │
│          │ ⚠️ 中国/东南亚缺口   │ 无官方免费 API             │
│ 3-制裁   │ ✅ P0即可运行         │ OFAC SLS; OS商用待授权     │
│ 4-关税/宏│ ✅ 强覆盖（P0/P1×3） │ WITS+WTO+IMF+frankfurter   │
│ 5-物流   │ ⚠️ 部分覆盖           │ AIS免费(船位)+ShipsGo付费  │
│ 6-买家线 │ 🔴 覆盖薄弱           │ 官方无免费精准 API         │
└──────────┴───────────────────────┴───────────────────────────┘
```

**结论**：类别 1-4 可形成完整闭环，P0/P1 免费官方源足以覆盖；类别 5 物流追踪需付费（集装箱精确追踪），类别 6 买家线索无官方免费层，是本赛道唯一付费硬缺口。

---

## 附录：源 domain 分类对照（probe ledger schema）

| 源 | domain |
|----|--------|
| UN Comtrade, Eurostat Comext, Census Trade, WITS | D11 企业贸易 / D14 宏观经济 |
| GLEIF, Companies House, OpenCorporates | D11 企业背调 |
| OFAC SLS, OpenSanctions | D8 合规/制裁 |
| WTO API, IMF DOTS, World Bank | D14 宏观经济 |
| frankfurter / ECB | D13 金融/汇率 |
| aisstream, AISHub, ShipsGo | D11 物流/航运 |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> 文档版本：v1.0 · 初稿：2026-06-13 · 作者：probe 数据源调研
> 所有凭据字段：PLACEHOLDER（真值存 ~/vault/credentials/）
> 下次更新触发条件：UN Comtrade 或 OpenSanctions 定价政策变更时

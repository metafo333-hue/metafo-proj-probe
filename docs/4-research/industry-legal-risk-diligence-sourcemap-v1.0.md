# probe · 法律/风控/尽调行业 决策闭环最小源集 + 接入可行性 + 付费源报价单 v1.0

> 日期：2026-06-13 · 性质：纯调研核实（WebSearch/WebFetch 核实公开信息，未注册账号、未调接口、未付款）
> 引擎：元探 / MetaProbe · 域：D8 法规合规 / D11 企业财务 / D4 出处溯源
> 合规铁律（D2 裁定·不可违）：probe **绝不自爬数据**（不写爬虫/不抓平台/不模拟登录/不抓包/不逆向）；**只调第三方官方/授权 API**。已被司法判违法的供应商**永久拒用**。
> 公司主体：绵阳零元电子商务有限公司（USCC + ICP 蜀ICP备2026010386号-1）→ 可用于需企业实名/资质认证的 API 申请。
> 节点：probe-a（独立公网 EIP + mihomo 代理）可访问境内外源；Mac 本地直连部分境外源受限。
> ledger schema 对齐：`probe/app/datasources/ledger.yaml` v8（domain/access_type/method/authority_score/freshness/cost/license/status）。
> 上游已有调研：`datasource-diligence-c-v1.md`（C 尽调风控域 5 子场景）—— 本文聚焦「决策闭环最小源集」收敛 + 价格 web 复核。

---

## 〇、核心结论（先行）

1. **决策闭环能否闭合？** —— **境外对手方可完全闭合**（工商/制裁/资产三类各 ≥2 独立官方免费源）；**境内（中国）对手方半闭合**：制裁/资产可闭合，但**工商穿透 + 司法涉诉 + 失信被执行 + 行政处罚四类全部无官方开放 API**，必须经**授权商业聚合商**（天眼查/企查查/启信宝）中转 → 触发 R1（付费）+ 企业资质认证。这是结构性合规债，非技术问题。
2. **最大风险点**：中国官方系统（gsxt 国家企业信用信息公示系统 / wenshu 裁判文书网 / zhixing 中国执行信息公开网 / creditchina 信用中国）**均无官方开放 API**，只有网页 + APP/小程序。**probe 铁律禁止自爬这些网页**（裁判文书网逆向、信用中国 IP 封禁即典型不可走路径）→ 唯一合规路径 = 付费商业聚合商，且该聚合商须**数据来源合法授权**（避免蝉妈妈式爬虫判例风险）。
3. **P0 立即可接（免费官方 API · 无需 key 或仅注册 key）**：境外工商/制裁/资产侧 **7 个**已 live（edgar/gleif/ofac_sls/sanctions_network/crt_sh/rdap_icann/wikidata_sparql/osv 系列），本任务**补缺新增 P0 候选 3 个**（OpenOwnership BODS、Companies House UK、Shodan InternetDB 免费层）。
4. **需 R1 付费**：天眼查/企查查/启信宝（中国工商+司法，三选一或互备）、Shodan 完整 API、OpenSanctions 商业数据 license、OpenCorporates Essentials（境外工商）—— **共 4~6 个**视采购策略。
5. **报价单合计年成本区间**：**约 ¥6,000 ~ ¥60,000+/年**（下限=Shodan $49 一次性 + 天眼查按量小额 + 自托管 OpenSanctions 仅 license；上限=天眼查/企查查中量包 + OpenSanctions 商业 license + OpenCorporates Essentials £2,250）。中国工商 API 按量计费弹性极大，具体随调用量浮动。

---

## ① 决策闭环最小源集总表

> 一份完整尽调报告需 7 类数据。✅=已 live / 🟡=cataloged 待接 / 🆕=本任务新增候选 / 🔴=无合规 API 拒用。

| # | 尽调类别 | 境内（中国对手方）最小源 | 境外（跨境对手方）最小源 | domain | 闭环状态 |
|---|---------|----------------------|----------------------|--------|---------|
| 1 | 工商基础+股权穿透 | 🔴 官方 gsxt 无 API → 🟡天眼查/企查查/启信宝(R1) | ✅edgar(美) +✅gleif(全球LEI L2母子) +🆕OpenCorporates(R1,200国) +🆕CompaniesHouse(英免费) +🆕OpenOwnership(受益人,免费) | D11 | 境外✅ / 境内需R1 |
| 2 | 司法涉诉+失信执行 | 🔴 wenshu/zhixing 无官方API·禁爬 → 🟡天眼查/企查查司法接口(R1·须授权来源) | ✅edgar(美诉讼披露) · 海外判例多为商业库 | D11/D8 | 境内**强依赖R1** |
| 3 | 行政处罚+经营异常+严重违法 | 🔴 creditchina/gsxt 无API → 🟡天眼查/企查查经营异常接口(R1) | ✅ofac_sls/✅sanctions_network(监管行动部分覆盖) | D8/D14 | 境内需R1 |
| 4 | 制裁+反洗钱+PEP | ✅ofac_sls +✅sanctions_network +🟡OpenSanctions/Yente(PEP·商用R1) | 同左（全球名单同源） | D8 | ✅可闭合(≥2源) |
| 5 | 知识产权+资质 | 🔴 商标局/专利局 cnipa 无统一开放API → 🟡天眼查/企查查商标专利接口(R1) | ✅uspto/epo 有官方API(本任务标记为后续候选) | D11 | 境内需R1 |
| 6 | 资产/技术侧风险(供应商技术尽调) | ✅crt_sh +✅rdap_icann +✅urlscan +✅virustotal +✅abuseipdb +🆕ShodanInternetDB(免费) → 完整版🟡Shodan(R1) | 同左（全球同源） | D8/D12 | ✅可闭合 |
| 7 | 海外企业（跨境对手方） | — | ✅edgar +✅gleif +🆕OpenCorporates(R1) +🆕CompaniesHouse(英) +🟡OpenAleph(自托管) | D11 | ✅可闭合(≥2源) |

**闭环判定**：境外尽调 7 类全部 ≥1 官方/授权源、关键 3 类 ≥2 源 → **闭合**。境内尽调类别 1/2/3/5 的**唯一合规通道是付费商业聚合商**，制裁(4)/资产(6)走免费官方源 → **半闭合，R1 解锁后全闭合**。

---

## ② 七类逐项源核实

> 每项含：源名/vendor · 类别 · domain · access_type · method · 官方API? · 资质 · 直连/probe-a · 权威分/时效/license · 接入档 · 实测证据(URL+核实日 2026-06-13)。

### 类别 1 · 工商基础 + 股权穿透（D11）

| 源 | access | method | 官方API | 资质 | 节点 | 权威/时效/license | 档 | 证据 |
|----|--------|--------|--------|------|------|------------------|----|------|
| **SEC EDGAR** ✅已live | free | O | ✅ efts.sec.gov 全文检索API | 无 | probe-a/Mac | 10/daily/公有领域 | P0 | https://efts.sec.gov · https://www.sec.gov/edgar/sec-api-documentation |
| **GLEIF LEI** ✅已live | free | O | ✅ api.gleif.org/api/v1 含 Level2 母子股权 | 无 | Mac直连 | 9/daily/CC0 | P0 | https://api.gleif.org/api/v1 |
| **OpenCorporates** 🆕/🟡catalog | paid_with_key | O | ✅ api.opencorporates.com/v0.4 | 否(公益通道可申请免费) | probe-a | 8/varies/开放许可 | P1免费层(200/月50/日)→P3商用 | https://opencorporates.com/pricing/（核实：Essentials £2,250/yr · Starter £6,600 · Basic £12,000 · 免费层 200/月仍在 · 公益项目免费通道存在）|
| **Companies House (UK)** 🆕 | free_with_key | O | ✅ 官方免费REST API | 注册免费key | probe-a | 9/daily/英国政府开放 | P0(注册key) | https://developer.company-information.service.gov.uk/ |
| **OpenOwnership BODS** 🆕 | free | D/O | ✅ 受益所有权数据集+API | 无 | probe-a | 8/weekly/CC0 | P1 | https://www.openownership.org/ |
| **OpenAleph (OCCRP)** 🟡catalog | free | S(自托管) | 公开API仅限新闻调查·商用须自托管 | 无 | probe-a自托管 | 7/varies/MIT软件 | P3(自托管) | https://openaleph.org/ |
| **天眼查开放平台** 🟡catalog | paid_with_key | O | ✅ open.tianyancha.com | **是·企业实名认证** | probe-a | 8/daily/商业授权 | **P3·R1** | https://open.tianyancha.com/ （1.8亿实体·90+维度·工商/股权/股东/受益人/变更·免费500条/日·超出按条计费约¥0.05~0.15/条·会员门槛¥198/年·精确分档需登录后台·见报价单注） |
| **企查查开放平台** 🟡catalog | paid_with_key | O | ✅ openapi.qcc.com | **是·企业实名认证** | probe-a | 8/daily/商业授权 | **P3·R1** | https://openapi.qcc.com/ （2.3亿实体·工商详情/股东/主要人员/分支/变更·新用户20次免费测试·多数接口"面议"，基础搜索¥0.01/次）|
| **启信宝(合合信息)** 🆕catalog | paid_with_key | O | ✅ intsig.com 企业数据API | **是·企业认证** | probe-a | 8/realtime/商业授权 | **P3·R1** | https://www.intsig.com/public/solution_new/api.shtml （3亿+机构·2000亿条·1000+风控标签·工商/股权/司法/失信/舆情/资产·金融风控向）|

**结论**：境外工商穿透用 EDGAR+GLEIF+OpenCorporates+CompaniesHouse 即 ≥2 源闭合。**中国工商穿透无任何官方开放 API**（gsxt 国家企业信用信息公示系统仅网页+APP+小程序，禁爬）→ 必须 R1 接入天眼查/企查查/启信宝其一为主、其二为互备。

### 类别 2 · 司法涉诉 + 失信执行（D11/D8）

| 源 | access | method | 官方API | 节点 | 档 | 证据 |
|----|--------|--------|--------|------|----|------|
| **中国裁判文书网 wenshu** | — | 🔴 | **无官方开放API·网页+反爬+逆向风险** | — | 🔴拒用(直采) | https://wenshu.court.gov.cn/ （核实：仅网页，近期升级维护；坊间"逆向"方案 probe 铁律禁用）|
| **中国执行信息公开网 zhixing/zxgk** | — | 🔴 | **无官方开放API·仅网页+APP** | — | 🔴拒用(直采) | http://zxgk.court.gov.cn/ |
| **信用中国 creditchina** | — | 🔴 | **无官方开放API·网页易封IP** | — | 🔴拒用(直采) | https://www.creditchina.gov.cn/ |
| **天眼查/企查查司法接口** 🟡 | paid_with_key | O | ✅ 聚合商提供裁判文书核查/被执行人/失信/限高接口 | probe-a | **P3·R1·须核实供应商数据来源合法授权** | https://openapi.qcc.com/dataApi/887（企业裁判文书核查API）|
| **SEC EDGAR(美诉讼披露)** ✅ | free | O | ✅ 8-K/10-K Legal Proceedings | probe-a | P0 | https://efts.sec.gov |

**结论**：**境内司法涉诉/失信/被执行/限高数据无任何合法直采途径**——四个官方网站全无开放 API，且 probe 禁止爬取。唯一合规路径=授权商业聚合商 API（天眼查/企查查），且**采购前必须核实该聚合商对裁判文书/执行数据的来源具备合法授权**（规避蝉妈妈 2025 厦门判赔 490 万式爬虫违法判例的连带风险）。**这是本行业最大合规风险点。**

### 类别 3 · 行政处罚 + 经营异常 + 严重违法（D8/D14）

| 源 | access | method | 官方API | 档 | 证据 |
|----|--------|--------|--------|----|------|
| **gsxt 经营异常/严重违法名录** | — | 🔴 无官方API | — | 🔴拒用(直采) | https://www.gsxt.gov.cn/ |
| **creditchina 行政处罚** | — | 🔴 无官方API | — | 🔴拒用(直采) | https://www.creditchina.gov.cn/ |
| **天眼查/企查查 经营异常/行政处罚接口** 🟡 | paid_with_key·O | ✅聚合 | **P3·R1** | https://open.tianyancha.com/api_list |
| **ofac_sls / sanctions_network** ✅live | free·O | ✅(境外监管行动部分覆盖) | P0 | https://www.treasury.gov/ofac/downloads |

**结论**：境内行政处罚/经营异常同样无官方 API，走聚合商 R1。

### 类别 4 · 制裁 + 反洗钱 + PEP（D8）—— **唯一境内外都能免费闭合的类别**

| 源 | access | method | 官方API | 档 | 证据 |
|----|--------|--------|--------|----|------|
| **OFAC SDN/SLS** ✅live | free·O | ✅ treasury.gov 下载+API | P0 | https://www.treasury.gov/ofac/downloads · https://sanctionssearch.ofac.treas.gov/ |
| **sanctions.network** ✅live | free·O | ✅ api.sanctions.network（聚合OFAC/UN/EU/UK官方名单）| P0 | https://api.sanctions.network |
| **OpenSanctions + Yente** 🟡catalog | free(非商用)/paid(商用) | S自托管/O | ✅ 350+源·含PEP | **自托管软件免费，但商用数据 license R1** | https://www.opensanctions.org/ （核实 2026-06-13：**营利公司内部合规KYC也需付费数据license**，无 blanket 豁免；仅记者/反腐NGO/学术/被侵略国公共机构 0 成本；SaaS API €0.10/次·>20k/月有量价；自托管 yente 软件免费仅需 bulk data license，价格须联系销售）|
| **OFAC/UN/EU/UK 官方下载** ✅ | free·D | ✅ 各官方 | P0 | 同 ofac_sls |

**结论**：制裁/PEP 类 ✅ 凑齐 ≥3 独立官方免费源（OFAC + sanctions.network + 官方下载），**probe 闸2 跨源印证可跑通**。OpenSanctions 仅在需要 PEP 深度+350源聚合且商业化时触发 R1（数据 license）。

### 类别 5 · 知识产权 + 资质（D11）

| 源 | access | method | 官方API | 档 | 证据 |
|----|--------|--------|--------|----|------|
| **CNIPA 商标局/专利局** | — | 🔴 无统一开放API | — | 🔴拒用(直采) | — |
| **USPTO / EPO(境外)** 🆕候选 | free_with_key·O | ✅ 官方API | P1(后续) | https://developer.uspto.gov/ · https://www.epo.org/ |
| **天眼查/企查查 商标专利接口** 🟡 | paid_with_key·O | ✅聚合 | **P3·R1** | https://open.tianyancha.com/api_list |

**结论**：境内知产走聚合商 R1；境外可用 USPTO/EPO 官方免费 API（标记为后续 P1 候选，本任务未深核）。

### 类别 6 · 资产/技术侧风险（供应商技术尽调）（D8/D12）—— **免费闭合**

| 源 | access | method | 官方API | 档 | 证据 |
|----|--------|--------|--------|----|------|
| **crt.sh** ✅live | free·O | ✅证书透明 | P0 | https://crt.sh |
| **RDAP/ICANN** ✅live | free·O | ✅域名注册 | P0 | https://rdap.org/ |
| **urlscan.io** ✅live | free_with_key·O | ✅ | P0/P1 | https://urlscan.io |
| **VirusTotal** ✅live | free_with_key·O | ✅(商用须商业版) | P1 | https://www.virustotal.com/ |
| **AbuseIPDB** ✅live | free_with_key·O | ✅ | P1 | https://www.abuseipdb.com/ |
| **OSV/NVD/GitHub Advisory** ✅live | free·O | ✅漏洞 | P0 | https://osv.dev · https://nvd.nist.gov |
| **Shodan InternetDB** 🆕 | free·O | ✅ internetdb.shodan.io 免费暴露资产 | P0(免费层) | https://internetdb.shodan.io/ |
| **Shodan 完整API** 🟡catalog | paid·O | ✅ | **P3·R1·$49一次性** | https://account.shodan.io/billing（核实 2026-06-13：membership $49 一次性·含 100 query+100 scan credits/月；Freelancer $69/月·Small Business $359/月·Corporate $1099/月）|

**结论**：资产/技术尽调 ✅ 免费层即闭合（crt.sh+RDAP+InternetDB+OSV ≥2 源）；商用深扫触发 Shodan R1（成本极低 $49 一次性）。

### 类别 7 · 海外企业（跨境对手方）（D11）

EDGAR(美) + GLEIF(全球LEI) + OpenCorporates(200国·R1) + Companies House(英·免费) + OpenAleph(自托管) → ≥2 源闭合。详见类别 1 表。

---

## ③ 付费源报价单（走 R1 用 · 所有价格 WebFetch 官方页核实 · 核实日 2026-06-13）

| 源名 | 套餐 | 单价/年费 | 覆盖能力 | 推荐优先级 | 触发R1 | 价格来源URL(核实2026-06-13) |
|------|------|----------|---------|-----------|--------|------------------------------|
| **天眼查 开放平台** | 按量计费(条) | 免费500条/日·超出约¥0.05~0.15/条·会员门槛¥198/年·精确分档须登录后台 | 中国工商/股权/股东/受益人/司法/失信/被执行/经营异常/行政处罚/商标专利 | ⭐P1(境内首选) | ✅+企业资质 | https://open.tianyancha.com/ |
| **企查查 开放平台** | 按接口计费 | 基础搜索¥0.01/次·多数接口"面议"·新用户20次免费测试 | 同天眼查(2.3亿实体) | ⭐P2(天眼查互备) | ✅+企业资质 | https://openapi.qcc.com/ |
| **启信宝(合合信息)** | 数据包/API/实时库 | 面议(金融风控向·企业定价) | 工商/股权/司法/失信/舆情/资产·1000+风控标签 | P2(金融风控场景) | ✅+企业认证 | https://www.intsig.com/public/solution_new/api.shtml |
| **Shodan** | Membership 一次性 | **$49 一次性**(含100 query+100 scan credits/月) | 暴露资产/端口/服务指纹·供应商技术尽调 | ⭐P1(成本极低) | ✅ | https://account.shodan.io/billing |
| Shodan | Freelancer | $69/月(10k query·5,120 scan) | 同上·中量 | P3 | ✅ | 同上 |
| Shodan | Small Business | $359/月(200k query) | 同上·大量 | P3 | ✅ | 同上 |
| **OpenSanctions** | 商业数据 license(自托管) | 联系销售(按内部/转售+行业分档) | 350+源制裁/PEP·自托管 yente 软件免费仅需数据license | P2(制裁深度+商用) | ✅ | https://www.opensanctions.org/licensing/ |
| OpenSanctions | SaaS API | €0.10/次·>20k/月量价 | 同上·托管 | P3 | ✅ | https://www.opensanctions.org/api/ |
| **OpenCorporates** | Essentials | **£2,250/年** | 200国企业注册/工商 | P3(境外深度) | ✅ | https://opencorporates.com/pricing/ |
| OpenCorporates | Starter/Basic | £6,600 / £12,000 /年 | 同上·更高限额 | P3 | ✅ | 同上 |
| OpenCorporates | 公益项目 | **免费**(须申请审批) | 同上·NGO/学术/记者 | (主体非公益·一般不适用) | — | https://opencorporates.atlassian.net/servicedesk/customer/portal/4 |

**年成本区间测算**：
- **精简起步（推荐 R1 首批）**：Shodan $49 一次性(≈¥350) + 天眼查按量小额(初期免费500/日多数够用，超量数百~数千元) + OpenSanctions 自托管(仅 license，可先用免费 OFAC/sanctions.network 替代延后) → **首年约 ¥1,000 ~ ¥6,000**。
- **完整商用（高端尽调客户）**：天眼查/企查查中量包(¥1万~3万/年量级) + OpenSanctions 商业 license(数千~数万) + OpenCorporates Essentials £2,250(≈¥2万) + Shodan 订阅 → **约 ¥40,000 ~ ¥60,000+/年**。
- 中国工商 API 弹性最大，成本完全随调用量浮动；**精确分档价须企业实名登录后台获取**（本任务禁注册，故标注为待核）。

---

## ④ 验证冗余评估（probe 闸2 跨源印证：一个论断需 ≥2 独立源）

| 高价值类别 | 独立源数 | 是否 ≥2 | 印证可行性 |
|-----------|---------|---------|-----------|
| **工商基础** | 境外：EDGAR+GLEIF+OpenCorporates+CompaniesHouse=**4** ✅ / 境内：天眼查+企查查+启信宝=**3**(均 R1) | 境外✅免费 / 境内✅需R1 | 境外免费即可双源印证；境内须至少接 2 个聚合商互验(天眼查+企查查) |
| **司法涉诉** | 境外：EDGAR=1(弱) / 境内：天眼查司法+企查查司法=**2**(均 R1·均聚合自同源官网) | ⚠️境内"2源"实为**同源聚合**(都来自 wenshu/zxgk 官网)→ **伪冗余风险** | **闸2 警告**：两家聚合商数据同源，跨源印证仅验"聚合准确性"非"事实独立性"。建议加 SEC EDGAR(境外)或官网人工抽样复核作第二维度 |
| **制裁/AML** | OFAC+sanctions.network+官方下载+OpenSanctions=**≥3** ✅ | ✅免费 | 真·多独立官方源，闸2 完整跑通 |

**核心冗余结论**：
- **制裁类**冗余最健康（多官方独立源，免费）。
- **工商类**境外健康、境内需接 2 个聚合商才达标。
- **司法类**存在**伪冗余陷阱**：天眼查与企查查司法数据均爬/聚合自同一批官网(wenshu/zxgk)，互验只能发现聚合错误、无法独立印证事实。**建议**：司法类论断标注 `confidence=single-source-aggregated`，重大尽调结论须官网人工复核兜底，不可仅凭单一聚合 API 下定论。

---

## ⑤ 接入排期建议（P0/P1/P3）

### P0 · 立即可接（免费官方 API · 无需付费授权）
- 已 live（复用）：edgar / gleif / ofac_sls / sanctions_network / crt_sh / rdap_icann / wikidata_sparql / osv / nvd / github_advisory
- **本任务新增 P0 候选**：① **Shodan InternetDB**（免费暴露资产，0 成本）② **Companies House UK**（注册免费 key，英国工商）③ **OpenOwnership BODS**（受益人，免费数据集）
- 动作：写 datasource 模块 → 过 gate19 → status=live。

### P1 · 需注册 key（免费/低门槛）
- urlscan / virustotal / abuseipdb（已 live）+ OpenCorporates 免费层(200/月) + USPTO/EPO(境外知产，后续深核)
- 动作：注册免费 key（触发 R8 邮箱授权流程，由元东方 1 次授权），不付费。

### P3 · 付费 R1（须元东方密码授权 + 企业资质认证）
- **第一批（最高 ROI）**：① Shodan membership $49 一次性 ② 天眼查开放平台（境内尽调的关键解锁，企业资质用绵阳零元主体申请）
- **第二批**：企查查（天眼查司法类互备，破伪冗余）+ OpenSanctions 商业 license（制裁深度+商用合规）
- **第三批（高端客户驱动）**：OpenCorporates Essentials £2,250 + 启信宝（金融风控场景）
- 动作：本任务只登记+报价，**不开通**；R1 报价清单已备好，待元东方密码确认后逐项接入。

---

## ⑥ 合规拒用清单（永久拒用 / 禁直采）

| 对象 | 拒用原因 | 替代 |
|------|---------|------|
| 🔴 **裁判文书网 wenshu** 直采/逆向 | 无官方API·有反爬·逆向方案违反 probe 不自爬铁律·涉刑事风险 | 授权商业聚合商API(须核实来源授权) |
| 🔴 **中国执行信息公开网 zxgk** 直采 | 无官方API·禁爬 | 同上 |
| 🔴 **信用中国 creditchina** 直采 | 无官方API·IP易封·禁爬 | 同上 |
| 🔴 **gsxt 国家企业信用信息公示系统** 直采 | 无官方API·仅网页/APP·禁爬 | 天眼查/企查查/启信宝(R1) |
| 🔴 **CNIPA 商标/专利** 直采 | 无统一开放API·禁爬 | 聚合商(境内R1) / USPTO·EPO(境外免费) |
| 🔴 **蝉妈妈类爬虫供应商** | 2025 厦门判赔490万·司法判违法·永久拒用 | 不采用 |
| 🔴 **AKShare(全系爬虫)/yfinance(逆向)** | 爬虫/逆向合规问题 | 官方API源 |
| 🔴 **任何"社工库/人肉/手机定位/通话记录"接口** | 刑法253之一侵犯公民个人信息罪·搜索过程中出现此类站点一律拒用 | 仅官方制裁名单KYC查询 |
| ⚠️ **天眼查/企查查司法接口** | 可用但**采购前必须核实其裁判文书/执行数据来源具备合法授权**，否则连带违法风险 | 采购前做供应商合规尽调 |
| 🔴 **人物 OSINT 画像拼装** | 即使每条合法，拼装构成处理敏感个人信息·persist_policy=ephemeral不落库 | 仅制裁名单核查 |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1

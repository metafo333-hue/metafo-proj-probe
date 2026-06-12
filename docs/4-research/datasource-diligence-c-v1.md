# probe · C尽调风控域 数据源调研报告 v1.0

> 日期：2026-06-10 · 性质：调研证据层（5子场景×三层优先级 + 四闸 · 含人物OSINT红线）
> 方法：三层优先级（L1官方/开源干净·L2授权第三方·L3公开低成本辅助）· 永不代爬 · 守个保法最小必要
> 合规框架：核心红线=**不自己爬数据**（不自建爬虫/不模拟登录/不抓包）· 人物信息 persist_policy=ephemeral（不落库红线）
> 参见 [调研方法论v1.1](datasource-research-methodology-v1.0.md)
> 上游：[架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) C-diligence · [feasibility-v1](probe-github-datasource-feasibility-v1.md) §C

---

## 一、综述

### 三层覆盖总评

C尽调风控域下设 5 个子场景：**C1企业背调 · C2人物背调 · C3投融资尽调 · C4供应商风险 · C5合规法律资产风险**。本次调研横跨全部子场景，覆盖 L1/L2/L3 三层，合计评估数据源 40+ 个，最终采纳/拟采纳 25+ 个，排除 10+ 个（含合规红线明确剔除）。

| 子场景 | L1可用 | L2待授权 | L3辅助 | 核心结论 |
|--------|--------|---------|--------|---------|
| **C1 企业背调** | OpenSanctions/GLEIF/EDGAR | 天眼查/企查查/Sayari | OpenCorporates | 中国工商必经天眼查；全球制裁/股权走L1即可 |
| **C2 人物背调** | OpenSanctions PEP端/Wikidata | 天眼查人物关联 | GLEIF/EDGAR高管 | 🔴 一律ephemeral不落库；画像拼装工具全部排除 |
| **C3 投融资尽调** | edgartools/GLEIF/OpenAleph | Crunchbase/天眼查 | Companies House | L1已覆盖海外；国内私募填补需R1付费 |
| **C4 供应商风险** | OpenSanctions+Yente/sanctions.network | SecurityScorecard/天眼查 | OFAC/UN/EU官方 | 制裁层L1充足；中国供应商雷达需天眼查R1 |
| **C5 合规法律资产** | crt.sh/RDAP/VirusTotal/Shodan InternetDB | Shodan完整API/MS EASM | OFAC/EU制裁 | 资产发现L1覆盖率高；商用需Shodan$49 R1 |

### 核心结论

1. **制裁/PEP筛查**：OpenSanctions 是全域 L1 基础层，350+官方来源聚合，非商业免费，5子场景均可复用。
2. **中国企业背调**：官方工商系统（gsxt/裁判文书）无公开API，必须经天眼查/企查查等商业平台中转，是**结构性合规债**，需 R1+R4 企业资质授权。
3. **人物OSINT**：🔴 最高级红线，全场景 persist_policy=ephemeral；画像聚合工具（Sherlock/Maigret/SpiderFoot）及人肉/社工库**一票否决**，详见第四章。
4. **资产风险**：crt.sh/RDAP/urlscan.io/Shodan InternetDB 形成L1免费资产发现底座，商用时 Shodan 完整API成本极低（$49一次性）。
5. **免费与商用分界**：OpenSanctions数据CC-BY-NC（非商业免费，商业需Bulk License）；VirusTotal/Shodan InternetDB 仅非商业免费——**商业化路径上必须触发对应R1**。

### 🔴 C2人物背调红线置顶声明

> **probe对人物OSINT采取最严格处理原则，此红线与任何业务优先级同级或更高：**
>
> - 任何通过probe获取的个人信息，**persist_policy强制=ephemeral**，即时查询后不落入任何数据库/文件/缓存
> - **禁止拼装个人画像**——即使每条碎片信息本身合法，拼装行为构成《个人信息保护法》下的处理敏感个人信息
> - **禁止将人物信息与企业信息交叉关联后存储**（如"张三在哪些公司任职"查询可以，但结果不入库）
> - 刑法253之一（侵犯公民个人信息罪）是明确刑事红线
> - 唯一合法目的：制裁名单核查（KYC/AML，基于官方名单的是否在列查询），且仅使用官方或OpenSanctions等合法渠道

---

## 二、5子场景源卡明细

### C1 企业背调

#### L1 · 官方/开源干净（推荐优先接入）

| # | 源名 | URL/Repo | 数据内容 | 许可证/成本 | 采纳决策 |
|---|------|---------|---------|-----------|---------|
| 1 | **OpenSanctions + Yente** | https://www.opensanctions.org / https://yente.followthemoney.tech | 350+来源制裁/PEP·全球黑名单·风险实体 | 软件MIT·数据CC-BY-NC·商业需Data License | ✅ 非商业P0采纳·商业待R1 |
| 2 | **OpenAleph（OCCRP Aleph）** | https://openaleph.org | 跨境公司/泄露/制裁·10亿+记录·开源版2025-12 sunset迁OpenAleph | 自托管MIT | ⚠️ 自托管备选·公开API仅新闻调查 |
| 3 | **OpenOwnership BODS** | https://www.openownership.org | 受益所有权·英国+30国 | CC0免费 | ✅ P1采纳（欧洲股权穿透场景） |
| 4 | **SEC EDGAR** | https://efts.sec.gov / edgartools | 美国上市公司工商/财报/内部人交易 | 公有领域·免费 | ✅ P0采纳（美股） |
| 5 | **GLEIF LEI API** | https://www.gleif.org | 全球法人识别码+Level2母子股权关系·200+国 | CC-BY·免费 | ✅ P0采纳（全球LEI穿透） |

#### L2 · 授权第三方/商业API（待R1/R4授权）

| # | 源名 | URL | 数据内容 | 成本估算 | 采纳决策 |
|---|------|-----|---------|---------|---------|
| 6 | **天眼查开放平台** | https://open.tianyancha.com | 1.8亿实体·90+维度·工商/股权/司法/经营异常 | 免费500条/日·超出¥0.05/条·需企业资质 | ⚠️ 待授权R1+R4（中国企业背调首选） |
| 7 | **企查查** | https://openapi.qcc.com | 2.3亿实体·同类维度 | 商业付费·需企业资质 | ⚠️ 待授权R1（天眼查备选） |
| 8 | **启信宝** | https://www.qixin.com/api-introduce | 2.3亿实体·偏金融风控 | 商业付费 | ⚠️ 待授权R1（第三备选） |
| 9 | **Sayari** | https://sayari.com | 4亿企业+4.6亿人物·200国·企业关系图谱 | 数万美元/年（企业定价） | ⚠️ 待授权R1（P2高成本·高端合规需求） |

#### L3 · 公开低成本辅助

| # | 源名 | 访问方式 | 说明 | 采纳决策 |
|---|------|---------|------|---------|
| 10 | **OpenCorporates** | https://opencorporates.com | 免费200条/月·商业付费 | ✅ P1采纳 |
| 11 | **国家企业信用公示系统 gsxt** | 无官方API（经天眼查合规读取） | 直爬违反不自己爬红线 | ❌ probe不直接爬·经天眼查覆盖 |
| 12 | **裁判文书网** | 2023起公众检索受限·经天眼查降级 | 滞后1-3月·非全量 | ⚠️ 经天眼查降级覆盖 |

> **结构性缺口说明**：中国裁判文书2023后受限·中国非上市私企财务无官方API·中国工商无官方公开API——以上三项必须经天眼查等商业平台中转，是不可绕过的**结构性合规债**。

---

### C2 人物背调（🔴 persist_policy=ephemeral 全场景强制）

> 本子场景全部数据源受最高级红线约束：查询结果不落库、不建档、不做画像拼装。

#### L1 · 官方/开源干净（合规目的内可用·ephemeral）

| # | 源名 | URL/Repo | 数据内容 | 许可证 | 采纳决策 |
|---|------|---------|---------|--------|---------|
| 1 | **OpenSanctions PEP端** | https://www.opensanctions.org/pep/ | 全球PEP（政治敏感人员）/制裁名单·KYC/AML合法目的查询 | CC-BY-NC·非商业免费 | ✅ P0采纳（合规筛查·不落库） |
| 2 | **Wikidata SPARQL** | https://query.wikidata.org | 公众人物公开任职/政治角色·不含私人信息 | CC0·免费 | ✅ P1采纳（公众人物公开属性·ephemeral） |
| 3 | **WikiRate** | https://wikirate.org | 企业高管ESG公开披露·研究机构背景 | CC-BY·免费key | ✅ P2采纳（高管ESG·ephemeral） |

#### L2 · 授权第三方（仅公开登记角色·严格边界）

| # | 源名 | 使用边界 | 成本 | 采纳决策 |
|---|------|---------|------|---------|
| 4 | **天眼查人物关联** | 仅"自然人在企业公开登记角色"（张三在哪些公司任职）·禁扩展个人信息档案·ephemeral | 企业资质+R1 | ⚠️ P1待授权（仅公开登记·不建档） |
| 5 | **启信宝人物** | 同路径同限制 | R1 | ⚠️ 天眼查备选 |
| 6 | **Sayari人物** | 4.6亿人物公开注册信息·非隐私挖掘·ephemeral | 数万美元/年 | ⚠️ P2高成本备选 |

#### L3 · 公开辅助（高管公开披露·ephemeral）

| # | 源名 | 数据内容 | 采纳决策 |
|---|------|---------|---------|
| 7 | **OpenSanctions官方数据集** | 350+官方制裁名单聚合 | ✅ P0（ephemeral） |
| 8 | **GLEIF** | 企业高管公开登记角色 | ✅ P1（ephemeral） |
| 9 | **SEC EDGAR Form4/DEF14A** | 上市公司高管公开披露 | ✅ P1（ephemeral） |

#### ❌ 红线排除（一票否决）

| 工具/方向 | 弃用理由 |
|----------|---------|
| **Sherlock / Maigret** | 跨平台账号聚合拼装人物画像·PIPL处理敏感个人信息无合法依据·刑法253之一·闸A一票否决 |
| **SpiderFoot（人物模式）** | 同上·OSINT聚合画像·与probe禁拼装画像红线正面冲突 |
| 任何人肉/社工库 | 非法获取公民个人信息·明确刑事红线 |
| **人物画像拼装（即使碎片合规）** | 拼装行为本身违反PIPL·禁止 |

---

### C3 投融资尽调

#### L1 · 官方/开源干净

| # | 源名 | URL/Repo | 数据内容 | 许可证/成本 | 采纳决策 |
|---|------|---------|---------|-----------|---------|
| 1 | **edgartools** | dgunning/edgartools MIT | SEC文件·XBRL财报/13F/Form4内部人交易·2026出MCP server | MIT·免费 | ✅ P0采纳 |
| 2 | **GLEIF LEI API** | https://www.gleif.org | 全球法人识别+Level2母子关系·覆盖200+国 | CC-BY·免费 | ✅ P0采纳 |
| 3 | **OpenAleph / OCCRP Aleph** | https://openaleph.org | 10亿+记录·跨境公司/泄露/投资关系·自托管MIT | MIT自托管 | ✅ 自托管采纳·公开API需授权 |

#### L2 · 授权第三方/商业API（待R1）

| # | 源名 | URL | 数据内容 | 成本 | 采纳决策 |
|---|------|-----|---------|------|---------|
| 4 | **Crunchbase API v4** | https://data.crunchbase.com/docs | 融资轮次/投资机构/50+字段·2026废免费层 | $49/月起 | ⚠️ 待授权R1（Sprint4） |
| 5 | **PitchBook Direct Data** | pitchbook.com | 私募深度·机构投资·12k-70k/年 | $12k-70k/年 | ⚠️ 待授权R1（中大B客户才值·高成本） |
| 6 | **天眼查** | https://open.tianyancha.com | 169维度·股权穿透·融资记录·试用20次 | 企业认证+付费 | ⚠️ 待授权R1+R4（国内投融资首选） |

#### L3 · 公开低成本辅助

| # | 源名 | URL | 内容 | 采纳决策 |
|---|------|-----|------|---------|
| 7 | **SEC EDGAR EFTS全文检索** | https://efts.sec.gov | 免费无key·布尔检索·S-1/10-K/424B等 | ✅ P0采纳 |
| 8 | **GLEIF Golden Copy** | gleif.org | 全量LEI每日更新·CC-BY免费·离线股权穿透 | ✅ P0采纳（离线穿透） |
| 9 | **Companies House** | https://developer.company-information.service.gov.uk | 英国企业工商/股权/filing·免费REST | ✅ P1采纳 |

---

### C4 供应商风险（批量·订阅雷达）

#### L1 · 官方/开源干净

| # | 源名 | URL/Repo | 数据内容 | 许可证/成本 | 采纳决策 |
|---|------|---------|---------|-----------|---------|
| 1 | **OpenSanctions + Yente** | https://www.opensanctions.org | 350+源·Yente5.0 logic-v2·自托管8GB/60GB·30分钟更新 | 非商业免费/商业Bulk License | ✅ 非商业P0·商业R1 |
| 2 | **sanctions.network** | https://sanctions.network | OFAC+UN+EU三列表·postgREST接口·任何用途免费 | 免费任何用途 | ✅ P0采纳（轻量补充） |
| 3 | **SpiderFoot（域名/资产被动侦察）** | spiderfoot.net / MIT | 供应商域名/资产被动侦察·批量扫描 | MIT自托管 | ✅ P1采纳（自托管被动侦察·非人物模式） |

#### L2 · 授权第三方/商业API（待R1）

| # | 源名 | URL | 数据内容 | 成本 | 采纳决策 |
|---|------|-----|---------|------|---------|
| 4 | **SecurityScorecard** | https://securityscorecard.com | 供应商网络安全评分A-F | 5位数年费 | ⚠️ 待授权R1（先评ROI·有SpiderFoot+Shodan替代可延后） |
| 5 | **Sayari Graph** | https://sayari.com | 36亿记录·供应链穿透·企业合同 | 企业定价 | ⚠️ 待授权R1（高端合规客户场景） |
| 6 | **天眼查变更订阅** | https://open.tianyancha.com | 经营异常/工商变更实时推送雷达 | 企业认证+付费 | ⚠️ 待授权R1+R4（中国供应商雷达） |

#### L3 · 官方制裁原始层

| # | 源名 | URL | 内容 | 采纳决策 |
|---|------|-----|------|---------|
| 7 | **OFAC SLS** | https://ofac.treasury.gov/sanctions-list-service | 美国官方制裁REST·免费 | ✅ P0采纳（原始数据层） |
| 8 | **UN制裁 / EU FSF** | 官方下载 | 官方制裁名单·已整合进OpenSanctions | ✅ P0采纳（走OpenSanctions统一层） |

> **缺口**：Yente商业部署需Bulk License（R1）；中国出口管制名单暂无整合方案；供应商批量实时变更雷达国内只有天眼查路径。

---

### C5 合规法律资产风险

#### L1 · 官方/开源干净

| # | 源名 | URL/Repo | 数据内容 | 许可证/成本 | 采纳决策 |
|---|------|---------|---------|-----------|---------|
| 1 | **crt.sh** | https://crt.sh | 证书透明度·子域发现·JSON无key | 免费无key | ✅ P0采纳（资产发现） |
| 2 | **RDAP（+ who-dat）** | https://rdap.iana.org | ICANN 2025弃WHOIS·结构化JSON域名溯源·who-dat MIT自托管 | 免费 | ✅ P0采纳（域名溯源） |
| 3 | **VirusTotal** | https://docs.virustotal.com | 70+引擎域名/URL声誉 | 免费4req/min·商业产品禁用免费层 | ✅ 非商业P0·商业需R1 |
| 4 | **urlscan.io** | https://urlscan.io | URL扫描·免费5000/月 | 免费 | ✅ P0采纳（低频资产扫描） |
| 5 | **AbuseIPDB** | https://www.abuseipdb.com | IP信誉·免费1000条/天 | 免费 | ✅ P1采纳 |
| 6 | **Shodan InternetDB** | https://internetdb.shodan.io | 无key·IP端口/CVE·周更 | 仅非商业免费 | ✅ 非商业P0·商业R1 |

#### L2 · 授权第三方/商业API（待R1）

| # | 源名 | URL | 数据内容 | 成本 | 采纳决策 |
|---|------|-----|---------|------|---------|
| 7 | **Shodan API完整版** | https://shodan.io | 全网暴露面·IP资产/端口/CVE·可商用 | 一次性$49会员即商用 | ⚠️ 待授权R1（**强烈建议**·成本极低） |
| 8 | **MS Defender EASM** | Azure | 资产暴露面管理·$0.011/资产/天 | Azure订阅 | ⚠️ 待授权R1（补充） |
| 9 | **WhoisXML** | whoisxmlapi.com | 批量历史WHOIS | 按需付费 | ⚠️ 待授权R1（按需） |

#### L3 · 官方制裁/域名辅助

| # | 源名 | 内容 | 采纳决策 |
|---|------|------|---------|
| 10 | **OpenSanctions** | 制裁名单名字核查·非商业免费 | ✅ 非商业P0 |
| 11 | **OFAC/EU/UN** | 官方制裁·免费 | ✅ P0 |
| 12 | **RDAP IANA bootstrap** | 官方bootstrap端点·免费 | ✅ P0 |

> **缺口**：.cn域名RDAP覆盖率低（ccTLD仅34%·CNNIC无公开RDAP端点）；微信小程序/App链接无风险API；境内域名历史溯源需WhoisXML等付费方案。

---

## 三、推荐首选源汇总表

> 状态口径：✅ 立即可接（非商业·零成本） · ⚠️R1 待授权付费 · ⚠️自托管 需运维投入 · ❌ 排除

| 源名 | 覆盖子场景 | 层级 | 许可证/成本 | 商用限制 | 优先批次 |
|------|----------|------|-----------|---------|---------|
| **OpenSanctions + Yente** | C1/C2/C4/C5 | L1 | CC-BY-NC / 商业Bulk License | 非商业免费 · 商业R1 | P0（非商用）/ R1（商用） |
| **GLEIF LEI API** | C1/C2/C3 | L1 | CC-BY · 免费 | 无 | P0 |
| **SEC EDGAR / edgartools** | C1/C2/C3 | L1 | 公有领域 · 免费 | 无 | P0 |
| **GLEIF Golden Copy** | C3 | L3 | CC-BY · 免费 | 无 | P0 |
| **SEC EDGAR EFTS** | C3 | L3 | 公有领域 · 免费 | 无 | P0 |
| **OFAC SLS** | C4/C5 | L3 | 官方 · 免费 | 无 | P0 |
| **sanctions.network** | C4 | L1 | 免费任何用途 | 无 | P0 |
| **crt.sh** | C5 | L1 | 免费无key | 无 | P0 |
| **RDAP** | C5 | L1 | 免费 | 无 | P0 |
| **urlscan.io** | C5 | L1 | 免费5000/月 | 免费层 | P0 |
| **OpenOwnership BODS** | C1 | L1 | CC0 · 免费 | 无 | P1 |
| **OpenCorporates** | C1 | L3 | 免费层200/月 | 商业付费 | P1 |
| **Companies House** | C3 | L3 | UK Open Gov · 免费 | 无 | P1 |
| **Wikidata SPARQL** | C2 | L1 | CC0 · 免费 | 无 | P1（ephemeral） |
| **AbuseIPDB** | C5 | L1 | 免费1000/天 | 免费层 | P1 |
| **SpiderFoot（资产侦察）** | C4/C5 | L1 | MIT · 自托管 | 无 | P1（自托管） |
| **OpenAleph** | C1/C3 | L1 | MIT · 自托管 | 无 | P1（自托管） |
| **Shodan InternetDB** | C5 | L1 | 非商业免费 | 商业禁用免费层 | P0（非商用）|
| **VirusTotal** | C5 | L1 | 非商业免费 | 商业禁用免费层 | P0（非商用）|
| **天眼查** | C1/C2/C4 | L2 | 企业资质+付费 | R1+R4 | Sprint3待授权 |
| **Crunchbase** | C3 | L2 | $49/月起 | R1 | Sprint4待授权 |
| **Shodan完整API** | C5 | L2 | $49一次性 | R1 | Sprint3待授权（强推） |

---

## 四、🔴 红线与合规边界

### 4.1 C2人物OSINT · persist_policy=ephemeral 铁律

**这是probe最高级合规红线，与P0红线同级：**

- **不落库**：任何自然人相关查询结果（任职角色/制裁状态/公开披露）一律不写入PG、Redis、SQLite或任何持久化存储
- **不建档**：禁止对同一自然人多次查询结果进行汇总、关联或存储
- **不拼装画像**：即使每条信息来自合法公开来源（工商登记/制裁名单/公开报道），将其拼装成个人画像仍构成《个人信息保护法》下的处理行为，无合法依据
- **唯一例外**：制裁名单核查（KYC/AML目的·基于官方名单的二值查询）——**但查询结果依然ephemeral，不留痕**

法律依据：
- 《个人信息保护法》第13条（处理须有合法依据）
- 《刑法》第253条之一（侵犯公民个人信息罪·5年以下有期徒刑）
- 处理敏感个人信息须取得单独同意（PIPL第29条）

### 4.2 被排除的隐私挖掘工具（C2红线）

| 工具/服务 | 排除理由 |
|----------|---------|
| **Sherlock**（sherlock-project/sherlock） | 跨平台账号用户名枚举·聚合拼装身份·PIPL/刑253一票否决 |
| **Maigret**（soxoj/maigret） | Sherlock增强版·更强画像拼装·同样一票否决 |
| **SpiderFoot（人物模式）** | 人物OSINT模式聚合多源信息·禁入probe人物查询链路 |
| **任何人肉/社工库** | 非法获取公民个人信息·明确刑事红线 |

> 注：SpiderFoot在C4供应商风险中以「域名/资产被动侦察」模式采纳（不涉及人物信息），与上述人物模式是不同使用场景。

### 4.3 数据出境与PIPL

- 天眼查/企查查/启信宝涉及中国自然人登记角色数据，出境前须评估《数据出境安全评估办法》
- 即使是企业公开登记信息，大规模批量出境可能触发安全评估义务
- probe使用境内服务器缓存时需遵守PIPL；若数据流向境外节点则需额外评估

### 4.4 免费层非商业限制汇总

| 源 | 非商业 | 商业 |
|----|--------|------|
| OpenSanctions数据（CC-BY-NC） | 免费 | 需Bulk License·R1 |
| VirusTotal免费API | 可用 | 禁用免费层·需付费API·R1 |
| Shodan InternetDB | 可用 | 禁用免费层·完整API $49·R1 |
| Shodan完整API | — | $49一次性·即可商用 |
| Crunchbase API | 2026废免费层 | $49/月·R1 |

---

## 五、待授权清单

### R1付费授权（需元东方支付决策）

| # | 源名 | 子场景 | 预估成本 | 必要性 | 建议批次 |
|---|------|--------|---------|--------|---------|
| 1 | **天眼查开放平台** | C1/C2/C4 | ¥0.05/条超额+企业资质 | 中国企业背调/供应商雷达**唯一可行路径** | Sprint3·高优先 |
| 2 | **Shodan完整API** | C5 | $49一次性·永久商用 | 资产风险商业化·ROI极高 | Sprint3·强烈建议 |
| 3 | **OpenSanctions Bulk License** | C1/C2/C4 | 待询价 | 商业化后制裁筛查合规前提 | Sprint3·与商业化同步 |
| 4 | **VirusTotal付费API** | C5 | $0.01/query起 | 商业化后URL/域名声誉 | Sprint3·与商业化同步 |
| 5 | **Crunchbase API v4** | C3 | $49/月起 | 投融资数据·海外VC/PE覆盖 | Sprint4 |
| 6 | **企查查 / 启信宝** | C1 | 商业付费 | 天眼查容灾备选 | Sprint4（天眼查先） |
| 7 | **WhoisXML** | C5 | 按需 | .cn历史WHOIS补充 | Sprint4·按需 |
| 8 | **SecurityScorecard** | C4 | 5位数年费 | 供应商安全评分·有替代先评ROI | Sprint5（评ROI后决策） |
| 9 | **PitchBook Direct Data** | C3 | $12k-70k/年 | 私募深度·仅高端客户值 | Sprint5·慎重 |
| 10 | **Sayari** | C1/C2/C4 | 数万美元/年 | 高端合规·200国覆盖 | Sprint5·大客户才触发 |

### R4企业资质要求

| 源名 | 资质要求 |
|------|---------|
| 天眼查 | 企业营业执照+法人认证（绵阳零元电子商务） |
| 企查查 | 企业认证 |
| 启信宝 | 企业认证 |

---

## 六、覆盖缺口与对策

| 缺口 | 影响子场景 | 严重性 | 对策 |
|------|----------|--------|------|
| **中国裁判文书全量**（2023后受限） | C1/C4 | 高 | 经天眼查降级覆盖（非全量·滞后1-3月）；无完美替代方案 |
| **中国非上市私企财务数据** | C1/C3 | 高 | 天眼查部分覆盖·深度财务仍是结构性缺口 |
| **中国工商无官方公开API** | C1 | 高 | 必经天眼查/企查查中转（结构性合规债） |
| **.cn域名RDAP覆盖率低**（ccTLD 34%）| C5 | 中 | RDAP补.cn时回退WHOIS；WhoisXML付费历史补全 |
| **微信小程序/App链接风险API** | C5 | 中 | 无现成解法；仅能查域名层·深层链接风险盲区 |
| **中国出口管制名单整合** | C4 | 中 | 暂无整合来源；待Sprint4评估专项数据库 |
| **Yente商业Bulk License** | C1/C2/C4 | 中 | 商业化时R1触发；非商业阶段自托管免费层 |
| **私募/VC深度数据（海外）** | C3 | 中 | PitchBook成本过高；Crunchbase $49/月为现阶段最优 |
| **供应商实时变更雷达（非中国）** | C4 | 低 | OpenSanctions 30分钟更新已覆盖制裁变更；工商变更雷达境外待补 |

---

## 七、对接批次建议

| 批次 | 时间 | 源名 | 动作 | 前提 |
|------|------|------|------|------|
| **P0·立即可接** | 当前Sprint | OpenSanctions自托管（非商业） | 部署Yente自托管·接ledger.yaml | 自托管资源 |
| **P0·立即可接** | 当前Sprint | GLEIF LEI API | 注册免费key·接L1 | 无 |
| **P0·立即可接** | 当前Sprint | edgartools + SEC EDGAR EFTS | 接C1/C3 | 无 |
| **P0·立即可接** | 当前Sprint | crt.sh / RDAP / urlscan.io | 接C5资产发现层 | 无 |
| **P0·立即可接** | 当前Sprint | sanctions.network | 接C4轻量制裁层 | 无 |
| **P0·立即可接** | 当前Sprint | OFAC SLS + UN/EU官方制裁 | 经OpenSanctions统一层接入 | 上游Yente部署 |
| **P1·Sprint3** | Sprint3 | 天眼查开放平台 | R1+R4企业授权·测试API·接C1/C4 | 元东方R1+R4确认·企业资质 |
| **P1·Sprint3** | Sprint3 | Shodan完整API $49 | 元东方R1确认后购买·接C5商用链路 | 元东方R1确认 |
| **P1·Sprint3** | Sprint3 | OpenSanctions Bulk License | 商业化时同步触发·询价 | 商业化决策 |
| **P1·Sprint3** | Sprint3 | OpenAleph自托管 | 评估存储/计算资源后部署 | ufo GPU资源评估 |
| **P2·Sprint4** | Sprint4 | Crunchbase API v4 | R1授权·接C3投融资 | 元东方R1确认 |
| **P2·Sprint4** | Sprint4 | 企查查 / 启信宝 | 天眼查容灾备选 | 天眼查已验证后评估 |
| **P3·Sprint5+** | Sprint5 | SecurityScorecard | ROI评估后决策 | 先用SpiderFoot+Shodan替代方案验证 |
| **P3·Sprint5+** | Sprint5 | Sayari | 高端合规大客户触发时再授权 | 大客户需求 |
| **P3·Sprint5+** | Sprint5 | PitchBook | 高端客户私募尽调需求出现时 | 需求驱动 |

---

> 文档状态：v1.0 调研证据层（2026-06-10）· 下一步=任务3 ledger.yaml C域源卡录入 + Yente自托管部署验证
> 相关：[调研方法论](datasource-research-methodology-v1.0.md) · [feasibility §C](probe-github-datasource-feasibility-v1.md) · [批次计划](datasource-research-onboarding-batch-plan-v1.0.md)

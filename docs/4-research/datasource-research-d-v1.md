# probe · D调研知识技术域 数据源调研报告 v1.0

> 日期：2026-06-10 · 性质：调研证据层（5子场景×三层+四闸）
> 方法：三层优先级 · 永不代爬 · 见 [调研方法论v1.1](datasource-research-methodology-v1.0.md)
> 上游：[架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) D-research · [feasibility-v1](probe-github-datasource-feasibility-v1.md) §D

---

## 一、综述

### 核心结论

**D调研知识技术域是probe五大赛道中免费开源源最丰富、M0零成本可立即接的源最多的领域**。五个子场景（D1深度调研底座、D2技术开源生态、D3学术专利、D4政策宏观经济、D5文档情报提取）均有高质量免费源直接可用，付费源仅在D3专利深度、D5商业OCR、D1语义增强等特定能力缺口时才需要。

主要发现：
- **L1层**：SearXNG、GDELT、Wikimedia/Wikidata、OSV.dev、deps.dev、dbnomics、Docling等均为MIT/Apache/CC0协议、免费自托管或无key可用，构成D域骨干
- **L3层官方权威源**：arXiv、FRED、World Bank、IMF、OECD、Eurostat等全部免费key，补充深度和权威性
- **最大单点缺口**：CNIPA中国专利无官方API（D3）、中国NBS无开放API（D4），是D域唯二无法零成本覆盖的权威来源
- **License红线**：PyMuPDF(AGPL)、MinerU(Apache附加商业条款)、marker-pdf(GPL+nc-sa模型)三个解析库需法务审查，不可直接商用

### 三层覆盖总评

| 子场景 | L1（开源自托管） | L2（综合服务） | L3（权威官方） | M0可用状态 |
|--------|----------------|--------------|--------------|-----------|
| D1 深度调研底座 | SearXNG·GDELT·Wikimedia | Tavily·Exa | arXiv·GitHub API | ✅ 立即可用 |
| D2 技术开源生态 | OSV·deps.dev·Libraries.io·GH Archive | Snyk(P1) | NVD·GitHub Advisory | ✅ 立即可用 |
| D3 学术专利 | OpenAlex·Crossref·arXiv | SemanticScholar·Lens | PubMed·USPTO·EPO | ✅ 部分立即可用 |
| D4 政策宏观经济 | dbnomics·fredapi·wbgapi | Alpha Vantage(P1) | FRED·WB·IMF·OECD·Eurostat | ✅ 立即可用 |
| D5 文档情报提取 | Docling·MarkItDown·trafilatura·unstructured·GROBID | LlamaParse·Mistral OCR | arXiv.py·EDGAR | ✅ 立即可用 |

---

## 二、5子场景源卡明细

### D1 深度调研底座

| 源 | 层级 | 官方文档 | License / 配额 | 裁决 |
|----|------|---------|---------------|------|
| **SearXNG** | L1 | https://docs.searxng.org | AGPL · 70+引擎聚合 · 已与LiteLLM/LangChain集成 · 自托管零成本 | **采纳（核心底座）** |
| **GDELT 2.0 DOC API** | L1 | https://api.gdeltproject.org | 完全免费无key · 全球新闻实时 · BigQuery历史查询 | **采纳（新闻首选）** |
| **Wikimedia REST API** | L1 | https://www.mediawiki.org/wiki/REST_API | CC BY-SA/CC0 · 完全免费 · 多语言维基百科+Wikidata SPARQL | **采纳P0** |
| **arXiv API** | L3 | https://info.arxiv.org/help/api | 免费无key · 速率≤1req/3s · 2026-02起偶发429需实现指数退避 | **采纳** |
| **GitHub API / PyGithub** | L3 | https://pygithub.readthedocs.io | 免费PAT · 5000req/h · repo/user/trend数据 | **采纳** |
| Tavily | L2 | https://docs.tavily.com | AI原生搜索 · 免费1000次/月 · Researcher $30/月 | **待授权R1（优先）** |
| Exa | L2 | https://exa.ai | 神经语义检索 · 免费1000次/月 · $49/月 | **待授权R1（与Tavily二选一）** |

> 说明：SearXNG AGPL协议在自托管服务器场景下合规（不分发软件本体）。Tavily/Exa属L2付费增强层，M0阶段可跳过，M1语义增强时优先选Tavily。

---

### D2 技术开源生态

| 源 | 层级 | 官方文档 | License / 配额 | 裁决 |
|----|------|---------|---------------|------|
| **OSV.dev** | L1 | https://osv.dev | Apache 2.0 · 40+生态漏洞聚合(含NVD/GHSA/PyPI/npm等) · 无速率限制 · 附带OSV-Scanner | **采纳（漏洞首选·无可替代）** |
| **deps.dev** | L1 | https://deps.dev | Google免费开放 · 5000万+包 · 依赖图/license/advisory全覆盖 | **采纳（依赖健康分析）** |
| **Libraries.io API** | L1 | https://libraries.io/api | 免费key · 34个包管理器 · 60req/min · SourceRank趋势评分 | **采纳（趋势分析）** |
| **GH Archive** | L1 | https://www.gharchive.org | 完全免费 · GitHub全量事件流 · BigQuery历史 · 15分钟粒度 | **采纳（活跃度趋势）** |
| **NVD CVE API** | L3 | https://nvd.nist.gov/developers | 官方CVE数据库 · 免费key · 50req/30s · CVSS评分权威来源 | **采纳（OSV已聚合·需CVSS v3细节时直连）** |
| **GitHub Advisory Database** | L3 | https://github.com/advisories | 免费 · CC-BY 4.0 · OSV格式 · OSV.dev已聚合 | **采纳（OSV已含·需溯源时直连）** |
| **GitHub REST API** | L3 | — | 同D1 · repo元数据骨架 | **采纳（核心骨架）** |
| Snyk | L2 | https://security.snyk.io | 自研专有漏洞数据库 · 公开repo免费 · Team $25/开发者/月 | **待授权P1（OSV未覆盖的Snyk专有漏洞时）** |
| ~~Sourcegraph~~ | L2 | — | 免费层已deprecated · 企业$49/用户/月 | **弃（改用GitHub Code Search API）** |

> 同源去重提示：OSV.dev已聚合NVD+GHSA+PyPI/npm advisory，三者直连会产生重复漏洞条目，默认以OSV为主路，需CVSS细节再走NVD。

---

### D3 学术专利

| 源 | 层级 | 官方文档 | License / 配额 | 裁决 |
|----|------|---------|---------------|------|
| **OpenAlex / PyAlex** | L1 | https://openalex.org | CC0 · 2.5亿学术作品 · 2026-02起需注册免费key+credit制 · 超量$1/天信用 | **采纳（学术首选）** |
| **Crossref / habanero** | L1 | https://api.crossref.org | 1.5亿DOI · 无key可用(polite pool加mailto) · Crossref Metadata Plus付费增强 | **采纳（DOI元数据权威）** |
| **arXiv** | L1 | — | 同D1 · 免费 · AI/CS预印本最权威 | **采纳（AI/CS最新论文）** |
| **Semantic Scholar** | L2 | https://api.semanticscholar.org | 2亿+论文 · 影响力评分 · 无key 100次/5min · 免费key申请后1RPS | **采纳（免费key申请·影响力评分）** |
| **Lens.org** | L2 | https://docs.api.lens.org | 学术+专利双库 · 180M专利(聚合USPTO+EPO+WIPO) · 非商业学术token免费 · 商业ITK付费 | **待授权（申请非商业学术token·专利主力）** |
| **PubMed Entrez / Biopython** | L3 | https://www.ncbi.nlm.nih.gov/books/NBK25497 | 3500万医学文献 · 免费key · 10req/s（有key）· 3req/s（无key）| **采纳（医学生命科学必选）** |
| **USPTO ODP** | L3 | https://data.uspto.gov | 全量美国专利 · 2026-03迁移新平台 · **2026-06-18起需账户·旧key失效须重申请** | **采纳（须重申请ODP账户key）** |
| **EPO OPS v3.2** | L3 | https://developers.epo.org | 欧洲专利 · 免费注册 · 4GB/周配额 | **采纳** |
| **WIPO PATENTSCOPE** | L3 | — | API付费600CHF/年 · Lens.org已聚合WIPO数据 | **待授权P2暂缓（Lens覆盖时无需直连）** |
| **CNIPA中国专利** | L3 | — | 无官方开放API · PatSnap/智慧芽均为企业付费产品 | **❌ 最大缺口·无零成本方案** |

> 同源去重提示：OpenAlex、Crossref、SemanticScholar均可按DOI去重；arXiv ID与DOI存在交叉（同一论文两个ID），需建arXiv-ID↔DOI映射表；Lens.org已聚合USPTO+EPO+WIPO，接入Lens后三者可不直连（除非需USPTO CVSS细节）。

---

### D4 政策宏观经济

| 源 | 层级 | 官方文档 | License / 配额 | 裁决 |
|----|------|---------|---------------|------|
| **dbnomics** | L1 | https://docs.db.nomics.world | 完全免费无key · 87个机构来源 · 9.5亿条时序(含FRED/WB/OECD/IMF/Eurostat) · 单点聚合 | **采纳P0（强烈推荐·最佳单点聚合）** |
| **fredapi** | L1 | https://github.com/mortada/fredapi | Apache 2.0 · FRED官方非官方封装 · 80万条美国时序 · 免费key · **禁止再分发原始API数据** | **采纳P0** |
| **wbgapi** | L1 | https://pypi.org/project/wbgapi | World Bank官方库 · 16000+指标 · 无key · CC-BY（禁商业再销售） | **采纳P0** |
| **pandas-datareader** | L1 | — | BSD · 多源统一接口(FRED/WB/OECD等) | **采纳P1（兜底备选）** |
| **FRED API** | L3 | https://fred.stlouisfed.org/docs/api | 80万美国经济时序 · 免费key · **数据来源须注明StLouisFed·禁再分发原始API响应** | **采纳P0** |
| **World Bank API** | L3 | https://datahelpdesk.worldbank.org | 16000+发展指标 · 无key · CC-BY（禁原始转售） | **采纳P0** |
| **IMF SDMX API** | L3 | https://data.imf.org/?sk=388dfa60-1d26-4ade-b505-a05a558d9a42 | 190国宏观数据 · 无key · 每连续10次请求后会短暂暂停（设backoff） | **采纳P0** |
| **OECD SDMX API** | L3 | https://data.oecd.org/api | 38成员国统计 · 无key · 单次最多100万观测 | **采纳P0** |
| **Eurostat API** | L3 | https://ec.europa.eu/eurostat/api/dissemination | 欧盟统计 · 无key · CC-BY · SDMX格式 | **采纳P0** |
| **data.gov Socrata API** | L3 | https://data.gov | 52万联邦数据集目录 · 免费key · 仅元数据目录（具体数据集各自API） | **采纳P1** |
| Alpha Vantage | L2 | https://www.alphavantage.co | 宏观端点 · 免费25次/天 · $50/月Premium | **待授权P1（dbnomics已覆盖大部分·性价比一般）** |
| 中国NBS | L3 | — | 官方无开放API · 经dbnomics nbsc库可部分接入（合规风险待评估） | **待授权（经dbnomics·合规风险需确认）** |
| Quandl / Nasdaq Data Link | L2 | — | 与FRED/WB数据高度重叠 | **待授权P2（重叠度高·推迟）** |

> 缺口说明：中国NBS、俄罗斯Rosstat、印度MOSPI等新兴市场官方机构无标准开放API，dbnomics通过第三方抓取提供部分数据（nbsc库合规风险需法务确认）。实时政策文本（如央行会议纪要PDF）需配D5文档解析。

---

### D5 文档情报提取

| 源 | 层级 | 官方文档 | License / 配额 | 裁决 |
|----|------|---------|---------------|------|
| **Docling** | L1 | https://github.com/docling-project/docling | MIT · 全格式(PDF/DOCX/PPTX/HTML/图片) · 版面分析/表格/公式/OCR · LF AI基金会孵化 · 61k stars | **采纳P0（主力解析引擎·首选）** |
| **MarkItDown** | L1 | https://github.com/microsoft/markitdown | MIT · 微软出品 · 全格式→Markdown轻量转换 · 无重型依赖 | **采纳P0（轻量补充·快速提取场景）** |
| **trafilatura** | L1 | https://github.com/adbar/trafilatura | Apache 2.0 · 网页正文精准抽取 · 毫秒级 · 去噪/导航栏/广告过滤 | **采纳P0（HTML正文抽取）** |
| **unstructured** | L1 | https://github.com/Unstructured-IO/unstructured | Apache 2.0 · 专为RAG预处理ETL · 多格式统一接口 | **采纳P0（RAG预处理管线）** |
| **GROBID** | L1 | https://github.com/grobidOrg/grobid | Apache 2.0 · 学术PDF结构化提取(参考文献/作者/摘要/章节) · 自托管Docker | **采纳P0（学术论文专属）** |
| **pdfplumber** | L1 | https://github.com/jsvine/pdfplumber | MIT · 金融报表/合同表格精度最高 · 像素级定位 | **采纳P1（金融合同场景）** |
| **arXiv.py / PyAlex / EDGAR** | L3 | — | 免费 · 研报/论文原文获取 · 配合Docling解析 | **采纳P0** |
| LlamaParse | L2 | https://www.llamaindex.ai/llamaparse | 免费层1万credits/月 · 超出按credit付费 | **待授权P1（免费层验证效果后决定）** |
| Mistral OCR 3 | L2 | https://mistral.ai/technology/#ocr | $1-2/千页 · SOTA OCR能力 · 支持手写/低质量扫描 | **待授权P1（性价比最优OCR·手写扫描场景）** |
| Azure Document Intelligence | L2 | https://azure.microsoft.com/zh-cn/products/ai-services/ai-document-intelligence | F0免费500页/月 · Read $1.5/千页 · 表单$50/千页 | **待授权P2** |
| AWS Textract | L2 | https://aws.amazon.com/textract | OCR $1.5/千页 · 表单/表格$50/千页 | **待授权P2** |
| PyMuPDF / pymupdf4llm | L1 | https://github.com/pymupdf/PyMuPDF | **AGPL-3.0 · 商业使用需Artifex付费商业许可** | **待授权P1（法务审查AGPL合规）** |
| MinerU | L1 | https://github.com/opendatalab/MinerU | Apache附加商业条款 · 超过MAU/营收阈值需商业许可 · 中国OpenDataLab团队 | **待授权P2（法务审查附加条款）** |
| ~~marker-pdf~~ | L1 | — | GPL-3.0 + 模型CC-BY-NC-SA · 双重许可 · 商业风险高 | **弃（双重许可·商业场景不可用）** |

---

## 三、推荐首选源汇总表

> M0批次：标注✅的源均可立即接入，无需R1付费授权。

| 子场景 | 首选源（M0零成本） | 能力覆盖 |
|--------|-----------------|---------|
| D1 深度调研 | SearXNG（自托管） + GDELT + Wikimedia/Wikidata | 通用检索底座+全球新闻+知识图谱 |
| D1 深度调研（学术） | arXiv API + GitHub API | 技术预印本+开源仓库 |
| D2 漏洞安全 | **OSV.dev**（无速率限制） | 40+生态漏洞聚合，含NVD+GHSA |
| D2 依赖健康 | **deps.dev** + Libraries.io | 5000万包依赖关系+SourceRank |
| D2 社区趋势 | GH Archive + GitHub API | GitHub全量事件流 |
| D3 学术元数据 | **OpenAlex** + **Crossref** | 2.5亿作品CC0 + 1.5亿DOI |
| D3 预印本 | arXiv API | AI/CS前沿 |
| D3 医学 | PubMed Entrez | 3500万医学文献 |
| D3 专利（国际） | EPO OPS v3.2 + **USPTO ODP**（需重申请key） | 欧美专利权威 |
| D4 宏观经济聚合 | **dbnomics**（87机构·9.5亿时序） | 单点覆盖FRED/WB/OECD/IMF/Eurostat |
| D4 美国经济 | fredapi（FRED 80万时序） | 美联储圣路易斯经济数据库 |
| D4 国际发展 | wbgapi（WB 16000指标） | 世界银行官方 |
| D5 PDF/全格式解析 | **Docling**（MIT） + MarkItDown（MIT） | 主力+轻量双引擎 |
| D5 网页正文 | **trafilatura** | 毫秒级HTML去噪抽取 |
| D5 RAG预处理 | **unstructured** | ETL标准管线 |
| D5 学术PDF | **GROBID**（自托管Docker） | 参考文献+结构化提取 |

---

## 四、待授权清单

> 按R1付费优先级分级。括号内为建议申请时序。

### R1付费待授权

| 源 | 子场景 | 费用 | 优先级 | 申请条件 |
|----|--------|------|--------|---------|
| Tavily | D1 | 免费1000/月 → $30/月Researcher | **P1（M1优先）** | 注册即可 |
| Exa | D1 | 免费1000/月 → $49/月 | P1（与Tavily二选一） | 注册即可 |
| Snyk | D2 | 公开repo免费 · Team $25/开发者/月 | P1（OSV缺口时） | OSV未覆盖的专有漏洞时 |
| Semantic Scholar | D3 | 免费key 1RPS | **P0（立即申请·免费）** | 邮件申请 https://api.semanticscholar.org |
| Lens.org | D3 | 非商业学术token免费 · 商业ITK付费 | **P1（申请非商业token）** | 机构邮箱申请 |
| WIPO PATENTSCOPE | D3 | 600CHF/年 | P2（Lens覆盖时暂缓） | 官方授权申请 |
| Alpha Vantage | D4 | 免费25/天 → $50/月 | P1（dbnomics缺口时） | 注册即可 |
| Quandl/Nasdaq Data Link | D4 | 按订阅 | P2（与FRED/WB高度重叠） | 延迟 |
| LlamaParse | D5 | 免费1万credits/月 | P1（免费层先验证） | 注册即可 |
| Mistral OCR 3 | D5 | $1-2/千页 | P1（手写/低质量扫描场景） | API key申请 |
| Azure Document Intelligence | D5 | F0免费500页/月 | P2 | Azure账号 |
| AWS Textract | D5 | $1.5/千页 | P2 | AWS账号 |

### 免费key申请（无R1·建议M0期间同步申请）

| 源 | 子场景 | 申请入口 | 说明 |
|----|--------|---------|------|
| Semantic Scholar API key | D3 | https://api.semanticscholar.org | 免费·提升限速到1RPS |
| USPTO ODP账户 | D3 | https://data.uspto.gov | **2026-06-18截止·旧key已失效·须重申请** |
| Libraries.io API key | D2 | https://libraries.io/api | 免费key·60req/min |
| FRED API key | D4 | https://fred.stlouisfed.org/docs/api/api_key.html | 免费·必须有才能用fredapi |
| data.gov API key | D4 | https://api.data.gov/signup | 免费key·访问联邦数据集 |

### 法务审查待确认

| 源 | 子场景 | License | 风险点 | 建议 |
|----|--------|---------|--------|------|
| PyMuPDF / pymupdf4llm | D5 | AGPL-3.0 | AGPL传染性·商业产品需Artifex商业许可 | 法务确认AGPL影响范围后决定 |
| MinerU | D5 | Apache + 附加商业条款 | 超过MAU/营收阈值需商业许可 | 法务确认具体阈值·短期暂不用 |
| dbnomics nbsc库（中国NBS） | D4 | 不明 | 数据来源合规性待确认 | 法务确认后才接 |

---

## 五、同源去重提示

D域多个子场景存在数据重叠，接入时需注意去重逻辑，避免同一数据被统计多次：

### D2 技术开源生态去重

- **OSV.dev已聚合**：NVD（CVE/CVSS）+ GitHub Advisory Database（GHSA）+ PyPI Safety advisory + npm advisory + RubyGems + Debian + Alpine等40+生态
- 建议：以OSV.dev为主路，只在需要获取CVSS v3.1精确评分细节（NVD独有字段）时才直连NVD
- GH Archive与GitHub API有重叠：GH Archive适合批量历史分析，GitHub API适合实时查询，按需选择

### D3 学术专利去重

- **DOI为主键**：OpenAlex、Crossref、SemanticScholar均使用DOI作为论文唯一标识，三者数据按DOI去重
- **arXiv ID↔DOI映射**：同一论文在arXiv有arXivID（如2302.13971），发表后有DOI，需建映射表防止重复计入
- **Lens.org已聚合**：USPTO（美国专利）+ EPO（欧洲专利）+ WIPO PATENTSCOPE国际申请，接入Lens后三者可不直连（除非需USPTO/EPO原始文本）
- OpenAlex同时含arXiv预印本和正式发表版，需用DOI/arXiv ID去重

### D4 政策宏观经济去重

- **dbnomics已聚合**：FRED、World Bank、OECD、IMF、Eurostat等87个机构，通过统一API访问时避免重复抓取同一指标
- 建议：dbnomics作为主路；仅在dbnomics延迟>24h或字段缺失时才直连原始官方API（FRED等）

---

## 六、覆盖缺口与对策

### 已知缺口清单

| 缺口 | 子场景 | 严重程度 | 当前状态 | 对策 |
|------|--------|---------|---------|------|
| **CNIPA中国专利无官方API** | D3 | 🔴 高（中文技术情报盲区） | 无零成本方案 · PatSnap/智慧芽均企业付费 | 短期：经Lens.org获取在华申请的PCT国际专利 · 长期：评估PatSnap/智慧芽ROI |
| **中国NBS官方无开放API** | D4 | 🟡 中（宏观经济中国数据） | dbnomics nbsc库可部分覆盖·合规风险待确认 | 待法务确认dbnomics nbsc合规性后接入 |
| **新兴市场数据稀薄** | D4 | 🟡 中（俄/印/东南亚） | 无官方API · dbnomics部分覆盖 | dbnomics聚合层已覆盖部分 · 接受缺失 |
| **中文PDF OCR精度** | D5 | 🟡 中（中文文档解析） | Docling中文精度待实测 | 待实测后决定：备选PaddleOCR（Apache 2.0·百度开源·中文OCR专精） |
| **marker-pdf弃用** | D5 | 🟢 低（已有替代） | 已弃 · Docling替代 | 无需操作 |
| **Sourcegraph免费层弃用** | D2 | 🟢 低（已有替代） | 已弃 · GitHub Code Search API替代 | 无需操作 |
| **实时政策文本解析** | D4 | 🟡 中（央行/政府PDF） | 无专用管线 | 配合D5 Docling+trafilatura建立政策文本解析子流程 |

### 重点缺口说明

**CNIPA中国专利**：中国国家知识产权局（CNIPA）至今无官方开放API，是D域唯一无零成本解决方案的权威来源。短期绕道方案：
1. 通过Lens.org获取在中国申请的PCT国际专利（覆盖~60%但有延迟）
2. Google Patents Public Data（BigQuery公开集）含部分中国专利
3. 长期评估：PatSnap学术版或专利5（国内替代），按ROI决定

**中文PDF OCR**：Docling在英文PDF的版面分析和公式识别方面SOTA，但中文复杂排版（表格嵌套/竖排/繁体）精度需实测。备选方案PaddleOCR（Apache 2.0，百度开源）专为中文设计，可作为中文文档处理的兜底补充。

---

## 七、对接批次建议

D域是**M0零成本批次的主力**，可立即接入的免费源覆盖率在五大赛道中最高。

### M0批次（立即可接·无需授权）

**优先接入顺序**（按价值密度和接入难度综合排序）：

| 批次 | 源 | 预计接入工时 | 价值 |
|------|----|-----------|----|
| M0-D1 | SearXNG（已自托管）+ GDELT + Wikimedia/Wikidata | 0.5天（已有自托管底座） | 通用检索骨架 |
| M0-D2 | OSV.dev + deps.dev + Libraries.io | 1天 | 技术安全完整覆盖 |
| M0-D4 | dbnomics + fredapi + wbgapi | 1天 | 宏观经济单点聚合 |
| M0-D5 | Docling + trafilatura + GROBID（Docker） | 1.5天 | 文档解析完整管线 |
| M0-D3 | OpenAlex + Crossref + arXiv | 1天 | 学术覆盖骨架 |
| M0-D2补 | GH Archive + GitHub API | 0.5天（GitHub API已有） | 趋势活跃度 |

> M0-D4中dbnomics聚合了87个机构，单个接入点覆盖宏观经济全域，建议优先级仅次于SearXNG。

### M1批次（需key申请·部分R1）

| 批次 | 源 | 前置条件 |
|------|----|----|
| M1-D3 | Semantic Scholar（免费key）+ PubMed Entrez | 申请API key（免费） |
| M1-D3 | USPTO ODP（需重申请）+ EPO OPS | 重申请账户（2026-06-18前） |
| M1-D3 | Lens.org（非商业token） | 申请学术token |
| M1-D5 | LlamaParse（免费tier验证） | 注册即可 |
| M1-D1 | Tavily或Exa（二选一） | R1授权 |

### M2批次（付费·按需评估ROI）

- Mistral OCR 3（手写扫描场景）
- PyMuPDF商业授权（法务确认后）
- PatSnap/智慧芽中国专利（ROI评估后）

---

> 文档版本：v1.0 · 2026-06-10
> 作者：probe技术文档撰写员
> 关联文档：[datasource-research-methodology-v1.0.md](datasource-research-methodology-v1.0.md) · [probe-github-datasource-feasibility-v1.md](probe-github-datasource-feasibility-v1.md) · [datasource-research-onboarding-batch-plan-v1.0.md](datasource-research-onboarding-batch-plan-v1.0.md)

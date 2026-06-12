# 元探（MetaProbe）· 构建初心总纲 v1.0

> 数值真源见 records/probe-ssot-master-reconciliation-v1.0.md §1·与本文冲突以该表为准
> 性质：据现有素材综合的立项报告 v1.0（非逐字对话沉淀）
> 日期：2026-06-08
> 命名：「元探」（MetaProbe）——工作名已收敛·正式名待**商业命名轨**签发（非元典录·见 [SSOT §1](../records/probe-ssot-master-reconciliation-v1.0.md)）
> 子域：probe.metafoclaw.com
> 来源素材：
> - [probe-intelligence-engine-design-v1.md](../3-build/probe-intelligence-engine-design-v1.md)（四层架构/双审 8 闸验证层/17 域数据源仓库）
> - [probe-master-solution-v2.md](../probe-master-solution-v2.md)（总方案入口·两支柱·执行规划）
> - [probe-github-datasource-feasibility-v1.md](../4-research/probe-github-datasource-feasibility-v1.md)（6路扇出调研·合规缺口·接入优先级）
> - [probe-alignment-topology-prelaunch-v1.md](../records/probe-alignment-topology-prelaunch-v1.md)（对齐核查·拓扑图·上线前章节）
> - [subproject-decisions-2026-06-03.md](../../../metafoclaw-git/docs/decisions/subproject-decisions-2026-06-03.md)（D2 不爬取合规裁定）

---

## ⚠️ 范围边界声明（防做错 · 必读）

- **本文件 = 元探情报引擎的立项初心，是「引擎矩阵」中元探这条线的地基文件，不是整个引擎矩阵的总构思。**
- 元探是矩阵的**情报底座**——给 MetaAsk 澄清意图后路由过来的任务提供「多源采集 → 验证 → 整合」服务，给 MetaDesign/MetaCut/MetaLearn 喂「经过验证的真材料」。
- **对外一期声明 `["自媒体","金融"]`**（2026-06-08 元东方裁定金融正式纳入对外一期）。其余业务域以场景模板形式在内部开发，待质量门通过后再逐批对外声明——不过早宣布超出兑现能力的范围。
  > 诚实标注：金融能力 S1 落地中，对外声明已纳入金融、能力随 S1 逐步补齐（非已交付）。
- **合规红线 = 不自己爬数据（D2·元东方裁定，2026-06-08 收敛）**：元探**自身**不实施任何爬取（自写爬虫 / 抓取平台数据 / 模拟登录 / 抓包 / 逆向签名）。**可用任何第三方付费 / 免费 API、或能全自动化获取的数据提供方式**——第三方如何取数（含其内部访问机制）由其自行担责，元探只作调用方；底线是数据**准确、真实**（验证层双审 8 闸把关），供应商优先正规主体、避开已被司法判违法者（如蝉妈妈）。

---

## 一句话初心（地基）

> **任何人，丢进一句话或任意素材（链接、图片、视频、文档、实体名字），元探把它变成「多源采集 → 专业验证 → 可溯源、可证伪的情报成品」——别人给观点，元探给带可信度标签、可回放、扛得住证伪的结论。**

魔法点：价值不在 AI 分析（大路货），在三件通用大模型给不了的事：
1. **数据源护城河**——合法、专业、多为付费的真实数据端口，17 个信息域（D1-D17）统一适配；
2. **抗污染验证**——每条数据、每个结论多源交叉、溯源、对抗证伪，双审 8 闸（闸0 过程留痕 + 闸1-7 结果审核）；
3. **解耦铁律**——信息源可任意热插拔，换源只改数据质量，不动处理流程。

> 来源：[design-v1 §0](../3-build/probe-intelligence-engine-design-v1.md)，[master-solution-v2 §0/§1](../probe-master-solution-v2.md)

---

## 服务对象

| 画像 | 要的东西 | 元探立场 |
|------|---------|---------|
| **C 端个人**（创作者/消费者/求职） | 快速拍板结论、操作风险排雷 | 自媒体垂类首发·免费评级拉新 |
| **小 B**（MCN/电商/独立开发/中小企业） | 竞品情报、合规确认、选题雷达 | 月度订阅 + 按次深探 |
| **中大 B**（投资/品牌/咨询/法务风控） | 尽调报告、企业背调、持续监测 | 订阅 + 企业定制（高客单，波次接入） |
| **内部引擎**（MetaDesign/MetaCut/MetaLearn） | 经验证的情报成材 | 内部结算·情报底座角色 |

三类外部用户的需求方向各异，**第一锚点是自媒体创作者**——v2 已深耕的锚点垂类 A，先把这一个场景做到「断层式好」，再横向铺展其他业务域。

> 来源：[design-v1 §5](../3-build/probe-intelligence-engine-design-v1.md)

---

## 核心机制

### 机制一：数据源仓库（支柱①）

仓库由三件东西构成：
1. **多域目录/台账（catalog）**：17 个信息域（D1 真相核查/D2 内容结构拆解/D3 视觉多模态/D4 出处溯源/D5 竞品横评/D6 发布者画像/D7 二创路径/D8 法规合规/D9 地域受众/D10 学术科研/D11 企业财务/D12 开源技术/D13 金融行情/D14 宏观政策，对齐 ledger.yaml v5 真源），每个源携带统一元数据 schema（域/接入方式/权威分/合规/成本/标准19）；
   （D15 促销/D16 任务/D17 AI优惠 见 ledger.yaml v5·真源）
2. **准入门（gate）**：标准19核验 + R1 付费授权 + 合规判定，`status=active` 才放行；
3. **适配器（adapter）**：每个源实现 `DataSourceAdapter` 统一契约，热插拔，换源对流程零影响。

五类接入方式（从高到低优先）：
- **L** 开源库本地嵌入（Docling/whisperX/imagehash）——零风险零成本；
- **S** 可自托管开源服务（SearXNG/RSSHub/SpiderFoot）——数据自控；
- **W** 官方开源 SDK（PyGithub/arXiv.py/vt-py）——官方跟进，配额受控；
- **O** 官方开放 API（OpenCorporates/YouTube Data）——权威，需 key/付费；
- **D** 开源数据集批量（OpenSanctions/GDELT）——量大历史全，实时性稍弱。

**禁止（铁律②·D2 裁定）= 元探自己爬**：probe 自身实施的爬取行为一律禁止——自写爬虫、抓取平台数据、模拟登录、抓包、逆向签名。**可用**：任何第三方付费/免费 API、或能全自动化获取的数据提供方式（第三方对其取数方式自行担责，元探只作调用方），且数据须经验证层确保**准确、真实**。已被司法判违法的供应商（蝉妈妈）弃用。

> 来源：[design-v1 §2](../3-build/probe-intelligence-engine-design-v1.md)，[feasibility-v1 §1-5](../4-research/probe-github-datasource-feasibility-v1.md)，[D2裁定](../../../metafoclaw-git/docs/decisions/subproject-decisions-2026-06-03.md)

---

### 机制二：抗污染验证层 双审 8 闸（闸0 过程留痕 + 闸1-7 结果审核）（支柱②）

验证层独立于数据源，**源无关**——换源不影响这条链：

| 闸 | 名称 | 做什么 |
|----|------|--------|
| 闸0 | 过程留痕 | 全程 trace 留痕（OpenLLMetry+Langfuse）+ run 快照 + 哈希链审计；其它闸的地基 |
| ① | 溯源 provenance | 每条数据带 {源/URL/时间戳/权威分}；无源不立论 |
| ② | 多源交叉印证 | 一个论断需 ≥2 个独立源印证；单源 → 标「未证实」 |
| ③ | 独立性/抗循环 | 检测 N 源同一出处（转载链）→ 坍缩为 1；抗 AIGC |
| ④ | 时效×权威加权 | 按 freshness × authority_score 加权，旧/低权威降权 |
| ⑤ | 矛盾检测 | 冲突论断显式并列，不静默二选一 |
| ⑥ | 对抗证伪 | opus×3 多视角生成 + ×2 证伪（默认 refuted=true），多数票才采信 |
| ⑦ | 置信标注 | 每个结论附「置信度 + 证据链 + 反方观点」；禁裸断言 |

审核分**极速版 / 深度分析版双形态 · 智能界定**（2026-06-10 收敛 · 见 [speed-depth-tiering-v1.0](../3-build/probe-speed-depth-tiering-v1.0.md)）：系统智能界定每个任务走哪版（默认极速兜底 + 确定性自评 + 按需升级），每版各自精品——⚡极速版（闸0/1/2/7[+3/5]·快·留痕+溯源+交叉·标注未全验）/ 🔬深度分析版（闸0-7全开+对抗证伪·可溯源可证伪）。钱买的是深度分析版（8闸全验+对抗证伪+多源专业数据），极速版在其定位也是认真精品；付费差异另在次数/形态/便捷/特殊服务。**完整设计见 [audit-system-v1](../3-build/probe-audit-system-v1.md)。**

> 来源：[design-v1 §3](../3-build/probe-intelligence-engine-design-v1.md)，[alignment-prelaunch §3.4](../records/probe-alignment-topology-prelaunch-v1.md)

---

### 机制三：四层引擎架构（解耦·源无关）

```
素材输入：链接 / 图片 / 视频 / 文档 / 文字 / 名字(实体)
   │
   ▼  MetaAsk 意图澄清 → 任务类型 + 输出规格 + 深度档 + 交付形态
   │
┌──┴──────────────── 元探（MetaProbe）───────────────────┐
│ L4 整合层  拆解 → 重组 → 归纳（七段报告/conclusion_block） │
│ L3 验证层  双审 8 闸 抗污染 / 对抗证伪（源无关）          │
│ L2 采集层  素材解析 + 数据源路由 + 多源并发扇出             │
│ L1 接入层  适配器（registry 驱动 · 热插拔 · 标准19 门）     │
│ ─── 数据源仓库 catalog（17 域 · 元数据统一 schema）───── │
└──┬──────────────────────────────────────────────────┘
   ▼  成材（引用 + 置信度 + 证据链 + aigc_flag）
 → MetaDesign 排版 / MetaCut 视频 / MetaLearn 飞轮 / GEO 分发
```

**解耦铁律**：L2/L3/L4 全部源无关。换掉一个 L1 适配器，只改「数据质量 → 分析结果」，对处理流程零影响。

> 来源：[design-v1 §4](../3-build/probe-intelligence-engine-design-v1.md)，[alignment-prelaunch §3.2](../records/probe-alignment-topology-prelaunch-v1.md)

---

### 机制四：交付形态（同一情报内核·多形态渲染）

同一份验证后情报内核（L4 产物）可渲染成不同形态——形态由 MetaAsk 按用户喜好 + token 预算选，内核不重做：

| 形态 | 成本 | 适用 |
|------|------|------|
| 文字 / Markdown | 最低 | 默认基础形态 |
| 信息图 / 图表 | 中 | 数据可视化 |
| HTML 交互报告 | 中高 | 专业交付（→ MetaDesign）|
| PPT / 演示稿 | 中高 | 汇报路演（→ MetaDesign）|
| 视频 / 口播讲解 | 最高 | 自媒体分发（→ MetaCut）|

**铁律**：情报内核只算一次，形态升级 = 多花 token，不多花数据成本。

> 来源：[design-v1 §5.5](../3-build/probe-intelligence-engine-design-v1.md)

---

## 立项依据

### 为什么做

1. **AI 分析是大路货，但「可溯源可证伪的结论」不是。** 通用大模型会被污染，不会专门为用户整合多域专业付费源 + 做抗污染验证——整合 + 验证 = 护城河，别人懒得做这脏活。
2. **数据源整合壁垒已存在雏形。** 现有 `app/datasources/`（adapter/registry/ledger/标准19）+ 三层深度线 + v2 七段报告已是可用基座（P0 已有），不是从零开始。
3. **v2 锚点垂类（自媒体）已验证需求。** probe v2「链接情报决策室」已跑通自媒体场景，升级为通用情报引擎是在已验证基础上横向扩展，而非推翻重来。
4. **引擎矩阵需要情报底座。** MetaAsk 问准意图后，MetaDesign/MetaCut 需要「经过验证的真材料」才能出专业成品——元探是矩阵不可或缺的前置层。

> 来源：[design-v1 §1](../3-build/probe-intelligence-engine-design-v1.md)，[master-solution-v2 §1](../probe-master-solution-v2.md)

### 护城河本质

不是「更多爬虫」（法律雷区），而是：
- **隔离风险**：第三方持牌担责，元探不踩反爬铁律、不背技术责任；
- **整合壁垒**：17 信息域、几十个第三方 API 统一适配 + 交叉验证，是长期脏活；
- **不可替代**：大公司通用模型不会专门为单个用户整合多域专业付费源 + 做抗污染验证。

---

## 命名（元典录待签发）

- **中文名**：元探（工作名）——候选原有「元察·谛 / 元探·真」，当前统一用「元探」，**最终命名待商业命名轨正式签发**；
- **英文**：MetaProbe（已确认，对外一致使用）；
- **子域**：probe.metafoclaw.com（已在役）；
- **引擎矩阵代号**：情报引擎（数据/情报底座）；
- **进度**：P2（按 master-plan 引擎标准进度 P0-P5）。

> ⚠️ 待确认：元典录签发中文名及字——在此之前，文案、界面、对外材料一律用「元探」作为临时标准名。

---

## 第一刀：锚点垂类先做到「断层式好」

- **第一刀 = 自媒体垂类 A，做到「断层式好」**，再横向铺 B/C/D/E。
- 三层深度线（public/preview/paid）在锚点垂类先跑通，作为其他垂类的模板；
- **M1 公开档（无成本·无风险·约 1 周）**：粘贴链接 → 评级 + 结构 + 公开结论；
- **M2 付费档（约 2-3 周）**：须过 C2 质量门实评（完成度≥80%/准确性≥20pct提升/省力≥3×/盲评≥70%）+ 成品人工复核≥80%（**不可自过**，Manus 教训）；
- **M3 大厅上架**：待母体 HttpToolClient + identity/verify + registry 三维标签，不阻塞 M1/M2。

> 三层深度线切割是硬约束：public 禁显结构/二创/竞品；preview 仅 1 条二创简版；paid 才给完整七段+竞品横评。（来源：[alignment-prelaunch §1.2 C-2](../records/probe-alignment-topology-prelaunch-v1.md)）

---

## 落地路线（MVP → 护城河）

| 阶段 | 内容 | R1 成本 |
|------|------|--------|
| **Wave 1（零成本）** | ledger 升多域 catalog + 首批免费源适配器（Wikimedia/GitHub/GDELT/Docling/SearXNG）+ 闸0 过程留痕 | 0 |
| **Wave 2（零成本）** | 自托管扩源（RSSHub/SpiderFoot/Yente）+ 免费层 API（VirusTotal/YouTube Data/OpenCorporates）+ 审核标准 + 交付层骨架 | 0 |
| **Wave 3（零成本）** | 验证层双审 8 闸 engine（证伪 + 场景路由 27 模板 + 质量门）| 0 |
| **Wave 4（逐个 R1）** | 付费源按 ROI 顺序授权（DataForSEO → 天眼查 → Keepa → TinEye → Crunchbase·序以 master-solution §4 为准·金融内部例外见 finance-track-f）| 付费 |

> Wave 1-3 全零 R1 成本，可直接开工。
> 来源：[master-solution-v2 §4](../probe-master-solution-v2.md)，[feasibility-v1 §6](../4-research/probe-github-datasource-feasibility-v1.md)

---

## 服务化定位：双边服务体（三段开放 + 速览/深探）

> 反向补入 2026-06-08：本引擎不止 C 端「查询→结果」，同时是 B 端服务体。完整可落地 manifest / 商业模式见 `运营报告/engine-platform/landable/metaprobe.md`，框架见母规范 engine-as-service-bside-api-design-v1.0（元探是三段聚合的最典型样板）。

### 三段开放（入口聚合 / 处理飞轮 / 出口资产）

- **入口段·聚合什么**：40+ 免费合规源统一适配（SearXNG/GDELT/Wikidata/GitHub-API/arXiv/OpenCorporates/OSV/WebArchive/VirusTotal 等），覆盖 17 个信息域；B 端对接「一个口」即继承全部资源端查询能力 + 已清洗 + 已统一计量，比自建对接 N 套 API 省去全部脏活。
- **处理段·能力 + 飞轮**：四层引擎（L1 适配器/L2 采集/L3 双审 8 闸验证/L4 整合）独立于数据源；每次调用回流两条飞轮数据——源命中率更新「哪个源对哪类情报准」的效用模型，8 闸结论持续累积污染模式库，越多调用→闸门越准→结论越可信。
- **出口段·结果资产**：结论以 `result_id` 唯一可寻址，支持 json/html/markdown/ppt_outline/video_brief 多形态；`conclusion_block`（headline/key_points[]/data_table/brand_anchor）可直接被 MetaFlow 下游或 B 端产品程序化拉取、嵌入、组合。

### 价值四层

- **商业**：按 `source_queries` 额度池预购，把 C 端一次性情报查询翻转成 B 端可订阅、按量叠加的 MRR 曲线——同一套引擎同时开两条收入。
- **聚合**：一个端口替 B 客户做掉对接 17 信息域×40+ 资源端、N 套鉴权、N 套限流、N 套质量清洗的全部脏活；资源端越多这一个口越值钱。
- **飞轮**：B 端调用量本身是引擎的免费燃料——越多调用→越懂哪个源准/哪里易被污染→闸门越精→结论越可信→B 端越愿意调用。
- **战略**：元探是开放引擎矩阵的情报底座——向上给元询喂已验证素材、给元绘/元剪提供有来源的内容料，向下经元枢组合成「情报→排版→成片」的成品级组合 API。

### 商业模式 × 推广咬合（★）

- **目标 B 客户**：自媒体 MCN/工作室、电商品牌竞调团队、投融资/尽调机构、SaaS/AI 产品开发者、舆情监控/品牌安全团队。
- **primary meter**：`source_queries`（资源端查询额度池）——深探任务（多源全 8 闸）比速览任务消耗更多 sq，定价天然区分付费深度，比纯按调用次数计费更公平，且直接对应引擎真实成本曲线。
- **★推广即变现咬合点**：元探最锋利的咬合在于——`catalog_query` 公开接口 + `probe.metafoclaw.com/sources` 数据源目录页，让搜索引擎可索引 17 域×40+ 源的真实清单（长尾 SEO/开发者获客零增量成本）；每份 public 档报告和 B 端嵌入的 `conclusion_block` 自带 `brand_anchor` 归因，B 端用量越大元探曝光越多，推广费由 B 端承担——这是 PLG 病毒式获客的技术落点，而非广告语。

### 速览 / 深探（统一对话）

- **速览 L0 信号**：`depth=public`·单源/P0 底座少数源·闸1+闸2+闸7 轻验·≤10s 同步返·输出「评级 + 一句话结论 + Admiralty 源可靠性标签 + ⚠️单源警示」·标注「速览·未全验」；即使速览也比普通 AI 搜索多出 Admiralty 标注和单源警示，这是速览档的差异化，不只是「快」。
- **深探全验证**：`depth=paid`·多源扇出·双审 8 闸全开（闸0 过程留痕哈希链 + 闸6 对抗证伪 opus×3 生成 + opus×2 默认 refuted 证伪 + 多数票≥3/5 采信）·async P99≤300s·输出完整七段报告 + 强制元数据标签·task_done 事件推送；「别人给观点，元探给扛得住证伪的情报定论」。

> ⚠️ 计费 meter / 定价待元东方确认（R1）；对外发布走 R-CL。来源：`运营报告/engine-platform/landable/metaprobe.md`。

---

## ⚠️ 待元东方确认项

| # | 事项 | 阻塞什么 | 状态（2026-06-06 逐个过审）|
|---|------|---------|---------|
| **W1** | **商业命名轨正式签发「元探」中文名**（候选：元察·谛/元探·真）| 不阻塞开发；阻塞对外品牌物料 | 🔴 **待签发**——工作名「元探」已全局统一使用，待商业命名轨（MetaX+中文俗名双名并存·naming.md A轨）正式签发 |
| **W2** | **Wave 1-3 零成本部分是否即可开工** | 阻塞 Sprint 启动 | ✅ **已确认+已完成**——Wave1+2 建成（数据源/审核/交付三层·selftest 11/11），Wave3 待开 |
| **W3** | **Wave 4 付费源授权顺序确认**：DataForSEO → 天眼查 → Keepa → TinEye → Crunchbase（通用序·真源 master-solution §4·金融例外 finance-track-f）| 阻塞变现阶段 | 🟡 **建议接受此 ROI 顺序**——待真接付费源时逐个走 R1，**不阻塞当前** |
| **W4** | **manifest.industry 对外一期 `["自媒体","金融"]`**（2026-06-08 元东方裁定金融正式纳入）| 阻塞 manifest schema | ✅ **已确认（含金融）**——schema enum 须含「金融」；金融能力 S1 落地中、声明已纳入、能力随 S1 补齐；selftest 须同步更新断言 |
| **W5** | **master-plan 是否补元探独立 Part** | 阻塞 MetaFlow 编排接入 | 🟡 **建议暂缓**——已在台账 §10.2.1 + 双视角调和登记，待 MetaFlow 真编排时再补 capability 声明，**不阻塞** |
| **W6** | **天眼查接入须公司资质（R4 门）**——绵阳零元电子商务主体资质是否满足天眼查企业 API 申请条件？| 阻塞 C 域尽调场景 | 🔴 **待元东方裁定**（R4·涉公司资质，非我可代决）|
| **W7** | **DeepfakeBench 图像 AIGC 检测（CC BY-NC 非商用）** | 阻塞 E 域图像溯源变现 | 🟡 **建议短期商业 API/原型·长期找 Apache 模型**——待 E 域变现再定，**不阻塞** |
| **W8** | **服务化计费 meter（source_queries 额度池）定价方案确认**（Free 200sq/月·Light/Pro/Business 阶梯·Pay-as-you-go 单价）| 阻塞 B 端商业化上线 | 🔴 **待元东方 R1 密码确认**——当前仅设计草案，不触发真扣费 |

> **逐个过审小结（2026-06-06）**：W2/W4 ✅ 已落实；W3/W5/W7 🟡 已给建议、不阻塞当前；**仅 W1（命名签发）、W6（天眼查公司资质 R4）、W8（计费定价 R1）真正需元东方拍板**。

---

> v1.0 定稿 2026-06-08。本文件是初心地基，功能排期/技术选型不得反向覆盖它；若实现与初心冲突，改实现，不改初心。
> 元东方确认任何待确认项后，直接在对应 ⚠️ 处补注「已确认：…」并更新版本号。

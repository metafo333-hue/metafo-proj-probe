# probe 技术底座与功能模块 · GitHub 成熟方案调研作战计划 v1.0

> 日期：2026-06-11 · 性质：**可执行调研方案**（进入「系统编排」实施前的技术选型作战图）
> 轴向声明：与 [feasibility-v1](probe-github-datasource-feasibility-v1.md) **正交不重叠**——那份是**数据源轴**（用什么料），本份是**技术实现轴**（用什么件）。两轴各自真源、互相引用。
> 事实仲裁：数值/术语以 [records/probe-ssot-master-reconciliation-v1.0.md](../records/probe-ssot-master-reconciliation-v1.0.md) 为准（域17/赛道9/闸8/场景27）。

---

## 〇、方案一句话

**【是什么】** 把 probe 全部待建功能按 13 个模块对表，先裁**底座姿态** → 逐模块在 GitHub 找**成熟方案移植** → 按统一 **tech-gate 标准**组合落位 → 调研中顺带**补盲发现** → 全程安全+真实性纪律。
**【铁律】** 成熟移植 > 自研；自研只留护城河三件（可信度内核 / 数据源治理 / 交付 Core IR）。凡 GitHub 有成熟件可移植的，自研即违纪；凡涉"敢出结论"的可信度判定，移植即妥协。

---

## 一、愿景定位升级提炼（v2.1 草案 · 待元东方拍板后回填真源）

> 现行定位（master-solution §0）：probe 卖「带可信度标签、可回放、扛得住证伪的结论」。本节升级**不改卖什么，改怎么造**——把工程姿态升进愿景层。

### 升级三条

**① 工程姿态入宪 ——「轮子取天下，天平自己造」**
底座与四肢全部用业界成熟件（采集接入/内容抽取/调度外环/渲染交付/评测观测），自锻只三件不可替代物：

| 自锻件 | 为什么不能移植 |
|--------|--------------|
| **可信度内核**：双审 8 闸 + 对抗证伪 + 真值发现 | 这是 probe 的"天平"——全部价值所在，移植 = 把命门交给别人的标尺 |
| **数据源治理**：ledger/SCT/赛道注册表 + gate19 | 17 域 9 赛道的源资产与合规判定是积累型护城河，无现成对应物 |
| **交付 Core IR**：一份结论 → 多形态一致渲染 | 可信度标签贯穿交付的一致性契约，与 8 闸标签体系强耦合 |

**② 定位升维 —— 从「情报引擎」到「可信度基础设施」**
采集和编排谁都能搭（开源整机已成熟），probe 的不可替代 = **任何信息流过它，出来都带可信度标签、可回放、扛证伪**。底座可换、外件可换，天平不换。这把竞争从"功能比拼"（必输给大厂）切到"信任积累"（时间复利）。

**③ 演进飞轮显式化 —— 可替换外环 + 不动内核**
移植件构成**可替换外环**：MAPE-K 监测之下，任何外件按指标门换件升级，换件不动契约（L1 四暗号 + SCT 注册）。自锻件构成**不动内核**。"加能力 = 换件/加件，不重构"——这正是赛道注册表"加赛道=改数据不改架构"在技术栈上的同构延伸。

### 回填路径（拍板后执行 · 保 SSOT 不漂移）
master-solution §0/§1（定位真源·加"工程姿态"一行）→ founding-charter 补"工程姿态"节 → reconciliation §1 登记"工程姿态=借力锻芯"为事实键。**拍板前本节仅为草案，各文档不得先行复制。**

---

## 二、调研总原则（六条 · 全程生效）

| # | 原则 | 内容 |
|---|------|------|
| 1 | **移植三档判定** | 每模块结论必须落档：**A 引依赖**（pip/容器原装直用）> **B vendor 移植**（fork 固化进仓改造）> **C 借鉴自研**（读架构抄思想）。优先级 A>B>C，降档必须给"为什么 A/B 不行"的理由 |
| 2 | **红线适配先于选型** | 任何采集类候选先过「**不自己爬**」红线（真源 [feasibility §5](probe-github-datasource-feasibility-v1.md)）+ PIPL（真源 privacy）。爬虫框架类（Firecrawl/Crawlee 等）**默认 ❌ 不得做采集用途**，只可借鉴其抽取/调度思想（C 档）；RSSHub 类聚合按**路由逐条**核合规（官方 API 路由 ✅ / 逆向抓取路由 ❌） |
| 3 | **已决不重开** | 冻结项：编排七决策 D1-D7（Scatter-Gather asyncio 内核·真值发现·Redis token-bucket·S2 Hatchet 候选）、纯 Claude 多代理编排、PG+Redis 数据脊柱、FastAPI 骨架+四暗号契约。调研若发现颠覆性更优 → 走**变更指控**流程：证据卡 + 对抗证伪 + 元东方拍板，禁静默重开 |
| 4 | **真实性 R0.8** | 禁凭印象/训练记忆断言任何 repo 指标——本方案候选**只列名不列数**，stars/commit/license 全部执行时现场实测采集；每源卡 7 必采字段（§七）；双源核验 + 每批 1 路证伪 |
| 5 | **安全前置** | license 闸（AGPL 须隔离评估）→ pip-audit/CVE → 供应链（官方源/typosquat/SBOM）→ **沙箱实测**（ufo 开发机或本机 venv，禁 probe-a 生产首装） |
| 6 | **整体优先可重排** | 为整体架构一致，允许对成熟方案**裁剪重排**（只取其模块）；也允许微调我方编排去就成熟件（高 blast 时走变更流程上桌）。一句话：方案适配架构优先，架构迁就方案要拍板 |

---

## 三、阶段 R1 · 底座引擎选型（先裁姿态，再选名字）

### 3.1 三种底座姿态（互斥 · R1 的第一裁定）

| 姿态 | 含义 | 代价 | 预判 |
|------|------|------|------|
| **S-整机** | 拿一个 deep-research 开源整机当 probe 骨架，我方功能注入它 | 弃现有 app/ 骨架 + 四暗号契约重对 + 8 闸嵌入别人的管线 | 仅当某整机成熟度碾压且可深改 |
| **S-框架** | 引一个 pipeline/agent 框架库做 L2-L4 管线载体，骨架仍我方 | 框架锁定与升级风险 | 重点评估对象 |
| **S-借鉴** | 保持自有 FastAPI+asyncio 骨架，逐模块移植组件 + 抄整机架构思想 | 集成胶水自担 | **当前默认假设**（已有 app/ 骨架+契约+8闸雏形+编排已决） |

### 3.2 底座候选清单（指标全部 ⚠️ 待实测 · 只列名与调研问题）

| 候选 | 类型 | 看点 | 关键调研问题 |
|------|------|------|------------|
| GPT-Researcher | 整机·多代理研究器 | plan→并发检索→引文→报告全流程，最接近 probe 主链 | 检索编排与引文管理**可否拆件**；与 8 闸的接缝在哪 |
| STORM（stanford-oval） | 整机·报告生成 | 视角引导提问 + 大纲驱动写作 | 大纲机制 → 七段报告骨架的映射价值 |
| open_deep_research（LangChain 系 / HF smolagents 系） | 整机/框架 | supervisor-researcher 图式编排 | LangGraph 依赖代价；图结构喂 G1 DAG schema |
| Tongyi DeepResearch（阿里） | 整机·模型+框架 | 中文生态 ReAct rollout | 与"纯 Claude 编排"冻结决策的冲突面有多大 |
| Onyx（前 Danswer） | 整机·企业搜索 RAG | **几十个连接器资产** | 连接器层**单拆**喂 L1 接入的可行性（最大看点） |
| Perplexica | 整机·SearXNG 前端 | 与我方 SearXNG 底座同源 | focus-mode 检索路由设计借鉴 |
| RAGFlow（infiniflow） | 整机·深文档 RAG | 文档深解析强 | 解析件单拆喂模块 2 |
| MindSearch（InternLM） | 整机·多代理搜索 | **DAG 化搜索规划** | 直接喂 G1 扇出计划 DAG schema |
| Haystack 2.x | 框架·组件化 pipeline | 管线组件化 + 可观测 | 做 L2-L4 载体 vs 自有 pipeline.py 的得失 |
| LlamaIndex / LangGraph | 框架 | 生态最大 | 锁定风险·只取数据连接件的可行性 |
| txtai | 框架·轻量 | 嵌入+pipeline 轻 | 与 pgvector 的配合成本 |

### 3.3 评估七维与产出

七维：架构契合（四暗号/asyncio 亲和）/ 可拆性 / 维护活性 / 许可 / 社区健康 / 安全面 / 弃用出口成本。
**编排**：3 生成路（整机优先派 / 框架优先派 / 借鉴优先派 各自立论）+ 2 证伪路（默认 refuted）→ 多数票 → **底座裁定卡** → 元东方拍板 → 冻结进 reconciliation §1。

---

## 四、阶段 R2 · 功能模块 → 成熟方案对照查找（13 模块）

> 每模块产出一张**技术源卡**（模板见 §七）。候选只列名，执行时实测。

| # | 模块 | 需求真源 | 候选（⚠️全待实测） | 关键调研问题 | 红线/注意 | 喂缺口 |
|---|------|---------|------------------|------------|----------|--------|
| 1 | L1 源接入与连接器 | ledger.yaml / feasibility | Onyx connectors · RSSHub（逐路由）· SearXNG（已底座）· GDELT 客户端 | 连接器协议抽象 vs 我方 adapter 基类的归一 | RSSHub 路由级"不爬"筛查 | G3·G9 |
| 2 | 内容抽取与规整 | design L2 | **已移植✅**：trafilatura/htmldate/courlan/markitdown/magika · 增补评估：unstructured · docling | PDF 表格/扫描件深抽取；中文效果 | — | — |
| 3 | 验证层·事实核查与矛盾（闸2/闸5 工具链） | audit-system | Loki(OpenFactVerification) · FacTool · OpenFactCheck · NLI 模型（DeBERTa-NLI 系/cross-encoder） | 框架整移 vs 拆件喂闸；claim 拆解件单用 | 框架自带搜索**必须换成我方源**（红线+源治理） | G4 |
| 4 | 验证层·AIGC/污染检测（闸3） | audit-system | Binoculars · fast-detect-gpt | 中文文本效果；算力需求（ufo GPU 可承接） | 检测结果只做标签不做断言（诚实标注） | — |
| 5 | 实体对齐与去重（真值发现前置） | orchestration D5 | splink · dedupe · recordlinkage · datasketch(minhash) | 实体对齐件成熟度；真值发现算法（CRH/TruthFinder 系）预判 **C 档借鉴自研** | — | G4 |
| 6 | 编排外环 S2 durable 队列 | orchestration D7（冻结：内核 asyncio 不动） | Hatchet（已候选·复核健康度）· arq · taskiq · dramatiq | 仅复核 Hatchet 健康 + 轻量对照，**不重开内核决策** | 按指标门才升级 | G1 |
| 7 | 限流/熔断/重试件 | orchestration D6 | aiolimiter · pyrate-limiter(Redis backend) · pybreaker · tenacity | 与已决"Redis token-bucket per-source"的实现复用度 | — | G6 |
| 8 | 质量评测 harness | quality-eval | Ragas · DeepEval · promptfoo · langfuse(self-host) · phoenix | LLM-as-judge 多代理对接纯 Claude 编排；回归门 CI 化 | eval 数据禁带 PII | G8 |
| 9 | 监测雷达 | monitoring | changedetection.io（整机）vs 拆 diff 思想自研 | 整机挂 probe-a 的资源面 vs 只要 diff 内核 | 监测目标同样过"不爬"红线 | — |
| 10 | 隐私/PII 工程 | privacy | presidio · scrubadub | **中文 PII 识别实测**是关键（PIPL）；脱敏管线先于采集（probe-a 红线） | sensitive 三态承接 | — |
| 11 | 交付渲染管线 | delivery | WeasyPrint(html→pdf) · Pandoc · Marp/python-pptx(P2 ppt) · pyecharts · mermaid-cli | Core IR（自研不动）→ 各渲染器的接缝 | 渲染缓存=独立第三层（脊柱§三注） | — |
| 12 | 成本/可观测 | cost-metering | litellm（已有✅）· OpenTelemetry（机3 Jaeger 在役） · langfuse（与#8合并评估） | cost_event 双本账与 litellm spend 的对账 | — | G6 |
| 13 | 对象存储与存证 | 脊柱(真源悬空) | MinIO · SeaweedFS · garage · + 网页存证(SavePageNow API) | 选型+bucket 规范+lifecycle+落哪台机（probe-a 本机 or ufo）| 存证内容过 persist_policy 门 | **G7** |

---

## 五、组合与分配标准（tech-gate 12 项 + 落位四规则）

### 5.1 tech-gate 准入 12 项（仿 gate19 思想 · 每个候选过闸留痕）

| 闸 | 检查 | 不过处置 |
|----|------|---------|
| T1 | license 商用兼容：MIT/Apache/BSD 🟢 · LGPL 🟡 · **AGPL 🔴**（须独立服务隔离评估）· 无 license ❌ | 🔴→隔离评估或降 C 档 |
| T2 | 近 90 天有 commit | 降档或证明稳定终态（如 Pandoc 类成熟件豁免） |
| T3 | 近 1 年有 release | 同上 |
| T4 | bus factor > 1 或机构背书 | 标单点风险 |
| T5 | issue 响应活性（中位数实测） | 标弃用风险 |
| T6 | pip-audit/CVE 零高危未修 | ❌ 或锁版本+跟踪 |
| T7 | 依赖树重量（拖进多少传递依赖） | 超重→评估拆件 |
| T8 | 供应链：官方源、签名、typosquat 核对 | ❌ |
| T9 | Python≥3.12 / asyncio 亲和 | 不亲和→隔离进程或降档 |
| T10 | 可拆性：能只取所需模块 | 不可拆→S-整机姿态专议 |
| T11 | 文档/测试覆盖可用 | 标集成成本 |
| T12 | 弃用出口成本（替换路径预案） | 无出口→慎入 A 档 |

### 5.2 落位四规则（每个采纳件必须）

1. **登记**：入 tech-registry（建议落 ledger.yaml 平行的 `techstack.yaml` 或 SCT 扩展段）——名/档位/license/版本钉死/替换出口
2. **落格**：映射到 **L1-L4 × 四引擎矩阵**单元格（reconciliation §4）——一件一格、职责单一
3. **契约**：不破坏 L1 四暗号 + SCT 注册；外件全部包在我方 adapter 后面（防 vendor 渗透到业务层）
4. **冲突裁决**：件-件冲突 → 整体一致性优先 → 先裁剪件、再考虑微调编排 → 高 blast 变更上桌拍板

---

## 六、阶段 R3 · 补充辅助能力扫描（开放发现 · 信息收集完整后的补盲）

**纪律**：每路调研代理必带第二任务——**顺手登记 adjacent 能力**（与主题无关但对 probe 有用的发现）→ 统一登记表（能力/来源 repo/价值假设/对应赛道或闸）→ 主代理汇总评估 → 有价值的入 G 缺口清单或 backlog，无价值的留痕即弃。

**预设扫描面**（执行时主动看一眼）：
GEO 生成引擎优化 · 网页存证（Wayback SavePageNow）· OCR（PaddleOCR/Tesseract·证据图片化文档）· 翻译层 · 轻量知识图谱（NetworkX 级）· 时间线自动生成 · citation graph · simhash/minhash 去重 · 语种检测 · 可信源元数据集（媒体偏倚/可信度数据库类）

---

## 七、安全与真实性执行纪律（每源卡必过）

**技术源卡模板 · 7 必采字段**（全部现场实测，禁引用记忆）：

```
repo:         <URL>                    checked_at: <date>
license:      <SPDX·实测 LICENSE 文件>
activity:     last_commit / latest_release / open_issues（实测）
community:    stars+forks（仅参考·非决定因子）
security:     pip-audit 结果 / 已知 CVE / 依赖树深度
hands_on:     沙箱装得上 ✅/❌ + 最小 demo 跑通 ✅/❌（ufo 或本机 venv）
verdict:      档位 A/B/C + tech-gate 过闸记录 + 替换出口
```

- **双源核验**：GitHub 页 + 第二源（官方 docs/PyPI/论文）交叉，单源不定案
- **证伪**：每批结论 1 路对抗证伪代理（prompt 默认 refuted=true，要求推翻）
- **实测环境**：ufo 开发机（Docker/GPU）或本机 venv；**禁 probe-a 生产首装**
- **零凭据**：调研全程不需任何 key；遇到必须 key 试用的 → 记录后走 R1 流程，不当场注册

---

## 八、执行编排（波次 / 代理 / 产出 / 验收门）

| 波 | 内容 | 编排（R37） | 产出 | 验收门 |
|----|------|-----------|------|--------|
| **R0 准备** | 冻结已决清单 + 源卡模板 + 目录就位 | 单代理 sonnet | 本方案 + 模板 | 元东方过目本方案 |
| **R1 底座** | 三姿态对决（§三） | **opus 集成**：3 生成视角（整机/框架/借鉴）+ 2 证伪 | 底座裁定卡 | 元东方拍板姿态 |
| **R2 模块** | 13 模块源卡（§四），4 批 × 3-4 模块并发 | sonnet 扇出 + opus 汇总；每批 1 证伪 | 13 张技术源卡 | tech-gate 过闸记录齐全 |
| **R3 组合+补盲** | tech-gate 评审 + L×引擎落位 + 补充登记（§六） | opus 单代理 | 组合定案表 + 补盲清单 | 与 G1-G11 逐项对账 |
| **R4 总册** | 汇总 + 终轮对抗证伪 + 拍板包 | opus 集成 | `techstack-decision-v1.0.md` | 元东方拍板 |

- **成本**：全程零 R1 金钱成本（GitHub/web 公开信息 + 本地沙箱）
- **产出落点**：本目录（4-research/）`techstack-` 前缀；决策总册定稿后登 README 与 master-solution §七
- **时间预估**：R1 与 R2 首批可并行；全程 2-4 个工作会话量级

---

## 九、调研喂养 G1-G11 缺口对照（research feeds gaps）

| 缺口（reconciliation §8） | 由哪路调研喂 |
|--------------------------|------------|
| G1 扇出 DAG schema | R1（MindSearch/LangGraph 图结构借鉴）+ R2#6 |
| G3 SCT/ledger 字段对账 | R2#1（连接器协议抽象反推字段） |
| G4 可靠度三表示换算 | R2#3（事实核查框架的置信表示）+ R2#5 |
| G6 成本门契约 | R2#7 + R2#12 |
| **G7 对象存储真源** | **R2#13（直接定型）** |
| G8 master S1 施工表 | R4 总册（选型定 → 施工表才能编） |
| G9 gate19 补七赛道 | R2#1 连接器调研顺带 |
| G11 consistency-gate 脚本 | R3 补盲（链接检查类工具借鉴） |

> G2（scenario 模板）/G5（partial schema）/G10（ledger 域 bug）为纯内部设计/修复项，不依赖外部调研，随 S1 施工。

---

## 十、待拍板清单

| # | 事项 | 建议 |
|---|------|------|
| 1 | §一 愿景升级三条（工程姿态入宪/定位升维/飞轮显式化）是否采纳回填真源 | 采纳——它把"成熟移植>自研"从口头纪律变成宪法判据 |
| 2 | R1 底座姿态预判 S-借鉴 是否同意作为默认假设（让 3+2 对决推翻它，而非论证它） | 同意——已有骨架/契约/已决编排，举证责任应在"换底座"一方 |
| 3 | 启动指令：批准后 R1+R2 首批即可开跑（零成本） | 待令 |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> 关联：[reconciliation 仲裁总册](../records/probe-ssot-master-reconciliation-v1.0.md) · [feasibility 数据源轴](probe-github-datasource-feasibility-v1.md) · [编排方案](../3-build/probe-orchestration-engine-solution-v1.0.md) · [master-solution 入口](../probe-master-solution-v2.md)

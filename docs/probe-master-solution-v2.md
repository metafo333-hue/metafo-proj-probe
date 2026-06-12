# probe 情报引擎 · 总方案 v2.0（consolidated · 单一真源）

> 日期：2026-06-06 · 地位：**唯一入口总册**，把分散的 5 份设计/调研/审核文档收敛成一份层次分明、逻辑严谨、前后一致的方案，并给出多线程执行规划。
> 编写规范：每章先给【一句话·是什么】+【结论·确定方向】（第一性原理，不含糊）。
>
> **版本说明**：本文是 **v2 consolidated 总册**（非旧 v2 方案；旧 v2 = probe-solution-design-v2.html·已归档 _archive/）；本册总纲/执行波次已被 [probe-alignment-topology-prelaunch-v1.md](records/probe-alignment-topology-prelaunch-v1.md)（0-charter 立项总纲）继承。

---

## 〇、方案一句话

**【是什么】** probe = 把「一句话需求 + 任意素材（链接/图/视频/文档/文字/名字）」变成「多源采集 → 专业审核 → 对抗证伪后**可溯源、可证伪**的情报成品」的情报引擎。
**【结论】** probe 的护城河不是 AI 分析（人人都能做），而是 **「别人给观点，probe 给带可信度标签、可回放、扛得住证伪的结论」**。

---

## 一、两支柱（第一性原理）

| 支柱 | 一句话 | 结论 | 真源文档 |
|------|--------|------|---------|
| **① 数据源** | 谁的料更专业、更全、更真，结论就更不可替代 | 不靠爬虫靠**合法专业源整合**：17 域 catalog + 5 类接入 + 「源的源」持续扩 | [feasibility-v1](4-research/probe-github-datasource-feasibility-v1.md) |
| **② 审核** | 能分析不算本事，**给得出依据、扛得住证伪**才是 | 双审 8 闸 + Admiralty 专业标准 + 对抗证伪：每条结论带三标签 | [audit-system-v1](3-build/probe-audit-system-v1.md) |

两支柱在 **L3 验证层**交汇：数据源供料 → 审核体系判真。**这是 probe 的全部价值所在。**

---

## 一·补、工程姿态（技术栈策略 · v2.1 入宪 · 2026-06-11）

> 来源：R1-R4 技术栈 GitHub 调研实战裁定（[底座裁定卡](4-research/techstack-cards/techstack-base-verdict-v1.0.md) · [技术栈决策总册](4-research/techstack-decision-v1.0.md)）
> 地位：§一 两支柱是战略护城河，本节是工程实施哲学——外环借成熟轮子·内核护城河自锻，两者合起来才是完整 probe 工程观。

**三条工程戒律（R1-R4 源码级实战验证 · 2026-06-11 入宪）：**

① **「轮子取天下，天平自己造」——外环借·内核锻**
- **可替换外环**（连接器/抽取/限流/渲染/评测）→ S-借鉴姿态：成熟开源 vendor 移植/借思想/拒整机依赖，随技术演进可换件。实战验证：S-整机(GPT-Researcher)被 refuted（scraper 平行出网 + 105 依赖背负），S-框架(Haystack)被 refuted（@component 脱离 Pipeline = 空装饰器）
- **护城河内核（三件·不外包）**：① 可信度引擎 8 闸 + 对抗证伪 ② 真值发现 / ledger 源治理 ③ Core IR 结论形态——稀释即失去竞争壁垒

② **定位升维：情报引擎 → 可信度基础设施**
- 给任何下游（MetaAsk / MetaLearn / MetaCut / MetaFlow / 用户直查）提供「可溯源·可证伪·可回放·可替换」的信任底座
- 技术栈对齐：13 模块全本地推理 / 零 SaaS 订阅 / 全链路可追溯至代码

③ **演进飞轮：可替换外环 + 不动内核**
- 外环件按 tech-gate 12 条随时替换（docling → 更强抽取器 / Hatchet → 更强队列…），内核积累对抗证伪数据 → 越用越准 → 接入更多源
- 与数据飞轮联动（MetaLearn §7）：验证层命中 → 回流 MetaLearn → 审核越来越准

---

## 二、章节地图（层级明确 · 去冗余 · 单一真源）

> 原 5 份文档有重叠（七段报告/三层深度线/验证层在多处出现）。本表确立**每个主题只有一个真源**，其余引用不重写。

| 章 | 主题 | 一句话结论 | 真源（唯一） |
|----|------|-----------|------------|
| 0 | 定位与价值主张 | 卖「可溯源、可证伪的结论」 | 本册 §0/§1 |
| 1 | 引擎矩阵与契约 | 双视角(引擎+子项目)·L1四暗号·MetaFlow可调度 | [alignment-prelaunch](records/probe-alignment-topology-prelaunch-v1.md) §2 |
| 2 | **支柱①数据源仓库** | 17域catalog·5类接入·标准19门 | feasibility-v1（catalog真源） |
| 2.5 | **赛道注册表** | 17域(D1-D17)+**9赛道**(A–E横向5业务域 + F金融/G元惠/H任务/I AI优惠旗舰)·type/tier/weight/presentation 四元数据·"加赛道=改数据不改架构" | [track-registry-v1.1](3-build/probe-track-registry-architecture-v1.0.md) |
| 3 | 四层引擎架构 | L1接入/L2采集/L3验证/L4整合·源无关解耦 | design-v1 §4 + 拓扑图 alignment §3 |
| 4 | **支柱②审核体系** | 双审8闸+专业标准+对抗证伪 | audit-system-v1（真源·已升级旧7闸） |
| 5 | 场景与交付 | **9赛道**(A–E横向5业务域 + F金融/G元惠/H任务/I AI优惠旗舰)·27场景·对外一期=自媒体A+金融F(G/H 孵化中 incubating)·七段报告·三层深度线·交付多模态 | design-v1 §5 + [track-registry](3-build/probe-track-registry-architecture-v1.0.md) |
| 6 | 合规与红线 | **单条红线「不自己爬」**（probe 不实施爬取/逆向/模拟登录；第三方API可用，供应商担责）；独立保留：个保法最小必要/aigc_flag/原料进结论出；弃蝉妈妈 | feasibility-v1 §5（红线口径真源） |
| 7 | GEO与飞轮 | geo_publishable+conclusion_block·源命中回流MetaLearn | alignment §2(A-2) |
| 8 | 上线门与里程碑 | M1公开档→M2付费档(C2质量门+人工复核)→M3大厅 | alignment §4 |
| 9 | 多线程执行规划 | 见本册 §4 | 本册 §4 |

**去冗余裁定（已消除的重复）**：
- 验证层：design-v1 §3 旧 7 闸 → **作废**，统一以 audit-system-v1 八闸为准。
- 三层深度线：统一定义在 design-v1 §5.4 + audit-system §5（审核分档），其余处只引用。
- 七段报告：唯一真源 = v2 方案 + design-v1 §5；其余处只引用编号，不重抄定义。
- 合规铁律：唯一真源 = feasibility-v1 §5；各文档只引用不重列。

---

## 三、整体逻辑链（前后一致 · 一条主线贯穿）

```
一句话需求/素材
   │  MetaAsk 澄清意图 → 任务类型+输出规格+深度档+交付形态
   ▼
[支柱①] L1接入(适配器·17域catalog·标准19门) → L2采集(多源扇出)
   │
   ▼
[支柱②] L3审核(闸0过程留痕 → 闸1-7结果审核 → 对抗证伪 → 三标签)
   │
   ▼
L4整合(七段报告/conclusion_block) → 按三层深度线裁剪(guards C4)
   │
   ▼
交付(文字/图/HTML/PPT/视频) + GEO分发 + 源命中回流MetaLearn
   │
   └─ 全程闸0 trace 留痕 · 成本计入cost.base · 走L1四暗号契约
```

---

## 四、多线程执行规划（先后顺序 + 并行波次）

**【一句话】** 按「依赖关系」分 4 波，每波内部多线程并行，波间串行；零成本部分（Wave1-3）先全做完，付费源（Wave4）最后按 R1 逐个接。

### 依赖总则
```
Wave1 地基(零成本) ──▶ Wave2 扩源+审核栈(零成本) ──▶ Wave3 对抗证伪+场景+质量门 ──▶ Wave4 付费源+GEO+MetaFlow
闸0过程留痕 = 其它审核闸的前提(Wave1 先起)  ·  七段报告依赖审核体系出标签(Wave3)
```

### Wave 1 · 地基（3 线程并行 · 全零成本可回滚）
| 线程 | 任务 | 产出 |
|------|------|------|
| **T-A 数据源** | ledger 升多域catalog + catalog.py加载器 + 首批免费源模块(wikipedia/github/osv/webarchive/searxng) | 数据源仓库骨架可查可调 |
| **T-B 契约对齐** | manifest `industry=["自媒体","金融"]`（2026-06-08 纳入金融）+补`subdomain`；invoke 补`geo_publishable`+`conclusion_block`+`version`；同步 selftest 断言 | 契约对齐 master-plan·selftest 11/11 保持 |
| **T-C 审核地基** | 闸0过程留痕(OpenLLMetry+Langfuse) + P0审核工具(SemHash/MiniCheck/nli-deberta/Binoculars) | 双审地基可用 |

### Wave 2 · 扩源 + 审核栈（3 线程并行 · 零成本）
| 线程 | 任务 |
|------|------|
| **T-D 扩免费源** | 自托管 RSSHub/SpiderFoot/Yente + 免费层 VirusTotal/urlscan/arXiv/OpenAlex/edgartools/OpenCorporates/GDELT |
| **T-E 审核标准** | 闸1-7 工具栈接入 + Admiralty双轴/证据分级/四眼 强制元数据标签 + 极速版/深度分析版双形态·智能界定（默认极速兜底 + 确定性自评 + 按需升级·每版各自精品·见 [speed-depth-tiering-v1.0](3-build/probe-speed-depth-tiering-v1.0.md)） |
| **T-F 交付层** | 七段报告骨架 + 三层深度线裁剪 + 交付形态(文字/图/HTML) |

### Wave 3 · 证伪 + 场景 + 质量门（3 线程并行）
| 线程 | 任务 |
|------|------|
| **T-G 对抗证伪** | 双审8闸·闸6 D3-Judge模式复刻于 probe opus 编排(生成路×3+证伪路×2+裁决+后验门)·完整8闸见audit-system-v1 |
| **T-H 场景路由** | 27场景模板(锚点A自媒体先跑通) + MetaAsk意图路由 |
| **T-I 质量门** | C2质量门实评 + 成品人工复核≥80%(M2付费档前置·不可自过) |

### Wave 4 · 变现 + 编排（按 R1 逐个）
付费源逐个授权(DataForSEO→天眼查→Keepa→TinEye→Crunchbase) + GEO分发管线 + MetaFlow编排接入(capability声明) + M3大厅上架。

**并发编排引擎（2026-06-10 落方案 · 解 L2 多赛道多 API 协同）**：单任务扇出到 N 赛道×M API 的并发/时延/调度内核，**已有完整设计真源** [orchestration-engine-solution-v1.0](3-build/probe-orchestration-engine-solution-v1.0.md)（经深度调研证伪）。七项已定决策：① **Scatter-Gather 内核**（不为单请求扇出上 Airflow/Temporal）② **asyncio.TaskGroup+timeout** 结构化并发（避 PEP 789 异步生成器取消坑）③ 聚合器**三态完成条件 + partial 显式标注**（慢源不阻塞）④ **反应式对冲**降尾延迟（仿 Envoy·仅超时触发·**免费源开/付费源禁**·控成本）⑤ **真值发现**而非多数票做多源冲突消解（喂 8 闸）⑥ 集中式 **Redis token-bucket** per-source 限流 + 429 退避 + 熔断 ⑦ **S1 单机 asyncio → S2 durable 队列（Hatchet 候选）** 按指标门演进。落地分 OS1-OS4（OS1-3 零成本单机·与 Wave1-3 同期；OS4 对齐本波编排接入）。

### 4.1 阶段编号对照表（消歧 · 三套编号一图对齐）

> ⚠️ **同名异义警示**：feasibility-v1 的 **P0/P1/P2 是「数据源接入优先级」**（哪批源先接），与 design-v1 的 **P0-P4「引擎标准进度阶段」**（引擎成熟度）**同名异义，勿混**。下表把本册 Wave 波次、design 进度阶段、里程碑三套编号对齐到同一时间轴。

| 本册执行波次（Wave） | design 引擎进度阶段（P0-P5） | 里程碑（M1-M3） | 一句话 |
|---------------------|------------------------------|----------------|--------|
| Wave 1 地基（零成本）| P2（当前位置·基座搭建）| — | ledger 升多域 catalog + 闸0 + 契约对齐 |
| Wave 2 扩源+审核栈（零成本）| P2→P3 | **M1 公开档**（粘链接→评级+结构+公开结论）| 免费源全栈 + 双审 8 闸标准 + 交付骨架 |
| Wave 3 证伪+场景+质量门 | P3 | **M2 付费档**（过 C2 质量门 + 人工复核≥80%）| 对抗证伪 + 27 场景 + 质量门 |
| Wave 4 变现+编排（按 R1）| P4→P5 | **M3 大厅上架**（待母体 HttpToolClient+identity+registry）| 付费源 + GEO + MetaFlow + 上架 |

> 注：feasibility-v1 的 **P0/P1/P2 数据源优先级**在 Wave 1-2 落地（P0 免费底座先接、P1/P2 按 ROI 逐批），属「接哪批源」维度，不参与上表的「引擎阶段」时间轴。

### 4.2 编排线 OS（跨波并行 · L2 采集层运行时 · 解多赛道多 API 协同）

**【一句话】** 编排引擎是 **L2 采集层的内部能力**，不改 M1/M2/M3 公开里程碑；OS1-OS3 全零成本单机、**与 Wave1-3 同期并行**（喂 M1 性能体感），OS4 对齐 Wave4 编排接入。真源 [orchestration-engine-solution-v1.0](3-build/probe-orchestration-engine-solution-v1.0.md)。

| 编排槽 | 排进波次 | 任务 | 产出 | 成本 |
|--------|---------|------|------|------|
| **OS1 编排内核** | 并入 **Wave 1**（随 T-A 数据源骨架）| Scatter-Gather + 元数据驱动扇出计划 + TaskGroup 超时预算 + 单赛道失败隔离 | `app/orchestrate/` 内核·极速版同步扇出可跑 | 零·单机 |
| **OS2 流式合成+反应式对冲** | 并入 **Wave 2**（随 T-D 扩源）| 聚合器三态 + partial 标注 + 免费源反应式对冲(付费源禁) + 进程内 Semaphore 限流 | 慢源不阻塞·尾延迟实测下降 | 零 |
| **OS3 多源融合** | 并入 **Wave 3**（随 T-G 对抗证伪·喂 8 闸）| 真值发现迭代 + 时效衰减 + 实体对齐去重 + 冷启动先验喂值 | 多源冲突加权合成草稿入 L3 闸 | 零 |
| **OS4 分布式化（按需）** | 并入 **Wave 4**（编排接入）| Redis 集中式 token-bucket + 429 退避 + 熔断 + 评估升 Hatchet/Arq(小压测对比) | S2 形态·深度版异步+可回放 | 低·复用 Redis |

> 依赖纪律：OS1 是 OS2/OS3 的前提（先有扇出内核才能谈合成/对冲）；OS4 升 durable 队列由 §3.8 指标门触发（事件循环延迟/连接数/CPU 单核饱和/出口带宽），**不为未到规模预付分布式复杂度税**。OS1-OS3 与各自 Wave 同消息多线程并行，OS4 待指标门或地域瓶颈。

---

## 五、商业模式（极速版/深度分析版双形态·智能界定 · 定价/商业模式真源）

**【一句话】** **极速版 / 深度分析版双形态 · 智能界定**（默认极速兜底 + 确定性自评 + 按需升级 · 每版各自精品 · 见 §四 T-E + [audit-system §五](3-build/probe-audit-system-v1.md) + [speed-depth-tiering-v1.0](3-build/probe-speed-depth-tiering-v1.0.md)）；钱买的是**深度分析版**（8 闸全验 + 对抗证伪 + 多源专业数据），不是"极速版打折"——极速版在其定位也是认真精品（留痕+溯源+交叉，显著标注未全验）。
**【结论】** 按量 credits + 按件交付物为主；持续监测走订阅特例；**钱买深度分析版**（极速版认真精品但不做深度抗污染/对抗证伪，由系统智能界定走哪版让资源匹配任务需要，比"人人 8 闸全开"可持续）。

### 5.1 质量解耦定价原则（钱买四轴 · 都不碰质量）

| 轴 | 内容 |
|----|------|
| ① 次数/配额 | 免费 N 次/天精品 · 超额按量 credits |
| ② 输出形态 | 文字→图→HTML→PPT→视频，高形态多花 token（不多花数据成本） |
| ③ 便捷性 | 异步多通道通知 / 优先队列 / 订阅监测 / 批量 / API / 历史对比 |
| ④ 特殊服务 | 人工复核背书 / 定制模板 / 私有数据源接入 / 白标可商用 / SLA |

### 5.2 付费场景分层矩阵（用户档 × 场景）

| 用户档 | 心理 | 免费给什么 | 付费买什么 |
|--------|------|-----------|-----------|
| **C 端个人** | 怕花钱、要即用 | 每日 N 次精品 + 文字/基础图 | 额外次数① · 升级视频/PPT② · 多通道通知③ |
| **小 B** | 算 ROI、要效率 | 体验额度 | 月度配额包① · 批量③ · 订阅监测③ · API③ |
| **中大 B** | 要专属、要背书、肯付高客单 | 样例报告 | 人工复核背书④ · 定制模板④ · 私有源④ · 白标④ · SLA④ |

### 5.3 高端/特殊服务（④ 轴 · 高客单在此）
- 人工专家二审背书（尽调/投资的信任溢价）· 私有数据源接入（私域情报）· 定制模板+白标（咨询转售）· 持续监测雷达（B6/C4·订阅特例）· SLA/私密加密交付（法务/投资）

### 5.4 计费落地 + 成本控制
- 走母体声明式管线 `契约→dispatch→guard→wallet.debit`，注册 `tools/probe/contract.py`
- **质量门（8 闸全开）对所有档位都跑**；扣费扣在「次数 × 形态 token × 特殊服务」，不扣在验证强度
- 成本控制：**验证内核缓存复用**（同链接/实体不重跑 8 闸）+ 免费次数上限（按 LTV>CAC 反推）
- **API 调取治理（落地设计·2026-06-10）**：上面「缓存复用」「免费/付费选择」只是理念，完整落地见 **API 调取治理体系（5 份·§七）**——〔发现〕[风险清单 55 坑](3-build/probe-api-fetch-risk-checklist-v1.0.md)（含「重复调用涨成本」C1/C2/M5）→〔可见〕[成本埋点·双本账](3-build/probe-cost-metering-design-v1.0.md)（计费账 vs 供应商计量账·修 C4/M1）→〔选型〕[付费/免费分层决策+能力价值目录](3-build/probe-source-selection-and-capability-registry-v1.0.md)（默认免费兜底·信号触发升付费·成本门拦扣费雷）→〔应对〕[数据动态智能管控](3-build/probe-data-dynamic-governance-design-v1.0.md)（Data Governor 五信号+十步闸·每次调取动态决定 调/缓/降/拦）→〔保活〕[源运维与可靠性](3-build/probe-source-ops-and-reliability-design-v1.0.md)（健康 failover·schema 漂移·key 生命周期·录制回放）。

> 价格锚（低于豆包 68/200/500，按次付费不强制订阅）见 [alignment §2 C-7](records/probe-alignment-topology-prelaunch-v1.md)；行业主次/心理学/数据分级展示见 [design-v1 §5](3-build/probe-intelligence-engine-design-v1.md)；完整推导见 [bizmodel review](records/probe-value-presentation-and-bizmodel-review-v1.md)。

---

## 六、待决策（不阻塞 Wave1-3）
- 命名：MetaProbe 中文工作名 = **元探**（待元典录签发正式名）
- Wave4 付费源 R1 授权顺序（已建议 ROI 排序）
- master-plan 是否补 MetaProbe 独立 Part（喂 MetaFlow⑤反推）

---

## 七、文档体系（核心 5 份 + 赛道深化专题 · 本册为入口）

### 核心 5 份（各司其职）
| 文档 | 角色 |
|------|------|
| **master-solution-v2（本册）** | 唯一入口·总册·去冗余·执行规划 |
| design-v1 | 框架(架构/场景/交付)·§3旧7闸已作废 |
| feasibility-v1 | 支柱①数据源 catalog 真源 |
| audit-system-v1 | 支柱②审核体系真源 |
| alignment-topology-prelaunch-v1 | 对齐核查+拓扑图+上线前章节 |

### 赛道深化专题（2026-06-08 新增 · 金融F + 自媒体A 两大主攻赛道）
> 数据源判定真源仍是 feasibility-v1；以下为 F/A 两赛道的深化展开，与真源同源不悖（feasibility 给 5 域总览，这些给单赛道细栈）。
| 文档 | 角色 |
|------|------|
| datasource-finance-track-f-v1（含 v1.1） | 金融F数据源完整清单·feasibility 金融赛道深化（27+源/状态/成本总账/6 红线）|
| datasource-selfmedia-track-a-v1（含 v1.1） | 自媒体A数据源完整清单·feasibility A 域深化（官方源/合规债/逆向弃用）|
| **finance-track-f-design-and-competitive-v1.0** | 金融F设计方案+竞调·design 的金融赛道版（定位/4 子域/L1-L4/双审 8 闸/商业模式/MVP）|
| datasource-gate19-and-dedup-v1.0 | 接入核验(标准19逐源)+源的源去重图谱·feasibility 接入执行层 |

### API 调取治理体系（2026-06-10 新增 · 支柱②运行时落地 · 闭环：发现→可见→选型→应对→保活）
> 起因：盘点「probe 处理 API 信息调取的坑」（首坑=重复调用涨成本）。五份同源互引、对应 §5.4 成本控制的落地，其中风险清单为**活文档**（遇新坑持续入库·已演进至 v1.2/55 坑）。
| 文档 | 角色 |
|------|------|
| **probe-api-fetch-risk-checklist-v1.0**（活文档·gate·现 v1.2）| 〔发现〕API 调取风险**问题库**·55 坑分 10 类·S1 接入逐条过门·新坑持续补充 |
| **probe-cost-metering-design-v1.0**（设计·未落码）| 〔可见〕成本面·双本账(计费 vs 供应商计量)·cost_event schema·熔断阈值 |
| **probe-source-selection-and-capability-registry-v1.0**（设计·未落码）| 〔选型〕付费/免费分层决策·能力价值目录(扩 ledger 4 字段)·select_score·决策表 |
| **probe-data-dynamic-governance-design-v1.0**（设计·未落码）| 〔应对〕Data Governor 五信号+三段闸·每次调取动态智能管控 |
| **probe-source-ops-and-reliability-design-v1.0**（设计·未落码）| 〔保活〕源运维：E8 健康状态机+failover·E9 schema 漂移三道防线·E10 key 生命周期·Q5 录制回放 |

### 并发编排/调度体系（2026-06-10 新增 · L2 采集层运行时落地 · 解「多赛道多 API 怎么高效协同」）
> 起因：盘点「probe 处理单任务时调用多赛道组合 + 多 API，怎么增效率/合成/分配/压时长/要不要分布式」。需求规格→深度调研(5路扇出·23证伪存活)→最终方案，三份递进。
| 文档 | 角色 |
|------|------|
| **probe-orchestration-engine-solution-v1.0**（最终方案·决策已定）| 编排/调度层**架构与选型真源**·Scatter-Gather 内核+结构化并发+反应式对冲+真值发现+分布式限流+轻量→重量演进阶梯+OS1-4 落地 |
| probe-orchestration-concurrency-requirements-v1.0（需求规格）| 编排层需求条目 R1-R10（DAG/调度/并发/时延/合成/限流/容错/架构选型/硬件/可观测）·本方案之解 |

### 工程纵深设计体系（2026-06-10 新增 · 方案设计阶段查漏补全 · 闭 7 缺口）
> 起因：方案设计阶段查漏——主线（架构/数据源/审核/商业/编排）已自洽，但几个工程纵深只有零散提及无专门设计。补全 5 份，**数据脊柱为底、其余引用之**。
| 文档 | 闭缺口 | 角色 |
|------|--------|------|
| **probe-data-persistence-and-cache-design-v1.0**（数据脊柱）| #1 数据模型 + #5 缓存层 | PG 数据模型(12 表·probe schema)+Redis 两层缓存+限流+任务态·**其余设计共同引用的存储真源**·persist_policy 红线执行抓手 |
| **probe-quality-eval-methodology-v1.0** | #2 质量评测 | 分形态质量度量+golden set+eval harness(LLM-judge 对抗集成)+回归防退化门+置信度校准·M2"可溯源可证伪"全验前置 |
| **probe-privacy-retention-compliance-engineering-v1.0** | #3 隐私留存 | 红线从"声明"落"管线可执行"·人物 OSINT 不落库双重硬保障(应用层+PG 触发器)+PII 脱敏三点+留存矩阵+删除权+aigc 全链路 |
| **probe-monitoring-radar-and-feedback-loop-design-v1.0** | #4 监测雷达 + #7 反馈闭环 | 监测订阅状态机+diff 检测+告警(成本控制 flash-first)+反馈防刷三道门→在线修正源可靠度·与 MetaLearn 飞轮分工(R22 不直连) |
| **probe-delivery-rendering-pipeline-design-v1.0** | #6 交付形态生成 | 统一内核 Core IR→多形态渲染·M1 上 text/img/html·PPT/视频后期·护城河可见(三标签+溯源强制呈现) |

> 区分：[s1-impl-plan §二](3-build/probe-s1-impl-plan-v1.0.md) 的 6 条是**实现阶段代码断层**（code 落后 design），非设计缺口；本体系是**设计阶段补的纵深**，两者不混。

> 归档：datasource-selection-v1（早期开源库+五平台调研）已被 feasibility-v1 取代 → `_archive/datasource-selection-v1.md.archived-20260608`（独有的开源处理库 F1 选型作历史保留）。

---

> 下一步：执行 Wave 1（T-A/T-B/T-C 三线程并行）——全零成本、可回滚、不碰生产。

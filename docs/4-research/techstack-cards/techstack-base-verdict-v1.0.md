# probe 底座裁定卡 v1.0（R1 对决产物 · **已拍板 2026-06-11 · 冻结**）

> 日期：2026-06-11 · 拍板：**2026-06-11 元东方确认·执行包 6 条已并入 s1-impl-plan §六 Wave1**
> 机制：3 生成路（整机/框架/借鉴 各自立论·实测调研）+ 2 证伪路（默认 refuted·实测攻击）→ 多数票
> 上游方案：[techstack-github-research-plan-v1.0.md](../techstack-github-research-plan-v1.0.md) §三 · 真实性：全部主张经 WebFetch 源码级实测（checked_at: 2026-06-11）

---

## 裁定：S-借鉴 胜出（保自有骨架 · 拆纯协议 · 抄思想 · 拒整机拒重框架）

| 派别 | 立论核心 | 证伪结果 | 判定 |
|------|---------|---------|------|
| **S-整机**（GPT-Researcher 当中段） | custom retriever 可拔→红线落地·8闸后置质检·190行wrapper | ① RETRIEVER=custom **不真正关爬**——scraper 是平行出网路径（researcher.py 实测：无 raw_content 的 URL 仍自爬），红线靠"每条带>100字正文"的**隐性契约**凑巧堵住，立论方未声明未实测 ② 依赖实测 **105+ 直接依赖**（LangChain 全家桶+LangGraph+numpy<2.3 钉子），与冻结 asyncio 内核构成**双层编排嵌套** ③ Py3.14 零证据 ④ LLM 层(ChatAnthropic 一等公民)与产物可观测两点 survives | ❌ **partially-refuted** |
| **S-框架**（Haystack @component 载体） | 只用 @component 不用其 Pipeline·锁定最浅·白拿 typed sockets/YAML | ① 源码实测：typed sockets/YAML 序列化**全是 Pipeline 层特性**，直接 `.run()` 零类型校验——不用 Pipeline 则 @component 退化为**空装饰器** ② 必装依赖含 openai+posthog（遥测 SDK，对采集系统是负资产）③ pydantic（FastAPI 已自带）可做真校验的 typed I/O——**增量价值为负** | ❌ **refuted** |
| **S-借鉴**（保骨架·拆件·抄思想） | 唯一真浅耦合 vendor 件=Onyx 连接器协议·其余四件抄思想·护城河不稀释 | ① Onyx connectors **确在 MIT 侧**（license 边界实测通过·EE 钩子是软回退非硬耦合）② 但"重命名移植"低估——实测需剪枝 **~9 个内部模块子树**（interfaces.py 281行14类 + models.py 645行），工作量上调一档 ③ 抄思想避开依赖背负与冻结冲突，方向被两路证伪共同确认正确 | ✅ **partially survives → 胜出** |

**三派实质收敛**（证伪路2 交叉验证）：终态都是「顶层 asyncio Scatter-Gather 冻结自研 + 8闸/ledger/Core IR 护城河自研 + 中段借数据接入」。真分歧只在**借多深**：借"带行为整机"（太深·撞红线撞冻结）vs 借"抽象壳"（空壳·毒依赖）vs **借"纯协议契约"（正确档位）**。

---

## 裁定后的执行包（Wave1 内·随 OS1 启动）

| # | 动作 | 来源 | 喂哪 | 工作量级 |
|---|------|------|------|---------|
| 1 | **vendor · Onyx 连接器协议**：BaseConnector/Load/Poll/Checkpointed 三态契约 + Document/Section，按 ~9 模块剪枝清单显式移植（DocumentSource enum/ExternalAccess/db.enums×2/make_url_compatible/IndexingHeartbeat stub/RawFileCallback stub） | onyx(MIT) | L2 采集层统一接口 + Core IR 的 Document 形态 | 中（剪枝+stub） |
| 2 | **抄契约 · raw_content 零爬不变量**（证伪路1 贡献）：检索器只回 `{url, raw_content}`、正文由合规源预填、抓取器收空列表——把"不自己爬"做成**数据结构层不变量**，写进 ledger 源接入契约（每条必带正文），比开关关爬更硬。**修正（M1 卡实测）**：Onyx Document 模型无 raw_content 字段、正文落 `TextSection.text`——接入契约写法以"Document.sections[].text 必非空"表达同一不变量 | gpt-researcher 设计点 + onyx 字段实测 | 红线工程化 + ledger 接入规范 | 小 |
| 3 | **抄 schema · MindSearch DAG**：WebSearchGraph 的 node dict(content+type)/edge dict(id/name/state三态) 抄成我方 dataclass，执行层用已决 TaskGroup（不引 lagent/线程池） | mindsearch(Apache-2.0) | **G1 扇出计划 DAG schema** | 小 |
| 4 | **抄思想 · STORM 视角引导提问**：找相关主题→生成多视角→并行对话 骨架抄成提示词模板，驱动七段报告（不引 dspy·用纯Claude） | storm(MIT) | 七段报告生成器 | 小 |
| 5 | **抄思想 · ODR 状态分层**：raw_notes(原始) vs compressed_research(精炼) 分层语义，设计聚合器三态+partial 字段（不引 langgraph·PG+Redis 持久） | open_deep_research(MIT) | Scatter-Gather 聚合器状态 | 小 |
| 6 | **参考 · provider 映射与产物 schema**：GPT-R 的 get_llm 分发结构、source_urls/research_context/research_sources 三 getter 字段，作我方聚合器输出 IR 参考 | gpt-researcher | 聚合器输出 schema | 零（参考） |

## 风险登记（借鉴姿态自认+证伪修正）

1. 集成胶水自担、上游 schema 演进不自动跟随 → 对策：执行包 #1 的剪枝清单显式化 + 季度对照上游 diff
2. 重复踩坑盲区（失败重试/部分结果/去重的边角 case）→ 对策：执行包 #5 抄状态分层时连边界处理注释一起读
3. 工作量曾被低估 → 已上调：#1 为"中"级（~9 模块剪枝），非"重命名即可"

---

> 拍板项：① 本裁定（S-借鉴+执行包6条）② 连带方案 §一 愿景升级三条（工程姿态入宪——本裁定即其第一次实践）
> 拍板后：执行包并入 s1-impl-plan（升级为全量 S1 施工表·缺口 G8）· 本卡冻结进 reconciliation §1 事实表

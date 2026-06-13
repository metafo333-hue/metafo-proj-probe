# probe · 设计↔实现差距 + S1 施工清单 v1.0

> 日期：2026-06-10 · 性质：**方案层文档**——记录逻辑链路审查发现的"文档↔代码断层"，作为**方案定稿后 S1 实现的施工图**
> 背景：2026-06-10 逻辑链路审查发现——probe **文档设计完整自洽**，但**代码落后于设计**，主线断层全在"文档↔代码"垂直方向（详见审查结论）。
> 🔒 纪律：**方案制定阶段不就地改代码**。断层在此清单沉淀，方案定稿后**统一 S1 实现**，不哪里发现缺口就就地补哪里。

---

## 一、可落地性已验证（方案制定中顺手验证 · 非正式 S1 · 已 selftest 过）

> 为确认"护城河设计能兑现"，在审查中顺手接通验证（已通过 selftest 8 passed），证明设计可落地；正式 S1 时纳入并接真 backend。

| 项 | 内容 | 状态 |
|----|------|------|
| **8 闸接入活管线** | `pipeline._deep` → `run_audit`：deep_probe 结论原子化（fact_check.claims + 结构）→ 8 闸 → conclusion_label（可溯源可证伪标识各档都给）| ✅ 已接 · selftest 过 · 结构兑现（StubBackend）|
| **确定性自评（信号C）** | `app/audit/certainty.py`：基于 conclusion_label（置信/证据/源数/AIGC/矛盾）算确定性分 → "极速交付 or 建议升级深度版" | ✅ 已建 · 实测逻辑正确（单源低置信→建议升级）|

> 意义：护城河 8 闸 + 智能界定信号 C 从"文档设计"验证为"可跑代码"。真实质量待接真模型 backend（替换 StubBackend 即可）。

---

## 一·补 · 设计层裁定（2026-06-10 定稿 · 实现留 S1）

> 应"在设计方案层面全部进行"——把设计层能定的待决项一次性裁定，代码实现统一留 S1。

| # | 设计待决项 | ✅ 设计裁定 | S1 落实方式 |
|---|-----------|-----------|------------|
| **D1** | 数据源放行口径（qualified vs gate_passed）| **qualified（采购边界·主门·正规商业 API 采购即放行）为准；gate_passed（gate19 官方授权）作更高合规等级备选标记、不阻断**——符合 2026-06-04 采购方边界裁定 | S1 落 `get_adapter` 注释 + ledger gate19 选填、对 active 源校验一致 |
| **D2** | 三层裁剪字段统一（apply_depth_line 扁平 vs redact_by_tier 七段）| **统一到七段报告 s1-s7 + `redact_by_tier`**（design-v1 七段是核心交付，redact 按 s1-s7 精确裁剪更完整）；`apply_depth_line`（扁平·临时）**废弃** | S1：deep_probe 产 s1-s7 字段 · `_deep` 改用 redact_by_tier · 删 apply_depth_line |
| **D3** | 确定性自评因子权重 | **规则版 v1 定稿**（置信 0.4 / 证据 0.3 / 源数 0.2 / AIGC −0.15 / 矛盾 −0.2 · 阈值 0.5）；真实数据后 S1 可迭代为 ML/LLM 版（speed-depth §9.1④ 扩展位）| certainty.py 已建 · S1 接真 backend 后校准阈值 |
| **D4** | 第三方担责法律口径 | **采集层担责成立；二次分发 / 聚合再处理 / 个保法拼背调三处 probe 自建合规判定层**（已补诚实限定·愿景书§九 + feasibility）| S1 在 governor 加这三处的合规判定 hook |
| **D5** | governor 统一取数挂载点 | **S1 先在 l0 凿出唯一取数函数 `fetch_one(url, kind)`**——收敛现 article/doc→extractors、video/social→registry 两岔路；governor 接管此唯一入口（"禁绕过"才有落点）| S1：重构 `l0.extract_public` → 统一 fetch + `governor.fetch` 包装 |

> **设计层至此全部裁定** · 代码实现统一 S1 · 守"方案制定与实现分阶段"。剩余待决全是元东方决策/流程项（命名签发 / R1 付费授权 / 天眼查资质），非设计层面可定。

---

## 二、待 S1 实现的断层清单（按审查优先级）

> **2026-06-13 重盘**（代码实态逐项核对·台账此前滞后）：6 条中 3 条已完成、3 条半成——剩余工作量远小于纸面。

| # | 断层 | 处理方式 | 涉及文件 | 验收标准 | 状态(2026-06-13 重盘) |
|---|------|---------|---------|---------|--------|
| 1 | **8 闸接真 backend** | StubBackend → 真模型（faithfulness/nli/judge/detect_aigc） | `app/audit/backends.py` | conclusion_label 出真实审核值 | ✅ **LIVE（2026-06-13 probe-a 生产验证）**：run_audit 默认兜底 StubBackend()→get_backend() 已修并部署（备份 gates.py.bak.20260613-114402）·重启后 backend=litellm·selftest 11/11·真任务实测忠实度 0.70 真值+矛盾检出（声称42万 vs 来源38.6万）。⚠️ provider 校准（2026-06-13 诊断）：代码 provider 顺序已正确（litellm 第一优先），但 **litellm(ufo2:4000) 应用层 ReadTimeout**（Tailscale 通 38ms·TCP 连得上·HTTP chat 请求 10s 无响应=ufo2 litellm cc-sonnet 路由挂起）→ 自动 fallback deepseek-chat（正常服务·便宜）。**根因在 ufo2 litellm 服务侧**（非 probe-a·非代码）。M1 deepseek 够用；M2 付费深度需 Claude 质量 → 列 infra 跟进：debug ufo2 litellm cc-sonnet 上游 |
| 2 | **数据源准入门口径** | 文档化裁定：`qualified`（采购边界·主门）· `gate_passed`（gate19 官方授权·更高合规备选·非阻塞）；`get_adapter` 对 active 源校验一致 | `registry.py` 注释 + `gate19-and-dedup` 文档 | 口径单一、无"两套门"歧义 | ✅ **已完成**（registry.py 双口径注释+实现核验）|
| 3 | **`_chat` 透出 usage** | `_chat` 返 `(text, usage)`，调用方累计 usage → 喂 cost | `llm.py` + `l0.deep_probe` + `pipeline` | cost_event 有真 token 数 | ✅ **已完成**（`_chat_with_usage` 返 (text, usage_dict) 核验）|
| 4 | **governor 统一取数入口** | 先在 pipeline/l0 凿出**唯一取数函数**（现在 article/doc 走 extractors、video/social 走 registry 两条岔路），governor 才有挂载点接管"禁绕过" | `l0` / `pipeline` + 新建 `governor.py` | 取数走唯一入口·可被治理 | ✅ **已完成**（governor.py `fetch_one(url, kind)` 核验·2026-06-12 建）|
| 5 | **metering 埋点** | 包装 llm/api 出口埋 cost_event（cost-metering 设计落码） | 新建 `metering.py` | 每次调用成本可见 | 🚧 **JSONL 已工作·PG 迁移待决**：metering.py 已建并跑 JSONL（M1 可用·成本已记录）；设计（W2-10/R28）要求 PG `probe_cost_events` 表。**实情**：probe app 当前零 PG 接线·venv 未装 psycopg → 迁 PG = 引入首个 PG 依赖（pip+DDL·半不可逆）。**非 M1 阻塞**（M1 免费档 premium=0 无计费）·服务 M2 付费计费精度 → 列为 M2 前置·不抢 M1 |
| 6 | **字段错位 / redact 死代码** | deep_probe 产七段 s1-s7 字段 → 用 `redact_by_tier`；删废弃的 `apply_depth_line` | `l0` / `guards.py` | 单一裁剪函数·字段对齐 | ✅ **LIVE（2026-06-13 probe-a 部署）**：`apply_depth_line` 已删·selftest 三档检查改走七段 redact_by_tier·重启后 selftest 11/11 不退化（备份 guards/selftest .bak.20260613-115146）|

> 新三文档（API 调取治理三件套：risk-checklist / cost-metering / data-dynamic-governance）的完整落码 = 上表 #3/#4/#5，它们要编排的 `governor.py`/`metering.py` 现不存在，需先凿挂载点（#4）才有落点。

---

## 三、S1 施工顺序（审查 ROI 排序 · 方案定稿后照此执行）

1. **把 run_audit 正式纳入 _deep + 对齐字段 + 接真 backend** —— 一次解决"护城河未真兑现"+"字段错位"（已起步验证，S1 接真 backend 完成）。
2. **裁定统一数据源放行口径，让 get_adapter 校验一致** —— 堵 E2/E3，否则接第一个源即崩。
3. **凿 governor 挂载点**（统一取数函数 + `_chat` 返 usage + 确定性自评已建）—— 让三件套从"设计闭环"变"可落地闭环"。
4. **metering 埋点 + 字段统一** —— 成本可见 + 单一裁剪。

---

## 四、母体侧依赖（M3 前置 · 不阻塞 S1 侧 1-3）

`HttpToolClient` + `identity/verify` + `registry 三维标签` —— 母体（metafoclaw 平台）侧缺口，probe 侧 selftest 自验不依赖；M3 大厅上架前需母体补齐。

---

## 五、纪律小结

- **方案制定与实现分阶段**：本清单是方案层产物；代码实现统一在方案定稿后的 S1 进行。
- **不就地补**：审查/检测发现的断层，沉淀到此清单，不在方案阶段散兵游勇改核心代码。
- **可落地性验证除外**：仅为确认设计能兑现而做的最小验证（如本次 8 闸接入），已 selftest 隔离、不影响方案，作为锚点保留。

> v1.0 定稿 2026-06-10 · **v2.0 补入 2026-06-11**（技术栈 R1-R4 调研产物·§六/§七 新增·G8 缺口关闭）。本清单随方案演进更新；S1 启动时作为施工图。

---

## 六、完整 S1 施工总表（R1-R4 技术栈调研产物 · G8 缺口关闭）

> 2026-06-11 补入 · 来源：[底座裁定卡](../4-research/techstack-cards/techstack-base-verdict-v1.0.md) + [技术栈决策总册](../4-research/techstack-decision-v1.0.md)（R4 产物·28件定案）
> 覆盖：执行包 6 条 + 断层清单 §二 + M1-M13 源卡「S1 可部署」项全量汇聚
> 唯一悬决：ufo GPU 总 VRAM 未核实（影响 M4 AIGC 精确层·已移入 §七 S2 门控）

### Wave1 · OS1 · 核心骨架（护城河真兑现 · 约 7 天）

| # | 施工项 | 来源 | L层/引擎 | 验收标准 |
|---|------|------|---------|---------|
| W1-1 | vendor · Onyx 连接器协议（BaseConnector/Load/Poll/Checkpointed 三态契约 + Document/Section · ~9模块剪枝清单显式移植）| 执行包#1 | L2 统一接口 + Core IR Document | 三态接口定义完整；Document.sections[].text 非空校验通过 |
| W1-2 | raw_content 不变量 → ledger 接入契约（sections[].text 必非空·空 sections 被 adapter 拒绝·把「不自己爬」升为数据结构层不变量）| 执行包#2 | ledger 接入规范 | 接入规范写进注释 + 空 sections 测试用例 → 拒绝通过 |
| W1-3 | MindSearch DAG schema → G1 扇出计划（node dict content/type + edge dict id/name/state 三态 · 抄成我方 dataclass · 执行层用已决 TaskGroup）| 执行包#3 | L2 扇出 DAG | G1 闭合；dataclass 可实例化 + TaskGroup 骨架可跑 |
| W1-4 | ODR 聚合器三态 + partial 字段（raw_notes / compressed_research / partial_flag · 借 open_deep_research 状态分层·不引 langgraph · PG+Redis 持久）| 执行包#5 | L2 聚合器状态 | 三态 dataclass 定义 + partial 标注逻辑通过单测 |
| W1-5 | 8 闸接真 backend（MiniCheck-T5-770M → 闸2英文 + cross-encoder/nli-deberta → 闸5英文 + Erlangshen-Roberta-110M → 中文闸2/5）| 断层#1 + M3 | L3 Validator | conclusion_label 出真实审核值；StubBackend 退役 |
| W1-6 | claim 拆解前置（Loki prompt 模板 + litellm + spaCy zh 句分割）| M3 | L3 闸前处理 | claim list 非空 → 逐条送 NLI 通过集成测试 |
| W1-7 | `_chat` 透出 usage（返回 (text, usage) · 调用方累计 usage → 喂 cost）| 断层#3 | L2 LLM 出口 | cost_event 含真实 token 数；metering 可收 |
| W1-8 | governor 统一取数入口（`fetch_one(url, kind)` 单函数 · `governor.fetch` 包装 · 原 article/doc vs video/social 两岔路合并）| 断层#4 | L1→L2 Governor | 全量取数走唯一入口；原 extract_public 两岔路消除 |
| W1-9 | 数据源准入口径统一（`qualified`=采购主门 · `gate_passed`=gate19 备选非阻塞 · `get_adapter` 对 active 源校验一致）| 断层#2 | L1 适配器 | 接第一个源不崩；口径单一无歧义注释 |

### Wave2 · OS2 · 数据管线（全路打通 · 约 7 天）

| # | 施工项 | 来源 | L层/引擎 | 验收标准 |
|---|------|------|---------|---------|
| W2-1 | docling 2.101.0（MIT · ONNX 无强制 torch）替换 markitdown（markitdown 退为备选）| M2 | L2 内容抽取 | 表格抽取精度≥95%；扫描 PDF CJK 正常 |
| W2-2 | throttled-py 3.3.1 Token Bucket per-source（S1 内存版 · S2 换 Redis 后端）| M7 | Governor 限流 | per-source 令牌桶；超限返回 429 |
| W2-3 | tenacity 9.1.4 指数退避（429/5xx · 最多 3 次 · 不死循环）| M7 | Governor 重试 | 429 自动退避；max_retries=3 通过 |
| W2-4 | circuitbreaker 2.1.3（3 次失败 → 开路 · 60s 恢复）| M7 | Governor 熔断 | 宕源开路；主流程不阻塞继续跑其他源 |
| W2-5 | presidio + 自写 CN PatternRecognizer + zh_core_web_sm（中文姓名/手机/身份证脱敏）| M10 | Guardian 脱敏 | 中文姓名 4/4 检出（默认模型 0/4 是已知坑）；sensitive 字段脱敏 |
| W2-6 | Playwright 1.60.0 Chromium pool（PDF + 图卡截图 · ≤2 async worker · fonts-noto-cjk 前置安装）| M11 | L4 渲染核心 | PDF 生成通过；图卡 screenshot 通过；CJK 无方块 |
| W2-7 | python-pptx 1.0.2（MIT · 零 C 库）PPTX 生成 | M11 | L4 渲染 | 中文字体 PPTX 正常；字体 fallback 无乱码 |
| W2-8 | matplotlib 3.10.9（PSF-BSD）静态图表 PNG（禁 emoji · 嵌 PDF/PPT）| M11 | L4 渲染 | PNG 嵌入 PDF 不报错；CJK 轴标签正常 |
| W2-9 | litellm spend PG 直读（`LiteLLM_SpendLogs` 覆盖>90%字段 · 零新存储 · LLM 面计量）| M12 | Governor 计量 | per-model per-day cost 可查；无新表 |
| W2-10 | `metering.py` 数据源 API 计量（`probe_cost_events` PG 表 · 每次 API 调用成本写表）| M12 / 断层#5 | Governor 计量 | 每次调用成本写表；可按源/天聚合 |
| W2-11 | OTel FastAPI Instrumentor + OTLP → ufo Jaeger（既有观测中枢 · 零新服务）| M12 | Governor HTTP trace | HTTP trace 在 ufo Jaeger 可见；三 pip 包安装通过 |
| W2-12 | Garage 单二进制部署于 probe-a（probe-evidence bucket + 60 天 Expiration lifecycle）| M13 | L4 对象存储 G7✓ | bucket 可读写；60 天 lifecycle 配置验证；G7 缺口关闭 |
| W2-13 | `apt install fonts-noto-cjk`（probe-a 系统字体一次安装 · Playwright/matplotlib 共享）| M11 共用 | 系统层 | 全部渲染件 CJK 字符不出方块 |
| W2-14 | STORM 视角提问提示词（视角≥3 路 → 并行对话 → 七段 s1-s7 · 纯 Claude · 不引 dspy）| 执行包#4 | L4 七段报告 | s1-s7 字段全填；视角互不重复 |
| W2-15 | 字段错位修复 + `redact_by_tier` 统一（`apply_depth_line` 扁平函数废弃 · D2 裁定落码）| 断层#6 | L4 整合 | 单一裁剪函数通过；dead code 删除；selftest 保持 |

### Wave3 · OS3 · 实体治理 + 质量闭环（约 7 天）

| # | 施工项 | 来源 | L层/引擎 | 验收标准 |
|---|------|------|---------|---------|
| W3-1 | splink 4.0.16（MIT · DuckDB→PG 10行适配）实体对齐 | M5 | L3 Orchestrator 去重 | 小样本实体匹配 precision>0.9 |
| W3-2 | datasketch 1.10.0（MIT）MinHashLSH 内容去重（中文 bigram shingling 实测通过）| M5 | L3 内容去重 | Jaccard>0.8 集合被去重；中文字符通过 |
| W3-3 | 自研 TruthDiscovery ~60 行（Li et al. CRH 变体 · 多源冲突仲裁 · 无维护库可用）| M5 | L3 真值发现 | 4 源以上冲突时仲裁出主流值；单测通过 |
| W3-4 | pgvector（平台既有）语义去重（cosine>0.95 视为重复 · 无新依赖）| M5 | L3 语义去重 | embedding + 相似度查询通过；无新装包 |
| W3-5 | DeepEval（Apache · pytest 原生 · judge 走 Claude 多代理）CI eval harness | M8 | Guardian CI | 每次 PR 跑评测；指标不退步才合并；CI 门通过 |
| W3-6 | Wikipedia-API 0.15.0（MIT）LoadConnector（sections[].text 满足不变量）| M1 | L1 连接器 | 全文正文非空；W1-2 不变量校验通过 |
| W3-7 | RSSHub 官方镜像自托管 + BLOCK_LIST（仅 A/B 级路由 · C 级屏蔽）| M1 | L1 连接器 | antiCrawler/requirePuppeteer=true 路由被 BLOCK_LIST 过滤 |
| W3-8 | feedparser（BSD-2）RSS 解析 + SearXNG（AGPL）URL 发现层 | M1 | L1 连接器 | URL 发现 → feedparser 解析端到端通过 |
| W3-9 | GPT-R 产物 schema 参考（source_urls / research_context / research_sources 三字段 → 聚合器输出 IR · 不引依赖）| 执行包#6 | L4 输出 Core IR | 聚合器输出含三字段；参考实现落码 |

---

## 七、S2 指标门清单（未进 S1 · 触发后再做）

| 件 | 来源 | 触发指标 |
|----|------|---------|
| Hatchet Lite / Procrastinate durable 队列 (M6) | M6 卡 S2门控 | P99 pending>200ms 或 completion>30s 或 2 OOM/day 或 50+活跃源>5s 任务（5条中≥3触发）|
| Fast-DetectGPT CPU 统计层 闸3-L1 (M4) | M4 卡 | ufo→probe-a Tailscale GPU 调用链就绪 |
| Binoculars 精确层 闸3-L2 (M4·需32GB VRAM) | M4 卡 ⚠️ | ufo GPU 总 VRAM 核实≥32GB；否则 INT4 量化 |
| Qwen2.5-7B LoRA 中文 AIGC (M4) | M4 卡 | ufo GPU 就绪 + 1-2 天微调排期 |
| MinerU 3.2.3 容器化 REST（中文扫描专项 · M2 B档）| M2 卡 | 中文扫描场景覆盖率需求触发 |
| inscriptis+difflib 监测雷达（M9·拆思想自研）| M9 卡 | S2 运营期·有具体监测源需求时 |
| throttled-py Redis 后端切换（M7 S2 升级）| M7 卡 | S1 内存版承压（并发>20源）|
| pyecharts/mermaid.js 交互图表（M11 B档）| M11 卡 | 对外产品交互图表需求触发（可提前 S1 末进）|
| promptfoo A/B 测试（M8 B档）| M8 卡 | B 档辅助；⚠️ OpenAI 已收购·长期中立性待观察 |

> **S1 共 33 项**（Wave1·9 + Wave2·15 + Wave3·9）· S2 指标门 9 件 · G8 缺口至此关闭。
> 本表随 S1 进展更新：✅=完成 / 🚧=进行中 / ⬜=待启动。

# probe · 引擎数据持久化与缓存层设计 v1.0

> 日期：2026-06-10 · 性质：probe 引擎**数据模型（PG 持久化）+ 缓存层（Redis）**设计真源
> 补缺口：方案设计阶段查漏 #1（引擎整体数据模型·此前只有 cost_event 单表）+ #5（缓存层架构·此前只有"缓存复用"概念散落）。是其余设计文档（评测/监测/反馈）共同引用的**数据脊柱**。
> 真源边界：本文 = probe **数据存储**真源；cost_event 字段细节仍以 [cost-metering-v1.0](probe-cost-metering-design-v1.0.md) 为准（本文引用不重定义）；源元数据 schema 仍以 [design-v1 §2.4](probe-intelligence-engine-design-v1.md) 为准。
> 约束遵从：R28 业务数据入 PG · R14 无进程内可变状态 · server-roles（probe = 非交易共用业务）· feasibility §5 红线（人物 OSINT 只即时查不落库）· R27（视频/大文件不入仓）。

---

## 〇、一句话 + 三条铁律

**【一句话】** probe 的数据分三层落位：**持久业务数据 → PG（tencent-sh 主库 `probe` schema）**；**易失高频数据（缓存/限流/任务进度）→ Redis（probe 独立实例·非交易总线）**；**大块交付物（图/HTML/PPT/视频）→ 对象存储/临时盘（不进 PG 主表）**。

**【三条铁律】**
1. **红线优先于存储**：`persist_policy` 决定一条数据能不能落库。人物 OSINT / 敏感主体 → `ephemeral`（只在内存/短 TTL 缓存流转，**禁写 PG**），违反即 P0。
2. **源无关**：所有表对具体数据源零硬编码，源信息以 `source_id` 外键引 registry（换源不改表）。
3. **缓存键带源版本**：源升级 → `source_version` bump → 相关缓存自动失效（防陈旧污染喂进结论）。

---

## 一、存储分层总览

```
┌──────────────────────────────────────────────────────────────┐
│  PG (tencent-sh 主库 · schema=probe · 持久业务数据)            │
│  任务 / 结论成品 / 源命中日志 / 断言事实 / 审核留痕 /          │
│  源可靠度 / 监测订阅 / 监测快照 / 用户反馈 / 评测金标          │
│  ✗ 不存：人物OSINT结论(ephemeral) · 大块二进制交付物           │
├──────────────────────────────────────────────────────────────┤
│  Redis (probe 独立实例 · 非 boss8001-b 交易总线 · 易失)        │
│  L1结论缓存 / L2源响应缓存 / per-source令牌桶 / 异步任务进度   │
├──────────────────────────────────────────────────────────────┤
│  对象存储 / 临时盘 (大块交付物)                                │
│  图/HTML/PPT/视频 成品 → 存 uri·PG 表只留引用(R27)             │
└──────────────────────────────────────────────────────────────┘
```

**落位裁定**（对齐 server-roles）：
- **PG**：probe 是 metafoclaw 名下非交易业务 → 数据进 tencent-sh 本地 PG，新建 `probe` schema（R28：新项目新建 DB/schema）。交易数据禁混入（T3）。
- **Redis**：probe 需自己的 Redis 做缓存/限流/任务态。**用独立实例**，禁复用 boss8001-b 交易信号总线（T4：信号 Redis 不迁移、不起第二个交易 Redis——probe 的是缓存 Redis，用途不同、实例分开，落 tencent-sh 或 ufo2）。
- **对象存储**：图/HTML/PPT/视频体积大，存对象存储或临时盘，PG 只存 `uri`（R27：视频/>10M 不入仓）。

---

## 二、PG 数据模型（schema=probe）

> 字段给核心列；`id` 统一 `bigserial` 主键，时间戳统一 `timestamptz`。每张表的 CREATE 须配 DO 块 `ADD COLUMN IF NOT EXISTS`（R27 gate_router 同步纪律），存量库不自动迁移。

### 2.1 `probe_task` — 任务（一切的锚点 · 兼"历史对比"载体）

| 列 | 类型 | 说明 |
|----|------|------|
| id | bigserial PK | 任务 ID |
| user_id | text | 用户（关联 hub identity）|
| intent | text | MetaAsk 澄清后的意图 |
| task_type | text | 27 场景之一（如 `selfmedia.link_rating`）|
| tier | text | `flash`(极速) / `deep`(深度) |
| input_material | jsonb | 输入素材（链接/图/文/名字…的引用，非大文件本体）|
| fanout_plan | jsonb | 本次扇出计划（赛道/API/DAG·orchestration 产出）|
| status | text | `queued/running/partial/done/failed` |
| **persist_policy** | text | `normal` / `ephemeral` / `sensitive`（三态真源在此·判定逻辑见 privacy §三）|
| incomplete | bool | 是否 partial 交付（超预算/降级）|
| delivery_format | text | `text/img/html/ppt/video` |
| total_cost | numeric | 累计成本（汇总 cost_event）|
| created_at / completed_at | timestamptz | |

> **三态说明**：`normal` = 常规业务数据可持久落库；`ephemeral` = 人物 OSINT / 高频易失数据，仅在内存/短 TTL 缓存流转、**禁写 PG**；`sensitive` = PIPL 特殊类型/人物 OSINT，留存 ≤ 60 天、禁出境（承接 privacy 的 sensitive 档），由 Guardian 和 `persist_policy` 留存门联合执行。

> "历史对比"= 按 `user_id` 索引 task + conclusion，无需独立表；同主体多次任务做 diff。

### 2.2 `probe_source_hit` — 源命中日志（每次取数一行 · 喂可观测+成本+飞轮）

| 列 | 类型 | 说明 |
|----|------|------|
| id / task_id(FK) | | |
| source_id / api_id | text | 引 registry（源无关）|
| latency_ms | int | 本次时延（喂对冲 defer 窗标定）|
| outcome | text | `success/degraded/failed/timeout` |
| hit_cache | bool | 是否缓存命中（喂缓存命中率）|
| cost | numeric | 本次调用成本（付费源）|
| raw_ref | text | 原始响应在 Redis/对象存储的引用（非本体）|
| created_at | timestamptz | |

### 2.3 `probe_claim` — 归一化断言/事实（真值发现的输入·实体对齐后）

| 列 | 类型 | 说明 |
|----|------|------|
| id / task_id(FK) | | |
| entity_key | text | 实体规范化键（实体对齐去重后）|
| claim | text | 断言内容 |
| value | jsonb | 值 |
| source_ids | text[] | 支持此断言的源（保留全部出处→溯源闸）|
| confidence | numeric | 真值发现加权后置信 |
| freshness_ts | timestamptz | 信息时点（喂时效衰减）|
| **persist_policy** 继承 task | | ephemeral 任务此表不落 |

### 2.4 `probe_conclusion` — 结论成品（七段报告+三标签）

| 列 | 类型 | 说明 |
|----|------|------|
| id / task_id(FK) | | |
| conclusion_block | jsonb | conclusion_block（GEO/对外）|
| seven_section | jsonb | 七段报告 s1-s7 |
| conclusion_label | jsonb | 三标签（置信/证据等级/Admiralty）|
| incomplete | bool | 标"未全验"|
| geo_publishable | bool | 是否可 GEO 分发 |
| created_at | timestamptz | |

> ⚠️ `persist_policy=ephemeral` 的任务：**不写本表**，结论仅经 API 即时返回后丢弃（人物 OSINT 红线）。

### 2.5 `probe_artifact` — 交付物/作品库（大块走对象存储）

| 列 | 类型 | 说明 |
|----|------|------|
| id / task_id(FK) | | |
| format | text | text/img/html/ppt/video |
| uri | text | 对象存储/临时盘地址（PG 不存本体·R27）|
| bytes | bigint | 大小 |
| created_at / expires_at | timestamptz | 留存周期由隐私设计定 |

### 2.6 `probe_source_reliability` — 源可靠度（真值发现先验+在线更新·飞轮落点）

| 列 | 类型 | 说明 |
|----|------|------|
| source_id PK | text | |
| reliability | numeric | 当前可靠度（0-1）|
| prior | numeric | Admiralty 分级喂的冷启动先验 |
| sample_count | int | 累计样本（喂收敛稳定性）|
| updated_at | timestamptz | |

> 这是 truth discovery 冷启动护栏的存储：先验来自 registry 的 Admiralty 评级；用户反馈（§ 2.8）在线修正。

### 2.7 `probe_monitor_subscription` / `probe_monitor_snapshot` — 监测雷达（B6/C4·详见监测设计文档）

`subscription`：id · user_id · target · schedule(cron) · last_run · status · diff_rule
`snapshot`：id · subscription_id(FK) · snapshot(jsonb) · captured_at（供 diff 检测）
> 字段与状态机详见 [monitoring-radar-and-feedback-loop](probe-monitoring-radar-and-feedback-loop-design-v1.0.md)，本文只登记表归属。

### 2.8 `probe_feedback` — 用户反馈纠错（闭环·回调源可靠度）

| 列 | 类型 | 说明 |
|----|------|------|
| id / conclusion_id(FK) / user_id | | |
| kind | text | `confirm/dispute/correct` |
| payload | jsonb | 纠正内容 + 指向的源 |
| applied | bool | 是否已回调 source_reliability |
| created_at | timestamptz | |
> 闭环逻辑详见监测/反馈设计文档，本文登记表。

### 2.9 `probe_eval_goldenset` — 评测金标（质量评测·详见评测文档）

`id · task_type · input · expected(jsonb) · rubric(jsonb) · tier · created_at`
> 供回归基准/质量度量，字段与用法见 [quality-eval-methodology](probe-quality-eval-methodology-v1.0.md)。

### 2.10 `probe_cost_event` — 成本事件（已有·引用不重定义）

字段以 [cost-metering-v1.0](probe-cost-metering-design-v1.0.md) 的 cost_event schema 为准；`task_id` FK 关联本模型。

### 2.11 `probe_audit_trace` — 闸0过程留痕 + 8闸结果

`id · task_id(FK) · gate(闸号) · verdict · evidence_ref(Langfuse/OpenLLMetry 链接) · created_at`
> 重型 trace 本体在 Langfuse（Wave1 T-C），PG 只存指针 + 闸结论。

---

## 三、Redis 缓存层设计（probe 独立实例）

> 本文 §三 = **数据缓存**（L1 结论/L2 源响应）真源；渲染产物缓存（HTML/图片/视频等交付物的 CDN/临时盘层）是独立第三层，真源在 delivery §七，两者不混淆。

### 3.1 两层缓存（命中率 vs 时效的分级）

| 层 | 键 | 值 | TTL 策略 | 失效 |
|----|----|----|---------|------|
| **L1 结论缓存** | `concl:{hash(归一化query + tier + 涉及源版本集)}` | conclusion 引用 | 按信息域分级（百科 τ 长/舆情 τ 短）| query 命中且未过期直接返回 |
| **L2 源响应缓存** | `src:{source_id}:{source_version}:{hash(params)}` | 原始响应 | 按源时效分级 | `source_version` bump 自动失效 |

- **键含 `source_version`**（铁律 3）：源升级即旧键作废，不会喂陈旧数据进结论。
- **ephemeral 任务**：L1 结论缓存**不写**（人物 OSINT 不留痕）；L2 源响应缓存可短 TTL（即时查的中转），但带 `ephemeral` 标记、TTL ≤ 任务生命周期。

**档位/用户隔离硬化（K4 · 2026-06-10 自 [risk-checklist](probe-api-fetch-risk-checklist-v1.0.md) 入库）**：
1. **L1 键含 `tier`（上表已有）= 跨档隔离的唯一保证**——禁任何"省存储"优化把 tier 从键里拿掉；变更此键结构 = 高 blast，必过 review。
2. **L2 源响应缓存有意不含 tier**：原始源数据本身无档位属性，跨档共享是省成本的正确行为——但**前提是交付前必经 `redact_by_tier` 裁剪**（guards.py），L2 数据禁直达用户。
3. **幂等/在途复用必带 tier 校验**：编排器去重复用在途任务结果时（[orchestration](probe-orchestration-engine-solution-v1.0.md) 扇出去重），必须比对请求 tier ≤ 在途任务 tier，禁止免费请求搭车复用付费深探在途结果。
4. **含用户私有输入的任务**（上传文档/私有上下文）：L1 键追加 `user_id` 维度或直接不写共享缓存——公共链接查询才可跨用户共享。

### 3.2 限流计数（per-source 令牌桶）

`ratelimit:{source_id}` → token-bucket（Lua 原子）。单机 S1 阶段可先用进程内 `asyncio.Semaphore`，升 S2 分布式时切 Redis（对齐 [orchestration §3.6](probe-orchestration-engine-solution-v1.0.md)）。

### 3.3 异步任务进度（深度版）

`task:{id}:progress` → 增量合成进度（流式聚合的"证据在增长"前端可读）。TTL = 任务完成后短时保留。

### 3.4 缓存与成本/治理的联动

缓存命中 = 不调用外部 API = 省成本，是 [data-dynamic-governance](probe-data-dynamic-governance-design-v1.0.md) 的「缓」分支落点；命中/未命中写 `probe_source_hit.hit_cache`，喂缓存命中率看板。

---

## 四、与现有体系接口

| 接面 | 关系 |
|------|------|
| orchestration-engine-solution | 编排器读写 task/fanout_plan/source_hit/缓存/限流；本文是其持久化底座 |
| cost-metering | cost_event schema 真源；本模型 FK 关联 |
| audit-system 8闸 | claim/conclusion/audit_trace 是闸的输入输出落点 |
| source registry（feasibility）| 所有 source_id 外键引此（源无关）|
| 隐私留存设计 | persist_policy / expires_at / ephemeral 红线的执行依据 |
| 监测/反馈/评测设计 | subscription/snapshot/feedback/goldenset 表归属此模型 |

---

## 五、落地（并入 S1·OS1 同期）

- S1 建 `probe` schema + 核心 5 表（task/source_hit/claim/conclusion/source_reliability）→ 撑 M1。
- 监测/反馈/评测/artifact 表按对应功能上线时建（不一次性全建）。
- 每表 CREATE 配 DO 块 ADD COLUMN（R27）；建表脚本走 tencent-sh PG，`.bak` 先备份（R0.6）。

---

> 落盘：probe/docs/3-build/probe-data-persistence-and-cache-design-v1.0.md
> 性质：数据脊柱设计（决策已定）· 闭缺口 #1+#5 · 待并入 master-solution-v2 §七

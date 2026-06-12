# probe · 多赛道并发编排引擎 · 最终解决方案 v1.0

> 日期：2026-06-10 · 性质：probe 编排/调度层**最终解决方案**（决策已定，可据此落地）
> 输入：需求规格 [orchestration-concurrency-requirements-v1.0](probe-orchestration-concurrency-requirements-v1.0.md)（本文为其解）+ 深度调研（5 路扇出·23 条证伪存活·2 条已证伪剔除）
> 真源边界：本文 = probe **编排/调度层**架构与选型真源；数据源引 feasibility-v1，审核引 audit-system-v1，档位引 speed-depth-tiering-v1.0，成本引 source-selection / cost-metering / data-dynamic-governance。
> 证据分级标注：✅**已证伪验证**（调研三票存活，带一手出处）｜📐**标准工程实践**（业界通行，调研抓到来源但未进 top-25 验证集，按通行做法采用）｜⚠️**待标定/调研未覆盖**（诚实标注，落地时实测回填）。

---

## 〇、方案一句话 + 七项已定决策

**【一句话】** probe 的编排层 = 一个 **Scatter-Gather（扇出-聚合）内核**：把单个情报任务按元数据驱动展开成多赛道·多 API 的并发扇出，用**带超时预算的聚合器**边到边合成，慢源不阻塞、付费源不浪费，多源冲突用**真值发现**而非多数票消解——**先单机异步，撑不住再升 durable 队列**。

**【七项已定决策】**（不再反复议，前提变才重提）

| # | 决策点 | 已定方向 | 依据 |
|---|--------|---------|------|
| D1 | 编排架构 | **Scatter-Gather 模式**为内核，**不上** Airflow/Temporal 做单请求扇出 | ✅ EIP / AWS |
| D2 | 并发原语 | **asyncio.TaskGroup + asyncio.timeout**（py3.11+）/ anyio 双超时语义 | ✅ PEP 789 / AnyIO |
| D3 | 结果合成 | **聚合器三态完成条件**（全等待/首达/固定超时）+ partial 显式标注 | ✅ EIP / AWS / SearXNG |
| D4 | 尾延迟 | **反应式对冲**（仿 Envoy·仅超时触发）·**免费源开 / 付费源禁** | ✅ Tail at Scale / Envoy / gRPC |
| D5 | 多源融合 | **真值发现迭代**（源可靠度×一致性）+ 时效衰减项 + 实体对齐 | ✅ Li et al. survey（时效/对齐为📐补强） |
| D6 | 分布式限流 | **集中式 Redis token-bucket + Lua 原子** per-source + 429 退避 + 熔断 | 📐 标准实践 |
| D7 | 队列演进 | **S1 单机 asyncio → S2 durable 队列（Hatchet 候选）**，按指标门升级 | ✅ Hatchet docs（临界点为⚠️待标定） |

---

## 一、调研结论速览（带出处）

### ✅ 已证伪验证（23 条存活的核心 6 组）

1. **Scatter-Gather 是教科书级正解**（EIP / AWS Prescriptive Guidance）。AWS 明确把「聚合多个 API 数据成一个准确响应」「优化涉及多数据源的复杂查询」列为本模式的 exact use case，并规定「配置超时忽略过慢响应 + 告知客户端结果不完整」。SearXNG 生产实现：per-source `request_timeout` 默认 2.0s，`max_request_timeout` 上限 10.0s——慢源直接被丢出结果而非阻塞整查询。

2. **结构化并发正解 = TaskGroup + timeout**（PEP 789 / AnyIO）。AnyIO 两个超时原语语义不同：`move_on_after()` 超时**静默退出**（best-effort 部分结果）、`fail_after()` 超时**抛 TimeoutError**（硬失败）——编排器按任务挑策略。取消一个 cancel scope 会级联取消所有嵌套 scope 并立即中断 IO 等待——这正是"一个超时分支取消其余兄弟扇出"的机制。**关键坑**：async generator + cancel scope 会取消**错误的任务**（症状 `Attempted to exit cancel scope in a different task`），禁止把 TaskGroup/timeout 放进会跨 yield 的异步生成器。

3. **尾延迟会被扇出放大，对冲是解药**（Dean & Barroso, The Tail at Scale, CACM 2013）。单组件 p99=1s，并发收 100 台 → **63% 用户请求 >1s**。对冲：第一请求超过 95 分位预期时延后才发副本 → 额外负载约 +5%。BigTable 实测：10ms 后发对冲，**p99.9 从 1800ms 降到 74ms，仅多 2% 请求**。Tied requests（双副本互相取消）median −16%、p99.9 −40%、磁盘开销 <1%。

4. **生产对冲两种范式**（gRPC / Envoy）。gRPC 用 `hedgingDelay` 当成本旋钮（不设 = maxAttempts 个请求**同时齐发**，最贵模式）。Envoy 是**反应式**：仅 per-try 超时才触发对冲，**不取消**原请求、保留多个在飞、取第一个"good"响应——天然契合"只对慢尾巴对冲"的省钱诉求。**已证伪剔除**：「gRPC 并行齐发再取消败者」是错的——gRPC 默认按 delay 错峰、不自动取消败者。

5. **多源冲突用真值发现而非多数票**（Li et al., A Survey on Truth Discovery, KDD 2016）。多数票假设所有源等可靠，是错误默认。真值发现估计每源可靠度再加权，**能选出少数派正确值**（"少数派智慧"）。核心是**迭代两步循环**：用当前源权重算真值 → 用当前真值反估源权重 → 收敛为止。**已证伪剔除**：「TruthFinder 是唯一正解」——它只是该族一个实例，**survey 级迭代原理**才是稳妥推荐。

6. **撑不住单机就上 durable 队列**（Hatchet docs）。Hatchet 用 Postgres 做唯一持久层（易自托管），支持 per-source/per-user **动态限流**（CEL 表达式按 input/metadata 取 key），存全量执行历史，压测 ~10k tasks/s（厂商数据·硬件相关·<100 req/s 推荐纯 PG）。对比：Celery/BullMQ 用 durability 换吞吐。**决策律**：要吞吐+复用 Redis → Celery/Dramatiq/Arq；要可回放历史+内建动态 per-source 限流+易运维 → Hatchet（接受更高单任务资源开销）。

### ⚠️ 调研未覆盖（诚实标注，本文用📐标准实践补，落地实测）

- **DP4** Celery/Arq/Dramatiq/Temporal 全量横评——只有 Hatchet vs Celery/BullMQ 存活，其余按通行认知给（见 §3.7）。
- **DP5** 单机 asyncio 并发临界点的**具体指标阈值**——无存活声明，本文给监控门思路但**阈值留⚠️待压测**（见 §3.8）。
- **DP7** 分布式限流机制选型 / 429 退避 / 熔断阈值——无 top-25 存活声明（调研抓到 slashid / callr Redis+Lua / api7 / ayrshare 四篇但未进验证集），本文按📐标准实践给（见 §3.6）。
- **DP6** 实体对齐/去重 + 时效衰减——survey 只证了"可靠度×一致性"，时效与对齐为📐补强。

---

## 二、probe 编排引擎总架构

```
                       ┌──────────────────────────────────────────┐
   一句话需求/素材 ──▶ │  MetaAsk 意图 → 任务类型 + 档位 + 交付规格   │
                       └──────────────────────────────────────────┘
                                         │
                   ┌─────────────────────▼─────────────────────┐
                   │  ① 任务编译器  Task Compiler                │  元数据驱动
                   │  场景模板 + 源 registry → 扇出计划(DAG)      │  (非硬编码)
                   └─────────────────────┬─────────────────────┘
                                         │ scatter
         ┌───────────────┬───────────────┼───────────────┬───────────────┐
         ▼               ▼               ▼               ▼               ▼
     赛道1(搜索)      赛道2(百科)      赛道3(代码)      赛道4(新闻)      赛道N(付费)
     ├ API a          ├ API d          ├ API f          ├ API h          ├ API j
     ├ API b          └ API e          └ API g          └ API i          (禁对冲·过成本门)
     └ API c        ②结构化并发扇出 TaskGroup + per-node 超时预算 + 反应式对冲(仅免费源)
         └───────────────┴───────────────┬───────────────┴───────────────┘
                                         │ gather (流式·边到边)
                   ┌─────────────────────▼─────────────────────┐
                   │  ③ 聚合器  Aggregator                       │  完成条件三态:
                   │  归一化 → 实体对齐去重 → 真值发现合成        │  全等待/首达/固定超时
                   │  → 超时预算到 → 出 partial(标"未全验")       │
                   └─────────────────────┬─────────────────────┘
                                         │
                   ┌─────────────────────▼─────────────────────┐
                   │  L3 审核 8 闸  +  L4 整合(七段报告)          │
                   └────────────────────────────────────────────┘

  横切设施: 集中式 Redis 限流(per-source token-bucket) · 分级缓存 · 可观测打点 · cost 门
  运行形态: S1 单机 asyncio(极速版同步) ←指标门→ S2 durable 队列(深度版异步)
```

**一句话**：编排器 = **任务编译器（元数据→扇出计划）+ 结构化并发扇出 + 聚合器（流式合成）**三件套，横切挂限流/缓存/可观测/成本门，运行形态按负载在单机异步与 durable 队列间演进。

---

## 三、核心机制设计（8 决策点 → probe 落地）

### 3.1 编排内核：Scatter-Gather + 元数据驱动扇出（D1）

- **✅ 不为单请求扇出上重型工作流引擎**。Airflow/Dagster/Prefect 是面向"定时批处理 DAG / 数据管道"的，调度延迟以秒计、有调度器开销；probe 单请求扇出要的是**毫秒级派发 + 进程内低延迟**——用 Scatter-Gather + asyncio 即可。重型引擎只在"跨任务、需持久编排历史"时才考虑（→ §3.7 升 durable 队列，而非 Airflow）。
- **元数据驱动扇出计划**：任务编译器读「场景模板（选哪些信息域）× 源 registry（每域有哪些 API + 能力/时延档/成本/限流组/可否对冲）」，**生成本次扇出计划**——换源/换模板只改声明，编排器零改（落实 L1-L4 源无关铁律）。
- **依赖建模**：扇出计划是浅 DAG——绝大多数赛道**独立**（直接并发）；少数有依赖（"先搜索拿实体 ID → 再查实体详情"）按拓扑分两波，**波间不设硬 barrier，就绪即推进**（pipeline）。

### 3.2 结构化并发：TaskGroup + 超时预算（D2）

- **✅ 主原语**：`asyncio.TaskGroup`（一个子任务抛错自动取消其余兄弟，强于 `gather`）+ `asyncio.timeout` 做预算。需要"超时取部分结果不抛错"时用 **AnyIO `move_on_after()`**；需要"超时即判失败"用 **`fail_after()`**。
- **超时预算下放**：任务总预算（按档位）→ 切给各赛道节点（按时延档）。节点超预算 → cancel scope 级联中断其 IO，**不无限等**。
- **✅ 必避的坑（PEP 789）**：禁止把 TaskGroup/timeout scope 放进"跨 yield 的 async generator"——会取消错误任务。probe 的流式聚合若用异步生成器吐结果，**生成器内部不得再开 cancel scope**；扇出与 yield 分层（扇出在 TaskGroup 内完成，结果经 queue 交给外层生成器吐出）。
- **单赛道失败隔离**：每个赛道任务用 `try/except` 包裹，失败 → 记"该维度缺失"，不抛出拖垮 TaskGroup（用 `return_exceptions` 等价语义：收集异常而非传播）。

### 3.3 流式增量合成：聚合器三态（D3）

- **✅ 完成条件是设计旋钮**（EIP）：
  - **全等待**（≈ `gather`）：合成必须看全集时（全局去重/排序）——仅深度版关键波次用。
  - **首达**（≈ `wait first`）：多等价源取最快（配合 3.4 对冲）。
  - **固定超时预算**（≈ 默认）：到点即合成已到结果，慢源**后补增量更新**。
- **partial 必须显式标注**（AWS：「告知客户端结果不完整」）——对齐极速版"诚实标注未全验"铁律：超预算交付时结论带 `incomplete: true` + 缺失维度列表。
- **边到边合成**：结果到一个并入一个（增量），前端可见"证据在增长"；不等整波。
- **超时锚 SearXNG 真值**：per-source 默认 2.0s、硬上限 10.0s 作为初始档（⚠️ probe 按自己源时延分布压测重标，见 §六 T1 目标）。

### 3.4 尾延迟优化：反应式对冲（D4）★ 成本敏感

- **✅ 为什么必须做**：probe 扇出 N 源，单源慢尾会被放大成整任务慢尾（100 源 p99=1s → 63% 任务 >1s）。
- **✅ 采用 Envoy 反应式模型，不用 gRPC 齐发模型**：仅当某源**超过其 per-try 超时**才补发对冲到等价源，取首个 good 响应——只为慢尾巴付代价，而非全员齐发。
- **✅ 免费源开 / 付费源禁**（核心成本纪律）：对冲会乘倍请求量。
  - **免费源/自托管源**（SearXNG/Wikimedia/GDELT 等）：开对冲，defer 窗设在该源 ~95 分位时延（额外负载 ~+5%）。
  - **付费/计量源**（DataForSEO/天眼查/Keepa）：**禁对冲**（多发 = 多花钱），改用"单发 + 超时降级到免费等价源"。
  - **非幂等调用**：禁对冲。
- 与 §3.6 限流联动：对冲补发也走 per-source 令牌桶，不破配额。

### 3.5 多源融合与冲突消解：真值发现（D5）

- **✅ 弃多数票，用真值发现迭代**：归一化后对同一断言，按"源可靠度 × 一致票数"加权，**保留少数派**（高可靠单源可压过多数低质源）。迭代两步：算真值 → 反估源权重 → 收敛。
- **✅ 冷启动护栏**（survey caveat）：首轮源可靠度用 registry 预置先验（Admiralty 源分级喂初值），**不让算法把自己早期错误共识当真值**；对"全体一致但可疑"的源簇加警示（喂 8 闸·矛盾闸/抗污染闸）。
- **📐 时效衰减项**（survey 未覆盖，补强）：在可靠度权重上叠 `freshness = exp(-Δt/τ)`，τ 按信息域定（百科 τ 长、舆情 τ 短）——舆情类新源压过陈旧源。
- **📐 实体对齐/去重**（survey 未覆盖，补强）：合成前先做记录链接（实体规范化 + 别名归并 + 模糊匹配），同一实体跨源合并、保留全部出处（喂溯源闸）。
- **与 8 闸的分工**：真值发现是 L4 合成内的**加权机制**，最终真假判定仍过 L3 八闸 + 对抗证伪——融合给"加权草稿"，闸给"可信度标签"。

### 3.6 分布式限流与配额（D6）📐 标准实践

> 调研此点无 top-25 存活声明，以下按业界通行做法定，落地实测校准。

- **集中式 Redis + Lua 原子令牌桶**（per-source）：每个外部 API 一个令牌桶 key，多 worker 共享；用 Lua 脚本保证"取令牌+判额"原子，避免竞态。这是跨进程/跨机限流的通行解（单机 asyncio 阶段可先用进程内 `asyncio.Semaphore`，升分布式时换 Redis）。
- **双层限流**：① 全局并发上限（防打满本机/出口）② per-source QPS + 日配额（防单源 429）。
- **429 退避**：指数退避 + 抖动（`base * 2^n + rand`），尊重 `Retry-After` 头；**不硬重试**。
- **熔断**：单源连续失败/限流超阈 → 本任务内熔断降级到等价源/缓存，半开探测恢复。
- **付费源前置成本门**：调用前过 cost 门（对齐 source-selection / cost-metering），超预算降级或停。

### 3.7 任务队列演进：单机 → durable（D7）

- **✅ S1 起点 = 单机 asyncio**（无队列）。极速版本来就是"秒级同步出结果"，进程内协程扇出延迟最低、零运维。**不要一上来上 Celery/Hatchet**（过早分布式税）。
- **✅ S2 升级触发 = 出现以下任一**：需要**可回放执行历史**（深度版尽调要审计轨迹）/ 需要**跨 worker 动态 per-source 限流** / 需要**可靠重试与降级编排** / 单机吞吐触顶（见 §3.8）。
- **队列选型**（⚠️ 全量横评调研未覆盖，按存活证据 + 📐通行认知）：

| 队列 | 持久层 | 适配 probe 点 | 取舍 |
|------|--------|--------------|------|
| **Hatchet**（✅推荐候选）| Postgres | 内建动态 per-source/per-user 限流·全量执行历史·易自托管 | 单任务资源开销高·<100 req/s 推荐纯 PG·厂商 v1 演进快⚠️ |
| Celery | Redis/RabbitMQ | 生态最成熟·复用 Redis | 📐执行后不留历史·限流需自建 |
| Dramatiq | Redis/RabbitMQ | 比 Celery 轻·中间件清爽 | 📐生态小·功能少 |
| Arq | Redis | asyncio 原生·轻·复用 Redis | 📐功能最小·无内建限流 |
| Temporal | 自有/DB | 持久工作流·强一致 | 📐重·学习曲线陡·适合长流程非短扇出 |

- **probe 建议**：S2 首选评估 **Hatchet**（per-source 动态限流 + 可回放历史正中深度版尽调要害，且 Postgres 与 probe 业务库同栈）；若届时吞吐压力大于审计需求，退 **Arq**（asyncio 原生 + 复用 Redis 缓存实例）。⚠️ 决策落地前做一次真实负载小压测对比。
- **Hatchet 限流坑**（✅ docs）：多步骤渲染出**相同 CEL key 会塌缩成一个全局限流**——per-source key 设计必须显式带 source_id。

### 3.8 单机→分布式临界点（D5/部分）⚠️ 待压测

> 调研无存活阈值声明。下为**监控门设计**，阈值压测回填。

- **"先单机后分布式"是合理默认**（IO 密集 = 协程吃满即可），但**不盲目坚持**——挂以下指标，触门才升 S2：
  - **事件循环延迟**（event-loop lag）：单次迭代滞后持续 > ⚠️_X_ ms（协程被饿）。
  - **打开连接数 / fd**：接近进程上限或出口连接池饱和。
  - **CPU 单核饱和**：asyncio 单进程吃满一核（合成/解析变 CPU 密集时尤其）→ 先 `loop.run_in_executor` 卸载，仍满则多 worker。
  - **出口带宽 / DNS**：大响应聚合打满出口。
- **横向扩第一步往往是多进程（同机多 worker）而非跨机**；跨机分布式留给"就近付费源/抗封出口池"的地域瓶颈（对齐需求 R8.2 S3）。

---

## 四、轻量 → 重量 技术栈演进阶梯（★ 核心交付）

| 阶段 | 形态 | 编排 | 并发 | 限流 | 队列/持久 | 对冲 | 适用 | 升级触发 |
|------|------|------|------|------|----------|------|------|---------|
| **S0 雏形** | 单进程同步 | 手写串行 | 无 | 无 | 无 | 无 | demo 验证逻辑 | 一有并发需求即升 |
| **S1 单机异步**（✅起点）| 单进程 asyncio | Scatter-Gather + 浅 DAG | TaskGroup+timeout | `asyncio.Semaphore`(进程内) | 无(内存态) | 反应式·仅免费源 | 极速版同步·中小并发 | §3.8 任一指标门触发 |
| **S2 单机异步+durable 队列**（主力）| asyncio + Hatchet/Arq | 同上·任务入队 | 同上 | Redis 集中式 token-bucket | Postgres(Hatchet)/Redis(Arq) | 反应式·成本门约束 | 深度版异步·可回放·跨 worker 限流 | 地域时延/出口封禁瓶颈 |
| **S3 就近分布式** | 多区 worker 池 + 中心合成 | 中心编排·就近采集 | 各 worker asyncio | 全局 Redis + 区域子桶 | 同 S2 | 反应式·跨区 | 海外付费源就近·抗封 IP 池 | 规模化后再评估 |

**铁律**：**S1 起步，按指标门逐级升，不跳级、不为未到规模预付复杂度税。** 单任务内永远是 asyncio 扇出（低延迟）；S2/S3 加的是"任务间"的持久、限流、就近——任务内并发模型不变。

---

## 五、与 probe 现有体系的接口

| 接面 | 关系 | 说明 |
|------|------|------|
| MetaAsk | 上游 | 给任务类型+档位+交付规格 → 决定扇出计划深浅 |
| 源 registry（feasibility-v1）| 输入 | 提供赛道→API 映射 + 能力/时延/成本/限流/可否对冲元数据 → 编译扇出计划 |
| **L2 采集层** | **本体** | 本编排器**就是** L2「多源并发扇出」的实现内核 |
| L3 审核 8 闸（audit-system-v1）| 下游/内嵌 | 真值发现给加权草稿 → 8 闸定真假与可信标签；聚合器把闸排进合成波 |
| L4 整合 | 下游 | 接收归一化+对齐+加权后的中间表示 → 七段报告 |
| speed-tiering-v1.0 | 参数源 | 档位 → 超时预算/并发深度/对冲开关/是否走 S2 异步 |
| source-selection / cost-metering / data-governance | 横切 | per-source 限流取其能力目录；付费源对冲/调用过成本门 + Data Governor 五信号 |
| MetaFlow | 上游编排 | 本编排器作为 probe 引擎内部 L2 调度；对外仍只走 L1 四暗号契约（R22 不直连）|

---

## 六、落地 Sprint 规划

| Sprint | 目标 | 产出 | 成本 |
|--------|------|------|------|
| **OS1 编排内核** | Scatter-Gather + 元数据驱动扇出计划 + TaskGroup 超时预算 + 单赛道失败隔离 | `app/orchestrate/` 内核·极速版同步扇出可跑 | 零(单机) |
| **OS2 流式合成 + 反应式对冲** | 聚合器三态 + partial 标注 + 免费源反应式对冲（付费源禁）+ 进程内 Semaphore 限流 | 慢源不阻塞·尾延迟实测下降 | 零 |
| **OS3 多源融合** | 真值发现迭代 + 时效衰减 + 实体对齐去重 + 冷启动先验喂值 | 多源冲突加权合成·喂 8 闸 | 零 |
| **OS4 分布式化（按需）** | Redis 集中式 token-bucket + 429 退避 + 熔断 + 评估升 Hatchet/Arq（小压测对比）| S2 形态·深度版异步+可回放 | 低(Redis 复用) |

> OS1-OS3 全零成本单机可回滚，与 master-solution Wave1-3 同期并行；OS4 对齐 Wave4 编排接入。

---

## 七、诚实边界（R0.8）

- **调研未覆盖、本文按📐标准实践给的**：DP4 队列全量横评、DP5 单机临界点具体阈值、DP6 实体对齐/时效项、DP7 限流机制细节——这些**落地时实测校准**，不当已验证结论引用。
- **待标定初值**：超时预算（SearXNG 2.0s/10.0s 仅作起点）、对冲 defer 窗（按各源 95 分位）、熔断阈值、S1→S2 指标门——全部压测回填。
- **厂商数据**：Hatchet 10k tasks/s 为厂商自报（硬件相关），选型前独立小压测。
- **已证伪剔除（勿采信）**：① "gRPC 齐发再取消败者"——错，默认错峰不取消；② "TruthFinder 是唯一正解"——只是真值发现族一实例。

---

## 附 · 关键出处

- Scatter-Gather：[Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/BroadcastAggregate.html) · [AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/scatter-gather.html)
- 联邦检索超时：[SearXNG outgoing settings](https://docs.searxng.org/admin/settings/settings_outgoing.html)
- 结构化并发：[PEP 789](https://peps.python.org/pep-0789/) · [AnyIO cancellation](https://anyio.readthedocs.io/en/stable/cancellation.html)
- 尾延迟/对冲：[Dean & Barroso, The Tail at Scale (CACM 2013)](https://cacm.acm.org/research/the-tail-at-scale/)
- 生产对冲：[gRPC request hedging](https://grpc.io/docs/guides/request-hedging/) · [Envoy router filter](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter) · [Envoy #5841](https://github.com/envoyproxy/envoy/issues/5841)
- 真值发现：[Li et al., A Survey on Truth Discovery (arXiv:1505.02463)](https://arxiv.org/pdf/1505.02463)
- durable 队列：[Hatchet](https://github.com/hatchet-dev/hatchet) · [Hatchet rate limits](https://docs.hatchet.run/home/rate-limits)
- 📐限流参考（未进验证集）：slashid id-based rate limiting · callr Redis+Lua · api7 rate limiting guide · ayrshare 429 handling

---

> 落盘：probe/docs/3-build/probe-orchestration-engine-solution-v1.0.md
> 性质：最终解决方案（决策已定）· 解需求规格 v1.0 · 待并入 master-solution-v2 §四/§七

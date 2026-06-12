# 技术源卡 M6 · S2 durable 队列（候选复核·不重开内核）

> 需求真源：orchestration-solution D7（冻结：S1 asyncio Scatter-Gather → S2 按指标门升级 durable 队列）· 喂缺口 G1
> checked_at: 2026-06-11 · 方法：WebSearch + GitHub/PyPI/docs 实拉，禁凭记忆

---

## 候选实测

### 1. Hatchet（hatchet-dev/hatchet）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/hatchet-dev/hatchet |
| license | **MIT（100% 开源，官方明文"100% MIT-licensed"）** |
| stars | **7.3k** |
| 最近活跃 | **v0.89.0 · 2026-06-10**（昨天；Python SDK v1.33.7 · 2026-06-09）|
| self-host 资源需求 | Hatchet Lite = 单 Docker 镜像 `ghcr.io/hatchet-dev/hatchet/hatchet-lite:latest`；无官方明文 RAM 规格；实测社区反馈约 **512MB–1GB** RAM（含 bundled PG 的 gRPC+Web UI+引擎）；CPU 轻负载下 0.1–0.5 core |
| 存储依赖 | **PostgreSQL only**（Lite 内置 PG 15.6 或接外部 `DATABASE_URL`）；**不需要 Redis**；可复用 probe 已有 PG ✅ |
| Python + asyncio SDK | **hatchet-sdk v1.33.7**（PyPI 稳定版）；Python ≥3.10；`async def` task 直接装饰；Pydantic 输入输出；活跃维护 |
| 可回放支持 | ✅ **Durable event log 全量持久化**；`"every task…is stored in a durable event log and ready to be replayed"` 官方文档明文；Web UI 可手动 replay 任意 run |
| 已知限制 | 连接池泄漏（issue #3694：gRPC LISTEN 通道重连时泄漏 pool slots）；L7 proxy idle timeout 截断 stream（#3280，Envoy/Azure 环境）；Python SDK 仍无 APIRouter 式注册模式（#3502）|
| checked_at | 2026-06-11 |

---

### 2. arq（python-arq/arq，原 samuelcolvin/arq）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/python-arq/arq |
| license | MIT |
| stars | **2.9k** |
| 最近活跃 | v0.28.0 · 2026-04-16；但 **issue #510 明确标注"maintenance only mode"**（no new features）|
| self-host 资源需求 | 零额外进程——纯 Python 库；worker 进程本身；Redis 需已有 |
| 存储依赖 | **Redis only**（无 PG）；probe 已有 Redis ✅；但无 PG 持久化 |
| Python + asyncio SDK | ✅ 核心就是 asyncio-based；API 简洁 |
| 可回放支持 | ❌ **无内置 replay**；job result 存 Redis 短 TTL；历史不可查；无 durable log |
| 关键缺陷 | maintenance-only 意味着不会新增 replay/durable 能力；Redis-only 无 PG 持久层 |
| checked_at | 2026-06-11 |

---

### 3. taskiq（taskiq-python/taskiq）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/taskiq-python/taskiq |
| license | MIT |
| stars | **2.2k** |
| 最近活跃 | v0.12.4 · 2026-05-08；仓库 2026-05-30 更新 |
| self-host 资源需求 | 零额外进程；多 broker 插件按需装 |
| 存储依赖 | Redis（taskiq-redis）/ RabbitMQ / NATS / Kafka；**无原生 PG broker**；需第三方插件或自写 |
| Python + asyncio SDK | ✅ 原生 full async；FastAPI / AioHTTP 集成 |
| 可回放支持 | ❌ 未发现内置 replay 能力；result backend 存结果但无 durable event log |
| 关键缺陷 | 无 PG backend（probe 若不想加 RabbitMQ/NATS 则存储依赖不匹配）；无 replay |
| checked_at | 2026-06-11 |

---

### 4. dramatiq

| 字段 | 值 |
|------|-----|
| repo | https://github.com/Bogdanp/dramatiq |
| license | LGPL-3.0 |
| stars | ~4.5k（文档引用 v2.1.0）|
| 最近活跃 | v2.1.0 changelog 引用；2026-01 博客文章引用 |
| 存储依赖 | Redis 或 RabbitMQ；PG 支持靠 `dramatiq-pg` 第三方包（非官方）|
| Python + asyncio SDK | ⚠️ 通过可选 `AsyncIO` middleware 支持 async；1 thread/worker 跑 event loop，非原生 |
| 可回放支持 | ❌ 无内置 replay；消息消费即删除 |
| license 风险 | **LGPL-3.0** — 若 probe 代码与其动态链接需注意传播条款（使用层面一般可接受，但不如 MIT 干净）|
| checked_at | 2026-06-11 |

---

### 5. SAQ（tobymao/saq）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/tobymao/saq |
| license | MIT |
| stars | **860** |
| 最近活跃 | v0.26.4 文档；PyPI 最近 release 2026-01-08 |
| self-host 资源需求 | 零额外进程；依赖 Redis 或 PG |
| 存储依赖 | **Redis（RedisQueue）或 PostgreSQL（PostgresQueue）** — 两者 API 一致可切换；probe 已有两者 ✅✅ |
| Python + asyncio SDK | ✅ **asyncio-native 设计**；延迟 <5ms（低于 arq）|
| 可回放支持 | ⚠️ 有 requeue 机制（stuck job sweeper、fail vs cancel 区分）；但**无 Hatchet 级 durable event log**；replay 需手动重入队 |
| 关键优势 | 极轻量；PG+Redis 双 backend 无需加新存储；asyncio 性能好 |
| 关键缺陷 | 860 stars（社区小）；无内置 replay UI；无工作流 DAG 支持 |
| checked_at | 2026-06-11 |

---

### 6. Procrastinate（procrastinate-org/procrastinate）——补充候选

| 字段 | 值 |
|------|-----|
| repo | https://github.com/procrastinate-org/procrastinate |
| license | MIT |
| stars | **1.3k** |
| 最近活跃 | v3.8.1 · 2026-04-08；仓库 2026-06-09 活跃 |
| self-host 资源需求 | 零额外进程；纯 PG 驱动 |
| 存储依赖 | **PostgreSQL only（PG 13+）**；`LISTEN/NOTIFY` + `SELECT FOR UPDATE SKIP LOCKED` 实现队列；不需要 Redis ✅（只用已有 PG）|
| Python + asyncio SDK | ✅ 原生 async；推荐 async 模式；psycopg3 async 原生支持 |
| 可回放支持 | ✅ **手动 retry 支持**（`procrastinate retry <job_id>`）；job state machine（TODO/DOING/SUCCEEDED/FAILED/CANCELLED/ABORTED）；stalled job 检测+自动重入队；job history 在 PG 表持久化 |
| 关键优势 | **纯 PG，零新依赖**；job history 天然落 PG 持久；stalled-job 自动 retry；MIT |
| 关键缺陷 | 无 Web UI（需接入外部监控）；无 DAG 工作流；PG LISTEN/NOTIFY 在极高并发下有扩展瓶颈；文档指出"需要 real monitoring tools 才算生产就绪" |
| checked_at | 2026-06-11 |

---

## Hatchet 健康度复核结论

**结论：Hatchet 仍是 S2 最强候选，但资源开销是主要顾虑。**

| 维度 | 2026-06-11 复核结果 | 结论 |
|------|-------------------|------|
| license | MIT ✅ 官方明文 | 无变化，健康 |
| 活跃度 | v0.89.0 昨日（2026-06-10）release；Python SDK v1.33.7 前天 release | 极活跃 ✅ |
| self-host 资源 | Hatchet Lite 单镜像；无官方规格；社区反馈 ≥512MB；引入 Go 控制平面进程 | ⚠️ 比轻量库重，但有 Lite 模式可接受 |
| 存储依赖 | PostgreSQL only，无 Redis 依赖；可直接复用 probe 已有 PG | ✅ 完美契合 |
| Python SDK 成熟度 | v1.33.7 生产稳定；Pydantic 集成；async def 原生支持 | ✅ 成熟 |
| 可回放 | Durable event log + Web UI replay，业界最完整 | ✅ |
| 已知风险 | gRPC 连接池泄漏（#3694）；L7 proxy stream 截断（#3280）；probe 部署在 boss8001-a 受 Tailscale 保护，无 L7 proxy，#3280 风险低 | ⚠️ #3694 需监控但不致命 |

**对 probe 场景的额外评估**：probe 的 S2 升级触发条件是"单机 asyncio 撑不住"，即任务量大到需要多 worker + 持久化 + 可观测。Hatchet 的强项（durable log + replay + PG-only）与 probe 需求高度匹配。Lite 模式的内存开销（~512MB）在专用节点 probe-a（已有独立机器）上可接受。

---

## S2 指标门草案

> S1 → S2 升级的可测量触发阈值建议（任一命中即触发评估，3 条同时命中建议升级）

| 指标 | 阈值 | 测量方式 |
|------|------|---------|
| **TaskGroup 积压深度** | 持续 >200 pending tasks（10 min 滚动均值）| asyncio queue `qsize()` 监控 + Prometheus gauge |
| **任务完成延迟 P99** | >30s（单次采集任务从入队到完成）| `time.monotonic()` 首尾打点；Prometheus histogram |
| **Worker OOM/崩溃频率** | >2 次/天（asyncio worker 进程因内存 OOM 重启）| systemd restart count；`/proc/<pid>/status VmRSS` |
| **可回放需求出现** | 任意一次需要重跑历史 run（debug/数据补采）且无法靠重入队解决 | 主观触发：运营需求 |
| **并发源数量** | 活跃数据源 >50 个且深度版异步任务耗时 >5s/个 | `SELECT COUNT(DISTINCT source_id) FROM probe_jobs WHERE status='active'` |

**建议**：S2 评估会议门槛 = 以上 5 条任意 **3 条同时触发**，触发后走 EG-2 评估+元东方授权再升级，不自动升级。

---

## tech-gate 12 闸速查表

> 针对 S2 核心需求：durable + 可回放 + 复用已有 PG 或 Redis（不加第三个存储）+ asyncio + 自托管可行

| 闸 | 问题 | Hatchet | SAQ | Procrastinate | arq | taskiq |
|----|------|:---:|:---:|:---:|:---:|:---:|
| G1 | 开源许可证可商用（MIT/Apache）？ | ✅ MIT | ✅ MIT | ✅ MIT | ✅ MIT | ✅ MIT |
| G2 | Python ≥3.10 兼容？ | ✅ | ✅ | ✅ 3.10+ | ✅ | ✅ |
| G3 | asyncio 原生支持？ | ✅ | ✅ | ✅ | ✅ | ✅ |
| G4 | 复用已有 PG（无需加新存储）？ | ✅ PG-only | ✅ PG backend 可选 | ✅ PG-only | ❌ Redis-only | ❌ 无 PG broker |
| G5 | 复用已有 Redis（无需加新存储）？ | ❌ 不用 Redis（但 PG 已有即满足 G4）| ✅ Redis 主 backend | ❌ 不用 Redis | ✅ Redis-only | ✅ |
| G6 | G4 或 G5 至少一个满足（不加第三存储）？ | ✅ | ✅ | ✅ | ✅ | ⚠️ 需 RabbitMQ/NATS |
| G7 | Durable job 持久化（重启不丢任务）？ | ✅ event log | ✅ PG/Redis 持久 | ✅ PG 持久 | ⚠️ Redis TTL 短 | ⚠️ 取决于 broker |
| G8 | 可回放（replay/retry 历史 run）？ | ✅ Web UI replay | ⚠️ 手动重入队 | ✅ `retry` CLI + job history | ❌ | ❌ |
| G9 | 工作流 DAG / 多步骤编排？ | ✅ 内置 DAG | ❌ 单任务 | ❌ 单任务 | ❌ | ❌ |
| G10 | 自托管资源合理（单节点可运行）？ | ✅ Lite ~512MB | ✅ 零进程 | ✅ 零进程 | ✅ 零进程 | ✅ 零进程 |
| G11 | 社区活跃（2026 内有 release）？ | ✅ 2026-06 | ✅ 2026-01 | ✅ 2026-04 | ✅ 2026-04（但 maintenance-only）| ✅ 2026-05 |
| G12 | S2 升级路径清晰（S1 asyncio 兼容）？ | ✅ Python SDK 渐进迁移 | ✅ drop-in worker | ✅ 渐进迁移 | ⚠️ 架构差异大 | ⚠️ broker 切换代价 |

**全 12 闸通过**：Hatchet 11/12（G5 不用 Redis 但 G4+G6 覆盖）、Procrastinate 10/12（G5 不用 Redis、G9 无 DAG）、SAQ 9/12（G8 弱、G9 无 DAG）

---

## verdict

### S2 首选：Hatchet Lite

**档位：A — 有条件推荐，优先**

| 维度 | 评分 | 理由 |
|------|------|------|
| 与 D7 决策对齐度 | ★★★★★ | D7"durable + 可回放"需求 Hatchet 覆盖最全；PG-only 精准复用 probe 已有存储 |
| 工程成本 | ★★★☆☆ | Lite 引入额外 Docker 服务；gRPC SDK 学习曲线；#3694 连接池泄漏需监控 |
| 未来扩展 | ★★★★★ | DAG 编排、AI Agent 工作流、分布式 worker 开箱即用；路线图与 probe 演进方向一致 |
| S1→S2 迁移路径 | ✅ | S1 asyncio task 改造为 Hatchet `@hatchet.task()` 装饰，逐步迁移 |

**部署建议**：probe-a 节点；`docker compose` 起 Hatchet Lite + 复用已有 PG；Python worker 进程独立部署。

---

### S2 备选 A：Procrastinate

**档位：A- — 极轻量 PG-only，适合"不想运行额外服务"场景**

| 优势 | 缺陷 |
|------|------|
| 零新服务：只用已有 PG，无 Docker 额外进程 | 无 Web UI；无 DAG；高并发 LISTEN/NOTIFY 有扩展瓶颈 |
| MIT；3.8k commit 活跃；replay CLI 支持 | 文档坦言监控工具尚不完善 |
| PG job history 天然持久；stalled job 自动检测 | 无 Hatchet 级可观测性 |

**适用场景**：S2 升级触发但任务量中等（<1000 任务/分钟）、不需要 DAG、团队希望零运维额外服务时优先。

---

### S2 备选 B：SAQ

**档位：B+ — 轻量 asyncio，适合"只需 Redis 持久化、不要额外服务"场景**

| 优势 | 缺陷 |
|------|------|
| asyncio-native；延迟极低（<5ms）；PG+Redis 双 backend | 860 stars 社区小；replay 弱；无 DAG |
| 零新服务；MIT | 无 durable event log；长期维护不确定 |

---

### 不推荐

| 候选 | 原因 |
|------|------|
| arq | maintenance-only；Redis-only；无 replay；不符合 S2 durable 需求 |
| taskiq | 无 PG broker；无 replay；需引入 RabbitMQ/NATS 等第三存储 |
| dramatiq | LGPL-3.0（license 不如 MIT 干净）；async 非原生；无 replay |

---

### 决策树（快速判断）

```
S2 触发指标门命中 →
  是否需要 DAG 工作流编排？
    ✅ 是 → Hatchet（唯一选项）
    ❌ 否 →
      是否接受运行额外 Docker 服务（~512MB RAM）？
        ✅ 是 → Hatchet（replay UI + 可观测性最完整）
        ❌ 否 →
          已有 PG 为主？ → Procrastinate（零新服务）
          已有 Redis 为主？ → SAQ（轻量快速）
```

---

## 顺手发现

1. **Hatchet v1 分拆**：repo `hatchet-dev/hatchet-v1` 是历史版本归档，当前主线为 `hatchet-dev/hatchet`（v0.89.x）；PyPI `hatchet-sdk` 已到 v1.33.7，版本号体系不同步，勿混淆。

2. **arq 迁移至 python-arq 组织**：原 `samuelcolvin/arq` 已移至 `python-arq/arq`（Pydantic 组织接管），但 issue #510 确认 maintenance-only 状态，feature freeze，不适合 S2。

3. **SAQ 的 PostgresQueue 是较新功能**：SAQ 的 PG backend 在 0.20+ 版本引入，文档中 Redis 仍是一等公民，PG backend 文档较薄；引入前建议验证 PostgresQueue 在高并发下的行为。

4. **Procrastinate 的 PG LISTEN/NOTIFY 扩展限制**：单 PG 实例 LISTEN/NOTIFY channel 在高并发（>500 workers）时有广播风暴风险；probe S2 初期不会触碰此边界，但 S3+ 扩展时需留意。

5. **Hatchet #3694 连接池泄漏对 probe 的影响评估**：泄漏发生于 gRPC LISTEN 通道重连时；probe-a 通过 Tailscale 内网访问 Hatchet，网络稳定，重连频率低；但仍建议部署时设置 PG `max_connections=100` 并监控 `pg_stat_activity` 连接数。

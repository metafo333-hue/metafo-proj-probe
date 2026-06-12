# 技术源卡 M12 · 成本/可观测

> 需求真源：cost-metering（双本账·cost_event） · 已有：litellm✅（ufo2 自托管·PG 在役）+ 机3 OTel 中枢✅（Jaeger+Prometheus+Grafana） · 喂缺口 G6
> checked_at: 2026-06-11 · 实测方式：现场 WebSearch + WebFetch 源码/文档级验证

---

## 候选实测

### 1. litellm spend tracking（已在役·LLM 计量面）

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/BerriAI/litellm |
| **license** | MIT（proxy 核心）|
| **stars** | ~38.9k |
| **最近活跃** | 持续高频，2026-06 仍在活跃发版 |
| **存储依赖** | PostgreSQL（已接：ufo2:5432/litellm 共享库，57 张表已建） |
| **与已有栈集成路径** | ✅ 已在役。tencent-sh:5432/litellm + ufo2:4000 + ufo:4000 双 proxy 共享同一 DB，spend logs 已真实落表验证（[[project_litellm_prisma_db_20260527]]） |
| **checked_at** | 2026-06-11 |

**LiteLLM_SpendLogs 完整字段（现场 schema.prisma 实测）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| request_id | String (PK) | 请求唯一 id |
| call_type | String | 调用类型（completion/embedding 等）|
| api_key | String | virtual key |
| spend | Float | 本次 USD 消耗 |
| total_tokens | Int | 总 token 数 |
| prompt_tokens | Int | 输入 token |
| completion_tokens | Int | 输出 token |
| startTime / endTime | DateTime | 请求时间窗口 |
| request_duration_ms | Int? | 时延 ms |
| model | String | 模型名 |
| model_id / model_group | String? | 路由组 |
| custom_llm_provider | String? | provider 标识（deepseek/qwen/anthropic…）|
| api_base | String? | 实际命中端点 |
| user / end_user | String? | 用户标识 |
| metadata / request_tags | Json? | 自定义维度 |
| cache_hit / cache_key | String? | 缓存状态 |
| team_id / organization_id | String? | 团队/组织 |
| status | String? | success/fail |
| session_id / agent_id | String? | 会话/Agent 归属 |
| messages / response | Json? | 请求响应原文（可选存储）|

**聚合表**（日汇总，已存在于共享 DB）：
- `LiteLLM_DailyUserSpend` · `LiteLLM_DailyTeamSpend` · `LiteLLM_DailyTagSpend` · `LiteLLM_DailyAgentSpend` · `LiteLLM_DailyOrganizationSpend` · `LiteLLM_DailyEndUserSpend`

---

### 2. OpenLLMetry / traceloop（LLM 链路 trace 层）

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/traceloop/openllmetry |
| **license** | Apache-2.0 |
| **stars** | ~7.2k |
| **最近活跃** | v0.61.0 发布 2026-05-31，持续维护 |
| **存储依赖** | ❌ **零存储依赖** — 纯 OTel exporter 层，自己不存数据、不起 DB，只往下游 OTel backend 推 spans |
| **与已有栈集成路径** | ✅ 直接接机3 Jaeger。配置一行：`Traceloop.init(app_name="probe", otlp_endpoint="100.64.0.8:4317")` 即走 OTLP/gRPC 推 Tailscale 内网 ufo Jaeger。支持 Anthropic/OpenAI/LangChain 等 LLM provider 自动 instrument。 |
| **checked_at** | 2026-06-11 |

**限制**：只做 LLM 调用的 trace（token/latency/model），不做数据源 API 调用计数（非 LLM 面）。不自带 UI，依赖 Jaeger/Grafana 看图。

---

### 3. Arize Phoenix（LLM 专用观测 UI + eval，轻量替代 Langfuse）

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/Arize-ai/phoenix |
| **license** | ⚠️ **Elastic License 2.0 (ELv2)** — 非 OSI 开源。**关键判定：内部自托管使用完全允许**（官方文档明确："Self-hosting on your own infrastructure is free and fully permitted"）；禁止场景 = 把 Phoenix 作为服务提供给第三方用户，probe 内部使用不触发。 |
| **stars** | ~10.1k |
| **最近活跃** | v17.3.0 发布 2026-06-10，极活跃 |
| **存储依赖** | ✅ **无需 ClickHouse**。仅 SQLite（默认，无需配置）或 PostgreSQL（生产推荐）。本栈已有 PG，直接可用。 |
| **与已有栈集成路径** | 部署：`docker run -p 6006:6006 arizephoenix/phoenix:latest`（单容器）+ 环境变量接 PG：`PHOENIX_SQL_DATABASE_URL=postgresql://...`。接机3 PG 或 tencent-sh PG 均可。OTel span 接收：Phoenix 内置 OTLP endpoint（port 4317），probe FastAPI 侧 `FastAPIInstrumentor` + OTel SDK 双发即可（Jaeger + Phoenix 同时收）。 |
| **checked_at** | 2026-06-11 |

**优势**：内置 LLM eval UI（prompt/response 浏览、trace 树、打分）。支持 OpenInference（最广泛 LLM OTel 语义约定）。
**劣势**：ELv2 许可虽内部可用，但若 probe 未来对外提供观测即服务则触发限制。独立进程多一个服务要管。

---

### 4. OpenTelemetry Python SDK + FastAPI auto-instrument（基础链路层）

| 维度 | 内容 |
|------|------|
| **package** | `opentelemetry-instrumentation-fastapi==0.63b1`（2026-05-21）+ `opentelemetry-exporter-otlp-proto-grpc==1.39.1` |
| **license** | Apache-2.0 |
| **存储依赖** | ❌ 零依赖，纯 SDK + exporter |
| **Jaeger 支持** | ✅ Jaeger 原生支持 OTLP（port 4317 gRPC / 4318 HTTP）。机3 ufo Jaeger 已在役，直接推。 |
| **与已有栈集成路径** | 两行启用：`FastAPIInstrumentor.instrument_app(app)` + 设 `OTEL_EXPORTER_OTLP_ENDPOINT=http://100.64.0.8:4317`（Tailscale 内网到 ufo）。零侵入。 |
| **checked_at** | 2026-06-11 |

---

### 5. OpenMeter（API 通用计量 · 否决）

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/openmeterio/openmeter |
| **license** | Apache-2.0 |
| **stars** | ~2.0k |
| **存储依赖** | ❌ **重型**：PostgreSQL + **ClickHouse** + Kafka，生产部署走 Kubernetes。 |
| **与已有栈集成路径** | 不适配。ClickHouse + Kafka 违反本卡「不引新重型存储」约束。 |
| **结论** | ❌ 否决 |
| **checked_at** | 2026-06-11 |

---

## litellm spend 对账小节

### LiteLLM_SpendLogs → cost_event 映射可行性

| cost_event 字段 | litellm 来源字段 | 可行性 |
|-----------------|-----------------|--------|
| call_id | `request_id` | ✅ 直接映射 |
| task_id | `metadata->task_id`（自定义注入）| ✅ 通过 metadata 透传 |
| user_id | `end_user`（hash 后）| ✅ 需 hash 处理守 R2 |
| surface | 固定 `"llm"`（litellm 侧只记 LLM 面）| ✅ |
| source_id | `custom_llm_provider` | ✅ 直接映射 |
| units | `{input_tokens: prompt_tokens, output_tokens: completion_tokens}` | ✅ |
| unit_cost | 反推：`spend / total_tokens`（或 litellm 内部单价表）| ⚠️ 需额外查 litellm 内部 cost_per_token |
| cost_real | `spend`（Float USD）| ✅ 直接映射 |
| billed | probe 自有 billing.py 结果（不在 litellm 表里）| ⚠️ 需 probe 侧注入 |
| status | `status`（success/fail）| ✅ |
| cache_hit | `cache_hit`（String "True"/"False"，需转 bool）| ✅ |
| latency_ms | `request_duration_ms` | ✅ |
| ts | `startTime` | ✅ |

**结论**：LiteLLM_SpendLogs 与 cost_event 高度重叠，**LLM 面的计量账可以直接读 litellm 共享 DB 取数，无需重复埋点**。缺口仅两处：
1. `unit_cost` 需从 litellm 内部 model_prices_and_context_window.json 取真实单价（或直接用 `spend/tokens` 反算）
2. `billed`（用户侧计费结果）需 probe 侧注入 metadata 再关联

**数据源 API 面（非 LLM）** litellm 完全无记录 → 必须由 probe 自研 `cost_event` 覆盖，这是 metering.py 的唯一不可替代部分。

**双本账对账流程**：
```
litellm_db.LiteLLM_SpendLogs (LLM 计量真源)
    ↓ 夜间 ETL / 按需查
probe_cost_events (统一视图·含数据源 API + LLM 两面)
    ↓ 日聚合
probe_cost_daily (看板·熔断信号)
```

---

## OTel 接入最短路径

### FastAPI auto-instrument → Tailscale → ufo Jaeger 链路草案

```
probe FastAPI (probe-a:8000)
  │
  │  pip install:
  │    opentelemetry-instrumentation-fastapi==0.63b1
  │    opentelemetry-exporter-otlp-proto-grpc==1.39.1
  │    opentelemetry-sdk
  │
  ├─ FastAPIInstrumentor.instrument_app(app)   # 零侵入，HTTP 进出自动 trace
  │
  └─ OTLPSpanExporter(endpoint="100.64.0.8:4317", insecure=True)
           │
           │  Tailscale 内网 (probe-a 100.64.0.5 → ufo 100.64.0.8)
           │
           ▼
     ufo Jaeger :4317 (OTLP gRPC，已在役)
           │
           ▼
     Grafana (ufo :3000，已在役) — Jaeger datasource 接入
```

**配置最简形式（probe app/main.py 头部）**：
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = TracerProvider()
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="100.64.0.8:4317", insecure=True))
)
trace.set_tracer_provider(provider)
FastAPIInstrumentor.instrument_app(app)
```

**+ LLM trace（OpenLLMetry 叠加，可选）**：
```python
from traceloop.sdk import Traceloop
Traceloop.init(app_name="probe", otlp_endpoint="100.64.0.8:4317")
# 自动 instrument anthropic/openai/litellm 调用，token/latency 随 HTTP span 一同送 Jaeger
```

**注意事项**：
- ufo Jaeger 经 Tailscale 100.64.0.8，probe-a 已入 headscale fleet（[[project_fleet_health_check_20260610]]），网络可达
- `insecure=True` 在 Tailscale 内网可接受（非公网暴露）
- BatchSpanProcessor 异步批发，不阻塞请求路径
- Prometheus metrics 已由 ufo 机3 scrape probe-a node_exporter，HTTP 请求级 span 则由 Jaeger 补全

---

## tech-gate 12 闸速查表

| 闸 | 问题 | 结论 |
|----|------|------|
| **G12-1** | litellm spend log 能否直接用作 LLM 计量真源？ | ✅ 是。字段覆盖度 >90%，task_id 通过 metadata 注入，无需重复埋点 |
| **G12-2** | 数据源 API 面（非 LLM）有无现成件？ | ❌ 无。litellm 不记 API req。OpenMeter/Lago 需引 ClickHouse/Kafka。**cost_event 自研是最短路径** |
| **G12-3** | OTel FastAPI auto-instrument 成熟度？ | ✅ 成熟。v0.63b1（2026-05-21），一行接入，Jaeger 原生 OTLP 支持 |
| **G12-4** | 到 ufo Jaeger 的网络路径有无阻断？ | ✅ Tailscale 内网可达。probe-a(100.64.0.5)→ufo(100.64.0.8):4317 |
| **G12-5** | LLM trace 专用语义（token/model/prompt）有无现成件？ | ✅ OpenLLMetry Apache-2.0，零存储依赖，一行接 Jaeger，stars 7.2k 活跃 |
| **G12-6** | Langfuse 轻量替代的存储开销？ | Phoenix: SQLite/PG，无 ClickHouse ✅。但 ELv2 许可，内部用可，商用需复查 |
| **G12-7** | Phoenix 许可是否阻断内部使用？ | ✅ 内部自托管完全许可（官方明确），只禁作托管服务对外销售 |
| **G12-8** | 新引存储系统数量？ | **零新存储**：仅 pip 包（SDK/exporter），全用已有 PG + Jaeger + Prometheus |
| **G12-9** | cost_event 落库守规？ | 需守 R28（业务数据入 PG）+ R27（ADD COLUMN IF NOT EXISTS）+ R-EHW（cron 写三锁）|
| **G12-10** | Prometheus 与 OTel 如何并存？ | 互补不冲突：Prometheus 做系统指标（CPU/mem/disk·machine3 全 fleet scrape），OTel trace 做请求级链路；Grafana 接两个 datasource |
| **G12-11** | 是否需要独立 UI（Phoenix）还是 Jaeger+Grafana 够？ | 取决于需求：trace/latency 看 Jaeger 够；若需 LLM prompt/response 浏览+eval UI 才加 Phoenix |
| **G12-12** | 双本账对账流程锁定？ | ✅ LLM 面读 litellm_db；数据源 API 面自研 metering.py；夜间 ETL 汇总进 probe_cost_daily |

---

## verdict

### 组合定案（三档）

**档位 A · 必做（S1 施工）**：

| 组件 | 角色 | 行动 |
|------|------|------|
| litellm_db.LiteLLM_SpendLogs | LLM 计量账真源 | 直接读，不重复建表 |
| probe `metering.py`（自研） | 数据源 API 计量账（唯一不可替代部分）| 新建 `@meter` 装饰器 + `probe_cost_events` PG 表 |
| OTel FastAPI Instrumentor | HTTP 请求 trace（latency/status/路由）| 3 包 pip install + 5 行 init 代码 |
| OTel OTLP exporter → ufo Jaeger | Trace 后端（已在役）| 零新服务，配 endpoint 即可 |

**档位 B · 推荐（S2 按需）**：

| 组件 | 角色 | 条件 |
|------|------|------|
| OpenLLMetry（traceloop） | LLM 调用级 trace（token/model/prompt span）| 若需 Jaeger 中看 LLM 调用详情，叠加一行 `Traceloop.init()` |
| Arize Phoenix | LLM prompt/response 浏览 + eval UI | 若需人工复查 LLM 输出质量；单容器部署接已有 PG |

**档位 C · 否决**：

| 组件 | 原因 |
|------|------|
| OpenMeter | ClickHouse + Kafka，违反零新重型存储约束 |
| Langfuse self-host | ClickHouse 强依赖（v3 架构），M8 卡已判 P0 不引 |
| Lago / Flexprice | billing platform 过重，probe 自研 cost_event 已满足 |

### 落矩阵格

**Governor（成本/可观测）**：A 档必做 + B 档 S2 可选。观测链路最短路径 = OTel FastAPI Instrumentor（3 包）→ Tailscale → 已有 ufo Jaeger，**零新服务、零新存储、5 行代码**。成本计量 = litellm DB 读（LLM 面）+ probe metering.py（API 面）双源汇入 probe_cost_daily。

---

## 顺手发现

1. **litellm_db 已有 6 张 DailyXxxSpend 聚合表**：`LiteLLM_DailyTagSpend` 支持 request_tags 维度聚合，probe 可通过注入 `request_tags={"task_id": ..., "source_id": ...}` 零改 litellm 本体即得 per-source LLM 日维度汇总，可直接驱动 Q3 成本看板的 LLM 面，减少 ETL 工作量。
2. **OpenLLMetry 2026-03 被 Dynatrace 收购**（Traceloop team 并入 Dynatrace）：项目维持 Apache-2.0 并继续独立，收购方表态"继续支持多 provider 含 Claude"，但长期维护风险上升一档——若 S2 引入 OpenLLMetry，应设季度健康检查 cron。
3. **Phoenix `phoenix-evals` 子包是 Apache-2.0**（主包是 ELv2）：若只需 eval 功能不需 Phoenix UI，可单独引 `pip install arize-phoenix-evals`，许可更干净。

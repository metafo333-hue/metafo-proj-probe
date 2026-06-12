# 技术源卡 M8 · 质量评测 harness

> 需求真源：quality-eval 方法论 · 喂缺口 G8 · judge=纯Claude多代理（冻结）
> checked_at: 2026-06-11 · 实测方式：现场搜索 + 官方文档抓取

---

## 候选实测

### 1. Ragas

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/vibrantlabsai/ragas |
| **license** | Apache-2.0 |
| **stars** | ~14.3k |
| **最近活跃** | v0.4.3 发布 2026-01-13，维护正常 |
| **judge 可插拔证据** | ✅ 完全可插拔。`llm_factory("claude-3-5-sonnet", client=Anthropic(...))` 直接支持；内置 LLM Adapters 支持 Anthropic/Bedrock/LiteLLM/Groq/Mistral。使用 `instructor` 库实现结构化输出，judge 模型随时换。 |
| **CI 集成方式** | pytest 兼容；可在 GitHub Actions 中 `pip install ragas` 后直接 import 跑批量 eval，无原生 CI runner 但集成标准 pytest 流程可做回归门 |
| **self-host 依赖** | 无服务端依赖，纯 Python 库，本地/CI 直跑；若接 Langfuse 观测则需 Langfuse（见下） |
| **hands_on** | 文档实测：`llm_factory` + `from anthropic import Anthropic` 示例完整，可用 |
| **PII 合规** | 数据不离本地，全量本地跑，✅ 零 PII 风险 |

---

### 2. DeepEval (Confident AI)

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/confident-ai/deepeval |
| **license** | Apache-2.0 |
| **stars** | ~16.1k |
| **最近活跃** | "Opus 4.8: Day 0 Support" 发布 2026-05-28，高度活跃 |
| **judge 可插拔证据** | ✅ 完全可插拔。继承 `DeepEvalBaseLLM`，实现 `get_model_name / load_model / generate / a_generate` 四方法即可接任意 LLM。官方文档提供 Claude (`from anthropic import Anthropic` + `instructor.from_anthropic`) 完整示例，无模型限制。 |
| **CI 集成方式** | ✅ 一流。pytest 原生集成（`assert_test()`）；GitHub Actions 直接 `deepeval test run`；内置 `pass_rate / avg_score / p50/p90/p95_score` 回归门阈值断言；阈值可配置（默认 0.5，可自定义）。 |
| **self-host 依赖** | 纯 Python 库，本地/CI 直跑；云平台 Confident AI 可选（不强依赖）；数据不强制上云 |
| **hands_on** | 文档实测：CI 集成文档完整，pytest 示例可复用 |
| **PII 合规** | 不登录 `deepeval login` 则数据不上云，✅ 本地跑 PII 安全 |

---

### 3. promptfoo

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/promptfoo/promptfoo |
| **license** | MIT |
| **stars** | ~22.1k |
| **最近活跃** | v0.121.15 发布 2026-06-05，极活跃 |
| **judge 可插拔证据** | ✅ 完全可插拔。YAML 中 `defaultTest.options.provider: anthropic:messages:claude-sonnet-4-5-20250929` 即可；支持断言级单独覆盖 provider；CLI `--grader` 参数实时切换；支持 vLLM 本地 judge。 |
| **CI 集成方式** | ✅ 一流。官方 GitHub Actions action；JUnit XML 输出原生接 CI 测试视图；`--fail-on-error` 退出码控门；JSON 输出可解析 pass rate 做阈值门；artifact 存档比较历史回归。 |
| **self-host 依赖** | 纯 Node.js CLI，SQLite 本地存储；可 Docker 部署；无外部数据库强依赖 |
| **hands_on** | 实测：YAML 配置语法清晰，`anthropic:messages:claude-*` 直接可用 |
| **PII 合规** | 本地运行，数据不外发，✅ 合规 |
| **注意** | ⚠️ 2026-03-09 OpenAI 收购 promptfoo，MIT 许可承诺维持但长期中立性存疑；官方表态继续支持多 provider 含 Claude |

---

### 4. Langfuse（self-host）

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/langfuse/langfuse |
| **license** | MIT（核心）+ EE 功能有商业限制 |
| **stars** | ~13k+ |
| **最近活跃** | v3.x，2025 年 ClickHouse 架构迁移完成，持续活跃 |
| **judge 可插拔证据** | ✅ 支持自定义 judge 模型。LLM-as-a-Judge 评估器可配置任意 LLM Connection（含 Claude Sonnet/GPT-4o/Gemini Pro）；与 Ragas 合作内置评估器库；支持 SDK 自定义代码评估器回写 Score |
| **CI 集成方式** | ⚠️ 非原生 CI eval 框架。面向观测/追踪平台；dataset experiments 可批量跑，但无 pytest 原生门；需配合 SDK 脚本写回归逻辑 |
| **self-host 依赖** | ❌ **重。v3 强制 ClickHouse**（见下节详述）+ PostgreSQL + Redis/Valkey + S3/MinIO，6 容器；最低 4 vCPU / 8GB RAM / 100GB 磁盘 |
| **hands_on** | ClickHouse 冷启动 >1 分钟，整体 docker compose up 约 6 容器 |
| **PII 合规** | 自托管可控，但架构复杂度高；traces 存 ClickHouse，需运维保障 |

---

### 5. Arize Phoenix

| 维度 | 内容 |
|------|------|
| **repo** | https://github.com/Arize-ai/phoenix |
| **license** | ⚠️ **Elastic License 2.0 (ELv2)** — 非 OSI 认证开源，禁止作为托管服务对外提供 |
| **stars** | ~10.1k |
| **最近活跃** | v17.3.0 发布 2026-06-10，活跃 |
| **judge 可插拔证据** | ✅ 模型无关（via LiteLLM 适配器）；支持 ClassificationEvaluator / 自定义 LLMEvaluator；内置 Anthropic 适配器；多模型多维度 judge 可并发 |
| **CI 集成方式** | ⚠️ 无官方 pytest 原生 CI gate；需通过 SDK 拉取 eval 结果脚本化断言；tracing 强项，eval-gate 弱项 |
| **self-host 依赖** | 相对轻：单容器 `pip install arize-phoenix` 或 Docker；无 ClickHouse 强依赖；SQLite/PostgreSQL 可选 |
| **hands_on** | 本地 `phoenix serve` 即可跑 |
| **PII 合规** | 自托管合规，但 ELv2 许可需法务确认内部使用边界 |

---

## langfuse self-host 依赖核实（ClickHouse 真假·最新版架构）

**结论：ClickHouse 是 Langfuse v3 的强制依赖，坑属实，且比 MetaLearn 调研时更重。**

| 组件 | 必须/可选 | 说明 |
|------|-----------|------|
| **ClickHouse ≥24.3** | **必须** | OLAP 存储 Trace/Observation/Score，无法跳过；≥25.5.2 版本有极端内存 bug，建议固定 25.5.2 |
| **PostgreSQL** | 必须 | 元数据事务库 |
| **Redis / Valkey** | 必须 | 队列 + 缓存 |
| **S3 / MinIO** | 必须 | 事件持久化 + 文件上传 |
| **Langfuse Web 容器** | 必须 | 主应用 |
| **Langfuse Worker 容器** | 必须 | 异步处理 |

**资源下限**：4 vCPU / 8 GB RAM / 100 GB 磁盘（6 容器 docker compose）。  
ClickHouse 冷启动超 1 分钟，存储随 trace 量增长约 1–2 GB / 百万条。

**与 MetaLearn 调研坑一致**：ClickHouse 强依赖确认，v2→v3 迁移不可逆，不可降级回 PostgreSQL-only。

---

## 组合方案（eval 库用 X + 观测用 Y · 与 M12 cost/litellm 的边界）

### 推荐方案 A：DeepEval（eval harness）+ 轻量 Langfuse-lite 或无观测

```
probe CI 流：pytest + deepeval
  ├── judge = Claude 多代理（3×sonnet 生成 + 2×opus 证伪，通过 DeepEvalBaseLLM 接入）
  ├── 回归门 = pass_rate/p90_score 阈值断言，GitHub Actions 退出码控门
  └── 数据本地，无 PII 外泄
```

**与 M12（cost/litellm）边界**：DeepEval 调用 Claude 走 ufo2 LiteLLM proxy（`bl-*` 别名），M12 的 litellm 层做 cost tracking + 限流；eval harness 只关注分数，不重复做 cost 观测。若需 trace 存档，在 DeepEval 自定义回调写 score 到轻量 SQLite，不引入 Langfuse 6 容器栈。

### 推荐方案 B：promptfoo（补充场景）

用于**跨模型比较**和**red team 扫描**场景（probe 数据源切换时的 A/B 质量对比），YAML 声明式配置轻，与主 DeepEval 流程并行跑不冲突。

### 方案 C（暂不推荐）：Langfuse + Ragas 内置评估库

若 ufo（机3）上独立起 Langfuse 6 容器栈（符合机3 Docker 实验环境职责），可接 Ragas 评估器做观测+eval 一体。但 ClickHouse 运维成本高，P1 以后有需要再评估。

---

## tech-gate 12 闸速查表

| 闸 | 问题 | DeepEval | promptfoo | Ragas | Langfuse | Phoenix |
|----|------|----------|-----------|-------|----------|---------|
| G1 | judge 模型可插拔？ | ✅ 任意 LLM | ✅ YAML 一行换 | ✅ llm_factory | ✅ LLM Connection 可换 | ✅ LiteLLM 适配 |
| G2 | Claude 多代理 judge 支持？ | ✅ 官方示例 | ✅ anthropic: provider | ✅ Anthropic 直连 | ✅ Claude Sonnet 支持 | ✅ Anthropic 适配器 |
| G3 | pytest / CI 原生？ | ✅ 一流 | ✅ 一流 | ⚠️ 需自写门 | ❌ 非 CI 框架 | ❌ 需脚本化 |
| G4 | 回归门（阈值断言）？ | ✅ pass_rate/p90 内置 | ✅ --fail-on-error + JSON | ⚠️ 自写 | ❌ | ❌ |
| G5 | self-host 无云依赖？ | ✅ 纯本地 | ✅ 纯本地 | ✅ 纯本地 | ⚠️ 6容器重栈 | ✅ 单容器 |
| G6 | PII 本地化？ | ✅ 不登录不上云 | ✅ 本地 SQLite | ✅ | ✅（但运维复杂） | ✅ |
| G7 | 许可证无商业风险？ | ✅ Apache-2.0 | ✅ MIT | ✅ Apache-2.0 | ✅ MIT（核心） | ⚠️ ELv2 法务确认 |
| G8 | 27 场景分层抽样支持？ | ✅ dataset + testcase | ✅ YAML vars | ✅ EvaluationDataset | ✅ dataset experiments | ✅ dataset |
| G9 | 多代理取多数投票？ | ✅ 自定义 metric 可实现 | ⚠️ 需外部聚合 | ✅ 可多 judge 聚合 | ⚠️ | ⚠️ |
| G10 | GitHub Actions 示例存在？ | ✅ 官方文档 | ✅ 官方文档 | ⚠️ 无官方模板 | ❌ | ❌ |
| G11 | 换模型/改闸触发回归？ | ✅ 阈值门可配置 | ✅ --fail-on-error | ⚠️ 自写 | ❌ | ❌ |
| G12 | 与 M12 litellm 兼容？ | ✅ 走 proxy | ✅ 走 proxy | ✅ 走 proxy | ✅ 有 litellm 集成 | ✅ litellm 适配器内置 |

---

## verdict

**档位：DeepEval 主选（A级）· promptfoo 补充（B级）· Ragas 可选（B级评测指标补充）**

**理由：**

- **DeepEval** 是唯一同时满足「judge 可插拔 Claude」+「pytest 原生回归门」+「本地 PII 安全」+「活跃维护（2026-05-28 最新版）」的框架。内置 pass_rate/p90 阈值断言直接对应"换模型/改闸/加源必过 CI"的需求，Apache-2.0 许可无商业风险。**选定为主 eval harness。**

- **promptfoo** 补充用于跨模型 A/B 比较和 red team 扫描场景，YAML 声明式轻量，OpenAI 收购后短期 MIT 不变，但长期中立性需观察。

- **Ragas** 的 RAG 专项指标（faithfulness/context_precision）在 probe 金标 27 场景中有用，可作为 DeepEval 自定义 metric 的评分依据引入，不必独立运行。

- **Langfuse** ClickHouse 6 容器栈成本 > 收益，P0 阶段不引入；P1 若机3 有余量可评估。

- **Phoenix** ELv2 非 OSI 开源，需法务确认，且 CI 集成弱，优先级低。

**落矩阵格**：`M8-eval-harness = DeepEval（主）+ promptfoo（A/B扫描辅）`，judge 调用走 ufo2 LiteLLM proxy，cost 观测由 M12 负责，M8 不重复做。

---

## 顺手发现

1. **promptfoo 被 OpenAI 收购（2026-03-09）**：MIT 许可承诺维持，但若未来 Claude 支持降级需提前切换方案。
2. **ClickHouse ≥25.5.2 内存 bug**：Langfuse 官方建议固定在 25.5.2，有坑记录。
3. **Langfuse + ClickHouse 是行业趋势**：2025 年 ClickHouse 直接收购了 Langfuse，二者深度绑定，未来独立性进一步降低。
4. **DeepEval "Opus 4.8: Day 0 Support"**（2026-05-28）：与我方 claude-sonnet-4-6 同期，该框架跟进 Anthropic 新模型极快，适合作为主框架。
5. **Phoenix v17.3.0**（2026-06-10，昨天刚发）：更新极快，但 ELv2 法律风险仍在。

# 元探（MetaProbe）· 对外 API 文档 v1.0

> 日期：2026-06-06 · 子域：`probe.metafoclaw.com` · 契约版本：`1`
> 性质：probe 引擎对母体/B 端的唯一接口规范（P2 阶段 apidoc 材料）。底层走 L1 四暗号契约（invoke/manifest/billing/profile）。
> 真源：契约 schema 在 `probe/contract/*.json`（本文档据其生成，schema 变更须同步本文档）。

---

## 〇、一句话

**POST 一句话指令 + 任意素材 → 异步返 `task_id` → 轮询拿「带可信度标签、可回放、扛得住证伪」的情报成品。**

---

## 一、端点总览

| 端点 | 方法 | 作用 | 同步性 |
|------|------|------|--------|
| `/api/v1/invoke` | POST | 一句话/链接 → 异步返 `{task_id, status_url}` | 异步（长任务铁律） |
| `/api/v1/task/{id}` | GET | 轮询 `status/progress/deliverable/meta/cost` | — |
| `/api/v1/manifest` | GET | 三维画像标签（喂母体 L4 推荐/矩阵） | 同步 |
| `/api/v1/selftest` | POST | 准入自检（契约合规 11 项） | 同步 |
| `/api/v1/health` | GET | 健康检查 | 同步 |

**鉴权**：请求带母体下发的短时 `user_token`（不暴露真凭据）；匿名请求降级为 public 免费档。

---

## 二、POST /api/v1/invoke

### 请求体（request）
| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `instruction` | string | ✅ | 一句话指令（如「整理这条抖音链接的关键数据做选题依据」）|
| `version` | string | | 客户端声明的契约版本，如 `"1"` |
| `context` | object | | 上下文（如 `ip_profile` 受众画像）|
| `attachments` | string[] | | 素材：链接 / 图片 / 视频 / 文档 URL |
| `user_token` | string | | 平台下发短时 token（不暴露真凭据）|
| `billing_context` | object | | 计费上下文 |

### 响应体（response · 异步返 task）
长任务铁律：invoke 立即返 `{task_id, status_url}`，结果经 `/task/{id}` 轮询。最终 deliverable 结构如下。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `deliverable` | any | ✅ | 成品（七段报告 / conclusion_block，按交付形态渲染）|
| `meta` | object | ✅ | 元信息（见下）|
| `cost` | object | ✅ | 成本（`base` 必填 + `premium_data`）|

**meta 字段**：
| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `aigc_flag` | boolean | ✅ | 是否含 AI 生成内容（硬性 guard）|
| `models_used` | string[] | | 所用模型（**含验证层对抗证伪的 opus，喂 MetaFlow 效益层**）|
| `data_sources` | string[] | | 命中的数据源 id（喂 MetaLearn 飞轮）|
| `confidence` | number | | 综合置信度 |
| `duration_ms` | integer | | 耗时 |
| `tool_id` | string | | 处理该次请求的工具（审计/分账）|
| `contract_version` | string | | 本次响应遵循的契约版本 |
| `geo_publishable` | boolean | | 结论是否可在当前地域合规发布（GEO 分发用）|
| `conclusion_block` | object | | 结构化结论块（`headline` / `key_points[]` / `data_table` / `brand_anchor`），供前端直渲 + GEO 管线 |

**cost 字段**：`base`（number·必填，含验证层 LLM 成本）+ `premium_data`（number·付费源数据成本）。

### 三层深度线（按 user_token 档位裁剪 · 硬约束）
| 档 | 可见 |
|----|------|
| public（匿名）| 仅评级 + 一句话结论 |
| preview（免费登录）| + 结构骨架 + 1 条二创简版 + 合规摘要 |
| paid（付费）| 完整七段报告 + 竞品横评 + 三路二创 + 完整合规 |

> **铁律**：① 原料进结论出——任何出口不透传第三方原始 JSON；② public/preview 禁泄露 paid 内容。

---

## 三、GET /api/v1/task/{id}

返回 `{status, progress, deliverable?, meta?, cost?}`。`status ∈ {pending, running, done, error}`；`done` 时带完整 deliverable/meta/cost。

---

## 四、GET /api/v1/manifest

三维画像，喂母体 L4 推荐路由。
| 字段 | 类型 | 必填 | 说明 |
|------|------|:--:|------|
| `name` | string | ✅ | 引擎名（MetaProbe / 元探）|
| `subdomain` | string | | 子域标识 `"probe"` |
| `industry` | string[] | ✅ | **对外一期 `["自媒体","金融"]`**（2026-06-08 元东方裁定金融正式纳入·enum 约束；金融能力 S1 落地中、声明已纳入、能力随 S1 补齐；扩展更多业务域时更新）|
| `angle` | string[] | ✅ | 切入角度（如 链接分析 / 情报）|
| `solves` | string | ✅ | 解决什么 |
| `pricing_tier` | enum | ✅ | `free` / `premium` / `oss` |
| `sample_input` / `sample_output` | string | | 样例 |

---

## 五、POST /api/v1/selftest（准入门）

母体准入前跑，返回 `{passed, total, checks[], admission, blockers[]}`。**当前 11/11 通过**。契约合规 11 项覆盖：四暗号字段齐全、`aigc_flag` 必填、`cost.base` 必填、`geo_publishable`/`conclusion_block` 字段就位、`manifest.industry` 锁定等。`passed==total` 才 `admission=true`。

---

## 六、GET /api/v1/health
返回 `{ok: true}` + 版本/时间戳。

---

## 七、计费契约（billing）
`base`（基础成本）+ `premium_data`（付费源数据成本）+ `settlement{tool_id, share}`（phase1 记账·phase2 分成）。失败不扣费。

## 八、用户画像契约（profile）
`user_id` + `preferences` + `industry_focus[]`（母体 L3 统一用户层下发，用于 D9 IP 适配）。

---

> 变更纪律：`probe/contract/*.json` 任一 schema 改动，必须同步本文档 + 跑 `/selftest` 确认仍 11/11（C-5）。

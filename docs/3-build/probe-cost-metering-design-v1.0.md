# probe · 成本埋点设计（方案 · 未落码）v1.0

> 日期：2026-06-10 · 性质：**设计方案**（本轮只设计·S1 落码点见 §八）· 不在本轮改 billing.py
> 起因：[风险清单](probe-api-fetch-risk-checklist-v1.0.md) Q3「无成本看板」= 让 C/M/F/W 全部隐形的元缺口 → 先把「每次调取烧了多少」变可见
> 关系：本文 = 成本**可见层**真源 · 上游问题库 [risk-checklist](probe-api-fetch-risk-checklist-v1.0.md) · 下游应对 [dynamic-governance](probe-data-dynamic-governance-design-v1.0.md)（埋点数据喂动态管控做熔断/降级）
> 守规：业务数据入 PG(R28)·禁全局可变状态(R14)·凭据脱敏(R2)·元护写三锁(R-EHW)

---

## 一、第一性：两本账，不是一本

probe 现有 [billing.py](../../app/core/billing.py) 只回答「**向用户收多少**」（cost{base, premium_data}，失败不扣）。它**不回答**「**向供应商烧了多少**」。两者必须分开记账——这是修 C4/M1 的根：

| 账本 | 回答 | 谁付 | 失败时 | 现状 |
|------|------|------|--------|------|
| **计费账（billing）** | 向用户报价收多少 | 用户钱包 wallet.debit | **不扣**(保护用户) | ✅ billing.py 有 |
| **计量账（metering）** | 向供应商真实烧多少 | probe 自己 | **照记**(失败/重试/fallback 都是真消耗) | 🔴 **本设计新增** |

> 关键：用户侧「失败不扣」是对的；但供应商按 req/token 计费时，**失败、重试、provider fallback 都已经烧了钱**。计量账记的是「真实供应商消耗」，是对账(C6)、熔断(C8)、看板(Q3)、多租户限额(Q1/Q2)的唯一数据源。

---

## 二、两个成本面（埋哪里）

| 面 | 计量单位 | 单价来源 | 埋点位置 | 对应坑 |
|----|---------|---------|---------|--------|
| **数据源 API** | req / 条 / 按量 | 供应商定价(回填真实账单) | [datasources/base.py](../../app/datasources/base.py) `fetch_metadata` 出口 | C1-C8 F1-F3 W1-W3 |
| **LLM API** | input/output token | provider 计费(deepseek/qwen/opus) | [services/llm.py](../../app/services/llm.py) `_chat` 出口 | M1-M5 |

**统一手法**：不在每个适配器里散写埋点（违 speed-depth §9.5 禁硬编码散落），而是**一个装饰器/包装器**统一拦截两面的每次出站调用 → 产出一条 `cost_event`。

---

## 三、核心数据模型 · cost_event（每次调取一条）

```jsonc
{
  "call_id":     "uuid",            // 本次调用唯一 id（幂等/重试关联）
  "task_id":     "task-xxx",        // 归属任务
  "user_id":     "hash(uid)",       // 用户(脱敏 hash·守 R2/PIPL·不存明文)
  "surface":     "datasource|llm",  // 成本面
  "source_id":   "tikhub|deepseek", // 数据源 id 或 LLM provider
  "kind":        "video|deep|...",  // 调取类型
  "units":       {"req": 1} ,       // 或 {"input_tokens":N,"output_tokens":M}
  "unit_cost":   0.007,             // 真实单价(回填·非桩值)
  "cost_real":   0.007,             // 本次真实供应商消耗(= units×unit_cost)
  "billed":      0.20,              // 本次向用户计费(billing·失败=0)
  "status":      "success|fail|cached|degraded|skipped", // 结果态
  "cache_hit":   false,             // 命中缓存(cost_real=0 的省钱凭证)
  "retry_seq":   0,                 // 第几次重试(C3 雪崩可见)
  "fallback_of": null,              // 若为 fallback，指向被替代的 call_id(M1 双扣可见)
  "url_hash":    "hash(canon_url)", // 规范化 URL 的 hash(守 U3/R2·不存全 URL)
  "latency_ms":  820,
  "ts":          "2026-06-10T..."
}
```

**字段设计要点**：
- `status=cached/skipped` → `cost_real=0`：缓存命中和去重跳过都记一条**省钱事件**，量化动态管控的收益。
- `retry_seq>0` 与 `fallback_of≠null`：让 C3 重试雪崩、M1 fallback 双扣**在数据里直接可见**，不再靠猜。
- `cost_real` vs `billed` 分离：C6 漂移 = 看 `Σbilled − Σcost_real` 的毛利曲线，跌穿即报警。
- `user_id/url_hash` 一律 hash：守 R2 凭据卫生 + PIPL（U3、L5）。

---

## 四、采集 → 聚合 → 看板（三段）

```
[每次调取] ──cost_event──▶ [事件流] ──日聚合──▶ [PG 聚合表] ──▶ [Q3 成本看板]
   埋点(§二装饰器)          缓冲/批写          R28 入 PG          per-source/llm/user/task
```

### 4.1 落库（守 R28：业务数据入 PG，不用 SQLite）
- 明细：`probe_cost_events`（高频写·可先落对象存储/Redis 流再批入 PG）
- 聚合：`probe_cost_daily`（维度：日期 × user × source × surface × status）
- 加列守 R27（gate_router DO 块同步：CREATE 改了必补 ALTER ADD COLUMN IF NOT EXISTS）
- 写聚合若走 cron → 守 R-EHW 元护写三锁（fcntl 锁 + 原子替换 + version 冻结）

### 4.2 看板维度（Q3）
| 维度 | 回答 | 触发动作 |
|------|------|---------|
| per-source | 哪个源最烧/命中率 | 低命中→查 U3·高烧→评 ROI |
| per-LLM | token 消耗/fallback 率 | 高 fallback→查 M1 |
| per-user | 谁烧得多 | 接 Q1 限额 |
| per-task | 单任务成本 | 异常高→查 F1 扇出/C5 分页 |
| 毛利 | Σbilled−Σcost_real | 跌穿阈值→C6 重定价 |
| 省钱 | Σcached+skipped 省下的 cost | 量化缓存/去重收益 |

---

## 五、熔断阈值（埋点喂动态管控）

埋点不只是「看」，它的实时累计值是[动态管控](probe-data-dynamic-governance-design-v1.0.md)的**输入信号**：

| 阈值 | 触发 | 动作(交动态管控执行) |
|------|------|---------------------|
| 单任务额度 | task 累计 cost_real > 上限 | 停止加源/降级极速版(F1) |
| per-user 日额度 | user 当日 cost_real > 档位额度 | 拒新付费调用/引导升档(Q1) |
| 单源日额度 | source 当日 > 预算 | 该源熔断→降级备用源/缓存(C8) |
| 重试连发 | 同 call retry_seq≥N | 停重试+退避(C3) |
| 毛利跌穿 | 日毛利 < 0 | 告警元东方+评估重定价(C6) |

> 阈值不写死在代码——存配置表，按用户档/数据类型动态取（守 speed-depth §9.5）。

---

## 六、与现有体系的关系（不推翻）

| 现有 | 角色 | 本设计如何接 |
|------|------|------------|
| billing.py | 计费账(对用户) | 不动·metering 与它并行·billed 字段引它的结果 |
| cost_hint()（base/tikhub）| 桩单价 | metering 回填 `unit_cost` 真实值→反向修 cost_hint(C6) |
| tasks 层「失败→cost=None」| 用户失败不扣 | 保留·但 metering 照记 cost_real(C4) |
| audit gates | 质量 | 不涉成本·但缓存前过闸(K1)由管控编排 |

---

## 七、隐私与安全（守 R2/PIPL）
- `user_id`、`url_hash` 一律单向 hash，**不存明文 URL / 用户标识**（U3、L5、R2-L12）。
- cost_event **不含**第三方原始数据/凭据，只含计量元数据。
- 看板访问受 hub SSO（L1-L4 RBAC），成本数据属敏感运营数据。

---

## 八、S1 落码点（本轮不写·仅列清单）

1. `app/core/metering.py`（新）：`cost_event` 模型 + 装饰器 `@meter(surface=...)`
2. 包装 `datasources/base.fetch_metadata` 与 `services/llm._chat` 出口埋点
3. PG 表 `probe_cost_events` / `probe_cost_daily`（守 R27/R28）
4. 日聚合 job（守 R-EHW 三锁）
5. 看板页（接 hub·守 H5-First + 元历时钟 R16）
6. 阈值配置表 + 读取接口（喂动态管控）
7. 桩单价 → 真实账单回填对账流程（修 C6）

---

## 九、版本/变更记录
| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-10 | 双本账模型+cost_event schema+三段采集+熔断阈值·设计定稿(未落码) |

> 一句话：**计量账先于一切**——没有「每次烧多少」的真实数据，缓存省了多少、毛利正不正、谁该限额，全是拍脑袋。本设计是把 probe 从「烧完才知道」拉到「每次都可见」的地基。

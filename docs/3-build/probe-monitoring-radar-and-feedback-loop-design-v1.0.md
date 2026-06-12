# probe · 持续监测雷达 + 用户反馈纠错闭环设计 v1.0

> 日期：2026-06-10 · 性质：**设计方案**（本轮只设计，S2 落码；S1 专注单次查询核心链路）
> 补缺口：#4 持续监测雷达（B6/C4 订阅 feature 的完整设计）+ #7 用户反馈纠错闭环（结论错误→源可靠度在线修正）
> 真源边界：本文 = 监测订阅+快照+反馈三张表的**逻辑与状态机**真源；表字段归属以 [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) 为准；编排复用 [orchestration](probe-orchestration-engine-solution-v1.0.md) 的扇出流程；成本联动见 [cost-metering](probe-cost-metering-design-v1.0.md)；动态管控见 [data-governance](probe-data-dynamic-governance-design-v1.0.md)。
> 约束遵从：R28 业务数据入 PG（tencent-sh 主库 probe schema）· R14 禁全局可变状态 · server-roles T1/T2（cron/定时任务在云服务器，不在本地 Mac）· **人物 OSINT 红线：监测雷达禁用于持续监控自然人，监测目标仅限行业/企业/话题/账号公开维度**。

---

## 〇、一句话 + 七项已定决策

**【一句话】** 监测雷达 = 把单次扇出变成**周期性重查 + 快照 diff + 告警分发**的订阅服务；反馈闭环 = 把用户对结论的纠正**聚合回调 probe_source_reliability**，在线修正真值发现先验，是冷启动护栏的唯一在线更新来源。

**【七项已定决策】**

| # | 决策点 | 已定方向 | 依据 |
|---|--------|---------|------|
| D1 | 监测触发机制 | PostgreSQL `pg_cron` 驱动 subscription 调度，单机 cron 产出任务行，**不另起外部调度器** | 📐 对齐 tencent-sh PG 主库已有 pg_cron，无新组件依赖 |
| D2 | 重查复用 | 每次重查 = 复用 orchestration 扇出流程（同档 flash/deep），不另起采集管线 | ✅ orchestration-engine-solution §二 |
| D3 | diff 检测 | snapshot 存 jsonb，diff = 结构化字段比对 + 关键指标变动 + 新事件出现，**不做全文字符串比对** | 📐 标准实践 |
| D4 | 告警去重 | 同 subscription 同类变化 cooling_period（默认 24h）内不重复推送 | 📐 标准实践，防刷屏 |
| D5 | 成本控制 | 订阅档位 = 按频率+维度数收月费，周期内仅在 diff 触发时深查；否则只跑 flash+缓存优先 | 本文 §A5 |
| D6 | 反馈防刷 | 单用户单结论 confirm/dispute 只计 1 票；correct 需提供替换值；全局多用户聚合后才调整 reliability，**单票最大调整幅度 ≤ 0.02** | 本文 §B8 |
| D7 | 与 MetaLearn 分工 | probe 内部闭环（本文）= 源可靠度在线修正，走 probe schema；MetaLearn 飞轮 = 跨引擎能力演化，走 L1 契约 event，**两者禁直连**（R22） | 本文 §B10 |

---

## A 部分 · 持续监测雷达（缺口 #4）

### A1 · 订阅模型：监测目标类型与红线

#### 允许的监测目标类型

| 类型 | 典型示例 | 监测维度 | 频率档位 |
|------|---------|---------|---------|
| **行业/赛道** | 跨境电商、AI 生成视频工具 | 政策、融资、竞品入局、技术突破 | 日/周 |
| **企业/品牌** | 某上市公司、某 AI 创业 | 公告、新闻舆情、产品发布、ESG 事件 | 日/周 |
| **话题/关键词** | "跨境独立站 SEO"、"视频号电商" | 内容声量、情感趋势、核心媒体报道 | 日/周/月 |
| **账号公开维度** | 某 YouTube 频道公开指标 | 粉丝增量、发布频率、互动率公开统计 | 周/月 |

#### 明确禁止（OSINT 红线 · 与 feasibility §5 对齐）

```
❌ 自然人持续监控：禁止以真实姓名/身份证/手机号/邮箱为 target 创建 subscription
❌ 账号画像落库：账号维度的监测结果 persist_policy = ephemeral（只推告警，不落 PG 快照）
❌ 关联分析：禁止把多个账号公开维度结合追踪以还原自然人位置/行为轨迹
❌ 政治人物/司法案件：监测 target 类型须过 registry gate19 合规门，上述类型拒绝创建订阅
```

> ⚠️ 系统层面：`probe_monitor_subscription.target_type` 枚举只允许 `industry / company / topic / account_public`；`account_public` 创建时需额外通过合规门审批，快照表 `persist_policy` 强制 `ephemeral`（不落 PG，只经 Redis 短暂中转推完即丢）。

#### 监测维度（dimension）

每个 subscription 携带 `dimensions` 数组（存在 `diff_rule.dimensions` jsonb 字段），例：

```jsonc
{
  "dimensions": ["funding", "product_launch", "regulatory", "media_volume"],
  "thresholds": {
    "media_volume_delta": 30,   // 声量变化≥30%触发告警
    "sentiment_shift": 0.15,    // 情感均值偏移≥0.15触发告警
    "new_events_min": 1         // 有至少1条新事件触发告警
  }
}
```

维度数量是计费参数（见 §A6）。

---

### A2 · 监测状态机：subscription 生命周期

```
                         create
                            │
                            ▼
             ┌──────────── active ────────────┐
             │         (正常调度中)            │
             │  pg_cron 命中 → enqueue_check   │
             │                                 │
      pause(用户)                          quota_exhaust(月额度耗尽)
             │                                 │
             ▼                                 ▼
          paused ──resume──▶ active         quota_paused ──续费──▶ active
             │                                 │
      cancel(用户)                       expire(到期未续)
             │                                 │
             ▼                                 ▼
          cancelled                         expired
             │                                 │
             └──────────────┬──────────────────┘
                            ▼
                        (终态·数据保留N天后归档)

  调度执行失败时：
     error_count < 3 → status 保持 active，retry_at = now + backoff
     error_count ≥ 3 → status = error(需人工或自动恢复)
```

**状态字段**：`probe_monitor_subscription.status` 枚举：`active / paused / quota_paused / expired / cancelled / error`

**调度流程**（pg_cron 驱动）：

```
pg_cron 每分钟扫 probe_monitor_subscription
WHERE status = 'active'
  AND next_run_at <= now()
→ 对每行：
  1. 原子更新 next_run_at = next_cron_tick(schedule)，last_run = now()
  2. INSERT probe_monitor_job (subscription_id, triggered_at, status='queued')
  3. 信号写入 Redis pub/sub channel "monitor:jobs"（轻量通知，不阻塞 pg_cron）
→ probe 后台 worker（tencent-sh asyncio worker）订阅 channel → 取 job → 执行重查
```

> ✅ 对齐 server-roles：pg_cron + probe worker 均在 tencent-sh（主库所在机）运行；不在本地 Mac 跑 cron。

**失败重试与降级**：

| 失败场景 | 动作 |
|---------|------|
| 扇出超时/降级返回 partial | 接受 partial 结论做 diff，快照标记 `incomplete=true`，告警带"本次数据不完整" |
| L2 采集全失败（所有源超时）| 本次跳过，error_count++，下轮重试；不产生空快照 |
| error_count=3 | status → error，推送用户告警"监测暂时中断"，等人工确认或自动 reset |
| 用户额度耗尽 | status → quota_paused，推送引导续费通知 |

---

### A3 · diff 检测：快照比对机制

**快照结构**（`probe_monitor_snapshot.snapshot` jsonb）：

```jsonc
{
  "captured_at": "2026-06-10T08:00:00Z",
  "task_id": "task-xxx",                  // 本次重查任务 ID
  "conclusion_label": {                   // 三标签快照
    "confidence": 0.82,
    "evidence_grade": "B",
    "admiralty": "B2"
  },
  "key_metrics": {                        // 按 dimension 提取的关键指标
    "media_volume_7d": 1240,
    "sentiment_avg": 0.61,
    "funding_events": []
  },
  "top_events": [                         // 本次识别的新事件（最多N条）
    {"title": "...", "source": "...", "ts": "..."}
  ],
  "incomplete": false
}
```

**diff 算法**（`diff_rule` 驱动，不做全文比对）：

```python
def compute_diff(prev: dict, curr: dict, diff_rule: dict) -> DiffResult:
    alerts = []

    # 1. 关键指标变动（阈值对比）
    for metric, threshold in diff_rule["thresholds"].items():
        prev_val = prev["key_metrics"].get(metric)
        curr_val = curr["key_metrics"].get(metric)
        if prev_val is not None and curr_val is not None:
            delta_ratio = abs(curr_val - prev_val) / (abs(prev_val) + 1e-9)
            if delta_ratio >= threshold:
                alerts.append(AlertItem(type="metric_shift", metric=metric,
                                        prev=prev_val, curr=curr_val, delta_ratio=delta_ratio))

    # 2. 新事件出现（top_events 对比：以 source+title hash 去重）
    prev_event_ids = {hash_event(e) for e in prev.get("top_events", [])}
    new_events = [e for e in curr.get("top_events", [])
                  if hash_event(e) not in prev_event_ids]
    if len(new_events) >= diff_rule["thresholds"].get("new_events_min", 1):
        alerts.append(AlertItem(type="new_events", events=new_events))

    # 3. 置信/证据等级下滑（质量退化主动告警）
    if curr["conclusion_label"]["confidence"] < prev["conclusion_label"]["confidence"] - 0.15:
        alerts.append(AlertItem(type="confidence_drop", ...))

    return DiffResult(has_change=bool(alerts), alerts=alerts)
```

**快照保留策略**：
- 每次重查产一条 snapshot；PG 保留最近 **N=30** 条（按 subscription_id 窗口清理）
- 历史趋势（指标时序）在 snapshot jsonb 内隐含；不另建时序 DB
- `account_public` 类型 subscription：snapshot 不落 PG（`persist_policy=ephemeral`），diff 在内存算完即丢，只推告警

---

### A4 · 告警分发：通知与去重

**告警优先级分级**：

| 级别 | 触发条件 | 通知方式 |
|------|---------|---------|
| P1 重大变化 | 指标剧变≥50% 或 新融资/重大政策事件 | 即时微信推送（Server酱）|
| P2 中等变化 | 阈值触发但幅度适中 | 微信推送（合并当日其他 P2）|
| P3 轻微变化 | 有新事件但未达阈值 | 周汇总邮件（不单独推）|

**通知底座**（对齐已有 origin-notify.py）：

```bash
# tencent-sh 推送（复用 R21/R23 已有底座）
ssh tencent-sh python3 /root/scripts/origin-notify.py \
  --push "【监测告警】${target_name} 出现 ${alert_type}" \
  --desp "${alert_detail}"
```

**告警去重/抑制**（防刷屏）：

```
probe_monitor_alert_log (subscription_id, alert_type, alert_hash, sent_at)
规则：
  1. 同 subscription + 同 alert_type + alert_hash 相同 → cooling_period（默认 24h）内不重发
  2. P2 级当日合并：当天第一条 P2 立即推；后续 P2 累积到 23:00 发日汇总
  3. subscription 在 error/paused 状态时不发监测告警（只发状态变更通知）
  4. 用户可设置静默时段（do_not_disturb 字段在 subscription）
```

**多通道扩展位**（📐 S2 后扩展）：
- 邮件（hub 账户 email）
- Webhook（用户自定义推送地址）
- 当前 S2 仅支持 Server酱微信推送，其他通道留 channel 字段预占位

---

### A5 · 成本控制：监测不能无限烧 API

> 持续监测是"周期性重复调用"，若不管控，月成本 = 单次成本 × 频率 × 订阅数，极易爆炸。

**三层成本控制策略**：

**① 缓存优先**

每次 monitor 重查先过 [data-governance](probe-data-dynamic-governance-design-v1.0.md) 的 Data Governor：
- `新鲜度信号`：监测目标所在信息域，如行业趋势 τ=12h；若上次快照距今 < τ 且无外部触发，直接复用 L2 源响应缓存，不打 API
- 缓存命中 = 本次监测 API 成本 ≈ 0（只有轻量 diff 计算）

**② flash-first 周期扫描，deep 按需触发**

```
每次定时重查默认走 flash（极速版）：
  → flash 产 key_metrics + top_events
  → diff 检测到变化且达 P1 级 → 自动升 deep 深查一次（记入计量账）
  → 仅 P2/P3 变化 → 不升 deep，flash 结论即告警内容

好处：80% 的周期扫描仅消耗 flash 成本（约是 deep 的 1/5 - 1/10）
```

**③ 订阅档位限频**

| 档位 | 最高频率 | 维度数上限 | 月 API 调用预算 |
|------|---------|----------|---------------|
| 基础订阅 | 每日 1 次 | ≤ 3 维度 | 30 flash + 3 deep |
| 标准订阅 | 每日 2 次 | ≤ 6 维度 | 60 flash + 10 deep |
| 专业订阅 | 每小时 1 次 | ≤ 12 维度 | 720 flash + 30 deep |

超出预算 → status → quota_paused，不静默超量（保护 probe 自身成本）。

**成本联动**（写 cost_event）：每次 monitor 重查的每个 API 调用写一条 `cost_event`，`task_id` 关联监测任务，可在成本看板里按 subscription 聚合查监测总支出。

---

### A6 · 订阅计费：与按量 credits 的关系

**计费设计原则**：监测是持续服务，不适合按量 credits（按量 = 一次性消耗，不含持续成本）。走**订阅特例月费制**。

| 费用构成 | 说明 |
|---------|------|
| 基础月费 | 按档位（基础/标准/专业）固定月费，覆盖 API 调用预算 |
| 超量 deep 费 | 触发 deep 超过月预算时，按件从用户 credits 扣（复用 billing.py） |
| 告警次数 | 月内 P1 告警含在月费；P2/P3 无上限 |

**与按量 credits 的接口**：
- 月费在 hub identity 计费系统（S3 实现）处理，probe 只关心 `subscription.status` 是否 `active`
- 超量 deep 调用：`billing.py wallet.debit(user_id, cost, reason="monitor_deep_upgrade")`
- 试用期：新 subscription 创建后 7 天免费 flash 监测（不消耗 credits）

---

## B 部分 · 用户反馈纠错闭环（缺口 #7）

### B7 · 反馈采集：UI 入口与 payload 结构

**三种反馈类型**：

| kind | 含义 | 用户操作 | 权重 |
|------|------|---------|------|
| `confirm` | 结论正确，用户确认 | 👍 按钮，一键 | 正向信号，权重低（懒于操作的多） |
| `dispute` | 结论有问题，但用户不知道正确答案 | ⚠️ 按钮 + 可选备注（1-200字）| 负向信号，触发人工复审 flag |
| `correct` | 结论明确错误，用户提供替换值 | ✏️ 按钮 + 必填替换内容 | 强负向信号，触发源可靠度回调 |

**UI 入口规则**：
- 每条结论七段报告（s1-s7）底部显示反馈栏
- `ephemeral` 任务（人物 OSINT）：**不显示反馈入口**（结论本身不落库，无 conclusion_id 可挂）
- 反馈入口仅对创建该任务的 user_id 本人显示（不开放公开投票，防刷）

**payload 结构**（存 `probe_feedback.payload` jsonb）：

```jsonc
// kind=confirm
{"note": "可选备注，最多200字"}

// kind=dispute
{
  "note": "必填备注（1-200字，描述疑点）",
  "disputed_section": "s3",            // 可选，指向哪一段
  "disputed_claim_ids": ["claim-xxx"]  // 可选，指向哪些断言
}

// kind=correct
{
  "disputed_claim_ids": ["claim-xxx"], // 必填，指向哪个断言错了
  "correction": "正确的信息内容",       // 必填替换值
  "correction_source_url": "https://...", // 可选，用户提供的来源
  "note": "可选备注"
}
```

---

### B8 · 反馈→源可靠度回调：聚合规则与防刷

**回调目标**：`probe_source_reliability`（source_id · reliability · prior · sample_count · updated_at）

**回调触发条件**：只有 `kind=correct` 且 `disputed_claim_ids` 非空时触发回调。`confirm`/`dispute` 不直接修改 reliability（只记录用于统计）。

**回溯路径**：`probe_feedback.disputed_claim_ids → probe_claim.source_ids → probe_source_reliability`

**聚合策略**（防单用户滥用）：

```
每次收到 kind=correct 时：
1. 立即写入 probe_feedback（applied=false）
2. 不立即修改 reliability，进入"待聚合池"

聚合任务（pg_cron 每小时执行）：
  对每个 source_id：
    取最近 24h 内 applied=false 的 correct 反馈
    统计：
      N_correct = 不同 user_id 的纠正投票数
      N_total   = 该 source 同期命中的任务数（来自 probe_source_hit）
      correction_rate = N_correct / max(N_total, 1)

    调整量计算：
      delta = min(correction_rate * 0.1, MAX_SINGLE_DELTA)  // MAX_SINGLE_DELTA = 0.02
      new_reliability = max(0.05, old_reliability - delta)   // 下限 0.05，不清零

    生效条件（同时满足才执行）：
      ① N_correct >= MIN_VOTES（默认 = 3，避免单用户定生死）
      ② correction_rate >= 0.05（纠正率 ≥ 5% 才值得调整）
      ③ 距上次同方向调整 >= 6h（防频繁震荡）

    若生效：
      UPDATE probe_source_reliability SET reliability=new_reliability,
             sample_count=sample_count+N_correct, updated_at=now()
      UPDATE probe_feedback SET applied=true WHERE ...
      写 probe_reliability_change_log（source_id, delta, trigger="user_feedback",
                                        n_votes=N_correct, ts=now()）
```

**防刷/防投毒机制**：

| 威胁 | 防御 |
|------|------|
| 单用户批量刷 correct | 同 user_id 同 source_id 24h 内只计 1 票（聚合时去重 distinct user_id）|
| 僵尸账号刷投票 | MIN_VOTES=3 门槛 + 账户信用积分门（S3 实现，当前 ⚠️ 待标定）|
| 恶意拉低竞品可靠度 | `correction_rate >= 0.05` + `sample_count` 越大 delta 越小（贝叶斯衰减：delta × prior_weight / sample_count）|
| 快速震荡（反复刷高打低）| 6h 冷却期 + 变动有下限（0.05）防清零 |
| 用户自身信用低（滥用反馈者）| `probe_feedback` 写 user_credit_at_time（快照记录时刻信用分），聚合时权重 × user_credit（⚠️ 待 S3 identity 信用体系接入）|

> ⚠️ 防刷阈值待标定：MIN_VOTES / MAX_SINGLE_DELTA / correction_rate 下限 / 用户信用权重，均需运行后实测回填。

---

### B9 · 闭环与真值发现的衔接

**在线修正路径**：

```
用户反馈 → 聚合回调 → probe_source_reliability.reliability 更新
                                    ↓
              下次任务真值发现迭代（orchestration §2.2 D5）：
              迭代步骤1：用 current_reliability（已含修正）加权计算真值估计
              迭代步骤2：用真值反估 reliability（迭代收敛）
                   → new_reliability 写回（如与反馈修正方向一致，收敛加速）
```

**冷启动先验保护**：

`probe_source_reliability.prior` 字段（来自 registry Admiralty 评级）**不被反馈直接修改**。`reliability` 是在线运行态，`prior` 是出厂先验。

当 `sample_count` 很小（< 20）时，真值发现用**后验混合**：

```
effective_reliability = α * reliability + (1 - α) * prior
其中 α = min(sample_count / 20.0, 1.0)  // 样本少时向先验回归
```

好处：避免 3 票就把一个高质量源的可靠度打崩，冷启动阶段先验主导，样本积累后逐渐由在线数据接管。

---

### B10 · 与 MetaLearn 飞轮的关系

**分工说明**：

| 维度 | probe 内部闭环（本文） | MetaLearn 跨引擎飞轮 |
|------|---------------------|---------------------|
| 目的 | probe 引擎**自身质量自愈** | 平台**跨引擎能力演化** |
| 数据流 | 用户反馈 → 源可靠度在线修正 | 源命中日志 → MetaLearn 学习 |
| 写入位置 | probe schema（PG） | MetaLearn 自己的 event store |
| 触发接口 | probe 内部聚合任务 | R22 五环禁直连 → 走 L1 契约 event |
| 反馈粒度 | 具体结论 + 具体源 | 任务类型 + 命中源集合（不含用户纠正内容）|

**接口设计**（禁直连，走 L1 契约）：

probe 在任务完成时向事件总线发 `probe.task_completed` 事件（source_hit 聚合，不含 `probe_feedback` 内容）。MetaLearn 订阅此事件做飞轮更新。probe_feedback 的内容**不发给 MetaLearn**（用户纠正内容含潜在敏感信息，不应跨引擎流转）。

**两条飞轮互不干扰**：MetaLearn 更新的是"什么源/什么场景命中率高"（宏观能力），probe 内部修正的是"这个源这次结论对不对"（微观可靠度）——粒度和语义不同，可并存。

---

### B11 · 诚实边界（已知未定项）

| 项目 | 状态 | 说明 |
|------|------|------|
| 反馈 MIN_VOTES 阈值 | ⚠️ 待标定 | 目前给 3，需运行后看真实用户反馈频率调整 |
| MAX_SINGLE_DELTA 上限 | ⚠️ 待标定 | 目前给 0.02，需看可靠度收敛速度 |
| 用户信用体系权重 | ⚠️ 待 S3 接入 | 当前所有投票等权，S3 接入 identity 信用后加权 |
| 监测频率最小间隔 | ⚠️ 待标定 | 当前专业档最高每小时 1 次；API 成本压测前不开放更高频 |
| `account_public` 合规门 | ⚠️ 待实现 | 需 registry gate19 扩展支持账号合规审批流 |
| correction_rate 下限 0.05 | ⚠️ 待标定 | 低频场景（任务量小）时 5% 门槛可能太高 |

---

## 总览：两个闭环的数据流图

```
                ┌──────────────────────────────────────────────────────────────┐
                │                    A · 监测雷达                              │
                │                                                              │
  subscription  │  pg_cron → enqueue_job → probe worker                       │
  (active)      │                              │                               │
                │                              ▼                               │
                │                    复用 orchestration 扇出                   │
                │                    (flash 优先 / diff 触发 deep)             │
                │                              │                               │
                │                    probe_monitor_snapshot(新)               │
                │                              │                               │
                │                    diff_detect(prev vs curr)                 │
                │                              │                               │
                │               ┌─────────────┴───────────────┐               │
                │            无变化                          有变化             │
                │           (不告警)                   告警分发(去重后)         │
                │                                  origin-notify.py → 用户     │
                └──────────────────────────────────────────────────────────────┘

                ┌──────────────────────────────────────────────────────────────┐
                │                   B · 反馈纠错闭环                           │
                │                                                              │
  用户看结论     │  UI反馈入口(confirm/dispute/correct)                         │
                │         │                                                    │
                │         ▼                                                    │
                │  probe_feedback(applied=false)                               │
                │         │                                                    │
                │  每小时聚合任务                                               │
                │         │                                                    │
                │    ┌────┴────┐                                               │
                │  confirm   correct(N_correct>=MIN_VOTES)                     │
                │    │         │                                               │
                │  仅统计    probe_source_reliability.reliability -= delta     │
                │             │                                                │
                │           applied=true                                       │
                │             │                                                │
                │    下次任务真值发现迭代 → 新结论质量更高                       │
                └──────────────────────────────────────────────────────────────┘
```

---

> 落盘路径：`/Users/metafo/Downloads/metafoclaw/probe/docs/3-build/probe-monitoring-radar-and-feedback-loop-design-v1.0.md`
> 性质：闭缺口 #4（持续监测雷达完整设计）+ #7（用户反馈→源可靠度在线修正闭环）· 待并入 master-solution-v2 §七（运行时状态闭环节）

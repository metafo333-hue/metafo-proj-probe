# probe · 数据源运维与可靠性设计（方案 · 未落码）v1.0

> 日期：2026-06-10 · 性质：**设计方案**（本轮只设计·S1/S2 落码点见 §七）
> 起因：[risk-checklist v1.1](probe-api-fetch-risk-checklist-v1.0.md) 入库的源运维缺口 **E8（健康度/failover）· E9（schema 漂移）· E10（key 生命周期）· Q5（沙箱回放）**——四条同属「**外部供应商不可控**」风险面，并行的监测雷达监的是业务对象、不是源本身，故独立成篇。
> 关系：API 调取治理体系第 5 份 ·〔发现〕[risk-checklist](probe-api-fetch-risk-checklist-v1.0.md) →〔可见〕[cost-metering](probe-cost-metering-design-v1.0.md) →〔选型〕[source-selection](probe-source-selection-and-capability-registry-v1.0.md) →〔应对〕[dynamic-governance](probe-data-dynamic-governance-design-v1.0.md) →〔**保活**〕本文
> 数据底座：健康指标落 [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) `probe_source_hit`（已有每次取数一行）+ 本文新增聚合视图；限流/熔断状态走 Redis（同其 §3.2）

---

## 〇、第一性：源是别人的，挂是常态

probe 的料全部来自**外部 API**——供应商会宕机、会改响应、会砍端点、会让 key 过期。这些**不归 probe 控制，但后果全归 probe 背**（用户只看到"probe 不出结果"）。所以需要一层「源运维」：**把不可控的外部，变成可观测、可自愈、可演练的内部**。

```
E8 源死了 → 自动感知+摘除+failover（不等用户报障）
E9 源变了 → 响应过 schema 校验即报警（不让脏数据进结论）
E10 key 过期 → 提前预警+轮换（不上线后猝死）
Q5 开发测试 → 录制回放（不烧真钱）
```

---

## 一、E8 · 源健康 registry + 自动 failover

### 1.1 健康指标（从已有 probe_source_hit 聚合，不新增埋点）

| 指标 | 算法 | 窗口 |
|------|------|------|
| 成功率 | success / total | 滑动 1h / 24h |
| P95 时延 | latency_ms 分位 | 滑动 1h |
| 连续失败数 | 连续 fail 计数 | 实时 |
| 配额健康 | 429 占比 | 滑动 1h |

### 1.2 健康状态机（per-source · Redis 实时 + PG 留痕）

```
healthy ──连续失败≥N 或 1h成功率<80%──▶ degraded（降权·select_score 扣分）
degraded ──连续失败≥2N 或成功率<50%──▶ down（摘除·路由绕开）
down ──半开探测：间隔指数退避发 1 个探测请求成功──▶ degraded ──持续恢复──▶ healthy
```

- 状态变更写 `probe_source_health_event`（PG 留痕，喂周报）；`down` 持续 > 24h → 通知元东方（origin-notify）。
- **与熔断的分工**：熔断（orchestration §3.6）是**单次调用级**的快速失败；本状态机是**源级**的中期裁定——熔断器跳闸次数是状态机的输入之一。

### 1.3 自动 failover（接选型目录的 substitutable_by）

源 `down/degraded` 时，Governor 选源直接读健康状态：
- 有替代源（`substitutable_by` 非空，如 天眼查→企查查）→ **自动切换**，结果标注 `source_substituted: true`（诚实标注，不假装原源）。
- 无替代 → 走 [dynamic-governance §五](probe-data-dynamic-governance-design-v1.0.md) 降级阶梯（缓存→占位），**绝不硬重试打死源**。

> 这就是为什么选型目录坚持「接 1 备 1」（gate19-dedup B9 裁定）——备份源不是冗余，是 failover 的前提。

---

## 二、E9 · schema 漂移持续检测（契约测试）

### 2.1 三道防线

| 防线 | 时机 | 做法 | 成本 |
|------|------|------|------|
| ① 响应轻校验 | **每次调用**（适配器 `_normalize` 前）| 关键字段存在性+类型检查（pydantic 轻 schema·只校验 probe 用到的字段，不校验全响应）| 微秒级·零外部成本 |
| ② 漂移告警 | 校验失败时 | 计 `schema_drift` 事件 → 1h 内漂移率 > 阈值 → 源转 degraded + 通知 | 零 |
| ③ 定期契约测试 | cron 周级 | 用 Q5 录制的金标响应做回归（**回放为主**），每源仅 1 次真实调用对比金标 | ≈1 req/源/周 |

### 2.2 漂移分级处置

```
新增字段（probe 不用）→ 忽略·记 info
probe 用的字段改名/改类型 → 该源 degraded + 告警 → 人工修 _normalize → 金标更新
端点直接 404/砍掉（Spotify 模式）→ down + failover + 评估替代源
```

> 守 R0.8：漂移期间该源数据**禁入结论**（宁缺勿假），占位或替代源补。

---

## 三、E10 · key 生命周期管理

### 3.1 key 台账（vault 真值 + ledger 元数据 · 不存明文于仓）

每个需 key 的源在 ledger 补 `key_meta`（守凭据纪律：仓内只存元数据，真值在 `~/vault/credentials/` + 服务器 env）：

```yaml
key_meta:
  env_var: PROBE_TIKHUB_KEY        # 注入变量名
  expires_at: null                  # 到期日（无到期填 null）
  quota_reset: monthly              # 配额重置周期
  rotation_policy: manual           # manual / auto
  owner: 元东方                      # R8：注册主体
```

### 3.2 三条纪律

1. **到期预警**：cron 日检 `expires_at`，T-14/T-7/T-1 三档通知（origin-notify）——吸取 ops 证书手动到期教训；证书类同此管理。
2. **轮换流程**：新 key 配好 → 双 key 并行验证（新 key 真实调用 1 次成功）→ 切流 → 旧 key 失效。**禁先删后换**。
3. **多 key 池边界**：同源多 key 仅用于**故障冗余**（主 key 失效切备）——**禁用多 key 绕供应商配额**（违 ToS = L4 同类红线；要更多配额走正道升套餐 + R1）。

---

## 四、Q5 · 沙箱录制回放（record-once / replay）

### 4.1 机制

```
首次（联调时·真实调用 1 次）→ 录制：请求参数 hash → 响应存 fixtures/{source_id}/{hash}.json（脱敏后）
之后（test / selftest / CI / 本地 dev）→ 回放：同参数直接读 fixture，零外部调用、零成本
```

- 模式开关：`PROBE_HTTP_MODE = live | replay | record`（默认 dev/CI = replay；生产 = live）。
- fixture **录制时脱敏**：剥 key/token/个人信息字段再落盘（守 R2 + PIPL）。
- fixture 即 E9 契约测试的**金标**——一份资产两用。

### 4.2 边界
- fixture 只覆盖确定性接口；搜索类（SearXNG）结果天然漂移，回放仅验 schema 不验内容。
- ephemeral 任务（人物 OSINT）**禁录制 fixture**（不留痕红线优先于省钱）。

---

## 五、统一视图：源运维看板（接 hub）

| 面板 | 内容 | 数据源 |
|------|------|--------|
| 源健康总览 | 全源 健康状态/成功率/P95/最近事件 | source_hit 聚合 + 健康状态机 |
| 漂移雷达 | schema_drift 事件流 + 待修 _normalize 清单 | E9 事件 |
| key 到期日历 | 各源 key/证书到期倒计时 | key_meta |
| 成本联动 | 跳转 [cost-metering](probe-cost-metering-design-v1.0.md) 看板 per-source 成本 | cost_event |

> 守 H5-First + 元历时钟 R16；受 hub SSO。

---

## 六、与治理体系闭环（第 5 份的位置）

```
selection（选哪个源）──读健康状态──▶ 本文 E8 健康 registry
governance（每次调取十步闸）──闸⑥重试退避──▶ 本文熔断/状态机裁定源级处置
metering（烧多少）──source_hit/429──▶ 本文健康指标的原料
risk-checklist（问题库）──E8/E9/E10/Q5──▶ 本文 = 这四条的对策归口 → 落码后回填 ✅
```

---

## 七、落码点（本轮不写·按优先级）

| 优先 | 项 | 排期建议 |
|------|----|---------|
| S1 | ① 响应轻校验（pydantic 轻 schema·随适配器联调一起写）| 随 Wave1 T-A |
| S1 | ② Q5 replay 层（selftest/CI 立刻省钱·fixture 兼做 E9 金标）| 随 Wave1 T-A |
| S1 | ③ key_meta 进 ledger + 到期预警 cron | 零依赖·随时 |
| S2 | ④ 健康状态机 + failover（依赖 source_hit 有量后才有意义）| 随 Wave2 扩源 |
| S2 | ⑤ 源运维看板 | 随 Wave2/3 |

---

## 八、版本/变更记录
| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-10 | E8 健康状态机+failover · E9 三道防线契约测试 · E10 key 台账三纪律 · Q5 录制回放 · 设计定稿(未落码) |

> 一句话：**源是别人的、挂是常态**——健康度自动感知摘除切换（E8）、响应漂移即报警禁入结论（E9）、key 到期提前预警禁先删后换（E10）、开发测试回放不烧真钱（Q5），把外部不可控变成内部可运维。

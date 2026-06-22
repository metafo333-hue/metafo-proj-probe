# probe 付费数据源成本优化深度设计 v1.0

> 2026-06-22 · 覆盖 JZL（极致了数据）+ TikHub 两个付费源
> 核心约束：**数据等价** —— 每项优化都不得改变采集产出的结果（字段/数值/完整度）
> 关联：[probe-cost-metering-design-v1.0.md](probe-cost-metering-design-v1.0.md)（计费埋点设计）

---

## 一、现状诊断（基于源码逐行实查）

### 1.1 关键修正：测试不烧钱，钱花在生产采集

| 假设 | 实查结论 |
|------|---------|
| ~~建设期 220 测真打付费 API~~ | ❌ **证伪**：33 个测试全 `unittest.mock` 拦截，零网络零付费 |
| ¥5.7（91.79→86.09）来源 | ✅ **生产/演示环境真实采集**（ledger.yaml 记 2026-06-20 新华社账号实测 feeds_count=46810） |

→ 优化重点从"测试回放"转向**生产采集的缓存 + 成本闸 + 批量**。

### 1.2 三大结构性漏点（JZL + TikHub 共有）

| 漏点 | 实查证据 | 后果 |
|------|---------|------|
| **无缓存** | `jzl_channels.py` 仅 v2_name 去重；`tikhub.py` 无缓存；唯一缓存设施 `attribution_cache.py` 只缓存视听分析结果，不缓存 API 响应 | 同一对象跨任务重复扣费 |
| **无成本闸** | `base.cost_hint()` 只用于事后给 `billing.premium_data` 报价（`pipeline.py:164`），调用前不估算、不拦截、无日预算 | 跑飞了不会停 |
| **批量未用** | `tikhub.py:172` `fetch_batch_douyin_stats()` 已定义（$0.025/50条）但 account_chain 仍走单条循环（$0.001×N） | play_count 补充多花一倍 |

### 1.3 计费埋点落到哪一步（metering 现状）

cost-metering 设计 7 项落码清单，实查仅 2 项完成：

| 清单项 | 状态 |
|--------|------|
| ① `metering.py` record()/summarize() | ✅ 完成（但只被 LLM 调用方使用） |
| ② datasources 出口埋点 | 🔴 **未做**（数据源调用不写 metering） |
| ③ `probe_cost_events` 表 | ✅ 完成（含 `cache_hit`/`retry_seq`/`fallback_of` 字段，已为缓存预留） |
| ③ `probe_cost_daily` 聚合表 | 🔴 未做 |
| ④ 日聚合 job / ⑤ 看板 / ⑥ 阈值配置 / ⑦ 对账回填 | 🔴 未做 |

→ `probe_cost_events` 表是空的，所以现在**无法逐笔对账**（呼应"看不到 ¥5.7 花在哪"）。

---

## 二、统一切面架构：HTTP 底层 source_cache（⚠️ 审核修正）

### 2.1 切面挂载点（实查 + 审核纠正）

**原设计拟挂 `registry.get_adapter()` / `fetch_metadata` —— 审核证伪**：

```
路径A（l0 取数）：l0.get_adapter(kind) → adapter.fetch_metadata(url, kind)
路径B（业务链）：wechat_chain.py:28 / account_chain.py:142 直接 JZLChannelsAdapter()
                 → 裸调 fetch_account_search / fetch_v2_name / fetch_article_* ...（¥0.9 三步桥等花钱大头）
```

- `get_adapter()` 只被 l0 两处调用；**services 业务链直接 `JZLChannelsAdapter()` 裸调，绕过 `fetch_metadata`**。
- 故挂在 `get_adapter`/`fetch_metadata` 只能覆盖路径A，**漏掉路径B 的付费大头**。
- **真正的唯一收口 = adapter 的 HTTP 底层方法**：JZL 的 `_post_json`（search/principal/history/article_detail/comment/v2_name 全经它）、`_post_form`（wxvideo）、read_zan GET；TikHub 的 SDK 调用。两条路径最终都汇于此。
- **额外红利**：底层方法带 `path` 参数 → 天然**端点级 TTL**（`article_detail` 永久 vs `read_zan` 1h），比 fetch_metadata 粗粒度更省更精确；且 registry/l0/chain **全部零改动**。

### 2.2 source_cache.cached_call 三步流水（每个付费 HTTP 出口都走）

```
cached_call(source_id, endpoint, params, fetch_fn, cost_cny):
  1. cache 查  —— TTL>0 且命中未过期 → 返回深拷贝副本（埋点 status=cached, cache_hit=true, cost=0）
  2. live 调用 —— 调 fetch_fn()（原 HTTP 闭包）；抛异常 → 埋点 fail、不缓存、重抛
  3. 记账+存  —— 埋点 metering.record_datasource(surface=datasource)；成功结果按端点 TTL 写 cache
```
- **TTL 默认 0（不缓存）**：仅 `_TTL` 表登记的安全端点缓存；`get_remain_money` 等实时端点 TTL=0。
- **数据等价**：内容不变型长 TTL、时变型短 TTL、`force_refresh` 旁路、深拷贝防污染、只缓存成功。

### 2.3 实际改动集（P0 已落地）

| 文件 | 改动 |
|------|------|
| `app/datasources/source_cache.py` | **新建** `cached_call`（端点级缓存 + 计费埋点收口） |
| `app/services/metering.py` | **新增** `record_datasource()`；`_pg_insert` 兼容 datasource event（units/cost_real） |
| `app/datasources/jzl_channels.py` | `_post_json`/`_post_form`/read_zan GET 包 `cached_call` + 端点成本表 `_JZL_COST` |
| `app/datasources/tikhub.py` | `fetch_metadata` 的 SDK 调用包 `cached_call`（按 url 端点级缓存） |
| `tests/test_source_cache.py` | **新建** 11 项单测（命中/TTL/等价/隔离/失败/埋点/开关） |

> registry / l0 / wechat_chain / account_chain **零改动** —— 切面下沉到 HTTP 底层的直接收益。
> 成本闸 + 配额（原 2.2 步骤 3）下沉为 P1：在 `cached_call` 真调前加预算检查即可，不改架构。

---

## 三、缓存层设计（数据等价的核心）

**唯一可能"影响结果"的优化是缓存**——缓存了旧值就可能和实时真调不一致。靠**按数据不变性分级 TTL + force_refresh 旁路**保证等价。

### 3.1 端点不变性分级（实查端点经济学）

| 端点 | 单价 | 不变性 | TTL | 缓存键 | 等价论证 |
|------|------|--------|-----|--------|---------|
| `article_detail` | ¥0.045 | **内容不变型** | 永久 | url | 文章发布后正文不变，缓存值=真调值 |
| `principal_info` | FREE | 内容不变型 | 永久 | ghid | 企业主体信息变更罕见 |
| `history_by_ghid?get_finder=1` | ¥0.5 | 内容不变型 | 永久 | ghid | 公众号↔视频号绑定关系固定 |
| `wx_account/search` | ¥0.2 | 准不变 | 7 天 | keyword | fans/avg_read 周级更新，7天内可接受 |
| `wxvideo` type=1（列表） | ¥0.2/页 | 时变型 | 6 小时 | v2_name+page | 新视频持续发布 |
| `read_zan`（阅读量） | ¥0.04 | 时变型 | 1 小时 | url | 阅读量小时级增长 |
| `article_comment2` | ¥0.06 | 时变型 | 1 小时 | url+page | 评论新增 |
| `wxvideo` type=4（搜索） | ¥0.5 | 时变型 | 12 小时 | keyword | 搜索排序日级变化 |
| `get_remain_money` | FREE | 实时 | **不缓存** | — | 余额必须实时 |
| TikHub `video_data`/`statistics` | $0.001 | 时变型 | 1 小时 | aweme_id | 播放/点赞实时增长 |

### 3.2 数据等价的三道保险

1. **TTL 分级**：内容不变型才永久缓存（与真调严格等值）；时变型短 TTL，过期即重取。
2. **force_refresh 旁路**：调用方可传 `force_refresh=True` 跳过缓存——需要实时快照（如发报告前刷阅读量）时保证拿真值。
3. **TTL 可配 + 默认偏保守**：阈值进配置表（落码清单⑥），分析口径若要更高新鲜度可整体调低，不改代码。

### 3.3 存储

- 复用 metering 的 PG（`probe_collect`），新建 `probe_source_cache(source_id, cache_key, kind, response_json, fetched_at, ttl_s)`，主键 `(source_id,cache_key)`。
- PG 不可达 → 回落进程内 LRU（与 metering 回落 JSONL 同思路，不阻塞主流程）。
- **顺带修**：metering 现在每次 `psycopg.connect()` 新建连接，缓存层引入轻量连接池，两者共用。

---

## 四、成本闸 + 配额（不影响结果的拦截）

- **预估**：调用前累加 `cost_hint`，对照 `task_budget` / `daily_budget`（配置表，默认日 ¥10）。
- **fail-loud 而非静默丢**：超限时**停下来 + 告警 + 写 metering status=skipped**，绝不返回残缺数据冒充成功——所以不会产出"错误结果"，只会明确"未采"。这是"不影响结果"的关键：要么拿到完整真值，要么明确报缺，没有中间的脏数据。
- **高价端点门控**：`kw_search`/`hot_typical_search`/`web_search`（¥0.5）、`original_article_count`（¥1.0）默认进确认白名单，非显式开启不调。

---

## 五、批量优化（TikHub 专属 + JZL 分页）

| 源 | 优化 | 省费 | 等价性 |
|----|------|------|--------|
| **TikHub** | account_chain 聚合 aweme_id 后统一调 `fetch_batch_douyin_stats`（已定义未用），替代单条循环 | 100 条 $0.10→$0.05（**省 50%**） | 批量端点返回字段与单条一致 |
| **TikHub** | play_count 注入：批量拿统计，仍只对 douyin 注入（逻辑不变） | 同上 | play_count 取值不变 |
| **JZL** | `history_by_ghid` 已用分页（¥0.02/篇 vs 单篇 ¥0.045），无需改 | 已优 | — |

---

## 六、metering 落码补全（对账闭环）

补设计清单②③④⑤⑦，让"看得见花在哪"：

1. **数据源埋点**（②）：代理第 5 步调 `metering.record(surface="datasource", source_id, kind, units={req:1}, cost_real, cache_hit, ...)`。
2. **`probe_cost_daily`**（③④）：日聚合 job 按 (date, source_id, status) 汇总。
3. **对接 ops 看板**（⑤）：ops-brain 新增"数据源用量"读 `probe_cost_daily`，与已上线的**余额监控卡**互补——余额卡看"还剩多少"，用量看板看"每笔花在哪"。
4. **桩值→真账单对账**（⑦）：cost_hint 是桩值，定期用 dajiala 后台流水 / TikHub `get_user_daily_usage` 回填 `unit_cost` 真值。

---

## 七、JZL ↔ TikHub 对称处理矩阵

| 能力 | JZL | TikHub | 实现位置 |
|------|-----|--------|---------|
| 余额监控（已上线） | ✅ `get_remain_money` | ✅ `get_user_info.balance` | ops-brain balance API |
| 统一缓存切面 | ✅ | ✅ | CostControlledAdapter（同一代理） |
| 成本闸/配额 | ✅ | ✅ | 同上 |
| metering 埋点 | ✅ surface=datasource | ✅ surface=datasource | 同上 |
| 批量优化 | 分页（已优） | `fetch_batch_douyin_stats` 接入 | adapter 内 |
| 高价端点门控 | kw_search/original_article_count | （TikHub 单价低，暂无） | 闸白名单 |

> ⚠️ **TikHub 落地前置**：ledger.yaml 中 TikHub `status: pending`（probe 生产 `PROBE_TIKHUB_KEY` 待注入）。余额端点已用 vault 的 probe-smoke key 实测通（$19.92），但生产采集激活仍需按 R8/R1 完成 key 注入。缓存/闸/批量的代理层代码不阻塞，key 到位即生效。

---

## 八、落地分期（按 ROI）

| 期 | 内容 | 预期效果 | 状态 |
|----|------|---------|--------|
| **P0** | `source_cache.cached_call`（端点级缓存）+ 数据源 metering 埋点 | 重复对象省 50-80%；对账可见 | ✅ **已落地**（11 单测全过·零网络） |
| **P0** | TikHub SDK 调用缓存 | 同 url 重复解析省 | ✅ 已落地（live 待 key） |
| **P0+** | TikHub 单条 play_count 纳入缓存（同 aweme_id 1h 不重复扣费） | 重复 play_count 省 | ✅ 已落地 |
| **P0+** | TikHub 批量 `fetch_batch_douyin_stats` 接 account 级多视频 | play_count 补充省 50% | 🚧 阻塞：account 级多视频 play_count 走 `combo_deep_probe` 独立包（不在 probe 仓），且 TikHub key pending。批量方法已就绪待该侧接入 |
| **P1** | 成本闸 + 日预算（`PROBE_DAILY_BUDGET_CNY`，默认 ¥10·超则 fail-loud） | 防跑飞，硬上限 | ✅ 已落地（4 单测） |
| **P1** | `probe_cost_daily` 聚合视图 + `summarize_datasource()`（命中率/省费/拦截） | 逐笔明细+省费量化 | ✅ 已落地（视图+PG/JSONL 双路·1 单测） |
| **P1** | ops 用量看板（消费 `summarize_datasource`） | 可视化 | ⏳ 待做（需定 probe→ops 数据路径：probe HTTP 暴露 vs ops 连 probe-a PG） |
| **P2** | 真账单对账回填 unit_cost | 桩值→真值 | ⏳ 待做 |

### 落地补记（2026-06-22）

- **新增 env 旋钮**：`PROBE_SOURCE_CACHE`（缓存总开关）、`PROBE_COST_GATE`（闸开关）、
  `PROBE_DAILY_BUDGET_CNY`（日预算）、`PROBE_TTL_<端点>`（按端点调 TTL）。全部有保守默认。
- **成本闸语义**：超日预算 → 抛 `source_cache.BudgetExceeded`（fail-loud），埋点 `status=skipped`，
  绝不返回残缺数据冒充成功（守数据等价）。免费端点、缓存命中不受闸。
- **DB migration**：`migrations/002_probe_cost_daily.sql`（视图·幂等·无需调度 job）。

**单账号完整微信情报包**估算：现 ~¥0.95 → 优化后 ~¥0.3-0.5（**省 40-50%**），且数据完整度不变。

---

## 九、数据等价总验收

每项优化的"不影响结果"判据，上线前逐条验：

| 优化 | 验收方法 |
|------|---------|
| 内容不变型缓存 | 同 url 缓存命中值 vs force_refresh 真调值，逐字段 diff = 0 |
| 时变型 TTL 缓存 | TTL 内命中；TTL 外自动重取；force_refresh 必拿真值 |
| 成本闸 | 超限时返回 status=skipped（明确报缺），绝无残缺数据冒充 success |
| 批量替代单条 | 批量结果 vs 单条结果同字段同值 |
| metering 埋点 | 埋点不改变 fetch_metadata 返回值（只旁路记账） |

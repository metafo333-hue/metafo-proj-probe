# probe 合规门 · 四赛道准入门定义 v1.0

> 日期：2026-06-11 · 性质：**Guardian 安全引擎的可执行检查项** —— ledger `tracks.*.verify_profile` 的落地定义。
> 上游：[运行时架构 §8.1 分层智能(安全用规则)](probe-datasource-runtime-architecture-v1.0.md) · [赛道架构 §8.1 合规红线](probe-track-registry-architecture-v1.0.md) · [F 金融设计 §3.5](finance-track-f-design-and-competitive-v1.0.md)
> 🔴 铁律：合规门是**确定性规则**，不交给概率模型；智能只能加拦截、不能放松(运行时 §8.1)。

---

## 0. 通用结构（每个门都含三件）

```
准入五问(新源进该赛道前逐项过·全 yes 才允许 status: cataloged→vetting)
 ① 数据公开合规获取(非代爬·穿透上游)？
 ② 是否存在为违规行为导流的风险？
 ③ 个保法最小必要(是否采集个人敏感数据)？
 ④ 是否触碰持牌/资质红线？
 ⑤ exclude_categories 黑名单品类是否已在端口层落标记？
+ 红线清单(该赛道禁做)
+ exclude_categories(黑名单品类·永不采集/呈现)
```

---

## 1. `finance-8gate` · 金融 F

- **准入门**：F 双审 8 闸(见 [finance 设计 §2.5](finance-track-f-design-and-competitive-v1.0.md))
- **红线**：不荐股、不导流非持牌、6 红线(F 设计 §3.5)
- **exclude_categories**：`[场外配资, 非法荐股, 虚拟币传销盘]`
- **persist_policy**：行情/公开数据 normal；个人持仓/账户 → ephemeral

## 2. `deal-compliance-gate` · 元惠 G

- **红线**：禁虚假比价(先涨后降)、禁失效券引流、禁刷返利、守各联盟 ToS
- **exclude_categories**：`[刷单返现, 资金盘返利]`
- **专属验证**：`deal-pricefraud-gate`(历史价对比防虚标 / 券可用性实测 / 返利兑现核验 / 全网最低真比价)
- **persist_policy**：价格/促销数据 normal

## 3. `task-compliance-gate` · 任务 H（🔴 灰产防火墙·全板块合规风险最高）

- **红线**：
  - 只做**合规任务规则情报**(整理各平台官方任务有哪些规则/奖励)
  - ❌ 禁为刷单/灰产/资金盘**导流**
  - ❌ 禁教唆违反平台 ToS 薅羊毛
  - ❌ 不收集任务参与者个人数据
- **exclude_categories**：`[刷单刷量, 拉人头传销, 高额返利诱充, 批量账号薅羊毛, 博彩资金盘任务]`
- **特别**：候选源**先过本门再进调研**——灰产源不浪费调研/采集资源(降本×安全协同，运行时 §五)
- **persist_policy**：任务规则 normal；参与者数据 → 禁采集

## 4. `ai-deal-gate` · AI 优惠 I

- **红线**：
  - **永不代爬**：awesome-list 走 commit atom RSS / 官方 API(GitHub/HF/Kaggle)，禁 HTML 代爬
  - ❌ 禁 **key 倒卖/共享源**(如 `alistaitsacle/free-llm-api-keys` 类——分发第三方 API key 违各厂 ToS)
  - license 合规：CC-BY-NC 商用弃；开源模型走商用 license 白名单(apache/mit/bsd…)
- **exclude_categories**：`[API-key倒卖, 共享account, 非授权镜像站]`
- **persist_policy**：优惠/规则数据 normal

---

## 5. 与运行时的接口（Guardian 两次出场）

| 出场 | 环节 | 用门做什么 |
|------|------|-----------|
| **预检** | 选源前(生命周期 ①) | 候选源过该赛道 `verify_profile` 五问 + 红线 → 不过则**挡掉**(不进 Governor 选源) |
| **落库** | 验证后(生命周期 ⑤) | 按 `persist_policy` 决定能否写 PG(敏感→ephemeral 禁库) |

> Guardian 读 SCT 的**合规维**(`safety: {license, persist_policy, crawl, pii, gate}`)执行。门的判定结果回填 SCT，复用不重判。

---

## 附：SCT 源能力表 ↔ ledger 映射（SCT 不另起·以 ledger 为载体）

SCT 四维**大部分已存在于 ledger 条目**，只需补缺字段：

| SCT 维 | ledger 现有字段 | 待补字段 |
|--------|----------------|---------|
| 成本维 | `access_type` · `cost` | `cache_ttl` · 计量口径 |
| 性能维 | `freshness` | `latency_p50/p95` · `rate_limit` · `hedging_eligible` |
| 可靠维 | `authority_score` | `reliability`(在线学习) · `freshness_window` · `dedup` |
| 合规维 | `license` · `status` | `persist_policy` · `crawl` · `pii` · `gate`(=verify_profile) |

> 结论：**SCT = ledger 条目的运行时四维视图**，不新建分裂的表；接源时按上表补全四维即可。

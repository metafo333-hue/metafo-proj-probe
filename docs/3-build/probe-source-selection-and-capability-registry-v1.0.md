# probe · 数据源选型决策 + 能力价值目录设计（方案 · 未落码）v1.0

> 日期：2026-06-10 · 性质：**设计方案**（本轮只设计·S1 落码点见 §八）
> 回答元东方：「**付费/免费调用怎么界定与选择？是不是每个 API 能做什么、价值多少都要存好一个列表用于快速选择判断？**」
> 关系：API 调取治理体系第 4 份 · 上游问题库 [risk-checklist](probe-api-fetch-risk-checklist-v1.0.md)（C7/C8/F1/Q1 选型相关坑）· 选源是 [dynamic-governance](probe-data-dynamic-governance-design-v1.0.md) §三闸④「合规门+选源」的深化 · 成本单价接 [cost-metering](probe-cost-metering-design-v1.0.md)
> 哲学母本：[speed-depth-tiering §三](probe-speed-depth-tiering-v1.0.md)（默认兜底+确定性自评+按需升级）——本文把它从「选哪版」下沉到「选哪个源（免费/付费）」

---

## 一、两个回答（先给结论）

### Q1 · 付费 vs 免费怎么界定选择？
**不是让用户预选「我要免费/付费」，而是 Governor 按信号分层智能选源**：

```
默认免费兜底 ──覆盖够+置信够──▶ 直接交付（零成本）
   │ 不够（免费源覆盖不了 / 置信度低 / 时效要求高 / 用户付费档 / blast高）
   ▼ 升级付费源 ──成本门通过──▶ 调付费（计量入账）
   │ 超额/未授权/限流
   ▼ 降级阶梯：付费→免费→缓存→占位（永不违规爬·永不拒服务）
```

> 一句话：**免费优先、不够才付费、付费有门、超了能降**——资源匹配任务真实需要，和 speed-depth「极速兜底/按需升级」同构。

### Q2 · 要不要建「能力×价值×成本」列表存好快速选？
**要——而且 probe 雏形已有，差三个字段就能驱动决策**（见 §二）。这个列表 = **数据源能力价值目录**，是 Governor 选源的「快速查表」依据，避免每次临时判断。

---

## 二、现状：雏形已有，差三样（诚实盘点）

[ledger.yaml](../../app/datasources/ledger.yaml) 每源已登记，[catalog.py](../../app/datasources/catalog.py) 已能按维度查：

| 已有字段 | 作用 | 选型够用？ |
|---------|------|-----------|
| `domain` D1-D17 | 覆盖哪个信息域 | ⚠️ 太粗（域级，非能力级）|
| `access_type` free/paid/*_with_key | 免费还是付费 | ✅ 选型基础 |
| `authority_score` 1-10 | 权威度 | ✅ 排序用 |
| `freshness` realtime/daily/.. | 时效 | ✅ 接 TTL |
| `cost` 文本 | 价格 | 🔴 **非结构化·机读不了** |
| `status` live/pending/.. | 可用性 | ✅ |
| `supported_kinds` | 支持类型 | ✅ |

**差的三样（补上才能机读选型）**：
1. **`capability`（能力标签）** — 比 domain 细：这源具体能回答什么问题（如 `[公司财报, 13F持仓, 高管信息]`），用于精准匹配任务需求。
2. **`value_score`（数据价值 1-10）** — 区别于权威度：**独家性/深度**（付费源凭什么值钱 = 免费拿不到的深度）。
3. **`free_quota`（结构化免费额度）** — tikhub 现在「送约50次」写在 `cost` 文本里，governor 读不了。结构化成 `{daily, total, reset, remaining}`，才能判断「免费额度还剩几次、该不该升付费」。

---

## 三、付费/免费分层决策框架（核心）

### 3.1 升级到付费的触发信号（满足任一 → 评估升付费）
| 信号 | 判断 | 来源 |
|------|------|------|
| **覆盖缺口** | 免费源 capability 覆盖不了任务需求 | 能力目录匹配 |
| **置信不足** | 确定性自评 < 阈值（单源/源冲突/无交叉）| audit 自评(信号③)|
| **时效要求** | 任务要 realtime 但免费源只有 daily | freshness 比对 |
| **用户档位** | 付费用户/深度版任务 | billing 档(信号①)|
| **blast 高** | 决策/尽调/对外 → 要可溯源可证伪 | MetaAsk blast |

> **任一不满足 → 留在免费档**（默认兜底）。**满足 → 进 3.3 成本门**，不是无脑升。

### 3.2 同域多源排序（怎么从候选里挑）
Governor 对命中同一需求的候选源算**选型综合分**，取最优：

```
select_score = w1·authority_score      (权威)
             + w2·value_score          (价值/独家深度)
             + w3·freshness_match      (时效匹配任务)
             - w4·cost_factor          (成本·免费=0)
             - w5·quota_pressure       (免费额度剩余越少越降权)
             - w6·compliance_risk      (合规债/再分发限制扣分)
权重 w 按任务 blast 动态调：blast高→value/freshness 权重升、cost 权重降
```

> 「智能」体现：随手查 → cost 权重高（挑免费）；尽调 → value/freshness 权重高（该付费就付费）。

### 3.3 成本门（升付费前最后一道·堵 C7/C8/Q1）
- **R1 授权检查**：付费源未过 R1 → 不调，走免费降级或占位（L1）。
- **额度检查**：用户/任务/源额度（接埋点信号①）→ 超额则降级。
- **自动扣费雷**：试用/订阅类（Trading Economics）→ 强制 R1 人工确认（C7）。
- **免费额度优先耗用**：付费源若有免费额度（tikhub 50次）→ 先用 `free_quota.remaining`，耗尽才进付费计量。

### 3.4 决策流（一张图）
```
任务需求(capability 需要什么)
   ▼ 能力目录匹配候选源
[免费源覆盖够 + 置信够 + 时效够?] ──是──▶ 选免费(select_score 取优) → 调 → 交付(成本0)
   │否（3.1 触发信号）
   ▼ 3.3 成本门(R1/额度/扣费雷/免费额度优先)
[通过?] ──是──▶ 选付费(select_score 取优) → 调 → 计量入账
   │否
   ▼ 降级阶梯：免费源 → 缓存(标非实时) → 合规占位  ❌绝不违规爬/拒服务
```

---

## 四、能力价值目录 schema（在 ledger 上扩，不另起炉灶）

每源在现有字段基础上**新增 4 字段**（守 R27：CREATE 改了配套同步）：

```yaml
tikhub:
  # ── 现有字段保留 ──
  domain: [D5, D6]
  access_type: paid_with_key
  authority_score: 7
  freshness: realtime
  status: pending
  # ── 新增 4 字段（选型决策用）──
  capability: [短视频元数据, 笔记互动数据, 账号画像, 五平台覆盖]   # 能力标签(细于 domain)
  value_score: 8            # 数据价值(独家深度·国内平台无官方替代→高)
  free_quota:               # 结构化免费额度(替代 cost 文本里的"送50次")
    total: 50
    daily: null
    reset: none
    remaining: 50           # 运行时由埋点回写
  substitutable_by: []      # 可替代的免费源(空=无免费替代→该付费时无可降级·决定升付费必要性)
```

**substitutable_by 是关键**：YouTube 的 tikhub 入口 `substitutable_by: [youtube_official]` → 有免费官方替代 → 选型直接走免费、tikhub 撤出（已对齐 B9 去重图谱）；国内平台空 → 无替代 → 该付费时认了。

---

## 五、源选型决策表样例（同域怎么选 · 接 datasource 清单）

| 信息域 | 免费主力（默认） | 付费升级（触发条件） | 触发信号 |
|--------|----------------|---------------------|---------|
| D11 企业财务 | edgartools/OpenCorporates/Companies House | 天眼查/企查查(中国工商深度) | 免费源不覆盖中国主体 |
| D13 金融行情 | Frankfurter/FRED/DeFiLlama/CCXT | Polygon/AlphaVantage(美股实时) | 时效要 realtime + 付费档 |
| D5/D6 自媒体 | YouTube官方/Reddit/oEmbed/播客RSS | tikhub(国内五平台) | 国内平台无官方替代 |
| D14 宏观政策 | SDMX/NBS/官方RSS | Trading Economics(必走R1) | 🔴 扣费雷·强制人工确认 |

> 这张表 = 决策表的人读版；机读版 = §四 schema 字段 + §3.2 select_score 算法，Governor 直接查表选，不临时拍。

---

## 六、与现有体系接通（不重造）

```
能力价值目录(ledger 扩字段) ──catalog.select_source()──▶ Governor 选源信号④⑤
         ▲                                                    │
   埋点回写 remaining/unit_cost ◀──── cost-metering ◀──── 调用后埋点
```

| 组件 | 角色 | 本设计如何接 |
|------|------|------------|
| ledger.yaml | 数据源台账 | 扩 4 字段升级为能力价值目录 |
| catalog.py | 查询层 | 加 `select_source(need, signals)` 选型函数 |
| registry gate19 | 合规门 | 成本门前置合规校验(L1)|
| metering(待建)| 成本 | 回写 `free_quota.remaining` + `unit_cost` 真实值(修 C6)|
| Governor(待建)| 选源执行 | 调 catalog 选型 + 三段闸 |

---

## 七、为什么不让用户自己选免费/付费

| 用户预选 | 本设计·智能选型 |
|---------|----------------|
| 用户得懂每个源能力/价格 | 系统按能力目录+信号自动选 |
| 免费一律差/付费一律好 | 免费够用就免费·该付费才付费 |
| 选错源浪费或不够 | select_score 算最优·降级兜底 |
| 付费雷自己踩 | 成本门拦自动扣费(C7)|

> 用户只表达「要查什么、多重要」（MetaAsk 意图），**选哪个源、免费还是付费、调几次，是系统的事**。

---

## 八、S1 落码点（本轮不写·仅列清单）
1. ledger.yaml 全源补 `capability`/`value_score`/`free_quota`/`substitutable_by`（守 R27 配套同步）
2. `catalog.select_source(need, blast, signals)` 选型函数（§3.2 select_score）
3. Governor 选源闸调用 catalog（接 dynamic-governance §三闸④）
4. 埋点回写 `free_quota.remaining` + `unit_cost`（接 metering）
5. 成本门：R1/额度/扣费雷/免费额度优先（§3.3）

---

## 九、版本/变更记录
| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-06-10 | 分层选型决策框架+能力价值目录 schema(扩 ledger 4 字段)+select_score+决策表·设计定稿(未落码) |

> 一句话回答元东方：**付费/免费不靠用户选、靠系统按「能力价值目录」智能选——目录雏形 ledger 已有，补 capability/value_score/free_quota/substitutable_by 四字段就能机读快速判断；选型规则=免费优先、信号触发升付费、成本门拦雷、降级兜底。**

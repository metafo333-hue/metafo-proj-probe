# probe 数据源板块 · 总册与拓扑（板块导航 SSOT）

> 日期：2026-06-10 · 性质：把散在 `3-build`(架构) + `4-research`(调研) 的全部数据源资料，按**逻辑层次 / 主次关系 / 阅读顺序**串成一张图。
> 定位：**数据源板块的唯一导航入口**——任何人找数据源资料先看本册。
> 范围：1 个真源 + 1 套架构 + 1 套方法论 + 9 赛道调研 + 1 套采集地基 + 横向治理体系。

---

## 0. 一句话

probe 数据源板块 = **五层金字塔**：从「判定什么源能用」(真源) → 「赛道怎么分类」(架构) → 「怎么找/审/接」(方法论) → 「9 赛道实际有哪些源」(调研) → 「怎么持续自动采集」(采集地基)。**从抽象判定到落地采集，逐层收敛。**

---

## 一、整体逻辑：五层结构（主线）

```
L0 真源层   ── 一切判定的根(SSOT)：能不能用、合规不合规
L1 架构层   ── 赛道怎么分类、源归哪个域
L2 方法论层 ── 怎么找源、怎么审源、分几批接
L3 调研层   ── 9 赛道实际调研出的真实源清单
L4 采集层   ── 源怎么持续自动化采集(可订阅注册表)
─────────────────────────────────────────────
横向治理     ── 选型/成本/可靠性/管控(贯穿 L0-L4)
```

| 层 | 职责 | 核心文档 |
|----|------|---------|
| **L0 真源** | 数据源判定唯一标准 + 接入门 + 去重 | [feasibility-v1](probe-github-datasource-feasibility-v1.md)(5 域·6 范式·合规红线) · [gate19+去重](datasource-gate19-and-dedup-v1.0.md)(标准19 接入门) · `app/datasources/ledger.yaml`(域与源状态·代码层真源) |
| **L1 架构** | 9 赛道三层分类、源归域 | [track-registry-architecture v1.1](../3-build/probe-track-registry-architecture-v1.0.md)(type/tier/weight/presentation + D 域 + 边界裁定) |
| **L2 方法论** | 找/审/接的标准动作 | [研究方法论 v1.1](datasource-research-methodology-v1.0.md)(三层优先级 + 四审核闸 + 机器可读源卡) · [分批次对接计划](datasource-research-onboarding-batch-plan-v1.0.md)(6 批次 B0-B5) |
| **L3 调研** | 9 赛道真实源清单 | A/B/C/D/E/F/G/H/I 九份赛道报告(见 §五矩阵) |
| **L4 采集** | 持续自动化采集地基 | [I 分类+GitHub策略](datasource-aideal-track-i-classification-v1.md) → [I 源注册表](datasource-aideal-source-registry-v1.md)(35 源 YAML + 五路采集架构) |
| **横向治理** | API 调取治理体系 | [选型能力价值目录](../3-build/probe-source-selection-and-capability-registry-v1.0.md) · [成本埋点](../3-build/probe-cost-metering-design-v1.0.md) · [源运维可靠性](../3-build/probe-source-ops-and-reliability-design-v1.0.md) · [数据动态管控](../3-build/probe-data-dynamic-governance-design-v1.0.md) · [API风险清单](../3-build/probe-api-fetch-risk-checklist-v1.0.md) |
| **⭐ 运行时控制平面** | 把上述各层编排成统一运行时 | [**数据源运行时架构(四引擎·高效准确安全降本协同)**](../3-build/probe-datasource-runtime-architecture-v1.0.md)——SCT源能力表 + 四引擎(Governor/Orchestrator/Validator/Guardian) + 请求生命周期 |

---

## 二、主次关系（真源 vs 派生 · 冲突裁定）

```
唯一真源(SSOT)
 ├─ feasibility-v1      ← 数据源「能不能用/合规」判定真源
 └─ ledger.yaml(代码层) ← 域定义(D1-D17)与源状态(live/pending)真源
        │
        ▼ 一级派生(不可与真源冲突)
   track registry 架构 · 研究方法论 · 批次计划 · gate19 接入门
        │
        ▼ 二级派生(各赛道深化·同源不悖)
   9 赛道数据源调研报告(A-I)
        │
        ▼ 三级落地(采集实现)
   I 源注册表(GitHub-First 采集地基)
        │
        ▼ 应用产物(对内降本)
   metafoclaw 自用 AI 资源手册
```

**冲突裁定铁律**：任何下游文档与 `feasibility-v1` / `ledger.yaml` 冲突 → **以真源为准**(如 D 域语义已据 ledger 校准过 D9 误标)。

---

## 三、阅读顺序（按读者分）

| 读者 | 目的 | 路径 |
|------|------|------|
| **决策者** | 看全局/拍板 | 本总册 → [架构 §3 注册表](../3-build/probe-track-registry-architecture-v1.0.md) → §五 9 赛道矩阵 |
| **调研员** | 找源/补调研 | [方法论](datasource-research-methodology-v1.0.md) → [批次计划](datasource-research-onboarding-batch-plan-v1.0.md) → 对应赛道报告 → [源注册表](datasource-aideal-source-registry-v1.md) |
| **工程师** | 接入/采集 | [gate19 标准19](datasource-gate19-and-dedup-v1.0.md) → [源注册表 §四采集架构](datasource-aideal-source-registry-v1.md) → `ledger.yaml` |
| **运营** | 薅羊毛降本 | [metafoclaw 自用手册](metafoclaw-ai-resource-playbook-v1.md) |

---

## 四、文档拓扑图

```
┌──────────────────────────── L0 真源层 (SSOT) ────────────────────────────┐
│  feasibility-v1                gate19+去重           ledger.yaml(代码层)  │
│  数据源判定真源·5域6范式        标准19接入门·源去重    域D1-D17·源状态     │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │ 派生·不可冲突
┌───────────────────────────────────▼─────────── L1 架构层 ────────────────┐
│  track-registry-architecture v1.1                                        │
│  9赛道分类(横向A-E + 旗舰F/G/H/I) · type/tier/weight/presentation · D域   │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────── L2 方法论层 ──────────────┐
│  研究方法论v1.1(三层优先级·四审核闸·源卡)  ──┐                            │
│  分批次对接计划(B0底座→B5付费源)            ──┘ 指导下层怎么调研           │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │ 产出
┌───────────────────────────────────▼─────────── L3 调研层 ────────────────┐
│  横向业务域:  A自媒体  B商业  C尽调  D调研  E核查                          │
│  垂直旗舰道:  F金融   G元惠  H任务  I·AI优惠                               │
│              (9 份赛道数据源报告 · 共 ~3300 行)                            │
└───────────────────────────────────┬──────────────────────────────────────┘
                                    │ I赛道深化(GitHub-First)
┌───────────────────────────────────▼─────────── L4 采集层 ────────────────┐
│  I分类+GitHub策略 → I源注册表(35源·YAML订阅·五路采集架构)                 │
│                          └→ metafoclaw自用手册(对内降本应用)              │
└──────────────────────────────────────────────────────────────────────────┘
   ║                                                                    ║
   ╚═══════ 横向治理(贯穿L0-L4):选型价值目录·成本埋点·源运维·动态管控 ═══════╝
```

---

## 五、9 赛道总览矩阵（一张表看全）

| 赛道 | 类型 | 数据源现状 | 关键结论 | 报告 |
|------|------|-----------|---------|------|
| **A 自媒体** | 横向 | 官方 OAuth 受限·逆向弃 | 走官方 API + 公开热榜 | [A](datasource-selfmedia-track-a-v1.md) |
| **B 商业市场** | 横向 | 诊断层免费·电商/App 付费 | 开源诊断层零成本(wappalyzergo/sitespeed) | [B](datasource-business-b-v1.md) |
| **C 尽调风控** | 横向 | 制裁开源·工商需资质 | 🔴 人物 OSINT 红线 ephemeral | [C](datasource-diligence-c-v1.md) |
| **D 调研知识** | 横向 | ⭐**免费源最丰富** | OSV/OpenAlex/Docling 全免费 | [D](datasource-research-d-v1.md) |
| **E 真伪核查** | 横向 | 核查源丰富·NC 商用红线 | 商业化三切换(VirusTotal/GSB/OpenPhish) | [E](datasource-verify-e-v1.md) |
| **F 金融** | 旗舰 | 设计完整 27+ 源 | 双审 8 闸·部分付费 R1 | [F](datasource-finance-track-f-v1.md) |
| **G 元惠** | 旗舰 | 联盟 API 成熟需 R4 | 中国电商三联盟批量申请 | [G](datasource-deal-track-g-v1.md) |
| **H 任务** | 旗舰 | 规则源结构性稀缺 | 自建工具 + RSSHub 监测 | [H](datasource-task-track-h-v1.md) |
| **I AI 优惠** | 旗舰 | ⭐**GitHub 源最优** | 35 源注册表·GitHub-First 采集 | [I内容](datasource-aideal-track-i-v1.md)·[I分类](datasource-aideal-track-i-classification-v1.md)·[I注册表](datasource-aideal-source-registry-v1.md) |

> 两极反差：**D/E/I 域免费开源源极丰富**(直接零成本起步)；**G/H 旗舰道源稀缺或需资质**(联盟 R4 / 自建)。

---

## 六、全量文档索引（按层归类）

**L0 真源**：feasibility-v1(216) · gate19+去重(151)
**L1 架构**：track-registry-architecture v1.1
**L2 方法论**：研究方法论 v1.1(219) · 分批次对接计划(204)
**L3 调研**：A(196) · B(584) · C(351) · D(285) · E(282) · F(240) · G(402) · H(558)
**L4 采集**：I内容(325) · I分类(90) · I源注册表(799) · metafoclaw自用手册(263)
**横向治理**：选型价值目录 · 成本埋点 · 源运维可靠性 · 数据动态管控 · API风险清单

---

## 七、当前状态与下一步

**✅ 已完成**：9 赛道数据源调研全覆盖 · I 赛道 GitHub-First 源注册表(35 源·五路采集架构) · 板块逻辑梳理(本册)

**✅ 已落地(2026-06-11)**：
1. ✅ `ledger.yaml` v5 加 `tracks:` 段(9 赛道) + 域 D15/D16/D17 — **实测通过·零悬空引用**
2. ✅ 三合规门建档 → [compliance-gates v1](../3-build/probe-compliance-gates-v1.md)(deal/task/ai-deal + SCT↔ledger 映射)

**⬜ 待落地(下一步·代码层运行时)**：
3. M0 实跑：实现四引擎(Guardian 合规门 + Governor 免费阶梯 + 缓存)，按 §四采集架构接 D/E/I 零成本源(SCT 以 ledger 条目为载体，补四维字段)
4. 真实平台清单按 SSOT 落镜像层 `metafoclaw-git/docs/engines/probe/1-inventory/`

> 维护纪律：新增赛道/源 → 先过 L0 真源判定 → 落对应层 → 回填本总册 §五矩阵 + §六索引。

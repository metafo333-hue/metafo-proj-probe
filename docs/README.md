# probe 文档目录（docs/）· 分类导航

> 2026-06-08 建立分类目录骨架 · 对齐镜像层 `metafoclaw-git/docs/engines/probe/` 范式（源↔镜结构一致，投影最简）
> SSOT：本目录（`probe/docs/`）= **authoring 源** · 镜像层 = 投影（治理规则见 [records/ssot-governance](records/probe-ssot-governance-v1.md)）

---

## 📖 入口

**① 数值/术语冲突先查** → [records/probe-ssot-master-reconciliation-v1.0.md](records/probe-ssot-master-reconciliation-v1.0.md)（**SSOT 事实仲裁总册** · 域17/赛道9/闸8/阶段/命名 + 阶段换算表 + 门闸对照表 + L1-L4↔四引擎映射 + 矛盾处置 + 编排接口缺口）
**② 工程执行入口** → [probe-master-solution-v2.md](probe-master-solution-v2.md)（总册·把分散文档收敛成一份，含完整文档地图）
**③ 愿景宪法** → [0-charter/probe-vision-from-dialogue-v1.0.md](0-charter/probe-vision-from-dialogue-v1.0.md)（愿景唯一真源）

---

## 🗂 分类目录（按文档生命周期 0 → archive）

| 目录 | 类别 | 内容 | 现状 |
|------|------|------|------|
| **0-charter/** | 立项总纲 / 愿景 | [founding-charter-v1.0](0-charter/founding-charter-v1.0.md)（立项全本）· [vision-from-dialogue-v1.0](0-charter/probe-vision-from-dialogue-v1.0.md)（愿景真源·魂） | ✅（vision-v1.0 冗余已归档 2026-06-11） |
| **1-inventory/** | 现状盘点 | [probe-inventory-v1.0](1-inventory/probe-inventory-v1.0.md) | ✅ |
| **2-roadmap/** | 路线图 | [launch-roadmap](2-roadmap/probe-launch-roadmap.html)（术语升级中·上线作战图） | ✅（upgrade-plan 旧代次已归档 2026-06-11） |
| **3-build/** | 架构 · 构建 · 设计 | [design-v1](3-build/probe-intelligence-engine-design-v1.md) · [**赛道注册表架构v1.1(9赛道·三层分类·元惠/任务深挖·合规/边界/路由补强)**](3-build/probe-track-registry-architecture-v1.0.md) · [**⭐数据源运行时架构v1.1(四引擎控制平面+智能控制层·高效准确安全降本·越用越优)**](3-build/probe-datasource-runtime-architecture-v1.0.md) · [合规门定义(4赛道准入门·Guardian依据)](3-build/probe-compliance-gates-v1.md) · [audit-system-v1](3-build/probe-audit-system-v1.md) · [api-v1](3-build/probe-api-v1.md) · [金融F设计竞调](3-build/finance-track-f-design-and-competitive-v1.0.md) · **API调取治理体系(5份)**：[风险清单(活文档gate·v1.2/55坑)](3-build/probe-api-fetch-risk-checklist-v1.0.md) · [成本埋点设计](3-build/probe-cost-metering-design-v1.0.md) · [选型与能力价值目录](3-build/probe-source-selection-and-capability-registry-v1.0.md) · [数据动态智能管控设计](3-build/probe-data-dynamic-governance-design-v1.0.md) · [源运维与可靠性](3-build/probe-source-ops-and-reliability-design-v1.0.md) · **并发编排/调度体系(2份)**：[编排引擎方案](3-build/probe-orchestration-engine-solution-v1.0.md) · [需求规格](3-build/probe-orchestration-concurrency-requirements-v1.0.md) · **工程纵深设计体系(5份·2026-06-10查漏补全)**：[数据脊柱(持久化+缓存)](3-build/probe-data-persistence-and-cache-design-v1.0.md) · [质量评测方法论](3-build/probe-quality-eval-methodology-v1.0.md) · [隐私留存合规工程](3-build/probe-privacy-retention-compliance-engineering-v1.0.md) · [监测雷达+反馈闭环](3-build/probe-monitoring-radar-and-feedback-loop-design-v1.0.md) · [交付形态生成管线](3-build/probe-delivery-rendering-pipeline-design-v1.0.md) · [设计↔实现差距+S1施工清单](3-build/probe-s1-impl-plan-v1.0.md) | ✅ |
| └ **3-build/contract/** | 契约 schema | （真源在 `probe/contract/` 代码层）| ⬜ 空·占位 |
| **4-research/** | 调研 | [**⭐技术栈决策总册(R4产物·28件组合定案·G1-G11全对账·待拍板)**](4-research/techstack-decision-v1.0.md) · [**🛠技术底座GitHub调研作战计划(13模块·tech-gate 12闸·R0-R4波次·含愿景升级v2.1草案)**](4-research/techstack-github-research-plan-v1.0.md) · [底座裁定卡+13张源卡](4-research/techstack-cards/) · [**📍数据源板块总册(五层拓扑·9赛道矩阵·全量索引)**](4-research/datasource-board-master-index-v1.md) · [feasibility-v1（数据源真源）](4-research/probe-github-datasource-feasibility-v1.md) · [金融F数据源](4-research/datasource-finance-track-f-v1.md) · [自媒体A数据源](4-research/datasource-selfmedia-track-a-v1.md) · [gate19+去重](4-research/datasource-gate19-and-dedup-v1.0.md) · [**分批次调研对接计划(6批次·D域校准·元惠/任务端口调研单)**](4-research/datasource-research-onboarding-batch-plan-v1.0.md) · [**调研方法论v1.1(三层优先级·四审核闸·系统要求矩阵·机器可读源卡)**](4-research/datasource-research-methodology-v1.0.md) · **9赛道数据源调研全覆盖(A-I·真源 ledger.yaml v5)**：[元惠G(8端口·15待授权)](4-research/datasource-deal-track-g-v1.md) · [任务H(规则源稀缺·灰产严筛)](4-research/datasource-task-track-h-v1.md) · [商业市场B(6场景)](4-research/datasource-business-b-v1.md) · [尽调风控C(5场景·人物OSINT红线)](4-research/datasource-diligence-c-v1.md) · [调研知识D(5场景·免费源最丰富)](4-research/datasource-research-d-v1.md) · [真伪核查E(4场景·NC商用红线)](4-research/datasource-verify-e-v1.md) · **第九赛道AI优惠**：[**分类+GitHub-First采集策略(8品类端口·源头中心)**](4-research/datasource-aideal-track-i-classification-v1.md) · [**⭐源注册表(35源·YAML订阅清单·五路采集架构)**](4-research/datasource-aideal-source-registry-v1.md) · [AI优惠专项I(各大厂免费额度/创业扶持/监测雷达)](4-research/datasource-aideal-track-i-v1.md) · [⭐metafoclaw自用降本手册(零授权立即薅+扶持申请)](4-research/metafoclaw-ai-resource-playbook-v1.md) · [**🔗短视频认知体系×自媒体A桥接(需求侧↔供给侧映射·分层引用不复制)**](4-research/short-video-playbook-bridge-v1.0.md) | ✅ |
| **6-datasources/** | 数据源接入运营 | [**⭐API参考手册(56源·7维度·接入状态)**](6-datasources/probe-api-reference-v1.0.md) · [**接入排期表(优先级分批·待注册9·待部署7)**](6-datasources/probe-api-integration-schedule-v1.0.md) · [**激活台账(key状态·注册方式·vault路径)**](6-datasources/probe-datasource-activation-log-v1.0.md) · [README](6-datasources/README.md) | ✅ 2026-06-12 |
| **records/** | 治理 · 对齐决策记录 | [**⭐SSOT主仲裁总册**](records/probe-ssot-master-reconciliation-v1.0.md) · [ssot-governance](records/probe-ssot-governance-v1.md) · [alignment-prelaunch](records/probe-alignment-topology-prelaunch-v1.md) · [bizmodel-review](records/probe-value-presentation-and-bizmodel-review-v1.md) · [tikhub-R1授权评估](records/tikhub-r1-authorization-report-v1.0.md) · [读序 README](records/README.md) | ✅ |
| **_archive/** | 归档 | datasource-selection-v1 · solution-design-v2 · master-solution-from-v3.6 · **vision-v1.0** · **upgrade-plan-v1**（均被取代·各带归档声明）| ✅ |

---

## 🧭 各类放什么（资料归位规则）

- **0-charter**：立项初心、愿景、总纲。一个引擎"为什么存在"。
- **1-inventory**：现状家底盘点（已有什么、缺什么）。
- **2-roadmap**：阶段路线图、升级计划、里程碑。
- **3-build**：架构设计、审核体系、对外 API、各赛道设计方案——"怎么做"的权威层。契约 schema 子目录对应 `probe/contract/`。
- **4-research**：数据源调研、可行性、选型、接入核验——"用什么料"的证据层。`feasibility-v1` 是数据源判定**唯一真源**，金融F/自媒体A 是其赛道深化。
- **6-datasources**：数据源接入运营三件套——参考手册（能力速查）·排期表（优先级管理）·激活台账（key 状态）。代码真源始终是 `ledger.yaml`，本目录是人工操作档案。
- **records**：SSOT 治理、对齐核查、决策留痕——"怎么管"的治理记录层。
- **_archive**：被取代的历史版本（命名 `<原名>.archived-YYYYMMDD`），只读留存、不再引用为真源。

---

## ⬜ 空目录说明（类别齐全·资料待补）

| 空目录 | 为何空 | 资料何时补 |
|--------|--------|-----------|
| `3-build/contract/` | 契约 schema **真源在 `probe/contract/`（代码层）**，docs 不放码 | 如需契约说明文档（非 schema 本体）落此 |

> 占位用 `.gitkeep`。目录类别齐全 = 任何新文档都有明确归位，不再平铺堆叠。
> 2026-06-11 整合：原「0-charter/1-inventory 镜像层原生」口径已纠正——按 SSOT「真源在 `probe/docs/`」，立项愿景/盘点的 canonical 已从投影层 `metafoclaw-git/docs/engines/probe/` 收编入本源层（投影层保留副本，下次 re-sync 自源层覆盖即一致）。散落顶层 `probe-master-solution-v2-from-v3.6.md`（v3.6 抽出的旧版总册）已归档至 `_archive/`，被本目录 `probe-master-solution-v2.md`（235 行 canonical）取代。

---

> 维护纪律：新文档按上表归位，不在 docs 根平铺；被取代的旧版移入 `_archive/` 加 `.archived-` 后缀；改动后跑 ssot-governance 的 consistency-gate 校验引用完整性。

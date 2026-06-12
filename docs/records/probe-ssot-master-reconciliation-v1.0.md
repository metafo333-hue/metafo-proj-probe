# probe 文档体系 · SSOT 主仲裁总册 v1.0

> 日期：2026-06-11 · 地位：**进入"系统编排"实施前的对齐基线**。本文是 probe 全部 50+ 份文档的**唯一事实仲裁层**——任何数值/术语/编号冲突，以本文 §1 真源表为准。
> 来历：六路并发审计（集群 A 愿景/B 架构/C 工程纵深/D 构建/E 数据源/F 治理）+ 代码层地基核验（ledger.yaml v5 / gates.py / contract schema · 2026-06-11）。
> 维护纪律：事实只在"真源"处维护，其余文档**引用本表**、禁复制字面值。改真值 = 改真源 + 更新本表，再传播。

---

## §0 一句话与三条裁定原则

**【是什么】** 把六路审计查出的 **3 处已知漂移 + 8 处新矛盾**，按"代码 > 最新权威文档 > 旧文档"一次性钉死真值，并补齐编排实施前缺的 4 张对照表。

**裁定三原则**：
1. **代码即真源**：ledger.yaml / gates.py / contract/*.schema.json 是运行时事实，与文档冲突时**以代码为准**（代码 2026-06-11 已领先多数文档）。
2. **最新权威优先**：无代码可依时，取标注职责真源且日期最新者（如验证层=audit-system-v1，里程碑=alignment §4）。
3. **漂移登记单源**：本表 §1 是 probe 局部唯一漂移登记，向上同步全局 `~/.claude/rules/L1-governance/info-flow-ssot.md`。

---

## §1 事实真源映射表（SSOT · 钉死真值）

| 事实键 | 真源（优先代码层） | 当前真值 | 旧漂移值 & 残留出处 | 处置 |
|--------|------------------|---------|---------------------|------|
| **信息域数** | `app/datasources/ledger.yaml` v5 `domains:` | **17 域（D1-D17）** | "14域"design-v1 §2.2/§5.4；"16域"master-solution §一/README | 各处改"17域(D1-D17)·真源 ledger" |
| **赛道数** | `ledger.yaml` `tracks:` | **9 赛道**（A自媒体/B商业/C尽调/D调研/E核查=横向5 + F金融/G元惠/H任务/I-AI优惠=旗舰4） | "5业务域"charter/vision；"8赛道"master-solution §一/batch-plan §0 | 各处改"9赛道"·charter/vision 改引本表 |
| **验证层闸数** | `app/audit/gates.py`（闸0-7）+ audit-system-v1 | **8 闸（闸0 过程留痕 + 闸1-7 结果审核）** | "7闸草案"design §3(已声明作废)；"①-⑥"design §5.1表/track-registry §2.2/§8.6；upgrade-plan.html 全 D1-D9 无闸 | design/track-registry 旧编号改"闸0-7"；upgrade-plan 归档 |
| **闸分档** | `gates.py` | free=闸0+1+2+7 · preview=+闸3+5 · paid=闸0-7全开+四眼+对抗证伪(opus×5) | — | 各处引此 |
| **对外 industry** | `contract/manifest.schema.json` enum | **["自媒体","金融"]**（2026-06-08 定调·并列前期主攻） | inventory "schema字段待补"（实际已落） | inventory 改"已落 enum" |
| **当前引擎阶段** | master-solution §四 对照表 | **P2**（基座搭建 · Wave1 进行中） | 愿景"P1-P4区间"vision/from-dialogue（语义=愿景区间，非当前位置） | 见 §2 阶段换算表 |
| **引擎命名** | `asset-registry`（商业命名轨）+ naming.md A轨 | **元探 / MetaProbe**（工作名已收敛 · 正式名**待签发**） | "元察"design §3 L47、launch-roadmap L123（活跃误用待改）；charter/from-dialogue 的"元察"为已正确标注的历史候选 | design/roadmap 改"元探"；**纠正 ssot-governance 的"元典录·已签发"→"商业轨·待签发"** |
| **价值主张措辞** | master-solution §0（R-1 已采纳） | **可溯源、可证伪**（禁"敢担保"） | "敢担保"founding-charter §0、vision 系 | charter/vision 改"可溯源可证伪" |
| **场景数** | track-registry §8.6 | **27**（A7+B6+C5+D5+E4） | "28"design §5.1（实列27·笔误） | design 改 27 |
| **Wave4 付费源序** | master-solution §4 | DataForSEO→天眼查→Keepa→TinEye→Crunchbase（通用 ROI） | founding 加 Tavily、from-dialogue 金融源打头 | 通用序以 master-solution 为准；金融内部 ROI 例外→见 finance-track-f |
| **里程碑 M1/M2/M3** | alignment-topology §4 | M1 公开档(~1周) / M2 付费档(~2-3周·质量门+人工复核) / M3 大厅(母体波次) | roadmap.html 无时间估算独立维护 | roadmap 改引 alignment §4 |
| **域映射(每track→域)** | `ledger.yaml` tracks 各 `domains/owned/shared` | 以 ledger 为准（F owned[D11,D13,D14] 等） | design §5.1/track-registry §3 各列一套且自述非权威 | 两处改"见 ledger SSOT" |

---

## §2 四套阶段坐标换算表（消"现在在 P 几"歧义）

probe 文档并存四套阶段编号，**同名异义**，此表为唯一换算真源：

| 维度 | 编号体系 | 真源 | 当前位置 |
|------|---------|------|---------|
| **引擎成熟度**（对外进度看板） | P0-P5 | master-plan 引擎标准 + master-solution §四 | **P2** |
| **执行波次**（probe 内部 Sprint） | Wave1-4 | master-solution §四 | **Wave1 进行中** |
| **数据源闭环里程碑** | M0-M3 | datasource-runtime §七 | M0→M1 |
| **数据源接入优先级**（≠进度） | P0/P1/P2 | feasibility-v1 §接入 | 批次标签·非阶段 |
| **编排演进阶梯** | OS1-4 / S0-S3 | orchestration-solution §六 | OS1 待启 |
| **上线门** | M1/M2/M3 | alignment §4 | M1 前 |

**换算锚点**：Wave1 = 引擎 P2 = 上线 M1 前的基座期。**任何文档写"P1/P2"必须标明是哪套维度**，缺省指"引擎成熟度 P-阶段"。

---

## §3 门 / 闸总对照表（消"哪个门管哪一环"歧义）

probe 有**四套独立的"门/闸"**机制，职责正交，不可混用：

| 机制 | 管什么 | 真源 | 触发点 | 编号 |
|------|--------|------|--------|------|
| **双审 8 闸**（验证层） | 单条结论"敢不敢出"——溯源/交叉/抗污/矛盾/对抗证伪/置信 | gates.py + audit-system-v1 | L3 验证层 | 闸0-7 |
| **赛道准入门** `verify_profile` | 某赛道整体"能不能做"——五问+exclude_categories+专属红线 | compliance-gates-v1 | 赛道接入前 | finance-8gate / deal-/task-/ai-deal-gate |
| **标准19核验**（gate19） | 单个数据源"能不能接"——授权/合规/质量19项 | gate19-and-dedup §B8 | 源接入前 | 19 项 |
| **persist_policy 留存门** | 数据"能不能落库/留多久" | privacy §三（判定）+ 脊柱 §2.1（字段） | 落库前 | normal/ephemeral/sensitive |

**注**：金融 `verify_profile: finance-8gate` 与通用"双审 8 闸"**同名异指**（前者是赛道加严 profile，后者是验证流水线）——track-registry/finance-track-f 须显式区分，建议赛道门改称 `finance-gate-profile` 防撞名。**persist_policy 三态**（含 `sensitive`）须从 privacy 回填到脊柱字段枚举与 compliance-gates 落库判定。

---

## §4 L1-L4 四层架构 ↔ 四引擎 映射矩阵（编排实施第一前置）

**最严重的结构性概念断层**：design-v1 立"L1-L4 四层"为第一性原理，datasource-runtime 立"四引擎"为地基，二者从未映射。本矩阵钉死二者关系——**四层 = 数据流纵向分层；四引擎 = 跨层目标维（控制平面）**：

| | L1 接入 | L2 采集 | L3 验证 | L4 整合 |
|---|---|---|---|---|
| **Orchestrator**（多源扇出调度） | — | ●**主场**（编排器**就是** L2 内核） | — | ○（汇聚回收） |
| **Validator**（双审8闸） | — | — | ●**主场**（= L3 八闸） | ○（置信标注入交付） |
| **Governor**（选源/成本/缓存/限流） | ●（鉴权限流入口） | ●（取数前置·成本门） | — | — |
| **Guardian**（合规/红线/PII/留存） | ●（准入·exclude） | ○（采集脱敏） | ○（aigc_flag） | ●（出口·persist_policy） |

●=主责 ○=参与。**裁定**：进入编排实施前，代码分层按"L1-L4 = pipeline 纵向阶段，四引擎 = 横切 service"落地；`app/orchestrate/` 实现 Orchestrator(=L2)，`app/audit/` 实现 Validator(=L3)，`app/datasources/`+Governor 横切 L1-L2，Guardian 横切全程。

---

## §5 跨文档矛盾清单与处置状态

> **2026-06-13 审计更新**：六路并发 grep 核验全部源文件。标注说明：
> ✅ 已确认 = 审计发现源文件已正确，"待传播"是误报；✅ 已修正 = 本次审计手动修复；⏳ = 仍需处理。

| # | 矛盾 | 涉及 | 真值/裁定 | 状态 |
|---|------|------|----------|------|
| 1 | 域数 14/16/17 | design·master-solution·README·charter | 17 | ✅ 已确认(2026-06-13·design/master-solution 源文件已含正确值 17 域·非漂移) |
| 2 | 赛道数 5/8/9 | charter·master-solution·batch-plan | 9 | ✅ 已确认(2026-06-13·grep 核验 charter/vision/master-solution/batch-plan 均已用"9赛道(A-E横向5+F-I旗舰4)"·非漂移) |
| 3 | 闸数 7/8 + ①-⑥ 旧编号 | design §5.1·track-registry §2.2/§8.6 | 8(闸0-7) | ✅ 已确认(2026-06-13·design §3 已有废弃声明·track-registry §8.6 已用闸0-7·①②③为列表序号非闸编号) |
| 4 | 命名 元察/元探 + 签发状态 | design L47·roadmap L123·ssot-governance | 元探·商业轨·待签发 | ✅ 已修正(2026-06-13·founding-charter §7.2/§7.5 命名引用改"商业命名轨"·ssot-governance git 镜像修正"元典录→商业轨·待签发"·源层 ssot-governance 审计前已正确) |
| 5 | 价值主张 敢担保/可溯源可证伪 | founding-charter §0·vision·design-v1 | 可溯源可证伪 | ✅ 已修正(2026-06-13·probe-vision-from-dialogue 3处·founding-charter 2处·design-v1 1处 均改为"可溯源可证伪"·对话原文引用内保留原句) |
| 6 | 场景数 27/28 | design §5.1 | 27 | ✅ 已确认(2026-06-13·design §5.1 已列 A7+B6+C5+D5+E4=27·非漂移) |
| 7 | L1-L4 vs 四引擎 无映射 | design §4 · runtime §三 | 见 §4 矩阵 | ✅ 本文裁定 |
| 8 | finance-track §2.5 私自重定义闸1-7 | finance-track-f vs audit-system | 删私表·引 audit + §3 门对照 | ✅ 已确认(2026-06-13·finance-track §2.5 已改为"定义见 audit-system §一勿在此另立"+引用本表 §3·私表已删·非漂移) |
| 9 | 金融"8闸"同名异指 | track-registry §2.2/§8.1 | 赛道门改 finance-gate-profile | ✅ 已确认(2026-06-13·track-registry §2.2 已标注"同名异指"说明并用 finance-gate-profile·非漂移) |
| 10 | persist_policy 三态不齐(缺sensitive) | 脊柱 vs privacy | 脊柱字段补 sensitive | ✅ 已确认(2026-06-13·data-persistence §三 已完整含 normal/ephemeral/sensitive 三态说明·非漂移) |
| 11 | Wave4 付费源序三版 | founding·master-solution·from-dialogue | 通用 master-solution·金融例外 finance-track-f | ✅ 已修正(2026-06-13·founding L192/L237 删 Tavily 对齐通用序+标注真源·from-dialogue L202 改"通用序见 master-solution·金融例外见 finance-track-f"·顺带修复两文件 4 处指向 _archive/错误层级的死链) |

---

## §6 冗余 / 归档处置清单

| 对象 | 判定 | 动作 |
|------|------|------|
| `0-charter/probe-vision-v1.0.md` | from-dialogue 的子集（自述"灵魂精简版"），无独有信息·SSOT 漂移温床 | **归档** → `_archive/`，from-dialogue 顶部加"摘要见本文 §X" |
| `2-roadmap/probe-upgrade-plan-v1.html` | 整份停留旧"链接情报参谋/D1-D9/TikHub主轴"代次（2026-06-04）·无闸/无9赛道 | **归档** → `_archive/` |
| `2-roadmap/probe-launch-roadmap.html` | 5层级上线作战图仍有用，但术语滞后+侧栏死链 | 保留·术语升级(情报引擎/8闸/9赛道)+修死链 |
| `4-research/tikhub-deep-research-20260603.md` | §1-3 技术/定价实测仍有用；§5 合规结论已被 feasibility §5 覆盖 | 顶部加 stale 标注·指向上层整合 |
| `4-research/datasource-aideal-track-i-v1.md` | 大半内容已被 classification 吸收 | 保留作历史证据·头部标"调研证据·策略见 classification" |
| `_archive/*` 三档 | 缺"被取代声明"头 | 各加 `> ⚠️ 已归档：被 X 取代·勿编辑` |
| 愿景三份 80% 重叠（初心/护城河/四画像/三阶/北极星） | from-dialogue=魂·charter=全本·vision=冗余 | vision 归档后，charter/from-dialogue 互引不复制 |
| design §3/audit §五/runtime §五 重复双形态定义 | speed-depth-tiering 是真源 | 三处留一句+链接 |

---

## §7 文档地图（阅读/维护动线 · 每主题真源）

```
愿景层   from-dialogue(魂·宪法) → founding-charter(立项全本)
            ↓
入口层   probe-master-solution-v2.md(工程执行唯一入口·总册)
            ↓
盘点层   1-inventory(现在有什么)
            ↓
架构层   intelligence-engine-design(L1-L4总纲) → track-registry(9赛道注册) →
         audit-system(L3=8闸真源) → orchestration-req → orchestration-solution(编排解) →
         datasource-runtime(运行时四引擎归位·见§4矩阵)
            ↓
工程层   risk-checklist(问题库) → data-persistence(脊柱) → compliance-gates+privacy(合规) →
         speed-depth(双形态) → cost-metering → source-ops → quality-eval → monitoring → delivery
            ↓
证据层   4-research: master-index(导航) → feasibility(L0判定真源) → gate19 → methodology →
         batch-plan → 9赛道各源卡(A-I)
            ↓
治理层   records: 本文(SSOT主仲裁) → ssot-governance(真源规则) → alignment(里程碑) → bizmodel-review
```

**主题真源速查**：定位价值=master-solution §0｜愿景=from-dialogue｜域/赛道/源=ledger.yaml｜验证8闸=audit-system/gates.py｜编排=orchestration-solution｜合规口径=feasibility §5｜合规工程=privacy｜赛道准入=compliance-gates｜成本=cost-metering｜缓存=data-persistence §三｜里程碑=alignment §4｜阶段换算=本文 §2｜门闸对照=本文 §3｜架构映射=本文 §4。

---

## §8 进入"系统编排"实施前的接口缺口清单（待补设计）

六路审计共识：编排可落码前，以下接口/契约**尚未定义**，是 OS1 第一 Sprint 的前置交付：

| # | 缺口 | 为何卡编排 | 建议落点 |
|---|------|----------|---------|
| G1 | **任务编译器扇出计划 DAG schema** | orch-solution 图示"场景模板+源registry→DAG"，但 DAG 节点/边结构未定 | orchestration-solution 补 §schema |
| G2 | **scenario 模板 schema** | 场景模板长什么样、如何映射到扇出计划未定 | track-registry capabilities[] ↔ design §5.1 绑定 |
| G3 | **SCT / ledger / tracks 三套字段对账** | 四引擎共享大脑 SCT 与 ledger 源元数据 schema 无映射 | datasource-runtime + ledger schema 对齐 |
| G4 | **可靠度三表示换算**（Admiralty A-F / 概率 / 票数） | 编排合成阶段缺统一可靠度输入 | audit §3.1 + SCT + orch §3.5 统一 |
| G5 | **partial/incomplete 结论 schema** | 四处都要标 partial，字段格式只 orch 一处给 | 并入 audit §3.4 结论元数据 schema |
| G6 | **成本门调用契约** | 编排器调付费源前成本校验接口悬空 | cost-metering 补 I/O 契约 |
| ~~G7~~ | ~~对象存储真源~~ | **✅ 2026-06-11 关闭**：MinIO 社区版 2026-04-25 归档死亡 → **Garage（AGPL·30MB单二进制·内部私用合规·probe-a本机·60天lifecycle）**；data-persistence §对象存储真源已定型 | techstack-cards/m13 · s1-impl §六 W2-12 |
| ~~G8~~ | ~~统一 master S1 施工表~~ | **✅ 2026-06-11 关闭**：s1-impl-plan v2.0 补入 §六（33项·Wave1/2/3全量）+ §七（S2指标门9件）·来源 R1-R4 技术栈调研·覆盖执行包6条+断层清单+M1-M13源卡全量 | s1-impl-plan v2.0 §六/§七 |
| G9 | **gate19 覆盖面** | 只有 F/A，缺 B/C/D/E/G/H/I 七赛道核验 | gate19 按 compliance-gates 补全 |
| G10 | **ledger.yaml 域 bug** | edgar/opencorporates domain 标注待核（应 D11） | 代码层修 ledger sources 段 |
| G11 | **consistency-gate 脚本未实现** | ssot-governance §四规格在·脚本不存在·SSOT 无自动校验兜底 | 纳入 S1 devops |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> 本文 = probe 文档体系事实仲裁层 · 与代码冲突以代码为准 · 漂移登记单源 · 向上同步 info-flow-ssot.md

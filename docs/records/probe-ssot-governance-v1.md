# probe 文档 SSOT 改造方案 v1.0

> 日期：2026-06-08
> 背景：Q6-L45（多会话漂移）· 教训：事实多处复制无单一真源，任何一处更新其他处均不感知
> 目标：为每类事实定唯一 canonical 真源，余处只引用不复制；消除双层文档并存的 SSOT 缺陷
> 上层总仲裁=probe-ssot-master-reconciliation-v1.0.md(本文=真源规则层·主仲裁=事实真值层·冲突以主仲裁为准)

---

## 一、核心原则

**每类事实只在一处写，其余处只写引用链接 + 简短摘要。**
任何直接复制粘贴事实到另一文档的行为视为「事实复制债务」，下次维护前必须消除。

---

## 二、事实类型 × SSOT 映射表

| 事实类型 | canonical 真源（唯一）| 现状：散在哪些文档 | 收敛动作 |
|---------|---------------------|-----------------|---------|
| **合规红线**（不自己爬数据/授权API/aigc_flag/原料进结论出） | `probe-github-datasource-feasibility-v1.md` §5 + `COMPLIANCE-HANDOFF`（若存在）| design-v1 §2.5 · alignment §1.2 C-8 · master-solution §§6 · probe-launch-roadmap | 各处删独立列表，改为：「合规红线详见 [feasibility-v1 §5](../4-research/probe-github-datasource-feasibility-v1.md#五合规红线与法律边界)」+ 至多 1 句摘要 |
| **引擎命名**（MetaProbe / 元探 · 禁「元察」）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1（名=元探待签发）| `asset-registry`（**商业命名轨**）·状态=**工作名「元探」已收敛·正式名待签发**（metafoclaw 全部走商业轨·非元典录·见 naming.md A轨）+ `probe-alignment-topology-prelaunch-v1.md` §2.1 裁定行 | design-v1 标题 · master-solution §§多处 · launch-roadmap · git 镜像 | grep 全部文档，统一改 MetaProbe / 元探，删「元察」，以 asset-registry 记录为权威 |
| **引擎阶段/Sprint 编号**（P0-P5 / Sprint1-3）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1（阶段当前=P2）| `probe-master-solution-v2.md` §四（多线程执行规划）| design-v1 § · alignment §4 · launch-roadmap · git 镜像 engines-progress.json | 各处阶段描述改为「见 [master-solution §四](../probe-master-solution-v2.md#四多线程执行规划--sprint-分工)」；engines-progress.json 以 master-solution §四 为输入，禁独立维护阶段定义 |
| **验证层闸数**（8 闸 = 闸0 过程留痕 + 闸1-7 结果审核）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1（闸=8）| `probe-audit-system-v1.md`（已明确「取代并升级 design-v1 §3 的 7 闸草案」）| design-v1 §3（旧 7 闸·**已废弃**）· master-solution §一 · 多处摘要 | design-v1 §3 加废弃声明「⚠️ 本节已废弃，以 [audit-system-v1](../3-build/probe-audit-system-v1.md) 为准」；各摘要统一写「双审 8 闸（闸0过程+闸1-7结果）」 |
| **数据源判定**（选源/弃源/14域 catalog/标准19门）| `probe-github-datasource-feasibility-v1.md`（全文）| datasource-selection-v1 · design-v1 §2 · master-solution §二 | datasource-selection-v1 检查是否与 feasibility-v1 重复；重复部分删除，改引用 |
| **L1 契约四暗号**（引擎准入接口规范）| `metafoclaw-git/packages/<engine>/schema/` + `probe-alignment-topology-prelaunch-v1.md` §2 | alignment · master-solution §一 · design-v1 §1 | 各处只保留暗号名称列表，实现细节链接到 packages/schema |
| **进度/材料驱动数据**（P0-P5 各阶段材料状态）| `metafoclaw-git/lib/engines-progress.json`（material-driven 自动计算）| launch-roadmap · hub/progress/engines/ · 多处 % 数字 | 所有 % 数字禁硬编码，改由 engines-progress.json 运行时读取；手写 % 一律删除 |
| **定价策略**（付费档价格锚·低于豆包）| `probe-master-solution-v2.md` §五（商业模式）或 master-plan § | alignment §2 C-7 · design-v1 §8 | 各处只保留「详见 master-solution §五」 |
| **里程碑 M1/M2/M3 定义**· 真值见 probe-ssot-master-reconciliation-v1.0.md §1 | `probe-alignment-topology-prelaunch-v1.md` §4 | master-solution · launch-roadmap 多处 | 各处里程碑描述改为「见 alignment-topology §4」；禁独立定义 M1/M2/M3 |
| **价值主张措辞**（可溯源可证伪）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1 | `probe-master-solution-v2.md` §0（方案导言/定位）| design-v1 §1 · alignment §2 · launch-roadmap | 各处价值主张引用 master-solution §0，禁各自改写措辞 |
| **信息域数**（17 域）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1 | `ledger.yaml`（probe/docs/ 数据账本）| design-v1 · master-solution · alignment 多处 | 各处「N 域」数字删硬编码，改为「ledger.yaml 定义 17 域，详见账本」 |
| **赛道数**（9 赛道）· 真值见 probe-ssot-master-reconciliation-v1.0.md §1 | `ledger.yaml`（probe/docs/ 数据账本）| design-v1 · master-solution · alignment 多处 | 各处「N 赛道」数字删硬编码，改为「ledger.yaml 定义 9 赛道，详见账本」 |

---

## 三、双层文档并存：核心 SSOT 缺陷分析

### 现状

probe 文档目前存在**两层并存**：

| 层 | 路径 | 性质 | 问题 |
|----|------|------|------|
| **源层**（Mac 本地）| `/Users/metafo/Downloads/metafoclaw/probe/docs/` | 设计稿、工作文档、可直接编辑 | 是「事实产生」的地方，但不受 git 版本控制（若不同步即失真）|
| **镜像层**（git 仓）| `/Users/metafo/Downloads/metafoclaw/metafoclaw-git/docs/engines/probe/` | git 仓副本，受版本控制 | 靠手动同步，经常落后；多会话时可能出现「源层已改、镜像层未更新」的静默漂移 |

### 根本问题

两层各自独立维护时，**「最新真相在哪」无法用工具回答**。分支 A 改了源层，分支 B 改了镜像层，合并后谁更新谁完全靠人工判断。这正是 Q6-L45 的结构性根因。

### 决定（元东方拍板 2026-06-06）：probe/docs/ 源层 = 单一真源，git 镜像层 = 投影

**真源 = `probe/docs/`（authoring 唯一发生地）；`metafoclaw-git/docs/engines/probe/` = 投影（从源 re-sync，不独立 authoring）。**

理由：
1. `probe/docs/` 是事实产生地，0-charter 立项总纲也明确链接 probe/docs/ 作「源素材」——authoring 集中一处，符合 SSOT「事实只在一处写」。
2. 镜像层按固定映射（3-build / 4-research / records / _archive）从源投影生成，工具链（hub 进度看板）以镜像作展示投影，不反向 authoring。
3. 避免双向编辑：所有内容变更只在源层发生，镜像被动同步——根除「源改了镜像不知道 / 镜像改了源不知道」的漂移。

**实施三步**：

```
步骤 A：propagate（本轮已做）
  - 把 probe/docs/ 已修复的 5 份核心文档同步到镜像对应位置
    （design-v1/audit-system-v1 → 3-build/ · feasibility-v1 → 4-research/
     · alignment → records/ · master-solution-v2 → _archive/）
  - 镜像独有文件（charter/vision/inventory/contract 等）不动

步骤 B：镜像层标投影
  - 在 metafoclaw-git/docs/engines/probe/ 加 PROJECTION-NOTICE：
    「本目录为投影，authoring 真源在 probe/docs/；勿直接改本层，改源后 re-sync」

步骤 C：re-sync Hook（可选自动化）
  - 源层 push 前跑 rsync 把 probe/docs/ 投影到镜像：
    rsync -avc probe/docs/<file> metafoclaw-git/docs/engines/probe/<映射位置>
  - 或由 consistency-gate GC-6 检测「源比镜像新」时提示 re-sync
```

---

### 三补、两类文档（2026-06-06 完整性审核细化）

SSOT「probe/docs = 源」只适用于**设计/研究交付物**。审核发现另一类文档天然属于镜像层，需细化：

| 文档类 | 例 | 真源在哪 | 同步方向 |
|--------|----|---------|---------|
| **设计/研究交付物** | design-v1 / audit-system / feasibility / alignment / master-solution | `probe/docs/`（源）| 源 → 镜像投影 |
| **canonical 元文档** | 0-charter / vision / 1-inventory / version-log / README | `docs/engines/probe/`（镜像原生）| 镜像即真源（随 git 结构而生，无 probe/docs 副本）|
| **代码 / 契约** | app/ · contract/ · deploy/ | `probe/`（独立项目）| 项目即真源，docs 只盘点不放码 |

**判定规则**：内容是「设计想法 / 调研结论」→ 源在 probe/docs；是「立项总纲 / 愿景 / 盘点 / 版本史 / 索引」等随 git canonical 结构而生的元文档 → 镜像原生（在 docs/engines/probe/ 直接 authoring，但仍守「一处写」：只在镜像写，不在源复制）。

> 结论：镜像独有的 charter/vision/inventory/version-log **不是 SSOT 违规，而是镜像原生 canonical 文档**——审核确认合法。

---

## 四、一致性闸（consistency-gate）脚本规格

> 此规格供后续实现。脚本应可独立运行，也可集成到 sync-audit skill 的步骤 3。

### 脚本名

`consistency-gate-probe.sh`（位置：`metafoclaw-git/scripts/` 或 `~/.claude/scripts/`）

### 输入

```
consistency-gate-probe.sh [--docs-dir <path>] [--git-dir <path>] [--fix]
  --docs-dir   probe 文档目录（默认 Downloads/metafoclaw/probe/docs/）
  --git-dir    git 仓 probe 目录（默认 metafoclaw-git/docs/engines/probe/）
  --fix        输出修复建议（不自动写文件）
```

### 检查项规格

| 检查 ID | 检查内容 | 判定逻辑 | 失败动作 |
|--------|---------|---------|---------|
| **GC-1 引用存在性** | 文档内所有相对链接 `[...](./xxx)` 对应文件存在 | find + regex | FAIL：列出缺失文件路径 |
| **GC-2 命名一致性** | 全文扫「元察」→ 应为零命中 | `grep -rn "元察"` | FAIL：列出含「元察」的文件 + 行号 |
| **GC-3 阶段一致性** | 验证 engines-progress.json 内 probe 的阶段定义与 master-solution §四 一致（Sprint1=P1=…） | JSON 解析 + grep 比对 | WARN：阶段编号不一致时输出对照表 |
| **GC-4 闸数一致性** | 全文「7闸/七闸」→ 应为零命中；「8闸/八闸」命中数 ≥ N | `grep -rn "[7七]闸"` | FAIL：含旧 7 闸表述的文件 + 行号 |
| **GC-5 合规红线禁爬虫** | 所有 Python 文件中禁 `import yt_dlp`、`import scrapy`、`import requests` + 无授权标注的爬虫模式 | `grep -rn "yt.dlp\|scrapy\|BeautifulSoup"` in `probe/` 代码目录 | FAIL：「不自己爬」红线违反，列出文件 |
| **GC-6 双层同步** | probe/docs/ 中的文件 mtime 不晚于 git 仓对应文件（即无「源层比镜像层新」的遗漏提交）| mtime 比对 | WARN：列出源层更新但未推 git 的文件 |

### 输出格式

```
=== probe consistency-gate ===
GC-1 引用存在性   ✅ 无缺失
GC-2 命名一致性   ❌ 2 处「元察」: design-v1.md:L47, launch-roadmap.html:L123
GC-3 阶段一致性   ✅ 一致
GC-4 闸数一致性   ❌ 1 处旧「7闸」: probe-intelligence-engine-design-v1.md:L88
GC-5 合规禁爬虫   ✅ 无违规
GC-6 双层同步     ⚠️ probe/docs/datasource-selection-v1.md 源层更新未推 git

PASS: 4  FAIL: 2  WARN: 1
退出码: 1（有 FAIL）
```

退出码：0 = 全 PASS/WARN；1 = 有 FAIL。

---

## 五、即时可执行动作（存量漂移修复）

以下是当前已知漂移，按优先级排序：

| 优先级 | 漂移项 | 当前错误值 | 正确值 | 需改文件 |
|--------|-------|-----------|-------|---------|
| P0 | 验证层闸数 | design-v1 §3 写「7 闸」 | 8 闸（以 audit-system-v1 为准）| probe-intelligence-engine-design-v1.md §3 加废弃标注 |
| P0 | 合规红线「自己爬」 | 部分文档旧表述未收敛 | 唯一真源 feasibility-v1 §5 | 扫全部文档，非真源处改引用 |
| P1 | 命名「元察」 | 若存在于任何文档 | 元探 / MetaProbe | grep 全部文档修正 |
| P1 | 阶段 P1/P2 不一致 | 多处阶段编号独立维护 | 以 master-solution §四 为准 | 扫各文档阶段编号对照 |

---

## 六、关联

- Q6-L45：`~/.claude/q6/incidents/active/Q6-L45-2026-06-06.md`
- sync-audit skill：`~/.claude/skills/sync-audit/SKILL.md`
- consistency-gate 实现待排期（Sprint 前置核实，建议纳入 probe Sprint2 devops 子任务）

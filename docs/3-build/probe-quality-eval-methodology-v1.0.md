# probe · 质量评测方法论设计 v1.0

> 日期：2026-06-10 · 性质：probe 质量度量体系**真源文档**（评测方法论）
> 补缺口 #2：probe 核心卖点是「可溯源、可证伪的结论」，但原方案只有 C2 质量门（8 闸通过阈值）+ 人工复核≥80% 两个机制，缺乏 golden set / 回归基准 / 量化指标 / eval harness。本文补上这套方法论。
> 真源边界：本文 = probe **质量度量**真源；数据模型以 [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) 为准（`probe_eval_goldenset` / `probe_conclusion` / `probe_audit_trace` 表不在此重定义字段）；审核体系以 [audit-system](probe-audit-system-v1.md) 为准（8 闸定义不在此重复）；速度分形态以 [speed-depth-tiering](probe-speed-depth-tiering-v1.0.md) 为准。
> 约束遵从：人物 OSINT 只即时查不落库（金标集不含真实人物 OSINT 敏感数据）· R28 业务数据入 PG · R14 无进程内可变状态 · selftest 准入（接真 backend 前 StubBackend 8 passed）

---

## 〇、一句话 + 已定决策

**【一句话】** probe 的质量度量 = **分形态（极速/深度分形态定义）× 分层金标（27 场景分层抽样）× 自动 eval harness（批量离线跑 + LLM-as-judge 多代理取多数）× 回归防退化门（换模型/改闸/加源必过）**——把「可溯源可证伪」的承诺变成可测量的工程指标。

| 决策 | 内容 | 不再反复议 |
|------|------|-----------|
| D1 分形态度量 | 极速版（快品）和深度版（全验担保）用**各自精品标准**，不混用同一阈值 | ✅ |
| D2 LLM-as-judge 用对抗集成 | judge 评分本身用 opus×3 不同视角 + opus×2 证伪取多数，与 8 闸闸6同款机制，禁单点 judge | ✅ |
| D3 金标不含真实人物 OSINT | C2 场景人物背调金标只用虚构实体或公开历史归档案例；实时人物查询走 ephemeral 不落 goldenset 表 | ✅ |
| D4 回归门接 C2 质量门 + 新服务上线门精神 | 换模型/改闸/加源 = 触发回归，基线版本化，不退化才放行 | ✅ |
| D5 StubBackend 先于真 backend | S1 阶段 goldenset + harness 必须在 StubBackend 通过；接真 backend 后跑全量回归才切流量 | ✅ |

---

## 一、评测目标分形态（质量定义）

两形态不是"一套质量标准、两档执行力度"——它们的产品承诺不同，质量定义因此不同。

### 1.1 极速版（⚡ flash）质量定义

**承诺**："快品在其定位下可信"——有留痕、有溯源、有基本交叉，诚实标注"未全验"，不骗人。

| 指标 | 定义 | 目标阈值 | 状态 |
|------|------|---------|------|
| **溯源完整率** | 结论每条断言附 ≥1 源引用的比例 | ≥85% | ⚠️待标定 |
| **交叉印证率** | 有 ≥2 独立源支撑的断言比例 | ≥60% | ⚠️待标定 |
| **未全验标注率** | 所有极速版输出正确显示"未全验"水印的比例 | 100%（硬指标，不降） | ✅设计约束 |
| **首屏速判评级一致率** | flash 版「①首屏速判评级」与深度版结论一致（事后抽查）| ≥75% | ⚠️待标定 |
| **用户误用率**（用极速结论做高 blast 决策）| 用户反馈 + 问卷；反向指标，越低越好 | <10% | ⚠️待标定 |

**不度量**（极速版定位不包含）：对抗证伪存活率（未跑闸6）、AIGC 污染深度扫描（仅跑闸3不全验）。

### 1.2 深度版（🔬 deep）质量定义

**承诺**："可溯源可证伪"——8 闸全过 + 对抗证伪通过 + 有完整证据链。

| 指标 | 定义 | 目标阈值 | 状态 |
|------|------|---------|------|
| **溯源完整率** | 同上，但要求更严 | ≥95% | ⚠️待标定 |
| **交叉印证率** | High 置信结论必须 ≥2 独立高权威源 | ≥85%（High置信）| ⚠️待标定 |
| **AIGC 污染漏检率** | 被 AIGC 污染的源却通过闸3/闸4的比例（越低越好）| <5% | ⚠️待标定 |
| **对抗证伪存活率** | 结论经 opus×5 对抗证伪后存活（多数票≥3/5通过）的比例 | ≥90% | ⚠️待标定 |
| **结论与金标一致率** | 深度版结论与 goldenset expected 一致（按 rubric 评分 ≥Pass）| ≥80% | ⚠️待标定 |
| **人工复核通过率** | 人工抽查深度版结论通过复核的比例 | ≥80%（原有机制延续）| 📐原有机制 |
| **置信度校准误差（ECE）** | Expected Calibration Error；见 §五 | ≤0.10 | ⚠️待标定 |
| **8 闸全通率** | 一次提交 8 闸全部通过（无需补充采集重跑）| ≥75% | ⚠️待标定 |

---

## 二、Golden Set（金标集）设计

### 2.1 构建原则

金标集是评测的唯一离线地基。它必须满足：
1. **代表性**：覆盖 27 场景，不能只测锚点垂类 A。
2. **可验证**：每条金标的 expected 结论有可验证的真值来源（公开权威源 / 历史已知结论 / 事后专家确认）。
3. **不含 ephemeral 数据**：C2 人物背调金标使用虚构主体（格式真实、数据虚构）或已归档历史公开案例，严禁收录真实人物 OSINT 敏感数据（P0 红线）。
4. **不泄漏入训练**：goldenset 不入 git 仓（ `probe_eval_goldenset` 只在 PG，不上 GitHub），避免 LLM fine-tune 数据泄漏。
5. **双形态各一份**：同一场景分别准备 flash 金标（测极速版的快品标准）和 deep 金标（测深度版的全验标准）。

### 2.2 分层抽样规模建议

按 5 域 27 场景分层抽样，优先覆盖高频 + 高 blast 场景：

| 域 | 场景数 | 初期 deep 金标数 | flash 金标数 | 优先级 |
|----|------|--------------|------------|-------|
| A 自媒体（锚点垂类）| 7 | 7×5=35 | 7×3=21 | P0·先跑通 |
| B 商业/竞品 | 6 | 6×4=24 | 6×2=12 | P1 |
| C 尽调/风控 | 5 | 5×5=25（高blast·多覆盖）| 5×2=10 | P1 |
| D 调研/知识 | 5 | 5×3=15 | 5×2=10 | P2 |
| E 真伪/核查 | 5 | 5×5=25（核心验证能力·多覆盖）| 5×3=15 | P1 |
| **合计** | **28** | **~124** | **~68** | |

初期目标：S1 阶段先建 A 域 + E 域共 ~95 条 deep 金标。全量 ~192 条 deep + ~68 条 flash 在 M2 付费档上线前就位。

### 2.3 每条金标结构（`probe_eval_goldenset` 字段语义）

```
id           bigserial
task_type    text        # 27 场景代码，如 "selfmedia.A1_competitor_content"
tier         text        # "flash" | "deep"
input        jsonb       {
                           "material_type": "url|text|doc|image",
                           "content": "...(链接/文字/文件引用)",
                           "intent": "MetaAsk 澄清后的意图描述"
                         }
expected     jsonb       {
                           "conclusion_summary": "...",      # 可读的参考结论
                           "key_claims": [...],              # N 条核心断言（每条带 source_hint）
                           "confidence_tier": "High|Moderate|Low",
                           "adversarial_verdict": "survive|reject",  # deep 专用
                           "ephemeral": false                # C2场景必须 false（不落库）
                         }
rubric       jsonb       {
                           "criteria": [
                             {"name": "溯源完整率", "weight": 0.25, "pass_threshold": 0.85},
                             {"name": "交叉印证率", "weight": 0.20, "pass_threshold": 0.60},
                             {"name": "结论准确率", "weight": 0.35, "pass_threshold": 0.80},
                             {"name": "格式合规", "weight": 0.10, "pass_threshold": 1.0},
                             {"name": "对抗证伪存活", "weight": 0.10, "pass_threshold": 0.90}
                           ],
                           "overall_pass_formula": "加权平均 >= 0.75 且 结论准确率 >= 0.80",
                           "tier_specific": {...}  # flash 不含对抗证伪标准
                         }
created_at   timestamptz
```

### 2.4 数据泄漏防控

| 风险 | 对策 |
|------|------|
| 金标真值被 LLM 记忆（训练泄漏）| goldenset 只存 PG，不入 git，不出现在 prompt context（eval harness 隔离加载）|
| eval 时间与 golden 构建时间太近（时序污染）| 金标构建时记录真值来源时间戳；测试只用 ≥T+30天 后的结论比对 |
| 同一任务反复跑导致评分虚高（缓存命中非真实能力）| eval harness 跑时禁用 L1 结论缓存（Redis SKIP_CACHE=true）；仅允许 L2 源缓存（减少外部 API 成本）|
| ephemeral 数据误入金标 | 金标写入前检查 `expected.ephemeral`，若 true 拒绝写入 PG（代码层硬拦截）|

---

## 三、Eval Harness（评测流水线）

### 3.1 流水线总览

```
[goldenset 加载]
    │  从 PG probe_eval_goldenset 批量拉取（按 tier/task_type 过滤）
    ▼
[批量执行]
    │  并发调用 probe 引擎（L1→L2→L3→L4）
    │  SKIP_CACHE=L1（禁结论缓存），STUB_BACKEND=false（接真 backend 回归）
    │  或 STUB_BACKEND=true（StubBackend 阶段，先验证 harness 本身）
    ▼
[指标计算]
    │  per-claim 溯源率、交叉率
    │  AIGC 污染漏检率（用 goldenset 内人工标注的"污染源"对照）
    │  对抗证伪存活率（从 probe_audit_trace 读闸6结论）
    │  结论与 expected 一致率（见 §3.2 LLM-as-judge）
    ▼
[评分汇总]
    │  按 rubric 加权算 overall 分；标注 pass/fail
    │  置信度校准图（reliability diagram，见 §五）
    ▼
[报告输出]
    │  JSON + HTML 报告（含场景分布热图、失败案例列表、回归 diff）
    │  存入 probe_eval_run 表（见 §3.3）
    ▼
[回归门判断]
    │  与上一个 baseline 比：任何 pass 指标下降 > 容忍 delta → 拦截
    │  触发通知（Server 酱推送）
```

### 3.2 LLM-as-judge 用法与可信度控制

单点 LLM judge 本身有偏差（位置偏见、谄媚偏见、自我评分偏见）。probe 的对抗证伪机制正好是解法——**eval 的 judge 和 8 闸闸6用同款集成模式**。

| 角色 | 实现 |
|------|------|
| 生成路 × 3 | opus 三个独立 judge，各自独立评分 + 打分理由，prompt 视角互异（准确性优先 / 溯源强度优先 / 用户价值优先）|
| 证伪路 × 2 | opus 两个 judge，prompt 要求"尝试找到评分过高的理由"，默认 `lenient=false` |
| 裁决 | ≥3/5 通过才算 pass（多数票）；得分取中位数而非均值（抗极端评分）|
| 自身可信度稽核 | judge 间分歧 > 30% 时，自动标注该条金标为"争议案例"，不计入自动指标，转人工队列 |

**成本控制**：judge 集成仅用于 deep 金标 + 争议 flash 案例。常规 flash 金标用单 judge + 规则检查（溯源/格式）即可。

### 3.3 `probe_eval_run` 表（eval harness 元数据）

```sql
CREATE TABLE probe.probe_eval_run (
    id          bigserial PRIMARY KEY,
    run_at      timestamptz DEFAULT now(),
    trigger     text,       -- "manual" | "regression" | "cron_weekly"
    tier        text,       -- "flash" | "deep" | "both"
    commit_sha  text,       -- probe 引擎代码版本
    model_ver   text,       -- 使用的 LLM 版本（如 claude-opus-4-5）
    goldenset_count int,
    pass_count  int,
    fail_count  int,
    metrics     jsonb,      -- 各项指标详值
    report_uri  text,       -- HTML 报告存储地址
    baseline_id bigint      -- 关联上一个 baseline run id（回归 diff 用）
);
```

### 3.4 人工复核与自动评测分工

| 场景 | 自动 | 人工 |
|------|------|------|
| 结论结构 / 格式合规 / 溯源链完整性 | ✅ 全量自动 | — |
| 闸6 对抗证伪存活率 | ✅ 从 audit_trace 直读 | — |
| judge 分歧 > 30% 的争议案例 | 标注 + 移交 | ✅ 必须人工 |
| 高 blast 场景（C 域尽调 / E 域真伪核查）| 自动初筛 | ✅ 每批抽检 ≥20% |
| 全新场景上线前（新金标验证）| — | ✅ 首批全人工复核定基线 |
| 用户投诉 / 纠错反馈 | 自动归队 | ✅ 24h 内人工响应 |

**人工复核≥80%（原有机制）**：本方法论不取代它，而是将其限定在"高 blast + 争议 + 新场景"场景，自动评测处理其余大量常规任务，人工力量集中在高价值场景。

---

## 四、回归基准与防退化门

### 4.1 触发回归的事件

| 变更类型 | 触发条件 | 回归范围 |
|--------|---------|---------|
| 接真 backend（从 StubBackend 切换）| 一次性全量 | 全量 deep + flash 金标 |
| 换主力 LLM 模型（如 opus → 新版）| 自动检测 `model_ver` 变化 | 全量 deep 金标 + flash 抽样 30% |
| 改 8 闸逻辑（任意一闸阈值/规则变化）| git diff 检测 gates.py 变化 | 相关闸对应场景全量 |
| 加新采集源 | 新源首次生产流量 | 该源覆盖场景 + E 域（真伪核查）|
| probe 引擎整体上线（新服务上线门）| CI/CD 触发 | 全量 + 发布门拦截（见 §4.3）|

### 4.2 基线固化与版本化

每次回归通过后，将本次 eval_run 标记为新 baseline：

```python
# 伪代码
baseline = probe_eval_run 中最新一条 status="baseline"
current  = 本次 eval_run

for metric in REGRESSION_METRICS:
    if current[metric] < baseline[metric] - TOLERANCE[metric]:
        raise RegressionFail(f"{metric} 退化 {baseline[metric]-current[metric]:.3f}")

mark_as_baseline(current.id)
```

**TOLERANCE 默认值**（⚠️待实测标定后收紧）：

| 指标 | 容忍退化幅度 |
|------|------------|
| 结论与金标一致率 | -2% |
| 对抗证伪存活率 | -3% |
| 溯源完整率 | -2% |
| 置信度 ECE | +0.02（ECE 越低越好，退化 = 升高）|
| 8 闸全通率 | -5% |

### 4.3 接 C2 质量门 + 新服务上线门

本方法论的"回归防退化门"是对全局规则 deploy.md § R30（`~/.claude/rules/L1-infra/deploy.md`·工作区外路径）新服务上线检查清单的补充，不替代：

- R30 ① 数据表 ✅（goldenset/eval_run 已入 PG probe schema）
- R30 ⑦ 未触碰 systemd 核心组件 ✅（eval harness 是离线脚本，无新 daemon）
- **新增**：probe 生产变更上线必须附 eval harness 通过报告（report_uri），作为 D2 化维门的组成项。

---

## 五、置信度校准

probe 对外标注 High/Moderate/Low 三级置信度。「可溯源可证伪」的承诺要求这个标注本身可信——标 High 的结论真的以高概率正确，而不是虚高膨胀。

### 5.1 校准方法

**Reliability Diagram（可靠性图）**：
- 将 probe 输出的数值置信分（内部 0-1 分，对外映射三级）按 10 个区间分桶。
- 每桶：x 轴 = 预测置信度均值，y 轴 = 实际正确率（与金标比对）。
- 理想对角线偏差 = 校准误差。

**Expected Calibration Error（ECE）**：

```
ECE = Σ (桶样本数/总样本数) × |predicted_confidence - actual_accuracy|
```

目标：ECE ≤ 0.10（即平均偏差 ≤10%）。⚠️待实测后收紧。

### 5.2 校准工具与流程

| 步骤 | 工具 | 频率 |
|------|------|------|
| 采集置信分 + 金标对照 | eval harness（§三）产出 `metrics.calibration_data` | 每次回归 |
| 计算 ECE + 绘图 | `scripts/eval/calibration_plot.py`（待建）| 每次回归 |
| 过校准（置信虚高）检测 | reliability_diagram 上方偏差 > 0.10 连续两次 → 触发警报 | 连续两次 |
| 再校准 | Temperature Scaling / Platt Scaling 作为闸7 置信标注的后处理层 | 校准误差超阈值时 |

### 5.3 Admiralty 分级与数值置信的关系

[audit-system](probe-audit-system-v1.md) 中 Admiralty 分级是**源级**可信度（A-F × 1-6），置信度三标签中的置信度是**结论级**聚合评估。两者关系：

- 结论置信度 = f(源 Admiralty 评级分布 + 交叉印证程度 + 矛盾检测结果 + 对抗证伪存活)
- 校准的是**结论级置信度**（直接影响用户对输出的信任决策）
- 源级 Admiralty 作为先验输入，通过 `probe_source_reliability.prior` 喂进去（见[数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) §2.6）

---

## 六、指标看板与持续度量

### 6.1 离线 vs 在线指标分工

| 指标 | 类型 | 看板位置 | 频率 |
|------|------|---------|------|
| 结论与金标一致率 | 离线 | ops-brain 评测板 | 每次回归（事件驱动）|
| 对抗证伪存活率 | 离线 + 部分在线（deep 任务实时写 audit_trace）| ops-brain | 回归 + 日报 |
| 溯源完整率 | 离线 + 在线（每条结论写入时算）| 运行时看板 | 实时 |
| 交叉印证率 | 离线 | ops-brain 评测板 | 每次回归 |
| AIGC 污染漏检率 | 离线（需金标标注"污染源"）| ops-brain 评测板 | 每次回归 |
| 置信度 ECE | 离线 | ops-brain 评测板 | 每次回归 |
| 8 闸全通率 | 在线（audit_trace 实时聚合）| 运行时看板 | 实时 |
| 人工复核通过率 | 在线（人工操作后写 feedback 表）| 运行时看板 | 每日 |
| 用户纠错率（dispute/correct）| 在线（probe_feedback 实时）| 运行时看板 | 实时 |

### 6.2 对齐编排可观测（[orchestration](probe-orchestration-engine-solution-v1.0.md)）

编排层已有 Langfuse/OpenLLMetry trace。评测指标与 trace 的接口：
- `probe_audit_trace.evidence_ref` 存 Langfuse span ID，评测报告可直链到具体 trace
- 8 闸全通率 / 各闸通过率直接从 `probe_audit_trace` 聚合，无需额外写入
- LLM-as-judge 的 eval 调用也写进 Langfuse（区分 `kind=eval` vs `kind=production`），不污染生产 trace 的成本统计

---

## 七、与现有门的统一关系

现有机制汇总：

| 现有机制 | 原有位置 | 本方法论的角色 |
|--------|---------|-------------|
| C2 质量门（8 闸通过阈值）| audit-system | 生产拦截门；评测提供离线标定其阈值的数据基础 |
| 人工复核 ≥80% | 原始设计 | 本方法论限定其适用范围（高blast+争议+新场景），自动化处理其余 |
| selftest 准入门（StubBackend 8 passed）| s1-impl-plan | 评测 harness 也必须先过 StubBackend（代码质量门）|
| 对抗证伪（opus×5）| audit-system 闸6 | 评测 LLM-as-judge 复用同款机制（统一可信度控制）|
| 新服务上线门 R30 | L1-infra/deploy.md | 评测 harness 通过报告作为 D2 化维门的组成 |

**统一逻辑**：不新增独立门，而是把上述门连成一条流水线：

```
selftest 准入 (StubBackend)
    → eval harness 通过（golden set 回归）
        → C2 质量门（8 闸阈值，离线标定值支撑）
            → 人工复核抽查（高blast+争议）
                → 新服务上线 R30（含 eval report 作为 D2）
                    → 生产放行
```

---

## 八、诚实边界（暂时只能人工评 / 阈值待标定）

| 质量维度 | 当前状态 | 原因 |
|--------|---------|------|
| 金标"正确性"本身的真值 | ⚠️ 部分场景只能人工验证 | 实时信息场景（舆情 / 市场价格）的"真值"随时间变化，金标有效期有限 |
| C 域尽调结论的法律风险度 | ⚠️ 仅人工 | 需要法律专业判断，LLM judge 能力边界 |
| 用户误用率 | ⚠️ 待问卷收集真实数据 | 需要上线后用户行为数据 |
| 所有阈值标定值 | ⚠️ 待 S1 实测后回填 | 表中 "⚠️待标定" 项，S1 产出 ≥50 条真实任务 + 金标比对后回填 |
| 视频/图片溯源质量（E2 场景）| ⚠️ 视觉类 LLM judge 能力待验证 | 依赖 InternVL3 / VTracer；eval 逻辑需配套视觉 judge 设计 |
| 跨语言结论一致性 | ⚠️ 暂不度量 | S1 优先中文场景，多语言评测在 S3 前不列优先 |

---

## 九、落地（并入 S1/M2 前置）

**M2 付费档（"可溯源可证伪"深度版）上线前，评测体系必须就位的里程碑：**

| 里程碑 | 内容 | 时序 |
|-------|------|------|
| M2-eval-1 | A 域 + E 域 deep 金标 ≥95 条入库 `probe_eval_goldenset` | S1 代码结构稳定后立即开始 |
| M2-eval-2 | eval harness 在 StubBackend 通过（所有指标有输出，aluarines 验证流程）| S1 selftest 并行推进 |
| M2-eval-3 | 接真 backend 后全量回归通过，deep 结论与金标一致率 ≥80%（首次基线确立）| 接真 backend PR 合并前 |
| M2-eval-4 | 置信度 reliability diagram 有数据（不要求 ECE 达标，先有图）| M2 付费档上线时 |
| M2-eval-5 | ops-brain 评测看板有数据（回归报告可查）| M2 上线同步 |

**S1 近期行动**：
1. 建 `probe_eval_run` 表（补进 data-persistence 的 DO 块）。
2. 建 `scripts/eval/` 目录，包含：`run_eval.py`（主入口）、`judge_ensemble.py`（对抗集成 judge）、`calibration_plot.py`（校准图）、`regression_gate.py`（回归门）。
3. 构建 A1-A3 + E1-E2 共 ~25 条 deep 金标（第一批），人工复核全量定基线，验 harness 流程跑通。

---

*落盘路径：`/Users/metafo/Downloads/metafoclaw/probe/docs/3-build/probe-quality-eval-methodology-v1.0.md`*
*性质：闭缺口 #2 · 待并入 master-solution-v2 §七（评测与质量保障）*

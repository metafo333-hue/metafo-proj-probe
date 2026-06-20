# probe 盲评框架 · README

> 元验 L5 业务验收 · 商业假设验证
> 日期：2026-06-20

---

## 一、这是什么

**核心假设**：多维度报告（含视听六层/L2多条规律/L3账号判断/L4竞品对比）比单维报告（仅账号画像）对用户更有价值。

这是 probe **定价与商业化的核心依据**。不验证这个假设，就没有理由向用户收费换多维报告。

本目录是 promptfoo 盲评框架 + 脱敏样例。**⚠️ 尚未真跑**——原因：需要真实多样本（≥20 个不同账号）和批量跑预算，当前框架是搭好等样本就绪后跑。

---

## 二、诚实说明（未真跑）

| 状态 | 说明 |
|------|------|
| ✅ 框架已搭 | `promptfooconfig.yaml` + `datasets/` 结构完整，可直接跑 |
| ✅ 脱敏样例 | 2 条魔芋号风格脱敏样例，供调试评委 prompt 用 |
| ❌ 未真跑 | 评委 LLM 调用需 ufo2 LiteLLM 在线 + LITELLM_MASTER_KEY |
| ❌ 未批量验证 | C2 判据（≥70% 盲评胜率）需 ≥20 个真实账号样本才统计有效 |
| ❌ 未付费跑 | 每条样本约 2-4 次 LLM 调用，20 样本约 80 次调用，按硅基流动估算约 ¥2-5 |

**里程碑**：当 probe 有 ≥20 个真实账号的对比报告对后，批量跑这个框架，观察 winner=多维报告 的比例是否 ≥70%。

---

## 三、怎么跑

### 前置条件

```bash
# 1. 安装 promptfoo
npm install -g promptfoo
# 或免安装
npx promptfoo@latest --version

# 2. 确认 ufo2 LiteLLM 可达（tailscale 需在线）
curl http://100.64.0.7:4000/health

# 3. 设置评委模型密钥（不要写死在配置里）
export LITELLM_MASTER_KEY="从 vault 取"
```

### 运行评测

```bash
# 进入 eval 目录
cd probe/eval

# 跑盲评（2 条样例，约 4 次 LLM 调用）
npx promptfoo eval --config promptfooconfig.yaml

# 查看结果（Web UI）
npx promptfoo view

# 输出 JSON（批量统计用）
# 结果在 eval/results/blind_eval_results.json
```

### 批量胜率统计（真实跑完后）

```bash
# 统计多维报告胜率（需先确认哪个变量对应多维报告）
python3 scripts/calc_win_rate.py eval/results/blind_eval_results.json
```

---

## 四、评测设计说明

### 对比什么

| 对比项 | 内容 |
|--------|------|
| **单维报告（report_a 或 report_b）** | 仅账号画像：均值数据 + 简单描述，无视听分析/L2规律/L3判断 |
| **多维报告（report_a 或 report_b）** | 七段完整报告：视听六层/L2多条规律/L3账号整体性/L4方向 |
| **顺序随机** | A/B 标签随机对应单维/多维，防评委主观偏差 |

### 为什么是 LLM-as-Judge

- 人工盲评是金标准，但成本高（需招募≥20 名真实短视频运营人员）
- LLM-rubric 作为**一轮自动筛选**：rubric 分 ≥4 且 winner=多维报告 → 进入人工抽样复核
- 评委模型选 Qwen3-32B（推理能力强，对短视频行业有认知，自托管无数据出门风险）

### 四维判据（来源：元验 L5 C2 评分卡）

| 维度 | 含义 | 权重 |
|------|------|------|
| **信息量** | 覆盖维度是否完整（视听六层/L2/L3/L4） | 25% |
| **可执行性** | 用户看完能做什么（具体行动清单+优先级） | 30% |
| **诚实度** | 黑盒数据是否如实标「拿不到」，不硬凑 | 20% |
| **决策可用性** | 能否直接做「要/不要参考」的决策 | 25% |

### 通过判据（C2 四维 · 元验 L5）

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **盲评胜率** | ≥70% | 多维报告 winner 比例 ≥70%（需≥20样本统计） |
| **零追问交付** | ≥80% | 用户拿到报告无需追问即可决策 |
| **省力** | ≥3× | 对比自行收集信息，节省时间 ≥3 倍 |
| **准确** | ≥20pct 提升 | 对比纯直觉判断，准确率提升 ≥20 个百分点 |

> 当前框架只覆盖「盲评胜率」这一项（自动化评测）。其余三项需要真实用户研究（访谈/问卷），属于人工 L5 验收范畴。

---

## 五、数据集说明

```
eval/datasets/
└── blind_eval_samples.jsonl    # 脱敏样例（2条）
    # 每条字段：
    # account_context: 账号背景（脱敏）
    # report_a: 报告 A（单维或多维，随机分配）
    # report_b: 报告 B（另一版本）
```

### 新增真实样本

```jsonl
{"vars":{"account_context":"...", "report_a":"...", "report_b":"..."}}
```

**样本要求**：
- 同一账号的两版报告（单维 vs 多维），由 `probe/app/services/account_report.py` 生成
- 账号数据必须脱敏（不含真实 uid/link，只保留量级描述）
- 涉密字段（数据源）不得出现在任何报告中（验收标准维度4）

---

## 六、评委模型备选

| 选项 | 端点 | 优先级 | 说明 |
|------|------|--------|------|
| **ufo2 LiteLLM + Qwen3-32B** | `http://100.64.0.7:4000/v1` | 首选 | 完全自托管，数据不出门 |
| **硅基流动 Qwen3-32B** | `https://api.siliconflow.cn/v1` | 备选 | 低成本，国内，数据不出中国 |

切换方式：修改 `promptfooconfig.yaml` 中 `providers[0].config.apiBaseUrl`。

⚠️ 禁用 OpenAI / Anthropic 云端 API 跑评测（数据出门违反安全铁律）。

---

## 七、关联文档

| 文档 | 位置 |
|------|------|
| 报告验收标准（判据真源） | `运营报告/probe-word-report-acceptance-standard-v1.0.md` |
| 分析逻辑框架（多维报告内容依据） | `运营报告/probe-analysis-logic-framework-v1.0.md` |
| 七段输出规范 | `metafoclaw-git/docs/engines/probe/3-build/probe-deep-analysis-output-spec-v1.2.md` |
| 元验五阶（L5 业务验收位置） | `~/.claude/rules/L1-infra/acceptance.md` |
| 账号报告生成代码 | `probe/app/services/account_report.py` |

# 技术源卡 M3 · 事实核查与矛盾检测工具链

> 需求真源：audit-system-v1 闸2（多源交叉 + 忠实度）/ 闸5（矛盾检测 NLI）
> 喂缺口 G4（可靠度表示）· 8闸主体自研不外包
> checked_at: 2026-06-11 · 调研员：probe M3 subagent

---

## 候选实测

### 1. Loki / OpenFactVerification（Libr-AI）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/Libr-AI/OpenFactVerification |
| **license** | MIT |
| **stars** | ~1,100 |
| **最近活跃** | 2024-10（arXiv v1 发布）；COLING 2025 Demo 收录 |
| **架构一句话** | 五步流水线：Decomposer → CheckWorthiness → QueryGen → EvidenceRetriever(Serper) → ClaimVerifier(LLM + 可选NLI) |
| **搜索层可换性** | ⚠️ 当前绑 Serper API（Google Search），官方路线图计划支持 LlamaIndex 接自定义源；每个组件实现为独立 Python 类，**可替换但需自行改写 EvidenceRetriever** |
| **中文支持** | ✅ 官方文档明确支持中英双语（arXiv 论文确认） |
| **hands_on** | 无 venv 实测（依赖 OpenAI API + Serper Key）；论文 pipeline 描述与 README 一致 |
| **pip install** | `pip install -r requirements.txt`（无 PyPI 包，需 Poetry 或 requirements） |

**关键细节**：
- Claim Verifier 支持可选 NLI 模型对证据片段做 entailment/contradiction 排序，**是喂闸5的接口点**
- 四步 LLM + 一步搜索；LLM 层支持本地模型（ollama 等），Serper 是唯一外部搜索锁点
- 论文 arXiv:2410.01794，COLING 2025 Demos Section 4

---

### 2. FacTool（GAIR-NLP）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/GAIR-NLP/factool |
| **license** | Apache-2.0 |
| **stars** | ~933 |
| **最近活跃** | ⚠️ README 最新公告 2023-09；无 2024-2025 更新记录，**疑似停止维护** |
| **架构一句话** | 工具增强型框架：四任务（QA/代码/数学/文献）各用专属工具调用（搜索/执行器/计算器/Scholar API）+ LLM 验证 |
| **搜索层可换性** | ⚠️ 强绑 Serper API（QA任务）+ Scraper API（文献任务），无官方替换接口 |
| **中文支持** | ✅ 有 ChineseFactEval 基准数据集（2023-09 发布），核心逻辑可处理中文 |
| **hands_on** | 可 `pip install factool`；dataset/chinese/ 目录存在，结构完整 |
| **pip install** | `pip install factool` ✅ |

**关键细节**：
- 非纯 NLI 路线，更侧重工具调用（代码执行 / 数学验证），与闸5矛盾检测用途相关度低于 Loki/MiniCheck
- 停止维护风险高，OpenAI API 依赖版本可能过旧
- 有中文数据集是亮点，但无中文 NLI 专项模型

---

### 3. MiniCheck（Liyan06 / BespokeLabs）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/Liyan06/MiniCheck |
| **license** | Apache-2.0（小模型）；Bespoke-MiniCheck-7B = CC BY-NC 4.0（**商用需联系授权**） |
| **stars** | ~211 |
| **最近活跃** | EMNLP 2024 收录；2024 年活跃 |
| **架构一句话** | 纯本地 NLI 评分器：`MiniCheck(document, sentence) → [0,1]`，无需联网，grounding-doc 忠实度判定 |
| **搜索层可换性** | ✅ 不涉及搜索层，纯本地推理，直接喂（文档, 声明）对即可 |
| **中文支持** | ❌ 文档无中文支持；在英文 LLM-AggreFact 基准训练，中文性能未知 |
| **hands_on** | `pip install "minicheck @ git+https://github.com/Liyan06/MiniCheck.git@main"` |
| **模型变体** | MiniCheck-RoBERTa-Large / MiniCheck-DeBERTa-v3-Large / MiniCheck-Flan-T5-Large(770M 推荐) / Bespoke-MiniCheck-7B(SOTA) |

**关键细节**：
- **最符合闸2忠实度判定**：给定 retrieved evidence + claim → 输出支持概率，零网络调用
- GPT-4 级准确率，Flan-T5-Large 版本仅 770M，CPU 可推
- 商用路线选 Flan-T5/DeBERTa 变体（Apache-2.0），避开 7B CC-NC 版本
- 论文 arXiv:2404.10774，EMNLP 2024

---

### 4. OpenFactCheck（MBZUAI / yuxiaw）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/mbzuai-nlp/OpenFactCheck |
| **license** | AGPL-3.0 ⚠️（**Copyleft，商用需注意传染性**） |
| **stars** | ~29（低） |
| **最近活跃** | v1.0.1 PyPI；v2 开发中 |
| **架构一句话** | 统一评估框架：CUSTCHECKER（自定义事实核查流）/ LLMEVAL（LLM 事实性评测）/ CHECKEREVAL（核查器可靠度基准） |
| **搜索层可换性** | ✅ 设计为"可定制自动事实核查系统"，支持接入自定义 checker 组件；但文档未明确说明替换 retriever 的 API |
| **中文支持** | ❌ 无明确提及 |
| **hands_on** | `pip install openfactcheck==1.0.1` |

**关键细节**：
- 定位是评测框架而非生产 pipeline，更适合对比多个核查器的准确率
- AGPL-3.0 对 probe 产品化有法律风险，需确认使用方式（仅本地用/SaaS化）
- stars 极低，社区支持弱

---

### 5. AlignScore（yuh-zha / ACL 2023）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/yuh-zha/AlignScore |
| **license** | MIT |
| **stars** | ~164 |
| **最近活跃** | ACL 2023 论文；2023 年发布，无 2024 后更新记录，**维护冻结** |
| **架构一句话** | 统一对齐函数：RoBERTa-base/large 在 7 任务（NLI/QA/摘要/IR 等）联合训练，输出忠实度分数 |
| **搜索层可换性** | ✅ 不涉及搜索，纯本地 context→claim 打分 |
| **中文支持** | ❌ 英文训练数据（SNLI/MultiNLI 等），无中文支持 |
| **hands_on** | `git clone && pip install .`（无 PyPI）；需 PyTorch 1.12.1 |

**关键细节**：
- 与 MiniCheck 功能重叠（忠实度打分），但 MiniCheck 在 EMNLP 2024 更新、准确率更高
- 可作为 MiniCheck 的备选/交叉验证器
- 不推荐作为主力件（维护冻结 + 被 MiniCheck 性能超越）

---

### 6. cross-encoder/nli-deberta-v3 系列（sentence-transformers）

| 字段 | 值 |
|------|----|
| **repo/model** | https://huggingface.co/cross-encoder/nli-deberta-v3-large |
| **license** | MIT（模型卡无明确说明，DeBERTa-v3 原模型为 MIT） |
| **stars/downloads** | 高下载量（HuggingFace 主流 NLI 模型） |
| **最近活跃** | 持续维护（sentence-transformers 官方维护） |
| **架构一句话** | DeBERTa-v3-large 在 SNLI+MultiNLI 训练，输出 contradiction/entailment/neutral 三分类 |
| **搜索层可换性** | ✅ 纯本地推理，无搜索依赖 |
| **中文支持** | ❌ 仅英文（SNLI/MultiNLI 训练） |
| **hands_on** | `pip install sentence-transformers`；`CrossEncoder('cross-encoder/nli-deberta-v3-large').predict([...])` |
| **MNLI 准确率** | MNLI mismatched: 90.04%，SNLI: 92.38% |

**关键细节**：
- **闸5矛盾检测最轻量可控选项**（英文场景）
- 变体：xsmall(22M) / small(44M) / base(86M) / large(304M) — 按延迟需求选
- 不适合中文，需配对中文 NLI 模型

---

## 拆件分析

| 候选 | 整移 | 拆什么件 | 只抄思想 |
|------|------|---------|---------|
| **Loki** | ❌ 不整移（Serper 绑死 + OpenAI 依赖） | ✅ **Decomposer（claim拆解）** + **CheckWorthiness 过滤逻辑**：抽取两个 LLM prompt 模板，接 ufo2 litellm | ✅ 五步流水线结构可作 audit-system 的闸前预处理参考 |
| **FacTool** | ❌ 停止维护 + 双 API 锁定 | ✅ ChineseFactEval 数据集可复用作测试集 | ✅ 多任务（代码/数学/文献）核查设计，未来拓展参考 |
| **MiniCheck** | ✅ **推荐整移 Flan-T5-Large 变体**（喂闸2忠实度） | ✅ `scorer.score(docs=[ev], claims=[sent])` 接口直接调用 | ✅ synthetic 数据构造方法（GPT-4 生成反例）可指导闸5训练集制备 |
| **OpenFactCheck** | ❌ AGPL-3.0 风险 | ✅ CHECKEREVAL 评测方法论（用人工标注数据评估 checker 可靠度） | ✅ pipeline 组合模式参考 |
| **AlignScore** | ❌ 被 MiniCheck 超越，维护冻结 | ❌ 不拆 | ✅ 七任务联合训练思想（多任务迁移提升忠实度判定） |
| **DeBERTa-v3-NLI** | ✅ **直接整移（英文闸5矛盾检测）** | ✅ `CrossEncoder.predict([premise, hypothesis])` → contradiction 分数 | ✅ MNLI three-class 设计（contradiction/neutral/entailment 三态）映射闸5输出 |

---

## 中文 NLI 模型小节

> 英文 NLI 模型（DeBERTa-v3 / MiniCheck）不支持中文，probe 需处理中文内容时必须另配。

### 可用中文 NLI / 矛盾检测模型清单

| 模型 | 来源 | 训练数据 | 性能 | License | 推荐程度 |
|------|------|---------|------|---------|---------|
| **IDEA-CCNL/Erlangshen-Roberta-110M-NLI** | IDEA CCNL | CMNLI + OCNLI + SNLI(中)，共 101万样本 | CMNLI 80.83 / OCNLI 78.56 | Apache-2.0 | ⭐⭐⭐ 推荐首选（110M 轻量 + 开放协议） |
| **Jaren/chinese-roberta-wwm-ext-large-NLI** | 社区 | SNLI + MNLI + DNLI + KvPI + OCNLI + CMNLI | 未公布 | ❌ 无 license 声明 | ⚠️ 性能预期较强但无协议风险 |
| **IDEA-CCNL/Erlangshen-MacBERT-325M-NLI-Chinese** | IDEA CCNL | FewCLUE OCNLI | OCNLI Few-shot | Apache-2.0 | ⭐⭐ 适合 few-shot 场景 |
| **uer/sbert-base-chinese-nli** | UER | ChineseTextualInference | 未公布 | Apache-2.0 | ⭐⭐ sentence embedding 向量相似场景 |

**实测来源**：HuggingFace model cards 直接 fetch（2026-06-11）+ OCNLI 论文（arXiv:2010.05444）

**中文 NLI 落矩阵建议**：
- 闸5矛盾检测（中文）→ `Erlangshen-Roberta-110M-NLI`，Apache-2.0，轻量，可本地部署 ufo（GPU）
- 更强性能可选 `chinese-roberta-wwm-ext-large-NLI`（large 骨架），但需确认 license

---

## tech-gate 12 闸速查表

> 按 probe audit-system-v1 闸编号映射工具件落点

| 闸 | 名称 | 本卡推荐工具件 | 备注 |
|----|------|-------------|------|
| 闸1 | 来源可信度 | — | 源注册表（M7/M10 范畴） |
| **闸2** | **多源交叉 + 忠实度** | **MiniCheck-Flan-T5-Large**（英文）/ Erlangshen-Roberta-110M（中文） | `score(docs=[evidence], claims=[sent])` → 支持概率阈值 |
| 闸3 | 引用溯源 | — | 链接抽取层（M2 范畴） |
| 闸4 | 时效性 | — | 发布时间解析（日期抽取） |
| **闸5** | **矛盾检测（NLI）** | **cross-encoder/nli-deberta-v3-large**（英文）/ Erlangshen-Roberta-110M（中文） | contradiction score > 阈值 → 标记矛盾对 |
| 闸6 | 对抗证伪 | Claude 多代理（已决·不在本卡）| R23.1 集成模式 |
| 闸7 | 实体一致性 | — | NER 对比（M2 范畴） |
| 闸8 | 综合置信度 | MiniCheck raw_prob → G4 可靠度表示 | 0-1 概率输出直接喂 G4 缺口 |

**Claim 拆解（前置所有闸）**：
- 优先用 **Loki 的 Decomposer LLM prompt 模板**（抽取，非整移框架）
- 接 ufo2 litellm 别名（bl-flash / 本地模型）
- 输出：原子声明列表，每条含溯源位置

---

## verdict

### 工具件档位评定

| 候选 | 档位 | 理由 |
|------|------|------|
| **MiniCheck-Flan-T5-Large** | **A（直接整移）** | 纯本地 NLI、Apache-2.0、EMNLP 2024 SOTA、770M CPU 可推、接口极简 `score(docs, claims)` |
| **cross-encoder/nli-deberta-v3-large** | **A（直接整移）** | 英文矛盾检测首选、MIT、sentence-transformers 维护、三分类输出完美映射闸5 |
| **Erlangshen-Roberta-110M-NLI** | **A（中文场景）** | Apache-2.0、110M、OCNLI/CMNLI 训练、IDEA CCNL 出品质量可信 |
| **Loki Decomposer（拆件用）** | **B（抽 prompt 模板）** | 框架不整移（Serper 锁）但 claim 拆解 prompt 设计高质量；中文支持是加分 |
| **FacTool** | **C（仅数据集参考）** | 停止维护 + 双 API 锁；ChineseFactEval 数据集有参考价值 |
| **AlignScore** | **C（存档备查）** | 被 MiniCheck 超越 + 维护冻结 |
| **OpenFactCheck** | **C（评测参考）** | AGPL-3.0 风险 + stars 极低；评测方法论可借鉴 |

**落矩阵格（Validator = L3）**：

```
L3 验证层工具件分配
├── claim 拆解（前置）  → Loki Decomposer prompt 模板 × ufo2 litellm
├── 闸2 忠实度判定     → MiniCheck-Flan-T5-Large（英）/ Erlangshen-110M（中）
├── 闸5 矛盾检测       → DeBERTa-v3-NLI（英）/ Erlangshen-110M（中）
└── 闸8 G4 可靠度输出  → MiniCheck raw_prob float → 可靠度归一化
```

**红线确认（不自己爬 + 源治理）**：MiniCheck / DeBERTa-v3-NLI / Erlangshen 三件均为纯本地推理，零网络调用，**完全符合 probe 红线**。

---

## 顺手发现

1. **Bespoke-MiniCheck-7B = CC BY-NC 4.0**（非商用），商用路线必须用 Flan-T5-Large / DeBERTa-v3 变体（Apache-2.0）
2. **FacTool 疑似停止维护**（最新公告 2023-09），建议不作为生产依赖
3. **OpenFactCheck AGPL-3.0**：若 probe 以 SaaS 形式提供服务，AGPL 要求开源整个服务端，需法律确认
4. **AlignScore 被 MiniCheck 超越**：同为忠实度打分器，MiniCheck 2024 年在 LLM-AggreFact 基准上全面领先，AlignScore 可降级为交叉验证备选
5. **中文 NLI 缺口**：目前最佳中文选项（Erlangshen-Roberta-110M）OCNLI 78.56 / CMNLI 80.83，距英文顶配（90%+）仍有差距，高精度中文场景建议同步用 LLM 重验（接闸6）
6. **claim 拆解无独立 PyPI 包**：Loki/FacTool 的 claim decomposer 都是 LLM prompt 驱动，无专门 NLP library，直接抽 prompt 模板是最轻量路线；若需无 LLM 的句子级分割，spaCy 中文模型（zh_core_web_sm）可作 fallback

---

*sources（现场实测 2026-06-11）*：
- Loki repo: https://github.com/Libr-AI/OpenFactVerification
- Loki paper: https://arxiv.org/abs/2410.01794
- FacTool repo: https://github.com/GAIR-NLP/factool
- MiniCheck repo: https://github.com/Liyan06/MiniCheck
- MiniCheck paper: https://arxiv.org/abs/2404.10774
- OpenFactCheck: https://github.com/mbzuai-nlp/OpenFactCheck
- AlignScore: https://github.com/yuh-zha/AlignScore
- DeBERTa-v3-NLI: https://huggingface.co/cross-encoder/nli-deberta-v3-large
- Bespoke-MiniCheck-7B: https://huggingface.co/bespokelabs/Bespoke-MiniCheck-7B
- Erlangshen-Roberta-110M-NLI: https://huggingface.co/IDEA-CCNL/Erlangshen-Roberta-110M-NLI
- Jaren/chinese-roberta-NLI: https://huggingface.co/Jaren/chinese-roberta-wwm-ext-large-NLI
- uer/sbert-chinese-nli: https://huggingface.co/uer/sbert-base-chinese-nli

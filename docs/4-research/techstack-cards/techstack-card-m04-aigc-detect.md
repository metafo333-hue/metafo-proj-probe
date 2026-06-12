# 技术源卡 M4 · AIGC/污染检测(闸3)

> 需求真源：audit-system-v1 闸3 · 原则：只标签不断言
> checked_at: 2026-06-11 · 调研员：probe M4 agent

---

## 候选实测

### 1. Binoculars（ahans30）

| 字段 | 内容 |
|------|------|
| **Repo** | https://github.com/ahans30/Binoculars |
| **License** | BSD-3-Clause |
| **Stars** | ~385（2026-06-11） |
| **最近活跃** | ICML 2024 发表；GitHub 仍可用，近期无重大 commit |
| **方法** | Zero-shot；用 Falcon-7B + Falcon-7B-Instruct 双模型对比 PPL/X-PPL 比值，无需任何训练数据 |
| **中文效果** | **未评估中文**。论文评测了 Urdu/Russian/Bulgarian/Arabic（M4 数据集），结论：低资源语言假阳性率低，但机器文本常被误判为人类；中文完全空白 |
| **算力需求** | 两个 Falcon-7B 各需 ~16GB VRAM（FP16），合计约需 **32GB+ VRAM**；INT8 量化可压至约 16GB；CPU 运行极慢不推荐 |
| **误报率数据** | 英文场景 FPR=0.01%（论文实测，ChatGPT 生成文本 TPR>90%）；非英语场景 FPR 数据未报告；⚠️非母语英语作者误报问题在同类方法中普遍存在（见缺口分析） |
| **优劣** | ✅ 无需训练·适应新模型·英文效果顶级 ❌ 中文未知·双 7B 显存大·对低资源语言机器文本易漏报 |

---

### 2. Fast-DetectGPT（baoguangsheng）

| 字段 | 内容 |
|------|------|
| **Repo** | https://github.com/baoguangsheng/fast-detect-gpt |
| **License** | MIT |
| **Stars** | ~407（2026-06-11） |
| **最近活跃** | ICLR 2024 发表；仓库活跃 |
| **方法** | Zero-shot；以条件概率曲率（conditional probability curvature）替代 DetectGPT 的扰动步骤，速度提升约 340×；支持代理模型 scoring |
| **中文效果** | 原论文**未测中文**；EnsemJudge（NLPCC2025 冠军）将其作为子模块之一（使用 Qwen2.5-7B/GLM-4-9B 作为评分模型），在中文语境下有实测 |
| **算力需求** | 论文实验用 Tesla A100 80G；实际推理使用单个评分模型（可选 GPT-2 级小模型）；轻量模式 CPU 可跑，但精度下降 |
| **误报率数据** | 对 PADBen 基准（抗改写攻击）FPR@strict=约 16%；AUROC≈0.84；英文场景整体优于 DetectGPT 但不如 Binoculars |
| **优劣** | ✅ MIT 开源·速度快·可换小模型降算力 ❌ 中文未直接验证·准确率不及 Binoculars（英文）·改写攻击下 FPR 较高 |

---

### 3. EnsemJudge（NLPCC2025 中文冠军）

| 字段 | 内容 |
|------|------|
| **Repo** | https://github.com/johnsonwangzs/MGT-Mini |
| **Paper** | EnsemJudge: Enhancing Reliability in Chinese LLM-Generated Text Detection (arXiv:2603.27949) |
| **License** | 仓库开源；具体 license ⚠️ 待确认 |
| **Stars** | 新仓，较少 |
| **最近活跃** | 2025 年 NLPCC 共享任务第一名，2026-03 论文挂 arXiv |
| **方法** | 18 子检测器动态集成（规则/无训练/有训练三类混合）+ 边界案例走 Qwen2.5-72B-Instruct ICL 决策 |
| **中文效果** | **中文专项实测最佳**：宏 F1=**0.9922**（含对抗样本完整测试集）；非对抗样本 F1=1.0000；64 字短文 F1=0.9590；512 字以上 F1=1.0000 |
| **算力需求** | 18 子模块中含多个 7B 模型（Qwen2.5-7B / GLM-4-9B），边界案例需 72B 模型；**全量运行需大型 GPU 节点**；可裁剪为仅用轻量子集 |
| **误报率数据** | 论文未明确报告 FPR；对抗样本 F1=0.9870-0.9990（含改写/扰动攻击） |
| **优劣** | ✅ 中文目前最强·鲁棒性高·开源可裁剪 ❌ 全量需 72B 模型·重度工程·对 probe-a 直接部署不现实 |

---

### 4. LLM Encoder vs Decoder·LoRA 中文检测（Qwen2.5-7B LoRA）

| 字段 | 内容 |
|------|------|
| **Paper** | arXiv:2509.00731（2025-09，中文 AI 文本检测） |
| **方法** | LoRA fine-tune Qwen2.5-7B（rank=16）二分类；对比编码器（RoBERTa/BERT）与解码器模型 |
| **中文效果** | Qwen2.5-7B+LoRA：**95.94%准确率**；BERT-large：79.33%；RoBERTa-wwm-ext-large：76.31% |
| **算力需求** | 训练需 GPU；推理期 7B 模型 INT8 约 8-10GB VRAM；LoRA 权重小可发布 |
| **误报率数据** | 未明确报告 FPR；解码器模型在 distribution shift 下 precision-recall 更均衡 |
| **优劣** | ✅ 中文效果强·LoRA 权重轻·有开放复现路径 ❌ 需要微调数据·对新域可能退化 |

---

### 5. M4GT-Bench + XLM-R（多语言参考基线）

| 字段 | 内容 |
|------|------|
| **Repo** | https://github.com/liamdugan/raid（RAID）；M4GT-Bench 于 ACL 2024 发表 |
| **方法** | XLM-R fine-tune 多语言分类；代表了通用多语言基线 |
| **中文效果** | XLM-R 中文子集 F1=**84.73%**（Precision 76.85%/Recall 95.18%）；属"60<F1<85"中等档 |
| **算力需求** | XLM-R-large 约 1.3B 参数；推理 CPU 可跑（较慢），GPU 加速约 10-20× |
| **误报率数据** | Precision 76.85%（即 FPR 约 23%，较高） |
| **优劣** | ✅ 已有中文 benchmark 数据·多语言单模型 ❌ FPR 高·精度不理想 |

---

## 中文检测缺口分析

| 问题 | 现状 |
|------|------|
| **主流检测器均英文向** | Binoculars / Fast-DetectGPT 论文均未测中文，PPL 比值法在非 Common Crawl 主导语言效果未知 |
| **中文专项研究起步** | NLPCC2025 共享任务（DetectRL-ZH）才是第一个正式中文 benchmark；30+ 团队参赛，冠军 F1=0.9922 |
| **主流方法迁移风险** | perplexity-based 方法在中文 LLM（Qwen/DeepSeek）上未系统验证；中文字符级结构与英文词边界不同 |
| **短文本是最大弱点** | EnsemJudge 实测：64 字 F1=0.9590 vs 512 字 F1=1.0000；probe 来源可能含大量短摘要/标题 |
| **高质量中文生成更难检测** | Qwen2.5 生成文本人类感极强，RoBERTa 对其准确率仅 88.91% |
| **误报伦理风险** | 非母语中文写作（如翻译稿、简洁风格）可能被 perplexity 方法误判；建议置信度标注而非硬判定（符合闸3只标签原则） |

---

## 部署方案草案

### 架构：ufo（GPU 主节点）+ probe-a（CPU 轻量调用）

```
probe-a（采集节点·无 GPU）
    ↓ Tailscale 100.64.0.8 内网调用
ufo（GPU 算力机·RTX 系列）
    ├── aigc-detect-api（FastAPI 服务）
    │   ├── 轻量层：Fast-DetectGPT（Qwen2.5-7B INT8·约 10GB VRAM）
    │   └── 精确层：Binoculars（Falcon-7B×2·约 32GB VRAM·仅英文源调用）
    └── 结果缓存：Redis（content hash → label·TTL 24h）
```

**推荐分级策略：**

| 级别 | 方法 | 触发条件 | 算力 |
|------|------|---------|------|
| L0·超轻量 | 规则启发（句式均匀/标点异常/特征词）| 全量预筛，Recall 优先 | CPU·probe-a 本机 |
| L1·统计检测 | Fast-DetectGPT（Qwen2.5-7B INT8）| 通过 L0 的文本 | ufo GPU·约 10GB VRAM |
| L2·精确（英文）| Binoculars（Falcon-7B×2）| 英文来源·置信低 | ufo GPU·约 32GB VRAM |
| L2·精确（中文）| Qwen2.5-7B LoRA fine-tuned | 中文来源·置信低 | ufo GPU·约 10GB VRAM·⏳需训练 |

**关键链路约束：**
- probe-a → ufo 走 Tailscale 100.64.0.8，内网延迟 <5ms
- ufo GPU 内存总量需确认（若 <32GB 则 Binoculars L2 精确层需 INT4 量化或仅保留 L1）
- 结果只写 `aigc_label`（`suspected_ai` / `likely_human` / `uncertain`）+ confidence score；**不做硬断言**，符合闸3原则

**近期可落地（无需训练）：**
1. ufo 部署 Fast-DetectGPT（Qwen2.5-7B INT8）→ L1 层立即可用
2. probe-a 侧 L0 规则检测纯 Python CPU 跑
3. 中文 LoRA 版本：用 NLPCC2025 DetectRL-ZH 数据集 fine-tune Qwen2.5-7B（⏳约 1-2 天训练）

---

## tech-gate 12 闸速查表（M4 涉及闸3）

| 闸 | 名称 | M4 AIGC 检测的答案 |
|----|------|------------------|
| G1 | 数据合规 | 检测器本身不产生数据，输入来源文本已过 G1 |
| G2 | 来源可溯 | 检测结果写入 `aigc_label` 字段，可溯 |
| G3 | **抗污染/抗AIGC（本闸）** | 本模块本身即 G3 实现；输出置信标签不做硬断言 |
| G4 | 去重 | 结果缓存（content hash）避免重复推理 |
| G5 | 时效性 | 检测方法随 LLM 迭代需更新；定期 benchmark 验证 |
| G6 | 权威性验证 | 不适用（G3 是统计检测，不判权威性） |
| G7 | 来源独立性 | 检测器为独立模块，不影响 G7 |
| G8 | 一致性 | 同文本 deterministic 输出（固定种子） |
| G9 | 实体对齐 | 不适用 |
| G10 | 隐私/PIPL | 检测器仅用文本特征，无 PII 读取 |
| G11 | 存储合规 | 仅存 hash+label，不存原文 |
| G12 | 输出幂等 | ✅ 相同 content hash → 相同标签（缓存保证） |

---

## verdict

**档位：B+（有条件推荐·中文需补训练）**

| 维度 | 结论 |
|------|------|
| 英文场景 | Binoculars（L2）+ Fast-DetectGPT（L1）可覆盖，FPR 极低（0.01%），闸3有效 |
| 中文场景 | 短期用 Fast-DetectGPT（Qwen2.5 backbone）作 L1；中期 fine-tune LoRA 版达 95.94%；EnsemJudge 架构可参考但重度 |
| 算力路径 | L0 CPU probe-a·L1/L2 GPU ufo；probe-a 通过 Tailscale 调 ufo API，链路清晰 |
| 误报伦理 | **务必以置信度标签输出，不做硬断言**；已符合闸3"只标签不断言"原则；FPR 超过 5% 时应降级为"uncertain"而非"suspected_ai" |
| 落矩阵格 | **Validator = L3 · 闸3（AIGC/污染标签）** |

**推荐优先级：**
1. **近期（0 训练成本）**：Fast-DetectGPT（MIT·Qwen backbone·L1 统计层）
2. **同步（零成本 English）**：Binoculars（BSD-3·L2 精确层·仅英文来源）
3. **中期（需微调）**：Qwen2.5-7B + LoRA fine-tune on DetectRL-ZH（NLPCC2025 公开数据集）
4. **参考架构**：EnsemJudge（NLPCC2025 冠军·F1=0.9922·中文最强·开源可裁剪核心子模块）

---

## 顺手发现

1. **NLPCC2025 DetectRL-ZH 是目前最好的中文 AIGC 检测公开 benchmark**，30+ 团队参赛，数据集已公开（http://tcci.ccf.org.cn/conference/2025/taskdata.php），可直接用于 M4 训练/评估。

2. **Binoculars 使用 Falcon-7B**，但 EnsemJudge 实测改用 Qwen2.5-7B 作为 Binoculars 的 backbone 在中文上效果更好——意味着 Binoculars 方法可以换模型骨架，适配中文 LLM。

3. **EnsemJudge 中文 F1=0.9922 但全量需 Qwen2.5-72B-Instruct 作决策兜底**；若只取其 18 子模块中的轻量子集（不含 72B 决策模块），可以大幅降低算力成本，精度略降但仍可接受。

4. **误报伦理红线**：2025 Stanford 研究显示非母语英语写作的 FPR 超 20%；中文场景中对简洁风格/翻译腔的误判概率更高，建议 probe M4 对所有结果附 confidence_score，下游消费方自决阈值，不由 M4 硬切。

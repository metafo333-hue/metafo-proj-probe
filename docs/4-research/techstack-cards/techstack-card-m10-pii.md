# 技术源卡 M10 · 隐私/PII 工程

> 需求真源：privacy 设计（persist_policy 三态·PIPL）· probe-a 红线：脱敏管线先于采集
> checked_at: 2026-06-11 · 本卡有现场实测数据（/tmp/ts-m10 venv + presidio 2.2.359）

---

## 候选实测

### C1 · presidio（microsoft）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/microsoft/presidio |
| **license** | MIT |
| **stars** | 8.6k（2026-06-11） |
| **最近活跃** | 最新版 2.2.362（2026-03-18）· 持续发版 |
| **PyPI** | presidio-analyzer 2.2.359 / presidio-anonymizer 2.2.362 |
| **核心依赖** | spacy + phonenumbers + tldextract（不含 NLP 模型本身） |
| **包体积** | presidio-analyzer 201 kB（不含 spaCy 模型；en_core_web_sm ~12 MB） |

**中文 PII 支持（关键调研结论 · 现场实测 2026-06-11）：**

官方文档明确：默认只支持英文。`supported_entities` 页面无任何中国/CN locale 条目。实测用 `language="zh"` 直接报 `KeyError: 'zh'`——需先挂载 zh spaCy 模型。

现场实测结论：

| 实体类型 | 默认支持 | 需要定制 | 实测结果 |
|---------|---------|---------|---------|
| 中文手机号（1[3-9]xxxxxxxx）| ❌ 无专属 recognizer | 自定义 PatternRecognizer | 添加 5 行 regex 后 score=0.85 ✅ |
| 中国居民身份证（18位）| ❌ 无内置 | 自定义 PatternRecognizer | 添加 regex 后 score=0.90 ✅ |
| 邮箱地址 | ✅ 通用 | — | score=1.00 ✅ |
| 中文姓名（PERSON）| ❌ 严重缺口 | 需中文 NER 模型 | **全部 0 条（缺口确认）** |
| 中文地址（LOCATION）| ❌ 严重缺口 | 需中文 NER 模型 | 仅英文 NER 有效 |

脱敏实测（加了自定义 recognizer 后）：

```
原文: 身份证：110101199001011234，手机：13812345678，邮箱：zhangwei@example.com
脱敏: 身份证：<CN_ID_CARD>，手机：<CN_PHONE_NUMBER>，邮箱：<EMAIL_ADDRESS>
```

姓名检测全部失败：`张伟 / 李明 / 王芳 / 王小明` → PERSON 结果均为 0 条。

**中文 NER 修复路径：**
- 安装 `zh_core_web_sm`（~12 MB）或 `zh_core_web_trf`（BERT 级别·~400 MB）
- 配置 `NlpEngineProvider` 加载 zh 语言模型
- spaCy 中文 NER 社区反馈精度"比英文差很多，尤其 ORG vs LOC 混淆严重"
- 社区替代方案：`zh_PII`（6 stars · ltm920716）用 `zh_core_web_sm + en_core_web_lg + xx_ent_wiki_sm` 三模型组合

**hands_on 评分（中文场景）：** 结构化好、扩展性强；但开箱对 PIPL 五类 PII 只能自动覆盖邮箱，其余 4 类（手机/身份证/姓名/地址）全需定制——开发成本中等（3~5 天定制 + 调优）。

---

### C2 · scrubadub（LeapBeyond）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/LeapBeyond/scrubadub |
| **license** | MIT（原 deanmalmgren 版）/ Apache-2.0（scrubadubdub 衍生）|
| **stars** | ~407（2026-06-11） |
| **最近活跃** | 最新版 v2.0.1（2023-09-01）· **2023 年后无版本发布** |
| **中文 PII 支持** | ❌ 无中文 locale · 无中文手机号/身份证 detector |
| **依赖重量** | 可选接 spaCy、Stanford NER（独立子包 scrubadub_spacy/scrubadub_stanford）|
| **hands_on** | 英文场景轻量好用；中文场景需从零写 Detector；维护停滞风险高 |
| **checked_at** | 2026-06-11 |

结论：中文 PII 零原生支持 + 维护停滞（2023 年后无新版）→ 不推荐。

---

### C3 · MingJing（nn0nkey · 中文专项）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/nn0nkey/MingJing |
| **license** | MIT |
| **stars** | 16（2026-06-11） |
| **最近活跃** | 3 次 commit（具体时间戳未公开）· 项目较新 |
| **中文 PII 支持** | ✅ 专为中文设计：身份证（CN_ID_CARD）/ 手机号（CN_PHONE）/ 邮箱 / 姓名/地址（NER）/ API Key / JWT 等 29+ 类 |
| **依赖重量** | FastAPI + spaCy（中文模型）+ React + Docker · **全栈服务型，不是纯库** |
| **三引擎架构** | 规则引擎（regex）+ NLP 引擎（spaCy zh）+ LLM 引擎（可配云/本地）|
| **hands_on** | 直接可用的 API 服务；但 stars 极低 + commit 极少 = 生产信任度低 |
| **checked_at** | 2026-06-11 |

结论：中文覆盖最全，但项目太新、社区太小，不适合作为 probe PIPL 管线的核心依赖，可作为参考实现。

---

### C4 · OpenAI Privacy Filter（openai · 2026-04-22 新发布）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/openai/privacy-filter + HuggingFace openai/privacy-filter |
| **license** | Apache 2.0 |
| **参数量** | 1.5B 总参数 / 50M 活跃参数（MoE 架构）|
| **中文支持** | ⚠️ **"主要英文；非英文/非拉丁字符性能下降"** · 官方明确警告 |
| **实体类型** | 8 类：private_person / private_phone / private_address / private_email / account_number / private_url / private_date / secret |
| **依赖重量** | 需加载 ~1B 模型权重（Mac/laptop 可运行）|
| **hands_on** | 浏览器可运行；对中文场景官方自己标注"out-of-distribution"评估 · 不适合生产用于 PIPL |
| **checked_at** | 2026-06-11 |

结论：英文场景强，中文官方明确降级警告→ probe PIPL 场景不可依赖。

---

### C5 · GLiNER2-PII（fastino/Urchade · 2026 新发布）

| 维度 | 数据 |
|------|------|
| **repo** | arxiv.org/abs/2605.09973 · HuggingFace fastino/gliner2-privacy-filter-PII-multi |
| **license** | 研究发布（未明确商业条款）|
| **参数量** | ~300M（0.3B） |
| **中文支持** | ⚠️ 声称"7 语言多语种"训练，具体是否含 zh **未在公开文档明确列出** |
| **实体类型** | 42 类 PII（7 大类：个人/联系/政府ID/金融/数字身份/凭据/日期）|
| **SPY Benchmark** | span-level F1 最高（超过 OpenAI Privacy Filter）|
| **hands_on** | 学术新发布；presidio 有 GLiNER 集成示例；中文支持待验证 |
| **checked_at** | 2026-06-11 |

结论：学术前沿但中文 zh 支持证据不足；可列为 P1 验证候选（若 zh 支持确认则有望升主方案）。

---

### C6 · zh_PII（ltm920716 · 社区中文 presidio 扩展）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/ltm920716/zh_PII |
| **license** | 未注明 |
| **stars** | 6（2026-06-11） |
| **中文支持** | ✅ 专为 presidio 中文场景扩展：PERSON / ID_CARD / PHONE_NUMBER / LOCATION 等 13 类 |
| **依赖重量** | 需 zh_core_web_sm + en_core_web_lg + xx_ent_wiki_sm（三模型） |
| **hands_on** | single commit · stars 极低 · 无版本发布 · 仅可参考实现思路 |
| **checked_at** | 2026-06-11 |

结论：提供中文 presidio 集成的技术路径参考，但不可直接生产使用。

---

## 中文 PII 缺口分析

### 现状（实测确认）

presidio 默认配置对 PIPL 五类核心 PII 的覆盖：

| PIPL 核心 PII 类型 | presidio 默认 | 中文 regex 扩展后 | 中文 NER 加持后 |
|-------------------|--------------|------------------|----------------|
| 手机号 | ❌ 只匹配 US_BANK_NUMBER（低置信）| ✅（5 行 regex·score 0.85）| ✅ |
| 身份证号（18位）| ❌ 无识别 | ✅（regex·score 0.90）| ✅ |
| 邮箱 | ✅（score 1.00）| ✅ | ✅ |
| 中文姓名 | ❌ 完全失效（实测 0 条）| ❌ regex 无法覆盖 | 需 zh NER 模型 |
| 中文地址 | ❌ 完全失效 | ❌ | 需 zh NER 模型 |

### 修复方案

**Level 1（必须·probe-a 脱敏管线基线）**：
- 为 presidio 添加 2 个 PatternRecognizer（CN_ID_CARD + CN_PHONE_NUMBER）
- 开发量：~50 行代码 + 正则测试用例

**Level 2（推荐·覆盖姓名/地址）**：
- 安装 `zh_core_web_sm` 挂载 zh NlpEngine
- 注意：spaCy zh NER 对中文姓名识别精度有限（尤其短名字），需结合 context words 提升召回
- 备选：接 zh_core_web_trf（BERT，精度更高但 ~400 MB，probe-a 内存占用需评估）
- 开发量：~1~2 天调试

**Level 3（可选·PIPL 高合规要求）**：
- 接 GLiNER2-PII（待验证 zh 支持）或本地中文 NER 微调模型
- 开发量：需研究投入

### 社区现成中文方案

| 方案 | 可用程度 | 说明 |
|------|---------|------|
| `ltm920716/zh_PII` | 仅参考 | presidio 中文扩展 · 6 stars · 单 commit |
| `nn0nkey/MingJing` | 参考 + 部分借鉴 | 29+ 中文 PII 类型的 regex 库 · 全栈服务 |
| 自写 PatternRecognizer | **推荐 Level 1** | 50 行代码·正则覆盖手机号/身份证已实测 OK |
| spaCy zh_core_web_sm/trf | **推荐 Level 2** | 解决姓名/地址 NER · 需评估精度 |

---

## tech-gate 12 闸速查表

| 闸 | 项目 | presidio+扩展 | 说明 |
|---|------|-------------|------|
| G1 | 许可证合规 | ✅ MIT | 商业使用无限制 |
| G2 | 活跃维护 | ✅ 持续发版（2026-03-18 最新）| scrubadub ❌ 停滞 2023 |
| G3 | 中文 PII 覆盖（手机号）| ⚠️→✅ 需定制 | 5 行 regex 解决 |
| G4 | 中文 PII 覆盖（身份证）| ⚠️→✅ 需定制 | regex 解决 |
| G5 | 中文 PII 覆盖（姓名）| ⚠️ 需 zh NER | zh_core_web_sm 或 trf |
| G6 | 中文 PII 覆盖（地址）| ⚠️ 需 zh NER | 同上 |
| G7 | persist_policy 三态集成 | ✅ 可编程接入 | 管线层封装 |
| G8 | 性能（probe-a 单机）| ✅ regex 路径极快 | trf 路径需测基准 |
| G9 | 依赖重量 | ✅ 核心 201 kB | +spaCy 模型（sm:12MB/trf:400MB）|
| G10 | 图像 PII（如身份证照片）| ⚠️ 需 presidio-image-redactor | 额外模块 |
| G11 | 流式/batch 支持 | ✅ batch 接口可用 | REST API 可选 |
| G12 | PIPL 人物 OSINT 落库红线 | ✅ 管线层强制 ephemeral | 架构层强制，非库层责任 |

---

## verdict

**档位：A（Guardian·横切全程）**

**理由：**
presidio（MIT · 8.6k stars · 持续维护）作为 probe 脱敏管线的核心框架。

- 正则类 PII（手机号、身份证号）：presidio + 自写 PatternRecognizer，实测开箱即用，共 50 行代码，零外部模型依赖。
- NER 类 PII（姓名、地址）：挂载 `zh_core_web_sm` 解决基础需求；精度要求高时升级 `zh_core_web_trf`（需评估 probe-a 内存约束）。
- scrubadub：排除（维护停滞）。OpenAI Privacy Filter：排除（中文官方降级警告）。GLiNER2-PII：P1 候选（待 zh 支持确认）。

**替换出口（若 presidio 不够）：**
- 姓名 NER 精度不足 → 评估接 GLiNER2-PII（zh 支持确认后）或微调中文 NER 模型
- 合规审计需要 → 接 PostgreSQL Anonymizer（数据落库后 PG 层二次脱敏）

**落矩阵格：Guardian 横切全程**

probe 脱敏管线架构位置：

```
采集层 → [M10 Guardian: presidio 脱敏管线]
            ├── PatternRecognizer(CN_ID_CARD, CN_PHONE_NUMBER)  # Level1 必须
            ├── SpacyNlpEngine(zh_core_web_sm)                  # Level2 推荐
            └── AnonymizerEngine → 替换/掩码/哈希
         → [persist_policy 三态路由]
            ├── normal    → 正常入库
            ├── ephemeral → 不落库，仅内存处理
            └── sensitive → 脱敏后入库/丢弃（人物OSINT → ephemeral）
```

---

## 顺手发现

1. **OpenAI Privacy Filter（2026-04-22）** 值得关注：MoE 架构 50M 活跃参数，可在 laptop 运行，但中文非拉丁字符明确降级——待中文支持改善后可替代 GLiNER。
2. **GLiNER2-PII（arxiv 2605.09973）** 声称多语言 42 类实体，SPY Benchmark 最优，但 zh 语言支持未在公开文档明确 → 值得 1 小时快速验证（`pip install gliner` + 中文文本测试）。
3. presidio 2.2.362 新增 **GLiNER 集成示例**（`microsoft.github.io/presidio/samples/python/gliner/`），两者可叠加使用——如 GLiNER 做 NER，presidio 做编排+匿名化。
4. 实测发现 presidio 英文引擎将中文整段文本误识别为 ORGANIZATION（score 0.85）——生产用 `zh` 引擎时需显式 deny 英文 NER 的误匹配，或设置 `deny_list_score_multiplier`。

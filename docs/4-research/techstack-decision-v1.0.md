# probe 技术栈决策总册 v1.0（R4 产物 · **已拍板 2026-06-11**）

> 日期：2026-06-11 · 拍板：**2026-06-11 元东方确认·冻结为施工依据**
> 上游：[底座裁定卡](techstack-cards/techstack-base-verdict-v1.0.md) + 13 张源卡（M1-M13）+ [研究计划](techstack-github-research-plan-v1.0.md) §五/§九
> 机制：R1 底座对决（3 生成路 + 2 证伪路多数票）+ R2 逐模块源卡（全程 WebFetch 源码级实测）→ R3 组合定案 + R4 总册收口
> 纪律：只汇总不新增调研；各卡数据冲突已标注（见 §三）；档位/落位/出口全程对齐源卡 verdict

---

## 〇 一句话

**底座取「S-借鉴」姿态（保自有 asyncio Scatter-Gather 骨架·拆纯协议·抄思想·拒整机拒重框架）**；13 模块共采纳 **约 28 个件**（A 档直引 + B 档隔离 vendor + C 档借鉴自研），覆盖 G1-G11 全部缺口；**全程零金钱成本**——所有采纳件为开源自托管或本地推理，无任何付费 API / SaaS 订阅（R1 付费红线未触发），唯一外部网络调用为 GDELT/Wikimedia/SavePageNow 等免费官方端点。

---

## 一 底座裁定摘要

三派（S-整机 GPT-Researcher / S-框架 Haystack / S-借鉴）实质收敛于同一终态——「顶层 asyncio Scatter-Gather 冻结自研 + 8闸/ledger/Core IR 护城河自研 + 中段借数据接入」，真分歧只在借多深。**S-借鉴胜出**：S-整机被证伪（custom retriever 不真正关爬+105 依赖背负+冻结冲突），S-框架被证伪（不用 Pipeline 则 @component 退化空装饰器+openai/posthog 毒依赖）。胜出方唯一真浅耦合 vendor 件 = Onyx 连接器协议（MIT 侧），其余四件（MindSearch DAG / STORM 视角 / ODR 状态分层 / GPT-R 字段 schema）抄思想避开依赖背负。执行包 6 条随 OS1 启动（见 §八）。

---

## 二 全栈组合定案表（核心交付）

> 落位列：L1 接入 / L2 采集抽取 / L3 验证 / L4 整合渲染 + Governor 横切 / Guardian 横切。状态：✅可立即引 / ✂️需剪枝/定制 / ⏳S2再议。

| 模块 | 采纳件（版本/license） | 档 | 落位 | 替换出口 | 状态 |
|------|----------------------|----|------|---------|------|
| **底座** | Onyx 连接器协议（MIT·vendor 移植） | vendor | L2 统一接口+Core IR Document | 自研协议 | ✂️~9模块剪枝 |
| **底座** | MindSearch DAG / STORM / ODR / GPT-R（抄思想·不引依赖） | 参考 | G1 DAG schema / 七段报告 / 聚合器三态 | — | ✅ |
| **M1 连接器** | Wikipedia-API 0.15.0（MIT） | A | L1·LoadConnector | pywikibot | ✅ raw_content全文 |
| **M1 连接器** | RSSHub（AGPL·官方镜像自托管·仅A/B级路由） | A | L1·PollConnector | 直连官方RSS | ✅ BLOCK_LIST 屏 C 级 |
| **M1 连接器** | feedparser（BSD-2）/ SearXNG（AGPL·URL发现层） | A/底座 | L1 解析 / URL发现 | — | ✅ |
| **M1 连接器** | gdeltdoc 1.12.0（MIT·近3月·国际新闻） | S3备 | L1·PollConnector | httpx 直连 GDELT | ⏳ 维护偏低 |
| **M2 抽取** | docling 2.101.0（MIT·ONNX无强制torch） | A | L2·内容抽取器（markitdown 深抽取升级） | 表格回 markitdown | ✅ |
| **M2 抽取** | MinerU 3.2.3（自定义license·强制torch+20GB） | B | L2·中文扫描专项子管线（容器化REST） | docling+RapidOCR | ⏳ 对外产品化需复查 license |
| **M2 抽取** | unstructured（Apache·借鉴 partition 接口） | C | — | docling | ✅ 不引依赖 |
| **M3 事实核查** | MiniCheck-Flan-T5-Large 770M（Apache） | A | L3·闸2忠实度（英文） | AlignScore | ✅ 本地推理 |
| **M3 事实核查** | cross-encoder/nli-deberta-v3-large（MIT） | A | L3·闸5矛盾检测（英文） | Erlangshen | ✅ |
| **M3 事实核查** | Erlangshen-Roberta-110M-NLI（Apache） | A | L3·闸2/闸5（中文） | chinese-roberta-large-NLI | ✅ |
| **M3 事实核查** | Loki Decomposer（抽 prompt 模板·非整移） | B | L3·claim拆解前置×litellm | spaCy zh 句分割 | ✅ |
| **M4 AIGC检测** | Fast-DetectGPT（MIT·Qwen backbone） | B+ | L3·闸3 L1统计层（ufo GPU） | — | ✅ 0训练成本 |
| **M4 AIGC检测** | Binoculars（BSD-3·Falcon-7B×2·仅英文） | B+ | L3·闸3 L2精确层（ufo GPU·32GB） | INT4量化 | ✅ |
| **M4 AIGC检测** | Qwen2.5-7B LoRA on DetectRL-ZH（中文95.94%） | B+ | L3·闸3 中文精确层（ufo GPU） | EnsemJudge子集 | ⏳需1-2天微调 |
| **M5 实体去重** | splink 4.0.16（MIT·DuckDB/PG） | A | L3·OS3实体对齐层 | dedupe | ✅ 锁版本勿冒进v5 |
| **M5 实体去重** | datasketch 1.10.0（MIT·MinHashLSH） | A | L3·OS3内容去重层 | — | ✅ 中文bigram实测 |
| **M5 实体去重** | pgvector（平台已有·语义去重） | A | L3·OS3语义对齐层 | — | ✅ 无新依赖 |
| **M5 实体去重** | 自研 TruthDiscovery 60行（Li et al. CRH变体） | C | L3·OS3真值发现层 | — | ✅ 无成熟维护库 |
| **M6 durable队列** | Hatchet Lite（MIT·PG-only·~512MB） | A | L2·S2 durable编排 | Procrastinate | ⏳S2指标门触发 |
| **M6 durable队列** | Procrastinate 3.8.1（MIT·纯PG·零新服务） | A- | L2·S2 备选 | SAQ | ⏳S2 |
| **M7 限流熔断** | throttled-py 3.3.1（MIT·Token Bucket+Redis） | A | Governor·L2 per-source限流 | pyrate-limiter | ✅ S1内存→S2 Redis |
| **M7 限流熔断** | tenacity 9.1.4（Apache·429退避） | A | Governor·L3 重试 | — | ✅ |
| **M7 限流熔断** | circuitbreaker 2.1.3（BSD-3·熔断） | A- | Governor·L1 源宕开路 | purgatory | ✅ |
| **M8 质量评测** | DeepEval（Apache·pytest原生回归门） | A | Guardian·CI eval harness | promptfoo | ✅ judge走Claude多代理 |
| **M8 质量评测** | promptfoo（MIT·A/B+red team） | B | Guardian·跨模型扫描辅 | — | ✅ ⚠️OpenAI已收购 |
| **M8 质量评测** | Ragas（Apache·RAG指标补充） | B | Guardian·DeepEval自定义metric | — | ✅ |
| **M9 监测雷达** | inscriptis 2.7.1 + difflib（Apache+stdlib·自研diff） | 推荐 | L4·monitor/diff_engine（挂APScheduler） | changedetection.io整机 | ⏳S2·拆思想自研 |
| **M10 PII** | presidio（MIT·8.6k）+ 自写 CN PatternRecognizer | A | Guardian·脱敏管线横切全程 | GLiNER2-PII | ✅ +zh_core_web_sm |
| **M11 渲染** | Playwright 1.60.0（Apache·pdf+图卡截图） | A | L4·渲染核心（共用Chromium pool） | WeasyPrint | ✅ |
| **M11 渲染** | python-pptx 1.0.2（MIT·零C库） | A | L4·PPTX生成 | Marp CLI | ✅ 中文实测 |
| **M11 渲染** | matplotlib 3.10.9（PSF-BSD·静态图表） | A | L4·图表PNG（嵌PDF/PPT） | — | ✅ 禁emoji |
| **M11 渲染** | pyecharts 2.1.0（MIT·交互HTML）/ mermaid.js内嵌 | A | L4·交互图表 / 图示 | mermaid-cli Docker | ✅ |
| **M12 成本可观测** | litellm spend（MIT·已在役·LLM计量真源） | A | Governor·读共享DB不重埋点 | — | ✅ |
| **M12 成本可观测** | OTel FastAPI Instrumentor + OTLP→ufo Jaeger（Apache） | A | Governor·HTTP trace | — | ✅ 零新服务 |
| **M12 成本可观测** | 自研 metering.py（数据源API计量·唯一不可替代） | A | Governor·probe_cost_events PG | — | ✅ |
| **M12 成本可观测** | OpenLLMetry（Apache）/ Phoenix（ELv2内部可用） | B | Governor·LLM trace/eval UI | — | ⏳S2按需 |
| **M13 对象存储** | Garage（AGPL·30MB单二进制·内部私用合规） | A | L4·存证+渲染产物（probe-a本机） | SeaweedFS | ✅ G7定型 |

**否决件清单**：MinIO（2026-04归档死）· OpenMeter/Langfuse（ClickHouse重栈）· imgkit/wkhtmltopdf（上游EOL）· recordlinkage（16月停更）· FacTool/AlignScore（停更）· OpenFactCheck（AGPL+29 stars）· scrubadub（中文零支持+停更）· OpenAI Privacy Filter（中文官方降级）· arq/taskiq/dramatiq（无replay/无PG/LGPL）· huginn/urlwatch（Ruby/无API）· RustFS（Beta不成熟）。

---

## 三 跨卡协同与冲突清单

### 协同点（实测各卡 verdict 间复用）

| # | 协同 | 涉及卡 | 说明 |
|---|------|--------|------|
| 协1 | **Playwright Chromium pool 三处共用** | M11(pdf+图卡) · M9(存证截图) · M13(probe-evidence入库) | 单一 asyncio worker pool（≤2 Chromium 进程）同时供 PDF 生成 / 图卡截图 / 网页存证快照，省重复启动 |
| 协2 | **ufo GPU 节点三模型共址** | M3(NLI) · M4(AIGC) · M5(embedding) | M3 NLI + M4 Fast-DetectGPT/Binoculars + M5 text2vec embedding 全部落 ufo GPU（probe-a 禁GPU·T红线）；probe-a 经 Tailscale 100.64.0.8 内网调 |
| 协3 | **litellm 调用链贯穿 judge+拆解** | M8(judge) · M3(Loki拆解) · M12(计量) | M8 DeepEval judge 与 M3 claim 拆解都走 ufo2 litellm `bl-*` 别名；M12 直接读 litellm spend DB 做 LLM 面计量，三卡共用一条 LLM 通道 |
| 协4 | **Redis 总线多用途复用** | M7(token-bucket) · M4(content hash缓存) · M5(MinHashLSH backend) | probe-a 已有 Redis（机6限流总线）同时承载限流 / AIGC 结果缓存 / MinHash 跨进程状态，不起第二 Redis |
| 协5 | **PG 单库多模块落表** | M5(splink PG) · M6(Hatchet/Procrastinate PG) · M12(cost_events) · M9(change_events) | 全部复用 probe-a 本机 PG，零新存储；M6 选 PG-only 队列正是为此 |
| 协6 | **OTel→ufo Jaeger 既有中枢** | M12 · M8 | trace 推机3 ufo 既有 Jaeger+Grafana+Prometheus，零新观测服务 |
| 协7 | **inscriptis 是 changedetection.io diff 真源** | M9 | 直接用 inscriptis+difflib 等价获得整机 diff 质量，绕开 Flask 孤岛 |
| 协8 | **fonts-noto-cjk 全渲染件共用** | M11 全部 | probe-a 部署首步 apt 一次，Playwright/matplotlib/WeasyPrint 共享 |

### 冲突点（4 处·已标注不擅裁）

| # | 冲突 | 涉及卡 | 标注 |
|---|------|--------|------|
| 冲1 | **GPU 算力排布争用** | M4(Binoculars 双Falcon-7B 需32GB VRAM) vs M3(NLI 110M-770M) vs M2(MinerU torch+20GB) | ⚠️ ufo GPU 总 VRAM 未在卡中核实；M4-L2 精确层 32GB 是最大单点，若 ufo VRAM<32GB 则 Binoculars 需 INT4 量化或仅保留 L1。**待 ufo GPU 规格核实后排期**（M4 卡已自标⏳） |
| 冲2 | **raw_content 不变量字段名分歧** | 底座执行包#2 vs M1 实测 | 底座原写「检索器回 {url, raw_content}」，M1 实测 Onyx Document **无 raw_content 字段**，正文落 `TextSection.text`。底座已纳入修正（执行包#2 改为「Document.sections[].text 必非空」），**两卡已对齐**，非未决冲突，登记备查 |
| 冲3 | **Phoenix license 判定两卡口径** | M8(标 ELv2 需法务确认·优先级低) vs M12(标 ELv2 内部自托管完全许可) | ⚠️ M8 偏保守、M12 引官方「self-hosting fully permitted」明文判内部可用。**取 M12 口径**（更新·有官方出处），但若 probe 未来对外提供观测即服务则触发限制——此边界两卡一致，仅 P0 内部用判定上 M12 更明确 |
| 冲4 | **promptfoo OpenAI 收购的长期中立性** | M8 | ⚠️ 非卡间冲突，单卡自标风险：2026-03 OpenAI 收购 promptfoo，MIT 短期不变但 Claude 支持长期存疑。M8 已将其降为 B 档辅助、DeepEval 为主，风险已隔离 |

**冲突总数：4 处**（其中冲2/冲3 实为已对齐的口径统一，真未决仅冲1 GPU 排布 + 冲4 长期风险监控）。

---

## 四 依赖总账

### A 档 pip 依赖清单（分组）

**核心轻量（probe-a 本机·CPU）**：
```
# 连接器/抽取
Wikipedia-API  feedparser  gdeltdoc  docling  markitdown(已有)  trafilatura(已有)  magika(已有)
# 实体去重
splink==4.0.16  sqlalchemy  psycopg2-binary  datasketch  pgvector
# 限流/队列/重试
throttled-py[redis]  tenacity  circuitbreaker
# 评测
deepeval  promptfoo(Node)  ragas
# PII
presidio-analyzer  presidio-anonymizer
# 监测
inscriptis  (difflib=stdlib)
# 渲染（部分）
python-pptx  matplotlib  pyecharts
# 可观测
opentelemetry-instrumentation-fastapi  opentelemetry-exporter-otlp-proto-grpc  opentelemetry-sdk
litellm(已在役·ufo2)
```

**模型类（落 ufo GPU·非 probe-a）**：
```
# 事实核查 NLI（本地推理）
minicheck(Flan-T5-Large 770M)  sentence-transformers(deberta-v3-nli)  transformers(Erlangshen-110M)
# AIGC 检测
fast-detect-gpt(Qwen2.5-7B backbone)  binoculars(Falcon-7B×2)  peft(Qwen2.5-7B LoRA·中文)
# embedding
text2vec-base-chinese  或 ufo2 litellm bl-embed 别名
```

**渲染类（含系统级依赖）**：
```
playwright==1.60.0    → playwright install chromium --with-deps（~350MB Chromium）
```

### 系统级依赖（apt·probe-a）
- `fonts-noto-cjk fonts-noto-cjk-extra`（~100MB·所有渲染件共用·部署第一步）
- Chromium OS 依赖（随 playwright install --with-deps 自动）
- WeasyPrint（仅备选）需 `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0`
- Garage 单二进制（~30MB·无外部依赖）

### 承载分布

| 节点 | 承载 |
|------|------|
| **probe-a（4C8G·CPU·禁GPU）** | 全部连接器 / docling 抽取 / splink+datasketch+pgvector 去重 / throttled+tenacity+circuitbreaker 限流 / presidio 脱敏 / inscriptis 监测 / Playwright+python-pptx+matplotlib 渲染 / Garage 对象存储 / OTel SDK / metering.py / Hatchet/Procrastinate(S2) / Redis+PG 本机 |
| **ufo（GPU 算力机）** | M3 NLI 模型 / M4 AIGC 检测模型（Fast-DetectGPT/Binoculars/中文LoRA）/ M5 embedding / MinerU 容器（M2 中文扫描专项·条件触发）/ 既有 Jaeger+Grafana+Prometheus（接 OTel trace） |
| **ufo2（共用平台）** | litellm proxy（`bl-*` 别名·M3 拆解 + M8 judge + M12 计量真源共用） |

> 内存峰值估测（probe-a 并发）：Playwright 2 worker ~400MB + matplotlib ~80MB + python-pptx ~50MB + Garage ~1GB + docling ONNX 按需 ≈ 8G 有余量（M11 卡实测结论）。

---

## 五 G1-G11 缺口对账表

| 缺口 | 被哪张卡/采纳件喂 | 状态 |
|------|------------------|------|
| **G1 扇出 DAG schema** | 底座（MindSearch WebSearchGraph node/edge dict 抄成 dataclass）+ M6（执行层 TaskGroup/Hatchet） | 已定型 |
| **G2 scenario 模板** | 纯内部设计·随 S1 施工（不依赖外部调研） | 仍开放（内部项） |
| **G3 SCT/ledger 字段对账** | M1（Onyx 连接器协议反推字段·Document.sections[].text 不变量） | 已定型 |
| **G4 可靠度三表示换算** | M3（MiniCheck raw_prob float 归一化）+ M5（splink match_prob + 自研 TruthDiscovery source_reliability） | 已定型 |
| **G5 partial schema** | 纯内部设计·随 S1（底座抄 ODR raw_notes/compressed_research 状态分层喂聚合器三态） | 部分（思想已喂·schema 待写） |
| **G6 成本门契约** | M7（Token Bucket 熔断退避）+ M12（litellm spend + 自研 metering.py cost_event） | 已定型 |
| **G7 对象存储真源** | M13（Garage 直接定型·bucket 命名+lifecycle 三态映射） | 已定型 |
| **G8 master S1 施工表** | R4 总册（本文件·选型定 → 见 §八施工接力清单） | 部分（本册输出输入清单·施工表待 s1-impl 编） |
| **G9 gate19 补七赛道** | M1（连接器调研顺带·RSSHub 路由三级合规分类喂赛道覆盖） | 部分 |
| **G10 ledger 域 bug** | 纯内部修复项·不依赖外部调研·随 S1 | 仍开放（内部项） |
| **G11 consistency-gate 脚本** | M9（inscriptis+difflib diff 工具借鉴可用于链接/一致性检查） | 部分（工具借鉴·脚本待写） |

---

## 六 补盲汇总（各卡顺手发现收割·有价值列入 backlog）

| 来源 | 发现 | backlog 价值 |
|------|------|------------|
| M1 | Onyx Document 无 raw_content 字段（已并入底座执行包#2修正） | 已处理 |
| M1 | RSSHub AGPL 网络 copyleft：只 pull 官方镜像不 fork 修改即规避传染 | 部署纪律·入 S1 |
| M2 | docling-eval / OmniDocBench 可作 probe 中文文档精度评测集 | M8 评测集扩充候选 |
| M2 | RapidOCR 独立 pip 包·ONNX·中文优于 tesseract | M2 中文 OCR 轻量备选 |
| M3 | spaCy zh_core_web_sm 可作无 LLM 的 claim 句分割 fallback | M3 降级路径 |
| M4 | NLPCC2025 DetectRL-ZH 数据集公开·中文 AIGC 检测最佳 benchmark | M4 微调数据源（已入选型） |
| M4 | Binoculars 可换 Qwen2.5-7B backbone 适配中文（EnsemJudge 实证） | M4 中文增强路径 |
| M5 | 中文公司名 blocking rule：前3-4字符 block + regex 清洗地区词 | M5 实施细节 |
| M5 | datasketch Redis backend 内置·可复用机6 Redis | 已纳入协同4 |
| M6 | Procrastinate PG LISTEN/NOTIFY 高并发(>500 worker)广播风暴 | S3+ 扩展留意 |
| M8 | Phoenix `arize-phoenix-evals` 子包是 Apache（主包 ELv2） | 若只需 eval 引子包·许可更干净 |
| M9 | changedetection.io 整机仅 S3+ 大量自有 HTML 可视化审阅场景保留 | S3+ 辅助工具 |
| M10 | presidio 2.2.362 新增 GLiNER 集成示例·可叠加 | M10 NER 增强候选 |
| M10 | OpenAI Privacy Filter MoE 50M 活跃参数·中文改善后可替 GLiNER | P1 跟踪 |
| M11 | mermaid-cli Docker 唯一开箱内置 font-noto-cjk | 若选 mermaid-cli 路径省字体配置 |
| M11 | pyecharts PNG 走 Playwright 截图绕开 Selenium 生态分裂 | M11 实施纪律 |
| M12 | litellm 已有 6 张 DailyXxxSpend 聚合表·注入 request_tags 零改本体得 per-source 日汇总 | M12 减 ETL 工作量 |
| M13 | RustFS（Apache·26.5k·Beta）6 月后成熟可替 SeaweedFS 第二备选 | M13 长期跟踪 |
| M13 | SavePageNow→Playwright PDF→Garage→60天 lifecycle 完整存证链无第三方依赖 | M13 存证链 |

---

## 七 安全与许可总核

### AGPL 件清单与隔离方式（3 件·全内部私用合规）

| 件 | 模块 | 隔离方式 |
|----|------|---------|
| **Garage** | M13 对象存储 | probe-a 私有基础设施·仅 probe 内部读写·不对外 SaaS → 不触发 AGPL 网络开放义务（M13 顺手发现#3 已留备注） |
| **RSSHub** | M1 连接器 | 只 pull 官方 Docker 镜像·不 fork 修改代码 → 规避传染（M1 顺手发现#2） |
| **SearXNG** | M1 URL发现 | 同 RSSHub·自托管官方镜像不改 |

### 遥测/许可风险类

- **posthog**（Haystack 必装）：已在底座 S-框架证伪中拒绝（采集系统负资产）
- **promptfoo**：OpenAI 2026-03 收购·已降 B 档辅助·DeepEval 为主隔离
- **OpenLLMetry**：Dynatrace 2026-03 收购·维持 Apache·S2 引入需季度健康检查 cron
- **Phoenix（ELv2）**：内部自托管官方明文许可·对外服务触发限制·取 M12 口径

### License 分布统计（约 28 采纳件）

| License | 件数 | 代表 |
|---------|------|------|
| MIT | ~13 | Wikipedia-API/docling/splink/datasketch/throttled-py/python-pptx/pyecharts/mermaid/litellm/Hatchet/Procrastinate/promptfoo/feedparser/circuitbreaker(BSD)... |
| Apache-2.0 | ~9 | docling? unstructured(借)/MiniCheck/Erlangshen/tenacity/DeepEval/Ragas/Playwright/inscriptis/OTel/OpenLLMetry |
| BSD（2/3/PSF） | ~4 | feedparser/circuitbreaker/Binoculars/matplotlib |
| AGPL-3.0 | 3 | Garage/RSSHub/SearXNG（全隔离·内部私用） |
| ELv2 | 1 | Phoenix（内部可用·S2） |
| 自定义/待确认 | 2 | MinerU(月活/收入阈值条款)/EnsemJudge(参考) |

> 无 GPL-3.0 传染件入选（truthdiscovery GPL 已明确弃用·改自研 60 行）。MinerU 自定义 license 仅内部用低风险·对外产品化前须复查。

---

## 八 S1 施工接力（给 s1-impl-plan 的输入清单·按依赖顺序）

### 执行包 6 条（底座·随 OS1 启动）
1. vendor Onyx 连接器协议（~9 模块剪枝移植）→ L2 统一接口
2. raw_content 零爬不变量（Document.sections[].text 必非空·写入 ledger 接入契约）
3. 抄 MindSearch DAG schema → G1 扇出
4. 抄 STORM 视角引导提问 → 七段报告
5. 抄 ODR 状态分层 → 聚合器三态+partial
6. 参考 GPT-R provider 映射与产物 schema → 聚合器输出 IR

### 各卡「立即可装」件（按依赖顺序排）

**第一波·零成本零训练 CPU 件（probe-a·S1 直装）**：
```
apt: fonts-noto-cjk fonts-noto-cjk-extra          ← 渲染前置（最先）
pip: Wikipedia-API feedparser gdeltdoc            ← M1 连接器
pip: docling                                       ← M2 抽取
pip: splink==4.0.16 sqlalchemy psycopg2-binary datasketch pgvector  ← M5 去重
pip: throttled-py[redis] tenacity circuitbreaker  ← M7 限流（S1 内存 backend）
pip: presidio-analyzer presidio-anonymizer + zh_core_web_sm  ← M10 脱敏（红线·先于采集）
pip: inscriptis                                    ← M9 监测
pip: python-pptx matplotlib pyecharts              ← M11 渲染（部分）
playwright install chromium --with-deps            ← M11 渲染核心
pip: opentelemetry-* (3包)                         ← M12 trace
pip: deepeval                                      ← M8 评测
自研: TruthDiscovery 60行 / metering.py            ← M5/M12
Garage 单二进制部署 + bucket 初始化                ← M13 对象存储
```

**第二波·GPU 模型（ufo·S1 可并行下载）**：
```
M3: minicheck(Flan-T5-Large) + deberta-v3-nli + Erlangshen-110M  ← 本地 NLI
M4: fast-detect-gpt(Qwen2.5-7B) + binoculars(Falcon-7B×2)        ← AIGC L1/L2
M5: text2vec-base-chinese 或 ufo2 bl-embed 别名                   ← embedding
```

**第三波·条件触发（指标门/微调·S1 后）**：
```
M4: Qwen2.5-7B LoRA on DetectRL-ZH    ← ⏳需1-2天微调（中文精确层）
M2: MinerU 容器化 REST                 ← ⏳中文重度扫描专项触发
M6: Hatchet Lite / Procrastinate       ← ⏳S2 指标门（5条任3触发）
M12: OpenLLMetry / Phoenix             ← ⏳S2 按需
```

> 红线纪律：M10 presidio 脱敏管线必须先于采集代码上线（probe-a T 红线·PIPL）；M1 RSSHub 自托管须配 BLOCK_LIST 屏蔽 C 级逆向路由。

---

## 九 待拍板三项

1. **底座裁定 + 愿景升级**：S-借鉴胜出 + 执行包 6 条；连带研究计划 §一愿景升级三条（工程姿态入宪）
2. **全栈组合定案表**（§二）：约 28 采纳件的档位/落位/替换出口/状态——**组合的标准**最终体现；其中 M2 MinerU 对外产品化 license、冲1 ufo GPU VRAM 排布（Binoculars 32GB 单点）需在排期时核实
3. **S1 施工启动**：执行包 + 第一波 CPU 件并入 s1-impl-plan 升级为全量施工表（缺口 G8）；第二波 GPU 件并行下载；第三波条件触发件留指标门

---

> 落盘：`/Users/metafo/Downloads/metafoclaw/probe/docs/4-research/techstack-decision-v1.0.md`
> 冻结后并入 reconciliation §1 事实表 · 各源卡数据冲突 4 处见 §三（真未决 = 冲1 GPU 排布 + 冲4 长期风险监控）

# probe / 元探 MetaProbe · 引擎深耕规划 v1.0

> 日期：2026-06-14 · 性质：基于 6 路 GitHub 多维调研合成的深耕路线图（扩展性 / 实用性 / 有效性 三轴）
> 调研方式：6 个并发 subagent（提取层 / 可扩展架构 / 验证证伪 / 合规数据源 / 交付竞品 / 编排管线），各自 GitHub + web 调研后合成。
> 铁律承袭：① 不自建爬虫（feasibility-v1 §5 红线真源）② 外环借·内核锻（master-solution v2.1 §一·补）③ 全本地推理 / 零 SaaS 订阅 / 许可证商用友好。

---

## 〇、一句话

probe 已是成熟引擎（双支柱 + 四层 + M1 上线），深耕 = 把**三轴**做穿：
- **扩展性**：加数据源/提取器/赛道 = 改配置不改架构（消灭 ledger.yaml 双源漂移）
- **实用性**：提取层从"文章+文档"扩到"音频/图像/PDF/多模态" + 接入一批**零成本合规**数据源
- **有效性**：把护城河"证伪"从思想落到**断言级核验**（原子分解 → NLI 来源蕴含校验 → 异构对抗）

---

## 一、扩展性轴（架构插件化 · D2）

### 核心病灶：双源漂移
`ledger.yaml`（手维护 17 域）与 Python extractor class **分离维护** = Q6-L45 同构问题（两处独立更新、互不感知 → 不一致）。

### 裁定：Python class 为唯一真源，yaml 降级为 CI 派生产物

借鉴组合（**只取三个轻量范式，拒绝整机**）：
- **yt-dlp** `suitable()` URL 路由 + `_WORKING=False` 停用不删代码
- **Scrapy** 优先级 int 字典（直接对应 probe 多源并发权重）
- **Unstructured** 统一入口 + optional extras 分级安装（`pip install probe[tiktok,weibo]`）

### 落地动作（P0，~1.5 天）
1. `extractors/base.py` 补类级 manifest 字段：`DOMAIN/TRACK/LEDGER_DOMAIN/REQUIRES_AUTH/AUTH_TYPE/VAULT_KEY/RATE_LIMIT_RPS/PROXY_REQUIRED/_WORKING/VERSION/OUTPUT_FIELDS` + 三方法 `suitable()/extract()/health_check()`
2. `extractors/_registry.py`：`autodiscover()`（仅扫仓库内 `probe/extractors/` 一处）+ `export_ledger()`
3. `Makefile`：`gen-ledger` + `validate-ledger`（进 CI 必过门，ledger.yaml 标注"派生产物·禁手改"）
4. pipeline stage 优先级字典化（L1-L4 可插拔，新增 stage 只加字典条目）

**收益**：加一个新源 = 新建子目录 + 填 manifest 字段 + `make gen-ledger`，架构零改动。

### 明确拒绝（反例）
- ❌ Airbyte Docker 化 connector（probe-a 2c4g 会 OOM）
- ❌ LlamaIndex 300+ 独立 pip 包（内部单 repo 版本矩阵爆炸）
- ❌ yt-dlp 多路径文件系统扫描（probe-a 有公网 EIP，任意文件注入风险 → 限扫一处）
- ❌ entry_points 暂不引入（留给未来社区开放，接口先保持向下兼容）

---

## 二、实用性轴（提取层扩展 + 合规供料 · D1 + D4 + D6）

### 2.1 提取层（extractors/ 扩展）

**合规边界铁律**：下载平台视频本身踩红线 ❌；对**用户自有/授权 API 返回**的素材做本地 ASR/OCR 推理 = ✅ 安全（工具无采集行为）。

| 优先级 | 新增 | 工具 | 许可证 | 5GB GPU | 理由 |
|--------|------|------|--------|---------|------|
| **P0** | `document.py` 升级 | **Docling**（IBM）| MIT ✅ | CPU 可跑 | 61k★·格式最全·内置 Whisper ASR（一库解决文档+音频）|
| **P0** | `audio.py` | **faster-whisper** | MIT ✅ | ✅ INT8 large-v3 ~3.5-4GB | 音视频→文字·CTranslate2 快 4× |
| **P0** | `image.py` | **PaddleOCR** | Apache 2.0 ✅ | ✅ <1GB | 截图/图片 OCR + 版面分析 |
| **P1** | `audio.py` 词级时间戳 | WhisperX | BSD-2 ✅ | ✅ | 溯源引用精度（"第2:34秒说的"）·diarization 关闭 |
| **P1** | `article.py` fallback | readability-lxml | Apache 2.0 ✅ | — | trafilatura 提<200字时兜底·零成本 |
| **P1 谨慎** | `document_cjk.py` | MinerU | ⚠️ 自定义许可 | ⚠️ pipeline≥4GB | 中文 PDF/研报补充·**先读 LICENSE 原文再落** |
| **排除** | — | Marker | ❌ GPL+$2M门槛 | — | 许可证违规 |
| **排除** | — | Surya | ❌ 模型营收门槛+竞争禁止 | — | 法律风险 |
| **排除** | — | insanely-fast-whisper | — | ❌ 需 FlashAttn-2 | 5GB 不达标 |

> 一条优化：Docling 已内置 Whisper，`audio.py` 可先走 Docling 后端，`faster-whisper` 仅在需精细量化/批处理控制时旁路引入，减依赖。

### 2.2 合规数据源（ledger.yaml 扩源 · 全部供应商担责型）

**立即可接（免费·合规无争议·无需 R1）**——覆盖新闻/科技/AI/金融四赛道：

| 优先级 | 源 | 覆盖 | 额度 |
|--------|------|------|------|
| 1 | **GDELT DOC 2.0** | 全球新闻/舆情/实体图谱 | 零注册·15分钟实时·无限 |
| 2 | **Finnhub** | 股票/外汇/加密/基本面/新闻情绪 | 60次/分·永久免费（金融赛道 F 首选）|
| 3 | **YouTube Data API v3** | 视频/频道/搜索/趋势 | 10k单位/天·Google官方（唯一开放可查任意公开内容的主流平台）|
| 4 | **Product Hunt API v2** | AI工具/新品发布 | 注册即用（AI 优惠赛道 I 差异化）|
| 5 | **Hacker News API** | 科技/AI 实时讨论 | Firebase官方·无限免费 |
| +补 | Wikipedia/Wikidata·RSS/Atom·Semantic Scholar·The Guardian·Alpha Vantage | 知识/媒体/学术 | 全免费授权 |

> ledger.yaml 新增片段已由 D4 调研给出（带 `compliance/supplier_liability/cost_tier` 字段），可直接套用。

**国内平台硬结论（2026 未变且收紧）**：抖音/小红书/微博/B站 官方 API **均不支持"任意链接情报"**（仅给自有账号）。

**TikHub 风险缓释（已接·不弃用·立即可做·无需 R1）**：属"用户担责型代爬"。在合规文档明确"仅处理公开非个人数据·不存EU居民个人信息"，ledger 标注 `supplier_liability: false, risk_level: medium`。

**付费源待 R1 元东方确认**：X/Twitter API（~$200-500/月）、NewsAPI Developer（$449/月）、Alpha Vantage Premium（$50/月起）。**勿擅自接。**

### 2.3 编排管线（pipeline.py 升级 · D6）

**核心判断：Scatter-Gather 用 asyncio 原生即够，不引队列。**

| 步骤 | 目标 | 依赖 |
|------|------|------|
| Step1（现在）| 真实 Scatter-Gather（单源超时隔离·一源挂不拖垮）→ 8闸 → 存PG | 无（asyncio+redis 已有）|
| Step2（上线前）| 全链路可观测 + 熔断 | `opentelemetry-sdk`（OTLP→ufo:4318/Jaeger）+ `aiobreaker`（异步·非 pybreaker）|
| Step3（量上来再评估）| 持久重试 + 内置UI | **Hatchet**（MIT·7.1k·原生asyncio·docker-compose+probe-a现有PG零增量）|

> Step3 触发条件：任务量 ≥50 QPS 或需跨重启 resume，否则 Step1+2 已够。
> 拒绝：Temporal（BSL+需Cassandra/ES·2c4g撑不住）、Airflow/Dagster（批处理框架·用法不符）、LangGraph/CrewAI 整机（升级激进·成本熔断难控）。

---

## 三、有效性轴（护城河深化 · D3 + D5）

### 3.1 验证层：从"思想"落到"断言级核验"

**最关键的认知**：当前 probe 8 闸 + 对抗证伪是**思想就位**，但缺三个工程动作。学术实测背书（arXiv:2605.06635，14 个前沿 LLM）：引用链接可达率 >94%、内容相关 >80%，但**事实准确率仅 24%-77%**（GPT-5 Mini 仅 39%，Claude Opus 4.5 最高 77%）。**链接活 + 内容相关 ≠ 事实正确**——这正是 probe 护城河的学术级背书，建议引进对外文案。

| 优先级 | 动作 | 借鉴 | 受益闸 |
|--------|------|------|--------|
| **P0** | 断言**原子分解** + 重要性过滤（低重要性走轻量路径，省核查资源）| Loki（MIT·1.1k）+ SAFE（Apache·DeepMind）| 闸3 |
| **P0** | 每条溯源链接做 **NLI 蕴含校验**（来源文本是否真支撑该断言）| VeriCite / FACTUM | 闸4-5 |
| **P1** | `trace.py` 每步 wrap 为 **Jaeger OTLP span**（8闸推理链可视回放·零新增基础设施）| Jaeger（ufo 已有）| 全闸 |
| **P1** | 对抗证伪 3 Agent 用**异构信源**（官方声明/学术库/时序数据）消除同构共盲 | Tool-MAD 思路 | 闸6 |
| **P2** | 媒体信源 prior 评分（已知机构进 Admiralty 前查白名单）| NELA-GT（学术数据集·非爬虫）| 闸1 |
| **P2** | probe **输出报告嵌 C2PA manifest**（声明"本结论由 probe 基于以下来源生成"）| c2pa-rs（MIT·349★）| 输出凭证 |

**花架子警示（避开）**：
1. **CoT ≠ 可解释性**（Oxford 2025）：让 LLM 解释"为何可信"是事后合理化叙述，非真实推理。`trace.py` 必须记**实际检索步骤**，不能只记 LLM 自报推理文本。
2. **整段一次性验证 = 精度假象**：必须先原子分解，否则 certainty 虚高。
3. **MAD 同构盲点**：多 Agent 用同 LLM+同检索工具 = 系统性共盲，看似多路实则单点失效。
4. FActScore 已停维（2023-10），用活跃分支 OpenFActScore。
5. C2PA 正确用途是**为 probe 自己输出嵌签名**（第三方信源未必有 manifest），非验证输入。

> 与 R-TR（运行层不可信）精神同源：Manus 失败第13/14条正是"伪造证据/虚假核验"——不做独立核验就是卖假安全感。

### 3.2 交付层：七段报告 + 三层深度线 + falsifiable_signals

**全行业空白 = probe 机会**：GPT-Researcher/STORM/Perplexica 全部缺独立事实核验层、反驳/证伪信号、报告级可信度评分。

**七段报告结构（对齐三层深度线）**：

| 段 | 内容 | 层级 | 差异化 |
|----|------|------|--------|
| 1 | 情报摘要（30秒结论）| public | 让用户感受"有货" |
| 2 | 来源溯源清单（数量public·详情paid）| public/paid | — |
| 3 | 核心发现前3段（末段截断）| preview | 制造张力 |
| 4 | **反驳/质疑层 `falsifiable_signals`** | paid | **全行业唯一** |
| 5 | 时间线/演变 | paid | — |
| 6 | 风险与局限（不确定性量化）| paid | — |
| 7 | 决策建议 + PDF 导出 | paid | Perplexity Pages 已回滚·稳定即差异化 |

**付费墙裁定**：probe 按**报告深度**门控（内容价值门），**不按次数**（Perplexity 按使用量门 = AI 烧 GPU 边际成本不趋零，传统 Freemium 在 AI 失效）。截断铁律：preview 第3段末插 CTA，**不在"魔法时刻"前截断**（摘要看完前拦截 = 直接流失）。

**对外 API 范式**（供下游 MetaAsk/MetaLearn/MetaCut/MetaFlow 调用）：返回 `summary/source_count/credibility_score（段落粒度）/preview/full_report/citations[{url,fact_verified,credibility}]/falsifiable_signals`。

**一句话差异化**：> 市面卖"找到来源"，probe 卖"来源经核验、结论可被证伪"。

---

## 四、分阶段路线（叠加在现有 M1/M2/M3 上）

| 阶段 | 主题 | 关键交付 | 依赖 |
|------|------|---------|------|
| **D-Ext（扩展性·~3天）** | 插件化架构 | base.py manifest + autodiscover registry + gen-ledger CI 门 + pipeline stage 字典 | 无外部依赖·纯重构 |
| **D-Use（实用性·~1周）** | 提取层+供料+管线 | Docling/faster-whisper/PaddleOCR 三 extractor + 5 个免费合规源入 ledger + asyncio Scatter-Gather + Jaeger OTLP | GPU 实测显存·源 API key 申请 |
| **D-Eff（有效性·~1-2周）** | 护城河 | 原子分解+NLI 校验（闸3-5）+ 异构对抗（闸6）+ trace span 化 + 七段报告/falsifiable_signals 落地 | LLM 网关（ufo2 LiteLLM）|
| **持续** | 运营期 L6 | 灰度晋升/SLO/效益漂移（对齐 acceptance.md L6）| — |

**优先级建议**：先做 **D-Ext（扩展性）**——它是地基，做完后 D-Use 的"加源/加提取器"才能享受"改配置不改架构"红利；D-Eff 是护城河，价值最高但依赖 LLM 稳定，可与 D-Use 并行。

---

## 五、待元东方拍板项

1. **付费数据源**（X/Twitter ~$200-500/月、NewsAPI $449/月、Alpha Vantage Premium）→ R1 门，未确认不接。
2. **MinerU 许可证**：商用门槛阈值须读 LICENSE 原文确认后才决定是否落 `document_cjk.py`。
3. **TikHub 去留**：当前缓释（补合规声明）vs 长期是否替换（覆盖最广但用户担责型代爬）。
4. **三层深度线定价**：报告深度门控的具体价格点（与平台整体经济模型一体化，归元东方）。
5. **优先级排序**：D-Ext / D-Use / D-Eff 三阶是否按本规划顺序，或调整。

---

## 关联
- 总方案真源：[probe-master-solution-v2.md](../probe-master-solution-v2.md)（§一·补 工程姿态 / §4 审核体系 / §6 合规红线）
- 数据源可行性红线真源：[feasibility-v1](../4-research/probe-github-datasource-feasibility-v1.md) §5
- 审核 8 闸真源：[audit-system-v1](../3-build/probe-audit-system-v1.md)
- 验收方法论：`~/.claude/rules/L1-infra/acceptance.md`（元验五阶 · L3 真实接入 / L6 运营期）
- 已决：[decision_probe_tikhub_keep_paid](../../../../.claude-commerce/projects/-Users-metafo/memory/decision_probe_tikhub_keep_paid_20260613.md)（否决自托管爬虫·保留 TikHub）

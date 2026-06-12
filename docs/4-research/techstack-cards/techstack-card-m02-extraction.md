# 技术源卡 M2 · 内容抽取与规整（增补）

> 模块需求真源：design L2
> 已有件：trafilatura / htmldate / courlan / markitdown / magika ✅
> 本卡评估：unstructured（Unstructured-IO）· docling（IBM/docling-project）· MinerU（opendatalab）[第三候选]
> checked_at: 2026-06-11

---

## 候选实测

### 候选 A · unstructured（Unstructured-IO）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/Unstructured-IO/unstructured |
| **license (SPDX)** | Apache-2.0 ✅ |
| **stars** | 14.9k（checked_at: 2026-06-11） |
| **latest release** | v0.23.0（2026-06-10，checked_at: 2026-06-11） |
| **open issues** | 181（量级：中） |
| **PyPI package** | `unstructured` · 基础包 1.6 MB wheel |
| **依赖重量（核心）** | 基础包：backoff / beautifulsoup4 / lxml / nltk / numpy / requests / unstructured-client 等 ~20 依赖，**无 torch**（基础安装）|
| **依赖重量（全量）** | `unstructured[local-inference]` → 拉入 unstructured-inference → 需要 **torch + torchvision + detectron2**；detectron2 需从源码编译，磁盘占用估计 **3–6 GB**（torch 约 2 GB）；`unstructured[all-docs]` 另需 tesseract-ocr / libreoffice / poppler-utils 系统依赖 |
| **中文支持证据** | 未见官方中文专项声明；OCR 走 tesseract-ocr，需另装 `tesseract-lang` 中文语言包；表格 OCR 精度未见中文基准测试 ⚠️未核实 |
| **hands_on** | `pip install unstructured` 成功（v0.18.32，Python 3.14 venv）；`from unstructured.partition.auto import partition` 导入 ✅；local-inference 额外安装未测（依赖 detectron2 需编译）|
| **checked_at** | 2026-06-11 |

**基准测试摘要（英文文档）：**
- SCORE-Bench（Unstructured 自评）：总体表格得分 0.844，幻觉率最低（Tokens Added 0.027），内容保真度 0.917
- 独立第三方（Procycons）：Unstructured 在复杂表格上准确率 75%，慢于 docling（51–141 s/页 vs docling 6–65 s）
- **注意**：上述基准均为英文文档，无中文测试数据

---

### 候选 B · docling（IBM Research Zurich / LF AI & Data Foundation）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/docling-project/docling |
| **license (SPDX)** | MIT ✅ |
| **stars** | 61.4k（checked_at: 2026-06-11） |
| **latest release** | v2.101.0（2026-06-10，checked_at: 2026-06-11） |
| **open issues** | 862（量级：较多，活跃项目） |
| **PyPI package** | `docling`（meta 包，拉入 `docling-slim`）· `docling-slim` 约 50 MB |
| **依赖重量（核心）** | `docling-slim`：certifi / docling-core / pydantic / requests / tqdm，**无强制 torch**；完整 `docling` 包：`docling-parse`（PDF 原生解析，C++ 后端）+ onnxruntime；layout 和 table 模型走 ONNX，不强制 GPU |
| **依赖重量（可选）** | `docling[vlm]` → 拉入 **torch ≥2.2.2**（VLM 管线，约 2 GB）；`docling[easyocr]` → EasyOCR；`docling[rapidocr]` → RapidOCR（轻量，ONNX 后端）|
| **中文支持证据** | 支持插件式 OCR 后端：EasyOCR（支持 80+ 语言含中文）、RapidOCR（针对中文优化，Baidu PaddleOCR 上游）、Tesseract；Granite-Docling 多语言能力处于「早期实验阶段，尚未验证企业级稳定性」（IBM Research 官方声明）；默认模式（程序化 PDF 无需 OCR）中文表格效果 ⚠️待实测 |
| **hands_on** | `pip install docling` 成功（v2.101.0，Python 3.14 venv）；`from docling.document_converter import DocumentConverter` 导入 ✅；完整转换链路需下载 ONNX 模型（首次运行时自动）|
| **checked_at** | 2026-06-11 |

**基准测试摘要：**
- 独立第三方（Procycons，英文 PDF）：复杂表格单元格准确率 97.9%，结构层次保留最优；处理速度 6–65 s/页（随文档规模线性）
- EasyOCR 集成下：L4 GPU 每页 481 ms OCR，x86 CPU 约 3.1 s，M3 Max 约 1.26 s

---

### 候选 C · MinerU（opendatalab · 上海人工智能实验室）

| 字段 | 值 |
|------|----|
| **repo** | https://github.com/opendatalab/MinerU |
| **license (SPDX)** | MinerU Open Source License（基于 Apache-2.0，含附加条款）⚠️ |
| **license 附加条款** | 月活 >1 亿 或 月收入 >2000 万美元 → 须另购商业授权；在线服务须在产品界面或公开文档中显著声明使用了 MinerU；均满足则自动终止。当前 probe 场景（内部工具·非对外服务）风险低，但需注意日后对外产品化时的合规边界 |
| **stars** | 67.2k（checked_at: 2026-06-11） |
| **latest release** | v3.2.3（2026-06-04，checked_at: 2026-06-11） |
| **open issues** | 6（量级：极少，可能因关闭速度快） |
| **PyPI package** | `mineru` · wheel 约 1.6 MB（模型权重运行时下载） |
| **依赖重量（核心）** | **强制 torch ≥2.8**（必须）+ vLLM（可选加速）+ PaddleOCR + Ray + FastAPI + Gradio；最小磁盘 **20 GB SSD**（含模型权重） |
| **中文支持证据** | 109 语言 OCR 识别（PaddleOCR，百度出品，中文支持强）；OmniDocBench v1.5 得分 86.2（state-of-the-art）；**已知弱点**：中英混排场景准确率低于纯英文（PaddleOCR 模型特性），MinerU 2.x 和 Marker 均存在此问题 |
| **hands_on** | ⏳待本地实测（torch ≥2.8 + 20 GB 磁盘要求，超出 3 分钟快测预算，跳过） |
| **checked_at** | 2026-06-11 |

**基准测试摘要：**
- OmniDocBench v1.5：pipeline 后端 86.2 分（VLM MinerU3.x，state-of-the-art）
- 表格：TableMaster + StructEqTable 双模型融合，跨页表格合并已支持（v3.x）
- 主要竞争优势：中文文档整体效果、PDF 扫描件抗性、公式识别（LaTeX）

---

## tech-gate 12 闸速查表

> T = tech-gate 闸；✅ 过 / 🟡 有条件过 / ❌ 不过 / ⏳ 待验

| 闸 | 名称 | unstructured | docling | MinerU |
|----|------|:------------:|:-------:|:------:|
| T1 | 许可证合规（商用）| ✅ Apache-2.0 | ✅ MIT | 🟡 自定义（内部用低风险·对外需核查） |
| T2 | 依赖可控（无隐性 GPL/AGPL）| ✅ | ✅ | 🟡 需核查 vLLM/Ray 子依赖 |
| T3 | 安装不破 probe .venv | 🟡 基础包 ✅·local-inference 需 detectron2 编译 | ✅ 基础包无 torch·ONNX 模式 | ❌ 强制 torch + 20 GB 磁盘·破坏轻量性 |
| T4 | Python 版本兼容（3.10+）| ✅ ≥3.11 | ✅ ≥3.10 | ✅ 3.10–3.13 |
| T5 | 无强制网络调用（离线可跑）| 🟡 API 模式需联网·本地模式可离线 | ✅ ONNX 模型本地；首次需下载 | 🟡 模型下载后可离线 |
| T6 | 中文文档支持（有证据）| 🟡 tesseract-lang 需额外安装·无中文专项测试 | 🟡 RapidOCR 插件支持·Granite 多语言实验阶段 | ✅ PaddleOCR·109 语言·已知中英混排弱点 |
| T7 | PDF 复杂表格抽取 | 🟡 复杂表格 75% 准确率（第三方基准） | ✅ 97.9% 单元格准确率（复杂表格） | ✅ TableMaster 双模型·跨页合并 |
| T8 | 扫描件 / 图像 PDF | 🟡 需 tesseract + detectron2（重） | ✅ EasyOCR/RapidOCR 插件（可选重） | ✅ 原生 OCR + VLM 双引擎 |
| T9 | 维护活跃度（近 3 个月有提交）| ✅ v0.23.0 发布 2026-06-10 | ✅ v2.101.0 发布 2026-06-10 | ✅ v3.2.3 发布 2026-06-04 |
| T10 | 依赖重量可接受（不强制大模型）| 🟡 基础包轻·全量重 | ✅ 基础包不带 torch·按需可选 | ❌ 强制 torch + 20 GB |
| T11 | 社区规模与健康 | 🟡 14.9k stars·181 issues（中量） | ✅ 61.4k stars·LF AI & Data 孵化 | ✅ 67.2k stars·活跃 |
| T12 | 与已有件无功能冲突 | 🟡 与 trafilatura HTML 抽取有重叠·分工可划清 | ✅ 专注 PDF/Office·与 trafilatura HTML 互补 | ✅ 专注 PDF/Office 扫描件·互补 |

**闸汇总：**

| 候选 | ✅ | 🟡 | ❌ |
|------|----|----|----|
| unstructured | 5 | 6 | 0 |
| docling | 9 | 3 | 0 |
| MinerU | 6 | 3 | 3 |

---

## 对比结论

### 已有件负责范围

| 已有件 | 职责 |
|--------|------|
| `trafilatura` | 网页 HTML 正文抽取·去广告导航 |
| `htmldate` | 文档发布日期推断 |
| `courlan` | URL 过滤/规范化 |
| `markitdown` | Office/PDF 轻量转 Markdown（无 OCR·程序化 PDF） |
| `magika` | 文件类型检测 |

### 已有件弱项（本卡要填补）

1. **PDF 表格深抽取**：markitdown 无表格结构感知，复杂多列/跨页表格会打平
2. **扫描件 / 图像 PDF**：已有件无 OCR 管线
3. **复杂版式**（双栏学术 PDF、中文年报、财报）：markitdown 版式盲
4. **中文文档效果**：trafilatura/markitdown 中文内容无专项优化

### 增补件分工

| 场景 | 推荐件 | 理由 |
|------|--------|------|
| 程序化 PDF（有文字层）表格+版式 | **docling**（基础 ONNX 模式） | 97.9% 表格准确率·无强制 torch·MIT 许可 |
| 扫描 PDF / 图像 PDF | **docling + RapidOCR** | RapidOCR 轻量·ONNX·中文支持优于 EasyOCR CPU |
| 重度中文扫描年报 / 财报 | MinerU（条件引入） | PaddleOCR 中文强但需 20 GB 磁盘，仅在专项管线按需隔离跑 |
| HTML 网页正文 | 继续 trafilatura（不变） | 已测通·轻量 |
| 文件格式嗅探 | 继续 magika（不变） | 无重叠 |

### 重叠处裁定

- `unstructured` vs `trafilatura`：HTML 抽取重叠，trafilatura 更轻量专一，unstructured 全能但重，**裁定：不引 unstructured 做 HTML 抽取**
- `docling` vs `markitdown`：markitdown 作为快速通道（无版式要求时），docling 作为深抽取通道（表格/扫描要求时），**两者共存·按文档复杂度路由**

---

## verdict

### unstructured

**档位：C · 借鉴（不引入依赖）**

- 理由：基础包虽轻，但 PDF 表格全量能力须 `local-inference` → detectron2 编译复杂 + torch；独立第三方基准表格仅 75% 且极慢（51–141 s/页）；与 docling 相比性价比低；中文无保障
- 借鉴价值：其 `partition()` 统一接口设计模式可参考·其 SCORE-Bench 评估框架可用作 probe 自测基准
- 替换出口：表格场景用 docling 替代；HTML 场景 trafilatura 已覆盖

### docling

**档位：A · 引依赖（推荐引入）**

- 理由：MIT 许可·61.4k stars·IBM Research + LF AI & Data 背书·独立基准表格 97.9%·基础安装无强制 torch（ONNX 后端）·Python ≥3.10·装+import 实测 ✅·维护极活跃（2026-06-10 发版）
- 落 L×四引擎矩阵：**L2 采集层 × 内容抽取器（Content Extractor）**；作为 markitdown 的深抽取升级通道，按路由条件触发（有表格结构 or 复杂版式 or 扫描件）
- 替换出口：不替换 markitdown（保留快速通道），在 L2 内新增 `docling_extractor.py` 路由层，复杂 PDF → docling，简单 HTML/纯文字 → 已有件

### MinerU

**档位：B · vendor（隔离集成·条件触发）**

- 理由：67.2k stars·中文扫描件最强（PaddleOCR 出身）·跨页表格已支持；但强制 torch + 20 GB 磁盘破坏轻量性；许可证附加条款需注意对外产品化时的合规边界；安装未实测（⏳）
- 使用方式：独立 Docker 容器或独立进程，通过 REST API 调用（MinerU 自带 FastAPI server）；不与主 .venv 混装；仅在「重度中文扫描 PDF / 复杂年报财报」专项管线按需调用
- 落 L×四引擎矩阵：**L2 采集层 × 中文文档专项子管线（可选·容器化）**

---

## 顺手发现（adjacent 能力登记）

1. **docling-serve**（PyPI）：docling 的 HTTP API 包装，可一键起 REST server，probe 如需多进程共享 docling 可直接用
2. **docling-eval**（PyPI）：官方基准评估框架，可用于 probe 自建中文文档测试集的精度评测
3. **MinerU FastAPI server 模式**：MinerU 自带 `mineru-api` 启动命令，天然支持容器化 vendor 集成
4. **unstructured SCORE-Bench**（https://unstructured.io/blog/introducing-score-bench-an-open-benchmark-for-document-parsing）：开放评估框架，包含 Text/Table/Element 三维指标，可作为 probe 内容抽取质量门的参考设计
5. **Granite-Docling（IBM，2026）**：docling 的 VLM 增强版，端到端文档理解（含图表理解），实验阶段但值得跟踪；多语言路线图已在推进
6. **RapidOCR**（docling 插件）：独立 PyPI 包，ONNX 后端，CPU 友好，可单独引入作为中文 OCR 轻量备选，优于 tesseract 中文效果，劣于 PaddleOCR GPU 模式
7. **OmniDocBench**（opendatalab，2024-12）：覆盖中英双语混合 PDF 的综合基准，MinerU 主导但已开源，probe 中文文档精度评测可复用该数据集

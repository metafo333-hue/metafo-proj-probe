# probe · 交付形态生成管线设计 v1.0

> **日期**：2026-06-10
> **性质**：设计方案（管线架构·M1 可落码）
> **真源边界**：形态矩阵定义仍引 [design-v1](probe-intelligence-engine-design-v1.md) §5.5；
> 七段报告结构真源在 `app/services/report.py`；
> 渲染入口真源在 `app/services/deliverable.py`（已有 text/markdown/html 真实实现·image/ppt/video 为 stub）；
> 数据落点真源在 [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md)（`probe_conclusion` / `probe_artifact`）；
> 本文**补缺口 #6**：design-v1 §5.5 有矩阵没有管线，本文做「怎么生成每种形态」的落地设计。
> **约束遵从**：R-H5 H5-First（HTML 响应式） · R27（视频/>10M 不入仓·走 video-index 映射） · server-roles T1/T2（probe = 非交易共用业务，部署在 ufo2）· spec-engine 品牌大脑复用（不另起视觉系统）

---

## 〇、一句话 + 已定决策

**同一份 L4 验证后的情报内核（`probe_conclusion`），由统一渲染管线按形态分路输出；内核只算一次，换形态只重渲染，不重采集、不重审核。**

| # | 已定决策 | 依据 |
|---|---------|------|
| D1 | **情报内核中间表示（Core IR）**= `conclusion_block` + `seven_section`(s1-s7) + `conclusion_label`(三标签)，所有渲染器从同一 IR 出发，不各自解析原始数据 | 消除形态间数据不一致；C-8 保证（渲染层不接触第三方原始 JSON） |
| D2 | **M1 先上三形态**：text / markdown（速览卡）/ HTML（响应式报告）；image / PPT / video 标为后期（P 阶段） | M1 优先可用·成本可控·已有代码基础 |
| D3 | **护城河必须可见**：每种形态必须呈现三标签（置信/证据等级/Admiralty）+ 溯源域；极速版必须水印"⚡ 未全验·重大决策请用深度版"，任何形态禁止静默降级不标注 | [speed-tiering](probe-speed-depth-tiering-v1.0.md) §三铁律 + design-v1 §5.5 |
| D4 | HTML / 图形态复用 metafoclaw 破晓品牌 tokens-brand.css + spec-engine，不另建视觉系统 | 品牌一致性；spec-engine 已落地 |
| D5 | 交付物大块（图/HTML 文件/>10K / PPT / 视频）存对象存储或临时盘，PG 的 `probe_artifact.uri` 只存引用 | [数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) §2.5 · R27 |
| D6 | 渲染结果按 `conclusion_id + fmt + depth_tier + brand_version` 缓存；同一内核换形态不重跑 L2-L4 | 成本控制·体验提速 |
| D7 | 形态选择路由由 MetaAsk 在意图澄清时确定，接入母体声明式管线（`/api/v1/invoke`）；形态 token 成本单独计入计费轴②（不混入数据成本轴①） | [cost-metering](probe-cost-metering-design-v1.0.md) · design-v1 §5.5 |

---

## 一、统一内核 → 多形态架构

### 1.1 情报内核中间表示（Core IR）

```
Core IR = {
  conclusion_block : dict     # GEO/对外结论（顶层判断·headline·decision_tip）
  seven_section    : {
    s1_first_screen     : ...  # ① 首屏速判·评级 A/B/C/D + 15s 拍板
    s2_fact_check       : ...  # ② 真相核查·D1·overall_credibility + claims
    s3_content_breakdown: ...  # ③ 内容拆解·结构公式·钩子·复用标签
    s4_competitor_matrix: ...  # ④ 竞品横评（paid only）
    s5_recreation_paths : ...  # ⑤ 二创方案（三层深度线裁剪）
    s6_risk_compliance  : ...  # ⑥ 风险合规·D8
    s7_full_detail      : ...  # ⑦ 完整明细（dimensions_summary 已加工摘要）
  }
  conclusion_label : {
    confidence_level    : High / Moderate / Low        # 置信度
    evidence_grade      : （s2 overall_credibility 映射）# 证据等级
    source_reliability  : A-F （Admiralty 双轴·源可靠性）
    info_credibility    : 1-6 （Admiralty 双轴·信息可信度）
    depth_tier          : flash / deep                 # 档位水印
    incomplete          : bool                         # 超预算截断标志
    source_domains      : list[str]                    # 溯源域列表
  }
}
```

**这是唯一输入**：所有渲染器只接收 Core IR（已经 `guards.redact_by_tier` 按深度线裁剪），不回溯 L2/L3 原始数据。真源在 `app/services/report.py`（数据类定义）+ `app/services/deliverable.py`（渲染入口）。

### 1.2 管线全图

```
  L2 采集扇出
       │
  L3 双审 8 闸 + 对抗证伪
       │
  L4 整合 → build_seven_section_report()
       │
  ┌────▼─────────────────────────────────────────────────────────┐
  │  情报内核（Core IR）                                          │
  │  probe_conclusion { conclusion_block, seven_section,         │
  │                      conclusion_label }  ← PG 持久化         │
  └────┬──────────┬──────────┬─────────┬──────────┬─────────────┘
       │          │          │         │          │
  ┌────▼──┐  ┌───▼────┐ ┌───▼────┐ ┌──▼────┐ ┌──▼──────┐
  │ text  │  │markdown│ │  html  │ │ image │ │ppt/video│
  │渲染器 │  │渲染器  │ │渲染器  │ │渲染器 │ │ stub    │
  │(M1✅) │  │(M1✅)  │ │(M1✅)  │ │(P1⚠️) │ │ (P2⚠️) │
  └───────┘  └────────┘ └───────┘ └───────┘ └─────────┘
       │          │          │         │          │
       └──────────┴──────────┴────┬────┴──────────┘
                                  │
                       probe_artifact { format, uri, bytes, expires_at }
                       大块 → 对象存储/临时盘；PG 只留 uri (R27)
```

**原则**：内核往下是单向渲染，渲染器之间不互调，每个渲染器对 Core IR 是只读访问。

---

## 二、逐形态生成方案

### 2.1 文字形态（text / markdown）— M1 ✅

**定位**：最轻形态·零依赖·极速版速览卡 vs 深度版完整七段。

| 维度 | 极速版（flash）速览卡 | 深度版（deep）完整七段 |
|------|---------------------|---------------------|
| **渲染内容** | s1（评级+headline+拍板+行动）+ conclusion_label 三标签 + 溯源域 + ⚡水印 | s1-s7 全段 + 三标签 + 溯源域 + 深度版标识 |
| **字数估算** | ≤200 字 | 800-2000 字 |
| **token 渲染成本** | < 200 tok（模板填充） | < 500 tok（结构化输出） |
| **水印/标注** | `⚡ 极速版·轻验·重大决策请用深度版` 必须在首行 | `🔬 深度分析版·已全验·可溯源可证伪` 标识在首行 |
| **溯源呈现** | 末行：`来源：${source_domains.join(' · ')}` | 每段下方内联溯源；s7 完整 source_hint |
| **三标签呈现** | `[置信:${confidence_level}] [Admiralty:${source_reliability}-${info_credibility}] [证据:${evidence_grade}]` 一行 | 同上 + s2 claims 逐条 verdict |

**实现**：`deliverable._render_text` / `_render_markdown` 已有基础实现（M1 真实代码）；
M1 补强：① 在所有输出头部注入三标签行 ② 极速版注入水印 ③ 溯源域追加到末尾。

**incomplete 截断处理**：若 `conclusion_label.incomplete == true`，文字头部加：
`⚠️ 本报告因预算限制未完整采集，缺失：${missing_dimensions}，结论仅供参考。`

---

### 2.2 图形态（image）— P1 ⚠️

**定位**：信息图/评级卡·数据可视化·「一图看懂」·SNS 可分享。

#### 2.2.1 子形态矩阵

| 子形态 | 内容来源 | 生成方式 | 用途 |
|--------|---------|---------|------|
| **评级卡**（rating-card） | s1（评级+headline+拍板）+ conclusion_label 三标签 | LLM → SVG 模板渲染 | 速览·SNS 分享 |
| **证据链图**（evidence-chain） | s2（claims_summary·verdict 列表）+ 溯源域 | Mermaid/D3 → PNG/SVG | 核查说明·可信度可视化 |
| **竞品横评图**（competitor-chart） | s4（items·name/score/note） | Chart.js 柱图/雷达图 → PNG | paid 专属·竞品比较 |

#### 2.2.2 生成技术方案

```
Core IR → 图数据提取（extract_image_data.py）
         → 选模板（rating-card / evidence-chain / competitor-chart）
         → SVG 模板 + 品牌 tokens 注入
             ├─ 品牌色：tokens-brand.css 变量提取（--mfc-blue / --mfc-orange 等）
             ├─ 字体：Fredoka + Noto Sans SC（破晓品牌标准）
             └─ 布局：MetaDesign L1 契约 /api/v1/invoke（handoff=MetaDesign）
         → SVG/PNG 产物 → 对象存储 → probe_artifact.uri
```

**图形渲染路径**：
- **M1 阶段**（stub）：`_render_image_stub` 返回 handoff dict，由 MetaDesign 接管；probe 准备好 `payload_hint`（markdown 文本 + brand_anchor）。
- **P1 阶段**（接入）：`extract_image_data(core_ir) → MetaDesign.invoke(payload)` 真实调用；产物写 `probe_artifact`。

**品牌一致性**：图形态**禁止**在 probe 侧硬编码颜色/字体；所有视觉变量由 spec-engine `tokens-brand.css` 提供，MetaDesign 排版时注入。

**三标签/溯源在图中的呈现**：评级卡底部固定一行小字：
`置信度：${confidence_level} | Admiralty ${source_reliability}-${info_credibility} | 来源：${source_domains[0]}等`；
极速版加橙色水印条「⚡ 轻验版」。

---

### 2.3 HTML 形态（html）— M1 ✅

**定位**：自包含响应式页面·H5-First（一套代码手机+桌面）·专业交付·可发 hub·含溯源可展开 + 可信度可视化。

#### 2.3.1 已有基础与 M1 补强

`deliverable._render_html` 已有基础实现（七段 HTML 骨架·内嵌 CSS·评级徽章）。
M1 补强的三项：

| 补强项 | 当前状态 | M1 目标 |
|--------|---------|--------|
| 品牌 tokens | 内嵌简单 CSS | 引入 spec-engine 品牌 CSS 变量（--mfc-blue / --mfc-orange / Fredoka 字体）或内联等效值 |
| 三标签可视化 | 缺失 | 固定顶部「可信度条」：置信度·Admiralty 双轴·极速版/深度版标识 |
| 溯源可展开 | s7.source_hint 存在但无交互 | 每段旁「[查看溯源 ▼]」展开列 source_domains；深度版 s7 可展开 dimensions_summary |

#### 2.3.2 HTML 模板结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <!-- H5-First：mobile-first responsive，禁 hover-only，触摸热区≥44px -->
  <title>probe 情报报告 · ${headline}</title>
  <style>/* spec-engine 品牌 tokens 内联 + 响应式骨架 */</style>
</head>
<body>
  <!-- 可信度条（固定顶部·任何深度档均显示） -->
  <header class="probe-credibility-bar">
    <span class="depth-badge ${depth_tier}">⚡极速版 / 🔬深度版</span>
    <span class="confidence">置信：${confidence_level}</span>
    <span class="admiralty">Admiralty ${source_reliability}-${info_credibility}</span>
    <span class="source-count">源：${source_domains.length} 处</span>
    <!-- 极速版：橙色水印条·禁止隐藏 -->
  </header>

  <!-- ① 首屏速判：评级大徽章 + headline + 拍板 + 行动步骤 -->
  <!-- ② 真相核查：claims 表格 + 各条 verdict 图标 -->
  <!-- ③ 内容拆解（三层深度线·paid unlock） -->
  <!-- ④ 竞品横评（paid only·locked 提示） -->
  <!-- ⑤ 二创方案（三路 / preview 截断） -->
  <!-- ⑥ 风险合规 -->
  <!-- ⑦ 完整明细 + [查看溯源 ▼] 可展开 -->

  <!-- 底部：ICP 备案 蜀ICP备2026010386号-1（若公开可访问·nginx-02 规则） -->
</body>
</html>
```

**自包含**：HTML 文件不依赖外部 CDN（字体 base64 内嵌或 Google Fonts CDN 链接二选一）；
可直接存对象存储 → `probe_artifact.uri` 引用 → 发 hub 或直接发给用户。

**incomplete 截断**：若 `incomplete == true`，可信度条追加橙色「⚠️ 数据不完整」徽章。

---

### 2.4 PPT 形态（ppt）— P2 ⚠️

**定位**：结构化幻灯·汇报/路演·七段映射 7 页核心页 + 1 封面 + 1 尾页。

#### 2.4.1 七段 → 幻灯页映射

| 页 | 来源 | 内容 |
|----|------|------|
| 封面（P0） | conclusion_block | 标题·日期·评级大字·probe 品牌角标 |
| P1 | s1 | ① 首屏速判：评级·headline·拍板·行动步骤 |
| P2 | s2 | ② 真相核查：claims 表·verdict 图标 |
| P3 | s3 | ③ 内容拆解：结构公式可视化 |
| P4 | s4 | ④ 竞品横评：评分雷达图（paid only；免费页占位"付费解锁"） |
| P5 | s5 | ⑤ 二创方案：三路卡片 |
| P6 | s6 | ⑥ 风险合规：风险等级 + 要点 |
| P7 | s7 | ⑦ 完整明细 + 溯源列表 |
| 尾页 | conclusion_label | 三标签全览·可信度说明·极速版水印 |

#### 2.4.2 技术方案

**首选**：`python-pptx`（📐标准实践·无服务依赖·可自托管）→ 生成 `.pptx` → 对象存储 → `probe_artifact`。

```
Core IR → extract_ppt_data(core_ir)
        → pptx_builder.py（python-pptx · 品牌模板 template.pptx）
            ├─ 品牌色/字体从 tokens-brand.css 提取的常量（不走运行时 CSS 解析）
            └─ 竞品横评图：Matplotlib 生成 PNG 嵌入
        → .pptx 文件 → 对象存储 → probe_artifact.uri
```

**备选**：若 HTML→PPT 转换成熟度更高（LibreOffice headless / Playwright 打印），可先产 HTML 再转；但 python-pptx 更稳定可控，优先。

**R27 合规**：.pptx 文件属大块交付物，不入 git 仓；PG 只存 uri；`expires_at` 按隐私留存策略设置。

---

### 2.5 视频形态（video）— P3 ⚠️

**定位**：脚本→配音→画面合成；适配社交平台·短视频·路演录屏。

#### 2.5.1 架构占位（P3）

```
Core IR → 视频脚本生成
  ├─ 脚本来源：s5_recreation_paths（二创方案·借/换/串三路任选一路展开）
  │           + s1 headline/拍板（开场白）
  │           + conclusion_label（片尾可信度声明）
  └─ 格式：分镜脚本 JSON { scene, narration, duration, visual_hint }[]

脚本 → MetaCut（元剪·元剪引擎）L1 契约 /api/v1/invoke
  ├─ payload：分镜脚本 + 原始内容素材引用（s7.source_hint URL 列表）
  ├─ 配音：TTS（P3 接入第三方 TTS 或 MetaCut 内置）
  └─ 画面：素材剪辑 / 字幕 / 字幕动效

产物 → .mp4 → **不入 git 仓（R27）** → 对象存储
      → video-index.md 映射（文件名·对象存储 URI·时长·场景）
      → probe_artifact { format:"video", uri:"oss://...", bytes:..., expires_at:... }
```

**M1 现状**：`_render_video_stub` 已有 handoff dict 占位（`engine:MetaCut`·`contract_endpoint:/api/v1/invoke`）；P3 落地时直接替换 stub 实现，调用 MetaCut 契约。

**video-index 映射格式**（probe 专属）：
```
## probe 视频产物索引
| conclusion_id | scene | 时长 | 对象存储 URI | 生成时间 | 备注 |
```

---

## 三、形态选择路由

### 3.1 路由逻辑

```
MetaAsk 意图澄清完成
  │
  ├─ 用户明确指定形态 → 检查 token 预算 → 直接路由
  │
  └─ 未指定 → 默认路由（见下表）
```

**默认形态表**：

| 档位 | 用户类型 | 默认形态 | 原因 |
|------|---------|---------|------|
| ⚡ 极速版 | 所有 | `markdown`（速览卡） | 轻快·即时可读 |
| 🔬 深度版 | 免费 | `markdown`（完整七段） | 无 premium 形态权限 |
| 🔬 深度版 | 付费按次 | `html`（响应式报告） | 专业交付·可发 hub |
| 🔬 深度版 | 订阅/企业 | `html` 默认·可升 `ppt` / `image` | 高客单·多形态可选 |

### 3.2 形态权限矩阵

| 形态 | public | preview | paid（按次）| 订阅+ |
|------|--------|---------|------------|-------|
| text / markdown（速览卡） | ✅ 速览卡 s1 only | ✅ 完整七段（部分 locked） | ✅ 完整 | ✅ |
| html | ❌ | ✅ 简版（locked 段多） | ✅ 完整 | ✅ |
| image（评级卡） | ✅ 仅评级卡 | ✅ | ✅ | ✅ |
| image（竞品图/证据链图） | ❌ | ❌ | ✅ | ✅ |
| ppt | ❌ | ❌ | ✅（P2 上线后）| ✅ |
| video | ❌ | ❌ | ❌（P3 上线后）| ✅ |

---

## 四、token 预算与成本

### 4.1 各形态渲染 token 估算

| 形态 | 渲染 token 成本（估算） | 说明 |
|------|----------------------|------|
| text（速览卡·极速）| 100-200 tok | 模板填充·无 LLM 调用 |
| markdown（七段·深度）| 300-600 tok | 结构化输出·无 LLM 调用 |
| html（响应式）| 500-1000 tok | HTML 模板渲染·无 LLM 调用 |
| image（评级卡）| 1000-2000 tok | SVG 模板 + MetaDesign 调用 |
| image（竞品图）| 2000-4000 tok | 数据可视化 + MetaDesign 排版 |
| ppt（7-9 页）| 3000-6000 tok | python-pptx 生成 + 竞品图嵌入（P2）|
| video（1-3 分钟）| 8000-20000 tok | TTS + 画面合成（P3）|

**计费联动**（② 输出形态轴）：渲染 token 成本单独入 `probe_metering` 的 `tokens_render` 字段；`billing.py` 报价时叠加 `cost_render`（与数据成本 `cost_data` 分开记）；失败不扣费（现有 billing.py 规则保留）。

### 4.2 超预算降级策略

```
形态选择后·估算渲染 token
  │
  ├─ 预算充足 → 正常渲染
  │
  └─ 超预算（预估 > budget_remaining * 0.8）
        → 自动降级：video → ppt → html → markdown → text
        → 告知用户："形态已降级为 ${降级后形态}，原因：token 预算不足（余 ${余额}）"
        → 禁止静默降级（必须显式告知）
```

**超预算截断（partial 结果）**：若 L4 整合因预算截断，`conclusion_label.incomplete = true`；
渲染层检测到后：① 在输出顶部加截断标注 ② 降级形态（不产大块产物）③ 明确列出缺失维度。

---

## 五、可信度与溯源的呈现规范

每种形态**必须**呈现以下元素，且**禁止省略**：

| 呈现元素 | text / markdown | html | image | ppt | video |
|---------|----------------|------|-------|-----|-------|
| 极速版水印 `⚡` | 首行 | 顶部可信度条（橙色）| 水印角标 | 封面页右下角 + 片头字幕 | 片头字幕·全程角标 |
| 置信度（H/M/L）| 末行三标签行 | 顶部可信度条 | 底部小字 | 尾页 | 片尾字幕 |
| Admiralty 双轴 | 末行三标签行 | 顶部可信度条 | 底部小字 | 尾页 | 片尾字幕 |
| 溯源域列表 | 末行 `来源：...` | s7 可展开 ▼ | 底部 1 条（+N more）| 尾页完整列表 | 片尾滚动字幕 |
| incomplete 警告 | 首行 ⚠️ | 顶部条橙色徽章 | 角标 `⚠️ 不完整` | 封面页橙色提示框 | 片头 ⚠️ 字幕 |

**未全验标注铁律**（来自 [speed-tiering](probe-speed-depth-tiering-v1.0.md) §三）：
- 极速版水印**不可缩小到不可见**（HTML：font-size≥12px；图：opacity≥0.6）
- 深度版不加"⚡水印"但必须有"🔬已全验"标识
- `incomplete: true` 警告**优先级高于档位标识**，有截断就显示，不管档位

**Admiralty 解读**（用户可见文案）：
```
source_reliability A → 已验证可靠来源
source_reliability C-D → 通常可信/偶有不可信
info_credibility 1 → 经多源确认
info_credibility 4-6 → 不可信/无法判断
```
HTML/PPT 可在三标签旁加 `(?)` tooltip 展开 Admiralty 完整解读。

---

## 六、品牌一致性

所有视觉形态（html / image / ppt）遵循同一套视觉决策：

| 元素 | 真源 | 在各形态的应用 |
|------|------|-------------|
| 主色 `--mfc-blue` (#1E3A8A) | `tokens-brand.css` | 标题·评级 A 徽章·可信度条背景 |
| 强调色 `--mfc-orange` (#FF7A1A) | `tokens-brand.css` | 极速版水印·incomplete 警告·行动按钮 |
| 主字体 Fredoka | 品牌标准 | 大标题·评级数字 |
| 正文字体 Noto Sans SC | 品牌标准 | 中文正文·表格 |
| 评级色 A🟢/B🟡/C🟠/D🔴 | `deliverable.py _RATING_EMOJI` | 所有形态的评级徽章 |
| probe 品牌 logo | spec-engine 资产 | HTML footer·PPT 封面角标·图底部角标 |

**实施原则**：HTML 形态在 `<style>` 块内声明 CSS 变量（等效于 tokens-brand.css 的值提取）；
image/PPT 形态通过 `token_extractor.py`（spec-engine 侧工具）读取真源常量，不手动维护颜色值。

---

## 七、缓存与复用

### 7.1 渲染产物缓存 key

```
cache_key = hash(conclusion_id, fmt, depth_tier, brand_version, locale)
```

- `conclusion_id`：PG `probe_conclusion.id`（内核唯一标识）
- `fmt`：text/markdown/html/image/ppt/video
- `depth_tier`：flash / deep
- `brand_version`：tokens-brand.css 的 commit SHA（品牌更新时自动失效）
- `locale`：zh-CN（当前仅中文，预留）

### 7.2 缓存策略

| 形态 | 存储位置 | TTL | 复用条件 |
|------|---------|-----|---------|
| text / markdown | Redis（字符串·小） | 24h | 同 cache_key |
| html | 对象存储（文件）+ Redis（uri 引用） | 72h | 同 cache_key |
| image | 对象存储 + Redis（uri 引用） | 72h | 同 cache_key |
| ppt | 对象存储 + Redis（uri 引用） | 24h（较大·及时释放）| 同 cache_key |
| video | 对象存储 | 7天（oss·用户明确保存才延长）| 同 cache_key |

**换形态不重跑采集审核**：MetaAsk 选形态时，先查 `probe_conclusion` 是否存在（同一任务已有内核）→ 有则直接查渲染缓存 → 缓存命中则返回 uri → 缓存未命中则仅重渲染（不回 L2-L4）。

---

## 八、接入声明式管线

### 8.1 invoke 调用约定

```
POST /api/v1/invoke
{
  "tool": "probe",
  "input": {
    "query": "...",
    "delivery_format": "html",        // 形态参数（新增）
    "depth": "deep",                  // 深度档
    "budget_tokens": 5000             // 预算（可选·系统有默认值）
  }
}
```

`delivery_format` 是 M1 新增参数，`contract.py` 需补充到 invoke schema。

### 8.2 扣费流程

```
invoke 进入
  → guard（权限检查：形态权限矩阵 §三.2）
  → 估算渲染 token → 检查预算
  → 执行 L2-L4（数据成本轴①·billing.py 现有逻辑）
  → 执行渲染（形态 token 成本轴②·tokens_render 字段）
  → 两轴成本相加 → wallet.debit（成功才扣·失败不扣）
  → 返回产物（uri 或内联内容）
```

**分轴记账**：`probe_metering` 记 `tokens_data`（L2-L4 成本）+ `tokens_render`（渲染成本）；
`billing.py` 的 `billed` = f(tokens_data, tokens_render, 档位加成)；
形态越高 `tokens_render` 越大，不影响 `tokens_data`。

### 8.3 image / ppt / video 的跨引擎 handoff

需要 MetaDesign 或 MetaCut 参与的形态，probe 通过母体 invoke 路由（不直接调 MetaDesign 内部接口）：

```
probe render(fmt="image")
  → 构造 handoff payload { engine:"MetaDesign", input:{...} }
  → POST /api/v1/invoke { tool:"metadesign", ... }
  → MetaDesign 返回产物 uri
  → probe 写 probe_artifact { format:"img", uri:... }
```

遵循 **R22 五环禁直连** 原则：probe 不直接 import metadesign 代码，走 invoke 契约路由。

---

## 九、M1 优先级与实施指引

| 形态 | 阶段 | 代码现状 | M1 补强点 |
|------|------|---------|---------|
| text | M1 ✅ | `_render_text` 真实实现 | 补三标签行 + 极速版水印行 + 溯源末行 |
| markdown | M1 ✅ | `_render_markdown` 真实实现 | 同上 |
| html | M1 ✅ | `_render_html` 基础实现 | 补「可信度条」顶部元素 + 溯源展开 + 品牌 token + H5-First 响应式 |
| image | P1 ⚠️ | `_render_image_stub` 占位 | P1 接入 MetaDesign invoke·实现 extract_image_data |
| ppt | P2 ⚠️ | `_render_ppt_stub` 占位 | P2 python-pptx 实现·品牌模板 template.pptx |
| video | P3 ⚠️ | `_render_video_stub` 占位 | P3 接入 MetaCut invoke·分镜脚本生成·video-index.md |

**M1 三件事**（可直接落码）：
1. `deliverable.py` 的 text/markdown/html 三个渲染函数，在输出头部统一注入 `_render_credibility_header(core_ir)` 函数（三标签 + 深度水印 + incomplete 警告）
2. HTML 渲染补「可信度条」DOM 块 + 溯源 `<details>` 可展开 + 响应式断点
3. `contract.py` invoke schema 补 `delivery_format` 参数·权限矩阵检查

---

## 十、诚实边界声明

| 形态 | 成熟度 | 说明 |
|------|--------|------|
| text / markdown | ✅ M1 可用 | 真实实现·M1 补强后立即可用 |
| html | ✅ M1 可用 | 基础实现已在·M1 补强可信度条 |
| image | ⚠️ P1（设计好·未接）| MetaDesign 接入未验证·stub 占位 |
| ppt | ⚠️ P2（方案好·未实现）| python-pptx 技术路径成熟·需开发·需品牌模板 |
| video | ⚠️ P3（架构占位）| MetaCut 依赖 P3 成熟·TTS/合成管线有外部依赖·勿在 M1/P1 承诺 |

**不存在的假设**：视频/PPT 生成依赖 MetaCut/MetaDesign 的 invoke 接口真实可用，当前均为 stub 占位；P1-P3 落地前，这两种形态对用户展示为「即将上线」，不承诺时间。

---

## 关联文档

- 形态矩阵真源：[design-v1](probe-intelligence-engine-design-v1.md) §5.5
- 情报内核数据结构：[数据脊柱](probe-data-persistence-and-cache-design-v1.0.md) §2.4-2.5
- 深度档位·智能界定：[speed-tiering](probe-speed-depth-tiering-v1.0.md)
- 编排并发设计：[orchestration](probe-orchestration-engine-solution-v1.0.md)
- 成本计量分轴：[cost-metering](probe-cost-metering-design-v1.0.md)
- 渲染入口代码真源：`app/services/deliverable.py`（render 函数·FmtLiteral）
- 七段报告数据类：`app/services/report.py`（Section1-7 dataclass）
- 三标签数据类：`app/audit/standards.py`（ConclusionLabel · Admiralty）

---

> 落盘路径：`/Users/metafo/Downloads/metafoclaw/probe/docs/3-build/probe-delivery-rendering-pipeline-design-v1.0.md`
> 性质：**闭缺口 #6**（design-v1 §5.5 形态矩阵的管线落地设计）· 待并入 master-solution-v2 §七

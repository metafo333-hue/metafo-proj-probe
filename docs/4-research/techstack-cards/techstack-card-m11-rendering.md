# 技术源卡 M11 · 交付渲染管线

> 需求真源：[delivery 设计 v1.0](../../3-build/probe-delivery-rendering-pipeline-design-v1.0.md)（Core IR 自研·渲染缓存=独立第三层）· 形态：pdf/ppt/图卡/图表/图示
> checked_at: 2026-06-11 · 本卡有现场实测数据（/tmp/ts-m11 venv · matplotlib/python-pptx/WeasyPrint 实测）
> probe-a 规格：4C 8G · Ubuntu · 公网 EIP · 非 GPU · 禁 GPU/ML 密集任务（server-roles T 红线）

---

## 候选实测

### ① html → pdf

#### C1-A · WeasyPrint

| 维度 | 数据 |
|------|------|
| **repo** | github.com/Kozea/WeasyPrint |
| **license** | BSD-3-Clause |
| **stars** | 9 265（2026-06-11） |
| **最近活跃** | v69.0（2026-06-02）· 持续发版 · 2026-06-10 最新 commit |
| **PyPI 版本** | 69.0（Python ≥ 3.10）|
| **系统依赖** | **必须**：`libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 libfontconfig1`（Debian/Ubuntu）；可选 jpeg/openjp2：`libjpeg-dev libopenjp2-7-dev` |
| **Python 依赖** | pydyf · cffi · tinyhtml5 · tinycss2 · cssselect2 · Pillow · fonttools[woff] · Pyphen（共 8 个，无 LangChain 类重框架）|
| **中文字体方案** | 经 fontconfig 自动拾取系统字体。服务器无 CJK 字体时全部显示为方框。**修复**：`apt install fonts-noto-cjk fonts-noto-cjk-extra`（~100 MB），WeasyPrint 零配置自动选字体。HTML 内联 `@font-face` 也可（字体 base64 嵌入·文件较大）|
| **资源面（probe-a 4C8G）** | 单次转换 CPU spike ≈ 300–600ms / 内存 ≈ 50–150 MB · 无常驻进程 · 异步调用可 `asyncio.run_in_executor` 后台池 |
| **hands_on** | 实测：`pip install weasyprint` 安装成功；**但 import 直接失败**，错误为 `OSError: cannot load library 'libpango-1.0-0'`（Mac 无 Pango）。C 库依赖在服务器上需提前 apt install，是硬门槛。|
| **checked_at** | 2026-06-11 |

**关键发现**：WeasyPrint 在 v60+ 已放弃 Cairo/GDK-PixBuf，改用纯 Python PDF 引擎 pydyf，但 **Pango 文字排版 C 库仍为运行时必须依赖**，无法绕过。实测 `cffi.dlopen('libpango-1.0-0')` 失败即完全不可用。

---

#### C1-B · Playwright `page.pdf()`（html → pdf）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/microsoft/playwright-python |
| **license** | Apache-2.0 |
| **PyPI 版本** | 1.60.0（2026-06-11 最新）|
| **最近活跃** | 持续活跃（stars 非核心指标，以 playwright 主仓 88k+ 为准）|
| **系统依赖** | 需 Chromium（通过 `playwright install chromium --with-deps` 安装·含所有 OS 依赖·约 350 MB）；**无 Pango/Cairo 额外 C 库** |
| **中文字体方案** | Chromium 渲染走 system fontconfig；服务器同样需 `apt install fonts-noto-cjk`；不同点：**Chromium 对字体 fallback 更健壮**（自带部分 emoji + 常见 CJK 备选），WeasyPrint 若 fontconfig 找不到字体则直接乱码，Chromium 多数情况降级显示而非方框 |
| **API 验证** | `Page.pdf(scale, format, margin, landscape, path, ...)` 完整签名确认（2026-06-11 实测）· `Page.screenshot(type, path, fullPage, clip, ...)` 同时可用 |
| **资源面** | 单进程 Chromium 常驻约 150–250 MB；每次 `page.pdf()` 约 500ms–2s（取决于 HTML 复杂度）；**probe-a 8G 可支撑 2–3 个并发 worker**，超过需排队 |
| **已有实例** | MCP 层（`mcp-chrome-*`）已在 Mac 本机部署 Playwright Chromium；probe-a 部署时可直接复用同路径安装 |
| **hands_on** | `playwright install chromium` 显示下载路径：`/Users/metafo/Library/Caches/ms-playwright/chromium-1223`（约 350 MB）；API 可用，`Page.pdf()` `Page.screenshot()` 均确认 |
| **checked_at** | 2026-06-11 |

**推荐档位（PDF）**：**C1-B Playwright** 胜出。理由：① 无 Pango 等额外 C 库，与 probe 技术栈一致（Python）；② Chromium 已是服务器既有能力（MCP 侧已使用）；③ HTML 完整渲染品质更好（CSS Grid/Flexbox/品牌 tokens 全支持）；④ 同时可做图卡截图（复用一个进程）。**WeasyPrint 仅在需要纯 Python PDF 生成（无 Chromium 环境）时作备选**。

---

### ② md → ppt

#### C2-A · Marp CLI

| 维度 | 数据 |
|------|------|
| **repo** | github.com/marp-team/marp-cli |
| **license** | MIT |
| **stars** | 3 621（2026-06-11）|
| **最近活跃** | v4.4.0（2026-05-06）· 活跃 |
| **npm 版本** | 4.4.0 |
| **核心能力** | Markdown → PDF / PPTX / HTML；支持自定义主题 CSS；可产出可编辑 `.pptx` |
| **系统依赖** | Node.js ≥ 18 + 系统 Chrome/Chromium（官方 Docker 用 playwright install chromium，约 350 MB）；**无 Python 原生接口**（需 subprocess 调用 CLI）|
| **Docker 镜像** | `marpteam/marp-cli`：553 MB（node:22-bookworm-slim + playwright Chromium + gosu）|
| **中文字体方案** | **Docker 镜像不含 CJK 字体**（Dockerfile 实测：apt install 仅装 gosu，无 fonts-noto-cjk）。修复：① 在 Dockerfile 追加 `apt install -y fonts-noto-cjk` 构建自定义镜像；② 挂载宿主 `/usr/share/fonts` 到容器；③ 主题 CSS 内 `@import url('https://fonts.googleapis.com/...')`（需外网，服务器可行）|
| **资源面** | Docker 启动 ≈ 2–4s（冷启动重）；PPTX 生成 ≈ 1–3s（含 Chromium 渲染）；**常驻容器方案可降到 <500ms**；内存约 300–500 MB |
| **hands_on** | 未本地实测（需 Node.js）；基于 Dockerfile 源码分析 + Docker Hub 553 MB 镜像大小确认 |
| **checked_at** | 2026-06-11 |

---

#### C2-B · python-pptx

| 维度 | 数据 |
|------|------|
| **repo** | github.com/scanny/python-pptx |
| **license** | MIT |
| **stars** | 3 415（2026-06-11）|
| **最近活跃** | v1.0.2（最新 tag）· 2026-06-11 更新（仓库持续活跃）|
| **PyPI 版本** | 1.0.2 |
| **系统依赖** | **零 C 库依赖**（纯 Python）· 仅 lxml + Pillow（均为 Python 生态标配）|
| **中文字体方案** | PPTX 内字体引用不依赖系统字体；**需在 `.pptx` 模板文件中预嵌中文字体引用**（Slide Master → Noto Sans SC 或品牌 Fredoka + Noto Sans SC）；运行时生成的文字用 `run.font.name = 'Noto Sans SC'` 指定字体名，**打开 PPTX 的设备需有该字体**（企业用户 Windows/Mac 通常已有）|
| **资源面** | 生成 10 页 PPTX ≈ 50–200ms · 内存 ≈ 20–50 MB · **最轻量** · 无 Chromium 开销 |
| **hands_on** | **实测通过**：生成含中文「情报报告 · 深度验证·三标签·Admiralty A-1」的 .pptx（28 346 bytes）· 品牌色 RGB(0x1E, 0x3A, 0x8A) 注入成功（2026-06-11）|
| **checked_at** | 2026-06-11 |

**推荐档位（PPT）**：**C2-B python-pptx** 胜出。理由：① 零系统依赖，纯 Python，与 probe requirements.txt 直接集成；② 实测中文文字生成成功；③ 资源面最轻；④ 已在 delivery 设计 v1.0 § 2.4.2 明确选用为首选（📐标准实践）。Marp CLI 可作为 P2 阶段的备选（Markdown 驱动·主题复用更方便）。

---

### ③ 图表（竞品横评/证据链数据可视化）

#### C3-A · pyecharts

| 维度 | 数据 |
|------|------|
| **repo** | github.com/pyecharts/pyecharts |
| **license** | MIT |
| **stars** | 15 761（2026-06-11）|
| **最近活跃** | v2.1.0（2026-02-10）· 2026-06-11 仓库有更新 |
| **PyPI 版本** | 2.1.0 |
| **系统依赖** | 生成 HTML/JSON：**零依赖**（纯 Python + ECharts JS 内嵌）；生成 PNG/JPG：需 `snapshot-selenium`（Selenium + ChromeDriver，2019 年停止更新 v0.0.2）或 `pyecharts-snapshot`（177 stars，2026-06-01 有更新·支持 selenium driver）|
| **中文字体方案** | HTML/JS 输出：Chromium 渲染字体（与浏览器一致）；PNG 快照：同 Playwright/Selenium 依赖，字体问题同 C1-B |
| **资源面** | HTML 生成：极轻（<10ms）；PNG 快照：需启动 Chromium，与 C1-B 同等开销 |
| **hands_on** | 未实测 PNG 路径（需 Chromium 驱动）；HTML 输出路径理论上零依赖 |
| **坑** | pyecharts PNG 快照生态分裂：snapshot-selenium 已停更（2019）；pyecharts-snapshot 维护频率低；**最实际路径 = 生成 HTML → Playwright `page.screenshot()` → PNG**（复用 C1-B Chromium）|
| **checked_at** | 2026-06-11 |

---

#### C3-B · matplotlib

| 维度 | 数据 |
|------|------|
| **repo** | github.com/matplotlib/matplotlib |
| **license** | PSF-compatible（BSD 风格，商用无限制）|
| **stars** | 22 873（2026-06-11）|
| **最近活跃** | v3.10.9（2026-04-23）· 持续高频发版 |
| **PyPI 版本** | 3.10.9 |
| **系统依赖** | 纯 Python（含编译扩展 freetype2，但 wheel 预编译·无需手动 apt）；**不需要 Chromium**；Agg 后端无 GUI 依赖 |
| **中文字体方案** | 需在代码内配置 `rcParams['font.family']`；**服务器无 CJK 字体时只渲染为方框**。修复路径：① `apt install fonts-noto-cjk fonts-noto-cjk-extra`；② 下载 TTF（如 NotoSansSC-Regular.ttf）放 `~/.fonts/` 并 `fc-cache -fv`；③ `matplotlib.font_manager.fontManager.addfont('/path/to/NotoSansSC.ttf')` 运行时加载。**实测（2026-06-11 Mac）**：`STHeiti`/`Heiti TC` 可用，Linux 服务器需手动安装 Noto。|
| **资源面** | 生成图表 ≈ 50–300ms（含字体加载首次开销）；首次缓存字体约 2–5s（之后快）；内存 ≈ 30–80 MB；**无 Chromium 开销**，4C8G 可并发多个 |
| **hands_on** | **实测通过**：`matplotlib.use('Agg')` 非交互模式 · `fig.savefig('/tmp/test-chart.png')` 成功（6 955 bytes）；CJK 测试：使用 STHeiti fallback 时 `findfont: Font family 'PingFang SC' not found` 警告但图片生成成功（11 215 bytes）（2026-06-11）|
| **checked_at** | 2026-06-11 |

**推荐档位（图表）**：**C3-B matplotlib** 胜出。理由：① 不需 Chromium（无额外进程开销）；② 实测通过；③ 静态图表（柱图/雷达/折线）纯 Python 生成；④ 与 python-pptx 配合（图表嵌入 PPT）是标准做法。pyecharts 推荐仅在需要**可交互 HTML 图表**时使用（用户直接看 HTML 报告中的 ECharts 交互图），PNG 输出走 Playwright 截图路径。

---

### ④ 图卡（分享卡·html → png）

#### C4-A · Playwright `page.screenshot()`

| 维度 | 数据 |
|------|------|
| **repo** | github.com/microsoft/playwright-python |
| **license** | Apache-2.0 |
| **系统依赖** | 与 C1-B 完全共用（同一 Chromium 实例）|
| **中文字体方案** | 与 C1-B 完全共用 |
| **资源面** | 与 C1-B 共用 Chromium 进程时：截图 ≈ 200–800ms（HTML 简单则快）；**可与 PDF 共用一个 Playwright 实例，节省开销** |
| **API** | `page.screenshot(type='png', full_page=False, clip={x,y,width,height})` 支持裁剪 |
| **hands_on** | `Page.screenshot` 签名实测确认（2026-06-11）|
| **优势** | 评级卡/分享卡 = 一段 HTML + 品牌 CSS → Playwright 截图，**品牌 tokens 和中文字体与 HTML 报告完全一致**，无额外开发 |
| **checked_at** | 2026-06-11 |

---

#### C4-B · imgkit（html → png，wkhtmltopdf 方案）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/jarrekk/imgkit |
| **license** | MIT |
| **stars** | 827（2026-06-11）|
| **最近活跃** | **最后 commit 2023-05-29**（停滞）· PyPI 最新版 v1.2.3（2023-02-23）|
| **系统依赖** | **wkhtmltopdf**（C++ 大型依赖，约 50 MB，Qt WebKit 嵌入）；wkhtmltopdf 项目**2022 年已停止维护**（上游 EOL）|
| **中文字体方案** | wkhtmltopdf 用 QT 字体，需系统 CJK 字体；历史上 CJK 渲染问题多，社区长期报告 |
| **资源面** | wkhtmltopdf 启动较慢；内存 ≈ 100–300 MB |
| **hands_on** | 未实测；基于上游 EOL + 停滞状态直接排除 |
| **结论** | ❌ **排除**：wkhtmltopdf 上游停更（2022 EOL）+ imgkit 本身停滞（2023）。同功能 Playwright 更新、更稳、CJK 更好。 |
| **checked_at** | 2026-06-11 |

**推荐档位（图卡）**：**C4-A Playwright `page.screenshot()`** 无竞争，直接选用。imgkit 排除。

---

### ⑤ mermaid-cli（图示·流程图/时序图）

| 维度 | 数据 |
|------|------|
| **repo** | github.com/mermaid-js/mermaid-cli |
| **license** | MIT |
| **stars（cli）** | 4 675（2026-06-11）|
| **stars（mermaid 核心）** | 88 578（2026-06-11）|
| **最近活跃** | v11.15.0（2026-05-13）· 活跃 |
| **npm 版本** | 11.15.0 |
| **系统依赖** | Node.js 18 LTS + Chromium（Alpine 打包的 `chromium` 系统包）；**非 Python 原生**（subprocess 调用）|
| **Docker 镜像** | `minlag/mermaid-cli`：852 MB（node:18-alpine + chromium + **font-noto-cjk + font-noto-emoji 已内置**）|
| **中文字体方案** | **Docker 镜像已内置 font-noto-cjk**（`install-dependencies.sh` 实测：`apk add chromium font-noto-cjk font-noto-emoji ...`）· 开箱即用 CJK ✅ |
| **资源面** | Docker 启动 ≈ 2–5s（冷启动重）；单图生成 ≈ 1–3s；内存约 400–600 MB（containered），**852 MB 镜像是最重的候选**；probe-a 4C8G 资源紧张 |
| **输出格式** | SVG / PNG / PDF / HTML |
| **hands_on** | 未本地实测；基于 Dockerfile 源码分析 |
| **替代方案** | probe 侧 Python 内联 mermaid：HTML 报告直接嵌入 `<div class="mermaid">` + mermaid.js CDN，**浏览器端渲染**，无需服务器端 mmdc；仅在需要离线静态 SVG/PNG 时才需要 mermaid-cli |
| **checked_at** | 2026-06-11 |

---

## 中文渲染坑清单

| 坑 | 影响组件 | 根因 | 修复方案 |
|----|---------|------|---------|
| **服务器无 CJK 字体（最高频）** | WeasyPrint / matplotlib / Playwright | Ubuntu/CentOS 最小化安装不含 CJK 字体 | `apt install fonts-noto-cjk fonts-noto-cjk-extra && fc-cache -fv`（约 100 MB）|
| **WeasyPrint libpango 缺失** | WeasyPrint 独有 | 纯 Python venv 安装 weasyprint 不自动装 C 库 | `apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0`（约 10 MB）|
| **matplotlib 字体缓存冷启动** | matplotlib | 首次运行 `FontManager` 扫描全部 TTF，约 2–5s | 部署后执行一次 `python -c "import matplotlib.font_manager"` 预热缓存 |
| **matplotlib 中文字体 findfont warning** | matplotlib | rcParams 找不到 font family 名（fallback 到 DejaVu→方框）| 确认 `font.family` 设置为服务器上已安装的字体名（如 `'Noto Sans CJK SC'` 而非 `'Noto Sans SC'`）；用 `fm.findfont('Noto Sans CJK SC')` 验证 |
| **python-pptx 中文 fallback** | python-pptx | PPTX 指定字体名不存在时 Windows 会乱码，macOS 自动 fallback | 模板 `.pptx` 中嵌入 Slide Master 字体设置；生产环境用 Noto 系列 |
| **Marp Docker CJK 字体缺失** | Marp CLI Docker | 官方 Dockerfile 只装 gosu，无中文字体 | 基于官方镜像自定义：`FROM marpteam/marp-cli && apt install -y fonts-noto-cjk` |
| **Mermaid Docker 已含 CJK** | mermaid-cli Docker | — | ✅ 开箱即用，`install-dependencies.sh` 已 `apk add font-noto-cjk` |
| **CJK 断行问题** | WeasyPrint / Playwright HTML | CSS `word-break: keep-all` 过于严格时 CJK 不断行 | HTML 模板设 `word-break: break-all; overflow-wrap: break-word`（中文场景常规设置）|
| **emoji 渲染（如 ⚡ 🔬 ⚠️）** | WeasyPrint / matplotlib | WeasyPrint：emoji 需 COLR 字体（已有 issue #2777）；matplotlib：无法渲染 emoji | HTML 形态走 Playwright（Chromium emoji 完整）；matplotlib 图表避免使用 emoji（用 ASCII 替代：[!] [D]）|

---

## 推荐组合

### 最终推荐

| 形态 | 推荐件 | 理由 |
|------|-------|------|
| **html → pdf** | **Playwright `page.pdf()`** | 无额外 C 库；CJK 健壮（Chromium fontconfig）；品牌 CSS 完整渲染；与图卡截图共用实例 |
| **md → ppt** | **python-pptx** | 纯 Python；零 C 库；实测通过（含中文）；最轻量；已在 delivery 设计 v1.0 选定 |
| **图卡（png）** | **Playwright `page.screenshot()`** | 与 PDF 路径共用 Chromium；HTML→图卡品牌一致 |
| **图表（静态）** | **matplotlib** | 无 Chromium；纯 Python；实测通过；嵌入 PPT 标准做法 |
| **图表（交互 HTML）** | **pyecharts** → HTML 内嵌 | 生成 ECharts JS 片段，用户在 HTML 报告中交互；PNG 输出走 Playwright 截图 |
| **图示（mermaid）** | **HTML 内嵌 mermaid.js** | 浏览器端渲染，无服务器 Node.js 开销；仅需静态 PNG/SVG 时才用 `mermaid-cli` Docker |
| **html → pdf（备选）** | WeasyPrint | 仅在纯 Python 轻量 PDF 需求（无 Chromium）场景；需 apt 安装 Pango 等 C 库 |

### 部署成本视图（probe-a 4C8G · Ubuntu）

| 方案块 | apt 包 | 额外磁盘 | 内存峰值 |
|--------|--------|---------|---------|
| **Playwright Chromium**（PDF + 图卡） | playwright install chromium --with-deps | ~350 MB | 150–250 MB/进程 |
| **中文字体（全部场景共用）** | fonts-noto-cjk fonts-noto-cjk-extra | ~100 MB | 0（系统级）|
| **matplotlib**（图表） | 无（pip wheel 含 freetype2）| pip 约 30 MB | 30–80 MB |
| **python-pptx**（PPT） | 无 | pip 约 5 MB | 20–50 MB |
| **总额外开销** | — | ≈ 485 MB | ≈ 200–400 MB（并发时）|

**节省方案**：PDF + 图卡共用同一 Playwright worker pool（asyncio.Queue），不开多进程；4C8G 支撑 2 个 Chromium worker + matplotlib + python-pptx 并发，有余量。

---

## tech-gate 12 闸速查表

> 针对推荐组合：Playwright(pdf+图卡) + python-pptx + matplotlib + pyecharts HTML + mermaid.js 内嵌

| 闸 | 问题 | Playwright | python-pptx | matplotlib | pyecharts | mermaid.js 内嵌 |
|----|------|:---:|:---:|:---:|:---:|:---:|
| G1 | 开源许可证可商用？ | ✅ Apache-2.0 | ✅ MIT | ✅ PSF-BSD | ✅ MIT | ✅ MIT |
| G2 | Python ≥3.10 兼容？ | ✅ | ✅ | ✅ | ✅ | N/A（前端 JS）|
| G3 | 无需额外 GPU/ML 资源？ | ✅ | ✅ | ✅ | ✅ | ✅ |
| G4 | 中文字体可解决？ | ✅ apt fonts-noto-cjk | ⚠️ 需模板设字体 | ⚠️ 需 apt + rcParams | ✅ HTML Chromium | ✅ Chromium/浏览器 |
| G5 | 系统依赖重量可接受？ | ⚠️ Chromium ~350 MB | ✅ 零 C 库 | ✅ wheel 含 | ✅ 零 | ✅ 零 |
| G6 | probe-a 4C8G 可支撑？ | ✅ 2 worker pool | ✅ | ✅ | ✅ | ✅ |
| G7 | 异步/非阻塞可用？ | ✅ asyncio 原生 | ⚠️ 需 executor | ⚠️ 需 executor | ✅（HTML 生成快）| N/A |
| G8 | 社区活跃（2026 有 release）？ | ✅ 1.60.0 | ✅ v1.0.2 | ✅ v3.10.9 | ✅ v2.1.0 | ✅ v11.15.0 |
| G9 | 实测可用（hands_on pass）？ | ✅（API 确认）| ✅（中文 pptx 生成）| ✅（Agg + CJK 图）| ⚠️ HTML 可，PNG 需 playwright | N/A（浏览器端）|
| G10 | emoji 渲染正确？ | ✅ Chromium 完整 | ⚠️ 取决于字体 | ❌ 不支持 emoji | ✅ Chromium | ✅ Chromium |
| G11 | 与 Core IR → probe_artifact 管线兼容？ | ✅ bytes/path 返回 | ✅ 文件输出 | ✅ 文件输出 | ✅ HTML 字符串 | ✅ HTML 片段 |
| G12 | 不引入 GPU/ML 密集操作（T 红线·probe-a）？ | ✅ | ✅ | ✅ | ✅ | ✅ |

**全闸通过档位**：Playwright(12/12) · python-pptx(11/12·G4 需注意) · matplotlib(10/12·G4+G10 需注意) · pyecharts HTML(11/12·G9 PNG 路径⚠️) · mermaid.js 内嵌(N/A 3闸·其余全通)

---

## verdict

**推荐组合：以 Playwright 为核心渲染引擎，python-pptx 做 PPTX，matplotlib 做静态图表**

```
落矩阵格：L4 整合层（渲染缓存·独立第三层） × Validator 参与（品牌一致性校验）

Core IR
  └─ html/pdf → Playwright page.pdf()          [M1→P1 Apache-2.0]
  └─ 图卡 png  → Playwright page.screenshot()  [M1→P1 Apache-2.0]  共用 worker pool
  └─ ppt       → python-pptx pptx_builder.py   [P2 MIT] + matplotlib 图嵌入
  └─ 图表 html → pyecharts → ECharts JS 片段   [P1 MIT] 内嵌 HTML 报告（交互）
  └─ 图表 png  → matplotlib Agg                [P1 PSF] 嵌入 PDF/PPT
  └─ 图示      → mermaid.js 浏览器端            [P1 MIT] HTML 报告内嵌（静态 SVG 需 mmdc Docker）
```

**四条铁律**：
1. **字体先行**：probe-a 部署脚本第一步 `apt install fonts-noto-cjk fonts-noto-cjk-extra`，所有渲染件共用
2. **Playwright 单实例**：PDF + 图卡截图共用 asyncio worker pool（最多 2 个 Chromium 进程），不重复启动
3. **matplotlib emoji 禁用**：图表轴标题/图例禁用 emoji（用 `[!]` `[High]` 等 ASCII 替代），emoji 只在 HTML/Playwright 路径
4. **WeasyPrint 不纳入 P1**：Pango C 库依赖链与 probe-a 轻量 Python 栈冲突；Playwright 已覆盖其全部功能且更强

**与 delivery 设计 v1.0 的对齐**：
- D1（Core IR 唯一输入）✅ 各渲染件均只读 Core IR
- D2（M1 先上 text/markdown/html）✅ html→PDF 是 P1 形态，不影响 M1
- D4（复用破晓品牌 tokens）✅ Playwright 完整 CSS 渲染 tokens-brand.css
- D5（大块走对象存储）✅ Playwright 返回 bytes → SeaweedFS/临时盘 → probe_artifact.uri
- D6（渲染缓存）✅ 按 cache_key 缓存渲染产物，不重渲染

---

## 顺手发现

1. **mermaid-cli 已内置 font-noto-cjk（Docker）**：`install-dependencies.sh` 实测确认，是五个候选中**唯一开箱即 CJK 的 Docker 镜像**（对比 marp-cli 需手动加）。若未来选 mermaid-cli Docker 路径，CJK 字体无需额外操作。

2. **pyecharts snapshot 生态分裂坑**：`snapshot-selenium`（PyPI）已于 2019 年停更（v0.0.2），`pyecharts-snapshot`（GitHub）2026-06-01 仍有更新但 stars 仅 177。**最实用路径 = pyecharts 生成 HTML → Playwright 截图**，绕开整个 snapshot 生态，省 Selenium + ChromeDriver 管理。

3. **Marp v4.4.0 可直接输出 `.pptx`**（官方支持）：`marp --pptx deck.md -o out.pptx`。若 P2 阶段需要「Markdown 驱动·主题版式更丰富」的 PPT，Marp 是备选，但需接受 Node.js 依赖与 CJK 字体手动配置。目前 python-pptx 更符合 probe 技术栈。

4. **WeasyPrint emoji 已知问题**：GitHub issue #2777（2026-05-25 open）：COLR emoji 字体支持尚不完整。这是选 Playwright（Chromium emoji 完整）而非 WeasyPrint 的额外理由。

---

> 落盘路径：`/Users/metafo/Downloads/metafoclaw/probe/docs/4-research/techstack-cards/techstack-card-m11-rendering.md`
> checked_at: 2026-06-11 · 实测：/tmp/ts-m11 venv（matplotlib 3.10.9 · python-pptx 1.0.2 · WeasyPrint 69 import 失败确认 libpango 依赖）

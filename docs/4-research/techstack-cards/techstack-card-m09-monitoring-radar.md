# 技术源卡 M9 · 监测雷达

> 需求真源：monitoring-radar 设计（S2）· 红线：监测目标限合法许可源 / API endpoint / 自有页面，禁监测任意第三方页面
> checked_at: 2026-06-11 · 实测范围：GitHub repo metadata + API doc + 架构文档现场抓取

---

## 候选实测

### 1. changedetection.io（整机）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/dgtlmoon/changedetection.io |
| license | Apache-2.0 |
| stars | 32,000 |
| 最近活跃 | v0.55.7 · 2026-05-25（距今约 2 周） |
| 主语言 | Python 81.4% · JS 6.5% · HTML 8.1% |
| API 可编程性 | ✅ 完整 REST API（OpenAPI spec at `/api/v1/full-spec`）；CRUD watch / 获取 snapshot / **跨版本 diff**（`GET /api/v1/watch/{uuid}/difference/{from}/{to}`，支持 text/HTML/markdown/colored-HTML 格式）；可批量导入 URL；webhook 通知（Apprise 100+ 渠道）|
| 内部架构 | Flask 3.1 + Werkzeug · 文件系统 datastore（`/datastore` 目录，orjson 加速）· 内置优先级队列调度（`RecheckPriorityQueue`）· diff 核心：`changedetectionio/diff.py` · HTML 预处理：`changedetectionio/html_tools.py`（使用 inscriptis 做 HTML→text 转换）|
| 存储后端 | 纯文件系统（JSON/orjson），**无 PG/Redis/SQLite 原生支持**；与我方 PG+Redis 完全独立 |
| 资源占用 | 无 Playwright：约 100 MB RAM，CPU <1%；启用 Playwright/Chrome：推荐 ≥2 GB RAM |
| Docker 镜像 | `dgtlmoon/changedetection.io:latest`；ARM v6/v7/arm64 均支持 |

**红线适配评估（关键）**：
changedetection.io 本质是定时抓页面的完整爬取系统。probe 红线"不自己爬数据"意指**不对任意第三方页面发起非授权采集**，而非禁止所有 HTTP 请求。整机合法使用场景仅限：
1. 监测我方自有页面（hub.metafoclaw.com / api endpoint）
2. 监测已获授权的合法许可数据源（有 robots.txt 允许 + ToS 许可 + API Key 访问）
3. 监测纯 API endpoint（JSON 响应变更）

在上述约束下，整机的"爬取网页"能力 **90% 闲置**，真正用到的只有：调度触发 + HTTP fetch + diff 计算 + 告警分发 4 个模块。

---

### 2. changedetection.io diff 内核拆用（拆思想自研）

内核实际由两部分组成（源码考证）：

| 组件 | 实现 | 可单独 pip 安装 |
|------|------|----------------|
| HTML→text | **inscriptis** 2.7.1（Apache-2.0，342 stars，2026-02-27 最新）| ✅ `pip install inscriptis` |
| 文本 diff | Python 标准库 **difflib**（`SequenceMatcher` / `HtmlDiff`）或 **lxml.html.diff**（`<ins>`/`<del>` 标注）| ✅ 零额外依赖 |

自研 diff 管线最小实现：
```python
from inscriptis import get_text          # HTML → 结构化纯文本
import difflib

old_text = get_text(old_html)
new_text = get_text(new_html)
diff = list(difflib.unified_diff(
    old_text.splitlines(), new_text.splitlines(),
    lineterm=""
))
```
此方案：无额外服务依赖 · 零 Docker overhead · 直接插入我方 APScheduler 调度任务 · 结果存 PG · 变更事件发 Redis。

---

### 3. urlwatch（轻量对照）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/thp/urlwatch |
| license | BSD（COPYING 文件，标准 BSD-3） |
| stars | 3,100 |
| 最近活跃 | 967 commits on master，49 tags（具体最近日期页面未显示，约 2024-2025） |
| 主语言 | Python 70.5% |
| API 可编程性 | ❌ 无 REST API；仅命令行工具；通知靠配置文件 |
| 资源占用 | 极轻（纯 CLI Python 工具，按需运行）|
| 集成难度 | 高：无嵌入 API，只能作为外部进程调用或解析其通知 |

**红线适配**：同 changedetection.io，需限合法许可源。作为 CLI 工具可用 cron 驱动，但无法编程集成 PG/Redis，扩展性差。

---

### 4. huginn（重量级对照）

| 字段 | 值 |
|------|-----|
| repo | https://github.com/huginn/huginn |
| license | MIT |
| stars | 42,000+ |
| 运行时 | Ruby on Rails · MySQL/PostgreSQL · 需 Unicorn worker |
| 内存要求 | 推荐 2 GB RAM（最低 0.5 GB 但极不稳定）；2+ vCPU 推荐 |
| API 可编程性 | ✅ 有 Agent API，但生态以 GUI 工作流为主 |
| 集成难度 | 极高：Ruby 技术栈与我方 Python 完全异构；需独立 MySQL/PG 实例 |

**红线适配**：预判正确 ❌ 排除。Ruby 技术栈 + 2GB 内存 + 复杂运维 = 与 probe-a 资源面和技术栈不匹配。

---

## 整机 vs 拆思想分析（红线约束下 changedetection.io 整机价值重估）

### 整机价值重估

| 维度 | 红线约束前 | 红线约束后 |
|------|-----------|-----------|
| 核心能力 | 监测任意网页变更 | 仅限合法许可源/API/自有页面 |
| 爬取能力利用率 | 100%（核心用例）| ~10%（仅合法 API endpoint / 自有页） |
| Playwright JS 渲染 | 高频用于复杂页面 | 几乎不需（API endpoint 是纯 JSON）|
| 内置调度器价值 | 高（核心功能）| 低（我方已有 APScheduler 决策）|
| 独立 datastore 价值 | 高（自成体系）| 负（与 PG 主库形成数据孤岛）|
| 告警 / 通知系统 | 高（Apprise 100+ 渠道）| 中（我方已有 origin-notify.py；但 Apprise 可复用）|
| Docker 隔离运维 | 低额外成本 | 与我方 PG+Redis+APScheduler 形成并行系统，增运维面 |

**结论**：整机在红线约束下变成"大炮打蚊子"——引入 Flask Web UI + 文件系统双写 + 独立调度器，换来的核心能力（diff 计算）可以用 inscriptis + difflib 50 行代码复现。唯一有价值的整机场景：**若 S2 需监测大量自有 HTML 页面（非 API）且需可视化 diff 审阅界面**，整机的 Web UI 省开发成本。

### 拆思想自研优势

1. **零额外服务**：inscriptis + difflib 是纯 Python 库，不需 Docker sidecar
2. **统一数据层**：diff 结果直接入 PG `monitor_snapshots` / `change_events` 表，触发 Redis 事件
3. **调度复用**：直接挂 APScheduler 任务，无双调度器竞争
4. **资源省**：无 Flask server overhead，probe-a 节约 ~100-200 MB RAM
5. **红线透明**：我方代码完全控制 fetch 对象，无黑盒爬取

---

## tech-gate 12 闸速查表

| 闸 | 问题 | changedetection.io 整机 | 拆思想（inscriptis+difflib）| urlwatch | huginn |
|----|------|------------------------|---------------------------|----------|--------|
| G1 | 开源许可合规 | ✅ Apache-2.0 | ✅ Apache-2.0 + stdlib | ✅ BSD-3 | ✅ MIT |
| G2 | 红线适配（不自己爬） | ⚠️ 工具本身是爬虫，需严格限合法源配置 | ✅ 我方控制 fetch 对象，透明可审 | ⚠️ 同整机，需限合法源 | ⚠️ 同 |
| G3 | 与 PG 集成 | ❌ 文件系统孤岛，无原生 PG 支持 | ✅ 直接写 PG | ❌ 无 | ✅（但需额外 PG 实例）|
| G4 | 与 Redis 集成 | ❌ 无 | ✅ 直接发事件 | ❌ 无 | ❌ 用 MySQL |
| G5 | APScheduler 复用 | ❌ 自带独立调度器 | ✅ 直接挂 APScheduler | ❌ 依赖系统 cron | ❌ 自带 DelayedJob |
| G6 | 资源占用 | ⚠️ ~100 MB（无Playwright）/ ~2GB（有）| ✅ < 10 MB（纯库）| ✅ 极轻 | ❌ 推荐 2 GB RAM |
| G7 | probe-a 技术栈匹配 | ⚠️ Python 但独立 Flask 服务 | ✅ 直接 import | ✅ Python CLI | ❌ Ruby |
| G8 | API 可编程性 | ✅ 完整 REST API | ✅ 函数级调用 | ❌ 仅 CLI | ⚠️ 有 API 但 Ruby |
| G9 | diff 格式丰富度 | ✅ text/HTML/markdown/colored | ⚠️ 需自实现输出格式 | ⚠️ unified diff 为主 | ⚠️ Agent 级别可配 |
| G10 | 告警通知 | ✅ Apprise 100+ 渠道 | ⚠️ 需对接 origin-notify.py | ⚠️ 邮件/Slack 等配置 | ✅ 丰富 |
| G11 | 社区活跃度 | ✅ 32k stars · v0.55.7（2026-05） | ✅（各库均活跃维护）| ⚠️ 3.1k · 活跃度一般 | ✅ 42k · 但重量 |
| G12 | 运维复杂度 | ⚠️ 额外 Docker 服务 + 独立 datastore | ✅ 零额外服务 | ✅ 轻但功能受限 | ❌ 极重 |

---

## verdict

**档位：推荐 · 拆思想自研（inscriptis + difflib）**

**部署形态**：无独立服务，作为 probe 工程内部 Python 模块（`probe/monitor/diff_engine.py`）直接调用，挂 APScheduler 定时任务，结果写 PG `change_events` 表，变更触发 Redis `monitor:change` 事件，下游走反馈闭环（回调源可靠度模块）。

**落矩阵格**：

| 维度 | 内容 |
|------|------|
| 选型决策 | 拆思想自研（inscriptis 2.7.1 + difflib）|
| 排除整机原因 | 红线约束使核心能力 90% 闲置；文件系统孤岛与 PG 数据层冲突；引入独立 Flask 服务增运维面 |
| 条件保留整机场景 | 若 S3+ 出现大量自有 HTML 页面需人工可视化审阅 diff，可作为辅助工具（只读 API 查 diff，不当数据真源）|
| 核心依赖 | `pip install inscriptis` （Apache-2.0 · 342 stars · 2026-02-27 v2.7.1）|
| 补充依赖 | Python stdlib `difflib`（零额外依赖）or `lxml.html.diff`（如需 `<ins>`/`<del>` HTML 标注）|
| 合法源配置强制 | fetch 对象必须在 `allowed_sources` 白名单（PG 表）中注册，probe 调度器启动时校验，无白名单记录的 URL 禁 fetch |
| S2 实施入口 | `probe/monitor/` 新建：`scheduler.py`（APScheduler job）+ `diff_engine.py`（inscriptis+difflib）+ `change_events` PG 表 migration |

**替代备选**：changedetection.io 整机（仅 S3+ 可视化审阅补充角色，非主路径）

---

## 顺手发现

1. **changedetection.io 调度器**：使用自研 `RecheckPriorityQueue`（非 APScheduler / Celery），属于内嵌线程队列，不可复用也不可外部替换。
2. **inscriptis 在 changedetection.io 中的地位**：从 `html_tools.py` 源码结构看，inscriptis 是 changedetection.io 的 HTML→text 真源库；直接使用 inscriptis 等价于获取与整机相同的 diff 质量。
3. **changedetection.io 存储无 PG 支持**：截至 v0.55.7，全部数据存文件系统（orjson），官方无 PG backend roadmap，长期将形成双写孤岛风险。
4. **Playwright 资源跳变**：从纯 HTTP fetch（~100MB）启用 Playwright 后内存推荐翻 20×（~2GB），probe-a 应明确禁用 Playwright 模式（针对 API endpoint 监测无需 JS 渲染）。
5. **urlwatch 实际停更状态**：GitHub 页面显示 967 commits / 49 tags，但最近活跃度信息未能从 fetch 中获取明确时间线，建议 S2 前二次核实最近 commit 日期后再最终排除或保留。

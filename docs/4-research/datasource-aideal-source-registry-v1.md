# probe · AI优惠赛道 源注册表(GitHub-First 采集地基) v1.0

> 日期：2026-06-10 · 性质：I赛道8端口的GitHub源生态深调成果汇总 = 可持续采集的源注册表
> 关系：[分类+GitHub策略](datasource-aideal-track-i-classification-v1.md) 的深调落地·把⚠️候选逐一核实
> 真源：全部经 GitHub API/WebFetch 实查 star/活跃度/license/采集方式·查证2026-06-10
> 铁律：永不代爬·无官方API的源只人工参考不入自动管线

---

## 一、概述

### 核心结论：GitHub-First 验证成功

8端口深调证实 **GitHub 社区众包 awesome-list 是 AI 赛道最优采集层**——覆盖全、时效高、合规零摩擦。关键验证：

| 端口 | 源丰富度 | 关键发现 |
|------|---------|---------|
| I1 LLM API额度 | ✅ 丰富 | mnfst/data.json 可直接机器读取；cheahjs bot每2-3天自动刷新 |
| I2 云credits/扶持 | ✅ 中等 | 国际覆盖完整；国内云完全空白需自建 |
| I3 加速器/孵化 | ⚠️ 稀缺 | yc-oss/api 是唯一自动化源；其余需人工季度更新 |
| I4 AI开发工具 | ✅ 丰富 | 双采法（list发现+repo健康度）可构建多维health_score |
| I5 GPU算力 | ⚠️ 中等 | awesome-list滞后6-12月；gpuhunt是唯一实时价格库 |
| I6 黑客松/竞赛 | ✅ 中等 | mlcontests JSON免认证；Kaggle有官方API |
| I7 开源模型/数据集 | ✅ 极丰富 | HuggingFace Hub API 是结构化金矿；90万+模型可filter |
| I8 情报聚合元层 | ✅ 丰富 | Olshansk hourly刷新；planet-ai.net统一出口 |

### 三条关键发现

1. **中国厂商系统性空白**：I1/I2/I3端口对国内主流厂商（智谱/百炼/Kimi/文心/阿里/腾讯/华为）几乎零覆盖，需自建中国AI资源专项跟踪表。
2. **机器可读差异巨大**：同样是 awesome-list，mnfst 提供 data.json 直接机器读；多数 list 只有 markdown 需解析——采集优先级应按机器可读性排序。
3. **实时价格唯一解**：GPU算力端口(I5)只有 gpuhunt 一个 PyPI 库实现自动化实时采集；所有 awesome-list 在价格维度均严重滞后。

---

## 二、8端口推荐主源

### I1 · LLM API 额度

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| mnfst/awesome-free-llm-apis | 4.9k | 持续 | CC0-1.0 | **data.json机器可读·curl直取**；commit atom订阅 | ✅ 首选·入自动管线 |
| cheahjs/free-llm-api-resources | 23.2k | bot每2-3天 | ⚠️未明确 | atom订阅；14永久+12试用 | ✅ 主源·license待确认后入管线 |
| open-free-llm-api/awesome-freellm-apis | 24 | 今日活跃 | — | atom；依赖freellm.net | ⚠️ 备用·量小需评估 |
| amardeeplakshkar/awesome-free-llm-apis | 50 | 停更3月 | CC0 | atom | ❌ 停更·排除 |
| LiLittleCat/awesome-free-chatgpt | 21k | — | — | — | ❌ 品类不符·镜像站非API |
| alistaitsacle/free-llm-api-keys | — | — | — | — | 🚫 **永久排除**·key倒卖·违ToS |

**I1 缺口**：中国厂商（智谱GLM/百炼/Kimi/文心）无专项awesome-list·采集空白·需自建人工维护表

---

### I2 · 云 credits / 扶持计划

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| dakshshah96/awesome-startup-credits | 2.9k | 持续 | CC0 | markdown解析；Cloud Computing分区 | ✅ 主源 |
| t3-sh/cloudcredits.io | 70 | — | MIT | 网站后端结构化数据；200+条；AI/ML显式分类 | ✅ 主源·API端点待探 |
| doanbactam/awesome-builder-programs | 127 | — | — | markdown；**唯一含AI credits独立分区**(Anthropic/OpenAI/HF) | ✅ 补充·AI分区价值高 |
| ripienaar/free-for-dev | 123k | 持续 | — | GenAI分区；⚠️SPA渲染需Playwright | ⚠️ 辅助·SPA采集成本高 |

**I2 缺口**：国内云完全空白（阿里仅1条·腾讯/华为零覆盖）·需自建「国内云AI扶持计划」人工跟踪表

---

### I3 · 加速器 / 孵化项目

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| yc-oss/api | 184 | **每日Actions刷新** | — | **JSON API直取**：yc-oss.github.io/api/companies/all.json；5956家·61行业·全字段 | ✅ 首选·唯一自动化 |
| ahmadnassri/awesome-accelerators | 27 | 停更 | — | — | ❌ 停更·排除 |
| awesome-incubators | 12 | — | — | — | ❌ 太小·排除 |

**I3 人工季度更新**（无API·代爬禁）：
- Techstars：博客RSS + YC官网batch页(RSSHub路由)
- NVIDIA Inception：4万成员目录不公开·官方公告页人工监测
- Microsoft Founders Hub：官方博客人工
- a16z：无portfolio API·人工

**I3 缺口**：中国本土加速器（创新工场/真格/IDG）无覆盖·NVIDIA Inception目录不公开

---

### I4 · AI 开发工具

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| e2b-dev/awesome-ai-agents | 28.2k | ⚠️停更15月 | — | atom；**权威基线**·停更但存量完整 | ✅ 种子列表·不作实时源 |
| kyrolabs/awesome-agents | 2.4k | **今日活跃** | — | atom；补新框架 | ✅ 实时补充·双采主力 |
| tensorchord/Awesome-LLMOps | 5.8k | 持续 | CC0 | atom；150+工具12子类·**可观测/LLMOps覆盖最广** | ✅ 主源 |
| dangkhoasdc/awesome-vector-database | 353 | **今日活跃** | CC0 | atom | ✅ 向量库专项 |
| ai-boost/awesome-harness-engineering | 1.7k | **今日活跃** | — | atom；工程模式 | ✅ 工程实践信号 |
| wong2/awesome-mcp-servers | 4.1k | 持续 | MIT | atom；400+MCP服务 | ✅ MCP生态监测 |
| Shubhamsaboo/awesome-llm-apps | 114k | 持续 | Apache-2.0 | atom；**非list但star=框架流行度黄金信号** | ✅ 流行度信号层 |

**I4 双采法**：awesome-list 发现工具 → GitHub API 拉各工具 repo（star/release/last_commit）→ 计算 health_score（star趋势 + 近90天commit + release频率）

**I4 缺口**：向量库list star偏低·建议补充 GitHub topic `vector-database` 按star排序直接采；商业编码工具（Cursor/Windsurf）无对应list

---

### I5 · GPU 算力

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| zszazi/Deep-learning-in-cloud | 814 | 2026-03 | MIT | atom；40+供应商+免费层+学术+startup·**覆盖最广** | ✅ 供应商骨架列表 |
| dstackai/gpuhunt | 49 | 2026-05 | MPL-2.0 | **PyPI库**：`pip install gpuhunt` → `gpuhunt.query()`；13商业云实时价格 | ✅ **唯一实时价格源·必入管线** |
| eric-prog/GPU-Grants | 109 | 2025-09 | — | atom；18个学术信贷项目 | ✅ 学术GPU资源补充 |
| binga/cloud-gpus | 470 | 停更5年 | — | — | ❌ 旧GPU型号·排除 |

**I5 缺口**：awesome-list 跟不上 GPU 价格变动（降幅60-80%·list滞后6-12月）·实时价格必须走 gpuhunt + 各供应商官方定价页；学术HPC（NSF ACCESS/NAIRR）无list需官方直链

---

### I6 · 黑客松 / 竞赛

| 主源 repo | star | 最近活跃 | license | 采集方式 | 裁决 |
|-----------|------|---------|---------|---------|------|
| Kaggle/kaggle-api | — | 官方维护 | Apache-2.0 | **官方Python SDK**：`kaggle competitions list --category=featured` + reward字段 + category/sort_by参数；需 kaggle.json 认证 | ✅ 首选·官方权威 |
| mlcontests/mlcontests.github.io | 206 | 持续 | GPL-3.0 | **raw JSON免认证**：competitions.json；341条多平台；tag过滤AI | ✅ 多平台覆盖·免认证便于采集 |
| Hackalist | 490 | ⚠️停更2025-03 | — | JSON API | ⚠️ 停更·仅作历史参考 |

**I6 人工月更**（无API·代爬禁）：
- Devpost：最大黑客松平台·无公开API
- lablab.ai：AI黑客松高质量汇聚·无API

**I6 缺口**：天池（中国最大奖金平台·$103万级奖金）API 待调研·目前不确定是否有公开API；无奖黑客松存在低估风险

---

### I7 · 开源模型 / 数据集

| 主源 | star | 最近活跃 | license | 采集方式 | 裁决 |
|------|------|---------|---------|---------|------|
| HuggingFace Hub API list_models() | 官方 | 持续维护 | HF Terms | **huggingface_hub SDK**：`list_models(filter=["apache-2.0","mit"])` + downloads/likes/parameters字段；需HF_TOKEN；90万+模型 | ✅ **首选·最权威** |
| HuggingFace Hub API list_datasets() | 官方 | 持续维护 | HF Terms | 同SDK；30万数据集 | ✅ 首选 |
| mlabonne/llm-datasets | 4.6k | 2026-04 | — | atom；**微调数据集·license标注率高** | ✅ 微调数据集专项 |
| Hannibal046/Awesome-LLM | 26.9k | ⚠️停更近1年 | — | atom | ⚠️ 停更·作生态全景背景参考 |
| eugeneyan/open-llms | 12.8k | 停更16月 | — | — | ❌ 停更·仅作种子列表 |
| argilla | — | 停更3年 | — | — | ❌ 完全排除 |

**I7 特殊注意**：
- HF API 限速分级：匿名<100req/day；HF_TOKEN<1000；PRO无限制
- LICENSE_COMMERCIAL_WHITELIST 需维护：llama/gemma 等自定义 license 需人工判商用可行性
- 数据集过滤：排除 `cc-by-nc-*` 系列（NC=NonCommercial·不可商用）
- trending 无公开 API·需人工追踪

**I7 缺口**：license 二义性（自定义license的商用判断）；HF trending 无公开 API

---

### I8 · 情报聚合元层（厂商 RSS）

| 主源 repo/URL | star | 最近活跃 | license | 采集方式 | 裁决 |
|---------------|------|---------|---------|---------|------|
| Olshansk/rss-feeds | 598 | **hourly GitHub Actions** | MIT | XML feed列表；31个厂商；含 Anthropic/Mistral/xAI/Perplexity/Meta AI代理feed | ✅ 首选综合聚合 |
| planet-ai.net/rss.xml | — | 持续 | — | 一站式30+厂商统一RSS出口·免费 | ✅ 备用统一出口 |

**I8 厂商官方 RSS（直连·已实查）**：

| 厂商 | RSS URL | 状态 |
|------|---------|------|
| OpenAI | openai.com/news/rss.xml | ✅ 有效 |
| DeepMind | deepmind.google/blog/rss.xml | ✅ 有效 |
| Google AI | blog.google/technology/ai/rss/ | ✅ 有效 |
| HuggingFace | huggingface.co/blog/feed.xml | ✅ 有效 |
| Claude Code | code.claude.com/docs/en/changelog/rss.xml | ✅ 有效 |

**I8 无官方RSS（走Olshansk代理feed）**：

| 厂商 | 状态 | 备注 |
|------|------|------|
| Anthropic | Olshansk代理 | news/engineering/research三路 |
| Mistral | Olshansk代理 | 2026-05加入 |
| xAI | Olshansk代理 | 2026-05加入 |
| Perplexity | Olshansk代理 | 2026-05加入 |
| Meta AI | Olshansk代理 | ⚠️ **feed滞后至2024-09·超1年未更新** |
| Cohere | Olshansk代理 | ⚠️ feed滞后至2025-05 |

**I8 缺口**：Meta AI RSS滞后超1年·实质失效；Cohere滞后；RSSHub Anthropic路由已合并但公共实例403·需自托管Docker

---

## 三、AI源注册表 YAML

> 可订阅清单·每源标注 atom/API/RSS URL·分端口分层
> 直接用：配置到 probe 采集调度器的 source_catalog.yaml

```yaml
# probe · AI优惠赛道 源注册表 v1.0
# 生成：2026-06-10 · 维护：probe-datasource 团队
# 铁律：永不代爬 · source_type: human_only 的源不进自动管线

probe_aideal_sources:

  # ── I1：LLM API 额度 ──────────────────────────────────────
  - id: i1-mnfst-awesome-free-llm
    port: I1
    name: "mnfst/awesome-free-llm-apis"
    tier: primary
    repo_url: "https://github.com/mnfst/awesome-free-llm-apis"
    machine_readable_url: "https://raw.githubusercontent.com/mnfst/awesome-free-llm-apis/main/data.json"
    atom_url: "https://github.com/mnfst/awesome-free-llm-apis/commits/main.atom"
    source_type: atom_and_json_api
    license: CC0-1.0
    stars: 4900
    refresh_cadence: "on_commit"
    notes: "data.json直接机器可读·39家200+模型·首选入自动管线"

  - id: i1-cheahjs-free-llm-resources
    port: I1
    name: "cheahjs/free-llm-api-resources"
    tier: primary
    repo_url: "https://github.com/cheahjs/free-llm-api-resources"
    atom_url: "https://github.com/cheahjs/free-llm-api-resources/commits/main.atom"
    source_type: atom
    license: "⚠️未明确·待确认"
    stars: 23200
    refresh_cadence: "bot_2_3_days"
    notes: "bot自动更新·14永久免费+12试用·license明确后升主力"

  - id: i1-openfreellm-awesome
    port: I1
    name: "open-free-llm-api/awesome-freellm-apis"
    tier: backup
    repo_url: "https://github.com/open-free-llm-api/awesome-freellm-apis"
    atom_url: "https://github.com/open-free-llm-api/awesome-freellm-apis/commits/main.atom"
    source_type: atom
    stars: 24
    refresh_cadence: "on_commit"
    notes: "今日活跃但量小·依赖freellm.net·备用"

  # ── I2：云 credits / 扶持计划 ────────────────────────────
  - id: i2-daksh-startup-credits
    port: I2
    name: "dakshshah96/awesome-startup-credits"
    tier: primary
    repo_url: "https://github.com/dakshshah96/awesome-startup-credits"
    atom_url: "https://github.com/dakshshah96/awesome-startup-credits/commits/main.atom"
    source_type: atom_markdown
    license: CC0
    stars: 2900
    refresh_cadence: "on_commit"
    notes: "Cloud Computing分区·parseMarkdown提取条目"

  - id: i2-cloudcredits-io
    port: I2
    name: "t3-sh/cloudcredits.io"
    tier: primary
    repo_url: "https://github.com/t3-sh/cloudcredits"
    site_url: "https://cloudcredits.io"
    source_type: atom_and_web
    license: MIT
    stars: 70
    refresh_cadence: "on_commit"
    notes: "200+条·AI/ML显式分类·后端结构化数据·API端点待探"

  - id: i2-doanbactam-builder-programs
    port: I2
    name: "doanbactam/awesome-builder-programs"
    tier: primary
    repo_url: "https://github.com/doanbactam/awesome-builder-programs"
    atom_url: "https://github.com/doanbactam/awesome-builder-programs/commits/main.atom"
    source_type: atom_markdown
    stars: 127
    refresh_cadence: "on_commit"
    notes: "唯一含AI credits独立分区(Anthropic/OpenAI/HF)"

  - id: i2-ripienaar-free-for-dev
    port: I2
    name: "ripienaar/free-for-dev"
    tier: supplementary
    repo_url: "https://github.com/ripienaar/free-for-dev"
    atom_url: "https://github.com/ripienaar/free-for-dev/commits/main.atom"
    source_type: atom_spa_web
    stars: 123000
    refresh_cadence: "on_commit"
    notes: "GenAI分区·⚠️SPA渲染需Playwright·采集成本高·辅助用"

  # ── I3：加速器 / 孵化项目 ────────────────────────────────
  - id: i3-ycoss-api
    port: I3
    name: "yc-oss/api (YC Companies)"
    tier: primary
    repo_url: "https://github.com/yc-oss/api"
    api_url: "https://yc-oss.github.io/api/companies/all.json"
    atom_url: "https://github.com/yc-oss/api/commits/main.atom"
    source_type: json_api
    stars: 184
    refresh_cadence: "daily_github_actions"
    notes: "唯一自动化·每日Actions刷新·5956家·61行业·全字段"

  - id: i3-techstars-blog-rss
    port: I3
    name: "Techstars Blog RSS"
    tier: human_monitor
    rss_url: "https://www.techstars.com/blog/rss"
    source_type: rss_human
    refresh_cadence: "monthly_manual"
    notes: "公告监测·无法自动结构化·人工月更"

  # ── I4：AI 开发工具 ──────────────────────────────────────
  - id: i4-e2b-awesome-ai-agents
    port: I4
    name: "e2b-dev/awesome-ai-agents"
    tier: seed_list
    repo_url: "https://github.com/e2b-dev/awesome-ai-agents"
    atom_url: "https://github.com/e2b-dev/awesome-ai-agents/commits/main.atom"
    source_type: atom_markdown
    stars: 28200
    refresh_cadence: "on_commit"
    notes: "⚠️停更15月·权威存量基线·作种子列表不作实时源"

  - id: i4-kyrolabs-awesome-agents
    port: I4
    name: "kyrolabs/awesome-agents"
    tier: primary
    repo_url: "https://github.com/kyrolabs/awesome-agents"
    atom_url: "https://github.com/kyrolabs/awesome-agents/commits/main.atom"
    source_type: atom_markdown
    stars: 2400
    refresh_cadence: "on_commit"
    notes: "今日活跃·补新框架·双采实时主力"

  - id: i4-tensorchord-awesome-llmops
    port: I4
    name: "tensorchord/Awesome-LLMOps"
    tier: primary
    repo_url: "https://github.com/tensorchord/Awesome-LLMOps"
    atom_url: "https://github.com/tensorchord/Awesome-LLMOps/commits/main.atom"
    source_type: atom_markdown
    license: CC0
    stars: 5800
    refresh_cadence: "on_commit"
    notes: "150+工具12子类·可观测/LLMOps覆盖最广"

  - id: i4-dangkhoasdc-vector-database
    port: I4
    name: "dangkhoasdc/awesome-vector-database"
    tier: primary
    repo_url: "https://github.com/dangkhoasdc/awesome-vector-database"
    atom_url: "https://github.com/dangkhoasdc/awesome-vector-database/commits/main.atom"
    source_type: atom_markdown
    license: CC0
    stars: 353
    refresh_cadence: "on_commit"
    notes: "今日活跃·向量库专项"

  - id: i4-aiboost-harness-engineering
    port: I4
    name: "ai-boost/awesome-harness-engineering"
    tier: primary
    repo_url: "https://github.com/ai-boost/awesome-harness-engineering"
    atom_url: "https://github.com/ai-boost/awesome-harness-engineering/commits/main.atom"
    source_type: atom_markdown
    stars: 1700
    refresh_cadence: "on_commit"
    notes: "今日活跃·工程模式"

  - id: i4-wong2-awesome-mcp-servers
    port: I4
    name: "wong2/awesome-mcp-servers"
    tier: primary
    repo_url: "https://github.com/wong2/awesome-mcp-servers"
    atom_url: "https://github.com/wong2/awesome-mcp-servers/commits/main.atom"
    source_type: atom_markdown
    license: MIT
    stars: 4100
    refresh_cadence: "on_commit"
    notes: "400+MCP服务·MCP生态监测专项"

  - id: i4-shubhamsaboo-awesome-llm-apps
    port: I4
    name: "Shubhamsaboo/awesome-llm-apps (流行度信号)"
    tier: signal
    repo_url: "https://github.com/Shubhamsaboo/awesome-llm-apps"
    atom_url: "https://github.com/Shubhamsaboo/awesome-llm-apps/commits/main.atom"
    source_type: atom_github_api
    license: Apache-2.0
    stars: 114000
    refresh_cadence: "on_commit"
    notes: "非list·star趋势=框架流行度黄金信号·配合GitHub API health_score"

  - id: i4-github-topic-vector-database
    port: I4
    name: "GitHub Topic: vector-database (补充采集)"
    tier: supplementary
    api_url: "https://api.github.com/search/repositories?q=topic:vector-database&sort=stars&order=desc"
    source_type: github_search_api
    refresh_cadence: "weekly"
    notes: "向量库list star低·直接topic搜索按star补充覆盖"

  # ── I5：GPU 算力 ─────────────────────────────────────────
  - id: i5-zszazi-deep-learning-cloud
    port: I5
    name: "zszazi/Deep-learning-in-cloud"
    tier: primary
    repo_url: "https://github.com/zszazi/Deep-learning-in-cloud"
    atom_url: "https://github.com/zszazi/Deep-learning-in-cloud/commits/main.atom"
    source_type: atom_markdown
    license: MIT
    stars: 814
    refresh_cadence: "on_commit"
    notes: "40+供应商+免费层+学术+startup·骨架列表·2026-03活跃"

  - id: i5-dstackai-gpuhunt
    port: I5
    name: "dstackai/gpuhunt (实时价格)"
    tier: primary
    repo_url: "https://github.com/dstackai/gpuhunt"
    pypi_package: "gpuhunt"
    api_usage: "from gpuhunt import query; query()"
    atom_url: "https://github.com/dstackai/gpuhunt/commits/main.atom"
    source_type: python_library
    license: MPL-2.0
    stars: 49
    refresh_cadence: "continuous"
    notes: "⭐唯一自动化实时GPU价格·13商业云·必入管线·2026-05更新"

  - id: i5-ericprog-gpu-grants
    port: I5
    name: "eric-prog/GPU-Grants"
    tier: supplementary
    repo_url: "https://github.com/eric-prog/GPU-Grants"
    atom_url: "https://github.com/eric-prog/GPU-Grants/commits/main.atom"
    source_type: atom_markdown
    stars: 109
    refresh_cadence: "on_commit"
    notes: "18个学术信贷项目·2025-09活跃"

  # ── I6：黑客松 / 竞赛 ───────────────────────────────────
  - id: i6-kaggle-api
    port: I6
    name: "Kaggle API (官方)"
    tier: primary
    repo_url: "https://github.com/Kaggle/kaggle-api"
    api_usage: "kaggle competitions list --category=featured --sort-by=prize"
    source_type: official_api
    license: Apache-2.0
    auth_required: true
    auth_method: "~/.kaggle/kaggle.json"
    refresh_cadence: "on_demand"
    notes: "官方SDK·reward/category/sort_by字段完整·需认证"

  - id: i6-mlcontests-competitions
    port: I6
    name: "mlcontests/mlcontests.github.io"
    tier: primary
    repo_url: "https://github.com/mlcontests/mlcontests.github.io"
    api_url: "https://raw.githubusercontent.com/mlcontests/mlcontests.github.io/main/competitions.json"
    atom_url: "https://github.com/mlcontests/mlcontests.github.io/commits/main.atom"
    source_type: raw_json
    license: GPL-3.0
    stars: 206
    refresh_cadence: "on_commit"
    notes: "341条多平台·免认证·tag过滤AI·首选无认证多平台源"

  - id: i6-hackalist
    port: I6
    name: "Hackalist"
    tier: deprecated
    stars: 490
    source_type: json_api
    notes: "⚠️停更2025-03·仅作历史参考·不入自动管线"

  # ── I7：开源模型 / 数据集 ────────────────────────────────
  - id: i7-hf-hub-models
    port: I7
    name: "HuggingFace Hub API - Models"
    tier: primary
    api_usage: |
      from huggingface_hub import list_models
      models = list_models(
        filter=["apache-2.0", "mit", "cc-by-4.0"],
        sort="downloads",
        direction=-1,
        limit=1000
      )
    source_type: official_api
    auth_required: true
    auth_method: "HF_TOKEN env var"
    stars: "N/A (官方API)"
    refresh_cadence: "daily"
    notes: "90万+模型·license字段结构化·必须维护LICENSE_COMMERCIAL_WHITELIST"

  - id: i7-hf-hub-datasets
    port: I7
    name: "HuggingFace Hub API - Datasets"
    tier: primary
    api_usage: |
      from huggingface_hub import list_datasets
      datasets = list_datasets(
        filter=["apache-2.0", "mit", "cc-by-4.0"],
        sort="downloads",
        direction=-1
      )
    source_type: official_api
    auth_required: true
    auth_method: "HF_TOKEN env var"
    stars: "N/A (官方API)"
    refresh_cadence: "daily"
    notes: "30万数据集·排除cc-by-nc-*·license二义性自定义license需人工判断"

  - id: i7-mlabonne-llm-datasets
    port: I7
    name: "mlabonne/llm-datasets"
    tier: supplementary
    repo_url: "https://github.com/mlabonne/llm-datasets"
    atom_url: "https://github.com/mlabonne/llm-datasets/commits/main.atom"
    source_type: atom_markdown
    stars: 4600
    refresh_cadence: "on_commit"
    notes: "微调数据集专项·license标注率高·2026-04活跃"

  # ── I8：情报聚合元层（厂商 RSS）────────────────────────────
  - id: i8-olshansk-rss-feeds
    port: I8
    name: "Olshansk/rss-feeds"
    tier: primary
    repo_url: "https://github.com/Olshansk/rss-feeds"
    atom_url: "https://github.com/Olshansk/rss-feeds/commits/main.atom"
    feeds_base: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main"
    source_type: atom_and_rss_proxy
    license: MIT
    stars: 598
    refresh_cadence: "hourly_github_actions"
    vendor_feeds:
      - vendor: Anthropic
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_news.xml"
      - vendor: Anthropic Engineering
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_engineering.xml"
      - vendor: Anthropic Research
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml"
      - vendor: Mistral
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_mistral_news.xml"
      - vendor: xAI
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_xai_news.xml"
      - vendor: Perplexity
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_perplexity_blog.xml"
      - vendor: Meta AI
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_meta_ai.xml"
        warning: "⚠️ 滞后至2024-09·超1年未更新·内容可能陈旧"
      - vendor: Cohere
        feed_url: "https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_cohere_blog.xml"
        warning: "⚠️ 滞后至2025-05"
    notes: "hourly自动刷新·31个厂商·首选综合聚合层"

  - id: i8-planet-ai-unified
    port: I8
    name: "planet-ai.net RSS (统一出口)"
    tier: backup
    rss_url: "https://planet-ai.net/rss.xml"
    source_type: rss
    refresh_cadence: "continuous"
    notes: "30+厂商统一出口·免费·Olshansk失效时备用"

  # 厂商官方直连 RSS
  - id: i8-openai-news
    port: I8
    name: "OpenAI News RSS"
    tier: direct
    rss_url: "https://openai.com/news/rss.xml"
    source_type: rss
    refresh_cadence: "on_publish"
    notes: "官方直连·已实查有效"

  - id: i8-deepmind-blog
    port: I8
    name: "DeepMind Blog RSS"
    tier: direct
    rss_url: "https://deepmind.google/blog/rss.xml"
    source_type: rss
    refresh_cadence: "on_publish"
    notes: "官方直连·已实查有效"

  - id: i8-googleai-blog
    port: I8
    name: "Google AI Blog RSS"
    tier: direct
    rss_url: "https://blog.google/technology/ai/rss/"
    source_type: rss
    refresh_cadence: "on_publish"
    notes: "官方直连·已实查有效"

  - id: i8-huggingface-blog
    port: I8
    name: "HuggingFace Blog RSS"
    tier: direct
    rss_url: "https://huggingface.co/blog/feed.xml"
    source_type: rss
    refresh_cadence: "on_publish"
    notes: "官方直连·已实查有效"

  - id: i8-claudecode-changelog
    port: I8
    name: "Claude Code Changelog RSS"
    tier: direct
    rss_url: "https://code.claude.com/docs/en/changelog/rss.xml"
    source_type: rss
    refresh_cadence: "on_publish"
    notes: "官方直连·已实查有效"

  # 学术/研究层
  - id: i8-arxiv-llm-cs-cl
    port: I8
    name: "arXiv cs.CL RSS"
    tier: research
    rss_url: "https://arxiv.org/rss/cs.CL"
    source_type: rss
    refresh_cadence: "daily"
    notes: "计算语言学·LLM学术论文日更"

  - id: i8-arxiv-cs-ai
    port: I8
    name: "arXiv cs.AI RSS"
    tier: research
    rss_url: "https://arxiv.org/rss/cs.AI"
    source_type: rss
    refresh_cadence: "daily"
    notes: "AI综合·学术论文日更"

  - id: i8-hn-ai-rss
    port: I8
    name: "Hacker News AI 关键词 RSS"
    tier: community
    rss_url: "https://hnrss.org/newest?q=AI+LLM+GPT&comments=10"
    source_type: rss
    refresh_cadence: "continuous"
    notes: "社区信号·hnrss.org服务"

  - id: i8-producthunt-ai
    port: I8
    name: "ProductHunt AI 分类 RSS"
    tier: community
    rss_url: "https://www.producthunt.com/feed?category=artificial-intelligence"
    source_type: rss
    refresh_cadence: "daily"
    notes: "AI新产品发布信号"
```

---

## 四、采集架构

四层采集管线，从外到内按信号类型分工：

### ① awesome-list commit atom 监测

**原理**：每个 GitHub repo 均有 `commits/<branch>.atom` 端点，无需认证，变更即推送。

```
监测端点格式：https://github.com/<owner>/<repo>/commits/main.atom
轮询策略：对 tier:primary 的 awesome-list 每小时拉一次 atom
增量判断：对比 <id> 字段（commit SHA），新条目触发解析
解析目标：从 markdown diff 中提取新增行（以 - 或 * 开头的 list item）
```

**适用源**：I1/I2/I4/I5/I6 中的 markdown-based awesome-list

### ② repo 元数据 GitHub API 双采

**用途**：I4 双采法中计算工具 repo 的 health_score

```python
# GitHub Search API + repo 元数据
GET https://api.github.com/repos/<owner>/<repo>
# 关键字段
{
  "stargazers_count": int,          # star 总数
  "pushed_at": "ISO8601",           # 最近 push 时间
  "updated_at": "ISO8601",
  "open_issues_count": int          # 活跃度信号
}

# Releases API
GET https://api.github.com/repos/<owner>/<repo>/releases?per_page=5
# 计算 release_velocity = 近5次release时间跨度

# health_score 公式
health_score = (
  log(stars + 1) * 0.3 +
  (1 if days_since_push < 90 else 0) * 0.4 +
  release_velocity_score * 0.3
)
```

**认证**：需 GitHub PAT，限速 5000 req/h（认证）vs 60 req/h（匿名）

### ③ 厂商官方 RSS 直采

**轮询策略**：每 30 分钟拉一次已知有效的官方 RSS（I8 direct tier）

```
优先级：官方直连 > Olshansk代理 > planet-ai.net统一出口
去重：以 <guid>/<link> 为主键，入库前 dedup
过滤：含 ["free", "credit", "grant", "open source", "launch"] 关键词的条目优先推送
```

### ④ HuggingFace Hub API + Kaggle API

**HF Hub**：

```python
from huggingface_hub import HfApi
api = HfApi(token=os.environ["HF_TOKEN"])

# 商用友好模型（每日增量）
new_models = api.list_models(
    filter=["apache-2.0", "mit", "cc-by-4.0"],
    sort="lastModified",
    direction=-1,
    limit=100
)

# 商用许可白名单（需维护，部分license需人工判断）
LICENSE_COMMERCIAL_WHITELIST = [
    "apache-2.0", "mit", "cc-by-4.0", "bsd-2-clause", "bsd-3-clause",
    "openrail", "creativeml-openrail-m",
    # 以下需逐案人工判断
    # "llama3", "gemma", "qwen" -- 自定义license
]
LICENSE_COMMERCIAL_BLACKLIST = [
    "cc-by-nc-4.0", "cc-by-nc-sa-4.0",  # NonCommercial
    "gpl-3.0",                             # Copyleft
]
```

**Kaggle API**：

```bash
# 安装：pip install kaggle
# 认证：~/.kaggle/kaggle.json
kaggle competitions list \
  --category featured \
  --sort-by prize \
  --page-size 50 \
  --csv
```

### ⑤ 自托管 RSSHub（Anthropic 路由已合并）

**用途**：Anthropic、部分无官方RSS的厂商

```bash
# Docker 自托管
docker run -d \
  -p 1200:1200 \
  -e CACHE_EXPIRE=600 \
  diygod/rsshub:latest

# Anthropic 路由（已合并入 RSSHub mainline）
GET http://localhost:1200/anthropic/blog
GET http://localhost:1200/anthropic/news

# 注意：公共实例 rsshub.app 对部分路由返回 403，必须自托管
```

---

## 五、跨端口缺口总览

| 缺口类型 | 涉及端口 | 具体问题 | 建议处置 |
|---------|---------|---------|---------|
| **中国厂商系统空白** | I1/I2/I3 | 智谱GLM/百炼/Kimi/文心/阿里/腾讯/华为无专项awesome-list覆盖 | 自建「中国AI资源专项跟踪表」·人工季度更新 |
| **国内云credits空白** | I2 | 阿里仅1条·腾讯/华为零覆盖 | 自建国内云AI扶持计划人工表·跟踪官方博客 |
| **中国加速器无覆盖** | I3 | 创新工场/真格/IDG无GitHub源 | 人工追踪官网公告·季度更新 |
| **GPU价格list严重滞后** | I5 | awesome-list跟不上GPU价格变动（降60-80%·滞后6-12月） | 生产必走gpuhunt实时库+官方定价页·禁用list价格 |
| **Meta AI RSS失效** | I8 | feed滞后至2024-09·超1年·实质失效 | 改走Meta AI官方博客Playwright采集或人工月更 |
| **Cohere RSS滞后** | I8 | 滞后至2025-05 | 短期接受·配合Olshansk代理观察 |
| **RSSHub公共实例被block** | I8 | rsshub.app 403 | 自托管Docker·见§四⑤ |
| **天池API待调** | I6 | 中国最大奖金竞赛平台·API可用性未知 | 列入下轮调研·探测阿里云dataworks/tianchi API |
| **HF trending无公开API** | I7 | trending榜单无官方API端点 | 人工追踪·每周人工登记Top10 |
| **license二义性** | I7 | llama/gemma自定义license商用需人工判断 | 维护LICENSE_COMMERCIAL_WHITELIST·人工审核队列 |
| **商业编码工具无list** | I4 | Cursor/Windsurf/Copilot等商业工具无awesome-list | 直接GitHub topic搜索 + 官方博客RSS |
| **NVIDIA Inception目录不公开** | I3 | 4万成员目录无法采集 | 仅监测官方公告·人工季度盘点 |

---

## 六、永久排除

以下源永久排除，不入自动管线，不入人工参考列表：

| 排除源 | 排除原因 | 分类 |
|--------|---------|------|
| **alistaitsacle/free-llm-api-keys** | key倒卖·严重违反厂商ToS·法律风险 | 🚫 合规红线 |
| **任何代理/中转平台收集的API key** | 来源不明·使用构成违规·账号封禁风险 | 🚫 合规红线 |
| **binga/cloud-gpus** | 停更5年·旧GPU型号·无参考价值 | ❌ 过时数据 |
| **eugeneyan/open-llms** | 停更16月·模型列表严重过时 | ❌ 过时数据（仅种子列表场景人工参考） |
| **ahmadnassri/awesome-accelerators** | 停更·内容过时 | ❌ 过时数据 |
| **awesome-incubators (12★)** | star极低·无维护 | ❌ 不可信 |
| **argilla** | 停更3年 | ❌ 过时数据 |
| **Devpost（代爬）** | 无公开API·代爬违TOS | ⚠️ 人工参考·不入自动管线 |
| **lablab.ai（代爬）** | 无公开API | ⚠️ 人工月更·不入自动管线 |
| **任何需逆向JS/XHR拦截的站点** | 代爬·probe铁律禁止 | 🚫 永久排除 |

---

> 维护说明：本注册表随深调进行版本递进（v1.0 = 2026-06-10首版）·
> 每次新增源需经过「star/活跃度/license/采集方式」四项实查才可升 tier:primary·
> ⚠️标记源须在下轮深调前消除或降级

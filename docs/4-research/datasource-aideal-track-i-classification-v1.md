# probe · AI优惠专项 I赛道 数据分类 + GitHub-First 采集策略 v1.0

> 日期：2026-06-10 · 性质：第九赛道(AI/Agent资源优惠情报)的**分类底座 + 数据源头策略**(先分类→定源头→再深调)
> 关系：本文是分类与采集框架；[datasource-aideal-track-i-v1](datasource-aideal-track-i-v1.md) 是首轮内容调研(按本分类归位)；[metafoclaw自用手册](metafoclaw-ai-resource-playbook-v1.md) 是自用应用
> 上游：[赛道注册表架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) I-aideal · [feasibility-v1 §1 GitHub 6范式](probe-github-datasource-feasibility-v1.md)

---

## 一、为什么 AI 赛道必须 GitHub-First（与其他赛道的根本不同）

| 维度 | 其他赛道(电商/金融/本地生活) | **AI 赛道** |
|------|------------------------------|------------|
| 数据源头 | 各平台官方 API / 网页 | **GitHub 社区众包 awesome-list** |
| 维护方式 | 平台单方控制 | 开发者社区 PR + bot 自动更新 |
| 时效 | 看平台更新 | **bot 每 5-10 天自动刷新**(cheahjs/free-llm-api-resources) |
| 合规 | 多需资质/付费/防代爬 | GitHub API 官方 + commit RSS·**完全合规不代爬** |
| 覆盖 | 单平台 | 一个 list 横扫几十家厂商 |
| 成本 | 多付费 | **全免费** |

**四条 GitHub-First 理由：**
1. **社区原生**：AI 免费资源由开发者在 GitHub 用 awesome-list 持续众包维护，是该领域**唯一权威、最全、最新**的聚合层——人工聚合站(joinsecret/getaiperks)又贵又慢又无 API。
2. **自动化友好**：每个 list 都有 `commits/*.atom` 可订阅，GitHub API 官方拉 star/release/活跃度，**零代爬**，契合 probe 铁律。
3. **一鱼三吃**：一个 awesome-list 同时是「免费额度清单」+「新资源发现」+「变更监测」三重源。
4. **开源资产本体**：AI 模型/框架/工具/数据集本身就托管在 GitHub/HuggingFace，star/release/issue 活跃度即**健康度信号**(对接 D2 技术情报域能力)。

> 一句话：其他赛道 probe 是「采油」，AI 赛道 probe 是**「在社区已经炼好的油库里接管道」**——GitHub awesome-list 就是炼好的油库。

---

## 二、AI 赛道数据分类（8 品类端口 × GitHub 金矿源头）

> 三级结构：**端口(品类)→ 分类(细分)→ 条目(具体优惠/资源)**。每端口标注其 GitHub 核心源头。✅=ai-8路已实查确认 · ⚠️=候选待深调核实。

| # | 端口(品类) | 分类(细分) | GitHub 金矿源头 |
|---|-----------|-----------|----------------|
| **I1** | **LLM/模型 API 额度** | 永久免费层 / 新用户赠送 / 试用 credits | ✅ `cheahjs/free-llm-api-resources`(23.2k·bot自动) · ⚠️`amardeeplakshkar/awesome-free-llm-apis` · ✅`LiLittleCat/awesome-free-chatgpt`(已降温) |
| **I2** | **云厂商 AI credits/扶持** | 海外云startup credits / 国内云额度 | ✅`ripienaar/free-for-dev`(123k·GenAI分区) · ⚠️`awesome-startup-credits` 类 |
| **I3** | **创业加速器/孵化** | 加速器(YC/a16z) / 厂商扶持(Inception/Founders Hub) | ⚠️聚合较少·官方为主 + `creditforstartups` 类清单待核实 |
| **I4** | **Agent/AI开发工具免费层** | Agent框架 / 向量库 / 编码工具 / 可观测 | ⚠️`kyrolabs/awesome-langchain` · `e2b-dev/awesome-ai-agents` · `steven2358/awesome-generative-ai` |
| **I5** | **GPU/算力资源** | 免费GPU / 算力券 / 学术算力 | ⚠️`zszazi/Deep-Learning-Cloud-Providers` · `binga/cloud-gpus` 类待核实 |
| **I6** | **黑客松/竞赛/活动** | 奖金竞赛 / 厂商黑客松(送API额度) | 官方API：Kaggle CLI ✅ · Devpost(无API·人工) · ⚠️awesome-hackathon 类 |
| **I7** | **开源模型/数据集/资源** | 模型权重 / 数据集 / 微调资源 | HuggingFace Hub(模型/数据集) · ⚠️`Hannibal046/Awesome-LLM` · `eugeneyan/open-llms` |
| **I8** | **情报聚合/监测源(元层)** | awesome-list本身 / 厂商RSS | ✅`ripienaar/free-for-dev` · ✅`cheahjs/free-llm-api-resources` · ✅`Olshansk/rss-feeds`(599·厂商RSS每小时) |

> 交叉轴：① 提供方域(海外/国内·云/模型厂/工具商/社区) ② 优惠类型(永久免费/限时/需申请/竞赛) ③ 面向(开发者/创业者/学生/企业) ④ 对 metafoclaw 自用价值。

---

## 三、GitHub-First 采集范式（对接 feasibility §1 GitHub 6 范式）

| 范式 | 用法 | 落点 |
|------|------|------|
| **① awesome-list commit 监测** | 订阅每端口金矿 list 的 `commits/*.atom` → diff 抽变更行 → 入队列 | **主力**·I1/I2/I8 |
| **② repo 元数据** | GitHub API 拉 star/release/issue 活跃度 → 工具/框架健康度 | I4/I7 工具健康 |
| **③ GitHub Topics/Trending** | 按 topic(`llm`/`ai-agents`/`free-tier`) + trending 发现**新**资源 | 新资源发现 |
| **④ HuggingFace Hub API** | 模型/数据集元数据(下载量/likes/license) | I7 开源模型 |
| **⑤ GitHub-hosted RSS** | `Olshansk/rss-feeds` 生成的厂商官方 feed(Anthropic等无官方RSS的) | I8 厂商公告 |
| **⑥ 官方 API 补充** | Kaggle CLI(竞赛) + HN Algolia + Reddit PRAW + Product Hunt(非GitHub但补社区首发) | I6/社区信号 |

**采集中枢设计**：probe 维护一张「AI 源注册表」——每端口登记其权威 awesome-list(repo + atom URL + 维护活跃度 + 覆盖内容)，统一订阅 commit，bot 更新即触发 diff 入 probe 事件队列。**这就是 AI 赛道的「数据采集地」**。

---

## 四、深度调研安排（基于分类 · GitHub 优先 · 下一步）

> 上轮已扫「优惠内容」；本轮深调焦点不同 = **系统摸透每个端口的 GitHub 源头生态**(有哪些权威 awesome-list、star/活跃度、覆盖度、采集方式)，建成可持续采集的源注册表。

| 路 | 端口 | 深调任务 |
|----|------|---------|
| 深-I1 | LLM API额度 | 摸透 free-llm-api-resources 生态 + 同类 list 横评 + 结构化 schema |
| 深-I2 | 云credits/扶持 | free-for-dev GenAI分区 + startup-credits 类 list 核实 |
| 深-I3 | 加速器/孵化 | 加速器/厂商扶持的 GitHub/官方源(聚合最弱·需补) |
| 深-I4 | AI开发工具 | awesome-langchain/awesome-ai-agents 等核实 + repo健康度采集法 |
| 深-I5 | GPU算力 | 免费GPU清单类 list 核实 + 时效性评估 |
| 深-I6 | 黑客松/竞赛 | Kaggle/Devpost API + 黑客松聚合 list |
| 深-I7 | 开源模型/数据集 | HuggingFace Hub API + Awesome-LLM 类 + open-llms |
| 深-I8 | 情报聚合源(元层) | 把各端口 awesome-list 汇成 probe AI源注册表 + 订阅方案 |

**每路产出**：该端口的「GitHub 源生态清单」(repo + star + atom URL + 活跃度 + 覆盖 + 四闸审核) → 汇入 probe AI 源注册表。

> ✅ **深调已完成(2026-06-10)**：8 端口 GitHub-First 深调 + 源注册表落地 → **[datasource-aideal-source-registry-v1](datasource-aideal-source-registry-v1.md)**(35 源·YAML 订阅清单·五路采集架构)。⚠️ 候选已逐一核实，关键落地：I1 `mnfst/awesome-free-llm-apis`(有 data.json 机器可读) · I3 `yc-oss/api`(每日自动 JSON·证实加速器品类聚合最弱) · I5 `dstackai/gpuhunt`(唯一实时价格自动化) · I7 HuggingFace Hub API(license 结构化 filter) · I8 厂商官方 RSS 清单 + Olshansk 代理。永久排除 `alistaitsacle/free-llm-api-keys`(key 倒卖违 ToS)。

---

## 五、与已有产物的关系

- 本文 = I 赛道**分类与源头框架**(方法论)
- `datasource-aideal-track-i-v1` = 首轮**优惠内容**调研(按本分类 8 端口可重新归位)
- `metafoclaw-ai-resource-playbook` = 自用降本应用
- 下一步深调产出 = **probe AI 源注册表**(GitHub awesome-list 订阅清单)，是 I 赛道可持续采集的地基

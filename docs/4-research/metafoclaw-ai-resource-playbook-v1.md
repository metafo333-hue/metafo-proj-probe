# metafoclaw · AI资源自用降本行动手册 v1.0

> 日期：2026-06-10  
> 性质：运营降本行动清单（源于probe第九赛道AI优惠调研）  
> 用途：把各大厂AI免费额度/创业扶持转成metafoclaw可立即执行的领取/申请清单  
> ⚠️ 额度以官方当前页面为准，查证于2026-06-10，时效随时变动请复核

---

## 一、🟢 零授权立即领（本周可领 · 无需公司资质 · 无需付费）

> 优先做这批：注册即得，最快今天生效，直接接入LiteLLM路由。

| 资源 | 价值 | 领取入口 | 时效 | metafoclaw用途 |
|------|------|---------|------|---------------|
| **火山方舟协作奖励计划** | 每日200万tokens循环永续 | https://www.volcengine.com/docs/82379/1391869 | 循环每日刷新 | LiteLLM加一路Doubao；probe多赛道并发主力 |
| **智谱BigModel** | GLM-4.7-Flash永久免费 + 新用户2000万tokens永久 | https://bigmodel.cn | 永久（2000万一次性） | 永久备用推理通道；embedding免费跑知识库 |
| **阿里云百炼** | 新用户每模型100万，合计约7000万tokens | https://bailian.console.aliyun.com | 90天 | ⚠️90天用尽，优先跑probe数据采集/批量任务 |
| **硅基流动** | 2000万tokens + ¥14余额 + bge-m3 embedding永久免费 | https://siliconflow.cn | tokens有期限；bge-m3永久 | OpenAI兼容直接接LiteLLM；embedding零成本本地知识库 |
| **腾讯混元Lite 256K** | 永久免费（256K超长上下文） | https://cloud.tencent.com/product/hunyuan | 永久 | 超长文档处理；probe大段内容整合 |
| **百度ERNIE-Speed** | 永久免费 | https://cloud.baidu.com/product/wenxinworkshop | 永久 | 中文场景兜底；MetaLearn中文问答 |
| **讯飞星火Lite** | 永久免费 + 新用户200万tokens | https://www.xfyun.cn/doc/spark | 永久（200万一次性） | 语音+文本备用通道 |
| **Google Gemini免费层** | Flash 1500 RPD（每日1500请求）永久 | https://aistudio.google.com | 永久 | ⚠️内容可能用于训练，禁止传入用户敏感数据；MetaAsk英文问答 |
| **Groq** | 永久免费（最快推理，Llama/Mixtral） | https://console.groq.com | 永久 | 低延迟场景；probe快速赛道 |
| **Mistral Devstral** | 免费层（代码能力强） | https://console.mistral.ai | ⚠️复核当前策略 | 代码生成辅助；MetaDesign规格引擎 |
| **Cohere** | 每月1000次API免费 | https://dashboard.cohere.com | 每月重置 | 文本分类/rerank；probe验证层L3 |
| **Oracle Cloud Always Free** | 永久4核24GB ARM实例（可运行7B量化模型） | https://oracle.com/cloud/free | 永久 | ⚠️注册需信用卡验证（R4授权）；自托管小模型推理；备份节点 |
| **Cloudflare Workers AI** | 每日10,000 Neurons永久免费 | https://developers.cloudflare.com/workers-ai | 永久每日 | 边缘推理；CDN层快速响应；全球低延迟入口 |

### 免费GPU算力（批量任务 / 模型微调）

| 平台 | 额度 | 时效 | 用途 |
|------|------|------|------|
| Kaggle | 30小时/周 T4/P100 | 每周重置 · 最稳定 | probe模型评估；embedding批处理 |
| Google Colab | T4随机可用 | 按session | 快速实验；脚本调试 |
| 百度AI Studio | 48小时基础 + 邀请裂变最高120小时 | 季度性 | 中文模型微调；数据处理 |
| 阿里PAI-DSW | 750计算时（约3个月） | 3个月 | ⚠️需领取激活；批量向量化任务 |

### 立即执行步骤（今天可做）

1. 注册火山方舟账号 → 加入协作奖励计划 → 获取API Key → 加入LiteLLM `config.yaml`
2. 智谱 + 硅基流动 + 阿里百炼 各注册领额度 → 统一接入LiteLLM fallback路由
3. Groq注册获API Key → 加`groq/llama3-70b-8192`路由作低延迟通道
4. Google AI Studio → 建API Key → 接Gemini Flash（注意数据隔离）
5. 在LiteLLM `router_settings` 按成本从低到高排序：国内免费层 → Google/Groq免费 → 付费通道

---

## 二、🟡 创业扶持申请（需公司主体 · 高价值 · 按优先级×可行性排序）

> 主体：绵阳零元电子商务有限公司  
> ⚠️ 使用公司营业执照/邮箱申请走R4验证；申请企业邮箱走R8授权

### 优先级矩阵

| 计划 | 价值 | 申请门槛 | 可行性 | 建议时间 | 杠杆说明 |
|------|------|---------|--------|---------|---------|
| **NVIDIA Inception** ★ | 免费会员 → 解锁AWS Portfolio $100k + Nebius $150k | 成立≤10年 + 有AI产品 + 公司官网 | 🟢 高（零费用·自助） | 本周 | 最高杠杆：加入本身免费，解锁下游两个大额奖励 |
| **Microsoft Founders Hub** ★ | 起步$5k → 最高$150k Azure + $2,500 OpenAI credits | 无需融资·自助申请 | 🟢 高（3日审核） | 本周 | 立即可得$5k，Azure覆盖ufo2/tencent-sh迁移备用 |
| **AWS Activate Founders** | $1,000 AWS credits | 需官网+AI产品描述 | 🟢 高（自助） | 本周（先于Portfolio） | 先拿Founders资格 → NVIDIA Inception加持后升Portfolio $100k |
| **Google for Startups AI Track** | 最高$350,000 GCP credits | AI-first产品 + 需加速器/合作伙伴推荐 + Gemini核心 | 🟡 中（需推荐信） | 1-2个月（准备材料） | $350k是最大单项；需先有加速器背书 |
| **Anthropic Startup Program** | $25,000 Claude credits | 需VC融资 | 🔴 当前不可行 | 暂缓 | ⚠️条款明确排除中国大陆注册主体，需香港/国际实体 |
| **a16z Speedrun** | $1M现金 + $5M credits | 顶级投资人筛选 | 🔴 极难（录取率<0.4%） | 积累后再看 | SR008下批；现阶段准备材料为主 |
| **Stripe Atlas** | $500建公司 → $20k SaaS权益包 | 美国法人实体 | 🔴 需美国实体 | 暂缓 | ⚠️绵阳主体不适用；如设海外实体可跟进 |

### 各项申请要点

#### NVIDIA Inception（本周最优先）
- 申请地址：https://nvidia.com/en-us/startups
- 必备：公司官网（metafoclaw.com ✅）+ 产品描述（AI工具平台 ✅）+ 成立年份
- 审核：7-10个工作日
- 获批后立即：①申请AWS Activate Portfolio（$100k） ②申请Nebius AI（$150k GPU credits）
- 材料准备：公司简介100字英文 + AI用途描述（probe情报引擎/MetaAsk/MetaDesign）

#### Microsoft Founders Hub（本周可做）
- 申请地址：https://microsoft.com/en-us/startups
- 自助提交：公司名 + 产品网址 + AI用途描述
- 3日内获$5,000 Azure起步额度，后续可升级
- Azure用途：CDN / 备份存储 / 容器服务替代部分ufo2负载

#### AWS Activate Founders → Portfolio路径
- Founders申请：https://aws.amazon.com/activate
- 先拿$1,000 Founders额度（自助即可）
- NVIDIA Inception获批后 → 用Inception会员资格申请AWS Portfolio（$100k）
- 路径：Founders($1k) → NVIDIA Inception → Portfolio($100k)

#### Google for Startups AI Track
- 申请地址：https://cloud.google.com/startup/ai
- 需要：AI-first产品证明（probe引擎 + MetaAsk等）+ Gemini API集成 + 加速器推荐信
- 准备：①将Gemini Flash接入LiteLLM作为演示 ②联系本地创业加速器或YC alumni背书
- 最高$350k GCP，覆盖全部算力需求

---

## 三、🔧 开发降本工具（自托管零成本 · 部署ufo2）

> metafoclaw已有ufo2服务器（`ssh ufo2`，内部平台学阵），以下工具可直接部署。  
> 部署前查`server-roles.md`确认职能范围（ufo2允许内部工具部署 ✅）

| 工具 | 功能 | 部署方式 | 月成本 | 优先级 |
|------|------|---------|--------|--------|
| **Langfuse** | LLM全链路可观测（traces/evals/cost） | Docker Compose，ufo2 `/opt/langfuse/` | ¥0（自托管） | 🔴 最高（LiteLLM天然集成） |
| **Chroma** | 本地RAG向量库 | pip install / Docker，ufo2 | ¥0 | 🟡 中（probe知识库起步） |
| **Qdrant** | 高性能向量搜索（开源自托管） | Docker，ufo2 | ¥0 | 🟡 中（规模化后替代Chroma） |
| **Modal** | GPU推理按量计费 | 云端（Python SDK） | $30/月永久credits | 🟢 低门槛（免费额度够实验） |
| **Zilliz Cloud** | 托管向量库（5GB免费层） | 云端注册 | ¥0（5GB内） | 🟡 中（不想自托管时用） |
| **Pinecone** | 托管向量库（2GB免费层） | 云端注册 | ¥0（2GB内） | 🟢 可选 |

### Langfuse部署建议（最高优先 · 一次接入收益最大）

```bash
# ufo2上部署Langfuse（/opt/langfuse/）
# 详细操作见 server-roles.md 部署三问确认后执行
ssh ufo2
mkdir -p /opt/langfuse/env
# docker-compose.yml + .env配置（env/目录·chmod 600·不入git）
# 接LiteLLM：在litellm config.yaml加 success_callback: ["langfuse"]
```

LiteLLM集成一行配置：
```yaml
# litellm config.yaml
litellm_settings:
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]
```

> ⚠️ Helicone已进维护模式，不再推荐。Langfuse是当前最活跃替代。

### 向量库选型建议

- **起步阶段**：Chroma本地部署，零成本，probe R&D阶段够用
- **生产阶段**：Qdrant自托管（ufo2），性能更好，水平扩展
- **不想运维**：Zilliz Cloud免费5GB（probe知识源去重/检索）

---

## 四、🎯 活动机会（可参与的黑客松 · 战略价值）

| 活动 | 截止/时间 | 奖励 | 战略价值 | 行动 |
|------|---------|------|---------|------|
| **Band of Agents Hackathon** ★ | 2026-06-19截止 | 奖金+曝光 | 🔴 极高：probe多赛道并发编排引擎直接复用（≥3 Agent协作要求与probe架构完美契合） | **立即报名**，用probe Scatter-Gather内核参赛 |
| **Forum × Anthropic Agentic Hackathon** | 关注发布 | Claude credits + Forum Ventures投资人对接 | 🟡 高：claude credits降本 + VC人脉 | 关注Forum官网，有发布即报名 |
| **ARC Prize 2026** | 里程碑6月30日 | $850k奖池 | 🟡 中：技术声誉 + probe主动探索Agent方向验证 | 了解任务格式；与probe编排方向结合评估可行性 |

### Band of Agents Hackathon行动计划（距截止9天）

- **入口**：lablab.ai（搜索Band of Agents）
- **参赛方案**：用probe的Scatter-Gather多赛道并发引擎作为核心Agent编排展示
- **最少组队**：≥3个Agent协作（probe已有：采集Agent + 验证Agent + 聚合Agent ✅）
- **可提交内容**：probe情报引擎 demo + 多赛道并发结果展示
- **双重收益**：①参赛奖励 ②实战验证probe OS1-OS3设计

---

## 五、申请策略与执行顺序

### 叠加逻辑（杠杆最大化路径）

```
第1步：NVIDIA Inception（本周·免费·7-10天）
    ↓ 获批后解锁
第2步a：AWS Activate Portfolio（$100k AWS credits）
第2步b：Nebius AI（$150k GPU credits）

并行：
Microsoft Founders Hub（本周·3日·$5k起）
AWS Activate Founders（本周·自助·$1k，作Portfolio跳板）
```

```
第3步：Google AI Track（1-2月·准备加速器推荐信·最高$350k GCP）
    前置：接入Gemini API演示 + 联系加速器合作
```

```
长期：
a16z Speedrun（积累产品数据和用户后）
Anthropic Startup（需VC背书 + ⚠️需解决主体问题）
```

### 按可用时间分配

| 时间投入 | 行动 | 预期收益 |
|---------|------|---------|
| **今天（2-3小时）** | 注册火山方舟+智谱+硅基流动+阿里百炼+Groq → 接LiteLLM | 合计~1.2亿tokens免费额度上线 |
| **本周（1天）** | NVIDIA Inception + Microsoft Founders Hub + AWS Founders申请 | 解锁$250k+潜在额度 |
| **本周（半天）** | Band of Agents Hackathon报名 + 准备probe演示 | 奖金+技术声誉 |
| **1-2个月** | Google AI Track准备 + Langfuse部署 | $350k GCP + 完整可观测 |

---

## 六、🔴 红线与风险提示

### 授权规则

| 操作类型 | 规则 | 触发条件 |
|---------|------|---------|
| 申请需付费的任何项目 | **R1授权**：出报价清单→元东方密码确认→执行 | Oracle Cloud信用卡验证/付费升级/Stripe Atlas |
| 使用公司营业执照/法人信息 | **R4授权**：说明操作+元东方验证 | NVIDIA Inception/Microsoft Hub/Google AI Track等需公司资质 |
| 使用元东方任何邮箱注册 | **R8授权**：明确1次授权（Agent+操作+限时） | 所有需企业邮箱的申请 |

### 已知风险

1. **Anthropic Startup排除中国大陆**：条款明确不支持中国大陆注册主体（绵阳零元电子商务）。如要申请需香港或国际实体，暂缓直至主体问题解决。

2. **海外扶持主体问题**：微软/Google/AWS官方支持中国公司申请，但部分条款需确认。NVIDIA Inception通常接受，建议用英文填写公司信息。

3. **Google/xAI免费层数据训练**：Google Gemini API免费层内容可能用于模型训练，**禁止传入用户PII、商业机密、敏感数据**。仅用于metafoclaw内部研发/测试场景。

4. **额度时效陷阱**：阿里百炼90天、百度部分额度有期限。领取后立即规划批量任务消耗（probe数据采集/embedding批处理），不要囤积等过期。

5. **免费额度上限**：各免费层均有RPM/RPD限制（如Gemini Flash 15 RPM）。生产流量不可完全依赖免费层，需LiteLLM设置fallback到付费通道。

6. **Oracle Always Free信用卡**：注册需绑定信用卡（验证用，不扣费）。这触发R4资产验证，需元东方确认才能绑卡。实例4核24GB ARM可跑llama.cpp量化模型，价值大但需R4授权。

7. **申请材料一致性**：各平台公司描述保持一致（AI工具平台 / metafoclaw.com / 绑定公司邮箱），避免审核被拒因描述不一致。

---

## 附录：LiteLLM接入速查

接入新免费模型只需在`config.yaml`添加：

```yaml
model_list:
  # 火山方舟
  - model_name: doubao-pro-32k
    litellm_params:
      model: volcengine/doubao-pro-32k
      api_key: os.environ/VOLCENGINE_API_KEY
  
  # 智谱GLM-4.7-Flash（永久免费）
  - model_name: glm-4-flash
    litellm_params:
      model: zhipuai/glm-4-flash
      api_key: os.environ/ZHIPUAI_API_KEY
  
  # 硅基流动（OpenAI兼容）
  - model_name: siliconflow-qwen
    litellm_params:
      model: openai/Qwen/Qwen2.5-7B-Instruct
      api_base: https://api.siliconflow.cn/v1
      api_key: os.environ/SILICONFLOW_API_KEY
  
  # Groq（最快推理）
  - model_name: groq-llama3-70b
    litellm_params:
      model: groq/llama3-70b-8192
      api_key: os.environ/GROQ_API_KEY
  
  # Gemini Flash（⚠️内部研发用，禁用户敏感数据）
  - model_name: gemini-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: os.environ/GEMINI_API_KEY
```

---

> 手册版本：v1.0 · 2026-06-10  
> 下次复核：2026-07-10（或收到官方额度变更通知时）  
> 关联文档：probe第九赛道调研报告 · LiteLLM配置 `ufo2:/opt/litellm-proxy/`

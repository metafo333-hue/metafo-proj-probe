# probe · AI优惠专项 I赛道 数据源+优惠情报调研报告 v1.0

> 定位说明：本文=I 赛道首轮全景调研（历史证据）。采集策略与分类底座见 datasource-aideal-track-i-classification-v1.md，最终落地 YAML 见 datasource-aideal-source-registry-v1.md（35源）。AI 优惠额度数字变动快——具体额度以本文为调研快照，自用降本行动见 metafoclaw-ai-resource-playbook-v1.md（引用本文·勿各自独立维护数字）。

> 日期：2026-06-10 · 性质：第九赛道(AI/Agent资源优惠情报)·调研证据层
> 定位：G元惠的AI垂直专项(G管消费品省钱·I管AI/Agent资源省钱+搞资源)·双重价值(对外AI开发者情报+metafoclaw自用降本)
> 方法：实查各大厂AI优惠/免费额度/创业扶持/活动 + 三层数据源 · 永不代爬
> 上游：[赛道注册表架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) I-aideal · [元惠G](datasource-deal-track-g-v1.md)
> ⚠️时效声明：AI优惠变化极快(如Google 2026-04收紧免费层)·所有额度以官方当前页面为准·本报告查证于2026-06-10

---

## 一、综述

### 赛道定位

I赛道（AI优惠专项）是G元惠赛道的垂直延伸，专注AI/Agent开发者资源——LLM API免费额度、云厂商AI credits、创业扶持计划、GPU算力优惠、开发工具免费层、黑客松奖励六大品类。双重价值：

1. **对外情报**：probe向AI开发者用户输出「当前最可薅的AI资源」结构化情报，差异化于通用省钱应用
2. **metafoclaw自用降本**：直接指导metafoclaw技术栈采购决策，已有Langfuse/LiteLLM等自用场景

### 核心发现（6条）

1. **免费AI资源极丰富，可立即薅的多**：海外Gemini Flash 1500RPD永久、Groq永久高速推理、Cloudflare Workers AI每日10k Neurons均无需申请；国内智谱GLM-4-Flash永久免费+128K上下文、腾讯混元Lite永久——零成本起步的技术栈可立即组建。
2. **最高价值单项：Google AI Track最高$350k**（AI-first企业+VC融资）；无需融资最高：Microsoft Founders Hub $150k（3日自助审核）。
3. **NVIDIA Inception是零门槛杠杆放大器**：免费加入后解锁AWS Activate $100k+Nebius GPU $150k等联动权益，成立10年内有AI产品即符合，7-10天生效——metafoclaw当前应立即申请。
4. **国内字节火山方舟协作奖励计划价值极高**：手动加入后每日200万tokens循环，长期零成本，适合高频API调用场景。
5. **Langfuse开源自托管是metafoclaw LLM可观测最优解**：与LiteLLM原生集成，ufo2已有部署基础，完整功能零成本——无需付费Helicone（已进维护模式）。
6. **中国大陆主体申请海外创业扶持有结构性风险**：Anthropic Startup条款明确排除中国大陆主体；YC/a16z等偏向北美；建议以香港/国际实体申请，或优先申请无地区限制项目（NVIDIA Inception、Microsoft Founders Hub、Google for Startups Start tier）。

### 6类优惠全景

| 类别 | 代表最优项 | 估算最高价值 | 门槛 |
|------|----------|------------|------|
| 海外云AI Credits | Google AI Track | $350k | 需VC融资+AI-first |
| 国内云AI额度 | 阿里百炼~7000万tokens | ¥~3500等值 | 新用户注册即得 |
| 海外LLM免费额度 | Gemini Flash 1500RPD | 长期可用 | 注册即得 |
| 国内LLM免费额度 | 火山方舟协作每日200万 | 长期循环 | 手动加入计划 |
| 创业加速器 | Microsoft Founders Hub | $150k | 自助申请·无需融资 |
| GPU+黑客松 | NVIDIA Inception联动 | $25k-100k算力 | AI产品即符合 |

---

## 二、海外云厂商 AI Credits + 创业扶持

### 优惠卡总表

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 |
|------|-------|------|------|-----|------|
| AWS Activate Founders | Amazon Web Services | $1,000 credits | 无门槛·自助申请 | https://aws.amazon.com/activate | 申请后2年 |
| AWS Activate Portfolio | Amazon Web Services | 最高$200,000 credits | 需VC/孵化器OrgID | https://aws.amazon.com/activate/portfolio | 申请后2年 |
| AWS Gen AI Accelerator | Amazon Web Services | $1,000,000 credits | 录取率<2%·竞争性选拔 | https://aws.amazon.com/startups/accelerators | 项目期 |
| SageMaker 免费层 | Amazon Web Services | 2个月免费 | 新账户 | https://aws.amazon.com/free | ⚠️仅2月·到期自动计费 |
| Microsoft Founders Hub L1 | Microsoft | $5,000 Azure credits (立即) | 自助注册·无需融资 | https://www.microsoft.com/en-us/startups | 1年 |
| Microsoft Founders Hub L3 | Microsoft | 最高$150,000 Azure + $2,500 OpenAI credits | 分级解锁·里程碑达成 | https://www.microsoft.com/en-us/startups | 3日审核 |
| Google for Startups · Start | Google | $2,000 credits | 成立5年内 | https://startup.google.com | 1年 |
| Google for Startups · Scale | Google | $200,000 credits | 需股权融资 | https://startup.google.com | 2年 |
| **Google for Startups · AI Track** | Google | **最高$350,000 credits** | AI-first企业+股权融资+Gemini核心使用 | https://startup.google.com/programs/ai-for-startups | 竞争性·年度 |
| Oracle Cloud Always Free | Oracle | 4核24GB ARM·存储·网络·永久 | 注册即得 | https://www.oracle.com/cloud/free | **永久免费** |
| IBM watsonx for Startups | IBM | $1,000–$10,000/月 × 12月 | 资质申请 | https://www.ibm.com/impact/ibm-for-startups | 12月 |
| Cloudflare Workers AI | Cloudflare | 10,000 Neurons/日·永久 | 注册即得 | https://developers.cloudflare.com/workers-ai | **永久** |

**注**：AWS Bedrock无免费层·按使用计费。⚠️中国大陆主体申请海外扶持有地区限制，建议用香港/国际实体。

---

## 三、国内云厂商 AI 优惠

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 |
|------|-------|------|------|-----|------|
| 百炼新用户额度 | 阿里云 | 每模型100万tokens·合计~7,000万 | 新用户注册 | https://bailian.console.aliyun.com | 90天 |
| 阿里云创业者计划 | 阿里云 | 最高100万元抵扣金 | 创业企业资质申请 | https://startup.aliyun.com | 年度 |
| **火山方舟协作奖励计划** | 字节跳动 | **每日200万tokens循环·长期** | 手动加入计划 | https://console.volcengine.com/ark | **长期循环** |
| 火山方舟安心体验额度 | 字节跳动 | DeepSeek官方托管·新用户赠 | 新用户 | https://console.volcengine.com/ark | 有限期 |
| 混元Lite永久免费 | 腾讯云 | HunYuan-Lite·256K上下文·永久 | 注册即得 | https://cloud.tencent.com/product/hunyuan | **永久** |
| 微信小程序成长计划 | 腾讯云 | 1亿tokens | 需上线微信小程序 | https://cloud.tencent.com/act/pro/hunyuan | 计划期内 |
| 千帆新用户额度 | 百度智能云 | 各模型100万tokens | 新用户 | https://cloud.baidu.com/product/wenxin | 3月 |
| ERNIE-Speed/Lite永久免费 | 百度智能云 | 永久·QPS有限制 | 注册即得 | https://cloud.baidu.com/product/wenxin | **永久** |
| 飞桨AI Studio算力 | 百度 | 免费GPU算力·48h/项目 | 注册即得 | https://aistudio.baidu.com | 每项目48h |
| GLM-4.7-Flash永久免费 | 智谱AI | 永久免费·高QPS | 注册即得 | https://open.bigmodel.cn | **永久** |
| 智谱新用户赠额 | 智谱AI | 2,000万tokens·永久有效 | 新用户注册 | https://open.bigmodel.cn | **永久有效** |
| 硅基流动新用户 | 硅基流动 | 2,000万tokens + ¥14优惠券 | 新用户注册 | https://siliconflow.cn | 有限期 |
| 硅基流动embedding | 硅基流动 | bge-m3 embedding永久免费(RAG) | 注册即得 | https://siliconflow.cn | **永久** |
| 讯飞星火Lite | 科大讯飞 | 永久免费 | 注册即得 | https://xinghuo.xfyun.cn | **永久** |
| 讯飞新用户赠额 | 科大讯飞 | 200万tokens | 新用户 | https://xinghuo.xfyun.cn | 有限期 |
| 华为云AI创业计划 | 华为云 | 120万昇腾算力 | 资质申请 | https://www.huaweicloud.com/startup | ⚠️迁移成本高·昇腾生态较封闭 |

---

## 四、海外 LLM API 免费额度

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 | 备注 |
|------|-------|------|------|-----|------|------|
| **Gemini Flash 免费层** | Google | 1,500 RPD·15RPM·永久 | 注册即得·⚠️内容用于训练 | https://ai.google.dev/pricing | **永久** | Flash最慷慨·Pro已付费化(2026-04) |
| Groq 免费层 | Groq | 永久免费·速率透明 | 注册即得 | https://console.groq.com | **永久** | 推理速度最快800tok/s·Llama/Qwen |
| xAI Grok | xAI | 注册$25+数据共享$150/月 | 注册+启用数据共享 | https://console.x.ai | 月续·⚠️数据用于训练 | 首月等效$175 |
| Anthropic新用户 | Anthropic | $5 API credits | 新账户 | https://console.anthropic.com | 到期 | ⚠️金额小·仅用于测试 |
| **Claude for Open Source** | Anthropic | **6月Max×20免费·价值$1,200** | 开源项目申请·当前活动 | https://anthropic.com/open-source | ⚠️时效有限·2026-06当前可用 | 高价值·尽快申请 |
| Anthropic Startup | Anthropic | $25,000 credits | 需VC融资·⚠️排除中国大陆主体 | https://anthropic.com/startups | 年度 | 中国实体受限 |
| OpenAI新用户 | OpenAI | $5(⚠️待核实) | 新账户 | https://platform.openai.com | 到期 | ⚠️各方信息不一致·以官网为准 |
| OpenAI Startup | OpenAI | $2,500–$50,000 credits | 入驻合作孵化器 | https://openai.com/startups | 申请后 | 需孵化器资质 |
| Mistral 免费层 | Mistral AI | 限速免费层 | 注册即得 | https://console.mistral.ai | **永久** | Devstral代码模型免费 |
| Together AI | Together | 无免费层·充值$5起 | 付费用户 | https://api.together.xyz | — | ⚠️需付费·但DeepSeek推理稳定 |
| Together Accelerator | Together | $50,000 credits | 加速器项目录取 | https://www.together.ai/accelerator | 项目期 | 竞争性申请 |
| Fireworks AI | Fireworks | $1 注册赠 | 新账户 | https://fireworks.ai | 到期 | ⚠️金额小 |
| Cohere 免费层 | Cohere | 1,000次调用/月 | 注册即得 | https://cohere.com | **永久** | 低额度·实验用 |
| HuggingFace Inference | HuggingFace | 免费层·有限速 | 注册即得 | https://huggingface.co/inference-api | **永久** | 冷启动慢 |
| DeepSeek 海外 | DeepSeek | 5M tokens | 新用户 | https://platform.deepseek.com | 有限期 | ⚠️稳定性差·建议走Together/DeepInfra托管 |

---

## 五、国内 LLM API 免费额度

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 |
|------|-------|------|------|-----|------|
| **GLM-4-Flash永久免费** | 智谱AI | 永久·128K上下文·支持联网 | 注册即得 | https://open.bigmodel.cn | **永久** |
| 阿里百炼~7000万 | 阿里云 | 各模型合计~7,000万tokens | 新用户 | https://bailian.console.aliyun.com | 90天 |
| Kimi API | Moonshot AI | ~1,000万tokens+文件API免费+1M上下文 | 新用户 | https://platform.moonshot.cn | 有限期 |
| 硅基流动 | 硅基流动 | ¥14+免费bge-m3 embedding·OpenAI兼容 | 新用户 | https://siliconflow.cn | ¥14有限期·embedding永久 |
| 混元Lite永久 | 腾讯云 | 256K上下文·永久 | 注册即得 | https://cloud.tencent.com/product/hunyuan | **永久** |
| 商汤日日新 | 商汤科技 | 公测免费(限时) | 公测期间 | https://console.sensecore.cn | ⚠️限时·公测结束后付费化 |
| 讯飞星火200万 | 科大讯飞 | 200万tokens+Lite永久免费 | 新用户+Lite永久 | https://xinghuo.xfyun.cn | 新用户有限期·Lite永久 |
| ERNIE-Speed/Lite永久 | 百度智能云 | 永久·QPS有限 | 注册即得 | https://cloud.baidu.com/product/wenxin | **永久** |
| MiniMax-M2 | MiniMax | 限时免费 | 公测期间 | https://minimaxi.com | ⚠️限时 |
| DeepSeek官方 | DeepSeek | 无赠送额度 | — | https://platform.deepseek.com | — | 走硅基流动/百炼托管版替代 |

---

## 六、AI 创业加速器 + 扶持计划

### 无需融资·可自助申请（优先级最高）

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 |
|------|-------|------|------|-----|------|
| **NVIDIA Inception** | NVIDIA | 解锁AWS $100k+Nebius $150k等联动权益+折扣+会议资源 | **免费加入·有AI产品·成立10年内** | https://www.nvidia.com/en-us/startups | **7-10天生效·长期** |
| Microsoft Founders Hub | Microsoft | $5k立即→$150k分级+$2,500 OpenAI credits | 自助注册·无需融资·3日审核 | https://www.microsoft.com/en-us/startups | 按里程碑解锁 |
| Google for Startups · Start | Google | $2,000 credits | 成立5年内 | https://startup.google.com | 1年 |
| Stripe Atlas 权益包 | Stripe | $500→$20,000合作方权益 | Stripe Atlas注册公司用户 | https://stripe.com/atlas | 入驻后 |
| HuggingFace Startup | HuggingFace | 6个月Pro | 申请审核 | https://huggingface.co/startups | 6月 |
| YC Startup School | YC | $25,000 credits（合作方）| 技术背景选拔·无需融资 | https://www.startupschool.org | 批次制 |
| YC Summer Grants | YC | 学生$20,000+$90,000权益 | 在校学生+项目 | https://www.ycombinator.com/grants | 年度 |

### 需融资/竞争性申请

| 名称 | 提供方 | 价值 | 条件 | URL | 时效 |
|------|-------|------|------|-----|------|
| **Google AI Track** | Google | 最高$350,000 credits | AI-first+股权融资+Gemini核心 | https://startup.google.com/programs/ai-for-startups | 年度·竞争性 |
| Google for Startups · Scale | Google | $200,000 credits | 股权融资 | https://startup.google.com | 2年 |
| AWS Activate Portfolio | AWS | 最高$200,000 credits | VC/孵化器OrgID | https://aws.amazon.com/activate/portfolio | 申请后2年 |
| AWS Gen AI Accelerator | AWS | $1,000,000 credits | 录取率<2%·竞争性 | https://aws.amazon.com/startups/accelerators | 项目期 |
| Anthropic Startup | Anthropic | $25,000 credits | VC融资·⚠️排除中国大陆主体 | https://anthropic.com/startups | 年度 |
| a16z Speedrun | a16z | $1M投资+>$5M credits | 录取率<0.4%·SR008下批 | https://a16z.com/speedrun | 批次制 |
| Sequoia Arc | Sequoia | $250k SAFE+$600k credits | 股权友好·偏北美 | https://www.sequoiacap.com/arc | 批次制 |
| YC Fall 2026 | YC | $500,000（$125k SAFE+$375k MFN） | 截止2026-07-27 | https://www.ycombinator.com/apply | 截止2026-07-27 |
| Together Accelerator | Together | $50,000 credits | 竞争性 | https://www.together.ai/accelerator | 项目期 |

---

## 七、Agent/AI 开发工具免费层

### 可观测 & 追踪

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| **Langfuse 开源自托管** | Langfuse | 完整LLM可观测·无限追踪 | 开源自托管·免费 | https://github.com/langfuse/langfuse | **metafoclaw已有ufo2部署·与LiteLLM原生集成** |
| LangSmith 免费层 | LangChain | 5,000 traces/月 | 注册即得 | https://smith.langchain.com | 超限付费 |
| ⚠️Helicone | Mintlify | — | — | — | ⚠️进入维护模式(被Mintlify收购)·不推荐新接入·用Langfuse替代 |

### 向量数据库 / RAG

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| **Chroma 开源自托管** | Chroma | 本地RAG·零成本 | 开源自托管 | https://github.com/chroma-core/chroma | **最推荐·metafoclaw可立即用** |
| Pinecone 免费层 | Pinecone | 2GB·~100k向量 | 注册即得 | https://www.pinecone.io | 永久免费层 |
| Qdrant 免费层 | Qdrant | 免费集群 | 注册即得 | https://cloud.qdrant.io | ⚠️闲置4周后删除 |
| Zilliz Cloud 免费层 | Zilliz | 5GB + $100 credits | 注册即得 | https://zilliz.com | 有限期 |
| Weaviate 免费层 | Weaviate | 免费沙盒 | 注册即得 | https://weaviate.io | ⚠️仅14天 |

### Agent 编排框架

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| CrewAI 开源 | CrewAI | 开源·无限本地执行 | 开源自用 | https://github.com/crewAIInc/crewAI | 云端50执行/月免费 |
| LangGraph 开源 | LangChain | 开源本地编排·无限 | 开源自用 | https://github.com/langchain-ai/langgraph | 云端付费 |

### 推理基础设施

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| **Modal 免费层** | Modal | $30/月credits·永久 | 注册即得 | https://modal.com | **永久·GPU推理·serverless** |
| LlamaParse 免费层 | LlamaIndex | 10,000 credits/月(~1,000页) | 注册即得 | https://cloud.llamaindex.ai | 永久免费层 |

### AI 编码工具

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| Cursor Hobby | Cursor | 基础免费·2000次自动补全 | 注册即得 | https://cursor.com | 学生Pro 1年免费 |
| GitHub Copilot Free | GitHub | 基础免费 | 注册即得 | https://github.com/features/copilot | ⚠️新申请2026-04暂停 |
| Windsurf | Codeium | 无限Tab补全·免费层 | 注册即得 | https://windsurf.com | 无限Tab补全最慷慨 |
| v0 by Vercel | Vercel | $5/月基础免费 | 订阅 | https://v0.dev | UI生成 |
| Bolt.new | StackBlitz | 150,000 tokens/天·免费 | 注册即得 | https://bolt.new | 全栈AI生成 |

---

## 八、GPU 算力优惠 + 黑客松/竞赛活动

### 免费 GPU 算力

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| **Kaggle Notebooks** | Google/Kaggle | 30h/周·P100/T4 | 注册即得 | https://www.kaggle.com/code | **最稳定·无需申请** |
| Google Colab 免费层 | Google | T4·15-30h/周·不稳定 | 注册即得 | https://colab.research.google.com | 有断线风险 |
| **Modal 免费层** | Modal | $30/月credits·A10/A100 | 注册即得 | https://modal.com | 已列开发工具·serverless |
| Google TPU Research Cloud | Google | 大额TPU·申请制 | 研究项目申请 | https://sites.research.google/trc | 学术偏向 |
| NVIDIA Inception联动 AWS | NVIDIA/AWS | $25k–$100k AWS credits(含GPU) | NVIDIA Inception成员 | https://www.nvidia.com/en-us/startups | 通过Inception解锁 |
| Nebius AI Studio | Nebius | $150k credits(GPU) | NVIDIA Inception成员 | https://studio.nebius.ai | 通过Inception解锁 |
| NVIDIA 学术计划 | NVIDIA | 30,000 H100小时 | 教职人员 | https://www.nvidia.com/en-us/gpu-cloud/academic | 学术限定 |

### 国内免费/低价算力

| 名称 | 提供方 | 价值 | 条件 | URL | 备注 |
|------|-------|------|------|-----|------|
| 百度AI Studio | 百度 | 48h GPU + 裂变120h | 注册/分享裂变 | https://aistudio.baidu.com | 裂变机制实际可扩大 |
| 阿里PAI-DSW | 阿里云 | 750计算时·A10/V100 | 新用户 | https://www.aliyun.com/product/bigdata/learn | 3月有效期 |
| AutoDL / Featurize | 第三方 | 低价按需·RTX4090约¥2/h | 付费·按需 | https://www.autodl.com | ⚠️付费但极低价·国内GPU最佳性价比 |

### 黑客松 / 竞赛奖励

| 名称 | 组织方 | 价值 | 截止/时间 | URL | 备注 |
|------|-------|------|----------|-----|------|
| ARC Prize 2026 | ARC Prize Foundation | $850,000奖池·里程碑 | 2026-06-30里程碑节点 | https://arcprize.org | AGI基准测试·高难度 |
| **Band of Agents Hackathon** | lablab.ai | credits+投资曝光 | **2026-06-19截止** | https://lablab.ai | **probe编排引擎可直接复用参赛** |
| Forum × Anthropic Hackathon | Forum/Anthropic | Claude credits+投资人曝光 | 滚动开放 | https://forum.dev | 多期次·关注开放通知 |
| ⚠️Eazo $300k黑客松 | Eazo | $300,000奖池 | **主场次已结束** | — | ⚠️已过期·不适用 |

---

## 九、数据源层：AI优惠持续监测雷达

### 三层数据源矩阵

#### 层1·开源列表（最高优先·无Key·合规）

| 数据源 | Stars | 特点 | 监测方式 | 状态 |
|-------|-------|------|---------|------|
| **cheahjs/free-llm-api-resources** | 23,200+ | AI免费API最权威整合·每5-10天自动更新 | GitHub atom RSS订阅：`github.com/cheahjs/free-llm-api-resources/commits/main.atom` | ✅ 立即采纳 |
| **ripienaar/free-for-dev** | 123,000+ | AI/ML分区·全品类免费层 | GitHub atom RSS订阅：`github.com/ripienaar/free-for-dev/commits/main.atom` | ✅ 立即采纳 |
| **Olshansk/rss-feeds** | 599 | 厂商官方RSS聚合列表·含Anthropic/OpenAI等无官方RSS的厂商·每小时更新 | 订阅此RSS列表再二次过滤 | ✅ 立即采纳 |

#### 层2·社区聚合（中优先·部分需key）

| 数据源 | API类型 | 关键词过滤 | 成本 | 状态 |
|-------|--------|----------|------|------|
| HN Algolia API | REST·无key | `free credits` / `api pricing` / `startup program` / `free tier` | 免费·10,000 req/h | ✅ 立即采纳 |
| Reddit PRAW | OAuth·非商业免费 | r/LocalLLaMA / r/MachineLearning / r/artificial | 非商业免费 | ✅ 采纳·注意非商业条款 |
| Product Hunt GraphQL | 免费dev token | `AI` + `free` / `credits` 标签 | 免费dev token | ✅ 采纳 |
| Kaggle API CLI | CLI·免费 | 竞赛奖励·数据集 | 免费 | ✅ 采纳 |

#### 层3·人工参考（低优先·无官方API·不接入自动化）

| 来源 | 说明 | 处理方式 |
|-----|------|---------|
| joinsecret.com | AI/SaaS优惠聚合·无官方API | ❌ 禁代爬·人工参考 |
| getaiperks.com | AI优惠专题 | ❌ 禁代爬·人工参考 |
| lablab.ai | 黑客松聚合 | ❌ 禁代爬·人工参考 |
| Devpost | 竞赛聚合 | ❌ 禁代爬·人工参考 |

### 自动化监测方案

```
方案一：GitHub Actions atom订阅
  1. 订阅 cheahjs/ripienaar 两仓库 commit atom RSS
  2. GitHub Actions定时拉取(每6h)：diff提取变更行
  3. 变更含关键词(free/pricing/credits/tier/limit)→推送probe事件队列

方案二：RSS聚合关键词过滤
  - 使用 Olshansk/rss-feeds 中厂商官方RSS
  - 每小时拉取·关键词匹配：free / pricing / credits / tier / limit / startup
  - 命中→写probe事件·标注来源+时间戳

方案三：社区轮询
  - HN Algolia: 每4h查询 tags=story & query=AI+credits 最近24h
  - Reddit PRAW: r/LocalLLaMA 热帖标题扫描
  - Product Hunt: weekly AI产品新发布扫描

存储：probe专用Redis或PG（不复用boss8001-b交易Redis·遵循服务器职能隔离T4规则）
去重：URL+标题hash去重·7天TTL
```

---

## 十、注意事项

### 时效风险

- AI优惠政策变化极快：Google Gemini Pro免费层已于2026-04付费化；各厂商免费额度随时可能调整。
- **本报告查证于2026-06-10，所有具体额度以各厂商官方当前页面为准**。
- 黑客松/活动类优惠有截止日期，见第八节标注。

### 数据隐私

- Gemini Flash免费层：内容用于模型训练——生产环境勿传敏感数据。
- xAI Grok数据共享计划：开启后数据用于训练——仅适合非敏感测试。
- 国内平台：百度/讯飞等均在中国监管体系内——敏感业务逻辑勿上传。

### 地区限制

- Anthropic Startup计划：条款明确排除中国大陆注册主体。
- YC/a16z等美国加速器：偏向美国/北美实体，中国主体录取率更低。
- 建议申请策略：无地区限制项目（NVIDIA Inception、Microsoft Founders Hub、Google Start tier）优先申请；有地区限制项目考虑香港/国际实体路径。

### 中国主体申请海外优惠风险

- 部分项目（AWS Activate Portfolio、Google Scale/AI Track）需VC/孵化器背书，中国大陆主体需确认合作VC已注册该计划。
- 海外credits绑定信用卡时注意超出免费额度自动扣费风险——建议设置消费告警。
- 海外账户注册如需手机号/地址，需用对应地区真实信息，勿使用虚假信息。

### metafoclaw自用建议（立即行动项）

| 优先级 | 行动 | 预期价值 |
|-------|------|---------|
| P0·本周 | 申请NVIDIA Inception | 解锁AWS $100k+Nebius $150k·7-10天生效 |
| P0·本周 | 注册Microsoft Founders Hub L1 | $5k立即到账·3日审核 |
| P0·本周 | 加入火山方舟协作奖励计划 | 每日200万tokens循环·长期零成本 |
| P1·本月 | Claude for Open Source申请 | 6月Max×20·价值$1,200 |
| P1·本月 | 接入Langfuse自托管 | ufo2已有基础·LLM可观测完整能力 |
| P2·季度 | 绑定Google for Startups Start | $2,000 credits·低门槛 |

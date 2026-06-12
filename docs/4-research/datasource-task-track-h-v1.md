# probe · 任务H赛道 数据源调研报告 v1.0

> 日期：2026-06-10 · 性质：调研证据层（8端口×三层优先级扇出调研+四闸审核+合规严筛）
> 方法：开源API > 综合服务 > 权威官方 三层 · 永不代爬 · 合规严筛排除灰产 · 见 [调研方法论v1.1](datasource-research-methodology-v1.0.md)
> 上游：[赛道注册表架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) H-task · [分批次计划B4](datasource-research-onboarding-batch-plan-v1.0.md) · 真源域 D16（任务与激励）

---

## 一、调研综述

### 最重要的诚实结论

**任务H赛道的"结构化规则数据源"极度稀缺——各平台签到/浏览/裂变/消费任务规则属内部运营配置，几乎无任何开放API，只能靠RSSHub监测公开公告+人工/NLP提炼规则schema。**

这是客观现实，非调研遗漏。各平台（京东/拼多多/淘宝/B站/抖音等）的任务中心规则均为内部动态配置，有意保持不透明（尤其裂变玩法如砍价随机算法），外部调研无从直接采集。

### 三层覆盖度总评

| 层级 | 定义 | H赛道覆盖质量 | 说明 |
|------|------|-------------|------|
| 层1·开源工具 | 可自托管·license干净·零成本 | ★★★★☆ 较好 | Label Studio/LimeSurvey/OpenLoyalty/badgr-server等·但均为"自建系统工具"非"情报源" |
| 层2·商业API | 商业服务·需开户/付费·合规担责方清晰 | ★★★☆☆ 中等 | Prolific/穿山甲/Toloka/Cint可用·但覆盖创作激励/电商裂变规则的商业API几乎空白 |
| 层3·权威官方 | 平台官方API·最权威 | ★★☆☆☆ 薄弱 | YouTube Analytics可用·国内平台几乎零开放·规则文档仅帮助中心文本 |

### 五条核心结论

1. **规则情报 vs 系统工具**：H赛道调研中最重要的区分——众多开源工具（OpenLoyalty/Label Studio/badgr-server/Oasis）是"自建任务/积分/成就系统"的底座工具，本身不是外部情报源；probe的情报价值在于利用这些工具建模后，对照外部平台规则建立schema，再监测规则变更。

2. **电商任务规则结构性封闭**：签到/浏览/裂变/消费积分规则（京东互动/拼多多助力/淘宝邀新/B站签到）均属内部运营配置，无任何程序化接入渠道。唯一可行路径：RSSHub订阅官方公告 → 活动页文本解析 → NLP提炼规则schema入库。

3. **创作激励国内全封闭**：B站/抖音/视频号/小红书的创作激励规则和收益数据均无公开API（且B站逆向API已收律师函），只有YouTube Analytics提供创作者账号自助查询。

4. **众包/问卷/成就端口有亮点**：这三个端口存在层1高质量开源工具（Label Studio/CVAT/LimeSurvey/Formbricks/badgr-server/Oasis）可自托管，是整个H赛道最可落地的部分。

5. **灰产密度高**：任务H赛道是灰产重灾区（网赚刷单/刷量/拉人头任务站），合规严筛排除项比其他赛道多，宁可少接不碰。

---

## 二、8端口源卡明细

> 说明：每端口注明两类源的区别：
> - **A类（情报源）**：提供外部平台任务规则情报的源，H赛道极稀缺
> - **B类（系统工具）**：自建任务/积分/成就/问卷系统的开源/SaaS工具，不是外部情报，但可用于建模规则schema或probe自身功能底座

---

### 端口H1 · 签到打卡

| 源名 | 层级 | URL |
|------|------|-----|
| RSSHub | 层1开源（A类·间接） | https://github.com/DIYgod/RSSHub |
| bilibili-API-collect | 层1（已弃） | https://github.com/SocialSisterYi/bilibili-API-collect |
| BiliBiliToolPro | 层1（有限参考） | https://github.com/RayWangQvQ/BiliBiliToolPro |
| 聚合数据juhe.cn | 层2 | https://www.juhe.cn/ |
| 京东互动玩法 | 层3（仅公开页） | https://www.cnblogs.com/Jcloud/p/17117056.html |
| 抖音/快手开放平台 | 层3 | — |

**RSSHub**
- 能力：万能RSS聚合，可订阅平台公告/活动页，无专属签到规则路由，间接覆盖需NLP提炼
- 接入：MIT·零成本·自托管
- 合规：MIT·无爬取红线·灰产筛：通过
- 裁决：**采纳候选（规则变更通知层）**——不提供结构化规则数据，但是规则变更监测的核心工具

**bilibili-API-collect**（A类·弃）
- 能力：B站逆向API文档，含签到规则结构
- 接入：2026-01-28已收B站律师函，停止维护，文档已删除
- 合规：灰产筛：**ToS违规+法律追诉，一票否决**
- 裁决：**弃（法律追诉·不可接入）**

**BiliBiliToolPro**（有限参考）
- 能力：B站自动任务执行工具，可参考规则结构建模
- 合规：账号自动化操作违B站ToS
- 裁决：**有限参考（可参考规则结构建立schema·禁止任何执行能力接入probe）**

**聚合数据juhe.cn**（弃）
- 能力：实查无签到规则/任务中心分类API
- 裁决：**弃（无此类数据）**

**京东互动玩法**（A类·仅公开页）
- 能力：京东任务中心6类任务（签到/浏览/跳转等）规则结构已知，JSF接口仅内部，无对外API
- 裁决：**仅公开页**——规则结构可建schema但无程序化接入

**覆盖缺口**：结构化规则数据几乎无现成API（平台内部配置），只能公开页+RSSHub监测+NLP。

---

### 端口H2 · 浏览观看

| 源名 | 层级 | URL |
|------|------|-----|
| RSSHub | 层1开源 | https://github.com/DIYgod/RSSHub |
| 穿山甲Open API | 层2（A类·权威） | http://open-api.csjplatform.com/ · https://www.csjplatform.com/ |
| TradPlus/极光Adpub | 层2（A类·补充） | https://docs.tradplusad.com/ |
| 微信小游戏视频号激励政策 | 层3 | https://developers.weixin.qq.com/community/ |
| 抖店开放平台 | 层3 | https://op.jinritemai.com/docs/api-docs/ |
| 京东互动玩法浏览任务 | 层3 | 同端口H1 |

**穿山甲Open API**（A类·情报源）
- 能力：字节官方激励视频S2S奖励回调——user_id/trans_id/reward_name/reward_amount/sign字段，"看广告得奖励"行业标准schema，是最接近"浏览赚奖励"结构化情报的权威文档
- 接入：需企业资质开户
- 合规：字节官方·灰产筛：通过
- 裁决：**采纳候选（激励视频奖励schema权威参考）**——注意是广告主接入文档，情报价值在规则结构建模，而非电商"看视频得金币"直接等同

**TradPlus/极光Adpub**
- 能力：广告聚合中间件，多平台激励视频S2S统一回调，可横向对比多平台奖励规则
- 裁决：**补充参考（横向对比多平台奖励规则）**

**微信小游戏视频号激励政策**（层3·仅公开页）
- 能力：创作者侧激励（流量分成+CPS），非用户侧签到，无API
- 裁决：**仅公开页**

**抖店开放平台**（层3·待实证）
- 能力：JS渲染，未能实证是否有用户激励API
- 裁决：**待实证**

**覆盖缺口**：用户侧"看视频得积分"无结构化API，最接近的权威结构是穿山甲激励广告schema（但与电商浏览赚金币逻辑不同）。

---

### 端口H3 · 分享裂变

| 源名 | 层级 | URL |
|------|------|-----|
| RefRef | 层1开源（B类·工具） | https://github.com/amicalhq/refref |
| RSSHub | 层1（弃·此端口） | — |
| GrowSurf | 层2（B类·工具） | https://growsurf.com |
| Enable3 Rewards API | 层2（B类·工具） | https://enable3.io/rewards-api |
| 淘宝渠道邀请码API | 层3 | taobao.tbk.sc.invitecode.get |
| 拼多多多多进宝/京东联盟 | 层3 | — |

**RefRef**（B类·系统工具）
- 能力：AGPLv3，自建邀请拉新系统，referral追踪，alpha阶段
- 合规：AGPLv3——**商业使用须律师确认传染性**，灰产筛：通过
- 裁决：**probe自建参考非情报源**——若用于probe自身裂变功能底座，需法务确认AGPLv3条款

**GrowSurf**（B类·不适用情报采集）
- 能力：邀请系统SaaS，$95/月，只能看接入GrowSurf的客户数据，非外部平台规则
- 裁决：**不适用情报采集（自建工具）**

**Enable3 Rewards API**（B类·不适用情报采集）
- 能力：搭建自有奖励系统，非外部情报
- 裁决：**不适用情报采集**

**淘宝渠道邀请码API**（层3·仅CPS）
- 能力：联盟推广者渠道邀请码，非终端裂变活动规则
- 裁决：**合规可用但无活动规则文本**

**拼多多多多进宝/京东联盟**（层3·仅CPS）
- 能力：仅推广链接/订单数据，无活动规则查询接口
- 裁决：**仅CPS推广非规则情报**

**RSSHub（此端口）**
- 实查：电商活动公告路由不覆盖（shopping路由404），自制路由触犯爬取红线
- 裁决：**弃（电商裂变活动不覆盖）**

**覆盖缺口**：三层均无主流电商裂变活动（拼多多助力/淘宝邀新/京东组队）结构化规则API。平台有意保持不透明（砍价随机算法设计如此），只能依赖活动公告页文本解析+NLP提炼。

---

### 端口H4 · 消费下单

| 源名 | 层级 | URL |
|------|------|-----|
| OpenLoyalty | 层1开源（B类·底座工具） | https://github.com/sbodak/open-loyalty · https://docs.openloyalty.io |
| 聚合数据 | 层2 | — |
| Voucherify | 层2（B类·规则参考） | https://docs.voucherify.io |
| 淘宝/京东/微信联盟 | 层3 | — |

**OpenLoyalty**（B类·系统工具·强烈推荐）
- 能力：完整积分系统REST API——积分转移/消费记录/奖励活动/邀请/会员等级，Docker自托管，月处理10亿事件
- 接入：Apache-2.0·商用友好·零成本自托管
- 合规：灰产筛：通过·许可证：Apache-2.0无传染性
- 裁决：**强烈推荐（probe消费积分任务规则引擎底座）**——重要说明：这是B类系统工具，是probe自建消费积分功能的底座，不是"从外部平台采集积分规则"的情报源

**Voucherify**（B类·规则设计参考）
- 能力：100+ API，referral/积分/奖励，免费层500用户
- 裁决：**规则设计参考非外部情报**

**淘宝/京东/微信联盟**（层3·仅CPS）
- 能力：仅CPS推广/订单，积分规则（淘金币/京豆/PLUS）无结构化查询API
- 裁决：**仅CPS非积分规则**

**聚合数据**：电商分类无积分任务/消费返利专项API，裁决：**不适用**

**覆盖缺口**：无现成源提供"他人平台消费积分规则"结构化情报。各平台积分权益规则以帮助中心文本/活动页公示。对策：人工整理知识库 + 官方帮助页变更监测（RSSHub订阅变更公告）。

---

### 端口H5 · 创作产出

| 源名 | 层级 | URL |
|------|------|-----|
| YouTube Analytics & Reporting API | 层3权威（A类·首选） | https://developers.google.com/youtube/reporting |
| Phyllo | 层2（A类·昂贵） | https://www.getphyllo.com/ |
| 哔哩哔哩开放平台 | 层3 | https://openhome.bilibili.com/doc |
| 抖音开放平台 | 层3 | https://developer.open-douyin.com/ |
| 微信视频号创作分成 | 层3 | https://ad.weixin.qq.com/docs/273 |
| 小红书蒲公英 | 层3 | https://open.xiaohongshu.com/ |

**YouTube Analytics & Reporting API**（A类·情报源·首选）
- 能力：OAuth2.0，收益指标（estimatedRevenue/cpm等），每日10000 quota免费，仅账号本人数据不能跨账号
- 接入：免费·Google账号OAuth
- 合规：官方API·灰产筛：通过·ToS合规
- 裁决：**推荐（创作者绑定账号自助查YPP收益·首选）**

**Phyllo**（A类·昂贵）
- 能力：聚合20+平台创作者收益（YouTube/TikTok/Instagram等），走官方OAuth非爬取，约$20000/年起
- 合规：官方OAuth聚合·灰产筛：通过
- 裁决：**有价值但昂贵（后期多平台统一展示方可考虑·待R1）**

**哔哩哔哩开放平台**（层3·无创作激励API）
- 能力：中视频计划收益/创作激励数值不开放，仅播放互动数据，中视频规则仅运营公告
- 合规：逆向项目bilibili-API-collect已收律师函，一切逆向路径否决
- 裁决：**创作激励无API（结构性封闭）**

**抖音开放平台**（层3·无创作收益API）
- 能力：创作激励计划无公开revenue API，企业认证后仅自有账号数据
- 裁决：**无创作收益API**

**微信视频号创作分成**
- 能力：规则文档公开（https://ad.weixin.qq.com/docs/273），收益接口不开放
- 裁决：**规则可读无结构化API**

**小红书蒲公英**
- 能力：蒲公英API门槛极高（年消耗≥500万方可申请）
- 裁决：**门槛过高·排除**

**覆盖缺口**：国内平台（B站/抖音/视频号/小红书）创作激励规则和收益均无公开API，规则仅运营公告。只有YouTube Analytics提供创作者账号本人收益API化查询。结构性封闭，非调研遗漏。

---

### 端口H6 · 答题问卷

| 源名 | 层级 | URL |
|------|------|-----|
| Prolific | 层2（A类·首选） | https://www.prolific.com/api · https://docs.prolific.com/ |
| Cint/Lucid Marketplace | 层2（A类） | https://developer.lucidhq.com/ |
| Respondent | 层2（A类·备选） | https://www.respondent.io/api |
| LimeSurvey | 层1开源（B类·工具） | https://github.com/LimeSurvey/LimeSurvey |
| Formbricks | 层1开源（B类·工具） | https://github.com/formbricks/formbricks |
| 问卷星 | 层3（国内·条件性） | https://www.wjx.cn/api.aspx |

**Prolific**（A类·情报源+受访者平台·首选）
- 能力：学术/商业调研，完整Research API（创建研究/招募/审批/Bonus支付），GDPR合规，研究员账号自助获token，有R包
- 接入：研究员账号注册，平台费33.5%，按参与者付费
- 合规：GDPR·灰产筛：通过·注意：参与者主要英语区，**不覆盖中国大陆**
- 裁决：**端口H6首选（海外调研最合规API最完整·待R1预算确认）**

**Cint/Lucid Marketplace**（A类·中期推荐）
- 能力：全球最大样本交换，3.35亿消费者，100+国，ESOMAR合规
- 接入：企业级，需联系integrations@cint.com商务对接
- 裁决：**推荐（中期·需商务对接·待R1）**

**Respondent**（A类·备选）
- 能力：400万verified参与者，B2B专业人群，按session收费
- 裁决：**备选（专业受访者场景）**

**LimeSurvey**（B类·工具层·推荐）
- 能力：GPL，自托管问卷，RemoteControl API（XML-RPC/JSON-RPC）+REST，GDPR数据自主
- 接入：GPL·自托管·零成本
- 合规：数据自主·灰产筛：通过·注意GPL传染性（若二次分发需律师确认）
- 裁决：**推荐（问卷发放工具层·probe自建问卷底座首选之一）**

**Formbricks**（B类·工具层·推荐）
- 能力：AGPL-v3，现代Next.js问卷，REST API，德国GDPR合规
- 接入：AGPL-v3·自托管·零成本
- 合规：灰产筛：通过·**AGPL-v3商业使用须律师确认传染性**
- 裁决：**推荐（工具层·与LimeSurvey并列·AGPLv3须法务确认）**

**问卷星**（层3·条件性）
- 能力：付费版数据推送API（Webhook），等保三级+ISO27001，不提供给受访者发钱API
- 合规：受访者数据须遵PIPL，个人数据合规成本高
- 裁决：**条件性推荐（国内场景·需PIPL合规方案·受访者PII不落probe库）**

**排除项**：网赚问卷站（收奖网/爱调查——灰产薅羊毛刷量，一票否决）；刷单任务平台（灰产一票否决）；Qualtrics（$5040/年起，成本不合理）

**合规特别说明**：个人数据persist_policy必须明确——PII不落probe库，由平台管理，结果去标识化后才持久化，国内场景遵PIPL。

**覆盖缺口**：中文受访者panel合规路径有限（问卷星条件性，Prolific不覆盖大陆），国内调研需单独方案。

---

### 端口H7 · 众包悬赏

| 源名 | 层级 | URL |
|------|------|-----|
| Label Studio | 层1开源（B类·首选） | https://github.com/HumanSignal/label-studio |
| CVAT | 层1开源（B类） | https://github.com/cvat-ai/cvat |
| Toloka | 层2（A类） | https://toloka.ai |
| Amazon MTurk | 层2（慎用） | https://docs.aws.amazon.com/mturk/ |
| Prolific | 层2（A类） | 同端口H6 |
| Clickworker | 层2（A类） | https://www.clickworker.com/api/ |
| Scale AI | 层2（不推荐） | https://scale.com/docs |
| 阿里众包 | 层3（排除） | https://crowd.alibaba.com |
| 百度众测 | 层3（排除） | https://test.baidu.com |

**Label Studio**（B类·工具层·首选）
- 能力：Apache-2.0，多类型标注，完整REST API+Python SDK，webhook，自托管数据留本地
- 接入：Apache-2.0·商用友好·零成本·自托管
- 合规：灰产筛：通过·Apache-2.0无传染性
- 裁决：**首选（自托管·license最干净·API最完整·众包标注底座）**

**CVAT**（B类·工具层·推荐）
- 能力：MIT，图像/视频/3D标注，REST API+Python SDK，v2.67.0（2026-06）活跃维护
- 接入：MIT·自托管·零成本
- 合规：灰产筛：通过
- 裁决：**推荐（计算机视觉标注场景）**

**Toloka**（A类·平台·推荐）
- 能力：全球众包，REST API+toloka-kit SDK，crowd-kit开源
- 接入：按任务付费
- 合规：数据境外存储·需确认GDPR/数据居留合规·灰产筛：通过
- 裁决：**推荐（待授权·确认数据居留合规方可接入）**

**Amazon MTurk**（慎用）
- 能力：最老牌众包，boto3 SDK
- 合规：灰产筛：通过
- 裁决：**慎用（API可用但2025任务量大幅萎缩"实际已死"，可靠性存疑）**

**Prolific**（端口H7·推荐）
- 同端口H6，高质量标注/RLHF场景首选
- 裁决：**推荐（待R1·RLHF最佳众包平台）**

**Clickworker**（A类·欧洲合规·推荐）
- 能力：德国正规，REST API，7M众包员，GDPR合规
- 裁决：**推荐（待R1·欧洲合规众包平台）**

**Scale AI**（不推荐）
- 能力：企业级AI数据标注平台
- 接入：$93,000/年起，sales流程
- 裁决：**不推荐（成本/流程不适合自动化接入）**

**阿里众包**（排除）
- 实查：220万众包员，无对外公开REST API
- 裁决：**排除（无公开API）**

**百度众测**（排除）
- 实查：无对外开放API
- 裁决：**排除（无公开API）**

**灰产排除项**：刷单/刷量悬赏；虚假关注任务；拉人头任务站；逆向爬取众包平台；返现APP任务平台——全部一票否决。

**覆盖缺口**：国内众包平台（阿里众包/百度众测）无公开API，中文众包场景有缺口。

---

### 端口H8 · 成长成就

| 源名 | 层级 | URL |
|------|------|-----|
| Open Badges 3.0 + badgr-server | 层1开源（B类·标准·首选） | https://1edtech.github.io/openbadges-specification/ · https://github.com/edubadges/badgr-server |
| Oasis | 层1开源（B类） | https://github.com/isuru89/oasis |
| Gamification-Engine(gengine) | 层1（弃·停更） | https://github.com/ActiDoo/gamification-engine |
| Trophy.so | 层2（B类·SaaS） | https://trophy.so/developers |
| Steam Web API | 层3权威（A类·参考） | https://partner.steamgames.com/doc/webapi_overview |
| Open Badge Factory | 层3（可选） | https://openbadgefactory.com/ |
| Duolingo | 层3（排除） | — |

**Open Badges 3.0 + badgr-server**（B类·标准底座·首选）
- 能力：国际开放标准（W3C VC兼容），徽章发行REST API，MIT/Apache开源实现可自托管
- 接入：开源标准·选edubadges fork（非mozilla停更版）
- 合规：灰产筛：通过·开放标准无许可风险
- 裁决：**首选（成就标准数据结构基础·probe自建成就系统标准层）**——注意：这是B类工具，用于建立schema标准，非外部成就情报源

**Oasis**（B类·工具·推荐·注意开发状态）
- 能力：Apache-2.0，事件驱动成就（积分/徽章/里程碑/排行榜），REST API，Redis驱动
- 接入：Apache-2.0·自托管·零成本
- 合规：灰产筛：通过
- 裁决：**推荐（注意README标注"开发中"·生产使用前须评估稳定性）**

**Gamification-Engine(gengine)**（弃）
- 能力：MIT，但最后release v0.4.0=2020年1月，已5年停更
- 裁决：**不推荐（停止维护）**

**Trophy.so**（B类·SaaS·小规模免费）
- 能力：游戏化SaaS，Streaks/Achievements/Points/Leaderboards API，7语言SDK，100 MAU免费
- 接入：100 MAU免费·规模化需付费
- 合规：灰产筛：通过
- 裁决：**推荐（小规模免费可接入·规模化待R1）**

**Steam Web API**（A类·情报源·推荐）
- 能力：公开成就数据（解锁率/排行榜），免费key，数据可读
- 接入：免费key注册
- 合规：**ToS明确禁止数据商业再出售**·灰产筛：通过（只要不商业再出售）
- 裁决：**推荐（游戏成就规则及解锁率的权威参考源）**——这是端口H8少数真正的A类情报源之一，注意ToS禁商业再出售

**Open Badge Factory**（可选）
- 能力：商业Open Badges，2025新版OpenAPI，付费
- 裁决：**可选（付费·若需托管服务可评估）**

**Duolingo**（排除）
- 能力：标杆成就养成设计案例·官方API已关闭，逆向违ToS
- 裁决：**排除（无API·仅设计参考）**

**重要区分**：
- 端口H8的层1开源工具（Open Badges标准/Oasis）是"自建成就系统"底座（B类）
- **Steam Web API是端口H8少数可读公开成就规则数据的A类情报源**
- "成就规则（设计文档）"和"用户成就数据"是两类完全不同的源——后者需OAuth/企业合约；probe聚焦前者

**覆盖缺口**：无中文平台（微信读书/知乎/B站）开放成就API；养成线数据高度平台锁定。

---

## 三、推荐首选源汇总表

| 端口 | 层1首选 | 层2首选 | 层3权威 | 性质说明 |
|------|--------|--------|--------|---------|
| H1·签到打卡 | RSSHub（规则变更监测） | — | 京东互动玩法（仅公开页） | 无结构化API·监测层为主 |
| H2·浏览观看 | RSSHub | 穿山甲Open API | 抖店开放平台（待实证） | 穿山甲是激励广告schema·非电商积分 |
| H3·分享裂变 | —（无合适层1） | —（无外部情报商业API） | 淘宝渠道邀请码（仅CPS） | 三层均无裂变规则情报·公告NLP为主 |
| H4·消费下单 | OpenLoyalty（B类底座） | Voucherify（B类规则参考） | — | 无外部情报源·自建schema+公告监测 |
| H5·创作产出 | — | Phyllo（昂贵·待R1） | YouTube Analytics（首选） | 国内全封闭·仅YouTube可API化 |
| H6·答题问卷 | LimeSurvey/Formbricks（B类工具） | Prolific（首选·待R1）/Cint（中期） | 问卷星（国内·条件性） | Prolific最合规API最完整 |
| H7·众包悬赏 | Label Studio/CVAT（B类工具） | Toloka/Prolific/Clickworker（待R1） | — | 国内无公开API·海外合规平台待授权 |
| H8·成长成就 | Open Badges+badgr-server/Oasis（B类） | Trophy.so（小规模免费） | Steam Web API（A类·成就数据） | Steam是端口H8唯一A类情报源 |

---

## 四、合规严筛排除项（H赛道特别 · 重点章节）

> H赛道是灰产重灾区。"宁可少接不碰灰产"是本赛道首要原则。

### 4.1 一票否决类（法律追诉/ToS明确禁止）

| 项目 | 类型 | 排除原因 |
|------|------|---------|
| bilibili-API-collect | 逆向API文档 | 2026-01-28已收B站律师函·停止维护删除文档·法律追诉风险 |
| 所有B站逆向接入路径 | 逆向工程 | B站律师函已发·逆向路径全部封禁 |
| 自制RSSHub路由（爬电商活动） | 自建爬虫 | 触犯probe"永不代爬"红线 |

### 4.2 灰产一票否决类（任务/问卷刷量生态）

| 类型 | 典型项目 | 排除理由 |
|------|---------|---------|
| 网赚问卷站 | 收奖网、爱调查 | 灰产薅羊毛刷量·数据质量极差·法律风险 |
| 刷单任务平台 | 各类"接单平台" | 刷单违法·灰产一票否决 |
| 刷量/虚假互动悬赏 | 虚假关注任务站 | 平台ToS违规+灰产 |
| 拉人头任务站 | 各类返利APP | 传销特征·灰产 |
| 逆向爬取众包平台 | 阿里众包爬取等 | 无官方API即无程序化接入路径·不代爬 |
| BiliBiliToolPro执行能力 | BiliBiliToolPro | 账号自动化违B站ToS·禁止执行能力接入probe（仅可参考规则结构） |

### 4.3 条件性排除（不满足条件则排除）

| 项目 | 条件 | 排除原因（若不满足） |
|------|------|------------------|
| 问卷星 | 需完整PIPL合规方案·PII不落probe库 | 个人数据合规成本高 |
| Formbricks | 需法务确认AGPLv3商业使用传染性 | AGPLv3商业使用风险 |
| RefRef | 需法务确认AGPLv3商业使用传染性 | AGPLv3商业使用风险 |
| Steam Web API | 禁止数据商业再出售（ToS明确） | 违ToS |
| Toloka | 需确认数据居留合规（境外存储） | 数据跨境合规风险 |

### 4.4 成本不合理类（排除）

| 项目 | 原因 |
|------|------|
| Qualtrics | $5040/年起·成本不合理 |
| Scale AI | $93000/年起+sales流程·不适合自动化 |
| 小红书蒲公英API | 年消耗≥500万方可申请·门槛过高 |

---

## 五、待授权清单（R1/R4）

> R1 = 需元东方付费授权确认 · R4 = 需元东方资产使用授权

| 项目 | 端口 | 授权类型 | 预估成本 | 说明 |
|------|------|---------|---------|------|
| Prolific | H6/H7 | R1 | 按参与者付费·平台费33.5% | 海外调研/RLHF众包首选·待预算确认 |
| Cint/Lucid | H6 | R1 | 企业级·商务对接 | 中期大规模样本·需销售流程 |
| Phyllo | H5 | R1 | $20000/年起 | 多平台创作收益聚合·昂贵 |
| Clickworker | H7 | R1 | 按任务付费 | 欧洲合规众包平台 |
| Trophy.so（规模化） | H8 | R1 | 100 MAU以上需付费 | 小规模先免费验证 |
| 穿山甲Open API | H2 | R1 | 需企业资质开户 | 激励视频schema权威参考 |
| Toloka | H7 | R1 + 合规确认 | 按任务付费 | 需先确认数据居留合规 |

---

## 六、覆盖缺口与对策（核心）

### 6.1 全局性缺口：规则情报源结构性稀缺

H赛道最根本的缺口不是调研不足，而是**结构性现实**：

各平台任务规则（签到积分/浏览赚金币/裂变助力/消费返利）属于内部运营配置，既是竞争壁垒，也是防薅羊毛的安全设计（如砍价随机算法从设计上就不透明）。没有任何商业激励驱动平台开放这类规则数据。

**应对路径**：
```
官方公告/帮助中心页 → RSSHub订阅变更事件 → 规则文本变更触发 → NLP提炼规则schema → 入probe规则知识库
```

### 6.2 逐端口缺口明细

| 端口 | 缺口性质 | 对策 |
|------|---------|------|
| H1·签到打卡 | 规则内部配置·无API | RSSHub监测公告+公开页schema提炼 |
| H2·浏览观看 | "浏览积分"规则无API·激励广告与之不同 | 穿山甲schema建模+公告监测 |
| H3·分享裂变 | 三层均空白·平台有意不透明 | 活动公告NLP+人工整理cracking cases |
| H4·消费下单 | 无外部情报源 | OpenLoyalty自建schema+帮助中心变更监测 |
| H5·创作产出 | 国内全封闭（律师函/无API） | YouTube Analytics自助查；国内只能运营公告文本 |
| H6·答题问卷 | 中文受访者panel合规路径有限 | 问卷星（条件性）·国内独立合规方案 |
| H7·众包悬赏 | 国内平台（阿里/百度）无公开API | 先Label Studio自托管·国内场景另行方案 |
| H8·成长成就 | 中文平台全封闭；养成数据平台锁定 | Open Badges标准建schema·Steam作为参考基准 |

### 6.3 亮点端口（可立即落地）

- **H6/H7** 的层1开源工具（Label Studio / CVAT / LimeSurvey / Formbricks）：Apache/GPL许可，自托管，API完整，**零成本可立即自托管验证**
- **H8** 的Open Badges 3.0标准（edubadges fork）：国际开放标准，可直接建成就schema，**是整个H赛道schema质量最高的层1资产**
- **H4** 的OpenLoyalty：Apache-2.0，月处理10亿事件，**是消费积分规则引擎最完整的底座**
- **H5** 的YouTube Analytics：官方API，每日10000 quota免费，**国内外创作收益唯一可API化的权威源**

---

## 七、对接批次建议

### 接batch-plan B4执行顺序

**阶段一：零成本层1开源工具自托管（立即可启动）**

优先级顺序及理由：

1. **Label Studio**（端口H7·Apache-2.0·license最干净）→ 自托管验证众包标注底座
2. **LimeSurvey**（端口H6·GPL·注意传染性）→ 问卷发放工具层验证
3. **Formbricks**（端口H6·AGPL-v3·法务确认后）→ 现代问卷工具并行验证
4. **OpenLoyalty**（端口H4·Apache-2.0）→ 消费积分规则引擎自托管
5. **badgr-server/edubadges fork**（端口H8·开放标准）→ Open Badges成就schema建立
6. **Oasis**（端口H8·Apache-2.0·注意开发中状态）→ 事件驱动成就引擎评估
7. **CVAT**（端口H7·MIT）→ 图像/视频标注底座（可与Label Studio并行）

**阶段二：RSSHub规则监测层（与阶段一并行）**

- 部署RSSHub订阅各端口相关平台官方公告频道
- 建立规则变更事件流 → NLP提炼schema流水线
- 重点端口：H1/H2/H3/H4（规则情报A类源最稀缺的四个端口）

**阶段三：YouTube Analytics接入（待账号OAuth验证）**

- 端口H5唯一A类情报源，免费quota充足
- 需创作者账号绑定OAuth，不能跨账号

**阶段四：待授权商业平台（R1确认后）**

按优先级：
1. **Prolific**（端口H6/H7）→ 最合规API最完整·待预算
2. **穿山甲Open API**（端口H2）→ 需企业资质开户
3. **Toloka**（端口H7）→ 需先确认数据居留合规再申请
4. **Clickworker**（端口H7）→ 欧洲合规众包平台
5. **Cint/Lucid**（端口H6）→ 商务对接·中期大规模
6. **Phyllo**（端口H5）→ 昂贵·多平台统一后期方案

**阶段五：Steam Web API（端口H8·A类参考源）**

- 免费key·注意ToS禁商业再出售
- 用于成就解锁率/排行榜数据作为游戏化成就设计参考基准

---

> 文档状态：v1.0 调研证据层完成 · 待接batch-plan B4执行
> 下游文档：probe-track-registry-architecture（赛道注册表·H-task域配置）

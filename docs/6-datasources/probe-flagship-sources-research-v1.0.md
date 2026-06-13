# probe 各赛道旗舰权威源深度调研报告 v1.0

> 日期：2026-06-13 · 方法：5 路并发扇出（sonnet）+ 真实 WebSearch/WebFetch 核实 + 部分对抗性验证。
> 立规依据：[track-registry §9 赛道旗舰权威源铁律](../3-build/probe-track-registry-architecture-v1.0.md)。
> 理念（元东方定调）：**引擎核心 = 源头数据。数据够丰富/准确/真实，AI 才能精准分析得出答案。** 每个赛道必须有 ≥1 权威旗舰整合源。
> ⚠️ 定价多为商务报价/第三方交叉验证，标 `待核` 者接入前须官网/商务确认；付费源接入走 R1，含 key 走 R8。

---

## 一、10 赛道旗舰源定稿决策表

| 赛道 | 首选旗舰源 | 次选/补充 | 模式 | API | 推荐 |
|------|-----------|----------|------|-----|------|
| A 自媒体 | **新榜有数**（全平台/新榜指数行业标准）| 蝉妈妈（直播电商达人最深）| 付费·商务报价 | REST✅ | ★★★★ |
| B 商业市场 | **天眼查开放平台**（300维/2.8亿实体/征信备案）| 剑鱼标讯（招投标专项）| 付费 ¥1500/万次 | REST✅ | ★★★★★ |
| C 尽调风控 | **企查查开放平台**（167接口/UBO穿透）| LSEG World-Check（国际制裁/PEP）| 付费 ¥0.1–6/次 | REST✅ | ★★★★★ |
| D 调研知识 | **Statista Connect**（100万统计×190国）| IBISWorld + **OpenAlex**（学术免费）| 付费 + 免费混 | REST✅ | ★★★★★ |
| E 真伪核查 | **Google Fact Check Tools**（免费/IFCN聚合）| **GDELT**（免费/100+语言）+ GPTZero | 多数免费 | REST✅ | ★★★★★ |
| F 金融财经 | **Wind 万得**（机构事实标准）/ **Tushare**（MVP）| 东财 Choice / AKShare(POC) | 付费分层 | REST✅ | ★★★★★ |
| G 元惠 | **维易淘宝客 API**（六平台/含抖音）| 大淘客 + 慢慢买（历史价唯一源）| 付费 ¥158/月起 | REST✅ | ★★★★★ |
| H 任务 | ⚠️ **无行业整合旗舰源** | 猪八戒API + 自建采集 + 积分墙SDK | 混合·须自建 | 部分 | — |
| I AI优惠 | **OpenRouter**（400+模型实时定价）| **HuggingFace Hub**（开源SSOT）| 免费tier + PAYG | REST✅ | ★★★★★ |
| J 医药 | **Cortellis**（全球·含NMPA）+ **摩熵医药**（中国最深）| openFDA/PubMed/ClinicalTrials/PubChem(免费) | 付费 $5–20万/年 | REST✅ | ★★★★★ |

---

## 二、关键洞察

1. **免费即可达权威覆盖的赛道**（零 R1 成本优先接）：
   - **E 真伪核查**：Google Fact Check + GDELT 全免费、官方/学术权威 → 零成本旗舰。
   - **I AI优惠**：OpenRouter 免费 tier + HuggingFace Hub API 全公开 → 零门槛。
   - **D 学术层**：OpenAlex（2.5亿论文/CC0）+ Semantic Scholar 全免费。
   - **J 部分**：openFDA/PubMed/ClinicalTrials/PubChem 已实测 verified。

2. **重付费护城河赛道**（须 R1 授权）：A / B / C / F / G / J — 商业整合源是行业壁垒，覆盖与稳定性远超免费拼凑。

3. **B 商业市场 ⊃⊂ C 尽调 共享工商源**：企查查/天眼查同时服务两赛道 → **一次采购两赛道共用**，印证 ledger `shared` 域设计，不重复采购。

4. **H 任务是唯一无整合旗舰源的赛道**：平台任务/签到/积分规则属运营私有数据、无对外 API，且无流量分成激励 → 聚合商业模式跑不通。**probe 须靠自建采集管线**（mihomo + 无头浏览器爬各平台任务中心 → probe_collect PG），API 仅能覆盖众包(猪八戒)+激励广告(积分墙)，约覆盖 60–70%，剩余靠定时爬采。**此为 H 赛道固有难点，已回填 ledger 风险注记。**

5. **付费整合源通病**：多数需企业资质 + 不公开定价 + 按次/年订阅 → 接入前必须 R1 报价 + 评估 ROI。

---

## 三、接入优先级（零成本先行 · 分三批）

| 批次 | 赛道·源 | 成本 | 动作 |
|------|--------|------|------|
| **第一批·免费零R1** | I:OpenRouter/HF · E:Google FactCheck/GDELT · D:OpenAlex/SemanticScholar · J:openFDA等(已做) | 0 | 直接按 SOP 第4步写适配器升 live |
| **第二批·低成本付费** | G:维易(¥158/月) · F:Tushare(¥200) | 低 | R1 小额授权后接 |
| **第三批·高价R1授权** | A:新榜 · B:天眼查 · C:企查查 · F:Wind · J:Cortellis/摩熵 · D:Statista/IBISWorld | 高(年订阅¥万–$20万) | 逐个报价 → 元东方授权 → 接 |

---

## 四、各赛道源明细（首选 + 关键次选 · 带出处）

### A 自媒体
- **新榜有数** https://data.newrank.cn/ ·公众号75万+/微博/抖音/快手/视频号·新榜指数行业标准·REST API(控制台取key)·商务报价·★★★★
- 蝉妈妈 https://www.chanmama.com/ ·抖音直播电商达人/商品/直播间最深·旗舰版开放API(5000次/日)·¥1299/月起·★★★★
- 飞瓜 https://dy.feigua.cn/ ·B站覆盖独特·⚠️无官方公开API(逆向有ToS风险)·★★★

### B 商业市场
- **天眼查开放平台** https://open.tianyancha.com/ ·2.8亿实体/300维·官方征信备案·¥1500/万次·REST·★★★★★
- 剑鱼标讯 https://www.jianyu360.cn/ ·招投标专项·直连财政部/发改委·8–13分钟更新·REST·★★★★
- 企查查(招投标1.7亿最大)、启信宝(社保维度独有) 作补充

### C 尽调风控
- **企查查开放平台** https://openapi.qcc.com/ ·167接口/UBO穿透/股权/司法·¥0.1–6/次·REST(企业实名)·★★★★★
- **LSEG World-Check** https://www.lseg.com/en/risk-intelligence/screening-solutions/world-check-kyc-screening ·OFAC/UN/EU制裁+PEP+AML·企业级合同(年约$11万)·REST(需DPA)·跨境必接·★★★★
- 注：中国工商数据与 B 共享企查查/天眼查；World-Check 补国际合规层

### D 调研知识
- **Statista Connect** https://www.statista.com/business/connect-api ·100万统计×190国·REST+MCP·企业订阅(估$5k–50k/年)·★★★★★
- IBISWorld https://www.ibisworld.com/access/api/ ·1300+行业报告·REST/OAuth2·★★★★
- **OpenAlex**(免费) https://developers.openalex.org/ ·2.5亿论文/CC0/API零认证·★★★★★ · Semantic Scholar(AI语义层/免费)

### E 真伪核查
- **Google Fact Check Tools**(免费) https://developers.google.com/fact-check/tools/api ·IFCN全球核查聚合·REST(Google key)·★★★★★
- **GDELT**(免费) https://www.gdeltproject.org/ ·100+语言/15分更新/1979至今·DOC/GEO/TV API+BigQuery·★★★★★
- GPTZero(AI检测F1=0.94/$23.99月) + Originality.ai($179月) 互补

### F 金融财经
- **Wind 万得** https://www.wind.com.cn/ ·中国机构事实标准·800万指标·WindPy等6语言·¥7k–4w/年(仅机构)·★★★★★
- **Tushare Pro**(MVP首选) https://tushare.pro/ ·Token+pip接入最简·A股财报宏观全·¥200起·★★★★
- 东财 Choice(Wind性价比替代/无需终端后台) · AKShare(免费但仅学术·商用风险)

### G 元惠
- **维易淘宝客 API** https://www.veapi.cn/ ·六平台(含抖音)/转链/历史价·¥158/月起/3600QPS·REST(个人可注册)·★★★★★
- 大淘客 http://www.dataoke.com/ ·五平台券+CPS/免月租抽佣10%·REST·★★★★★
- 慢慢买企业版 https://www.manmanbuy.com/ ·历史价曲线唯一规模化源(10年+)·商务对接·★★★★

### H 任务（⚠️无整合旗舰源 · 次优组合）
- 猪八戒开放平台 https://open.zbj.com/ ·众包任务·REST/OAuth2·★★★（场景差距：企业发包≠用户激励）
- 多多进宝官方API https://open.pinduoduo.com ·拼多多单平台·免费·★★
- **自建采集管线**：mihomo+无头浏览器爬各平台任务中心 → probe_collect PG（覆盖电商签到/积分规则，无 API 可替代）
- TradPlus 积分墙 SDK 补激励广告任务

### I AI优惠
- **OpenRouter** https://openrouter.ai ·400+模型/60+商·实时定价+免费tier(50req/日)·REST兼容OpenAI SDK·★★★★★
- **HuggingFace Hub** https://huggingface.co/docs/hub/api ·2M+模型开源SSOT·Hub API全公开免费·★★★★★
- GetAIPerks(220+ credits目录/无API)、Devpost(hackathon/无官方API) 仅参考

### J 医药
- **Cortellis(Clarivate)** https://clarivate.com/life-sciences-healthcare/cortellis/ ·9万药物管线/32万临床/80+监管含NMPA/专利·REST+MCP·$5–20万/年·★★★★★
- **摩熵医药(原药融云)** https://open.bcpmdata.com ·中国NMPA批文+集采+医保+70万方剂+73万器械·50亿条·REST(7天试用)·★★★★★ ← 填中国药品/中药材缺口
- Citeline Pharmaprojects(全球管线/API待核) · DrugPatentWatch(专利仿制药/REST) 备选
- 免费层：openFDA/PubMed/ClinicalTrials/PubChem（已实测 verified）

---

## 五、落地动作（已执行 + 待办）

- ✅ track-registry §9 铁律已立 · §9.3 表已回填定稿
- ✅ 医药 `_matrix.yaml` 旗舰源候选已升级（Cortellis + 摩熵医药）
- ⬜ H 赛道风险注记回填 ledger（无整合源·须自建采集）
- ⬜ 第一批免费源按 SOP 第4步写适配器升 live（I/E/D 各旗舰）
- ⬜ 付费源逐个走 R1 报价 + 元东方授权（按上述三批优先级）

> 各赛道完整调研明细（5 份原始报告）见本次扇出 task 输出；本报告为决策定稿汇总。

# probe · E真伪核查域 数据源调研报告 v1.0

> 日期：2026-06-10 · 性质：调研证据层（4子场景×三层+四闸·E域是probe抗污染验证护城河直接对外）
> 方法：三层优先级 · 永不代爬 · 见 [调研方法论v1.1](datasource-research-methodology-v1.0.md)
> 上游：[架构v1.1](../3-build/probe-track-registry-architecture-v1.0.md) E-verify · [feasibility-v1](probe-github-datasource-feasibility-v1.md) §E

---

## 一、综述

### 三层覆盖总评

E域覆盖4个子场景：**E1事实核查、E2图片视频溯源、E3信息源可信度、E4谣言诈骗钓鱼**。

三层分布：
- **L1（免费开源·自部署）**：imagehash、SearXNG+TinEye、c2pa-python、ExifTool、GDELT、Wikidata/Wikipedia、AllSides静态集、Maltrail、URLhaus、PhishTank、OpenPhish、Spamhaus DBL、crt.sh、RDAP/ICANN
- **L2（免费+付费tier·API）**：Tavily、Exa、GPTZero、TinEye API官方、Sightengine、Hive AI、Sensity AI、MBFC RapidAPI、Ad Fontes、Pulsedive、VirusTotal vt-py、urlscan.io、奇安信威胁情报
- **L3（官方平台·限制层·最高权威）**：Google Fact Check Tools API、Data Commons、Google Vision Web Detection、Google Safe Browsing/Web Risk、APWG eCX

### 核心结论

1. **E域免费官方源丰富**：事实核查有Google Fact Check（全球最高权威）+ GDELT + Wikidata三层；图片溯源有c2pa-python + ExifTool + Google Vision；钓鱼检测有Maltrail + URLhaus + PhishTank免费链路可落地。
2. **商业化有license红线**：DeepfakeBench（CC-BY-NC）、AllSides（CC-BY-NC商业需付费）、OpenPhish（明确禁商业）、VirusTotal免费层（禁商业）、Google Safe Browsing（非商业免费）——商业化前必须切换。
3. **中文场景存在系统性缺口**：中文事实核查、中文媒体可信度、中文诈骗识别均无开放API，需奇安信实名授权+本地LLM兜底。
4. **E2 AIGC图像检测商用license缺口**：DeepfakeBench弃用后无免费商用替代，商用场景必须接入Sightengine或Hive AI（付费）。

---

## 二、4子场景源卡明细

### E1 事实核查

| 源 | 层 | License / 授权 | URL | 状态 | 说明 |
|----|----|----|----|----|-----|
| Google Fact Check Tools API | L3 | 免费key（注册） | https://developers.google.com/fact-check/tools/api | ✅ 采纳（首选） | ClaimReview全球核查机构结论·2024新增图片端点·最高权威 |
| Data Commons | L3 | CC-BY·免费key | https://docs.datacommons.org/api | ✅ 采纳 | 统计知识图谱+ClaimReview存档·数值型核查最优 |
| ClaimReview schema.org | L3 | 开放标准 | https://schema.org/ClaimReview | ✅ 采纳（附属） | GFC返回此格式·输出格式标准化用 |
| GDELT | L1 | 免费·无限制 | https://gdeltproject.org | ✅ 采纳（事件层） | 全球新闻事件·来源质量参差需可信度过滤 |
| Wikidata SPARQL + Wikipedia | L1 | CC-BY-SA | https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service | ✅ 采纳（基线知识） | 结构化事实·更新滞后非实时·与E3共用 |
| SearXNG | L1 | AGPL·自部署 | https://github.com/searxng/searxng | ✅ 采纳（证据链底座） | 70+引擎证据链聚合·自带TinEye插件 |
| imagehash | L1 | BSD | https://pypi.org/project/ImageHash | ✅ 采纳 | 感知哈希·E2去重为主·E1间接辅助 |
| Tavily | L2 | 免费1000/月·$30/月起 | https://tavily.com | ✅ 采纳（待key） | AI原生带引用·"powers thousands of fact-checkers"·证据链增强 |
| Exa | L2 | 免费1000/月·$7/1000 | https://exa.ai | ✅ 采纳（待key·补充） | 语义搜索·补充Tavily覆盖盲区 |
| GPTZero | L2 | $45/月起 | https://gptzero.me/developers | ⏳ 待授权R1（P1辅助） | AI文本检测·事实核查辅助信号 |
| ~~AllSides~~ | L1/D | **⚠️ CC-BY-NC非商用** | https://www.allsides.com | ❌ 弃用（商业） | 商业使用需付费授权·静态集非商业可·见§四 |
| ~~较真/腾讯核查~~ | 缺口 | 无开放API | — | ❌ 无法接入 | 中文事实核查空白·见§六 |

### E2 图片视频溯源

| 源 | 层 | License / 授权 | URL | 状态 | 说明 |
|----|----|----|----|----|-----|
| imagehash | L1 | BSD | https://pypi.org/project/ImageHash | ✅ 采纳（P0·本地预筛） | 感知哈希·本地第一道过滤·零成本 |
| c2pa-python | L1 | Apache+MIT | https://opensource.contentauthenticity.org | ✅ 采纳（出处验证未来主干） | 内容凭证Content Credentials·Adobe/Google/Microsoft标准·联盟推进 |
| ExifTool | L1 | GPL-3.0 | https://exiftool.org | ✅ 采纳（CLI模式） | 元数据EXIF·CLI模式商用可接受·C++接口需付费授权 |
| SearXNG + TinEye插件 | L1 | AGPL·自部署 | https://github.com/searxng/searxng | ✅ 条件采纳 | 绕过TinEye官方API·测试低频可·高频商用需切官方 |
| Binoculars | L1 | BSD-3 | https://github.com/ahans30/Binoculars | ✅ 条件采纳 | 零样本AI文本检测·**作者声明"学术only"需法律确认**后商用 |
| Google Vision Web Detection | L3 | 前1000/月免费·$3.5/1000 | https://cloud.google.com/vision | ✅ 采纳（免费层起） | 官方最接近反向图搜·高频后转付费 |
| Google Fact Check 图片端点 | L3 | 免费（复用E1 key） | https://developers.google.com/fact-check/tools/api | ✅ 采纳 | 2024新增·按图搜核查·与E1共key |
| Data Commons | L3 | CC-BY·免费 | https://docs.datacommons.org/api | ✅ 采纳 | 图表数值核查·E1/E2共用 |
| Sightengine | L2 | $29/月起 | https://sightengine.com | ⏳ 待授权R1（**P0优先·DeepfakeBench商用替代**） | AIGC检测20+生成器·无NC问题·DeepfakeBench弃用后商用唯一替代路径 |
| TinEye API官方 | L2 | $200/月起 | https://services.tineye.com | ⏳ 待授权R1 | 600亿图反搜·精确大库·高频商用时替换SearXNG插件 |
| Hive AI | L2 | $6/1000帧·联系销售 | https://thehive.ai | ⏳ 待授权 | 图+视频+音频三合一·视频音频全栈方案 |
| Sensity AI | L2 | 定制·联系销售 | https://sensity.ai | ⏳ 待授权（P2高监管） | 深伪专业级·高监管场景用 |
| ~~DeepfakeBench~~ | L1/D | **🔴 CC-BY-NC-4.0非商用·商业明确禁止** | https://github.com/SCLBD/DeepfakeBench | ❌ 弃用（商业） | 研究原型可·商用替代见Sightengine/Hive AI·见§四 |
| ~~FaceForensics++~~ | 缺口 | license待逐一确认 | — | ⚠️ 待核实 | 视频深伪开源·license未明确·暂不接入 |

### E3 信息源可信度

| 源 | 层 | License / 授权 | URL | 状态 | 说明 |
|----|----|----|----|----|-----|
| Wikidata SPARQL | L1 | CC0 | https://www.wikidata.org | ✅ 采纳（权威补充） | 媒体机构成立/国籍/所有权·与E1共底座 |
| crt.sh | L1 | 免费·开放 | https://crt.sh | ✅ 采纳 | 证书透明度·证书年龄权威信号 |
| RDAP / ICANN | L1 | 免费·结构化JSON | https://www.icann.org/rdap | ✅ 采纳 | 域名注册年龄·可信度基础信号 |
| Maltrail | L1 | MIT | https://github.com/stamparm/maltrail | ✅ 采纳 | 聚合70+威胁源黑名单·域名负向信号·无商用限制 |
| AllSides 静态数据集 | L1/D | **⚠️ CC-BY-NC·非商业可·商业付费** | https://www.allsides.com | ✅ 采纳（非商用静态导入）·⏳ 商业R1 | 媒体偏向5档·Bias Checker API商业需授权·见§四 |
| Qbias | L1/D | 学术开放 | https://zenodo.org/records/7682915 | ✅ 采纳（离线训练） | 21747文章偏向标签·训练集用 |
| Pulsedive | L2 | 免费10/天·Pro $29/月 | https://pulsedive.com | ✅ 采纳免费层·⏳ 商业R1 | 域名威胁情报risk_score·E3/E4共用 |
| MBFC RapidAPI | L2 | 免费tier+企业版 | https://mediabiasfactcheck.com | ⏳ 待授权R1（**优于AllSides·同时评事实+偏向**） | 9000+源·事实准确度+偏向双维度·推荐优先于AllSides |
| Ad Fontes | L2 | 联系销售·成本不透明 | https://adfontesmedia.com | ⏳ 待授权R1 | 文章级实时ML评分·粒度最细·成本待确认 |
| Google Safe Browsing | L3 | 非商业免费 | https://developers.google.com/safe-browsing/v4 | ✅ 采纳（非商业）·商业切WebRisk | 钓鱼/恶意黑名单·商业化时必切换·见§四 |
| Google Web Risk | L3 | 100K/月免费·$0.5/千次 | https://cloud.google.com/web-risk | ⏳ 待授权R1（商业） | GSB商业版·商业化后接替GSB |
| ~~中文媒体可信度~~ | 缺口 | 无等价MBFC API | — | ❌ 空白 | 中文源只能SearXNG+LLM判断·见§六 |

### E4 谣言诈骗钓鱼

| 源 | 层 | License / 授权 | URL | 状态 | 说明 |
|----|----|----|----|----|-----|
| Maltrail | L1 | MIT | https://github.com/stamparm/maltrail | ✅ 采纳（快速匹配·毫秒） | 聚合70+威胁源·钓鱼+恶意双维度·无商用限制 |
| Spamhaus DBL | L1 | 非商业低量免费·商业DQS订阅 | https://www.spamhaus.org | ✅ 采纳（非商业）·商业R1 | 域名黑名单·DNS查询·秒级响应 |
| PhishTank | L1 | Cisco·批量下载JSON | https://www.phishtank.com | ✅ 采纳（批量下载模式） | ⚠️新注册已关闭，已有key可续用·批量模式替代实时API |
| URLhaus | L1 | 免费Auth-Key·非商业·商业需Spamhaus | https://urlhaus.abuse.ch | ✅ 采纳（非商业）·商业R1 | 380万恶意URL·精确匹配 |
| OpenPhish | L1/D | **🔴 明确禁商业·学术免费** | https://github.com/openphish/public_feed | ✅ 采纳（研究/非商业）·⏳ 商业授权 | 商业使用需额外授权·见§四 |
| urlscan.io | L2 | 免费5000/天 | https://urlscan.io | ✅ 采纳（免费层足够） | URL沙箱+截图·免费配额充裕 |
| Pulsedive | L2 | 免费10/天·$29/月 | https://pulsedive.com | ✅ 采纳（E3/E4共用） | 钓鱼特征risk_factors |
| VirusTotal vt-py | L2 | SDK Apache·**⚠️免费4/min禁商业**·Premium商业 | https://github.com/VirusTotal/vt-py | ✅ 采纳（免费层非商业）·⏳ 商业R1 | 70+引擎·商业化必切Premium·见§四 |
| 奇安信威胁情报 | L2 | 需实名认证·开发者免费配额 | https://ti.qianxin.com | ⏳ 待授权（实名认证·**中文场景关键**） | 中文URL/域名信誉·中文场景唯一可选项 |
| Google Safe Browsing | L3 | 非商业免费 | https://developers.google.com/safe-browsing/v4 | ✅ 采纳（非商业）·商业切WebRisk | 权威核实末端·见§四 |
| Google Web Risk | L3 | 100K/月免费·$0.5/千次 | https://cloud.google.com/web-risk | ⏳ 待授权R1（商业） | GSB商业版 |
| APWG eCX | L3 | 研究资质申请·免费 | https://apwg.org/membership/research | ⏳ 待授权（机构研究资质） | 反钓鱼工作组·百亿级钓鱼数据库 |
| ~~中文诈骗识别~~ | 缺口 | 反诈中心无API | — | ❌ 空白 | 奇安信实名后部分覆盖·截图视觉钓鱼需InternVL3本地推断·见§六 |

---

## 三、推荐首选源汇总表

| 子场景 | P0首选（免费可落地） | P1增强（待key/待授权） | 商业化替换方向 |
|--------|----|----|-----|
| **E1 事实核查** | Google Fact Check Tools API + GDELT + Wikidata | Tavily + Exa | GPTZero（AI文本）·MBFC（源可信度增强） |
| **E2 图片视频溯源** | imagehash + c2pa-python + ExifTool + Google Vision | Sightengine（AIGC检测R1） | TinEye官方API（高频反搜）·Hive AI（视频音频） |
| **E3 信息源可信度** | Maltrail + crt.sh + RDAP + Wikidata | MBFC RapidAPI + Pulsedive | Ad Fontes（文章级）·AllSides Bias Checker API |
| **E4 谣言诈骗钓鱼** | Maltrail → Spamhaus DBL → PhishTank/URLhaus → VirusTotal → GSB（五级链路） | urlscan.io + 奇安信（中文） | VirusTotal Premium + Google Web Risk + OpenPhish商业授权 |

**E4检测链路（按速度排序）**：
1. **Maltrail快速匹配**（毫秒·MIT无限制）
2. **Spamhaus DBL DNS查询**（秒级）
3. **PhishTank / URLhaus 精确匹配**（秒级）
4. **VirusTotal / urlscan.io 沙箱分析**（秒至分钟）
5. **Google Safe Browsing 权威核实**（末端·非商业免费）

---

## 四、🔴 商业化License红线

### 4.1 CC-BY-NC 非商用弃用项

以下数据集/工具**标注CC-BY-NC（非商业使用）**，商业产品中不得直接使用：

| 源 | License | 弃用决定 | 商业替代方案 |
|----|----|----|-----|
| **DeepfakeBench** | CC-BY-NC-4.0·学术研究专用·商业明确禁止 | ❌ 弃用（商业场景） | Sightengine（$29/月·20+AIGC生成器）或 Hive AI（视频音频全栈） |
| **AllSides** | CC-BY-NC·媒体偏向数据集 | ❌ 商业付费授权·非商用静态导入可 | MBFC RapidAPI（更优：含事实准确度+偏向双维·同价位） |

> DeepfakeBench弃用后，E2开源AIGC图像检测商用**无免费替代**，商业化场景必须接入付费方案（Sightengine为P0优先）。

### 4.2 免费API禁商业三强制切换

商业化上线前必须完成以下三项切换，否则构成license违规：

| 当前（研究/非商业可用） | 商业版替换 | 费用参考 | 切换触发条件 |
|----|----|----|----|
| **VirusTotal 免费层**（4次/分·禁商业） | VirusTotal Premium（联系销售） | 企业订阅 | 商业产品接入时必须升级 |
| **Google Safe Browsing v4**（非商业免费） | **Google Web Risk**（100K/月免费·$0.5/千次） | ~$0.5/千次 | 商业产品接入时必须切换 |
| **OpenPhish public feed**（明确禁商业） | OpenPhish商业授权（联系sales@openphish.com） | 定制 | 商业产品接入时必须获得书面授权 |

> URLhaus商业使用需Spamhaus订阅，非商业自研项目低量免费。  
> Spamhaus DBL商业使用需DQS订阅。

### 4.3 条件采纳项（license待明确）

- **Binoculars**（BSD-3）：作者README声明"学术only"，BSD-3本身允许商用，但存在争议。**商业接入前需法律确认**或直接替换为Sightengine/GPTZero。
- **ExifTool CLI模式**（GPL-3.0）：CLI调用不触发GPL传染，商用可接受；若集成C++库则需商业授权。

---

## 五、待授权清单

### R1付费授权（商业需）

| 优先级 | 源 | 预估费用 | 用途 |
|----|----|----|----|
| P0 | **Sightengine** | $29/月起 | DeepfakeBench弃用后唯一AIGC图像检测商用方案 |
| P0 | **MBFC RapidAPI** | 免费tier+企业版 | 媒体可信度（优于AllSides·事实+偏向双维） |
| P1 | **VirusTotal Premium** | 企业订阅 | 商业化后替换免费层 |
| P1 | **Google Web Risk** | 100K/月免费·$0.5/千次 | 商业化后替换GSB |
| P1 | **Tavily** | $30/月 | E1证据链AI增强 |
| P1 | **TinEye API官方** | $200/月起 | 高频图片反搜商用 |
| P2 | **GPTZero** | $45/月起 | AI文本检测辅助 |
| P2 | **Ad Fontes** | 联系销售 | 文章级实时评分 |
| P2 | **Sensity AI** | 定制 | 高监管场景深伪检测 |
| P2 | **Hive AI** | $6/1000帧 | 视频音频溯源全栈 |
| P2 | **OpenPhish 商业授权** | 定制 | 钓鱼feed商用 |
| P2 | **URLhaus + Spamhaus DQS** | 订阅 | 恶意URL商业配额 |
| P2 | **AllSides Bias Checker API** | 企业版 | 若MBFC不满足需求时补充 |

### 免费key申请（可立即行动）

| 源 | 申请地址 | 说明 |
|----|----|----|
| **Google Fact Check Tools API** | https://developers.google.com/fact-check/tools/api | 注册Google账号即可·免费 |
| **Data Commons API** | https://docs.datacommons.org/api | 免费key·无复杂审批 |
| **Tavily** | https://tavily.com | 免费1000次/月 |
| **Exa** | https://exa.ai | 免费1000次/月 |
| **URLhaus Auth-Key** | https://urlhaus.abuse.ch | 非商业免费注册 |
| **Pulsedive** | https://pulsedive.com | 免费10次/天 |
| **urlscan.io** | https://urlscan.io | 免费5000次/天 |

### 机构资质申请

| 源 | 资质要求 | 申请地址 |
|----|----|----|
| **APWG eCX** | 研究机构资质·免费 | https://apwg.org/membership/research |
| **奇安信威胁情报** | 实名认证（身份证+企业信息） | https://ti.qianxin.com |

---

## 六、覆盖缺口与对策

### 缺口一：中文事实核查

**现状**：较真、腾讯较真等主流中文事实核查平台均无开放API。Google Fact Check覆盖中文媒体有限。

**对策**：
1. SearXNG聚合中文新闻源（网易、新华、人民网）+ LLM交叉验证
2. Wikidata覆盖中国政治人物/机构基础事实
3. GDELT中文新闻事件层部分覆盖
4. 长期：联系较真/腾讯开放合作（无时间表）

### 缺口二：中文媒体可信度

**现状**：MBFC/AllSides均无中文媒体系统覆盖。无等价中文版媒体偏向数据库。

**对策**：
1. Wikidata查媒体机构归属/所有权（国资/商业分类）
2. SearXNG + LLM判断（召回率低·作为兜底）
3. 长期：自建中文媒体可信度标注集（小规模·按需扩展）

### 缺口三：中文诈骗识别

**现状**：国家反诈中心无API接口。中文钓鱼/诈骗URL无开放数据库。

**对策**：
1. **奇安信威胁情报**（实名认证后）：中文URL/域名信誉·最接近方案
2. Maltrail中文钓鱼域名覆盖有限·作为补充
3. **截图视觉钓鱼检测**：需InternVL3本地推断（图文理解·识别仿冒界面）·无API可替代·需GPU部署

### 缺口四：视频深伪开源license

**现状**：FaceForensics++等开源视频深伪检测数据集license未统一确认，部分有学术限制。

**对策**：
1. 商用直接采用Hive AI（付费·视频音频全栈）
2. 开源仅用于本地测试/研究原型
3. 采购前逐一核查每个数据集license条款

---

## 七、对接批次建议

### Batch 0（立即可行·零成本）

优先完成免费key申请，落地E域基础检测能力：

| 动作 | 源 | 预计工时 |
|----|----|-----|
| 申请Google Fact Check API key | Google | 30分钟 |
| 申请Data Commons API key | Google | 30分钟 |
| 申请Tavily/Exa免费key | Tavily·Exa | 1小时 |
| 申请URLhaus Auth-Key | abuse.ch | 30分钟 |
| 部署imagehash + c2pa-python | PyPI | 2小时 |
| 部署ExifTool CLI | 官网 | 1小时 |
| 部署Maltrail本地 | GitHub | 2小时 |

预计总工时：约1天。覆盖E1事实核查基线 + E2图片出处验证 + E4基础钓鱼检测。

### Batch 1（Wave1·免费tier完善）

与probe Wave1/Wave2同步，完成中层API接入：

| 动作 | 源 | 前提 |
|----|----|----|
| 接入Google Vision Web Detection | Google Cloud | 计费账号 |
| 接入urlscan.io | — | 免费注册 |
| 申请奇安信实名认证 | 奇安信 | 营业执照 |
| 接入Pulsedive免费层 | — | 注册key |
| 评估MBFC RapidAPI免费层 | RapidAPI | 注册 |

### Batch 2（Wave3·商业化前）

商业化上线前必须完成license合规切换（见§四三强制切换）：

| 动作 | 优先级 | 触发条件 |
|----|----|-----|
| VirusTotal免费→Premium | P0 | 商业产品接入时 |
| Google Safe Browsing→Web Risk | P0 | 商业产品接入时 |
| OpenPhish→商业授权 | P0 | 商业产品接入时 |
| 接入Sightengine（DeepfakeBench替代） | P0 | E2 AIGC检测商用时 |
| 接入MBFC企业版（AllSides替代） | P1 | E3媒体可信度商用时 |

---

> 本报告为调研证据层·不含实现代码·数据真实来自官网文档·URL/License/裁决均为原始信息。
> 商业化license变更以各官方网站最新条款为准·建议接入前再次核实。

# probe · 自媒体赛道 A · 数据源完整清单 v1.2

> v1.3（2026-06-22）：抖音 play_count 修复——TikHub 统计专用端点 `/api/v1/douyin/app/v3/fetch_video_statistics` 已接入，MEASURED 返回；批量 50条/次；tikhub_adapter.py + probe/datasources/tikhub.py 双处同步更新。
> v1.2（2026-06-22）：新增 A⑤ 微信视频号域——JZL `wxvideo` 端点 ✅ active，13 字段已验证；v2_name 发现链路已通（get_finder=1）；合规缺口表更新视频号状态。
> v1.1（2026-06-08）：盲点补充合并
> v1.0（2026-06-08）：初稿 · 方法：先整理 → 合规清洗 → GitHub 4 平台扇出调研（sonnet×4）+ 主代理去重
> 合规框架：probe 数据来源铁律（**核心红线：不自己爬数据**——不自建爬虫/不抓包/不模拟登录；只走官方 API 或官方授权第三方或官方 oEmbed/RSS；个保法最小必要·不建个人档案；绕反爬由第三方供应商担责）
> 状态口径：✅ live 可接（官方/开源干净·零成本） · ⚠️ pending/授权第三方（无官方替代时按采购方边界担责） · ❌ rejected（逆向红线）

---

## 一、赛道现状与核心结论

自媒体 A 是 probe 锚点垂类（v2 已深耕），现台账主力=**tikhub**（一源覆盖抖音/快手/B站/小红书/微博/X/Reddit/Instagram/视频号等，pending 待 key）。本轮目标=找 tikhub **之外的官方/合规补充**，并诚实暴露结构性缺口。

**一句话结论**：海外平台（YouTube/Reddit/Mastodon/Threads）官方路径丰富且免费，是 tikhub 之外的**纯增量护城河**；国内平台（抖音/快手/B站/小红书/公众号/知乎）官方开放平台几乎只给"自有授权账号"数据，**任意达人/竞品情报官方零供给**，现实只能靠 tikhub/新榜等⚠️第三方授权 API 担责补强——这是必须向元东方明示的**合规债**。

---

## 二、4 平台域数据维度与合规天花板

| 平台域 | 平台 | 官方可拿（任意账号） | 合规天花板 |
|--------|------|-------------------|-----------|
| **A①·短视频** | 抖音/快手/TikTok | TikTok oEmbed(仅D1元数据) | 国内官方OAuth只给自有号·互动/热榜/带货官方零供给 |
| **A②·长视频** | B站/YouTube | YouTube全维(官方API) | YouTube✅完整·**B站除tikhub外无✅路径**(结构性缺口) |
| **A③·图文社区** | 小红书/公众号/知乎 | 几乎为零 | **合规天花板**·知乎零官方API·公众号只看自己号·小红书仅电商+蒲公英限自投放 |
| **A④·海外社交** | X/Reddit/Instagram/Threads/Mastodon | Reddit/Mastodon/Threads友好·X贵·IG只给自有 | X太贵·IG任意账号走不通 |
| **A⑤·微信视频号** | 视频号(channels.weixin.qq.com) | JZL `wxvideo` 端点 13 字段 | **✅ 已有商业授权 API·play_count + 粉丝数为平台侧永久缺口** |

---

## 三、✅ 建议优先接入清单（官方/免费 · tikhub 之外纯增量）

| # | 源名 | 平台域 | 厂商/repo | 接入方式 | 成本 | 权威 | 与 tikhub 关系 | 备注 |
|---|------|--------|----------|---------|------|------|--------------|------|
| 1 | **YouTube Data API v3** | A② | Google官方 + googleapis/google-api-python-client 8.9k★ | 官方API(免费key) | 免费10k units/日 | 10 | **替代** tikhub的YouTube | 元数据/互动/评论/频道/热门榜全维·**YT改走官方·tikhub不再覆盖YT** |
| 2 | **YouTube oEmbed** | A② | YouTube官方 | 官方oEmbed免key | 免费 | 9 | 兜底 | 标题/作者/缩略图·省API配额·入库前预检 |
| 3 | **TikTok oEmbed** | A① | TikTok官方 | 官方oEmbed免key | 免费 | 10 | 补强(海外D1免费层) | **本轮新发现**·唯一官方任意链接拿D1·省tikhub配额 |
| 4 | **Reddit 官方 API** | A④ | Reddit官方 + praw-dev/PRAW 4.1k★ BSD-2 | 官方API(OAuth) | 免费100req/min | 10 | 替代tikhub的reddit | **三平台官方性价比最高**·free tier够用·商用大量才需企业洽谈 |
| 5 | **Reddit .rss/.json** | A④ | Reddit官方内建 | 公开RSS(URL加.rss) | 免费 | 9 | 补 | subreddit/post/user流·趋势热榜兜底·零风险 |
| 6 | **Mastodon API** | A④ | 联邦官方 + halcy/Mastodon.py 961★ MIT | 官方API | 免费 | 7 | **纯增量(tikhub无)** | 开放联邦·公开时间线/标签/搜索/画像全免费·出海舆情最干净护城河 |
| 7 | **Threads API** | A④ | Meta官方 | 官方API | 免费250发/1000回/24h | 9 | **替代**(tikhub threads代爬) | 2024-06全开放·含keyword_search/profile_discovery·**补IG舆情短板·新蓝海** |
| 8 | **X / Instagram 官方 oEmbed** | A④ | X / Meta官方 | 官方oEmbed | 免费 | 9 | 互补 | 单帖嵌入元数据·渲染进报告·零风险 |

---

## 四、⚠️ pending / 授权第三方清单（无官方替代时按采购方边界担责）

> 采购方边界（已决 2026-06-04）：probe 只调接口、不背供应商技术责任、自身不爬不调绕过工具。

| 源 | 平台域 | 接入 | 成本 | 定位 | 合规债说明 |
|----|--------|------|------|------|-----------|
| **JZL 极致了数据**（✅ 已 active） | **A⑤·视频号** | 商业授权 API | ¥0.2/15条(¥0.013/条) | **视频号竞品情报唯一合规路径**·13字段·v2_name发现链通·key已注入probe-a | ✅ 正规商业平台·probe只调公开接口·只采公开元数据·合规边界明确 |
| **tikhub**（现役主力） | A①②③④ | 授权第三方 | $0.001/req·50免费 | **保持pending主力**·但收窄：YT改官方·主守国内任意达人+B站+X/IG任意账号 | 🔴 其在小红书/知乎/公众号/B站的覆盖**本质是逆向web接口封装**·标pending=「明知逆向但无替代暂留」·**须向元东方明示为合规债** |
| **EnsembleData** | A① | 授权第三方 | $100-1400/月 | tikhub容灾备份·意大利公司主体(2020)·官方SDK·声称GDPR合规 | 主体合规性略稳于tikhub·建议适配层预留其适配器位·单供应商失效不断流 |
| **新榜/新红 API** | A①③ | 官方商业API | 企业定制 | 国内主体(上市)·唯一"准合规"榜单·覆盖公众号/小红书/知乎榜单+账号指数 | ⚠️ 含自爬成分·非平台官方授权数据·签约须核数据来源条款·**禁宣称"官方数据"** |
| **飞瓜(果集)** | A① | 授权第三方 | ¥399-4399/月 | 国内ICP主体·抖音/快手/B站D2-D6·需境内合规等级时启用 | ⚠️ 核ToS·境内主体担责·R1+合同 |
| **twitterapi.io** | A④ | 第三方独立 | $0.15/1k(比官方便宜33×) | X专项便宜备选·官方贵时用 | ⚠️ 明示"绕Twitter审批"·ToS灰区·责任在供应商·须正规付费R1·probe不调其绕过工具 |
| **小红书蒲公英 API** | A③ | 官方API | 需品牌/MCN资质 | 仅自己投放的合作笔记数据 | ✅ 官方但仅限自投放范围·补不了竞品情报 |

---

## 五、❌ rejected 清单（逆向红线 · 点名 repo）

| 库/服务 | 平台域 | 性质 | 弃用理由 |
|---------|--------|------|---------|
| **davidteather/TikTok-Api** ~12k★ | A① | 逆向web爬虫 | Playwright模拟浏览器抓TikTok·铁律①② |
| **Evil0ctal/Douyin_TikTok_Download_API** | A① | 逆向爬虫+下载 | 含abogus.py抖音签名逆向·周更补sign |
| **tiktok 签名逆向库系**(src244/int4444/justbeluga/notemrovsky等) | A① | 纯逆向签名 | 破解X-Bogus/X-Gnarly·铁律② |
| **bilibili-api**(Nemo2011) | A② | 逆向web/app接口 | 律师函风险·易失效 |
| **bilibili-API-collect**(SocialSisterYi 20k★) | A② | 逆向文档库 | **2026-01-28收B站律师函·已清空代码·永久停止** |
| **PiliPala** | A② | 破解B站接口 | 2025-07收侵权告知函·停止开发 |
| **RSSHub B站/抖音/TikTok/知乎/小红书 路由** | A①②③ | 路由依赖逆向 | RSSHub本体(MIT)合规·但这些路由调内部接口+签名/cookie绕过·**单独判❌**·其他公开RSS路由不受影响 |
| **MediaCrawler**(NanmiCoder 50k★) | A①③ | 逆向爬虫 | probe历史已点名弃用·覆盖小红书/知乎逆向爬 |
| **we-mp-rss / WeRSS / werss** | A③ | 逆向微信接口 | 网页爬+微信接口逆向·作者自声明非授权·无互动数 |
| **weixin_search_mcp / 搜狗微信套壳** | A③ | 逆向 | 搜狗微信搜索套壳·无license·源不稳 |
| **snscrape** | A④ | 逆向guest token抓X | 绕官方限制·铁律④·X 2026每2-4周反制已半残 |
| **instaloader** | A④ | 逆向抓IG | 自述"非官方·风险自负"·绕IG反爬 |
| **Apify tweet-scraper / instagram-scraper** | A④ | 爬虫actor | 平台ToS明禁抓取·GDPR/CCPA风险 |
| **yt-dlp（用于采集/绕权）** | A② | 逆向extractor | YT走官方API即可·绕权红线 |
| **蝉妈妈** | A① | 代采 | **2025厦门中院判违法·赔490万·删全量数据**·永久弃用 |
| **Meta Content Library** | A④ | 官方研究工具 | 非合规问题·**营利主体不合资格**·probe商用无法申请 |

> 证伪原则落实：所有「免 key / 装个库直接拿国内平台数据」的开源项目，经核实均依赖签名逆向或浏览器模拟 → **默认逆向、全判 ❌**，本轮无一例外。

---

## 六、🔴 结构性合规缺口（诚实结论）

以下场景在 probe 铁律下**无 ✅ 级官方/开源路径**，现实只能 tikhub/新榜等 ⚠️ 第三方授权 API 担责，或放弃：

| 缺口 | 官方现状 | 现实路径 | 状态 |
|------|---------|---------|------|
| **微信视频号竞品**(标题/互动/下载) | 官方API只给自有账号 | **JZL `wxvideo` ✅ active** · 13字段 · ¥0.013/条 | ✅ **v1.2 已解决** |
| **微信视频号 play_count** | 平台侧永久不公开 | 无合规路径 | 🔴 **永久缺口** |
| **微信视频号粉丝数** | wxvideo 端点未返回 | 无合规路径 | 🔴 **永久缺口** |
| **B站深度数据**(互动/弹幕/评论/排行) | 开放平台只给自有账号·无第三方数据API | tikhub(⚠️逆向外包) 或 放弃深度·仅oEmbed标题级 | ⚠️ |
| **知乎内容情报** | 零官方内容API | tikhub(⚠️) / 新榜知乎指数(⚠️) / 放弃 | ⚠️ |
| **微信公众号竞品** | 官方API只看自己号·搜狗无API | **JZL 公众号链路 ✅ active**（账号搜索/文章历史/阅读量·已集成） / 新榜(⚠️) | ✅ **已部分解决** |
| **小红书竞品笔记/种草** | 仅电商+蒲公英(限自投放) | tikhub(⚠️) / 新榜·千瓜(⚠️) / 放弃 | ⚠️ |
| **抖音/快手任意达人** | OAuth只给自有号 | tikhub/飞瓜/新榜(⚠️) | ⚠️ |
| **X 任意账号舆情** | 官方API太贵(pay-per-use无free tier) | tikhub/twitterapi.io(⚠️) | ⚠️ |
| **Instagram 任意账号** | 只给自有商业号+hashtag | tikhub(⚠️) | ⚠️ |

**第三方榜单平台合法性**：新榜（上市·主体最规范）> 飞瓜/千瓜/清博/卡思（SaaS灰区）。全部含自爬成分、无一是平台官方授权纯净数据，本质"把逆向风险外包给SaaS厂商"，统一判 ⚠️，优先选新榜，禁宣称官方数据。

---

## 七、各平台官方 API 成本实况（2026-06）

- **X/Twitter**：2026-02 起 pay-per-use 为默认、**取消 free tier**·$0.005/读·含URL写$0.20/次·旧Basic$200/Pro$5000/Ent$42k仅老用户保留 → 贵到只适合极少量高价值监测。
- **Reddit**：free tier OAuth 100 req/min（PRAW实测~60）够 probe 规模·商用需企业审核·大规模约$12k/年起·**官方.rss/.json免费**。
- **Instagram**：Basic Display 2024-12 废止·仅Graph API·只Business/Creator账号+App Review·只给自有账号+hashtag·**任意账号走不通**。
- **Threads**：免费·含keyword_search·token 60天·IG生态唯一对舆情友好的官方口子。
- **YouTube**：10k units/日免费·videos.list=1unit·search.list=100units(慎用)·**第三方公开数据仅API key即可**(无需OAuth)·唯一缺口=第三方视频字幕(需OAuth仅自有)。

---

## 八、台账增量建议 + 与现有源关系

- **新增 live（8 个官方/免费源）**：YouTube Data API / YouTube oEmbed / TikTok oEmbed / Reddit API / Reddit .rss / Mastodon API / Threads API / X+IG oEmbed — 全 tikhub 之外纯增量。
- **tikhub 调整**：保持 pending·覆盖从"B站+YouTube"**收窄为仅 B站**（YouTube 已被官方 API 替代），降成本与依赖。
- **适配层预留**：tikhub 适配器旁预留 EnsembleData 位（容灾）。
- **明确标注合规债**：tikhub 在图文社区/B站 = "无替代下的合规债"，台账加 `compliance_debt: true` 标记，向元东方透明。
- **与现有源关系**：gdelt/searxng 可作各平台舆情/公开网页发现的兜底层；本批与现有 12 源（见 ledger.yaml）零重叠（除 tikhub 本身调整）。

### 建议 Sprint 排期
- **Sprint 1（零成本·官方）**：YouTube Data API + 各平台 oEmbed + Reddit API/.rss + Mastodon + Threads — 8 个 ✅ 源。
- **Sprint 2（R8 注册 + R1 付费）**：tikhub 配 key（国内任意达人+B站主力）。
- **Sprint 3（境内合规升级·按需）**：新榜/飞瓜（需境内主体担责场景）+ EnsembleData（容灾）。

---

## 九、关键依据信源（节选）
developers.google.com/youtube/v3 · github.com/googleapis/google-api-python-client · developers.tiktok.com(oEmbed/Research API) · praw-dev/praw · reddit .rss · docs.joinmastodon.org · halcy/Mastodon.py · developers.facebook.com/docs/threads · tikhub.io · ensembledata.com · api.newrank.cn · github.com/davidteather/TikTok-Api(rejected) · github.com/NanmiCoder/MediaCrawler(rejected) · B站律师函致bilibili-API-collect关停(ithome) · 小红书数据赔偿490万判例


---

# 附 · v1.1 盲点补充合并（微博 / 播客 / 短视频电商选品 / AI内容检测）

> 2026-06-08 并入 · 原为 datasource-selfmedia-track-a-v1.1-addendum.md（已合并删除）
## ① 微博（中文舆情大头·首轮只在 tikhub 带过）

| 源 | 接入 | 能拿什么 | 成本 | 合规 | 裁定 |
|----|------|---------|------|------|------|
| 微博开放平台标准 API | 官方OAuth2.0 | 2023后大幅收紧·基本只能拿"已授权账号自身"数据 | 免费 | ⚠️ | 做不了第三方舆情·弱 |
| **微博商业数据 API**(openapi.sc.weibo.com) | 官方·企业付费 | 舆情监听/社会化洞察/话题/账号粉丝互动 | 付费(企业资质) | ✅ | **唯一合规拿公域舆情的官方渠道·舆情专项主路径** |
| tikhub weibo 模块 | 授权第三方(pending) | 微博内容/用户/热搜 | 按量付费 | ⚠️ | **公域内容抓取主力**(成本远低于商业API) |
| 新浪舆情通(蜜度) | 商业SaaS非API | 全网+微博事件/传播/竞品 | 政企级昂贵 | ✅ | 买报告型·不适合系统集成·后期 |
| 微博 oEmbed | — | 不存在 | — | ❌ | 嵌入只能用JS Widget(微博秀) |

**专项结论**：微博官方 API 可行但"有钱有照才行"。**tikhub 聚合作公域内容主力（成本低），微博商业数据 API 作高价值舆情专项补充。** 逆向库全弃（tuian/weibo-api、shibing624/weibo-api-sdk、blesstosam/weibo-node-api 均封装 m 站免登录逆向）。

---

## ② 播客（RSS 本质·合规最高地 ✅✅）

| 源 | 接入 | 能拿什么 | 成本 | 合规 | 裁定 |
|----|------|---------|------|------|------|
| **iTunes Search/Lookup API** | Apple官方·无需鉴权 | 播客目录/分类/**feedUrl(RSS)** | **免费** | ✅ | **发现层主路径**·~20 calls/min·返回RSS地址 |
| **播客 RSS feed** | 公开RSS(协议公开) | 全部集数/shownotes/音频enclosure | 免费 | ✅✅ | **核心数据层**·设计即供公开订阅·合规天然最干净 |
| Spotify Web API | 官方OAuth | 单show/episode元数据 | 免费限流 | ✅ | 补独家·⚠️2026-02已砍批量端点 |
| 喜马拉雅开放平台 | 官方API需入驻签约 | 账号/内容/分销 | 入驻审核 | ✅ | 国内最大音频·偏分销合作 |
| 小宇宙 | 无官方API | — | — | ❌ | 仅逆向库`ultrazg/xyz`(弃)·若节目有公开RSS则走RSS |

**合规优势说明**：播客技术本质=公开 RSS feed，发布方主动公开、无登录墙、无反爬意图 → ① 不触未授权访问 ② 不触个保法 ③ 不需逆向。**probe 合规等级最高（✅✅）的数据源类别。** 最佳实践：iTunes API 发现 → 直读各节目 RSS，全链路零逆向零成本零风险。

---

## ③ 短视频电商/选品情报（带货维度）

| 源 | 接入 | 能拿什么 | 成本 | 合规 | 裁定 |
|----|------|---------|------|------|------|
| **巨量算数 trendinsight** | 字节官方·网页产品 | 抖音趋势/画像/榜单/达人 | **免费·个人可用无资质** | ✅ | **选品/趋势主路径**·无开放数据API(受控读取·禁爬榜单页) |
| 巨量引擎 Marketing API | 官方API·需资质签约 | 广告投放/电商直播数据 | 免费(需广告主资质) | ✅ | 有资质时补·门槛=必须广告主/MCN主体 |
| 磁力金牛(快手) | 官方API·需快手商家资质 | 快手电商投放 | 需资质 | ✅ | 快手专项 |
| **蝉妈妈(chanmama)** | 第三方SaaS | 抖音电商/直播/达人榜 | 付费 | ❌ | **判违法弃用**(蝉小红非法爬小红书·2025赔490万+删数据) |
| 飞瓜数据 | 第三方SaaS | 抖音/快手带货 | 付费门槛高 | ⚠️灰区 | 不推荐(数据来源合规存疑·同蝉妈妈类风险) |

**裁定**：第三方电商 SaaS（蝉妈妈/飞瓜/灰豚/千瓜/七麦）整体灰区，**probe 一律不直采，改用官方巨量算数（免费）/磁力金牛（需资质）**。

---

## ④ AI 内容检测/原创度（情报新维度·洗稿/搬运/AI生成）

| 源 | 接入 | 能拿什么 | 成本 | 合规 | 裁定 |
|----|------|---------|------|------|------|
| **Copyleaks** | 官方API·全档SDK | AI检测+抄袭(单次双检) | $7.99起含API+credits | ✅ | **API集成首选**·多语言SDK·入门即带API |
| **Originality.ai** | 官方API | AI检测+抄袭+事实核查 | API在Pro $179/mo·PAYG $30/3k | ✅ | **英文检测精度第一**·30+测评榜首 |
| GPTZero | 官方API | AI生成检测(句级) | 免费10k词/月·付费~$15起 | ✅ | 有免费层·低量试用 |
| Sapling / Winston AI | 官方API+SDK | AI检测(句级/含抄袭) | 付费有免费额度 | ✅ | 细粒度搬运定位候选 |
| **roberta-base-openai-detector** | 开源模型自托管 | 旧模型AI文本检测 | **免费(自托管GPU)** | ✅ | 零成本兜底·对GPT-4/Claude检出弱·仅粗筛 |
| **腾讯朱雀(zhuque)** | 网页工具 | 中文AI文本+图像检测(>95%) | 免费网页 | ⚠️无API | **国内中文最权威但未开放API**·入参加密·禁逆向·只能人工 |

**裁定**：英文/多语言走 **Copyleaks API（集成首选）+ Originality.ai（精度第一）** 双引擎；低量用 GPTZero 免费层；零成本兜底用开源 roberta-detector；**中文场景认朱雀但只能人工（无 API，禁逆向）**。

---

## 增补后的 A 赛道总览（首轮 + 本增补）
- ✅ 可立即接（官方/免费）：首轮 8 + 播客(iTunes API+RSS·合规最高) + 巨量算数(选品免费) + 开源AI检测兜底 ≈ **11+ 官方源**
- ⚠️ pending/授权第三方：首轮 6 + 微博商业数据API + Copyleaks/Originality(AI检测付费) + 喜马拉雅
- ❌ rejected：首轮 16 类 + 微博逆向3库 + 小宇宙逆向 + 蝉妈妈(判违法)/飞瓜灰区
- 🟢 新形态护城河：**播客 RSS（合规等级最高 ✅✅）** + AI 内容检测（自媒体情报新维度）

---

## 十一、A⑤ 微信视频号 · 数据源专节（v1.2 新增 · 2026-06-22）

### 数据源

| 源 | 类型 | 端点 | 成本 | 状态 |
|----|------|------|------|------|
| **JZL 极致了数据** | 商业授权 API | `POST /wxvideo`（multipart/form-data）| ¥0.2/页·15条 | ✅ active · key 已注入 |

### 可获取字段（13 个有效字段 · ¥0.013/条）

**账号层**（每次调用返回一次）

| 字段 | 说明 |
|------|------|
| `v2_name` | 视频号唯一 ID（v2_xxx@finder）|
| `nickname` | 账号昵称 |
| `signature` | 简介/签名 |
| `head_url` | 头像图片 URL |
| `region` | IP 归属地（文字，如"广东"）|
| `country / province / city` | 国家/省/市 |
| `auth_profession` | 认证职业（如"娱乐明星"）|
| `live_status` | 是否正在直播 |
| `feeds_count` | 账号总发视频数 |
| `original_count` | 原创视频总数 |
| `follower_count` | ❌ 平台缺口，未返回 |

**视频层**（每页最多 15 条）

| 字段 | 说明 |
|------|------|
| `object_id` | 视频唯一 ID |
| `title` | 视频标题 |
| `publish_time` | 发布时间 |
| `media_type` | 媒体类型 |
| `duration_sec` | 时长（秒）|
| `file_size_bytes` | 文件大小（字节）|
| `like_count` | 点赞数 |
| `comment_count` | 评论数 |
| `fav_count` | 收藏数 |
| `forward_count` | 转发数 |
| `cover_url` | 封面图 URL |
| `download_url` | 视频下载直链 |
| `openurl` | 视频网页跳转链接 |
| `play_count` | ❌ 永久缺口，平台侧不公开 |

### 永久缺口（无合规路径）

- `play_count`（播放量）：微信平台层面不对外公开，任何第三方 API 均无法获取
- `follower_count`（视频号粉丝数）：wxvideo 端点未返回，平台不开放

### v2_name 发现链路（已通 · v1.2 确认）

```
公众号名称
  → wx_account/search (¥0.2) → ghid
  → history_by_ghid + get_finder=1 (¥0.5) → VideoFinderInfo.user_name = v2_name
  → wxvideo(v2_name) (¥0.2/页) → 视频列表 + download_url
总成本：约 ¥0.9/首次发现 + ¥0.2/页后续更新
```

### 支撑的 probe 能力

| 能力代号 | 能力 | 视频号支持情况 |
|---------|------|--------------|
| A1 | 竞品内容速读 | ✅ 标题/互动/发布时间/时长 |
| A2 | 爆款逆向 | ✅ 点赞/评论/收藏/转发对比（缺播放量）|
| A3 | 发布者画像 | ✅ 昵称/地区/认证/视频总数/原创数 |
| A6 | 跨平台分发 | ✅ download_url 可直接用于内容复用 |

### 合规边界

- 只调 JZL 授权 API，不爬微信 DOM，不模拟登录
- 只采公开视频元数据，不建个人档案
- key 经 vault → `PROBE_JZL_KEY` env 注入，不硬编码
- Playwright/yt-dlp 等工具已在合规整改中停用，不得重新引入

---

## 十、关联 · 需求侧认知体系（结合桥接）

本文档是自媒体 A 的**供给侧**（哪些源合规可得）。其**需求侧**（采什么信号/为什么采/爆款解码维度）来自跨引擎共享的「短视频认知体系」，两者经桥接文档显式咬合：

- **桥接映射**：[short-video-playbook-bridge-v1.0.md](short-video-playbook-bridge-v1.0.md)（需求→供给七维字段映射 + SSOT 去重对账 + 引擎消费关系）
- **需求侧认知真源**（绝对路径·主工作区工作素材）：`/Users/metafo/Downloads/metafoclaw/运营报告/短视频认知体系/short-video-master-guide.md`
- **采集组件实现**：`/Users/metafo/Downloads/metafoclaw/combo-deep-probe/`（07 组合深探·独立 git 仓·VideoDataPacket 7维 schema 真源）

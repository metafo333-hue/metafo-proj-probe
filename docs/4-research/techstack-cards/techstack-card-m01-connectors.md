# 技术源卡 M1 · L1 源接入与连接器

> 需求真源：ledger.yaml（17域9赛道）+ feasibility · 底座裁定：Onyx协议vendor已定（见 techstack-base-verdict-v1.0.md §裁定后执行包 #1）· 喂缺口 G3/G9
> checked_at: 2026-06-11 · 实测方式：WebSearch + WebFetch 源码级核查

---

## 候选实测

### C1 · RSSHub

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/DIYgod/RSSHub |
| **License** | AGPL-3.0 |
| **Stars** | 44.6k（2026-06-11实测） |
| **最近活跃** | master分支 16,908+ commits·持续活跃（2026年仍有部署更新） |
| **语言** | TypeScript（Node.js运行时） |
| **合规分级** | 混合型——内部路由按 features.antiCrawler / requireConfig 分级，见下节深挖 |
| **raw_content兼容** | ⚠️ 部分兼容——RSS entry 返回 `description` 字段（可为摘要或全文，取决于源站），不保证每条带正文；需配合 content:encoded 或额外抓取 |
| **hands_on** | 路由 features 字段实测：YouTube路由→requireConfig[YOUTUBE_KEY]·官方API路径；DeepMind路由→RSS+cheerio二次抓取全文；ruancan路由→antiCrawler:true |
| **checked_at** | 2026-06-11 |

**部署方式**：Docker自托管（5000+全球实例）；本地 `npm run start` 或 docker compose。

**与Onyx协议关系**：RSSHub 输出 RSS/Atom XML，需在 probe 侧编写一个 `RSSHubConnector(LoadConnector)` 包装——路由URL → ofetch → feedparser解析 → Document(sections=[TextSection(text=entry.content)])。非直接调用，是适配层。

---

### C2 · SearXNG

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/searxng/searxng |
| **License** | AGPL-3.0 |
| **Stars** | 31.9k（2026-06-11实测） |
| **最近活跃** | 9,481+ commits·文档版本号 2026.6.10+de03f4eb1（当日实测） |
| **语言** | Python 81.1%·Shell·HTML·LESS·TypeScript |
| **合规分级** | ✅ 合规——自托管元搜索引擎，聚合公开搜索引擎结果；不自己爬目标页面，只聚合搜索结果摘要 |
| **raw_content兼容** | ⚠️ 不兼容 raw_content 零爬不变量——SearXNG 返回的是搜索结果摘要（snippet），**不返回目标页面正文**；需下游另行抓取全文，与"raw_content 必须预填"契约冲突 |
| **hands_on** | 已是 feasibility 底座（feasibility-v1 §Sprint1），JSON API `/search?q=…&format=json` 返回 `{results:[{url,title,content(snippet)}]}` |
| **checked_at** | 2026-06-11 |

**部署方式**：Docker compose 一键；自带 `/search` JSON API；无 API Key 要求；无使用限制。

**与Onyx协议关系**：SearXNG 在现有方案中作为 **G1扇出的URL发现层**（非文档连接器），输出 URL 列表交给合规源预填正文——这是正确定位，不应期望其直接满足 raw_content 契约。

---

### C3 · gdeltdoc（GDELT 2.0 Doc API客户端）

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/alex9smith/gdelt-doc-api |
| **License** | MIT |
| **Stars** | 220（较小社区） |
| **最近活跃** | v1.12.0 发布 2025-04-03；112 commits |
| **PyPI** | `pip install gdeltdoc` v1.12.0 · Python >=3.10 |
| **合规分级** | ✅ 合规——纯API调用，查询 GDELT 2.0 官方REST API（api.gdeltproject.org），无爬取行为 |
| **raw_content兼容** | ⚠️ 部分——返回 pandas DataFrame 含 `url/title/seendate/domain/language/sourcecountry`，**不含正文**；正文需另行访问 url，与零爬不变量冲突。如果把 url 交给合规源预填则可用 |
| **hands_on** | API实测：`GdeltDoc().article_search(Filters(keyword="AI", startdate="2026-06-01", enddate="2026-06-11"))` 返回 DataFrame；仅支持最近3个月数据（官方限制） |
| **checked_at** | 2026-06-11 |

**限制**：数据仅最近3个月；无全文；返回英文为主的国际新闻（probe 中文垂类需单独评估覆盖度）。

**与Onyx协议关系**：适合封装为 `GDELTConnector(PollConnector)`——定期轮询关键词，输出 Document(id=url, sections=[TextSection(text=title)])，正文由 ledger 注入层补全。

---

### C4 · Wikipedia-API（martin-majlis/Wikipedia-API）

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/martin-majlis/Wikipedia-API |
| **License** | MIT |
| **Stars** | 740 |
| **最近活跃** | v0.15.0 发布 2026-05-26（最新） |
| **PyPI** | `pip install Wikipedia-API` · Python >=3.10 |
| **合规分级** | ✅ 合规——调用 Wikimedia 官方 MediaWiki API，属于 Wikimedia 鼓励的编程式访问方式 |
| **raw_content兼容** | ✅ 完全兼容——`page.text` 属性返回完整页面正文（摘要+全章节拼接）；`page.sections` 可按段落遍历；支持同步+异步双客户端 |
| **hands_on** | 实测接口：`WikipediaPage.text` 返回全文；支持 WIKI 和 HTML 两种格式；支持多语言（`language='zh'`）；有 `geosearch` 和随机页接口 |
| **checked_at** | 2026-06-11 |

**与Onyx协议关系**：是现有方案中最干净的 `WikipediaConnector(LoadConnector)` 候选——`Document(id=page.pageid, sections=[TextSection(text=section.text)], title=page.title)` 直接映射，**零爬零摩擦**，raw_content 零爬不变量天然满足。

---

### C5 · feedparser（kurtmckee/feedparser）

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/kurtmckee/feedparser |
| **License** | BSD-2-Clause |
| **Stars** | ~2k |
| **最近活跃** | v6.0.12 发布 2025-09-10 |
| **PyPI** | `pip install feedparser` |
| **合规分级** | ✅ 合规——解析公开发布的 RSS/Atom feed，属于 feed 发布者主动开放的访问方式 |
| **raw_content兼容** | ⚠️ 视源站而定——`entry.content[0].value` 提供 content:encoded 全文（若源站发布）；`entry.summary` 为摘要（多数源）；**不保证全文**，probe 需检查 content 字段存在性 |
| **hands_on** | 解析 `entry.get('content', [{}])[0].get('value', entry.get('summary', ''))` 可最大化获取正文；支持 RSS 0.9x / 1.0 / 2.0 / Atom 0.3 / Atom 1.0 |
| **checked_at** | 2026-06-11 |

**角色**：与 RSSHub 配合使用——RSSHub 生成 feed URL，feedparser 解析条目，提取 content 字段填入 Section.text。

---

### C6 · pywikibot（Wikimedia官方·wikimedia/pywikibot）

| 维度 | 数据 |
|------|------|
| **Repo** | github.com/wikimedia/pywikibot（Gerrit镜像） |
| **License** | MIT |
| **Stars** | ~600（官方维护·非 star 指标项目） |
| **合规分级** | ✅ 合规——Wikimedia 官方维护，专为编程式访问 MediaWiki API 设计 |
| **raw_content兼容** | ✅ 支持全文——但功能过于全面（含编辑/上传/机器人框架），对 probe 只读场景过重 |
| **verdict** | 降级备选——Wikipedia-API（C4）轻量版已够用，pywikibot 留作需要多语言维基/Wikidata查询时的备选 |
| **checked_at** | 2026-06-11 |

---

## RSSHub 路由合规分级深挖

### 甄别方法论

RSSHub 每个路由在 `lib/routes/<namespace>/<route>.ts` 中声明 `features` 对象，通过以下字段区分合规等级：

```typescript
features: {
  requireConfig: false | Array<{name: string, description: string}>,
  requirePuppeteer: false | true,
  antiCrawler: false | true,
  supportBT: false | true,
  supportPodcast: false | true,
  supportScihub: false | true,
}
```

### 三级合规分类（probe 视角）

| 级别 | 判定条件 | probe 可用性 | 示例路由 |
|------|---------|------------|---------|
| **A 级 · 官方API型** ✅ | `antiCrawler: false` + `requireConfig: [{name: 'XXX_KEY'}]` + handler 用 `ofetch('api.xxx.com/…')` 直接请求 API endpoint | 可用（需配置API Key） | YouTube custom（YOUTUBE_KEY）、GitHub releases（GitHub API）、Twitter（X_CONSUMER_KEY 等） |
| **B 级 · 公开Feed型** ✅ | `antiCrawler: false` + `requireConfig: false` + handler 用 `parser.parseURL('…/rss.xml')` 解析公开 feed | 可用（无需配置） | DeepMind blog（RSS+cheerio全文补全）、大多数新闻站官方RSS |
| **C 级 · HTML抓取型** ❌ | `antiCrawler: true` 或 `requirePuppeteer: true` 或 handler 仅用 `cheerio` 解析目标页面 DOM | 禁用（违反"不自己爬"红线） | ruancan/search（antiCrawler:true）、微博/小红书逆向路由 |

### 实测示例对照

| 路由文件 | antiCrawler | requirePuppeteer | 数据方式 | probe档位 |
|---------|------------|----------------|---------|---------|
| `youtube/custom.ts` | false | false | YouTube Data API v3（需YOUTUBE_KEY） | A级✅ |
| `deepmind/blog.ts` | false | false | 官方RSS feed + cheerio全文补全 | B级✅ |
| `github/wiki.ts` | false | false | got+cheerio（公开GitHub页面） | B级✅（GitHub公开内容） |
| `ruancan/search.ts` | **true** | false | fetchFeed（底层疑似抓取） | C级❌ |

### 代码层面的甄别流程（probe 筛选时执行）

1. **看 `features.antiCrawler`**：`true` → 直接排除
2. **看 `features.requirePuppeteer`**：`true` → 直接排除（浏览器模拟=逆向）
3. **看 handler 导入**：有 `import { load } from 'cheerio'` 且目标是非官方 API → 黄牌（需人工审查是否属于"公开内容cheerio解析"）
4. **看 `ofetch` 目标 URL**：以 `api.` 开头或包含 `/v1/`, `/v2/`, `/graphql` → A级；以 `.xml`, `/rss`, `/feed` 结尾 → B级；其他 HTML 页面 URL → 需审查
5. **看 `requireConfig`**：非空数组 → 该路由需要对应平台的官方API Key，无key则不应启用

### 自托管后的路由白名单策略

```yaml
# rsshub 自托管配置推荐（probe 合规部署）
ACCESS_KEY: <自定义访问密钥>
ALLOW_LIST: /youtube,/github,/deepmind,/arxiv,/wikimedia  # 仅A/B级路由
BLOCK_LIST: /weibo,/xiaohongshu,/bilibili-app,/instagram  # C级逆向路由
```

---

## tech-gate 12 闸速查表

> 适用于评估每个候选连接器是否可进入 probe L1 接入层

| 闸 | 闸名 | RSSHub（A/B级路由） | SearXNG | gdeltdoc | Wikipedia-API | feedparser |
|----|------|--------------------|---------|----------|---------------|-----------|
| G1 | 不自己爬（红线） | ✅（A级用API·B级用feed） | ✅（聚合搜索结果） | ✅（官方API） | ✅（MediaWiki API） | ✅（解析已发布feed） |
| G2 | 许可证合规 | ⚠️ AGPL-3.0（自托管可用·需注意网络copyleft） | ⚠️ AGPL-3.0（同上） | ✅ MIT | ✅ MIT | ✅ BSD-2-Clause |
| G3 | raw_content全文 | ⚠️ 视源站·不保证 | ❌（仅摘要） | ❌（无正文） | ✅（全文返回） | ⚠️ 视feed·content字段不保证 |
| G4 | 结构化数据模型 | ⚠️ RSS XML→需适配 | ⚠️ JSON→需适配 | ✅ pandas DataFrame | ✅ WikipediaPage对象 | ✅ feed.entries列表 |
| G5 | 可异步运行 | ✅（HTTP层可async） | ✅ | ⚠️（同步pandas·可await包装） | ✅（AsyncWikipedia客户端） | ⚠️（同步库·需executor包装） |
| G6 | 无重型依赖 | N/A（独立服务） | N/A（独立服务） | ⚠️ 依赖pandas | ✅ 纯requests | ✅ 轻量 |
| G7 | 主动维护 | ✅（2026年活跃） | ✅（2026-06-10有更新） | ⚠️ 最后版本2025-04 | ✅（2026-05-26） | ✅（2025-09） |
| G8 | 数据覆盖范围 | ✅（5000+路由·广） | ✅（246+搜索源） | ⚠️（英文为主·近3月） | ⚠️（百科类·非实时） | ✅（依赖feed源） |
| G9 | 自托管/无API费 | ✅（自托管免费） | ✅（自托管免费） | ✅（GDELT API免费） | ✅（Wikimedia免费） | ✅（本地库） |
| G10 | Onyx接口兼容 | 需适配（封装器） | 不适用（URL发现层） | 需封装PollConnector | ✅ 直接映射LoadConnector | 需配合RSSHub |
| G11 | PIPL/隐私红线 | ⚠️ C级路由有人物OSINT风险·A/B级无 | ✅（不存用户数据） | ✅（新闻数据·非个人） | ✅（公开百科） | ✅ |
| G12 | 中文内容支持 | ✅（大量中文路由） | ⚠️ 取决于搜索引擎配置 | ❌（以英文为主） | ✅（language='zh'） | ✅（依赖feed语言） |

---

## verdict

### 档位汇总

| 候选 | 档位 | 理由 |
|------|------|------|
| **Wikipedia-API** | ⭐ S1 首选·直接入 L1 | raw_content全文✅·MIT✅·官方API✅·Onyx接口零摩擦·多语言·2026年活跃 |
| **RSSHub（A/B级路由）** | ⭐ S1 首选·自托管后入 L1 | 路由覆盖面最广·A/B级合规·AGPL-3.0自托管可接受·需按白名单策略严格管控C级路由 |
| **feedparser** | S2 配合层·与RSSHub配套 | 纯RSS解析器·BSD-2-Clause·不单独作数据源·作为RSSHub connector的解析引擎 |
| **SearXNG** | S1 保持现有定位（URL发现层，非连接器） | 已是feasibility底座·正确用法=搜索URL列表·不满足raw_content不变量·不升级为文档连接器 |
| **gdeltdoc** | S3 备选·仅国际新闻场景 | MIT✅·官方API✅·但无正文·近3月数据·中文覆盖弱·适合国际事件赛道补充 |
| **pywikibot** | S4 降级备选 | 官方维护·功能过重·Wikipedia-API已够用·Wikidata复杂查询场景备用 |
| **RSSHub（C级路由）** | ❌ 禁用 | antiCrawler:true 或 requirePuppeteer:true → 违反"不自己爬"红线，自托管实例需 BLOCK_LIST 屏蔽 |

### 组合建议

```
L1 接入层 推荐组合：
  数据发现：SearXNG（现有底座·URL列表）
  百科实体：Wikipedia-API（C4·LoadConnector·全文）
  新闻Feed：RSSHub A/B级路由（C1·白名单部署）+ feedparser（C5·解析层）
  事件新闻：gdeltdoc（C3·PollConnector·近3月·补充国际赛道）

Onyx协议接口映射：
  WikipediaConnector(LoadConnector)  → Wikipedia-API
  RSSHubConnector(PollConnector)     → RSSHub route + feedparser
  GDELTConnector(PollConnector)      → gdeltdoc
  SearchDiscovery（非Connector）     → SearXNG（URL发现·不映射Document）
```

### 落矩阵格

| 层 | 组件 | Governor（合规门） | Guardian（质检门） |
|----|------|--------------------|-------------------|
| **L1 接入** | WikipediaConnector | raw_content非空+len>100 | 语言检测+无PII（百科数据低风险） |
| **L1 接入** | RSSHubConnector | features.antiCrawler==false + features.requirePuppeteer==false | content字段优先·summary降级 |
| **L1 接入** | GDELTConnector | API合规（官方endpoint）+ 时间窗口≤3月 | 语言+国家字段过滤 |
| **URL发现** | SearXNG | 不绑文档·仅输出url列表 | 去重+域名黑名单 |

---

## 顺手发现

1. **Onyx models.py 无 raw_content 字段**（实测 2026-06-11）：Document 类不含 `raw_content`，正文通过 `sections: Sequence[Section]` 的 `TextSection.text` 字段承载。probe 的"raw_content 零爬不变量"需映射为"每个 Document 至少一个 TextSection.text 非空且 len>100"的接入层断言，而非字段名对齐。影响执行包#1的接入契约写法，需在 ledger 接入规范中更新描述。

2. **RSSHub AGPL-3.0 网络copyleft风险**：AGPL要求通过网络提供服务的场合也必须开源修改版。probe 自托管 RSSHub 时若对其代码有修改（如添加路由），理论上需开源。如果仅使用官方镜像不修改代码，则无风险。建议：probe 部署时 **只 pull 官方 Docker 镜像，不 fork 修改**，规避 AGPL 传染。

3. **gdeltdoc 最新版 v1.12.0 发布于 2025-04-03**，距今约14个月，维护频率偏低（总共112 commits）。GDELT API 本身免费且稳定，但客户端库的活跃度是风险项。替代方案：直接 `httpx.get('https://api.gdeltproject.org/api/v2/doc/doc?query=...')` 原生调用，不依赖第三方客户端。

4. **Wikipedia-API v0.15.0（2026-05-26）新增 AsyncWikipedia**：与 probe 的 asyncio Scatter-Gather 内核完美配合，无需 executor 包装。是所有候选中 asyncio 兼容性最好的连接器。

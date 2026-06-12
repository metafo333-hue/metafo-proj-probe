# probe 情报引擎 · 对齐核查 + 拓扑图 + 上线前章节梳理 v1.0

> 日期：2026-06-06 · 方法：2 路扇出真读核查（既有 probe 方案 + 平台总方案），全部原文引用
> 上游：[design-v1](../3-build/probe-intelligence-engine-design-v1.md) · [feasibility-v1](../4-research/probe-github-datasource-feasibility-v1.md) · [v2 方案（已归档）](../_archive/probe-solution-design-v2.html.archived-20260608) · master-plan v3.8（`metafoclaw-git/docs/platform/master-plan.md`）

---

## 1. 与既有 probe 方案对齐核查（point 1：是否参考了？）

**结论：新设计确实继承了 v2 核心（七段报告、三层深度线、适配器抽象、合规铁律、L1 契约），但核查发现 8 个「不能丢」的精确继承点必须在落地时守住。**

### 1.1 已正确继承 ✅
| 继承项 | v2 出处 | 新设计落点 |
|--------|---------|-----------|
| 卖「判断」非「数据」定位 | v2 §1 | design-v1 §0 价值主张 |
| 三层深度线 public/preview/paid | README + v2 §8 | design-v1 §5.4 |
| 适配器供应商抽象（可热插拔） | datasource-selection §4 | design-v1 §4 解耦铁律 |
| 合规铁律（不自己爬数据/授权API） | datasource-selection + COMPLIANCE-HANDOFF | design-v1 §2.5 + feasibility 全程 |
| 自媒体为首发垂类 | v2 §1 | design-v1 §5 锚点垂类 A |

### 1.2 ⚠️ 必须守住的 8 个精确继承点（核查新增）
| # | 不能丢的点 | 风险（丢了会怎样） |
|---|-----------|------------------|
| C-1 | **七段报告精确骨架**：①首屏速判(A/B/C/D评级+15秒拍板+三步行动) ②真相核查 ③内容拆解 ④竞品横评 ⑤二创方案 ⑥风险合规 ⑦完整明细。评级是 LLM 综合 D1/D2/D8 结论，**非字数判** | 回退成通用报告，丢掉"拍板级参谋"定位 |
| C-2 | **三层深度线切割是硬约束**：public 禁显结构/二创/竞品；preview 仅 1 条二创简版；paid 才给完整三路 | 公开层泄露付费价值，违反 guards C4 |
| C-3 | **D3视觉拆解/D9 IP适配是 Phase2**，不在 P0/P1 承诺 | 制造兑现不了的期望 |
| C-4 | **成品人工复核门**（首批10-20链接·人机一致性≥80%）开付费档前必过，C2 不可自过 | 付费档生死命门（Manus 教训） |
| C-5 | **四暗号契约 + aigc_flag**：每加一个 D 维度同步更新 selftest 断言 | selftest 11/11 破，准入失败 |
| C-6 | **datasources 供应商抽象层**：TikHub 不硬编码为唯一源，留 fallback | Proxycurl 式突然关停风险 |
| C-7 | **定价豆包价格锚**：paid 明显低于豆包 68/200/500，按次付费不强制订阅 | 改纯订阅需重新论证（已是 v2 结论） |
| C-8 | **「原料进结论出」C4 贯穿所有出口**：含合规占位/错误/fallback 都不透传第三方原始 JSON | 任一出口直吐 = 违反 CLAUDE.md 铁律 |

---

## 2. 与平台总方案对齐核查（point 3：master-plan 对齐）

**结论：probe 在 master-plan v3.8 是「已登记、未详写」（§10.2.1 台账一行 + v3.8 双视角调和注），新设计不与总方案冲突，但有 5 处契约字段/边界需对齐，其中 2 处必改。**

### 2.1 总方案对 probe 的定调（原文）
- **双视角调和（v3.8）**：「probe 既是引擎矩阵中的 MetaProbe 情报引擎（矩阵层），又可作为独立子项目运行（子工具视角）……原 probe 子项目决策不推翻，补一层引擎身份。」→ **新设计方向与总方案一致**。
- **link-intel 评 S 级**（Part 13）：probe 底层能力是「极高频前置、边界干净」的 Agent 工作流入口。
- **L1 四暗号契约**：①invoke ②出口meta ③cost ④manifest + ⑤selftest 准入；**双闸**：C2 评分卡(完成度≥80%/准确性≥20pct/省力≥3×/盲评≥70%) + 双螺旋门(🌀规模递增+🤝信任复利)。

### 2.2 需对齐的 5 项（🔴必改 / 🟡建议）
| # | 对齐项 | 现状 vs 总方案 | 动作 |
|---|--------|--------------|------|
| A-1 ✅ | **manifest `industry` 对外一期 `["自媒体","金融"]`**（2026-06-08 元东方裁定金融正式纳入）| 新设计扩 5 业务域；master-plan §5 矩阵分批填格 | manifest `industry=["自媒体","金融"]`（金融能力 S1 落地中、声明已纳入、能力随 S1 补齐）；其余业务域以场景模板内部开发，不对外声明 |
| A-2 🔴 | **缺 GEO 字段** `geo_publishable` + `conclusion_block{headline,key_points,data_table,brand_anchor}` | 02-api.md §1 要求；probe invoke.schema 无 | 补 schema；调研/榜单/对比类报告须 `geo_publishable=true` + 输出 conclusion_block（喂 Part12 GEO 分发） |
| A-3 🟡 | **invoke request 缺 `version`** | 02-api.md 请求体含顶级 `version`；probe request 无 | 补 `version:string` 到 invoke.schema request |
| A-4 🟡 | **manifest 缺 `subdomain`** | 02-api.md §2 含 `subdomain:"probe"`；schema 无 | 补 subdomain 到 manifest schema（核对 router 实返值） |
| A-5 🟡 | **验证层成本须计入** | 验证层 opus×3+×2 对抗证伪的 token 要进 `meta.models_used` + `cost.base` | 否则 MetaFlow ②效益层低估 probe 成本，组合排名失真 |

> 命名（元典录签发 MetaProbe 中文名）+ master-plan 补 probe Part = 已知待办，不阻塞开发。

---

## 3. 拓扑图集（point 2：图形拓扑增强逻辑性）

### 3.1 引擎矩阵中 probe 的位置 + MetaFlow 调度
```
                    ┌──────────────────────────────────────────┐
                    │   MetaFlow 编排中枢（矩阵大脑 v3.8.1）       │
                    │  ①编排 ②效益 ③实验 ④预测 ⑤反推             │
                    └───────┬───────────────────┬──────────────┘
                  过4暗号契约│ 注入 engine_fn    │效益回流(cost/latency/quality)
          ┌─────────┬───────┴────┬──────────┬───┴─────┬──────────┐
          ▼         ▼            ▼          ▼         ▼          ▼
      MetaAsk   MetaProbe★   MetaDesign  MetaCut  MetaLearn   MetaOps
      (问准)   (情报底座)     (做对·排版)  (剪辑)   (越用越智)  (检测)
          │         │            ▲          ▲         ▲
          └──意图──▶ │──情报成材──┘──拆解结论─┘──源命中回流┘
                     │
                母体=铁轨 · 引擎=列车 · 只走 L1 契约（禁直连·R22 五环）
```

### 3.2 probe 四层引擎架构 + 数据源仓库（17 域 · 对齐 ledger.yaml v4）
```
 输入素材：链接/图片/视频/文档/文字/名字(实体)
        │
        ▼  MetaAsk 意图澄清 → 任务类型 + 输出规格 + 深度档 + 交付形态
 ┌──────┴──────────────────────── MetaProbe ────────────────────────────┐
 │ L4 整合层   拆解 → 重组 → 归纳（七段报告 / conclusion_block）            │
 │ L3 验证层   双审8闸抗污染 + 对抗证伪（源无关·成本计入 cost.base·见audit-system-v1）│
 │ L2 采集层   素材解析 + 数据源路由 + 多源并发扇出                          │
 │ L1 接入层   适配器（registry 驱动 · 热插拔 · 标准19 门）                  │
 │ ───────── 数据源仓库 catalog ──────────────────────────────────────── │
 │  D1真相核查 D2内容拆解 D3视觉多模态 D4出处溯源 D5竞品横评 D6账号画像 D7二创路径   │
 │  D8法规合规 D9地域受众 D10学术 D11企业财务 D12开源技术 D13金融行情 D14宏观政策      │
 │  ←每源元数据:域/接入方式/权威分/合规/成本                                    │
 └──────┬───────────────────────────────────────────────────────────────┘
        ▼  成材（引用 + 置信度 + 证据链 + aigc_flag + geo_publishable）
   → MetaDesign 排版 / MetaCut 视频 / MetaLearn 飞轮 / GEO 分发
```

### 3.3 端到端数据流 × 三层深度线 × 七段报告
```
 一句话/链接 ─▶ /api/v1/invoke (async,task_id)
                      │
        ┌─────────────┼───────────────┐
        ▼             ▼               ▼
   L1 采集        L3 验证          L4 整合 ──▶ 七段报告
  (多源扇出)   (溯源/交叉/证伪)   (拆解归纳)      │
                                                ▼  按深度档裁剪(guards C4)
                      ┌──────────────┬──────────────────┐
                  public(匿名)     preview(注册)        paid(付费)
                  评级+一句话     +结构公式+1条二创    +完整7段+竞品横评
                  零成本引流       注册转化抓手        成品独有结论
                      └────────── /api/v1/task/{id} 轮询 deliverable ──────┘
```

### 3.4 验证层双审 8 闸流水线（抗污染护城河）
> 完整设计见 [probe-audit-system-v1.md](../3-build/probe-audit-system-v1.md)；旧 7 闸已升级为 8 闸。
```
 闸0 过程留痕（trace+哈希链·贯穿全程·其余闸的元前提）
        │
 多源原料 ─▶闸1溯源─▶闸2多源交叉印证─▶闸3抗循环/抗AIGC─▶闸4时效×权威加权
                                                               │
        闸7置信标注 ◀─闸6对抗证伪(opus×3生成+×2证伪·多数票) ◀─闸5矛盾检测
                │
                ▼  结论 + 置信度 + 证据链 + 反方观点（cost 计入 base）
   极速版/深度分析版双形态·智能界定（2026-06-10 收敛）：默认极速兜底+确定性自评+按需升级，每版各自精品；钱买的是深度分析版（闸0-7全开+对抗证伪+多源专业数据），极速版（闸0/1/2/7[+3/5]）在其定位也认真精品；付费差异另在次数/形态/便捷/特殊服务（见 ../3-build/probe-speed-depth-tiering-v1.0.md）
```

### 3.5 数据源接入方式 → 合规分层（隔离风险）
```
  ✅ 可用                                          ⛔ 弃用（probe 自己爬/绕）
  ┌────────────────────────────────────────┐    ┌──────────────────────────────┐
  │ L 开源库本地嵌入    (Docling/whisper)   │    │ probe 自写爬虫/逆向           │
  │ S 自托管开源服务    (SearXNG/RSSHub)    │    │ B站逆向bilibili-api(律师函)   │
  │ W 官方SDK           (PyGithub/vt-py)    │    │ 小红书逆向                   │
  │ O 官方开放API       (OpenCorporates)    │    │ 裁判文书爬虫                 │
  │ D 开源数据集        (OpenSanctions)     │    │ SimilarWeb非官方/pytrends绕过 │
  │ ★源的源 目录(public-apis/awesome-osint)│    │ 蝉妈妈（已判违法）           │
  │ TikHub等第三方聚合API(纯数据接口·供应商担责)│  │ TikHub captcha破解工具       │
  └────────────────────────────────────────┘    └──────────────────────────────┘
   第三方API红线：probe只调数据接口，不调供应商captcha/逆向工具；供应商担责
   video/social数据走第三方API，禁probe自己yt-dlp下载 · 付费源走 R1
```

---

## 4. 设计上线前章节梳理（point 4：上线前章节）

> 用途：把分散的设计/调研/对齐收敛成一份「上线前设计总册」的章节骨架。每章标注 [继承v2]/[新增]/[需对齐]，并挂对应上线门。

| 章 | 标题 | 内容要点 | 标签 | 挂门 |
|----|------|---------|------|------|
| **0** | 定位与价值主张 | 卖「判断」(v2) → 升级「情报引擎」三护城河(数据源/验证/解耦) | 继承+新增 | — |
| **1** | 引擎矩阵定位与契约 | MetaProbe 双视角；L1 四暗号+selftest；MetaFlow 调度；与5引擎组合 | 需对齐 | C2评分卡 |
| **2** | 数据源仓库 | 17 域 catalog + 接入方式5类 + 元数据schema + 标准19门 + 合规铁律 | 新增 | — |
| **3** | 四层引擎架构 + 解耦 | L1-L4 源无关；适配器热插拔；供应商抽象(C-6) | 继承+新增 | — |
| **4** | 验证层双审8闸 | 抗污染护城河；对抗证伪；成本计入(A-5)；极速版/深度分析版双形态·智能界定（每版各自精品·见 [speed-depth-tiering-v1.0](../3-build/probe-speed-depth-tiering-v1.0.md)）；完整设计见audit-system-v1 | 新增 | — |
| **5** | 场景与交付 | 5业务域27场景(对外一期自媒体+金融·A-1)；七段报告骨架(C-1)；三层深度线(C-2)；交付形态多模态 | 继承+需对齐 | — |
| **6** | 合规与红线 | 数据来源铁律4条；个保法最小必要；aigc_flag；原料进结论出(C-8)；R8/R1门(C-9) | 继承 | 合规官 |
| **7** | GEO 与飞轮 | geo_publishable+conclusion_block(A-2)；源命中回流 MetaLearn | 需对齐 | — |
| **8** | 上线门与里程碑 | M1公开档(零成本零风险)→M2付费档(C2质量门+人工复核C-4)→M3大厅 | 继承 | 双螺旋🟢🟢 |
| **9** | 待决策与签发 | 命名元典录；R1付费源ROI清单；manifest/schema字段补全(A-2/3/4) | 新增 | R1 |

### 上线三里程碑（继承 launch-roadmap · 最权威）
```
 M1 公开档(~1周)  零法律风险·零数据成本·不依赖外部授权
   门: L0母体对齐✅ + 双螺旋🟢🟢 + L1代码 + L2部署(DNS/nginx/Redis)
   交付: 粘贴文章链接 → D2结构+D7二创+评级 · 公网可访问
 M2 付费档(~2-3周)  TikHub key(R8+R1) + BGM版权
   门: 🔴C2质量门实评 + 🔴成品人工复核≥80%(C-4·不可自过)
   交付: 抖音链接 → 含BGM+竞品横评的完整七段报告
 M3 大厅上架(待母体波次)  不阻塞 M1/M2
   门: 母体 HttpToolClient + identity/verify + registry三维标签
```

---

## 5. 落地动作清单（核查产出的待办）

**🔴 必改（落 Sprint 1 一并做）**
1. `manifest.schema.json`：industry 对外一期 `["自媒体","金融"]`（2026-06-08 纳入金融）+ 补 `subdomain`（A-1/A-4）
2. `invoke.schema.json`：meta 补 `geo_publishable` + `conclusion_block`；request 补 `version`（A-2/A-3）
3. 验证层成本计入约定写进 design-v1（A-5）

**🟡 守住（落地纪律·写进章节6/8）**
4. 七段报告骨架 + 三层切割 + 人工复核门 + 原料进结论出（C-1/2/4/8）按上表守

**已知待办（不阻塞）**
5. 元典录签发正式中文名（工作名已定：**元探**）；master-plan 补 MetaProbe Part（capability 声明喂 MetaFlow⑤）

---

> 三份文档成体系：design-v1(框架) + feasibility-v1(数据源落地) + 本篇(对齐+拓扑+上线前章节)。
> 下一步建议：把 §5 的 🔴必改 3 项并入 Sprint 1，与 ledger 多域 catalog 一起落。

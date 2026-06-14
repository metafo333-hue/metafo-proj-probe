# probe · 短视频认知体系 × 自媒体赛道 A · 桥接映射 v1.0

> 日期：2026-06-14 · 类型：bridge（需求侧↔供给侧映射） · 状态：✅ 首版
> 定位：把跨引擎共享的「短视频认知/方法论体系」与 probe 自媒体赛道 A 的「数据源/采集工程」**显式咬合**——分层引用、不复制、不合并。
> 一句话：认知体系告诉 probe **采什么信号、为什么采**；probe 数据源文档解决 **怎么合规拿到**；本文档是两者之间的对账桥。

---

## 〇、为什么是「桥接」而不是「搬进来」

短视频认知体系（`运营报告/short-video-playbook/`）与 probe 自媒体分析是**两层不同的东西**，硬合并或整树拷贝都错：

| 维度 | 短视频认知体系 | probe `datasource-selfmedia-track-a-v1.md` |
|------|--------------|-------------------------------------------|
| 层次 | **需求/认知侧**：为什么采、采什么信号、赛道逻辑、爆款解码维度 | **供给/工程侧**：哪些 API 合规可得、✅⚠️❌ 红线台账 |
| 服务对象 | **跨引擎共享**（MetaWrite/MetaDrama/MetaReach/MetaLearn + probe） | probe 私有 |
| SSOT 真源 | `运营报告/short-video-playbook/`（认知层原处，工作素材） | probe git 仓（已版本化） |

**纪律**：本文档对认知层**只引用（绝对路径指针）、不复制**——避免一份知识两处维护必漂移（本仓 SSOT 铁律）。认知层任何内容更新只改其原处真源，本桥接只维护「映射关系」。

---

## 一、真源指针表（认知层各分块 → 绝对路径 + 在 probe 中的角色）

> 认知层原处真源（主工作区，未版本化的工作素材）。引用用绝对路径，跨窗口可靠。

| 分块 | 绝对路径 | 在 probe 自媒体的角色 |
|------|---------|---------------------|
| 主干成品 | `/Users/metafo/Downloads/metafoclaw/运营报告/short-video-playbook/short-video-master-guide.md` | 需求侧总纲·选题/赛道/爆款逻辑一篇读懂 |
| 01 底层认知 | `.../01-foundation/`（平权理念/时机/信息源六重身份） | 北极星·为什么做自媒体情报（信息差=竞争力） |
| 02 平台机制 | `.../02-platform-mechanism/traffic-race-and-weight.md` | **权重信号定义**（完播/互动/标签/ECPM）= probe 要采集与解读的指标 |
| 03 赛道战略 | `.../03-track-strategy/`（全品类/投产比/平权契合） | 与 probe **赛道注册表**（9 赛道）的概念对齐源 |
| 04 内容执行 | `.../04-account-content-ops/`（信息元素40项/活人感/技巧弹药库） | **信息元素 40 项**= probe 自媒体采集字段的需求清单 |
| 05 流量运营·采集层 | `.../05-traffic-ops/url-only-data-acquisition.md` | ⚙️ **工程件**：7 类数据可得性矩阵 = probe 数据源可行性规格（见 §三对账） |
| 06 规模化 | `.../06-scaling/multi-account-matrix.md` | 矩阵/风控逻辑·MetaReach 分发侧（probe 弱相关） |
| 07 工具·组合深探 | `.../07-tooling/combo-deep-probe-tool-design.md` | ⚙️ **工程件**：probe 采集层组件设计，代码已落 combo-deep-probe 独立仓（见 §三对账） |

---

## 二、需求→供给 核心映射（本桥接的实体）

这条链此前是隐性的，本节把它显式钉死——**认知概念 → 采集字段 → schema → 源覆盖**四级对应：

```
认知层(02/04)          05 可得性            07 VideoDataPacket        track-A 数据源
权重信号/信息元素40项 → 7类数据可得性矩阵  → 7维 Field{value,source,    → 哪个合规源供给该维
爆款解码维度             (公开3/估算2/黑盒3)    precision,ts}              (tikhub/yt-dlp/oEmbed...)
   = 为什么采              = 能不能采            = 怎么存(可追溯精度)        = 从哪合规拿
```

### 七维字段映射明细

| 数据维度（05/07 七维） | 认知层依据（采集动机） | 可得性（05） | probe 合规供给源（track-A） | precision 默认 |
|----------------------|---------------------|------------|--------------------------|---------------|
| ⑦ 元数据（标题/标签/封面/时长） | 选题/标签匹配（02）·信息元素（04） | 公开·准确 | tikhub / yt-dlp / 各平台 oEmbed | measured |
| ③ 互动累计 + 评论文本 | 互动权重信号（02）·评论挖矿（05） | 公开·准确⚠️PIPL | tikhub / yt-dlp / Reddit API | measured |
| ① 播放量/曝光 | 流量池赛马结果（02） | 半·分平台 | yt-dlp(YT/B站)·tikhub估算(抖音) | measured/estimated |
| ④ 粉丝画像 | 受众匹配/赛道契合（03） | 半·估算 | tikhub 估算 / 巨量算数 | estimated |
| ② 完播率/留存曲线 | **第一权重信号**（02）·爆款解码核心（05） | **黑盒** | 无合规源 → FeedAdapter 投喂 | fed/missing |
| ⑤ 流量来源结构 | 推荐/搜索/同城归因（02） | **黑盒** | 无合规源 → FeedAdapter 投喂 | fed/missing |
| ⑥ 转化/GMV/引流 | 商业价值=转化效率（03 投产比） | **黑盒** | 自有店铺后台 → FeedAdapter 投喂 | fed/missing |

> **关键洞察**：认知层把"完播率"列为第一权重信号、爆款解码核心，但它恰是结构性黑盒（任何合规第三方都拿不到）——这正是 07 设计 FeedAdapter（用户投喂补黑盒）的根本动机。**需求侧的"最想要"与供给侧的"最难拿"在此交汇**，是 probe 自媒体价值分析的天花板与护城河所在。

---

## 三、SSOT 去重对账（05/07 工程件 vs probe 现有文档·防漂移）

05/07 是工程设计件，与 probe 现有文档高度重叠。**逐项指定 canonical，余处引用，禁各留一份**：

| 事实/设计 | 出现处 | canonical 真源 | 处置 |
|----------|--------|--------------|------|
| 自媒体合规红线（不自爬/持牌第三方担责） | 05 §四 · track-A 序言 · 多份 | **`datasource-selfmedia-track-a-v1.md`**（probe 仓·已版本化） | 05 的红线视为其下游印证，引用 track-A，不另立 |
| 数据可得性矩阵（7类×途径） | 05 §一 · feasibility-v1 | **05 url-only**（最细，但⚠️部分未对抗验证） | 数字落地前以 probe 实测覆盖；feasibility 引用 05 |
| VideoDataPacket 7维 schema | 07 §二 · combo-deep-probe 代码 | **combo-deep-probe 仓 `combo_deep_probe/schema.py`**（代码即真源） | 07 设计文档标"实现见代码仓"，schema 改动以代码为准 |
| SourceAdapter 契约 / 路由策略 | 07 §三五 · combo-deep-probe 代码 | **combo-deep-probe 代码** | 同上 |
| 数据源清单（tikhub/yt-dlp/oEmbed...） | 07 §四 · track-A · `ledger.yaml` | **`app/datasources/ledger.yaml`**（probe 代码真源） | 07/track-A 均引用 ledger，禁手抄源清单 |
| 部署归属（probe-a 机6） | 07 §八 · `server-roles.md` | **`server-roles.md`**（机6 probe 采集节点） | 07 引用 server-roles |

> ✅ **核验记录（2026-06-14 · TikHub 真实 key 实测）**：05 的可得性矩阵核心论断已**实证**。
> - **key 状态**：probe-prod key 已配置入 vault（`~/vault/credentials/api/tikhub-key.txt` chmod 600），`get_user_info` 返回 code 200 验证有效（账号 06-13 注册·本次找回控制权 + 邮箱验证 + 密码重置）。
> - **实测样本**：bilibili `BV1QuEz65EsF`（热门页真实视频）→ `/api/v1/bilibili/web/fetch_one_video` code 200·返回 81 字段。
> - **结果（实证 05 的"公开 vs 黑盒"边界）**：✅ ⑦元数据(title/pubdate/desc) · ✅ ③互动(stat.view 播放量/danmaku/reply/favorite) · ✅ ④作者(owner.mid/name) **均返回**；❌ ②完播率/留存 · ❌ ⑤流量来源 · ❌ ⑥转化/GMV **均不返回**——与 05 预测完全一致。
> - **combo-deep-probe"已实测"声称证实属实**：dashboard 使用日志显示 06-13 已有真实 douyin 调用（hybrid/video_data·fetch_one_video），就是用此账号。
> - **成本**：核验仅耗免费额度 ~$0.001，付费余额 $20 未动。
> - ⚠️ **仍待补**：douyin（05 称播放量前台无→估算）/ tiktok / xiaohongshu 逐平台字段实测未做（需各平台真实 URL）；本次以 bilibili 确证结构边界。⚠️ **$20 付费余额来源待元东方确认（疑 06-13 已 R1 充值）**。

---

## 四、引擎消费关系（probe 只是消费者之一·防 probe 私有化误区）

认知层服务 5 个引擎，**不可 probe 私有化**。各引擎消费同一认知真源的不同层：

| 引擎 | 消费认知层哪部分 | 与 probe 关系 |
|------|----------------|--------------|
| **probe（本引擎）** | 信息源(01.7)·权重信号(02)·信息元素(04)·爆款解码维度(05) | 采集+解读情报燃料 |
| MetaWrite（文案/脚本） | 信息元素/技巧弹药库（04） | 消费 probe 采集的选题情报 |
| MetaDrama（短剧） | 剧情短剧赛道（03）+内容生产（04） | 消费 probe 趋势/竞品情报 |
| MetaReach（分发） | 机制（02）+流量运营（05）+矩阵（06） | 消费 probe 爆款信号反哺 |
| MetaLearn（学习反哺） | 数据反哺+爆款解码（05） | 与 probe 闭环（采集→解码→反哺） |

> 所以认知层归属 = 跨引擎共享层，probe 通过本桥接指针引用。**禁把认知体系当 probe 私产搬入 probe 仓。**

---

## 五、关联

- 需求侧认知真源（绝对路径，见 §一指针表）：`运营报告/short-video-playbook/`
- 供给侧 probe 真源：[datasource-selfmedia-track-a-v1.md](datasource-selfmedia-track-a-v1.md) · [feasibility-v1](probe-github-datasource-feasibility-v1.md) · `app/datasources/ledger.yaml`
- 采集组件代码：`/Users/metafo/Downloads/metafoclaw/combo-deep-probe/`（独立 git 仓）
- 部署职能：`server-roles.md` 机6 probe-a
- SSOT 治理纪律：[records/probe-ssot-governance-v1.md](records/probe-ssot-governance-v1.md)

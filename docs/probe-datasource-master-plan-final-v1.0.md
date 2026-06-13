# probe 数据源体系总方案（终稿 · SSOT 入口）v1.0

> 日期：2026-06-13 · 定位：**probe 数据源体系的单一入口（SSOT entry）**。本文只做「全局口径 + 决策定稿 + 指向真源」，不复制各真源明细。
> 理念（元东方定调）：**引擎核心 = 源头数据。数据够丰富、准确、真实，AI 才能精准分析、给出可信答案；源头不强，再好的模型也是无米之炊。**
> 真源边界（info-flow-ssot 纪律）：叶子数/赛道结构→覆盖图（脚本实测）；旗舰源定稿→深调报告 + track-registry §9；付费报价→R1 报价单；接入状态→激活台账。本文引用，不复制字面值。

---

## 一、数据架构：双层（🆓 开源免费底座 + 💰 中国本土付费增强）

probe 不是「单一付费聚合商的二道贩子」，而是 **开源免费源打底 + 中国本土付费源补深** 的双层结构：

| 层 | 角色 | 典型源 | 成本 | 接入门 |
|----|------|--------|------|--------|
| **🆓 开源免费底座** | 全球公开/官方/学术权威，无 key 或免费 tier 即可达 | openFDA · GLEIF · SEC EDGAR · World Bank · OpenSanctions · OpenAlex · Google Fact Check · GDELT · OpenRouter · HuggingFace · Tushare/AKShare · CoinGecko/FRED · yt-dlp | 0 | 直接写适配器 |
| **💰 中国本土付费增强** | 补「开源拿不到」的中国工商/司法/电商带货/比价/药品监管深度 | 天眼查 · 企查查 · 蝉妈妈/新榜 · 维易/慢慢买 · 摩熵医药 · Wind | 年订阅¥万–$20万 | R1 报价 + 元东方授权 |

**判据**：能用开源免费覆盖的，绝不付费；只有「中国官方无 API + 铁律禁爬」造成的结构性缺口，才走付费聚合商（见 §四 四类硬缺口）。

---

## 二、规模骨架（真源：覆盖图 · 脚本实测非估算）

**10 赛道 × 8 端口 = 80 个情报机制位；672 个品类树叶子（待对接行业板块）；18 信息域 D1–D18。**

| 赛道 | 类型 | 叶子 | gaps | 首选旗舰源（🆓 免费 / 💰 付费 双层） |
|------|------|------|------|------|
| A 自媒体 | horizontal | 67 | 6 | 🆓 yt-dlp / B站API / YouTube Data · 💰 蝉妈妈（直播电商带货）+ 新榜有数 |
| B 商业市场 | horizontal | 86 | 6 | 🆓 GLEIF / SEC EDGAR / World Bank · 💰 天眼查（中国工商）+ 剑鱼标讯 |
| C 尽调风控 | horizontal | 56 | 7 | 🆓 OpenSanctions / GLEIF / sanctions.network · 💰 企查查（中国司法/UBO） |
| D 调研知识 | horizontal | 67 | 7 | 🆓 World Bank / OECD / OpenAlex · 💰 Statista + IBISWorld |
| E 真伪核查 | horizontal | 44 | 8 | 🆓 Google Fact Check / GDELT / Wikidata（**全免费旗舰**）· 💰 GPTZero（补 AI 检测） |
| F 金融财经 | vertical | 54 | 7 | 🆓 Tushare / AKShare / SEC EDGAR / CoinGecko / FRED · 💰 Wind（机构事实标准） |
| G 元惠 | vertical | 80 | 7 | 🆓 联盟官方 API（大淘客/阿里妈妈，抽佣）· 💰 维易 + 慢慢买（历史价唯一源） |
| H 任务 | vertical | 65 | 7 | 🆓 自建采集 + 猪八戒 + 多多进宝 + 积分墙（**无整合旗舰源**·固有难点） |
| I AI优惠 | vertical | 131 | 6 | 🆓 OpenRouter / HuggingFace / GitHub（**全免费旗舰**·最深 131 叶子） |
| J 医药 | vertical | 22 | 4 | 🆓 openFDA / RxNorm / DailyMed / WHO / PubMed · 💰 摩熵医药（中国药品监管） |
| **合计** | — | **672** | **65** | — |

> 叶子数/gaps 为脚本实测（`yaml.safe_load` + 叶子递归计数）。真源：`metafoclaw-git/docs/engines/probe/1-inventory/_coverage-map.md`（镜像层）+ 各赛道 `_matrix.yaml`。

---

## 三、免费 / 付费分布（决定接入成本与优先级）

| 类别 | 赛道 | 说明 |
|------|------|------|
| **🆓 纯免费旗舰即可达主体** | E 核查 · I AI优惠 | 旗舰源全免费 → 零成本优先接 |
| **🆓+💰 免费打底 + 付费增强** | D 调研 · F 金融 · J 医药 | 免费层覆盖基础，付费补深度与中国数据 |
| **💰 必付费整合源（走 R1）** | A 自媒体 · B 商业 · C 尽调 | 行业整合数据无免费替代 |
| **🆓 自建为主** | H 任务 | 无整合源，靠自建爬采（工程成本而非采购成本） |
| **💰 低门槛付费** | G 元惠 | 维易 ¥158/月起，CPS 联盟多免费抽佣 |

---

## 四、四类付费硬缺口（无开源替代 · 结构性合规债）

中国官方系统（gsxt / 裁判文书网 / 信用中国 / NMPA）**全部无对外 API + probe 铁律禁爬** → 以下四类只能走付费聚合商，这是**结构问题，非省钱能绕开**：

| # | 缺口 | 赛道 | 唯一路径 |
|---|------|------|---------|
| 1 | 中国工商 / 司法 | B · C | 企查查 · 天眼查（B/C 共享，一次采购两赛道共用） |
| 2 | 抖音/快手/小红书 电商带货 | A | 蝉妈妈（直播电商达人/商品/直播间最深） |
| 3 | 电商比价 CPS / 历史价 | G | 维易 · 慢慢买（10 年+ 历史价曲线唯一规模化源） |
| 4 | 中国药品审批/集采/医保 | J | 摩熵医药 · 药智网（NMPA 批文+集采+医保） |

> 反向印证：E（核查）/I（AI优惠）/D 学术层/J 国际层 **无硬缺口**——开源免费即达权威覆盖。

---

## 五、接入优先级（零成本先行 · 分三批）

| 批次 | 内容 | 成本 | 动作 |
|------|------|------|------|
| **第一批·免费零 R1** | 全部 🆓 无 key 源写适配器升 live（I/E/D/J 免费层 + F 的 Tushare/AKShare/EDGAR + B/C 的 GLEIF/OpenSanctions/EDGAR） | 0 | 先 curl 实测（§3b）→ 按 SOP 第 4 步写适配器 |
| **第二批·低成本付费** | 维易（¥1280/年级）· Tushare Pro（¥200级）· 东财 Choice | 低 | R1 小额授权后接 |
| **第三批·高价 R1 逐个授权** | 天眼查/企查查 · 蝉妈妈/新榜 · Wind · Statista · 摩熵 · World-Check（仅跨境专项） | 高 | **按主攻赛道逐个 R1 报价 + 元东方授权，别全接** |

> 付费源接入走 **P0 R1**（报价→密码授权→开通），含 key 走 **R8 vault**。详细报价见 R1 报价单（§3c）。

---

## 六、矛盾修正（口径统一 · 本文为权威口径 · 真源同步待办见 §七）

| # | 矛盾 | 旧/漂移态 | **统一口径（本文权威）** |
|---|------|----------|----------|
| **M1** | 赛道数 | track-registry §3 标题「八条赛道注册表」，缺 I-aideal / J-pharma | **统一 10 赛道**（A–J）；track-registry §3 须补 I/J 两行，标题改「十条」 |
| **M2** | 信息域数 | 部分文档只述 D15-D16 | **统一 18 域（D1–D18）**；真源 ledger.yaml `domains:` 段 |
| **M3** | C 尽调国际合规源 | flagship/coverage 列 World-Check 为 C 次选旗舰 | **首选 OpenSanctions**（350+ 源/自托管 yente/商用 €1500/月级，降本 80%+）；**World-Check 降级为「跨境专项可选」**，仅高端跨境客户触发 |

---

## 七、真源同步待办（M1/M2/M3 传播 · 下一轮单独执行）

> 本文已声明统一口径；以下真源文件仍含旧态，需单独一轮逐个改 + 三源验证（**不在本步批量改**）：

- ⬜ M1：`docs/3-build/probe-track-registry-architecture-v1.0.md` §3 — 标题「八条→十条」，补 I-aideal / J-pharma 两行（含 schema 字段）
- ⬜ M1：`metafoclaw-git/.../_coverage-map.md` 已含 10 赛道（一致，无需改）
- ⬜ M3：track-registry §9.3 C 行 + coverage map C 行 — World-Check 标注「跨境专项可选」，OpenSanctions 升首选
- ⬜ M2：核对 ledger.yaml `domains:` 段确为 D1–D18 共 18 域（一致则仅登记，不改）

---

## 八、SSOT 引用索引（本文是入口 · 深度见各真源）

| 主题 | 真源文件 |
|------|---------|
| 赛道结构 / 叶子数 / 端口 | `1-inventory/_coverage-map.md`（镜像层·脚本实测）+ 各 `_matrix.yaml` |
| 旗舰源定稿（首选/次选/出处） | [深调报告](6-datasources/probe-flagship-sources-research-v1.0.md) + [track-registry §9](3-build/probe-track-registry-architecture-v1.0.md) |
| 开源免费替代（curl 实测 verified） | [开源替代清单](6-datasources/probe-opensource-alternatives-v1.0.md)（§3b·待建） |
| 付费源报价（R1 待拍板） | [R1 报价单](6-datasources/probe-r1-paid-source-quotation-v1.0.md) + [付费短名单](6-datasources/probe-paid-sources-shortlist-v1.0.md)（§3c·待建） |
| 接入状态 / live 进度 | [激活台账](6-datasources/probe-datasource-activation-log-v1.0.md) |
| 赛道分类 / 域 / 闸 真源仲裁 | `records/probe-ssot-master-reconciliation-v1.0.md` §1 |
| 新赛道接入 SOP | [新赛道 SOP](3-build/probe-new-track-onboarding-sop-v1.0.md) |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> v1.0 · 2026-06-13 · probe 数据源体系 SSOT 入口 · 上游：probe-master-solution-v2 · 理念真源：track-registry §9

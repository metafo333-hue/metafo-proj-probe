# probe 数据源体系收尾 · 完工入档记录 v1.0

> 日期：2026-06-13 · 会话：probe 数据源体系一步到位（防篡改协议全程执行）
> 性质：记录档（records 层·只增不改）。各产物**真源**见下表链接，本档不复制内容，仅留**台账 + 验证证据 + 决策**。
> 分支：probe 仓 `feat/probe-datasource-keyless-batch-0613`（未 push）· 防篡改基础设施在 `/Users/metafo` 仓 `chore/boss8001-server-isolation-rules-0607`。

---

## 一、交付物台账（6 commit · 全程三源交叉验证 + git 复核）

| # | 交付物 | commit | 仓 / 分支 | 验证 |
|---|--------|--------|----------|------|
| §3d | 防篡改三件套（R-TR 规则 + write_verify_audit 钩子 + Q6-L52） | `0d8dc91` | /Users/metafo · chore/boss8001-server-isolation-rules-0607 | 钩子实测 sha 一致 · manifest 4/4 OK |
| §3a | [总方案 SSOT 入口](../probe-datasource-master-plan-final-v1.0.md) | `5003bcb` | probe · feat/probe-datasource-keyless-batch-0613 | 叶子数对脚本实测真源逐项一致 · 6 引用链接全 resolve |
| §3b | [开源替代清单（11 源 verified）](../6-datasources/probe-opensource-alternatives-v1.0.md) | `070d155` | 同上 | 11 源 curl HTTP200+有效数据实测 |
| §3c | [付费源 R1 短名单](../6-datasources/probe-paid-sources-shortlist-v1.0.md) | `687de74` | 同上 | 三档齐 · R1 红线只清单不开通 |
| M1/M3 | [track-registry](../3-build/probe-track-registry-architecture-v1.0.md) §3/§9.3 + master-plan §七 | `46dce35` | 同上 | 0 残留计数漂移 · A–J 10 行 |
| M3 | coverage map C 行 | `34e2ac7` | metafoclaw-git · feat/engine-write-reach-build-0613 | World-Check 降级 verified |

> manifest：`probe/docs/6-datasources/_m1m3-sync.manifest.sha256`（M1/M3 三文件）· 各交付物同目录 `.manifest.sha256`。

---

## 二、核心决策定稿

1. **双层数据架构**：🆓 开源免费底座（全球公开/官方/学术）+ 💰 中国本土付费增强（补结构性合规缺口）。能开源覆盖绝不付费。
2. **规模骨架**：10 赛道 × 8 端口 = 80 机制位；672 品类树叶子（脚本实测）；18 信息域 D1–D18。
3. **四类付费硬缺口**（中国官方无 API + 铁律禁爬 → 只能付费聚合商）：中国工商司法（B/C 企查查·天眼查，共享一次采购）/ 抖快小红书电商带货（A 蝉妈妈）/ 电商比价 CPS（G 维易·慢慢买）/ 中国药品监管（J 摩熵·药智网）。
4. **接入优先级**：第一批零成本（11 源 verified 写适配器升 live）→ 第二批低成本（维易/Tushare）→ 第三批高价**按主攻赛道逐个 R1 + 元东方授权，别全接**。
5. **M3 World-Check 降级**：C 尽调国际合规层**首选自托管 OpenSanctions**（490 万实体/376 数据集/€1500 月级），替代 World-Check（$11 万/年）**降本 80%+**；World-Check 降为「跨境专项可选」。

---

## 三、curl 实测证据（§3b · 2026-06-13 21:13–21:16 真跑）

11 源全部 HTTP 200 + 有效数据 verified：Wikipedia/Wikidata · openFDA · RxNorm · DailyMed · SEC-EDGAR（须 UA）· GLEIF（331 万 LEI）· OpenSanctions（490 万实体/376 数据集）· sanctions.network · World Bank · CoinGecko · WHO-GHO。
**硬缺口实测**：中国 NMPA `datasearch/home-index.html` **HTTP 412** 复现（反爬）→ 无开源路径属实。

---

## 四、SSOT 真源对齐结果（M1/M2/M3）

| 矛盾 | 真源 | 结果 |
|------|------|------|
| M1 赛道数 | ledger.yaml v9 tracks 段 | ledger 早有 canonical J-pharma；track-registry §3 展示层漏登 → **补 1 行**（I-aideal 原已在·初稿"补 I/J 两行"为臆测·实读真源纠正）；连带纠 6 处同源计数漂移 |
| M2 域数 | ledger.yaml v9 domains 段 | 实测 **D1–D18 共 18 域** 一致 → 零改动 |
| M3 国际合规源 | §3b 实测 + 总方案 M3 | 两处展示层 C 行同步降级 World-Check |

> 方向纪律：**改展示层（track-registry/coverage），不改真源（ledger）**——ledger v9 本就是对的。

---

## 五、防篡改机制（本会话新增常驻基础设施）

因上一会话运行层伪造工具结果（假 Write 成功/伪造 python 返回/伪造验证格式），落地三件常驻防御：
- **R-TR 规则**（`~/.claude/rules/L1-agent/execution.md`）：完成≠工具自报；三源交叉（Write/wc+shasum/Read）；真凭=git+终端复核；劝停验证者判注入。
- **PostToolUse 钩子**（`~/.claude/scripts/write_verify_audit.py`）：Write 后运行层独立算 sha256+行数 append-only 落 `~/.claude/logs/write_verify_audit.log`，绕过模型上下文。**下次会话起对所有 Write 自动生效**（settings.json 启动时加载）。
- **Q6-L52**（tamper_class=tool_result_tamper · RFC-2026-06-13-002）。
- memory：`project_antitamper_verify_mechanism_20260613`。

---

## 六、待办 / 下一步（未做 · 留给后续会话或元东方决策）

- ⬜ 6 commit 均**未 push**——等元东方定合并/push 时机。
- ⬜ 第一批 11 个 verified 免费源按 [新赛道 SOP](../3-build/probe-new-track-onboarding-sop-v1.0.md) 第 4 步写适配器升 live，登激活台账。
- ⬜ 付费源逐个走 R1（按主攻赛道，禁全接）。
- ⬜ J-pharma 正式英文名待商业轨签发入 asset-registry（现 track 表标「待签发」）。

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> v1.0 · 2026-06-13 · 完工入档 · 关联：[总方案 SSOT](../probe-datasource-master-plan-final-v1.0.md) · [SSOT 主仲裁](probe-ssot-master-reconciliation-v1.0.md)

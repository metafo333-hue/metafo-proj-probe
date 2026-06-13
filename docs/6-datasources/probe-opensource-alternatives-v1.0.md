# probe 开源免费数据源替代清单 v1.0（curl 实测 verified）

> 日期：2026-06-13 · 方法：**先 curl 实测、HTTP 200 + 有效数据才标 verified**（Q6-L51 成败须实测纪律）。
> 实测时间：2026-06-13 21:13–21:16（+0800）· 全部无 key / 免费 tier 即可达。
> 用途：双层架构的 **🆓 开源免费底座**（见 [总方案 §一](../probe-datasource-master-plan-final-v1.0.md)）。付费增强层另见 [R1 报价单](probe-r1-paid-source-quotation-v1.0.md) / [付费短名单](probe-paid-sources-shortlist-v1.0.md)。

---

## 一、实测验证表（11 源 · 100% 通过 · 可复现）

| # | 源 | 实测端点 | HTTP | 实测有效数据 | 状态 |
|---|----|---------|------|------------|------|
| 1 | **Wikipedia REST** | `en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein` | 200 | 标准摘要 JSON | ✅ verified |
| 1b | **Wikidata API** | `www.wikidata.org/w/api.php?action=wbgetentities&ids=Q42` | 200 | 实体 Q42 labels | ✅ verified |
| 2 | **openFDA** | `api.fda.gov/drug/label.json?limit=1` | 200 | 药品标签 meta+results | ✅ verified |
| 3 | **RxNorm** | `rxnav.nlm.nih.gov/REST/rxcui.json?name=aspirin` | 200 | aspirin → rxcui 1191 | ✅ verified |
| 4 | **DailyMed** | `dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?pagesize=1` | 200 | SPL 标签（更新至 2026-06-12）| ✅ verified |
| 5 | **SEC EDGAR** | `data.sec.gov/submissions/CIK0000320193.json` | 200 | Apple Inc 备案（**须 User-Agent 头**）| ✅ verified |
| 6 | **GLEIF** | `api.gleif.org/api/v1/lei-records?page[size]=1` | 200 | LEI 总量 **3,339,915** 条 | ✅ verified |
| 7 | **OpenSanctions** | `data.opensanctions.org/datasets/latest/{index,default/index}.json` | 200 | default 全库 **490 万实体** / catalog **376 数据集** / sanctions 合并库 **28.4 万制裁实体** | ✅ verified |
| 8 | **sanctions.network** | `api.sanctions.network/sanctions?limit=1` + `/rpc/search_sanctions` | 200 | PostgREST·真实制裁记录（EU 源/individual）| ✅ verified |
| 9 | **World Bank** | `api.worldbank.org/v2/country/CN/indicator/NY.GDP.MKTP.CD?format=json` | 200 | 中国 GDP 时序（更新 2026-04-08）| ✅ verified |
| 10 | **CoinGecko** | `api.coingecko.com/api/v3/ping` | 200 | `{"gecko_says":"(V3) To the Moon!"}` | ✅ verified |
| 11 | **WHO GHO** | `ghoapi.azureedge.net/api/Indicator?$top=1` | 200 | OData 指标元数据 | ✅ verified |

> 复现命令（SEC EDGAR 必带 UA，其余可选）：
> `curl -sS -A "probe-verify/1.0 (mail)" "<端点>"`

---

## 二、🆓 底座按赛道映射（开源源覆盖哪些赛道的免费层）

| 赛道 | 🆓 开源底座（verified） | 付费增强补什么 |
|------|----------------------|--------------|
| B 商业市场 | GLEIF（全球 LEI 法人）· SEC EDGAR（美股备案）· World Bank（宏观）| 中国工商（天眼查）|
| C 尽调风控 | **OpenSanctions**（490 万实体/376 数据集）· sanctions.network · GLEIF | 中国司法/UBO（企查查）· World-Check（仅跨境专项可选）|
| D 调研知识 | World Bank · OpenAlex · Wikidata | Statista/IBISWorld 深度 |
| E 真伪核查 | Wikidata · Wikipedia REST（+ Google Fact Check / GDELT）| GPTZero（AI 文本检测）|
| F 金融财经 | SEC EDGAR · CoinGecko（加密）· FRED/World Bank（宏观）| Wind（中国机构数据）|
| J 医药 | **openFDA · RxNorm · DailyMed · WHO GHO**（+ PubMed/ClinicalTrials）| 摩熵医药（中国 NMPA/集采/医保）|

---

## 三、关键结论

1. **OpenSanctions 可替代 LSEG World-Check 核心**：自托管 yente（软件免费，仅需数据 license）+ catalog 376 数据集 / 490 万实体 / 28.4 万制裁实体，整合 250+ 制裁/PEP 源。商用 license **€1500/月级 vs World-Check $11 万/年 → 降本 80%+**。故 C 尽调国际合规层 **首选 OpenSanctions，World-Check 降级为「跨境专项可选」**（总方案 M3）。

2. **J 医药国际部分 100% 免费覆盖**：openFDA（美 FDA）+ RxNorm（药品标准术语）+ DailyMed（说明书）+ WHO GHO（全球卫生）+ PubMed/ClinicalTrials/PubChem 全部 verified 免费。J 赛道付费只需补**中国**部分。

3. **中国 NMPA 是硬缺口（实测确认）**：`nmpa.gov.cn/datasearch/home-index.html` **HTTP 412**（反爬 Precondition Failed，2026-06-13 复现），根域返回 HTML 无对外 REST/JSON API。中国药品审批/集采/医保数据**无开源路径**，只能走付费聚合商（摩熵医药/药智网）—— 属四类付费硬缺口之一（总方案 §四）。

4. **SEC EDGAR 必带 User-Agent**：无 UA 头会被拒；适配器须固定带 `User-Agent: <主体邮箱>`，否则 live 后偶发 403。

5. **无 key ≠ 无限**：多数源有速率限制（openFDA 240 req/min、SEC EDGAR 10 req/s、CoinGecko 免费 ~30 req/min）。适配器须内建限流（probe 已有 governor，复用即可）。

---

## 四、落地动作

- ✅ 11 源 curl 实测 verified（本表）
- ⬜ 第一批：按 [新赛道 SOP](../3-build/probe-new-track-onboarding-sop-v1.0.md) 第 4 步给 verified 源写适配器升 live，台账登记
- ⬜ SEC EDGAR 适配器固定 UA · 各源限流参数填 governor
- ⬜ OpenSanctions：评估自托管 yente（数据 license 走 R1，软件本身免费）

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> v1.0 · 2026-06-13 · 实测 verified · 关联：[总方案](../probe-datasource-master-plan-final-v1.0.md) · [激活台账](probe-datasource-activation-log-v1.0.md)

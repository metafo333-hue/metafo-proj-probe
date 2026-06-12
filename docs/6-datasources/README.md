# 6-datasources · 数据源接入运营

> 数据源接入的三件套：参考手册 · 排期表 · 激活台账  
> 代码层真源：`probe/app/datasources/ledger.yaml`（v8 · 56源 · 48 live）

---

## 三件套文档

| 序 | 文件 | 角色 | 何时读 |
|----|------|------|--------|
| ① | [probe-api-reference-v1.0.md](probe-api-reference-v1.0.md) | **接入参考手册**（每个 API 的服务内容/覆盖范围/特点/特长/优势/真实度/速率限制/状态） | 接入新源、评估能力、方案选型时 |
| ② | [probe-api-integration-schedule-v1.0.md](probe-api-integration-schedule-v1.0.md) | **接入排期表**（优先级分批 · 待注册 9 源 · 待部署 7 源 · AlphaVantage 待写 adapter） | 规划下一步接入工作时 |
| ③ | [probe-datasource-activation-log-v1.0.md](probe-datasource-activation-log-v1.0.md) | **激活台账**（每个源的 key 状态 · 注册方式 · 入 vault 时间） | 核查某源是否已激活、key 在哪 |

---

## 与其他层的关系

| 层 | 位置 | 说明 |
|----|------|------|
| 代码 SSOT | `probe/app/datasources/ledger.yaml` | 运行时权威，status/domain/cost 字段 |
| 调研层（能不能用） | `docs/4-research/datasource-*.md` | 赛道级源调研，9 赛道 A-I |
| 架构层（怎么用） | `docs/3-build/probe-datasource-runtime-architecture-v1.0.md` | 四引擎控制平面 |
| 接入运营层（接了什么） | 本目录（`6-datasources/`） | 已接·在接·待接的操作档案 |
| 凭据 | `~/vault/credentials/api/probe.env` | 真值，chmod 600 |

---

## 待办状态（2026-06-12）

| 项 | 数量 | 说明 |
|----|------|------|
| 待手动注册 key | 9 源 | FRED / BLS / HF / VirusTotal / urlscan / AbuseIPDB / NVD / Pulsedive / SemScholar |
| 待部署 probe-a | 7 源 | imf_sdmx / chinamoney_lpr / sge_gold / chinawealth / reddit_rss / exchange_deriv / wikidata_sparql |
| 待写 adapter | 1 源 | AlphaVantage（key 已在 vault） |
| 待 R1 授权 | 1 源 | TikHub（$0.001/req · D16 唯一覆盖）|

> 详见排期表 ② 和激活台账 ③。

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1

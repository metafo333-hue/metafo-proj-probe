# 跨境外贸源 · 可执行 adapter 接入清单 v1.0

> 把调研层 [industry-crossborder-trade-sourcemap-v1.0](../4-research/industry-crossborder-trade-sourcemap-v1.0.md) 转成实施顺序。
> 口径：对接 = 写 adapter + 实测真数据 + ledger status=live。
> 日期：2026-06-13 · 真源：本文件 + `app/datasources/ledger.yaml`

---

## 一、批次总览（按授权门槛排实施序）

| 批 | 门槛 | 源数 | 谁能做 | 状态 |
|----|------|------|--------|------|
| **B0 零授权 keyless** | 无需 key / 无需账号 | 3 新 | 元帅直接落地 | 🟢 WITS ✅ · UN Comtrade ✅ / Comext ⏳ |
| **B1 免费 key·自助注册** | 注册免费账号（R8 邮箱授权已有）| 3 | Playwright 自助·部分需手动过验证码 | ⬜ 待推 |
| **B2 需 probe-a 部署** | probe-a 上线 + 自托管/常驻 | 3 | 等 probe-a 部署 | ⬜ 阻塞于部署 |
| **B3 付费 R1** | 元东方密码授权 | 2 | 仅登记·待拍板 | ⬜ 报价待出 |

---

## 二、B0 · 零授权 keyless（立即可落地）

| 源 | module | domain | 端点 | 状态 |
|----|--------|--------|------|------|
| **WITS**（World Bank 关税） | `public/wits.py` | D14/D11 | `wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-tariff` | ✅ **已 live**（实测 chn/usa 关税 29 品类组 · probe 首个关税源） |
| **UN Comtrade**（双边贸易流） | `public/un_comtrade.py` | D11/D14 | `comtradeapi.un.org/public/v1/preview`（keyless preview·≤500条） | ✅ **已 live**（实测 China 2022 出口 $3.59T + 美国进口 224 伙伴 · 贸易流第二独立源） |
| Eurostat Comext（EU 贸易流 CN8） | `public/eurostat_comext.py` | D11/D14 | `ec.europa.eu/eurostat/api/comext/dissemination` | ⏳ time 参数格式待攻克（dissemination API 较 WITS 刁钻·降级 P1 续接） |

> 注：现有 `eurostat.py` 走通用统计 dissemination API，**不含 Comext 贸易库**；Comext 是独立贸易数据库，故列为新增。

## 三、B1 · 免费 key·自助注册（下一批·R8 邮箱授权已有）

> 注：UN Comtrade 原列 B1，实测发现 keyless preview 端点（≤500条）已够用 → 升 B0 已 live；
> 全量 subscription key 待用量超 preview 上限时再注册升级。

| 源 | module | 注册地址 | 审批 | 验证码风险 |
|----|--------|---------|------|-----------|
| **UK Companies House**（英国企业注册·董事·PSC · 海外企业第二源） | `public/companies_house.py` | developer.company-information.service.gov.uk | 即时 | 低·可自助 |
| **WTO Timeseries**（关税 Bound/MFN/优惠·NTM · 关税第二源） | `public/wto.py` | apiportal.wto.org | 自动批准 | 中 |
| **US Census Trade**（美国进出口 HS/NAICS） | `public/census_trade.py` | census.gov/developers | 邮件激活 | 中 |

## 四、B2 · 需 probe-a 部署（阻塞于 probe-a 上线）

| 源 | 原因 | 部署要求 |
|----|------|---------|
| **OpenSanctions yente**（多国制裁·模糊匹配） | 自托管服务 | probe-a · Docker 双容器 · 8GB RAM + ES |
| **aisstream.io**（实时 AIS 船位） | WebSocket 高带宽流 300 条/秒 | probe-a 后台常驻消费 |
| **AISHub**（实时船位备源） | 同上流式 | probe-a 常驻 |

## 五、B3 · 付费 R1（仅登记·待拍板）

| 源 | 用途 | 预估成本 | 触发条件 |
|----|------|---------|---------|
| OpenSanctions 商用 license | 生产级制裁筛查 | 联系报价（startup 折扣可申请） | 有商业合规客户时 |
| OpenCorporates 商用 API | 140+ 国企业查询 | £2,250/年起 | 有背调产品时 |
| ShipsGo 集装箱追踪 | 精确货物里程碑 | $20 起按量 | 有物流可视化产品时 |

---

## 六、验证冗余达标情况（闸 2 · 一论断需 ≥2 独立源）

| 数据类 | 独立源凑齐？ | 现状 |
|--------|------------|------|
| 海关贸易流 | ✅✅ **闸2 已达标** | WITS(已live) + UN Comtrade(已live) 两源均 live · US Census(B1) 作第三角 |
| 关税 | 🟡 单源 | WITS(已live·AHS) + WTO(B1·Bound/MFN) 待补第二源 |
| 海外企业 | 🟡 单源 | GLEIF(已live) + UK Companies House(B1) 待补第二源 |
| 制裁 | 🟡 单源 | OFAC SLS(已live) + OpenSanctions(B2/B3) 待补第二源 |

> **海关贸易流已双源 live → 这类论断闸2 跨源印证当下即可跑通。** 关税/企业/制裁各有一个 live 源打底，补齐 B1/B2 第二腿即全闭环。

---

## 七、实施纪律

1. 每个 adapter 仿 `public/frankfurter.py` / `public/wits.py` 风格：模块级 `META` + `configured()` + 取数函数 · 失败返空不抛。
2. 落 ledger 前必 **Mac 实测取到真数据**（R0.6），caveat 注明实测日期。
3. ledger.yaml 是共享文件 → 多 adapter 并发写代码可并行，**注册条目串行**（R36 反例：禁并发写同一文件）。
4. 完整 selftest 在 probe-a 运行时环境跑（本机无 fastapi 依赖）。

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1
> v1.0 · 2026-06-13 · 关联：[源地图](../4-research/industry-crossborder-trade-sourcemap-v1.0.md) · [激活台账](probe-datasource-activation-log-v1.0.md)

# 6-datasources · 数据源接入运营

> 代码层状态真源（唯一）：`probe/app/datasources/ledger.yaml`
> 本目录为人工操作档案，补充"为什么"和历史背景，不重定义 status。

---

## ⚠️ 合规架构声明

国内社媒平台（抖音/快手/B站/小红书/微博）官方开放平台**只给自有账号数据**，竞品情报官方零供给。probe 采购 TikHub 持牌付费 API 作为合规代理——这是已知的**合规债**，供应商担责"如何取数"，probe 只对"调用行为"负责。详见 [datasource-selfmedia-track-a-v1.md §六](../4-research/datasource-selfmedia-track-a-v1.md)。

---

## 文档清单

| 文件 | 角色 | 状态 |
|------|------|------|
| **[datasource-ledger-and-status-v2.md](datasource-ledger-and-status-v2.md)** | **主台账（当前·v2.0）** — 状态快照 + 合规架构 + 待办队列 + 凭据地图 | ✅ **当前维护** |
| [probe-api-reference-v1.0.md](probe-api-reference-v1.0.md) | 接入参考手册（56 源·7 维度·能力速查） | ✅ 长效参考 |
| [probe-datasource-activation-log-v1.0.md](probe-datasource-activation-log-v1.0.md) | 历史激活台账（2026-06-12 施工记录） | 📚 只读历史 |
| [probe-api-integration-schedule-v1.0.md](probe-api-integration-schedule-v1.0.md) | 历史排期表（2026-06-12 P0 wave 记录） | 📚 只读历史 |

---

## 与其他层的关系

| 层 | 位置 | 说明 |
|----|------|------|
| 代码 SSOT | `probe/app/datasources/ledger.yaml` | 运行时权威，status/domain/cost |
| 调研层（能不能用）| `docs/4-research/datasource-*.md` | 9 赛道 A-I 合规选型 |
| 架构层（怎么用）| `docs/3-build/probe-datasource-runtime-architecture-v1.0.md` | 四引擎控制平面 |
| 凭据 | `~/vault/credentials/api/probe.env` | 真值，chmod 600 |

---

> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1

# 元探 MetaProbe · 工作现状台账 v1.0

> ⚠️ **此文档已过期（停在 2026-06-13）**，以下内容已发生重大变化：
> - TikHub 已接入（key 已配），抖音 play_count 已修复（统计专用端点），JZL 微信视频号已接入
> - 数据源扩展至 58 源（ledger v9），wikidata_sparql/reddit_rss 已转 live
> - 案例库建成（5个案例），报告润色层已上线
> **当前状态真源**：[6-datasources/datasource-ledger-and-status-v2.md](6-datasources/datasource-ledger-and-status-v2.md)
>
> 更新：2026-06-13 · 性质：机械盘点（历史快照·不再维护）

---

## 一、文件夹结构总览

```
probe/
├── docs/                        ← 本地工作文档（比 git 更完整，见§五同步差距）
│   ├── 0-charter/               ← 立项文件（2 份）✅
│   ├── 1-inventory/             ← 现状盘点（1 份）✅
│   ├── 2-roadmap/               ← 路线图 HTML ✅
│   ├── 3-build/                 ← 工程设计文档（15 份）✅ 有14份未入git
│   ├── 4-research/              ← 技术调研+数据源（23 份）✅ 有17份未入git
│   ├── 5-brand/                 ← 品牌文案+UI设计规格（2 份）✅ 今日新建
│   ├── records/                 ← 决策记录（3 份）✅
│   ├── _archive/                ← 归档（4 份旧版）✅
│   ├── probe-master-solution-v2.md  ← 总方案单一真源 ✅
│   └── probe-work-status-v1.0.md   ← 本文件
│
├── app/                         ← Python 后端骨架
│   ├── main.py / config.py
│   ├── routers/                 ← invoke / manifest / task / selftest ✅骨架通
│   ├── core/                    ← billing / guards / sso / storage / tasks ✅
│   ├── audit/                   ← gates / standards / certainty / trace ✅骨架
│   ├── datasources/             ← registry / base / anysearch + 10 public 适配器
│   ├── extractors/              ← article / document ✅  video/social ⛔已隔离
│   ├── services/                ← pipeline / llm / report / deliverable ✅骨架
│   └── l0/                      ← _deprecated/ 已隔离 (爬虫路径)
│
└── 运营报告/（设计输出层·不在 probe/ 下）
    ├── probe-landing-v1.0.html     ← 落地页 ✅ 今日完成
    ├── probe-ui-v4.2.html          ← App Shell 最新版 ✅ 今日完成
    ├── probe-ui-v4.0/4.1.html     ← 历史版本
    ├── probe-ui-wireframe-v1-3.html ← 历史线框
    ├── probe-ui-design-spec-v2.0/2.1.md ← 设计规格（副本在5-brand/）
    └── probe-ui-competitive-research-v1.0.md
```

---

## 二、文档层（docs/）完整清单

### 0-charter · 立项
| 文件 | 状态 |
|------|------|
| founding-charter-v1.0.md | ✅ |
| probe-vision-from-dialogue-v1.0.md | ✅ |

### 1-inventory · 现状盘点
| 文件 | 状态 |
|------|------|
| probe-inventory-v1.0.md | ✅ 2026-06-08 |

### 3-build · 工程设计（15 份）
| 文件 | git？|
|------|------|
| probe-api-v1.md | ✅ 已入 |
| probe-audit-system-v1.md | ✅ 已入 |
| probe-intelligence-engine-design-v1.md | ✅ 已入 |
| probe-speed-depth-tiering-v1.0.md | ✅ 已入 |
| probe-s1-impl-plan-v1.0.md | ⚠️ 未入 git |
| probe-compliance-gates-v1.md | ⚠️ 未入 git |
| probe-api-fetch-risk-checklist-v1.0.md | ⚠️ 未入 git |
| probe-cost-metering-design-v1.0.md | ⚠️ 未入 git |
| probe-data-dynamic-governance-design-v1.0.md | ⚠️ 未入 git |
| probe-data-persistence-and-cache-design-v1.0.md | ⚠️ 未入 git |
| probe-datasource-runtime-architecture-v1.0.md | ⚠️ 未入 git |
| probe-delivery-rendering-pipeline-design-v1.0.md | ⚠️ 未入 git |
| probe-monitoring-radar-and-feedback-loop-design-v1.0.md | ⚠️ 未入 git |
| probe-orchestration-concurrency-requirements-v1.0.md | ⚠️ 未入 git |
| probe-orchestration-engine-solution-v1.0.md | ⚠️ 未入 git |
| probe-privacy-retention-compliance-engineering-v1.0.md | ⚠️ 未入 git |
| probe-quality-eval-methodology-v1.0.md | ⚠️ 未入 git |
| probe-source-ops-and-reliability-design-v1.0.md | ⚠️ 未入 git |
| probe-source-selection-and-capability-registry-v1.0.md | ⚠️ 未入 git |
| probe-track-registry-architecture-v1.0.md | ⚠️ 未入 git |
| finance-track-f-design-and-competitive-v1.0.md | ⚠️ 未入 git |

### 4-research · 技术调研 + 数据源（23 份）
| 分类 | 份数 | git？|
|------|------|------|
| techstack-cards（M01-M13 + 底座裁定 + 决策总册）| 15 份 | ⚠️ 大部分未入 git |
| datasource 各域（A/B/C/D/E/F/G/H/I 赛道）| 12 份 | ⚠️ 未入 git |
| datasource-board-master-index | 1 份 | ⚠️ 未入 git |
| tikhub 深度调研 | 1 份 | ✅ 已入 |
| probe-github-datasource-feasibility-v1 | 1 份 | ✅ 已入 |

### 5-brand · 品牌文案（今日新建）
| 文件 | 状态 |
|------|------|
| probe-brand-copy-v1.0.md | ✅ 2026-06-12 新建 |
| probe-ui-design-spec-v2.1.md | ✅ 副本 |

### 6-datasources · 数据源接入运营（2026-06-12 新建）
| 文件 | 状态 |
|------|------|
| probe-api-reference-v1.0.md | ✅ 56源·7维度·接入状态 |
| probe-api-integration-schedule-v1.0.md | ✅ 优先级分批·排期 |
| probe-datasource-activation-log-v1.0.md | ✅ key状态·注册方式·vault路径 |
| README.md | ✅ |

### records · 决策记录
| 文件 | 状态 |
|------|------|
| probe-alignment-topology-prelaunch-v1.md | ✅ |
| probe-ssot-governance-v1.md | ✅ |
| probe-ssot-master-reconciliation-v1.0.md | ✅ 2026-06-11 仲裁 |
| probe-value-presentation-and-bizmodel-review-v1.md | ✅ |
| tikhub-r1-authorization-report-v1.0.md | ✅ TikHub付费授权评估 |
| README.md | ✅ 读序索引 |

---

## 三、代码层（app/）状态

### 已通（骨架可跑）
| 模块 | 状态 | 说明 |
|------|------|------|
| FastAPI 主入口 | ✅ | main.py + config.py |
| 5 个 API 路由 | ✅ | invoke/task/manifest/selftest/health |
| selftest 自检 | ✅ **11/11 通过** | 准入门全过 |
| 审核八闸骨架 | ✅ | gates.py + standards.py + certainty.py + trace.py |
| 三层深度裁剪 | ✅ | guards.py：public/preview/paid |
| SSO 身份验证 | ✅ | core/sso.py |
| billing 骨架 | ✅ | core/billing.py |
| anysearch 适配器 | ✅ | datasources/anysearch.py |
| 10 个 public 适配器 | ✅骨架 | arxiv/edgar/gdelt/github/opencorporates/osv/searxng/virustotal/webarchive/wikipedia |
| article/doc 提取器 | ✅ | extractors/ |

### 存根/未接真实后端
| 模块 | 状态 | 阻塞点 |
|------|------|--------|
| **八闸 backends** | ⚠️ StubBackend | 须接真实 LLM（faithfulness/nli/judge/aigc） |
| **tikhub 适配器** | ⚠️ 代码就绪·无 key | 需 R1 付费授权 |
| **governor.py** | ❌ 未建 | S1 施工：统一取数入口 |
| **metering.py** | ❌ 未建 | S1 施工：成本埋点 |
| llm._chat usage 透传 | ⚠️ 未做 | 成本无法计量 |
| 字段统一（s1-s7/redact_by_tier） | ⚠️ 错位 | D2 裁定已定，S1 落实 |

### 已隔离（不可用）
| 路径 | 原因 |
|------|------|
| app/l0/_deprecated/ (yt-dlp/Playwright 路径) | 违反「不自己爬」红线，已停用 |
| video/social 提取 | 须先经第三方合规 API |

---

## 四、UI / 设计层（运营报告/）

| 文件 | 版本 | 状态 |
|------|------|------|
| probe-ui-wireframe-v1.0~3.0.html | 历史线框 | ⚠️ 已过时·可归档 |
| probe-ui-design-spec-v2.0.md | 设计规格旧版 | ⚠️ 已被 v2.1 取代 |
| **probe-ui-design-spec-v2.1.md** | **设计规格** | ✅ **当前规格**（→ 5-brand/副本同步）|
| probe-ui-competitive-research-v1.0.md | 竞品研究 | ✅ 保留 |
| probe-ui-v4.0~4.2.html | App Shell 历史版 | ⚠️ 已过时·可归档 |
| probe-ui-v4.3.html | App Shell | 历史版（过渡） |
| probe-ui-v4.4.html | App Shell | 历史版（过渡） |
| **probe-ui-v4.5.html** | **App Shell** | ✅ **当前最新**（平台标准外壳参考）|
| **probe-landing-v1.0.html** | **落地页** | ✅ 当前有效 |
| probe-api-catalog-v1.0.html | API 目录 | ✅ 参考 |
| probe-datasource-dashboard-v1.0.html | 数据源看板 | ✅ 参考 |
| probe-brand-copy-v1.0.md | 文案库 | ✅ 2026-06-12（→ 5-brand/）|

---

## 五、git 同步差距（2026-06-13 更新）

**工作目录超前 git，未提交内容：**

| 层 | 未入 git 数量 | 内容 |
|----|------------|------|
| 0-charter | **1 份** | founding-charter-v1.0.md（新建·git 仍有旧 probe-vision-v1.0） |
| 3-build 设计文档 | **14 份** | finance-track + 完整工程设计（含 s1-impl-plan 等）|
| 4-research 调研 | **17 份** | 技术栈卡片 13 张 + 数据源域调研 A-I |
| 5-brand | **2 份** | 文案库 + 设计规格副本 |
| **6-datasources（全新目录）** | **4 份** | api-reference + integration-schedule + activation-log + README |
| records 新增 | **2 份** | tikhub-r1-authorization-report + README |
| probe-work-status-v1.0.md | **1 份** | 本文件 |
| records/probe-ssot-master-reconciliation-v1.0.md | 1 份 | SSOT 主仲裁总册 |
| **合计** | **~42 份** | 含全新 6-datasources 目录 + founding-charter + tikhub 报告 |

**git 有但工作目录版本不一致：**
- `3-build/COMPLIANCE-HANDOFF.md`（git 源·probe/docs 无此文件·属 deploy 注意事项）
- `3-build/DEPLOY.md`（同上）
- `records/probe-ssot-governance-v1.md`（git 镜像已同步修正"元典录→商业轨" 2026-06-13）

---

## 六、上线阻塞清单

| 项 | 阻塞类型 | 说明 |
|----|---------|------|
| probe.metafoclaw.com 域名部署 | 技术 | nginx conf + probe-a 部署脚本 |
| 八闸接真实 LLM backend | 技术 | StubBackend → 真模型 |
| tikhub API key | **R1 付费** | 需元东方授权 + 价格确认 |
| S1 施工（governor + metering + 字段） | 技术 | s1-impl-plan-v1.0.md 有完整清单 |
| 文档同步入 git | 运维 | 34 份未入 git |

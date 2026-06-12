# 技术源卡 M13 · 对象存储与存证（定型 G7）

> 需求真源：data-persistence（对象存储悬空）+ delivery（渲染产物）+ privacy（lifecycle 三态）· 喂缺口 G7
> checked_at: 2026-06-11 · 调研员：probe 技术调研 subagent

---

## 候选实测

### MinIO

| 维度 | 数据 |
|------|------|
| Repo | github.com/minio/minio |
| License SPDX | AGPL-3.0 |
| License 变化史 | 2021-05 从 Apache-2.0 迁移至 AGPL-3.0；2025-03 从社区版 WebUI 删除 policy/replication/监控等管理功能；2026-04-25 **主仓库已归档（read-only）** |
| Stars | 归档前约 50k+ |
| 最近活跃 | **2026-04-25 仓库归档，停止社区维护** |
| 单机资源占用 | 4–32 GB RAM（企业级设计，单机有额外开销） |
| S3 兼容 | 最完整（历史上是事实标准） |
| Lifecycle Rule 支持 | 支持（但管理 API 已移入商业版 AIStor） |
| 运维复杂度 | 中（单机可跑，但 AGPL 合规成本高） |
| checked_at | 2026-06-11 |

### SeaweedFS

| 维度 | 数据 |
|------|------|
| Repo | github.com/seaweedfs/seaweedfs |
| License SPDX | Apache-2.0 |
| License 变化史 | 始终 Apache-2.0，无变化 |
| Stars | ~32.8k（2026-06-08 release v4.32 最新） |
| 最近活跃 | **活跃**：v4.32 发布于 2026-06-08，14,149 commits |
| 单机资源占用 | Master 进程 ≈512 MB·Volume 进程 1–2 GB；单机 Docker 示例 master 512M/volume 1G |
| S3 兼容 | 较好（核心 API + 部分高级 API）；包含 `s3lifecycle` package |
| Lifecycle Rule 支持 | **⚠️ 部分实现，存在已知 bug**：Issue #6619（2025-03 开，状态 Open）——`bucket_lifecycle_configuration` 删除所有文件而非仅过期文件；TTL 过期另有原生机制可用 |
| 运维复杂度 | 中（Master+Volume+Filer 三组件，单机可合并运行） |
| checked_at | 2026-06-11 |

### Garage（deuxfleurs）

| 维度 | 数据 |
|------|------|
| Repo | github.com/deuxfleurs-org/garage（镜像）· 主仓：git.deuxfleurs.fr/Deuxfleurs/garage |
| License SPDX | AGPL-3.0 |
| License 变化史 | 始终 AGPL-3.0；NLnet/NGI0 欧盟资助，2025 年持续维护 |
| Stars | ~3.9k（GitHub 镜像，主仓另计） |
| 最近活跃 | 活跃：89 个 tag，2025–2026 持续 commit；NLnet 资金保障至少到 2025 年底 |
| 单机资源占用 | **极低**：单静态二进制 ~30 MB，运行内存 ≥1 GB，树莓派可跑 |
| S3 兼容 | 核心 API 完整；高级 API 缺失（见下方详表） |
| Lifecycle Rule 支持 | **部分支持**：仅 `AbortIncompleteMultipartUpload` 和 `Expiration` action；不支持 versioning 相关 lifecycle；`ExpiredObjectDeleteMarker` 不支持 |
| 运维复杂度 | **低**：单二进制，无外部依赖（无 ZooKeeper/etcd/独立 DB） |
| checked_at | 2026-06-11 |

**Garage 不支持的重要 S3 API：**
- ACL/Policy 端点（全缺）
- Object Versioning（stub 只返回"未启用"）
- Replication
- Object Locking
- Server-side Encryption（SSE）
- Object/Bucket Tagging

### RustFS（新发现·候选补充）

| 维度 | 数据 |
|------|------|
| Repo | github.com/rustfs/rustfs |
| License SPDX | Apache-2.0 |
| License 变化史 | 2025-07 开源，始终 Apache-2.0；定位为 MinIO 替代 |
| Stars | ~26.5k（2025-12 Beta 发布时数据） |
| 最近活跃 | 活跃：2800+ commits；2025-12 Beta；**尚在 Beta 阶段** |
| 单机资源占用 | ≥2 GB RAM |
| S3 兼容 | MinIO 兼容接口，drop-in 替换 |
| Lifecycle Rule 支持 | 待确认（Beta 阶段文档不完整） |
| 运维复杂度 | 低（单二进制，类 MinIO 操作） |
| checked_at | 2026-06-11 |

> ⚠️ RustFS 处于 Beta 阶段（2025-12），生产可用性风险高，本卡记录备案，**不作主选**。

---

## MinIO License 风波核实（现场查证）

**结论（2026-06-11 查证）：**

MinIO 的开源历史经历了三次关键转折，累积导致社区信任崩塌：

1. **2021-05 License 变更**：从 Apache-2.0 改为 AGPL-3.0。AGPL 要求：任何通过网络向用户提供 MinIO 服务的人（即使只修改了代码而未分发二进制），都必须开放对应源码。对商业闭源应用构成法律障碍，MinIO 也已有实际诉讼案例。

2. **2025-03 功能阉割**：从社区版 WebUI 删除了 policy 管理、实时监控、Replication 控制等核心管理功能，仅保留基本对象浏览器。完整管理功能迁入 AIStor Enterprise（起价约 $96k/年，约 ¥250k/PB/年）。社区反应极为负面（"只留了一个烦人的弹窗"）。

3. **2026-04-25 仓库归档（最关键）**：主仓库 github.com/minio/minio 已设为只读/归档状态，社区版开发实质终止。这意味着：
   - 安全漏洞不再收到社区修复
   - 新版本仅在商业渠道发布
   - Fork 维护者接手风险（AGPL 条件下 fork 合法，但维护成本全自担）

**对 probe 项目的直接影响**：MinIO 社区版已死，**不应作为新项目的技术选型**。即使内部私用（无商业分发）AGPL 本身勉强合规，但一个归档仓库意味着零安全维护。完全排除。

---

## 极简对照方案（本地盘 + nginx 静态）

**方案描述**：放弃对象存储层，直接用本地文件系统存储交付物，nginx 作为静态文件服务器对内暴露。

| 评估维度 | 得分 | 说明 |
|---------|------|------|
| 运维成本 | ✅ 极低 | 无新组件，仅文件夹 + nginx location |
| 开发成本 | ✅ 极低 | 直接写文件，无 SDK |
| S3 接口 | ❌ 无 | 未来迁移需改所有上传/下载代码 |
| Lifecycle 三态 | ⚠️ 手工 cron | 需自写 cleanup 脚本（7天 TTL、60天敏感数据）；无原子性保证 |
| 水平扩展 | ❌ 不支持 | 多进程写同目录有竞争风险 |
| 备份 | ⚠️ 依赖 rsync | 需手工配备份 cron 到 ufo:/data/backups/probe-collect/ |
| 存储上限 | ⚠️ 受限 probe-a 本机盘 | 无法弹性扩容（存储型盘非弹性） |
| 权限控制 | ❌ 粗粒度 | 仅 nginx 路径级，无 bucket/prefix 级控制 |

**适用条件**：只有当以下 **全部** 成立时才考虑：
- 交付物总量长期 <5 GB
- 无多实例部署计划
- 接受未来迁移代码成本
- lifecycle 三态用 cron 手工实现可接受

**本项目判断**：probe 的 persist_policy 三态（normal/ephemeral/sensitive）需要可靠 lifecycle，且未来可能多任务并发写入，**极简方案不达标**，作为 fallback 记录，不作主推荐。

---

## 存证捎带（SavePageNow API 现状）

**端点**：`https://web.archive.org/save/{TARGET_URL}`

| 维度 | 现状 |
|------|------|
| 费用 | 免费，无已知付费层 |
| 认证 | 无需 API key（GET 请求即可），但高频使用建议注册账号以获更高配额 |
| 速率限制 | **未公开具体数字**（Internet Archive GitHub issue #274，2024-10-31 开，至今无官方回应）；社区经验：每页间隔数分钟、保持低并发（1–3 路）可稳定运行；超限返回 HTTP 429 |
| 响应格式 | HTTP 响应头 `Content-Location` 指向已存档 URL（如 `/web/20260611120000/https://...`） |
| 限制 | 登录门/动态内容/SPA 不能完整存档；嵌入资源（CSS/图片）可能缺失 |
| 可用性 | 依赖 archive.org 服务稳定性；历史上有计划性维护期 |
| 替代方案 | SingleFile CLI（本地存档为单 HTML）· browsertrix/webrecorder（完整 WARC 存档）· 本地 Playwright 截图（快照替代） |

**probe 存证场景建议**：SavePageNow 适合"顺手存一下"的低频存证（如重要情报来源的公开页面）。对于 probe 的系统性网页快照需求，更稳健的是本地 Playwright `browser_take_screenshot` 存为 PNG/PDF 后入对象存储，SavePageNow 作为补充注释链接即可。速率限制不透明是最大风险，**不宜作为 pipeline 关键依赖**。

---

## tech-gate 12 闸速查表

| 闸 | 问题 | Garage (推荐) | SeaweedFS (备选) | 本地盘 (兜底) |
|----|------|-------------|----------------|------------|
| G1 | License 生产可用 | ⚠️ AGPL-3.0（内部私用合规·禁商业分发） | ✅ Apache-2.0 | ✅ N/A |
| G2 | 单机可运行（4C8G） | ✅ ≥1 GB RAM | ✅ ≥1.5 GB RAM | ✅ 零额外 |
| G3 | S3 API 兼容（核心） | ✅ 核心完整 | ✅ 核心完整 | ❌ 无 |
| G4 | Lifecycle Expiry 支持 | ✅ Expiration action 支持 | ⚠️ Bug #6619 open | ⚠️ 手工 cron |
| G5 | 单二进制/低依赖 | ✅ 30 MB 静态二进制 | ❌ 多组件（Master+Volume+Filer） | ✅ 无 |
| G6 | 活跃维护 | ✅ EU 资助·2025–2026 活跃 | ✅ v4.32·2026-06-08 | ✅ N/A |
| G7 | 归档/弃坑风险 | 低（公益资助·非商业驱动） | 低（Apache·活跃） | 无 |
| G8 | probe-a 本机部署可行 | ✅ 资源匹配 | ✅ 资源可行 | ✅ 天然 |
| G9 | bucket lifecycle 三态映射 | ✅ Expiration days 可配 | ⚠️ TTL 原生机制可替代 | ❌ 手工 |
| G10 | 无 PG/外部 DB 依赖 | ✅ 内嵌元数据（SQLite-like） | ⚠️ Filer 需 MySQL/SQLite | ✅ |
| G11 | 运维门槛 | ✅ 低（单二进制 + config） | ⚠️ 中（三组件协调） | ✅ 极低 |
| G12 | 存证/WebUI 可选 | ✅ 无强依赖 | ✅ 有内置 UI | ✅ nginx |

---

## verdict：G7 定型建议

### 选型结论：Garage（首选）

**理由**：
- 唯一满足"极低资源 + 单二进制 + S3 兼容 + Lifecycle Expiry + 无商业风险"五要素组合的方案
- AGPL-3.0 对 probe **内部私用**（不对外分发 SaaS）不构成实际法律障碍——probe-a 是私有基础设施，无网络分发义务触发
- MinIO 已归档出局；SeaweedFS lifecycle bug 未修复（Open #6619）带入数据残留风险；RustFS Beta 不成熟
- 资源占用与 probe-a（4C8G·已有 PG+Redis）完全兼容，预留 1 GB 足够

### 落机：probe-a 本机

**依据**：交付物与采集数据同源，本机存储避免 Tailscale 传输延迟；4C8G 资源预算，Garage 仅占 ~1 GB RAM；符合 T3 数据边界（采集数据留 probe-a）。

### Bucket 命名草案

```
probe-deliveries          # PDF/PPT/图片等大型交付物（normal persist）
probe-renders             # HTML 渲染快照（ephemeral·7天 TTL）
probe-evidence            # 网页存证截图（sensitive·≤60天）
probe-tmp                 # 任务中间产物（ephemeral·24h TTL）
```

### Lifecycle 三态映射

| persist_policy | Bucket | Garage Lifecycle Rule | 保留期 |
|----------------|--------|----------------------|--------|
| `normal` | probe-deliveries | 无自动过期（手工清理或按需） | 无限期 |
| `ephemeral` | probe-renders / probe-tmp | `Expiration.Days = 7`（renders）/ `Days = 1`（tmp） | 7天 / 1天 |
| `sensitive` | probe-evidence | `Expiration.Days = 60` | ≤60天（满足 PIPL 最小化要求） |

**lifecycle rule 配置示例（S3 XML）**：
```xml
<LifecycleConfiguration>
  <Rule>
    <ID>ephemeral-expire</ID>
    <Status>Enabled</Status>
    <Expiration><Days>7</Days></Expiration>
  </Rule>
</LifecycleConfiguration>
```

### 替换出口

- 若 Garage AGPL 内部合规审计不通过 → **SeaweedFS**（Apache-2.0，等待 #6619 修复，或用 TTL 原生机制替代 S3 lifecycle）
- 若交付物总量长期 <5 GB 且无多实例需求 → **本地盘 + nginx**（以 cron 脚本实现三态清理）
- MinIO（社区版）和 RustFS（Beta）**不进候选**

---

## 顺手发现

1. **RustFS**（Apache-2.0，2025-07 开源，Rust 实现，MinIO drop-in 替换）：26.5k stars，2025-12 Beta，社区增速极快，但生产稳定性未经验证。若 6 个月后成熟，可作为第二备选替换 SeaweedFS。
2. **MinIO 仓库归档（2026-04-25）**：任何现存依赖 MinIO 社区版的系统均应制定迁移计划，这是本卡调研中最重要的突破性事实。
3. **Garage AGPL 内部豁免逻辑**：AGPL 的"网络使用触发源码开放"条款，其触发条件是"通过网络向他人提供服务"——probe-a 的对象存储仅供 probe 内部读写，不对外用户开放，**不触发 AGPL 开放义务**。与 garage 作为生产基础设施使用法律风险极低，但建议在 probe 技术决策文档中留一行备注。
4. **SeaweedFS lifecycle bug #6619**（2025-03·Open）：若选 SeaweedFS，短期 workaround = 用 TTL 原生 `entry TTL` 字段替代 S3 lifecycle，功能等价但 API 不标准。
5. **存证替代链**：SavePageNow（顺带注释）→ Playwright PDF 存本地 → 入 probe-evidence bucket（Garage）→ 60天 lifecycle 清理。完整链路无第三方依赖。

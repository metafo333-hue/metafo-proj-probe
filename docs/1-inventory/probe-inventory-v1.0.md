# 元探（MetaProbe）· 现状盘点 v1.0 · 2026-06-08

> 性质：probe 引擎「现在有什么」的事实盘点（②盘点层）。
> 对应初心见 [0-charter/founding-charter-v1.0.md](../0-charter/founding-charter-v1.0.md)，差距规划见 [2-roadmap/](../2-roadmap/)。
> 代码真源在独立项目仓 `metafo-proj-probe`（本目录只盘点，不放代码）。

---

## 一、L0 真源（零改动黑盒）

probe 的底层能力直接复用 **link-intel skill**（probe 的前身），通过 `importlib` 黑盒加载进 `app/l0`，不改一行：

| 脚本 | 能力 | 状态 |
|------|------|------|
| extract.py | 图文/文档快提取（article/doc/video/social 四类） | article/doc ✅ 已通 · **video/social：原 yt-dlp 自取已隔离，改走第三方 API**（红线#6）|
| deep.py | 深探调研（D1-D9 维度路由） | phase2（深探 LLM）|
| subtitle.py | 字幕提取（faster-whisper ASR） | ⚠️ **原 yt-dlp 下平台视频违反红线「不自己爬」→ 已隔离**；须先经第三方 API 拿到合规音频再 ASR |
| media.py | 媒体处理（ffmpeg 音轨 + demucs BGM 分离 + 关键帧） | ⚠️ 仅处理第三方 API/授权来源素材，不自取平台视频 |

> ⚠️ **红线对齐（D2「不自己爬」·2026-06-06 修）**：subtitle.py/media.py 的 yt-dlp 自取平台视频路径 = probe 自己爬，已停用隔离（见 [3-build/COMPLIANCE-HANDOFF.md](../3-build/COMPLIANCE-HANDOFF.md)）。video/social 数据一律走第三方 API（TikHub 等·供应商担责），ASR/媒体处理只作用于合规拿到的素材。
> 实测产出样本见 `link-intel-showcase`（article/doc 已通；video/social 待第三方 API 接入）。

## 二、L1 契约（对母体唯一接口）

| 端点 | 状态 |
|------|------|
| POST /api/v1/invoke（异步返 task_id） | ✅ |
| GET /api/v1/task/{id}（轮询 deliverable/cost） | ✅ |
| GET /api/v1/manifest（三维标签） | ✅ |
| POST /api/v1/selftest（准入自检） | ✅ **11/11 通过** |
| GET /api/v1/health | ✅ |

- 单元测试 **pytest 6/6 通过**。
- 契约 schema 见 [3-build/contract/](../3-build/contract/)（invoke/manifest/billing/profile）。
- ⚠️ schema 待补字段（见 records 对齐核查 A-2/A-3/A-4）：`geo_publishable` + `conclusion_block`、invoke `version`、manifest `subdomain`。

## 三、三层深度线（不泄露付费价值）

| 档 | 可见内容 | 状态 |
|----|---------|------|
| public（匿名） | 仅评级 + 标题 | ✅ guards 已切 |
| preview（免费登录） | 评级 + 结构骨架 | ✅ |
| paid（付费） | 完整 7 段报告 | ⏳ 待 M2 质量门 |

## 四、数据源（registry 驱动 · 热插拔）

| 适配器 | 域 | 状态 |
|--------|----|----|
| anysearch | D1 真相核查/事实核验 | ✅ 已接 |
| tikhub | D5/D6 竞品横评·账号画像(抖音/TikTok) | 🛠 代码就绪 · 待 key（R8+R1）|
| ledger.yaml | 数据源台账 | ✅ |

> 17 域 catalog 完整规划见 [3-build/probe-intelligence-engine-design-v1.md](../3-build/probe-intelligence-engine-design-v1.md) §4；多源调研见 [4-research/](../4-research/)。

## 五、部署与母体对接

| 项 | 状态 |
|----|------|
| probe.metafoclaw.com 子域 | ⏳ 待部署（DNS/nginx/Redis）|
| cookie domain=.metafoclaw.com SSO | 代码就绪（app/core/sso.py）|
| 母体侧 HttpToolClient + identity/verify | ❌ 待母体波次补 |
| registry-snippet（http transport 注册） | ✅ 已备 |

## 六、里程碑当前位置

```
 M1 公开档  ████████░░  代码就绪,待部署+母体 HttpToolClient
 M2 付费档  ██░░░░░░░░  待 TikHub key + C2 质量门 + 人工复核≥80%
 M3 大厅    ░░░░░░░░░░  待母体波次(不阻塞 M1/M2)
```

---

> 盘点口径：2026-06-08。后续每次能力变更同步更新本文件 + version-log.json。
> 绵阳零元电子商务有限公司 · 蜀ICP备2026010386号-1

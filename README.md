# 🛰️ probe · 链接情报

> metafoclaw 母体「**第一个远程镶嵌工具**」——验证「远程项目镶嵌」铁轨打通的样本。
> 母体是铁轨、probe 是列车：**内部 L0 零改动，对外只实现 L1 契约**（[02-api.md](../metafoclaw-git/docs/standards/02-api.md)）。

## 母体坐标

| 项 | 值 |
|----|-----|
| 子域名 | `probe.metafoclaw.com` |
| 三维标签 | 自媒体 × 链接分析 × 免费(公开提取)+付费(深探) |
| 传输 | HTTPS · http transport（≠ monorepo inprocess） |
| 挂载批次 | 🥇 首挂（边界干净、无数据成本、验证最快） |

## L1 契约端点（02-api.md）

| 端点 | 作用 |
|------|------|
| `POST /api/v1/invoke` | 一句话/链接 → 异步返 `{task_id, status_url}`（长任务铁律） |
| `GET /api/v1/task/{id}` | 轮询 `status/progress/deliverable/meta/cost` |
| `GET /api/v1/manifest` | 三维标签（喂 L4 推荐/矩阵） |
| `POST /api/v1/selftest` | 准入自检（契约合规 11 项） |
| `GET /api/v1/health` | 健康 |

## 镶嵌 6 步落点

| 步 | 实现 |
|----|------|
| 1 三端点 | `app/routers/{invoke,manifest,selftest,task}.py` |
| 2 SSO | `app/core/sso.py`（校验母体 short-lived user_token；匿名→免费档） |
| 3 计费 | `app/core/billing.py`（公开=免费档、深探=premium_data；失败不扣） |
| 4 guards | `app/core/guards.py`（aigc_flag + 禁直吐 + **公开/免费/付费三层深度线**） |
| 5 注册 | `deploy/registry-snippet.yaml`（交母体注册 http transport） |
| 6 部署 | `deploy/`（probe.metafoclaw.com · cookie domain=.metafoclaw.com） |

## 三层深度线（不泄露付费价值 · 02-api §7.4）

```
匿名(public)   → 仅评级 + 标题，锁结构/竞品/二创/合规
免费登录(preview) → 评级 + 结构骨架，锁竞品/二创/合规
付费(paid)      → 完整 7 段报告
```

## L0 自有链路（零改动）

`app/l0/scripts/` = 原 link-intel skill 4 脚本（extract/deep/subtitle/media），importlib 黑盒加载，**不改一行**。公开提取 article/doc 已通；video/social/深探 LLM = phase2（视频走隔离 worker）。

## 跑

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
uvicorn app.main:app --port 8080
curl -s localhost:8080/api/v1/selftest   # ok:true 11/11
pytest -q
```

## 定位

- 不进母体仓（monorepo / 文档仓）；独立项目（独立仓 `metafo-proj-probe`）。
- 部署/注册见 [deploy/DEPLOY.md](deploy/DEPLOY.md)。
- 母体侧待补：HttpToolClient + identity/verify（见 registry-snippet 注记）。

# probe 部署 · probe.metafoclaw.com（probe-a 实况版 v2.0）

> 2026-06-13 重写：反映 **probe-a 当前真实部署态**（已在役·非臆造步骤）。
> 部署目标 = **probe-a 独立节点**（T5v2 第三公网入口·独立 EIP 182.254.147.35·SSO 保护）。
> 拓扑：`~/.claude/rules/L1-infra/server-roles.md` 机6 + [[project_unified_entry_topology_20260610]]。
> SSH：`ssh probe-a-ts`（公网 22 已封·走 Tailscale 100.64.0.5）。

---

## 一、当前部署态（已在役 · 核实 2026-06-13）

| 维度 | 实况 |
|------|------|
| **代码路径** | `/opt/probe-app/`（注意：非旧文档的 `/opt/probe`）|
| **venv** | `/opt/probe-app/venv/` · Python 3.12.3 |
| **systemd** | `probe.service` · User=ubuntu · `uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2` · Restart=always |
| **env** | `EnvironmentFile=/opt/probe-app/env/.env`（真值·非入仓·已配 LITELLM/DEEPSEEK/BAILIAN/GITHUB 等 key）|
| **nginx** | `/etc/nginx/sites-enabled/probe.metafoclaw.com` · 80→443 跳转 · letsencrypt 证书（**到期 2026-09-01**）|
| **路由** | `location /` 和 `location /api` 均挂 `auth_request /__sso_verify` → `proxy_pass http://127.0.0.1:8001` |
| **API 前缀** | 真实路由带 `/api/v1`（invoke/manifest/selftest/task/health）|
| **selftest** | `POST /api/v1/selftest` → 11/11 ✅ |

---

## 二、日常更新流程（改代码 → 上线）

```bash
# 1 本地改完 → 同步单文件/目录到 probe-a（先 diff 确认仅预期差异）
scp app/<改动文件> probe-a-ts:/tmp/<file>-local.py
ssh probe-a-ts "diff /opt/probe-app/app/<路径> /tmp/<file>-local.py"   # 确认变更面

# 2 备份 + 替换 + AST 校验（R0.6：生产变更必 .bak）
ssh probe-a-ts "cd /opt/probe-app && cp app/<路径> app/<路径>.bak.\$(date +%Y%m%d-%H%M%S) \
  && cp /tmp/<file>-local.py app/<路径> \
  && venv/bin/python -c 'import ast; ast.parse(open(\"app/<路径>\").read()); print(\"AST OK\")'"

# 3 重启（需 sudo · polkit 限制普通 systemctl）
ssh probe-a-ts "sudo systemctl restart probe.service && sleep 3 && sudo systemctl is-active probe.service"

# 4 验收（selftest 11/11 不退化）
ssh probe-a-ts "curl -s -X POST http://127.0.0.1:8001/api/v1/selftest | \
  /opt/probe-app/venv/bin/python -c 'import sys,json; d=json.load(sys.stdin)[\"data\"]; print(d[\"passed\"],\"/\",d[\"total\"])'"

# 回滚：cp app/<路径>.bak.<时间戳> app/<路径> && sudo systemctl restart probe.service
```

> 装新依赖：`ssh probe-a-ts "/opt/probe-app/venv/bin/pip install <pkg>"` 后必重启。

---

## 三、🔴 M1 公开档上线前必决：匿名层 SSO 豁免

**当前 `location /api` 整体挂 `auth_request /__sso_verify`** → 匿名请求 `/api/v1/health` 返 302 跳登录。

但 M1 设计（三层深度线）要求**匿名用户能看 public 结论**（评级 + headline·premium=0）。二者冲突，上线前须裁定其一：

- **方案 A（推荐·最小改动）**：nginx 对 public 端点显式豁免 SSO——`location = /api/v1/health`、`location = /api/v1/manifest`、以及 invoke 的 anon 档路径 `auth_request off`；其余（preview/paid）仍走 SSO。守 nginx-01「JWT 公开路径必须显式注册」。
- **方案 B**：M1 先做"登录可见"，匿名公开层延后——牺牲拉新漏斗，但零 nginx 改动。

> 决策记录待补；改 nginx 属高 blast（公网主路由）→ 走 R-CL 必须级 + 元东方授权。

---

## 四、DNS / 证书

- A 记录：`probe.metafoclaw.com` → probe-a EIP `182.254.147.35`（已生效·公网 health 可达）
- 证书：letsencrypt 单域 · **2026-09-01 到期** · certbot 自动续期需确认 cron 在位
- ACME 续期路径：nginx 80 段 `location /.well-known/acme-challenge` 已配（root /opt/probe/site）

---

## 五、注册母体（M3 前置·不阻塞 M1）

部署 + selftest 过线后，把 [registry-snippet.yaml](../../deploy/registry-snippet.yaml) 交母体团队注册（http transport）。母体侧需补 `HttpToolClient` + `identity/verify` + registry 三维标签（s1-impl-plan §四·M3 前置）。

## 六、SSO cookie

跨子域登录互通：登录态 cookie `domain=.metafoclaw.com`（母体 SSO 下发），probe 只校验母体短时 user_token，不种登录 cookie。

# probe 部署 · probe.metafoclaw.com

> 部署在 tencent-sh（公网入口）。远程独立服务，经 L1 http transport 挂母体。

## 步骤

```bash
# 1 代码上云（R10：代码/构建上云，不在 Mac 跑生产）
rsync -az ~/Downloads/metafoclaw/probe/ tencent-sh:/opt/probe/ --exclude .venv --exclude __pycache__

# 2 装依赖
ssh tencent-sh 'cd /opt/probe && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'

# 3 配置（真值入 vault，不入仓）
ssh tencent-sh 'cp /opt/probe/.env.example /opt/probe/.env && vi /opt/probe/.env'  # 填 PROBE_API_KEY

# 4 systemd
ssh tencent-sh 'cp /opt/probe/deploy/probe.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable --now probe'
ssh tencent-sh 'curl -s localhost:8080/api/v1/health'   # {"code":0,...}

# 5 nginx（四禁对齐：/api 前缀、无 trailing slash、JWT 豁免显式）
ssh tencent-sh 'cp /opt/probe/deploy/nginx-probe.conf /etc/nginx/conf.d/ && nginx -t && systemctl reload nginx'

# 6 DNS：probe.metafoclaw.com → tencent-sh 公网 IP（A 记录）
#    证书：通配 *.metafoclaw.com 或单域 certbot

# 7 验收
curl -s https://probe.metafoclaw.com/api/v1/selftest | python3 -m json.tool   # ok:true 11/11
curl -s https://probe.metafoclaw.com/api/v1/manifest
```

## DNS 注意

`dig probe.metafoclaw.com` 当前返回 `198.18.1.188`（benchmark 保留段，疑本地 DNS 占位/拦截）——上线前确认公网 A 记录指向 tencent-sh 真实公网 IP。

## 注册母体

部署 + selftest 过线后，把 [registry-snippet.yaml](registry-snippet.yaml) 交母体团队注册（http transport）。母体侧需补 HttpToolClient + identity/verify（见 snippet 注记）。

## SSO cookie

跨子域登录互通：登录态 cookie `domain=.metafoclaw.com`（母体 SSO 下发），probe 只校验母体短时 user_token，不种登录 cookie。

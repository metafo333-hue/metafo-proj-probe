"""远程提取客户端 · probe-a 调 ufo 提取服务（D-Use 拓扑 2026-06-14）。

背景（server-roles 机6）：probe-a 禁 ML 密集任务；ML 中枢是 ufo(机3 GPU)。
重 ML 提取器（prefer_remote=True：audio/image/docling）在 probe-a 不本地跑，
经 Tailscale 调 ufo 上的 probe-extract 服务。

配置：env `PROBE_EXTRACT_SERVICE_URL`（如 http://100.64.0.8:8920）。
未配 → call_remote 返回 None → 上层回落本地（默认行为不变·可回滚）。
ufo 服务侧 = deploy/extract_service.py（复用同一套 app.extractors，在 GPU 机本地跑）。
"""
from __future__ import annotations

import os
from typing import Any

# ufo 提取服务地址（Tailscale 内网·未配则禁用远程·回落本地）
_SERVICE_URL = os.getenv("PROBE_EXTRACT_SERVICE_URL", "").rstrip("/")
_TIMEOUT = int(os.getenv("PROBE_EXTRACT_REMOTE_TIMEOUT", "120"))  # ASR 较慢·宽超时


def remote_enabled() -> bool:
    return bool(_SERVICE_URL)


def call_remote(kind: str, url: str) -> dict[str, Any] | None:
    """调 ufo 提取服务；未配服务地址或调用失败 → None（上层回落本地）。"""
    if not _SERVICE_URL:
        return None
    try:
        import httpx
    except ImportError:
        return None
    try:
        resp = httpx.post(
            f"{_SERVICE_URL}/extract",
            json={"kind": kind, "url": url},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        # 服务侧统一返回 {ok, result} 或 {ok:False, reason}
        if isinstance(data, dict) and data.get("ok"):
            return data.get("result")
        return {"failed": True,
                "reason": f"远程提取失败：{(data or {}).get('reason', '未知')}"}
    except Exception as e:  # noqa: BLE001 — 远程失败不抛,回 failed dict 由上层决定回落
        return {"failed": True, "reason": f"远程提取服务不可达：{e}"}

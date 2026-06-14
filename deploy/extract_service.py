"""probe-extract 服务 · 跑在 ufo(机3 GPU·ML 中枢) · D-Use 拓扑 2026-06-14。

为何独立服务：server-roles 机6(probe-a) 禁 ML 密集任务；重 ML 提取（audio ASR /
image OCR / docling）须在 ufo(GPU)跑。probe-a 经 Tailscale 调本服务（见 extractors/remote.py）。

复用同一套 app.extractors（无代码分叉）——本服务只是"在 GPU 机本地执行提取器"的 HTTP 壳。

部署（ufo · 须过 R30 新服务上线门）：
  - 装重依赖：pip install faster-whisper rapidocr-onnxruntime docling
  - 仅绑 Tailscale：uvicorn deploy.extract_service:app --host 100.64.0.8 --port 8920
    （server-roles：ufo 无公网·禁 0.0.0.0 对外·只 Tailscale 内网可达）
  - probe-a 配 env：PROBE_EXTRACT_SERVICE_URL=http://100.64.0.8:8920
  - systemd 单元名 probe-extract.service · 入 asset-registry · 元衡值守注册
合规：本服务仅处理 probe-a 传入的"直链公开音频/图片/文档 + 用户上传"，不做平台采集。
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from app.extractors import get_extractor, health_report

app = FastAPI(title="probe-extract", version="1.0.0")

# 仅允许本服务承载的重 ML kind（防被当通用代理滥用）
_ALLOWED = {"audio", "image", "doc"}


class ExtractReq(BaseModel):
    kind: str
    url: str


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "probe-extract", "extractors": health_report()}


@app.post("/extract")
def extract(req: ExtractReq) -> dict[str, Any]:
    if req.kind not in _ALLOWED:
        return {"ok": False, "reason": f"kind 不在本服务范围：{req.kind}"}
    ex = get_extractor(req.kind)
    if ex is None:
        return {"ok": False, "reason": f"无 {req.kind} 提取器"}
    try:
        result = ex.extract(req.url)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "reason": f"提取异常：{e}"}
    if result.get("failed"):
        return {"ok": False, "reason": result.get("reason", "提取失败")}
    return {"ok": True, "result": result}

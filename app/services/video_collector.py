"""短视频数据采集服务 · probe 调 combo-deep-probe(合规通路·授权源采集层)。

定位(隔离封装模式·合规通路):
  combo-deep-probe = 短视频"URL→7维数据"采集器(TikHub 授权源 + yt-dlp + 投喂补黑盒)。
  probe 通过本 service 调用它采集短视频公开数据 → 转 probe 友好格式 → 上层 LLM 深探出情报。
  **合规通路**:只走 TikHub 等授权源(供应商担责)·probe 原料进结论出·非暗线。
  (灰色/深度采集走独立暗线 aux-1·与本 service 无关·见 isolation-capsule-pattern.md)

依赖:probe venv `pip install -e <combo-deep-probe 路径>`;本地开发回退同级目录 sys.path。
"""
from __future__ import annotations

import os
import pathlib
import sys
from typing import Any


def _ensure_importable() -> None:
    """让 combo_deep_probe 可 import:已装则用,否则回退同级目录(本地开发)。"""
    try:
        import combo_deep_probe  # noqa: F401
        return
    except ImportError:
        # probe/ 与 combo-deep-probe/ 同级(.../metafoclaw/)
        cand = pathlib.Path(__file__).resolve().parents[3] / "combo-deep-probe"
        if cand.is_dir():
            sys.path.insert(0, str(cand))


def collect_video(url: str, tikhub_key: str | None = None) -> dict[str, Any]:
    """采集单条短视频数据 → probe 友好格式(字段级带 source/precision·便于审计)。"""
    _ensure_importable()
    from combo_deep_probe import build_default
    cdp = build_default(tikhub_key=tikhub_key or os.getenv("TIKHUB_API_KEY"))
    packet = cdp.collect(url)
    d = packet.to_dict()
    return {
        "ok": True,
        "platform": packet.platform,
        "video_id": packet.video_id,
        "url": packet.url,
        "dimensions": d["dimensions"],            # 7 维·字段级 {value,source,precision,ts}
        "coverage": packet.coverage_score,         # 数据完整度(实测占比)
        "sources": packet.sources_used,
        "missing_blackbox": packet.missing_blackbox,  # 缺失黑盒维度(完播/流量来源/转化)
        "collected_at": packet.collected_at,
    }


def collect_account(sec_user_id: str, count: int = 20, tikhub_key: str | None = None) -> dict[str, Any]:
    """账户分析(画像+作品矩阵+诊断)→ probe 友好格式。"""
    _ensure_importable()
    from combo_deep_probe import build_account_probe
    ap = build_account_probe(tikhub_key=tikhub_key or os.getenv("TIKHUB_API_KEY"))
    report = ap.analyze(sec_user_id=sec_user_id, count=count)
    return {"ok": True, **report.to_dict()}

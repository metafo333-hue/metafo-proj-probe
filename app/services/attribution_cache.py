"""视听归因缓存 · 本地 JSON 积累 · 账号跨会话样本 → 批量归因飞轮。

缓存位置：~/.probe_cache/av/{sec_uid_safe}/{aweme_id_safe}.json
每条存储：{"aweme_id": str, "like": int, "six_layer": {...}, "saved_at": str}

飞轮逻辑：
  每次视听分析（Qwen3-Omni）后存一条 → 同账号积累 ≥5 条后自动出归因段。
  zero extra API cost: 归因建立在已付费的 Omni 分析结果上，不重复调模型。

设计依据：probe-audiovisual-attribution-methodology-v1.0.md §三 + attribution.py _CONF_NONE=5
"""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone
from typing import Any

_CACHE_ROOT = pathlib.Path.home() / ".probe_cache" / "av"

# 与 attribution.py _CONF_NONE 保持一致（样本不足时不做归因）
_MIN_FOR_ATTRIBUTION = 5


def _account_dir(sec_uid: str) -> pathlib.Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (sec_uid or ""))
    return _CACHE_ROOT / safe[:64]


def save_av(sec_uid: str, aweme_id: str, like: int, six_layer: dict) -> None:
    """存单条视听分析结果到本地缓存（幂等：覆盖同 aweme_id 旧记录）。

    sec_uid:   抖音账号 sec_user_id（作为缓存分区键）
    aweme_id:  视频 ID（作为缓存文件名）
    like:      视频点赞数（归因分层用）
    six_layer: analyze_douyin_video 返回的六层结构化结果
    """
    if not sec_uid or not aweme_id or not isinstance(six_layer, dict):
        return
    d = _account_dir(sec_uid)
    d.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() else "_" for c in aweme_id)[:48]
    data = {
        "aweme_id": aweme_id,
        "like": int(like or 0),
        "six_layer": six_layer,
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    (d / f"{safe_id}.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def load_account_av(sec_uid: str) -> list[dict[str, Any]]:
    """加载账号所有已缓存视听记录 → [{like, six_layer}, ...] 供 attribute() 使用。

    六层为空或文件损坏的条目自动跳过。
    """
    d = _account_dir(sec_uid)
    if not d.exists():
        return []
    works: list[dict] = []
    for f in sorted(d.glob("*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            if raw.get("six_layer"):
                works.append({"like": raw.get("like", 0), "six_layer": raw["six_layer"]})
        except Exception:  # noqa: BLE001
            continue
    return works


def cache_stats(sec_uid: str) -> dict:
    """返回账号归因缓存统计：{count, min_needed, ready, missing}。"""
    n = len(load_account_av(sec_uid))
    return {
        "count": n,
        "min_needed": _MIN_FOR_ATTRIBUTION,
        "ready": n >= _MIN_FOR_ATTRIBUTION,
        "missing": max(0, _MIN_FOR_ATTRIBUTION - n),
    }


def render_attribution_progress(sec_uid: str) -> str:
    """当样本不足时，返回友好提示 markdown 段（告知用户还需分析几条）。"""
    stats = cache_stats(sec_uid)
    n = stats["count"]
    missing = stats["missing"]
    return (
        "### 你的爆款视听公式\n\n"
        f"> 📦 **归因样本积累中**：已分析 **{n}** 条视频，"
        f"还需再分析 **{missing}** 条同账号视频，将自动生成「爆款视听公式」。\n"
        ">\n"
        "> 这项功能用的是**你自己账号的数据**做对照（爆款 vs 平款），"
        "比抄别人的套路靠谱——利用已付费的视听分析结果，**零额外成本**。\n"
    )

"""InsightPacket · 灰度链 B（aux-1 个人侧 → probe 商业链）唯一跨边界契约。

指针非桥铁律（中性指针记忆 + isolation-capsule + v2.2 §8.4）：
  - aux-1 个人侧采集+净化（视频号等灰度源·具体工具/方法不在 probe 记录·属个人侧安排）
  - 跨边界**只过 InsightPacket**（纯文字洞察 + 脱敏指标），**禁携带任何原始媒体引用**
  - schema 层就拒绝 video_url/account_id/raw_text/file_path → 物理保证"只出洞察不出原片"
  - probe 接收后进**线索池（lead·Admiralty 默认 D）**·须依据池佐证才升级·不直接出口

法律兜底：分析≠传播·probe 只生产洞察（原创表达）·不复制/传播原片·两侧无实质连接。
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any

# 跨边界禁止携带的字段（schema 层拒绝·物理防"原片/可回溯标识"泄入商业链）
_FORBIDDEN_FIELDS = frozenset({
    "video_url", "url", "account_id", "sec_uid", "uid", "raw_text",
    "file_path", "media_path", "original", "raw_video", "cover_url",
})


@dataclass
class InsightPacket:
    """灰度链 B 唯一出口格式（aux-1 净化产出 → probe 接收）。"""
    insight_id: str                              # 随机·不追溯原视频
    platform: str = ""                           # wechat_channels / kuaishou / ...
    topic_tags: list = field(default_factory=list)   # 话题分类
    sentiment: str = "neutral"                   # pos / neg / neutral
    key_claims: list = field(default_factory=list)   # 核心声明（文字·非引用原文）
    metrics: dict = field(default_factory=dict)  # 脱敏量化（估算·非精确·无精确ID）
    duration_sec: int = 0                        # 可估算·非精确
    quality_tier: str = "C"                      # aux-1 内部自评 A/B/C
    collected_date: str = ""                     # ISO 日期·精度=天（防回溯到秒）
    # 明确无：video_url / account_id / sec_uid / raw_text / file_path

    def to_dict(self) -> dict:
        return asdict(self)


def reject_forbidden(payload: dict) -> list[str]:
    """检出 payload 里的禁止字段（含嵌套一层）。返回命中的禁字段名列表（空=干净）。"""
    hits = []
    for k, v in (payload or {}).items():
        if k.lower() in _FORBIDDEN_FIELDS:
            hits.append(k)
        if isinstance(v, dict):
            hits += [f"{k}.{x}" for x in reject_forbidden(v)]
    return hits


def from_ingest(payload: dict) -> tuple[InsightPacket | None, str]:
    """接收校验：aux-1 推来的 dict → InsightPacket。
    返回 (packet, "") 成功 / (None, 拒绝原因)。禁字段命中即拒（物理拦原片泄入）。"""
    if not isinstance(payload, dict):
        return None, "payload 非 dict"
    hits = reject_forbidden(payload)
    if hits:
        return None, f"拒收：携带禁止的原始媒体字段 {hits}（指针非桥·只接洞察不接原片）"
    if not payload.get("insight_id"):
        return None, "缺 insight_id"
    allowed = {f for f in InsightPacket.__dataclass_fields__}
    clean = {k: v for k, v in payload.items() if k in allowed}
    return InsightPacket(**clean), ""

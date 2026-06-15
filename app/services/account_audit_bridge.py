"""② AccountReport → ③ 八闸 claims+sources 转换器(regime B 真断点·纯函数)。

为什么需要它(优化方案 P1·真断点):
  combo 的 AccountReport 是「指标维度」,八闸 run_audit 吃「文本 claims + sources」,
  契约不同 → 代码里缺这个纯转换器。本函数把账号诊断原子化为 4-7 条原子 claim + 1 个源,
  **输出契约 == pipeline._build_audit_input 的返回**,run_audit 原样可吃。零 LLM/零网络/可单测。

provenance(对齐 lineage.py 哲学·诚实不高估):
  account 单一商业源(TikHub)→ reliability_hint='C'(单源未交叉佐证·Low),gate1 据此降置信。
  ——这正是"敢担保"在干活:单源账号裁决本就该 C/Low,不美化。
"""
from __future__ import annotations

import datetime
import json
from typing import Any


def account_to_claims_sources(
    account: dict[str, Any],
    account_url: str,
    source_id: str = "tikhub",
) -> tuple[list[str], list[dict]]:
    """AccountReport.to_dict() → (claims, sources)·契约同 pipeline._build_audit_input。"""
    profile = account.get("profile") or {}
    diag = account.get("diagnosis") or {}
    nickname = profile.get("nickname") or profile.get("unique_id") or "该账号"
    followers = profile.get("follower_count")
    n = account.get("works_analyzed") or len(account.get("works_sample") or [])

    claims: list[str] = []

    # ① 体量(profile·measured)
    if followers is not None:
        seg = f"据{source_id}授权源(单源·measured),{nickname}({followers}粉"
        if profile.get("total_favorited") is not None:
            seg += f"·获赞{profile['total_favorited']}"
        if profile.get("aweme_count") is not None:
            seg += f"·作品{profile['aweme_count']}"
        claims.append(seg + ")")

    # ② 互动/爆款(diagnosis·计算衍生)
    like = diag.get("like") or {}
    if like.get("avg") is not None:
        seg = f"近{n}条均赞{like['avg']}"
        if like.get("max") is not None:
            seg += f"、最高{like['max']}"
        if diag.get("burst_ratio") is not None:
            seg += f"、爆款比{diag['burst_ratio']}x"
        claims.append(seg)

    # ③ 垂直度
    if diag.get("vertical_score") is not None:
        top = diag.get("top_hashtags") or []
        tag = f"·头部标签#{top[0][0]}" if top and top[0] else ""
        claims.append(f"内容垂直度{diag['vertical_score']}{tag}")

    # ④ 粉丝级互动率
    if diag.get("like_per_follower") is not None:
        claims.append(f"粉丝级互动率{diag['like_per_follower']}(均赞÷粉丝数)")

    # ⑤ 更新节奏
    upd = diag.get("update") or {}
    if upd.get("avg_interval_hours") is not None:
        claims.append(f"更新间隔均{upd['avg_interval_hours']}小时(活跃度信号)")

    if not claims:
        claims = [f"{nickname} 账号数据不足以出诊断"]

    sources: list[dict] = [{
        "url": account_url,
        "title": f"{nickname} · {source_id}授权源账号画像",
        # 指标序列化进 text → 让 gate2 忠实度对真内容打分(优化方案 §4)
        "text": json.dumps({"profile": profile, "diagnosis": diag},
                           ensure_ascii=False)[:1000],
        "source_type": "primary",
        "reliability_hint": "C",     # 单一商业源·诚实 Low(非高估)·gate1 据此降置信
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
    }]
    return claims, sources

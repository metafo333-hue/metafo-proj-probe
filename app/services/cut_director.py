"""处方导播 · cut_director.py · 处方双层(point4)。

承 v3.2 飞轮③「策划交付包 DeliveryPackage」→ 驱动制作引擎(MetaCut)。
同一份处方,两层表达:
  前端(给人看):战略→战术→执行 三级层级·具体但看得懂的人话动作
  后端(给机器):结构化 cut_commands·MetaCut 引擎可直接执行的命令(时段/时长/钩子/选题/CTA/配乐)

数据来源:content_dna(最优时段/时长/选题/配乐)+ strategic_call(方向)+ track(赛道感知)+
audience(采购意向)。全部数据驱动·可溯源(每条命令带 rationale 指针)。
⚠️ 视觉/分镜细节归 MetaCut/视听层·本模块只给"数据层能定的参数"(何时发/多长/什么题/挂不挂车)。
"""
from __future__ import annotations

import re
from typing import Any

_HASHTAG_RE = re.compile(r"#([^#\s]{1,20})")
# 时段名 → MetaCut 可消费的时间窗
_SLOT_WINDOW = {
    "清晨5-9": "05:00-09:00", "上午9-12": "09:00-12:00", "午间12-14": "12:00-14:00",
    "下午14-18": "14:00-18:00", "晚间18-22": "18:00-22:00", "深夜22-5": "22:00-05:00",
    "晚间 18-22": "18:00-22:00", "下午 14-18": "14:00-18:00",
}


def _slot_to_window(slot: str | None) -> str | None:
    if not slot:
        return None
    for k, v in _SLOT_WINDOW.items():
        if k in slot:
            return v
    m = re.search(r"(\d{1,2})\s*-\s*(\d{1,2})", slot)
    return f"{int(m.group(1)):02d}:00-{int(m.group(2)):02d}:00" if m else None


def _dur_to_range(bucket: str | None) -> list[int] | None:
    if not bucket:
        return None
    m = re.search(r"(\d+)\s*-\s*(\d+)", bucket)
    if m:
        return [int(m.group(1)), int(m.group(2))]
    m2 = re.search(r"(\d+)", bucket)
    return [max(0, int(m2.group(1)) - 5), int(m2.group(1)) + 5] if m2 else None


def build_prescription(account: dict, deep: dict) -> dict[str, Any]:
    """处方双层:前端三级(战略/战术/执行人话)+ 后端 cut_commands(MetaCut可执行)。"""
    deep = deep or {}
    sc = deep.get("strategic_call") or {}
    track = (deep.get("industry") or {}).get("track_tier") or {}
    dna = account.get("content_dna") or {}
    rx = dna.get("next_video_rx") or {}
    bt = dna.get("best_time") or {}
    bd = dna.get("best_duration") or {}
    topics = dna.get("topics") or {}
    music = (account.get("extra_signals") or {}).get("hot_music") or []
    au = deep.get("audience") or {}
    intent = au.get("intent_signal") or []
    is_b2b = track.get("is_b2b_leads")

    # ── 数据层能定的执行参数 ──
    window = _slot_to_window(bt.get("best"))
    dur = _dur_to_range(bd.get("best"))
    topic_tags = (topics.get("top_hashtags") or [])[:3]
    cta = ("主页/置顶引导加微信·把采购咨询导私域成交" if is_b2b
           else "评论区引导关注·下条预告")
    bgm = (music[0].get("title") if music else None)

    # ── 前端三级层级(人话·具体但看得懂)──
    strategy = {"level": "战略", "text": sc.get("call", "—"), "why": sc.get("why", "")}
    tactic = {"level": "战术·本周", "steps": (rx.get("steps") or [])[:3]}
    execute_human = {"level": "执行·下条",
                     "text": (f"{bt.get('best','')}发·{bd.get('best','')}·"
                              f"选题「{('、'.join(topic_tags))}」·{cta}")}

    # ── 后端 cut_commands(MetaCut 引擎可直接执行)──
    cut_commands = {
        "engine": "metacut", "schema_ver": "1.0",
        "account": account.get("nickname"),
        "strategy": sc.get("call"),
        "priority": "P0" if sc.get("color") == "red" else "P1",
        "next_clip": {
            "post_window": window,                 # 发布时间窗(实测最优时段)
            "duration_s": dur,                     # 时长区间(实测高互动)
            "topic_tags": topic_tags,              # 选题话题(爆款共性)
            "hook": _infer_hook(topics, is_b2b),   # 钩子类型(数据层推断)
            "cta": cta,                            # 转化引导
            "bgm_ref": bgm,                        # 配乐(热门·可选)
            "anchor": False if is_b2b and (account.get("commerce_density") or 0) == 0 else None,
        },
        "avoid": _constraints(deep),               # 禁忌(跨标签蹭热点等)
        "rationale": _rationale(sc, au, dna),      # 可溯源依据(为什么这么剪)
        "handoff": "v3.2 飞轮③ DeliveryPackage → MetaCut 制作引擎",
    }
    return {
        "front": {"strategy": strategy, "tactic": tactic, "execute": execute_human},
        "cut_commands": cut_commands,
    }


def _infer_hook(topics: dict, is_b2b: bool) -> str:
    """钩子类型(数据层推断·非视觉)。"""
    ex = (topics.get("exemplar") or {}).get("desc", "")
    if any(w in ex for w in ("价格", "多少", "钱", "报价")):
        return "price_reveal"      # 价格揭秘型
    if is_b2b:
        return "origin_proof"      # 源头实证型(B端工厂/产地)
    return "story_hook"            # 故事钩子型


def _constraints(deep: dict) -> list[str]:
    cons = ["跨标签蹭泛热点(乱算法标签·伤垂直度)"]
    env = deep.get("env") or {}
    if "不建议硬蹭" in (env.get("implication") or ""):
        cons.append("追时事/游戏热点(与赛道无关)")
    return cons


def _rationale(sc: dict, au: dict, dna: dict) -> list[str]:
    r = [f"战略依据:{sc.get('why','')[:60]}"]
    if au.get("intent_signal"):
        r.append(f"承接依据:评论现采购意向「{'、'.join(au['intent_signal'])}」·需导私域")
    bt = dna.get("best_time") or {}
    if bt.get("best"):
        r.append(f"时段依据:实测 {bt.get('verdict','')}")
    return r

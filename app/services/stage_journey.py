"""运营阶段引擎 · stage_journey.py · 已走过→当前→接下来(进阶规划)。

承用户启发:不只说"当前阶段",要说**已走过哪些阶段 / 现在哪个阶段 / 接下来哪些阶段**,
并把"该怎么做"锚定成**进阶动作**(从这站到下一站的关键动作)。这是把"诊断快照"升级成
"运营旅程 + 进阶规划"——v3.2 生命周期轴的运营落地。

每阶段带:入场粉丝量级 / 核心任务 / 出场标准(进阶条件·可数据判)。
赛道感知:B端(线索游戏·几千精准粉就能变现)vs 泛娱乐(流量游戏·门槛高)两套阶梯。
数据驱动定位:已完成=满足进阶标准的阶段·当前=匹配现状·接下来=下一阶段+解锁条件。
"""
from __future__ import annotations

from typing import Any

from app.services import benchmarks as BM

# B端运营阶段(承 CAT §五·B端线索游戏)·每阶段:(name, lo, hi, task, advance)
_STAGES_B2B = [
    ("冷启·打标签", 0, 1000, "验证内容模型·让算法认你是什么号", "垂直度稳 + 过千粉"),
    ("起号·建信任", 1000, 10000, "攒专业人设·建信任·把咨询沉淀", "过万粉 + 私域承接接通"),
    ("初变现", 10000, 50000, "引流私域成交·低价课/样品/线索转化", "稳定线索转化 + 复购"),
    ("成长", 50000, 500000, "训练营/高价课/1对1/招商", "多变现路径打透"),
    ("成熟", 500000, 10 ** 12, "课程矩阵·IP商业化·企培", "—"),
]
# 泛娱乐运营阶段(承 PB §A2)
_STAGES_GEN = [
    ("冷启·打标签", 0, 5000, "验证内容·让算法打标签·禁碰变现", "过5千粉 + 内容模型稳"),
    ("初变现", 5000, 50000, "找最适配变现路径·软植入测试", "稳定商单/带货"),
    ("成长变现", 50000, 500000, "多路径打透 + 私域沉淀", "多元变现稳定"),
    ("成熟", 500000, 5000000, "多元变现叠加 + 矩阵化", "IP/品牌化"),
    ("头部", 5000000, 10 ** 12, "IP商业化·品牌化", "—"),
]


def build_journey(account: dict, deep: dict | None = None) -> dict[str, Any]:
    """运营阶段旅程:已走过/当前/接下来 + 进阶条件 + 进阶动作锚点。"""
    deep = deep or {}
    track = (deep.get("industry") or {}).get("track_tier") or \
        BM.classify_track(account.get("industry_tag") or account.get("nickname"))
    is_b2b = track.get("is_b2b_leads")
    stages = _STAGES_B2B if is_b2b else _STAGES_GEN
    f = account.get("follower") or 0

    # 当前阶段索引(按粉丝量级)
    cur_idx = 0
    for i, (_, lo, hi, _, _) in enumerate(stages):
        if lo <= f < hi:
            cur_idx = i
            break
    else:
        cur_idx = len(stages) - 1

    # 进阶缺口:下一阶段解锁条件 + 数据判断还差什么
    nxt_idx = min(cur_idx + 1, len(stages) - 1)
    advance = stages[cur_idx][4]
    gaps = _advance_gaps(account, stages[cur_idx], deep, is_b2b)

    def _node(i):
        name, lo, hi, task, adv = stages[i]
        state = "done" if i < cur_idx else ("current" if i == cur_idx else "future")
        return {"idx": i, "name": name, "fans_range": f"{_fmt(lo)}-{_fmt(hi)}",
                "task": task, "advance": adv, "state": state}

    nodes = [_node(i) for i in range(len(stages))]
    return {
        "is_b2b": is_b2b,
        "nodes": nodes,
        "criteria": _criteria(account, is_b2b),   # 评定依据(怎么判这个阶段·指令1)
        "current": stages[cur_idx][0],
        "current_idx": cur_idx,
        "current_task": stages[cur_idx][2],
        "next": stages[nxt_idx][0] if nxt_idx != cur_idx else None,
        "advance_criteria": advance,
        "advance_gaps": gaps,                  # 进阶还差什么(数据判)
        "done": [stages[i][0] for i in range(cur_idx)],
        "future": [stages[i][0] for i in range(cur_idx + 1, len(stages))],
        "verdict": _verdict(stages, cur_idx, nxt_idx, gaps),
        "source": "CAT §五(B端) / PB §A2(泛娱乐)·赛道感知阶段模型",
    }


def _criteria(account: dict, is_b2b: bool) -> dict:
    """阶段评定依据:用哪些维度判这个阶段(给用户看依据·指令1)。"""
    f = account.get("follower") or 0
    cd = account.get("commerce_density")
    vs = account.get("vertical_score")
    dims = [
        {"dim": "粉丝量级", "value": _fmt(f),
         "why": "决定能用哪条变现路径·" + ("B端几千精准粉就能引流私域" if is_b2b
                                          else "泛娱乐需更大量级才变现")},
        {"dim": "承接基建", "value": ("有" if (cd or 0) > 0 else "无(商业密度0)"),
         "why": "私域/橱窗承接是否接通·B端起号→初变现的硬门槛"},
        {"dim": "垂直度", "value": (str(vs) if vs is not None else "—"),
         "why": "算法是否给你打稳标签·冷启→起号的关键"},
    ]
    return {"dims": dims,
            "note": "阶段=按粉丝量级定位 + 承接/垂直度判进阶就绪度·赛道感知"
                    "(B端线索游戏 vs 泛娱乐流量游戏门槛不同)",
            "source": "CAT §五(B端阶段) · PB §A2(泛娱乐阶段) · 单粉价值 CM §二层A"}


def _advance_gaps(account: dict, cur_stage, deep: dict, is_b2b: bool) -> list[str]:
    """进阶到下一阶段还差什么(数据可判的列出来)。"""
    name, lo, hi, task, adv = cur_stage
    f = account.get("follower") or 0
    gaps = []
    # 粉丝量级缺口
    if f < hi:
        gaps.append(f"粉丝量级:{_fmt(f)}→{_fmt(hi)}(还差 {_fmt(hi - f)})")
    # 承接缺口(B端起号期关键:私域承接)
    if is_b2b and "承接" in adv and (account.get("commerce_density") or 0) == 0:
        gaps.append("私域承接:当前商业密度0·零承接·需补私域钩子(这是进阶硬条件)")
    # 内容模型/垂直度(冷启期)
    if "垂直" in adv or "内容模型" in adv:
        vs = account.get("vertical_score")
        if vs is not None and vs < 0.6:
            gaps.append(f"垂直度:{vs}·需收敛到 0.6+(算法打标签)")
    return gaps


def _verdict(stages, cur_idx, nxt_idx, gaps) -> str:
    cur = stages[cur_idx][0]
    if nxt_idx == cur_idx:
        return f"已到{cur}(顶阶)"
    nxt = stages[nxt_idx][0]
    if gaps:
        return f"你在【{cur}】·距【{nxt}】还差:{gaps[0].split('·')[0]}"
    return f"你在【{cur}】·进阶条件已近满足·可冲【{nxt}】"


def _fmt(n: int) -> str:
    if n >= 10 ** 11:
        return "∞"
    return f"{n // 10000}万" if n >= 10000 else str(n)

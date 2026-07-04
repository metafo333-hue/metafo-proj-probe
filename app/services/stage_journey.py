"""运营阶段引擎 · stage_journey.py · 阶段链条 + 阶段×维度矩阵(指令5)。

承用户:运营阶段要深度+链条——不只说"当前阶段"和一个任务,要做到:
  ① 每阶段从多维度补(内容/承接/私域/数据/人设·不只一件事)
  ② 真链条:每阶段产出 → 喂给下阶段输入(建信任→产线索→促成交→促复购→矩阵复利)
  ③ 完整架构:阶段×维度矩阵(每格=该阶段该维度做什么)
  ④ 每阶段一句专业战略方向
赛道感知:B端(线索游戏)vs 泛娱乐(流量游戏)两套阶梯。出处=自有方法论 CAT/PB/CM。
"""
from __future__ import annotations

from typing import Any

from app.services import benchmarks as BM

# 五大工作维度(阶段×维度矩阵的列)
WORK_DIMS = [("内容", "🎬"), ("承接", "🔗"), ("私域", "💬"), ("数据", "📊"), ("人设", "🎭")]
COMPLIANCE = "合规红线(贯穿全程):不碰违禁词/虚假宣传·B端资质前置·真实人设不夸大"

# B端运营阶段(承 CAT §五·B端线索游戏)·(name, lo, hi, task, advance)
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

# ── 阶段×维度 战术库(链条式·每阶段:方向+5维动作+产出喂给下阶段)──────────────────
# dims 顺序对齐 WORK_DIMS:内容/承接/私域/数据/人设
_PLAY_B2B = {
    "冷启·打标签": {
        "direction": "先让算法认识你是谁——把垂直标签焊死,这一站不谈钱",
        "dims": {"内容": "单一选题垂直输出·验证内容模型(别杂)", "承接": "暂不变现·主页签名写清身份占位",
                 "私域": "先不引流·积累内容资产", "数据": "盯垂直度/完播·验证算法有没有给你打标",
                 "人设": "立住『我是做什么的』一句话身份"},
        "feeds": "产出=稳定的垂直标签 → 喂下一站『建信任』的内容信誉地基"},
    "起号·建信任": {
        "direction": "把专业人设立起来·让刷到的人信你——信任是B端的硬通货",
        "dims": {"内容": "专业输出+复刻自己爆款·显性化信任状(源头/工艺/资质)",
                 "承接": "主页+评论区置顶挂私域钩子·接通承接管道",
                 "私域": "评论引导加微信·黄金2h响应·开始沉淀线索",
                 "数据": "看口碑演化(采购意向趋势)+评论真实性", "人设": "信任状摆出来(36年/非遗/源头工厂)"},
        "feeds": "产出=信任+私域入口 → 喂下一站『初变现』的线索池"},
    "初变现": {
        "direction": "把信任变成第一笔成交·跑通最小变现闭环(MVP变现)",
        "dims": {"内容": "内容加挂载/软植入·小批量选品测试", "承接": "私域成交SOP·样品/起订量/低价课接住",
                 "私域": "私域分层·促首单·沉淀成交话术", "数据": "盯转化率/客单/复购信号",
                 "人设": "从『专家』升级到『可交易的供应商』"},
        "feeds": "产出=验证过的变现路径 → 喂下一站『成长』的规模化模板"},
    "成长": {
        "direction": "把跑通的单条路径规模化·多变现路径并行·从单点到系统",
        "dims": {"内容": "矩阵化选题·稳定爆款产线", "承接": "多SKU/多价位·分销/招商体系",
                 "私域": "社群运营·复购/转介绍机制", "数据": "看LTV/各渠道ROI·砍低效",
                 "人设": "行业IP化·从供应商到品类代言"},
        "feeds": "产出=多路径稳定变现 → 喂下一站『成熟』的IP商业化"},
    "成熟": {
        "direction": "IP商业化·把影响力沉淀成可复制的商业资产(组织化)",
        "dims": {"内容": "内容团队化·IP人格化", "承接": "课程矩阵/企培/自有品牌",
                 "私域": "私域品牌化运营·会员体系", "数据": "看品牌资产/矩阵协同效应",
                 "人设": "行业领袖·标准制定者"},
        "feeds": "顶阶·转向矩阵号复制与品牌资产沉淀"},
}
_PLAY_GEN = {
    "冷启·打标签": {
        "direction": "验证内容模型·让算法打标签·这一站禁碰变现",
        "dims": {"内容": "垂直选题·测内容模型", "承接": "不变现", "私域": "不引流",
                 "数据": "盯完播/垂直度", "人设": "立内容人格"},
        "feeds": "产出=被算法识别的内容标签 → 喂『初变现』"},
    "初变现": {
        "direction": "找最适配的变现路径·软植入测试·别硬来",
        "dims": {"内容": "内容+软植入测试", "承接": "商单/橱窗试水", "私域": "轻度沉淀粉丝",
                 "数据": "看商单转化/带货GMV", "人设": "人格IP雏形"},
        "feeds": "产出=验证过的变现路径 → 喂『成长变现』"},
    "成长变现": {
        "direction": "多路径打透+私域沉淀·把流量复利化",
        "dims": {"内容": "矩阵化内容产线", "承接": "多变现叠加", "私域": "私域社群沉淀",
                 "数据": "看多路径ROI", "人设": "稳定人格IP"},
        "feeds": "产出=多元稳定变现 → 喂『成熟』"},
    "成熟": {
        "direction": "多元变现叠加+矩阵化·从账号到品牌",
        "dims": {"内容": "团队化内容", "承接": "品牌/代言/矩阵", "私域": "品牌私域",
                 "数据": "品牌资产", "人设": "品牌人格"},
        "feeds": "产出=品牌资产 → 喂『头部』"},
    "头部": {
        "direction": "IP商业化·品牌化·行业头部",
        "dims": {"内容": "IP内容宇宙", "承接": "品牌商业化", "私域": "粉丝品牌",
                 "数据": "行业影响力", "人设": "行业领袖"},
        "feeds": "顶阶"},
}

# 价值链(链条全景·跨阶段的一条主线)
_CHAIN_B2B = ["建信任", "产线索", "促成交", "促复购", "矩阵复利"]
_CHAIN_GEN = ["打标签", "测变现", "复利化", "品牌化", "头部化"]


def build_journey(account: dict, deep: dict | None = None) -> dict[str, Any]:
    """运营阶段旅程:已走过/当前/接下来 + 进阶条件 + 阶段×维度矩阵 + 链条。"""
    deep = deep or {}
    track = (deep.get("industry") or {}).get("track_tier") or \
        BM.classify_track(account.get("industry_tag") or account.get("nickname"))
    is_b2b = track.get("is_b2b_leads")
    stages = _STAGES_B2B if is_b2b else _STAGES_GEN
    play = _PLAY_B2B if is_b2b else _PLAY_GEN
    chain = _CHAIN_B2B if is_b2b else _CHAIN_GEN
    f = account.get("follower") or 0

    cur_idx = 0
    for i, (_, lo, hi, _, _) in enumerate(stages):
        if lo <= f < hi:
            cur_idx = i
            break
    else:
        cur_idx = len(stages) - 1

    nxt_idx = min(cur_idx + 1, len(stages) - 1)
    advance = stages[cur_idx][4]
    gaps = _advance_gaps(account, stages[cur_idx], deep, is_b2b)

    def _node(i):
        name, lo, hi, task, adv = stages[i]
        state = "done" if i < cur_idx else ("current" if i == cur_idx else "future")
        pb = play.get(name, {})
        return {"idx": i, "name": name, "fans_range": f"{_fmt(lo)}-{_fmt(hi)}",
                "task": task, "advance": adv, "state": state,
                "direction": pb.get("direction", ""), "dims": pb.get("dims", {}),
                "feeds": pb.get("feeds", ""), "chain_link": chain[i] if i < len(chain) else ""}

    nodes = [_node(i) for i in range(len(stages))]

    # 阶段×维度矩阵(完整架构·指令5③)
    matrix = {
        "dims": [d for d, _ in WORK_DIMS],
        "icons": {d: ic for d, ic in WORK_DIMS},
        "rows": [{"stage": n["name"], "state": n["state"], "chain": n["chain_link"],
                  "cells": [n["dims"].get(d, "—") for d, _ in WORK_DIMS]} for n in nodes],
        "compliance": COMPLIANCE,
    }
    # 链条全景(产出→输入·指令5②)
    chain_flow = [{"link": chain[i], "stage": stages[i][0],
                   "feeds": play.get(stages[i][0], {}).get("feeds", ""),
                   "state": nodes[i]["state"]} for i in range(len(stages))]

    cur = nodes[cur_idx]
    return {
        "is_b2b": is_b2b,
        "nodes": nodes,
        "criteria": _criteria(account, is_b2b),
        "current": stages[cur_idx][0],
        "current_idx": cur_idx,
        "current_task": stages[cur_idx][2],
        "current_direction": cur["direction"],       # 当前阶段专业方向(指令5④)
        "current_dims": cur["dims"],                  # 当前阶段五维该做什么(指令5①)
        "current_feeds": cur["feeds"],                # 当前阶段产出喂给谁(指令5②)
        "next": stages[nxt_idx][0] if nxt_idx != cur_idx else None,
        "advance_criteria": advance,
        "advance_gaps": gaps,
        "done": [stages[i][0] for i in range(cur_idx)],
        "future": [stages[i][0] for i in range(cur_idx + 1, len(stages))],
        "matrix": matrix,
        "chain_flow": chain_flow,
        "chain_name": " → ".join(chain),
        "verdict": _verdict(stages, cur_idx, nxt_idx, gaps),
        "source": "CAT §五(B端) / PB §A2(泛娱乐)·赛道感知阶段×维度模型",
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
    if f < hi:
        gaps.append(f"粉丝量级:{_fmt(f)}→{_fmt(hi)}(还差 {_fmt(hi - f)})")
    if is_b2b and "承接" in adv and (account.get("commerce_density") or 0) == 0:
        gaps.append("私域承接:当前商业密度0·零承接·需补私域钩子(这是进阶硬条件)")
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

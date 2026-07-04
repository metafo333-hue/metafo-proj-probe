"""基础数据判断引擎 · basics_judge.py · 每个基础数据给「档位标尺」(指令1+追加)。

承用户:基础数据不能裸列·也不能只甩个"健康"。每条要回答四问——
  ① 当前情况(你的值+处在哪档)  ② 一共几档(标尺)
  ③ 每档由什么决定(decided_by)  ④ 目标(进上一档要到多少)
→ 让用户心中有数、看着明确、目标明确。

实现:每指标定义一组有序档位(best→worst)+判据·命中第一个为真者即当前档·
上一档即明确目标。阈值多为经验值(标待校准)·比例类(关注比/获赞比)相对稳健。
"""
from __future__ import annotations

from typing import Any, Callable

_GOOD, _MID, _BAD = "good", "mid", "bad"


def _grade(label: str, value_str: str, raw: float, decided_by: str,
           tiers: list[tuple[str, str, str, Callable[[float], bool]]]) -> dict[str, Any]:
    """tiers: [(档名, level, 判据文案, 谓词)] 按 best→worst 排·取首个为真者。"""
    hit = next((i for i, (_, _, _, pred) in enumerate(tiers) if pred(raw)), len(tiers) - 1)
    name, level, _cond, _ = tiers[hit]
    tier_list = [{"name": n, "cond": c, "level": lv, "hit": i == hit}
                 for i, (n, lv, c, _) in enumerate(tiers)]
    if hit == 0:
        target = f"已处最优档「{name}」·保持"
    else:
        bn, _blv, bc, _ = tiers[hit - 1]
        target = f"目标 {bc} → 进「{bn}」档"
    return {"label": label, "value": value_str, "raw": raw, "decided_by": decided_by,
            "tier_now": name, "level": level, "tiers": tier_list, "target": target}


def judge_basics(account: dict) -> list[dict[str, Any]]:
    """逐条基础数据 → 档位标尺。空数据跳过(诚实·不编造)。"""
    out: list[dict] = []
    f = account.get("follower") or 0
    fing = account.get("following_count")
    tot = account.get("total_favorited")
    aw = account.get("aweme_count")
    al = account.get("avg_like")
    ml = account.get("max_like")
    mx = account.get("max_follower")
    burst = account.get("burst_ratio")
    gap = account.get("update_gap_days")

    # ① 关注/粉丝比 → 账号性质(越低越像真创作者)
    if fing is not None and f:
        r = fing / f
        out.append(_grade(
            "关注/粉丝比", f"{fing}/{f}={r*100:.0f}%", r,
            "由关注克制度决定:真创作者只关注少数同行;关注≈粉丝多为互关刷量",
            [("真实创作者", _GOOD, "≤10%", lambda x: x <= 0.1),
             ("偏正常", _MID, "10–50%", lambda x: x <= 0.5),
             ("疑互关/营销号", _BAD, ">50%", lambda x: True)]))

    # ② 获赞总/粉丝 → 累计影响力(越高粉丝越真实活跃)
    if tot is not None and f:
        per = tot / f
        out.append(_grade(
            "获赞总/粉丝", f"{tot}/{f}={per:.1f}", per,
            "由粉丝真实活跃度+内容累计质量决定:单粉累计贡献赞数·越高粉丝越真",
            [("优秀", _GOOD, "≥5", lambda x: x >= 5),
             ("健康", _GOOD, "3–5", lambda x: x >= 3),
             ("一般", _MID, "1–3", lambda x: x >= 1),
             ("偏弱(疑买粉/低活)", _BAD, "<1", lambda x: True)]))

    # ③ 内容产出效率 → 单条平均互动(与作品数无关·量多≠效率高)
    if al is not None:
        vol = f"·共{aw}作品" if aw is not None else ""
        out.append(_grade(
            "内容产出效率", f"均{al}赞{vol}", al,
            "由内容质量/选题钩子决定·非作品数:124条但均赞低=勤奋但单条转化弱(质优于量)",
            [("强", _GOOD, "均赞≥300", lambda x: x >= 300),
             ("良", _GOOD, "100–300", lambda x: x >= 100),
             ("一般", _MID, "30–100", lambda x: x >= 30),
             ("弱", _BAD, "<30", lambda x: True)]))

    # ④ 掉粉 → 峰值回撤(越低越稳)
    if mx is not None and f and mx > 0:
        pct = (mx - f) / mx * 100
        out.append(_grade(
            "粉丝稳定度", f"峰值{mx}→当前{f}(回撤{pct:.0f}%)", pct,
            "由近期内容质量+更新连续性决定:回撤大常因断更/内容滑坡/违规限流",
            [("稳定", _GOOD, "回撤<5%", lambda x: x < 5),
             ("轻度掉粉", _MID, "5–15%", lambda x: x < 15),
             ("明显掉粉", _BAD, "≥15%", lambda x: True)]))

    # ⑤ 爆款能力 → 最高赞÷均赞(越高越能破圈)
    if burst is not None:
        tail = f"(最高赞{ml})" if ml else ""
        out.append(_grade(
            "爆款能力", f"{burst}{tail}", burst,
            "由是否有可复制爆款结构决定:≥3=能跑出爆款·复刻那几条钩子/选题即可放大",
            [("强", _GOOD, "≥5", lambda x: x >= 5),
             ("有", _GOOD, "3–5", lambda x: x >= 3),
             ("平", _MID, "1.5–3", lambda x: x >= 1.5),
             ("无爆款", _BAD, "<1.5", lambda x: True)]))

    # ⑥ 更新节奏 → 发布间隔(越短算法越友好)
    if gap is not None:
        out.append(_grade(
            "更新节奏", f"约{gap}天/条", gap,
            "由发布纪律决定:断更掉算法权重·稳定连续>偶尔爆发",
            [("高频活跃", _GOOD, "≤2天/条", lambda x: x <= 2),
             ("节奏适中", _MID, "2–5天/条", lambda x: x <= 5),
             ("更新偏慢", _BAD, ">5天/条", lambda x: True)]))

    return out


def summary(judges: list[dict]) -> dict[str, Any]:
    """总览:几项几档·一句心中有数。"""
    g = sum(1 for j in judges if j["level"] == _GOOD)
    m = sum(1 for j in judges if j["level"] == _MID)
    b = sum(1 for j in judges if j["level"] == _BAD)
    weak = [j["label"] for j in judges if j["level"] == _BAD]
    line = f"{len(judges)} 项基础数据:{g} 项达标 / {m} 项中等 / {b} 项需补"
    if weak:
        line += "·短板=" + "、".join(weak)
    return {"good": g, "mid": m, "bad": b, "weak": weak, "line": line}

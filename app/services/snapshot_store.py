"""快照库 · 完整 B 的历史机制(跨次采集算轨迹)。

时序导数分两半(见 time_series.py):
  单次可算 → 内容时序(互动斜率/衰减)·已落地;
  需历史   → 账号涨粉轨迹/处方前后对照·本模块。

机制:每次 /board 分析,记一条轻量快照(时间戳+关键标量)到 data/snapshots/{slug}.jsonl,
按"日"去重(同账号同日只记一条)。读取时**回填既有 data/cases/*/meta.json 历史**
(归集设施已存多次分析·北川魔芋有 0621/0622/0627 三次)→ 立刻有真实轨迹·非从零等。

只存账号级聚合标量(粉丝/均赞/健康/阶段)·不落任何个人字段(守 PIPL·M7①)。
本模块是普通运行时(非 workflow 脚本)·datetime.now() 可用。
"""
from __future__ import annotations

import glob
import json
import pathlib
import statistics as _S
from datetime import datetime
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parents[2]   # probe/
_SNAP_DIR = _ROOT / "data" / "snapshots"
_CASES_DIR = _ROOT / "data" / "cases"


def _slug(nick: str) -> str:
    """与 cases_store._slug 对齐(尽量复用)·失败则本地兜底。"""
    try:
        from app.services.cases_store import _slug as cs_slug
        return cs_slug(nick)
    except Exception:  # noqa: BLE001
        import re
        s = re.sub(r"[^a-z0-9]+", "", (nick or "acct").lower())
        return s or "acct"


def record(account: dict, board: dict, sec_uid: str | None = None) -> dict | None:
    """记一条快照(按日去重)。返回写入的 snapshot dict 或 None(失败不拖垮接口)。"""
    try:
        nick = account.get("nickname") or "acct"
        slug = _slug(nick)
        ladders = board.get("ladders") or {}
        l4 = ladders.get("l4") or {}
        l3 = ladders.get("l3") or {}
        # 记录本次给的处方(供下次采集对照"建议有没有用")
        rx = None
        if l3.get("conclusion"):
            rx = {"call": l3.get("conclusion"), "color": l3.get("strategic_color"),
                  "steps": (l3.get("this_week") or [])[:3]}
        snap = {
            "ts": datetime.now().isoformat(timespec="seconds"),  # noqa: DTZ005
            "date": datetime.now().strftime("%Y-%m-%d"),         # noqa: DTZ005
            "nickname": nick, "sec_uid": sec_uid,
            "follower": account.get("follower"),
            "max_follower": account.get("max_follower"),
            "avg_like": account.get("avg_like"),
            "max_like": account.get("max_like"),
            "health": (board.get("raw") or {}).get("scores", {}).get("c1", {}).get("score"),
            "commerce_density": account.get("commerce_density"),
            "stage": l4.get("stage"),
            "prescription": rx,
        }
        _SNAP_DIR.mkdir(parents=True, exist_ok=True)
        fp = _SNAP_DIR / f"{slug}.jsonl"
        # 按日 upsert:同日已有则用最新一条覆盖(最新分析最完整·含处方)·非简单跳过。
        existing = [r for r in _read_jsonl(fp) if r.get("date") != snap["date"]]
        existing.append(snap)
        existing.sort(key=lambda r: r.get("date") or "")
        with fp.open("w", encoding="utf-8") as f:
            for r in existing:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return snap
    except Exception:  # noqa: BLE001
        return None


def _read_jsonl(fp: pathlib.Path) -> list[dict]:
    if not fp.exists():
        return []
    out = []
    for line in fp.read_text("utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return out


def _backfill_from_cases(nick: str) -> list[dict]:
    """从既有 data/cases/*/meta.json 回填历史快照(账号名匹配)。"""
    out = []
    for mp in glob.glob(str(_CASES_DIR / "*" / "meta.json")):
        try:
            m = json.loads(pathlib.Path(mp).read_text("utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if (m.get("account_name") or m.get("nickname")) != nick:
            continue
        date = m.get("analyzed_date") or (m.get("analyzed_at") or "")[:10]
        if not date:
            continue
        out.append({
            "ts": m.get("analyzed_at") or date, "date": date,
            "nickname": nick, "sec_uid": m.get("sec_uid"),
            "follower": m.get("follower"), "avg_like": m.get("avg_like"),
            "max_like": m.get("max_like"), "health": None,
            "commerce_density": None, "stage": None, "_from": "case",
        })
    return out


def load_history(nick: str) -> list[dict]:
    """合并 snapshots/{slug}.jsonl + 回填 cases·按日去重·按日期升序。"""
    slug = _slug(nick)
    snaps = _read_jsonl(_SNAP_DIR / f"{slug}.jsonl") + _backfill_from_cases(nick)
    by_date: dict[str, dict] = {}
    for s in snaps:
        d = s.get("date")
        if not d:
            continue
        # 同日:优先用 snapshots(更全·含 health)·case 回填作兜底
        if d not in by_date or s.get("_from") != "case":
            by_date[d] = s
    return [by_date[d] for d in sorted(by_date)]


# ── 跨快照导数:涨粉轨迹 / 互动趋势 / 健康趋势 / 处方对照 ──────────────────────────
def trajectory(history: list[dict]) -> dict[str, Any]:
    pts = [h for h in history if h.get("follower") is not None]
    if len(pts) < 2:
        return {"enough": False,
                "verdict": f"历史快照 {len(pts)} 个(<2)·涨粉轨迹积累中·"
                           "每次分析自动存档·攒够2次即出真实曲线",
                "snapshots": len(pts)}
    first, last = pts[0], pts[-1]
    df = (last["follower"] or 0) - (first["follower"] or 0)
    days = _date_span(first.get("date"), last.get("date")) or 1
    daily = df / days if days else 0
    pct = round(df / (first["follower"] or 1) * 100, 2)
    base = first["follower"] or 1
    # 涨粉判定(日增 vs 体量)
    daily_pct = daily / base * 100
    if daily_pct >= 1:
        verdict = "快速涨粉"
    elif daily_pct >= 0.1:
        verdict = "稳定涨粉"
    elif daily_pct > -0.05:
        verdict = "涨粉停滞(平台期)"
    else:
        verdict = "掉粉"
    # 互动趋势(avg_like)
    likes = [h.get("avg_like") for h in history if h.get("avg_like") is not None]
    like_trend = None
    if len(likes) >= 2 and likes[0]:
        lp = round((likes[-1] - likes[0]) / likes[0] * 100, 1)
        like_trend = (f"均赞 {likes[0]}→{likes[-1]}(" + ("持平" if abs(lp) < 5
                      else f"{'+' if lp > 0 else ''}{lp}%") + ")")
    # 健康趋势(若有)
    healths = [(h.get("date"), h.get("health")) for h in history if h.get("health") is not None]
    health_trend = None
    if len(healths) >= 2:
        hd = healths[-1][1] - healths[0][1]
        health_trend = f"健康 {healths[0][1]}→{healths[-1][1]}({'+' if hd >= 0 else ''}{hd})"
    return {
        "enough": True, "snapshots": len(pts),
        "verdict": verdict,
        "follower_path": [(h.get("date"), h.get("follower")) for h in pts],
        "follower_delta": df, "span_days": days, "daily_rate": round(daily, 1),
        "follower_pct": pct,
        "like_trend": like_trend, "health_trend": health_trend,
        "detail": (f"{first.get('date')}→{last.get('date')}({days}天)·"
                   f"{first['follower']}→{last['follower']}粉"
                   f"({'+' if df >= 0 else ''}{df}·{'+' if pct >= 0 else ''}{pct}%)·"
                   f"日均{'+' if daily >= 0 else ''}{round(daily, 1)}粉"),
        "note": "跨次采集真实轨迹·只存账号级聚合标量(守PIPL)·快照越多越准",
    }


def _date_span(d1: str | None, d2: str | None) -> int | None:
    try:
        a = datetime.strptime(d1, "%Y-%m-%d")
        b = datetime.strptime(d2, "%Y-%m-%d")
        return max(1, (b - a).days)
    except Exception:  # noqa: BLE001
        return None


# ── 处方前后对照(证明系统建议有没有用)──────────────────────────────────────────
def prescription_effect(history: list[dict]) -> dict[str, Any]:
    """找最早带处方的快照·对照其后指标真实变化。

    诚实立场:测的是**结果**(处方后指标动没动)·不是**执行**(用户做没做)——
    公开数据看不到执行·只能看结果·明确标注。指标改善≠处方一定有效(可能其他因素),
    但指标恶化是清晰的反向信号。
    """
    rx_snaps = [h for h in history if h.get("prescription")]
    if not rx_snaps:
        return {"enough": False,
                "verdict": "尚无带处方的历史快照·处方对照从本次起算·下次采集见效"}
    rx0 = rx_snaps[0]                       # 最早一次处方
    latest = history[-1]
    if rx0.get("date") == latest.get("date"):
        return {"enough": False,
                "verdict": f"本次首记处方「{(rx0.get('prescription') or {}).get('call','')}」"
                           "·下次采集即可对照指标变化(看建议有没有用)"}
    days = _date_span(rx0.get("date"), latest.get("date")) or 1

    def _delta(key):
        a, b = rx0.get(key), latest.get(key)
        if a is None or b is None:
            return None
        return b - a
    df, dl, dh = _delta("follower"), _delta("avg_like"), _delta("health")
    moves = []
    if df is not None:
        moves.append(f"粉丝{'+' if df >= 0 else ''}{df}")
    if dl is not None:
        moves.append(f"均赞{'+' if dl >= 0 else ''}{dl}")
    if dh is not None:
        moves.append(f"健康{'+' if dh >= 0 else ''}{dh}")
    # 结果判定(诚实:改善/持平/恶化·非"处方有效")
    score = sum(1 for d in (df, dl, dh) if d is not None and d > 0) - \
        sum(1 for d in (df, dl, dh) if d is not None and d < 0)
    if score > 0:
        outcome = "处方后指标改善(方向对·建议大概率有用)"
    elif score < 0:
        outcome = "处方后指标恶化(建议没起效/未执行/或有外部因素)"
    else:
        outcome = "处方后指标持平(待更久观察)"
    return {
        "enough": True,
        "rx_date": rx0.get("date"), "rx_call": (rx0.get("prescription") or {}).get("call"),
        "rx_steps": (rx0.get("prescription") or {}).get("steps", []),
        "days_since": days,
        "metric_moves": moves,
        "outcome": outcome,
        "verdict": f"{rx0.get('date')} 建议「{(rx0.get('prescription') or {}).get('call','')}」"
                   f"·{days}天后:{('·'.join(moves) or '指标未取到')}·{outcome}",
        "note": "测结果非执行(公开数据看不到用户做没做)·指标改善≠唯一归因·恶化是清晰反向信号",
    }

"""归集画廊 · gallery.py · 所有数据分析输出自动汇集(point5)。

规范:以后数据分析**不再单独出地址**·每次 /board 分析自动入库到一个集中画廊·
一个入口看全部、可横向对比。承 v3.2 案例库/经验沉淀。

机制:register() 每次分析 → ① 写报告 HTML 到 metaboard/reports/{slug}-{date}.html
② 追加记录到 gallery-index.json(按 slug 留最新)③ 重生成 gallery.html(静态对比页·
无JS·8911直接看)。METABOARD_GALLERY_DIR 可覆盖默认路径。
只存账号级聚合标量(守 PIPL)。
"""
from __future__ import annotations

import json
import os
import pathlib
import re
from datetime import datetime
from typing import Any

_PROBE = pathlib.Path(__file__).resolve().parents[2]            # probe/
_DEFAULT = _PROBE.parent / "运营报告" / "metaboard"             # metafoclaw/运营报告/metaboard
_BLUE, _ORANGE = "#1E3A8A", "#FF7A1A"


def _dir() -> pathlib.Path:
    return pathlib.Path(os.getenv("METABOARD_GALLERY_DIR", str(_DEFAULT)))


def _slug(nick: str) -> str:
    try:
        from app.services.cases_store import _slug as cs
        return cs(nick)
    except Exception:  # noqa: BLE001
        return re.sub(r"[^a-z0-9]+", "", (nick or "acct").lower()) or "acct"


def register(account: dict, board: dict, html: str) -> dict | None:
    """汇集一次分析到画廊。返回 {report_url, gallery_url} 或 None(失败不拖垮接口)。"""
    try:
        gdir = _dir()
        (gdir / "reports").mkdir(parents=True, exist_ok=True)
        nick = account.get("nickname") or "账号"
        slug = _slug(nick)
        date = datetime.now().strftime("%Y-%m-%d")             # noqa: DTZ005
        rel = f"reports/{slug}-{date}.html"
        (gdir / rel).write_text(html, "utf-8")

        L = board.get("ladders") or {}
        s = (board.get("raw") or {}).get("scores", {})
        l1, l4 = L.get("l1") or {}, L.get("l4") or {}
        track = ((board.get("raw") or {}).get("deep") or {})  # may be absent
        rec = {
            "slug": slug, "nickname": nick, "date": date,
            "follower": account.get("follower"),
            "health": (s.get("c1") or {}).get("score"),
            "grade": (s.get("c7") or {}).get("grade"),
            "track": _track_name(l1),
            "stage": _stage_name(l1),
            "strategy": ((L.get("l3") or {}).get("conclusion")),
            "pred_stage": l4.get("stage"),
            "report": rel,
        }
        idx_fp = gdir / "gallery-index.json"
        idx = _read_index(idx_fp)
        idx = [r for r in idx if r.get("slug") != slug]        # 同账号留最新
        idx.append(rec)
        idx.sort(key=lambda r: r.get("date") or "", reverse=True)
        idx_fp.write_text(json.dumps(idx, ensure_ascii=False, indent=1), "utf-8")

        (gdir / "gallery.html").write_text(_render_gallery(idx), "utf-8")
        return {"report": rel, "gallery": "gallery.html", "count": len(idx)}
    except Exception:  # noqa: BLE001
        return None


def _track_name(l1: dict) -> str | None:
    h = l1.get("heading") or {}
    now = h.get("now") or l1.get("conclusion") or ""
    return now.split("·")[0] if now else None


def _stage_name(l1: dict) -> str | None:
    now = (l1.get("heading") or {}).get("now") or l1.get("conclusion") or ""
    parts = now.split("·")
    return parts[1] if len(parts) > 1 else None


def _read_index(fp: pathlib.Path) -> list[dict]:
    if not fp.exists():
        return []
    try:
        return json.loads(fp.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return []


def _stamp() -> str:
    return ('scenario=metaboard;format=html;template=gallery;renderer=gallery;'
            'engine=metaboard;board_ver=3.3;v=1')


def _render_gallery(idx: list[dict]) -> str:
    rows = ""
    for r in idx:
        g = r.get("grade") or "—"
        rows += (f'<tr><td><a href="{r.get("report","")}">{r.get("nickname","")}</a></td>'
                 f'<td>{r.get("track") or "—"}</td><td>{r.get("stage") or "—"}</td>'
                 f'<td>{_n(r.get("follower"))}</td>'
                 f'<td><b>{_n(r.get("health"))}</b></td><td>{g}</td>'
                 f'<td style="font-size:12px">{r.get("strategy") or "—"}</td>'
                 f'<td style="font-size:12px">{r.get("pred_stage") or "—"}</td>'
                 f'<td style="font-size:11px;color:#6B7280">{r.get("date","")}</td></tr>')
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-metaform" content="{_stamp()}">
<title>元板 · 分析画廊 · 全账号归集对比</title>
<style>
 body{{font-family:-apple-system,"PingFang SC",sans-serif;color:#1F2937;background:#F8FAFC;margin:0}}
 .wrap{{max-width:1100px;margin:0 auto;padding:20px}}
 h1{{color:{_BLUE}}} .sub{{color:#6B7280;font-size:14px;margin-top:-8px}}
 table{{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0;background:#fff;border-radius:10px;overflow:hidden}}
 th{{background:{_BLUE};color:#fff;text-align:left;padding:9px 11px;position:sticky;top:0}}
 td{{padding:8px 11px;border-bottom:1px solid #EEF2F7}}
 tr:nth-child(even) td{{background:#EFF6FF}} a{{color:{_BLUE};font-weight:600}}
 .tag{{display:inline-block;background:{_ORANGE};color:#fff;font-size:12px;padding:2px 10px;border-radius:10px}}
</style></head><body><div class="wrap">
<h1>元板 · 分析画廊</h1>
<p class="sub">所有账号分析自动归集于此 · 共 <span class="tag">{len(idx)} 个账号</span> · 横向对比 · 点昵称看完整报告</p>
<table><tr><th>账号</th><th>赛道</th><th>阶段</th><th>粉丝</th><th>健康</th><th>评级</th>
<th>战略处方</th><th>趋势</th><th>更新</th></tr>{rows}</table>
<p style="font-size:12px;color:#9CA3AF">元板 MetaBoard v3.3 · 自动归集 · 每次 /board 分析自动入库 · 同账号留最新</p>
</div></body></html>"""


def _n(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)) and v >= 10000:
        return f"{v/10000:.1f}万"
    return str(v)

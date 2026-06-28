"""契约对接桥 · contract_adapter.py · probe 分析 → MetaForm 自适应输出契约 doc。

对方窗口(MetaForm account-diagnosis 场景·render_contract 引擎)实施渲染;本模块只产
**契约 doc**(meta + blocks·语义角色),不动对方引擎/场景/schema(尊重边界)。

五项深化(2026-06-28)全部落到契约:
  指令1 基础数据档位标尺(判断+依据+几档+目标)        → appendix ①
  指令2 内容→口碑→势能 因果链 + 二阶导轨迹             → evidence + appendix ②
  指令3 全基础数据整理(身份表+判断表)                  → appendix ①
  指令4 八维7层详解 + 增强雷达(基准环/短板红/轴值)     → appendix ④
  指令5 运营阶段链条 + 阶段×维度矩阵 + 专业方向         → situation + actions + appendix ③

不变量:N6 内部代号(C1/C9)不进客户版→指标一律人话标签;show_accounting 默认 false。
⚠️ render_contract 仅 appendix.html 放行原始 HTML·其余角色文本一律被 html.escape→纯文本无标签。
"""
from __future__ import annotations

from typing import Any

# C 代号 → 人话标签(N6:客户版禁出 C1/C9)
_LABEL = {"c1": "健康", "c2": "粉丝质量", "c3": "商业转化", "c4": "内容力",
          "c5": "赛道", "c6": "破圈", "c7": "评级", "c8": "私域"}
_COMPLIANCE = "数据源合规授权 · 国内不出境"
_LV_COL = {"good": "#059669", "mid": "#D97706", "bad": "#DC2626", "na": "#9CA3AF"}


def _g(d, *ks, default=None):
    cur = d
    for k in ks:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur


def _n(v, dash="—"):
    return dash if v is None else str(v)


def build_contract_doc(board: dict[str, Any]) -> dict[str, Any]:
    """build_board 输出 → MetaForm 契约 doc(source=metaboard·对方按 account-diagnosis 渲)。"""
    L = board.get("ladders") or {}
    l1, l2, l3, l4 = (L.get("l1") or {}, L.get("l2") or {}, L.get("l3") or {}, L.get("l4") or {})
    s = _g(board, "raw", "scores", default={})
    nick = board.get("nickname") or "账号"
    idn = l1.get("identity") or {}

    journey = board.get("journey") or {}
    basics = board.get("basics") or {}
    judges = board.get("basics_judge") or []
    bsum = board.get("basics_summary") or {}
    causal = board.get("causal") or {}

    meta = {
        "subject_name": nick, "platform": "抖音",
        "subtitle": _track_subtitle(l1),
        "fans": board_follower(board),
        "grade": _g(s, "c7", "grade"),
        "health_score": _g(s, "c1", "score"),
        "show_accounting": False,            # N6:对外纯诊断·算账走内部
        "compliance": _COMPLIANCE,
    }

    blocks = [
        _verdict(l3, l1),
        _situation(l1, idn, journey),
        _key_issue(l2, l4),
        _evidence(s, l2, l4, idn, bsum, causal),
        _actions(l3, journey),
        _forecast(l4, journey),
        _scope(l2, s),
        _appendix(l2, s, journey, basics, judges, bsum, causal),
    ]
    blocks = [b for b in blocks if b]
    return {"source": "metaboard", "doc": {"meta": meta, "blocks": blocks}}


def board_follower(board) -> int | None:
    return _g(board, "ladders", "l1", "milestone", "follower")


def _track_subtitle(l1) -> str:
    now = _g(l1, "heading", "now") or l1.get("conclusion") or ""
    return (now.split("·")[0] + " · 价值阶梯诊断") if now else "价值阶梯诊断"


# ── verdict 脊柱(战略判断·N1 唯一)──
def _verdict(l3, l1) -> dict:
    call = l3.get("conclusion") or "—"
    why = _g(l3, "front", "strategy", "why") or l3.get("strategic_why") or ""
    stage = _g(l1, "heading", "now") or ""
    game = "该玩线索游戏，不玩流量游戏。" if "B端" in stage or "B 端" in stage else ""
    return {"role": "verdict", "spine": f"**{call}**——{why}",
            "tagline": (stage.split("·")[-1] + " · " + game) if game else stage}


# ── situation 处境(你在链条哪一站 + 专业方向 + 形象一致性)──
def _situation(l1, idn, journey) -> dict:
    h = l1.get("heading") or {}
    cur = journey.get("current", "")
    link = ""
    for n in journey.get("nodes") or []:
        if n.get("state") == "current":
            link = n.get("chain_link", "")
            break
    done = journey.get("done") or []
    fut = journey.get("future") or []
    lead = (f"你在运营链条「{journey.get('chain_name','')}」的【{cur}】" +
            (f"（{link}）" if link else "") +
            (f"，已走过 {'、'.join(done)}" if done else "") +
            (f"，接下来 {'、'.join(fut[:2])}" if fut else "") + "。")
    txt = ""
    if journey.get("current_direction"):
        txt += f"这一站的专业方向：{journey['current_direction']}。"
    txt += journey.get("verdict", "")
    if h.get("endstate"):
        txt += f"。终极目标:{h['endstate'][:40]}"
    if idn.get("consistency") is not None:
        txt += f"。形象一致性 {idn.get('consistency')}（{idn.get('self_match','')}）"
    return {"role": "situation", "lead": lead, "text": txt + "。"}


# ── key_issue 最该一件事(因果流 + 热评原话 + 收口)──
def _key_issue(l2, l4) -> dict:
    tc = l2.get("top_concern") or {}
    chain = l2.get("chain") or []
    kou = next((c for c in chain if c.get("layer") == "口碑层"), {})
    se = l4.get("sentiment_evo") or {}
    flow = []
    if se.get("enough"):
        flow.append({"text": f"评论采购意向{se.get('intent_trend','')[:20]}"})
    if (l2.get("deep_commerce") or {}).get("conclusion"):
        flow.append({"text": l2["deep_commerce"]["conclusion"][:30], "bad": True})
    hot = l2.get("hot_comments") or {}
    clusters = l2.get("comment_clusters") or {}
    note = ""
    if clusters.get("enough"):
        note = "热评诉求：" + "、".join(f"「{c['theme']}」" for c in (clusters.get("clusters") or [])[:3])
    elif hot.get("enough") and hot.get("top"):
        note = "最高赞评论：「" + (hot["top"][0]["text"][:24]) + "」"
    return {"role": "key_issue",
            "lead": (kou.get("diagnosis") or tc.get("what") or "最该聚焦的一件事")[:50],
            "flow": flow or [{"text": tc.get("what", "")[:40]}],
            "note": note,
            "punch": tc.get("advice") or _g(kou, "link") or ""}


# ── evidence 证据(人话标签·非C代号·N6)+ 基础数据总评 + 因果链结论 ──
def _evidence(s, l2, l4, idn, bsum, causal) -> dict:
    items = []
    # 基础数据总评(指令1·一句心中有数)·value 须短(官方 .val 是 nowrap)
    if bsum.get("line"):
        items.append({"label": "基础数据体检", "sub": "档位标尺总览·详见附录",
                      "value": f"{bsum.get('good',0)}达标·{bsum.get('mid',0)}中·{bsum.get('bad',0)}需补",
                      "def": "每项基础数据按档位标尺判断(几档/由什么决定/目标)·详见附录基础数据表。"})
    # 因果链结论(指令2·内容→口碑→势能)·value 用短标签·全句进附录
    if causal.get("chain_verdict"):
        br = causal.get("broken")
        val = (br["link"] + " 断点") if br else "三环咬合·放大窗口"
        items.append({"label": "内容因果链", "sub": "内容→口碑→势能·详见附录",
                      "value": val,
                      "def": "把内容/口碑/势能三块串成因果链·看哪种内容真带来口碑与势能、哪一环在漏。"})
    se = l4.get("sentiment_evo") or {}
    if se.get("enough"):
        e, l = se.get("early") or {}, se.get("late") or {}
        items.append({"label": "口碑采购意向", "sub": "评论采购/咨询语义趋势",
                      "value": f"早 {e.get('intent_rate')} → 近 {l.get('intent_rate')} · {se.get('verdict','')}",
                      "def": "评论中采购/咨询/下单类语义占比趋势。上升=视频在持续产线索。"})
    attr = l2.get("attribution") or {}
    if attr.get("enough") and attr.get("top_driver"):
        td = attr["top_driver"]
        items.append({"label": "内容驱动因子", "sub": "哪个数据因子最驱动互动",
                      "value": f"{td.get('factor')}（差 {td.get('spread')}x）",
                      "def": "控制变量看哪个因子(时段/时长/话题)对互动落差最大。"})
    for code, sub in (("c1", "全域加权健康"), ("c3", "带货+转化+承接"), ("c8", "私域成熟度")):
        sc = _g(s, code, "score")
        if sc is not None:
            items.append({"label": _LABEL[code], "sub": sub, "value": f"{sc} 分",
                          "def": f"{_LABEL[code]}综合评分(0-100)。"})
    if idn.get("consistency") is not None:
        items.append({"label": "形象一致性", "sub": "昵称×简介×内容×评论是否同一身份",
                      "value": f"{idn.get('consistency')} · {idn.get('self_match','')}",
                      "def": "对外人设与数据里真实的你是否匹配。"})
    return {"role": "evidence", "items": items} if items else None


# ── actions 进阶动作(专业方向 + 当前阶段五维该做 + cut 命令)──
def _actions(l3, journey) -> dict:
    items = []
    nxt = journey.get("next")
    gaps = journey.get("advance_gaps") or []
    # ① 战略方向(最高优先·指令5④)
    direction = journey.get("current_direction")
    if direction:
        why = ""
        if nxt and gaps:
            why = f"进【{nxt}】的硬条件：{gaps[0].split('·')[0]}。"
        items.append({"title": direction, "why": why, "priority": "战略方向·最高优先"})
    # ② 当前阶段五维该做(指令5①·链条式多维)
    for dim, act in (journey.get("current_dims") or {}).items():
        items.append({"title": f"【{dim}】{act}", "why": "", "priority": "本周·五维并进"})
    # ③ 兜底:若无 journey 维度,回退处方步骤
    if len(items) <= 1:
        front = l3.get("front") or {}
        for st in (_g(front, "tactic", "steps") or l3.get("this_week") or [])[:3]:
            items.append({"title": st, "why": "", "priority": "本周"})
    # ④ cut 命令摘要(给制作引擎·人话版)
    nc = _g(l3, "cut_commands", "next_clip") or {}
    if nc.get("post_window"):
        items.append({"title": f"下条按 MetaCut 参数拍：{nc.get('post_window')}发·"
                               f"{(nc.get('duration_s') or ['?','?'])}s·"
                               f"选题{('/'.join(nc.get('topic_tags') or []))}·{nc.get('cta','')}",
                      "why": "数据驱动的执行参数·可直接喂剪辑引擎",
                      "priority": "执行"})
    return {"role": "actions", "items": items} if items else None


# ── forecast 会怎样(能不能进下一站·时序+二阶导+轨迹+处方对照)──
def _forecast(l4, journey) -> dict:
    parts = []
    if l4.get("enough"):
        parts.append(f"内容时序：{l4.get('trend','')}·{l4.get('stage','')}")
    accel = l4.get("acceleration") or {}
    if accel.get("enough"):
        parts.append(f"势能二阶导：{accel.get('verdict','')}（{accel.get('implication','')[:24]}）")
    tj = l4.get("trajectory") or {}
    if tj.get("enough"):
        parts.append(f"账号轨迹：{tj.get('verdict','')}·{tj.get('detail','')}")
    rx = l4.get("rx_effect") or {}
    if rx.get("enough"):
        parts.append(f"处方对照：{rx.get('outcome','')}")
    nxt = journey.get("next")
    lead = (f"接通进阶条件能进【{nxt}】；不补则卡在【{journey.get('current','')}】。"
            if nxt else "按数据趋势推进。")
    if not parts:
        return {"role": "forecast", "lead": lead,
                "text": "时序导数与账号轨迹需更多作品/多次采集后给出（每次分析自动存档）。"}
    return {"role": "forecast", "lead": lead, "text": "；".join(parts) + "。"}


# ── scope 边界集中(N3+N5)──
def _scope(l2, s) -> dict:
    cav = []
    if _g(s, "c3", "missing"):
        cav.append("未开通星图，拿不到、未纳入评分：官方报价、带货/转化指数、粉丝消费力画像")
    anom = l2.get("engagement_anomaly") or {}
    if anom.get("enough"):
        cav.append(f"互动操纵只查了结构（{anom.get('verdict','')}），真实播放量是黑盒、未核查")
    cav.append("八维行业基准与部分阈值为经验值，待用 50–100 个真实账号建分位基线后校准")
    return {"role": "scope", "text": "。".join(cav) + "。"}


# ══════════════════════════════════════════════════════════════════════════════
# appendix 图表化深度(html·唯一放行图表/富文本的角色)·新 IA 六段
# ══════════════════════════════════════════════════════════════════════════════
def _appendix(l2, s, journey, basics, judges, bsum, causal) -> dict:
    from app.services import board_render as R, dimension_guide as DG
    parts = []

    # ① 账号基础数据:身份表 + 档位标尺判断表(指令1+3)
    parts.append(_basics_identity(basics))
    parts.append(_basics_judge_table(judges, bsum))

    # ② 内容→口碑→势能 因果链(指令2)
    parts.append(_causal_html(causal))

    # ③ 运营阶段:旅程图 + 阶段×维度矩阵 + 链条 + 评定依据(指令5)
    parts.append(_stage_html(journey, R))

    # ④ 八维:增强雷达(基准环/短板红) + 7层详解(指令4)
    parts.append(_dims_html(s, R, DG))

    # ⑤ 内容归因(柱状)+ 因子解释
    parts.append(_attribution_html(l2, R, DG))

    # ⑥ 评论实录(观众原话)
    parts.append(_comments_record(l2))

    return {"role": "appendix",
            "title": "展开完整数据（基础标尺 · 因果链 · 阶段矩阵 · 八维详解 · 归因 · 评论实录）",
            "html": "".join(p for p in parts if p)}


_H = "<div style='font-weight:700;color:#1E3A8A;margin:14px 0 5px;font-size:14px'>{}</div>"
_SUB = "<div style='font-size:11px;color:#9CA3AF;margin-bottom:4px'>{}</div>"


def _basics_identity(b) -> str:
    """身份类基础数据(非数值·指令3 全整理)。"""
    if not b:
        return ""
    rows = ""
    for lab, key in (("昵称", "nickname"), ("抖音号", "unique_id"), ("个人简介", "signature"),
                     ("属地", "ip_location"), ("个人认证", "custom_verify"),
                     ("企业认证", "enterprise_verify")):
        v = b.get(key)
        if v:
            rows += f"<tr><td style='white-space:nowrap;color:#6B7280'>{lab}</td><td>{str(v).replace(chr(10),' ')[:80]}</td></tr>"
    return (_H.format("账号基础数据 · 身份资料") + f"<table>{rows}</table>") if rows else ""


def _ruler(tiers) -> str:
    """档位标尺:几档·命中档高亮·flex-wrap+chip nowrap(防窄列逐字竖排)。"""
    chips = ""
    for t in tiers:
        hit = t.get("hit")
        col = _LV_COL.get(t.get("level"), "#9CA3AF")
        bg, fg, fw = (col, "#fff", "700") if hit else ("#F1F3F5", "#9CA3AF", "400")
        mark = "▶" if hit else ""
        chips += (f"<span style='white-space:nowrap;padding:2px 9px;border-radius:9px;"
                  f"background:{bg};color:{fg};font-weight:{fw};font-size:11px'>"
                  f"{mark}{t['name']}·{t['cond']}</span>")
    return f"<div style='display:flex;flex-wrap:wrap;gap:4px'>{chips}</div>"


def _basics_judge_table(judges, bsum) -> str:
    """基础数据档位标尺·卡片版(指令1:判断+依据+几档+目标)。

    用 div 卡片+flex-wrap 而非表格:表格 auto-layout 会把标尺列挤到逐字竖排。
    每卡:① 指标+值+当前档badge+目标(一行 flex-wrap) ② 档位标尺(flex-wrap) ③ 由什么决定。
    """
    if not judges:
        return ""
    cards = ""
    for j in judges:
        col = _LV_COL.get(j["level"], "#374151")
        cards += (
            "<div style='border:1px solid #E5E7EB;border-radius:8px;padding:9px 12px;margin:7px 0'>"
            "<div style='display:flex;flex-wrap:wrap;align-items:baseline;gap:8px'>"
            f"<b style='font-size:13px'>{j['label']}</b>"
            f"<span style='color:#374151'>{j['value']}</span>"
            f"<span style='background:{col};color:#fff;padding:1px 9px;border-radius:9px;"
            f"font-size:11px;font-weight:700'>{j['tier_now']}</span>"
            f"<span style='margin-left:auto;color:#6B7280;font-size:11px'>🎯 {j['target']}</span>"
            "</div>"
            f"<div style='margin:6px 0'>{_ruler(j['tiers'])}</div>"
            f"<div style='color:#9CA3AF;font-size:11px'>由什么决定:{j['decided_by']}</div>"
            "</div>")
    head = _SUB.format(bsum.get("line", "") + "·每项给『判断 + 由什么决定 + 几档 + 目标』")
    return (_H.format("账号基础数据 · 判断标尺（你在哪档 · 由什么决定 · 目标进哪档）") + head + cards)


def _causal_html(causal) -> str:
    """内容→口碑→势能 因果链图(指令2)。"""
    nodes = causal.get("nodes") or []
    if not nodes:
        return ""
    cards = []
    for i, nd in enumerate(nodes):
        bad = not nd.get("ok")
        border = "#DC2626" if bad else "#059669"
        bg = "#FEF2F2" if bad else "#F0FDF4"
        ms = "".join(f"<div style='font-size:11px;color:#6B7280'>{k}: {_n(v)}</div>"
                     for k, v in (nd.get("metrics") or {}).items() if v not in (None, [], ""))
        cards.append(
            f"<div style='flex:1;min-width:150px;border:1.5px solid {border};background:{bg};"
            f"border-radius:8px;padding:8px 10px'>"
            f"<div style='font-weight:700'>{nd.get('icon','')} {nd.get('stage','')}</div>"
            f"<div style='font-size:12px;color:#374151;margin:2px 0'>{nd.get('headline','')}</div>"
            f"<div style='font-size:11px;color:#6B7280'>{nd.get('detail','')[:48]}</div>{ms}</div>")
    arrow = "<div style='align-self:center;color:#9CA3AF;font-size:20px;padding:0 2px'>→</div>"
    flow = arrow.join(cards)
    verdict = causal.get("chain_verdict", "")
    vcol = "#DC2626" if causal.get("broken") else "#059669"
    return (_H.format("内容 → 口碑 → 势能 · 因果链（哪种内容带来口碑与势能 · 哪一环在漏）")
            + f"<div style='display:flex;gap:4px;flex-wrap:wrap;align-items:stretch'>{flow}</div>"
            + f"<div style='margin-top:6px;padding:7px 10px;border-left:3px solid {vcol};"
              f"background:#F8FAFC;font-size:12px;color:#374151'><b style='color:{vcol}'>链条结论</b>："
              f"{verdict}</div>"
            + _SUB.format(causal.get("value", "")))


def _stage_html(journey, R) -> str:
    """运营阶段:旅程图 + 阶段×维度矩阵 + 链条全景(指令5)。"""
    if not journey.get("nodes"):
        return ""
    out = _H.format("运营阶段旅程") + R._stepper(journey["nodes"]) \
        + f"<div style='font-size:12px;color:#374151'><b>{journey.get('verdict','')}</b></div>"
    # 当前阶段专业方向 + 五维该做(全文)+ 产出喂给下一站(链条)
    if journey.get("current_direction"):
        dims_li = "".join(f"<li><b>{d}</b>：{a}</li>"
                          for d, a in (journey.get("current_dims") or {}).items())
        out += (f"<div style='margin:6px 0;padding:8px 11px;background:#FFF7ED;border-left:3px solid #F59E0B;"
                f"font-size:12px'><b>当前站方向</b>：{journey['current_direction']}"
                f"<ul style='margin:5px 0 4px;padding-left:18px'>{dims_li}</ul>"
                f"<span style='color:#6B7280'>{journey.get('current_feeds','')}</span></div>")
    # 阶段×维度矩阵(完整架构·格内取首句作概览·全文见上方当前站)
    m = journey.get("matrix") or {}
    if m.get("rows"):
        icons = m.get("icons", {})
        th = "".join(f"<th>{icons.get(d,'')}{d}</th>" for d in m["dims"])
        body = ""
        for r in m["rows"]:
            st = r["state"]
            mark = {"done": "✓", "current": "▶", "future": "○"}[st]
            rbg = "background:#EFF6FF" if st == "current" else ""
            cells = "".join(f"<td style='font-size:11px;{rbg}'>{(c or '—').split('·')[0]}</td>"
                            for c in r["cells"])
            nm = f"{mark} {r['stage']}<br><span style='color:#9CA3AF;font-size:10px'>{r['chain']}</span>"
            body += f"<tr style='{rbg}'><td style='white-space:nowrap;font-weight:{'700' if st=='current' else '400'}'>{nm}</td>{cells}</tr>"
        out += (_H.format("阶段 × 维度矩阵 · 完整运营架构（链条：" + journey.get("chain_name", "") + "）")
                + _SUB.format("格内取核心动作概览·当前站全文见上方")
                + f"<table><tr><th>阶段 / 链条环</th>{th}</tr>{body}</table>"
                + _SUB.format(m.get("compliance", "")))
    # 评定依据
    crit = journey.get("criteria") or {}
    if crit.get("dims"):
        rows = "".join(f"<tr><td>{d['dim']}</td><td>{d['value']}</td>"
                       f"<td style='color:#6B7280;font-size:11px'>{d['why']}</td></tr>"
                       for d in crit["dims"])
        out += (_SUB.format("阶段评定依据：" + crit.get("note", ""))
                + f"<table><tr><th>评定维度</th><th>你的值</th><th>为什么看它</th></tr>{rows}</table>"
                + _SUB.format("出处：" + crit.get("source", "")))
    return out


def _dims_html(s, R, DG) -> str:
    """八维:增强雷达(基准环/短板红/轴值) + 7层详解(指令4)。"""
    items = DG.radar_items(s)               # (label, value, benchmark)
    out = ""
    if len(items) >= 3:
        out += (_H.format("账号八维雷达（实线=你 · 橙虚线=行业基准 · 红▼=最该补的短板）")
                + f"<div style='text-align:center'>{R._radar(items)}</div>")
    dims = DG.all_dims(s)                    # 按分升序·最弱在前
    rows = ""
    for d in dims:
        col = _LV_COL.get(d["level"], "#374151")
        vs = d.get("vs_bench") or ""
        rows += (
            f"<tr><td style='white-space:nowrap'><b>{d['name']}</b>"
            f"<br><span style='color:#9CA3AF;font-size:10px'>{d['what'][:22]}</span></td>"
            f"<td style='text-align:center;font-weight:700;color:{col}'>{_n(d['score'])}"
            f"<br><span style='font-size:10px;color:#9CA3AF'>{d['zone']}</span></td>"
            f"<td style='font-size:11px;color:#6B7280'>{vs}<br>基准{_n(d.get('bench'))}</td>"
            f"<td style='font-size:11px'>{d['impact'][:28]}</td>"
            f"<td style='font-size:11px;color:#374151'>{d['lever'][:24]}</td></tr>")
    out += (_H.format("八维 7 层详解（按分升序 · 先补短板 · 每维:是什么/分/对标/影响/最快杠杆）")
            + "<table><tr><th>维度</th><th>分/档</th><th>对标基准</th><th>影响什么</th>"
              "<th>最快杠杆</th></tr>" + rows + "</table>"
            + _SUB.format("行业基准为经验值·待 50–100 真实账号建分位基线后校准"))
    return out


def _attribution_html(l2, R, DG) -> str:
    attr = l2.get("attribution") or {}
    if not (attr.get("enough") and attr.get("factors")):
        return ""
    out = (_H.format("内容归因 · 因子驱动力（组间落差倍数）")
           + R._bars([(f["factor"], f["spread"]) for f in attr["factors"][:5]], color="#0891B2"))
    exp = "".join(f"<li><b>{f['factor']}</b>（落差 {f['spread']}x）：{DG.ATTR_GUIDE.get(f['factor'],'')}</li>"
                  for f in attr["factors"][:4] if DG.ATTR_GUIDE.get(f["factor"]))
    out += (f"<div style='font-size:12px;color:#374151'>{DG.ATTR_SPREAD_DEF}</div>"
            f"<ul style='font-size:12px;color:#374151'>{exp}</ul>")
    return out


def _comments_record(l2) -> str:
    hot = l2.get("hot_comments") or {}
    top = hot.get("top") or []
    if not top:
        return ""
    rows = "".join(f"<tr><td style='color:#6B7280;white-space:nowrap'>{h.get('digg',0)}赞</td>"
                   f"<td>{(h.get('text') or '')[:48]}</td></tr>" for h in top[:8])
    return (_H.format("评论实录（观众原话 · 按热度）")
            + f"<table><tr><th>热度</th><th>评论</th></tr>{rows}</table>"
            + _SUB.format("采样非全量·热评经平台算法排序"))

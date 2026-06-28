"""契约对接桥 · contract_adapter.py · probe 分析 → MetaForm 自适应输出契约 doc。

对方窗口(MetaForm account-diagnosis 场景·render_contract 引擎)实施渲染;本模块只产
**契约 doc**(meta + blocks·语义角色),不动对方引擎/场景/schema(尊重边界)。

契约角色(block_roles.yaml·account-diagnosis 必填 verdict/key_issue/evidence/actions/scope):
  verdict   脊柱(一句话定性·N1唯一)        ← 战略判断
  situation 处境(你是什么→成为什么)         ← 定位航向 + 形象一致性
  key_issue 最该一件事(因果流+热评+收口)    ← top_concern + 诊断链口碑层 + 承接断点
  evidence  证据(人话标签·非C代号·N6)       ← 关键指标/信号(翻成人话)
  actions   本周做(带优先级)                ← 处方前端三级 + cut 命令摘要
  forecast  会怎样                          ← 时序+轨迹+处方对照
  scope     边界集中(拿不到什么·N3/N5)      ← 未开星图/黑盒/待校准
  appendix  深度展开(html)                  ← 八维雷达/五段拆解/聚类
不变量:N6 内部代号(C1/C9)不进客户版→指标一律人话标签;show_accounting 默认 false。
"""
from __future__ import annotations

from typing import Any

# C 代号 → 人话标签(N6:客户版禁出 C1/C9)
_LABEL = {"c1": "健康", "c2": "粉丝质量", "c3": "商业转化", "c4": "内容力",
          "c5": "赛道", "c6": "破圈", "c7": "评级", "c8": "私域"}
_COMPLIANCE = "数据源合规授权 · 国内不出境"


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
    track = _g(l1, "heading") or {}
    idn = l1.get("identity") or {}

    meta = {
        "subject_name": nick, "platform": "抖音",
        "subtitle": _track_subtitle(l1),
        "fans": board_follower(board),
        "grade": _g(s, "c7", "grade"),
        "health_score": _g(s, "c1", "score"),
        "show_accounting": False,            # N6:对外纯诊断·算账走内部
        "compliance": _COMPLIANCE,
    }

    journey = board.get("journey") or {}
    basics = board.get("basics") or {}
    blocks = [
        _verdict(l3, l1),
        _situation(l1, idn, journey),
        _key_issue(l2, l4),
        _evidence(s, l2, l4, idn),
        _actions(l3, journey),
        _forecast(l4, journey),
        _scope(l2, s),
        _appendix(l2, s, journey, basics),
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


# ── situation 处境(你在旅程哪一站·已走/接下来)+ 形象一致性 ──
def _situation(l1, idn, journey) -> dict:
    h = l1.get("heading") or {}
    cur = journey.get("current", "")
    done = journey.get("done") or []
    fut = journey.get("future") or []
    lead = (f"你在运营旅程的【{cur}】" +
            (f"，已走过 {'、'.join(done)}" if done else "") +
            (f"，接下来 {'、'.join(fut[:2])}" if fut else "") + "。")
    # 进阶规划 + 航向终态 + 形象一致性(文字精简·细节进 appendix 图)
    txt = journey.get("verdict", "")
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


# ── evidence 证据(人话标签·非C代号·N6)──
def _evidence(s, l2, l4, idn) -> dict:
    items = []
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
    # 关键分(人话标签)
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


# ── actions 进阶动作(锚定阶段进阶·带优先级)+ cut 命令 ──
def _actions(l3, journey) -> dict:
    front = l3.get("front") or {}
    steps = _g(front, "tactic", "steps") or l3.get("this_week") or []
    items = []
    # 进阶动作:把本周动作锚定到"从当前站进下一站"
    nxt = journey.get("next")
    gaps = journey.get("advance_gaps") or []
    strat = _g(front, "strategy", "text")
    if strat:
        why = _g(front, "strategy", "why", default="")[:50]
        if nxt and gaps:
            why = f"这是进【{nxt}】的硬条件：{gaps[0].split('·')[0]}。" + why
        items.append({"title": strat, "why": why, "priority": "最高优先·进阶关键"})
    for st in steps[:3]:
        items.append({"title": st, "why": "", "priority": "本周"})
    # cut 命令摘要(给制作引擎·人话版)
    nc = _g(l3, "cut_commands", "next_clip") or {}
    if nc.get("post_window"):
        items.append({"title": f"下条按 MetaCut 参数拍：{nc.get('post_window')}发·"
                               f"{(nc.get('duration_s') or ['?','?'])}s·"
                               f"选题{('/'.join(nc.get('topic_tags') or []))}·{nc.get('cta','')}",
                      "why": "数据驱动的执行参数·可直接喂剪辑引擎",
                      "priority": "执行"})
    return {"role": "actions", "items": items} if items else None


# ── forecast 会怎样(能不能进下一站·时序+轨迹+处方对照)──
def _forecast(l4, journey) -> dict:
    parts = []
    if l4.get("enough"):
        parts.append(f"内容时序：{l4.get('trend','')}·{l4.get('stage','')}")
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
    # ⚠️ render_contract 对 scope.text 转义→禁 html 标签·纯文本(N3 边界集中)
    cav = []
    if _g(s, "c3", "missing"):
        cav.append("未开通星图，拿不到、未纳入评分：官方报价、带货/转化指数、粉丝消费力画像")
    anom = l2.get("engagement_anomaly") or {}
    if anom.get("enough"):
        cav.append(f"互动操纵只查了结构（{anom.get('verdict','')}），真实播放量是黑盒、未核查")
    cav.append("部分阈值为经验值，待用 50–100 个真实账号建分位基线后校准")
    return {"role": "scope", "text": "。".join(cav) + "。"}


# ── appendix 图表化+详解深度(html·唯一放行图表/富文本的角色)──
# 补:账号基础数据(指令3)·评论实录(指令3)·8维详解是什么+怎么提高(指令4)·归因解释(指令5)
def _appendix(l2, s, journey, basics) -> dict:
    from app.services import board_render as R, dimension_guide as DG
    _h = "<div style='font-weight:700;color:#1E3A8A;margin:12px 0 4px'>{}</div>"
    parts = []

    # ① 账号基础数据(指令3·给用户信息与参考)
    parts.append(_basics_table(basics))

    # ② 运营阶段旅程图 + 评定依据(指令1)
    if journey.get("nodes"):
        parts.append(_h.format("运营阶段旅程") + R._stepper(journey["nodes"])
                     + f"<div style='font-size:12px;color:#374151'>{journey.get('verdict','')}</div>")
        crit = journey.get("criteria") or {}
        if crit.get("dims"):
            rows = "".join(f"<tr><td>{d['dim']}</td><td>{d['value']}</td>"
                           f"<td style='color:#6B7280;font-size:12px'>{d['why']}</td></tr>"
                           for d in crit["dims"])
            parts.append("<div style='font-size:12px;color:#6B7280;margin-top:4px'>阶段评定依据："
                         + crit.get("note", "") + "</div>"
                         + f"<table><tr><th>评定维度</th><th>你的值</th><th>为什么看它</th></tr>{rows}</table>"
                         + f"<div style='font-size:11px;color:#9CA3AF'>出处：{crit.get('source','')}</div>")

    # ③ 账号八维雷达 + 每维详解(是什么/怎么提高)(指令4)
    radar = l2.get("radar") or {}
    items = [(_LABEL.get(r["key"].lower(), r["label"]), r["score"])
             for r in (radar.get("account_self") or []) if r.get("score") is not None]
    if len(items) >= 3:
        parts.append(_h.format("账号八维（外环强/内缩弱）") + R._radar(items))
    dims = DG.all_dims(s)
    dim_rows = "".join(
        f"<tr><td><b>{d['name']}</b><br><span style='color:#6B7280;font-size:11px'>{d['what']}</span></td>"
        f"<td style='text-align:center;font-weight:700;color:{_dim_col(d['score'])}'>{_n(d['score'])}</td>"
        f"<td style='font-size:12px'>{d['how']}</td></tr>" for d in dims)
    parts.append(_h.format("八维详解 · 是什么 + 怎么提高（按分升序·先补短板）")
                 + f"<table><tr><th>维度</th><th>分</th><th>怎么提高</th></tr>{dim_rows}</table>")

    # ④ 关键指标 vs 行业基准(子弹图)
    bullets = ""
    for code, bm, lab in (("c1", 55, "健康"), ("c3", 40, "商业转化"), ("c4", 50, "内容力")):
        sc = _g(s, code, "score")
        if sc is not None:
            bullets += R._bullet(sc, bm, label=lab)
    if bullets:
        parts.append(_h.format("关键指标 vs 行业基准") + bullets)

    # ⑤ 内容归因(柱状)+ 因子解释(指令5)
    attr = l2.get("attribution") or {}
    if attr.get("enough") and attr.get("factors"):
        parts.append(_h.format("内容归因·因子驱动力")
                     + R._bars([(f["factor"], f["spread"]) for f in attr["factors"][:5]], color="#0891B2"))
        exp = "".join(f"<li><b>{f['factor']}</b>（落差 {f['spread']}x）：{DG.ATTR_GUIDE.get(f['factor'],'')}</li>"
                      for f in attr["factors"][:4] if DG.ATTR_GUIDE.get(f["factor"]))
        parts.append(f"<div style='font-size:12px;color:#374151'>{DG.ATTR_SPREAD_DEF}</div>"
                     f"<ul style='font-size:12px;color:#374151'>{exp}</ul>")

    # ⑥ 评论实录(指令3·真实原话·观众想什么)
    parts.append(_comments_record(l2))

    return {"role": "appendix",
            "title": "展开完整数据（基础资料 · 阶段依据 · 八维详解 · 指标基准 · 归因解释 · 评论实录）",
            "html": "".join(p for p in parts if p)}


def _basics_table(b) -> str:
    if not b:
        return ""
    rows = ""
    for lab, key, suf in (("昵称", "nickname", ""), ("抖音号", "unique_id", ""),
                          ("个人简介", "signature", ""), ("属地", "ip_location", ""),
                          ("个人认证", "custom_verify", ""), ("企业认证", "enterprise_verify", ""),
                          ("粉丝数", "follower", ""), ("历史峰值粉丝", "max_follower", ""),
                          ("作品数", "aweme_count", ""), ("获赞总数", "total_favorited", ""),
                          ("关注数", "following_count", ""),
                          ("均赞", "avg_like", ""), ("最高赞", "max_like", "")):
        v = b.get(key)
        if v:
            vv = str(v).replace("\n", " ")[:70]
            rows += f"<tr><td style='white-space:nowrap'>{lab}</td><td>{vv}{suf}</td></tr>"
    return ("<div style='font-weight:700;color:#1E3A8A;margin:6px 0 4px'>账号基础数据</div>"
            f"<table>{rows}</table>") if rows else ""


def _comments_record(l2) -> str:
    hot = l2.get("hot_comments") or {}
    top = hot.get("top") or []
    if not top:
        return ""
    rows = "".join(f"<tr><td style='color:#6B7280'>{h.get('digg',0)}赞</td>"
                   f"<td>{(h.get('text') or '')[:48]}</td></tr>" for h in top[:8])
    return ("<div style='font-weight:700;color:#1E3A8A;margin:12px 0 4px'>评论实录（观众原话·按热度）</div>"
            f"<table><tr><th>热度</th><th>评论</th></tr>{rows}</table>"
            "<div style='font-size:11px;color:#9CA3AF'>采样非全量·热评经平台算法排序</div>")


def _dim_col(sc) -> str:
    if sc is None:
        return "#9CA3AF"
    return "#DC2626" if sc < 40 else ("#D97706" if sc < 60 else "#059669")

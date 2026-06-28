"""元板分层渲染 · 三屏层次呈现 (HTML / Markdown)。

把 board.build_board 的四级坐标下钻数据,渲染成「结论前置 → 四层下钻 → 诊断处方」
三屏层次的自包含 HTML(破晓品牌色·响应式)。承 v3.2 输出层次:
  第一屏 一句话结论(进门即看)
  第二屏 四层下钻(环境→行业→账号→单条·zoom·每层带算账)
  第三屏 诊断卡处方(每卡 问题→结论→证据→处方)
颜色全部取自 metaform/base.yaml 品牌真源(brand_blue/orange/ink)。
"""
from __future__ import annotations

from typing import Any

# 破晓品牌色(= 运营报告/metaform/base.yaml · packages/ui/tokens/tokens-brand.css)
_BLUE = "#1E3A8A"
_ORANGE = "#FF7A1A"
_ORANGE_CTA = "#C2540F"
_INK = "#1F2937"
_ZEBRA = "#EFF6FF"

_SEV_COLOR = {"red": "#DC2626", "yellow": "#D97706", "green": "#059669", None: "#6B7280"}
_SEV_LABEL = {"red": "🔴", "yellow": "🟡", "green": "🟢", None: "⚪"}

# ── MetaForm 溯源戳(承 Q6-L55:交付物须带"身份证"·必须过统一输出)──
# 元板是 MetaForm 认可的交付类产物(format=metaboard·引擎在本服务),
# 输出须自带戳,方能过 运营报告/metaform/gate-output.py 的输出范围闸。
_BOARD_VER = "3.2"


def _metaform_stamp(fmt: str) -> str:
    """生成 MetaForm 溯源戳字符串(与 metaform/lib/stamp.py 同构)。"""
    return (f"scenario=metaboard;format={fmt};template=four-layer-drilldown;"
            f"renderer=board_render;engine=metaboard;board_ver={_BOARD_VER};v=1")


def _n(v, suffix="", dash="—"):
    return f"{v}{suffix}" if v is not None else dash


# ══════════════════════════════════════════════════════════════════════════════
# v2.0 价值阶梯渲染(描述→诊断→处方→预测)·第一屏=完整答案·正文渐进折叠
# ══════════════════════════════════════════════════════════════════════════════

_RUNG_COLOR = {1: "#6B7280", 2: "#D97706", 3: "#059669", 4: "#DC2626"}
_RUNG_ICON = {1: "①", 2: "②", 3: "③", 4: "④"}


def render_ladder_html(board: dict[str, Any]) -> str:
    nick = board.get("nickname") or "该账号"
    L = board.get("ladders") or {}
    h = board.get("headline") or {}
    acc = board.get("accounting") or {}
    parts = [_ladder_head(nick),
             _ladder_answer_screen(nick, L, h),     # 第一屏:完整答案(4阶梯结论)
             _ladder_detail(L.get("l1"), _desc_body),
             _ladder_detail(L.get("l2"), _diag_body),
             _ladder_detail(L.get("l3"), _rx_body),
             _ladder_detail(L.get("l4"), _pred_body),
             _screen_accounting(acc),
             _ladder_foot()]
    return "\n".join(parts)


def _ladder_head(nick: str) -> str:
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>元板 v2.0 · {nick} · 价值阶梯</title>
<style>
  *{{box-sizing:border-box}}
  body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
       color:{_INK};line-height:1.65;margin:0;background:#F8FAFC}}
  .wrap{{max-width:860px;margin:0 auto;padding:16px}}
  h1{{font-size:21px;color:{_BLUE};margin:.2em 0}}
  .answer{{background:linear-gradient(135deg,{_BLUE},#2747a8);color:#fff;
          border-radius:16px;padding:22px 24px;margin:14px 0}}
  .answer .tag{{font-size:12px;opacity:.85}}
  .rung-line{{display:flex;align-items:flex-start;gap:10px;padding:11px 0;
             border-bottom:1px solid rgba(255,255,255,.14)}}
  .rung-line:last-child{{border-bottom:none}}
  .rung-badge{{flex:none;width:54px;font-size:12px;font-weight:700;opacity:.9;padding-top:2px}}
  .rung-q{{font-size:11.5px;opacity:.7;margin-bottom:2px}}
  .rung-c{{font-size:15px;font-weight:700}}
  .rung-c.call{{color:{_ORANGE};font-size:16px}}
  details{{background:#fff;border-radius:12px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.06);
          overflow:hidden}}
  summary{{padding:14px 18px;cursor:pointer;font-weight:700;font-size:15px;list-style:none;
          display:flex;align-items:center;gap:8px}}
  summary::-webkit-details-marker{{display:none}}
  summary .moat{{margin-left:auto;font-size:11px;font-weight:400;padding:2px 9px;border-radius:9px}}
  summary .badge{{font-size:13px;color:#fff;width:24px;height:24px;border-radius:50%;
                 display:inline-flex;align-items:center;justify-content:center;flex:none}}
  .body{{padding:0 18px 16px}}
  .concl{{font-size:14px;background:{_ZEBRA};border-radius:8px;padding:9px 12px;margin:4px 0 10px}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;margin:6px 0}}
  th{{background:{_BLUE};color:#fff;text-align:left;padding:6px 9px}}
  td{{padding:5px 9px;border-bottom:1px solid #EEF2F7}}
  tr:nth-child(even) td{{background:{_ZEBRA}}}
  ul{{margin:.3em 0;padding-left:1.2em}} li{{margin:.22em 0;font-size:13px}}
  .five{{border:1px dashed {_BLUE}33;border-radius:9px;padding:9px 12px;margin:7px 0;background:#FAFBFF}}
  .five .k{{font-weight:700;color:{_BLUE}}}
  .impl{{font-size:13px;background:#FFF7ED;border-radius:8px;padding:7px 10px;margin-top:5px}}
  .acc-total{{font-size:26px;font-weight:800;color:{_ORANGE}}}
  .screen{{background:#fff;border-radius:12px;padding:18px 22px;margin:12px 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
  .screen-tag{{display:inline-block;font-size:12px;color:#fff;background:{_BLUE};padding:3px 10px;border-radius:10px;margin-bottom:10px}}
  h2{{font-size:16px;color:{_BLUE}}} .note{{font-size:12px;color:#6B7280}}
  .pending{{color:#9CA3AF;font-style:italic}}
</style></head><body><div class="wrap">
<h1>元板 v2.0 · {nick}</h1>
<p class="note" style="margin-top:-4px">价值阶梯 · 描述 → 诊断 → 处方 → 预测 · 第一屏即完整答案,余下按需展开</p>"""


def _ladder_answer_screen(nick: str, L: dict, h: dict) -> str:
    """第一屏 = 完整答案:4 阶梯结论一句话堆叠(进门即看·不用滚)。"""
    sc = h.get("strategic_call") or {}
    def line(rung, q, concl, is_call=False):
        cls = "rung-c call" if is_call else "rung-c"
        return (f'<div class="rung-line"><div class="rung-badge">{_RUNG_ICON[rung]} {("描述","诊断","处方","预测")[rung-1]}</div>'
                f'<div><div class="rung-q">{q}</div><div class="{cls}">{concl}</div></div></div>')
    l1, l2, l3, l4 = L.get("l1") or {}, L.get("l2") or {}, L.get("l3") or {}, L.get("l4") or {}
    pred = (l4.get("conclusion") if l4.get("enough")
            else f'<span class="pending">{l4.get("conclusion", "积累中")}</span>')
    return f"""<div class="answer">
  <div class="tag">🎯 一眼答案(四阶梯结论)</div>
  {line(1, l1.get('question',''), l1.get('conclusion',''))}
  {line(2, l2.get('question',''), l2.get('conclusion',''))}
  {line(3, l3.get('question',''), l3.get('conclusion',''), is_call=True)}
  {line(4, l4.get('question',''), pred)}
</div>"""


def _ladder_detail(ld: dict | None, body_fn) -> str:
    if not ld:
        return ""
    rung = ld.get("rung", 1)
    col = _RUNG_COLOR.get(rung, "#6B7280")
    moat = ld.get("moat", "")
    moat_bg = {"竞品也能做": "#EFF6FF", "竞品部分能做": "#FFFBEB"}.get(moat, "#FEF2F2")
    moat_fg = {"竞品也能做": "#1E3A8A", "竞品部分能做": "#D97706"}.get(moat, "#DC2626")
    open_attr = "open" if rung in (3, 4) else ""   # 处方/预测默认展开(最值钱)
    return f"""<details {open_attr}><summary>
  <span class="badge" style="background:{col}">{_RUNG_ICON[rung]}</span>
  阶梯{rung}·{ld.get('name')}({ld.get('question')})
  <span class="moat" style="background:{moat_bg};color:{moat_fg}">{moat}</span></summary>
  <div class="body"><div class="concl">{ld.get('conclusion','')}</div>{body_fn(ld)}</div></details>"""


def _desc_body(ld: dict) -> str:
    lis = "".join(f"<li>{d}</li>" for d in (ld.get("details") or []))
    src = f'<div class="note">出处:{ld.get("source")}</div>' if ld.get("source") else ""
    return f"<ul>{lis}</ul>{src}"


def _diag_body(ld: dict) -> str:
    out = ""
    tc = ld.get("top_concern") or {}
    if tc.get("title"):
        out += (f'<div class="impl">⚠️ 最该关注:{_SEV_LABEL.get(tc.get("severity"))} '
                f'{tc.get("title")} — {tc.get("what","")}</div>')
    out += _five(ld.get("deep_health"), "健康分·深度拆解")
    out += _five(ld.get("deep_commerce"), "商业转化·为什么这个分")
    # 诊断卡简表
    cards = [x for x in (ld.get("details") or []) if x]
    if cards:
        rows = "".join(f'<tr><td>{_SEV_LABEL.get(x.get("severity"))} {x.get("title")}</td>'
                       f'<td>{x.get("conclusion","")}</td></tr>' for x in cards)
        out += f'<table><tr><th>诊断卡</th><th>结论</th></tr>{rows}</table>'
    return out


def _rx_body(ld: dict) -> str:
    out = ""
    if ld.get("strategic_why"):
        col = _SEV_COLOR.get(ld.get("strategic_color"), "#059669")
        out += (f'<div style="background:{col};color:#fff;border-radius:9px;padding:10px 13px;margin-bottom:8px">'
                f'<b>🎯 {ld.get("conclusion")}</b><br><span style="font-size:12.5px;opacity:.95">{ld.get("strategic_why")}</span></div>')
    week = ld.get("this_week") or []
    if week:
        out += '<div style="font-weight:700;color:#059669;margin:6px 0 3px">📌 本周做这几件</div>'
        out += '<ol style="padding-left:1.3em;font-size:13px">' + "".join(f"<li>{w}</li>" for w in week) + "</ol>"
    if ld.get("audience_intent"):
        out += f'<div class="impl">💰 {ld.get("audience_implication","")}</div>'
    return out


def _pred_body(ld: dict) -> str:
    out = ""
    # 内容时序(单次可算)
    if ld.get("enough"):
        rows = []
        for label, key in (("阶段", "stage"), ("互动趋势", "trend"), ("更新节奏", "rhythm"),
                           ("爆款衰减", "decay")):
            if ld.get(key):
                rows.append(f"<tr><td>{label}</td><td>{ld[key]}</td></tr>")
        ne = ld.get("next_estimate")
        if ne:
            rows.append(f'<tr><td>下条预估</td><td>赞约 {ne.get("like_median")}'
                        f'(区间 {ne.get("like_range",["?","?"])[0]}-{ne.get("like_range",["?","?"])[1]})·'
                        f'<span class="note">{ne.get("note","")}</span></td></tr>')
        out += (f'<div style="font-weight:700;color:{_BLUE};margin:4px 0">内容时序(单次可算)</div>'
                f'<table><tr><th>维度</th><th>判定</th></tr>{"".join(rows)}</table>')
        if ld.get("rx_eta"):
            out += f'<div class="impl">⚡ {ld.get("rx_eta")}</div>'
    else:
        out += f'<div class="impl">⏳ 内容时序:{ld.get("conclusion")}</div>'
    # 账号轨迹(跨次采集·完整B)
    out += _trajectory_block(ld.get("trajectory"))
    # 处方前后对照(证明建议有没有用)
    out += _rx_effect_block(ld.get("rx_effect"))
    out += f'<div class="note">置信:{ld.get("conf","—")}·内容时序单次可算·账号轨迹+处方对照靠累积</div>'
    return out


def _rx_effect_block(rx: dict | None) -> str:
    if not rx:
        return ""
    head = '<div style="font-weight:700;color:#7C3AED;margin:8px 0 4px">处方前后对照(建议有没有用)</div>'
    if not rx.get("enough"):
        return head + f'<div class="impl" style="background:#F5F3FF">⏳ {rx.get("verdict")}</div>'
    steps = "、".join(rx.get("rx_steps") or [])
    return (head + f'<table><tr><th>项</th><th>真实对照</th></tr>'
            f'<tr><td>处方日</td><td>{rx.get("rx_date")}·建议「{rx.get("rx_call","")}」</td></tr>'
            f'<tr><td>{rx.get("days_since")}天后</td><td>{("·".join(rx.get("metric_moves") or []))}</td></tr>'
            f'<tr><td>结果</td><td><b>{rx.get("outcome","")}</b></td></tr></table>'
            + (f'<div class="note">当时建议步骤:{steps}</div>' if steps else "")
            + f'<div class="note">{rx.get("note","")}</div>')


def _trajectory_block(tj: dict | None) -> str:
    if not tj:
        return ""
    head = f'<div style="font-weight:700;color:#DC2626;margin:8px 0 4px">账号轨迹(跨次采集·真实历史)</div>'
    if not tj.get("enough"):
        return head + f'<div class="impl">⏳ {tj.get("verdict")}</div>'
    rows = f'<tr><td>涨粉判定</td><td><b>{tj.get("verdict")}</b></td></tr>'
    rows += f'<tr><td>轨迹</td><td>{tj.get("detail","")}</td></tr>'
    if tj.get("like_trend"):
        rows += f'<tr><td>互动趋势</td><td>{tj["like_trend"]}</td></tr>'
    if tj.get("health_trend"):
        rows += f'<tr><td>健康趋势</td><td>{tj["health_trend"]}</td></tr>'
    path = tj.get("follower_path") or []
    path_str = " → ".join(f"{d}:{f}" for d, f in path)
    return (head + f'<table><tr><th>维度</th><th>真实历史</th></tr>{rows}</table>'
            f'<div class="note">📍 {path_str}</div>'
            f'<div class="note">{tj.get("note","")}·快照 {tj.get("snapshots")} 个</div>')


def _five(d: dict | None, title: str) -> str:
    if not d:
        return ""
    rows = f'<div class="k">{title}</div>'
    if d.get("conclusion"):
        rows += f'<div style="font-size:13px"><b>结论:</b>{d["conclusion"]}</div>'
    for lab, key in (("拆解", "breakdown"), ("依据", "evidence")):
        items = d.get(key)
        if items:
            rows += (f'<div style="font-size:12px"><b>{lab}:</b>'
                     + "、".join(str(x) for x in items[:4]) + "</div>")
    if d.get("benchmark"):
        rows += f'<div style="font-size:12px;color:#6B7280">📐 基准:{d["benchmark"]}</div>'
    if d.get("implication"):
        rows += f'<div class="impl" style="font-size:12.5px">💡 {d["implication"]}</div>'
    return f'<div class="five">{rows}</div>'


def _ladder_foot() -> str:
    return ('<p class="note" style="text-align:center;margin:18px 0">'
            '元板 MetaBoard v2.0 · 价值阶梯交付 · 数据合规授权·国内不出境 · '
            '阶梯4 时序导数=单次采集可算·账号轨迹需多次采集(积累中)</p></div></body></html>')


def _score_bar(score, width=120):
    """画一个分值条(0-100)。"""
    if score is None:
        return f'<span style="color:#9CA3AF">待数据</span>'
    pct = max(0, min(100, float(score)))
    col = _ORANGE if pct < 50 else (_BLUE if pct < 75 else "#059669")
    return (f'<span style="display:inline-block;width:{width}px;height:8px;'
            f'background:#E5E7EB;border-radius:4px;vertical-align:middle;overflow:hidden">'
            f'<span style="display:block;width:{pct}%;height:100%;background:{col}"></span></span>'
            f'<b style="margin-left:8px;color:{_INK}">{round(pct)}</b>')


# ══════════════════════════════════════════════════════════════════════════════
def render_board_html(board: dict[str, Any]) -> str:
    nickname = board.get("nickname") or "该账号"
    h = board.get("headline") or {}
    layers = board.get("layers") or {}
    acc = board.get("accounting") or {}

    parts = [_html_head(nickname),
             _screen1_headline(nickname, h),
             _screen2_drilldown(layers, acc),
             _screen3_cards(layers),
             _screen_accounting(acc),
             _screen_coverage(board.get("data_coverage")),
             _html_foot()]
    return "\n".join(parts)


def _screen_coverage(cov: dict | None) -> str:
    """数据覆盖诚实账:新接入了哪些·哪些空(原因)·哪些冗余。"""
    if not cov:
        return ""
    shown = cov.get("new_signals_shown") or []
    empty = cov.get("empty_this_account") or []
    redun = cov.get("redundant_or_niche") or []
    shown_html = "".join(f'<span class="chip" style="background:#ECFDF5;color:#059669">{s}</span> '
                         for s in shown) or "（无）"
    empty_html = "".join(f"<tr><td>{e['ep']}</td><td style='color:#9CA3AF'>{e['reason']}</td></tr>"
                         for e in empty)
    redun_html = "".join(f"<tr><td>{e['ep']}</td><td style='color:#9CA3AF'>{e['reason']}</td></tr>"
                         for e in redun)
    return f"""<div class="screen"><span class="screen-tag">数据覆盖 · 诚实账(采集→展示)</span>
<h2>本轮新接入并展示({len(shown)} 项·原采集未展示)</h2>
<div style="line-height:2.2">{shown_html}</div>
<h2>此账号空返回(诚实标原因·不编造)</h2>
<table><tr><th>端点</th><th>为什么空</th></tr>{empty_html}</table>
<h2>冗余/小众(不单列)</h2>
<table><tr><th>端点</th><th>原因</th></tr>{redun_html}</table>
<div class="note">{cov.get('note','')}</div>
</div>"""


def _html_head(nickname: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-metaform" content="{_metaform_stamp('html')}">
<title>元板 · {nickname} · 四层下钻数据板块</title>
<style>
  :root {{ --blue:{_BLUE}; --orange:{_ORANGE}; --ink:{_INK}; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
         color:{_INK}; line-height:1.6; margin:0; background:#F8FAFC; }}
  .wrap {{ max-width:920px; margin:0 auto; padding:16px; }}
  .screen {{ background:#fff; border-radius:14px; padding:22px 24px; margin:16px 0;
            box-shadow:0 1px 3px rgba(0,0,0,.06); }}
  .screen-tag {{ display:inline-block; font-size:12px; color:#fff; background:{_BLUE};
                padding:3px 10px; border-radius:10px; margin-bottom:14px; }}
  h1 {{ font-size:22px; color:{_BLUE}; margin:.2em 0; }}
  h2 {{ font-size:17px; color:{_BLUE}; border-left:4px solid {_ORANGE};
       padding-left:10px; margin:1em 0 .6em; }}
  .headline-box {{ background:linear-gradient(135deg,{_BLUE},#2747a8); color:#fff;
                  border-radius:12px; padding:20px 22px; }}
  .headline-box .score {{ font-size:40px; font-weight:800; color:{_ORANGE}; }}
  .concern {{ background:rgba(255,255,255,.12); border-radius:10px; padding:12px 14px;
             margin-top:12px; }}
  .layer {{ border:1px solid #E5E7EB; border-radius:12px; padding:16px 18px;
           margin:12px 0; position:relative; }}
  .layer .coord {{ font-size:16px; font-weight:700; color:{_BLUE}; }}
  .layer .zoom {{ font-size:13px; color:#6B7280; margin-left:8px; }}
  .layer .q {{ font-size:13px; color:#374151; font-style:italic; margin:6px 0 10px; }}
  .cost-chip {{ position:absolute; top:16px; right:18px; font-size:12px;
               background:{_ZEBRA}; color:{_BLUE}; padding:3px 10px; border-radius:10px;
               font-weight:700; }}
  .kv {{ display:flex; flex-wrap:wrap; gap:6px 24px; font-size:14px; margin:4px 0; }}
  .kv .k {{ color:#6B7280; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; margin:8px 0; }}
  th {{ background:{_BLUE}; color:#fff; text-align:left; padding:7px 10px; }}
  td {{ padding:6px 10px; border-bottom:1px solid #EEF2F7; }}
  tr:nth-child(even) td {{ background:{_ZEBRA}; }}
  .card {{ border:1px solid #E5E7EB; border-left-width:5px; border-radius:10px;
          padding:14px 16px; margin:10px 0; }}
  .card h3 {{ margin:0 0 8px; font-size:15px; }}
  .card .ev {{ font-size:13px; color:#374151; }}
  .card .rx {{ font-size:13px; background:{_ZEBRA}; border-radius:8px; padding:8px 10px;
              margin-top:8px; }}
  .acc-total {{ font-size:28px; font-weight:800; color:{_ORANGE}; }}
  .note {{ font-size:12px; color:#6B7280; margin-top:8px; }}
  @media(max-width:600px) {{ .cost-chip{{position:static; display:inline-block; margin-top:6px;}}
                            .screen{{padding:16px;}} }}
</style></head><body><div class="wrap">
<h1>元板 · {nickname}</h1>
<p style="color:#6B7280;margin-top:-6px">四层下钻数据板块 · 环境 → 行业 → 账号 → 单条 · 算账视角</p>"""


# ── 第一屏:一句话结论 ──────────────────────────────────────────────────────
def _screen1_headline(nickname: str, h: dict) -> str:
    tc = h.get("top_concern") or {}
    sev = tc.get("severity")
    sc = h.get("strategic_call") or {}
    sc_col = _SEV_COLOR.get(sc.get("color"), "#fff")
    sc_block = ""
    if sc.get("call"):
        sc_block = f"""<div style="background:{sc_col};border-radius:10px;padding:14px 16px;margin-bottom:12px">
    <div style="font-size:12px;opacity:.9;color:#fff">🎯 核心战略判断</div>
    <div style="font-size:19px;font-weight:800;color:#fff;margin:3px 0">{sc.get('call')}</div>
    <div style="font-size:13px;color:#fff;opacity:.95">{sc.get('why')}</div>
  </div>"""
    return f"""<div class="screen"><span class="screen-tag">第一屏 · 一句话结论</span>
<div class="headline-box">
  <div>账号健康 <span class="score">{_n(h.get('health_score'))}</span>
       <span style="font-size:15px">分 · 商业评级 {_n(h.get('grade'))}</span></div>
  {sc_block}
  <div class="concern">
    <div style="font-size:13px;opacity:.85">⚠️ 最该关注的 1 件事</div>
    <div style="font-size:16px;font-weight:700;margin:4px 0">
      {_SEV_LABEL.get(sev,'')} {_n(tc.get('title'))}</div>
    <div style="font-size:14px">{_n(tc.get('what'))}</div>
    {f'<div style="font-size:13px;margin-top:6px;opacity:.9">→ {tc.get("advice")}</div>' if tc.get('advice') else ''}
  </div>
</div></div>"""


# ── 第二屏:四层下钻 ────────────────────────────────────────────────────────
def _screen2_drilldown(layers: dict, acc: dict) -> str:
    blocks = [_layer_block(layers.get(k)) for k in ("env", "industry", "account", "video")]
    return ('<div class="screen"><span class="screen-tag">第二屏 · 四层下钻 '
            '(从大盘到单条)</span>' + "".join(blocks) + "</div>")


def _layer_block(L: dict | None) -> str:
    if not L:
        return ""
    cost = L.get("cost_yuan")
    cost_txt = "≈¥0" if (cost or 0) < 0.01 else f"¥{cost:.3f}"
    body = _layer_body(L)
    # #6 诚实降级提示(无星图层明说商业数据取不到·不留空)
    status = L.get("star_status")
    status_html = ""
    if status and "未开星图" in status:
        status_html = (f'<div style="font-size:12px;color:#D97706;background:#FFF7ED;'
                       f'border-radius:8px;padding:6px 10px;margin:6px 0">⚠️ {status}</div>')
    return f"""<div class="layer">
  <span class="cost-chip">本层成本 {cost_txt}</span>
  <div><span class="coord">{L.get('coord')}</span><span class="zoom">{L.get('zoom')}</span></div>
  <div class="q">用户问:{L.get('user_question')}</div>
  {status_html}
  {body}
  <div class="note">价值:{L.get('value')} · 层级:{L.get('level')}</div>
</div>"""


def _layer_body(L: dict) -> str:
    coord = L.get("coord", "")
    if coord.startswith("①"):
        base = (f'<div class="kv"><span><span class="k">账号身位:</span>{_n(L.get("subject_tier"))}</span></div>'
                f'<div class="kv"><span><span class="k">热点契合:</span>'
                f'{_n(_g(L,"hot_fit","verdict"))}</span>'
                f'<span><span class="k">黑马选题:</span>{_n(_g(L,"dark_horse","verdict"))}</span></div>')
        return base + _deep_block(L.get("deep")) + _env_hot_block(L.get("env_hot"))
    if coord.startswith("②"):
        rk = L.get("industry_rank_percent")
        rk_txt = f"行业前 {round((1-rk)*100)}%" if isinstance(rk, (int, float)) and rk <= 1 else _n(rk)
        base = (f'<div class="kv"><span><span class="k">赛道:</span>{_n(L.get("track_keyword"))}</span>'
                f'<span><span class="k">蓝海度:</span>{_score_bar(L.get("blue_ocean_score"),80)}</span></div>'
                f'<div class="kv"><span><span class="k">商业身位:</span>{rk_txt}</span></div>')
        return base + _deep_block(L.get("deep")) + _competitor_block(L.get("competitor"))
    if coord.startswith("③"):
        return _layer_account_body(L)
    if coord.startswith("④"):
        base = (f'<div class="kv"><span><span class="k">内容力:</span>{_score_bar(L.get("content_score"),80)}</span>'
                f'<span><span class="k">爆款率:</span>{_n(L.get("burst_ratio"))}</span></div>'
                f'<div class="kv"><span><span class="k">均赞:</span>{_n(L.get("avg_like"))}</span>'
                f'<span><span class="k">最高赞:</span>{_n(L.get("max_like"))}</span>'
                f'<span><span class="k">距上次更新:</span>{_n(L.get("update_gap_days"),"天")}</span></div>')
        return base + _deep_block(L.get("deep"), "互动质量·深度拆解") + _next_video_block(L)
    return ""


def _next_video_block(L: dict) -> str:
    """渲染「下条怎么拍」处方 + 内容 DNA 六维(作品矩阵组合·无星图也满血)。"""
    rx = L.get("next_video_rx") or {}
    dna = L.get("dna") or {}
    if not (rx.get("steps") or dna):
        return ""
    steps_html = "".join(f"<li>{s}</li>" for s in (rx.get("steps") or []))
    rx_html = (f'<div style="background:{_ZEBRA};border-radius:10px;padding:12px 14px;margin-top:10px">'
               f'<div style="font-weight:800;color:{_BLUE};margin-bottom:6px">📌 下条怎么拍</div>'
               f'<ol style="margin:.2em 0;padding-left:1.2em;font-size:13px">{steps_html}</ol></div>'
               if steps_html else "")
    dna_rows = ""
    for label, key in (("⏰ 最优时段", "best_time"), ("⏱️ 最优时长", "best_duration"),
                       ("🎯 爆款选题", "topics"), ("#️⃣ 高效话题", "hashtags"),
                       ("🛒 带货判断", "anchor"), ("💬 评论选题池", "comment_pool")):
        v = dna.get(key)
        if v:
            dna_rows += f"<tr><td style='white-space:nowrap'>{label}</td><td>{v}</td></tr>"
    dna_html = (f'<table style="margin-top:8px"><tr><th>内容 DNA(作品矩阵组合)</th><th></th></tr>{dna_rows}</table>'
                if dna_rows else "")
    return rx_html + dna_html


def _layer_account_body(L: dict) -> str:
    g = L.get("grade") or {}
    rows = [
        ("综合健康 C1", _g(L, "health", "score"), _g(L, "health", "phase")),
        ("商业评级 C7", g.get("grade"), g.get("desc")),
        ("粉丝质量 C2", _g(L, "fans_quality", "score"), ""),
        ("商业转化 C3", _g(L, "commerce", "score"), _g(L, "commerce", "path")),
        ("破圈能力 C6", _g(L, "breakout", "score"), _g(L, "breakout", "verdict")),
        ("私域成熟 C8", _g(L, "private", "score"), ""),
        ("变现机会 C12", _g(L, "monetize", "score"), _g(L, "monetize", "verdict")),
    ]
    trs = "".join(
        f"<tr><td>{name}</td><td>{_score_bar(sc,90) if isinstance(sc,(int,float)) else _n(sc)}</td>"
        f"<td style='color:#6B7280'>{_n(note,'','')}</td></tr>"
        for name, sc, note in rows)
    table = f'<table><tr><th>指标</th><th>分值</th><th>说明</th></tr>{trs}</table>'
    # 深度五段式 + 受众洞察(新接入:评论热词+粉丝分布+采购意向)
    return table + _deep_block(L.get("deep_health"), "健康分·深度拆解") + \
        _deep_block(L.get("deep_commerce"), "商业转化·为什么这个分") + \
        _audience_block(L.get("audience"))


def _combo_card(title: str, conclusion: str, lines: list, implication: str | None,
                impl_color: str = "#FFF7ED") -> str:
    """通用组合洞察卡(评论热词/竞品/大盘等扩展信号·绿色虚线区分于五段式蓝)。"""
    lis = "".join(f"<li>{x}</li>" for x in lines if x)
    impl = (f'<div style="font-size:13px;background:{impl_color};border-radius:8px;'
            f'padding:7px 10px;margin-top:5px">💡 {implication}</div>') if implication else ""
    return (f'<div style="border:1px dashed #05966933;border-radius:10px;'
            f'padding:10px 12px;margin:8px 0;background:#F6FFFB">'
            f'<div style="font-weight:800;color:#059669;margin-bottom:4px">🔌 {title}'
            f'<span style="font-size:11px;color:#9CA3AF;font-weight:400">(新接入·原采集未展示)</span></div>'
            f'<div style="font-size:13.5px;margin:3px 0"><b>{conclusion}</b></div>'
            f'<ul style="margin:.1em 0;padding-left:1.3em;font-size:12.5px">{lis}</ul>{impl}</div>')


def _audience_block(d: dict | None) -> str:
    if not d:
        return ""
    impl = d.get("implication")
    return _combo_card("受众洞察 · 评论热词+粉丝分布+采购意向",
                       d.get("conclusion", ""), d.get("breakdown", []), impl,
                       impl_color="#FEF2F2" if d.get("intent_signal") else "#FFF7ED")


def _competitor_block(d: dict | None) -> str:
    if not d:
        return ""
    comp_lines = list(d.get("breakdown", []))
    comps = d.get("competitors") or []
    if comps:
        comp_lines.append("竞品圈:" + "、".join(
            f"{c['name']}({_fmt_fans(c.get('fans'))})" for c in comps[:5]))
    return _combo_card("竞品雷达 · 算法关联+粉丝同关",
                       d.get("conclusion", ""), comp_lines, d.get("implication"))


def _env_hot_block(d: dict | None) -> str:
    if not d:
        return ""
    return _combo_card("大盘热点深化 · 上升/热搜/挑战/平台选题",
                       d.get("conclusion", ""), d.get("breakdown", []), d.get("implication"))


def _fmt_fans(n):
    if not isinstance(n, (int, float)):
        return "—"
    return f"{n/10000:.1f}万" if n >= 10000 else str(int(n))


def _deep_block(d: dict | None, title: str | None = None) -> str:
    """渲染五段式深度块:结论→拆解→依据→基准→推论(带出处)。"""
    if not d:
        return ""
    head = f'<div style="font-weight:800;color:{_BLUE};margin:6px 0 4px">{title}</div>' if title else ""
    rows = ""
    if d.get("conclusion"):
        rows += f'<div style="font-size:13.5px;margin:3px 0"><b>结论:</b>{d["conclusion"]}</div>'
    for label, key in (("拆解", "breakdown"), ("依据", "evidence")):
        items = d.get(key)
        if items:
            lis = "".join(f"<li>{x}</li>" for x in items)
            rows += (f'<div style="font-size:12.5px;margin:2px 0"><b>{label}:</b>'
                     f'<ul style="margin:.1em 0;padding-left:1.3em">{lis}</ul></div>')
    if d.get("benchmark"):
        rows += (f'<div style="font-size:12.5px;color:#6B7280;margin:2px 0">'
                 f'📐 <b>基准对比:</b>{d["benchmark"]}</div>')
    if d.get("implication"):
        rows += (f'<div style="font-size:13px;background:#FFF7ED;border-radius:8px;'
                 f'padding:7px 10px;margin-top:5px">💡 <b>推论:</b>{d["implication"]}</div>')
    return (f'<div style="border:1px dashed #1E3A8A33;border-radius:10px;'
            f'padding:10px 12px;margin:8px 0;background:#FAFBFF">{head}{rows}</div>')


# ── 第三屏:诊断卡处方 ──────────────────────────────────────────────────────
def _screen3_cards(layers: dict) -> str:
    acc_cards = (layers.get("account") or {}).get("cards") or {}
    blocks = []
    for key in ("churn", "pricing", "track"):
        blocks.append(_card_block(acc_cards.get(key)))
    return ('<div class="screen"><span class="screen-tag">第三屏 · 诊断卡处方 '
            '(问题→结论→处方)</span>' + "".join(b for b in blocks if b) + "</div>")


def _card_block(card: dict | None) -> str:
    if not card:
        return ""
    sev = card.get("severity")
    col = _SEV_COLOR.get(sev, "#6B7280")
    advice = card.get("advice")
    return f"""<div class="card" style="border-left-color:{col}">
  <h3>{_SEV_LABEL.get(sev,'')} {_n(card.get('title'))}</h3>
  <div class="ev">{_n(card.get('conclusion'))}</div>
  {f'<div class="rx">处方:{advice}</div>' if advice else ''}
</div>"""


# ── 算账屏 ────────────────────────────────────────────────────────────────
def _screen_accounting(acc: dict) -> str:
    per = acc.get("per_layer_yuan") or {}
    roi = acc.get("roi") or {}
    names = {"env": "① 环境", "industry": "② 行业", "account": "③ 账号", "video": "④ 单条"}
    trs = "".join(
        f"<tr><td>{names.get(k,k)}</td><td>¥{v:.4f}</td></tr>"
        for k, v in per.items())
    return f"""<div class="screen"><span class="screen-tag">算账 · 这笔账划不划算</span>
<h2>本次诊断成本(按四层归因)</h2>
<table><tr><th>层</th><th>成本</th></tr>{trs}
<tr><td><b>合计</b></td><td><b>¥{_n(acc.get('total_yuan'))}</b>({acc.get('mode')})</td></tr></table>
<h2>你的 ROI 账</h2>
<div class="kv"><span><span class="k">你付出:</span><span class="acc-total">¥{_n(acc.get('total_yuan'))}</span> + 看报告约 8 分钟</span></div>
<table>
  <tr><th>等效替代</th><th>价值</th></tr>
  <tr><td>手动分析</td><td>约 {_n(roi.get('equiv_manual_hours'))} 小时</td></tr>
  <tr><td>专家会诊</td><td>{_n(roi.get('equiv_expert'))}</td></tr>
  <tr><td>外包报价</td><td>¥{_n(roi.get('equiv_outsource_yuan'))}</td></tr>
</table>
<div class="note">💡 {acc.get('compound_note')}</div>
</div>"""


def _html_foot() -> str:
    return ('<p style="text-align:center;color:#9CA3AF;font-size:12px;margin:20px 0">'
            '元板 MetaBoard · 数据源合规授权·国内不出境 · 经验阈值标注「待校准」处以 50-100 真实账号建分位基线后解锁'
            '</p></div></body></html>')


def _g(d, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return default if cur is None else cur


# ── Markdown(轻量·给仪表盘/IM)─────────────────────────────────────────────
def render_board_md(board: dict[str, Any]) -> str:
    h = board.get("headline") or {}
    tc = h.get("top_concern") or {}
    L = board.get("layers") or {}
    acc = board.get("accounting") or {}
    out = [f"<!-- x-metaform: {_metaform_stamp('md')} -->",
           f"# 元板 · {board.get('nickname') or '账号'}", ""]
    out.append(f"**健康 {_n(h.get('health_score'))} 分 · 评级 {_n(h.get('grade'))}**")
    out.append(f"⚠️ 最该关注:{_SEV_LABEL.get(tc.get('severity'),'')} "
               f"{_n(tc.get('title'))} — {_n(tc.get('what'))}")
    out.append("")
    for k in ("env", "industry", "account", "video"):
        ly = L.get(k) or {}
        cost = ly.get("cost_yuan") or 0
        ct = "≈¥0" if cost < 0.01 else f"¥{cost:.3f}"
        out.append(f"## {ly.get('coord')} · {ly.get('zoom')}({ct})")
        out.append(f"_{ly.get('user_question')}_ → 价值:{ly.get('value')}")
        out.append("")
    out.append(f"## 算账 · 合计 ¥{_n(acc.get('total_yuan'))}({acc.get('mode')})")
    out.append(f"💡 {acc.get('compound_note')}")
    return "\n".join(out)

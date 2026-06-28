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


def _metaform_stamp(fmt: str, template: str = "four-layer-drilldown") -> str:
    """生成 MetaForm 溯源戳字符串(与 metaform/lib/stamp.py 同构)。"""
    return (f"scenario=metaboard;format={fmt};template={template};"
            f"renderer=board_render;engine=metaboard;board_ver={_BOARD_VER};v=1")


def _n(v, suffix="", dash="—"):
    return f"{v}{suffix}" if v is not None else dash


# ══════════════════════════════════════════════════════════════════════════════
# SVG 迷你折线图(零依赖·内嵌·破晓色)· 图表规范:图 + 一句结论 = 一眼即达
# ══════════════════════════════════════════════════════════════════════════════

def _sparkline(points: list, *, width: int = 260, height: int = 56,
              color: str = _BLUE, fill: bool = True, suffix: str = "") -> str:
    """画一条迷你折线·points=[(label, value)]·首尾标值·零依赖内嵌 SVG。"""
    pts = [(str(la), float(v)) for la, v in (points or []) if v is not None]
    if len(pts) < 2:
        return '<span style="color:#9CA3AF;font-size:12px">数据点不足·图待积累</span>'
    ys = [v for _, v in pts]
    ymin, ymax = min(ys), max(ys)
    rng = (ymax - ymin) or 1
    n = len(pts)
    pad_x, pad_y = 8, 10
    iw, ih = width - pad_x * 2, height - pad_y * 2
    coords = []
    for i, (_, v) in enumerate(pts):
        px = pad_x + (i / (n - 1)) * iw
        py = pad_y + (1 - (v - ymin) / rng) * ih
        coords.append((px, py))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    area = ""
    if fill:
        area = (f'<polygon points="{pad_x},{height-pad_y} {poly} {width-pad_x},{height-pad_y}" '
                f'fill="{color}" opacity="0.08"/>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{color}"/>'
                   for x, y in coords)
    # 首尾值标注
    first_lab = f'<text x="{coords[0][0]:.0f}" y="{height-1}" font-size="9" fill="#6B7280">{pts[0][0]}</text>'
    last_lab = f'<text x="{width-pad_x}" y="{height-1}" font-size="9" fill="#6B7280" text-anchor="end">{pts[-1][0]}</text>'
    v0 = f'<text x="{coords[0][0]:.0f}" y="{coords[0][1]-5:.0f}" font-size="10" fill="{color}" font-weight="700">{_fmtnum(ys[0])}{suffix}</text>'
    v1 = f'<text x="{coords[-1][0]:.0f}" y="{coords[-1][1]-5:.0f}" font-size="10" fill="{color}" font-weight="700" text-anchor="end">{_fmtnum(ys[-1])}{suffix}</text>'
    return (f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'style="max-width:100%">{area}'
            f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2"/>'
            f'{dots}{first_lab}{last_lab}{v0}{v1}</svg>')


def _fmtnum(v: float) -> str:
    if v >= 10000:
        return f"{v/10000:.1f}万"
    return str(int(v)) if v == int(v) else f"{v:.2f}"


def _chart_row(title: str, svg: str, verdict: str = "") -> str:
    """图表规范:标题 + 图 + 一句结论(一眼即达)。"""
    v = f'<div style="font-size:12.5px;color:#374151">{verdict}</div>' if verdict else ""
    return (f'<div style="margin:8px 0"><div style="font-size:12.5px;color:{_BLUE};font-weight:700">{title}</div>'
            f'{svg}{v}</div>')


def _bars(items: list, *, width: int = 280, bar_h: int = 16, gap: int = 6,
          color: str = _BLUE) -> str:
    """水平柱状图(标准可复用)·items=[(label, value[, color])]·按值归一。"""
    rows = [(str(t[0]), float(t[1]), t[2] if len(t) > 2 else None)
            for t in (items or []) if t[1] is not None]
    if not rows:
        return ""
    vmax = max(r[1] for r in rows) or 1
    label_w = 86
    svg_h = len(rows) * (bar_h + gap)
    out = [f'<svg width="{width}" height="{svg_h}" viewBox="0 0 {width} {svg_h}" style="max-width:100%">']
    for i, (la, v, c) in enumerate(rows):
        y = i * (bar_h + gap)
        bw = (v / vmax) * (width - label_w - 44)
        col = c or color
        out.append(f'<text x="0" y="{y+bar_h-3}" font-size="11" fill="#374151">{la[:7]}</text>')
        out.append(f'<rect x="{label_w}" y="{y}" width="{max(2,bw):.0f}" height="{bar_h}" rx="3" fill="{col}"/>')
        out.append(f'<text x="{label_w+bw+4:.0f}" y="{y+bar_h-3}" font-size="10" fill="#6B7280">{_fmtnum(v)}</text>')
    out.append("</svg>")
    return "".join(out)


def _radar(items: list, *, size: int = 200, color: str = _BLUE) -> str:
    """雷达图(标准可复用)·items=[(label, value0-100)]·N轴蛛网。"""
    import math
    pts = [(str(la), max(0, min(100, float(v)))) for la, v in (items or []) if v is not None]
    n = len(pts)
    if n < 3:
        return ""
    cx = cy = size / 2
    r = size / 2 * 0.66
    # 背景环(25/50/75/100)
    rings = ""
    for frac in (0.25, 0.5, 0.75, 1.0):
        ring = " ".join(
            f"{cx + r*frac*math.cos(2*math.pi*i/n - math.pi/2):.1f},"
            f"{cy + r*frac*math.sin(2*math.pi*i/n - math.pi/2):.1f}" for i in range(n))
        rings += f'<polygon points="{ring}" fill="none" stroke="#E5E7EB" stroke-width="0.7"/>'
    # 数据多边形
    dpts, labels = [], ""
    for i, (la, v) in enumerate(pts):
        ang = 2 * math.pi * i / n - math.pi / 2
        rr = r * v / 100
        dpts.append(f"{cx+rr*math.cos(ang):.1f},{cy+rr*math.sin(ang):.1f}")
        lx, ly = cx + (r+12)*math.cos(ang), cy + (r+12)*math.sin(ang)
        anchor = "middle" if abs(math.cos(ang)) < 0.3 else ("start" if math.cos(ang) > 0 else "end")
        labels += f'<text x="{lx:.0f}" y="{ly:.0f}" font-size="9.5" fill="#6B7280" text-anchor="{anchor}">{la}</text>'
    poly = " ".join(dpts)
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" style="max-width:100%">'
            f'{rings}<polygon points="{poly}" fill="{color}" fill-opacity="0.18" '
            f'stroke="{color}" stroke-width="1.6"/>{labels}</svg>')


def _progress(pct: float, *, width: int = 220, color: str = _ORANGE) -> str:
    """进度条(标准可复用·里程碑用)。"""
    p = max(0, min(100, pct))
    return (f'<div style="height:8px;width:{width}px;max-width:100%;background:#E5E7EB;'
            f'border-radius:4px;overflow:hidden;display:inline-block;vertical-align:middle">'
            f'<div style="width:{p}%;height:100%;background:{color}"></div></div>'
            f'<b style="margin-left:8px;color:{color}">{round(p)}%</b>')


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
    # 算账(point2)移出对外报告·只留纯专业分析·成本走内部 ops(JSON 里仍有·不渲染)
    parts = [_ladder_head(nick),
             _ladder_answer_screen(nick, L, h),     # 第一屏:完整答案(4阶梯结论)
             _ladder_detail(L.get("l1"), _desc_body),
             _ladder_detail(L.get("l2"), _diag_body),
             _ladder_detail(L.get("l3"), _rx_body),
             _ladder_detail(L.get("l4"), _pred_body),
             _ladder_foot()]
    return "\n".join(parts)


def _ladder_head(nick: str) -> str:
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-metaform" content="{_metaform_stamp('html', 'value-ladder')}">
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
    out = _heading_block(ld.get("heading"))          # 现状→航向→终态(三段论述)
    out += _identity_block(ld.get("identity"))       # 形象一致性审计
    lis = "".join(f"<li>{d}</li>" for d in (ld.get("details") or []))
    out += f"<ul>{lis}</ul>{_milestone_block(ld.get('milestone'))}"
    if ld.get("source"):
        out += f'<div class="note">出处:{ld.get("source")}</div>'
    return out


def _identity_block(idn: dict | None) -> str:
    """形象一致性审计:全部资料 + 六信号一致性 + 自我匹配 + 简介三要素。"""
    if not idn:
        return ""
    p = idn.get("profile") or {}
    match = idn.get("self_match", "")
    mcol = {"高度匹配": "#059669", "部分匹配": "#D97706"}.get(match, "#DC2626")
    # 六信号一致性·柱状(图示)
    sig = idn.get("signals") or {}
    bars = _bars([(k, 100 if v else 8, (None if v else "#DC2626"))
                  for k, v in sig.items() if v is not None], color="#059669", bar_h=13)
    # 简介三要素·徽章
    el = idn.get("elements") or {}
    badges = "".join(
        f'<span class="chip" style="background:{"#ECFDF5" if v else "#FEF2F2"};'
        f'color:{"#059669" if v else "#DC2626"}">{"✓" if v else "✗"} {k}</span> '
        for k, v in el.items())
    profile_rows = ""
    for label, key in (("昵称", "nickname"), ("简介", "signature"), ("抖音号", "unique_id"),
                       ("属地", "ip_location"), ("个人认证", "custom_verify"),
                       ("企业认证", "enterprise_verify")):
        v = p.get(key)
        if v:
            vv = str(v).replace("\n", " ")[:60]
            profile_rows += f'<tr><td style="white-space:nowrap">{label}</td><td>{vv}</td></tr>'
    tc = (f'<div class="note">📌 {idn["trust_confirmed"]}</div>' if idn.get("trust_confirmed") else "")
    adv = "".join(f"<li>{a}</li>" for a in (idn.get("advice") or []))
    return (f'<div style="border:1px solid {mcol}33;border-radius:10px;padding:12px 14px;margin:8px 0;background:#FAFBFF">'
            f'<div style="font-weight:800;color:{mcol}">🪪 形象一致性 · '
            f'<b>{match}</b>(统一度 {idn.get("consistency")})</div>'
            f'<div style="font-size:13px;margin:3px 0">{idn.get("verdict","")}</div>'
            f'<details style="box-shadow:none;margin:4px 0"><summary style="font-size:12px;color:#6B7280">全部基础资料 ▾</summary>'
            f'<table>{profile_rows}</table></details>'
            + _chart_row("六信号是否指向同一身份", bars, f"对齐:{('、'.join(idn.get('aligned') or []))}")
            + f'<div style="font-size:12.5px;margin:4px 0">简介专业三要素:{badges}</div>'
            f'{tc}<ul style="font-size:12.5px">{adv}</ul>'
            f'<div class="note">{idn.get("note","")}</div></div>')


def _heading_block(h: dict | None) -> str:
    """阶段1 航向:你现在是→该往哪走→终极成为(三段递进·箭头流)。"""
    if not h or not h.get("now"):
        return ""
    steps = [("你现在是", h.get("now"), "#6B7280"),
             ("该往哪走", h.get("direction"), _ORANGE),
             ("终极成为", h.get("endstate"), _BLUE)]
    rows = ""
    for i, (k, v, col) in enumerate(steps):
        arrow = '<div style="color:#9CA3AF;font-size:14px;margin:1px 0">↓</div>' if i else ""
        rows += (f'{arrow}<div style="display:flex;gap:8px;align-items:baseline">'
                 f'<span style="flex:none;font-size:11px;color:#fff;background:{col};'
                 f'padding:2px 8px;border-radius:9px">{k}</span>'
                 f'<span style="font-size:13.5px;font-weight:600">{_n(v)}</span></div>')
    logic = ""
    if h.get("logic"):
        logic = ('<details style="margin-top:6px;box-shadow:none"><summary style="padding:4px 0;font-size:12px;color:#6B7280">逻辑依据 ▾</summary>'
                 + "".join(f'<div style="font-size:12px;color:#6B7280">· {x}</div>' for x in h["logic"])
                 + "</details>")
    return (f'<div style="background:{_ZEBRA};border-radius:10px;padding:12px 14px;margin:4px 0 10px">'
            f'{rows}{logic}</div>')


def _milestone_block(ms: dict | None) -> str:
    if not ms:
        return ""
    nxt = ms.get("next")
    body = f'<div style="font-size:13px"><b>里程碑:</b>{ms.get("current","")}</div>'
    if nxt:
        body += (f'<div style="font-size:12.5px;margin:4px 0 2px">🎯 {nxt.get("verdict","")}</div>'
                 + _progress(nxt.get("pct", 0)))
    return f'<div style="background:#fff;border:1px solid {_ZEBRA};border-radius:8px;padding:9px 12px;margin:6px 0">{body}</div>'


_RADAR_LABELS = {"c1": "健康", "c2": "粉丝", "c3": "转化", "c4": "内容",
                 "c5": "赛道", "c6": "破圈", "c7": "评级", "c8": "私域"}


def _diag_body(ld: dict) -> str:
    """阶段2 全整合诊断(point3):雷达一眼看强弱 → 5层数据链(流量→互动→口碑→转化→真实)·
    14指标+所有信号全织入·层层因果联想 → 矿脉/热评/聚类/归因/异常作各层证据 → 诊断卡收口。"""
    out = ""
    tc = ld.get("top_concern") or {}
    if tc.get("title"):
        out += (f'<div class="impl">⚠️ 最该关注:{_SEV_LABEL.get(tc.get("severity"))} '
                f'{tc.get("title")} — {tc.get("what","")}</div>')
    # ① 14指标雷达(账号自身8维·一眼看强弱·图示 point1)
    radar = ld.get("radar") or {}
    items = [(_RADAR_LABELS.get(r["key"].lower(), r["label"]), r["score"])
             for r in (radar.get("account_self") or []) if r.get("score") is not None]
    if len(items) >= 3:
        out += _chart_row("账号八维雷达(自身实力)", _radar(items),
                          "外环=强·内缩=弱·一眼看短板长板")
    # ② 诊断链:5 层因果(流量→互动→口碑→转化→真实)
    for seg in (ld.get("chain") or []):
        out += _chain_layer(seg)
    # ②' 口碑层证据:热评原话 + 诉求聚类(真实引用·gold)
    out += _comment_voice_block(ld.get("hot_comments"), ld.get("comment_clusters"))
    out += _anomaly_block(ld.get("engagement_anomaly"))
    # ③ 五段式深拆(健康/商业转化·点此细看)
    out += ('<details style="box-shadow:none;border:1px dashed #E5E7EB"><summary style="font-size:13px">📐 关键指标五段式深拆(健康/商业转化·点开)</summary><div class="body">'
            + _five(ld.get("deep_health"), "健康分·深度拆解")
            + _five(ld.get("deep_commerce"), "商业转化·为什么这个分") + '</div></details>')
    # ④ 内容归因(柱状图 point1)
    out += _attribution_chart(ld.get("attribution"))
    # ⑤ 诊断卡简表
    cards = [x for x in (ld.get("details") or []) if x]
    if cards:
        rows = "".join(f'<tr><td>{_SEV_LABEL.get(x.get("severity"))} {x.get("title")}</td>'
                       f'<td>{x.get("conclusion","")}</td></tr>' for x in cards)
        out += f'<table><tr><th>诊断卡</th><th>结论</th></tr>{rows}</table>'
    return out


def _chain_layer(seg: dict) -> str:
    """诊断链一层:层名 + 指标 + 诊断 + 连到下一层(箭头因果·专业联想)。"""
    col = seg.get("color", _BLUE)
    metrics = "".join(f'<span class="chip" style="background:#fff;border:1px solid {col}33;color:{col}">{m}</span> '
                      for m in (seg.get("metrics") or []) if m)
    link = (f'<div style="font-size:12px;color:#9CA3AF;margin-top:3px">{seg["link"]}</div>'
            if seg.get("link") else "")
    return (f'<div style="border-left:3px solid {col};padding:8px 0 8px 12px;margin:6px 0">'
            f'<div style="font-weight:700;color:{col};font-size:13.5px">{seg.get("layer")}</div>'
            f'<div style="margin:3px 0">{metrics}</div>'
            f'<div style="font-size:13px"><b>诊断:</b>{seg.get("diagnosis","")}</div>{link}</div>')


def _attribution_chart(at: dict | None) -> str:
    """内容归因·柱状图(组间落差·哪个数据因子最驱动)。"""
    if not at or not at.get("enough"):
        return _attribution_block(at)
    bars = _bars([(f["factor"], f["spread"]) for f in (at.get("factors") or [])[:5]],
                 color="#0891B2")
    return _chart_row("内容归因·因子驱动力(组间落差倍数)", bars,
                      f'💡 {at.get("implication","")}')


def _rx_body(ld: dict) -> str:
    """阶段3 处方双层(point4):前端三级层级(战略→战术→执行·人话)+ 后端 cut 命令(MetaCut)。"""
    out = ""
    front = ld.get("front") or {}
    # 三级层级·递进(战略→战术→执行)
    strat = front.get("strategy") or {}
    if strat.get("text"):
        col = _SEV_COLOR.get(ld.get("strategic_color"), "#059669")
        out += (f'<div style="background:{col};color:#fff;border-radius:9px;padding:11px 14px;margin-bottom:8px">'
                f'<div style="font-size:11px;opacity:.85">① 战略层·方向</div>'
                f'<b style="font-size:15px">🎯 {strat.get("text")}</b>'
                f'<div style="font-size:12.5px;opacity:.95;margin-top:2px">{strat.get("why","")}</div></div>')
    tactic = front.get("tactic") or {}
    if tactic.get("steps"):
        out += ('<div style="font-weight:700;color:#059669;margin:6px 0 3px">② 战术层·本周做这几件</div>'
                '<ol style="padding-left:1.3em;font-size:13px">'
                + "".join(f"<li>{w}</li>" for w in tactic["steps"]) + "</ol>")
    ex = front.get("execute") or {}
    if ex.get("text"):
        out += (f'<div style="background:{_ZEBRA};border-radius:8px;padding:9px 12px;margin:6px 0">'
                f'<div style="font-size:11px;color:{_BLUE};font-weight:700">③ 执行层·下条怎么拍</div>'
                f'<div style="font-size:13.5px">{ex.get("text")}</div></div>')
    if ld.get("audience_intent"):
        out += f'<div class="impl">💰 {ld.get("audience_implication","")}</div>'
    # 后端 cut 命令(MetaCut 可执行·折叠·给工程/制作引擎)
    out += _cut_commands_block(ld.get("cut_commands"))
    return out


def _cut_commands_block(cc: dict | None) -> str:
    """后端 MetaCut 执行命令(结构化·折叠·人不必看·引擎直接消费)。"""
    if not cc:
        return ""
    import json
    nc = cc.get("next_clip") or {}
    # 人类可读摘要(命令的白话版)
    summ = []
    if nc.get("post_window"):
        summ.append(f"发布窗 {nc['post_window']}")
    if nc.get("duration_s"):
        summ.append(f"时长 {nc['duration_s'][0]}-{nc['duration_s'][1]}s")
    if nc.get("hook"):
        summ.append(f"钩子 {nc['hook']}")
    if nc.get("topic_tags"):
        summ.append("选题 " + "/".join(nc["topic_tags"]))
    raw = json.dumps(cc, ensure_ascii=False, indent=1)
    return ('<details style="box-shadow:none;border:1px dashed #7C3AED55;margin-top:8px">'
            '<summary style="font-size:13px;color:#7C3AED">⚙️ 后端·MetaCut 执行命令(引擎直接执行·点开看)</summary>'
            f'<div class="body"><div style="font-size:12.5px;color:#374151">{"·".join(summ)}</div>'
            f'<pre style="background:#0F172A;color:#E2E8F0;border-radius:8px;padding:10px;'
            f'font-size:11px;overflow-x:auto;white-space:pre-wrap">{raw}</pre>'
            f'<div class="note">承 v3.2 飞轮③ DeliveryPackage → MetaCut 制作引擎·每条命令可溯源</div></div></details>')


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
    # 口碑演化(矿脉③·先行信号)
    out += _sentiment_block(ld.get("sentiment_evo"))
    # 账号轨迹(跨次采集·完整B)
    out += _trajectory_block(ld.get("trajectory"))
    # 处方前后对照(证明建议有没有用)
    out += _rx_effect_block(ld.get("rx_effect"))
    out += f'<div class="note">置信:{ld.get("conf","—")}·内容时序单次可算·账号轨迹+处方对照靠累积</div>'
    return out


def _comment_voice_block(hot: dict | None, clu: dict | None) -> str:
    """热评TOP + 评论聚类(采了没接·补)。"""
    if not (hot and hot.get("enough")) and not (clu and clu.get("enough")):
        return ""
    head = '<div style="font-weight:700;color:#0D9488;margin:8px 0 4px">🗣️ 评论之声·热评+诉求聚类(采了没接·已补)</div>'
    out = ""
    if hot and hot.get("enough"):
        rows = "".join(
            f'<tr><td>{"🔥" if h.get("is_hot") or h.get("stick") else ""}{h["digg"]}赞</td>'
            f'<td>{h["text"][:30]}</td></tr>' for h in (hot.get("top") or [])[:5])
        out += f'<table><tr><th>热度</th><th>热评(观众最认同的声音)</th></tr>{rows}</table>'
    if clu and clu.get("enough"):
        chips = "".join(f'<span class="chip">{c["theme"]}({c["count"]})</span> '
                        for c in (clu.get("clusters") or []))
        out += f'<div style="font-size:12.5px;margin-top:4px">高频诉求聚类:{chips}</div>'
    return head + out


def _anomaly_block(an: dict | None) -> str:
    """互动操纵异常(④虚假检测补强·作品矩阵零成本)。"""
    if not an or not an.get("enough"):
        return ""
    col = _SEV_COLOR.get(an.get("level"), "#6B7280")
    flagged = ""
    if an.get("flagged"):
        flagged = "<div class='note'>反常作品:" + "、".join(
            f"{f['desc']}(赞{f['like']}/评{f['comment']})" for f in an["flagged"]) + "</div>"
    return (f'<div style="font-weight:700;color:{col};margin:8px 0 4px">🕵️ 互动操纵检测(④补强)</div>'
            f'<div style="font-size:13px"><b>{_SEV_LABEL.get(an.get("level"))} {an.get("verdict")}</b></div>'
            f'{flagged}<div class="note">{an.get("note","")}</div>')


def _attribution_block(at: dict | None) -> str:
    """矿脉②:内容归因(哪个数据因子驱动互动)。"""
    if not at:
        return ""
    head = '<div style="font-weight:700;color:#0891B2;margin:8px 0 4px">🔬 内容归因·哪个数据因子最驱动互动(矿脉②)</div>'
    if not at.get("enough"):
        return head + f'<div class="note">{at.get("verdict")}</div>'
    rows = "".join(
        f'<tr><td>{f["factor"]}</td><td>差 {f["spread"]}x</td>'
        f'<td style="font-size:11.5px">{f["best"]}({f["best_eng"]}) vs {f["worst"]}({f["worst_eng"]})</td></tr>'
        for f in (at.get("factors") or [])[:4])
    return (head + f'<div style="font-size:13px"><b>{at.get("verdict")}</b></div>'
            f'<table><tr><th>因子</th><th>组间落差</th><th>最好 vs 最差</th></tr>{rows}</table>'
            f'<div class="impl">💡 {at.get("implication")}</div>'
            f'<div class="note">{at.get("note","")}</div>')


def _sentiment_block(se: dict | None) -> str:
    """矿脉③:口碑演化(评论时间线意图/情感趋势)。"""
    if not se:
        return ""
    head = '<div style="font-weight:700;color:#DB2777;margin:8px 0 4px">💬 口碑演化·评论时间线(矿脉③·先行信号)</div>'
    if not se.get("enough"):
        return head + f'<div class="note">{se.get("verdict")}</div>'
    e, l = se.get("early") or {}, se.get("late") or {}
    # 图示:采购意向率 早→近 折线(point1)
    intent_chart = _sparkline([("早期", (e.get("intent_rate") or 0) * 100),
                               ("近期", (l.get("intent_rate") or 0) * 100)],
                              color="#DB2777", suffix="%")
    return (head
            + _chart_row("采购/咨询意向率(早→近)", intent_chart,
                         f"<b>{se.get('verdict')}</b>·{se.get('intent_trend','')}")
            + f'<div class="impl">💡 {se.get("implication","")}</div>'
            f'<div class="note">{se.get("note","")}·{se.get("span","")}</div>')


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
    head = '<div style="font-weight:700;color:#DC2626;margin:8px 0 4px">📈 账号轨迹(跨次采集·真实历史)</div>'
    if not tj.get("enough"):
        return head + f'<div class="impl">⏳ {tj.get("verdict")}</div>'
    # 图示:涨粉折线(point1·一眼即达)
    path = [(d[5:] if d and len(d) > 5 else d, f) for d, f in (tj.get("follower_path") or [])]
    chart = _sparkline(path, color="#DC2626")
    extra = ""
    if tj.get("like_trend"):
        extra += f'<div style="font-size:12.5px">互动:{tj["like_trend"]}</div>'
    if tj.get("health_trend"):
        extra += f'<div style="font-size:12.5px">健康:{tj["health_trend"]}</div>'
    return (head + _chart_row("粉丝轨迹", chart, f"<b>{tj.get('verdict')}</b>·{tj.get('detail','')}")
            + extra + f'<div class="note">{tj.get("note","")}·快照 {tj.get("snapshots")} 个</div>')


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

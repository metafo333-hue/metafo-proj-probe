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
             _html_foot()]
    return "\n".join(parts)


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
        return base + _deep_block(L.get("deep"))
    if coord.startswith("②"):
        rk = L.get("industry_rank_percent")
        rk_txt = f"行业前 {round((1-rk)*100)}%" if isinstance(rk, (int, float)) and rk <= 1 else _n(rk)
        base = (f'<div class="kv"><span><span class="k">赛道:</span>{_n(L.get("track_keyword"))}</span>'
                f'<span><span class="k">蓝海度:</span>{_score_bar(L.get("blue_ocean_score"),80)}</span></div>'
                f'<div class="kv"><span><span class="k">商业身位:</span>{rk_txt}</span></div>')
        return base + _deep_block(L.get("deep"))
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
    # 深度五段式:健康分拆解 + 商业转化为什么这个分(纠赛道误判)
    return table + _deep_block(L.get("deep_health"), "健康分·深度拆解") + \
        _deep_block(L.get("deep_commerce"), "商业转化·为什么这个分")


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

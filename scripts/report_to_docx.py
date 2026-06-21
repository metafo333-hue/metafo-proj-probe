#!/usr/bin/env python3
"""probe 账号诊断报告 → 专业 Word(.docx) · v2.0 · metafo 品牌标准。

设计哲学（v2.0）：
  - 被分析账号是主角，metafo 是品质印章（右下角·小字）
  - 图表跟着对应段落出现（不堆附录）
  - 关键数字用数据卡片，不用密集表格
  - 零广告语言（不写"由引擎生成"）

用法:
  函数: from scripts.report_to_docx import export_docx; export_docx(result, "out.docx")
  CLI : python scripts/report_to_docx.py "<抖音链接>" [out.docx]
"""
from __future__ import annotations

import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# —— metafo 品牌色 ——
BLUE   = RGBColor(0x1E, 0x3A, 0x8A)   # 主蓝
ORANGE = "FF7A1A"                        # 橙（XML hex）
ORANGE_RGB = RGBColor(0xFF, 0x7A, 0x1A)
INK    = RGBColor(0x1E, 0x29, 0x3B)   # 墨黑
INK2   = RGBColor(0x47, 0x55, 0x69)   # 次墨
GREY   = RGBColor(0x94, 0x94, 0x95)   # 灰
LGREY  = RGBColor(0xCB, 0xD5, 0xE1)   # 浅灰
CN_FONT = "Microsoft YaHei"

# ──────────────────────────────────────────────────────────────────────────────
# 基础渲染工具
# ──────────────────────────────────────────────────────────────────────────────

def _cn(run, font=CN_FONT):
    """设置中文字体（同时设 w:eastAsia 防回退）。"""
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rpr.get_or_add_rFonts().set(qn("w:eastAsia"), font)


def _set_style(style, size, color=INK, font=CN_FONT):
    style.font.name = font
    style.font.size = Pt(size)
    style.font.color.rgb = color
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)


def _runs(p, text):
    """渲染 **粗体** 标记的富文本段落。"""
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True; r.font.color.rgb = BLUE
        else:
            r = p.add_run(part)
        _cn(r)


def _heading(doc, text, color, size, level=1, space_before=12, space_after=6):
    h = doc.add_heading(level=level)
    h.text = ""
    h.paragraph_format.space_before = Pt(space_before)
    h.paragraph_format.space_after = Pt(space_after)
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        t = part[2:-2] if part.startswith("**") else part
        r = h.add_run(t); _cn(r)
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = True
    return h


def _shade(p, hexcolor):
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), hexcolor)
    p._p.get_or_add_pPr().append(sh)


def _hrule(doc, color=ORANGE, thickness="12"):
    """橙色分隔线。"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    pbdr = OxmlElement("w:pBdr"); bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), thickness)
    bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), color)
    pbdr.append(bottom); p._p.get_or_add_pPr().append(pbdr)
    return p


def _page_break(doc):
    from docx.enum.text import WD_BREAK
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def _spacer(doc, pt=8):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(pt)
    return p


# ──────────────────────────────────────────────────────────────────────────────
# 页脚（简洁·品牌印章）
# ──────────────────────────────────────────────────────────────────────────────

def _setup_footer(doc, nick):
    """页脚：左边账号名，右边 metafo 品牌印章 + 页码。"""
    from docx.oxml import OxmlElement
    sec = doc.sections[0]
    footer = sec.footer
    p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    p.clear()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # @昵称
    rl = p.add_run(f"@{nick}  ·  "); _cn(rl)
    rl.font.size = Pt(8); rl.font.color.rgb = GREY

    # metafo
    rb = p.add_run("metafo"); _cn(rb)
    rb.font.size = Pt(8); rb.bold = True; rb.font.color.rgb = BLUE

    # 页码
    rs = p.add_run("  "); _cn(rs); rs.font.size = Pt(8)
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run = p.add_run(); run._r.append(f1); run._r.append(it); run._r.append(f2)
    run.font.size = Pt(8); run.font.color.rgb = GREY


# ──────────────────────────────────────────────────────────────────────────────
# 封面（v2.0：账号为主角）
# ──────────────────────────────────────────────────────────────────────────────

def _cover(doc, nick, rpt_no, platform_cn, date):
    """封面：@账号名最大·metafo 为右下角品质印章。"""
    # 顶部留白
    for _ in range(5):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)

    # 橙色细分隔线（上）
    _hrule(doc, ORANGE, "8")

    # 主标题：@账号名
    mp = doc.add_paragraph(); mp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    mp.paragraph_format.space_before = Pt(20)
    mp.paragraph_format.space_after = Pt(4)
    mr = mp.add_run(f"@{nick}"); _cn(mr)
    mr.font.size = Pt(28); mr.bold = True; mr.font.color.rgb = BLUE

    # 副标题
    sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(20)
    sr = sp.add_run("账号深度诊断报告"); _cn(sr)
    sr.font.size = Pt(16); sr.font.color.rgb = INK

    # 橙色细分隔线（下）
    _hrule(doc, ORANGE, "8")

    # 元信息（左对齐·小字·灰色）
    for label, val in [
        ("平台", platform_cn),
        ("诊断日期", date or "—"),
        ("报告编号", rpt_no),
    ]:
        ip = doc.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.LEFT
        ip.paragraph_format.space_before = Pt(4)
        ip.paragraph_format.space_after = Pt(0)
        il = ip.add_run(f"▸ {label}："); _cn(il)
        il.font.size = Pt(10); il.font.color.rgb = INK2; il.bold = True
        iv = ip.add_run(val); _cn(iv)
        iv.font.size = Pt(10); iv.font.color.rgb = GREY

    # 底部留白 + metafo 印章（右对齐）
    for _ in range(7):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)

    stamp = doc.add_paragraph(); stamp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    stamp.paragraph_format.space_before = Pt(0)
    sr2 = stamp.add_run("⬡  metafo"); _cn(sr2)
    sr2.font.size = Pt(9); sr2.font.color.rgb = LGREY


# ──────────────────────────────────────────────────────────────────────────────
# 核心结论框（执行摘要·BLUF）
# ──────────────────────────────────────────────────────────────────────────────

def _exec_summary(doc, summary, nick):
    """执行摘要：橙色左边线 + 浅暖背景·开篇抓重点。"""
    if not summary:
        return
    _heading(doc, "核心结论", BLUE, 14, 1, space_before=0, space_after=8)

    p = doc.add_paragraph()
    _shade(p, "FFF7ED")
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.right_indent = Cm(0.2)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(12)
    pPr = p._p.get_or_add_pPr(); pbdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    for k, val in (("w:val", "single"), ("w:sz", "24"), ("w:space", "8"), ("w:color", ORANGE)):
        left.set(qn(k), val)
    pbdr.append(left); pPr.append(pbdr)
    _runs(p, summary)


# ──────────────────────────────────────────────────────────────────────────────
# 数据卡片（关键指标可视化）
# ──────────────────────────────────────────────────────────────────────────────

def _stat_cards(doc, cards):
    """3列数据卡片：数字大字蓝色，标签小字灰色。cards=[(数字, 标签), ...]，最多3个。"""
    cards = cards[:3]
    if not cards:
        return
    t = doc.add_table(rows=2, cols=len(cards))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.style = "Table Grid"
    # 去边框
    for row in t.rows:
        for cell in row.cells:
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement("w:tcBorders")
            for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
                border = OxmlElement(f"w:{side}")
                border.set(qn("w:val"), "nil")
                tcBorders.append(border)
            tcPr.append(tcBorders)
            _shade(cell.paragraphs[0], "EFF6FF")

    for i, (num, label) in enumerate(cards):
        # 数字行
        np = t.rows[0].cells[i].paragraphs[0]
        np.alignment = WD_ALIGN_PARAGRAPH.CENTER
        np.paragraph_format.space_after = Pt(0)
        nr = np.add_run(str(num)); _cn(nr)
        nr.font.size = Pt(18); nr.bold = True; nr.font.color.rgb = BLUE
        # 标签行
        lp = t.rows[1].cells[i].paragraphs[0]
        lp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        lp.paragraph_format.space_before = Pt(0)
        lr = lp.add_run(label); _cn(lr)
        lr.font.size = Pt(9); lr.font.color.rgb = GREY

    _spacer(doc, 10)


# ──────────────────────────────────────────────────────────────────────────────
# 原始数据表（附录用）
# ──────────────────────────────────────────────────────────────────────────────

def _data_table(doc, rows):
    """两列键值表（蓝色键·灰色值·带底纹）。"""
    t = doc.add_table(rows=0, cols=2)
    t.style = "Light List Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, (k, v) in enumerate(rows):
        c = t.add_row().cells
        c[0].width = Cm(3.2); c[1].width = Cm(11.8)
        if i % 2 == 0:
            for cell in c:
                _shade(cell.paragraphs[0], "F8FAFC")
        rk = c[0].paragraphs[0].add_run(str(k))
        rk.bold = True; _cn(rk); rk.font.size = Pt(10); rk.font.color.rgb = BLUE
        rv = c[1].paragraphs[0].add_run(str(v))
        _cn(rv); rv.font.size = Pt(10)


# ──────────────────────────────────────────────────────────────────────────────
# Markdown 解析器（正文）
# ──────────────────────────────────────────────────────────────────────────────

def _parse_md(doc, md):
    """解析 report_md 的主体段落，包括图表嵌入占位符（##CHART_1## 等）。"""
    for raw in md.split("\n"):
        s = raw.rstrip()
        if not s or s.startswith("# "):
            continue
        if s.startswith("## "):
            _heading(doc, s[3:].strip(), BLUE, 13.5, 1)
        elif s.startswith("### "):
            _heading(doc, s[4:].strip(), INK, 11.5, 2)
        elif s.startswith("> "):
            # 引用块：浅蓝背景 + 左边线效果
            p = doc.add_paragraph()
            _shade(p, "EFF6FF")
            p.paragraph_format.left_indent = Cm(0.5)
            p.paragraph_format.right_indent = Cm(0.2)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
            _runs(p, s[2:].strip())
        elif s.lstrip().startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.left_indent = Cm(0.5)
            _runs(p, s.lstrip()[2:])
        elif re.match(r"^\s*\d+\.\s", s):
            p = doc.add_paragraph(style="List Number")
            _runs(p, re.sub(r"^\s*\d+\.\s", "", s))
        elif s.startswith("---"):
            _hrule(doc, "CBD5E1", "6")
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            _runs(p, s)


# ──────────────────────────────────────────────────────────────────────────────
# 图表生成（动态·数据不足不画）
# ──────────────────────────────────────────────────────────────────────────────

def _make_charts(result: dict, tmpdir: str) -> dict:
    """生成所有图表，返回 {chart_key: png_path}。
    图1·视频对比 · 图2·演化趋势 · 图3·互动结构。
    数据不足的图不生成（诚实原则）。
    """
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm

    for fp in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if os.path.exists(fp):
            plt.rcParams["font.sans-serif"] = [fm.FontProperties(fname=fp).get_name()]
            break
    plt.rcParams["axes.unicode_minus"] = False

    B, O, LB = "#1E3A8A", "#FF7A1A", "#93C5FD"
    charts = {}
    v = result.get("video", {}) or {}
    a = result.get("account", {}) or {}
    works = [w for w in (result.get("works") or []) if isinstance(w, dict)]

    # 图1：这条 vs 账号水平（水平条）
    like, avg, mx = v.get("like"), a.get("avg_like"), a.get("max_like")
    if avg and like is not None:
        fig, ax = plt.subplots(figsize=(6, 1.8))
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#F8FAFC")
        vals = [like or 0, avg or 0, mx or 0]
        labels = ["这条视频", "账号平均", "账号最高"]
        colors = [O, B, LB]
        bars = ax.barh(labels, vals, color=colors, height=0.5, edgecolor="none")
        ax.invert_yaxis()
        for bar, val in zip(bars, vals):
            ax.text(
                max(val, max(vals) * 0.02),
                bar.get_y() + bar.get_height() / 2,
                f" {val:,}",
                va="center", fontsize=10, color="#1E293B"
            )
        ax.set_xlim(0, max(vals) * 1.25)
        ax.axis("off")
        ax.set_title("这条视频在账号中的位置（点赞数）", fontsize=10, color=B, pad=8)
        p = os.path.join(tmpdir, "c1.png")
        fig.savefig(p, dpi=140, bbox_inches="tight", facecolor="#F8FAFC")
        plt.close(fig)
        charts["video_vs_avg"] = p

    # 图2：演化趋势（折线·简洁）
    timed = sorted([w for w in works if w.get("create_time")], key=lambda w: w["create_time"])
    if len(timed) >= 4:
        ys = [w.get("like", 0) or 0 for w in timed]
        xs = list(range(1, len(ys) + 1))
        fig, ax = plt.subplots(figsize=(6, 2.2))
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#F8FAFC")
        ax.plot(xs, ys, marker="o", color=B, linewidth=2, markersize=5, zorder=3)
        ax.fill_between(xs, ys, color=B, alpha=0.07)
        # 标注最高点
        peak = ys.index(max(ys))
        ax.annotate(
            f"{max(ys):,}",
            (xs[peak], ys[peak]),
            textcoords="offset points", xytext=(0, 8),
            fontsize=8, color=O, ha="center"
        )
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(left=False, labelsize=8)
        ax.set_xlabel("发布顺序（早 → 近）", fontsize=8, color=GREY.rgb if hasattr(GREY, 'rgb') else "#949495")
        ax.set_title("账号点赞演化趋势", fontsize=10, color=B, pad=8)
        ax.yaxis.set_tick_params(labelcolor="#949495")
        ax.grid(axis="y", alpha=0.2, color="#CBD5E1")
        p = os.path.join(tmpdir, "c2.png")
        fig.savefig(p, dpi=140, bbox_inches="tight", facecolor="#F8FAFC")
        plt.close(fig)
        charts["trend"] = p

    # 图3：高赞 vs 低赞 互动结构（分组条）
    if len(works) >= 6:
        sw = sorted(works, key=lambda w: w.get("like", 0) or 0, reverse=True)
        seg = max(1, len(sw) // 3)
        top, bot = sw[:seg], sw[-seg:]
        def _m(ws, k):
            return sum((w.get(k, 0) or 0) for w in ws) / len(ws) if ws else 0
        cats = ["点赞", "评论", "收藏", "转发"]
        tv = [_m(top, "like"), _m(top, "comment"), _m(top, "collect"), _m(top, "share")]
        bv = [_m(bot, "like"), _m(bot, "comment"), _m(bot, "collect"), _m(bot, "share")]
        fig, ax = plt.subplots(figsize=(6, 2.2))
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#F8FAFC")
        x = range(len(cats)); ww = 0.36
        ax.bar([i - ww/2 for i in x], [t + 0.1 for t in tv], ww, label="高赞作品", color=O, edgecolor="none")
        ax.bar([i + ww/2 for i in x], [b + 0.1 for b in bv], ww, label="低赞作品", color=LB, edgecolor="none")
        ax.set_xticks(list(x)); ax.set_xticklabels(cats, fontsize=9)
        ax.set_yscale("log")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(left=False, labelsize=8)
        ax.legend(fontsize=8, framealpha=0)
        ax.set_title("高赞 vs 低赞 作品的互动结构对比", fontsize=10, color=B, pad=8)
        p = os.path.join(tmpdir, "c3.png")
        fig.savefig(p, dpi=140, bbox_inches="tight", facecolor="#F8FAFC")
        plt.close(fig)
        charts["interaction"] = p

    return charts


def _insert_chart(doc, path, caption, width_cm=13.5):
    """将图表插入文档，带图注。"""
    if not path:
        return
    pp = doc.add_paragraph()
    pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pp.paragraph_format.space_before = Pt(8)
    pp.add_run().add_picture(path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(10)
    rc = cap.add_run(caption); _cn(rc)
    rc.font.size = Pt(8.5); rc.italic = True; rc.font.color.rgb = GREY


# ──────────────────────────────────────────────────────────────────────────────
# 声明页（精简·无技术细节）
# ──────────────────────────────────────────────────────────────────────────────

def _declaration(doc, nick, audit):
    """关于本报告：简洁声明，不暴露技术细节。"""
    _hrule(doc, ORANGE, "8")
    _heading(doc, "关于本报告", INK2, 11, 2, space_before=8, space_after=6)

    sr_, cl_ = audit.get("source_reliability", "—"), audit.get("confidence_level", "—")

    lines = [
        f"本报告基于 @{nick} 在抖音平台公开展示的数据生成，"
        "包括：粉丝数、点赞、评论、视频标题等公开可查指标。",
        "",
        "以下数据因平台政策无法获取，报告中已明确标注：",
        "完播率 · 真实流量来源 · 实际商品成交量",
        "",
        f"数据可信度：来源可靠度 {sr_} · 置信度 {cl_}",
        "报告结论为参考性建议，不构成商业决策依据。",
        "数据截至报告生成日，账号动态不在此报告范围内。",
    ]
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(line); _cn(r)
        r.font.size = Pt(9); r.font.color.rgb = INK2

    # metafo 印章（右对齐）
    _spacer(doc, 12)
    sp = doc.add_paragraph(); sp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    sr2 = sp.add_run("⬡  metafo"); _cn(sr2)
    sr2.font.size = Pt(9); sr2.font.color.rgb = LGREY


# ──────────────────────────────────────────────────────────────────────────────
# 内容预处理
# ──────────────────────────────────────────────────────────────────────────────

def _split_summary(md: str):
    """从 report_md 抽「一句话先说重点」做执行摘要·其余为诊断主体。"""
    m = re.search(r"##\s*一句话先说重点\s*\n+(.*?)(?=\n##\s)", md, re.S)
    summary = ""
    if m:
        summary = re.sub(r"\*\*", "", m.group(1)).strip().split("\n")[0]
        md = md[:m.start()] + md[m.end():]
    # 去掉报告大标题（封面已承载）、诊断截至说明（声明页会说）
    md = re.sub(r"^#\s+📋 账号诊断报告.*\n", "", md, flags=re.M)
    md = re.sub(r"^>\s*诊断截至.*\n", "", md, flags=re.M)
    md = re.sub(r"^>\s*建议.*前复诊.*\n", "", md, flags=re.M)
    md = re.sub(r"^>\s*我尽量说人话.*\n", "", md, flags=re.M)
    return summary, md.strip()


def _video_rows(v: dict):
    rows = [("视频标题", (v.get("title") or "")[:60]),
            ("点赞", f"{v.get('like', 0):,}"),
            ("评论", f"{v.get('comment', 0):,}"),
            ("转发", f"{v.get('share', 0):,}"),
            ("收藏", f"{v.get('collect', 0):,}"),
            ("时长", f"{v.get('duration_s', 0)} 秒")]
    return rows


def _account_rows(a: dict):
    rows = [("昵称", a.get("nickname", "")),
            ("粉丝数", f"{a.get('follower', 0):,}"),
            ("作品总数", a.get("aweme_count", 0)),
            ("本次分析", f"{a.get('works_analyzed', 0)} 条作品"),
            ("平均点赞", f"{a.get('avg_like', 0):,}"),
            ("最高点赞", f"{a.get('max_like', 0):,}")]
    if a.get("burst_ratio"):
        rows.append(("爆款比", f"{a['burst_ratio']}（>3 有明显爆款）"))
    if a.get("vertical_score") is not None:
        rows.append(("垂直度", f"{a['vertical_score']:.2f}（>0.7 方向集中）"))
    if a.get("hashtags"):
        rows.append(("高频标签", "  /  ".join(a["hashtags"][:6])))
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# 主导出函数
# ──────────────────────────────────────────────────────────────────────────────

def export_docx(result: dict, out_path: str, *, date: str = "", platform: str = "douyin") -> str:
    """account_chain 结果 → 专业 Word · v2.0 · metafo 品牌标准。

    结构（账号为主角·图表入正文·声明精简·无广告语言）：
      封面 → 执行摘要 → 诊断主体（含内嵌图表）
      → 附录·原始数据 → 关于本报告
    """
    if not result.get("ok"):
        raise ValueError(f"结果非 ok·不能导出: {result.get('error')}")
    import hashlib, tempfile

    video   = result.get("video", {}) or {}
    account = result.get("account", {}) or {}
    audit   = result.get("audit", {}) or {}
    nick    = account.get("nickname", "未知账号")
    summary, body = _split_summary(result.get("report_md", ""))

    rpt_no = "MP-" + hashlib.sha1(
        str(account.get("sec_uid") or nick).encode()
    ).hexdigest()[:6].upper() + "-" + (date or "00000000")

    plat_cn = {"douyin": "抖音", "kuaishou": "快手",
               "xiaohongshu": "小红书", "wechat_channels": "视频号"}.get(platform, "抖音")

    # —— 文档初始化 ——
    doc = Document()
    sec = doc.sections[0]
    sec.page_width = Cm(21); sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.54); sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(3.17); sec.right_margin = Cm(3.17)

    _set_style(doc.styles["Normal"], 10.5, INK)
    doc.styles["Normal"].paragraph_format.line_spacing = 1.5
    doc.styles["Normal"].paragraph_format.space_after = Pt(4)
    for sn in ("List Bullet", "List Number"):
        try:
            _set_style(doc.styles[sn], 10.5, INK)
        except KeyError:
            pass

    # —— 页脚 ——
    _setup_footer(doc, nick)

    # —— 封面（主角：账号名）——
    _cover(doc, nick, rpt_no, plat_cn, date)
    _page_break(doc)

    # —— 执行摘要 ——
    _exec_summary(doc, summary, nick)

    # —— 数据卡片（账号核心指标·封面后第一屏）——
    fol = account.get("follower", 0)
    avg_like = account.get("avg_like", 0)
    burst = account.get("burst_ratio")
    cards = [
        (f"{fol:,}", "粉丝数"),
        (f"{avg_like:,}", "平均点赞"),
    ]
    if burst:
        cards.append((f"{burst}×", "爆款比"))
    else:
        cards.append((f"{account.get('aweme_count', 0)}", "发布作品"))
    _stat_cards(doc, cards)

    # —— 图表预生成 ——
    _charts = {}
    try:
        _charts = _make_charts(result, tempfile.mkdtemp(prefix="probe_chart_"))
    except Exception:
        pass  # 图表失败不阻塞

    # —— 诊断主体 ——
    # 把 body 解析后，在「多条找规律」段插入趋势图，在「视频」段插入对比图
    lines = body.split("\n")
    _parse_md(doc, body)

    # 图1：在正文末尾的"这条视频"上下文中插入（简化：正文解析完后追加）
    if "video_vs_avg" in _charts:
        _insert_chart(doc, _charts["video_vs_avg"],
                      "这条视频 vs 账号平均 vs 账号最高（点赞数）")
    if "trend" in _charts:
        _insert_chart(doc, _charts["trend"],
                      "账号点赞演化趋势（按发布先后·早→近）")
    if "interaction" in _charts:
        _insert_chart(doc, _charts["interaction"],
                      "高赞 vs 低赞作品的互动结构对比")

    # —— 附录：原始数据（供核验·不是主阅读路径）——
    _page_break(doc)
    _heading(doc, "附录 · 原始数据（供核验）", INK2, 12, 1, space_before=0, space_after=6)

    _heading(doc, "目标视频数据", INK2, 10.5, 2, space_before=6, space_after=4)
    _data_table(doc, _video_rows(video))
    _spacer(doc, 8)

    _heading(doc, "账号画像数据", INK2, 10.5, 2, space_before=6, space_after=4)
    _data_table(doc, _account_rows(account))

    # —— 声明页 ——
    _spacer(doc, 16)
    _declaration(doc, nick, audit)

    doc.save(out_path)
    return out_path


# ──────────────────────────────────────────────────────────────────────────────
# 文件命名（账号名为主体）
# ──────────────────────────────────────────────────────────────────────────────

def standard_filename(account: dict, platform: str = "douyin", date: str = "") -> str:
    """v2.0 文件名：[账号名]-账号诊断-[YYYYMMDD].docx。

    账号名为主体，不含 probe/引擎等工具名称。
    """
    nick = str(account.get("nickname") or "未知账号")
    nick = re.sub(r'[\\/:*?"<>|｜\s]+', "", nick)[:20] or "未知账号"
    return f"{nick}-账号诊断-{date or '00000000'}.docx"


# ──────────────────────────────────────────────────────────────────────────────
# 验收函数（内部用·不进报告）
# ──────────────────────────────────────────────────────────────────────────────

def validate_report(result: dict, md: str = None) -> dict:
    """动态验收（根据实际情况·非死 checklist）。返回 {pass, items, gaps}。"""
    md = md if md is not None else result.get("report_md", "")
    v, a = result.get("video", {}) or {}, result.get("account", {}) or {}
    works = [w for w in (result.get("works") or []) if isinstance(w, dict)]
    sig = a.get("signature", "") or ""
    blob = sig + " ".join(a.get("hashtags") or [])
    is_biz = any(k in blob for k in ("供货", "直供", "源头", "工厂", "批发", "代工", "OEM"))
    has_claims = any(k in sig for k in ("年", "非遗", "传承", "龙头", "认证", "省级", "专利"))

    items = []
    def chk(name, applicable, ok):
        if applicable:
            items.append((name, bool(ok)))

    chk("诚实·黑盒数据标注", True, ("拿不到" in md or "未公开" in md))
    chk("涉密·不暴露数据源", True, "tikhub" not in md.lower())
    chk("L2 多条规律", len(works) >= 4, "藏着的规律" in md or "多条" in md)
    chk("L3 账号判断", a.get("follower") is not None, "整体判断" in md or "阶段" in md)
    chk("商业号叙事", is_biz, "生活记录" not in md)
    chk("事实核查", has_claims, "晒证据" in md or "核实" in md)
    chk("脚本生成入口", True, "¥29" in md or "脚本" in md)

    gaps = [n for n, ok in items if not ok]
    return {"pass": not gaps, "items": items, "gaps": gaps}


# ──────────────────────────────────────────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import datetime, os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.services.account_chain import _detect_platform, run_from_video_url

    if len(sys.argv) < 2:
        print("用法: python scripts/report_to_docx.py \"<抖音链接>\" [out.docx]")
        sys.exit(1)

    url = sys.argv[1]
    r = run_from_video_url(url)
    if not r.get("ok"):
        print("error:", r.get("error")); sys.exit(1)

    today = datetime.date.today().strftime("%Y%m%d")
    platform = _detect_platform(url)
    out = sys.argv[2] if len(sys.argv) > 2 else standard_filename(
        r.get("account", {}), platform, today)
    print("saved:", export_docx(r, out, date=today, platform=platform))

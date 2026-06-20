#!/usr/bin/env python3
"""probe 账号诊断报告 → 专业 Word(.docx) · 标准报告导出器。

通用工具:接收 account_chain 结果 {ok, report_md, video, account, audit} → 一键出标准 Word。
排版标准(design-governance 破晓品牌·固化为模板):
  页面 A4 · 页边距标准 · 中文微软雅黑 · 标题层级(蓝H1/墨H2) · 正文行距1.5
  · 封面 · 数据表(蓝表头) · 引用块灰底 · 页脚(品牌+页码域) · 品牌色 蓝#1E3A8A/橙#FF7A1A。

用法:
  函数:  from scripts.report_to_docx import export_docx; export_docx(result, "out.docx")
  CLI :  python scripts/report_to_docx.py "<抖音链接>" [out.docx]   # 会跑采集(调授权数据接口·计费)
"""
from __future__ import annotations

import re

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# —— 品牌色(破晓) ——
BLUE = RGBColor(0x1E, 0x3A, 0x8A)
ORANGE = "FF7A1A"
INK = RGBColor(0x1E, 0x29, 0x3B)
INK2 = RGBColor(0x47, 0x55, 0x69)
GREY = RGBColor(0x94, 0x94, 0x95)
CN_FONT = "Microsoft YaHei"


def _cn(run, font=CN_FONT):
    run.font.name = font
    rpr = run._element.get_or_add_rPr()
    rpr.get_or_add_rFonts().set(qn("w:eastAsia"), font)


def _set_style(style, size, color=INK, font=CN_FONT):
    style.font.name = font
    style.font.size = Pt(size)
    style.font.color.rgb = color
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)


def _heading(doc, text, color, size, level=1):
    h = doc.add_heading(level=level)
    h.text = ""
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        t = part[2:-2] if part.startswith("**") else part
        r = h.add_run(t); _cn(r); r.font.size = Pt(size); r.font.color.rgb = color; r.font.bold = True
    return h


def _runs(p, text):
    for part in re.split(r"(\*\*[^*]+\*\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            r = p.add_run(part[2:-2]); r.bold = True; r.font.color.rgb = BLUE
        else:
            r = p.add_run(part)
        _cn(r)


def _shade(p, hexcolor):
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:fill"), hexcolor)
    p._p.get_or_add_pPr().append(sh)


def _hrule(doc, color=ORANGE):
    p = doc.add_paragraph()
    pbdr = OxmlElement("w:pBdr"); bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "12")
    bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), color)
    pbdr.append(bottom); p._p.get_or_add_pPr().append(pbdr)


def _page_number(p):
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MetaFo · probe 情报引擎    第 "); _cn(r); r.font.size = Pt(9); r.font.color.rgb = GREY
    f1 = OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = "PAGE"
    f2 = OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"), "end")
    run = p.add_run(); run._r.append(f1); run._r.append(it); run._r.append(f2)
    run.font.size = Pt(9); run.font.color.rgb = GREY
    r2 = p.add_run(" 页"); _cn(r2); r2.font.size = Pt(9); r2.font.color.rgb = GREY


def _table(doc, rows):
    t = doc.add_table(rows=0, cols=2); t.style = "Light List Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for k, v in rows:
        c = t.add_row().cells
        c[0].width = Cm(3.5); c[1].width = Cm(11.5)
        rk = c[0].paragraphs[0].add_run(str(k)); rk.bold = True; _cn(rk); rk.font.size = Pt(10); rk.font.color.rgb = BLUE
        rv = c[1].paragraphs[0].add_run(str(v)); _cn(rv); rv.font.size = Pt(10)


def _parse_md(doc, md):
    for raw in md.split("\n"):
        s = raw.rstrip()
        if not s or s.startswith("# "):
            continue
        if s.startswith("## "):
            _heading(doc, s[3:].strip(), BLUE, 15, 1)
        elif s.startswith("### "):
            _heading(doc, s[4:].strip(), INK, 12.5, 2)
        elif s.startswith("> "):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.5); _shade(p, "F1F5F9"); _runs(p, s[2:].strip())
        elif s.lstrip().startswith("- "):
            _runs(doc.add_paragraph(style="List Bullet"), s.lstrip()[2:])
        elif re.match(r"^\s*\d+\.\s", s):
            _runs(doc.add_paragraph(style="List Number"), re.sub(r"^\s*\d+\.\s", "", s))
        else:
            _runs(doc.add_paragraph(), s)


def _video_rows(v: dict):
    return [("视频标题", v.get("title", "")), ("点赞", v.get("like", 0)), ("评论", v.get("comment", 0)),
            ("转发", v.get("share", 0)), ("收藏", v.get("collect", 0)), ("时长", f"{v.get('duration_s', 0)} 秒")]


def _account_rows(a: dict):
    rows = [("昵称", a.get("nickname", "")), ("粉丝数", f"{a.get('follower', 0):,}"),
            ("作品总数", a.get("aweme_count", 0)), ("本次分析", f"{a.get('works_analyzed', 0)} 条兄弟视频"),
            ("平均点赞", a.get("avg_like", 0)), ("最高点赞", a.get("max_like", 0))]
    if a.get("burst_ratio"):
        rows.append(("爆款比", f"{a['burst_ratio']}（>3 有明显爆款）"))
    if a.get("vertical_score") is not None:
        rows.append(("垂直度", a["vertical_score"]))
    if a.get("hashtags"):
        rows.append(("高频标签", " / ".join(a["hashtags"][:8])))
    return rows


def _make_charts(result: dict, tmpdir: str) -> list:
    """动态图表:根据实际数据选择画哪些(数据不足的图不画·诚实不硬凑)。返回[(标题,png路径)]。
      图1 这条vs账号水平(有avg+like) · 图2 演化趋势(works≥4) · 图3 高赞vs低赞互动(works≥6)。"""
    import os
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager as fm
    for fp in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc"):
        if os.path.exists(fp):
            plt.rcParams["font.sans-serif"] = [fm.FontProperties(fname=fp).get_name()]
            break
    plt.rcParams["axes.unicode_minus"] = False
    B, O, L = "#1E3A8A", "#FF7A1A", "#93C5FD"
    charts = []
    v, a = result.get("video", {}) or {}, result.get("account", {}) or {}
    works = [w for w in (result.get("works") or []) if isinstance(w, dict)]

    like, avg, mx = v.get("like"), a.get("avg_like"), a.get("max_like")
    if avg and like is not None:
        fig, ax = plt.subplots(figsize=(5.4, 1.9))
        vals = [like or 0, avg or 0, mx or 0]
        bars = ax.barh(["这条视频", "账号平均", "账号最高"], vals, color=[O, B, L])
        ax.invert_yaxis()
        for b, val in zip(bars, vals):
            ax.text(b.get_width(), b.get_y() + b.get_height() / 2, f" {val}", va="center", fontsize=9)
        ax.set_title("这条视频在账号里的位置(点赞)", fontsize=11, color=B)
        ax.spines[["top", "right"]].set_visible(False)
        p = os.path.join(tmpdir, "c1.png"); fig.savefig(p, dpi=130, bbox_inches="tight"); plt.close(fig)
        charts.append(("这条 vs 账号水平", p))

    timed = sorted([w for w in works if w.get("create_time")], key=lambda w: w["create_time"])
    if len(timed) >= 4:
        ys = [w.get("like", 0) or 0 for w in timed]
        fig, ax = plt.subplots(figsize=(5.4, 2.1))
        ax.plot(range(1, len(ys) + 1), ys, marker="o", color=B, linewidth=2)
        ax.fill_between(range(1, len(ys) + 1), ys, color=B, alpha=0.08)
        ax.set_title("作品点赞趋势(按发布先后·早→近)", fontsize=11, color=B)
        ax.spines[["top", "right"]].set_visible(False)
        p = os.path.join(tmpdir, "c2.png"); fig.savefig(p, dpi=130, bbox_inches="tight"); plt.close(fig)
        charts.append(("L2 演化趋势", p))

    if len(works) >= 6:
        sw = sorted(works, key=lambda w: w.get("like", 0) or 0, reverse=True)
        seg = max(1, len(sw) // 3)
        top, bot = sw[:seg], sw[-seg:]
        def m(ws, k):
            return sum((w.get(k, 0) or 0) for w in ws) / len(ws) if ws else 0
        cats = ["点赞", "评论", "收藏", "转发"]
        tv = [m(top, "like"), m(top, "comment"), m(top, "collect"), m(top, "share")]
        bv = [m(bot, "like"), m(bot, "comment"), m(bot, "collect"), m(bot, "share")]
        fig, ax = plt.subplots(figsize=(5.4, 2.1))
        x = range(len(cats)); ww = 0.38
        ax.bar([i - ww / 2 for i in x], [t + 0.1 for t in tv], ww, label="高赞作品", color=O)
        ax.bar([i + ww / 2 for i in x], [b + 0.1 for b in bv], ww, label="低赞作品", color=L)
        ax.set_xticks(list(x)); ax.set_xticklabels(cats, fontsize=9)
        ax.set_yscale("log")
        ax.set_title("高赞 vs 低赞 作品的互动结构", fontsize=11, color=B)
        ax.legend(fontsize=8); ax.spines[["top", "right"]].set_visible(False)
        p = os.path.join(tmpdir, "c3.png"); fig.savefig(p, dpi=130, bbox_inches="tight"); plt.close(fig)
        charts.append(("高赞 vs 低赞 互动", p))

    return charts


def validate_report(result: dict, md: str = None) -> dict:
    """Word 报告动态验收(根据实际情况判断该有什么·非死 checklist)。
    返回 {pass, items:[(项, 达标)], gaps:[...]}。条件项仅在适用时才纳入验收。"""
    md = md if md is not None else result.get("report_md", "")
    v, a = result.get("video", {}) or {}, result.get("account", {}) or {}
    works = [w for w in (result.get("works") or []) if isinstance(w, dict)]
    sig = a.get("signature", "") or ""
    blob = sig + " ".join(a.get("hashtags") or [])
    is_biz = any(k in blob for k in ("供货", "直供", "源头", "工厂", "厂", "批发", "代工", "OEM"))
    has_claims = any(k in sig for k in ("年", "非遗", "传承", "龙头", "认证", "省级", "专利", "获奖"))

    items = []
    def chk(name, applicable, ok):
        if applicable:
            items.append((name, bool(ok)))

    # 固定铁律(总适用)
    chk("诚实·黑盒数据标注「拿不到」", True, ("拿不到" in md or "未公开" in md))
    chk("涉密·不暴露具体数据源", True, ("tikhub" not in md.lower()))
    chk("真实性·标注公开真值", True, ("真实" in md or "公开真" in md))
    # 条件项(根据实际情况)
    chk("L2 多条规律(有≥4条作品时)", len(works) >= 4, "藏着的规律" in md)
    chk("L2 诚实标注(没拿到逐条时)", len(works) < 4, "没拿到" in md)
    chk("L3 账号判断·生命周期", a.get("follower") is not None, "整体判断" in md)
    chk("商业号叙事(B2B不套生活记录)", is_biz, ("生活记录" not in md and "人生纠结" not in md))
    chk("②事实核查(有资质声称时)", has_claims, "晒证据" in md)
    chk("⑥合规提示(有资质声称时)", has_claims, ("虚假宣传" in md or "版权" in md))
    chk("无裸数字(关键数字带对比坐标)", v.get("like") is not None, ("平时" in md or "对比" in md or "vs" in md))

    gaps = [n for n, ok in items if not ok]
    return {"pass": not gaps, "items": items, "gaps": gaps}


def export_docx(result: dict, out_path: str, *, date: str = "") -> str:
    """account_chain 结果 {ok, report_md, video, account, audit} → 专业 Word。"""
    if not result.get("ok"):
        raise ValueError(f"结果非 ok·不能导出:{result.get('error')}")
    video = result.get("video", {}) or {}
    account = result.get("account", {}) or {}
    audit = result.get("audit", {}) or {}
    nick = account.get("nickname", "未知账号")

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
            doc.styles[sn].paragraph_format.line_spacing = 1.4
        except KeyError:
            pass

    # 封面
    tr = doc.add_paragraph().add_run("probe · 抖音账号诊断报告")
    _cn(tr); tr.font.size = Pt(24); tr.bold = True; tr.font.color.rgb = BLUE
    sr = doc.add_paragraph().add_run("实测样例 · 基于真实公开数据生成")
    _cn(sr); sr.italic = True; sr.font.size = Pt(11); sr.font.color.rgb = GREY
    _hrule(doc)
    meta = doc.add_paragraph()
    for label, val in [("分析对象", f"@{nick}"), ("数据来源", "合法授权渠道 · 平台公开数据"),
                       ("分析引擎", "probe account_chain"), ("生成日期", date or "—")]:
        rl = meta.add_run(f"{label}："); _cn(rl); rl.bold = True; rl.font.size = Pt(10); rl.font.color.rgb = INK2
        rv = meta.add_run(f"{val}    "); _cn(rv); rv.font.size = Pt(10)

    # 一、采集数据
    _heading(doc, "一、采集数据概览（平台公开真值 · 无一编造）", BLUE, 15)
    _heading(doc, "目标视频", INK, 12.5, 2); _table(doc, _video_rows(video))
    _heading(doc, "账号画像（含兄弟视频聚合）", INK, 12.5, 2); _table(doc, _account_rows(account))

    # 动态图表(根据实际数据选择画哪些·数据不足不插·诚实不硬凑)
    import tempfile
    _charts = []
    try:
        _charts = _make_charts(result, tempfile.mkdtemp(prefix="probe_chart_"))
    except Exception:
        _charts = []   # 图表失败不阻塞报告生成(降级·正文照出)
    if _charts:
        _heading(doc, "可视化（按数据自动生成）", INK, 12.5, 2)
        for ctitle, cpath in _charts:
            pp = doc.add_paragraph(); pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            pp.add_run().add_picture(cpath, width=Cm(13.5))
            cap = doc.add_paragraph(); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rc = cap.add_run(ctitle); _cn(rc); rc.font.size = Pt(9); rc.italic = True; rc.font.color.rgb = GREY

    # 二、诊断报告
    _heading(doc, "二、诊断报告（说人话 · 照着做）", BLUE, 15)
    _parse_md(doc, result.get("report_md", ""))

    # 三、声明
    _heading(doc, "三、数据来源与可信度声明", BLUE, 15)
    q = doc.add_paragraph(); _shade(q, "EFF6FF"); q.paragraph_format.left_indent = Cm(0.4)
    _runs(q, "本报告由 probe 引擎自动生成：合法授权渠道采集平台公开数据 → L1单条 / L2多条找规律 / L3账号判断 → ②事实核查 + ⑥合规 → 可信度担保 → 确定性规则生成（零 LLM 编造）。")
    sr_, cl_, es_ = audit.get("source_reliability", "?"), audit.get("confidence_level", "?"), audit.get("evidence_strength", "?")
    for line in [
        "**数字真实性**：粉丝/点赞/作品/标签/规律全部为平台**公开真值**，经合法授权渠道采集，未经编造或估算。",
        f"**可信度档位**：来源可靠度={sr_} · 置信度={cl_} · 证据强度={es_}。",
        "**安全与合法机制**：仅通过**合法授权的数据接口**采集公开数据，**不自建、不破解、不绕过平台防护**；采集与处理符合平台规则及数据安全规范，敏感字段脱敏处理。",
        "**样本边界**：单账号、单渠道，未跨源交叉验证；完播率/流量来源/转化等平台未公开数据不可得，诚实标注「拿不到」而非编造。",
    ]:
        _runs(doc.add_paragraph(style="List Bullet"), line)

    _page_number(sec.footer.paragraphs[0])
    doc.save(out_path)
    return out_path


def standard_filename(account: dict, platform: str = "douyin", date: str = "",
                      report_type: str = "account") -> str:
    """Word 报告标准文件名(全 ASCII kebab · 脱敏 · 可追溯)。

    格式: probe-<type>-<platform>-<对象sha1前8>-<YYYYMMDD>.docx
    例  : probe-account-douyin-a1b2c3d4-20260618.docx
      - type     : account(账号诊断) / video(单视频)
      - platform : douyin / kuaishou / xiaohongshu / ...
      - 对象哈希  : sec_uid 或昵称的 sha1 前8位(脱敏·不泄露账号原始ID·唯一可区分)
      - 日期      : YYYYMMDD
    """
    import hashlib
    ident = account.get("sec_uid") or account.get("nickname") or "unknown"
    h = hashlib.sha1(str(ident).encode("utf-8")).hexdigest()[:8]
    return f"probe-{report_type}-{platform}-{h}-{date or '00000000'}.docx"


if __name__ == "__main__":
    import datetime
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from app.services.account_chain import _detect_platform, run_from_video_url

    if len(sys.argv) < 2:
        print("用法: python scripts/report_to_docx.py \"<抖音链接>\" [out.docx]")
        print("  不给 out.docx 时按标准命名: probe-account-<平台>-<哈希8>-<YYYYMMDD>.docx")
        sys.exit(1)
    url = sys.argv[1]
    r = run_from_video_url(url)
    if not r.get("ok"):
        print("error:", r.get("error")); sys.exit(1)
    today = datetime.date.today().strftime("%Y%m%d")
    out = sys.argv[2] if len(sys.argv) > 2 else standard_filename(
        r.get("account", {}), _detect_platform(url), today)
    print("saved:", export_docx(r, out, date=today))

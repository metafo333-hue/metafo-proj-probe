#!/usr/bin/env python3
"""probe 账号诊断报告 → 专业 Word(.docx) · 标准报告导出器。

通用工具:接收 account_chain 结果 {ok, report_md, video, account, audit} → 一键出标准 Word。
排版标准(design-governance 破晓品牌·固化为模板):
  页面 A4 · 页边距标准 · 中文微软雅黑 · 标题层级(蓝H1/墨H2) · 正文行距1.5
  · 封面 · 数据表(蓝表头) · 引用块灰底 · 页脚(品牌+页码域) · 品牌色 蓝#1E3A8A/橙#FF7A1A。

用法:
  函数:  from scripts.report_to_docx import export_docx; export_docx(result, "out.docx")
  CLI :  python scripts/report_to_docx.py "<抖音链接>" [out.docx]   # 会跑采集(调TikHub付费)
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
    for label, val in [("分析对象", f"@{nick}"), ("数据来源", "TikHub 授权采集（抖音公开数据）"),
                       ("分析引擎", "probe account_chain"), ("生成日期", date or "—")]:
        rl = meta.add_run(f"{label}："); _cn(rl); rl.bold = True; rl.font.size = Pt(10); rl.font.color.rgb = INK2
        rv = meta.add_run(f"{val}    "); _cn(rv); rv.font.size = Pt(10)

    # 一、采集数据
    _heading(doc, "一、采集数据概览（TikHub 真值 · 无一编造）", BLUE, 15)
    _heading(doc, "目标视频", INK, 12.5, 2); _table(doc, _video_rows(video))
    _heading(doc, "账号画像（含兄弟视频聚合）", INK, 12.5, 2); _table(doc, _account_rows(account))

    # 二、诊断报告
    _heading(doc, "二、诊断报告（说人话 · 照着做）", BLUE, 15)
    _parse_md(doc, result.get("report_md", ""))

    # 三、声明
    _heading(doc, "三、数据来源与可信度声明", BLUE, 15)
    q = doc.add_paragraph(); _shade(q, "EFF6FF"); q.paragraph_format.left_indent = Cm(0.4)
    _runs(q, "本报告由 probe 引擎 account_chain 链路自动生成：抖音链接 → TikHub 授权采集 → L1单条/L2多条找规律/L3账号判断 → ②事实核查+⑥合规 → 八闸可信度担保 → 确定性规则生成（零 LLM 编造）。")
    sr_, cl_, es_ = audit.get("source_reliability", "?"), audit.get("confidence_level", "?"), audit.get("evidence_strength", "?")
    for line in [
        "**数字真实性**：粉丝/点赞/作品/标签/规律全部为 TikHub 采集的抖音公开真值，未经编造或估算。",
        f"**可信度档位**：source_reliability={sr_} · confidence={cl_} · evidence={es_}。",
        "**样本边界**：单账号、单数据源，未跨竞品交叉验证；完播率/流量来源/转化等黑盒数据不可得，诚实标注「拿不到」。",
        "**合规**：只走 TikHub 授权源，不自建破签名爬虫（probe 数据来源铁律）。",
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

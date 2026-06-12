"""交付形态渲染层 · Wave 2 交付层。

render(report, fmt) 支持 fmt ∈ {text, markdown, html}。
- text/markdown：真实实现
- html：基础实现（内嵌 CSS · 可浏览器直接打开）
- image/ppt/video：stub 接口，标注 → MetaDesign / MetaCut

C-8 保证：render 层仅接收已经过 guards.redact_by_tier 的 report，
          不直接接触第三方原始数据。
"""
from __future__ import annotations

import html as _html_lib
from typing import Any, Literal

FmtLiteral = Literal["text", "markdown", "html", "image", "ppt", "video"]

_RATING_EMOJI = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}
_LOCK_SYMBOL = "🔒"


# ─────────────────── 内部辅助 ───────────────────

def _get_s1(report: dict) -> dict:
    return report.get("s1_first_screen") or {}


def _get_s2(report: dict) -> dict:
    return report.get("s2_fact_check") or {}


def _get_s3(report: dict) -> dict:
    return report.get("s3_content_breakdown") or {}


def _get_s4(report: dict) -> dict:
    return report.get("s4_competitor_matrix") or {}


def _get_s5(report: dict) -> dict:
    return report.get("s5_recreation_paths") or {}


def _get_s6(report: dict) -> dict:
    return report.get("s6_risk_compliance") or {}


def _get_s7(report: dict) -> dict:
    return report.get("s7_full_detail") or {}


def _depth(report: dict) -> str:
    return report.get("depth", "unknown")


def _rating_line(report: dict) -> str:
    """从 report 中找评级（兼容 public 裁剪后字段在顶层）。"""
    s1 = _get_s1(report)
    rating = s1.get("rating") or report.get("rating") or "?"
    emoji = _RATING_EMOJI.get(rating, "⬜")
    return f"{emoji} 综合评级：{rating}"


# ─────────────────── text 渲染 ───────────────────

def _render_text(report: dict) -> str:
    depth = _depth(report)
    lines: list[str] = []

    lines.append("=" * 52)
    lines.append("  probe 情报报告")
    lines.append("=" * 52)
    lines.append(_rating_line(report))

    s1 = _get_s1(report)
    if s1:
        lines.append(f"结论：{s1.get('headline', '')}")
        lines.append(f"拍板：{s1.get('decision_tip', '')}")
        steps = s1.get("action_steps") or []
        if steps:
            lines.append("行动：" + " → ".join(str(s) for s in steps))
    else:
        lines.append(f"结论：{report.get('headline', '')}")
        if report.get("decision_tip"):
            lines.append(f"拍板：{report['decision_tip']}")

    if depth == "public":
        lines.append("")
        lines.append(f"{_LOCK_SYMBOL} {report.get('unlock_hint', '登录解锁更多')}")
        lines.append("=" * 52)
        return "\n".join(lines)

    # ② 真相核查
    s2 = _get_s2(report)
    if s2:
        lines.append("")
        lines.append("── ② 真相核查 ──")
        lines.append(f"总体可信度：{s2.get('overall_credibility', '未评估')}")
        for c in (s2.get("claims_summary") or []):
            lines.append(f"  {c.get('verdict', '❓')} {c.get('claim', '')} — {c.get('reason', '')}")
        if s2.get("_stub"):
            lines.append("  （真相核查待 LLM 接入）")

    # ③ 内容拆解
    s3 = _get_s3(report)
    if s3:
        lines.append("")
        lines.append("── ③ 内容拆解 ──")
        lines.append(f"结构公式：{s3.get('structure_formula', '—')}")
        if not s3.get("_preview"):
            lines.append(f"钩子：{s3.get('hook_summary', '—')}")
            tags = s3.get("reuse_tags") or []
            if tags:
                lines.append(f"复用标签：{' · '.join(str(t) for t in tags)}")
        else:
            lines.append(f"  {_LOCK_SYMBOL} 钩子/复用标签需付费档解锁")

    # ④ 竞品横评
    s4 = _get_s4(report)
    if s4.get("locked"):
        lines.append("")
        lines.append(f"── ④ 竞品横评 {_LOCK_SYMBOL} ──")
        lines.append(f"  {s4.get('unlock_hint', '付费档解锁')}")
    elif s4.get("items"):
        lines.append("")
        lines.append("── ④ 竞品横评 ──")
        for item in s4["items"]:
            lines.append(f"  {item.get('name', '')} | {item.get('score', '')} | {item.get('note', '')}")

    # ⑤ 二创方案
    s5 = _get_s5(report)
    lines.append("")
    lines.append("── ⑤ 二创方案 ──")
    if s5.get("_preview") or s5.get("locked"):
        hint = s5.get("preview_hint") or ""
        if hint:
            lines.append(f"  推荐方向：{hint}")
        lines.append(f"  {_LOCK_SYMBOL} {s5.get('unlock_hint', '完整三路需付费档解锁')}")
    elif s5.get("priority"):
        lines.append(f"推荐：{s5.get('priority')} — {s5.get('priority_reason', '')}")
        for key, label in [("borrow", "借路"), ("adapt", "换路"), ("remix", "串路")]:
            path = s5.get(key) or {}
            if path:
                lines.append(f"  {label}：{path.get('desc', '')} （投入:{path.get('input','')} 版权:{path.get('copyright_risk','')}）")
    else:
        lines.append("  （二创分析待完成）")

    # ⑥ 风险合规
    s6 = _get_s6(report)
    lines.append("")
    lines.append("── ⑥ 风险合规 ──")
    if s6.get("locked"):
        lines.append(f"  风险等级：{s6.get('risk_level', '—')}")
        lines.append(f"  {_LOCK_SYMBOL} {s6.get('unlock_hint', '合规详情需付费档解锁')}")
    else:
        lines.append(f"风险等级：{s6.get('risk_level', '—')}")
        lines.append(f"合规说明：{s6.get('compliance_note', '—')}")

    # ⑦ 完整明细
    s7 = _get_s7(report)
    if s7:
        lines.append("")
        lines.append("── ⑦ 完整明细 ──")
        lines.append(f"类型：{s7.get('kind', '')} | 来源域：{s7.get('source_hint', '')} | 字数：{s7.get('word_count_hint', 0)}")
        dim = s7.get("dimensions_summary") or {}
        for k, v in dim.items():
            lines.append(f"  {k}: {v}")

    lines.append("=" * 52)
    if report.get("unlock_hint"):
        lines.append(report["unlock_hint"])
    return "\n".join(lines)


# ─────────────────── markdown 渲染 ───────────────────

def _render_markdown(report: dict) -> str:
    depth = _depth(report)
    lines: list[str] = []

    lines.append("# probe 情报报告\n")
    lines.append(f"## ① 首屏速判\n")
    lines.append(_rating_line(report) + "\n")

    s1 = _get_s1(report)
    if s1:
        lines.append(f"**结论**：{s1.get('headline', '')}\n")
        lines.append(f"**15 秒拍板**：{s1.get('decision_tip', '')}\n")
        steps = s1.get("action_steps") or []
        if steps:
            lines.append("**三步行动**：\n")
            for i, s in enumerate(steps, 1):
                lines.append(f"{i}. {s}")
            lines.append("")
    else:
        lines.append(f"**结论**：{report.get('headline', '')}\n")
        if report.get("decision_tip"):
            lines.append(f"**拍板**：{report['decision_tip']}\n")

    if depth == "public":
        lines.append(f"\n> {_LOCK_SYMBOL} {report.get('unlock_hint', '登录解锁更多')}\n")
        return "\n".join(lines)

    # ② 真相核查
    s2 = _get_s2(report)
    if s2:
        lines.append("\n## ② 真相核查\n")
        lines.append(f"**总体可信度**：{s2.get('overall_credibility', '未评估')}\n")
        claims = s2.get("claims_summary") or []
        if claims:
            lines.append("| 声称 | 判定 | 依据 |")
            lines.append("|------|------|------|")
            for c in claims:
                lines.append(f"| {c.get('claim','')} | {c.get('verdict','❓')} | {c.get('reason','')} |")
            lines.append("")
        if s2.get("_stub"):
            lines.append("> 真相核查待 LLM 接入\n")

    # ③ 内容拆解
    s3 = _get_s3(report)
    if s3:
        lines.append("\n## ③ 内容拆解\n")
        lines.append(f"**结构公式**：`{s3.get('structure_formula', '—')}`\n")
        if not s3.get("_preview"):
            if s3.get("hook_summary"):
                lines.append(f"**钩子**：{s3['hook_summary']}\n")
            tags = s3.get("reuse_tags") or []
            if tags:
                lines.append(f"**复用标签**：{' · '.join(str(t) for t in tags)}\n")
        else:
            lines.append(f"> {_LOCK_SYMBOL} 钩子/复用标签需付费档解锁\n")

    # ④ 竞品横评
    s4 = _get_s4(report)
    lines.append("\n## ④ 竞品横评\n")
    if s4.get("locked"):
        lines.append(f"> {_LOCK_SYMBOL} {s4.get('unlock_hint', '付费档解锁')}\n")
    elif s4.get("items"):
        lines.append("| 名称 | 评分 | 备注 |")
        lines.append("|------|------|------|")
        for item in s4["items"]:
            lines.append(f"| {item.get('name','')} | {item.get('score','')} | {item.get('note','')} |")
        lines.append("")

    # ⑤ 二创方案
    s5 = _get_s5(report)
    lines.append("\n## ⑤ 二创方案\n")
    if s5.get("_preview") or s5.get("locked"):
        hint = s5.get("preview_hint") or ""
        if hint:
            lines.append(f"**推荐方向**：{hint}\n")
        lines.append(f"> {_LOCK_SYMBOL} {s5.get('unlock_hint', '完整三路需付费档解锁')}\n")
    elif s5.get("priority"):
        lines.append(f"**推荐**：{s5.get('priority')} — {s5.get('priority_reason', '')}\n")
        for key, label in [("borrow", "借路"), ("adapt", "换路"), ("remix", "串路")]:
            path = s5.get(key) or {}
            if path:
                lines.append(f"**{label}**：{path.get('desc', '')}  ")
                lines.append(f"- 投入：{path.get('input','')} · 版权风险：{path.get('copyright_risk','')}\n")
    else:
        lines.append("> 二创分析待完成\n")

    # ⑥ 风险合规
    s6 = _get_s6(report)
    lines.append("\n## ⑥ 风险合规\n")
    if s6.get("locked"):
        lines.append(f"**风险等级**：{s6.get('risk_level', '—')}\n")
        lines.append(f"> {_LOCK_SYMBOL} {s6.get('unlock_hint', '合规详情需付费档解锁')}\n")
    else:
        lines.append(f"**风险等级**：{s6.get('risk_level', '—')}\n")
        lines.append(f"**合规说明**：{s6.get('compliance_note', '—')}\n")

    # ⑦ 完整明细
    s7 = _get_s7(report)
    if s7:
        lines.append("\n## ⑦ 完整明细\n")
        lines.append(f"**类型**：{s7.get('kind','')} | **来源域**：{s7.get('source_hint','')} | **字数**：{s7.get('word_count_hint',0)}\n")
        dim = s7.get("dimensions_summary") or {}
        if dim:
            lines.append("| 维度 | 值 |")
            lines.append("|------|----|")
            for k, v in dim.items():
                lines.append(f"| {k} | {v} |")
            lines.append("")

    if report.get("unlock_hint"):
        lines.append(f"\n---\n> {report['unlock_hint']}")

    return "\n".join(lines)


# ─────────────────── html 渲染（基础实现） ───────────────────

_HTML_CSS = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  max-width:800px;margin:0 auto;padding:24px;background:#f9fafb;color:#111}
h1{font-size:1.4rem;color:#1e3a8a}h2{font-size:1.1rem;color:#374151;margin-top:24px}
.rating-A{color:#16a34a}.rating-B{color:#ca8a04}.rating-C{color:#ea580c}.rating-D{color:#dc2626}
.chip{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8rem;
  background:#e5e7eb;margin:2px}
.locked{background:#fef3c7;padding:8px;border-radius:4px;color:#92400e}
table{border-collapse:collapse;width:100%}th,td{border:1px solid #e5e7eb;padding:6px 10px;text-align:left}
th{background:#f3f4f6}
"""

def _e(s: Any) -> str:
    return _html_lib.escape(str(s))


def _render_html(report: dict) -> str:
    depth = _depth(report)
    s1 = _get_s1(report)
    rating = s1.get("rating") or report.get("rating") or "?"
    emoji = _RATING_EMOJI.get(rating, "⬜")
    headline = _e(s1.get("headline") or report.get("headline") or "")
    decision_tip = _e(s1.get("decision_tip") or report.get("decision_tip") or "")
    steps = s1.get("action_steps") or []

    parts = [
        f"<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>"
        f"<title>probe 情报报告</title><style>{_HTML_CSS}</style></head><body>",
        "<h1>probe 情报报告</h1>",
        f"<h2>① 首屏速判</h2>",
        f"<p class='rating-{_e(rating)}'><strong>{_e(emoji)} 综合评级：{_e(rating)}</strong></p>",
        f"<p><strong>结论：</strong>{headline}</p>",
    ]
    if decision_tip:
        parts.append(f"<p><strong>15 秒拍板：</strong>{decision_tip}</p>")
    if steps:
        parts.append("<ol>" + "".join(f"<li>{_e(s)}</li>" for s in steps) + "</ol>")

    if depth == "public":
        hint = _e(report.get("unlock_hint") or "登录解锁更多")
        parts.append(f"<div class='locked'>{_LOCK_SYMBOL} {hint}</div>")
        parts.append("</body></html>")
        return "".join(parts)

    # ② 真相核查
    s2 = _get_s2(report)
    if s2:
        parts.append("<h2>② 真相核查</h2>")
        parts.append(f"<p>总体可信度：<strong>{_e(s2.get('overall_credibility','未评估'))}</strong></p>")
        claims = s2.get("claims_summary") or []
        if claims:
            rows = "".join(
                f"<tr><td>{_e(c.get('claim',''))}</td><td>{_e(c.get('verdict',''))}</td>"
                f"<td>{_e(c.get('reason',''))}</td></tr>"
                for c in claims
            )
            parts.append(f"<table><tr><th>声称</th><th>判定</th><th>依据</th></tr>{rows}</table>")

    # ③ 内容拆解
    s3 = _get_s3(report)
    if s3:
        parts.append("<h2>③ 内容拆解</h2>")
        parts.append(f"<p>结构公式：<code>{_e(s3.get('structure_formula','—'))}</code></p>")
        if not s3.get("_preview"):
            if s3.get("hook_summary"):
                parts.append(f"<p>钩子：{_e(s3['hook_summary'])}</p>")
            tags = s3.get("reuse_tags") or []
            if tags:
                chips = "".join(f"<span class='chip'>{_e(t)}</span>" for t in tags)
                parts.append(f"<p>复用标签：{chips}</p>")
        else:
            hint = _e(s3.get("unlock_hint") or "钩子/复用标签需付费档解锁")
            parts.append(f"<div class='locked'>{_LOCK_SYMBOL} {hint}</div>")

    # ④ 竞品横评
    s4 = _get_s4(report)
    parts.append("<h2>④ 竞品横评</h2>")
    if s4.get("locked"):
        parts.append(f"<div class='locked'>{_LOCK_SYMBOL} {_e(s4.get('unlock_hint','付费档解锁'))}</div>")
    elif s4.get("items"):
        rows = "".join(
            f"<tr><td>{_e(i.get('name',''))}</td><td>{_e(i.get('score',''))}</td>"
            f"<td>{_e(i.get('note',''))}</td></tr>"
            for i in s4["items"]
        )
        parts.append(f"<table><tr><th>名称</th><th>评分</th><th>备注</th></tr>{rows}</table>")

    # ⑤ 二创方案
    s5 = _get_s5(report)
    parts.append("<h2>⑤ 二创方案</h2>")
    if s5.get("_preview") or s5.get("locked"):
        hint_txt = s5.get("preview_hint") or ""
        if hint_txt:
            parts.append(f"<p>推荐方向：{_e(hint_txt)}</p>")
        parts.append(f"<div class='locked'>{_LOCK_SYMBOL} {_e(s5.get('unlock_hint','完整三路需付费档解锁'))}</div>")
    elif s5.get("priority"):
        parts.append(f"<p><strong>推荐：{_e(s5['priority'])}</strong> — {_e(s5.get('priority_reason',''))}</p>")
        for key, label in [("borrow", "借路"), ("adapt", "换路"), ("remix", "串路")]:
            path = s5.get(key) or {}
            if path:
                parts.append(
                    f"<p><strong>{_e(label)}</strong>：{_e(path.get('desc',''))}"
                    f" <span class='chip'>投入:{_e(path.get('input',''))}</span>"
                    f" <span class='chip'>版权:{_e(path.get('copyright_risk',''))}</span></p>"
                )
    else:
        parts.append("<p>二创分析待完成</p>")

    # ⑥ 风险合规
    s6 = _get_s6(report)
    parts.append("<h2>⑥ 风险合规</h2>")
    if s6.get("locked"):
        parts.append(f"<p>风险等级：<strong>{_e(s6.get('risk_level','—'))}</strong></p>")
        parts.append(f"<div class='locked'>{_LOCK_SYMBOL} {_e(s6.get('unlock_hint','合规详情需付费档解锁'))}</div>")
    else:
        parts.append(f"<p>风险等级：<strong>{_e(s6.get('risk_level','—'))}</strong></p>")
        parts.append(f"<p>合规说明：{_e(s6.get('compliance_note','—'))}</p>")

    # ⑦ 完整明细
    s7 = _get_s7(report)
    if s7:
        parts.append("<h2>⑦ 完整明细</h2>")
        parts.append(
            f"<p>类型：{_e(s7.get('kind',''))} | "
            f"来源域：{_e(s7.get('source_hint',''))} | "
            f"字数：{_e(s7.get('word_count_hint',0))}</p>"
        )
        dim = s7.get("dimensions_summary") or {}
        if dim:
            rows = "".join(f"<tr><td>{_e(k)}</td><td>{_e(v)}</td></tr>" for k, v in dim.items())
            parts.append(f"<table><tr><th>维度</th><th>值</th></tr>{rows}</table>")

    if report.get("unlock_hint"):
        parts.append(f"<hr><p style='color:#6b7280'>{_e(report['unlock_hint'])}</p>")

    parts.append("</body></html>")
    return "".join(parts)


# ─────────────────── stub 接口（向 MetaDesign / MetaCut 路由） ───────────────────

def _render_image_stub(report: dict) -> dict:
    """图片渲染 stub → MetaDesign（spec-engine·排版交付）。

    TODO(Wave N)：调用 MetaDesign L1 契约 /api/v1/invoke，传入七段报告结论，
                  由 MetaDesign 负责排版产出 PNG/SVG。
    """
    return {
        "status": "stub",
        "message": "图片渲染需接入 MetaDesign 引擎（→ spec-engine / packages/metadesign-engine）",
        "handoff": {
            "engine": "MetaDesign",
            "contract_endpoint": "/api/v1/invoke",
            "payload_hint": "传入 七段报告 markdown 文本 + brand_anchor",
        },
    }


def _render_ppt_stub(report: dict) -> dict:
    """PPT 渲染 stub → MetaDesign。

    TODO(Wave N)：MetaDesign 支持 PPTX 输出模板后接入。
    """
    return {
        "status": "stub",
        "message": "PPT 渲染需接入 MetaDesign 引擎（PPTX 输出模板待 Wave N 开发）",
        "handoff": {"engine": "MetaDesign", "output_format": "pptx"},
    }


def _render_video_stub(report: dict) -> dict:
    """视频渲染 stub → MetaCut（元剪·视频引擎）。

    TODO(Wave N)：MetaCut 支持「脚本 → 视频」后，传入二创方案脚本 + 素材列表。
    """
    return {
        "status": "stub",
        "message": "视频渲染需接入 MetaCut 引擎（→ metafocut / MetaCut·元剪）",
        "handoff": {
            "engine": "MetaCut",
            "contract_endpoint": "/api/v1/invoke",
            "payload_hint": "传入 s5_recreation_paths 二创方案 + 原始内容素材引用",
        },
    }


# ─────────────────── 公开接口 ───────────────────

def render(report: dict[str, Any], fmt: FmtLiteral = "markdown") -> Any:
    """渲染七段报告为指定交付形态。

    Args:
        report: 已经过 guards.redact_by_tier 处理的报告 dict（或 SevenSectionReport.to_dict()）。
        fmt:    text / markdown / html / image / ppt / video

    Returns:
        str（text/markdown/html）或 dict（stub 形态）。

    C-8 说明：render 层不接触第三方原始数据，仅处理已加工的报告结构。
    """
    if fmt == "text":
        return _render_text(report)
    if fmt == "markdown":
        return _render_markdown(report)
    if fmt == "html":
        return _render_html(report)
    if fmt == "image":
        return _render_image_stub(report)
    if fmt == "ppt":
        return _render_ppt_stub(report)
    if fmt == "video":
        return _render_video_stub(report)
    raise ValueError(f"不支持的交付形态 fmt={fmt!r}，支持：text/markdown/html/image/ppt/video")

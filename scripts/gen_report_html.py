#!/usr/bin/env python3
"""report.md → report.html · 硅基流动免费模型排版 + Python 保底渲染。

用法:
    # 单个案例
    python3 scripts/gen_report_html.py <run_id>

    # 批量（所有案例）
    python3 scripts/gen_report_html.py --all

    # 强制重新生成（已有 html 也覆盖）
    python3 scripts/gen_report_html.py --all --force

原理:
    1. 读 data/cases/{run_id}/report.md
    2. 调 SiliconFlow Qwen2.5-7B-Instruct（免费额度）转 HTML
    3. 注入品牌样式 + 安全过滤
    4. 失败 → Python 保底渲染（不调 API·100% 可用）
    5. 写 data/cases/{run_id}/report.html
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import re
import urllib.request

_ROOT      = pathlib.Path(__file__).resolve().parents[1]
_CASES_DIR = _ROOT / "data" / "cases"
_SF_URL    = "https://api.siliconflow.cn/v1/chat/completions"
_SF_MODEL  = "Qwen/Qwen2.5-7B-Instruct"   # 免费额度

# ── 品牌 CSS（注入到每个 report.html 头部）───────────────────────────────────
_SCOPED_CSS = """
<style>
.prb { font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;font-size:14px;line-height:1.75;color:#1E293B;max-width:100%;word-break:break-word }
.prb h1,.prb h2 { color:#1E3A8A;margin:24px 0 10px;padding-bottom:8px;border-bottom:2px solid #EFF6FF;font-size:16px }
.prb h3 { color:#1E293B;font-size:14px;font-weight:700;margin:16px 0 8px }
.prb h4 { color:#475569;font-size:13px;font-weight:600;margin:12px 0 6px }
.prb p  { margin:0 0 10px }
.prb strong { color:#1E3A8A }
.prb em  { color:#FF7A1A;font-style:normal;font-weight:600 }
.prb blockquote {
  background:#F1F5F9;border-left:3px solid #FF7A1A;
  padding:10px 14px;margin:10px 0;border-radius:0 6px 6px 0;
  font-size:13px;color:#475569
}
.prb ul,.prb ol { margin:8px 0 10px 0;padding-left:0;list-style:none }
.prb li { padding:4px 0 4px 20px;position:relative;border-bottom:1px solid #F8FAFC }
.prb li:last-child { border-bottom:none }
.prb li::before { content:'▸';position:absolute;left:4px;color:#FF7A1A;font-size:11px;top:6px }
.prb ol li::before { content:counter(li)'.';counter-increment:li;font-weight:700;color:#1E3A8A;font-size:12px }
.prb ol { counter-reset:li }
.prb table { width:100%;border-collapse:collapse;margin:12px 0;font-size:13px }
.prb th { background:#1E3A8A;color:#fff;padding:8px 10px;text-align:left;font-size:12px }
.prb td { padding:7px 10px;border-bottom:1px solid #E2E8F0 }
.prb tr:nth-child(even) td { background:#EFF6FF }
.prb hr { border:none;border-top:2px solid #EFF6FF;margin:20px 0 }
.prb code { background:#F1F5F9;border:1px solid #E2E8F0;padding:1px 5px;border-radius:3px;font-size:12px;font-family:monospace }
/* 核心结论摘要框 */
.prb .bluf {
  background:#FFF7ED;border-left:4px solid #FF7A1A;
  padding:14px 16px;border-radius:0 8px 8px 0;
  margin:0 0 20px;font-size:14px;font-weight:500
}
.prb .bluf strong { color:#FF7A1A;font-size:15px }
/* 行动项颜色 */
.prb .act-red  { color:#B91C1C;font-weight:600 }
.prb .act-yel  { color:#92400E;font-weight:600 }
/* 可信度/诚实声明块 */
.prb .honest {
  background:#EFF6FF;border:1px solid #BFDBFE;
  padding:10px 14px;border-radius:6px;
  font-size:12px;color:#1E3A8A;margin:12px 0
}
</style>
"""

# ── SiliconFlow 提示词 ────────────────────────────────────────────────────────
_PROMPT = """你是专业的商业诊断报告排版专家。将以下 Markdown 格式的短视频账号诊断报告，转换为精美的 HTML 片段。

【严格输出规则】
- 只输出 <div class="prb">...</div> 这一个根元素，无任何额外文字或解释
- 不含 <!DOCTYPE>/<html>/<head>/<body> 标签
- 所有样式通过 class 实现，class 名称限用如下列表（已在外部定义好）

【可用 class】prb / bluf / honest / act-red / act-yel

【排版转换规则】
1. 「## 一句话先说重点」段 → <div class="bluf"><strong>…</strong> 正文…</div>，放在最前
2. ## 标题 → <h2>，### 标题 → <h3>，#### → <h4>
3. **文字** → <strong>，*文字* → <em>
4. > 引用块 → <blockquote>
5. - 或 * 列表项 → <ul><li>
6. 有序列表 → <ol><li>
7. 表格 → <table><thead><tr><th>…</th></tr></thead><tbody>…</tbody></table>
8. 🔴 开头的行 → class="act-red"，🟡 开头 → class="act-yel"
9. 「这份分析有多可信」「拿不到」「绝不瞎编」相关段 → 包在 <div class="honest">
10. --- 水平线 → <hr>
11. `代码` → <code>
12. 保留所有 emoji 原样（🔴🟡👉✅❌⚠️📊等）
13. 段落之间用 <p> 包裹

Markdown 报告：
---
{md}
---
直接输出 HTML，不要任何说明。"""


def _sf_convert(md: str, key: str) -> str | None:
    """调硅基流动 Qwen2.5-7B 把 md 转 HTML 片段。失败返回 None。"""
    payload = {
        "model": _SF_MODEL,
        "temperature": 0.2,
        "max_tokens": min(16000, max(4000, len(md) * 2)),
        "messages": [{"role": "user", "content": _PROMPT.format(md=md)}],
    }
    try:
        req = urllib.request.Request(
            _SF_URL, data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.load(r)
        raw = (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content", "").strip()
        # 验证：必须以 <div 开头且含 prb
        if raw and raw.startswith("<") and "prb" in raw:
            return raw
        return None
    except Exception as e:
        print(f"    SiliconFlow 调用失败: {e}")
        return None


# ── Python 保底渲染（纯规则·100% 可靠）────────────────────────────────────────
def _py_render(md: str) -> str:
    """Markdown → HTML（保底·不调 API）"""
    lines = md.split("\n")
    out, i = [], 0

    def esc(s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def inline(s: str) -> str:
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*",     r"<em>\1</em>", s)
        s = re.sub(r"`(.+?)`",       r"<code>\1</code>", s)
        return s

    bluf_done = False
    in_ul = in_ol = in_tbl = False

    def close_lists():
        nonlocal in_ul, in_ol, in_tbl
        if in_ul:  out.append("</ul>"); in_ul = False
        if in_ol:  out.append("</ol>"); in_ol = False
        if in_tbl: out.append("</tbody></table>"); in_tbl = False

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()

        # 一句话先说重点 → bluf 框
        if not bluf_done and s.startswith("## 一句话先说重点"):
            close_lists()
            i += 1
            bluf_lines = []
            while i < len(lines) and not lines[i].strip().startswith("## "):
                bluf_lines.append(lines[i].strip())
                i += 1
            bluf_text = " ".join(b for b in bluf_lines if b)
            out.append(f'<div class="bluf">{inline(bluf_text)}</div>')
            bluf_done = True
            continue

        # 标题
        if s.startswith("#### "):
            close_lists(); out.append(f"<h4>{inline(s[5:])}</h4>")
        elif s.startswith("### "):
            close_lists(); out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "):
            close_lists(); out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "):
            close_lists(); out.append(f"<h2>{inline(s[2:])}</h2>")

        # 水平线
        elif re.match(r"^-{3,}$", s):
            close_lists(); out.append("<hr>")

        # 引用
        elif s.startswith("> "):
            close_lists()
            out.append(f"<blockquote>{inline(s[2:])}</blockquote>")

        # 无序列表
        elif re.match(r"^[-*]\s", s):
            if not in_ul: out.append("<ul>"); in_ul = True
            if in_ol: out.append("</ol>"); in_ol = False
            cls = "act-red" if s.startswith("🔴") or "🔴" in s[:3] else \
                  "act-yel" if s.startswith("🟡") or "🟡" in s[:3] else ""
            text = re.sub(r"^[-*]\s+", "", s)
            out.append(f'<li class="{cls}">{inline(text)}</li>' if cls else f"<li>{inline(text)}</li>")

        # 有序列表
        elif re.match(r"^\d+\.\s", s):
            if not in_ol: out.append("<ol>"); in_ol = True
            if in_ul: out.append("</ul>"); in_ul = False
            text = re.sub(r"^\d+\.\s+", "", s)
            out.append(f"<li>{inline(text)}</li>")

        # 表格
        elif s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not in_tbl:
                out.append('<table><thead><tr>')
                out.append("".join(f"<th>{inline(c)}</th>" for c in cells))
                out.append("</tr></thead><tbody>")
                in_tbl = True
                i += 1  # 跳过 | --- | --- |
                continue
            else:
                if re.match(r"^\|[-| :]+\|$", s): pass  # 分隔行跳过
                else:
                    out.append("<tr>")
                    out.append("".join(f"<td>{inline(c)}</td>" for c in cells))
                    out.append("</tr>")

        # 可信度段
        elif "拿不到" in s or "绝不瞎编" in s or "这份分析有多可信" in s:
            close_lists()
            out.append(f'<div class="honest">{inline(s)}</div>')

        # 空行
        elif not s:
            close_lists()

        # 普通段落
        else:
            close_lists()
            if s:
                out.append(f"<p>{inline(s)}</p>")

        i += 1

    close_lists()
    return "\n".join(out)


def _build_html(run_id: str, account_name: str, date: str, body: str) -> str:
    """组装完整 report.html（含品牌 CSS + meta）"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>元探报告 · {account_name}</title>
{_SCOPED_CSS}
</head>
<body style="margin:0;padding:16px 20px 40px;background:#fff">
<div style="font-size:11px;color:#94A3B8;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #E2E8F0">
  <strong style="color:#1E3A8A">元探 MetaProbe</strong> · {account_name} · {date}
  <span style="float:right;background:#EFF6FF;padding:2px 8px;border-radius:4px">{run_id[-20:]}</span>
</div>
{body}
<div style="margin-top:32px;padding-top:12px;border-top:1px solid #E2E8F0;font-size:11px;color:#94A3B8;text-align:center">
  元探 MetaProbe · 数据来自合法授权渠道 · 所有数字均为平台公开真值
</div>
</body>
</html>"""


def gen_one(run_id: str, sf_key: str | None, force: bool = False) -> bool:
    """生成单个案例的 report.html。返回是否成功。"""
    case_dir  = _CASES_DIR / run_id
    md_path   = case_dir / "report.md"
    html_path = case_dir / "report.html"
    meta_path = case_dir / "meta.json"

    if not md_path.exists():
        print(f"  ⚠️  {run_id}: report.md 不存在，跳过")
        return False
    if html_path.exists() and not force:
        print(f"  ⏭  {run_id}: report.html 已存在（--force 覆盖）")
        return True

    md   = md_path.read_text("utf-8")
    meta = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {}
    account_name = meta.get("account_name", run_id)
    date         = meta.get("analyzed_date", "")

    print(f"  → {account_name} ({len(md)} 字)…", end=" ", flush=True)

    body = None

    # 1. 尝试硅基流动
    if sf_key:
        body = _sf_convert(md, sf_key)
        if body:
            print("✅ SiliconFlow", end=" ")
        else:
            print("⚠️  降级保底", end=" ")

    # 2. Python 保底
    if body is None:
        body = f'<div class="prb">{_py_render(md)}</div>'
        print("✅ Python渲染", end=" ")

    html = _build_html(run_id, account_name, date, body)
    html_path.write_text(html, "utf-8")
    print(f"→ {html_path.name} ({len(html)} 字)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id", nargs="?", help="单个 run_id")
    ap.add_argument("--all",   action="store_true", help="批量处理所有案例")
    ap.add_argument("--force", action="store_true", help="强制覆盖已有 html")
    ap.add_argument("--no-sf", action="store_true", help="跳过 SiliconFlow（纯 Python 渲染）")
    args = ap.parse_args()

    sf_key = None if args.no_sf else os.getenv("SILICONFLOW_API_KEY")
    if not sf_key and not args.no_sf:
        print("⚠️  未设置 SILICONFLOW_API_KEY，使用 Python 保底渲染")

    if args.all:
        cases = [d.name for d in _CASES_DIR.iterdir() if d.is_dir() and (d / "report.md").exists()]
        cases.sort()
        print(f"批量生成 {len(cases)} 个案例的 report.html：")
        ok = sum(gen_one(r, sf_key, args.force) for r in cases)
        print(f"\n完成 {ok}/{len(cases)} 个")
    elif args.run_id:
        gen_one(args.run_id, sf_key, args.force)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

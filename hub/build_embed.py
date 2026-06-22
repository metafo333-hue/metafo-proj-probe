#!/usr/bin/env python3
"""把 index.json + 各案例 report.html 内嵌进 probe-cases.html

目的：让 file:// 双击模式（浏览器禁 fetch 同级文件）也能在页面中间
直接渲染网页报告，无需启动 serve.py，点击不跳转。

用法：
  cd ~/Downloads/metafoclaw/probe
  python3 hub/build_embed.py

每次 report.html / index.json 重新生成后跑一次即可。
"""
import json
import pathlib
import re
import sys

ROOT  = pathlib.Path(__file__).resolve().parent.parent     # probe/
CASES = ROOT / "data" / "cases"
HTML  = ROOT / "hub" / "probe-cases.html"

DATA_BEGIN = '<script type="application/json" id="embedded-data">'
RPT_BEGIN  = '<script type="application/json" id="embedded-reports">'
SCRIPT_END = "</script>"


def _replace_block(text: str, begin_marker: str, new_inner: str) -> str:
    """替换 <script id=...>...</script> 的内部内容（块必须已存在）。"""
    start = text.index(begin_marker) + len(begin_marker)
    end   = text.index(SCRIPT_END, start)
    return text[:start] + "\n" + new_inner + "\n" + text[end:]


def main() -> int:
    if not HTML.exists():
        print(f"❌ 未找到 {HTML}")
        return 1

    index = json.loads((CASES / "index.json").read_text(encoding="utf-8"))
    text  = HTML.read_text(encoding="utf-8")

    # 1) embedded-data ← index.json（压缩单行）
    data_inner = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    text = _replace_block(text, DATA_BEGIN, data_inner)

    # 2) embedded-reports ← 各案例 report.html（run_id → html 字符串）
    reports = {}
    for case in index.get("cases", []):
        rid = case["run_id"]
        rp  = CASES / rid / "report.html"
        if rp.exists():
            reports[rid] = rp.read_text(encoding="utf-8")
    rpt_inner = json.dumps(reports, ensure_ascii=False, separators=(",", ":"))

    if RPT_BEGIN in text:
        text = _replace_block(text, RPT_BEGIN, rpt_inner)
    else:
        # 首次：在 embedded-data 块后插入 embedded-reports 块
        anchor = text.index(DATA_BEGIN)
        block_end = text.index(SCRIPT_END, anchor) + len(SCRIPT_END)
        insert = (
            '\n\n<!-- ====== 内嵌网页报告（file:// 模式中间栏渲染） ====== -->\n'
            f'{RPT_BEGIN}\n{rpt_inner}\n{SCRIPT_END}'
        )
        text = text[:block_end] + insert + text[block_end:]

    HTML.write_text(text, encoding="utf-8")

    total = sum(len(v) for v in reports.values())
    print(f"✅ 内嵌完成：{len(reports)} 份报告（{total:,} 字符）→ probe-cases.html")
    for rid in reports:
        print(f"   · {rid}")
    missing = [c["run_id"] for c in index.get("cases", []) if c["run_id"] not in reports]
    if missing:
        print(f"⚠️  缺 report.html（将无内嵌）：{', '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

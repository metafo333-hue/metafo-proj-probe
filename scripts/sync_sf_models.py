#!/usr/bin/env python3
"""硅基流动模型表周更同步工具 · sf-models-index.html → sf_models.json。

背景(probe-foundation-architecture-constraints 铁律一)：probe 全国产大模型。
sf-models-index.html 是运营报告里**每周更新一次**的硅基可用模型 + 价格 + 能力真源表。
本工具把它解析成结构化 JSON，供 model_router 做"成本×质量自适应选型"——
模型表周更 → 跑本工具重新生成 JSON → 路由层自动用上最新最优模型，无需改代码。

用法:
  python3 scripts/sync_sf_models.py [path/to/sf-models-index.html]
  默认读 运营报告/sf-models-index.html，输出 app/data/sf_models.json

设计:纯标准库(re)，零依赖，CI/probe-a 都能跑。HTML 缺失时不报错(保留旧 JSON)。
"""
from __future__ import annotations

import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_HTML = os.path.join(
    _HERE, "..", "..", "运营报告", "sf-models-index.html")
_OUT = os.path.join(_HERE, "..", "app", "data", "sf_models.json")

# 国产厂商白名单(数据不出境铁律·org 必须在此列)
_GOVCN_ORG = {
    "qwen", "deepseek-ai", "zai-org", "thudm", "moonshotai", "minimaxai",
    "baai", "tencent", "baidu", "paddlepaddle", "nex-agi", "internlm",
    "01-ai", "stepfun", "tele-ai", "opengvlab", "stabilityai",  # 末几个谨慎，靠 forbidden 兜底
}
# 海外模型硬禁(即便混入也剔除)
_FORBIDDEN = ("claude", "gpt-3", "gpt-4", "gpt-5", "gemini", "/o1", "/o3", "cc-")

_HDR = ["model_id", "org", "name", "state", "category", "tier", "size",
        "ctx_k", "caps", "price_in", "price_out", "cache", "unit",
        "promo", "scene", "note", "date"]


def _txt(html_cell: str) -> str:
    return re.sub(r"<[^>]+>", "", html_cell).strip()


def _price(s: str):
    """'¥0.70'/'FREE'/'-' → float 或 None(无价)。FREE→0.0。"""
    if not s:
        return None
    if "free" in s.lower():
        return 0.0
    m = re.search(r"[\d.]+", s)
    return float(m.group()) if m else None


def parse(html_path: str) -> dict:
    html = open(html_path, encoding="utf-8").read()
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S)
    out = []
    for r in rows:
        c = [_txt(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(c) < 12:
            continue
        d = dict(zip(_HDR, c))
        mid = d["model_id"]
        low = mid.lower()
        if any(b in low for b in _FORBIDDEN):
            continue  # 海外模型剔除
        org = (d.get("org") or "").lower()
        pin = _price(d.get("price_in"))
        pout = _price(d.get("price_out"))
        out.append({
            "id": mid,
            "org": d.get("org", ""),
            "category": d.get("category", ""),
            "tier": d.get("tier", ""),
            "ctx_k": d.get("ctx_k", ""),
            "caps": [x for x in re.split(r"[,\s]+", d.get("caps", "")) if x],
            "price_in": pin,
            "price_out": pout,
            "free": (pin == 0.0),
            "promo": d.get("promo", ""),
            "scene": d.get("scene", ""),
            "note": d.get("note", ""),
            "govcn": org in _GOVCN_ORG,
        })
    return {
        "source": os.path.basename(html_path),
        "model_count": len(out),
        "models": out,
    }


def main():
    html = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_HTML
    if not os.path.exists(html):
        print(f"⚠️ HTML 不存在: {html}·保留旧 JSON 不覆盖", file=sys.stderr)
        return 1
    data = parse(html)
    os.makedirs(os.path.dirname(_OUT), exist_ok=True)
    # 原子写
    tmp = _OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _OUT)
    govcn = sum(1 for m in data["models"] if m["govcn"])
    free = sum(1 for m in data["models"] if m["free"])
    print(f"✅ {data['model_count']} 模型 → {os.path.relpath(_OUT, _HERE)}"
          f"（国产 {govcn}·免费 {free}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""link-intel B 深探线：B1 取材 + 目录搭建 + B2 分类 + B3 路由，输出 brief 供 Claude 执行 B4-B7。

用法：
  python deep.py <URL> [--full]   # --full 触发深档路由（全 9 维度）
"""
import sys
import os
import json
import re
import pathlib
import datetime
import subprocess

# venv CLI 入 PATH
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")

SKILL_DIR = pathlib.Path(__file__).parent.parent
EXTRACT_SCRIPT = SKILL_DIR / "scripts" / "extract.py"
A_BASE = "提取产出"
B_BASE = "深探产出"

# ---- B1 取材 ----

def run_a_line(url: str) -> tuple:
    """调 extract.py，返回 (returncode, stdout, stderr)。"""
    r = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT), url],
        capture_output=True, text=True, timeout=300
    )
    return r.returncode, r.stdout, r.stderr


def _parse_slug(stdout: str) -> str:
    """从 A 线 stdout 解析 slug（[A6] 已归档：提取产出/<slug>...）。"""
    m = re.search(r"\[A6\] 已归档：提取产出/([^\s（(]+)", stdout)
    return m.group(1).rstrip("/\\") if m else ""


def load_a_content(slug: str) -> dict:
    """加载 A 线产出：来源.json + 文案/正文.md。"""
    root = pathlib.Path(A_BASE) / slug
    out = {"a_root": str(root), "slug": slug}
    src = root / "来源.json"
    if src.exists():
        out["源信息"] = json.loads(src.read_text(encoding="utf-8"))
    text = root / "文案" / "正文.md"
    if text.exists():
        out["正文"] = text.read_text(encoding="utf-8")
    return out


# ---- 目录搭建 ----

def setup_deep_dir(slug: str) -> pathlib.Path:
    """创建 深探产出/<slug>/ 目录，返回 Path。"""
    root = pathlib.Path(B_BASE) / slug
    root.mkdir(parents=True, exist_ok=True)
    return root


# ---- B2 分类（启发式预判，Claude 核实修正） ----

def b2_classify(content: dict) -> dict:
    text = content.get("正文", "")
    src = content.get("源信息", {})
    kind = src.get("kind", "article")

    # C1 内容形态
    c1 = "口播" if kind == "video" else "图文"

    # C2 商业意图（关键词扫描）
    buy_kw = ["购买", "下单", "链接", "优惠", "折扣", "店铺", "淘宝", "京东", "小黄车",
              "加购", "直播间", "商品", "buy now", "shop"]
    brand_kw = ["品牌", "合作", "广告", "sponsor", "赞助", "合作推广"]
    tl = text.lower()
    if any(w in tl for w in buy_kw):
        c2 = "带货"
    elif any(w in tl for w in brand_kw):
        c2 = "引流"
    else:
        c2 = "纯内容"

    # C3 二创价值（正文长度）
    c3 = "高" if len(text) > 800 else ("中" if len(text) > 200 else "低")

    # C4 风险等级（默认无险，需 Claude 核实）
    c4 = "无险"

    return {
        "C1": c1, "C2": c2, "C3": c3, "C4": c4,
        "_heuristic": True,
        "_note": "启发式预分类，请在 B2 步骤中核实修正（尤其 C1/C4）",
        "classified_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


# ---- B3 路由 ----

MUST_DIMS = ["D1", "D2", "D5", "D7"]
COND_DIMS = {
    "带货":   ["D6", "D8"],
    "C3高":   ["D2", "D7"],   # 已在必跑集，去重
    "边缘":   ["D8"],
    "红线":   ["D8"],
}


def b3_route(cls: dict, full: bool = False) -> dict:
    """按 B3 路由规则确定本次调研维度集合。"""
    if full:
        dims = list(f"D{i}" for i in range(1, 10))
        mode = "full"
    else:
        dims = list(MUST_DIMS)
        if cls["C2"] == "带货":
            dims += [d for d in COND_DIMS["带货"] if d not in dims]
        if cls["C3"] == "高":
            dims += [d for d in COND_DIMS["C3高"] if d not in dims]
        if cls["C4"] in ("边缘", "红线"):
            dims += [d for d in COND_DIMS[cls["C4"]] if d not in dims]
        # 确保顺序 D1..D9
        order = {f"D{i}": i for i in range(1, 10)}
        dims = sorted(set(dims), key=lambda d: order.get(d, 99))
        mode = "standard"

    return {
        "mode": mode,
        "dims_to_run": dims,
        "routed_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


# ---- brief 输出 ----

DIM_NAMES = {
    "D1": "真相核查",
    "D2": "结构拆解",
    "D3": "视觉拆解（需多模态 + 关键帧图片）",
    "D4": "出处溯源（WebSearch）",
    "D5": "竞品横评（WebSearch ≥3 竞品）",
    "D6": "发布者画像（WebFetch 作者主页）",
    "D7": "二创路径（综合 D1/D2/D8）",
    "D8": "合规风险（WebSearch 平台规则）",
    "D9": "IP 适配（需用户 IP 画像）",
}


def print_brief(url: str, slug: str, content: dict, cls: dict, route: dict,
                deep_root: pathlib.Path):
    """打印供 Claude 执行 B4-B7 的结构化 brief。"""
    src = content.get("源信息", {})
    text = content.get("正文", "")
    a_root = content.get("a_root", "")

    print("=" * 60)
    print("link-intel B 深探线 · 准备就绪")
    print("=" * 60)
    print(f"URL     : {url}")
    print(f"平台    : {src.get('kind', '?')} · {src.get('extractor', '?')}")
    print(f"标题    : {src.get('title', '（无）')}")
    print(f"A线产出 : {a_root}")
    print(f"深探目录: {deep_root}")
    print()

    print("── B2 分类（启发式，需 Claude 核实）──")
    for k in ["C1", "C2", "C3", "C4"]:
        print(f"  {k}: {cls[k]}")
    print(f"  ⚠ {cls['_note']}")
    print()

    print("── B3 路由 ──")
    print(f"  模式: {route['mode']}")
    print(f"  本次维度: {' '.join(route['dims_to_run'])}")
    print()

    print("── 正文摘要（前 500 字）──")
    print(text[:500] + ("..." if len(text) > 500 else ""))
    print()

    print("── B4-B7 执行清单（Claude 完成）──")
    print("B4 按以下维度并行调研（产出落 深探产出/<slug>/Dx-xxx.md）：")
    for d in route["dims_to_run"]:
        print(f"  [{d}] {DIM_NAMES.get(d, d)}")
    print()
    print("B5 聚合各维度产出，按 references/report-skeleton.md 7 段骨架撰写报告。")
    print("B6 按评级标准表给 A/B/C/D，填入段 1 首屏速判。")
    print(f"B7 报告落盘：{deep_root / '报告.md'}")
    print()
    print("自检前 5 条见 references/report-skeleton.md § 出报告前自检清单。")
    print("=" * 60)


# ---- 主流程 ----

def main():
    if len(sys.argv) < 2:
        print("用法：deep.py <URL> [--full]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    full_mode = "--full" in sys.argv

    # B1 取材：运行 A 线
    print(f"[B1] 运行 A 快提取线：{url}")
    rc, stdout, stderr = run_a_line(url)
    print(stdout.rstrip())
    if rc not in (0, 2):
        print(f"[B1] A 线异常退出（code={rc}）：{stderr[:200]}", file=sys.stderr)
        sys.exit(rc)

    slug = _parse_slug(stdout)
    if not slug:
        print("[B1] 无法从 A 线输出解析 slug，中止。", file=sys.stderr)
        sys.exit(3)

    content = load_a_content(slug)
    if not content.get("正文") and not content.get("源信息"):
        print("[B1] A 线产出为空（可能是视频/社交类），正文需手动补充。")

    # 搭建深探目录
    deep_root = setup_deep_dir(slug)

    # B2 分类
    cls = b2_classify(content)
    cls["slug"] = slug
    (deep_root / "分类.json").write_text(
        json.dumps(cls, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[B2] 分类写入：{deep_root}/分类.json")

    # B3 路由
    route = b3_route(cls, full=full_mode)
    route["slug"] = slug
    (deep_root / "路由.json").write_text(
        json.dumps(route, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[B3] 路由写入：{deep_root}/路由.json  维度: {route['dims_to_run']}")
    print()

    # 打印 brief
    print_brief(url, slug, content, cls, route, deep_root)


if __name__ == "__main__":
    main()

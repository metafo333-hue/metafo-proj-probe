#!/usr/bin/env python3
"""link-intel A 快提取线：链接归类 + 4 类提取器分发 + A6 归档。"""
import sys
import os
import re
import json
import hashlib
import subprocess
import pathlib
import datetime

# venv CLI 入 PATH（crwl / markitdown 装在 skill 专用 venv，subprocess 才调得到）
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")

# ---- A1 链接归类 ----
_VIDEO = re.compile(r"(douyin\.com|iesdouyin\.com|bilibili\.com|b23\.tv|"
                    r"youtube\.com|youtu\.be|kuaishou\.com)")
_SOCIAL = re.compile(r"(xiaohongshu\.com|xhslink\.com|weibo\.com|"
                     r"twitter\.com|x\.com)")
_DOC = re.compile(r"(\.pdf($|\?)|github\.com|arxiv\.org|readthedocs)")


def classify_url(url: str) -> str:
    """归为 video / social / doc / article 之一。"""
    u = url.lower()
    if _VIDEO.search(u):
        return "video"
    if _SOCIAL.search(u):
        return "social"
    if _DOC.search(u):
        return "doc"
    return "article"


def make_slug(title: str, url: str) -> str:
    """标题转 slug；标题缺失时用 URL 哈希兜底。"""
    s = re.sub(r"[^\w一-鿿]+", "-", (title or "").strip())
    s = s[:40].strip("-")
    if not s:
        h = hashlib.md5(url.encode()).hexdigest()[:8]
        s = f"link-{h}"
    return s


# ---- A3 各类提取器 ----
def _run(cmd, timeout=180):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return 1, "", str(e)


def extract_article(url: str) -> dict:
    """图文文章：Trafilatura → Crawl4AI → Jina Reader 逐级降级。"""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            data = trafilatura.extract(downloaded, output_format="json",
                                       with_metadata=True)
            if data:
                d = json.loads(data)
                if len(d.get("text", "")) >= 200:
                    d["_source"] = "trafilatura"
                    return d
    except Exception:
        pass
    code, out, _ = _run(["crwl", "crawl", url, "-o", "markdown"])
    if code == 0 and len(out.strip()) >= 200:
        return {"title": "", "text": out, "_source": "crawl4ai"}
    code, out, _ = _run(["curl", "-s", "--max-time", "60",
                         f"https://r.jina.ai/{url}"])
    if code == 0 and len(out.strip()) >= 200:
        return {"title": "", "text": out, "_source": "jina"}
    return {}


def extract_doc(url: str, out_dir: str) -> dict:
    """文档代码：GitHub raw 直取 / markitdown 转 PDF。"""
    if "github.com" in url and "/blob/" not in url:
        raw = url.rstrip("/") + "/raw/HEAD/README.md"
        code, out, _ = _run(["curl", "-sL", "--max-time", "60", raw])
        if code == 0 and out.strip():
            return {"title": "", "text": out, "_source": "github-raw"}
    os.makedirs(out_dir, exist_ok=True)
    local = os.path.join(out_dir, "原文档")
    _run(["curl", "-sL", "--max-time", "120", "-o", local, url])
    if os.path.exists(local):
        code, out, _ = _run(["markitdown", local])
        if code == 0 and out.strip():
            return {"title": "", "text": out, "_source": "markitdown"}
    return {}


def extract_social(url: str) -> dict:
    """社交图文：X 无方案直接提示；小红书/微博需 MediaCrawler（单独部署）。"""
    if re.search(r"(twitter\.com|x\.com)", url.lower()):
        return {"_source": "manual", "_note": "X 无免费提取方案，请手动粘贴文案"}
    return {"_source": "mediacrawler",
            "_note": "小红书/微博需 MediaCrawler 单独部署（NON-COMMERCIAL，仅研究用途）"}


# ---- A6 归档 ----
def archive(slug: str, kind: str, payload: dict, base: str = "提取产出"):
    """按素材仓库 5 大类建目录，写入产物。"""
    root = pathlib.Path(base) / slug
    for sub in ["文案", "音乐", "图片", "视频", "灵感"]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    if payload.get("text"):
        (root / "文案" / "正文.md").write_text(payload["text"],
                                              encoding="utf-8")
    src = {"url": payload.get("_url", ""), "kind": kind,
           "title": payload.get("title", ""),
           "extractor": payload.get("_source", ""),
           "版权状态": "未核实 · 直接复用需过版权门",
           "提取时间": datetime.datetime.now().isoformat(timespec="seconds")}
    (root / "来源.json").write_text(
        json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(root)


def main():
    if len(sys.argv) < 2:
        print("用法：extract.py <URL>")
        sys.exit(1)
    url = sys.argv[1]
    kind = classify_url(url)
    print(f"[A1] 归类：{kind}")
    if kind == "article":
        data = extract_article(url)
    elif kind == "doc":
        data = extract_doc(url, "/tmp/li-doc")
    elif kind == "social":
        data = extract_social(url)
    else:  # video
        data = {"_source": "video", "_note":
                "视频类：调 subtitle.py 下字幕、media.py 抽素材"}
    if not data or (kind in ("article", "doc") and not data.get("text")):
        print(f"[失败] 无法提取此链接（{kind}）。"
              f"按 references/extract-sop.md 边界说明归因。")
        sys.exit(2)
    data["_url"] = url
    slug = make_slug(data.get("title", ""), url)
    out = archive(slug, kind, data)
    print(f"[A6] 已归档：{out}（提取器：{data.get('_source')}）")


if __name__ == "__main__":
    main()

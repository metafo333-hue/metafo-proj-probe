#!/usr/bin/env python3
"""l0_rules_fetch.py — 定期抓取官方公开规则页，产出结构化 JSON 供 l0_environment 加载。

用法（cron 友好）：
    python3 scripts/l0_rules_fetch.py              # 正常跑
    python3 scripts/l0_rules_fetch.py --dry-run    # 只打印解析结果，不写文件

输出：data/l0_platform_rules.json（结构与 l0_environment 种子对齐）

抓取目标（只抓官方公开静态规则页·非个人数据·合规）：
  1. trust.douyin.com — 抖音安全与信任中心（社区规范·违规类型·AI标注规则）
     主页 https://trust.douyin.com/
     公约页 https://www.douyin.com/rule/policy
     文章页（多篇规范）https://trust.douyin.com/article/<id>
  2. 视频号营销规范（公开静态页，无需登录）
     https://channels.weixin.qq.com/shop/learning-center/detail.html?contentId=Article_1714298230_MSGCULXF&type=rule

诚实标注：
  - trust.douyin.com 是 SPA（React），纯 HTML 抓取只能拿到基础文本+meta，
    详细分类列表可能需 JS 渲染。本脚本走 HTML→正文文本→正则提取，
    页面结构变化时会 fallback 到种子（不崩）。
  - 视频号规范页同样是 SPA，营销规范文章页能拿到部分文本。
  - 两个目标都设 10s 超时；失败时保留上次 data/l0_platform_rules.json 或回退种子。

合规声明：
  - 只请求官方公开规范页（robots.txt 友好，不抓用户内容）
  - User-Agent 真实标注 probe-rules-fetch
  - 不存储任何个人数据
  - 请求间 2s 间隔，不并发轰炸
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# —— 路径 ——
_REPO_ROOT = Path(__file__).parent.parent
_DATA_DIR = _REPO_ROOT / "data"
_OUT_FILE = _DATA_DIR / "l0_platform_rules.json"

# —— 日志 ——
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [l0_rules_fetch] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("l0_rules_fetch")

# —— 请求参数 ——
_UA = "probe-rules-fetch/1.0 (metafoclaw compliance bot; +https://metafoclaw.com)"
_TIMEOUT = 10  # 秒
_INTER_REQ_DELAY = 2  # 请求间隔秒数

# —— 抓取目标 ——
# 每条: (name, url, description)
# 分优先级：第一批是最可能拿到纯文本内容的URL
_TARGETS = [
    (
        "douyin_trust_home",
        "https://trust.douyin.com/",
        "抖音安全与信任中心首页（含社区规范摘要）",
    ),
    (
        "douyin_policy",
        "https://www.douyin.com/rule/policy",
        "抖音社区自律公约（静态协议页）",
    ),
    (
        "douyin_trust_article_15358",
        "https://trust.douyin.com/article/15358",
        "抖音社区治理规范文章（已知公开文章）",
    ),
    (
        "wechat_channels_marketing_rule",
        "https://channels.weixin.qq.com/shop/learning-center/detail.html"
        "?contentId=Article_1714298230_MSGCULXF&type=rule",
        "微信视频号视频/直播营销信息发布规范",
    ),
]

# —— 种子（回退兜底，与 l0_environment.py 保持一致） ——
_SEED_AI_LABEL = (
    "AI 生成内容须显著标注（2026-03 新规·未标注会限流 50-80% 甚至下架）"
)
_SEED_FORBIDDEN = [
    "涉政敏感",
    "虚假宣传/夸大功效",
    "无资质做医疗·金融荐股",
    "未标注的 AI 内容",
    "盗用版权音乐/素材",
]
_SEED_MUSIC = "背景音乐用平台曲库的免费商用音乐，别用来路不明的（版权风险会限流）"


# ── 网络工具 ──────────────────────────────────────────────────────────────────

def _fetch_url(url: str) -> str | None:
    """抓取 URL 返回 HTML 文本；失败返回 None（不抛异常）。"""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            charset = "utf-8"
            content_type = resp.headers.get("Content-Type", "")
            m = re.search(r"charset=([\w-]+)", content_type)
            if m:
                charset = m.group(1)
            return resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        log.warning("HTTP %s: %s", e.code, url)
    except urllib.error.URLError as e:
        log.warning("URL error (%s): %s", e.reason, url)
    except Exception as e:  # noqa: BLE001
        log.warning("Fetch error (%s): %s", type(e).__name__, url)
    return None


def _strip_html(html: str) -> str:
    """粗去除 HTML 标签，保留文本内容（不依赖 BeautifulSoup）。"""
    # 去脚本/样式块
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # 去标签
    text = re.sub(r"<[^>]+>", " ", text)
    # 还原常见 HTML 实体
    for ent, ch in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                     ("&nbsp;", " "), ("&#34;", '"'), ("&#39;", "'")]:
        text = text.replace(ent, ch)
    # 压缩空白
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── 解析逻辑 ─────────────────────────────────────────────────────────────────

# 正则关键词→标准禁区名，按优先级排列
_FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"涉政|政治敏感|违反宪法|颠覆政权", "涉政敏感"),
    (r"虚假宣传|夸大功效|虚假广告|夸大宣传|虚假信息", "虚假宣传/夸大功效"),
    (r"无资质.{0,10}医疗|无证.{0,10}行医|无资质.{0,10}金融|荐股|非法金融", "无资质做医疗·金融荐股"),
    (r"AI.{0,10}(生成|内容).{0,20}(标注|标注|显示)|未标注.{0,10}AI", "未标注的 AI 内容"),
    (r"版权.{0,10}(音乐|素材)|盗用.{0,10}(音乐|图片|视频)|侵权", "盗用版权音乐/素材"),
    (r"色情|淫秽|低俗|裸露|性暗示", "色情/低俗内容"),
    (r"赌博|博彩|赌注", "赌博内容"),
    (r"毒品|吸毒|贩毒|违禁药品", "毒品/违禁药品"),
    (r"诈骗|欺诈|骗局|钓鱼", "诈骗/欺诈内容"),
    (r"谣言|虚假消息|虚假新闻", "散布谣言/虚假消息"),
    (r"网络暴力|人肉搜索|doxxing", "网络暴力/人肉搜索"),
    (r"未成年.{0,15}(保护|色情|诱导)|儿童.{0,10}(侵害|色情)", "未成年人保护违规"),
]

_AI_LABEL_PATTERNS = [
    r"AI.{0,20}(生成|创作).{0,40}(标注|标识|显示|显著)",
    r"(标注|标识).{0,20}AI.{0,20}(内容|生成)",
    r"AIGC.{0,30}(标注|标识)",
]

_MUSIC_PATTERNS = [
    r"(背景音乐|BGM|音乐).{0,40}(授权|版权|免费|曲库|商用)",
    r"(音乐|音频).{0,30}(侵权|版权|授权).{0,30}(限流|下架|处罚)",
]


def _extract_forbidden_zones(text: str) -> list[str]:
    """从文本中提取违禁区域，返回去重列表。"""
    found = []
    seen = set()
    for pattern, label in _FORBIDDEN_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE) and label not in seen:
            found.append(label)
            seen.add(label)
    return found


def _extract_ai_label_rule(text: str) -> str | None:
    """从文本中提取 AI 标注规则描述，未找到返回 None。"""
    for pat in _AI_LABEL_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # 从匹配开始位置（不往前偏移，避免跨句抓到上一句结尾）
            start = m.start()
            end = min(len(text), m.end() + 80)
            snippet = text[start:end].strip()
            # 按中英文句号/换行截断，取第一个足够长的片段
            parts = re.split(r"[。.！!？?\n]", snippet)
            for part in parts:
                part = part.strip()
                if len(part) > 8:
                    return part
    return None


def _extract_music_rule(text: str) -> str | None:
    """从文本中提取音乐版权规则描述，未找到返回 None。"""
    for pat in _MUSIC_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            # 从匹配开始位置（不往前偏移，避免跨句抓到上一句结尾）
            start = m.start()
            end = min(len(text), m.end() + 80)
            snippet = text[start:end].strip()
            # 按中英文句号/换行截断，取第一个完整片段
            parts = re.split(r"[。.！!？?\n]", snippet)
            # 找第一个长度 > 6 的片段
            for part in parts:
                part = part.strip()
                if len(part) > 6:
                    return part
    return None


def parse_page(name: str, html: str) -> dict[str, Any]:
    """从单个页面 HTML 解析出规则片段。"""
    text = _strip_html(html)
    return {
        "source": name,
        "text_length": len(text),
        "forbidden_zones": _extract_forbidden_zones(text),
        "ai_label_snippet": _extract_ai_label_rule(text),
        "music_snippet": _extract_music_rule(text),
        "text_preview": text[:300] if text else "",  # 调试用
    }


# ── 合并逻辑 ─────────────────────────────────────────────────────────────────

def merge_results(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """将多页解析结果合并为一个结构化规则对象（与 l0_environment 种子对齐）。

    合并策略：
    - forbidden_zones：所有页面结果 union，不够种子最低集时补种子
    - ai_label/music：优先用首个非空抓取值，没有则 None（调用方 fallback 到种子）
    """
    all_forbidden: set[str] = set()
    ai_label_raw: str | None = None
    music_raw: str | None = None
    sources_ok: list[str] = []

    for p in pages:
        if p.get("forbidden_zones"):
            all_forbidden.update(p["forbidden_zones"])
            sources_ok.append(p["source"])
        if not ai_label_raw and p.get("ai_label_snippet"):
            ai_label_raw = p["ai_label_snippet"]
        if not music_raw and p.get("music_snippet"):
            music_raw = p["music_snippet"]

    # 保证至少包含种子的核心 5 条
    for seed_item in _SEED_FORBIDDEN:
        if not any(seed_item in z or z in seed_item for z in all_forbidden):
            all_forbidden.add(seed_item)

    return {
        "forbidden_zones": sorted(all_forbidden),
        "ai_label": ai_label_raw,        # None = 调用方用种子
        "music": music_raw,              # None = 调用方用种子
        "sources_ok": sources_ok,
    }


# ── 主流程 ────────────────────────────────────────────────────────────────────

def fetch_and_parse() -> dict[str, Any]:
    """抓取所有目标页面，解析并合并，返回规则对象。失败页面跳过不崩。"""
    pages: list[dict[str, Any]] = []
    for i, (name, url, desc) in enumerate(_TARGETS):
        log.info("抓取 [%d/%d] %s: %s", i + 1, len(_TARGETS), name, url)
        html = _fetch_url(url)
        if html:
            parsed = parse_page(name, html)
            log.info(
                "  解析: forbidden=%d ai_label=%s music=%s text_len=%d",
                len(parsed["forbidden_zones"]),
                "有" if parsed["ai_label_snippet"] else "无",
                "有" if parsed["music_snippet"] else "无",
                parsed["text_length"],
            )
            pages.append(parsed)
        else:
            log.warning("  跳过 %s（抓取失败）", name)
        if i < len(_TARGETS) - 1:
            time.sleep(_INTER_REQ_DELAY)

    merged = merge_results(pages)

    # 构建最终输出，None 的字段 fallback 到种子（向后兼容）
    return {
        "schema_version": "1.0",
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "sources_ok": merged["sources_ok"],
        "fetch_coverage": f"{len(merged['sources_ok'])}/{len(_TARGETS)} 目标成功",
        "platform": {
            "ai_label": merged["ai_label"] or _SEED_AI_LABEL,
            "ai_label_from_fetch": merged["ai_label"] is not None,
            "forbidden_zones": merged["forbidden_zones"],
            "music": merged["music"] or _SEED_MUSIC,
            "music_from_fetch": merged["music"] is not None,
        },
        # 诚实标注：哪些字段是抓取得来的、哪些是种子 fallback
        "data_notes": {
            "ai_label": "从官方页提取" if merged["ai_label"] else "种子 fallback（官方页未匹配）",
            "music": "从官方页提取" if merged["music"] else "种子 fallback（官方页未匹配）",
            "forbidden_zones": (
                f"抓取 union + 种子补全（{len(merged['sources_ok'])} 页成功）"
                if merged["sources_ok"]
                else "全部种子（所有页面抓取失败）"
            ),
        },
    }


def build_seed_output() -> dict[str, Any]:
    """纯种子输出（所有页面失败时的最终兜底）。"""
    return {
        "schema_version": "1.0",
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "sources_ok": [],
        "fetch_coverage": "0/0 (全部失败·纯种子)",
        "platform": {
            "ai_label": _SEED_AI_LABEL,
            "ai_label_from_fetch": False,
            "forbidden_zones": list(_SEED_FORBIDDEN),
            "music": _SEED_MUSIC,
            "music_from_fetch": False,
        },
        "data_notes": {
            "ai_label": "种子 fallback",
            "music": "种子 fallback",
            "forbidden_zones": "全部种子（抓取全失败）",
        },
    }


def load_existing() -> dict[str, Any] | None:
    """加载上次成功写入的 JSON；不存在或损坏返回 None。"""
    if not _OUT_FILE.exists():
        return None
    try:
        with open(_OUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # noqa: BLE001
        log.warning("上次输出文件损坏: %s", e)
        return None


def write_output(data: dict[str, Any]) -> None:
    """原子写入（tempfile→rename 模式，防半写）。"""
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _OUT_FILE.with_suffix(".json.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.rename(_OUT_FILE)
        log.info("已写入 %s", _OUT_FILE)
    except Exception as e:  # noqa: BLE001
        log.error("写入失败: %s", e)
        tmp.unlink(missing_ok=True)
        raise


def main(dry_run: bool = False) -> int:
    """主入口。返回 0=成功, 1=部分成功(有 fallback), 2=全部失败(纯种子)。"""
    log.info("=== l0_rules_fetch 开始 ===")

    try:
        result = fetch_and_parse()
    except Exception as e:  # noqa: BLE001
        log.error("fetch_and_parse 异常: %s", e)
        result = None

    if result is None or not result.get("sources_ok"):
        # 全部失败 → 尝试用上次结果，否则纯种子
        existing = load_existing()
        if existing:
            log.warning("所有页面抓取失败，保留上次文件: %s", existing.get("fetched_at"))
            log.info("=== 结束 (保留上次) ===")
            return 1
        log.warning("所有页面抓取失败且无历史文件，输出纯种子")
        result = build_seed_output()
        if not dry_run:
            write_output(result)
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        log.info("=== 结束 (纯种子) ===")
        return 2

    log.info(
        "抓取完成: %s / %d 目标成功",
        len(result["sources_ok"]),
        len(_TARGETS),
    )

    if dry_run:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        write_output(result)

    exit_code = 0 if len(result["sources_ok"]) == len(_TARGETS) else 1
    log.info("=== 结束 (exit=%d) ===", exit_code)
    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抓取官方公开规则页，产出 data/l0_platform_rules.json")
    parser.add_argument("--dry-run", action="store_true", help="只打印解析结果，不写文件")
    args = parser.parse_args()
    raise SystemExit(main(dry_run=args.dry_run))

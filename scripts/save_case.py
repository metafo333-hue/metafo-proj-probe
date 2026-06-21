#!/usr/bin/env python3
"""probe 案例入库脚本 · probe/data/cases/ 归档体系。

用法（run_from_video_url 跑完后调用）:
    from scripts.save_case import save_case
    run_id = save_case(result, docx_path="/tmp/.../xxx.docx", tags=["真实账号"])

入库内容:
    data/cases/{run_id}/meta.json   — 元数据（供 index.json 索引）
    data/cases/{run_id}/report.md   — 完整报告（润色后或原文）
    data/cases/{run_id}/report.docx — Word 文件（从原路径复制过来）
    data/cases/index.json           — 全量索引（网页直接读取）

三轴锚点:
    sec_uid    → 同创作者跨视频分析 / 账号成长轨迹
    aweme_id   → 同视频跨系统版本迭代对比
    probe_ver  → 系统改进前后质量对比
"""
from __future__ import annotations

import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_CASES_DIR = _ROOT / "data" / "cases"
_INDEX_FILE = _CASES_DIR / "index.json"

# SiliconFlow 免费模型(摘要生成·轻量任务)
_SUMMARY_MODEL = "Qwen/Qwen2.5-7B-Instruct"
_SF_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"

_ACCOUNT_TYPES = [
    ("带货", ["带货", "直播", "主播", "测评", "种草", "好物"]),
    ("带货·B2B", ["B2B", "供货", "直供", "源头", "工厂", "批发", "代工", "OEM", "餐饮"]),
    ("知识", ["知识", "科普", "教育", "健康", "医", "学习", "干货", "技巧"]),
    ("本地服务", ["探店", "本地", "餐厅", "美食", "服务", "附近", "打卡"]),
    ("颜值·美妆", ["美妆", "护肤", "穿搭", "时尚", "颜值", "美容", "化妆"]),
    ("生活·vlog", ["生活", "日常", "记录", "vlog", "家庭"]),
]


def _probe_version() -> str:
    """当前 git commit hash 前 8 位·失败返回 unknown。"""
    try:
        r = subprocess.run(["git", "-C", str(_ROOT), "rev-parse", "--short=8", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _infer_type(account: dict) -> str:
    """从签名+标签推断账号类型。"""
    sig = (account.get("signature") or "").lower()
    tags = " ".join(account.get("hashtags") or []).lower()
    blob = sig + " " + tags
    for label, keywords in _ACCOUNT_TYPES:
        if any(k in blob for k in keywords):
            return label
    return "其他"


def _slugify(text: str, maxlen: int = 12) -> str:
    """中英文昵称 → 安全文件名片段。"""
    text = re.sub(r'[\\/:*?"<>|\s｜]+', "", text)
    return text[:maxlen] or "unknown"


def _gen_summary(report_md: str, account_name: str, sf_key: str | None) -> str:
    """调 SiliconFlow 免费模型生成 40 字以内卡片摘要·失败返回空串。"""
    key = sf_key or os.getenv("SILICONFLOW_API_KEY")
    if not key:
        return ""
    prompt = (f"下面是一份抖音账号诊断报告（账号：{account_name}）的摘录。"
              f"请用**不超过 40 个汉字**概括这个账号最关键的特征和诊断结论，"
              f"格式：「账号标签·核心特征·变现方向·当前阶段」，只输出这句话，无需任何解释。\n\n"
              f"{report_md[:2000]}")
    payload = {"model": _SUMMARY_MODEL, "temperature": 0.3, "max_tokens": 100,
               "messages": [{"role": "user", "content": prompt}]}
    try:
        req = urllib.request.Request(
            _SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.load(r)
        return (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content", "").strip()[:60]
    except Exception:
        return ""


def _load_index() -> dict:
    if _INDEX_FILE.exists():
        return json.loads(_INDEX_FILE.read_text("utf-8"))
    return {"version": "1.0", "updated_at": "", "cases": []}


def _save_index(idx: dict) -> None:
    idx["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    _INDEX_FILE.write_text(json.dumps(idx, ensure_ascii=False, indent=2), "utf-8")


def save_case(
    result: dict,
    *,
    docx_path: str | None = None,
    tags: list[str] | None = None,
    account_type: str | None = None,
    sf_key: str | None = None,
    gen_summary: bool = True,
) -> str:
    """probe 分析结果 → 归档入库。返回 run_id。

    result: run_from_video_url() 的返回值（或含 video/account/audit/report_md 的 dict）。
    docx_path: Word 文件路径（可选·拷入案例目录）。
    tags: 用户自定义标签（如 ["真实账号", "首次分析"]）。
    account_type: 手动指定类型（不传则自动推断）。
    gen_summary: 是否调 SiliconFlow 免费模型生成摘要（默认 True）。
    """
    video = result.get("video") or {}
    account = result.get("account") or {}
    audit = result.get("audit") or {}
    report_md = result.get("report_md") or ""
    polish_info = result.get("_polish") or {}   # polish_report 可写入此字段

    nick = account.get("nickname") or "未知账号"
    sec_uid = account.get("sec_uid") or ""
    aweme_id = result.get("aweme_id") or ""
    follower = account.get("follower") or 0
    avg_like = account.get("avg_like") or 0
    max_like = account.get("max_like") or 0

    now = datetime.datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    slug = _slugify(nick)
    run_id = f"douyin-{slug}-{date_str}-{time_str}"

    a_type = account_type or _infer_type(account)
    probe_ver = _probe_version()

    # AI 摘要
    ai_summary = ""
    if gen_summary and report_md:
        ai_summary = _gen_summary(report_md, nick, sf_key)

    # 验收状态
    from scripts.report_to_docx import validate_report
    val = validate_report(result, report_md)

    # 案例目录
    case_dir = _CASES_DIR / run_id
    case_dir.mkdir(parents=True, exist_ok=True)

    # report.md
    (case_dir / "report.md").write_text(report_md, "utf-8")

    # report.docx（拷贝）
    docx_stored = None
    if docx_path and os.path.exists(docx_path):
        dst = case_dir / "report.docx"
        shutil.copy2(docx_path, dst)
        docx_stored = str(dst)

    # meta.json（案例完整元数据）
    meta = {
        "run_id": run_id,
        "platform": "douyin",
        "sec_uid": sec_uid,
        "aweme_id": aweme_id,
        "account_name": nick,
        "account_type": a_type,
        "follower": follower,
        "avg_like": avg_like,
        "max_like": max_like,
        "burst_ratio": account.get("burst_ratio"),
        "vertical_score": account.get("vertical_score"),
        "hashtags": account.get("hashtags") or [],
        "signature": account.get("signature") or "",
        "video_title": video.get("title") or "",
        "video_like": video.get("like") or 0,
        "video_comment": video.get("comment") or 0,
        "video_collect": video.get("collect") or 0,
        "has_av": bool(result.get("six_layer")),
        "analyzed_at": now.isoformat(timespec="seconds"),
        "analyzed_date": now.strftime("%Y-%m-%d"),
        "probe_version": probe_ver,
        "polish": polish_info or {
            "ok": False, "mode": "unknown", "model": "", "segs_ok": 0, "segs_total": 0
        },
        "validation_pass": val.get("pass", False),
        "validation_gaps": val.get("gaps") or [],
        "ai_summary": ai_summary,
        "tags": tags or [],
        "audit": {
            "source_reliability": audit.get("source_reliability"),
            "confidence_level": audit.get("confidence_level"),
            "evidence_strength": audit.get("evidence_strength"),
        },
        "docx_path": docx_stored,
        "report_chars": len(report_md),
    }
    (case_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

    # 更新 index.json（卡片所需字段的扁平副本）
    idx = _load_index()
    idx_entry = {k: meta[k] for k in (
        "run_id", "platform", "sec_uid", "aweme_id", "account_name", "account_type",
        "follower", "avg_like", "max_like", "burst_ratio",
        "video_title", "video_like", "has_av", "analyzed_at", "analyzed_date",
        "probe_version", "polish", "validation_pass", "validation_gaps",
        "ai_summary", "tags", "report_chars",
    )}
    # 同账号版本链（sec_uid 相同的最新 run_id 作为 prev）
    same_acct = [c for c in idx["cases"] if c.get("sec_uid") == sec_uid and sec_uid]
    idx_entry["prev_run_id"] = same_acct[-1]["run_id"] if same_acct else None
    idx_entry["version_count"] = len(same_acct) + 1

    # 同视频版本链
    same_vid = [c for c in idx["cases"] if c.get("aweme_id") == aweme_id and aweme_id]
    idx_entry["prev_vid_run_id"] = same_vid[-1]["run_id"] if same_vid else None
    idx_entry["vid_version_count"] = len(same_vid) + 1

    idx["cases"].append(idx_entry)
    _save_index(idx)

    print(f"[save_case] ✅ {run_id}  账号={nick}  类型={a_type}  摘要={ai_summary[:30]}")
    return run_id


# ── CLI 补录入口 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    """
    补录已有案例:
    python scripts/save_case.py --backfill <meta.json路径>
    """
    import argparse
    parser = argparse.ArgumentParser(description="probe 案例补录")
    parser.add_argument("--backfill", help="已有案例 meta.json 路径（直接写入 index）")
    args = parser.parse_args()

    if args.backfill:
        meta = json.loads(open(args.backfill, "utf-8").read())
        idx = _load_index()
        existing_ids = {c["run_id"] for c in idx["cases"]}
        if meta["run_id"] not in existing_ids:
            idx["cases"].append({k: meta.get(k) for k in (
                "run_id", "platform", "sec_uid", "aweme_id", "account_name", "account_type",
                "follower", "avg_like", "max_like", "burst_ratio",
                "video_title", "video_like", "has_av", "analyzed_at", "analyzed_date",
                "probe_version", "polish", "validation_pass", "validation_gaps",
                "ai_summary", "tags", "report_chars",
            )})
            _save_index(idx)
            print(f"[backfill] ✅ {meta['run_id']}")
        else:
            print(f"[backfill] ⏭ 已存在: {meta['run_id']}")

"""视频分析归集·落盘器 (该存的方式)。

唯一家: probe/data/cases/ (复用既有归集设施·D-2026-06-27)。
生成器产出后调本模块 → 案例直接落进归集,网页/index/serve 全自动可见,
不再经"运营报告大杂院 → 扫描 → 登记 → 人肉入库"那条链。

persist_board(account, board, html, md): 元板结果 → 案例。元数据从结构化
board/account 直取(质量高于 HTML 回抽)。返回 run_id。

落盘后自动:写 report.html/md + meta.json + 回填 index.json + 登记表 + build_embed。
"""
from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys

_ROOT = pathlib.Path(__file__).resolve().parents[2]      # probe/
_CASES = _ROOT / "data" / "cases"
_IDX = _CASES / "index.json"
_REG = _CASES / "video-sources-registry.json"

_FLAT = ("run_id", "platform", "source", "sec_uid", "aweme_id", "account_name", "account_type",
         "follower", "avg_like", "max_like", "burst_ratio", "video_title", "video_like", "has_av",
         "analyzed_at", "analyzed_date", "probe_version", "polish", "validation_pass",
         "validation_gaps", "ai_summary", "tags", "report_chars", "video_comment", "video_collect")


def _slug(nick: str) -> str:
    try:
        from scripts.save_case import _slugify
        return _slugify(nick)
    except Exception:
        import hashlib, re
        a = re.sub(r"[^A-Za-z0-9]", "", nick)
        return (a[:12].lower() or "acct" + hashlib.md5(nick.encode()).hexdigest()[:8])


def _infer_type(account: dict) -> str:
    try:
        from scripts.save_case import _infer_type as f
        return f(account)
    except Exception:
        return "视频分析"


def _summary_from_board(board: dict) -> str:
    """从 board headline/accounting 取一句话摘要(结构化·非抓 HTML)。"""
    hl = board.get("headline") or {}
    for k in ("text", "conclusion", "title", "msg"):
        v = hl.get(k) if isinstance(hl, dict) else None
        if v:
            return str(v)[:120]
    layers = board.get("layers") or {}
    acc = (layers.get("account") or {}) if isinstance(layers, dict) else {}
    for k in ("conclusion", "summary", "text"):
        if acc.get(k):
            return str(acc[k])[:120]
    return "元板·四层下钻数据板块"


def _render_contract_html(board: dict) -> str | None:
    """board.contract_doc → 元数据诊断标准产出(走 metaform render_contract·进程内)。

    失败(metaform 不在/异常)返 None·persist_board 回退 ladder html。
    这把案例库 report.html 从 ladder render 收敛成「元数据诊断」契约标准产出。
    """
    doc = board.get("contract_doc")
    if not doc:
        return None
    try:
        import tempfile
        from app.services import gallery as _gal
        mf = _gal._dir().parent / "metaform"               # 运营报告/metaform(api.py 在根·自挂 lib)
        if mf.exists() and str(mf) not in sys.path:
            sys.path.insert(0, str(mf))
        import api  # metaform 渲染权威
        with tempfile.TemporaryDirectory() as td:
            res = api.render_data(doc, scenario="account-diagnosis", format="html", outdir=td)
            return pathlib.Path(res["path"]).read_text("utf-8")
    except Exception:  # noqa: BLE001 — metaform 不可达则回退·不拖垮入库
        return None


def _persist_works(cdir: pathlib.Path, works: list | None) -> None:
    """原始作品列表(parse_works 产物)与 board.json 同目录落一份 works.json。

    元会诊 MetaConsult v2 接缝一(design: metaconsult-fusion-redesign-v2.0.md §5)——
    供上层分诊台(triage)离线抽检消费,不参与本仓任何诊断/打分逻辑。
    works 为空/None 不落盘(不写空壳);写盘异常吞掉,不拖垮 board.json 归档主流程。
    """
    if not works:
        return
    try:
        (cdir / "works.json").write_text(
            json.dumps(works, ensure_ascii=False, indent=2), "utf-8")
    except Exception:  # noqa: BLE001 — 落盘失败不拖垮归档主流程
        pass


def persist_board(account: dict, board: dict, html: str, md: str = "",
                  tags: list[str] | None = None) -> str:
    """元板结果落进归集。返回 run_id。

    report.html 优先用「元数据诊断」契约标准产出(board.contract_doc → render_contract);
    metaform 不可达则回退 ladder html。让案例库自动展示元数据诊断报告。
    """
    nick = account.get("nickname") or board.get("nickname") or "未知账号"
    now = datetime.datetime.now()
    run_id = f"douyin-{_slug(nick)}-{now.strftime('%Y%m%d-%H%M%S')}"
    cdir = _CASES / run_id
    cdir.mkdir(parents=True, exist_ok=True)

    contract_html = _render_contract_html(board)       # 元数据诊断标准产出(优先)
    report_html = contract_html or html
    is_diag = bool(contract_html)
    if report_html:
        (cdir / "report.html").write_text(report_html, "utf-8")
    md = md or ""
    (cdir / "report.md").write_text(md, "utf-8")
    # 结构化板块原文一并存档(便于复算/精修)
    (cdir / "board.json").write_text(json.dumps(board, ensure_ascii=False, indent=2), "utf-8")
    # 原始作品列表顺带落盘(元会诊 MetaConsult v2 接缝一·§5)——account["works"] 在
    # account.py _build_account_for_diagnosis 全量采集路径已备好,这里只多存一份。
    _persist_works(cdir, account.get("works"))

    meta = {
        "run_id": run_id, "platform": "douyin", "source": "metaboard",
        "sec_uid": account.get("sec_uid") or "", "aweme_id": account.get("aweme_id") or "",
        "account_name": nick, "account_type": _infer_type(account),
        "follower": account.get("follower") or 0, "avg_like": account.get("avg_like") or 0,
        "max_like": account.get("max_like") or 0, "burst_ratio": account.get("burst_ratio"),
        "vertical_score": account.get("vertical_score"),
        "hashtags": account.get("hashtags") or [], "signature": account.get("signature") or "",
        "video_title": ("元数据诊断 · 账号诊断报告" if is_diag
                        else "元板·四层下钻数据板块(环境→行业→账号→单条·算账视角)"),
        "video_like": 0, "video_comment": 0, "video_collect": 0, "has_av": False,
        "analyzed_at": now.isoformat(timespec="seconds"), "analyzed_date": now.strftime("%Y-%m-%d"),
        "probe_version": ("元数据诊断 MetaDiag v1.0" if is_diag else "MetaBoard·四层下钻"),
        "polish": {"ok": True, "mode": "metaboard", "model": "", "segs_ok": 1, "segs_total": 1},
        "validation_pass": True, "validation_gaps": [],
        "ai_summary": _summary_from_board(board),
        "tags": tags or (["元数据诊断", "账号诊断", "自动入库"] if is_diag
                         else ["元板MetaBoard", "四层下钻", "自动入库", "视频测试数据"]),
        "audit": {"source_reliability": "公开数据+估算", "confidence_level": "中",
                  "evidence_strength": "Moderate"},
        "docx_path": None, "report_chars": len(report_html or md),
    }
    (cdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

    _backfill_index(meta)
    _register(run_id, nick, "运营报告内联")
    _refresh_embed()
    return run_id


def _render_research_html(md: str, title: str, case_dir: pathlib.Path) -> str:
    """md → html(走 MetaForm research 适配器·模板档即可)·落 case_dir/report.html。
    失败则回退:返回空串(页面用 report.md 兜底渲染)。"""
    try:
        import importlib.util
        mf = pathlib.Path("/Users/metafo/Downloads/metafoclaw/运营报告/metaform")
        if str(mf) not in sys.path:
            sys.path.insert(0, str(mf))
        from adapters import research  # type: ignore
        r = research.render(md, format="html", ts=datetime.datetime.now().strftime("%Y%m%d"),
                            title=title, outdir=str(case_dir))
        out = r.get("path")
        if out and pathlib.Path(out).exists():
            html = pathlib.Path(out).read_text("utf-8")
            (case_dir / "report.html").write_text(html, "utf-8")
            if pathlib.Path(out).name != "report.html":
                pathlib.Path(out).unlink(missing_ok=True)   # 清掉 x-x.html 等渲染默认名
            return html
    except Exception:
        pass
    return ""


def persist_research(title: str, md: str, *, source: str = "probe-research",
                     tags: list[str] | None = None, has_av: bool = False) -> str:
    """研究/调研类报告(无账号·如 probe-research/SVM 类) → 案例。返回 run_id。"""
    now = datetime.datetime.now()
    run_id = f"research-{_slug(title)}-{now.strftime('%Y%m%d-%H%M%S')}"
    cdir = _CASES / run_id
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "report.md").write_text(md or "", "utf-8")
    html = _render_research_html(md or "", title, cdir)

    # 摘要:取首个非标题非空行
    summary = ""
    for line in (md or "").splitlines():
        s = line.strip().lstrip("#").strip()
        if s and not s.startswith(("---", "===", "|")):
            summary = s[:120]; break

    meta = {
        "run_id": run_id, "platform": "research", "source": source,
        "sec_uid": "", "aweme_id": "", "account_name": title, "account_type": "研究·调研",
        "follower": 0, "avg_like": 0, "max_like": 0, "burst_ratio": None,
        "vertical_score": None, "hashtags": [], "signature": "",
        "video_title": title, "video_like": 0, "video_comment": 0, "video_collect": 0,
        "has_av": has_av, "analyzed_at": now.isoformat(timespec="seconds"),
        "analyzed_date": now.strftime("%Y-%m-%d"), "probe_version": source,
        "polish": {"ok": bool(html), "mode": "research", "model": "", "segs_ok": 1, "segs_total": 1},
        "validation_pass": True, "validation_gaps": [], "ai_summary": summary,
        "tags": tags or [source, "调研", "自动入库", "视频测试数据"],
        "audit": {"source_reliability": None, "confidence_level": None, "evidence_strength": None},
        "docx_path": None, "report_chars": len(md or ""),
    }
    (cdir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    _backfill_index(meta)
    _register_generic(run_id, title, source, "运营报告/MetaForm渲染")
    _refresh_embed()
    return run_id


def _register_generic(run_id: str, title: str, product: str, source: str) -> None:
    if not _REG.exists():
        return
    reg = json.loads(_REG.read_text("utf-8"))
    if any(e.get("run_id") == run_id for e in reg["entries"]):
        return
    reg["entries"].append({"product": product, "title": title, "source": source,
                           "status": "collected", "run_id": run_id})
    reg["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    _REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2), "utf-8")


def _backfill_index(meta: dict) -> None:
    idx = json.loads(_IDX.read_text("utf-8")) if _IDX.exists() else {"version": "1.0", "cases": []}
    if any(c["run_id"] == meta["run_id"] for c in idx["cases"]):
        return
    sec = meta.get("sec_uid") or ""
    same = [c for c in idx["cases"] if c.get("sec_uid") == sec and sec]
    e = {k: meta.get(k) for k in _FLAT}
    e.update(prev_run_id=(same[-1]["run_id"] if same else None), version_count=len(same) + 1,
             prev_vid_run_id=None, vid_version_count=1, video_share=0)
    idx["cases"].append(e)
    idx["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    _IDX.write_text(json.dumps(idx, ensure_ascii=False, indent=2), "utf-8")


def _register(run_id: str, title: str, source: str) -> None:
    if not _REG.exists():
        return
    reg = json.loads(_REG.read_text("utf-8"))
    if any(e.get("run_id") == run_id for e in reg["entries"]):
        return
    reg["entries"].append({"product": "metaboard", "title": title, "source": source,
                           "status": "collected", "run_id": run_id})
    reg["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d")
    _REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2), "utf-8")


def _refresh_embed() -> None:
    try:
        subprocess.run([sys.executable, str(_ROOT / "hub" / "build_embed.py")],
                       capture_output=True, timeout=30)
    except Exception:
        pass

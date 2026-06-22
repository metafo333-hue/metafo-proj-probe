"""P0-a 透传修复回归测试（B1/B2/B3/B4）。

覆盖：
  B3  _slugify 产出始终纯 ASCII（中文昵称不再进 run_id）
  B1  result 顶层 aweme_id 被 save_case 入库
  B2  sec_uid 从 account 或 result 兜底读到并入库
  B4  source 字段写入 meta + index（仪表盘图例不再显示「—」）
"""
from __future__ import annotations

import json
import re
import pathlib

import pytest

import scripts.save_case as sc


# ── B3: slug 纯 ASCII ─────────────────────────────────────────────
def test_slugify_chinese_is_ascii():
    out = sc._slugify("北川魔芋姐｜赵娟")
    assert out, "slug 不应为空"
    assert re.fullmatch(r"[a-z0-9]+", out), f"slug 必须纯小写 ASCII，实际: {out!r}"


def test_slugify_ascii_passthrough():
    assert sc._slugify("AnnaVlog") == "annavlog"


def test_slugify_deterministic():
    # 同输入两次必须一致（哈希回退也要确定性）
    assert sc._slugify("纯中文昵称测试") == sc._slugify("纯中文昵称测试")


# ── B1/B2/B4: save_case 入库透传 ──────────────────────────────────
@pytest.fixture
def _isolated_cases(tmp_path, monkeypatch):
    """把案例库重定向到 tmp，避免污染真实 data/cases。"""
    cases = tmp_path / "cases"
    cases.mkdir()
    monkeypatch.setattr(sc, "_CASES_DIR", cases)
    monkeypatch.setattr(sc, "_INDEX_FILE", cases / "index.json")
    return cases


def _fake_result(sec_in_account=True):
    acc = {"nickname": "北川魔芋姐｜赵娟", "follower": 4645,
           "avg_like": 105, "max_like": 383, "signature": "源头直供魔芋"}
    if sec_in_account:
        acc["sec_uid"] = "MS4wLjABAAAAxxx_secuid"
        acc["aweme_id"] = "7641434470629562865"
    return {
        "ok": True,
        "report_md": "# 测试报告\n账号诊断内容若干。",
        "video": {"title": "扎根北川深耕魔芋36年", "like": 196, "comment": 39, "collect": 6},
        "account": acc,
        "audit": {"source_reliability": "B", "confidence_level": "中", "evidence_strength": "中"},
        "aweme_id": "7641434470629562865",
        "sec_uid": "MS4wLjABAAAAxxx_secuid",
        "source": "tikhub",
        "six_layer": None,
    }


def test_save_case_persists_identity_and_source(_isolated_cases):
    run_id = sc.save_case(_fake_result(), gen_summary=False, tags=["测试"])
    # B3: run_id 纯 ASCII
    assert re.fullmatch(r"douyin-[a-z0-9]+-\d{8}-\d{6}", run_id), run_id

    meta = json.loads((_isolated_cases / run_id / "meta.json").read_text("utf-8"))
    assert meta["sec_uid"] == "MS4wLjABAAAAxxx_secuid"   # B2
    assert meta["aweme_id"] == "7641434470629562865"      # B1
    assert meta["source"] == "tikhub"                     # B4

    idx = json.loads((_isolated_cases / "index.json").read_text("utf-8"))
    entry = idx["cases"][-1]
    assert entry["source"] == "tikhub"                    # B4 入索引
    assert entry["sec_uid"] == "MS4wLjABAAAAxxx_secuid"


def test_save_case_sec_uid_fallback_from_result(_isolated_cases):
    """account 里没有 sec_uid 时，从 result 顶层兜底读到（B2 双保险）。"""
    run_id = sc.save_case(_fake_result(sec_in_account=False), gen_summary=False)
    meta = json.loads((_isolated_cases / run_id / "meta.json").read_text("utf-8"))
    assert meta["sec_uid"] == "MS4wLjABAAAAxxx_secuid"
    assert meta["aweme_id"] == "7641434470629562865"

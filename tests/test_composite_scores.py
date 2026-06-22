"""离线测试 · composite_scores.py 8复合指标

覆盖:
  1. 满字段正常计算 → 分数在[0,100] + 评级合法
  2. 缺字段降级 → 不崩 + missing 列表非空
  3. xprof 缺省 → 全指标仍可运行
  4. render_composite_section → 返回非空 markdown 含关键词
  5. compute_all → 返回8个键全有

运行:
  cd /Users/metafo/Downloads/metafoclaw
  PYTHONPATH=/Users/metafo/Downloads/metafoclaw/combo-deep-probe \
    python -m pytest probe/tests/test_composite_scores.py -v
"""
import sys
import os

# 确保 combo-deep-probe 在路径中（离线无需真 API·这里只是 import 路径）
_COMBO = "/Users/metafo/Downloads/metafoclaw/combo-deep-probe"
if _COMBO not in sys.path:
    sys.path.insert(0, _COMBO)

# 被测模块·通过绝对路径确保可找到
_PROBE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROBE_ROOT not in sys.path:
    sys.path.insert(0, _PROBE_ROOT)

import pytest
from app.services.composite_scores import (
    score_c1_health,
    score_c2_fans_quality,
    score_c3_commerce,
    score_c4_content,
    score_c5_track,
    score_c6_breakout,
    score_c7_grade,
    score_c8_private,
    compute_all,
    render_composite_section,
)


# ── 测试夹具 ──────────────────────────────────────────────────────────────────

def _full_account() -> dict:
    """合成满字段 account dict（覆盖方案的19字段）。"""
    return {
        "sec_uid": "test_uid",
        "aweme_id": "7001234567890",
        "nickname": "测试达人",
        "follower": 500_000,
        "max_follower": 600_000,
        "aweme_count": 200,
        "works_analyzed": 50,
        "signature": "专注美食分享",
        "avg_like": 15_000,
        "max_like": 800_000,
        "burst_ratio": 10.0,
        "vertical_score": 0.78,
        "hashtags": ["美食", "探店"],
        "with_commerce_entry": True,
        "live_commerce": True,
        "commerce_user_level": 3,
        "commerce_density": {"ratio": 0.3},
        "follower_drawdown": {"drawdown_pct": 8.5, "label": "轻度掉粉"},
        "engagement_structure": {"label": "实用型", "type": "practical"},
        "mix_count": 5,
        "series_count": 3,
    }


def _full_xprof() -> dict:
    """合成 XingtuProfile 字典·模拟星图数据。"""
    return {
        "is_xingtu": True,
        "price_short": 8200,
        "price_mid": 12000,
        "price_long": 18000,
        "cpm": {"cpm_1_20": 85.0, "cpm_21_60": 70.0, "cpm_60": 55.0},
        "expect_vv": {"value": 200_000},
        "link_shopping_index": {
            "avg_value": 72.0, "value": 68.0, "rank_percent": 0.08,
        },
        "link_convert_index": {
            "avg_value": 65.0, "value": 61.0, "rank_percent": 0.12,
        },
        "link_spread_index": {
            "avg_value": 58.0, "value": 55.0, "rank_percent": 0.15,
        },
        "link_star_index": {
            "avg_value": 70.0, "value": 66.0, "rank_percent": 0.10,
        },
        "cooperate_index": {
            "avg_value": 60.0, "value": 57.0, "rank_percent": 0.18,
        },
        "cp_index": {"avg_value": 55.0, "value": 52.0, "rank_percent": 0.20},
        "fans_portrait": [
            {
                "type": 3, "origin_type": 3, "display": "设备",
                "top5": [
                    {"name": "iPhone", "value": 42.5},
                    {"name": "华为", "value": 25.0},
                ],
            },
            {
                "type": 12, "origin_type": 12, "display": "客单价",
                "top5": [
                    {"name": "0-50", "value": 20.0},
                    {"name": "100-200", "value": 35.0},
                    {"name": "200-500", "value": 28.0},
                ],
            },
        ],
        "audience_portrait": [],
        "rec_videos": [
            {"title": "竞品A", "interact_rate": 0.05, "play_count": 500_000},
            {"title": "竞品B", "interact_rate": 0.04, "play_count": 300_000},
        ],
        "industry_tags": ["美食"],
    }


def _empty_account() -> dict:
    """最小化 account dict·测试降级。"""
    return {"sec_uid": "empty_uid", "nickname": "空白达人"}


# ── 测试用例 ──────────────────────────────────────────────────────────────────

class TestC1Health:
    def test_full_score_in_range(self):
        r = score_c1_health(_full_account())
        assert 0 <= r["score"] <= 100
        assert r["phase"] in ("上升", "平台", "衰退")
        assert isinstance(r["breakdown"], dict)
        assert len(r["breakdown"]) == 5

    def test_empty_account_no_crash(self):
        r = score_c1_health(_empty_account())
        assert 0 <= r["score"] <= 100
        assert len(r["missing"]) > 0

    def test_drawdown_from_max_follower(self):
        acc = {"follower": 900_000, "max_follower": 1_000_000, "aweme_count": 100}
        r = score_c1_health(acc)
        # 10% 掉粉·粉丝净值应 <满分
        assert r["breakdown"]["follower_net"] < 100


class TestC2FansQuality:
    def test_full_score_in_range(self):
        r = score_c2_fans_quality(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert r["label"] in ("高质量粉", "含水", "刷量风险")

    def test_no_xprof(self):
        r = score_c2_fans_quality(_full_account(), None)
        assert 0 <= r["score"] <= 100
        assert any("#需全量数据" in m for m in r["missing"])

    def test_empty_no_crash(self):
        r = score_c2_fans_quality(_empty_account(), None)
        assert 0 <= r["score"] <= 100
        assert len(r["missing"]) > 0


class TestC3Commerce:
    def test_with_xprof_score_in_range(self):
        r = score_c3_commerce(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert isinstance(r["path"], str) and len(r["path"]) > 0

    def test_no_commerce_entry(self):
        acc = dict(_full_account())
        acc["with_commerce_entry"] = False
        acc["live_commerce"] = False
        r = score_c3_commerce(acc, None)
        assert r["score"] < score_c3_commerce(_full_account(), None)["score"]

    def test_no_xprof_degrades(self):
        r = score_c3_commerce(_full_account(), None)
        assert 0 <= r["score"] <= 100
        assert any("星图" in m for m in r["missing"])


class TestC4Content:
    def test_full_score_in_range(self):
        r = score_c4_content(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert isinstance(r["weak"], str)

    def test_empty_account(self):
        r = score_c4_content(_empty_account(), None)
        assert 0 <= r["score"] <= 100
        assert len(r["missing"]) > 0


class TestC5Track:
    def test_full_score_in_range(self):
        r = score_c5_track(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert r["track"] in ("蓝海", "红海", "无路")

    def test_no_xprof(self):
        r = score_c5_track(_full_account(), None)
        assert 0 <= r["score"] <= 100


class TestC6Breakout:
    def test_full_score_in_range(self):
        r = score_c6_breakout(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert r["type"] in ("跨赛道破圈", "爆款型破圈", "账号级内循环")

    def test_empty_no_crash(self):
        r = score_c6_breakout(_empty_account(), None)
        assert 0 <= r["score"] <= 100


class TestC7Grade:
    def test_full_grade_valid(self):
        r = score_c7_grade(_full_account(), _full_xprof())
        assert r["grade"] in ("A", "B", "C", "D", "F")
        assert 0 <= r["score"] <= 100
        assert isinstance(r["desc"], str)

    def test_no_data_low_grade(self):
        r = score_c7_grade(_empty_account(), None)
        assert r["grade"] in ("C", "D", "F")  # 无数据应评级偏低

    def test_watered_engagement_lowers_score(self):
        acc = dict(_full_account())
        acc["engagement_structure"] = {"label": "刷量账号", "type": "risk"}
        r_watered = score_c7_grade(acc, _full_xprof())
        r_normal = score_c7_grade(_full_account(), _full_xprof())
        assert r_watered["score"] <= r_normal["score"]


class TestC8Private:
    def test_full_score_in_range(self):
        r = score_c8_private(_full_account(), _full_xprof())
        assert 0 <= r["score"] <= 100
        assert isinstance(r["path"], str)

    def test_no_series_low_score(self):
        acc = dict(_full_account())
        acc["mix_count"] = 0
        acc["series_count"] = 0
        r = score_c8_private(acc, None)
        r_normal = score_c8_private(_full_account(), None)
        assert r["score"] <= r_normal["score"]


class TestComputeAll:
    def test_returns_8_keys(self):
        result = compute_all(_full_account(), _full_xprof())
        assert set(result.keys()) == {"c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"}

    def test_all_scores_in_range(self):
        result = compute_all(_full_account(), _full_xprof())
        for k in ("c1", "c2", "c3", "c4", "c5", "c6", "c8"):
            assert 0 <= result[k]["score"] <= 100, f"{k}.score 超范围"
        assert 0 <= result["c7"]["score"] <= 100
        assert result["c7"]["grade"] in ("A", "B", "C", "D", "F")


class TestRenderCompositeSection:
    def test_returns_markdown(self):
        md = render_composite_section(_full_account(), _full_xprof())
        assert isinstance(md, str)
        assert len(md) > 100
        assert "复合指标" in md

    def test_contains_all_8_indicators(self):
        md = render_composite_section(_full_account(), _full_xprof())
        for label in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"):
            assert label in md, f"缺失指标 {label}"

    def test_degraded_section_notes_missing(self):
        # 无 xprof 时降级说明应出现
        md = render_composite_section(_empty_account(), None)
        assert "待全量数据" in md or "需全量数据" in md

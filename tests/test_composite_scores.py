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


# ── 深化子项 · 真实 schema 夹具 ───────────────────────────────────────────────

def _comment_deep_real() -> dict:
    """匹配 account.py _build_comment_deep 实测产出。"""
    return {
        "sample_size": 20,
        "ip_concentration": 0.25,   # 最高省份占比 25%(自然)
        "ip_diversity": 0.6,        # 12 个省份/20
        "level_dist": {"1": 14, "2": 6},   # 主楼14·楼中楼6 → l1=0.7
        "author_reply_rate": 0.3,
        "avg_digg": 8.0,
        "reply_active_rate": 0.4,
        "top_keywords": [
            {"word": "加微信", "count": 5},     # 导流加微
            {"word": "多少钱", "count": 4},     # 咨询购买
            {"word": "好看", "count": 6},
            {"word": "求教程", "count": 3},     # 求课求教
            {"word": "支持", "count": 2},
        ],
    }


def _xprof_dual_portrait() -> dict:
    """带双画像(粉丝vs观众)+rec_interact_rates+track 的真实 schema xprof。

    fans_portrait/audience_portrait 用 _p2c 适配后的字典形态 [{name,value}]·
    并额外测元组形态(原始 XingtuProfile)。
    """
    x = _full_xprof()
    # 字典形态画像(经 account.py _p2c)
    x["fans_portrait"] = [
        {"origin_type": 1, "type": 1, "display": "年龄",
         "top5": [{"name": "18-23", "value": 45.0}, {"name": "24-30", "value": 35.0}]},
        {"origin_type": 2, "type": 2, "display": "省份",
         "top5": [{"name": "广东", "value": 18.0}, {"name": "江苏", "value": 12.0},
                  {"name": "浙江", "value": 10.0}, {"name": "山东", "value": 8.0}]},
        {"origin_type": 3, "type": 3, "display": "设备",
         "top5": [{"name": "iPhone", "value": 42.0}, {"name": "华为", "value": 25.0}]},
        {"origin_type": 5, "type": 5, "display": "城市等级",
         "top5": [{"name": "新一线", "value": 28.0}, {"name": "一线", "value": 20.0},
                  {"name": "二线", "value": 18.0}]},
        {"origin_type": 8, "type": 8, "display": "城市",
         "top5": [{"name": "成都", "value": 22.0}, {"name": "重庆", "value": 15.0}]},
        {"origin_type": 12, "type": 12, "display": "客单价",
         "top5": [{"name": "0-50", "value": 20.0}, {"name": "100-200", "value": 35.0}]},
    ]
    # 观众与粉丝在年龄/省份上有错位 → 触发破圈
    x["audience_portrait"] = [
        {"origin_type": 1, "type": 1, "display": "年龄",
         "top5": [{"name": "24-30", "value": 42.0}, {"name": "31-40", "value": 30.0}]},
        {"origin_type": 2, "type": 2, "display": "省份",
         "top5": [{"name": "北京", "value": 20.0}, {"name": "广东", "value": 15.0}]},
    ]
    x["rec_interact_rates"] = [0.05, 0.04, 0.06, 0.03]   # 竞品代表作互动率(已算)
    return x


class TestDeepenedSubitems:
    def test_c2_bot_risk_multidim(self):
        acc = dict(_full_account())
        acc["comment_deep"] = _comment_deep_real()
        r = score_c2_fans_quality(acc, _xprof_dual_portrait())
        br = r["bot_risk"]
        assert br["degraded"] is False
        assert 0 <= br["score"] <= 100
        assert len(br["dims"]) >= 4   # 多维·至少 ip_c/ip_d/digg/reply
        assert len(br["evidence"]) >= 1
        assert br["verdict"] in (
            "健康(无明显水军特征)", "可疑(部分维度异常·建议二次核验)", "高风险(多维异常·疑刷量/控评)")

    def test_c2_bot_risk_high_concentration_lowers(self):
        acc = dict(_full_account())
        cd = _comment_deep_real()
        cd["ip_concentration"] = 0.85   # 高度集中疑刷
        cd["ip_diversity"] = 0.15
        acc["comment_deep"] = cd
        r_bad = score_c2_fans_quality(acc, None)["bot_risk"]
        acc2 = dict(_full_account())
        acc2["comment_deep"] = _comment_deep_real()
        r_good = score_c2_fans_quality(acc2, None)["bot_risk"]
        assert r_bad["score"] < r_good["score"]

    def test_c2_comment_realness(self):
        acc = dict(_full_account())
        acc["comment_deep"] = _comment_deep_real()
        cr = score_c2_fans_quality(acc, None)["comment_realness"]
        assert cr["degraded"] is False
        assert cr["level1_ratio"] == 0.7
        assert 0 <= cr["score"] <= 100

    def test_c2_geo_diversity(self):
        r = score_c2_fans_quality(_full_account(), _xprof_dual_portrait())
        gd = r["geo_diversity"]
        assert gd["degraded"] is False
        assert gd["top_province"] == "广东"
        assert gd["province_hhi"] is not None
        assert "型" in gd["verdict"]

    def test_c2_geo_degrades_without_portrait(self):
        r = score_c2_fans_quality(_full_account(), None)
        assert r["geo_diversity"]["degraded"] is True

    def test_c4_competitor_gap_attribution(self):
        r = score_c4_content(_full_account(), _xprof_dual_portrait())
        cg = r["competitor_gap"]
        assert cg["degraded"] is False
        assert cg["comp_median"] is not None
        assert cg["self_rate"] is not None
        assert cg["attribution"] is not None
        assert cg["verdict"] in ("互动领先竞品", "与竞品持平", "互动落后竞品")

    def test_c4_competitor_gap_degrades(self):
        r = score_c4_content(_full_account(), None)
        assert r["competitor_gap"]["degraded"] is True

    def test_c5_blue_ocean(self):
        acc = dict(_full_account())
        acc["track_competition"] = {"keyword": "美食", "result_count": 18, "has_more": True}
        r = score_c5_track(acc, _xprof_dual_portrait())
        bo = r["blue_ocean"]
        assert bo["degraded"] is False
        assert bo["result_count"] == 18
        assert "红海" in bo["verdict"]   # 满页+has_more → 红海

    def test_c5_blue_ocean_sparse(self):
        acc = dict(_full_account())
        acc["track_competition"] = {"keyword": "冷门赛道", "result_count": 2, "has_more": False}
        r = score_c5_track(acc, None)
        assert r["blue_ocean"]["score"] > 60   # 稀疏 → 蓝海高分

    def test_c6_portrait_mismatch_breakout(self):
        r = score_c6_breakout(_full_account(), _xprof_dual_portrait())
        age = r["age_mismatch"]
        geo = r["geo_mismatch"]
        assert age["degraded"] is False
        assert geo["degraded"] is False
        # 年龄 top 粉丝18-23 vs 观众24-30 → 切换
        assert age["top_switch"] is True
        assert isinstance(r["breakout_directions"], list)

    def test_c6_mismatch_degrades_single_portrait(self):
        x = _full_xprof()
        x["audience_portrait"] = []
        r = score_c6_breakout(_full_account(), x)
        assert r["age_mismatch"]["degraded"] is True

    def test_c8_private_intent_lexicon(self):
        acc = dict(_full_account())
        acc["comment_deep"] = _comment_deep_real()
        r = score_c8_private(acc, _xprof_dual_portrait())
        pi = r["private_intent"]
        assert pi["degraded"] is False
        assert "导流加微" in pi["hit_categories"]
        assert "咨询购买" in pi["hit_categories"]
        assert len(pi["hit_words"]) >= 2
        assert pi["score"] > 0

    def test_c8_private_intent_degrades(self):
        r = score_c8_private(_full_account(), None)
        assert r["private_intent"]["degraded"] is True

    def test_tuple_portrait_form_supported(self):
        """原始 XingtuProfile top5 元组形态也能解析(不止 _p2c 字典形态)。"""
        x = _full_xprof()
        x["fans_portrait"] = [
            {"origin_type": 2, "type": 2, "display": "省份",
             "top5": [("广东", 18), ("江苏", 12), ("浙江", 10)]},
        ]
        r = score_c2_fans_quality(_full_account(), x)
        assert r["geo_diversity"]["degraded"] is False
        assert r["geo_diversity"]["top_province"] == "广东"

    def test_deepened_insights_in_render(self):
        acc = dict(_full_account())
        acc["comment_deep"] = _comment_deep_real()
        acc["track_competition"] = {"keyword": "美食", "result_count": 5, "has_more": False}
        md = render_composite_section(acc, _xprof_dual_portrait())
        assert "深化子项洞察" in md

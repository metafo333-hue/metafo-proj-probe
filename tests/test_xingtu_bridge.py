"""章四 §4.5 内容×商业桥接测试·离线·0 网络/0 扣费。"""
import sys
import os

# combo-deep-probe 可选(离线可不可达)
sys.path.insert(0, "/Users/metafo/Downloads/metafoclaw/combo-deep-probe")

import unittest

from app.services import xingtu_profile as xp
from app.services.xingtu_profile import XingtuProfile, _assemble

# ── 合成数据 ──────────────────────────────────────────────────────────────────
_SAMPLE = {
    "kol_service_price_v1": {
        "price_info": [
            {"desc": "1-20s视频", "price": 8200, "settlement_desc": "固定价格",
             "video_type": 1, "is_open": True},
            {"desc": "21-60s视频", "price": 11200, "settlement_desc": "固定价格",
             "video_type": 2, "is_open": True},
        ],
        "industry_tags": ["美妆-面部洗护"],
    },
    "kol_cp_info_v1": {
        "expect_cpe": {"cpe_1_20": "228"},
        "expect_cpm": {"cpm_1_20": "2156"},
        "expect_vv": {"value": 380245},
    },
    "kol_fans_portrait_v1": {
        "distributions": [
            {"origin_type": 0, "type_display": "性别分布", "description": "男性居多,占比57%",
             "distribution_list": [{"distribution_key": "男", "distribution_value": "57"},
                                   {"distribution_key": "女", "distribution_value": "43"}]},
            {"origin_type": 2, "type_display": "省份分布", "description": "广东居多",
             "distribution_list": [{"distribution_key": "广东", "distribution_value": "17"}]},
        ],
    },
}

_ACCOUNT = {
    "follower": 100000,
    "avg_like": 5000,
    "video_stats": [],
}

_AV_SIX = {
    "emotion": {"score": 0.7, "conf": 0.9},
    "rhythm": {"score": 0.6, "conf": 0.8},
    "visual": {"score": 0.5, "conf": 0.85},
}


def _built() -> XingtuProfile:
    p = XingtuProfile(sec_uid="sec_x", kolid="888")
    _assemble(p, _SAMPLE)
    return p


class TestPerFanValue(unittest.TestCase):
    """Q4 单千粉报价"""

    def test_per_fan_value_calculation(self):
        """price_short=8200·follower=100000 → 82元/千粉·溢价"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT)
        pfv = bridge["per_fan_value"]
        self.assertIsNotNone(pfv)
        self.assertAlmostEqual(pfv["per_fan_k"], 82.0, places=1)
        self.assertEqual(pfv["label"], "溢价")

    def test_per_fan_low_label(self):
        """千粉价格低于5元 → 偏低"""
        acc = dict(_ACCOUNT, follower=2_000_000)  # 8200/2000000*1000 = 4.1
        bridge = xp.bridge_content_commercial(_built(), acc)
        pfv = bridge["per_fan_value"]
        self.assertIsNotNone(pfv)
        self.assertLess(pfv["per_fan_k"], 5.0)
        self.assertEqual(pfv["label"], "偏低")

    def test_per_fan_none_when_missing_follower(self):
        """follower 缺失 → per_fan_value=None"""
        bridge = xp.bridge_content_commercial(_built(), {})
        self.assertIsNone(bridge["per_fan_value"])

    def test_per_fan_none_when_no_price(self):
        """price_short=None → per_fan_value=None"""
        p = XingtuProfile(sec_uid="x", kolid="0")
        _assemble(p, {})
        bridge = xp.bridge_content_commercial(p, _ACCOUNT)
        self.assertIsNone(bridge["per_fan_value"])


class TestStyleVsPrice(unittest.TestCase):
    """Q1 视听风格 × 报价档位"""

    def test_quality_matches_b_tier(self):
        """av_six质量≥0.45 + 报价B级(8200) → 匹配"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT, av_six=_AV_SIX)
        svp = bridge["style_vs_price"]
        self.assertIsNotNone(svp)
        self.assertEqual(svp["price_tier"], "B")
        self.assertIsNotNone(svp["av_quality"])
        self.assertGreaterEqual(svp["av_quality"], 0.45)
        self.assertEqual(svp["match"], "匹配")

    def test_style_none_when_av_six_none(self):
        """av_six=None → style_vs_price=None"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT, av_six=None)
        self.assertIsNone(bridge["style_vs_price"])


class TestROI(unittest.TestCase):
    """ROI 复用 roi_triangle"""

    def test_roi_present(self):
        """price_short=8200·expect_vv=380245 → roi 不为 None·verdict=数据吻合可信"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT)
        roi = bridge["roi"]
        self.assertIsNotNone(roi)
        self.assertAlmostEqual(roi["actual_cpm"], 21.6, delta=0.2)
        self.assertEqual(roi["verdict"], "数据吻合可信")

    def test_roi_in_signals(self):
        """ROI 结果应进入 signals 列表"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT)
        sigs_text = " ".join(bridge["signals"])
        self.assertIn("ROI核验", sigs_text)


class TestPortraitConsistency(unittest.TestCase):
    """Q2 官方画像 vs 评论估算一致性"""

    def test_consistent_gender(self):
        """评论gender=男 与星图fans top=男 → match=True"""
        acc = dict(_ACCOUNT, comment_top_gender="男")
        bridge = xp.bridge_content_commercial(_built(), acc)
        pc = bridge["portrait_consistency"]
        self.assertIsNotNone(pc)
        self.assertTrue(pc["gender"]["match"])

    def test_inconsistent_city(self):
        """评论city=北京 vs 星图city=广东 → match=False·进入 signals"""
        acc = dict(_ACCOUNT, comment_top_city="北京")
        bridge = xp.bridge_content_commercial(_built(), acc)
        pc = bridge["portrait_consistency"]
        self.assertIsNotNone(pc)
        self.assertFalse(pc["city"]["match"])
        sigs_text = " ".join(bridge["signals"])
        self.assertIn("城市画像不一致", sigs_text)


class TestRenderBridge(unittest.TestCase):
    """render_bridge_section"""

    def test_render_contains_key_elements(self):
        """markdown 段应含单千粉/ROI/综合信号"""
        bridge = xp.bridge_content_commercial(_built(), _ACCOUNT, av_six=_AV_SIX)
        md = xp.render_bridge_section(bridge)
        self.assertIsNotNone(md)
        self.assertIn("单千粉报价", md)
        self.assertIn("ROI", md)
        self.assertIn("内容×商业桥接洞察", md)

    def test_render_none_when_empty(self):
        """空 bridge → render 返回 None"""
        self.assertIsNone(xp.render_bridge_section(None))
        self.assertIsNone(xp.render_bridge_section({}))


if __name__ == "__main__":
    unittest.main()

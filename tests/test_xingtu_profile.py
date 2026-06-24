"""星图整体并行模块测试·组装/组合洞察/渲染(离线·0 网络/0 扣费)。

fixture 基于 tikhub-xingtu-kol-sample.json 实测真值(2026-06-22)。
"""
import unittest

from app.services import xingtu_profile as xp
from app.services.xingtu_profile import XingtuProfile, _assemble

# 实测真实结构(精简)
_SAMPLE = {
    "kol_service_price_v1": {
        "price_info": [
            {"desc": "1-20s视频", "price": 8200, "settlement_desc": "固定价格", "video_type": 1, "is_open": True},
            {"desc": "21-60s视频", "price": 11200, "settlement_desc": "固定价格", "video_type": 2, "is_open": True},
            {"desc": "60s以上视频", "price": 14900, "settlement_desc": "固定价格", "video_type": 71, "is_open": True},
        ],
        "industry_tags": ["美妆-面部洗护", "传媒资讯-其他传媒资讯"],
    },
    "kol_cp_info_v1": {
        "expect_cpe": {"cpe_1_20": "228", "cpe_60": "414"},
        "expect_cpm": {"cpm_1_20": "2156", "cpm_60": "3918"},  # 分·/100=¥21.56-39.18
        "expect_vv": {"value": 380245},
    },
    "kol_xingtu_index_v1": {
        "cooperate_index": {"avg_value": 75.57, "rank": 449967, "rank_percent": 0.2137},
        "cp_index": {"avg_value": 64.02, "rank_percent": 0.1297},
        "link_shopping_index": {"avg_value": 53.4, "rank_percent": 0.0118},
        "link_convert_index": {"avg_value": 55.29, "rank_percent": 0.0022},
    },
    "kol_fans_portrait_v1": {
        "distributions": [
            {"origin_type": 0, "type_display": "性别分布", "description": "男性居多,占比57%",
             "distribution_list": [{"distribution_key": "男", "distribution_value": "57"},
                                   {"distribution_key": "女", "distribution_value": "43"}]},
            {"origin_type": 1, "type_display": "年龄分布", "description": "31到40岁居多,占比34%",
             "distribution_list": [{"distribution_key": "31-40", "distribution_value": "34"}]},
        ],
    },
    "kol_audience_portrait_v1": {
        "distributions": [
            {"origin_type": 0, "type_display": "性别分布", "description": "女性居多",
             "distribution_list": [{"distribution_key": "女", "distribution_value": "60"},
                                   {"distribution_key": "男", "distribution_value": "40"}]},
        ],
    },
}


def _built() -> XingtuProfile:
    p = XingtuProfile(sec_uid="sec_x", kolid="888")
    _assemble(p, _SAMPLE)
    return p


class TestAssemble(unittest.TestCase):
    def test_prices(self):
        p = _built()
        self.assertEqual(p.price_short, 8200)
        self.assertEqual(p.price_mid, 11200)
        self.assertEqual(p.price_long, 14900)
        self.assertEqual(len(p.prices), 3)
        self.assertIn("美妆-面部洗护", p.industry_tags)

    def test_cp_and_vv(self):
        p = _built()
        self.assertEqual(p.expect_vv, 380245)
        self.assertEqual(p.cpm.get("cpm_1_20"), "2156")

    def test_six_indices(self):
        p = _built()
        self.assertAlmostEqual(p.cooperate_index.avg_value, 75.57)
        self.assertAlmostEqual(p.link_shopping_index.avg_value, 53.4)   # 带货个体值(章四 GPM 修复)
        self.assertAlmostEqual(p.link_convert_index.rank_percent, 0.0022)

    def test_portrait_type_mapping(self):
        p = _built()
        # type0=性别 type1=年龄(实测真值·非反)
        types = {d["type"]: d["display"] for d in p.fans_portrait}
        self.assertEqual(types[0], "性别分布")
        self.assertEqual(types[1], "年龄分布")

    def test_is_xingtu_true(self):
        self.assertTrue(_built().is_xingtu)

    def test_empty_degrades(self):
        p = XingtuProfile(sec_uid="x")
        _assemble(p, {})
        self.assertFalse(p.is_xingtu)


class TestCombinationInsights(unittest.TestCase):
    def test_roi_triangle_fits(self):
        # actual = 8200/(380245/1000)=21.6; official=2156/100=21.56 → ratio≈1 吻合
        roi = xp.roi_triangle(_built())
        self.assertAlmostEqual(roi["actual_cpm"], 21.6, delta=0.2)
        self.assertAlmostEqual(roi["official_cpm"], 21.56, delta=0.1)
        self.assertEqual(roi["verdict"], "数据吻合可信")

    def test_breakout_signal_detects(self):
        # 粉丝性别top1=男·观众top1=女 → 破圈
        bo = xp.breakout_signal(_built())
        self.assertTrue(bo["has_breakout"])
        self.assertIn("性别", bo["dims"])

    def test_breakout_none_without_audience(self):
        p = _built()
        p.audience_portrait = []
        self.assertIsNone(xp.breakout_signal(p))

    def test_momentum_with_rank(self):
        m = xp.commercial_momentum(_built())
        self.assertEqual(m["rank"], "行业前21.4%")   # cooperate rank_percent 0.2137


class TestRender(unittest.TestCase):
    def test_render_business(self):
        md = xp.render_xingtu_profile_section(_built())
        self.assertIn("8,200", md)
        self.assertIn("带货指数", md)         # 个体商业值(GPM修复)
        self.assertIn("前1.2%", md)           # link_shopping rank_percent 0.0118
        self.assertIn("投放ROI", md)
        self.assertIn("破圈", md)
        self.assertNotIn("31到40岁", md)      # 画像详情移到独立 audience 段

    def test_render_fans_portrait(self):
        md = xp.render_fans_portrait_section(_built())
        self.assertIn("男性居多", md)
        self.assertIn("31到40岁", md)
        self.assertIn("星图官方", md)

    def test_render_none_when_not_xingtu(self):
        p = XingtuProfile(sec_uid="x")   # is_xingtu=False
        self.assertIsNone(xp.render_xingtu_profile_section(p))
        self.assertIsNone(xp.render_xingtu_profile_section(None))
        self.assertIsNone(xp.render_fans_portrait_section(p))


if __name__ == "__main__":
    unittest.main()

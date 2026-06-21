"""audience_profile.py + audience_source.py 离线测试 · 零网络 · 零 LLM · $0。

覆盖：
  - 样本门：粉丝<100 不诊断（target_only）/ <1000 只定性（definite=False）
  - 来源定色：A 路 official=🟩 / B 路 benchmark=🟨 / C 路 self_inferred=🟥
  - 结论颜色取更不确定的一方
  - 错位诊断：美业性别/地域/年龄错位判据
  - PIPL：C 路（粉丝列表聚合）默认关·授权也需总开关
  - 防玄学：目标画像标 🟨·无数据走 target_only·不冒充官方
"""
import unittest

from app.datasources import audience_source as src
from app.services.audience_profile import (
    diagnose, render_audience_section, INDUSTRY_TARGET_PROFILE,
)


# ── Fixtures（聚合统计·无个体信息·符合 PIPL）──
MISMATCH_BEAUTY = {  # 美业·实际严重错位：男多/外地多/偏年轻
    "source": "official_authorized",
    "gender": {"male": 55, "female": 45},
    "geo": {"本地": 20, "省内": 30, "全国": 50},
    "age": {"18-24": 60, "25-30": 25, "31-40": 15},
}
GOOD_BEAUTY = {  # 美业·实际匹配：女多/本地多/成熟
    "source": "official_authorized",
    "gender": {"male": 20, "female": 80},
    "geo": {"本地": 70, "省内": 20, "全国": 10},
    "age": {"25-30": 50, "31-40": 35, "18-24": 15},
}
BENCHMARK_DATA = {  # B 路对标
    "gender": {"male": 50, "female": 50},
    "geo": {"本地": 30, "全国": 70},
    "age": {"18-24": 55, "25-30": 45},
}


class TestSampleGate(unittest.TestCase):
    def test_under_100_target_only(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=50)
        self.assertEqual(d["mode"], "target_only")
        self.assertIn("target", d)

    def test_no_profile_target_only(self):
        d = diagnose(None, "美业", followers=5000)
        self.assertEqual(d["mode"], "target_only")
        self.assertIn("截图", d["note"])  # 引导上传后台

    def test_under_1000_definite_false(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=500)
        self.assertEqual(d["mode"], "diagnose")
        self.assertFalse(d["definite"])  # 只定性·不出百分比

    def test_over_1000_definite_true(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        self.assertTrue(d["definite"])

    def test_negative_followers_none(self):
        self.assertIsNone(diagnose(MISMATCH_BEAUTY, "美业", followers=-1))


class TestSourceColor(unittest.TestCase):
    def test_official_green(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        self.assertEqual(d["source_color"], "🟩")

    def test_benchmark_yellow(self):
        prof = src.from_benchmark(BENCHMARK_DATA)
        d = diagnose(prof, "美业", followers=5000)
        self.assertEqual(d["source_color"], "🟨")

    def test_self_inferred_red_and_color_min(self):
        prof = {"source": "self_inferred",
                "gender": {"male": 60, "female": 40},
                "geo": {"本地": 10, "全国": 90},
                "age": {"18-24": 70, "25-30": 30}}
        d = diagnose(prof, "美业", followers=5000)
        self.assertEqual(d["source_color"], "🟥")
        # 结论颜色取更不确定一方：目标🟨 + 实际🟥 → 🟥
        self.assertTrue(d["mismatches"])
        self.assertTrue(all(m["color"] == "🟥" for m in d["mismatches"]))


class TestMismatchDetection(unittest.TestCase):
    def test_beauty_full_mismatch(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        dims = {m["dim"] for m in d["mismatches"]}
        # 美业关键维度 gender/geo/age 全错位
        self.assertIn("gender", dims)
        self.assertIn("geo", dims)
        self.assertIn("age", dims)

    def test_beauty_geo_severe(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        geo = next(m for m in d["mismatches"] if m["dim"] == "geo")
        # 本地 20% vs 目标 60% → 严重错位
        self.assertIn("严重", geo["severity"])

    def test_good_account_no_mismatch(self):
        d = diagnose(GOOD_BEAUTY, "美业", followers=5000)
        self.assertEqual(d["mismatches"], [])

    def test_advice_present(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        for m in d["mismatches"]:
            self.assertTrue(m["advice"])


class TestPIPLComplianceCRoute(unittest.TestCase):
    def test_c_route_default_off(self):
        # ENABLE_FOLLOWER_AGGREGATION 默认 False
        self.assertFalse(src.ENABLE_FOLLOWER_AGGREGATION)
        self.assertIsNone(src.from_follower_list("sec123", "key", creator_authorized=True))

    def test_c_route_off_even_when_switch_on_without_auth(self):
        orig = src.ENABLE_FOLLOWER_AGGREGATION
        src.ENABLE_FOLLOWER_AGGREGATION = True
        try:
            # 总开关开·但未授权分析自己粉丝 → 仍 None
            self.assertIsNone(src.from_follower_list("sec123", "key", creator_authorized=False))
        finally:
            src.ENABLE_FOLLOWER_AGGREGATION = orig

    def test_creator_export_official_source(self):
        prof = src.from_creator_export({"gender": {"male": 1, "female": 1}})
        self.assertEqual(prof["source"], "official_authorized")

    def test_creator_export_empty_none(self):
        self.assertIsNone(src.from_creator_export(None))


class TestAntiMysticism(unittest.TestCase):
    def test_target_profile_all_industries_present(self):
        for ind in ("餐饮", "美业", "知识科普"):
            self.assertIn(ind, INDUSTRY_TARGET_PROFILE)

    def test_render_target_only_marks_inference(self):
        d = diagnose(None, "美业", followers=5000)
        md = render_audience_section(d)
        self.assertIn("🟨", md)  # 目标画像标经验推断
        self.assertIn("行业经验", md)

    def test_render_diagnose_no_fake_official(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=5000)
        md = render_audience_section(d)
        self.assertIn("画像来源", md)
        self.assertIn("绝不冒充官方", md)

    def test_render_small_sample_qualitative_only(self):
        d = diagnose(MISMATCH_BEAUTY, "美业", followers=500)
        md = render_audience_section(d)
        self.assertIn("小样本", md)

    def test_render_none_passthrough(self):
        self.assertIsNone(render_audience_section(None))


if __name__ == "__main__":
    unittest.main()

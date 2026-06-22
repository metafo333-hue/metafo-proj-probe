"""l0_environment L0 环境层 · 离线测试 · 零网络 · $0。

测确定性逻辑:schema 产出 / 粉丝分层 / 商业号额外高压线 /
平台规则种子 / 趋势拿不到时诚实标 / gaps 追踪 / 渲染。
"""
import unittest

from app.services.l0_environment import (
    build_l0_environment, render_l0_section, _tier,
)

ACCT_SMALL = {"nickname": "小号", "follower": 277}
ACCT_MID = {"nickname": "魔芋姐", "follower": 4645}
ACCT_BIG = {"nickname": "大V", "follower": 200000}


class TestL0Environment(unittest.TestCase):

    # ---- 分层 ----
    def test_tier_coldstart(self):
        t, _ = _tier(277)
        self.assertIn("冷启", t)

    def test_tier_waist(self):
        t, _ = _tier(50000)
        self.assertIn("腰部", t)

    def test_tier_head(self):
        t, _ = _tier(200000)
        self.assertIn("头部", t)

    # ---- build schema ----
    def test_build_has_schema_keys(self):
        l0 = build_l0_environment(ACCT_MID, track="产业带货")
        for k in ("track", "platform", "macro", "position_in_track", "data_source_meta"):
            self.assertIn(k, l0)

    def test_build_platform_rules_seed(self):
        l0 = build_l0_environment(ACCT_MID, track="美食")
        self.assertIn("AI", l0["platform"]["ai_label"])
        self.assertTrue(l0["platform"]["forbidden_zones"])

    def test_business_extra_redlines(self):
        l0_biz = build_l0_environment(ACCT_MID, track="B2B", is_business=True)
        l0_per = build_l0_environment(ACCT_MID, track="情感", is_business=False)
        self.assertGreater(len(l0_biz["platform"]["forbidden_zones"]),
                           len(l0_per["platform"]["forbidden_zones"]))
        self.assertTrue(any("虚假宣传" in z for z in l0_biz["platform"]["forbidden_zones"]))

    # ---- 拿不到诚实标(gaps) ----
    def test_trend_gap_tracked_when_no_source(self):
        l0 = build_l0_environment(ACCT_MID, track="美食")  # 无 track_trend
        self.assertIsNone(l0["track"]["trend_direction"])
        self.assertIn("赛道大盘趋势", l0["data_source_meta"]["gaps"])

    def test_trend_filled_when_source(self):
        l0 = build_l0_environment(ACCT_MID, track="美食", track_trend="上升")
        self.assertEqual(l0["track"]["trend_direction"], "上升")
        self.assertNotIn("赛道大盘趋势", l0["data_source_meta"]["gaps"])

    # ---- 渲染 ----
    def test_render_has_platform_rules(self):
        md = render_l0_section(build_l0_environment(ACCT_MID, track="美食"))
        self.assertIn("高压线", md)
        self.assertIn("赛道", md)

    def test_render_trend_gap_is_honest(self):
        md = render_l0_section(build_l0_environment(ACCT_MID, track="美食"))  # 无 trend
        self.assertIn("没接到", md)        # 诚实标·不瞎编

    def test_render_trend_present(self):
        md = render_l0_section(build_l0_environment(ACCT_MID, track="美食", track_trend="上升"))
        self.assertIn("上升", md)
        self.assertNotIn("没接到", md)

    def test_render_position(self):
        md = render_l0_section(build_l0_environment(ACCT_SMALL, track="情感"))
        self.assertIn("冷启", md)

    def test_render_hot_topics(self):
        l0 = build_l0_environment(ACCT_MID, track="美食", hot_topics=["秋天第一杯奶茶", "city不city"])
        md = render_l0_section(l0)
        self.assertIn("秋天第一杯奶茶", md)

    def test_render_empty_safe(self):
        self.assertEqual(render_l0_section(None), "")
        self.assertEqual(render_l0_section({}), "")

    def test_render_has_blackbox_honesty(self):
        md = render_l0_section(build_l0_environment(ACCT_MID, track="美食"))
        self.assertIn("黑盒", md)          # 算法权重黑盒·不作硬结论


if __name__ == "__main__":
    unittest.main(verbosity=2)

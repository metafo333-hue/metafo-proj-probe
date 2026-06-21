"""cold_start.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - route_mode: 0数据→冷启动 / 作品≥5或单条≥1000→常规 / 混合
  - cold_start_diagnose: 四支柱 + 按人群路径 + 心理干预 + 0播放解释
  - moat_score: 四维评分 + 信号不足不拍脑袋（防玄学）+ 按行业抓手
  - render_cold_start_section: 渲染 + 防玄学（0播放正常/同质化待确认）
"""
import unittest

from app.services.creator_segment import Segment
from app.services.cold_start import (
    route_mode,
    cold_start_diagnose,
    moat_score,
    render_cold_start_section,
    MOAT_HOOKS,
)


class TestRouteMode(unittest.TestCase):
    def test_zero_data_cold_start(self):
        self.assertEqual(route_mode({"works_count": 0, "max_single_views": 0}), "cold_start")

    def test_five_works_regular(self):
        # 作品≥5 → 切常规诊断
        self.assertEqual(route_mode({"works_count": 5}), "regular")

    def test_high_views_regular(self):
        # 单条曝光≥1000 → 切常规（即便作品少）
        self.assertEqual(route_mode({"works_count": 2, "max_single_views": 1500}), "regular")

    def test_under_5_low_views_cold(self):
        self.assertEqual(route_mode({"works_count": 3, "max_single_views": 200}), "cold_start")

    def test_aweme_count_fallback_key(self):
        # 容错 aweme_count 键名
        self.assertEqual(route_mode({"aweme_count": 6}), "regular")


class TestColdStartDiagnose(unittest.TestCase):
    def test_four_pillars_present(self):
        d = cold_start_diagnose(Segment.FRESH_GRAD, "知识科普")
        for key in ("track_fit", "benchmarks", "viral_teardown", "rhythm"):
            self.assertIn(key, d)
        # 对标三类齐全
        self.assertEqual(len(d["benchmarks"]), 3)
        types = {b["type"] for b in d["benchmarks"]}
        self.assertEqual(types, {"粉丝对标", "形式对标", "内容对标"})

    def test_per_segment_path_diff(self):
        # 应届 vs 中年 第一卡点不同（科学适应核心）
        fg = cold_start_diagnose(Segment.FRESH_GRAD)
        mid = cold_start_diagnose(Segment.MIDAGE_RESTART)
        self.assertNotEqual(fg["first_block"], mid["first_block"])
        # 应届第一卡点聚焦差异化/赛道；中年聚焦技能零+心理
        self.assertIn("差异化", fg["first_block"])
        self.assertIn("技能零", mid["first_block"])

    def test_psych_intervention_by_segment(self):
        mid = cold_start_diagnose(Segment.MIDAGE_RESTART)
        self.assertIn("恐惧期", mid["psych_block"])
        fg = cold_start_diagnose(Segment.FRESH_GRAD)
        self.assertIn("纠结期", fg["psych_block"])

    def test_zero_view_explain_present(self):
        # 防玄学铁律：0播放=正常，不归因内容差
        d = cold_start_diagnose(Segment.FRESH_GRAD)
        self.assertIn("正常", d["zero_view_explain"])
        self.assertIn("不是你的错", d["zero_view_explain"])

    def test_traffic_tiers_marked_volatile(self):
        # 流量层级数值必须标「随算法变·待外部验证」
        d = cold_start_diagnose(Segment.PRO_TRANSITION)
        self.assertIn("待外部验证", d["traffic_tiers"])


class TestMoatScore(unittest.TestCase):
    def test_full_metrics_scores(self):
        # 四维齐全 → 出风险分 + 等级
        m = moat_score({
            "topic_collision": 0.9,
            "template_ratio": 0.9,
            "persona_scarcity": 0.1,
            "experience_barrier": 0.1,
        }, track="餐饮", segment=Segment.MERCHANT_LOCAL)
        self.assertIsNotNone(m["risk_score"])
        self.assertEqual(m["risk_level"], "high")  # 全是高同质化信号
        self.assertFalse(m["needs_human"])

    def test_low_risk(self):
        m = moat_score({
            "topic_collision": 0.1,
            "template_ratio": 0.1,
            "persona_scarcity": 0.9,
            "experience_barrier": 0.9,
        })
        self.assertEqual(m["risk_level"], "low")

    def test_insufficient_signal_no_hard_score(self):
        # 防玄学：<3维有真值 → 不出风险分，标人工确认
        m = moat_score({"topic_collision": 0.8})
        self.assertIsNone(m["risk_score"])
        self.assertEqual(m["risk_level"], "unknown")
        self.assertTrue(m["needs_human"])
        self.assertIn("人工确认", m["note"])

    def test_none_metrics_no_score(self):
        m = moat_score(None)
        self.assertTrue(m["needs_human"])
        self.assertIsNone(m["risk_score"])

    def test_industry_hooks_matched(self):
        m = moat_score({"topic_collision": 0.5, "template_ratio": 0.5, "persona_scarcity": 0.5},
                       track="美业前后对比", segment=Segment.MERCHANT_LOCAL)
        self.assertEqual(m["industry"], "美业")
        self.assertEqual(m["hooks"], MOAT_HOOKS["美业"])

    def test_segment_guide_present(self):
        m = moat_score({"topic_collision": 0.5, "template_ratio": 0.5, "persona_scarcity": 0.5},
                       segment=Segment.MIDAGE_RESTART)
        self.assertIn("方法论", m["segment_guide"])

    def test_ai_replace_split(self):
        m = moat_score({"topic_collision": 0.5, "template_ratio": 0.5, "persona_scarcity": 0.5})
        self.assertTrue(m["ai_do"])
        self.assertTrue(m["human_do"])


class TestRender(unittest.TestCase):
    def test_render_cold_start_basics(self):
        account = {"works_count": 0, "max_single_views": 0}
        md = render_cold_start_section(account, Segment.FRESH_GRAD, target_track="知识科普")
        self.assertIn("冷启动诊断", md)
        self.assertIn("正常", md)          # 0播放安抚
        self.assertIn("对标", md)          # 四支柱
        self.assertIn("护城河", md)        # AI 护城河段

    def test_render_moat_insufficient_marks_human(self):
        # 同质化信号不足 → 暂不评级 ⚠️人工确认（防玄学）
        account = {"works_count": 0}
        md = render_cold_start_section(account, Segment.MERCHANT_LOCAL, target_track="餐饮")
        self.assertIn("⚠️人工确认", md)

    def test_render_hybrid_mode(self):
        # 混合模式提示叠加真实数据（route_mode 由 account 决定）
        account = {"works_count": 3, "max_single_views": 200}  # cold_start
        md = render_cold_start_section(account, Segment.MERCHANT_LOCAL, target_track="餐饮")
        self.assertIn("冷启动", md)

    def test_render_with_moat_metrics(self):
        account = {"works_count": 0}
        md = render_cold_start_section(
            account, Segment.MERCHANT_LOCAL, target_track="餐饮",
            moat_metrics={"topic_collision": 0.9, "template_ratio": 0.9,
                          "persona_scarcity": 0.1, "experience_barrier": 0.1})
        self.assertIn("同质化风险等级", md)
        self.assertIn("老板人格", md)  # 餐饮护城河抓手


if __name__ == "__main__":
    unittest.main()

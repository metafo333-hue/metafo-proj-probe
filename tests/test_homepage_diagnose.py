"""homepage_diagnose 主页承接力诊断 · 离线测试 · 零网络 · 零 LLM · $0。

测确定性逻辑:逐元素检测项 / 行业 must_have 断点 / 引流强×承接弱漏斗断点 /
阶段深度门(防过度诊断) / 字段缺失优雅降级(防玄学) / 合规明文导流标红 / 渲染降级。
"""
import unittest

from app.services.homepage_diagnose import (
    diagnose_homepage, detect_funnel_break, render_homepage_section,
    _stage_of, _check_bio, _check_nickname, _industry_weights,
)


class TestStageGate(unittest.TestCase):
    def test_stage_thresholds(self):
        self.assertEqual(_stage_of(0), "冷启动")
        self.assertEqual(_stage_of(499), "冷启动")
        self.assertEqual(_stage_of(500), "起号期")
        self.assertEqual(_stage_of(4999), "起号期")
        self.assertEqual(_stage_of(5000), "成长期")
        self.assertEqual(_stage_of(60000), "成熟期")

    def test_cold_start_skips_window_collection(self):
        """冷启动只查地基,不诊断橱窗/合集(防过度诊断·防早期挂橱窗污染标签)。"""
        acct = {"nickname": "张三", "signature": "我是张三", "follower": 100,
                "window_product_count": 0, "mix_count": 0}
        hp = diagnose_homepage(acct, track="带货电商", stage="冷启动")
        keys = {e["key"] for e in hp["elements"]}
        self.assertNotIn("window", keys)
        self.assertNotIn("collection", keys)
        self.assertIn("bio", keys)
        # 冷启动不给完整度评分(防早期玄学)
        self.assertIsNone(hp["completeness_score"])


class TestDeterministicChecks(unittest.TestCase):
    def test_nickname_with_geo_and_track_ok(self):
        r = _check_nickname({"nickname": "美甲师-成都"}, "时尚美妆")
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "🟩")

    def test_nickname_pure_net_name_flagged(self):
        r = _check_nickname({"nickname": "abc随便起的"}, "美食")
        self.assertFalse(r["ok"])
        self.assertIsNotNone(r["fix"])

    def test_bio_three_elements_ok(self):
        w = _industry_weights("知识科普")
        r = _check_bio({"signature": "我是10年理财老师,帮新手分享投资干货"}, "知识科普", w)
        self.assertTrue(r["ok"])
        self.assertGreaterEqual(r["n_elem"], 2)

    def test_bio_empty_flagged(self):
        w = _industry_weights("美食")
        r = _check_bio({"signature": ""}, "美食", w)
        self.assertFalse(r["ok"])
        self.assertIsNotNone(r["fix"])

    def test_bio_plaintext_wechat_compliance_red(self):
        """简介含明文微信号 → 合规标红(🟥)·断点。"""
        w = _industry_weights("美食")
        r = _check_bio({"signature": "我是卖货的,加微信12345678901"}, "美食", w)
        self.assertTrue(r["leak"])
        self.assertEqual(r["status"], "🟥")
        self.assertFalse(r["ok"])


class TestMissingFieldGraceful(unittest.TestCase):
    """防玄学:采集端没给的字段 → 标灰 missing,绝不默认值冒充检测。"""
    def test_poi_field_absent_marked_missing_not_failed(self):
        # 餐饮 must_have=poi,但账号没给 poi 字段 → 标灰,不算断点(诚实:无法判定)
        acct = {"nickname": "川味小馆-成都", "signature": "成都苍蝇馆子,招牌水煮鱼,人均50",
                "follower": 20000}
        hp = diagnose_homepage(acct, track="美食", stage="成长期")
        poi = next(e for e in hp["elements"] if e["key"] == "poi")
        self.assertTrue(poi.get("missing"))
        self.assertEqual(poi["status"], "🟨")
        self.assertIn("地址/POI", hp["missing_fields"])
        # 字段缺失不应制造主页 must_have 断点
        self.assertFalse(any(w["key"] == "poi" for w in hp["weak_points"]))

    def test_poi_field_present_but_empty_is_weak_point(self):
        # 字段给了但为空 → 这是真断点(确定性可判)
        acct = {"nickname": "川味小馆", "signature": "成都苍蝇馆子招牌水煮鱼人均50",
                "follower": 20000, "poi": ""}
        hp = diagnose_homepage(acct, track="美食", stage="成长期")
        self.assertTrue(any(w["key"] == "poi" for w in hp["weak_points"]))

    def test_blackbox_note_always_present(self):
        hp = diagnose_homepage({"nickname": "x", "signature": "我是x帮你分享", "follower": 100})
        self.assertIn("黑盒", hp["blackbox_note"])


class TestFunnelBreak(unittest.TestCase):
    """缺口核心:引流强×承接弱 → 断点判主页。"""
    def test_strong_inflow_weak_landing_break_at_homepage(self):
        account = {"follower": 1000, "avg_like": 100}
        video = {"like": 500}  # 5x avg → 爆了(引流强)
        homepage = {"weak_points": [{"element": "橱窗", "key": "window",
                                     "reason": "无橱窗", "fix": "补橱窗", "severity": "P0"}]}
        fb = detect_funnel_break(account, video, homepage)
        self.assertEqual(fb["break_at"], "主页")
        self.assertTrue(fb["strong_inflow"])
        self.assertTrue(fb["weak_landing"])
        self.assertIn("内容已出圈", fb["conclusion"])

    def test_comment_intent_words_are_strong_signal(self):
        account = {"follower": 1000, "avg_like": 100}
        video = {"like": 80, "comment_texts": ["多少钱啊", "在哪买", "怎么报名"]}
        homepage = {"weak_points": [{"element": "简介", "key": "bio",
                                     "reason": "Bio不全", "fix": "补bio"}]}
        fb = detect_funnel_break(account, video, homepage)
        self.assertEqual(fb["break_at"], "主页")
        self.assertGreaterEqual(fb["confidence"], 0.8)

    def test_weak_inflow_weak_landing_break_at_content(self):
        account = {"follower": 1000, "avg_like": 100}
        video = {"like": 90}  # 不爆
        homepage = {"weak_points": [{"element": "橱窗", "key": "window", "reason": "无橱窗"}]}
        fb = detect_funnel_break(account, video, homepage)
        self.assertEqual(fb["break_at"], "内容")

    def test_strong_inflow_strong_landing_break_at_downstream(self):
        account = {"follower": 1000, "avg_like": 100}
        video = {"like": 500}
        homepage = {"weak_points": []}
        fb = detect_funnel_break(account, video, homepage)
        self.assertEqual(fb["break_at"], "下游")

    def test_play_inflow_lower_confidence(self):
        """播放外推是黑盒,置信度应被压低(<0.7)。"""
        account = {"follower": 1000, "avg_like": 100}
        video = {"play": 10000, "like": 100}  # play/fol=10>5 但 like 不爆
        homepage = {"weak_points": [{"element": "橱窗", "key": "window", "reason": "无"}]}
        fb = detect_funnel_break(account, video, homepage)
        self.assertEqual(fb["break_at"], "主页")
        self.assertLess(fb["confidence"], 0.7)


class TestPersonaOptional(unittest.TestCase):
    def test_persona_absent_no_hard_guess(self):
        hp = diagnose_homepage({"nickname": "x", "signature": "我是x帮你分享", "follower": 1000})
        self.assertIsNone(hp["persona_goal"])

    def test_persona_present_sets_goal(self):
        hp = diagnose_homepage({"nickname": "x", "signature": "我是x", "follower": 1000},
                               persona="实体店主")
        self.assertIsNotNone(hp["persona_goal"])
        self.assertEqual(hp["persona_goal"]["goal"], "到店转化")


class TestRender(unittest.TestCase):
    def test_render_none_on_empty(self):
        self.assertIsNone(render_homepage_section(None))
        self.assertIsNone(render_homepage_section({"elements": []}))

    def test_render_contains_table_and_blackbox(self):
        hp = diagnose_homepage(
            {"nickname": "美甲-成都", "signature": "我是美甲师,帮你预约到店",
             "follower": 20000, "is_top": True, "mix_count": 2,
             "window_product_count": 0, "enterprise_verify": True, "poi": "成都春熙路"},
            works=[{"like": 5000}], track="时尚美妆", stage="成长期", persona="实体店主")
        md = render_homepage_section(hp)
        self.assertIn("逐元素体检", md)
        self.assertIn("|", md)  # 有表格
        self.assertIn("黑盒", md)  # 黑盒声明
        self.assertIn("PIPL", md)  # 头像粗判诚实声明
        self.assertIn("承接完整度", md)  # 成长期给评分

    def test_render_funnel_break_highlight(self):
        hp = diagnose_homepage(
            {"nickname": "abc", "signature": "", "follower": 1000, "avg_like": 100,
             "window_product_count": 0},
            works=[{"like": 500}], track="带货电商", stage="成长期")
        md = render_homepage_section(hp)
        self.assertIn("漏斗断点", md)


if __name__ == "__main__":
    unittest.main()

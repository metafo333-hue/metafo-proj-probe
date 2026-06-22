"""commercial.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - classify_track_value: S/A/B/C 各档 + B2B 识别
  - match_monetization_path: 主/次/禁忌路径 + 门槛判断 + R-M1/M2/M3
  - estimate_roi: 必含诚实标注 + 黑盒列表 + 路径匹配公式
  - render_commercial_section: 三层串联渲染 + 诚实铁律校验
"""
import unittest

from app.services.commercial import (
    classify_track_value,
    match_monetization_path,
    estimate_roi,
    render_commercial_section,
)

# ──────────────────────────────────────────────────────────────────────────────
# Fixture 定义
# ──────────────────────────────────────────────────────────────────────────────

# S档 · 医美B端 · 1.8万粉 · 互动率高
B2B_MEDICAL = {
    "nickname": "某医美机构官方号",
    "follower": 18000,
    "aweme_count": 80,
    "signature": "工厂直供·招商加盟·OEM贴牌",
    "avg_like": 650,
    "max_like": 2100,
    "hashtags": ["招商", "加盟", "源头工厂", "产业带"],
}

# S档 · 知识付费 · 职场/副业 · 3万粉
KNOWLEDGE_ACCOUNT = {
    "nickname": "职场副业老师",
    "follower": 30000,
    "aweme_count": 120,
    "signature": "职场干货·知识付费·教你副业赚钱",
    "avg_like": 1200,
    "max_like": 8000,
    "hashtags": ["知识付费", "职场", "副业", "考证", "干货"],
}

# A档 · 带货电商·美妆 · 6万粉
ECOM_BEAUTY = {
    "nickname": "美妆测评博主",
    "follower": 60000,
    "aweme_count": 200,
    "signature": "真实测评·好物种草·带货橱窗",
    "avg_like": 800,
    "max_like": 5000,
    "hashtags": ["美妆", "护肤", "种草", "好物", "穿搭"],
}

# B档 · 美食探店 · 2万粉
FOOD_ACCOUNT = {
    "nickname": "吃货探店达人",
    "follower": 20000,
    "aweme_count": 90,
    "signature": "美食探店·吃播菜谱·分享美味",
    "avg_like": 300,
    "max_like": 1200,
    "hashtags": ["美食", "探店", "吃播", "菜谱"],
}

# B档 · 情感/女性成长 · 8千粉 · 互动率高（关系深）
EMOTION_ACCOUNT = {
    "nickname": "情感共鸣博主",
    "follower": 8000,
    "aweme_count": 60,
    "signature": "女性情感·婚姻成长·陪伴",
    "avg_like": 400,  # 互动率=400/8000=5% → 深关系
    "max_like": 2000,
    "hashtags": ["情感", "女性", "婚姻", "陪伴", "女性成长"],
}

# C档 · 颜值才艺 · 500粉
TALENT_ACCOUNT = {
    "nickname": "才艺展示号",
    "follower": 500,
    "aweme_count": 15,
    "signature": "颜值日常·舞蹈才艺·搞笑短视频",
    "avg_like": 3,
    "max_like": 20,
    "hashtags": ["颜值", "才艺", "舞蹈", "搞笑", "泛娱乐"],
}

# 小粉丝 · 未达门槛
TINY_ACCOUNT = {
    "nickname": "新手博主",
    "follower": 200,
    "aweme_count": 5,
    "signature": "知识分享·职场干货",
    "avg_like": 8,
    "max_like": 30,
    "hashtags": ["知识", "职场", "干货"],
}


# ──────────────────────────────────────────────────────────────────────────────
# classify_track_value 测试
# ──────────────────────────────────────────────────────────────────────────────

class TestClassifyTrackValue(unittest.TestCase):

    def test_b2b_is_s_grade(self):
        """B2B/产业带货/招商加盟 → S档"""
        r = classify_track_value(B2B_MEDICAL)
        self.assertEqual(r["grade"], "S", f"B2B号应为S档，got: {r['grade']}")

    def test_knowledge_is_s_grade(self):
        """知识付费/职场/副业 → S档"""
        r = classify_track_value(KNOWLEDGE_ACCOUNT)
        self.assertEqual(r["grade"], "S", f"知识付费号应为S档，got: {r['grade']}")

    def test_ecom_beauty_is_a_grade(self):
        """美妆带货/种草 → A档"""
        r = classify_track_value(ECOM_BEAUTY)
        self.assertEqual(r["grade"], "A", f"美妆带货号应为A档，got: {r['grade']}")

    def test_food_is_b_grade(self):
        """美食探店 → B档"""
        r = classify_track_value(FOOD_ACCOUNT)
        self.assertEqual(r["grade"], "B", f"美食探店号应为B档，got: {r['grade']}")

    def test_talent_is_c_grade(self):
        """颜值才艺/泛娱乐 → C档"""
        r = classify_track_value(TALENT_ACCOUNT)
        self.assertEqual(r["grade"], "C", f"颜值才艺号应为C档，got: {r['grade']}")

    def test_calibration_note_always_present(self):
        """诚实铁律：必须有"需校准"标注"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY, FOOD_ACCOUNT, TALENT_ACCOUNT]:
            r = classify_track_value(acc)
            self.assertIn("需校准", r["calibration_note"],
                          f"{acc['nickname']} 缺少'需校准'标注")

    def test_fan_unit_value_is_range_not_point(self):
        """单粉价值必须是区间描述，不是精确点值"""
        r = classify_track_value(KNOWLEDGE_ACCOUNT)
        # 区间描述包含"–"或"—"
        self.assertTrue("–" in r["fan_unit_value"] or "—" in r["fan_unit_value"] or
                        "至" in r["fan_unit_value"] or "到" in r["fan_unit_value"],
                        f"单粉价值应为区间，got: {r['fan_unit_value']}")

    def test_roi_stars_format(self):
        """投产比用★表示，S档最高"""
        s_r = classify_track_value(B2B_MEDICAL)
        c_r = classify_track_value(TALENT_ACCOUNT)
        self.assertGreater(
            s_r["roi_stars"].count("★"),
            c_r["roi_stars"].count("★"),
            "S档★数应多于C档"
        )

    def test_returns_track_name(self):
        """必须返回 track_name"""
        r = classify_track_value(ECOM_BEAUTY)
        self.assertIn("track_name", r)
        self.assertTrue(len(r["track_name"]) > 0)


# ──────────────────────────────────────────────────────────────────────────────
# match_monetization_path 测试
# ──────────────────────────────────────────────────────────────────────────────

class TestMatchMonetizationPath(unittest.TestCase):

    def _get_path(self, account):
        tv = classify_track_value(account)
        return match_monetization_path(account, tv)

    def test_knowledge_account_primary_is_knowledge_pay(self):
        """S档知识付费账号 → 主路径=知识付费"""
        p = self._get_path(KNOWLEDGE_ACCOUNT)
        self.assertEqual(p["primary"], "知识付费",
                         f"知识付费号主路径应为知识付费，got: {p['primary']}")

    def test_b2b_primary_is_private_domain(self):
        """B2B/产业带货 → 主路径=私域变现"""
        p = self._get_path(B2B_MEDICAL)
        self.assertEqual(p["primary"], "私域变现",
                         f"B2B号主路径应为私域变现，got: {p['primary']}")

    def test_ecom_beauty_primary_is_affiliate(self):
        """A档评测/种草 → 主路径=带货佣金"""
        p = self._get_path(ECOM_BEAUTY)
        self.assertEqual(p["primary"], "带货佣金",
                         f"美妆带货号主路径应为带货佣金，got: {p['primary']}")

    def test_talent_c_grade_primary_is_livestream(self):
        """C档颜值才艺 → 主路径=直播打赏"""
        p = self._get_path(TALENT_ACCOUNT)
        self.assertEqual(p["primary"], "直播打赏",
                         f"颜值才艺号主路径应为直播打赏，got: {p['primary']}")

    def test_forbidden_path_present(self):
        """必须有禁忌路径且有理由"""
        for acc in [KNOWLEDGE_ACCOUNT, B2B_MEDICAL, ECOM_BEAUTY, TALENT_ACCOUNT]:
            p = self._get_path(acc)
            self.assertIn("forbidden", p, f"{acc['nickname']} 缺少禁忌路径")
            self.assertIn("forbidden_reason", p)
            self.assertTrue(len(p["forbidden_reason"]) > 5)

    def test_threshold_met_for_large_account(self):
        """6万粉美妆号带货门槛(1000粉)已达"""
        p = self._get_path(ECOM_BEAUTY)
        if p["primary"] == "带货佣金":
            self.assertTrue(p["threshold_met"],
                            "6万粉带货佣金门槛应已达")

    def test_threshold_not_met_for_tiny_account_ad(self):
        """200粉新手如主路径需5万粉广告·则未达"""
        p = self._get_path(TINY_ACCOUNT)
        # 如果主路径是广告合作，应未达门槛
        if p["primary"] == "广告合作":
            self.assertFalse(p["threshold_met"],
                             "200粉广告合作门槛不应达到")

    def test_deep_relationship_triggers_private_domain(self):
        """互动率高（情感号5%）→ 关系深 → 次路径含私域"""
        p = self._get_path(EMOTION_ACCOUNT)
        self.assertEqual(p["relationship_depth"], "深",
                         f"互动率5%应判断为'深'关系，got: {p['relationship_depth']}")
        # 次路径应为私域（深关系修正逻辑）
        has_private = (p["secondary"] == "私域变现" or p["primary"] == "私域变现")
        self.assertTrue(has_private, "深关系账号应有私域变现路径")

    def test_content_type_education_for_knowledge(self):
        """知识/干货内容 → R-M2=教"""
        p = self._get_path(KNOWLEDGE_ACCOUNT)
        self.assertEqual(p["content_type"], "教",
                         f"知识付费号内容类型应为'教'，got: {p['content_type']}")

    def test_threshold_note_always_present(self):
        """门槛说明必须存在"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY, TALENT_ACCOUNT, TINY_ACCOUNT]:
            p = self._get_path(acc)
            self.assertIn("threshold_note", p)
            self.assertTrue(len(p["threshold_note"]) > 0, f"{acc['nickname']} 门槛说明为空")

    def test_primary_secondary_different(self):
        """主路径和次路径不能相同"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY, FOOD_ACCOUNT, TALENT_ACCOUNT]:
            p = self._get_path(acc)
            self.assertNotEqual(p["primary"], p["secondary"],
                                f"{acc['nickname']} 主次路径相同")


# ──────────────────────────────────────────────────────────────────────────────
# estimate_roi 测试
# ──────────────────────────────────────────────────────────────────────────────

class TestEstimateRoi(unittest.TestCase):

    def _get_roi(self, account):
        tv = classify_track_value(account)
        path = match_monetization_path(account, tv)
        path["_grade"] = tv["grade"]
        return estimate_roi(account, path)

    def test_calibration_note_always_present(self):
        """诚实铁律：必须有"需真实数据校准"标注"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY, FOOD_ACCOUNT, TALENT_ACCOUNT]:
            roi = self._get_roi(acc)
            self.assertIn("校准", roi["calibration_note"],
                          f"{acc['nickname']} ROI缺少'校准'标注")
            self.assertIn("经验区间", roi["calibration_note"],
                          f"{acc['nickname']} ROI缺少'经验区间'标注")

    def test_black_box_gaps_always_present(self):
        """黑盒列表必须存在且非空"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY]:
            roi = self._get_roi(acc)
            self.assertIn("black_box_gaps", roi)
            self.assertGreater(len(roi["black_box_gaps"]), 0,
                               f"{acc['nickname']} 黑盒缺口列表为空")

    def test_roi_formula_mentions_path(self):
        """月产出公式应与当前路径相关"""
        # 知识付费路径 → 公式提到粉丝/付费率
        tv = classify_track_value(KNOWLEDGE_ACCOUNT)
        path = match_monetization_path(KNOWLEDGE_ACCOUNT, tv)
        path["_grade"] = tv["grade"]
        roi = estimate_roi(KNOWLEDGE_ACCOUNT, path)
        if path["primary"] == "知识付费":
            self.assertIn("付费率", roi["monthly_output_formula"])

    def test_ltv_cac_mentioned(self):
        """必须提到 LTV/CAC"""
        roi = self._get_roi(KNOWLEDGE_ACCOUNT)
        self.assertIn("LTV", roi["ltv_cac_range"] + roi["calibration_note"])

    def test_health_threshold_present(self):
        """必须有健康判据（LTV/CAC>3）"""
        roi = self._get_roi(ECOM_BEAUTY)
        self.assertIn("health_threshold", roi)
        self.assertIn("3", roi["health_threshold"])

    def test_no_exact_guarantee_wording(self):
        """禁止使用"保证"/"精确"/"一定"等承诺性词语"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY, FOOD_ACCOUNT]:
            roi = self._get_roi(acc)
            full_text = roi["monthly_output_formula"] + roi["payback_months"] + roi["calibration_note"]
            for bad_word in ["保证", "一定赚", "必然", "精确预测"]:
                self.assertNotIn(bad_word, full_text,
                                 f"{acc['nickname']} ROI含有承诺性词语: {bad_word}")


# ──────────────────────────────────────────────────────────────────────────────
# render_commercial_section 测试
# ──────────────────────────────────────────────────────────────────────────────

class TestRenderCommercialSection(unittest.TestCase):

    def test_three_layers_present(self):
        """三层标题必须都存在"""
        md = render_commercial_section(KNOWLEDGE_ACCOUNT)
        for section in ["层A", "层B", "层C"]:
            self.assertIn(section, md, f"商业诊断段缺少{section}")

    def test_honest_disclaimer_in_render(self):
        """诚实免责声明必须出现在渲染结果中"""
        md = render_commercial_section(ECOM_BEAUTY)
        self.assertIn("经验区间", md, "渲染段缺少'经验区间'诚实标注")
        self.assertIn("校准", md, "渲染段缺少'校准'诚实标注")

    def test_blackbox_guidance_in_render(self):
        """黑盒引导（传后台截图）必须出现"""
        md = render_commercial_section(FOOD_ACCOUNT)
        self.assertIn("黑盒", md, "渲染段缺少黑盒诚实标")

    def test_forbidden_path_in_render(self):
        """禁忌路径必须在渲染结果中明示"""
        md = render_commercial_section(KNOWLEDGE_ACCOUNT)
        self.assertIn("禁忌路径", md, "渲染段缺少禁忌路径")

    def test_transition_discipline_in_render(self):
        """过渡设计三段式纪律必须出现"""
        md = render_commercial_section(B2B_MEDICAL)
        self.assertIn("信任铺垫", md, "渲染段缺少信任铺垫期说明")

    def test_b2b_renders_private_domain(self):
        """B2B号渲染段提到私域变现"""
        md = render_commercial_section(B2B_MEDICAL)
        self.assertIn("私域", md, "B2B号渲染段应提到私域变现")

    def test_talent_c_grade_warns_low_roi(self):
        """C档号渲染段有低投产比警示"""
        md = render_commercial_section(TALENT_ACCOUNT)
        self.assertIn("C档", md, "C档渲染段应有档位标注")

    def test_track_value_passthrough(self):
        """track_value 可以外部传入（不重复计算）"""
        tv = classify_track_value(ECOM_BEAUTY)
        md_with_tv = render_commercial_section(ECOM_BEAUTY, track_value=tv)
        md_without = render_commercial_section(ECOM_BEAUTY)
        # 两者应产生相同的结果（同一账号同一输入）
        self.assertEqual(md_with_tv, md_without,
                         "传入track_value和内部计算应给出相同结果")

    def test_output_is_markdown(self):
        """输出是 Markdown 字符串"""
        md = render_commercial_section(KNOWLEDGE_ACCOUNT)
        self.assertIsInstance(md, str)
        self.assertIn("##", md, "输出应包含Markdown标题")
        self.assertIn("-", md, "输出应包含Markdown列表")

    def test_no_technical_field_names_in_render(self):
        """渲染结果不暴露内部字段名（说人话）"""
        md = render_commercial_section(KNOWLEDGE_ACCOUNT)
        for bad in ["vertical_score", "burst_ratio", "avg_like", "aweme_count"]:
            self.assertNotIn(bad, md, f"渲染段不应出现技术字段名: {bad}")


# ──────────────────────────────────────────────────────────────────────────────
# 边界与健壮性测试
# ──────────────────────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):

    def test_zero_follower_account(self):
        """零粉丝账号不崩溃"""
        acc = {
            "nickname": "刚注册",
            "follower": 0,
            "aweme_count": 0,
            "signature": "分享生活",
            "avg_like": 0,
            "max_like": 0,
            "hashtags": [],
        }
        r = classify_track_value(acc)
        self.assertIn("grade", r)
        p = match_monetization_path(acc, r)
        self.assertIn("primary", p)
        roi = estimate_roi(acc, {**p, "_grade": r["grade"]})
        self.assertIn("calibration_note", roi)

    def test_empty_signature_account(self):
        """无简介无标签账号不崩溃"""
        acc = {
            "nickname": "某某",
            "follower": 5000,
            "aweme_count": 30,
            "signature": "",
            "avg_like": 50,
            "max_like": 200,
            "hashtags": [],
        }
        md = render_commercial_section(acc)
        self.assertIsInstance(md, str)
        self.assertIn("层A", md)

    def test_very_large_follower_account(self):
        """千万粉大号不崩溃"""
        acc = {
            "nickname": "顶流明星",
            "follower": 10_000_000,
            "aweme_count": 500,
            "signature": "颜值才艺·娱乐搞笑",
            "avg_like": 50000,
            "max_like": 5_000_000,
            "hashtags": ["颜值", "才艺", "搞笑"],
        }
        r = classify_track_value(acc)
        self.assertIn("grade", r)
        p = match_monetization_path(acc, r)
        self.assertIn("threshold_met", p)

    def test_render_all_fixture_types(self):
        """所有 fixture 都能正常渲染（不报错）"""
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY,
                    FOOD_ACCOUNT, EMOTION_ACCOUNT, TALENT_ACCOUNT, TINY_ACCOUNT]:
            try:
                md = render_commercial_section(acc)
                self.assertIsInstance(md, str)
                self.assertGreater(len(md), 100, f"{acc['nickname']} 渲染结果太短")
            except Exception as e:
                self.fail(f"{acc['nickname']} 渲染失败: {e}")

    def test_each_grade_represented(self):
        """S/A/B/C 四个档都能被正确输出"""
        grades = set()
        for acc in [B2B_MEDICAL, KNOWLEDGE_ACCOUNT, ECOM_BEAUTY,
                    FOOD_ACCOUNT, EMOTION_ACCOUNT, TALENT_ACCOUNT]:
            r = classify_track_value(acc)
            grades.add(r["grade"])
        self.assertIn("S", grades, "S档未被任何fixture命中")
        self.assertIn("A", grades, "A档未被任何fixture命中")
        self.assertIn("B", grades, "B档未被任何fixture命中")
        self.assertIn("C", grades, "C档未被任何fixture命中")


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""action_planner.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - plan_actions: 诊断码→行动项映射 + 三因子打分排序正确性
  - 合规硬置顶（hard_top 永远第一·覆盖打分）
  - 阶段红线（forbid kind → 别做清单·不参与排序）
  - 强制 max_actions 截断（人群差异 2 vs 3）
  - 行业门控（POI 仅到店类触发）
  - 无映射码 → 不生成（防 LLM 自由发挥）
  - render_action_section: 防玄学注脚 + 完成标准 + 空输入优雅降级
"""
import unittest

from app.services.action_planner import (
    plan_actions,
    render_action_section,
    _score,
    _DIAGNOSIS_TO_ACTION,
)

# 餐饮号（到店类·POI 门控会放行）
RESTAURANT = {
    "nickname": "巷子口小馆",
    "follower": 8000,
    "signature": "本地探店·美食推荐",
    "avg_like": 300,
    "max_like": 900,
    "hashtags": ["美食", "探店"],
}

# 知识号（非到店·POI 门控会拦截）
KNOWLEDGE = {
    "nickname": "副业老师",
    "follower": 30000,
    "signature": "职场知识·副业成长",
    "avg_like": 1200,
    "max_like": 8000,
    "hashtags": ["知识", "成长"],
}


class TestScore(unittest.TestCase):
    def test_high_roi_low_difficulty_wins(self):
        """难度做分母：高 ROI 低难度的快赢分数更高。"""
        easy_win = _score(roi=4, difficulty=1, urgency=3)
        hard = _score(roi=4, difficulty=5, urgency=3)
        self.assertGreater(easy_win, hard)

    def test_no_divide_by_zero(self):
        self.assertGreater(_score(roi=3, difficulty=0, urgency=3), 0)


class TestPlanActions(unittest.TestCase):
    def test_diagnosis_maps_to_action(self):
        """有映射码 → 生成行动项；填占位符。"""
        plan = plan_actions(
            [{"code": "homepage_bio_incomplete",
              "params": {"who": "宝妈", "whom": "新手妈妈", "what": "省心带娃法"}}],
            stage="起号期", persona="应届生",
        )
        self.assertEqual(len(plan["top_actions"]), 1)
        txt = plan["top_actions"][0]["text"]
        self.assertIn("宝妈", txt)
        self.assertIn("新手妈妈", txt)

    def test_unmapped_code_skipped(self):
        """无映射码 → 不生成（防凭空 LLM 生成）。"""
        plan = plan_actions([{"code": "no_such_diagnosis_code"}], stage="成长期")
        self.assertEqual(len(plan["top_actions"]), 0)
        self.assertEqual(len(plan["dont_do"]), 0)

    def test_compliance_hard_top(self):
        """合规标红项无论 P 多少都置顶第一（封号=转化归零）。"""
        diagnoses = [
            {"code": "topic_drought"},          # ROI3 难4 紧2·低分
            {"code": "homepage_bio_incomplete"},# ROI4 难1 紧3·高分
            {"code": "compliance_hit", "params": {"bad_term": "最好", "good_term": "口碑不错"}},
        ]
        plan = plan_actions(diagnoses, stage="成长期", persona="应届生")
        first = plan["top_actions"][0]
        self.assertEqual(first["code"], "compliance_hit")
        self.assertTrue(first["hard_top"])

    def test_sort_by_score_when_no_hard_top(self):
        """无硬置顶、无阶段偏好时：按 P 降序（快赢冒头）。
        用成熟期（prefer=convert/private_domain），下面两项 kind 都不在 prefer 内，纯比 P。"""
        diagnoses = [
            {"code": "topic_drought"},           # volume·难4·低 P
            {"code": "homepage_bio_incomplete"}, # positioning·难1·高 P
        ]
        plan = plan_actions(diagnoses, stage="成熟期", persona="应届生")
        ps = [a["P"] for a in plan["top_actions"]]
        self.assertEqual(ps, sorted(ps, reverse=True))
        self.assertEqual(plan["top_actions"][0]["code"], "homepage_bio_incomplete")

    def test_stage_forbid_moves_to_dont_do(self):
        """冷启动阶段：monetize/volume/convert 类 → 别做清单·不进 top。"""
        diagnoses = [
            {"code": "homepage_bio_incomplete"},  # positioning·允许
            {"code": "topic_drought"},            # volume·冷启动 forbid
        ]
        plan = plan_actions(diagnoses, stage="冷启动", persona="应届生")
        top_codes = [a["code"] for a in plan["top_actions"]]
        self.assertIn("homepage_bio_incomplete", top_codes)
        self.assertNotIn("topic_drought", top_codes)
        self.assertEqual(len(plan["dont_do"]), 1)

    def test_compliance_survives_stage_forbid(self):
        """硬置顶合规项不被阶段红线移除（hard_top 豁免 forbid）。"""
        diagnoses = [
            {"code": "compliance_hit", "params": {"bad_term": "保过", "good_term": "认真教"}},
        ]
        plan = plan_actions(diagnoses, stage="冷启动", persona="应届生")
        self.assertEqual(len(plan["top_actions"]), 1)
        self.assertEqual(plan["top_actions"][0]["code"], "compliance_hit")

    def test_max_actions_truncation_persona(self):
        """人群差异：中年失业 max=2，应届生 max=3·强制截断。"""
        codes = [{"code": c} for c in
                 ["homepage_bio_incomplete", "homepage_pin_wrong",
                  "tag_drift", "private_domain_missing"]]
        plan_youth = plan_actions(codes, stage="成长期", persona="应届生")
        plan_mid = plan_actions(codes, stage="成长期", persona="中年失业")
        self.assertEqual(len(plan_youth["top_actions"]), 3)
        self.assertEqual(len(plan_mid["top_actions"]), 2)
        # 被截断的进 backlog
        self.assertGreater(len(plan_mid["backlog"]), 0)

    def test_industry_gate_poi(self):
        """POI 门控：餐饮号放行·知识号拦截。"""
        diag = [{"code": "homepage_no_poi"}]
        plan_rest = plan_actions(diag, account=RESTAURANT, stage="成熟期", persona="实体店主")
        plan_know = plan_actions(diag, account=KNOWLEDGE, stage="成熟期", persona="应届生")
        self.assertEqual(len(plan_rest["top_actions"]), 1)
        self.assertEqual(len(plan_know["top_actions"]), 0)

    def test_capability_team_lowers_difficulty(self):
        """团队号拍视频难度降·P 升。"""
        diag = [{"code": "topic_drought"}]
        solo = plan_actions(diag, stage="成长期", persona="应届生", capability={"team": False})
        team = plan_actions(diag, stage="成长期", persona="应届生", capability={"team": True})
        self.assertGreater(team["top_actions"][0]["P"], solo["top_actions"][0]["P"])

    def test_empty_input_graceful(self):
        plan = plan_actions(None)
        self.assertEqual(plan["top_actions"], [])
        self.assertEqual(plan["dont_do"], [])
        self.assertEqual(plan["backlog"], [])

    def test_missing_params_graceful(self):
        """占位符缺失 → 不崩·给可读占位。"""
        plan = plan_actions([{"code": "homepage_bio_incomplete"}], stage="起号期", persona="应届生")
        self.assertEqual(len(plan["top_actions"]), 1)
        self.assertIn("简介", plan["top_actions"][0]["text"])


class TestRenderActionSection(unittest.TestCase):
    def test_render_has_anti_mysticism_note(self):
        """防玄学：渲染含权重经验值标注 + 每项打分拆解。"""
        plan = plan_actions(
            [{"code": "homepage_bio_incomplete"}, {"code": "homepage_pin_wrong"}],
            stage="成长期", persona="应届生",
        )
        md = render_action_section(plan)
        self.assertIn("经验值", md)
        self.assertIn("需校准", md)
        # 每项打分拆解（可解释·防玄学评分）
        self.assertIn("为什么排这个位置", md)
        self.assertIn("ROI", md)
        # 完成标准存在
        self.assertIn("怎么算做完", md)

    def test_render_done_standard_type_marked(self):
        """完成标准区分结构类🟩 / 效果类🟥。"""
        plan = plan_actions(
            [{"code": "homepage_bio_incomplete"},      # structural
             {"code": "funnel_break_completion"}],     # blackbox
            stage="起号期", persona="应届生",
        )
        md = render_action_section(plan)
        self.assertIn("🟩可自动复检", md)
        self.assertIn("🟥需投喂后台数据", md)

    def test_render_dont_do_section(self):
        plan = plan_actions(
            [{"code": "homepage_bio_incomplete"}, {"code": "topic_drought"}],
            stage="冷启动", persona="应届生",
        )
        md = render_action_section(plan)
        self.assertIn("先别做", md)

    def test_render_empty_graceful(self):
        """空输入 → 友好降级·不崩·不报错。"""
        md = render_action_section(plan_actions(None))
        self.assertIn("没有识别到", md)
        self.assertTrue(md.startswith("## 🎯"))

    def test_render_compliance_marked(self):
        plan = plan_actions(
            [{"code": "compliance_hit", "params": {"bad_term": "包过", "good_term": "认真教"}}],
            stage="成长期", persona="应届生",
        )
        md = render_action_section(plan)
        self.assertIn("合规", md)


if __name__ == "__main__":
    unittest.main()

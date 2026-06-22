"""creator_segment.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - classify_segment: 6 类 segment 识别 + UNKNOWN 信号不足不硬猜
  - build_capability_profile: 五维采集 + 未提供留 None（不臆测）
  - feasibility_filter: 能力够 → 保留 / 够不着 → 降级 / 未采集 → 标待确认
  - _infer_stage / adapt_focus: 阶段推断 + 人群×阶段三轴适配
  - render_segment_section: 渲染 + 防玄学（置信度<0.6 标人工确认）
"""
import unittest

from app.services.creator_segment import (
    Segment,
    Stage,
    CapabilityProfile,
    classify_segment,
    build_capability_profile,
    feasibility_filter,
    adapt_focus,
    render_segment_section,
    _infer_stage,
)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

MERCHANT = {
    "nickname": "城南老火锅",
    "blue_v": True,
    "poi_bound": True,
    "follower": 3000,
    "aweme_count": 40,
    "signature": "城南老字号火锅·到店团购",
}

MCN = {
    "nickname": "XX传媒矩阵",
    "bound_accounts": 8,
    "follower": 200000,
    "aweme_count": 300,
}

FRESH_GRAD = {
    "nickname": "刚毕业的小李",
    "employ_status": "fresh_grad",
    "follower": 12,
    "works_count": 0,
}

MIDAGE = {
    "nickname": "老张说财务",
    "age_band": "35_50",
    "employ_status": "unemployed",
    "follower": 30,
    "works_count": 1,
    "signature": "20年财务经验·失业再就业",
}

PRO_TRANSITION = {
    "nickname": "上班族副业",
    "employ_status": "in_job",
    "follower": 2000,
    "aweme_count": 15,
    "signature": "下班搞副业",
}

KNOWLEDGE_IP = {
    "nickname": "法务老王",
    "employ_status": "in_job",
    "follower": 8000,
    "aweme_count": 60,
    "signature": "口播法务干货·职场避坑方法论",
    "hashtags": ["法务", "干货", "方法论"],
}

# 信号不足：只有昵称，无任何身份信号
SPARSE = {
    "nickname": "随便起的号",
    "follower": 100,
}


class TestClassifySegment(unittest.TestCase):
    def test_merchant_local(self):
        r = classify_segment(MERCHANT)
        self.assertEqual(r.segment, Segment.MERCHANT_LOCAL)
        self.assertGreaterEqual(r.confidence, 0.6)
        self.assertTrue(r.evidence)
        self.assertFalse(r.needs_human)

    def test_mcn_matrix(self):
        r = classify_segment(MCN)
        self.assertEqual(r.segment, Segment.MCN_MATRIX)
        self.assertGreaterEqual(r.confidence, 0.6)
        # MCN 门槛应带「随平台规则变」防玄学标注
        self.assertTrue(any("待复核" in e or "门槛" in e for e in r.evidence))

    def test_fresh_grad(self):
        r = classify_segment(FRESH_GRAD)
        self.assertEqual(r.segment, Segment.FRESH_GRAD)
        self.assertEqual(r.stage, Stage.COLD_START)

    def test_midage_restart(self):
        r = classify_segment(MIDAGE)
        self.assertEqual(r.segment, Segment.MIDAGE_RESTART)

    def test_pro_transition(self):
        r = classify_segment(PRO_TRANSITION)
        self.assertEqual(r.segment, Segment.PRO_TRANSITION)

    def test_knowledge_ip(self):
        # 在职 + 口播/方法论信号 → knowledge_ip，次身份在职转型
        r = classify_segment(KNOWLEDGE_IP)
        self.assertEqual(r.segment, Segment.KNOWLEDGE_IP)
        self.assertEqual(r.secondary, Segment.PRO_TRANSITION)

    def test_unknown_no_hard_guess(self):
        # 防玄学核心：信号不足 → UNKNOWN，不硬猜，needs_human=True
        r = classify_segment(SPARSE)
        self.assertEqual(r.segment, Segment.UNKNOWN)
        self.assertEqual(r.confidence, 0.0)
        self.assertTrue(r.needs_human)
        self.assertTrue(r.evidence)  # 仍给出「为什么判不了」的依据


class TestInferStage(unittest.TestCase):
    def test_cold_start_zero_data(self):
        self.assertEqual(_infer_stage({"works_count": 0}), Stage.COLD_START)

    def test_seeding_under_5(self):
        self.assertEqual(
            _infer_stage({"works_count": 3, "max_single_views": 200}), Stage.SEEDING)

    def test_regular_by_views(self):
        # 单条曝光破 1000 → 不再冷启动（至少起号期）
        s = _infer_stage({"works_count": 2, "max_single_views": 5000})
        self.assertNotEqual(s, Stage.COLD_START)

    def test_growth_and_mature(self):
        self.assertEqual(_infer_stage({"works_count": 50, "follower": 8000}), Stage.GROWTH)
        self.assertEqual(_infer_stage({"works_count": 50, "follower": 80000}), Stage.MATURE)


class TestCapabilityProfile(unittest.TestCase):
    def test_collect_known_dims(self):
        cap = build_capability_profile({
            "on_camera": "unwilling",
            "editing": "none",
            "time_budget": "fragment",
        })
        self.assertEqual(cap.on_camera, "unwilling")
        self.assertEqual(cap.editing, "none")
        # 未提供的维度留 None（不臆测）
        self.assertIsNone(cap.budget)
        self.assertIsNone(cap.team)
        self.assertEqual(cap.known_dims(), 3)

    def test_invalid_value_dropped(self):
        # 非法取值不接受 → None（防脏数据当结论）
        cap = build_capability_profile({"editing": "超神"})
        self.assertIsNone(cap.editing)

    def test_nested_capability_key(self):
        cap = build_capability_profile({"capability": {"team": "couple"}})
        self.assertEqual(cap.team, "couple")


class TestFeasibilityFilter(unittest.TestCase):
    def test_capable_keeps_action(self):
        cap = CapabilityProfile(editing="pro", time_budget="ample")
        out = feasibility_filter([{"kind": "complex_montage", "title": "复杂分镜"}], cap)
        self.assertEqual(out[0]["kind"], "complex_montage")
        self.assertNotIn("note", out[0])

    def test_downgrade_when_incapable(self):
        # 不会剪 + 不愿出镜 → 复杂分镜降级（铁律：方案难度≤能力天花板）
        cap = CapabilityProfile(editing="none", on_camera="unwilling", time_budget="fragment")
        out = feasibility_filter([{"kind": "complex_montage", "title": "复杂分镜"}], cap)
        self.assertNotEqual(out[0]["kind"], "complex_montage")
        self.assertIn("降级", out[0]["note"])

    def test_voice_over_downgrades_to_image_text_when_unwilling(self):
        cap = CapabilityProfile(on_camera="unwilling", editing="none")
        out = feasibility_filter([{"kind": "voice_over", "title": "口播"}], cap)
        self.assertEqual(out[0]["kind"], "image_text")

    def test_undetermined_marks_pending(self):
        # 能力未采集 → 不硬过也不硬降，标⚠️待确认（防玄学）
        cap = CapabilityProfile()  # 全 None
        out = feasibility_filter([{"kind": "complex_montage", "title": "复杂分镜"}], cap)
        self.assertEqual(out[0]["kind"], "complex_montage")
        self.assertIn("待确认", out[0]["note"])


class TestAdaptFocus(unittest.TestCase):
    def test_merchant_cold_start_low_freq(self):
        # 实体店冷启动应给「1-2 条/周」而非「5-7」（科学适应核心·防一刀切）
        a = adapt_focus(Segment.MERCHANT_LOCAL, Stage.COLD_START)
        self.assertIn("1-2 条", a["freq"])
        self.assertIn("经验", a["freq"])  # 阈值带🟨经验标注

    def test_fresh_grad_cold_start_no_freq(self):
        a = adapt_focus(Segment.FRESH_GRAD, Stage.COLD_START)
        self.assertIn("先定位", a["freq"])

    def test_unknown_prompts_signal(self):
        a = adapt_focus(Segment.UNKNOWN, Stage.COLD_START)
        self.assertIn("信号", a["focus"])

    def test_fallback_for_knowledge_ip(self):
        # knowledge_ip 无逐阶段细表 → 落 segment 级缺省，仍有诊断重点
        a = adapt_focus(Segment.KNOWLEDGE_IP, Stage.GROWTH)
        self.assertTrue(a["focus"])
        self.assertTrue(a["form"])


class TestRender(unittest.TestCase):
    def test_render_known_segment(self):
        md = render_segment_section(MERCHANT)
        self.assertIn("本地商家号", md)
        self.assertIn("怎么判断的", md)  # 带可证伪依据
        self.assertIn("到店", md)

    def test_render_unknown_flags_human(self):
        # 防玄学：UNKNOWN 必须标人工确认，不硬给身份
        md = render_segment_section(SPARSE)
        self.assertIn("⚠️人工确认", md)
        self.assertIn("不硬猜", md)

    def test_render_with_feasibility_downgrade(self):
        signals = dict(MIDAGE)
        signals.update({"on_camera": "unwilling", "editing": "none", "time_budget": "fragment"})
        actions = [{"kind": "complex_montage", "title": "复杂分镜脚本"}]
        md = render_segment_section(signals, actions=actions)
        self.assertIn("降级", md)

    def test_render_low_confidence_marks_human(self):
        # 弱判定（knowledge_ip 无人生处境信号·置信 0.55）→ 标人工确认
        weak = {"signature": "口播方法论干货", "hashtags": ["方法论", "干货"], "follower": 500}
        r = classify_segment(weak)
        self.assertLess(r.confidence, 0.6)
        md = render_segment_section(weak, result=r)
        self.assertIn("⚠️人工确认", md)


if __name__ == "__main__":
    unittest.main()

"""精准转化方案测试 · 离线 · 确定性 · 零 LLM · 零网络。

覆盖:
  diagnose_transition_stage  — 三阶段正确分类 / 互动深度判断 / R-C5红线出现
  suggest_hooks              — 三钩结构完整 / 视听六层有/无两路 / 置信度低不冒用
  diagnose_funnel            — 第一卡点优先找法 / 完播黑盒诚实标 / 各层触发
  render_conversion_section  — Markdown段结构完整 / 说人话 / 铁律出现

Fixture 对照:
  SMALL  — 小号(100粉·发8条·低互动) → 信任铺垫期·漏斗卡完播代理
  MID    — 中号(8000粉·发60条·中互动) → 软植入期
  BIG    — 大号(80000粉·发200条·深互动) → 显性转化期
  VIDEO_COLD  — 冷门视频(点赞5·无评论) → 完播代理卡点
  VIDEO_WARM  — 热门视频(点赞1000·评论50·收藏80) → 较好信号
  SIX_HIGH    — 视听六层高置信度(>0.5) → 口播证据钩
  SIX_LOW     — 视听六层低置信度(<0.5) → 不冒用·标ceiling
"""
import unittest

from app.services.conversion import (
    diagnose_transition_stage,
    suggest_hooks,
    diagnose_funnel,
    render_conversion_section,
    _interaction_depth,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

SMALL_A = {
    "nickname": "小芊", "follower": 100, "aweme_count": 8,
    "avg_like": 5, "max_like": 20, "vertical_score": 0.4,
    "signature": "分享生活",
}

MID_A = {
    "nickname": "魔芋姐", "follower": 8_000, "aweme_count": 60,
    "avg_like": 100, "max_like": 400, "vertical_score": 0.75,
    "signature": "源头工厂·餐饮直供",
}

BIG_A = {
    "nickname": "职场教练", "follower": 80_000, "aweme_count": 200,
    "avg_like": 2000, "max_like": 15_000, "vertical_score": 0.85,
    "signature": "帮你做好职业规划",
}

# works样本：用于互动深度计算
MID_WORKS = [
    {"like": 120, "comment": 8, "collect": 15, "share": 3},
    {"like": 90,  "comment": 5, "collect": 12, "share": 1},
    {"like": 80,  "comment": 3, "collect": 8,  "share": 0},
    {"like": 100, "comment": 6, "collect": 10, "share": 2},
]

BIG_WORKS = [
    {"like": 2000, "comment": 120, "collect": 250, "share": 50},
    {"like": 1800, "comment": 90,  "collect": 200, "share": 40},
    {"like": 2200, "comment": 130, "collect": 280, "share": 55},
]

VIDEO_COLD = {
    "like": 5, "comment": 0, "collect": 0, "share": 0,
    "title": "今天随便拍了个",
}

VIDEO_WARM = {
    "like": 1000, "comment": 50, "collect": 80, "share": 20,
    "title": "餐饮食材源头工厂实拍",
}

VIDEO_COLLECT_HEAVY = {
    "like": 500, "comment": 8, "collect": 120, "share": 10,
    "title": "职场副业完整路径",
}

# 高置信度视听六层
SIX_HIGH = {
    "auditory": {
        "bgm_style": {"v": "轻快", "conf": 0.85},
        "bgm_mood": {"v": "积极", "conf": 0.8},
        "speech_pace": {"v": "中", "conf": 0.9},
        "sound_fx": {"v": "无", "conf": 0.7},
    },
    "visual": {
        "quality": {"v": "清晰", "conf": 0.9},
        "color": {"v": "暖色", "conf": 0.85},
        "composition": {"v": "中景", "conf": 0.8},
        "transition": {"v": "切入", "conf": 0.75},
        "edit_pace": {"v": "中", "conf": 0.85},
    },
    "text": {"summary": {"v": "展示工厂生产流程", "conf": 0.9}},
    "narrative": {
        "hook": {"v": "「你知道你吃的魔芋是怎么做的吗？」", "conf": 0.88},
        "structure": {"v": "问题-解答-CTA", "conf": 0.8},
        "pacing": {"v": "渐进", "conf": 0.75},
    },
    "persona": {
        "on_screen": {"v": "有", "conf": 0.95},
        "style": {"v": "接地气", "conf": 0.85},
        "camera": {"v": "手持", "conf": 0.8},
    },
    "psychology": {
        "emotion_arc": {"v": "好奇-信任-行动", "conf": 0.82},
        "resonance": {"v": "真实感", "conf": 0.85},
        "hook_point": {"v": "工厂实拍", "conf": 0.9},
    },
    "evidence_ts": ["00:00-00:04", "00:12-00:18"],
}

# 低置信度视听六层(persona.on_screen conf=0.3 < 阈值)
SIX_LOW = {
    "auditory": {"bgm_style": {"v": "轻快", "conf": 0.6}, "speech_pace": {"v": "中", "conf": 0.55}},
    "visual": {"edit_pace": {"v": "快", "conf": 0.6}},
    "text": {"summary": {"v": "生活日常", "conf": 0.65}},
    "narrative": {"hook": {"v": None, "conf": 0.2}, "structure": {"v": "无明显", "conf": 0.4}},
    "persona": {"on_screen": {"v": "有", "conf": 0.3}},  # conf < 0.5 → 不用
    "psychology": {"resonance": {"v": "亲切感", "conf": 0.45}},
    "evidence_ts": [],
}


# ── TestDiagnoseTransitionStage ───────────────────────────────────────────────

class TestDiagnoseTransitionStage(unittest.TestCase):

    def test_small_account_trust_stage(self):
        """100粉·8条 → 信任铺垫期"""
        result = diagnose_transition_stage(SMALL_A, [])
        self.assertEqual(result["stage"], "信任铺垫期")
        self.assertIn("R-C5红线", result["hard_limit"])
        self.assertIn("❌", result["hard_limit"])  # 红线图标

    def test_mid_account_soft_stage(self):
        """8000粉·60条 → 软植入期(已过信任期·未到5万)"""
        result = diagnose_transition_stage(MID_A, MID_WORKS)
        self.assertEqual(result["stage"], "软植入期")
        self.assertIn("3:7", result["next_step"])  # 内容比例铁律
        self.assertIn("R-C5红线", result["hard_limit"])
        self.assertIn("30%", result["hard_limit"])  # 广告上限

    def test_big_account_explicit_stage(self):
        """80000粉·200条 → 显性转化期"""
        result = diagnose_transition_stage(BIG_A, BIG_WORKS)
        self.assertEqual(result["stage"], "显性转化期")
        self.assertIn("30%", result["hard_limit"])  # 广告上限仍保留
        self.assertIn("顺理成章", result["next_step"])  # 铁律用语

    def test_interaction_depth_deep(self):
        """高评论/收藏率 → 深互动"""
        depth = _interaction_depth(BIG_A, BIG_WORKS)
        self.assertEqual(depth, "深")

    def test_interaction_depth_shallow(self):
        """零works + 低均赞 → 浅互动"""
        depth = _interaction_depth(SMALL_A, [])
        self.assertEqual(depth, "浅")

    def test_reason_contains_data(self):
        """reason字段要含真实数字(粉丝量/发布数)"""
        r = diagnose_transition_stage(MID_A, MID_WORKS)
        self.assertIn("8000", r["reason"])
        self.assertIn("60", r["reason"])

    def test_next_step_nonempty(self):
        """三个阶段 next_step 都不能为空"""
        for account, works in [(SMALL_A, []), (MID_A, MID_WORKS), (BIG_A, BIG_WORKS)]:
            r = diagnose_transition_stage(account, works)
            self.assertTrue(r["next_step"].strip(), f"next_step 空了: {r['stage']}")


# ── TestSuggestHooks ──────────────────────────────────────────────────────────

class TestSuggestHooks(unittest.TestCase):

    def test_three_hooks_always_present(self):
        """三钩结构在任何情况下都必须存在"""
        for sl in [None, SIX_HIGH, SIX_LOW]:
            r = suggest_hooks(VIDEO_WARM, sl)
            self.assertIn("demand_hook", r)
            self.assertIn("trust_hook", r)
            self.assertIn("cta_type", r)
            self.assertIn("cta_note", r)

    def test_six_layer_high_conf_oral_trust(self):
        """高置信度六层 + 有人出镜 → 信任钩应含「口播」相关字"""
        r = suggest_hooks(VIDEO_WARM, SIX_HIGH)
        self.assertTrue(r["six_layer_used"])
        self.assertIn("口播", r["trust_hook"])  # 口播证据型

    def test_six_layer_high_conf_hook_reuse(self):
        """六层有开头钩子(高置信) → demand_hook应提及复制"""
        r = suggest_hooks(VIDEO_WARM, SIX_HIGH)
        # narrative.hook 高置信度 → 已有钩子，建议复制
        self.assertIn("复制", r["demand_hook"])

    def test_six_layer_low_conf_persona_not_used(self):
        """低置信度 persona.on_screen → 不能推断口播型·要标ceiling"""
        r = suggest_hooks(VIDEO_COLD, SIX_LOW)
        # persona.on_screen conf=0.3 < 0.5 → 不走"口播"路
        # ceiling note 应出现
        self.assertIsNotNone(r["six_layer_ceiling_note"])
        self.assertIn("置信度", r["six_layer_ceiling_note"])

    def test_no_six_layer_fallback(self):
        """无视听六层 → six_layer_used=False · 钩子仍可生成"""
        r = suggest_hooks(VIDEO_COLD, None)
        self.assertFalse(r["six_layer_used"])
        self.assertIsNone(r["six_layer_ceiling_note"])
        self.assertTrue(r["demand_hook"])

    def test_collect_heavy_private_cta(self):
        """收藏>点赞15% → CTA应是私信钩"""
        r = suggest_hooks(VIDEO_COLLECT_HEAVY, None)
        self.assertEqual(r["cta_type"], "私信钩")

    def test_cta_contains_rationale(self):
        """cta_note 非空且有解释"""
        r = suggest_hooks(VIDEO_WARM, None)
        self.assertTrue(len(r["cta_note"]) > 10)

    def test_cold_video_demand_hook_advice(self):
        """冷门视频(无六层hook)→ demand_hook 应给具体改法"""
        r = suggest_hooks(VIDEO_COLD, None)
        # 无 narrative.hook → 给建议
        self.assertIn("前3秒", r["demand_hook"])


# ── TestDiagnoseFunnel ────────────────────────────────────────────────────────

class TestDiagnoseFunnel(unittest.TestCase):

    def test_cold_video_funnel_completion_proxy(self):
        """冷门视频·极低互动 → 卡点在完播层(代理)·含黑盒标注"""
        r = diagnose_funnel(SMALL_A, VIDEO_COLD)
        self.assertIn("完播", r["first_bottleneck"])
        self.assertIn("黑盒", r["funnel_note"])
        self.assertTrue(r["funnel_blackbox"] or "黑盒" in r["funnel_note"])

    def test_warm_video_not_stuck_at_completion(self):
        """热门视频·互动不差 → 不卡在完播层"""
        r = diagnose_funnel(MID_A, VIDEO_WARM)
        self.assertNotIn("完播层代理", r["first_bottleneck"])

    def test_collect_heavy_private_path(self):
        """收藏重(有意向无路径) → 卡成交层(关注→成交)"""
        r = diagnose_funnel(BIG_A, VIDEO_COLLECT_HEAVY)
        self.assertIn("成交", r["first_bottleneck"])

    def test_funnel_always_has_action(self):
        """每个卡点诊断都要有 action"""
        for account, video in [
            (SMALL_A, VIDEO_COLD),
            (MID_A, VIDEO_WARM),
            (BIG_A, VIDEO_COLLECT_HEAVY),
        ]:
            r = diagnose_funnel(account, video)
            self.assertTrue(r["action"].strip(), f"action 空了: {r['first_bottleneck']}")

    def test_funnel_note_always_mentions_blackbox(self):
        """诚实标注：funnel_note 必须提完播黑盒"""
        for account, video in [(SMALL_A, VIDEO_COLD), (BIG_A, VIDEO_WARM)]:
            r = diagnose_funnel(account, video)
            self.assertIn("黑盒", r["funnel_note"])
            self.assertIn("完播", r["funnel_note"])

    def test_play_count_provided_completion_not_blackbox(self):
        """传入 play 数据 → completion_blackbox=False(外推值·有参考)"""
        video_with_play = dict(VIDEO_COLD, play=5000)
        r = diagnose_funnel(SMALL_A, video_with_play)
        self.assertFalse(r["funnel_blackbox"])
        # 但仍要标外推值不精确
        self.assertIn("外推", r["funnel_note"])

    def test_root_cause_nonempty(self):
        """root_cause 在所有分支都非空"""
        for account, video in [
            (SMALL_A, VIDEO_COLD),
            (MID_A, VIDEO_WARM),
        ]:
            r = diagnose_funnel(account, video)
            self.assertTrue(r["root_cause"].strip())


# ── TestRenderConversionSection ───────────────────────────────────────────────

class TestRenderConversionSection(unittest.TestCase):

    def _render(self, account, video, works=None, sl=None):
        return render_conversion_section(account, video, works, sl)

    def test_section_header(self):
        """报告段以 ## 精准转化方案 开头"""
        r = self._render(MID_A, VIDEO_WARM, MID_WORKS, SIX_HIGH)
        self.assertIn("## 精准转化方案", r)

    def test_three_subsections(self):
        """必须有 A/B/C/D 四个子段"""
        r = self._render(MID_A, VIDEO_WARM, MID_WORKS, SIX_HIGH)
        self.assertIn("### A.", r)
        self.assertIn("### B.", r)
        self.assertIn("### C.", r)
        self.assertIn("### D.", r)

    def test_hook_table_present(self):
        """钩子段要有 Markdown 表格(|)"""
        r = self._render(MID_A, VIDEO_WARM, MID_WORKS, SIX_HIGH)
        self.assertIn("需求激活钩", r)
        self.assertIn("信任建立钩", r)
        self.assertIn("行动引导钩", r)
        self.assertIn("|", r)  # Markdown 表格

    def test_max_three_hooks_reminder(self):
        """铁律提醒：一条最多3个钩"""
        r = self._render(MID_A, VIDEO_WARM)
        self.assertIn("3", r)
        self.assertIn("铁律", r)

    def test_funnel_blackbox_note_in_render(self):
        """完播黑盒诚实标注要出现在渲染段"""
        r = self._render(SMALL_A, VIDEO_COLD)
        self.assertIn("黑盒", r)

    def test_small_account_render_no_crash(self):
        """最小化输入(空works/无六层)不报错"""
        r = self._render(SMALL_A, VIDEO_COLD, works=[], sl=None)
        self.assertTrue(len(r) > 100)

    def test_big_account_private_domain_tip(self):
        """大号显性转化期 → 末尾一句话要提私域"""
        r = self._render(BIG_A, VIDEO_COLLECT_HEAVY, BIG_WORKS, SIX_HIGH)
        self.assertIn("私域", r)

    def test_trust_stage_foundation_tip(self):
        """信任铺垫期 -> 末尾一句话要说打地基或变现"""
        r = self._render(SMALL_A, VIDEO_COLD)
        self.assertIn("打地基", r)

    def test_no_six_layer_ceiling_warning_appears(self):
        """无视听六层 → 报告中要出现 '未传入' 或类似诚实提示"""
        r = self._render(MID_A, VIDEO_WARM, MID_WORKS, sl=None)
        self.assertIn("未传入", r)

    def test_r_c5_redline_appears(self):
        """R-C5红线标注要出现在报告中(信任期或软植入期)"""
        r = self._render(SMALL_A, VIDEO_COLD)
        self.assertIn("R-C5红线", r)

    def test_stage_reason_data_in_render(self):
        """阶段判断依据要含真实数字"""
        r = self._render(MID_A, VIDEO_WARM, MID_WORKS)
        self.assertIn("8000", r)  # 粉丝数

    def test_markdown_structure_valid(self):
        """输出是合法 Markdown (有标题/内容/非空)"""
        r = self._render(BIG_A, VIDEO_WARM, BIG_WORKS, SIX_HIGH)
        lines = r.strip().split("\n")
        headers = [l for l in lines if l.startswith("#")]
        self.assertGreaterEqual(len(headers), 4)  # 至少4个标题


if __name__ == "__main__":
    unittest.main(verbosity=2)

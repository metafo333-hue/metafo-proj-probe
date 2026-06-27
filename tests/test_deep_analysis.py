"""benchmarks.py + deep_analysis.py 离线自测 · 零网络 · $0。

核心:验证「赛道感知」纠正泛娱乐尺误判 B 端号(北川魔芋真实场景)。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import benchmarks as BM
from app.services import deep_analysis as DA
from app.services import composite_scores as CS

# 还原北川魔芋:B端源头工厂·4658粉·零变现·高评论
ACCT = {
    "nickname": "北川魔芋姐｜赵娟", "follower": 4658, "max_follower": 4660,
    "avg_like": 105, "avg_collect": 3, "aweme_count": 124,
    "with_commerce_entry": False, "live_commerce": False, "commerce_density": 0.0,
    "vertical_score": 0.7,
    "engagement_structure": {"comment_per_like": 0.235, "collect_per_like": 0.036,
                             "share_per_like": 0.022, "nature": "争议型(高评论)"},
    "content_dna": {"topics": {"top_hashtags": ["安福魔芋", "魔芋工厂", "餐饮食材"]}},
}


class TestBenchmarks(unittest.TestCase):

    def test_classify_b2b_from_hashtag(self):
        # "魔芋工厂"含"工厂"·"餐饮食材"含"食材" → S档B端
        t = BM.classify_track("魔芋工厂 餐饮食材 源头")
        self.assertEqual(t["tier"], "S")
        self.assertTrue(t["is_b2b_leads"])

    def test_classify_default_b(self):
        t = BM.classify_track("随便说点啥")
        self.assertIn("B", t["tier"])
        self.assertFalse(t["is_b2b_leads"])

    def test_fan_stage_b2b_lower_threshold(self):
        # B端 4658粉 = 起号期(B端门槛低·几千粉就能变现)
        s = BM.fan_stage(4658, is_b2b=True)
        self.assertEqual(s["stage"], "B端起号期")
        # 同样粉丝量泛娱乐 = 冷启动期(禁变现)
        s2 = BM.fan_stage(4658, is_b2b=False)
        self.assertEqual(s2["stage"], "冷启动期")

    def test_monetize_b2b_ready(self):
        track = BM.classify_track("魔芋工厂 源头供货")
        m = BM.monetize_readiness(4658, False, 0.0, track)
        self.assertTrue(m["ready"])          # B端几千粉已过门槛
        # B端变现走私域承接(线索游戏)·非泛娱乐带货
        self.assertIn("私域", m["gap"] + m["recommended_path"])

    def test_engagement_high_comment_flagged(self):
        bd = BM.engagement_breakdown(105, 4658,
                                     {"comment_per_like": 0.235, "collect_per_like": 0.036})
        cpl = next(p for p in bd["parts"] if p["metric"] == "评论赞比")
        self.assertIn("潜在咨询", cpl["verdict"])


class TestDeepAnalysis(unittest.TestCase):

    def setUp(self):
        self.scores = CS.compute_all(ACCT, None)

    def test_strategic_call_corrects_b2b(self):
        # 核心:B端高评论零承接 → 应判"补承接做线索"·NOT"先做流量"
        sc = DA.strategic_call_v2(ACCT, None, self.scores)
        self.assertIn("线索", sc["call"] + sc["why"])
        self.assertNotIn("先做流量", sc["call"])
        self.assertTrue(sc["track_aware"])
        self.assertIn("CM", sc["why"])       # 带出处

    def test_deep_industry_five_parts(self):
        d = DA.deep_industry(ACCT, None, self.scores)
        for k in ("conclusion", "breakdown", "evidence", "benchmark", "implication"):
            self.assertIn(k, d)
        self.assertEqual(d["track_tier"]["tier"], "S")

    def test_deep_commerce_explains_low_score(self):
        track = BM.classify_track(DA._track_signal(ACCT))
        d = DA.deep_commerce(ACCT, None, self.scores, track)
        # 商业转化低分要给"为什么"(缺失项 + 纠偏)
        self.assertTrue(d["breakdown"])
        self.assertIn("纠偏", d["implication"])

    def test_deep_health_breakdown(self):
        d = DA.deep_health(ACCT, self.scores)
        self.assertTrue(d["breakdown"])       # 健康分拆解非空
        self.assertIsNotNone(d.get("weakest"))

    def test_deep_env_five_parts(self):
        d = DA.deep_env(ACCT, self.scores)
        for k in ("conclusion", "breakdown", "evidence", "benchmark", "implication"):
            self.assertIn(k, d)
            self.assertTrue(d[k])             # 每段非空
        # 无热点数据时诚实标·不编造
        self.assertTrue(any("拿不到" in e or "未接通" in e or "黑马" in e or "热点" in e
                            for e in d["evidence"]))

    def test_deep_video_five_parts_with_benchmark(self):
        d = DA.deep_video(ACCT, self.scores)
        for k in ("conclusion", "breakdown", "evidence", "benchmark", "implication"):
            self.assertIn(k, d)
        # 基准须含互动率健康线 + 信号优先级 + 完播黑盒诚实标
        self.assertIn("3%", d["benchmark"])
        self.assertIn("完播", d["benchmark"])

    def test_build_deep_all_four_layers(self):
        deep = DA.build_deep(ACCT, None, self.scores)
        # 四层都有深度块(env/industry/health+commerce/video)
        for k in ("env", "industry", "health", "commerce", "video", "strategic_call"):
            self.assertIn(k, deep)


if __name__ == "__main__":
    unittest.main(verbosity=2)

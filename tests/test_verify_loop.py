"""verify_loop.py 离线测试 · 零网络 · 零 LLM · $0 · 临时目录存储（不污染真库）。

覆盖：
  - record_suggestion: 落库 + 三轴算 expect_metric/expect_cycle + 基线快照
  - mark_executed: 弱样本标记（<3 视频）
  - run_backtest: 自身前后差 → 归因 → 写库 → 反哺
  - attribute: 剔三层干扰（self_pre_post 不剔 / market_adjusted 剔大盘）+ 样本门 + 相关措辞
  - feed_back: 贝叶斯累积·禁单次翻转·配对<N 不进推荐池
  - cold_start_recommend: 借库（confidence≥medium 才返回）
  - 冷启动拒绝回测（防玄学）
  - render_verify_section: 相关措辞·诚实标
"""
import pathlib
import tempfile
import unittest

from app.services import verify_loop as vl


class VerifyLoopBase(unittest.TestCase):
    def setUp(self):
        # 临时目录隔离存储·不污染真库 ~/.probe_cache
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_root = vl._CACHE_ROOT
        vl._CACHE_ROOT = pathlib.Path(self._tmp.name)

    def tearDown(self):
        vl._CACHE_ROOT = self._orig_root
        self._tmp.cleanup()

    AXIS = {"industry": "知识科普", "audience_seg": "在职转型", "account_stage": "成长期"}
    BASELINE = {"followers": 1000, "avg_play": 5000, "avg_like": 200,
                "interaction_rate": 0.04, "homepage_visit": 300, "play_proxy": 4000}


class TestRecordSuggestion(VerifyLoopBase):
    def test_record_and_axis_derivation(self):
        sid = vl.record_suggestion("rep1", "acc_x", self.AXIS, "open_hook_conflict",
                                   "前3秒改成冲突开头", self.BASELINE)
        self.assertEqual(sid, 1)
        sugs = vl.list_suggestions("acc_x")
        self.assertEqual(len(sugs), 1)
        s = sugs[0]
        # 三轴 → expect_metric（知识科普→play_proxy）/ expect_cycle（成长期→21）
        self.assertEqual(s["expect_metric"], "play_proxy")
        self.assertEqual(s["expect_cycle_days"], 21)
        self.assertEqual(s["baseline_snapshot"]["followers"], 1000)
        self.assertFalse(s["executed"])

    def test_id_autoincrement(self):
        vl.record_suggestion("r", "acc_y", self.AXIS, "f1", "建议1", self.BASELINE)
        sid2 = vl.record_suggestion("r", "acc_y", self.AXIS, "f2", "建议2", self.BASELINE)
        self.assertEqual(sid2, 2)

    def test_missing_required_raises(self):
        with self.assertRaises(ValueError):
            vl.record_suggestion("r", "", self.AXIS, "f", "t", self.BASELINE)


class TestMarkExecuted(VerifyLoopBase):
    def test_weak_sample_under_3(self):
        sid = vl.record_suggestion("r", "acc", self.AXIS, "f", "t", self.BASELINE)
        self.assertTrue(vl.mark_executed("acc", sid, "2026-06-10", ["v1", "v2"]))
        s = vl.list_suggestions("acc")[0]
        self.assertTrue(s["executed"])
        self.assertTrue(s["weak_sample"])  # 2 < 3 → 弱样本

    def test_strong_sample_3plus(self):
        sid = vl.record_suggestion("r", "acc", self.AXIS, "f", "t", self.BASELINE)
        vl.mark_executed("acc", sid, "2026-06-10", ["v1", "v2", "v3", "v4"])
        self.assertFalse(vl.list_suggestions("acc")[0]["weak_sample"])

    def test_unknown_sug_returns_false(self):
        self.assertFalse(vl.mark_executed("acc", 999, "2026-06-10", ["v1"]))


class TestAttribute(VerifyLoopBase):
    def test_insufficient_sample(self):
        r = vl.attribute(delta_raw=100, market_baseline=0, season_factor=0,
                         sample_size=2, method="self_pre_post")
        self.assertEqual(r["verdict"], "insufficient_sample")
        self.assertEqual(r["confidence"], "参考")
        self.assertIsNone(r["delta_excess"])

    def test_self_pre_post_does_not_remove_market(self):
        # MVP 自身前后对比·不剔大盘 → delta_excess == delta_raw·caveat 明示未剔
        r = vl.attribute(delta_raw=500, market_baseline=400, season_factor=50,
                         sample_size=5, method="self_pre_post")
        self.assertEqual(r["delta_excess"], 500.0)  # 未剔除
        self.assertIn("未剔除", r["caveat"])
        self.assertEqual(r["verdict"], "correlated_up")

    def test_market_adjusted_removes_interference(self):
        # 剔大盘+季节后超额=500-400-50=50 → 仍相关上升·但若全归大盘则归零
        r = vl.attribute(delta_raw=500, market_baseline=400, season_factor=50,
                         sample_size=5, method="market_adjusted")
        self.assertEqual(r["delta_excess"], 50.0)
        self.assertEqual(r["verdict"], "correlated_up")
        self.assertEqual(r["confidence"], "medium")

    def test_interference_swallows_gain_to_no_effect(self):
        # 涨幅全是大盘+季节贡献 → 超额=0 → no_effect（防"改了A涨了就归功A"玄学）
        r = vl.attribute(delta_raw=500, market_baseline=400, season_factor=100,
                         sample_size=5, method="market_adjusted")
        self.assertEqual(r["delta_excess"], 0.0)
        self.assertEqual(r["verdict"], "no_effect")

    def test_did_high_confidence(self):
        r = vl.attribute(delta_raw=300, market_baseline=100, season_factor=50,
                         sample_size=6, method="did")
        self.assertEqual(r["confidence"], "high")
        self.assertIn("剔大盘+季节", r["caveat"])

    def test_no_caused_wording(self):
        # 铁律1：verdict 用 correlated·绝不出 caused/因为
        r = vl.attribute(delta_raw=100, market_baseline=0, season_factor=0,
                         sample_size=5, method="self_pre_post")
        self.assertTrue(r["verdict"].startswith("correlated"))
        self.assertNotIn("导致", r["caveat"])
        self.assertNotIn("因为", r["caveat"])


class TestRunBacktest(VerifyLoopBase):
    def test_self_pre_post_delta_and_feedback(self):
        sid = vl.record_suggestion("r", "acc", self.AXIS, "open_hook", "t", self.BASELINE)
        vl.mark_executed("acc", sid, "2026-06-10", ["v1", "v2", "v3", "v4"])
        # 重采 play_proxy 从 4000 → 6000，涨 2000
        result = {"play_proxy": 6000, "followers": 1500}
        bt = vl.run_backtest("acc", sid, result, sample_size=5)
        self.assertEqual(bt["metric"], "play_proxy")
        self.assertEqual(bt["delta_raw"], 2000.0)
        self.assertEqual(bt["verdict"], "correlated_up")
        # 反哺：feature_weight 库已记一次 hit
        recs = vl.cold_start_recommend(self.AXIS, min_confidence="参考")
        self.assertTrue(any(r["feature_key"] == "open_hook" and r["hit_count"] == 1 for r in recs))

    def test_cold_start_refuses_backtest(self):
        cold_axis = {**self.AXIS, "account_stage": "冷启动"}
        sid = vl.record_suggestion("r", "acc_cold", cold_axis, "f", "t", self.BASELINE)
        bt = vl.run_backtest("acc_cold", sid, {"followers": 9999}, sample_size=10)
        self.assertEqual(bt["verdict"], "no_backtest_cold_start")
        # 冷启动不喂权重（防噪声进飞轮）
        self.assertEqual(vl.cold_start_recommend(cold_axis, min_confidence="参考"), [])

    def test_insufficient_sample_not_fed_back(self):
        sid = vl.record_suggestion("r", "acc2", self.AXIS, "f2", "t", self.BASELINE)
        bt = vl.run_backtest("acc2", sid, {"play_proxy": 9000}, sample_size=1)
        self.assertEqual(bt["verdict"], "insufficient_sample")
        # 不进飞轮
        self.assertEqual(vl.cold_start_recommend(self.AXIS, min_confidence="参考"), [])

    def test_unknown_sug_returns_none(self):
        self.assertIsNone(vl.run_backtest("acc", 999, {}, sample_size=5))


class TestFeedBack(VerifyLoopBase):
    def test_single_hit_does_not_flip_weight_to_one(self):
        # 防单点偶然：单次命中权重不翻到 1（贝叶斯平滑）
        rec = vl.feed_back(self.AXIS, "fX", "correlated_up", 5)
        self.assertEqual(rec["hit_count"], 1)
        self.assertLess(rec["weight"], 1.0)
        self.assertEqual(rec["confidence"], "参考")  # 配对不足

    def test_accumulation_raises_confidence_and_weight(self):
        for _ in range(5):
            vl.feed_back(self.AXIS, "fY", "correlated_up", 5)
        rec = vl.feed_back(self.AXIS, "fY", "correlated_up", 5)  # 第6次
        self.assertEqual(rec["total_pairs"], 6)
        self.assertEqual(rec["confidence"], "medium")
        self.assertGreater(rec["weight"], 0.7)

    def test_miss_lowers_weight(self):
        for _ in range(3):
            vl.feed_back(self.AXIS, "fZ", "correlated_up", 5)
        for _ in range(3):
            vl.feed_back(self.AXIS, "fZ", "no_effect", 5)
        rec = vl.feed_back(self.AXIS, "fZ", "correlated_down", 5)
        # 3 hit / 4 miss → weight < 0.5
        self.assertLess(rec["weight"], 0.5)


class TestColdStartRecommend(VerifyLoopBase):
    def test_only_validated_features_returned(self):
        # 未达 medium confidence 的不进推荐池
        vl.feed_back(self.AXIS, "weak_feat", "correlated_up", 5)  # 1 pair → 参考
        for _ in range(5):
            vl.feed_back(self.AXIS, "strong_feat", "correlated_up", 5)  # 5 pairs → medium
        recs = vl.cold_start_recommend(self.AXIS, min_confidence="medium")
        keys = {r["feature_key"] for r in recs}
        self.assertIn("strong_feat", keys)
        self.assertNotIn("weak_feat", keys)

    def test_axis_isolation(self):
        for _ in range(5):
            vl.feed_back(self.AXIS, "feat_a", "correlated_up", 5)
        other = {"industry": "餐饮", "audience_seg": "实体店主", "account_stage": "成熟期"}
        self.assertEqual(vl.cold_start_recommend(other, min_confidence="medium"), [])


class TestRender(VerifyLoopBase):
    def test_render_none_when_no_backtest(self):
        vl.record_suggestion("r", "acc", self.AXIS, "f", "t", self.BASELINE)
        self.assertIsNone(vl.render_verify_section("acc"))

    def test_render_correlated_wording(self):
        sid = vl.record_suggestion("r", "acc", self.AXIS, "f", "前3秒加冲突", self.BASELINE)
        vl.mark_executed("acc", sid, "2026-06-10", ["v1", "v2", "v3"])
        vl.run_backtest("acc", sid, {"play_proxy": 6000}, sample_size=5)
        md = vl.render_verify_section("acc")
        self.assertIsNotNone(md)
        self.assertIn("相关", md)
        self.assertNotIn("导致", md)
        self.assertIn("参考级闭环", md)


if __name__ == "__main__":
    unittest.main()

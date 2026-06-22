"""trend_analysis.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - 样本门：<10 条不下趋势结论（防玄学硬门）
  - 作品基线趋势：上行/下行/平稳 + Mann-Kendall 显著性
  - 转折点识别：变点检测 + 动作归因 + 排除外部脉冲
  - 粉丝增速：复访快照二阶导 + 净掉粉 + 无快照标"需复访"
  - 分级衰退预警：红/黄/绿 + 人群敏感度
  - 防玄学：爆款离群剔除 / 短期波动≠趋势 / 单条不判
  - 渲染：看导数不看存量 + 诚实三问
"""
import unittest

from app.services.trend_analysis import (
    analyze_trend, render_trend_section, build_series, mark_outliers,
    baseline_trend, growth_trend, detect_change_points, attribute_turning_points,
    decline_alerts, mann_kendall, _median,
    MIN_WORKS_FOR_BASELINE, RELIABLE_WORKS,
    TrendResult,
)

DAY = 86400


def _works(values, start=1_700_000_000, step=3 * DAY):
    """造逐条作品（按时间递增·like=values[i]）。"""
    return [{"desc": f"作品{i} #日常", "like": v, "comment": v // 10,
             "collect": v // 20, "share": v // 30, "create_time": start + i * step}
            for i, v in enumerate(values)]


# ── 样本门 ──────────────────────────────────────────────────────────────────
class TestSampleGate(unittest.TestCase):
    def test_under_min_no_trend(self):
        res = analyze_trend(_works([10, 20, 30, 40, 50]))  # 5 < 10
        self.assertEqual(res["mode"], "breakthrough_check")
        self.assertEqual(res["confidence"], "insufficient")

    def test_cold_start_target_setting(self):
        res = analyze_trend([], stage="cold_start")
        self.assertEqual(res["mode"], "target_setting")

    def test_at_min_does_trend(self):
        res = analyze_trend(_works(list(range(10, 110, 10))))  # 10 条
        self.assertEqual(res["mode"], "full")


# ── 作品基线趋势 ─────────────────────────────────────────────────────────────
class TestBaselineTrend(unittest.TestCase):
    def test_rising(self):
        # 单调上行（显著）
        res = analyze_trend(_works([10, 12, 15, 18, 22, 27, 33, 40, 48, 60, 75, 90]))
        self.assertEqual(res["work_baseline"].direction, "rising")
        self.assertLessEqual(res["work_baseline"].significance, 0.10)

    def test_declining(self):
        res = analyze_trend(_works([90, 75, 60, 50, 42, 35, 28, 22, 18, 14, 11, 9]))
        self.assertEqual(res["work_baseline"].direction, "declining")

    def test_plateau_noise_not_trend(self):
        # 锯齿噪音 → 不显著 → 平稳（短期波动≠趋势）
        res = analyze_trend(_works([50, 48, 52, 49, 51, 47, 53, 50, 48, 52, 49, 51]))
        self.assertEqual(res["work_baseline"].direction, "plateau")

    def test_confidence_levels(self):
        ref = analyze_trend(_works(list(range(10, 25))))   # 15 条 → reference
        rel = analyze_trend(_works(list(range(10, 35))))   # 25 条 → reliable
        self.assertEqual(ref["work_baseline"].confidence, "reference")
        self.assertEqual(rel["work_baseline"].confidence, "reliable")


# ── 爆款离群剔除（防玄学） ───────────────────────────────────────────────────
class TestOutlier(unittest.TestCase):
    def test_outlier_marked(self):
        s = build_series(_works([10, 12, 11, 13, 10, 12, 11, 13, 10, 5000]))
        s = mark_outliers(s)
        self.assertTrue(s[-1].is_outlier)  # 5000 是爆款离群
        self.assertFalse(s[0].is_outlier)

    def test_outlier_excluded_from_baseline(self):
        # 平稳基线 + 一条爆款 → 不应被判为"在涨"
        res = analyze_trend(_works([10, 12, 11, 13, 10, 12, 11, 13, 10, 12, 11, 9000]))
        self.assertGreaterEqual(res["n_outliers"], 1)
        self.assertNotEqual(res["work_baseline"].direction, "rising")


# ── 转折点识别 + 归因 ───────────────────────────────────────────────────────
class TestChangePoint(unittest.TestCase):
    def test_detects_positive_jump(self):
        # 前 6 条低基线，后 6 条高基线（改主题后起飞）
        works = (_works([10, 11, 10, 12, 11, 10], start=1_700_000_000)
                 + [{"desc": f"新方向{i} #干货教程", "like": 100, "comment": 10,
                     "collect": 5, "share": 3,
                     "create_time": 1_700_000_000 + (6 + i) * 3 * DAY} for i in range(6)])
        s = build_series(works)
        s = mark_outliers(s)
        tps = detect_change_points(s)
        self.assertTrue(any(tp.direction == "positive" for tp in tps))

    def test_attribution_topic_shift(self):
        works = ([{"desc": "旧 #生活", "like": 10, "create_time": 1_700_000_000 + i * DAY}
                  for i in range(6)]
                 + [{"desc": "新 #干货", "like": 100, "create_time": 1_700_000_000 + (6 + i) * DAY}
                    for i in range(6)])
        s = mark_outliers(build_series(works))
        ws = sorted(works, key=lambda w: w["create_time"])
        tps = attribute_turning_points(ws, detect_change_points(s))
        pos = [tp for tp in tps if tp.direction == "positive"]
        self.assertTrue(pos)
        self.assertTrue(pos[0].attributable)
        self.assertIn("干货", pos[0].action_diff["new_topics"])

    def test_external_pulse_excluded(self):
        # 变点处那一条远超均值（被大V带飞/被推荐的单条爆点）→ external_pulse=True·不可归因。
        # 前 6 条低基线；第 7 条是 5000 的单点爆量，之后回落 → 变点在第 7 条，那条 >> 均值。
        works = ([{"desc": "常规 #生活", "like": 10, "create_time": 1_700_000_000 + i * DAY}
                  for i in range(6)]
                 + [{"desc": "被推荐 #生活", "like": 5000,
                     "create_time": 1_700_000_000 + 6 * DAY}]
                 + [{"desc": "回落 #生活", "like": 60,
                     "create_time": 1_700_000_000 + (7 + i) * DAY} for i in range(5)])
        s = mark_outliers(build_series(works))
        ws = sorted(works, key=lambda w: w["create_time"])
        tps = attribute_turning_points(ws, detect_change_points(s))
        pos = [tp for tp in tps if tp.direction == "positive"]
        self.assertTrue(pos)
        # 变点那条 (5000) 远超均值×4 → 判外部脉冲·不可归因
        self.assertTrue(pos[0].external_pulse)
        self.assertFalse(pos[0].attributable)

    def test_no_change_point_on_flat(self):
        s = mark_outliers(build_series(_works([50] * 14)))
        self.assertEqual(detect_change_points(s), [])


# ── 粉丝增速（复访快照） ──────────────────────────────────────────────────────
class TestGrowthTrend(unittest.TestCase):
    def test_no_snapshots_returns_none(self):
        res = analyze_trend(_works(list(range(10, 30))))
        self.assertIsNone(res["fans_trend"])  # 单次无快照 → 需复访

    def test_accelerating(self):
        # 涨粉率递增 → accelerating
        snaps = [{"timestamp": 1_700_000_000 + i * 7 * DAY, "follower": f}
                 for i, f in enumerate([1000, 1100, 1300, 1700, 2500])]
        ft = growth_trend(snaps)
        self.assertIsNotNone(ft)
        self.assertIn(ft.direction, ("accelerating", "rising"))

    def test_net_negative_declining(self):
        snaps = [{"timestamp": 1_700_000_000 + i * 7 * DAY, "follower": f}
                 for i, f in enumerate([5000, 4900, 4700, 4400, 4000])]
        ft = growth_trend(snaps)
        self.assertEqual(ft.direction, "declining")
        self.assertIn("净掉粉", ft.note)

    def test_too_few_snapshots(self):
        self.assertIsNone(growth_trend([{"timestamp": 1, "follower": 100}]))


# ── 分级衰退预警 ─────────────────────────────────────────────────────────────
class TestDeclineAlerts(unittest.TestCase):
    def test_red_on_net_loss(self):
        res = analyze_trend(
            _works(list(range(50, 30, -1))),  # 下行作品
            snapshots=[{"timestamp": 1_700_000_000 + i * 7 * DAY, "follower": f}
                       for i, f in enumerate([5000, 4900, 4700, 4400, 4000])])
        levels = {a.level for a in res["alerts"]}
        self.assertIn("red", levels)

    def test_yellow_on_baseline_decline(self):
        res = analyze_trend(_works([90, 80, 70, 62, 55, 48, 42, 36, 30, 25, 20, 16]))
        signals = [a.signal for a in res["alerts"]]
        self.assertTrue(any("基线" in s for s in signals))

    def test_green_on_plateau(self):
        res = analyze_trend(_works([50, 48, 52, 49, 51, 47, 53, 50, 48, 52, 49, 51]))
        self.assertTrue(any(a.level == "green" for a in res["alerts"]))

    def test_shop_owner_segment_softens(self):
        # 实体店主：增速衰减黄→绿（不慌粉丝波动）
        wt = TrendResult("work_baseline", "rising", 0.1, None, 0.05, False, "reliable")
        ft = TrendResult("fans_growth", "decelerating", -0.01, -0.01, 0.05, False, "reliable")
        series = build_series(_works([10, 12, 14, 16, 18, 20, 22, 24, 26, 28]))
        alerts = decline_alerts(wt, ft, series, segment="shop_owner")
        decel = [a for a in alerts if "增速" in a.signal]
        self.assertTrue(decel)
        self.assertEqual(decel[0].level, "green")


# ── Mann-Kendall ────────────────────────────────────────────────────────────
class TestMannKendall(unittest.TestCase):
    def test_monotonic_significant(self):
        self.assertLessEqual(mann_kendall([1, 2, 3, 4, 5, 6, 7, 8]), 0.05)

    def test_noise_not_significant(self):
        self.assertGreater(mann_kendall([5, 4, 6, 5, 4, 6, 5, 4]), 0.10)

    def test_too_few_returns_one(self):
        self.assertEqual(mann_kendall([1, 2]), 1.0)


# ── 渲染 ────────────────────────────────────────────────────────────────────
class TestRender(unittest.TestCase):
    def test_render_full_has_derivative_framing(self):
        md = render_trend_section(_works(list(range(10, 35))))
        self.assertIn("看导数不看存量", md)
        self.assertIn("作品基线趋势", md)
        self.assertIn("转折点", md)
        # 诚实三问
        self.assertIn("诚实", md)

    def test_render_insufficient(self):
        md = render_trend_section(_works([10, 20, 30]))
        self.assertIn("不下趋势结论", md)

    def test_render_needs_revisit_for_fans(self):
        md = render_trend_section(_works(list(range(10, 30))))
        self.assertIn("需复访", md)

    def test_render_cold_start(self):
        md = render_trend_section([], stage="cold_start")
        self.assertIn("冷启动", md)


if __name__ == "__main__":
    unittest.main()

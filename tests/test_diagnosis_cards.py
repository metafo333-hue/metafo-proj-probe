"""diagnosis_cards.py 离线自测 · 零网络 · 零 LLM · $0

覆盖:
  - diagnose_churn: 重度掉粉 / 轻度掉粉 / 正常 / 无数据
  - diagnose_pricing: 有星图路径 / 无星图兜底 / 虚高预警
  - diagnose_funnel: 各漏斗堵点 L1-L4 / 健康账号
  - diagnose_track: 各商业档 + 垂直度组合
  - render_diagnosis_section: 串联四卡输出 Markdown
"""
import sys
import os

# PYTHONPATH 注入: probe 根 + combo-deep-probe（如存在）
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

import unittest
from app.services.diagnosis_cards import (
    diagnose_churn,
    diagnose_pricing,
    diagnose_funnel,
    diagnose_track,
    render_diagnosis_section,
)

# ──────────────────────────────────────────────────────────────────────────────
# 合成 account dict
# ──────────────────────────────────────────────────────────────────────────────

HEAVY_CHURN = {
    "nickname": "重度掉粉号",
    "follower": 30000,
    "max_follower": 50000,   # drawdown = 40%
    "follower_drawdown": {"drawdown_pct": 40.0, "label": "重度掉粉"},
    "avg_like": 800,
    "vertical_score": 0.55,
    "engagement_structure": {"collect_rate": 0.005, "share_rate": 0.002},
    "commerce_density": 0.08,
    "with_commerce_entry": True,
}

LIGHT_CHURN = {
    "nickname": "轻度掉粉号",
    "follower": 92000,
    "max_follower": 100000,  # drawdown = 8%
    "follower_drawdown": {"drawdown_pct": 8.0},
    "avg_like": 2000,
    "vertical_score": 0.65,
    "engagement_structure": {},
    "commerce_density": 0.25,
    "with_commerce_entry": True,
}

HEALTHY_ACCOUNT = {
    "nickname": "健康头部号",
    "follower": 200000,
    "max_follower": 210000,  # drawdown = 4.8%
    "follower_drawdown": {"drawdown_pct": 4.8},
    "avg_like": 8000,
    "avg_play": 60000,
    "vertical_score": 0.78,
    "engagement_structure": {"collect_rate": 0.025, "share_rate": 0.012},
    "commerce_density": 0.30,
    "with_commerce_entry": True,
    "live_commerce": True,
    "hashtags": ["美妆", "护肤"],
}

NO_DATA_ACCOUNT = {
    "nickname": "零数据新号",
    "follower": 500,
    "max_follower": None,
    "follower_drawdown": None,
    "avg_like": 50,
    "vertical_score": None,
    "engagement_structure": None,
    "commerce_density": None,
    "with_commerce_entry": False,
}

LOW_TRAFFIC_ACCOUNT = {
    "nickname": "低流量号",
    "follower": 5000,
    "max_follower": 5500,
    "follower_drawdown": {"drawdown_pct": 9.0},
    "avg_like": 120,
    "avg_play": 800,   # L1 堵点
    "vertical_score": 0.40,
    "engagement_structure": {},
    "commerce_density": 0.05,
    "with_commerce_entry": False,
}

# 模拟 xprof dict (兼容 dict 接口)
MOCK_XPROF_GOOD = {
    "is_xingtu": True,
    "price_info": [
        {"video_type": 1, "price": 8200},   # ¥8200(实测元·非分·区别于CPM)
        {"video_type": 2, "price": 11200},
    ],
    "expect_vv": {"value": 800000},   # ¥8200报价对应~80万预期播放(自洽·cpm≈10)
    "link_shopping_index": {"avg_value": 65.0, "rank_percent": 0.05},
    "industry_tag": ["美妆", "护肤"],
}

MOCK_XPROF_HIGH_DEVIATION = {
    "is_xingtu": True,
    "price_info": [{"video_type": 1, "price": 50000}],  # 500元
    "expect_vv": {"value": 500000},  # 50万预期·实际才3万→偏差>50%
    "link_shopping_index": {"avg_value": 30.0, "rank_percent": 0.30},
}


# ──────────────────────────────────────────────────────────────────────────────
# Test Cases
# ──────────────────────────────────────────────────────────────────────────────

class TestDiagnoseChurn(unittest.TestCase):

    def test_heavy_churn(self):
        r = diagnose_churn(HEAVY_CHURN)
        self.assertEqual(r["card"], "P1")
        self.assertEqual(r["status"], "heavy_churn")
        self.assertEqual(r["severity"], "red")
        self.assertGreaterEqual(r["drawdown_pct"], 15.0)
        self.assertTrue(r["advice"])

    def test_light_churn(self):
        r = diagnose_churn(LIGHT_CHURN)
        self.assertEqual(r["status"], "light_churn")
        self.assertEqual(r["severity"], "yellow")
        self.assertGreater(r["drawdown_pct"], 5.0)
        self.assertLess(r["drawdown_pct"], 15.0)

    def test_normal(self):
        r = diagnose_churn(HEALTHY_ACCOUNT)
        self.assertEqual(r["status"], "normal")
        self.assertEqual(r["severity"], "green")

    def test_no_data_fallback(self):
        """无 follower_drawdown 且无 max_follower → unknown 状态而非崩溃。"""
        r = diagnose_churn(NO_DATA_ACCOUNT)
        self.assertEqual(r["status"], "unknown")
        self.assertIsNone(r["drawdown_pct"])

    def test_auto_calc_from_follower_fields(self):
        """max_follower + follower 自动计算 drawdown_pct（不依赖 follower_drawdown 字段）。"""
        acct = {
            "follower": 80000,
            "max_follower": 100000,
            "follower_drawdown": None,
            "engagement_structure": {},
        }
        r = diagnose_churn(acct)
        self.assertIsNotNone(r["drawdown_pct"])
        self.assertAlmostEqual(r["drawdown_pct"], 20.0, places=0)
        self.assertEqual(r["status"], "heavy_churn")


class TestDiagnosePricing(unittest.TestCase):

    def test_with_xingtu_fair(self):
        acct = {**HEALTHY_ACCOUNT, "avg_play": 800000}   # ¥8200报价对应~80万播放→CPM≈10(fair·自洽)
        r = diagnose_pricing(acct, MOCK_XPROF_GOOD)
        self.assertEqual(r["card"], "P3")
        self.assertIsNotNone(r["star_price_yuan"])
        self.assertAlmostEqual(r["star_price_yuan"], 8200.0)   # price 已是元(实测修复)
        self.assertIsNotNone(r["actual_cpm"])
        self.assertIn(r["status"], ("fair", "low"))

    def test_high_deviation_warning(self):
        acct = {**HEALTHY_ACCOUNT, "avg_play": 30000}
        r = diagnose_pricing(acct, MOCK_XPROF_HIGH_DEVIATION)
        # 预期 500000 vs 实际 30000 → 偏差 >50% → status=high or advice 含警告
        self.assertIsNotNone(r["vv_deviation_pct"])
        self.assertGreater(r["vv_deviation_pct"], 50.0)
        self.assertIn(r["status"], ("high",))

    def test_no_xingtu_fallback(self):
        r = diagnose_pricing(LOW_TRAFFIC_ACCOUNT)
        self.assertEqual(r["status"], "no_xingtu")
        # 兜底估算应给出结果
        self.assertIsNotNone(r["estimated_price_yuan"])

    def test_no_xingtu_no_play_data(self):
        r = diagnose_pricing(NO_DATA_ACCOUNT)
        self.assertEqual(r["status"], "no_xingtu")
        # 粉丝极少但不崩溃
        self.assertIn("advice", r)


class TestDiagnoseFunnel(unittest.TestCase):

    def test_l1_traffic_bottleneck(self):
        r = diagnose_funnel(LOW_TRAFFIC_ACCOUNT)
        self.assertEqual(r["card"], "P6")
        self.assertEqual(r["funnel_bottleneck"], "L1_traffic")
        self.assertEqual(r["severity"], "red")

    def test_l2_no_entry(self):
        acct = {**HEALTHY_ACCOUNT, "with_commerce_entry": False, "avg_play": 50000}
        r = diagnose_funnel(acct)
        self.assertEqual(r["funnel_bottleneck"], "L2_no_entry")
        self.assertEqual(r["severity"], "red")

    def test_l3_low_density(self):
        acct = {**HEALTHY_ACCOUNT, "commerce_density": 0.05}  # 5%
        r = diagnose_funnel(acct)
        self.assertEqual(r["funnel_bottleneck"], "L3_low_density")
        self.assertEqual(r["severity"], "yellow")

    def test_healthy_funnel(self):
        r = diagnose_funnel(HEALTHY_ACCOUNT)
        self.assertEqual(r["funnel_bottleneck"], "healthy")
        self.assertEqual(r["severity"], "green")

    def test_over_commercial_warn(self):
        acct = {**HEALTHY_ACCOUNT, "commerce_density": 0.75}  # 75% 过高
        r = diagnose_funnel(acct)
        self.assertIsNotNone(r.get("over_commercial_warn"))

    def test_no_data_graceful(self):
        r = diagnose_funnel(NO_DATA_ACCOUNT)
        self.assertIn("funnel_bottleneck", r)
        # 不应抛异常


class TestDiagnoseTrack(unittest.TestCase):

    def test_golden_combo_clear_vertical_high_commercial(self):
        r = diagnose_track(HEALTHY_ACCOUNT, MOCK_XPROF_GOOD)
        self.assertEqual(r["card"], "P4")
        self.assertEqual(r["vertical_tier"], "clear")
        self.assertIn(r["commercial_tier"], ("A", "S"))
        self.assertIn("prescription", r)

    def test_low_vertical_low_commercial(self):
        acct = {**NO_DATA_ACCOUNT, "vertical_score": 0.15}
        r = diagnose_track(acct)
        self.assertEqual(r["vertical_tier"], "chaotic")
        self.assertEqual(r["commercial_tier"], "D")  # 无星图
        self.assertTrue(r["advice"])

    def test_fuzzy_vertical_mid_commercial(self):
        acct = {**HEALTHY_ACCOUNT, "vertical_score": 0.45}
        xp = {**MOCK_XPROF_GOOD, "link_shopping_index": {"avg_value": 50.0, "rank_percent": 0.15}}
        r = diagnose_track(acct, xp)
        self.assertEqual(r["vertical_tier"], "fuzzy")
        self.assertEqual(r["commercial_tier"], "B")

    def test_no_xprof_no_crash(self):
        r = diagnose_track(HEALTHY_ACCOUNT)
        self.assertIn("commercial_tier", r)
        self.assertEqual(r["commercial_tier"], "D")  # 无 xprof→D档


class TestRenderDiagnosisSection(unittest.TestCase):

    def test_full_render(self):
        md = render_diagnosis_section(HEALTHY_ACCOUNT, MOCK_XPROF_GOOD)
        self.assertIn("P1", md)
        self.assertIn("P3", md)
        self.assertIn("P6", md)
        self.assertIn("P4", md)
        self.assertIn("经验值", md)  # 诚实标注必在

    def test_render_no_data_no_crash(self):
        md = render_diagnosis_section(NO_DATA_ACCOUNT)
        self.assertIsInstance(md, str)
        self.assertGreater(len(md), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)

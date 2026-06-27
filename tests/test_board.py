"""board.py + board_render.py 离线自测 · 零网络 · 零 LLM · $0。

覆盖:
  - build_board: 四层结构齐全 / 算账三态(开星图/无星图/缓存) / headline 取最高 severity
  - render_board_html: 三屏 + 四层 + 算账齐全 / 自包含 HTML
  - render_board_md: 四层 + 算账
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import board as B
from app.services import board_render as R

# 合成 account(开星图路径·掉粉重度→headline 应取 churn red)
ACCT = {
    "nickname": "测试美食号",
    "follower": 30000, "max_follower": 50000,   # drawdown 40% → 重度
    "follower_drawdown": {"drawdown_pct": 40.0, "label": "重度掉粉"},
    "avg_like": 800, "max_like": 8000, "burst_ratio": 10.0,
    "vertical_score": 0.55, "update_gap_days": 3.0,
    "engagement_structure": {"collect_rate": 0.005, "share_rate": 0.002},
    "commerce_density": 0.08, "with_commerce_entry": True,
    "industry_tag": "美食探店",
    "track_competition": {"keyword": "美食探店", "result_count": 18, "has_more": True},
}
# xprof_adapter(开星图·dict 形态·与 account.py _p2c/_ix 一致)
XPROF = {
    "expect_vv": 6000, "industry_tags": ["美食探店"], "industry_tag": "美食探店",
    "price_info": {"price_1_20": 8200, "price_21_60": 11200},
    "link_shopping_index": {"avg_value": 53.4, "rank_percent": 0.21},
    "link_shopping_index_avg": 53.4,
    "link_convert_index": {"avg_value": 55.29, "rank_percent": 0.30},
    "link_star_index": {"avg_value": 60.0, "rank_percent": 0.25},
    "fans_portrait": [], "audience_portrait": [], "rec_videos": [],
    "rec_interact_rates": [0.03, 0.04],
}


class TestBuildBoard(unittest.TestCase):

    def test_four_layers_present(self):
        b = B.build_board(ACCT, XPROF)
        for k in ("env", "industry", "account", "video"):
            self.assertIn(k, b["layers"], f"缺第 {k} 层")
            self.assertIn("cost_yuan", b["layers"][k])
            self.assertIn("user_question", b["layers"][k])
            self.assertIn("value", b["layers"][k])

    def test_layer_coords_ordered(self):
        b = B.build_board(ACCT, XPROF)
        self.assertTrue(b["layers"]["env"]["coord"].startswith("①"))
        self.assertTrue(b["layers"]["industry"]["coord"].startswith("②"))
        self.assertTrue(b["layers"]["account"]["coord"].startswith("③"))
        self.assertTrue(b["layers"]["video"]["coord"].startswith("④"))

    def test_headline_picks_worst_severity(self):
        b = B.build_board(ACCT, XPROF)
        # 重度掉粉 → churn severity=red → top_concern 应是掉粉卡
        self.assertEqual(b["headline"]["top_concern"]["severity"], "red")
        self.assertIn("掉粉", b["headline"]["top_concern"]["title"] or "")

    def test_strategic_call_present(self):
        b = B.build_board(ACCT, XPROF)
        sc = b["headline"]["strategic_call"]
        self.assertIn("call", sc)
        self.assertIn(sc["color"], ("red", "yellow", "green"))
        self.assertTrue(sc["why"])

    def test_strategic_call_traffic_first_when_low_commerce(self):
        # 低转化账号 → 应判"先做流量"
        acct = dict(ACCT)
        b = B.build_board(acct, None)  # 无星图→C3 商业转化极低
        self.assertIn("流量", b["headline"]["strategic_call"]["call"])

    def test_next_video_rx_in_video_layer(self):
        acct = dict(ACCT)
        acct["content_dna"] = {
            "next_video_rx": {"summary": "下条怎么拍 = ...",
                              "steps": ["发布时段:选 晚间 18-22", "暂不挂车:先做曝光"]},
            "best_time": {"verdict": "晚间表现最好"},
        }
        b = B.build_board(acct, XPROF)
        v = b["layers"]["video"]
        self.assertIsNotNone(v["next_video_rx"])
        self.assertEqual(len(v["next_video_rx"]["steps"]), 2)
        self.assertIsNotNone(v["dna"])

    def test_accounting_xingtu(self):
        b = B.build_board(ACCT, XPROF, cache_hit=False)
        acc = b["accounting"]
        self.assertIn("星图", acc["mode"])
        self.assertGreater(acc["total_yuan"], 1.0)   # 开星图 ≈ ¥1.07
        self.assertEqual(set(acc["per_layer_yuan"]), {"env", "industry", "account", "video"})

    def test_accounting_no_xingtu(self):
        b = B.build_board(ACCT, None, cache_hit=False)
        acc = b["accounting"]
        self.assertIn("无星图", acc["mode"])
        self.assertLess(acc["total_yuan"], 0.1)       # 无星图 ≈ ¥0.044
        # #6 修:行业层星图分位取不到→¥0;账号层采了 profile→非 0(诚实归因)
        self.assertEqual(acc["per_layer_yuan"]["industry"], 0.0)
        self.assertGreater(acc["per_layer_yuan"]["account"], 0.0)

    def test_accounting_cache_hit(self):
        b = B.build_board(ACCT, XPROF, cache_hit=True)
        self.assertEqual(b["accounting"]["total_yuan"], 0.0)
        self.assertIn("复诊", b["accounting"]["mode"])

    def test_radar_split_self_vs_env(self):
        # #4 修:雷达拆账号自身(C1-8) vs 环境情报(C9-14)
        b = B.build_board(ACCT, XPROF)
        radar = b["layers"]["account"]["radar"]
        self.assertEqual(len(radar["account_self"]), 8)
        self.assertEqual(len(radar["env_intel"]), 6)
        self.assertEqual(radar["account_self"][0]["key"], "C1")
        self.assertEqual(radar["env_intel"][0]["key"], "C9")
        # 环境组每项带"大盘情报·非账号得分"标注
        self.assertTrue(all("note" in r for r in radar["env_intel"]))

    def test_env_intel_topcap_flagged(self):
        # #4 修:C14 顶格(≥98)在环境组应标"疑标度撞顶·仅作情报参考"
        from app.services import composite_scores as CS
        # 构造 C14=100 的 account(billboard 数据丰富)
        acct = dict(ACCT)
        acct["board_low_fan"] = [{"title": f"#话题{i} #魔芋", "fans": 100, "play": 99999} for i in range(8)]
        acct["board_topics"] = [{"name": f"t{i}", "avg_play": 50000} for i in range(6)]
        b = B.build_board(acct, XPROF)
        c14 = next(r for r in b["layers"]["account"]["radar"]["env_intel"] if r["key"] == "C14")
        if isinstance(c14["score"], (int, float)) and c14["score"] >= 98:
            self.assertIn("情报", c14["note"])

    def test_headline_dedup_strategic_vs_concern(self):
        # #1 修:战略判断=红(先做流量)时·top_concern 不复述漏斗卡
        acct = dict(ACCT)
        b = B.build_board(acct, None)   # 无星图→C3低→战略=红
        if b["headline"]["strategic_call"]["color"] == "red":
            self.assertNotEqual(b["headline"]["top_concern"]["title"], "转化漏斗诊断")

    def test_no_star_layer_honest(self):
        # #6 修:无星图→②③ 标 star_status·成本归 ③ 非 0
        b = B.build_board(ACCT, None)
        self.assertIn("未开星图", b["layers"]["industry"]["star_status"])
        self.assertIn("未开星图", b["layers"]["account"]["star_status"])
        # ③ 账号采了 profile·成本非 0(诚实)
        self.assertGreater(b["accounting"]["per_layer_yuan"]["account"], 0)

    def test_cost_value_inversion(self):
        # 算账核心:账号层最贵·环境层≈0(成本价值错位)
        b = B.build_board(ACCT, XPROF)
        env_c = b["layers"]["env"]["cost_yuan"]
        acct_c = b["layers"]["account"]["cost_yuan"]
        self.assertLess(env_c, 0.05)
        self.assertGreater(acct_c, env_c * 10)


class TestRenderHtml(unittest.TestCase):

    def setUp(self):
        self.b = B.build_board(ACCT, XPROF)
        self.html = R.render_board_html(self.b)

    def test_self_contained(self):
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))
        self.assertIn("</html>", self.html)
        self.assertIn("#1E3A8A", self.html)   # 品牌蓝

    def test_three_screens(self):
        self.assertIn("第一屏 · 一句话结论", self.html)
        self.assertIn("第二屏 · 四层下钻", self.html)
        self.assertIn("第三屏 · 诊断卡处方", self.html)
        self.assertIn("算账", self.html)

    def test_four_coords_rendered(self):
        for c in ("① 环境", "② 行业", "③ 账号", "④ 单条"):
            self.assertIn(c, self.html)

    def test_cost_chips(self):
        self.assertIn("本层成本", self.html)
        self.assertIn("ROI", self.html)

    def test_md(self):
        md = R.render_board_md(self.b)
        self.assertIn("# 元板", md)
        self.assertIn("① 环境", md)
        self.assertIn("算账", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)

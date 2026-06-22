"""commercial_data · 离线测试 · 零网络 · 零 API 调用。

覆盖：
  - 品类佣金率查表（命中 / 兜底 / 区间合理性）
  - 赛道 GMV 档（命中 / 未知 / 诚实标 warning）
  - 星图报价估算（公式正确 / 保底价 / 边界零粉 / 赛道 CPM 差异）
  - 比价骨架降级（available=False · 含 mock_example）
  - 渲染段（含 ✅ 关键词 / 🔴 黑盒诚实标 / 投喂补充分支）
"""
import unittest

from app.services.commercial_data import (
    category_commission,
    category_gmv_tier,
    xingtu_price_estimate,
    price_compare,
    render_commercial_data_section,
)


class TestCategoryCommission(unittest.TestCase):

    def test_meizhuang_in_range(self):
        r = category_commission("美妆")
        self.assertEqual(r["category"], "美妆")
        self.assertGreaterEqual(r["rate_low_pct"], 5.0)
        self.assertLessEqual(r["rate_high_pct"], 50.0)
        # 美妆佣金下限应 >= 15%
        self.assertGreaterEqual(r["rate_low_pct"], 15.0)

    def test_shuzi_lower_than_meizhuang(self):
        meizhuang = category_commission("美妆")
        shuzi = category_commission("数码")
        self.assertLess(shuzi["rate_high_pct"], meizhuang["rate_low_pct"] + 5)

    def test_fuzzy_match(self):
        # 输入"数码手机"可匹配"数码"
        r = category_commission("数码手机")
        self.assertIn(r["category"], ("数码", "全品类"))

    def test_fallback_quanpinlei(self):
        r = category_commission("赛博朋克小玩意儿")
        self.assertEqual(r["category"], "全品类")
        self.assertGreaterEqual(r["rate_low_pct"], 5.0)

    def test_has_source_and_note(self):
        r = category_commission("食品")
        self.assertIn("精选联盟", r["source"])
        self.assertIsInstance(r["note"], str)
        self.assertTrue(len(r["note"]) > 10)

    def test_matched_input_preserved(self):
        r = category_commission("  母婴 ")
        self.assertEqual(r["matched_input"], "  母婴 ")


class TestCategoryGmvTier(unittest.TestCase):

    def test_meizhuang_s_grade(self):
        r = category_gmv_tier("美妆")
        self.assertEqual(r["tier"], "S级")
        self.assertEqual(r["category"], "美妆")   # 品类名在 category 字段

    def test_zhishifuji_s_plus(self):
        r = category_gmv_tier("知识付费")
        self.assertIn("S", r["tier"])

    def test_unknown_category(self):
        r = category_gmv_tier("外星蔬菜赛道")
        self.assertEqual(r["tier"], "未知")
        self.assertIn("暂无", r["desc"])

    def test_warning_always_present(self):
        r = category_gmv_tier("服饰")
        self.assertIsInstance(r["warning"], str)
        self.assertGreater(len(r["warning"]), 5)

    def test_source_present_for_known(self):
        r = category_gmv_tier("家居")
        self.assertIn("艾瑞", r["source"])

    def test_chan_mama_honesty_in_warning(self):
        r = category_gmv_tier("美妆")
        # 合规红线：蝉妈妈类数据只作方向参考
        self.assertIn("方向参考", r["warning"])


class TestXingtuPriceEstimate(unittest.TestCase):

    def test_zero_follower(self):
        r = xingtu_price_estimate(0)
        self.assertEqual(r["price_low_cny"], 0.0)
        self.assertEqual(r["price_high_cny"], 0.0)

    def test_price_low_lte_high(self):
        r = xingtu_price_estimate(10000, track="美妆")
        self.assertLessEqual(r["price_low_cny"], r["price_high_cny"])

    def test_floor_price_enforced(self):
        # 1 粉丝 × CPM 极低，应取到 floor
        r = xingtu_price_estimate(1, track="美妆")
        self.assertGreater(r["price_low_cny"], 0)

    def test_meizhuang_cpm_higher_than_jiaju(self):
        meizhuang = xingtu_price_estimate(100000, track="美妆")
        jiaju = xingtu_price_estimate(100000, track="家居")
        self.assertGreater(meizhuang["price_low_cny"], jiaju["price_low_cny"])

    def test_default_track_used_when_unknown(self):
        r = xingtu_price_estimate(50000, track="神秘赛道XYZ")
        self.assertIn("通用", r["cpm_track_key"])

    def test_has_calibration_note(self):
        r = xingtu_price_estimate(80000, track="财经")
        self.assertIn("互动率", r["calibration_note"])

    def test_formula_string_present(self):
        r = xingtu_price_estimate(30000)
        self.assertIn("30,000", r["formula"])

    def test_source_is_xingtu(self):
        r = xingtu_price_estimate(50000)
        self.assertIn("星图", r["source"])


class TestPriceCompare(unittest.TestCase):

    def test_mvp_returns_unavailable(self):
        r = price_compare("iPhone 16 Pro 256G")
        self.assertFalse(r["available"])

    def test_product_name_preserved(self):
        r = price_compare("某款美妆产品")
        self.assertEqual(r["product_name"], "某款美妆产品")

    def test_note_mentions_api(self):
        r = price_compare("AJ球鞋")
        self.assertIn("慢慢买", r["note"])
        self.assertIn("vault", r["note"])

    def test_mock_example_has_expected_keys(self):
        r = price_compare("test")
        ex = r["mock_example"]
        self.assertIn("current_price_cny", ex)
        self.assertIn("lowest_30d_cny", ex)
        self.assertIn("vs_avg_pct", ex)

    def test_key_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            price_compare("某商品", _api_key="fake-key-xyz")


class TestRenderCommercialDataSection(unittest.TestCase):

    ACCT_MID = {"nickname": "测试账号", "follower": 50000}
    ACCT_SMALL = {"nickname": "小号", "follower": 800}

    def test_render_has_section_header(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("商业数据参考", md)

    def test_render_has_commission(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("佣金率", md)
        self.assertIn("美妆", md)

    def test_render_has_gmv_tier(self):
        md = render_commercial_data_section(self.ACCT_MID, "服饰")
        self.assertIn("S级", md)

    def test_render_has_xingtu_estimate_for_big_account(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("50,000", md)
        self.assertIn("¥", md)

    def test_render_small_account_no_xingtu(self):
        md = render_commercial_data_section(self.ACCT_SMALL, "美妆")
        # 800粉不给报价·给积累建议
        self.assertIn("粉丝积累", md)

    def test_render_has_blackbox_honesty(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("🔴", md)
        self.assertIn("黑盒", md)
        self.assertIn("真实销量", md)

    def test_render_chan_mama_warning(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("方向参考", md)

    def test_render_price_compare_mentioned(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("慢慢买", md)

    def test_render_no_biz_data_shows_cta(self):
        md = render_commercial_data_section(self.ACCT_MID, "美妆")
        self.assertIn("投喂补", md)

    def test_render_with_biz_data(self):
        biz = {"近7日GMV": "12万", "完播率": "28%"}
        md = render_commercial_data_section(self.ACCT_MID, "美妆", biz_data=biz)
        self.assertIn("12万", md)
        self.assertIn("28%", md)
        self.assertIn("投喂数据", md)

    def test_render_data_source_footer(self):
        md = render_commercial_data_section(self.ACCT_MID, "知识付费")
        self.assertIn("精选联盟", md)
        self.assertIn("巨量星图", md)

    def test_render_empty_account_safe(self):
        md = render_commercial_data_section({}, "美妆")
        # 不抛异常·给出合理输出
        self.assertIn("商业数据参考", md)

    def test_render_unknown_track_fallback(self):
        md = render_commercial_data_section(self.ACCT_MID, "神秘小众赛道")
        # 兜底：给全品类佣金·未知GMV
        self.assertIn("商业数据参考", md)
        self.assertIn("暂无", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)

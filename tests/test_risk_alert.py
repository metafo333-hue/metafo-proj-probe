"""risk_alert.py 离线测试 · 零网络 · 零 LLM · $0

覆盖：
  - scan_risks: 行业切红线库（医疗/财经查·餐饮不查证券资质）
  - 三级分级（医疗缺资质🔴 / 夸大词🟡 / 结构性🟢）
  - 致命置顶排序
  - 三轴升降级（中年失业全压单号升级·起号期限流降级）
  - 黑盒诚实（原创度 is_blackbox·只提示不定论）
  - 防玄学注脚（possibility 概率非必然·source 有据·时效声明）
  - render_risk_section: 致命置顶 + 空输入优雅降级（不吓唬）
"""
import unittest

from app.services.risk_alert import (
    scan_risks,
    render_risk_section,
    _industry_of,
    _FATAL, _WARNING, _NOTICE,
)

# 医疗号·含红线词「疗效」
MEDICAL = {
    "nickname": "老中医养生堂",
    "follower": 20000,
    "signature": "祖传秘方·根治各种慢性病·疗效显著",
    "avg_like": 500,
    "max_like": 1200,
    "hashtags": ["健康", "养生"],
}

# 财经号·含红线词「荐股/稳赚」
FINANCE = {
    "nickname": "财富自由导师",
    "follower": 50000,
    "signature": "每日荐股·稳赚不赔·带你财富自由",
    "avg_like": 800,
    "max_like": 3000,
    "hashtags": ["财经", "投资"],
}

# 餐饮号·含通用夸大词「最好/第一」但无红线行业资质问题
RESTAURANT = {
    "nickname": "全城第一家",
    "follower": 6000,
    "signature": "全城最好吃的火锅·第一名",
    "avg_like": 200,
    "max_like": 2000,   # 单一爆款·结构性
    "hashtags": ["美食", "探店"],
}

# 干净号·无风险信号
CLEAN = {
    "nickname": "日常记录",
    "follower": 3000,
    "signature": "分享我的生活日常",
    "avg_like": 100,
    "max_like": 150,
    "hashtags": ["日常", "vlog"],
}


class TestIndustryDetect(unittest.TestCase):
    def test_medical_industry(self):
        self.assertEqual(_industry_of(MEDICAL), "医疗")

    def test_finance_industry(self):
        self.assertEqual(_industry_of(FINANCE), "财经")

    def test_restaurant_industry(self):
        self.assertEqual(_industry_of(RESTAURANT), "餐饮")


class TestScanRisks(unittest.TestCase):
    def test_medical_redline_fatal(self):
        """医疗号缺资质 + 命中红线词 → 🔴致命。"""
        findings = scan_risks(MEDICAL)
        ban = [f for f in findings if f["risk_type"] == "ban_redline"]
        self.assertTrue(ban)
        self.assertEqual(ban[0]["level"], _FATAL)
        self.assertEqual(ban[0]["possibility"], "high")
        self.assertIn("疗效", str(ban[0]["evidence"]))

    def test_finance_redline_fatal(self):
        findings = scan_risks(FINANCE)
        ban = [f for f in findings if f["risk_type"] == "ban_redline"]
        self.assertTrue(ban)
        self.assertEqual(ban[0]["level"], _FATAL)

    def test_restaurant_no_securities_check(self):
        """不误报：餐饮号不查证券资质·不应出财经红线。"""
        findings = scan_risks(RESTAURANT)
        ban = [f for f in findings if f["risk_type"] == "ban_redline"]
        # 餐饮无强资质红线库 → 不应有 ban_redline fatal
        self.assertFalse([f for f in ban if f["level"] == _FATAL])

    def test_restaurant_generic_exaggeration_warning(self):
        """餐饮号夸大词「最好/第一」→ 限流🟡（成长期·非降级·非致命）。"""
        findings = scan_risks(RESTAURANT, stage="成长期")
        flagged = [f for f in findings if f["risk_type"] == "limit_flow"
                   and f["evidence"].get("hit_keywords")]
        self.assertTrue(flagged)
        self.assertEqual(flagged[0]["level"], _WARNING)
        self.assertNotEqual(flagged[0]["level"], _FATAL)

    def test_fatal_sorted_to_top(self):
        """致命风险排第一。"""
        findings = scan_risks(MEDICAL)
        self.assertEqual(findings[0]["level"], _FATAL)

    def test_blackbox_originality_honest(self):
        """搬运/原创度黑盒 → is_blackbox 标记·只提示不定论。"""
        findings = scan_risks(CLEAN)
        bb = [f for f in findings if f.get("is_blackbox")]
        self.assertTrue(bb)
        self.assertIn("黑盒", bb[0]["caveat"])

    def test_structural_single_burst(self):
        """单一爆款（max≫avg）→ 结构性风险。"""
        findings = scan_risks(RESTAURANT)
        st = [f for f in findings if f["risk_type"] == "structural"]
        self.assertTrue(st)

    def test_midaged_unemployed_escalation(self):
        """中年失业 + 结构性 → 升级 warning（全压单号·容错极短）。"""
        base = scan_risks(RESTAURANT, persona="应届生")
        mid = scan_risks(RESTAURANT, persona="中年失业")
        st_base = [f for f in base if f["risk_type"] == "structural"][0]
        st_mid = [f for f in mid if f["risk_type"] == "structural"][0]
        self.assertEqual(st_base["level"], _NOTICE)
        self.assertEqual(st_mid["level"], _WARNING)

    def test_coldstart_limitflow_downgrade(self):
        """起号期限流 → 降级 notice + 附「冷启动正常」解释（防误判流失）。"""
        normal = scan_risks(RESTAURANT, stage="成熟期")
        cold = scan_risks(RESTAURANT, stage="起号期")
        lf_normal = [f for f in normal if f["risk_type"] == "limit_flow"
                     and f["evidence"].get("hit_keywords")]
        lf_cold = [f for f in cold if f["risk_type"] == "limit_flow"
                   and f["evidence"].get("hit_keywords")]
        self.assertEqual(lf_normal[0]["level"], _WARNING)
        self.assertEqual(lf_cold[0]["level"], _NOTICE)
        self.assertIn("冷启动", lf_cold[0]["action_advice"])

    def test_every_finding_has_source_and_possibility(self):
        """防玄学：每条风险带 source（有据）+ possibility（概率非必然）。"""
        for acct in (MEDICAL, FINANCE, RESTAURANT, CLEAN):
            for f in scan_risks(acct):
                self.assertTrue(f.get("source"), f"{acct['nickname']} 缺 source")
                self.assertIn(f["possibility"], ("high", "medium", "low"))
                self.assertTrue(f.get("caveat"))

    def test_sector_decline_homogeneous(self):
        """内容重复率 >40% → 赛道衰退警示。"""
        works = [{"desc": "今天探店火锅"} for _ in range(5)]  # 全同·重复率高
        findings = scan_risks(RESTAURANT, works=works, stage="成熟期")
        sd = [f for f in findings if f["risk_type"] == "sector_decline"]
        self.assertTrue(sd)


class TestRenderRiskSection(unittest.TestCase):
    def test_render_fatal_top(self):
        """致命风险置顶·先解决再谈增长。"""
        md = render_risk_section(MEDICAL)
        self.assertIn("🔴 致命风险", md)
        idx_fatal = md.index("🔴 致命风险")
        # 致命段在提示段之前
        if "🟢 提示" in md:
            self.assertLess(idx_fatal, md.index("🟢 提示"))

    def test_render_possibility_not_certainty(self):
        """防玄学：全程「可能性/概率非必然」·禁「一定被封」。"""
        md = render_risk_section(FINANCE)
        self.assertIn("可能性", md)
        self.assertIn("概率不是必然", md)
        self.assertNotIn("一定会被封", md)

    def test_render_time_validity(self):
        """时效声明：以平台最新规则为准。"""
        md = render_risk_section(MEDICAL)
        self.assertIn("以抖音最新规则为准", md)

    def test_render_clean_no_scare(self):
        """干净号 → 不吓唬·友好提示（§五没有红线则跳过）。"""
        md = render_risk_section(CLEAN)
        self.assertNotIn("🔴 致命风险", md)

    def test_render_industry_top_risk(self):
        """报告点明该行业第一高危。"""
        md = render_risk_section(MEDICAL)
        self.assertIn("封号红线", md)

    def test_render_empty_findings_graceful(self):
        """显式传空 findings → 不崩。"""
        md = render_risk_section(CLEAN, findings=[])
        self.assertIn("没扫到明显风险", md)


if __name__ == "__main__":
    unittest.main()

"""account_report v5 完整测试 · 离线 · 真数据 fixture · $0 · 零网络。

覆盖应具备的全部功能:
  段结构 / 说人话 / 真实引用 / 反抄袭 / 诚实标注 /
  business识别+叙事自适应 / track分类 /
  L2多条找规律 / L2缺失诚实标注 / L3账号判断(生命周期/护城河) /
  ②事实核查 + ⑥合规 / 边界健壮性。
两类 fixture 对照:个人号(@芊妤·女性成长·无资质声称) vs B2B号(魔芋·产业带货·有声称+works)。
"""
import unittest

from app.services.account_report import (
    build_report, _track, _is_business, _analyze_works,
)

# —— fixture 1: 个人号(女性成长·@芊妤·277粉·散·简介无资质声称·无works) ——
QIANYU_V = {"title": "是全心全意陪伴孩子，还是花80%在工作上呢？ #孩子事业到底应该怎么选",
            "like": 8, "comment": 2, "share": 1, "collect": 0, "duration_s": 58}
QIANYU_A = {"nickname": "芊妤不是芊妤", "follower": 277, "aweme_count": 19, "works_analyzed": 16,
            "signature": "🔥有一种英雄主义，依然选择热爱生活，珍惜生命。",
            "avg_like": 10, "max_like": 52, "burst_ratio": 4.7, "vertical_score": 0.5,
            "hashtags": ["女性智慧", "女性力量", "努力成为更好的自己", "感情共鸣", "生活感悟"]}

# —— fixture 2: B2B号(产业带货·魔芋·4645粉·不散·有声称+10条works) ——
MOYU_V = {"title": "餐饮门店直供拿货，缩减成本拉高利润 #餐饮供货#源头直供",
          "like": 77, "comment": 8, "share": 1, "collect": 1, "duration_s": 36}
MOYU_A = {"nickname": "北川魔芋姐｜赵娟", "follower": 4645, "aweme_count": 123, "works_analyzed": 20,
          "signature": "专注魔芋36年·源头工厂·非遗第五代传承人·省级龙头企业·餐饮连锁直供·OEM贴牌",
          "avg_like": 105, "max_like": 383, "burst_ratio": 3.6, "vertical_score": 0.7,
          "hashtags": ["魔芋工厂", "餐饮食材", "源头工厂", "餐饮供货", "魔芋代工"]}
MOYU_WORKS = [
    {"desc": "产地好物 #源头工厂 #特色农产", "like": 300, "comment": 15, "collect": 12, "share": 4, "create_time": 1715000000},
    {"desc": "特色农产直供 #源头工厂", "like": 280, "comment": 12, "collect": 10, "share": 3, "create_time": 1715300000},
    {"desc": "源头工厂实拍 #源头工厂", "like": 220, "comment": 9, "collect": 8, "share": 2, "create_time": 1715600000},
    {"desc": "魔芋豆腐做法", "like": 95, "comment": 3, "collect": 1, "share": 0, "create_time": 1716500000},
    {"desc": "今天厂里很忙", "like": 80, "comment": 2, "collect": 1, "share": 0, "create_time": 1716800000},
    {"desc": "餐饮合作案例 #餐饮供货", "like": 60, "comment": 2, "collect": 1, "share": 0, "create_time": 1717200000},
    {"desc": "随便拍拍 #生活", "like": 40, "comment": 1, "collect": 0, "share": 0, "create_time": 1717600000},
    {"desc": "分享日常", "like": 30, "comment": 0, "collect": 0, "share": 0, "create_time": 1717900000},
    {"desc": "随手记录", "like": 25, "comment": 1, "collect": 0, "share": 0, "create_time": 1718100000},
    {"desc": "周末", "like": 20, "comment": 0, "collect": 0, "share": 0, "create_time": 1718300000},
]
AUDIT = {"source_reliability": "C", "confidence_level": "Low", "evidence_strength": "Weak"}


class TestAccountReport(unittest.TestCase):

    # ---- 段结构 + 说人话 + 真实引用 + 反抄袭 + 诚实(承 v2 好断言·适配 v5) ----
    def test_report_structure(self):
        r = build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS)
        for must in ("账号诊断报告", "一句话先说重点", "你现在是什么情况",
                     "藏着的规律", "整体判断", "可信"):
            self.assertIn(must, r, f"报告缺段:{must}")

    def test_plain_language_no_jargon(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertNotIn("vertical_score", r)
        self.assertNotIn("burst_ratio", r)
        self.assertIn("太杂", r)               # 散(0.5)翻译成大白话
        self.assertIn("和你平时差不多", r)      # 8赞 vs 均10 → 大白话

    def test_uses_real_specifics(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("女性智慧", r)            # 真实标签
        self.assertIn("52", r)                  # 自己的爆款样本

    def test_anti_copy_value(self):
        self.assertIn("比抄别人靠谱", build_report(QIANYU_V, QIANYU_A, AUDIT))

    def test_honesty(self):
        r = build_report(QIANYU_V, QIANYU_A, AUDIT)
        self.assertIn("绝不瞎编", r)
        self.assertIn("只看了你一个号", r)
        self.assertIn("真实公开数据", r)

    # ---- business 识别 + 叙事自适应(修魔芋号被判"生活记录/人生纠结"的根因) ----
    def test_business_detection(self):
        self.assertTrue(_is_business(MOYU_A["signature"]))
        self.assertFalse(_is_business(QIANYU_A["signature"]))

    def test_business_narrative_not_personal_template(self):
        r = build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS)
        self.assertIn("产品力", r)
        self.assertNotIn("人生纠结", r)
        self.assertNotIn("生活记录", r)

    def test_personal_narrative(self):
        self.assertIn("真实", build_report(QIANYU_V, QIANYU_A, AUDIT))

    # ---- track 分类 ----
    def test_track_business(self):
        self.assertIn("B2B", _track(MOYU_A["signature"] + " ".join(MOYU_A["hashtags"]))[0])

    def test_track_personal(self):
        self.assertIn("女性", _track(" ".join(QIANYU_A["hashtags"]))[0])

    # ---- L2 多条找规律("一个视频→多个视频") ----
    def test_L2_finds_pattern(self):
        L2 = _analyze_works(MOYU_WORKS, 105)
        self.assertIsNotNone(L2)
        self.assertIn("源头工厂", L2["hot_tags"])   # 高赞集中在源头工厂
        self.assertIsNotNone(L2["trend"])

    def test_L2_in_report(self):
        r = build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS)
        self.assertIn("藏着的规律", r)
        self.assertIn("高赞", r)

    def test_L2_missing_is_honest(self):
        r = build_report(MOYU_V, MOYU_A, AUDIT, works=None)
        self.assertIn("没拿到", r)               # 诚实标注·不假装

    def test_L2_too_few_works(self):
        self.assertIsNone(_analyze_works([{"desc": "x", "like": 1}], 10))

    # ---- L3 账号判断(生命周期/护城河) ----
    def test_L3_lifecycle_coldstart(self):
        self.assertIn("冷启期", build_report(QIANYU_V, QIANYU_A, AUDIT))   # 277 粉

    def test_L3_lifecycle_growth(self):
        self.assertIn("成长期", build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS))  # 4645 粉

    def test_L3_moat(self):
        self.assertIn("护城河", build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS))

    # ---- ②事实核查 + ⑥合规 ----
    def test_fact_check_compliance_when_claims(self):
        r = build_report(MOYU_V, MOYU_A, AUDIT, works=MOYU_WORKS)   # 有"36年/非遗/龙头"
        self.assertIn("晒证据", r)               # ②
        self.assertIn("虚假宣传", r)              # ⑥

    def test_no_fact_check_when_no_claims(self):
        self.assertNotIn("晒证据", build_report(QIANYU_V, QIANYU_A, AUDIT))  # 个人号无资质声称

    # ---- 边界健壮性 ----
    def test_empty_data_robust(self):
        self.assertIn("账号诊断报告", build_report({}, {}, {}))   # 空数据不崩

    def test_missing_fields_robust(self):
        self.assertGreater(len(build_report({"title": "x"}, {"nickname": "y"}, {})), 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)

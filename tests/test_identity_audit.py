"""identity_audit.py 离线自测 · 零网络 · $0。

形象一致性(六信号对齐)+ 自我匹配 + 简介三要素 + 形象分裂检出。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import identity_audit as IA

# 北川魔芋真实资料(高度统一)
UNIFIED = {
    "nickname": "北川魔芋姐｜赵娟",
    "signature": "北川魔芋姐 | 赵娟\n🏭 专注魔芋36年 · 源头工厂\n🌱 北川花魔芋种植基地\n👩‍🍳 非遗魔芋豆腐第五代传承人",
    "ip_location": "IP属地：四川", "unique_id": "beichuanmoyu",
    "industry_tag": "魔芋工厂",
    "content_dna": {"topics": {"top_hashtags": ["源头工厂", "北川魔芋", "魔芋工厂"]}},
    "extra_signals": {"official_comment_words": [{"word": "魔芋", "count": 4},
                                                 {"word": "拿货", "count": 2}]},
    "track_competition": {"keyword": "魔芋工厂"},
}
# 形象分裂(昵称美妆·内容美食)
SPLIT = {
    "nickname": "美妆小仙女",
    "signature": "每天分享美妆护肤",
    "content_dna": {"topics": {"top_hashtags": ["家常菜", "美食教程", "做饭"]}},
    "extra_signals": {"official_comment_words": [{"word": "好吃", "count": 3}]},
    "track_competition": {"keyword": "美食"},
}


class TestIdentity(unittest.TestCase):

    def test_unified_high_consistency(self):
        r = IA.audit_identity(UNIFIED)
        self.assertEqual(r["core_identity"], "魔芋")
        self.assertGreaterEqual(r["consistency"], 80)
        self.assertEqual(r["self_match"], "高度匹配")

    def test_all_profile_collected(self):
        r = IA.audit_identity(UNIFIED)
        p = r["profile"]
        self.assertIn("北川魔芋姐", p["nickname"])
        self.assertIn("36年", p["signature"])
        self.assertEqual(p["ip_location"], "IP属地：四川")

    def test_three_elements(self):
        # 北川:我是谁(姐/传承人)·做什么(魔芋工厂)·凭什么(36年/非遗/第五代)→ 三要素齐
        r = IA.audit_identity(UNIFIED)
        self.assertEqual(r["elements_n"], 3)
        self.assertTrue(r["elements"]["凭什么"])

    def test_trust_confirmed_by_comments(self):
        # 评论"拿货"=B端采购 → 印证"源头工厂"信任状
        r = IA.audit_identity(UNIFIED)
        self.assertIn("印证", r["trust_confirmed"])

    def test_split_identity_detected(self):
        # 昵称美妆·内容美食 → 形象不统一
        r = IA.audit_identity(SPLIT)
        self.assertLess(r["consistency"], 80)
        self.assertIn("不统一", r["self_match"] + r["verdict"])

    def test_advice_present(self):
        r = IA.audit_identity(SPLIT)
        self.assertTrue(r["advice"])

    def test_honest_note(self):
        r = IA.audit_identity(UNIFIED)
        self.assertIn("不编造", r["note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

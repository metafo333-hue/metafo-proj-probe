"""contract_adapter.py 离线自测 · 零网络 · $0。

验证 build_board → MetaForm 契约 doc(8角色齐 / N6无C代号 / 必填角色 / 算账关)。
"""
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import contract_adapter as CA
from app.services import board as B, composite_scores as CS

ACCT = {
    "nickname": "北川魔芋姐｜赵娟", "follower": 4654, "max_follower": 4660,
    "avg_like": 105, "max_like": 383, "burst_ratio": 3.6, "commerce_density": 0.0,
    "vertical_score": 0.7, "industry_tag": "魔芋工厂",
    "signature": "专注魔芋36年·源头工厂·非遗第五代传承人",
    "engagement_structure": {"comment_per_like": 0.235, "collect_per_like": 0.036,
                             "nature": "争议型(高评论)"},
    "content_dna": {"topics": {"top_hashtags": ["源头工厂", "北川魔芋"],
                               "exemplar": {"desc": "产地直供多少钱"}},
                    "best_time": {"best": "晚间18-22"}, "best_duration": {"best": "60-90s"},
                    "next_video_rx": {"steps": ["晚18-22发", "60-90s", "暂不挂车"]}},
    "milestone": {"follower": 4654, "next": {"at": 5000, "gap": 346, "pct": 93.1,
                  "unlock": "接商单起步线", "verdict": "距5000差346粉"}},
    "extra_signals": {"official_comment_words": [{"word": "魔芋", "count": 4},
                                                 {"word": "拿货", "count": 2}]},
}


def _board():
    s = CS.compute_all(ACCT, None)
    c = {"churn": {"title": "掉粉", "severity": "green", "advice": "保持"},
         "pricing": {"title": "报价", "severity": "yellow"},
         "track": {"title": "赛道", "severity": "green"}}
    return B.build_board(ACCT, None, scores=s, cards=c)


class TestContractAdapter(unittest.TestCase):

    def setUp(self):
        self.doc = CA.build_contract_doc(_board())

    def test_structure(self):
        self.assertEqual(self.doc["source"], "metaboard")
        self.assertIn("doc", self.doc)
        self.assertIn("meta", self.doc["doc"])
        self.assertIn("blocks", self.doc["doc"])

    def test_required_roles_present(self):
        roles = {b["role"] for b in self.doc["doc"]["blocks"]}
        for r in ("verdict", "key_issue", "evidence", "actions", "scope"):  # account-diagnosis 必填
            self.assertIn(r, roles)

    def test_exactly_one_verdict(self):
        verdicts = [b for b in self.doc["doc"]["blocks"] if b["role"] == "verdict"]
        self.assertEqual(len(verdicts), 1)   # N1 唯一脊柱

    def test_n6_no_c_codes(self):
        import json
        blob = json.dumps(self.doc, ensure_ascii=False)
        # 客户版禁出 C1/C9 等内部代号(N6)
        self.assertNotIn("C1", blob)
        self.assertNotIn("C9", blob)
        self.assertNotIn("C14", blob)

    def test_accounting_off(self):
        self.assertFalse(self.doc["doc"]["meta"]["show_accounting"])

    def test_meta_scalars(self):
        m = self.doc["doc"]["meta"]
        self.assertEqual(m["subject_name"], "北川魔芋姐｜赵娟")
        self.assertEqual(m["fans"], 4654)
        self.assertEqual(m["compliance"], "数据源合规授权 · 国内不出境")

    def test_evidence_human_labels(self):
        ev = next(b for b in self.doc["doc"]["blocks"] if b["role"] == "evidence")
        labels = [i["label"] for i in ev["items"]]
        self.assertTrue(any("健康" in l for l in labels))   # 人话非代号

    def test_actions_have_priority(self):
        act = next(b for b in self.doc["doc"]["blocks"] if b["role"] == "actions")
        for it in act["items"]:
            self.assertIn("priority", it)    # N4 带优先级


if __name__ == "__main__":
    unittest.main(verbosity=2)

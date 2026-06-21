"""attribution.py 离线测试 · 零 LLM · 零网络 · 确定性统计验证。

覆盖：
  - 正常归因（对照组生效 + 差异提取）
  - 样本不足（<5 条）标"参考·样本不足"
  - 对照组反例：爆款和平款都高频的特征不算候选因子
  - 措辞检查：rendered 结论含"更常出现/相关"，不含"导致/因为"
  - 诚实边界：结论段含"点赞"边界声明
  - 空/无视听数据时不崩溃
  - 置信度分级（高/中/参考）
  - render_attribution_section 各路径正常输出
"""
import unittest
from app.services.attribution import attribute, render_attribution_section


# ─── stub 工厂 ──────────────────────────────────────────────────────────────

def _make_sl(bgm_style: str | None = None, speech_pace: str | None = None,
             color: str | None = None, edit_pace: str | None = None,
             hook: str | None = None, on_screen: str | None = None,
             conf: float = 0.85) -> dict:
    """构造 six_layer stub（conf 统一为合法高置信，单独控字段是否存在）。"""
    def _fv(v):
        return {"v": v, "conf": conf} if v else {"v": "", "conf": 0.0}

    return {
        "auditory": {
            "bgm_style": _fv(bgm_style),
            "bgm_mood": _fv(None),
            "speech_pace": _fv(speech_pace),
            "sound_fx": _fv(None),
        },
        "visual": {
            "quality": _fv(None),
            "color": _fv(color),
            "composition": _fv(None),
            "transition": _fv(None),
            "edit_pace": _fv(edit_pace),
        },
        "text": {"summary": _fv(None)},
        "narrative": {
            "hook": _fv(hook),
            "structure": _fv(None),
            "pacing": _fv(None),
        },
        "persona": {
            "on_screen": _fv(on_screen),
            "style": _fv(None),
            "camera": _fv(None),
        },
        "psychology": {
            "emotion_arc": _fv(None),
            "resonance": _fv(None),
            "hook_point": _fv(None),
        },
        "evidence_ts": [],
    }


def _work(like: int, bgm_style=None, speech_pace=None, color=None,
          edit_pace=None, hook=None, on_screen=None, conf: float = 0.85) -> dict:
    return {"like": like, "six_layer": _make_sl(
        bgm_style=bgm_style, speech_pace=speech_pace, color=color,
        edit_pace=edit_pace, hook=hook, on_screen=on_screen, conf=conf)}


# ─── 典型 fixture：12 条，爆款用"快"剪辑+暖色调，平款用"慢"+"冷色" ──────────

TOP_WORKS = [_work(500, bgm_style="轻快", edit_pace="快", color="暖色调", hook="冲突式") for _ in range(8)]
BOT_WORKS = [_work(20, bgm_style="轻快", edit_pace="慢", color="冷色调", hook="普通") for _ in range(4)]
MIXED_WORKS = TOP_WORKS + BOT_WORKS  # 12 条


class TestAttributeBasic(unittest.TestCase):

    def test_ok_with_enough_samples(self):
        """12 条样本应成功返回 ok=True。"""
        r = attribute(MIXED_WORKS)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["total_n"], 12)
        self.assertGreater(r["top_n"], 0)
        self.assertGreater(r["bot_n"], 0)

    def test_factors_extracted(self):
        """差异特征应被提取（edit_pace/color 有显著差）。"""
        r = attribute(MIXED_WORKS)
        self.assertTrue(r["ok"])
        feat_keys = {f["feature"] for f in r["factors"]}
        # edit_pace: top=快(8/8), bot=慢(4/4) → 差异100% > 阈值
        self.assertIn("visual.edit_pace", feat_keys, "edit_pace 应被归因")
        # color 同理
        self.assertIn("visual.color", feat_keys, "color 应被归因")

    def test_control_group_filters_common_features(self):
        """bgm_style「轻快」在爆款和平款都高频 → 不应进入因子列表（对照组生效）。"""
        r = attribute(MIXED_WORKS)
        self.assertTrue(r["ok"])
        # bgm_style「轻快」两层都高频（top=8/8, bot=4/4 → diff≈0）
        bgm_factors = [f for f in r["factors"]
                       if f["feature"] == "auditory.bgm_style" and f["value"] == "轻快"]
        self.assertEqual(len(bgm_factors), 0,
                         "爆款和平款都高频的特征不应列为候选因子（对照组铁律）")

    def test_factors_sorted_by_diff_desc(self):
        """因子应按差异大小降序排列。"""
        r = attribute(MIXED_WORKS)
        diffs = [f["diff"] for f in r["factors"]]
        self.assertEqual(diffs, sorted(diffs, reverse=True))

    def test_factor_has_all_required_keys(self):
        """每个因子必须含 top_count/bot_count 对照数据（透明可核）。"""
        r = attribute(MIXED_WORKS)
        for f in r["factors"]:
            for key in ("feature", "value", "top_count", "top_n",
                        "bot_count", "bot_n", "diff", "confidence"):
                self.assertIn(key, f, f"因子缺字段 {key}")


class TestSampleInsufficient(unittest.TestCase):

    def test_too_few_samples_returns_error(self):
        """< 5 条时 ok=False，且 error 含样本不足提示。"""
        r = attribute([_work(100), _work(50), _work(10)])
        self.assertFalse(r["ok"])
        self.assertIn("样本量", r.get("error", ""))

    def test_exactly_5_runs_ok(self):
        """恰好 5 条（= _CONF_NONE 阈值）时应成功。"""
        works = [_work(200, edit_pace="快"), _work(150, edit_pace="快"),
                 _work(50), _work(30), _work(10)]
        r = attribute(works)
        self.assertTrue(r["ok"], r)

    def test_small_tier_confidence_label(self):
        """样本量刚刚够（5 条）时置信度应标 '参考·样本不足'（层级各 <4）。"""
        works = [_work(200, edit_pace="快"), _work(150, edit_pace="快"),
                 _work(50, edit_pace="慢"), _work(30, edit_pace="慢"), _work(10)]
        r = attribute(works)
        self.assertTrue(r["ok"])
        # top/bot 各 2 条 → 低于 _CONF_LOW_MARK(4) → 整体 "参考·样本不足"
        self.assertEqual(r["confidence"], "参考·样本不足")


class TestConfidenceLevels(unittest.TestCase):

    def test_high_confidence_with_large_sample(self):
        """爆款和平款各 ≥ 8 条时置信度应为 '置信高'。"""
        top = [_work(300, edit_pace="快", color="暖色调") for _ in range(9)]
        bot = [_work(10, edit_pace="慢", color="冷色调") for _ in range(9)]
        r = attribute(top + bot)
        self.assertTrue(r["ok"])
        self.assertEqual(r["confidence"], "置信高")

    def test_medium_confidence(self):
        """爆款 4+、平款 4+ 时应为 '置信中'。"""
        top = [_work(300, edit_pace="快") for _ in range(5)]
        bot = [_work(10, edit_pace="慢") for _ in range(5)]
        r = attribute(top + bot)
        self.assertTrue(r["ok"])
        self.assertEqual(r["confidence"], "置信中")


class TestHonestBoundary(unittest.TestCase):

    def test_honest_boundary_present(self):
        """归因结果应含诚实边界声明（点赞 ≠ 完播 ≠ 流量）。"""
        r = attribute(MIXED_WORKS)
        self.assertIn("点赞", r.get("honest_boundary", ""))
        self.assertIn("完播", r.get("honest_boundary", ""))

    def test_no_causal_language_in_output(self):
        """归因 dict 不得出现"导致"或"因为"（相关≠因果铁律）。"""
        import json
        r = attribute(MIXED_WORKS)
        serialized = json.dumps(r, ensure_ascii=False)
        self.assertNotIn("导致", serialized)
        self.assertNotIn("因为", serialized)


class TestLowConfidenceField(unittest.TestCase):

    def test_low_conf_field_excluded(self):
        """conf < 0.45 的字段不参与归因（诚实过滤）。"""
        # 构造：爆款全是低置信度的 edit_pace
        low_conf_top = [_work(500, edit_pace="快", conf=0.3) for _ in range(8)]
        normal_bot = [_work(10) for _ in range(4)]
        r = attribute(low_conf_top + normal_bot)
        # 低 conf 字段被过滤，不应出现 edit_pace 因子
        edit_factors = [f for f in (r.get("factors") or []) if f["feature"] == "visual.edit_pace"]
        self.assertEqual(len(edit_factors), 0, "低置信字段不应参与归因")


class TestRenderAttributionSection(unittest.TestCase):

    def test_render_ok_path(self):
        """正常归因 → rendered 含对照数据格式（X/N vs 平款 X/N）。"""
        r = attribute(MIXED_WORKS)
        md = render_attribution_section(r)
        self.assertIn("爆款视听公式", md)
        self.assertIn("vs 平款", md)

    def test_render_no_causal_wording(self):
        """rendered 段不含因果措辞（"导致/因为"）。"""
        r = attribute(MIXED_WORKS)
        md = render_attribution_section(r)
        self.assertNotIn("导致", md)
        self.assertNotIn("因为", md)

    def test_render_contains_correlation_wording(self):
        """rendered 段含相关性措辞（防玄学铁律②）。"""
        r = attribute(MIXED_WORKS)
        md = render_attribution_section(r)
        # 应含"更常出现"或"相关"
        self.assertTrue("更常出现" in md or "相关" in md,
                        "结论段须用相关性措辞，不用因果")

    def test_render_contains_honest_boundary(self):
        """rendered 段含点赞诚实边界（防玄学铁律④）。"""
        r = attribute(MIXED_WORKS)
        md = render_attribution_section(r)
        self.assertIn("点赞", md)

    def test_render_insufficient_sample(self):
        """样本不足时 rendered 段含样本不足提示，不崩溃。"""
        r = attribute([_work(100), _work(50)])
        md = render_attribution_section(r)
        self.assertIn("样本", md)

    def test_render_none_input(self):
        """render_attribution_section(None) 不崩溃，返回含提示的字符串。"""
        md = render_attribution_section(None)
        self.assertIsInstance(md, str)
        self.assertGreater(len(md), 0)

    def test_render_confidence_tag_in_factors(self):
        """每个因子行应含置信度标签。"""
        top = [_work(300, edit_pace="快", color="暖色调") for _ in range(6)]
        bot = [_work(10, edit_pace="慢", color="冷色调") for _ in range(6)]
        r = attribute(top + bot)
        md = render_attribution_section(r)
        # 应出现置信度关键词
        has_conf = any(w in md for w in ("置信高", "置信中", "参考·样本不足"))
        self.assertTrue(has_conf, "因子行应含置信度标签")

    def test_render_sample_insufficient_flag_in_line(self):
        """小样本情况下因子行应含"参考·样本不足"。"""
        # 5 条：top=2, bot=2 → 层级 < _CONF_LOW_MARK
        works = [_work(200, edit_pace="快"), _work(150, edit_pace="快"),
                 _work(50, edit_pace="慢"), _work(30, edit_pace="慢"), _work(10)]
        r = attribute(works)
        md = render_attribution_section(r)
        self.assertIn("参考·样本不足", md)

    def test_render_no_factors_path(self):
        """无差异特征（全部均质）时 rendered 段含"没找到"提示，不崩溃。"""
        # 爆款和平款用完全相同的特征
        uniform = [_work(like, bgm_style="轻快", edit_pace="中",
                         color="暖色调", hook="普通") for like in [300, 200, 100, 50, 20, 10]]
        r = attribute(uniform)
        md = render_attribution_section(r)
        self.assertIsInstance(md, str)
        # 没有差异因子时应给出"没找到"提示
        if not r.get("factors"):
            self.assertIn("没找到", md)


class TestEdgeCases(unittest.TestCase):

    def test_works_without_six_layer(self):
        """作品缺少 six_layer 不崩溃（归因跳过该条）。"""
        works = [{"like": 500}, {"like": 400}] + [_work(10) for _ in range(5)]
        try:
            r = attribute(works)
            self.assertIsInstance(r, dict)
        except Exception as e:  # noqa: BLE001
            self.fail(f"缺 six_layer 不应崩溃: {e}")

    def test_empty_input(self):
        """空列表不崩溃，返回 ok=False。"""
        r = attribute([])
        self.assertFalse(r["ok"])

    def test_all_zero_likes(self):
        """全零点赞不崩溃（边界：分层逻辑不依赖非零）。"""
        works = [_work(0, edit_pace="快") for _ in range(6)]
        r = attribute(works)
        self.assertIsInstance(r, dict)
        self.assertTrue(r["ok"])


if __name__ == "__main__":
    unittest.main()

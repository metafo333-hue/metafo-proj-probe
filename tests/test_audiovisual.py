"""audiovisual 视听六层 · 离线测试 · 零网络 · $0。

只测确定性逻辑:JSON 解析容错 / 低 conf 过滤 / 渲染说人话+诚实声明。
真实调用(analyze_audiovisual 调 Qwen3-Omni)走手测 `python -m app.services.audiovisual <url>`。
analyze_by_layers 真实调用同理走手测:SILICONFLOW_API_KEY=xxx python -m app.services.audiovisual <url> layers
"""
import unittest

from app.services.audiovisual import (
    _parse_six_layer, _fld, render_av_section, LAYERS,
    fetch_video_as_data_uri, analyze_douyin_video,
    _parse_reasoning_layer, _merge_perception_reasoning, analyze_by_layers,
)

# —— fixture: 一份合法六层(mov_bbb 实测形态) ——
SIX = {
    "auditory": {"bgm_style": {"v": "轻音乐", "conf": 0.9}, "bgm_mood": {"v": "轻松", "conf": 0.9},
                 "speech_pace": {"v": "无口播", "conf": 1.0}, "sound_fx": {"v": "鸟叫", "conf": 0.3}},
    "visual": {"quality": {"v": "高", "conf": 0.9}, "color": {"v": "明亮", "conf": 0.9},
               "composition": {"v": "中心", "conf": 0.8}, "transition": {"v": "淡入", "conf": 0.8},
               "edit_pace": {"v": "慢", "conf": 0.9}},
    "text": {"summary": {"v": "兔子与蝴蝶嬉戏", "conf": 0.9}},
    "narrative": {"hook": {"v": "兔子追蝴蝶", "conf": 0.9}, "structure": {"v": "线性", "conf": 0.9},
                  "pacing": {"v": "慢", "conf": 0.9}},
    "persona": {"on_screen": {"v": "有", "conf": 0.9}, "style": {"v": "卡通", "conf": 0.9},
                "camera": {"v": "固定", "conf": 0.7}},
    "psychology": {"emotion_arc": {"v": "平稳", "conf": 0.8}, "resonance": {"v": "童趣", "conf": 0.9},
                   "hook_point": {"v": "胖兔子", "conf": 0.8}},
    "evidence_ts": ["00:00-00:03"],
}


class TestAudiovisual(unittest.TestCase):

    # ---- JSON 解析容错 ----
    def test_parse_plain_json(self):
        import json
        self.assertIsNotNone(_parse_six_layer(json.dumps(SIX)))

    def test_parse_json_fenced(self):
        import json
        wrapped = "这是分析结果:\n```json\n" + json.dumps(SIX) + "\n```\n完毕"
        d = _parse_six_layer(wrapped)
        self.assertIsNotNone(d)
        self.assertIn("auditory", d)

    def test_parse_garbage_returns_none(self):
        self.assertIsNone(_parse_six_layer("我无法分析这个视频"))
        self.assertIsNone(_parse_six_layer(""))
        self.assertIsNone(_parse_six_layer(None))

    def test_parse_missing_core_layers_rejected(self):
        # 缺听觉/视觉两层 = 无效(六层最低门)
        self.assertIsNone(_parse_six_layer('{"text":{"summary":{"v":"x","conf":1}}}'))

    # ---- 低 conf 过滤(对冲 <50% 天花板) ----
    def test_fld_filters_low_conf(self):
        self.assertIsNone(_fld(SIX["auditory"], "sound_fx", min_conf=0.45))  # conf 0.3 被滤
        self.assertIsNotNone(_fld(SIX["auditory"], "bgm_style", min_conf=0.45))  # conf 0.9 保留

    def test_fld_shows_conf_percent(self):
        self.assertIn("90%", _fld(SIX["auditory"], "bgm_style"))

    def test_fld_missing_field(self):
        self.assertIsNone(_fld(SIX["auditory"], "nonexistent"))
        self.assertIsNone(_fld({}, "x"))

    # ---- 渲染说人话 ----
    def test_render_has_layers(self):
        md = render_av_section(SIX)
        self.assertIn("听觉", md)
        self.assertIn("配乐", md)
        self.assertIn("视觉", md)

    def test_render_filters_low_conf_item(self):
        md = render_av_section(SIX, min_conf=0.45)
        self.assertNotIn("鸟叫", md)        # sound_fx conf 0.3 略去
        self.assertIn("轻音乐", md)          # bgm_style conf 0.9 保留

    def test_render_has_honesty_disclaimer(self):
        md = render_av_section(SIX)
        self.assertIn("准确率有限", md)       # 诚实声明·不作硬结论
        self.assertIn("置信度", md)

    def test_render_evidence_ts(self):
        self.assertIn("00:00-00:03", render_av_section(SIX))

    def test_render_empty_safe(self):
        self.assertEqual(render_av_section(None), "")
        self.assertEqual(render_av_section({}), "")

    # ---- 下载中转边界(离线·不触网) ----
    def test_fetch_empty_urls(self):
        out = fetch_video_as_data_uri([])
        self.assertFalse(out["ok"])

    def test_analyze_douyin_empty_urls_no_omni_call(self):
        # 无直链 → 下载失败 → 不应调 Omni(返回下载失败)
        out = analyze_douyin_video([])
        self.assertFalse(out["ok"])

    # ---- schema 常量对齐 ----
    def test_layers_constant(self):
        for k in ("auditory", "visual", "text", "narrative", "persona", "psychology"):
            self.assertIn(k, LAYERS)



# ──────────────────────────────────────────────────────────────
# 生产形态 analyze_by_layers 的离线单元测试
# ──────────────────────────────────────────────────────────────

# 感知层 fixture（Qwen3-Omni 产出·只含 auditory/visual/text/evidence_ts）
PERCEPTION_SIX = {
    "auditory": SIX["auditory"],
    "visual": SIX["visual"],
    "text": SIX["text"],
    "evidence_ts": SIX["evidence_ts"],
}

# 推理层 fixture（DeepSeek-V3 产出·只含 narrative/persona/psychology）
REASONING_SIX = {
    "narrative": SIX["narrative"],
    "persona": SIX["persona"],
    "psychology": SIX["psychology"],
}

import json as _json


class TestAnalyzeByLayers(unittest.TestCase):

    # ── _parse_reasoning_layer 解析容错 ──
    def test_parse_reasoning_plain_json(self):
        out = _parse_reasoning_layer(_json.dumps(REASONING_SIX))
        self.assertIsNotNone(out)
        self.assertIn("narrative", out)

    def test_parse_reasoning_fenced(self):
        wrapped = "分析完毕:\n```json\n" + _json.dumps(REASONING_SIX) + "\n```"
        out = _parse_reasoning_layer(wrapped)
        self.assertIsNotNone(out)
        self.assertIn("persona", out)

    def test_parse_reasoning_garbage_returns_none(self):
        self.assertIsNone(_parse_reasoning_layer("无法分析"))
        self.assertIsNone(_parse_reasoning_layer(""))
        self.assertIsNone(_parse_reasoning_layer(None))

    def test_parse_reasoning_missing_all_three_rejected(self):
        # 缺 narrative/persona/psychology 三层 = 无效
        self.assertIsNone(_parse_reasoning_layer('{"auditory":{"bgm_style":{"v":"x","conf":1}}}'))

    def test_parse_reasoning_partial_accepted(self):
        # 只有一层也接受（宽容·推理层可能部分输出）
        partial = {"narrative": REASONING_SIX["narrative"]}
        out = _parse_reasoning_layer(_json.dumps(partial))
        self.assertIsNotNone(out)

    # ── _merge_perception_reasoning 合并 ──
    def test_merge_produces_all_six_keys(self):
        merged = _merge_perception_reasoning(PERCEPTION_SIX, REASONING_SIX)
        for k in LAYERS:
            self.assertIn(k, merged)
        self.assertIn("evidence_ts", merged)

    def test_merge_preserves_auditory(self):
        merged = _merge_perception_reasoning(PERCEPTION_SIX, REASONING_SIX)
        self.assertEqual(merged["auditory"], SIX["auditory"])

    def test_merge_preserves_narrative(self):
        merged = _merge_perception_reasoning(PERCEPTION_SIX, REASONING_SIX)
        self.assertEqual(merged["narrative"], SIX["narrative"])

    def test_merge_empty_reasoning_tolerant(self):
        # 推理层全空 → 容错填空 dict，不崩
        merged = _merge_perception_reasoning(PERCEPTION_SIX, {})
        self.assertEqual(merged["narrative"], {})
        self.assertEqual(merged["persona"], {})
        self.assertEqual(merged["psychology"], {})

    def test_merge_evidence_ts_from_perception(self):
        merged = _merge_perception_reasoning(PERCEPTION_SIX, REASONING_SIX)
        self.assertEqual(merged["evidence_ts"], ["00:00-00:03"])

    # ── 合并产物可直接复用 render_av_section ──
    def test_merged_renderable(self):
        merged = _merge_perception_reasoning(PERCEPTION_SIX, REASONING_SIX)
        md = render_av_section(merged)
        self.assertIn("听觉", md)
        self.assertIn("视觉", md)
        self.assertIn("共鸣点", md)  # psychology.resonance
        self.assertIn("00:00-00:03", md)

    # ── analyze_by_layers 无 key → 立即返回错误 ──
    def test_analyze_by_layers_no_key(self):
        import os
        orig = os.environ.pop("SILICONFLOW_API_KEY", None)
        try:
            out = analyze_by_layers("https://example.com/test.mp4", sf_key=None)
            self.assertFalse(out["ok"])
            self.assertIn("SILICONFLOW_API_KEY", out["error"])
        finally:
            if orig is not None:
                os.environ["SILICONFLOW_API_KEY"] = orig


if __name__ == "__main__":
    unittest.main(verbosity=2)

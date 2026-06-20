"""test_l0_rules_fetch.py — l0_rules_fetch 解析逻辑离线测试。

全程 mock HTML·零网络·$0。
测试分组：
  A. HTML 去标签 / 正文提取
  B. forbidden_zones 提取（正则命中/未命中）
  C. AI 标注规则提取
  D. 音乐版权规则提取
  E. merge_results 合并与种子补全
  F. _load_rules_override 文件加载与 schema 校验
  G. 边界 / 健壮性（空页·损坏 JSON·缺字段）
"""
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import sys
import os

# 确保 probe root 在路径上
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.l0_rules_fetch import (
    _extract_ai_label_rule,
    _extract_forbidden_zones,
    _extract_music_rule,
    _strip_html,
    merge_results,
    parse_page,
    _SEED_FORBIDDEN,
    _SEED_AI_LABEL,
    _SEED_MUSIC,
)
from app.services.l0_environment import _load_rules_override, _RULES_OVERRIDE_FILE


# ── 测试 HTML 片段 ──────────────────────────────────────────────────────────

_HTML_DOUYIN_TRUST = """
<!DOCTYPE html>
<html>
<head><title>抖音安全与信任中心</title></head>
<body>
<script>window.__data = {};</script>
<style>body { font-family: sans-serif; }</style>
<div class="main">
  <h1>社区规范</h1>
  <section>
    <h2>违禁内容类型</h2>
    <ul>
      <li>涉政敏感内容，包括违反宪法原则、危害国家安全的内容</li>
      <li>虚假宣传，夸大功效，欺骗消费者</li>
      <li>无资质做医疗建议或金融荐股行为</li>
      <li>色情低俗内容，包含性暗示的裸露展示</li>
      <li>赌博博彩相关信息</li>
      <li>散布谣言和虚假消息</li>
      <li>网络暴力、人肉搜索等行为</li>
    </ul>
  </section>
  <section>
    <h2>AI 内容规范</h2>
    <p>AI 生成内容须显著标注，未标注 AI 内容将受到限流处理。</p>
  </section>
  <section>
    <h2>音乐版权</h2>
    <p>背景音乐应使用平台曲库中的授权音乐，盗用版权音乐素材将导致限流或下架。</p>
  </section>
</div>
</body>
</html>
"""

_HTML_EMPTY_BODY = "<html><head></head><body></body></html>"

_HTML_NO_VIOLATIONS = """
<html><body>
<p>欢迎来到我们的平台，这里只有美好的内容。</p>
</body></html>
"""

_HTML_PARTIAL = """
<html><body>
<p>AI 生成内容须显著标注，否则限流。</p>
</body></html>
"""

_HTML_WECHAT_CHANNELS = """
<!DOCTYPE html>
<html>
<head><title>微信视频号营销规范</title></head>
<body>
<article>
  <h1>微信视频号视频/直播营销信息发布规范</h1>
  <p>禁止发布虚假宣传和夸大宣传内容，违者将受到处罚。</p>
  <p>音频音乐版权须合法授权，未经授权使用版权音乐将被下架。</p>
  <p>AI 生成的内容需要显著标注标识，否则可能被限流。</p>
</article>
</body>
</html>
"""

# ── 组 A: HTML 去标签 ────────────────────────────────────────────────────────

class TestStripHtml(unittest.TestCase):

    def test_removes_script_and_style(self):
        result = _strip_html(_HTML_DOUYIN_TRUST)
        self.assertNotIn("<script>", result)
        self.assertNotIn("<style>", result)
        self.assertNotIn("window.__data", result)
        self.assertNotIn("font-family", result)

    def test_removes_tags(self):
        result = _strip_html("<p>Hello <b>World</b></p>")
        self.assertEqual(result, "Hello World")

    def test_decodes_html_entities(self):
        result = _strip_html("&amp; &lt; &gt; &nbsp;")
        self.assertIn("&", result)
        self.assertIn("<", result)
        self.assertIn(">", result)

    def test_empty_html(self):
        self.assertEqual(_strip_html(""), "")

    def test_collapses_whitespace(self):
        result = _strip_html("<p>  lots   of   spaces  </p>")
        self.assertNotIn("  ", result)

    def test_retains_chinese_text(self):
        result = _strip_html(_HTML_DOUYIN_TRUST)
        self.assertIn("违禁内容", result)
        self.assertIn("涉政敏感", result)

# ── 组 B: forbidden_zones 提取 ──────────────────────────────────────────────

class TestExtractForbiddenZones(unittest.TestCase):

    def test_detects_politics(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("涉政敏感", zones)

    def test_detects_false_advertising(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("虚假宣传/夸大功效", zones)

    def test_detects_medical_finance(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("无资质做医疗·金融荐股", zones)

    def test_detects_pornography(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("色情/低俗内容", zones)

    def test_detects_gambling(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("赌博内容", zones)

    def test_detects_rumor(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("散布谣言/虚假消息", zones)

    def test_detects_cyberbullying(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        zones = _extract_forbidden_zones(text)
        self.assertIn("网络暴力/人肉搜索", zones)

    def test_no_false_positives_on_empty(self):
        zones = _extract_forbidden_zones("")
        self.assertEqual(zones, [])

    def test_no_false_positives_on_clean_text(self):
        text = _strip_html(_HTML_NO_VIOLATIONS)
        zones = _extract_forbidden_zones(text)
        self.assertEqual(zones, [])

    def test_no_duplicates(self):
        # 文本中有两处涉政关键词
        text = "涉政敏感 涉政敏感内容 违反宪法"
        zones = _extract_forbidden_zones(text)
        self.assertEqual(zones.count("涉政敏感"), 1)

    def test_wechat_partial_page(self):
        text = _strip_html(_HTML_WECHAT_CHANNELS)
        zones = _extract_forbidden_zones(text)
        self.assertIn("虚假宣传/夸大功效", zones)

# ── 组 C: AI 标注规则 ────────────────────────────────────────────────────────

class TestExtractAiLabelRule(unittest.TestCase):

    def test_finds_ai_label_rule(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        rule = _extract_ai_label_rule(text)
        self.assertIsNotNone(rule)
        self.assertIn("AI", rule)

    def test_finds_ai_label_wechat(self):
        text = _strip_html(_HTML_WECHAT_CHANNELS)
        rule = _extract_ai_label_rule(text)
        self.assertIsNotNone(rule)

    def test_returns_none_when_absent(self):
        text = _strip_html(_HTML_NO_VIOLATIONS)
        rule = _extract_ai_label_rule(text)
        self.assertIsNone(rule)

    def test_returns_none_on_empty(self):
        self.assertIsNone(_extract_ai_label_rule(""))

    def test_snippet_is_reasonable_length(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        rule = _extract_ai_label_rule(text)
        if rule:
            self.assertGreater(len(rule), 5)
            self.assertLess(len(rule), 300)

# ── 组 D: 音乐版权规则 ──────────────────────────────────────────────────────

class TestExtractMusicRule(unittest.TestCase):

    def test_finds_music_rule(self):
        text = _strip_html(_HTML_DOUYIN_TRUST)
        rule = _extract_music_rule(text)
        self.assertIsNotNone(rule)
        self.assertIn("音乐", rule)

    def test_finds_music_rule_wechat(self):
        text = _strip_html(_HTML_WECHAT_CHANNELS)
        rule = _extract_music_rule(text)
        self.assertIsNotNone(rule)

    def test_returns_none_when_absent(self):
        text = _strip_html(_HTML_NO_VIOLATIONS)
        rule = _extract_music_rule(text)
        self.assertIsNone(rule)

    def test_returns_none_on_empty(self):
        self.assertIsNone(_extract_music_rule(""))

# ── 组 E: merge_results ──────────────────────────────────────────────────────

class TestMergeResults(unittest.TestCase):

    def _make_page(self, name: str, zones: list, ai: str | None = None, music: str | None = None):
        return {
            "source": name,
            "text_length": 500,
            "forbidden_zones": zones,
            "ai_label_snippet": ai,
            "music_snippet": music,
            "text_preview": "",
        }

    def test_union_of_forbidden_zones(self):
        pages = [
            self._make_page("p1", ["涉政敏感", "赌博内容"]),
            self._make_page("p2", ["色情/低俗内容", "涉政敏感"]),
        ]
        result = merge_results(pages)
        self.assertIn("涉政敏感", result["forbidden_zones"])
        self.assertIn("赌博内容", result["forbidden_zones"])
        self.assertIn("色情/低俗内容", result["forbidden_zones"])
        # 无重复
        self.assertEqual(len(result["forbidden_zones"]), len(set(result["forbidden_zones"])))

    def test_seed_items_always_present(self):
        """即使页面解析到 0 条，种子的核心 5 条也必须存在"""
        pages = [self._make_page("p1", [])]
        result = merge_results(pages)
        for seed in _SEED_FORBIDDEN:
            self.assertTrue(
                any(seed in z or z in seed for z in result["forbidden_zones"]),
                f"种子条目 '{seed}' 在合并结果中缺失",
            )

    def test_ai_label_first_non_none(self):
        pages = [
            self._make_page("p1", [], ai=None),
            self._make_page("p2", [], ai="AI 内容须标注"),
            self._make_page("p3", [], ai="另一条规则"),
        ]
        result = merge_results(pages)
        self.assertEqual(result["ai_label"], "AI 内容须标注")

    def test_ai_label_none_when_all_absent(self):
        pages = [self._make_page("p1", [], ai=None)]
        result = merge_results(pages)
        self.assertIsNone(result["ai_label"])

    def test_music_first_non_none(self):
        pages = [
            self._make_page("p1", [], music=None),
            self._make_page("p2", [], music="用授权音乐"),
        ]
        result = merge_results(pages)
        self.assertEqual(result["music"], "用授权音乐")

    def test_sources_ok_only_has_pages_with_zones(self):
        pages = [
            self._make_page("found", ["涉政敏感"]),
            self._make_page("empty", []),
        ]
        result = merge_results(pages)
        self.assertIn("found", result["sources_ok"])
        self.assertNotIn("empty", result["sources_ok"])

    def test_empty_pages_list(self):
        result = merge_results([])
        # 应当回退到种子，不崩
        self.assertIsInstance(result["forbidden_zones"], list)
        self.assertIsNone(result["ai_label"])
        self.assertIsNone(result["music"])

# ── 组 F: _load_rules_override ──────────────────────────────────────────────

class TestLoadRulesOverride(unittest.TestCase):

    def _make_valid_json(self, **overrides) -> str:
        base = {
            "schema_version": "1.0",
            "fetched_at": "2026-06-20T08:00:00+00:00",
            "fetch_coverage": "3/4 目标成功",
            "platform": {
                "ai_label": "AI 生成须标注（抓取）",
                "ai_label_from_fetch": True,
                "forbidden_zones": ["涉政敏感", "色情/低俗内容", "赌博内容",
                                    "虚假宣传/夸大功效", "无资质做医疗·金融荐股"],
                "music": "用授权音乐（抓取）",
                "music_from_fetch": True,
            },
        }
        base.update(overrides)
        return json.dumps(base, ensure_ascii=False)

    def test_returns_none_when_file_absent(self):
        with patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=False):
            result = _load_rules_override()
        self.assertIsNone(result)

    def test_loads_valid_file(self):
        json_str = self._make_valid_json()
        with patch("builtins.open", mock_open(read_data=json_str)), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIsNotNone(result)
        self.assertIsInstance(result["forbidden_zones"], list)
        self.assertGreater(len(result["forbidden_zones"]), 0)
        self.assertEqual(result["ai_label"], "AI 生成须标注（抓取）")
        self.assertEqual(result["music"], "用授权音乐（抓取）")

    def test_returns_fetched_at(self):
        json_str = self._make_valid_json()
        with patch("builtins.open", mock_open(read_data=json_str)), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIn("fetched_at", result)
        self.assertIn("2026", result["fetched_at"])

    def test_returns_none_on_corrupt_json(self):
        with patch("builtins.open", mock_open(read_data="{ not valid json {")), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIsNone(result)

    def test_returns_none_when_forbidden_zones_empty(self):
        """schema 不符（forbidden_zones 为空列表）→ None"""
        bad = json.dumps({"platform": {"forbidden_zones": [], "ai_label": "x"}})
        with patch("builtins.open", mock_open(read_data=bad)), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIsNone(result)

    def test_returns_none_when_platform_key_missing(self):
        bad = json.dumps({"schema_version": "1.0"})
        with patch("builtins.open", mock_open(read_data=bad)), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIsNone(result)

    def test_falls_back_to_seed_ai_when_null(self):
        """文件中 ai_label 为 None → 回退种子"""
        json_str = json.dumps({
            "platform": {
                "ai_label": None,
                "forbidden_zones": ["涉政敏感", "赌博内容", "色情/低俗内容",
                                    "虚假宣传/夸大功效", "无资质做医疗·金融荐股"],
                "music": None,
            }
        })
        with patch("builtins.open", mock_open(read_data=json_str)), \
             patch.object(type(_RULES_OVERRIDE_FILE), "exists", return_value=True):
            result = _load_rules_override()
        self.assertIsNotNone(result)
        self.assertEqual(result["ai_label"], _SEED_AI_LABEL)
        self.assertEqual(result["music"], _SEED_MUSIC)

# ── 组 G: 边界 / 健壮性 ─────────────────────────────────────────────────────

class TestRobustness(unittest.TestCase):

    def test_parse_page_empty_html(self):
        result = parse_page("test", _HTML_EMPTY_BODY)
        self.assertIsInstance(result["forbidden_zones"], list)
        self.assertIsNone(result["ai_label_snippet"])
        self.assertIsNone(result["music_snippet"])

    def test_parse_page_zero_length_string(self):
        result = parse_page("test", "")
        self.assertEqual(result["text_length"], 0)

    def test_strip_html_large_script_block(self):
        """大型 script 块不泄漏到文本"""
        html = "<html><body><script>" + "x" * 10000 + "</script><p>正文</p></body></html>"
        result = _strip_html(html)
        self.assertIn("正文", result)
        self.assertNotIn("x" * 100, result)  # script 内容不泄漏

    def test_merge_handles_none_ai_music(self):
        """所有页面 ai/music 为 None 时 merge 不崩"""
        pages = [{"source": "p", "text_length": 0,
                  "forbidden_zones": [], "ai_label_snippet": None,
                  "music_snippet": None, "text_preview": ""}]
        result = merge_results(pages)
        self.assertIsNone(result["ai_label"])
        self.assertIsNone(result["music"])
        self.assertIsInstance(result["forbidden_zones"], list)

    def test_extract_functions_do_not_raise_on_unicode(self):
        """极端 unicode 输入不崩"""
        text = "AI​生成　内容须�标注" * 10
        # 不抛异常即通过
        _extract_ai_label_rule(text)
        _extract_forbidden_zones(text)
        _extract_music_rule(text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

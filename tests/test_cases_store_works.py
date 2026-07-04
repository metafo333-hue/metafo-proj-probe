"""cases_store.py · works.json 落盘自测 · 零网络 · $0。

覆盖元会诊 MetaConsult v2 接缝一(design: 运营报告/metaconsult/
metaconsult-fusion-redesign-v2.0.md §5) —— persist_board 顺带落一份
works.json(原始作品列表)供上层分诊台(triage)离线抽检消费:

  - _persist_works: 有 works → 落盘且内容一致 / works=None|[] → 不落盘(不写空壳)
                     / 写盘异常(目录不存在等) → 吞掉不外抛
  - persist_board: 集成层验证——account 带 works → 同目录出 works.json;
                     account 不带 works → 不出 works.json 但 board.json 等主流程照常;
                     works 含不可 JSON 序列化对象 → works.json 落盘失败被吞·
                     board.json/meta.json/report.md 主流程不受影响。
"""
import json
import os
import pathlib
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROBE_ROOT = os.path.dirname(_HERE)
for _p in [_PROBE_ROOT, os.path.join(os.path.dirname(_PROBE_ROOT), "combo-deep-probe")]:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from app.services import cases_store as CS

WORKS_SAMPLE = [
    {"desc": "北川魔芋源头直供", "create_time": 1719999999, "duration_ms": 45000,
     "like": 105, "comment": 23, "share": 4, "collect": 12},
    {"desc": "多少钱一斤", "create_time": 1720086399, "duration_ms": 38000,
     "like": 88, "comment": 15, "share": 2, "collect": 9},
]

BOARD_MIN = {"headline": {}, "layers": {}}   # 无 contract_doc → _render_contract_html 短路返回 None


class TestPersistWorksHelper(unittest.TestCase):
    """直测 _persist_works(cdir, works) —— 不牵扯 _CASES/_IDX/_REG 全局路径。"""

    def test_works_present_writes_matching_content(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = pathlib.Path(td)
            CS._persist_works(cdir, WORKS_SAMPLE)
            fp = cdir / "works.json"
            self.assertTrue(fp.exists())
            self.assertEqual(json.loads(fp.read_text("utf-8")), WORKS_SAMPLE)

    def test_works_none_no_file(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = pathlib.Path(td)
            CS._persist_works(cdir, None)
            self.assertFalse((cdir / "works.json").exists())

    def test_works_empty_list_no_file(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = pathlib.Path(td)
            CS._persist_works(cdir, [])
            self.assertFalse((cdir / "works.json").exists())

    def test_write_failure_swallowed(self):
        # cdir 的父目录不存在 → write_text 触发 FileNotFoundError → 必须被吞掉·不外抛。
        with tempfile.TemporaryDirectory() as td:
            cdir = pathlib.Path(td) / "no-such-subdir"
            try:
                CS._persist_works(cdir, WORKS_SAMPLE)   # 不应抛异常
            except Exception as e:  # noqa: BLE001
                self.fail(f"_persist_works 不应向外抛异常,实际抛出: {e!r}")
            self.assertFalse((cdir / "works.json").exists())


class TestPersistBoardWorksIntegration(unittest.TestCase):
    """集成层:通过公开入口 persist_board() 验证 works.json 与 board.json 同目录落盘。

    monkeypatch _CASES/_IDX/_REG 到临时目录(禁污染真实 probe/data/cases);
    monkeypatch _refresh_embed 为空操作(禁触发真实 hub/build_embed.py 子进程)。
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        td = pathlib.Path(self._tmp.name)
        self._orig_cases = CS._CASES
        self._orig_idx = CS._IDX
        self._orig_reg = CS._REG
        self._orig_refresh = CS._refresh_embed
        CS._CASES = td / "cases"
        CS._IDX = CS._CASES / "index.json"
        CS._REG = CS._CASES / "video-sources-registry.json"   # 不存在 → _register 早退
        CS._refresh_embed = lambda: None

    def tearDown(self):
        CS._CASES = self._orig_cases
        CS._IDX = self._orig_idx
        CS._REG = self._orig_reg
        CS._refresh_embed = self._orig_refresh
        self._tmp.cleanup()

    def test_account_with_works_produces_works_json(self):
        account = {"nickname": "北川魔芋姐", "works": WORKS_SAMPLE}
        run_id = CS.persist_board(account, dict(BOARD_MIN), "<html>test</html>", "test md")
        cdir = CS._CASES / run_id
        self.assertTrue((cdir / "board.json").exists())
        wp = cdir / "works.json"
        self.assertTrue(wp.exists())
        self.assertEqual(json.loads(wp.read_text("utf-8")), WORKS_SAMPLE)

    def test_account_without_works_no_works_json_but_board_ok(self):
        account = {"nickname": "无作品号"}
        run_id = CS.persist_board(account, dict(BOARD_MIN), "<html>test</html>", "test md")
        cdir = CS._CASES / run_id
        self.assertTrue((cdir / "board.json").exists())
        self.assertTrue((cdir / "meta.json").exists())
        self.assertFalse((cdir / "works.json").exists())

    def test_unserializable_works_failure_does_not_break_main_flow(self):
        # works 内含 set() 不可 JSON 序列化 → _persist_works 内部吞异常·
        # persist_board 主流程(board.json/meta.json/report.md)必须照常完成。
        account = {"nickname": "坏数据号", "works": [{"desc": "x", "weird": {1, 2, 3}}]}
        run_id = CS.persist_board(account, dict(BOARD_MIN), "<html>test</html>", "test md")
        cdir = CS._CASES / run_id
        self.assertTrue((cdir / "board.json").exists())
        self.assertTrue((cdir / "meta.json").exists())
        self.assertTrue((cdir / "report.md").exists())
        self.assertFalse((cdir / "works.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""交付形态 image 真渲染测试（P3-c·matplotlib Agg·离线）+ PPT/视频诚实交接。"""
from __future__ import annotations

import os

from app.services import deliverable as dl


def test_image_from_account_metrics(tmp_path):
    report = {"title": "账号图表",
              "account": {"follower": 4645, "avg_like": 105, "max_like": 383,
                          "burst_ratio": 3.6}}
    out = dl._render_image(report, out_path=str(tmp_path / "c.png"))
    assert out["status"] == "ok" and out["format"] == "png"
    assert os.path.getsize(out["path"]) > 1000        # 真 PNG 字节
    assert out["n"] == 4


def test_image_from_scenario_sources(tmp_path):
    report = {"scenario": "D2", "sources": {"ok": 2, "empty": 0, "timeout": 1, "error": 1}}
    out = dl._render_image(report, out_path=str(tmp_path / "s.png"))
    assert out["status"] == "ok"
    assert dict(out["series"])["命中"] == 2


def test_image_empty_when_no_numeric():
    out = dl._render_image({"title": "纯文字", "text": "无数值"})
    assert out["status"] == "empty"


def test_render_dispatch_image_is_real(tmp_path):
    out = dl.render({"account": {"follower": 100, "avg_like": 10}}, fmt="image")
    assert out["status"] == "ok"
    os.remove(out["path"])                             # 清理临时 PNG


def test_ppt_video_are_honest_handoff():
    ppt = dl.render({}, fmt="ppt")
    vid = dl.render({}, fmt="video")
    assert ppt["status"] == "handoff" and ppt["handoff"]["engine"] == "MetaDesign"
    assert vid["status"] == "handoff" and vid["handoff"]["engine"] == "MetaCut"

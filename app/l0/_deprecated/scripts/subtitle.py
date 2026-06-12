#!/usr/bin/env python3
"""link-intel 字幕：yt-dlp 下字幕，无字幕降级本地 ASR。"""
import sys
import os
import subprocess
import pathlib
import glob

# venv CLI 入 PATH（yt-dlp / mlx_whisper 装在 skill 专用 venv，subprocess 才调得到）
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")


def fetch_subtitle(url: str, out_dir: str) -> dict:
    """优先下平台字幕（含自动字幕），转 srt。返回 {ok, path, source}。"""
    os.makedirs(out_dir, exist_ok=True)
    tmpl = os.path.join(out_dir, "字幕.%(ext)s")
    cmd = ["yt-dlp", "--write-subs", "--write-auto-subs",
           "--sub-langs", "zh-Hans,zh,en", "--skip-download",
           "--convert-subs", "srt", "-o", tmpl, url]
    subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    srt = glob.glob(os.path.join(out_dir, "*.srt"))
    if srt:
        return {"ok": True, "path": srt[0], "source": "yt-dlp字幕"}
    return {"ok": False, "path": None, "source": None}


def asr_local(audio_path: str, out_dir: str) -> dict:
    """无字幕时本地 ASR。Mac 优先 mlx-whisper，否则 faster-whisper。"""
    os.makedirs(out_dir, exist_ok=True)
    out_txt = os.path.join(out_dir, "字幕-ASR.txt")
    if sys.platform == "darwin":
        try:
            r = subprocess.run(
                ["mlx_whisper", audio_path, "--model",
                 "mlx-community/whisper-large-v3", "--output-dir", out_dir,
                 "--output-format", "txt"],
                capture_output=True, text=True, timeout=900)
            produced = glob.glob(os.path.join(out_dir, "*.txt"))
            if r.returncode == 0 and produced:
                return {"ok": True, "path": produced[0], "source": "mlx-whisper"}
        except FileNotFoundError:
            pass  # mlx-whisper 未安装 → 降级 faster-whisper
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(audio_path)
        text = "\n".join(seg.text.strip() for seg in segments)
        pathlib.Path(out_txt).write_text(text, encoding="utf-8")
        return {"ok": True, "path": out_txt, "source": "faster-whisper"}
    except Exception as e:
        return {"ok": False, "path": None, "source": f"ASR失败:{e}"}


if __name__ == "__main__":
    # 用法：subtitle.py <url> <out_dir> [audio_path]
    res = fetch_subtitle(sys.argv[1], sys.argv[2])
    if not res["ok"] and len(sys.argv) > 3:
        res = asr_local(sys.argv[3], sys.argv[2])
    print(res)

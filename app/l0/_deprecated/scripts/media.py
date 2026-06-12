#!/usr/bin/env python3
"""link-intel 音视频素材：ffmpeg 抽音轨/关键帧，demucs 分离 BGM/人声。"""
import sys
import os
import subprocess
import glob

# venv CLI 入 PATH（demucs 装在 skill 专用 venv，subprocess 才调得到）
os.environ["PATH"] = os.path.dirname(sys.executable) + os.pathsep + os.environ.get("PATH", "")


def extract_audio(video_path: str, out_dir: str) -> str:
    """从视频抽完整音轨为 wav。返回音轨路径。"""
    os.makedirs(out_dir, exist_ok=True)
    audio = os.path.join(out_dir, "完整音轨.wav")
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn",
                    "-acodec", "pcm_s16le", "-ar", "44100", audio],
                   capture_output=True, text=True, timeout=300)
    return audio if os.path.exists(audio) else ""


def split_stems(audio_path: str, out_dir: str) -> dict:
    """demucs 二分离：人声轨 + 无人声轨（≈BGM）。"""
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(["demucs", "--two-stems=vocals", "-o", out_dir,
                    audio_path], capture_output=True, text=True, timeout=900)
    # demucs 输出 <out_dir>/htdemucs/<音轨名>/{vocals,no_vocals}.wav
    vocals = glob.glob(os.path.join(out_dir, "**", "vocals.wav"),
                       recursive=True)
    bgm = glob.glob(os.path.join(out_dir, "**", "no_vocals.wav"),
                    recursive=True)
    return {"人声轨": vocals[0] if vocals else "",
            "BGM": bgm[0] if bgm else ""}


def extract_keyframes(video_path: str, out_dir: str, n: int = 6) -> list:
    """按场景变化抽关键帧，至多 n 张。"""
    os.makedirs(out_dir, exist_ok=True)
    pat = os.path.join(out_dir, "关键帧_%03d.jpg")
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vf",
                    f"select='gt(scene,0.3)',scale=720:-1", "-frames:v",
                    str(n), "-vsync", "vfr", pat],
                   capture_output=True, text=True, timeout=300)
    return sorted(glob.glob(os.path.join(out_dir, "关键帧_*.jpg")))


if __name__ == "__main__":
    # 用法：media.py <video_path> <out_dir>
    v, d = sys.argv[1], sys.argv[2]
    a = extract_audio(v, d)
    print("音轨:", a)
    print("分离:", split_stems(a, d) if a else "skip")
    print("关键帧:", extract_keyframes(v, d))

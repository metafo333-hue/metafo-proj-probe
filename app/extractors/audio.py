"""直链公开音频 → 文字 · faster-whisper（ASR · MIT · D-Use 2026-06-14）。

技术合规（铁律③）：仅转写「直链公开音频文件 / 用户上传 / 授权 API 返回的音频」。
**严禁**用于平台视频下载后转写（抖音/B站/YouTube 等 → classify 已归 video → datasources）。
本提取器只在 classify 判为 audio（直链 .mp3/.wav/... 后缀）时被调用。

显存/算力：faster-whisper INT8 可纯 CPU 跑；probe-a(2c4g 无 GPU) 默认 base 模型防卡死，
GPU 机(ufo)可 env 切 large-v3。模型/设备全 env 可调，不写死。
"""
from __future__ import annotations

import os
import tempfile
from typing import Any

from app.extractors.base import Extractor

# 抓取直链音频超时（秒）· 海外经 mihomo 代理
_FETCH_TIMEOUT = int(os.getenv("PROBE_FETCH_TIMEOUT", "30"))
_HTTP_PROXY = os.getenv("PROBE_FETCH_PROXY", "")
# ASR 模型/设备/量化（默认 CPU+base 防 2c4g 卡死；ufo GPU 可切 large-v3/cuda/float16）
_ASR_MODEL = os.getenv("PROBE_ASR_MODEL", "base")
_ASR_DEVICE = os.getenv("PROBE_ASR_DEVICE", "cpu")
_ASR_COMPUTE = os.getenv("PROBE_ASR_COMPUTE", "int8")
# 单文件大小上限（MB）· 防超大文件拖垮 task
_MAX_MB = int(os.getenv("PROBE_ASR_MAX_MB", "50"))


class AudioExtractor(Extractor):
    kind = "audio"
    lib = "faster-whisper"
    import_name = "faster_whisper"
    license = "MIT"
    requires_gpu = False  # CPU(int8) 可跑·GPU 更快（调度偏好,非硬性）

    def extract(self, url: str) -> dict[str, Any]:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            return {"failed": True, "reason": "faster-whisper 未安装"}

        tmp_path = self._fetch_audio(url)
        if isinstance(tmp_path, dict):  # 抓取失败,直接回错误 dict
            return tmp_path
        try:
            model = WhisperModel(_ASR_MODEL, device=_ASR_DEVICE, compute_type=_ASR_COMPUTE)
            segments, info = model.transcribe(tmp_path, beam_size=5)
            parts = [seg.text.strip() for seg in segments]
            text = " ".join(p for p in parts if p)
            if len(text) < 1:
                return {"failed": True, "reason": "ASR 输出为空（无语音/格式不支持）"}
            return {
                "title": "",
                "text": text,
                "extractor": f"faster-whisper:{_ASR_MODEL}",
                "language": getattr(info, "language", ""),
            }
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"ASR 失败：{e}"}
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _fetch_audio(self, url: str):
        """抓直链公开音频到临时文件；本地路径(file://或绝对路径)直接用。"""
        # 本地/已上传文件路径直接用（不抓网络）
        if os.path.isfile(url):
            return url
        try:
            import httpx
        except ImportError:
            return {"failed": True, "reason": "httpx 未安装"}
        kw: dict[str, Any] = {"timeout": _FETCH_TIMEOUT, "follow_redirects": True}
        if _HTTP_PROXY:
            kw["proxy"] = _HTTP_PROXY
        try:
            with httpx.Client(**kw) as client:
                with client.stream("GET", url) as r:
                    r.raise_for_status()
                    suffix = os.path.splitext(url.split("?")[0])[1] or ".mp3"
                    fd, path = tempfile.mkstemp(suffix=suffix, prefix="probe_asr_")
                    size = 0
                    limit = _MAX_MB * 1024 * 1024
                    with os.fdopen(fd, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=65536):
                            size += len(chunk)
                            if size > limit:
                                f.close()
                                os.unlink(path)
                                return {"failed": True,
                                        "reason": f"音频超 {_MAX_MB}MB 上限"}
                            f.write(chunk)
            return path
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"抓取音频失败：{e}"}

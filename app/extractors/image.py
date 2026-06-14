"""直链公开图片 → 文字（OCR）· RapidOCR（ONNX·CPU 友好·Apache-2.0·D-Use 2026-06-14）。

技术合规（铁律③）：仅 OCR「直链公开图片 / 用户上传截图 / 授权 API 返回图片」。
本提取器只在 classify 判为 image（直链 .jpg/.png/... 后缀）时被调用。

选型：RapidOCR(rapidocr-onnxruntime) 用 PaddleOCR 同源模型 + ONNX Runtime 推理，
纯 CPU 可跑、无 PaddlePaddle 重框架依赖 → 适配 probe-a(2c4g 无 GPU)。
高精度/版面需求场景可后续切 PaddleOCR(Apache-2.0·GPU 机)。
"""
from __future__ import annotations

import os
import tempfile
from typing import Any

from app.extractors.base import Extractor

_FETCH_TIMEOUT = int(os.getenv("PROBE_FETCH_TIMEOUT", "20"))
_HTTP_PROXY = os.getenv("PROBE_FETCH_PROXY", "")
_MAX_MB = int(os.getenv("PROBE_OCR_MAX_MB", "20"))


class ImageExtractor(Extractor):
    kind = "image"
    lib = "rapidocr-onnxruntime"
    import_name = "rapidocr_onnxruntime"
    license = "Apache-2.0"
    requires_gpu = False  # ONNX CPU 推理

    def extract(self, url: str) -> dict[str, Any]:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            return {"failed": True, "reason": "rapidocr-onnxruntime 未安装"}

        path = self._fetch_image(url)
        if isinstance(path, dict):
            return path
        try:
            ocr = RapidOCR()
            result, _elapse = ocr(path)
            if not result:
                return {"failed": True, "reason": "OCR 未识别到文字"}
            # result: [[box, text, score], ...] → 拼文本
            text = "\n".join(line[1] for line in result if len(line) >= 2 and line[1])
            if len(text.strip()) < 1:
                return {"failed": True, "reason": "OCR 输出为空"}
            return {"title": "", "text": text, "extractor": "rapidocr"}
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"OCR 失败：{e}"}
        finally:
            if path != url:  # 仅删临时文件,不删用户本地原图
                try:
                    os.unlink(path)
                except OSError:
                    pass

    def _fetch_image(self, url: str):
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
                r = client.get(url)
                r.raise_for_status()
                if len(r.content) > _MAX_MB * 1024 * 1024:
                    return {"failed": True, "reason": f"图片超 {_MAX_MB}MB 上限"}
                suffix = os.path.splitext(url.split("?")[0])[1] or ".jpg"
                fd, path = tempfile.mkstemp(suffix=suffix, prefix="probe_ocr_")
                with os.fdopen(fd, "wb") as f:
                    f.write(r.content)
            return path
        except Exception as e:  # noqa: BLE001
            return {"failed": True, "reason": f"抓取图片失败：{e}"}

"""视听六层理解 · 调 Qwen3-Omni(硅基流动) · MVP 全包(audiovisual)。

视频(画面+音轨) → Qwen3-Omni → 视听六层结构化(枚举 + 置信度 + 证据时间戳)。
MVP 用全包模式(一次产六层·选型方案 §三 A 档);生产切按层拆 prompt + 约束解码(§四)。
合规:走硅基国内不出境;数据传第三方 API(放宽"自托管",守"不出境");涉密不对外暴露模型/源。
真源方案:运营报告/probe-audiovisual-sixlayer-model-selection-v1.0.md
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

SF_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"
SF_MODEL = "Qwen/Qwen3-Omni-30B-A3B-Instruct"

# 六层 schema 键(供渲染/校验对齐)
LAYERS = ("auditory", "visual", "text", "narrative", "persona", "psychology")
_LAYER_CN = {"auditory": "听觉", "visual": "视觉", "text": "文本",
             "narrative": "叙事", "persona": "人设", "psychology": "心理"}

_SIX_LAYER_PROMPT = """你是短视频视听分析专家。请观看并聆听这个视频,按"视听六层"框架分析,只输出 JSON,不要任何额外文字或解释。

六层与字段:
- auditory 听觉: bgm_style 配乐风格 / bgm_mood 配乐情绪 / speech_pace 语速(快|中|慢|无口播) / sound_fx 音效设计
- visual 视觉: quality 画面质感 / color 主色调 / composition 构图 / transition 转场手法 / edit_pace 剪辑节奏(快|中|慢)
- text 文本: summary 字幕或口播要点(一句话)
- narrative 叙事: hook 开头钩子 / structure 结构 / pacing 信息节奏
- persona 人设: on_screen 是否有人出镜(有|无) / style 风格 / camera 镜头语言
- psychology 心理: emotion_arc 情绪曲线 / resonance 共鸣点 / hook_point 记忆点

每个字段输出对象 {"v":"判断值","conf":0.0到1.0置信度}。听不清/看不清/不确定的给低 conf(<0.5),不要硬编。
顶层加 "evidence_ts": ["关键时间段,如 00:03-00:07"]。

严格按此结构输出:
{"auditory":{"bgm_style":{"v":"","conf":0},"bgm_mood":{"v":"","conf":0},"speech_pace":{"v":"","conf":0},"sound_fx":{"v":"","conf":0}},"visual":{"quality":{"v":"","conf":0},"color":{"v":"","conf":0},"composition":{"v":"","conf":0},"transition":{"v":"","conf":0},"edit_pace":{"v":"","conf":0}},"text":{"summary":{"v":"","conf":0}},"narrative":{"hook":{"v":"","conf":0},"structure":{"v":"","conf":0},"pacing":{"v":"","conf":0}},"persona":{"on_screen":{"v":"","conf":0},"style":{"v":"","conf":0},"camera":{"v":"","conf":0}},"psychology":{"emotion_arc":{"v":"","conf":0},"resonance":{"v":"","conf":0},"hook_point":{"v":"","conf":0}},"evidence_ts":[]}"""


def _sf_key(key: str | None = None) -> str | None:
    return key or os.getenv("SILICONFLOW_API_KEY")


def analyze_audiovisual(video_url: str, sf_key: str | None = None, *,
                        max_frames: int = 16, fps: int = 2, timeout: int = 150) -> dict:
    """视频 URL(或 base64 data) → 视听六层结构化。

    返回 {ok:True, six_layer:dict, usage} 或 {ok:False, error, [raw]}。
    max_frames/fps 控视频帧数防 token 爆炸(长视频调小)。
    """
    key = _sf_key(sf_key)
    if not key:
        return {"ok": False, "error": "缺 SILICONFLOW_API_KEY(走 vault)"}
    payload = {
        "model": SF_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": _SIX_LAYER_PROMPT},
            {"type": "video_url",
             "video_url": {"url": video_url, "max_frames": max_frames, "fps": fps}},
        ]}],
        "max_tokens": 1400,
        "temperature": 0.3,
    }
    try:
        req = urllib.request.Request(
            SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.load(r)
    except Exception as e:  # noqa: BLE001 — 网络/超时统一降级,不阻塞主报告
        return {"ok": False, "error": f"Qwen3-Omni 调用失败:{e}"}

    content = (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content", "")
    six = _parse_six_layer(content)
    if six is None:
        return {"ok": False, "error": "六层 JSON 解析失败", "raw": content[:400]}
    return {"ok": True, "six_layer": six, "usage": resp.get("usage")}


def _parse_six_layer(content: str | None) -> dict | None:
    """从模型输出抠 JSON(容错 ```json``` 包裹 / 前后噪声)。最低需 听觉+视觉 两层。"""
    if not content:
        return None
    m = (re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.S)
         or re.search(r"(\{.*\})", content, re.S))
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(d, dict) or "auditory" not in d or "visual" not in d:
        return None
    return d


def _fld(layer: dict, key: str, min_conf: float = 0.0) -> str | None:
    """取字段值;conf 低于阈值返回 None(下游过滤,对冲 <50% 天花板)。"""
    f = (layer or {}).get(key)
    if not isinstance(f, dict):
        return None
    v, conf = f.get("v"), f.get("conf", 0)
    try:
        conf = float(conf)
    except (TypeError, ValueError):
        conf = 0.0
    if not v or conf < min_conf:
        return None
    return f"{v}" + (f"（{int(conf*100)}%）" if conf else "")


def render_av_section(six: dict | None, *, min_conf: float = 0.45) -> str:
    """视听六层结构化 → 报告"视听六层"段(说人话·只讲 conf≥阈值项·低 conf 诚实略去)。"""
    if not six:
        return ""
    a, v = six.get("auditory") or {}, six.get("visual") or {}
    nar, per = six.get("narrative") or {}, six.get("persona") or {}
    psy, txt = six.get("psychology") or {}, six.get("text") or {}
    lines = ["### 这条视频「看+听」拆出来的东西", ""]

    # 听觉(Omni 核心价值·六层唯一硬缺口)
    au = [x for x in (
        _fld(a, "bgm_style", min_conf) and f"配乐{_fld(a,'bgm_style',min_conf)}",
        _fld(a, "bgm_mood", min_conf) and f"情绪{_fld(a,'bgm_mood',min_conf)}",
        _fld(a, "sound_fx", min_conf) and f"音效{_fld(a,'sound_fx',min_conf)}",
        _fld(a, "speech_pace", min_conf) and f"语速{_fld(a,'speech_pace',min_conf)}",
    ) if x]
    if au:
        lines.append("- **听觉**：" + " · ".join(au))
    # 视觉
    vi = [x for x in (
        _fld(v, "color", min_conf) and f"主色{_fld(v,'color',min_conf)}",
        _fld(v, "composition", min_conf) and f"构图{_fld(v,'composition',min_conf)}",
        _fld(v, "transition", min_conf) and f"转场{_fld(v,'transition',min_conf)}",
        _fld(v, "edit_pace", min_conf) and f"剪辑节奏{_fld(v,'edit_pace',min_conf)}",
    ) if x]
    if vi:
        lines.append("- **视觉**：" + " · ".join(vi))
    if _fld(txt, "summary", min_conf):
        lines.append("- **内容**：" + _fld(txt, "summary", min_conf))
    if _fld(nar, "hook", min_conf):
        lines.append("- **开头钩子**：" + _fld(nar, "hook", min_conf))
    pe = [x for x in (
        _fld(per, "on_screen", min_conf) and f"出镜{_fld(per,'on_screen',min_conf)}",
        _fld(per, "style", min_conf) and f"风格{_fld(per,'style',min_conf)}",
    ) if x]
    if pe:
        lines.append("- **人设**：" + " · ".join(pe))
    if _fld(psy, "resonance", min_conf):
        lines.append("- **共鸣点**：" + _fld(psy, "resonance", min_conf))

    ts = six.get("evidence_ts")
    if isinstance(ts, list) and ts:
        lines.append(f"- **关键片段**：{ '、'.join(str(t) for t in ts[:4]) }")
    lines.append("")
    lines.append("> 说明：以上由视听理解模型对画面+音轨分析得出，每项带置信度；"
                 "**听觉/音乐类判断准确率有限**，低置信项已略去，仅作参考、不作硬结论。")
    return "\n".join(lines)


if __name__ == "__main__":  # 自检/手测:python -m app.services.audiovisual <video_url>
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.w3schools.com/html/mov_bbb.mp4"
    out = analyze_audiovisual(url)
    if out["ok"]:
        print("=== 六层结构化 ===")
        print(json.dumps(out["six_layer"], ensure_ascii=False, indent=2))
        print("\n=== 渲染段 ===")
        print(render_av_section(out["six_layer"]))
        print("\nusage:", out.get("usage"))
    else:
        print("失败:", out)

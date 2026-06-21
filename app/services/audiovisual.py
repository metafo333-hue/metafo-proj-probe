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


_DL_UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")


def fetch_video_as_data_uri(play_urls, *, max_mb: int = 40, timeout: int = 60) -> dict:
    """抖音 play_addr 直链(CDN 防盗链) → 本地带 UA 下载 → base64 data URI(中转喂 Omni)。

    实测(2026-06-20):抖音 CDN 直链硅基服务器直接拉会 HTTP 500(防盗链)·必须本地中转。
    play_urls=候选直链列表(含不同清晰度);**超 max_mb 不放弃·试下一个清晰度**(头部号高清视频可能 30MB+)·
    全部超限才返回 too_big(生产走临时 URL 非 base64)。
    """
    import base64
    too_big_min = None
    for url in (play_urls or []):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": _DL_UA, "Referer": "https://www.douyin.com/"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
        except Exception:  # noqa: BLE001 — 逐个直链试错,失败换下一个
            continue
        if not data:
            continue
        mb = len(data) / 1024 / 1024
        if mb > max_mb:
            too_big_min = mb if too_big_min is None else min(too_big_min, mb)
            continue   # 太大·试下一个清晰度(可能有低清更小版)
        b64 = base64.b64encode(data).decode()
        return {"ok": True, "data_uri": f"data:video/mp4;base64,{b64}", "size_mb": round(mb, 2)}
    if too_big_min is not None:
        return {"ok": False, "too_big": True,
                "error": f"各清晰度均 >{max_mb}MB(最小 {too_big_min:.1f}MB)·生产走临时 URL 方案"}
    return {"ok": False, "error": "所有直链下载失败(防盗链/链接过期)"}


def analyze_douyin_video(play_urls, sf_key: str | None = None, **kw) -> dict:
    """抖音直链列表 → 下载中转 → 视听六层(一步到位)。"""
    dl = fetch_video_as_data_uri(play_urls)
    if not dl.get("ok"):
        return dl
    out = analyze_audiovisual(dl["data_uri"], sf_key, **kw)
    if out.get("ok"):
        out["video_size_mb"] = dl["size_mb"]
    return out


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


# ─────────────────────────────────────────────────────────────
# 生产形态：按层拆 prompt · 两阶段调用
# 方案来源：运营报告/probe-audiovisual-sixlayer-model-selection-v1.0.md §四
#
# 设计：
#   ① 感知调用 → 听觉+视觉+文本（需真看真听，Qwen3-Omni 多模态核心价值）
#   ② 推理调用 → 叙事+人设+心理（基于①的感知证据做语义推理，纯文本即可）
#
# 约束解码：硅基 response_format 仅支持 type=text，不支持 json_schema/json_object
# （已查 https://docs.siliconflow.cn/cn/api-reference/chat-completions/chat-completions 文档
#  以及 /cn/capabilities/json-output 返回 404，文档例中只见 type:text）。
# 降级方案：prompt 强约束 + 多行 schema 模板 + _parse_six_layer 容错解析。
# ─────────────────────────────────────────────────────────────

# 感知层 prompt（听觉+视觉+文本·需真看真听）
_PERCEPTION_PROMPT = """你是短视频视听分析专家。仔细观看并聆听这个视频，只输出 JSON，不要任何额外文字或解释。

分析以下三层，每个字段输出 {"v":"判断值","conf":0.0到1.0置信度}。
听不清/看不清/不确定给低 conf(<0.5)，不要硬编。

严格按此结构输出:
{"auditory":{"bgm_style":{"v":"","conf":0},"bgm_mood":{"v":"","conf":0},"speech_pace":{"v":"","conf":0},"sound_fx":{"v":"","conf":0}},"visual":{"quality":{"v":"","conf":0},"color":{"v":"","conf":0},"composition":{"v":"","conf":0},"transition":{"v":"","conf":0},"edit_pace":{"v":"","conf":0}},"text":{"summary":{"v":"","conf":0}},"evidence_ts":[]}

字段说明:
- auditory.bgm_style: 配乐风格
- auditory.bgm_mood: 配乐情绪
- auditory.speech_pace: 语速(快|中|慢|无口播)
- auditory.sound_fx: 音效设计
- visual.quality: 画面质感
- visual.color: 主色调
- visual.composition: 构图
- visual.transition: 转场手法
- visual.edit_pace: 剪辑节奏(快|中|慢)
- text.summary: 字幕或口播要点(一句话)
- evidence_ts: 关键时间段列表(如["00:03-00:07"])"""

# 推理层 prompt 模板（叙事+人设+心理·基于感知证据·纯文本推理）
_REASONING_PROMPT_TPL = """你是短视频内容分析专家。以下是对一段视频的感知层分析结果（听觉/视觉/文本）：

{perception_json}

基于以上感知证据，对该视频做语义推理分析。只输出 JSON，不要任何额外文字或解释。
每个字段输出 {{"v":"判断值","conf":0.0到1.0置信度}}，无法推断的给低 conf(<0.5)。

严格按此结构输出:
{{"narrative":{{"hook":{{"v":"","conf":0}},"structure":{{"v":"","conf":0}},"pacing":{{"v":"","conf":0}}}},"persona":{{"on_screen":{{"v":"","conf":0}},"style":{{"v":"","conf":0}},"camera":{{"v":"","conf":0}}}},"psychology":{{"emotion_arc":{{"v":"","conf":0}},"resonance":{{"v":"","conf":0}},"hook_point":{{"v":"","conf":0}}}}}}

字段说明:
- narrative.hook: 开头钩子
- narrative.structure: 叙事结构
- narrative.pacing: 信息节奏
- persona.on_screen: 是否有人出镜(有|无)
- persona.style: 风格
- persona.camera: 镜头语言
- psychology.emotion_arc: 情绪曲线
- psychology.resonance: 共鸣点
- psychology.hook_point: 记忆点"""


def _call_sf_text(prompt: str, key: str, *, timeout: int = 120, max_tokens: int = 600) -> str | None:
    """调硅基纯文本模型（推理层·DeepSeek-V3 成本更低·感知层不用本函数）。

    返回 content 字符串，失败返回 None。
    注：推理层只需文字理解，不需多模态，用 DeepSeek-V3-0324 省成本。
    """
    import urllib.error
    # 推理层用 DeepSeek-V3（纯文本·便宜）；感知层仍走 Qwen3-Omni（多模态必须）
    TEXT_MODEL = "deepseek-ai/DeepSeek-V3-0324"
    payload = {
        "model": TEXT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        req = urllib.request.Request(
            SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        return None
    except Exception:  # noqa: BLE001
        return None
    return (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content")


def _call_sf_vision(video_url: str, prompt: str, key: str, *,
                    timeout: int = 150, max_tokens: int = 800,
                    max_frames: int = 16, fps: int = 2) -> str | None:
    """调硅基 Qwen3-Omni（多模态·感知层专用）。返回 content 字符串，失败返回 None。"""
    payload = {
        "model": SF_MODEL,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "video_url",
             "video_url": {"url": video_url, "max_frames": max_frames, "fps": fps}},
        ]}],
        "max_tokens": max_tokens,
        "temperature": 0.3,
        # 注：硅基 response_format 仅支持 type:text，不支持 json_schema/json_object
        # 故不传 response_format，靠 prompt 强约束 + _parse_six_layer 容错解析降级。
    }
    try:
        req = urllib.request.Request(
            SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.load(r)
    except Exception:  # noqa: BLE001
        return None
    return (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content")


def _merge_perception_reasoning(perception: dict, reasoning: dict) -> dict:
    """合并感知层和推理层结果，产出和 analyze_audiovisual 相同的 six_layer dict 结构。

    感知层必须含 auditory/visual/text/evidence_ts；
    推理层必须含 narrative/persona/psychology。
    缺失层用空 dict 填充（容错·不阻断）。
    """
    return {
        "auditory": perception.get("auditory") or {},
        "visual": perception.get("visual") or {},
        "text": perception.get("text") or {},
        "narrative": reasoning.get("narrative") or {},
        "persona": reasoning.get("persona") or {},
        "psychology": reasoning.get("psychology") or {},
        "evidence_ts": perception.get("evidence_ts") or [],
    }


def analyze_by_layers(video_url: str, sf_key: str | None = None, *,
                      max_frames: int = 16, fps: int = 2,
                      timeout: int = 150) -> dict:
    """生产形态：按层拆 prompt · 两阶段调用 · 对抗层间稀释。

    ① 感知调用（Qwen3-Omni 多模态）→ auditory + visual + text + evidence_ts
    ② 推理调用（DeepSeek-V3 纯文本，把①结果作上下文）→ narrative + persona + psychology

    返回格式和 analyze_audiovisual 完全相同：
        {ok:True, six_layer:dict, usage:{"perception":..., "reasoning":...}}
    或  {ok:False, error:str, [perception_raw], [reasoning_raw]}

    合并后的 six_layer 可直接传入 render_av_section 复用渲染逻辑。

    约束解码：硅基不支持 json_schema，降级为 prompt 强约束 + 容错解析（诚实标注）。
    """
    key = _sf_key(sf_key)
    if not key:
        return {"ok": False, "error": "缺 SILICONFLOW_API_KEY(走 vault)"}

    # ── ① 感知调用 ──────────────────────────────────────────────
    perception_raw = _call_sf_vision(
        video_url, _PERCEPTION_PROMPT, key,
        timeout=timeout, max_tokens=800, max_frames=max_frames, fps=fps)
    if not perception_raw:
        return {"ok": False, "error": "感知层调用失败(Qwen3-Omni 无响应)"}

    # 感知层解析：最低门 auditory+visual（_parse_six_layer 已有此检验）
    perception = _parse_six_layer(perception_raw)
    if perception is None:
        return {"ok": False, "error": "感知层 JSON 解析失败", "perception_raw": perception_raw[:400]}

    # ── ② 推理调用 ──────────────────────────────────────────────
    # 把感知结果序列化作推理上下文（只传感知层，不传视频 URL）
    perception_ctx = json.dumps(
        {k: perception.get(k) for k in ("auditory", "visual", "text", "evidence_ts")},
        ensure_ascii=False, indent=2)
    reasoning_prompt = _REASONING_PROMPT_TPL.format(perception_json=perception_ctx)

    reasoning_raw = _call_sf_text(reasoning_prompt, key, timeout=120, max_tokens=600)
    if not reasoning_raw:
        return {"ok": False, "error": "推理层调用失败(DeepSeek-V3 无响应)",
                "perception_raw": perception_raw[:400]}

    # 推理层解析：接受 narrative/persona/psychology 任意组合（宽容）
    reasoning = _parse_reasoning_layer(reasoning_raw)
    if reasoning is None:
        return {"ok": False, "error": "推理层 JSON 解析失败",
                "perception_raw": perception_raw[:400], "reasoning_raw": reasoning_raw[:400]}

    six = _merge_perception_reasoning(perception, reasoning)
    return {
        "ok": True,
        "six_layer": six,
        "usage": {"perception": "Qwen3-Omni(感知·多模态)", "reasoning": "DeepSeek-V3(推理·纯文本)"},
    }


def _parse_reasoning_layer(content: str | None) -> dict | None:
    """从推理层输出抠 JSON(容错)。最低需 narrative/persona/psychology 之一。"""
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
    if not isinstance(d, dict):
        return None
    # 最低门：含推理三层之一
    if not any(k in d for k in ("narrative", "persona", "psychology")):
        return None
    return d


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

"""报告 LLM 润色层 · 内容方法论原则1「真叙事感」(只重组表达·不新增事实)。

确定性 report_md → LLM 重写成有逻辑主线、像懂行的人聊天的诊断报告。
铁律(R0.8 真实性·违反即降级原文):
  1. 禁改任何数字   2. 禁新增事实/判断   3. 禁删关键结论
  4. 只重组表达(语序/过渡/口吻/突出重点)   5. 保留 markdown + emoji 标记
机制护栏(不靠模型自觉):
  - 润色后**校验原报告关键数字全部仍在**(规范化去逗号比对)·篡改/丢失即降级
  - 输出过短(<原文50%)即降级 · 调用失败即降级
开关 REPORT_POLISH=1 启用(默认关·保确定性纯度)。润色稿尾部标注"AI润色·数据来自确定性分析"。
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

SF_ENDPOINT = "https://api.siliconflow.cn/v1/chat/completions"


def _polish_model() -> str:
    """润色模型 = 模型路由层按周更表选(默认质量/成本均衡 Qwen3.5-122B·替旧 DeepSeek-V3)。
    REPORT_POLISH_MODEL env 可锁定(路由内部已处理)。路由不可用回退国产默认,永不阻塞。"""
    try:
        from app.services.model_router import select
        return select("polish") or "Qwen/Qwen3.5-122B-A10B"
    except Exception:
        return os.getenv("REPORT_POLISH_MODEL", "Qwen/Qwen3.5-122B-A10B")


POLISH_MODEL = _polish_model()  # 模块级快照(兼容);热选见 polish_report()

_PROMPT = """你是顶级的短视频账号诊断顾问。下面是一份「确定性规则」生成的账号诊断报告,内容全部正确,但表达有点像清单、段落之间是断的。

你的任务:把它**重写成一篇有逻辑主线、像一个懂行的人在跟创作者面对面聊他账号**的诊断报告——让他读完清楚"我是谁→卡在哪→为什么→怎么破"。

铁律(违反任何一条都是严重错误):
1. **禁止改任何数字**(粉丝数/点赞数/比例/百分比等,全部原样保留)。**数字必须保持阿拉伯数字原格式**——不能把 220000 改成"22万"、不能把 6438222 改成"643万"等中文单位缩写，必须原封不动保留阿拉伯数字
2. **禁止新增任何事实或判断**(原报告没说的结论,你绝不能编出来)
3. **禁止删除关键结论**(每段的核心判断和行动建议都要保留)
4. 你能做的只有:调整语序让逻辑更顺、加"正因为/所以"这类过渡句串联段落、把生硬的话说得更自然、突出重点
5. 保留 markdown 结构(## 标题 / 列表 / **粗体**)和所有 emoji 标记(🔴 🟡 👉)
6. **保持完整·绝不压缩精简**:原报告每一个段落(现状/规律/优势/怎么做/整体判断/赛道环境/可信度等)、每一个要点、每一条行动建议,都必须完整保留并重写——重写是为了表达更顺、逻辑更连贯,**不是为了缩短**。重写后篇幅应与原文相当或更丰富,绝不能删减任何段落或要点
7. **所有标题(## 和 ### 开头的行)必须一字不改、原文照搬**:如「这条视频「看+听」拆出来的东西」「你这N条作品藏着的规律」「你这个号整体判断」「你所在赛道的大环境」「这份分析有多可信」等——标题是报告骨架和系统识别锚点,你**只能重写标题下面的正文**,标题本身绝对不能改写、不能换说法、不能删除
8. **诚实标注的原话必须保留**:「拿不到」「绝不瞎编」「没接到」这类诚实声明是合规底线,必须原话保留,**不能**换成"无法获取""暂时缺失"等同义说法

原报告:
---
{md}
---
直接输出重写后的报告(markdown 格式),不要任何解释或开场白。"""

_NOTE = ("\n\n> 📝 本报告表达经 AI 润色（仅重组语言、串联逻辑，**不新增任何数据或判断**），"
         "所有数字与结论均来自确定性分析。")


def _nums(text: str) -> set:
    """提取 3 位以上数字(粉丝/赞等关键值)·规范化去逗号(防 4,645↔4645 误判)。"""
    return {n.replace(",", "") for n in re.findall(r"\d[\d,]{2,}", text or "")}


# 超此长度走分段润色(点1:太长的报告分段处理)·防单次 max_tokens 截断+长输入质量衰减
_SEGMENT_THRESHOLD = 7000
_ANCHORS = ("看+听", "藏着的规律", "整体判断", "赛道的大环境", "最该解决",
            "拿不到", "瞎编", "晒证据", "虚假宣传")


def _guards(md: str, polished: str, must_keep) -> str | None:
    """润色稿过护栏。通过返回 None,否则返回降级原因。守:过短/核心数字/锚点/诚实标注。"""
    if not polished or len(polished) < len(md) * 0.40:
        return "输出异常(过短)"
    keep = {str(n).replace(",", "") for n in (must_keep or [])
            if n and str(n).replace(",", "").isdigit()}
    if not keep:
        keep = {n for n in _nums(md) if len(n) >= 5}
    keep = {n for n in keep if n in _nums(md)}  # 只守本段确实出现的数字(分段安全)
    missing = keep - _nums(polished)
    if missing:
        return f"篡改/丢失核心数字 {sorted(missing)[:3]}"
    lost = [a for a in _ANCHORS if a in md and a not in polished]
    if lost:
        return f"改了关键锚点/诚实标注 {lost[:2]}"
    return None


def _polish_once(md: str, key: str, must_keep, timeout: int) -> dict:
    """单次润色 md(不含尾注)。{ok:True,polished} 或 {ok:False,fallback:md,error}。"""
    dyn_max_tokens = max(8000, int(len(md) * 2))
    payload = {"model": _polish_model(), "temperature": 0.5,
               "max_tokens": dyn_max_tokens,
               "messages": [{"role": "user", "content": _PROMPT.format(md=md)}]}
    try:
        req = urllib.request.Request(
            SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.load(r)
        polished = (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content", "").strip()
    except Exception as e:  # noqa: BLE001 — 任何失败降级原文,不阻塞
        return {"ok": False, "fallback": md, "error": f"润色调用失败:{e}"}
    bad = _guards(md, polished, must_keep)
    if bad:
        return {"ok": False, "fallback": md, "error": f"{bad}·降级原文(守真实性)"}
    return {"ok": True, "polished": polished}


def _split_sections(md: str) -> list[str]:
    """按顶层 ## 切段(段头随段)·首个 ## 前的引言自成一段。供长报告分段润色。"""
    parts, buf = [], []
    for ln in md.split("\n"):
        if ln.startswith("## ") and buf:
            parts.append("\n".join(buf))
            buf = [ln]
        else:
            buf.append(ln)
    if buf:
        parts.append("\n".join(buf))
    return parts or [md]


def polish_report(report_md: str, sf_key: str | None = None, *,
                  must_keep=None, timeout: int = 150) -> dict:
    """LLM 润色 report_md。短报告单次,长报告(>7000字)按 ## 分段逐段润色再拼接。

    返回 {ok:True, polished} 或 {ok:False, fallback:原文, error}。
    must_keep: 必须逐字保留的核心数字(粉丝/均赞/最高赞)。次要数字允许重述。
    分段:任一段润色失败→该段保留原文(优雅降级,部分润色仍可用)。
    """
    key = sf_key or os.getenv("SILICONFLOW_API_KEY")
    if not key or not report_md:
        return {"ok": False, "fallback": report_md, "error": "缺 key 或空报告"}

    # 短报告:单次润色
    if len(report_md) <= _SEGMENT_THRESHOLD:
        out = _polish_once(report_md, key, must_keep, timeout)
        if out["ok"]:
            return {"ok": True, "polished": out["polished"] + _NOTE, "note": "polished"}
        return {"ok": False, "fallback": report_md, "error": out["error"]}

    # 长报告:分段润色(点1)·逐段守护栏·段失败保原文
    segs = _split_sections(report_md)
    polished_segs, n_ok = [], 0
    for seg in segs:
        if len(seg.strip()) < 200:  # 太短的段不值得单独调,直接保留
            polished_segs.append(seg)
            continue
        out = _polish_once(seg, key, must_keep, timeout)
        if out["ok"]:
            polished_segs.append(out["polished"])
            n_ok += 1
        else:
            polished_segs.append(seg)  # 优雅降级:该段用原文
    if n_ok == 0:
        return {"ok": False, "fallback": report_md, "error": "分段润色全失败·降级原文"}
    return {"ok": True, "polished": "\n".join(polished_segs) + _NOTE,
            "note": f"polished_segmented({n_ok}/{len(segs)}段)"}

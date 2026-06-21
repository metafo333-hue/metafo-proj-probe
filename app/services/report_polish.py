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
POLISH_MODEL = os.getenv("REPORT_POLISH_MODEL", "deepseek-ai/DeepSeek-V3")

_PROMPT = """你是顶级的短视频账号诊断顾问。下面是一份「确定性规则」生成的账号诊断报告,内容全部正确,但表达有点像清单、段落之间是断的。

你的任务:把它**重写成一篇有逻辑主线、像一个懂行的人在跟创作者面对面聊他账号**的诊断报告——让他读完清楚"我是谁→卡在哪→为什么→怎么破"。

铁律(违反任何一条都是严重错误):
1. **禁止改任何数字**(粉丝数/点赞数/比例/百分比等,全部原样保留)
2. **禁止新增任何事实或判断**(原报告没说的结论,你绝不能编出来)
3. **禁止删除关键结论**(每段的核心判断和行动建议都要保留)
4. 你能做的只有:调整语序让逻辑更顺、加"正因为/所以"这类过渡句串联段落、把生硬的话说得更自然、突出重点
5. 保留 markdown 结构(## 标题 / 列表 / **粗体**)和所有 emoji 标记(🔴 🟡 👉)
6. **保持完整·绝不压缩精简**:原报告每一个段落(现状/规律/优势/怎么做/整体判断/赛道环境/可信度等)、每一个要点、每一条行动建议,都必须完整保留并重写——重写是为了表达更顺、逻辑更连贯,**不是为了缩短**。重写后篇幅应与原文相当或更丰富,绝不能删减任何段落或要点

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


def polish_report(report_md: str, sf_key: str | None = None, *,
                  must_keep=None, timeout: int = 150) -> dict:
    """LLM 润色 report_md。返回 {ok:True, polished} 或 {ok:False, fallback:原文, error}。

    must_keep: 必须逐字保留的核心数字列表(粉丝/均赞/最高赞等关键判断值)。
               次要数字(转发/收藏/日期)允许润色重述。不传则守所有 4 位+数字。
    """
    key = sf_key or os.getenv("SILICONFLOW_API_KEY")
    if not key or not report_md:
        return {"ok": False, "fallback": report_md, "error": "缺 key 或空报告"}
    payload = {"model": POLISH_MODEL, "temperature": 0.5, "max_tokens": 6000,
               "messages": [{"role": "user", "content": _PROMPT.format(md=report_md)}]}
    try:
        req = urllib.request.Request(
            SF_ENDPOINT, data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.load(r)
        polished = (((resp.get("choices") or [{}])[0]).get("message") or {}).get("content", "").strip()
    except Exception as e:  # noqa: BLE001 — 任何失败都降级原文,不阻塞
        return {"ok": False, "fallback": report_md, "error": f"润色调用失败:{e}"}

    if not polished or len(polished) < len(report_md) * 0.5:
        return {"ok": False, "fallback": report_md, "error": "润色输出异常(过短)·降级原文"}
    # 护栏:核心数字(粉丝/均赞/最高赞·must_keep)必须逐字仍在润色稿·防篡改关键判断值
    # 次要数字(转发/收藏/日期)允许润色重述(如"互动亮眼")·不强求逐字
    keep = {str(n).replace(",", "") for n in (must_keep or []) if n and str(n).replace(",", "").isdigit()}
    if not keep:
        keep = {n for n in _nums(report_md) if len(n) >= 4}  # 无指定则守 4 位+大数字
    missing = keep - _nums(polished)
    if missing:
        return {"ok": False, "fallback": report_md,
                "error": f"润色篡改/丢失核心数字 {sorted(missing)[:3]}·降级原文(守真实性)"}
    return {"ok": True, "polished": polished + _NOTE, "note": "polished"}

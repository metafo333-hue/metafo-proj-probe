"""综合分析报告生成器 · 确定性(规则驱动·零 LLM·零网络)。

输入:已采集的 video + account + audit 数据 → 输出 markdown 综合报告。
结构对齐设计:BLUF 首屏 + 满足(基本盘)+ 高于期望(未来预判 + 关联洞察)+ 创作处方(原创放大)+ 担保。
价值对齐北极星:处方默认"放大你自己的真东西",不是教抄;reliability 诚实标。
"""
from __future__ import annotations

from typing import Any

# 赛道关键词 → (赛道名, 单粉价值/变现路线)· 据 playbook 八大类(轻量·可扩展)
_TRACK_HINTS = [
    (("女性", "妈妈", "职场", "成长", "婚姻", "情感", "她"), "女性成长/情感", "中-高(情感共鸣→私域→陪伴/知识变现·走深不走量)"),
    (("育儿", "孩子", "宝妈", "母婴", "亲子"), "母婴育儿", "中(带货/本地/知识付费)"),
    (("美食", "探店", "吃", "菜", "厨"), "美食", "中-高(探店团购/带货)"),
    (("健身", "运动", "瑜伽", "减肥"), "健身运动", "中-高(带货/课程/社群)"),
    (("职场", "考证", "财经", "理财", "知识", "科普"), "知识教育", "高(引流私域·高客单)"),
    (("穿搭", "美妆", "时尚", "护肤"), "时尚美妆", "高(带货/品牌商单)"),
]


def _track_hint(text: str) -> tuple[str, str]:
    for kws, name, value in _TRACK_HINTS:
        if any(k in text for k in kws):
            return name, value
    return "生活方式(待细分)", "中(带货/本地/商单)"


def _rating(follower: int, vertical: float, max_like: int, avg_like: int) -> str:
    if follower < 1000:
        return "🟡 早期摸索期(小号 · 内容有潜力 · 方向待聚焦)" if max_like > avg_like * 3 \
            else "🟡 早期起步期(小号 · 需先跑出方向)"
    if vertical < 0.6:
        return "🟠 成长期 · 方向偏散(有量但算法没认清你)"
    return "🟢 成长期 · 方向清晰"


def _ratio_status(like: int, avg: float) -> tuple[float, str]:
    r = like / (avg + 1)
    if r > 2:
        return r, "账号内爆款"
    if r < 0.5:
        return r, "低于均值 · 偏翻车"
    return r, "账号常态"


def build_report(video: dict[str, Any], account: dict[str, Any],
                 audit: dict[str, Any]) -> str:
    """生成 markdown 综合报告(确定性)。"""
    nick = account.get("nickname") or "该账号"
    fol = account.get("follower") or 0
    avg = account.get("avg_like") or 0
    mx = account.get("max_like") or 0
    vert = account.get("vertical_score")
    vert = vert if vert is not None else 0.0
    burst = account.get("burst_ratio")
    works_n = account.get("works_analyzed") or 0
    aweme = account.get("aweme_count") or 0
    sig = (account.get("signature") or "")[:70]
    tags = account.get("hashtags") or []
    like = video.get("like") or 0

    ratio, status = _ratio_status(like, avg)
    track, track_value = _track_hint(" ".join(tags) + sig + (video.get("title") or ""))
    has_spark = mx > avg * 3 and mx > 0
    散 = vert < 0.6

    L = []
    L.append(f"# 📋 综合分析报告 · @{nick}")
    L.append("")
    L.append("> 数据:TikHub 授权源实时采集 · ⚠️ 真实系统会先**问清诉求**再定制;本份按「**创作者自己复盘**」出。")
    L.append("")

    # —— 一句话结论(BLUF)——
    L.append("## 🎯 一句话结论(先看这个)")
    core = f"你的真东西是「{track}」方向的真实表达,这是别人抄不走的护城河。"
    if 散:
        core += f"当前问题不是「内容不好」,而是账号太散(垂直度 {vert})、算法还没认清你是谁。"
    if status == "账号常态":
        core += f"这条 {like} 赞是账号常态、不是失败。"
    elif status == "账号内爆款":
        core += f"这条 {like} 赞是你的**账号内爆款**,值得复盘为什么。"
    else:
        core += f"这条 {like} 赞低于你均值,别灰心、看趋势。"
    L.append(f"**{core}**")
    L.append(f"**最该做的一件事:{'聚焦到 1-2 个真实母题' if 散 else '把已验证的方向做深做透'}。**")
    L.append(f"评级:{_rating(fol, vert, mx, avg)}")
    L.append("")

    # —— 满足(基本盘)——
    L.append("## ✅ 满足你问的(基本盘)")
    L.append(f"- **这条视频好不好?** → {like} 赞 = 账号均值({avg})的 **{ratio:.2f} 倍 = {status}**。")
    L.append(f"- **账号现状?** → {fol} 粉 · {aweme} 作品 · 均赞 {avg} · 最高 **{mx}** · 爆款比 {burst} · 垂直度 **{vert}**{'(偏散)' if 散 else ''}")
    L.append("")

    # —— 高于期望(超预期)——
    L.append("## 🚀 高于你期望的(超预期 · 价值所在)")
    L.append("**① 未来可能发生的(基于数据推断):**")
    if has_spark:
        L.append(f"- 你已有 **{mx} 赞的爆款样本** → 证明你的内容**能起量**,问题不在「会不会做」,在「聚不聚焦」。")
    L.append(f"- 「{track}」属**{track_value}**赛道,适合「**小而精、走深**」。")
    if 散:
        L.append("- 照当前「散」的轨迹,会一直「偶尔小爆、整体不温不火」;**一旦聚焦,算法认清你→推荐更稳**。")
    L.append("")
    L.append("**② 你可能没想到的(多维挖出来的):**")
    if 散:
        L.append(f"- 你大概以为问题是「内容不够好」,但数据说真问题是 **「垂直度 {vert}、太散」** —— **聚焦比换选题更重要**。")
    if status == "账号常态":
        L.append(f"- 别拿单条 {like} 赞否定自己:它是常态不是翻车,看的是趋势和聚焦。")
    L.append("")

    # —— 创作处方(原创放大)——
    L.append("## ✍️ 创作处方(原创放大 · 不是教你抄)")
    n = 1
    if 散:
        L.append(f"{n}. **聚焦母题** —— 从分散标签收敛到 1 个你最真实的切口。`指标:垂直度 {vert}→0.8+`"); n += 1
    L.append(f"{n}. **强化前 3 秒** —— 把冲突/问题提到开头。`指标:完播率(需投喂补)`"); n += 1
    if has_spark:
        L.append(f"{n}. **复制你自己的成功** —— 拆你那条 {mx} 赞的内核,多做那个方向 —— **放大你已验证的真东西,不抄别人**。"); n += 1
    L.append("")

    # —— 担保 ——
    L.append("## 🔖 数据可信度(担保 · 诚实交代)")
    L.append(f"- 源可靠性 **{audit.get('source_reliability','?')}** · 置信 **{audit.get('confidence_level','?')}** · 证据 **{audit.get('evidence_strength','?')}** · **单一来源未交叉佐证**")
    L.append("- ✅ 实测:点赞/评论/分享/粉丝/作品/标签　⚠️ 拿不到(抖音黑盒,**不编**):播放量、完播率、流量来源、转化")
    L.append("- 含义:**能给方向,别当铁证**;要更准需多源佐证。")
    return "\n".join(L)

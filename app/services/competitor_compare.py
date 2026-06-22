"""L4 竞品圈对比 · 确定性(规则驱动·零 LLM·零网络)。

三圈参照的"竞品圈":目标号 vs 同行横向定位——**无裸数字**,每个指标都给相对坐标
(排第几 / 差距倍数 / 谁值得学)。account 数据由 account_chain 各采一遍得到。
对应 probe 分析逻辑框架"粒度轴 L4 跨账号"。
"""
from __future__ import annotations

from typing import Any


def _rank(accts: list[dict], key: str, higher_better: bool = True) -> tuple[list, dict]:
    """返回 (降序 [(nickname,val)], {nickname: 排名(1基)})。"""
    vals = [(a.get("nickname") or "?", a.get(key) or 0) for a in accts]
    sv = sorted(vals, key=lambda x: x[1], reverse=higher_better)
    rank = {n: i + 1 for i, (n, _) in enumerate(sv)}
    return sv, rank


def compare_accounts(target: dict[str, Any], competitors: list[dict]) -> str:
    """目标号 vs 竞品横向对比段(markdown·说人话·无裸数字·相对定位)。

    target/competitors = account dict(nickname/follower/avg_like/max_like/vertical_score)。
    无竞品 → 返回空串(不插无意义段)。
    """
    competitors = [c for c in (competitors or []) if isinstance(c, dict) and c.get("nickname")]
    if not competitors:
        return ""
    accts = [target] + competitors
    n_all = len(accts)
    tname = target.get("nickname") or "你"
    tfol = target.get("follower") or 0
    tavg = target.get("avg_like") or 0

    _, fol_rank = _rank(accts, "follower")
    avg_sv, avg_rank = _rank(accts, "avg_like")
    _, vert_rank = _rank(accts, "vertical_score")

    L = [f"## 同行里你站在哪(和 {len(competitors)} 个同类号比)", ""]
    L.append(f"光看自己看不出好坏——把你和 {len(competitors)} 个同方向的号放一起比,位置就清楚了:")
    L.append("")
    L.append(f"- **粉丝量**:你在这 {n_all} 个号里排**第 {fol_rank[tname]}**"
             + (f"(你 {tfol} 粉)。" if tfol else "。"))

    avg_top_name, avg_top_val = avg_sv[0]
    if avg_rank[tname] == 1:
        L.append("- **平均点赞**:你排**第 1**——内容受欢迎程度在同行里领先,这是你的强项。")
    else:
        gap = avg_top_val / (tavg + 1)
        L.append(f"- **平均点赞**:你排**第 {avg_rank[tname]}**。做得最好的是「{avg_top_name}」"
                 f"(均赞约是你的 {gap:.1f} 倍)——值得研究他家内容。")

    L.append(f"- **聚焦度**:你排**第 {vert_rank[tname]}**"
             + ("(你最聚焦,系统最容易认清你)。" if vert_rank[tname] == 1
                else "(越靠前=方向越集中,系统越容易推你)。"))
    L.append("")

    if avg_rank[tname] > 1:
        L.append(f"**怎么用**:找出「{avg_top_name}」比你数据好的内容,看它的选题/开头/节奏强在哪,"
                 "结合你自己的真东西去学——不是抄,是补差距。")
    else:
        L.append("**怎么用**:你已是这圈里的领先者,保持节奏把优势拉大,别被追上。")
    L.append("")
    L.append("> 对比基于各号公开数据,样本为所选同行,非全行业排名,作相对参考。")
    return "\n".join(L)


def compare_from_urls(target_url: str, competitor_urls: list[str],
                      tikhub_key: str | None = None) -> dict:
    """目标抖音视频链接 + 竞品视频链接列表 → 各采账号 → 对比段。

    需 TikHub(付费·每个号一次采集);竞品视听六层默认关(省钱)。
    返回 {ok, compare_md, target, competitors} 或 {ok:False, error}。
    """
    from app.services.account_chain import run_from_video_url  # 延迟导入避免循环

    tgt = run_from_video_url(target_url, tikhub_key, with_audiovisual=False)
    if not tgt.get("ok"):
        return {"ok": False, "error": f"目标号采集失败:{tgt.get('error')}"}
    comps = []
    for u in (competitor_urls or []):
        r = run_from_video_url(u, tikhub_key, with_audiovisual=False)
        if r.get("ok"):
            comps.append(r["account"])
    if not comps:
        return {"ok": False, "error": "竞品号全部采集失败"}
    md = compare_accounts(tgt["account"], comps)
    return {"ok": True, "compare_md": md, "target": tgt["account"], "competitors": comps}

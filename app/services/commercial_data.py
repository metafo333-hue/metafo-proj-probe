"""商业数据增强 · 合规 · 公开数据查表先行 · 真实 API 骨架预留。

设计原则（承方法论 §四·七）：
  🟢 自动可填 = 公开行业数据查表（佣金率/GMV档/星图估值）
  🔴 黑盒靠投喂 = 真实销量/完播率/商单实际成交价 → 诚实标缺口
  ⚠️ 蝉妈妈类数据 = 禁作精确结论（方向参考）
  📌 真实 API（慢慢买/京东/精选联盟）= 骨架预留·MVP 降级返回 available=False

数据来源标注：
  - 佣金率区间 → 抖音精选联盟/行业公开政策（2026·非付费·公开）
  - GMV 大盘 → 艾瑞/QuestMobile/行业研报公开摘要
  - 星图报价公式 → 巨量星图公开定价模型（粉丝 × CPM 换算）
  - 比价 → 慢慢买 API（持牌·需企业资质 key·MVP 骨架预留）
"""
from __future__ import annotations

from typing import Any

# ── 公开行业数据查表（种子·定期对账官方政策页更新） ──────────────────────────────
# 来源：抖音精选联盟 2026 全品类最低 5%（官方公告）+ 行业研报公开摘要
# 各区间 = (最低%, 最高%) · 代表主流品类
_COMMISSION_TABLE: dict[str, tuple[float, float]] = {
    "美妆":     (20.0, 30.0),   # 彩妆/护肤/香水 · 精选联盟高佣品类
    "个护":     (18.0, 28.0),   # 个人护理/洗护
    "美食":     (15.0, 25.0),   # 食品饮料/零食/保健
    "母婴":     (12.0, 22.0),   # 母婴用品/玩具
    "服饰":     (10.0, 20.0),   # 服装/鞋帽/箱包
    "家居":     (10.0, 20.0),   # 家居日用/家纺
    "数码":     (5.0,  15.0),   # 手机/数码配件
    "家电":     (5.0,  12.0),   # 大家电/小家电
    "图书":     (10.0, 18.0),   # 图书/知识付费周边
    "知识付费": (20.0, 40.0),   # 课程/社群/专栏 · 无平台控价
    "本地服务": (5.0,  15.0),   # 团购/到店
    "全品类":   (5.0,  30.0),   # 兜底·平台最低 5% 官方要求
}

# GMV 大盘定性档位（来源：艾瑞 2025-2026 公开报告摘要 + 抖音电商官方公告）
# tier_label / approx_annual_gmv_cny / note
_GMV_TIER_TABLE: dict[str, dict[str, Any]] = {
    "美妆":     {"tier": "S级", "desc": "抖音电商第一大赛道·年 GMV 逾千亿"},
    "服饰":     {"tier": "S级", "desc": "与美妆并列抖音前两大赛道·合计 >50% 平台 GMV"},
    "食品":     {"tier": "A级", "desc": "高频复购·赛道年增速 >30%"},
    "母婴":     {"tier": "A级", "desc": "客单高·粉丝忠诚·赛道稳健"},
    "家居":     {"tier": "A级", "desc": "决策周期较长·直播间效果佳"},
    "数码":     {"tier": "B级", "desc": "品牌主导·KOL 佣金偏低·流量玩法受限"},
    "家电":     {"tier": "B级", "desc": "大品牌强势·KOL 空间有限"},
    "知识付费": {"tier": "S+级", "desc": "垂直精准·单用户 LTV 高·低流量高单价"},
    "本地服务": {"tier": "A级", "desc": "团购快速起量·但受地域限制"},
    "泛娱乐":   {"tier": "C级", "desc": "流量大变现弱·单粉价值 <1 元"},
}

# 星图报价 CPM 换算区间（来源：巨量星图公开参考定价 2025-2026）
# 实际报价 = max(粉丝 × CPM_low, 起步价) - max(粉丝 × CPM_high, 起步价)
_XINGTU_CPM_BY_TRACK: dict[str, tuple[float, float, int]] = {
    # track_keyword: (cpm_low 元/粉, cpm_high 元/粉, min_floor 元)
    "美妆":     (0.05, 0.15, 500),
    "数码":     (0.05, 0.12, 500),
    "家居":     (0.04, 0.10, 300),
    "母婴":     (0.05, 0.15, 500),
    "食品":     (0.03, 0.08, 300),
    "知识付费": (0.08, 0.20, 800),
    "财经":     (0.10, 0.30, 1000),
    "健康":     (0.08, 0.20, 800),
    "本地服务": (0.03, 0.08, 300),
    "_default": (0.03, 0.10, 300),  # 兜底
}


# ── 1. 品类佣金率区间 ─────────────────────────────────────────────────────────

def category_commission(category: str) -> dict[str, Any]:
    """品类佣金率区间（公开行业查表）。

    参数
        category: 品类名（模糊匹配·不区分大小写）

    返回
        {
          "category": str,        # 命中的标准品类名
          "rate_low_pct": float,  # 佣金率下限 %
          "rate_high_pct": float, # 佣金率上限 %
          "source": str,          # 数据来源说明
          "note": str,            # 使用说明
          "matched_input": str,   # 用户输入的 category
        }
    """
    cat_norm = category.strip().lower()
    matched_key = "全品类"
    for key in _COMMISSION_TABLE:
        if key in cat_norm or cat_norm in key:
            matched_key = key
            break
    low, high = _COMMISSION_TABLE[matched_key]
    return {
        "category": matched_key,
        "rate_low_pct": low,
        "rate_high_pct": high,
        "source": "抖音精选联盟官方政策 + 行业研报公开数据（2026）",
        "note": (
            "区间来自行业公开政策，实际佣金率因品牌和达人谈判而异。"
            "真实在投单品佣金请从精选联盟达人端查询（需账号授权）。"
        ),
        "matched_input": category,
    }


# ── 2. 赛道 GMV 体量档 ──────────────────────────────────────────────────────

def category_gmv_tier(category: str) -> dict[str, Any]:
    """赛道 GMV 大盘定性档位（公开研报摘要）。

    返回
        {
          "category": str,
          "tier": str,        # S+/S/A/B/C 级
          "desc": str,        # 定性描述
          "source": str,
          "warning": str,     # 诚实标：精确数字属黑盒
        }
    """
    cat_norm = category.strip()
    matched_key: str | None = None
    for key in _GMV_TIER_TABLE:
        if key in cat_norm or cat_norm in key:
            matched_key = key
            break
    if matched_key is None:
        return {
            "category": cat_norm,
            "tier": "未知",
            "desc": "该品类暂无公开 GMV 分级数据",
            "source": "—",
            "warning": "精确 GMV 数字属平台黑盒，仅精选联盟/抖音官方报告有定向披露。",
        }
    info = _GMV_TIER_TABLE[matched_key]
    return {
        "category": matched_key,
        "tier": info["tier"],
        "desc": info["desc"],
        "source": "艾瑞 / QuestMobile 2025-2026 公开报告摘要 + 抖音电商官方公告",
        "warning": (
            "精确 GMV 数字（品类/赛道级别）未公开，此处为定性档位。"
            "蝉妈妈等第三方平台的精确数字仅供方向参考，不作精确结论（合规红线）。"
        ),
    }


# ── 3. 星图广告报价估算 ──────────────────────────────────────────────────────

def xingtu_price_estimate(follower: int, track: str = "") -> dict[str, Any]:
    """星图广告报价区间估算（公式：粉丝 × CPM 换算）。

    依据：巨量星图公开参考定价模型 2025-2026。
    实际签单价受互动率/垂直度/独家条款影响，此处为理论区间。

    参数
        follower: 粉丝量
        track:    赛道（用于选 CPM 区间·可空）

    返回
        {
          "follower": int,
          "price_low_cny": float,   # 报价下限（元）
          "price_high_cny": float,  # 报价上限（元）
          "cpm_track_key": str,     # 命中的 CPM 档
          "formula": str,           # 公式说明
          "source": str,
          "calibration_note": str,  # 校准说明
        }
    """
    if follower <= 0:
        return {
            "follower": follower,
            "price_low_cny": 0.0,
            "price_high_cny": 0.0,
            "cpm_track_key": "—",
            "formula": "粉丝量为 0，无法估算",
            "source": "—",
            "calibration_note": "请传入有效粉丝量。",
        }

    # 选 CPM 档
    track_norm = track.strip()
    cpm_key = "_default"
    for k in _XINGTU_CPM_BY_TRACK:
        if k == "_default":
            continue
        if k in track_norm or track_norm in k:
            cpm_key = k
            break
    cpm_low, cpm_high, floor = _XINGTU_CPM_BY_TRACK[cpm_key]

    price_low = max(follower * cpm_low, float(floor))
    price_high = max(follower * cpm_high, float(floor))

    return {
        "follower": follower,
        "price_low_cny": round(price_low, 0),
        "price_high_cny": round(price_high, 0),
        "cpm_track_key": cpm_key if cpm_key != "_default" else "通用",
        "formula": f"粉丝({follower:,}) × CPM({cpm_low}-{cpm_high}元/粉) · 保底{floor}元",
        "source": "巨量星图公开参考定价模型（2025-2026）",
        "calibration_note": (
            "理论报价区间，实际签单受互动率/垂直度/排他条款影响。"
            "互动率 >5% 可上浮 20-50%；冷门赛道/低互动可能低于下限。"
            "真实市场价需看近期同体量同赛道达人实际报价（仅账号主自知）。"
        ),
    }


# ── 4. 商品比价骨架（慢慢买 API 预留·MVP 降级）───────────────────────────────

def price_compare(product_name: str, *, _api_key: str | None = None) -> dict[str, Any]:
    """商品历史比价（慢慢买 API 骨架·MVP 返回降级结构）。

    真实接入条件：
      1. 企业资质申请慢慢买开放平台 key（https://open.manmanbuy.com/）
      2. 将 key 写入 ~/vault/credentials/api/manmanbuy-api-key.txt
      3. 实例化时传入 _api_key（或从 vault 读取）

    MVP 阶段返回
        {
          "available": False,
          "product_name": str,
          "note": str,             # 指引接入方式
          "mock_example": dict,    # 结构示例（说明字段含义·供开发对齐）
        }
    """
    # 真实 API 路径（骨架·key 就绪后替换 pass 体）
    if _api_key:
        # TODO: 接入慢慢买开放平台 API
        # GET https://open.manmanbuy.com/openAPI/priceHistory
        # params: {"appKey": _api_key, "url": <商品 URL>}
        # 返回字段: current_price / lowest_price / highest_price / price_history[]
        raise NotImplementedError(
            "慢慢买 API key 已传入但实现待接——"
            "请在此处对接 open.manmanbuy.com 接口。"
        )

    return {
        "available": False,
        "product_name": product_name,
        "note": (
            "商品比价功能需接入慢慢买开放平台 API（持牌·商业资质）。"
            "MVP 阶段可由用户提供商品历史价格截图（投喂补充）。"
            "接入路径：企业申请 key → vault/credentials/api/manmanbuy-api-key.txt"
        ),
        "mock_example": {
            "current_price_cny": "用户/商品页实时价",
            "lowest_30d_cny": "近 30 日最低价",
            "highest_30d_cny": "近 30 日最高价",
            "vs_avg_pct": "相对均价偏差 % （正=偏贵·负=偏低）",
            "source": "慢慢买开放平台（商业持牌·数据可信）",
        },
    }


# ── 5. 报告"商业数据参考"段渲染 ──────────────────────────────────────────────

def render_commercial_data_section(
    account: dict[str, Any],
    track: str,
    biz_data: dict[str, Any] | None = None,
) -> str:
    """生成报告中"商业数据参考"段（说人话·标来源·🔴黑盒诚实标）。

    参数
        account:  账号基础数据（follower/nickname 等）
        track:    赛道名（由 account_report._track() 推断后传入）
        biz_data: 可选·账号主投喂的商业后台数据（🔴黑盒补充）
                  格式自由·有啥用啥·无则 None
    """
    follower = account.get("follower") or 0
    nickname = account.get("nickname") or "该账号"

    # 1. 品类佣金
    comm = category_commission(track)
    # 2. GMV 体量
    gmv = category_gmv_tier(track)
    # 3. 星图估值
    xt = xingtu_price_estimate(follower, track)

    L: list[str] = [
        "## 商业数据参考（合规公开数据 · 标黑盒缺口）",
        "",
        f"> 以下数据来自公开行业资料，标注了哪些真实可信、哪些是黑盒——"
        f"**宁可告诉你「没接到」，也不瞎编数字**。",
        "",
    ]

    # —— 赛道商业价值 ——
    L.append("### 1️⃣ 你所在赛道的商业体量")
    if gmv["tier"] != "未知":
        L.append(
            f"- **{track}** 是 **{gmv['tier']} 赛道**：{gmv['desc']}。"
        )
    else:
        L.append(f"- 「{track}」赛道暂无公开 GMV 分级数据，建议参考艾瑞/QuestMobile 行业报告。")
    L.append(f"  - ⚠️ {gmv['warning']}")
    L.append(f"  - 📌 数据来源：{gmv['source']}")
    L.append("")

    # —— 品类佣金率 ——
    L.append("### 2️⃣ 带货/合作佣金率参考")
    L.append(
        f"- **{comm['category']}** 品类行业佣金率通常在 "
        f"**{comm['rate_low_pct']:.0f}% – {comm['rate_high_pct']:.0f}%**。"
    )
    L.append(
        f"- 如果你目前的佣金率低于 {comm['rate_low_pct']:.0f}%，可以和品牌方谈——"
        f"这个品类的空间通常到得了 {comm['rate_high_pct']:.0f}%。"
    )
    L.append(f"  - 📌 {comm['note']}")
    L.append(f"  - 📌 数据来源：{comm['source']}")
    L.append("")

    # —— 星图广告报价估算 ——
    L.append("### 3️⃣ 广告合作理论报价区间（星图参考）")
    if follower >= 5000:
        L.append(
            f"- {nickname} 目前 **{follower:,} 粉丝**，理论广告报价区间约 "
            f"**¥{xt['price_low_cny']:,.0f} – ¥{xt['price_high_cny']:,.0f} / 条**。"
        )
        L.append(f"  - 公式：{xt['formula']}")
        L.append(f"  - 📌 {xt['calibration_note']}")
        L.append(f"  - 📌 数据来源：{xt['source']}")
    else:
        L.append(
            f"- {nickname} 目前粉丝量 {follower:,}，通常低于 5000 粉时广告商单较难接洽。"
            f"先做粉丝积累，待过万后报价会更清晰。"
        )
    L.append("")

    # —— 商品比价（黑盒·投喂补）——
    L.append("### 4️⃣ 商品比价 · 带货品竞争力")
    L.append(
        "- 🔴 **商品历史比价（真实价格 vs 历史均价）**：需接慢慢买开放 API——"
        "MVP 阶段暂未接入，可由你提供商品详情页截图来补充诊断。"
    )
    L.append(
        "- 核心诊断问题：你挂的链接定价是偏高还是偏低？佣金率高不高？"
        "这两个点对转化率影响超过 80% 的内容质量——"
        "**东西再好，贵于市场均价 20%+，转化就卡在价格**。"
    )
    L.append("")

    # —— 🔴 黑盒缺口诚实清单 ——
    L.append("### ⚠️ 这些还是黑盒·拿不到·诚实告你")
    blackbox_items = [
        "真实销量（GMV·商品维度）— 平台不公开·只有品牌方知道",
        "完播率 / 流量来源 / 粉丝画像 — 罗盘后台·只有账号主有",
        "商单实际成交价 — 主播/机构内部数据",
        "蝉妈妈等第三方平台的精确数字 — 仅作方向参考·禁作精确结论（合规红线）",
    ]
    for item in blackbox_items:
        L.append(f"- 🔴 {item}")

    # —— 🔴 投喂补充引导 ——
    if biz_data:
        L.append("")
        L.append("### 💬 你补充的商业后台数据")
        L.append("（以下来自账号主提供的投喂数据·仅用于本次诊断·不对外传播）")
        for k, v in biz_data.items():
            L.append(f"- {k}：{v}")
    else:
        L.append("")
        L.append(
            "> 💡 **想要更准确的诊断？** "
            "把带货后台截图（完播率、销量、流量来源）发给我，"
            "可以给出针对你真实数据的定制化分析——黑盒靠投喂补，诚实比猜测有用。"
        )

    L.append("")
    L.append(
        "> 商业数据来源：公开行业政策/研报（佣金率/GMV档）+ 巨量星图公开定价模型（报价）。"
        "慢慢买比价/精选联盟真实佣金/罗盘黑盒数据待账号主授权后接入。"
        "平台算法权重永久黑盒，谁说得精确都是猜的，本报告不作硬结论。"
    )

    return "\n".join(L)

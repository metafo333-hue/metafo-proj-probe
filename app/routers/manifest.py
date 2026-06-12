"""GET /api/v1/manifest · ② 画像契约（喂 L4 推荐 + 矩阵三维标签）。"""
from __future__ import annotations

from fastapi import APIRouter

from app import config

router = APIRouter(prefix="/api/v1", tags=["manifest"])


def manifest_data() -> dict:
    return {
        "name": "probe",
        "subdomain": config.SUBDOMAIN,
        "industry": ["自媒体", "金融"],
        "angle": ["链接分析", "数据采集", "链接二创", "视频诊断"],
        "pricing_tier": "免费+付费",
        "solves": "给任意链接→10秒内知道「值不值得做、怎么做、有没有风险」：公开提取正文(免费) + D2结构公式+D7借换串二创方案+D1联网真相核查(付费深探)。面向自媒体创作者的链接情报参谋。",
        "sample_input": "深探这条链接 https://example.com/article",
        "sample_output": "A/B/C/D评级 + 结构公式 + 借换串三路二创方案 + 真相核查（免费看评级/付费看完整报告）",
        "capabilities": {
            "A线·素材提取": ["文章正文MD", "GitHub/PDF→Markdown"],
            "B线·分析(LLM+联网)": ["D2结构拆解", "D7二创路径(借换串)", "D1真相核查(AnySearch联网)"],
            "B线·分析(待TikHub key)": ["D5竞品横评", "D6发布者画像", "D4出处溯源"],
            "phase2": ["D3视觉拆解", "ASR字幕", "D9 IP适配"],
        },
        "data_policy": {
            "sources": "仅第三方授权 API / 官方 API（核心红线：不自己爬数据·不自建爬虫·不模拟登录；绕反爬由第三方供应商担责）",
            "principle": "原料进结论出（第三方原始数据不直吐，加工成独有结论）",
            "account": "0 接管（不持用户账号凭据）",
            "privacy": "仅公开元数据 · 不建个人档案 · 守个保法最小必要（普通≥5000/敏感≥500 入刑）",
            "aigc": "结论标注 aigc_flag",
        },
        "version": config.CONTRACT_VERSION,
    }


@router.get("/manifest")
def manifest() -> dict:
    return {"code": 0, "data": manifest_data(), "msg": "ok"}

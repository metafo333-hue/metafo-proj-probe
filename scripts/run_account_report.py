#!/usr/bin/env python3
"""一条命令:抖音视频链接 → 综合分析报告。

用法:
    export TIKHUB_API_KEY=<key>   # 走 vault·不入仓
    python scripts/run_account_report.py "<抖音视频链接>"
输出:markdown 综合报告(BLUF + 满足 + 高于期望 + 处方 + 担保)。
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.services.account_chain import run_from_video_url


def main() -> int:
    if len(sys.argv) < 2:
        print('用法: python scripts/run_account_report.py "<抖音视频链接>"')
        return 1
    res = run_from_video_url(sys.argv[1])
    if not res.get("ok"):
        print("❌ 失败:", res.get("error"))
        return 2
    print(res["report_md"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

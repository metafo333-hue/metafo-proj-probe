"""L1 成品落对象存储 + 下载 URL（02-api §1 deliverable 落存储）。

MVP：本地目录 + 公网静态 URL（probe.metafoclaw.com/files/<task>/<name>）。
生产：MinIO / 天翼云 OSS + 短时预签名 URL + TTL 即用即抛（社交类最短 TTL）。
"""
from __future__ import annotations

from pathlib import Path

from app import config


def put_deliverable(task_id: str, files: dict[str, str]) -> list[dict]:
    """files: {filename: text_content} → 落盘 → [{name,url,size}]。"""
    base = Path(config.STORAGE_DIR) / task_id
    base.mkdir(parents=True, exist_ok=True)
    out: list[dict] = []
    for name, content in files.items():
        p = base / name
        p.write_text(content, encoding="utf-8")
        out.append({
            "name": name,
            "url": f"{config.PUBLIC_BASE}/files/{task_id}/{name}",
            "size": len(content.encode("utf-8")),
        })
    return out

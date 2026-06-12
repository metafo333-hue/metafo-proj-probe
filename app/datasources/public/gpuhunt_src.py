"""GPU 实时价格 · gpuhunt 库 · 无需 key · 免费。

数据源：
  gpuhunt.Catalog  — 聚合 AWS/Azure/GCP/Lambda/RunPod/Nebius/OCI/CloudRift/Verda 等
                     13 云（库按批次刷新 catalog，离线可读）
  catalog raw JSON — S3 公开 bucket，gpuhunt 内部自动拉取

合规：gpuhunt 为 MIT License（dstackai/gpuhunt），数据均来自各云官方公开价格页面。
     本模块仅调库接口，不直接爬云厂商网站。
失败返回空，不抛出。
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any

META: dict[str, Any] = {
    "id": "gpuhunt_src",
    "domain": ["D17", "D15"],
    "access_type": "free",
    "method": ["L", "W"],
    "kinds": ["gpu_price", "cloud_compute"],
}

_TIMEOUT = 60  # S3 catalog 下载较大
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com)",
}

# 模块级缓存
_catalog_cache: Any = None  # gpuhunt.Catalog instance


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def _get_catalog(force_reload: bool = False) -> Any:
    """获取或创建 gpuhunt Catalog 实例（带 module-level 缓存）。"""
    global _catalog_cache
    if _catalog_cache is None or force_reload:
        try:
            import gpuhunt  # noqa: PLC0415
            cat = gpuhunt.Catalog(auto_reload=False)
            cat.load()
            _catalog_cache = cat
        except Exception:
            return None
    return _catalog_cache


def query_gpu_prices(
    gpu_name: str | list[str] | None = None,
    provider: str | list[str] | None = None,
    max_price: float | None = None,
    min_gpu_memory: float | None = None,
    spot: bool | None = None,
    top_n: int = 50,
    force_reload: bool = False,
) -> list[dict[str, Any]]:
    """查询 GPU 实例价格（多云聚合）。

    Args:
        gpu_name:       GPU 名称过滤，如 "A100" / "H100" / ["A100", "V100"]
        provider:       云厂商过滤，如 "aws" / "gcp" / ["aws", "lambdalabs"]
                        可选值: aws / azure / gcp / lambdalabs / runpod / nebius /
                                oci / cloudrift / verda
        max_price:      最高时价（USD/h）
        min_gpu_memory: 最小 GPU 显存（GB），如 16.0 / 40.0 / 80.0
        spot:           True = 仅 spot · False = 仅按需 · None = 全部
        top_n:          最多返回条数（1-500）
        force_reload:   True = 强制重新下载 catalog

    Returns:
        [{"provider", "instance_name", "location", "gpu_name", "gpu_count",
          "gpu_memory_gb", "gpu_vendor", "cpu", "memory_gb", "price_usd_h",
          "spot", "source_id"}] 或空列表。
    """
    cat = _get_catalog(force_reload=force_reload)
    if cat is None:
        return []
    try:
        kwargs: dict[str, Any] = {"min_gpu_count": 1}
        if gpu_name is not None:
            kwargs["gpu_name"] = gpu_name
        if provider is not None:
            kwargs["provider"] = provider
        if max_price is not None:
            kwargs["max_price"] = max_price
        if min_gpu_memory is not None:
            kwargs["min_gpu_memory"] = min_gpu_memory
        if spot is not None:
            kwargs["spot"] = spot

        items = cat.query(**kwargs)
        results: list[dict[str, Any]] = []
        for item in items[:max(1, min(top_n, 500))]:
            results.append(_normalize_item(item))
        return results
    except Exception:
        return []


def cheapest_by_gpu(
    gpu_names: list[str] | None = None,
    spot: bool | None = None,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """按 GPU 型号取最低价，便于快速比价。

    Args:
        gpu_names: 关注的 GPU 列表，如 ["A100", "H100", "A10G"]；None = 全部
        spot:      True = 仅 spot · False = 仅按需 · None = 混合
        top_n:     每种 GPU 返回最多 N 条最低价

    Returns:
        按 gpu_name → price_usd_h 升序排列的条目列表。
    """
    all_items = query_gpu_prices(
        gpu_name=gpu_names, spot=spot, top_n=2000
    )
    if not all_items:
        return []
    # 按 gpu_name 分组取最低 top_n
    from collections import defaultdict
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in all_items:
        groups[item["gpu_name"]].append(item)
    results: list[dict[str, Any]] = []
    for gpu, group in sorted(groups.items()):
        group_sorted = sorted(group, key=lambda x: (x["price_usd_h"] or 99999))
        results.extend(group_sorted[:top_n])
    return results


def provider_summary() -> list[dict[str, Any]]:
    """汇总各云厂商 GPU 实例数量与最低价格。

    Returns:
        [{"provider", "gpu_instance_count", "min_price_usd_h",
          "gpu_types", "source_id"}] 或空列表。
    """
    all_items = query_gpu_prices(top_n=10000)
    if not all_items:
        return []
    from collections import defaultdict
    providers: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "min_price": 99999.0, "gpu_types": set()}
    )
    for item in all_items:
        p = item["provider"]
        providers[p]["count"] += 1
        price = item["price_usd_h"]
        if price is not None and price < providers[p]["min_price"]:
            providers[p]["min_price"] = price
        gpu = item["gpu_name"]
        if gpu:
            providers[p]["gpu_types"].add(gpu)
    results = []
    for p_name, stats in sorted(providers.items()):
        results.append({
            "provider": p_name,
            "gpu_instance_count": stats["count"],
            "min_price_usd_h": round(stats["min_price"], 4) if stats["min_price"] < 99999 else None,
            "gpu_types": sorted(stats["gpu_types"]),
            "source_id": META["id"],
        })
    return results


def _normalize_item(item: Any) -> dict[str, Any]:
    """标准化 gpuhunt CatalogItem。"""
    gpu_vendor = getattr(item, "gpu_vendor", None)
    cpu_arch = getattr(item, "cpu_arch", None)
    return {
        "provider": getattr(item, "provider", ""),
        "instance_name": getattr(item, "instance_name", ""),
        "location": getattr(item, "location", ""),
        "gpu_name": getattr(item, "gpu_name", ""),
        "gpu_count": getattr(item, "gpu_count", 1),
        "gpu_memory_gb": getattr(item, "gpu_memory", None),
        "gpu_vendor": str(gpu_vendor.value) if gpu_vendor else "",
        "cpu": getattr(item, "cpu", None),
        "memory_gb": getattr(item, "memory", None),
        "disk_size_gb": getattr(item, "disk_size", None),
        "price_usd_h": getattr(item, "price", None),
        "spot": getattr(item, "spot", False),
        "cpu_arch": str(cpu_arch.value) if cpu_arch else "",
        "flags": list(getattr(item, "flags", []) or []),
        "source_id": META["id"],
    }

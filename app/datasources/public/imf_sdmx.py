"""IMF SDMX · 国际货币基金组织官方数据 API · 无需 key · 免费 · 公有领域。

端点（SDMX_JSON）：
  dataflow_list  GET https://dataservices.imf.org/REST/SDMX_JSON.svc/Dataflow
  series         GET https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/{dataset}/{key}

合规：IMF Data Services 官方 REST API，数据为公有领域，商业使用合法。
失败返回空，不抛出。

常用数据集：
  IFS   - 国际金融统计 (CPI/汇率/利率/储备)
  BOP   - 国际收支
  WEO   - 世界经济展望（每年两次发布）
  DOT   - 贸易方向
  GFSR  - 全球金融稳定报告数据
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "imf_sdmx",
    "domain": ["D14", "D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["macro", "indicator", "fx", "rate"],
}

_API_BASE = "https://dataservices.imf.org/REST/SDMX_JSON.svc"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def dataflow_list() -> list[dict[str, Any]]:
    """列出 IMF 所有可用数据集（Dataflow）。

    Returns:
        [{"id", "name", "source_id"}] 或空列表。
    """
    url = f"{_API_BASE}/Dataflow"
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        # Structure → Dataflows → Dataflow
        dataflows = (
            data.get("Structure", {})
            .get("Dataflows", {})
            .get("Dataflow", [])
        )
        if not isinstance(dataflows, list):
            dataflows = [dataflows] if dataflows else []
        results: list[dict[str, Any]] = []
        for df in dataflows:
            if not isinstance(df, dict):
                continue
            names = df.get("Name", {})
            # Name 可能是 {"#text": "...", "@xml:lang": "en"} 或 list
            if isinstance(names, list):
                name_text = next(
                    (n.get("#text", "") for n in names if n.get("@xml:lang") == "en"),
                    ""
                )
            elif isinstance(names, dict):
                name_text = names.get("#text", "")
            else:
                name_text = str(names)
            results.append({
                "id": df.get("@id", ""),
                "name": name_text[:200],
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def compact_data(
    dataset: str,
    key: str = "all",
    start_period: str = "",
    end_period: str = "",
) -> list[dict[str, Any]]:
    """查询 IMF 紧凑格式时间序列数据。

    Args:
        dataset:      数据集 ID，如 "IFS"（国际金融统计）/ "BOP" / "DOT"
        key:          维度过滤键，格式依数据集而定。
                      例 IFS："{freq}.{country}.{indicator}"
                      如 "M.CN.PCPI_IX"（中国月度CPI）
                      用 "all" 可获取全部（数据量大，建议指定）
        start_period: 起始期，如 "2020" 或 "2020-01"（可选）
        end_period:   结束期，如 "2024" 或 "2024-12"（可选）

    Returns:
        [{"series_key", "obs_list": [{"period", "value"}], "source_id"}] 或空列表。
    """
    url = f"{_API_BASE}/CompactData/{dataset}/{key}"
    params: dict[str, str] = {}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        # CompactData → DataSet → Series
        dataset_obj = data.get("CompactData", {}).get("DataSet", {})
        series_list = dataset_obj.get("Series", [])
        if isinstance(series_list, dict):
            series_list = [series_list]
        if not isinstance(series_list, list):
            return []

        results: list[dict[str, Any]] = []
        for s in series_list:
            if not isinstance(s, dict):
                continue
            # 构建 series_key（所有 @ 开头属性）
            attrs = {k.lstrip("@"): v for k, v in s.items() if k.startswith("@")}
            obs_raw = s.get("Obs", [])
            if isinstance(obs_raw, dict):
                obs_raw = [obs_raw]
            obs_list: list[dict[str, Any]] = []
            for obs in (obs_raw or []):
                if not isinstance(obs, dict):
                    continue
                obs_list.append({
                    "period": obs.get("@TIME_PERIOD", ""),
                    "value": obs.get("@OBS_VALUE"),
                })
            results.append({
                "series_key": attrs,
                "obs_list": obs_list,
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


def ifs_indicator(
    country_code: str,
    indicator: str,
    freq: str = "M",
    start_period: str = "",
    end_period: str = "",
) -> list[dict[str, Any]]:
    """查询 IFS（国际金融统计）指标时序（便捷封装）。

    Args:
        country_code: IMF 国家码，如 "CN"（中国）/ "US" / "JP"
        indicator:    IFS 指标代码，如 "PCPI_IX"（CPI）/ "ENDA_XDC_USD_R"（汇率）
        freq:         频率 "M"（月）/ "Q"（季）/ "A"（年）
        start_period: 起始期，如 "2020-01"
        end_period:   结束期，如 "2024-12"

    Returns:
        [{"period", "value", "country", "indicator", "freq", "source_id"}] 或空列表。
    """
    key = f"{freq}.{country_code}.{indicator}"
    series = compact_data("IFS", key, start_period, end_period)
    results: list[dict[str, Any]] = []
    for s in series:
        for obs in s.get("obs_list", []):
            results.append({
                "period": obs["period"],
                "value": obs["value"],
                "country": country_code,
                "indicator": indicator,
                "freq": freq,
                "source_id": META["id"],
            })
    return results

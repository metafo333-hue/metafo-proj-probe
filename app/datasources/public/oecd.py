"""OECD SDMX · 经济合作与发展组织官方数据 API · 无需 key · 免费 · 公有领域。

端点（SDMX REST）：
  data    GET https://sdmx.oecd.org/public/rest/data/{agencyId},{flowRef},{version}/{key}
  flow    GET https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.NAD
合规：OECD SDMX API 官方公共访问，数据 CC BY 4.0 / OECD Terms，允许商业使用（须署名）。
失败返回空，不抛出。

常用数据流（flowRef 示例）：
  OECD.SDD.NAD,DSD_NAMAIN10@DF_TABLE1_EXPENDITURE,1.0  - 国民账户支出
  OECD.SDD.TPS,DSD_BOP@DF_BOP,1.0                      - 国际收支
  OECD.SDD.STES,DSD_KEI@DF_KEI,2.2                     - 主要经济指标 KEI

注意：SDMX REST v1.4 + JSON 格式，format 参数用 application/vnd.sdmx.data+json
"""
from __future__ import annotations

from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "oecd",
    "domain": ["D14", "D13"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["macro", "indicator", "rate"],
}

_API_BASE = "https://sdmx.oecd.org/public/rest"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/vnd.sdmx.data+json;version=1.0",
}
# 某些端点支持标准 JSON
_JSON_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def get_data(
    flow_ref: str,
    key: str = "all",
    start_period: str = "",
    end_period: str = "",
    last_n_observations: int = 0,
) -> dict[str, Any]:
    """获取 OECD SDMX 数据（原始 SDMX-JSON 结构）。

    Args:
        flow_ref:              数据流引用，格式 "{agencyId},{flowId},{version}"
                               如 "OECD.SDD.STES,DSD_KEI@DF_KEI,2.2"
        key:                   维度过滤键，"all" 取全部，或如 "M.USA+CHN...."
        start_period:          起始期，如 "2020-Q1" / "2020"
        end_period:            结束期，如 "2024-Q4"
        last_n_observations:   仅返回最后 N 个观测值（0 = 不限）

    Returns:
        原始 SDMX-JSON dict（含 data.dataSets 等），或空 dict。
    """
    # flow_ref 含逗号需编码为路径段，OECD API 接受 agency,flow,version
    url = f"{_API_BASE}/data/{flow_ref}/{key}"
    params: dict[str, str] = {"format": "jsondata"}
    if start_period:
        params["startPeriod"] = start_period
    if end_period:
        params["endPeriod"] = end_period
    if last_n_observations > 0:
        params["lastNObservations"] = str(last_n_observations)
    try:
        r = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return {}
        data = r.json()
        data["_source_id"] = META["id"]
        return data
    except Exception:
        return {}


def get_observations(
    flow_ref: str,
    key: str = "all",
    start_period: str = "",
    end_period: str = "",
    last_n_observations: int = 10,
    max_series: int = 50,
) -> list[dict[str, Any]]:
    """获取 OECD 数据并展平为观测值列表（便捷封装）。

    Args:
        flow_ref:            数据流引用
        key:                 维度过滤
        start_period:        起始期
        end_period:          结束期
        last_n_observations: 每序列最后 N 个观测值
        max_series:          最多返回多少序列

    Returns:
        [{"dims", "time_period", "value", "flow_ref", "source_id"}] 或空列表。
    """
    raw = get_data(flow_ref, key, start_period, end_period, last_n_observations)
    if not raw:
        return []
    try:
        data_section = raw.get("data", {})
        data_sets = data_section.get("dataSets", [])
        structures = data_section.get("structures", [])
        if not data_sets or not structures:
            return []

        structure = structures[0]
        dimensions_obs = (
            structure.get("dimensions", {}).get("observation", [])
        )
        dimensions_series = (
            structure.get("dimensions", {}).get("series", [])
        )
        # 构建 dimension label lookup
        def _labels(dims_list: list) -> list[list[str]]:
            result = []
            for d in dims_list:
                vals = d.get("values", [])
                result.append([v.get("name", v.get("id", "")) for v in vals])
            return result

        series_labels = _labels(dimensions_series)
        obs_labels = _labels(dimensions_obs)

        dataset = data_sets[0]
        series_map = dataset.get("series", {})

        results: list[dict[str, Any]] = []
        for series_key_str, series_val in list(series_map.items())[:max_series]:
            # series_key_str: "0:1:2:..." 索引
            s_indices = [int(i) for i in series_key_str.split(":")]
            s_dims: dict[str, str] = {}
            for i, dim_def in enumerate(dimensions_series):
                idx = s_indices[i] if i < len(s_indices) else 0
                label_list = series_labels[i]
                s_dims[dim_def.get("id", f"d{i}")] = (
                    label_list[idx] if idx < len(label_list) else str(idx)
                )
            obs_map = series_val.get("observations", {})
            for obs_key_str, obs_val_list in obs_map.items():
                o_indices = [int(i) for i in obs_key_str.split(":")]
                time_label = ""
                if dimensions_obs:
                    idx = o_indices[0] if o_indices else 0
                    tp_labels = obs_labels[0] if obs_labels else []
                    time_label = tp_labels[idx] if idx < len(tp_labels) else str(idx)
                value = obs_val_list[0] if obs_val_list else None
                results.append({
                    "dims": s_dims,
                    "time_period": time_label,
                    "value": value,
                    "flow_ref": flow_ref,
                    "source_id": META["id"],
                })
        return results
    except Exception:
        return []


def dataflow_list(agency_id: str = "OECD") -> list[dict[str, Any]]:
    """列出指定机构的可用数据流。

    Args:
        agency_id: 机构 ID，如 "OECD"

    Returns:
        [{"id", "name", "agency", "source_id"}] 或空列表。
    """
    url = f"{_API_BASE}/dataflow/{agency_id}"
    params = {"references": "none"}
    try:
        r = httpx.get(url, params=params, headers=_JSON_HEADERS, timeout=_TIMEOUT)
        if r.status_code != 200:
            return []
        data = r.json()
        dfs = (
            data.get("data", {})
            .get("dataflows", [])
        )
        results: list[dict[str, Any]] = []
        for df in (dfs or []):
            if not isinstance(df, dict):
                continue
            names = df.get("names", {})
            name_en = names.get("en", names.get("fr", "")) if isinstance(names, dict) else ""
            results.append({
                "id": df.get("id", ""),
                "name": name_en[:200],
                "agency": df.get("agencyID", agency_id),
                "source_id": META["id"],
            })
        return results
    except Exception:
        return []


# ── stats.oecd.org 旧 SDMX-JSON API（实测可达，作为主用） ─────────────────────

_STATS_BASE = "https://stats.oecd.org/SDMX-JSON/data"
_STATS_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; probe@metafoclaw.com)",
    "Accept": "application/json",
}


def kei(
    indicator: str = "CPALTT01",
    country: str = "USA",
    freq: str = "M",
    start_period: str = "2023-01",
    end_period: str = "",
    last_n: int = 12,
) -> dict[str, Any]:
    """OECD 主要经济指标（Key Economic Indicators · stats.oecd.org）。

    Args:
        indicator:    KEI 指标代码，如
                      "CPALTT01"（CPI）/ "LRUNTTTT"（失业率）/ "OECD_MEI_OB"（财政余额）
                      / "BPBLTT01"（国际收支）/ "IRLTLT01"（长期利率）
        country:      OECD 国家码，如 "USA" / "CHN" / "DEU" / "JPN" / "GBR"
        freq:         频率 "M"（月）/ "Q"（季）/ "A"（年）
        start_period: 起始期，如 "2023-01"
        end_period:   结束期（空=最新）
        last_n:       最近 N 个观测值（0=不限）

    Returns:
        {"indicator", "country", "freq", "observations": [{"period","value"}],
         "source_id"} 或空 dict。
    """
    # stats.oecd.org SDMX-JSON 路径格式: /{dataset}/{series_key}/all
    series_key = f"{indicator}.{country}.ST.{freq}"
    url = f"{_STATS_BASE}/KEI/{series_key}/all"
    params: dict[str, str] = {}
    if start_period:
        params["startTime"] = start_period
    if end_period:
        params["endTime"] = end_period
    if last_n > 0:
        params["lastNObservations"] = str(last_n)
    try:
        r = httpx.get(url, params=params, headers=_STATS_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return {}
        data = r.json()
        # SDMX-JSON v2 格式：data.dataSets + data.structures
        data_section = data.get("data", data)  # 兼容新旧格式
        ds_list = data_section.get("dataSets", [])
        if not ds_list:
            return {}
        obs_map = ds_list[0].get("series", {})
        # 时间维度标签从 data.structures 获取
        structures = data_section.get("structures", [data.get("structure", {})])
        dims_obs: list = []
        if structures:
            dims_obs = (
                structures[0]
                .get("dimensions", {})
                .get("observation", [])
            )
        time_labels: list[str] = []
        if dims_obs:
            time_labels = [v.get("id", "") for v in dims_obs[0].get("values", [])]
        # 只取 key 匹配 country 的 series（key 格式 "idx:0:idx:0:..."）
        # series_key 维度太复杂，取全部 obs 后合并
        points: list[dict[str, Any]] = []
        seen_periods: set = set()
        for _sk, sv in obs_map.items():
            obs = sv.get("observations", {})
            for obs_key, obs_val in obs.items():
                idx = int(obs_key)
                period = time_labels[idx] if idx < len(time_labels) else obs_key
                if period in seen_periods:
                    continue
                seen_periods.add(period)
                value = obs_val[0] if isinstance(obs_val, list) and obs_val else obs_val
                points.append({"period": period, "value": value})
        # 按期排序，取最新 last_n
        points.sort(key=lambda x: x["period"])
        if last_n > 0:
            points = points[-last_n:]
        return {
            "indicator": indicator,
            "country": country,
            "freq": freq,
            "observations": points,
            "source_id": META["id"],
        }
    except Exception:
        return {}

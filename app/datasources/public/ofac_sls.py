"""OFAC SDN · 美国财政部 OFAC 制裁名单（Specially Designated Nationals）。

端点（已验证可达）：
  SDN XML  GET https://www.treasury.gov/ofac/downloads/sdn.xml           — 完整 SDN XML（~2-3MB）
  合并名单 GET https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml — OFAC+UN+其他

合规：OFAC 制裁名单是美国政府官方公开数据，属于公有领域（U.S. Government Works）。
      官方地址：https://ofac.treasury.gov
      无 REST 搜索 API，本模块下载全量 XML 后本地解析搜索。
      ⚠️ 全量 XML ~2-3 MB，禁高频下载（建议缓存本地，按日更新；每次调用均触发下载）。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "ofac_sls",
    "domain": ["D8"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["sanctions", "sdn", "compliance"],
}

_SDN_XML_URL = "https://www.treasury.gov/ofac/downloads/sdn.xml"
_CONSOLIDATED_XML_URL = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.xml"
_TIMEOUT = 60   # 完整 XML 下载需要较长超时
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; compliance-research)",
    "Accept": "application/xml, text/xml, */*",
}


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def search_sdn(
    name: str,
    max_results: int = 20,
    consolidated: bool = False,
) -> list[dict[str, Any]]:
    """下载 OFAC SDN XML 并按名称搜索（全量下载 + 本地过滤）。

    ⚠️ 每次调用均触发完整 XML 下载（~2-3 MB），建议业务层做本地缓存。

    Args:
        name:         搜索关键词（姓名/实体名·大小写不敏感·部分匹配）
        max_results:  最多返回条数（1-200）
        consolidated: True = 使用合并名单（含 UN/EU/其他）；False = 仅 OFAC SDN

    Returns:
        [{"uid", "name", "type", "programs", "title", "remarks", "source_id"}] 或空列表。
    """
    url = _CONSOLIDATED_XML_URL if consolidated else _SDN_XML_URL
    try:
        r = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        # XML 命名空间
        ns_map = {
            "ofac": "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML",
        }
        # 尝试有命名空间和无命名空间两种
        entries = root.findall(".//sdnEntry") or root.findall(".//{https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XML}sdnEntry")
        if not entries:
            # 尝试任意命名空间
            entries = [e for e in root.iter() if e.tag.endswith("sdnEntry")]
        query = name.lower()
        results: list[dict[str, Any]] = []
        for entry in entries:
            normalized = _normalize_xml_entry(entry)
            if query in normalized.get("name", "").lower():
                results.append(normalized)
                if len(results) >= max(1, min(max_results, 200)):
                    break
        return results
    except Exception:
        return []


def download_sdn_sample(max_entries: int = 50) -> list[dict[str, Any]]:
    """下载 SDN XML 并返回前 N 条（用于验证可达性及格式）。

    Args:
        max_entries: 最多解析条数

    Returns:
        [normalized_entry, ...] 或空列表。
    """
    try:
        r = httpx.get(_SDN_XML_URL, headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True)
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.content)
        entries = [e for e in root.iter() if e.tag.endswith("sdnEntry")]
        return [_normalize_xml_entry(e) for e in entries[:max(1, max_entries)]]
    except Exception:
        return []


def _get_text(element: ET.Element, *tags: str, default: str = "") -> str:
    """从 XML 元素中提取嵌套文本（兼容带命名空间和不带命名空间）。"""
    for tag in tags:
        # 尝试无命名空间
        child = element.find(f".//{tag}")
        if child is None:
            # 尝试任意命名空间后缀
            child = next((e for e in element.iter() if e.tag.endswith(tag)), None)
        if child is not None and child.text:
            return child.text.strip()
    return default


def _normalize_xml_entry(entry: ET.Element) -> dict[str, Any]:
    """标准化 OFAC XML sdnEntry。"""
    uid = _get_text(entry, "uid")
    last_name = _get_text(entry, "lastName")
    first_name = _get_text(entry, "firstName")
    name = f"{first_name} {last_name}".strip() if first_name else last_name
    sdn_type = _get_text(entry, "sdnType")
    title = _get_text(entry, "title")
    remarks = _get_text(entry, "remarks")[:200]

    # 提取 program 列表
    programs: list[str] = []
    for prog in entry.iter():
        if prog.tag.endswith("program") and prog.text:
            programs.append(prog.text.strip())

    return {
        "uid": uid,
        "name": name,
        "type": sdn_type,
        "programs": programs,
        "title": title,
        "remarks": remarks,
        "source_id": META["id"],
    }

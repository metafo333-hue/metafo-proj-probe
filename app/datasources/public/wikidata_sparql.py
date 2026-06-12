"""Wikidata SPARQL · 结构化知识图谱查询 · 无需 key · 免费。

端点：GET/POST https://query.wikidata.org/sparql
  参数：query=<SPARQL> & format=json

合规：Wikidata 是维基媒体基金会运营的开放知识库，数据以 CC0 发布（公有领域）。
      SPARQL 端点免费开放，官方要求合理使用（请求间隔 ≥1s，批量查询用 stream 端点）。
      官方文档：https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service

常用示例查询：
  - 搜索公司实体
  - 查询人物信息（出生/职业/国籍）
  - 查询机构/组织
"""
from __future__ import annotations

import time
from typing import Any

import httpx

META: dict[str, Any] = {
    "id": "wikidata_sparql",
    "domain": ["D6", "D11"],
    "access_type": "free",
    "method": ["O"],
    "kinds": ["knowledge_graph", "entity", "person", "company", "sparql"],
}

_SPARQL_URL = "https://query.wikidata.org/sparql"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": "probe-intel/1.0 (metafoclaw.com; knowledge-research)",
    "Accept": "application/sparql-results+json",
}

# Wikidata 服务礼貌间隔（两次请求之间）
_POLITE_DELAY = 1.0  # 秒


def configured() -> bool:
    """无需 key，恒返回 True。"""
    return True


def sparql_query(query: str) -> list[dict[str, Any]]:
    """执行任意 SPARQL 查询并返回结果行。

    Args:
        query: SPARQL 查询字符串（SELECT 形式）

    Returns:
        [{"var1": value, "var2": value, ...}] 或空列表。
        每列值为字符串（URI 或 literal），已从 bindings 中提取。
    """
    try:
        r = httpx.get(
            _SPARQL_URL,
            params={"query": query, "format": "json"},
            headers=_HEADERS,
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        if r.status_code != 200:
            return []
        body = r.json()
        bindings = (body.get("results") or {}).get("bindings") or []
        results: list[dict[str, Any]] = []
        for binding in bindings:
            row: dict[str, Any] = {}
            for key, val_obj in binding.items():
                row[key] = val_obj.get("value", "")
            results.append(row)
        return results
    except Exception:
        return []


def search_company(
    name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """搜索公司/组织实体（按名称）。

    Args:
        name:  公司名称关键词（大小写不敏感）
        limit: 最多返回条数（1-50）

    Returns:
        [{"entity_id", "label", "description", "founded", "country", "website", "source_id"}]
        或空列表。
    """
    # 礼貌延迟
    query = f"""
SELECT DISTINCT ?entity ?entityLabel ?entityDescription ?founded ?country ?countryLabel ?website WHERE {{
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:api "EntitySearch" ;
                    wikibase:endpoint "www.wikidata.org" ;
                    mwapi:search "{name}" ;
                    mwapi:language "en" .
    ?entity wikibase:apiOutputItem mwapi:item .
  }}
  ?entity wdt:P31/wdt:P279* wd:Q43229 .   # instance of organization/subclass
  OPTIONAL {{ ?entity wdt:P571 ?founded . }}
  OPTIONAL {{ ?entity wdt:P17 ?country . }}
  OPTIONAL {{ ?entity wdt:P856 ?website . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh" . }}
}}
LIMIT {max(1, min(limit, 50))}
"""
    raw = sparql_query(query)
    time.sleep(_POLITE_DELAY)
    results: list[dict[str, Any]] = []
    for row in raw:
        entity_uri = row.get("entity", "")
        entity_id = entity_uri.split("/")[-1] if entity_uri else ""
        results.append({
            "entity_id": entity_id,
            "wikidata_url": entity_uri,
            "label": row.get("entityLabel", ""),
            "description": row.get("entityDescription", ""),
            "founded": row.get("founded", ""),
            "country": row.get("countryLabel", ""),
            "website": row.get("website", ""),
            "source_id": META["id"],
        })
    return results


def search_person(
    name: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """搜索人物实体（按名称）。

    Args:
        name:  人物姓名关键词
        limit: 最多返回条数

    Returns:
        [{"entity_id", "label", "description", "birth_date", "nationality",
          "occupation", "source_id"}] 或空列表。
    """
    query = f"""
SELECT DISTINCT ?entity ?entityLabel ?entityDescription ?birth ?nationalityLabel ?occupationLabel WHERE {{
  SERVICE wikibase:mwapi {{
    bd:serviceParam wikibase:api "EntitySearch" ;
                    wikibase:endpoint "www.wikidata.org" ;
                    mwapi:search "{name}" ;
                    mwapi:language "en" .
    ?entity wikibase:apiOutputItem mwapi:item .
  }}
  ?entity wdt:P31 wd:Q5 .   # instance of human
  OPTIONAL {{ ?entity wdt:P569 ?birth . }}
  OPTIONAL {{ ?entity wdt:P27 ?nationality . }}
  OPTIONAL {{ ?entity wdt:P106 ?occupation . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh" . }}
}}
LIMIT {max(1, min(limit, 50))}
"""
    raw = sparql_query(query)
    time.sleep(_POLITE_DELAY)
    results: list[dict[str, Any]] = []
    for row in raw:
        entity_uri = row.get("entity", "")
        entity_id = entity_uri.split("/")[-1] if entity_uri else ""
        results.append({
            "entity_id": entity_id,
            "wikidata_url": entity_uri,
            "label": row.get("entityLabel", ""),
            "description": row.get("entityDescription", ""),
            "birth_date": row.get("birth", ""),
            "nationality": row.get("nationalityLabel", ""),
            "occupation": row.get("occupationLabel", ""),
            "source_id": META["id"],
        })
    return results


def entity_facts(entity_id: str) -> dict[str, Any]:
    """查询实体的基本属性（P31/P17/P571/P856 等）。

    Args:
        entity_id: Wikidata 实体 ID，如 "Q95"（Google）/ "Q42"（Douglas Adams）

    Returns:
        {"entity_id", "label", "description", "instance_of", "country",
         "website", "properties", "source_id"} 或空 dict。
    """
    query = f"""
SELECT ?prop ?propLabel ?value ?valueLabel WHERE {{
  wd:{entity_id} ?prop ?value .
  FILTER(STRSTARTS(STR(?prop), STR(wdt:)))
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,zh" . }}
}}
LIMIT 50
"""
    raw = sparql_query(query)
    time.sleep(_POLITE_DELAY)
    if not raw:
        return {}
    properties: list[dict[str, str]] = []
    for row in raw:
        prop_uri = row.get("prop", "")
        prop_id = prop_uri.split("/")[-1] if prop_uri else ""
        properties.append({
            "property_id": prop_id,
            "property_label": row.get("propLabel", ""),
            "value": row.get("valueLabel") or row.get("value", ""),
        })
    return {
        "entity_id": entity_id,
        "wikidata_url": f"https://www.wikidata.org/entity/{entity_id}",
        "properties": properties,
        "source_id": META["id"],
    }

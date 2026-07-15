#!/usr/bin/env python3
"""
Calculate keyword relevance from top-5 ASIN candidates and filter/sort keywords.

Input:
  python keyword_relevance_pipeline.py source.json keyword_results.json 20

Arguments:
  1. source.json
  2. keyword_results.json
  3. total competitor ASIN count

Optional source.json fields for subject-aware keyword filtering:
  product_subject_terms / subject_terms / product_subject_phrases:
    product nouns or phrases that must remain central to retained keywords
  accessory_terms / included_accessory_terms:
    included parts or accessories that should not be selected as standalone keywords

keyword_results.json shape:
{
  "keywords": [
    {
      "keyword": "cooling rack",
      "monthly_searches": 11951,
      "monthly_purchases": 948,
      "purchase_rate": 0.0794,
      "related_asin_count": 14,
      "top_asins": [
        {"asin": "...", "title": "...", "bullets": [...], "description": "...", "material": "...", "dimensions": "..."}
      ]
    }
  ]
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from relevance_estimate import calculate_relevance

MAX_SELECTED_MONTHLY_SEARCHES = 10_000


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def normalize(text: str) -> str:
    return " ".join(text.lower().replace("-", " ").split())


def as_terms(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [normalize(value)]
    if isinstance(value, list):
        return [normalize(str(item)) for item in value if str(item).strip()]
    return []


def to_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    try:
        return int(float(str(value).replace(",", "").strip()))
    except ValueError:
        return 0


def source_terms(source: dict[str, Any], keys: list[str]) -> list[str]:
    terms: list[str] = []
    for key in keys:
        terms.extend(as_terms(source.get(key)))
    return sorted(set(term for term in terms if term))


def subject_alignment(source: dict[str, Any], keyword: str | None) -> str:
    """Classify whether a keyword names the product subject or only an accessory.

    For composite products, callers can add `product_subject_terms` and
    `accessory_terms` to source.json. Example:
      product_subject_terms: ["honigglas", "honey jar", "honigtopf"]
      accessory_terms: ["honiglöffel", "löffel", "spoon"]
    """
    keyword_norm = normalize(keyword or "")
    subject_terms = source_terms(source, ["product_subject_terms", "subject_terms", "product_subject_phrases"])
    accessory_terms = source_terms(source, ["accessory_terms", "included_accessory_terms"])

    if not keyword_norm or not subject_terms:
        return "unknown"

    has_subject = any(term in keyword_norm for term in subject_terms)
    has_accessory = any(term in keyword_norm for term in accessory_terms)

    if has_subject:
        return "subject_match_with_accessory" if has_accessory else "subject_match"
    if has_accessory:
        return "accessory_only"
    return "no_subject_match"


def search_volume_band(monthly_searches: int) -> str:
    if monthly_searches <= 0:
        return "missing"
    if monthly_searches > MAX_SELECTED_MONTHLY_SEARCHES:
        return "too_broad_over_10000"
    if monthly_searches >= 1_000:
        return "mid_tail"
    return "long_tail"


def keyword_relevance(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    top_asins = item.get("top_asins", [])[:5]
    scores = [
        calculate_relevance(source, candidate, use_image_match=False)["score_percent"]
        for candidate in top_asins
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
    monthly_searches = to_int(item.get("monthly_searches", 0))
    return {
      "keyword": item.get("keyword"),
      "monthly_searches": monthly_searches,
      "monthly_purchases": to_int(item.get("monthly_purchases", 0)),
      "purchase_rate": item.get("purchase_rate", 0) or 0,
      "related_asin_count": to_int(item.get("related_asin_count", 0)),
      "top5_relevance_scores": scores,
      "keyword_relevance_percent": avg_score,
      "search_volume_band": search_volume_band(monthly_searches),
      "subject_alignment": subject_alignment(source, item.get("keyword")),
    }


def adaptive_related_ratio(items: list[dict[str, Any]], asin_total_count: int) -> float:
    ratio = 0.2
    filtered = items
    while len(filtered) > 50 and ratio < 0.8:
        ratio += 0.05
        filtered = [
            item
            for item in items
            if item["related_asin_count"] >= asin_total_count * ratio and item["keyword_relevance_percent"] >= 60
        ]
    return round(ratio, 2)


def composite_score(item: dict[str, Any], asin_total_count: int) -> float:
    """综合关键词相关度 (0-100).

    权重:
      - 关键词相关度 (top5 ASIN 标题相似度均值)        × 55%
      - related_asin_count / asin_total_count × 100  × 40%
      - 转化率 (purchase_rate, 0-1) × 100              ×  5%

    purchase_rate 在 Amazon keyword source 数据里是 0-1 的小数 (例如 0.0794),
    乘 100 后进入百分制后再加权,保持三项尺度一致。
    """
    asin_ratio = (item["related_asin_count"] / asin_total_count) if asin_total_count else 0.0
    purchase_rate_pct = float(item.get("purchase_rate") or 0) * 100
    return round(
        item["keyword_relevance_percent"] * 0.55
        + asin_ratio * 100 * 0.40
        + purchase_rate_pct * 0.05,
        2,
    )


def main() -> int:
    if len(sys.argv) != 4:
        print("Usage: python keyword_relevance_pipeline.py source.json keyword_results.json asin_total_count", file=sys.stderr)
        return 1

    source = load_json(sys.argv[1])
    keyword_payload = load_json(sys.argv[2])
    asin_total_count = int(sys.argv[3])

    evaluated = [keyword_relevance(source, item) for item in keyword_payload.get("keywords", [])]
    ratio_threshold = adaptive_related_ratio(evaluated, asin_total_count)

    retained = []
    removed = []
    for item in evaluated:
        remove_reason = None
        if item["subject_alignment"] == "accessory_only":
            remove_reason = "accessory_only_without_product_subject"
        elif item["monthly_searches"] > MAX_SELECTED_MONTHLY_SEARCHES:
            remove_reason = "monthly_searches_over_10000_broad_head_term"
        elif item["keyword_relevance_percent"] < 60:
            remove_reason = "keyword_relevance_below_60"
        elif item["related_asin_count"] < asin_total_count * ratio_threshold:
            remove_reason = "related_asin_count_below_threshold"

        item["related_ratio_threshold"] = ratio_threshold
        item["related_ratio_percent"] = round((item["related_asin_count"] / asin_total_count) * 100, 2) if asin_total_count else 0.0
        item["composite_relevance"] = composite_score(item, asin_total_count)

        if remove_reason:
            item["remove_reason"] = remove_reason
            removed.append(item)
        else:
            retained.append(item)

    retained.sort(
        key=lambda item: (
            item["subject_alignment"] not in ("subject_match_with_accessory", "subject_match"),
            -item["composite_relevance"],
            -float(item.get("purchase_rate") or 0),
            -(item["monthly_searches"] or 0),
        )
    )

    # 按综合关键词相关度从高到低,top → 标题, 中段 → 五点, 末段 → 详情描述
    subject_retained = [item for item in retained if item["subject_alignment"] in ("subject_match_with_accessory", "subject_match")]
    bucket_pool = subject_retained if subject_retained else retained
    title_quota = min(5, len(bucket_pool))
    bullet_quota = min(20, max(0, len(bucket_pool) - title_quota))
    for index, item in enumerate(retained):
        if item not in bucket_pool:
            item["allocation_bucket"] = "search_terms"
            continue
        rank_in_bucket = bucket_pool.index(item)
        if rank_in_bucket < title_quota:
            item["allocation_bucket"] = "title"
        elif rank_in_bucket < title_quota + bullet_quota:
            item["allocation_bucket"] = "bullet"
        else:
            item["allocation_bucket"] = "description"

    result = {
        "asin_total_count": asin_total_count,
        "related_ratio_threshold": ratio_threshold,
        "retained_count": len(retained),
        "removed_count": len(removed),
        "retained_keywords": retained,
        "removed_keywords": removed,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

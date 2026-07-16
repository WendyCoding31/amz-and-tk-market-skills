#!/usr/bin/env python3
"""Normalize an Amazon product payload exported from any configured data source.

The agent is responsible for calling an MCP or obtaining an offline JSON file.
This script performs no network requests and reads no MCP configuration.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALIASES: dict[str, tuple[str, ...]] = {
    "asin": ("asin", "sku_id", "skuId", "item_id", "itemId", "id"),
    "title": ("title", "product_title", "productTitle", "name"),
    "brand": ("brand", "brand_name", "brandName", "store"),
    "product_url": ("product_url", "productUrl", "url", "link"),
    "image_url": ("image_url", "imageUrl", "main_image", "mainImage", "image"),
    "category": ("category", "category_name", "categoryName", "leaf_category"),
    "category_path": ("category_path", "categoryPath", "category_tree"),
    "category_id": ("category_id", "categoryId", "cat_id", "catId"),
    "price": ("price", "sale_price", "salePrice", "current_price"),
    "currency": ("currency", "currency_code", "currencyCode"),
    "rating": ("rating", "star", "stars", "score"),
    "review_count": ("review_count", "reviewCount", "ratings", "comment_count"),
    "monthly_sales_30d": ("monthly_sales_30d", "sales_30d", "sales30d", "monthly_sales"),
    "bsr": ("bsr", "best_seller_rank", "bestSellerRank", "rank"),
    "attributes": ("attributes", "specifications", "specs", "features"),
    "variants": ("variants", "variations", "variation_items", "children"),
    "sales_history": ("sales_history", "salesHistory", "trend", "history"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Provider output JSON")
    parser.add_argument("--asin", help="Choose a matching ASIN when the input contains multiple rows")
    parser.add_argument("--marketplace", help="Marketplace code recorded in the normalized output")
    parser.add_argument("--provider", default="user-configured-source")
    parser.add_argument("--queried-at", help="ISO-8601 query time")
    parser.add_argument("--output", help="Write normalized JSON to this path; stdout when omitted")
    return parser.parse_args()


def first_value(record: dict[str, Any], aliases: tuple[str, ...]) -> Any:
    for key in aliases:
        value = record.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def candidate_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "records", "products", "results", "list", "data"):
        nested = payload.get(key)
        if isinstance(nested, list):
            return [row for row in nested if isinstance(row, dict)]
        if isinstance(nested, dict):
            rows = candidate_rows(nested)
            if rows:
                return rows
    return [payload]


def choose_record(rows: list[dict[str, Any]], asin: str | None) -> dict[str, Any]:
    if not rows:
        raise ValueError("No product record found in input JSON")
    if asin:
        wanted = asin.strip().upper()
        for row in rows:
            value = first_value(row, ALIASES["asin"])
            if str(value or "").strip().upper() == wanted:
                return row
        raise ValueError(f"ASIN {asin} not found in input JSON")
    if len(rows) > 1:
        raise ValueError("Input contains multiple products; pass --asin")
    return rows[0]


def normalize(record: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    normalized = {field: first_value(record, aliases) for field, aliases in ALIASES.items()}
    normalized["marketplace"] = args.marketplace
    normalized["evidence"] = {
        "provider": args.provider,
        "queried_at": args.queried_at,
        "source_file": str(Path(args.input).expanduser().resolve()),
        "field_map": {
            field: next((key for key in aliases if record.get(key) not in (None, "", [], {})), None)
            for field, aliases in ALIASES.items()
        },
    }
    normalized["missing_fields"] = [
        field for field in ("asin", "title", "image_url", "category") if not normalized.get(field)
    ]
    return normalized


def main() -> int:
    args = parse_args()
    payload = json.loads(Path(args.input).expanduser().read_text(encoding="utf-8"))
    result = normalize(choose_record(candidate_rows(payload), args.asin), args)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(output.resolve())
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

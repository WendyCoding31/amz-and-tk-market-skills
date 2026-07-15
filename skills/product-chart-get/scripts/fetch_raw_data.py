#!/usr/bin/env python3
"""Normalize provider-exported Amazon product JSON for product-chart-get.

The agent calls any compatible MCP and saves its result as JSON. This script
does not call a fixed server, CLI, or endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def get_default_workspace() -> str:
    return os.path.expanduser(os.getenv("WORKSPACE", "~/Desktop"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="JSON exported from a configured data source")
    parser.add_argument("--date", "-d", required=True, help="Partition date YYYYMMDD")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--page", "-p", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--provider", default="user-configured-source")
    return parser.parse_args()


def rows_from(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "records", "products", "results", "list", "data"):
            if key in payload:
                rows = rows_from(payload[key])
                if rows:
                    return rows
        return [payload]
    return []


def value(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        candidate = row.get(key)
        if candidate not in (None, "", [], {}):
            return candidate
    return default


def normalize(row: dict[str, Any], date: str) -> dict[str, Any]:
    sku = value(row, "SKU_ID", "asin", "sku_id", "skuId", "item_id", "id")
    bullets = value(row, "五点描述", "bullets", "bullet_points", "features", default=[])
    return {
        "分区日期": value(row, "分区日期", "ds", "date", default=date),
        "SKU_ID": sku,
        "SPU_ID": value(row, "SPU_ID", "parent_asin", "spu_id", "spuId", default=sku),
        "英文标题": value(row, "英文标题", "title", "product_title", "name"),
        "商品链接": value(row, "商品链接", "product_url", "url", "link"),
        "主图链接": value(row, "主图链接", "image_url", "main_image", "image"),
        "一级类目ID": value(row, "一级类目ID", "category_id", "cat_id"),
        "类目ID路径": value(row, "类目ID路径", "category_id_path"),
        "一级类目": value(row, "一级类目", "top_category", "category"),
        "类目路径": value(row, "类目路径", "category_path", "category"),
        "售价": value(row, "售价", "price", "sale_price"),
        "货币": value(row, "货币", "currency", default=""),
        "评分次数": value(row, "评分次数", "review_count", "ratings"),
        "评分星级": value(row, "评分星级", "rating", "stars"),
        "SPU月销量": value(row, "SPU月销量", "spu_sales_30d", "parent_sales_30d"),
        "SKU月销量": value(row, "SKU月销量", "sku_sales_30d", "sales_30d", "monthly_sales"),
        "变体数量": value(row, "变体数量", "variant_count", "variants"),
        "卖家名称": value(row, "卖家名称", "seller_name", "seller", "shop"),
        "体积": value(row, "体积", "volume"),
        "重量": value(row, "重量", "weight"),
        "品牌": value(row, "品牌", "brand"),
        "五点描述": bullets,
        "详细描述": value(row, "详细描述", "description", "product_description"),
        "采集时间": value(row, "采集时间", "queried_at", "collected_at"),
    }


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    products = [normalize(row, args.date) for row in rows_from(payload)[: args.limit]]
    products = [row for row in products if row["SKU_ID"]]
    if not products:
        raise SystemExit("No product rows with an ASIN/SKU identifier were found")

    output_dir = Path(args.output).expanduser() if args.output else Path(get_default_workspace()) / f"{args.date}选品"
    output_dir.mkdir(parents=True, exist_ok=True)
    full_path = output_dir / f"data-get-第{args.page}页数据.json"
    mini_path = output_dir / f"mini_products-第{args.page}页.json"
    meta_path = output_dir / f"meta-第{args.page}页.json"

    full_path.write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mini = [
        {key: row.get(key, "") for key in ("SKU_ID", "SPU_ID", "英文标题", "五点描述", "详细描述", "类目路径")}
        for row in products
    ]
    mini_path.write_text(json.dumps(mini, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    meta_path.write_text(
        json.dumps(
            {
                "ds": args.date,
                "page": args.page,
                "count": len(products),
                "provider": args.provider,
                "source_file": str(input_path.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(full_path.resolve())
    print(mini_path.resolve())
    print(meta_path.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

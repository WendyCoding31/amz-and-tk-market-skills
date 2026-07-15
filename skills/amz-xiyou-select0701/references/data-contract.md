# Data Contract

This skill is data-source agnostic. A data source may be an MCP server, API, CLI, scraped export, local workbook, CSV, or user-provided table.

Use provider-specific tools only as adapters that fill the contracts below. Do not write provider-specific tool names into workbook business logic.

## Keyword Row Contract

Minimum fields:

| Canonical field | Meaning |
|---|---|
| `keyword` | English Amazon keyword |
| `keyword_cn` | concise Chinese translation |
| `category` | category or product-scene label |
| `openability_index` | semantic product-development judgment |

Optional fields:

| Canonical field | Meaning |
|---|---|
| `search_rank` | keyword rank / ABA / search-frequency rank |
| `weekly_searches` or `monthly_searches` | demand |
| `growth_rate` | search growth |
| `cpc` | suggested CPC |
| `conversion_rate` | click/order conversion rate |
| `top3_click_share` | click concentration |
| `top3_conversion_share` | conversion concentration |

## `keyword_to_representative_asins`

Input:

```json
{
  "keyword": "halloween treat bags",
  "marketplace": "US",
  "limit": 5,
  "fallback_queries": []
}
```

Output:

```json
[
  {
    "asin": "B0XXXXXXXX",
    "title": "...",
    "price": 9.99,
    "brand": "...",
    "seller": "...",
    "monthly_sales": 500,
    "sales_share": "4.2%",
    "source_query": "halloween treat bags",
    "source_method": "natural_results"
  }
]
```

Rules:

- Return 3-5 ASINs when possible.
- Prefer relevance over raw best-seller dominance.
- Keep the source query/method so fallback decisions remain auditable.
- Normalize ASIN strings to uppercase.
- Normalize price to USD numeric value when possible. If a provider returns cents such as `1049`, convert to `10.49`; ignore `0` or negative prices.

## `asin_traffic_summary`

Input:

```json
{
  "asin": "B0XXXXXXXX",
  "marketplace": "US"
}
```

Output:

```json
{
  "asin": "B0XXXXXXXX",
  "traffic_entrances": 1500,
  "natural_keyword_count": 1200,
  "ad_keyword_count": 300,
  "recommendation_keyword_count": 0,
  "data_status": "OK"
}
```

## `asin_traffic_keywords`

Input:

```json
{
  "asin": "B0XXXXXXXX",
  "marketplace": "US",
  "limit": 100
}
```

Output:

```json
[
  {
    "keyword": "treat bags",
    "keyword_cn": "糖果袋",
    "traffic_share": 0.042,
    "searches": 64000,
    "natural_rank": 12,
    "ad_rank": 1,
    "bid": 0.65,
    "conversion_rate": 0.04
  }
]
```

Rules:

- `traffic_share` should be decimal format (`0.042` = 4.2%).
- If only score/rank is available, map it to a comparable contribution score and state the limitation in the rules sheet.
- Pull at least the top 100 traffic keywords when available.

## Missing Data Policy

| Missing data | Output behavior |
|---|---|
| no representative ASINs | `待补数据` |
| 1-2 representative ASINs | `样本不足`; do not force 标品/非标品 |
| no traffic keyword list | keep ASIN summary fields; mark high/mid/low and cliff as `待查` |
| no price | leave price blank; do not use `0` |
| provider quota/error | write exact status in evidence sheet; do not invent fallback numbers |

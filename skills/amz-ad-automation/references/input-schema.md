# Input Schema for `generate_bulk_xlsx.py`

Create a JSON file in this shape, then run the generator script.

```json
{
  "sku": "SELLER-SKU-123",
  "start_date": "20260527",
  "output_path": "./output/amazon-ads.xlsx",
  "campaigns": [
    {
      "strategy": "S22",
      "ad_type": "sp_keyword",
      "daily_budget": 5,
      "bidding_strategy": "fixed",
      "grouping": "rank",
      "match_types": ["broad"],
      "ad_group_default_bid": 0.2,
      "top_of_search_percentage": 30,
      "keywords": [
        {"text": "gift card", "aba_rank": 8000, "bid": 0.35},
        {"text": "birthday card", "aba_rank": 42000, "bid": 0.3}
      ]
    }
  ]
}
```

## Top-Level Fields

| Field | Required | Notes |
|---|---|---|
| `sku` | Yes | Seller SKU. Do not use ASIN unless user confirms ASIN is also the seller SKU. |
| `start_date` | Yes | Accepts `YYYYMMDD` or `YYYY-MM-DD`; writes `YYYYMMDD`. |
| `output_path` | No | Can also be passed by CLI `--output`. |
| `campaigns` | Yes | One object per strategy/ad plan. |

## Campaign Fields

| Field | Required | Notes |
|---|---|---|
| `strategy` | Yes | `S1`-`S27`. |
| `ad_type` | No | One of `sp_keyword`, `asin`, `auto`; inferred from strategy if omitted. |
| `daily_budget` | No | Defaults to `5`. |
| `bidding_strategy` | No | `fixed`, `up_down`, `down_only`; default `fixed`. |
| `grouping` | No | `none`, `rank`, or `root_rank`. Some strategies default to rank grouping. |
| `match_types` | No | For keyword campaigns: `broad`, `exact`, `phrase`. |
| `ad_group_default_bid` | No | Defaults from campaign bid or strategy bid. |
| `top_of_search_percentage` | No | Adds `Bidding Adjustment` rows when present. |
| `keywords` | For SP keyword | Strings or objects with `text`, `aba_rank`, `bid`, optional `root`, optional `rank_bucket`. |

S22-specific rule: total `keywords` must be fewer than 50. Use at most 49 S22 keywords after filtering and ranking the source table.
| `asins` | For ASIN ads | Strings or objects with `asin`, optional `bid`. |
| `auto_targets` | For auto ads | Dict or list for `close-match`, `loose-match`, `substitutes`, `complements`. |

## Rank Buckets

When `grouping` is `rank` or `root_rank`, the generator buckets keywords by `aba_rank`:

| Bucket | Rank range | Group size |
|---|---:|---:|
| `R00010` | `<= 10000` | 3 |
| `R01050` | `10001-50000` | 15 |
| `R050150` | `50001-150000` | 20 |
| `R150PLUS` | `> 150000` | 30 |

You can still supply `rank_bucket` manually. Allowed values: `R00010`, `R01050`, `R050150`, `R150PLUS`.

## Examples

SP keyword exact campaign:

```json
{
  "sku": "SELLER-SKU-123",
  "start_date": "20260527",
  "campaigns": [
    {
      "strategy": "S4",
      "ad_type": "sp_keyword",
      "match_types": ["exact"],
      "daily_budget": 5,
      "ad_group_default_bid": 0.2,
      "keywords": [
        {"text": "gift card", "bid": 0.35},
        {"text": "birthday card", "bid": 0.35}
      ]
    }
  ]
}
```

ASIN product-targeting campaign:

```json
{
  "sku": "SELLER-SKU-123",
  "start_date": "20260527",
  "campaigns": [
    {
      "strategy": "S20",
      "ad_type": "asin",
      "daily_budget": 5,
      "asins": [
        {"asin": "B0ABCDEF12", "bid": 0.05},
        {"asin": "B0XYZXYZ99", "bid": 0.05}
      ]
    }
  ]
}
```

Automatic campaign:

```json
{
  "sku": "SELLER-SKU-123",
  "start_date": "20260527",
  "campaigns": [
    {
      "strategy": "S1",
      "ad_type": "auto",
      "daily_budget": 5,
      "bidding_strategy": "fixed",
      "top_of_search_percentage": 900,
      "auto_targets": {"close-match": 0.05, "loose-match": 0.05}
    }
  ]
}
```

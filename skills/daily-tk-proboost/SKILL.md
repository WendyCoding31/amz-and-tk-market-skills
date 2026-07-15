---
name: daily-tk-proboost
description: Generate a branded TikTok Shop cross-border ecommerce daily report poster from current web news and any compatible configured TikTok Shop data source. The skill id is retained for backward compatibility; runtime data and visual branding are provider-agnostic.
---

# Daily TK Report

Create one publish-ready TikTok 跨境日报 PNG. The user can supply a brand name, tagline, logo, follow QR, promo QR, and promo label. No marketplace provider or third-party brand is required.

## Inputs

- Country/region: default `全球TK`.
- Category: default `全部行业`.
- Brand name: default `TK跨境情报`.
- Tagline: optional.
- Logo/follow QR/promo QR: optional image URL or local path.

`全球TK` means scan the markets supported by the configured source. Record which markets were actually queried; do not imply global coverage when the source only returned one region.

## Data workflow

Generate exactly eight report items:

1. Four macro/news items from current primary or reputable web sources.
2. Four product/data items from a configured TikTok Shop MCP or an uploaded CSV/XLSX/JSON file.

Before querying, read [references/data-source.md](references/data-source.md). Map provider fields to logical capabilities such as `tiktok.market_overview`, `tiktok.product_search`, `tiktok.sales_history`, `tiktok.channel_mix`, and `tiktok.review_or_voice`. These labels are capabilities, not literal MCP tool names.

If a compatible source is unavailable, ask the user to configure one or provide an offline file. Do not invent GMV, sales, ranking, creator, country, date, or product facts.

## Evidence rules

- Separate web-sourced macro claims from marketplace commerce claims.
- Record provider, region, query time, window, source URL/title, and missing fields in working notes.
- Do not describe product/video/creator data as TikTok Ads account data.
- Each poster item needs one headline, one short paragraph, and a compact source label.

## Render

Prepare an eight-item JSON payload:

```json
{
  "items": [
    {
      "kind": "macro",
      "title": "headline",
      "body": "short paragraph",
      "source": "publisher or configured data source"
    }
  ]
}
```

Then render:

```bash
python3 scripts/render_report.py \
  --date-text "7月16日" \
  --market "美国" \
  --category "家居" \
  --brand-name "TK跨境情报" \
  --tagline "跨境市场与商品信号" \
  --logo "/optional/logo.png" \
  --follow-qr "/optional/follow-qr.png" \
  --promo-qr "/optional/promo-qr.png" \
  --promo-label "领取完整数据" \
  --items-json items.json \
  --output output.png
```

Omit all optional asset arguments when the user does not provide them. The renderer must still produce a complete poster with text-only branding.

## Output

Return the absolute PNG path and a brief note covering regions, time window, data source type, and missing fields. Do not create a scheduled automation unless the user separately asks for one.

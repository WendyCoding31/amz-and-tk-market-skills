---
name: rising-seller-leads
description: Find same-category, rising Amazon and TikTok Shop sellers/shops/brands for factories to contact as supplier or product-development leads. Use when the user asks to find 上升期卖家, 同类目卖家, 建联池, 潜在客户, 适合工厂开发的 Amazon/TK 卖家, 增长中的店铺, TikTok Shop 店铺, Amazon seller leads, supplier outreach targets, or sellers with recent 30/60/90 day growth, new SKU expansion, review growth, creator/video heat, ads/affiliate signals, and public contact channels.
---

# Rising Seller Leads

## Goal

Build a practical B2B outreach pool for factories:

`类目发现 -> 同类目定义 -> configured marketplace capabilities 增长卖家识别 -> configured seller-enrichment source 卖家信息补全 -> 质量过滤 -> 建联线索输出`

Use this skill when the user wants names and prioritization of sellers worth contacting, not just a generic seller list.

## Hard Rules

- Use `configured marketplace capabilities` for Amazon/TikTok Shop/TK platform data: category, SKU, seller/shop, sales, GMV, price, review, new products, creator/video heat, shop growth, and trend signals.
- Use `configured seller-enrichment source` `amazon.seller_search` for Amazon seller company enrichment when the user asks for seller company information, address, email, phone, business name, store rating, item count, annual sales, or contact fields.
- If `configured marketplace capabilities` or `configured seller-enrichment source` tools are not visible when needed, discover/search for the relevant MCP first. If still unavailable, stop and say the data source is unavailable; do not replace it with invented lead data.
- Do not invent contact information. Only include email, phone, address, website, LinkedIn, Instagram, TikTok account, or official store links when returned by `configured seller-enrichment source`, returned by `configured marketplace capabilities`, or found from a clearly public business source.
- `configured seller-enrichment source` `amazon.seller_search` phone/email fields may be masked as `****`; preserve the masked value and label it `configured seller-enrichment source已脱敏`, not as a real usable email/phone.
- Exclude or down-rank platform self-operated accounts, dominant mega-brands, pure low-price white-label copycats, and sellers with no visible supplier-fit reason.
- Answer in Chinese by default. Output should be directly usable by a factory BD or boss.

## Workflow

1. Normalize the factory's product/category into a `同类目定义`.
2. Use configured marketplace capabilities to discover candidate Amazon sellers and/or TikTok Shop shops in that category.
3. Use configured seller-enrichment source `amazon.seller_search` to enrich Amazon seller company/contact fields when seller IDs, seller names, SKUs, SPUs, or item titles are available.
4. Score growth with 30/60/90 day signals and expansion signals.
5. Filter candidates for supplier fit and contactability.
6. Output a ranked `建联池` with touch order, fit reason, and missing-data flags.

Load [references/rubric.md](references/rubric.md) before scoring and final output.

## 1. Define Same Category

Create a short `同类目定义` before querying:

- `产品语义`: what the product is and the buyer problem/use case.
- `平台关键词`: 2-5 Amazon English keywords and 2-5 TikTok creator/shop phrases.
- `类目路径`: Amazon category node and TikTok Shop category if known.
- `价格带`: factory target price and marketplace price band.
- `客群`: target buyer/user, e.g. pet owners, curly-hair users, new moms.
- `属性`: material, size, function, power/specs, bundle/accessories.
- `供应链相似度`: what kinds of sellers can realistically buy from this factory.

If the user only gives a product image/title/link, infer the category but state the assumption.

## 2. Query MCP Data Sources

Use available MCP tools according to platform and data need.

Explicit MCP tools used by this skill:

- `configured marketplace capabilities`: `amazon.product_search`, `amazon.product_detail`, `amazon.sales_history`, `amazon.review_search`, `amazon.market_overview`, `amazon.market_overview`, `amazon.market_overview`, `tiktok.market_overview`, `tiktok.market_overview`, `tiktok.product_search`, `tiktok.product_detail`, `tiktok.sales_history`, `tiktok.shop_search`, `tiktok.shop_detail`, `tiktok.market_overview`, `tiktok.shop_sales_history`, `tiktok.video_search`, `tiktok.live_search`.
- `configured seller-enrichment source`: `amazon.seller_search`.

Amazon discovery pattern:

- Use category/keyword mapping to find relevant category node.
- Use `amazon.product_search` for SKU candidates in the target category and price band.
- Use `amazon.product_detail` to extract title, seller name/id, brand, category, price, reviews, rating, link, and fulfillment.
- Use `amazon.sales_history` for recent 30-day sales and prior-period comparison.
- Use `amazon.review_search` when review recency or review quality matters.
- Use `amazon.market_overview`, `amazon.market_overview`, and `amazon.market_overview` for market context.
- Use `configured seller-enrichment source` `amazon.seller_search` after candidate seller discovery to enrich Amazon seller/company fields.

`configured seller-enrichment source` `amazon.seller_search` lookup inputs:

- `sellerId`: Amazon seller ID, exact match.
- `sellerName`: seller name, fuzzy match.
- `busName`: company/business name, fuzzy match.
- `skuId`: child ASIN/SKU ID, supports comma-separated batch lookup.
- `spuId`: parent ASIN/SPU ID, supports comma-separated batch lookup.
- `itemTitle`: item title keyword, fuzzy match through SKU-to-seller association.
- marketplace: normalized Amazon marketplace code; map it to the provider schema at runtime.
- `page`, `size`: pagination; size max 50.
- `sortFields`: multi-field sorting by `stars`, `ratings`, `item_cnt`, `sold_cnt_lst_yr`, `sold_amt_cur_yr`, or `seller_id`.

`configured seller-enrichment source` `amazon.seller_search` seller fields to preserve when returned:

- `seller_id`: seller ID.
- `seller_name`: seller/store name.
- `bus_name`: company/business name.
- `address`: seller/company address.
- `phone`: phone; may be masked as `****`.
- `email`: email; may be masked as `****`.
- `stars`: store rating.
- `ratings`: store rating count.
- `item_cnt`: active/listed item count.
- `sold_cnt_lst_yr`: last-year sales units.
- `sold_amt_cur_yr`: current-year sales amount.

If any of these fields are missing, output `configured seller-enrichment source暂未返回`. If `phone` or `email` is masked, output the masked value and mark `configured seller-enrichment source已脱敏`.

TikTok Shop discovery pattern:

- Use `tiktok.market_overview` or `tiktok.market_overview` to map category.
- Use `tiktok.product_search` to find product candidates by keyword/category/price/sales.
- Use `tiktok.product_detail` and `tiktok.sales_history` for product-level growth.
- Use `tiktok.shop_search`, `tiktok.shop_detail`, `tiktok.market_overview`, and `tiktok.shop_sales_history` for shop-level growth and SKU expansion.
- Use `tiktok.video_search`, `tiktok.live_search`, and expert tools when creator/video/live growth is part of the signal.

When the user asks for both Amazon and TK, query both. When they ask for one platform, stay focused on that platform.

## 3. Identify Rising Sellers

Prefer seller/shop-level growth signals. If seller-level trend is unavailable, infer cautiously from the seller's product-level signals and label it `商品侧推断`.

Look for:

- Recent 30/60/90 day sales or GMV growth.
- New SKU/product expansion in the same category.
- Review count or review velocity growth.
- TikTok content burst: new videos, creator count, live volume, views, GMV slope.
- Shop SKU count or active-product count growth.
- Ads, affiliate, creator, or live selling signs.
- Mid-sized seller behavior: enough traction to buy, not so large that supplier switching is impossible.

## 4. Filter for Contactability and Supplier Fit

Rank candidates higher when they show:

- Public business contact channel: official website, seller storefront, LinkedIn, Instagram, TikTok business account, email, or shop link.
- Product line fit with factory capabilities.
- Recent expansion into adjacent SKUs.
- Gaps that a factory can solve: cost, MOQ, variant speed, material quality, packaging, compliance, bundle design, or private label supply.
- Not fully locked to a giant brand or Amazon retail.

Filter out or clearly mark:

- Amazon.com/platform self-operated seller when supplier outreach is unlikely.
- Mega-brands with strong in-house supply chain unless the user explicitly wants brand leads.
- Extreme low-price sellers with weak quality or no margin.
- Sellers with no identifiable public contact route.
- Sellers whose products are not actually supply-chain similar despite keyword overlap.

## 5. Output

Default final answer:

1. `一句话结论`: what kind of sellers are worth targeting.
2. `同类目定义`: the normalized category and price band used.
3. `建联池`: ranked table with 5-20 candidates depending on data volume.
4. `优先触达顺序`: A/B/C priority and why.
5. `建联话术切入点`: 1-3 short angles based on the seller's growth signal and supplier gap.
6. `configured seller-enrichment source 卖家信息`: seller company/contact enrichment fields when Amazon sellers are included.
7. `数据缺口`: missing marketplace/seller-enrichment metrics or contact fields.

Keep the table actionable. Avoid long market-report prose unless the user asks for analysis.

Required table columns:

| 优先级 | 卖家/店铺 | 平台 | 主打产品 | 增长信号 | 联系方式来源 | 适配理由 | 下一步 |
|---|---|---|---|---|---|---|---|

When Amazon seller company information is requested, include a seller enrichment table with these `configured seller-enrichment source` fields:

| 卖家 | seller_id | seller_name | bus_name | address | phone | email | stars | ratings | item_cnt | sold_cnt_lst_yr | sold_amt_cur_yr |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|

If a field is missing, write `数据源未返回`, `configured seller-enrichment source暂未返回`, or `公开渠道待补`, not a guess.

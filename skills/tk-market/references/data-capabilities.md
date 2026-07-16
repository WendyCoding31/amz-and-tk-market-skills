# TikTok Shop data capabilities

These are logical capabilities, not literal MCP tool names. Discover a compatible configured source at runtime and record the provider-specific field mapping.

## Market And Category

- `tiktok.market_overview`: country/category totals, sales, GMV, active products, average price, new-product metrics, period comparisons.
- `tiktok.market_overview`: first/second-level category heatmap and category concentration.
- `tiktok.market_overview`: local-currency price-band sales, GMV, and product count.
- `tiktok.creator_search`: creator matrix by follower tier, sales, videos, and creator output.
- `tiktok.market_overview`: TikTok B2C category tree.

## Product

- `tiktok.product_search`: product-selection list with keyword/category filters, sorting, image search, sales, GMV, price, shop, creator, and video signals.
- `tiktok.product_detail`: product details, image/title/link/category, price, sales/GMV, creators, videos, rating, shop, and follow state.
- `tiktok.sales_history`: product sales, GMV, price, or other trend series.
- `tiktok.channel_mix`: recent product-card, shop self-run, and creator-driven sales/GMV channel split.
- `tiktok.review_or_voice`: product review/comment voice analysis by dimension.
- `tiktok.creator_search`: monthly creator-count trend for a product.
- `tiktok.creator_detail`: creator follower-tier analysis for a product.
- `tiktok.creator_detail`: product-selling creators by category dimension.

## Creator

- `tiktok.creator_search`: creator list with country, keyword, category, follower/engagement, sales, GPM, related product/shop filters, and sorting.
- `tiktok.creator_detail`: creator detail, followers, engagement, sales, GPM, bio, masked email, and quota-limited detail fields.
- `tiktok.creator_detail`: creator trend series such as likes, plays, and shares.
- `tiktok.creator_detail`: creator fan portrait such as gender and age distribution when available.
- `tiktok.creator_sales`: creator sales performance, sales-channel GMV split, and product-category GMV split.

## Video

- `tiktok.video_search`: video list with title, creator/product/shop, publish time, plays, engagement, recent sales/GMV, ad/boosting and selling type, script/summary markers, and pagination limits.
- `tiktok.video_detail`: video detail, play/engagement, type, summary/script flags, and follow state.
- `tiktok.video_detail`: speech or voice transcript when available.
- `tiktok.video_transcript`: video comment summary and collection/summarization status.
- `tiktok.video_transcript`: video comments with child replies.
- `tiktok.video_search`: newer structured video summary.
- `tiktok.video_transcript`: user's DIY script list for a video when available.

## Shop

- `tiktok.shop_search`: shop list; a normalized time window is required and must be mapped to the provider schema.
- `tiktok.shop_detail`: shop detail, categories, score, live products, link, and follow state.
- `tiktok.market_overview`: shop market metrics such as active/live products, sales, GMV, ranking, creators, videos, and live streams.
- `tiktok.shop_sales_history`: shop sales and review trend series.
- `tiktok.shop_search`: product-category count and sales share by shop.

## Reporting Rules

- Name the provider and actual source tool behind each important claim.
- Treat empty arrays, `data: null`, permission limits, or detail quota limits as observations, not as zero demand.
- Separate TikTok Shop commerce evidence from TikTok Ads account evidence. These tools do not expose campaign spend, CPC, CPM, CTR, ROAS, budget, bid, or ad-group structure.

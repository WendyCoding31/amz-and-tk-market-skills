# Product Market Scout Rubric

Use this reference after collecting platform data from `compatible Amazon source` and/or `compatible TikTok Shop source`, then before writing the final Chinese answer.

## Trend Labels

Use the best available 7/30/90 day signal. Prefer 30-day trend for executive conclusions, and use 7-day data for acceleration/deceleration.

- `上升盘`: 30-day sales/GMV/search/BSR signal is up at least 15%, or 7-day acceleration is strong and supported by product/video/shop growth.
- `稳定盘`: 30-day change is between -10% and +15%, demand is consistent, and top products remain active.
- `下滑盘`: 30-day sales/GMV/search/BSR signal is down more than 10%, especially if 7-day data is also weak.
- `早期起量`: TikTok GMV/sales/video signals are rising from a low base, with several recent creators/shops/products gaining traction.
- `数据不足`: the required platform MCP does not return enough comparable time-series data.

## Competition Labels

Amazon competition:

- `高`: many sellers/listings, top ASINs have strong review moats, price is compressed, or seller concentration is high.
- `中`: demand exists, top competitors are established, but there is room through variant/spec/content differentiation.
- `低`: few credible sellers, weak review moat, fragmented listings, or underserved attributes.

TikTok Shop competition:

- `高`: many shops and creators pushing similar products, multiple videos/products already saturated, price copying is obvious.
- `中`: some winning products and creators exist, but angles are not exhausted.
- `低`: few sellers/videos, weak creator coverage, or content demand exists without many product matches.

## Margin Health

If product cost, freight, duties, platform fees, ads/affiliate commission, and returns are available, judge contribution margin from a seller perspective. If cost is missing, use price band only as a proxy and mark `需要成本确认`.

- `健康`: estimated gross margin >= 35% or contribution margin >= 20%.
- `一般`: gross margin 20%-35%, or contribution margin 10%-20%.
- `偏薄`: gross margin < 20%, contribution margin < 10%, or market price is already heavily compressed.
- `需要成本确认`: selling price looks possible, but landed cost or commission/ads assumptions are missing.

## Seller-Entry Fit

Prefer `适合卖家切入` when these signals appear together:

- Clear demand exists on at least one platform.
- Competition is not purely brand/review-moat dominated.
- The seller can compete on price, variant selection, bundle design, listing quality, traffic strategy, or brand positioning.
- Product can be differentiated by specs, bundle, scenario, creator content, or compliance quality.
- Compliance/IP/logistics and after-sales risk are manageable.

Use caution labels:

- `适合小单测试`: TikTok signal is rising but Amazon is crowded, or data is early.
- `适合精铺切入`: demand exists, price band is clear, and seller can compete with efficient listing or traffic operations.
- `适合品牌化切入`: demand exists but requires better content, brand story, bundle, or review strategy.
- `只适合差异化切入`: demand exists but direct copy would enter a price war.
- `不建议进入`: demand is falling, margin is thin, review or brand moat is too strong, or compliance/IP/logistics risk is high.

## Platform Recommendation

- Recommend `Amazon` when demand is stable, search intent is clear, reviews matter, and the seller can compete on pricing, listing quality, reviews, or variants.
- Recommend `TikTok Shop` when the product is visual, demonstrable, impulse-friendly, problem-solving, giftable, or creator-friendly, especially if GMV/video signals are rising from a low base.
- Recommend `先TK测款再Amazon` when Amazon is mature/crowded but TikTok shows early traction.
- Recommend `两边都可` only when Amazon demand is healthy and TikTok content traction is also proven.
- Recommend `暂不建议` when both platforms show weak demand, high competition, or poor margin.

## Compact Card Template

Use this table shape by default:

| 维度 | Amazon | TikTok Shop/TK | 判断 |
|---|---|---|---|
| 产品映射 | {Amazon关键词/类目} | {TK表达/类目} | {是否同一类产品} |
| 需求 | {销量/BSR/收入/趋势} | {GMV/销量/趋势} | {强/中/弱} |
| 竞争 | {卖家/评论/变体/价格} | {店铺/达人/视频/价格} | {低/中/高} |
| 利润 | {价格带/卖家利润判断} | {价格带/佣金判断} | {健康/一般/偏薄/待确认} |
| 进入建议 | {Amazon卖家打法} | {TK卖家打法} | {最终建议平台} |

If data is incomplete, keep the cell explicit: `数据源未返回` or `需补成本`.

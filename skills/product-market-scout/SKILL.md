---
name: product-market-scout
description: Analyze whether a product, category, link, title, image, 1688 item, Amazon ASIN/listing, TikTok Shop item, factory SKU, or natural-language product idea is selling well on Amazon and/or TikTok Shop. Use when the user asks in Chinese or English about Amazon/TK/TikTok Shop sales performance, product opportunity, category trend, marketplace comparison, recent 7/30/90 day demand, BSR, GMV, sales, reviews, seller competition, creator/video heat, pricing, margin, or whether a factory should enter/supply a product. Trigger on Chinese boss-style prompts like 卖得怎么样, 有没有机会, 最近30天涨还是掉, 哪个平台更适合做, 蓝牙耳机在美国亚马逊, 猫抓板在 TikTok 美区.
---

# Product Market Scout

## Goal

Turn a boss-style question into a data-backed Chinese business conclusion:

`自然语言查询 -> 标准化商品识别 -> proboost-mcp 多平台数据查询 -> 规则判断 -> 老板能看懂的中文结论 + 简表卡片`

Use this skill for quick executive product checks, not long market reports unless the user asks for depth.

## Hard Rules

- Use `proboost-mcp` for every place that needs current product, category, Amazon, TikTok Shop, sales, GMV, BSR, price, review, seller, creator, video, or trend data.
- If `proboost-mcp` tools are not visible, discover them first with tool discovery/search for `proboost-mcp`. If they still cannot be called, stop and say the data source is unavailable; do not replace it with guesses.
- Never invent numeric market data. If a metric is missing, say `proboost 暂未返回` or `数据不足`, then lower confidence.
- Answer in Chinese by default. Keep the final answer executive-friendly: conclusion first, table second, caveats last.
- Default marketplace assumptions: Amazon = US, TikTok Shop/TK = US, trend window = last 30 days. State these assumptions only when they affect the answer.

## Workflow

1. Identify the product signal from the user's query.
2. Normalize it into platform-ready product expressions.
3. Query proboost-mcp for Amazon/TikTok/category data.
4. Judge trend, competition, margin health, and factory-entry fit.
5. Output a short Chinese conclusion plus a compact comparison card.

For detailed thresholds and table wording, load [references/rubric.md](references/rubric.md) before final judgment.

## 1. Identify Product Signal

Classify the input into one or more signal types:

- `keyword`: e.g. `蓝牙耳机`, `猫抓板`.
- `marketplace link`: Amazon/TikTok Shop/TK URL, ASIN, product ID, shop link.
- `source link`: 1688, Taobao, Alibaba, factory catalog, supplier page.
- `image`: product photo or screenshot.
- `title`: marketplace title, listing title, factory title.
- `factory SKU`: internal item number or style code.
- `category`: broad category or subcategory, e.g. `宠物用品里的猫抓板`.

If the signal is ambiguous, infer the most likely product and continue with a clearly labeled assumption. Ask a concise clarifying question only when a wrong product mapping would make the answer misleading.

## 2. Normalize Product

Create a compact `Product Map` before querying:

- `工厂款式名`: Chinese product name or internal style name.
- `Amazon关键词`: 2-5 English search terms and likely category.
- `TikTok表达`: 2-5 creator/shop-friendly phrases, including use-case wording.
- `类目归属`: Amazon category and TikTok Shop category if inferable.
- `核心属性`: material, size, function, target user, price tier, differentiators.
- `输入来源`: keyword/link/image/title/SKU/category and any extracted IDs.

For links, query the exact listing first, then broaden to category/keyword peers. For 1688/factory items, map source-title attributes to Amazon/TikTok buyer-facing terms before searching.

## 3. Query proboost-mcp

Use the relevant proboost-mcp tools available in the session. Prefer exact ID/link queries first, then keyword/category discovery.

Amazon data to collect when relevant:

- Sales/revenue estimate and trend for 7/30/90 days.
- BSR and BSR trend.
- Price band and median price.
- Review count, rating, review velocity.
- Seller/listing count, top ASINs, seller concentration.
- Variation count and key variants.
- Category rank/category fit.

TikTok Shop/TK data to collect when relevant:

- GMV, units sold/orders, and trend for 7/30/90 days.
- Top products, shops, and price band.
- Creator/affiliate intensity, video count, video views/engagement heat.
- Shop growth and repeat-performing shops.
- Content angle/use-case patterns.

Category/trend data to collect when relevant:

- Category or keyword trend for 7/30/90 days.
- Top rising products and declining products.
- Price movement, review/competition movement, and creator/video movement.

If the user asks "哪个平台更适合做", query both Amazon and TikTok Shop unless one platform is clearly outside scope.

## 4. Judge

Use the rubric reference to label:

- `盘子阶段`: 上升盘 / 稳定盘 / 下滑盘 / 早期起量 / 数据不足.
- `竞争强度`: 低 / 中 / 高.
- `利润空间`: 健康 / 一般 / 偏薄 / 需要成本确认.
- `工厂切入`: 适合小单测试 / 适合做供应链切入 / 不建议直接切 / 只适合差异化切入.
- `建议平台`: Amazon / TikTok Shop / 两边都可 / 先TK测款再Amazon / 暂不建议.

Prefer balanced judgment over hype. A product with high demand and high competition is not automatically a good opportunity.

## 5. Output Format

Default response shape:

1. `一句话结论`: 1-2 sentences, direct enough for a boss.
2. `简表卡片`: compact Markdown table comparing Amazon and TikTok Shop/TK.
3. `为什么`: 3-5 short bullets with the strongest data-backed reasons.
4. `下一步`: one practical action, e.g. `先测 TK 20-50 单`, `找 3 个差异化卖点`, `补工厂成本再算毛利`.
5. `缺口/风险`: only include when data is missing or confidence is limited.

Example tone:

`这个产品在 Amazon 属于成熟稳定盘，近30天需求平稳但卖家拥挤；TikTok Shop 还在起量早期，内容热度有信号，更适合先用小单测款。`

Keep the table short enough to paste into chat.

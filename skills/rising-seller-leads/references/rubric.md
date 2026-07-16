# Rising Seller Leads Rubric

Use this rubric after collecting configured marketplace capabilities data.

## Candidate Score

Score each candidate from 0-100. Use evidence, not vibes.

- `Category Fit` 0-25: semantic match, price-band match, buyer match, attributes, and supply-chain similarity.
- `Growth` 0-25: 30/60/90 day sales or GMV growth, SKU expansion, review velocity, TikTok content/creator/live acceleration.
- `Supplier Fit` 0-20: likely need for new products, private label, variants, better cost, better quality, faster launch, or compliance support.
- `Contactability` 0-15: configured seller-enrichment source seller company information, public website, official store, email, phone, address, LinkedIn, Instagram, TikTok business account, or clear seller/shop page.
- `Strategic Accessibility` 0-15: not platform retail, not a dominant mega-brand, not a zero-margin race-to-bottom seller, and not locked into an obvious closed supply chain.

Priority labels:

- `A`: 75-100. Contact first; strong fit plus clear growth/contact route.
- `B`: 55-74. Worth testing; good fit but one missing signal.
- `C`: 35-54. Keep in watchlist; weak contactability or incomplete growth data.
- `Exclude`: below 35 or fails a hard exclusion rule.

## Growth Signals

Use the strongest available evidence:

- `高增长`: recent 30-day sales/GMV up at least 20%, or 60/90 day slope is clearly positive with SKU/content expansion.
- `温和增长`: recent 30-day sales/GMV up 5%-20%, or stable sales with new SKU/review/content growth.
- `早期爆发`: TikTok shop/product/video GMV grows from a low base with several new creators/videos/live sessions.
- `稳定成熟`: sales are large but growth is flat; useful only if supplier gap is obvious.
- `数据不足`: growth data unavailable or only one product datapoint exists.

When only SKU-level data is available on Amazon, mark the seller growth as `商品侧推断`.

## Exclusion Rules

Exclude or down-rank:

- Platform retail/self-operated seller, e.g. Amazon.com, unless user asks for benchmark only.
- Mega-brand with entrenched brand moat and no realistic supplier angle.
- Pure low-price copycat where margin appears unhealthy.
- Product mismatch caused by keyword overlap but different supply chain.
- No public business contact route after reasonable enrichment.
- Compliance/IP risk too high for the factory's category.

## Amazon Seller Enrichment

When Amazon seller leads are requested, use `configured seller-enrichment source` `amazon.seller_search` after product/seller discovery whenever seller IDs, seller names, business names, SKUs, SPUs, or item titles are available.

Preserve every returned seller enrichment field in the output or in a supporting table:

- `seller_id`: seller ID.
- `seller_name`: seller/store name.
- `bus_name`: company/business name.
- `address`: company/seller address.
- `phone`: phone; may be masked as `****`.
- `email`: email; may be masked as `****`.
- `stars`: store rating.
- `ratings`: store rating count.
- `item_cnt`: active/listed item count.
- `sold_cnt_lst_yr`: last-year sales units.
- `sold_amt_cur_yr`: current-year sales amount.

If `phone` or `email` is `****`, score it as partial contactability only and label it `configured seller-enrichment source已脱敏`. Do not treat a masked value as a usable email or phone number. If a field is absent, write `configured seller-enrichment source暂未返回`.

## Outreach Fit Reasons

Use concrete supplier-fit reasons such as:

- `正在扩品`: multiple SKUs or variants indicate product-development appetite.
- `内容起量`: TikTok creator/video/live growth suggests they need faster supply and new angles.
- `评论痛点`: reviews mention quality, accessory, packaging, sizing, durability, noise, fit, or safety gaps.
- `价格带匹配`: their winning price band can support factory's target landed cost.
- `套装机会`: current sellers lack bundles/accessories/colorways.
- `合规升级`: factory can provide certification, packaging, labeling, or safer materials.
- `补货压力`: sales growth implies stock/MOQ/speed advantages matter.

## Contact Source Labels

Use exact source labels:

- `数据源店铺详情`
- `Amazon店铺页`
- `TikTok Shop页`
- `品牌官网`
- `LinkedIn公司页`
- `Instagram企业号`
- `TikTok企业号`
- `configured seller-enrichment source卖家信息`
- `configured seller-enrichment source已脱敏`
- `公开邮箱`
- `公开渠道待补`

Never output guessed email formats.

## Output Template

Start with a short conclusion:

`建议优先建联 A 类卖家：同类目、近30/90天有增长、还在扩品、有公开触达渠道，且不是 Amazon 自营或大品牌封闭供应链。`

Then use:

| 优先级 | 卖家/店铺 | 平台 | 主打产品 | 增长信号 | 联系方式来源 | 适配理由 | 下一步 |
|---|---|---|---|---|---|---|---|
| A | {name} | {Amazon/TK} | {products} | {30/60/90d growth or signal} | {source} | {supplier-fit reason} | {specific outreach action} |

After the table, add:

- `触达顺序`: A first, then B, C only watchlist.
- `话术切入`: one sentence tailored to the category and seller gap.
- `数据缺口`: list missing marketplace/contact fields.

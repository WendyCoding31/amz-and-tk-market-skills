---
name: amz-premium-select
description: Screen Amazon US shortlisted keywords, ASINs, or product ideas into premium semi-standard and non-standard product opportunities. Use when the user asks to continue from a keyword shortlist into ASIN/product validation, competitor candidate selection, traffic-entry analysis, monthly-sales gates, SKU development, or final Amazon product-opportunity workbooks. For keyword-only seed expansion and precise keyword screening, use amz-keyword-select0610 instead.
---

# AMZ Premium Select

Use this skill to turn Amazon US shortlisted keywords, ASIN research, or product ideas into a short list of developable semi-standard/non-standard products. The goal is not to find any product with sales; the goal is to find product opportunities with non-standard differentiation space, tolerable ad economics, verified ASIN evidence, and practical SKU development paths.

For seed-keyword expansion, full-pool keyword filtering, ABA/CPC/CPA keyword-only screening, and keyword-only Excel workbooks, use `amz-keyword-select0610` first. This skill starts after the user already has retained/observation keywords or explicitly asks to enter ASIN/product validation.

Default language is Chinese. Default marketplace is Amazon US unless the user specifies otherwise.

## Methodology boundary

This public package is self-contained. Private research notes, customer files, and historical workbooks are not runtime dependencies.

## Hard Rules

- Prioritize semi-standard products and non-standard products. Exclude pure standard products before SKU recommendation.
- Never invent live market numbers. Use live data tools when available; if not available, produce a framework, field checklist, and clearly mark numeric fields as `待查`.
- Treat data-source quota/tool blockers as hard blockers for live keyword expansion. Do not imply that live data was used when the provider is unavailable.
- Remove or downgrade branded, copyright, patent, trademark, or obvious IP-risk keywords/products.
- Keep product supply-demand ratio visible for human review, but do not use it as an automatic elimination rule.
- Final ASIN candidates must prioritize verified monthly sales of 50-1000 units. ASINs with monthly sales > 1000 are red-ocean/bestseller references only and must not be used as final candidate ASINs unless the user explicitly asks for benchmark competitors.
- For keyword-to-ASIN work, first build a candidate pool with `amazon.product_search` or `amazon.product_search`, then enrich each short-listed ASIN with detail, sales trend, and traffic tools. Do not choose ASINs only from titles or top-sales order.
- Keep exactly 3 backup ASINs per retained keyword when possible. If fewer than 3 qualified ASINs meet the sales/risk/semantic gates, output only the qualified ASINs and state the gap instead of forcing red-ocean or unsafe ASINs into the list.
- The required output artifact is an Excel workbook (`.xlsx`), not only a chat table. The chat response should be a short conclusion plus a link to the workbook.

## Data source

Read [references/data-source.md](references/data-source.md) before live queries. Use any configured source that covers the required fields, and record the field mapping and missing values.

| Workflow need | Required logical capability |
|---|---|
| Upstream keyword shortlist | Produced by `amz-keyword-select0610`; do not redo keyword-only screening here |
| Keyword-level candidate ASIN pool | `amazon.product_search` |
| ASIN detail, price, rating, category, seller, variants, listing quality | `amazon.product_detail` |
| ASIN sales, revenue, price and BSR trend | `amazon.sales_history` |
| Traffic entrance count and traffic summary | `amazon.traffic_structure` |
| Traffic keywords, CPC, search volume, purchase rate, rank and share | `amazon.keyword_research` + `amazon.traffic_structure` |
| Review/VOC signal | `amazon.review_search` |

If the source is unavailable or quota-blocked, continue with a degraded path: classify semantics, list required fields, and avoid numeric conclusions.

## Workflow

### 1. Normalize Input

Classify the user input:

- `seed_keyword`: broad term such as `gifts`.
- `keyword_pool`: pasted keywords or spreadsheet rows.
- `asin`: one or more Amazon ASINs.
- `product_idea`: natural-language product concept.
- `source_file`: local workbook, CSV, or notes file.

If the user gives only a seed keyword or asks for keyword-only screening, use `amz-keyword-select0610` first. If the user gives only ASINs, use them as candidate examples or competitor samples and infer/query their likely keyword entry points.

### 2. Keyword Shortlist Intake

If the user only gives a seed keyword or asks for keyword-only screening, stop and use `amz-keyword-select0610` first. Do not duplicate the keyword-selection workflow here.

When this skill receives retained/observation keywords from `amz-keyword-select0610`, preserve these keyword fields in the workbook and ASIN search notes:

- `关键词`, `关键词中文`, `ABA排名`, `当前同月ABA`, `去年同月ABA`, `前年同月ABA`, `ABA同比判定`.
- `CPC`, `转化率`, `CPA`, `集中度`, `月搜索量`, `月搜索量同比增长率`.
- `关键词阶段`, `开品建议`, `SKU方向`, `风险备注`.

Treat keyword-screening decisions as upstream evidence. Do not move a keyword with `CPA > 15`, `ABA above the user's ceiling`, brand/IP risk, or hard keyword rejection back into the ASIN candidate pool unless the user explicitly asks to override the keyword screen.

### 3. Build Keyword-to-ASIN Candidate Pool

For each retained keyword, first pull a candidate ASIN list with configured source `amazon.product_search` or `amazon.product_search`.

Candidate-pool filters:

| Field | Rule |
|---|---|
| Price | prefer > 25 USD; stronger > 35 USD |
| Monthly sales | final candidates must prioritize 50-1000 units/month |
| Product shape | holder, rack, stand, organizer, shelf, basket, bag, display, mount, bracket, tray, sign, decor, gift set, kit, pack, accessory, or similar semi/non-standard form |
| Scene/person | sympathy, women, spa, nurse, birthday, teacher, graduation, wedding, care package, outdoor, vehicle/boat/sports ecosystem, etc. |
| SKU expansion | must support at least 4 SKU directions through combination, theme, color, quantity, packaging, component, or material changes |
| Risk | remove or downgrade pure standard products, certification/safety-heavy products, strong brand/IP/patent risk, and low-price products that cannot be bundled |

Monthly sales gate:

| Monthly sales | Decision |
|---:|---|
| < 50 | observation only unless the niche is extremely precise and competition is weak |
| 50-1000 | preferred final ASIN candidate range |
| > 1000 | red-ocean/bestseller reference only; do not use as a final candidate |

After the candidate pool, enrich short-listed ASINs with:

- `amazon.product_detail`: title, brand, price, rating, reviews, category, seller, variants, and listing-quality evidence.
- `amazon.sales_history`: monthly sales, revenue, price, and BSR trend.
- `amazon.traffic_structure` and `amazon.keyword_research`: traffic entrance count, keyword structure, rank, CPC, purchase rate, supply-demand ratio, and traffic share.
- `review` when VOC, safety, sizing, material, odor, breakage, or compliance risk matters.

If configured source returns no qualified ASINs in the 50-1000 monthly-sales range, keep searching narrower scene/person/material/set keywords. If still unavailable, state `未找到合格 ASIN` and provide benchmark ASINs separately as non-final references.

### 4. ASIN and Product-Type Gate

For each retained candidate ASIN, inspect product, sales, and traffic structure:

- Price, category, sales, review count, rating.
- Verified monthly sales and sales trend.
- Traffic entrance count.
- Number of high-, mid-, and low-traffic keywords.
- Whether traffic distribution drops sharply from big words to tail words.
- CPC, conversion rate, CPR/ranking effort, category competition, monopoly/concentration.
- Differentiation: components, material, color, pattern, packaging, installation, use case.

Classify product type by traffic entrance count:

| Traffic entrances | Type | Decision |
|---:|---|---|
| < 100 | pure standard product | eliminate unless there is strong semi-standard evolution evidence |
| 100-500 | semi-standard product | keep if attributes and variants exist |
| > 500 | non-standard product | prioritize if economics and risk are acceptable |

Calculate cliff index when keyword ranking data is available:

```text
cliff_index = sum(last_3_keyword_ABA_ranks) / sum(top_3_keyword_ABA_ranks)
```

Interpretation:

| Cliff index | Meaning | Playbook |
|---:|---|---|
| > 3.5 | traffic depends heavily on big words | high-budget core-word play; only keep if differentiation is strong |
| around 1.0 | traffic is dispersed | multi-layer keyword play; usually better for non-standard products |
| lower/smaller | more dispersed | good for attribute-rich non-standard products |

Use the quadrant view:

| Entrances / cliff | Category type | Decision |
|---|---|---|
| low entrances + high cliff | big standard / semi-standard evolving | usually eliminate or keep only as cautious C |
| many entrances + high cliff | large non-standard | keep, but plan core words plus attribute words |
| low entrances + low cliff | small niche | low-ad test only |
| many entrances + low cliff | large non-standard with balanced traffic | top priority |

### 5. CPA Check

Use this formula:

```text
CPA = ad_spend / ad_orders = CPC / conversion_rate
```

CPA is the only ad-economics calculation this skill performs by default.

| CPA | Decision |
|---:|---|
| <= 10 USD | hard-screen pass |
| > 10 and <= 15 USD | observation only; do not count as hard-screen pass |
| > 15 USD | reject |

### 6. Semantic and SKU Development Check

Apply the artificial-success-sample logic:

```text
specific scene
+ clear buyer/person
+ semi-standard or non-standard shape
+ combinable set
+ light-customizable material
+ 4+ SKU variant paths
+ controllable IP/patent risk
= development candidate
```

Preferred product shapes:

- Holder, rack, stand, organizer, shelf, basket, bag, display, mount, bracket.
- Tray, sign, decor, centerpiece, garland, table runner, placemat.
- Gift set, party favors, kit, pack, assorted bulk products.
- Small accessories for boat, golf cart, trailer, tractor, pool, horse, camping, classroom, wedding, or party ecosystems.

Preferred materials/processes:

- Paper, wood, fabric, ceramic, glass, rattan/wicker, burlap, sticker/label, resin/silicone mold, balloon, pinata.
- Prefer print, decal, hand-painting, laser cutting, engraving, sewing, cutting, low-cost molding, or packaging combinations.
- Avoid large steel molds, heavy injection-mold development, hard certification products, and high-return products unless the user explicitly wants that path.

Practical product formula:

```text
event/person/theme
+ storage/display/gift/decor/set/accessory shape
+ easy-to-modify material
+ color/pattern/quantity/package/component variations
= semi-standard or non-standard SKU opportunity
```

### 7. Output

Always create an Excel workbook (`.xlsx`) as the main deliverable.

The workbook must include a main sheet named `筛选结果`.

- Row 1 must be a visible title row, for example `amz-premium-select - {seed keyword} 选品筛选结果`, preferably merged across the main table width. Use dark text so the title remains visible in WPS/Excel even if fill colors are not rendered.
- Row 2 must contain these required columns in this exact order. Put `关键词中文` immediately to the right of `关键词` so the user can scan the keyword meaning quickly.
- For keyword-discovery requests, the main `筛选结果` sheet is a qualified/observation shortlist, not a dump of all tested keywords. Exclude hard rejects from this sheet and place them in `淘汰记录` when needed.

| Column | Meaning |
|---|---|
| `关键词` | retained or observation candidate keyword generated from the seed; hard-rejected keywords belong in `淘汰记录`, not the main sheet |
| `关键词中文` | concise natural Chinese meaning of the keyword; translate the buying context for human review, do not repeat the English keyword or use awkward word-by-word translation |
| `ABA层级` | HTS / HT / MT / LT, based on the latest available ABA rank |
| `ABA排名` | latest available concrete ABA/search-frequency rank number from configured source |
| `CPC` | configured source PPC bid, USD |
| `转化率` | configured source purchase/click conversion rate; use percent format |
| `CPA` | `CPC / 转化率`; hard-screen pass only when <= 10 USD |
| `集中度` | Top 3 click/conversion concentration; use configured source top3/ARA concentration when available |
| `当前同月ABA` | current query month ABA/search-frequency rank |
| `去年同月ABA` | same-month ABA/search-frequency rank from last year |
| `前年同月ABA` | same-month ABA/search-frequency rank from two years ago |
| `ABA同比判定` | improved / unchanged / regression <=20% / regression >20% / 待查 |
| `入口数` | representative ASIN traffic entrance count from configured source traffic-source data |
| `断崖指数` | traffic cliff index; if keyword-level ranks are unavailable, write `待查` and explain in notes |
| `产品类型` | pure standard / semi-standard / non-standard, based on traffic entrances plus semantic review |
| `开品建议` | direct keep/drop recommendation and SKU development direction |

Recommended optional sheets:

- `执行摘要`: seed keyword, marketplace, latest data month, data source, keyword-screening counts, overall conclusion.
- `数据依据`: raw configured source observations, representative ASINs, ABA trend notes, and any unavailable fields.
- `淘汰记录`: hard rejects and rejection reasons, especially `CPA > 15`, `ABA above current ceiling`, brand/IP risk, pure standard product, or severe compliance/safety risk.

When the user asks to land keywords into ASINs, the workbook must also include an `ASIN备选` sheet.

`ASIN备选` rules:

- Keep up to 3 qualified backup ASINs per retained keyword.
- Final candidate ASINs must be in the 50-1000 monthly-sales range when configured source sales data is available.
- ASINs with monthly sales > 1000 may appear only as `爆品参考`, not as `最终备选`.
- If fewer than 3 qualified ASINs exist, leave only the qualified ASIN rows and explain `未找到足够合格 ASIN`.

Recommended `ASIN备选` columns:

| Column | Meaning |
|---|---|
| `关键词` | source keyword |
| `ASIN` | candidate ASIN |
| `Amazon链接` | product URL |
| `候选类型` | `最终备选` / `爆品参考` / `淘汰` |
| `选择等级` | S/A/B/C/D |
| `价格` | current or latest configured source price |
| `月销量` | verified monthly sales from `amazon.sales_history` or an equivalent normalized source |
| `月销售额` | verified monthly sales amount |
| `评分/评论数/变体数` | listing quality and competition context |
| `类目路径` | category path |
| `流量入口数` | traffic entrance count from traffic tools |
| `Top流量词` | main traffic keywords and their traffic shares when available |
| `产品形态` | holder/rack/stand/organizer/basket/bag/decor/gift set/kit/pack/accessory/etc. |
| `场景人群` | concrete scene and buyer/person |
| `4个SKU方向` | at least 4 SKU directions from theme, color, quantity, packaging, material, or component changes |
| `风险/降级原因` | pure standard, IP, certification/safety, low price, red-ocean, or other blocker |
| `下一步动作` | sourcing, compliance, CPA/ad, or review/VOC checks |
| `数据源` | configured source tools used |

In chat, return only a concise Chinese conclusion and a Markdown link to the workbook. Do not replace the workbook with a long market essay.

Use grades:

| Grade | Meaning |
|---|---|
| S | non-standard, many entrances, dispersed traffic, strong scene, healthy CPA |
| A | semi/non-standard with clear differentiation and acceptable CPA |
| B | usable but needs narrow keyword or CPA/ad control |
| C | cautious test only, small niche or fragile economics |
| D | pure standard, IP risk, low price, or ad economics fail |

## Example Final Verdict Wording

Use direct seller language:

`这个词可以继续看，但不是因为它有销量，而是因为它有明确婚礼/派对场景、候选 ASIN 不是纯标结构、月销量在 50-1000 的可切入区间，材料能轻定制，并且可以做 4 个以上主题变体。下一步应优先验证 CPC、转化率和 Top 3 集中度，确认 CPA 能否压在 10 美金以内。`

If blocked:

`当前只能做语义和流程判断，不能输出真实 ABA/CPC/转化率结论；configured configured source 的实时数据还没拿到或已被额度阻塞。`

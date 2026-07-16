---
name: amz-keyword-select0610
description: Screen Amazon US seed keywords or keyword pools into precise product-development keywords before ASIN research. Use when the user asks to find 精准关键词, 筛 gift/关键词库, apply ABA/CPC/CPA/search-growth filters, exclude gift cards/IP/pure generic terms, or output a keyword-only Excel shortlist. Do not use this skill for ASIN selection, competitor lookup, traffic-entry analysis, or final product-ASIN validation.
---

# AMZ Keyword Select 0610

Use this skill to turn a broad Amazon keyword such as `gift` or a pasted keyword pool into a short list of precise, product-developable keywords. Stop at the keyword layer. Do **not** enter ASIN selection, traffic entrance count, cliff index, review mining, or competitor validation.

Default language: Chinese. Default marketplace: Amazon US.

## Boundary

This skill owns only:

- Seed keyword expansion from a configured Amazon keyword source.
- Full-pool filtering, not page-1 picking.
- Keyword-level hard screens: price, PPC, conversion rate, CPA, concentration, ABA rank, trend, IP/brand risk, product semantics.
- Excel workbook output with retained/observation keywords plus elimination records.

This skill must not enter ASIN research, competitor discovery, review mining, or traffic-structure analysis. If the user asks to continue into ASINs, finish the keyword workbook first and hand off to the ASIN/product selection skill.

## Data Source

Read [references/data-source.md](references/data-source.md). Use any configured source that can provide the required keyword fields, and preserve the provider-specific field mapping.

| Need | Logical capability |
|---|---|
| Seed/root keyword pool | `amazon.keyword_research` |
| Exact ABA rank and same-month ABA history | `amazon.keyword_history` |
| Extra keyword trend check | `amazon.keyword_history` |

Never invent live market numbers. If the configured source is unavailable or quota-blocked, output a degraded framework with numeric fields marked `待查`.

## Full-Pool Entry Rule

For broad roots such as `gift`, do **not** start from unfiltered page 1. Page 1 is usually dominated by ultra-hot generic, brand, media, or gift-card terms.

Start from a full-pool keyword query using the provider's mapped fields:

```json
{
  "marketplace": "US",
  "seed_keyword": "<seed>",
  "month": "<yyyymm>",
  "min_average_price": 25,
  "max_cpc": 1,
  "exclude_terms": ["gift card", "gift cards"],
  "sort_by": "monthly_searches_desc"
}
```

This is a query intent, not a literal MCP request. Map it to the configured provider and record the exact exclusions.

## Field Mapping

Normalize provider fields into these canonical meanings before screening:

| Business field | Canonical field | Notes |
|---|---|---|
| 转化总占比 | `conversion_share` | Use for `<30%`; do not substitute click concentration |
| 点击集中度 | `click_concentration` | Different from 转化总占比 |
| 月搜索量同比增长率 | `search_volume_yoy` | Use `>0` only when upward YoY trend is requested |
| 近3个月增长率 | `search_growth_3m` | Do not confuse with YoY |
| PPC竞价 | `cpc` | CPC input for CPA |
| 购买率/转化率 | `purchase_rate` | Decimal format, e.g. `0.10` = 10% |

If two sources or interfaces return different counts for the same apparent filters, record both counts and the exact fields used. Do not force the numbers to match.

## Hard Rules

- ABA rank is ordinal: smaller number means stronger demand. A move from `15,159` to `118,080` is demand regression.
- User-relaxed ABA ceilings, such as `<=500,000`, are only outer boundaries. They do not override CPA failure, severe trend regression, IP risk, or weak product semantics.
- Main `筛选结果` contains only retained or observation keywords. Hard rejects go to `淘汰记录`.
- `CPA = cpc / purchase_rate`.
- CPA `<=10` is hard pass. CPA `>10 and <=15` is observation only. CPA `>15` is reject.
- Purchase/conversion rate must be `>5%` for a keyword to remain in the main sheet.
- `conversion_share` must be `<=0.30` for a keyword to remain in the main sheet.
- Remove gift card variants, brand/IP/trademark/copyright/media terms, book/movie/music terms, and obvious pure search-intent terms such as generic `ideas` unless they are only used as拆词入口.
- Avoid hard-compliance or inconvenient categories unless the user explicitly wants them: food, alcohol, perfume/cologne, supplements, weapons, safety-certified baby/child products.
- Broad age/person gift terms with both `CPA >10` and `ABA同比判定 = regression >20%` are rejected or拆词-only, not retained as product-development keywords.

## Workflow

### 1. Normalize Input

Classify the input:

- `seed_keyword`: a broad root such as `gift`, `teacher gift`, `baby shower gift`.
- `keyword_pool`: pasted rows or a workbook/CSV already containing keywords.
- `source_file`: local workbook or CSV.

If the input is a seed keyword, query the configured source. If the input is a pool or file, preserve source rows and add screening columns.

### 2. Build the Initial Pool

For a seed keyword:

1. Run the mapped `amazon.keyword_research` capability using the full-pool entry rule.
2. Paginate the filtered result set. Do not rely on page 1.
3. Save or preserve raw observations for `数据依据`/`初筛池明细`.
4. Apply local `conversion_share <= 0.30` if the provider does not expose a server-side filter.

For a `gift` baseline, a reasonable initial filter is:

```text
include keyword: gift
exclude: gift card, gift cards
price >= 25
PPC bid <= 1
转化总占比 <= 30%
optional: 月搜索量同比增长率 > 0
```

### 3. Metric Screen

Calculate for every row:

```text
CPA = cpc / purchase_rate
```

Apply:

| Field | Keep/observe rule |
|---|---|
| `avgPrice` | `>=25` |
| `bid` | `<=1` |
| `purchase_rate` | `>0.05` |
| `CPA` | `<=10` keep; `10-15` observe; `>15` reject |
| `conversion_share` | `<=0.30` |
| `search_volume_yoy` | `>0` only when the user asks for YoY-up pool |

Do not put CPA-over-15 rows in the main sheet.

### 4. Semantic Productability Screen

Keep keywords that point to a concrete product-development path:

```text
scene/person/event
+ semi-standard or non-standard form
+ set/basket/box/holder/decor/kit/pack/accessory shape
+ 4+ SKU variation paths
+ controllable IP/compliance risk
```

Good forms:

- gift set, gift basket, gift box, care package, keepsake, plaque, frame, ornament, sign, decor.
- holder, stand, rack, organizer, tray, bag, tumbler, mug, blanket, candle, kit, pack.
- wedding, baby shower, teacher, nurse, sympathy, memorial, get well, bridesmaid, new mom, birthday, graduation scenes.

Downgrade or reject:

- Pure generic terms: `gift for women`, `gift ideas`, `the gift`.
- Wide age terms unless they are拆词入口: `3 year old boy gift`, `gift for 2 year old boy`.
- Strong brand/IP/media terms.
- Food/perfume/alcohol-heavy gift basket markets unless the product can be redirected to non-food packaging/care-package forms.

### 5. ABA Supplement

Before writing the final main sheet, query `amazon.keyword_history` for every candidate that survived metric and semantic screening.

Keep these same-month fields visible:

- Current month ABA, e.g. `2026-05`.
- Last-year same-month ABA, e.g. `2025-05`.
- Two-years-ago same-month ABA, e.g. `2024-05`.

Judge ABA trend:

| Condition | 判定 |
|---|---|
| current rank <= last-year rank | `improved` |
| current rank is worse by <=20% | `regression <=20%` |
| current rank is worse by >20% | `regression >20%` |
| missing comparable ranks | `待查` |

Move candidates with latest ABA above the user's current ceiling out of the main sheet, even if other metrics look good.

ABA tiers:

| Tier | ABA rank |
|---|---:|
| HTS | `<10,000` |
| HT | `10,000-50,000` |
| MT | `50,000-200,000` |
| LT | `>200,000` |

## Output Workbook

Always create an `.xlsx` workbook.

Required sheets:

- `筛选结果`: retained and observation keyword shortlist only.
- `执行摘要`: seed, marketplace, month, data source, exact filters, counts by stage, conclusion.
- `数据依据`: field mapping, formulas, count discrepancies, raw data file path if any.
- `初筛池明细`: all tested keyword rows with computed CPA, stage, and reason.
- `淘汰记录`: hard rejects and downgrade reasons.
- `ABA趋势补充`: ABA same-month history for main-sheet keywords.

`筛选结果` row 1 is a visible title. Row 2 must contain these columns in this order:

| Column |
|---|
| `关键词` |
| `关键词中文` |
| `ABA层级` |
| `ABA排名` |
| `CPC` |
| `转化率` |
| `CPA` |
| `集中度` |
| `当前同月ABA` |
| `去年同月ABA` |
| `前年同月ABA` |
| `ABA同比判定` |
| `产品类型` |
| `关键词阶段` |
| `开品建议` |
| `SKU方向` |
| `风险备注` |
| `月搜索量` |
| `月购买量` |
| `月搜索量同比增长率` |
| `平均价格` |
| `商品数` |
| `供需比` |
| `类目` |
| `数据源` |

Do not include `入口数`, `断崖指数`, ASIN columns, monthly sales, review count, or competitor fields in this keyword-only workbook.

## Final Response

Return a short Chinese conclusion plus a Markdown link to the workbook. Mention:

- Initial pool count and filtered count.
- Main-sheet retained/observation count.
- Any important field mismatch, such as web UI count vs MCP count.
- The strongest keyword clusters.

Do not replace the workbook with a long essay.

---
name: listing-generator0514
description: "Use this skill to generate or optimize Amazon listings from one source ASIN for precise-follow selling across the 6 EU marketplaces (UK, DE, IT, FR, ES, NL). Keep the source ASIN physical facts unchanged, independently mine competitors and keywords per target marketplace, integrate VOC review evidence, strictly allocate and embed keywords by listing position, localize copy per marketplace, and export one template-aligned workbook per marketplace (6 workbooks per SKU)."
---

# listing-generator0514

Generate a better Amazon listing from one source ASIN while keeping the product facts strictly aligned to that source ASIN.

## Use this skill for

- one source ASIN listing generation
- one source ASIN listing optimization
- precise-follow selling workflows
- bilingual output: target-language listing plus Chinese draft
- multi-marketplace expansion: independent listings for UK, DE, IT, FR, ES, NL (6 workbooks per SKU)

## Default target marketplaces

Unless the user specifies otherwise, generate listings for all 6 EU marketplaces:

| Code | Marketplace | Language |
|------|-------------|----------|
| UK   | amazon.co.uk | English (en-GB) |
| DE   | amazon.de    | German (de-DE)  |
| IT   | amazon.it    | Italian (it-IT) |
| FR   | amazon.fr    | French (fr-FR)  |
| ES   | amazon.es    | Spanish (es-ES) |
| NL   | amazon.nl    | Dutch (nl-NL)   |

For each target marketplace, run the full workflow independently: competitor mining, keyword expansion, VOC analysis, listing writing, locale lint. Cross-marketplace reuse of competitors or keywords is not allowed.

## Keep this light

Do not keep large raw MCP responses in chat context.

Always do this instead:

- fetch source and competitor data into local JSON files
- fetch keyword results into local files or workbooks
- only bring back short summaries into context
- never paste long raw review blocks, long bullet arrays, or full keyword tables into the conversation unless the user explicitly asks

## Hard constraints

The source ASIN is the truth for product facts.

Never change these unless the user gives verified replacement data:

- material
- dimensions
- pack size
- color family
- structure and shape
- core function
- target usage form

Do not borrow physical attributes from competitors just because their listing looks better.

## Template alignment boundary

Align shared listing outputs to the manual workbook style:

- target-language listing sheet with field rows, final copy, character count, and character limit
- bilingual draft sheet with Chinese copy and translation/localization draft
- keyword sheet with allocation positions, keyword metrics, retention/drop decisions, embedding evidence, and raw keyword appendices

Do not reproduce the manual workbook's product-selection or supply-chain sheet unless explicitly asked. Excluded fields include 1688 links, sourcing price, logistics/FBA/profit/ROI calculations, supplier recommendations, seasonal flags, patent checks, and business scoring fields.

Keep the skill's extra evidence requirements. The manual template is the output style target, not a reason to remove the 100-row competitor relevance process, image relevance scoring, source-ASIN fact lock, or raw Amazon keyword source traceability.

## Review priority

Judge output in this order:

1. keyword precision
2. listing completeness

## Inputs

Required:

1. source ASIN
2. target workbook output directory or template path

Optional:

- target marketplaces list (default: all 6 — UK, DE, IT, FR, ES, NL)
- per-marketplace `web_site_id` overrides if non-default

Derived during workflow (repeated per target marketplace):

- source product detail JSON (shared across marketplaces — facts are immutable)
- per-marketplace competitor pool (independent)
- per-marketplace VOC review pool (independent)
- per-marketplace keyword workbook (independent)
- per-marketplace retained keyword list (independent)

Default output mode:

- target marketplace language listing sheet
- Chinese draft sheet (shared structure across the 6 workbooks; copy may be reused since Chinese is the bridge draft)
- 6 workbooks total per source ASIN, one per target marketplace

## Data source priority

Use this order for source and competitor product data:

1. `amazon.product_search` for the source leaf category 100-row competitor table
2. `amazon.product_search` for source/candidate detail backfill when available
3. `amazon.product_detail`
4. `amazon.sales_history`
5. Amazon frontend page only as manual verification fallback

Field trust order:

1. source physical attributes from a compatible `amazon.product_detail` source
2. listing text from the source detail or category product rows
3. URL, category, brand, title, and main image URL from `amazon.product_search`
4. sales context from `amazon.sales_history`

If sources disagree on physical attributes, stop and verify. Do not guess.

## Bundled scripts

- `scripts/fetch_listing_payload.py`
  - normalize one ASIN from provider-exported JSON
  - perform no network or MCP configuration access
  - write canonical JSON with provider and field-map evidence
- `scripts/relevance_estimate.py`
  - score one competitor against the source ASIN
  - extract both ASIN main image URLs and call a user-configured image-similarity adapter when available
  - default score basis is `60% image relevance + 40% title relevance`
  - output `score_percent`, `title_score_percent`, `component_scores.image_match`, and the `image_match` trace
  - use `--skip-image-match` only for explicit degradation; do not use title-only scoring to select competitors
- `scripts/title_relevance.py`
  - score title relevance between source and candidate titles
  - used by `relevance_estimate.py` as the title component of competitor relevance
- `scripts/keyword_relevance_pipeline.py`
  - filter and rank keywords from local JSON
- `scripts/bullet_similarity.py`
  - compute token Jaccard similarity between each drafted bullet and every Top-20 competitor's bullets
  - enforce the hard rule: similarity must be `< 50%` against any single competitor's corresponding-or-any bullet
  - usage: `python scripts/bullet_similarity.py <draft_bullets.json> <top20_bullets.json>` (exit 1 if any pair ≥ 50%)
- `scripts/locale_lint.py`
  - target-language hard-rule check on the finished workbook
  - supported marketplaces: UK, DE, IT, FR, ES, NL — pass `--marketplace <code>` (lowercase or uppercase)
  - common flags across all 6: 中国电商话术 / 单位与英寸残留 / sentence case 标题校验 / 英文 SEO 词渗透正文 (非英语站) / 数字本地化（小数点逗号/句点按站点）
  - DE-specific: 复合词分写提示 / 德语名词大小写
  - UK-specific: 英式拼写偏好（colour/centre 等）
  - WARN level: em dash → en dash, 翻译腔短语（按站点）
  - run before delivery per workbook: `python scripts/locale_lint.py <workbook.xlsx> --marketplace <code>` (exit 1 if any ERROR)

## Minimal workflow

### 1. Resolve source ASIN

Run:

```bash
python scripts/fetch_listing_payload.py <ASIN> --web-site-id <id> --output source.json
```

Collect:

- title
- bullets
- description if available
- main image URL
- brand
- category path
- price
- reviews and rating
- dimensions and weight
- recent sales context
- product subject phrase:
  - identify the actual thing being sold, not only its accessory
  - if the product is "honey jar with spoon", the subject is "honey jar with spoon" / "honey jar", not "spoon"
  - record subject terms and accessory terms in local notes or `source.json` when possible

### 2. Build the 100-row competitor review table (per target marketplace)

Repeat this step independently for each target marketplace (UK, DE, IT, FR, ES, NL). Each marketplace has its own leaf-category candidate pool, its own 100-row table, its own Top-20.

Do not manually hunt for `50` competitors.

Use the corresponding leaf category in the target marketplace:

1. Resolve the leaf category and marketplace code. If the source ASIN does not exist in the target marketplace, find the closest leaf category by category-path mapping or by querying with the source product subject phrase.
2. Call `amazon.product_search` for that exact leaf category:
   - query intent: target marketplace, exact leaf category, no subcategories, page size around 50, monthly sales descending
   - request server-side filters for launch date after `2023-01-01` and 30-day sales above `5` when supported
   - map this intent to the provider's actual schema; do not copy provider field names into the Skill logic
   - paginate until 100 valid rows are collected or the category is exhausted
3. Apply hard filters BEFORE deduplication / scoring:
   - normalized `monthly_sales_30d` must be **> 5**. If missing, do not treat it as zero or mark the row as passed unless another compatible source confirms it.
   - normalized `first_available_date` must be **> `2023-01-01`**. If missing or malformed, do not mark the row as passed unless another compatible source confirms it.
   - even after using server-side filters, re-check the returned rows locally before scoring, because missing or stale fields must not pass silently.
   - if filtered rows fall below 100, keep paginating (pages 3, 4, 5...) until 100 valid rows are collected, or the category is exhausted; record the exhaustion reason if fewer than 100 valid rows remain
4. Combine pages into one 100-row review table.
5. Deduplicate by ASIN.
6. Keep the full post-filter process table for human review.
   - The final `竞品相关度过程表` must contain only rows that pass the hard filters above.
   - Do not leave pre-2023 products, zero-sales products, or unverified-date/unverified-sales rows in the final competitor process table as “not adopted” rows.
   - Preserve rejected rows in a separate `竞品剔除记录` sheet with ASIN, title, sales, launch date, score fields, URL, and exact rejection reason.
7. If the source ASIN appears in the 100 rows of any marketplace, mark it with `is_source_asin=true` and exclude it from the final Top-20 competitor set for that marketplace.

Required columns in the 100-row review table:

- ASIN
- title
- main image URL
- product URL
- brand
- price
- 月销量 (`monthly_sales_30d`) — required for the filter and for downstream sales weighting
- 上架时间 (`first_available_date`) — required for the 2023 filter
- rating/reviews when available
- category path
- seller fields when available

### 3. Score competitor relevance

Run:

```bash
python scripts/relevance_estimate.py source.json candidate.json
```

For each row in the 100-row review table, the scoring flow is:

1. Extract the source ASIN main image URL and the candidate ASIN main image URL.
2. Call the user-configured image-matching adapter:
   - pass its path with `--image-match-script` or `IMAGE_MATCH_SCRIPT`;
   - score this candidate image against the source ASIN image;
   - if no adapter is configured, report the missing capability instead of guessing.
3. Call the title relevance script:
   - `scripts/title_relevance.py`
   - score this candidate title against the source ASIN title.
4. Calculate final relevance:
   - `综合相关度 = 主图相关度 * 60% + 标题相关度 * 40%`
5. Write these columns back to the post-filter process table:
   - `综合相关度`
   - `主图相关度`
   - `标题相关度`
   - `近30日销量` / `monthly_sales_30d`
   - `上架时间` / `launch_time` / `available_date`
   - `相关度判断`
   - title-match trace fields when helpful

Column order requirement: in the `竞品相关度过程表`, `近30日销量` and `上架时间` must appear immediately after `标题相关度`. Do not append these two columns at the far right of the sheet; they are part of the core competitor-selection evidence and should stay next to the relevance scores.

Use `score_percent` as `综合相关度`.

Sort the 100 rows by `综合相关度` descending and retain the top `20` non-source ASINs as competitors for listing generation.

If a main image URL or configured image-similarity adapter is unavailable:

- refetch the missing image URL from another allowed source before scoring
- if image-match still cannot be run, mark `score_basis=unscored_image_match_unavailable`
- do not use title-only relevance to select the final top-20 unless the user explicitly approves that degradation
- do not claim that image similarity was used

### 4. Preserve competitor evidence

The final workbook must preserve the post-filter competitor process table for human review.

The `竞品相关度过程表` is the cleaned working table: it must not contain rows that failed the hard sales/date filters. Preserve those rejected rows separately in `竞品剔除记录`, not inside the final competitor process table.

At minimum, include one of:

- a dedicated `竞品相关度过程表` / `Competitor relevance table` sheet, or
- a clearly separated table inside `关键词页`

The retained top-20 competitors must be visibly marked, for example:

- `相关度排名`
- `是否进入Top20`
- `综合相关度`
- `主图相关度`
- `标题相关度`

Also preserve the decision basis used downstream:

- competitor source: source leaf category, marketplace, normalized category id, page number, and sort basis if any
- relevance basis: source/candidate image URLs, image-match score or missing-image reason, title relevance score, final score formula, and reason the ASIN was retained or excluded from top-20

### 4.5. Collect VOC reviews (per target marketplace)

VOC (voice of customer) review evidence is required to drive bullet-point selling points and to surface use scenarios that competitor titles/bullets miss.

For each target marketplace, for each Top-20 retained competitor:

1. Call `amazon.review_search` with the competitor ASIN and the **target marketplace** site ID.
2. Fetch the top 20-100 reviews per competitor (sort by helpfulness or recency; cap at 100 per competitor — do not paginate further).
3. Save the raw review payload locally per marketplace.

Then build a `VOC证据表` sheet for that marketplace, with columns:

- 来源竞对 ASIN
- 评论原文（节选，≤200 字符）
- 评分（星级）
- 评论日期
- 提炼出的卖点 / 使用场景（中文 + 目标语言）
- 类型: 使用场景 / 体验好的点 / 痛点
- 是否与竞对官方卖点重复（是 = 跳过；否 = 候选）
- 是否采纳进 5 点 bullet（是/否 + 哪一个 bullet）

VOC analysis rules:

- prioritize use-scenario phrases and positive-experience points that do NOT appear in any Top-20 competitor's title/bullets
- discard reviews that only restate competitor official selling points (低增量)
- discard 1-2 star reviews unless they reveal a competitor weakness the source ASIN can credibly address (do not invent claims; cross-check against source ASIN facts)
- aggregate similar VOC points (e.g., "great for office desk" + "perfect for my home office" → one scenario "office / home office")
- the goal is 3-8 distinct VOC-derived points per marketplace, fed into the bullet-writing step

The VOC sheet is required output. The bullet-writing step (step 7) must cite VOC sheet rows when it adopts a VOC-derived selling point.

### 5. Expand keywords

Only this step should use Amazon keyword source keyword tools.

Use:

- `amazon.keyword_research` for bulk traffic keyword expansion
- `amazon.traffic_structure` only when competitor structure needs a supplement

Expected scale:

- `100-1000` raw keywords

Save the raw result locally. Keep only summaries in chat.

### 6. Filter and rank keywords

Target remaining count:

- `30-50`

Hard rules:

- keyword relevance estimate `< 60%` means remove
- selected keywords should not have monthly search volume above `10,000`
  - use medium/long-tail keywords first
  - avoid high-competition broad head terms even when the search volume is attractive
  - broad terms may be kept only as diagnostic context, not as retained title/bullet/search-term keywords
- keywords must name the product subject, not only an accessory or part
  - if the product is a honey jar with a spoon, keep phrases like `honigglas mit honiglöffel`, `honigtopf mit löffel`, or `honey jar with spoon`
  - remove accessory-only terms like `honiglöffel` / `spoon` because they attract shoppers looking for the accessory itself
  - keep one-word product nouns only when they are exact product subjects, such as `honigglas` or `honigtopf`

Run:

```bash
python scripts/keyword_relevance_pipeline.py source.json keyword_results.json <asin_total_count>
```

Composite keyword relevance formula (computed by `keyword_relevance_pipeline.py`):

```
综合关键词相关度 = 关键词相关度 × 55%
                + (related_asin_count / asin_total_count) × 100 × 40%
                + 转化率 (purchase_rate, 0-1) × 100 × 5%
```

All three terms are on a 0-100 scale before weighting, so the composite score is also 0-100.

The keyword decision table must expose the raw `related_asin_count` used in this formula as `相关产品数` / `related_asin_count`, plus `相关产品占比` when useful. This field is required for manual review and must not be hidden inside `综合关键词相关度`.

`相关产品数` must come from the normalized `related_asin_count` field. Map provider-specific fields before this step; do not embed provider field names in the scoring logic. Never calculate it from `综合关键词相关度`, infer it from `商品数`, or allow it to exceed the input competitor ASIN count. If the normalized field is missing, mark it `数据源未返回` and rerun or remap the source before manual review.

Keyword ranking order (applied to retained keywords):

1. product-subject precision (subject_match / subject_match_with_accessory ranks before non-subject)
2. composite keyword relevance (descending)
3. purchase conversion rate (descending)
4. monthly search volume (descending)
5. competitor phrase reuse and listing usability

The composite score MUST be carried through to the final keyword decision table as an explicit column. Sort the retained keyword decision table by composite score descending — top scores allocate to title (`T1-T5`), middle scores allocate to bullets (`B1-B5`), tail scores allocate to description (`D1-D5`). Search-term-only keywords sit below the description tail.

## Keyword embedding rules

Create a strict keyword allocation table before writing listing copy.

Minimum allocation positions:

- `T1`, `T2`, `T3`, optional `T4` and `T5`: title phrase positions
- `B1`, `B2`, `B3`, `B4`, `B5`: bullet-specific keyword positions
- `D1`, `D2`, `D3`, optional `D4` and `D5`: description keyword positions
- `Search Terms`: backend search terms

Allocation rules (driven by composite keyword relevance, descending):

- Title: top `1-3`, optionally top `1-5` of the composite-relevance-sorted retained list; prefer product-subject phrases, not accessory-only terms.
- Bullet points: the next `5-20` ranks below title, assigned to specific bullets before writing.
- Description: lower-priority retained phrases (the tail of the sorted list) that still fit naturally; do not pad with diagnostic terms.
- Search terms: top `20` of the remainder after removing phrases already heavily used in title/bullets.
- The composite-relevance score column itself is required in the keyword decision table — every retained row must carry its score so the title/bullet/description allocation can be audited against the sort.
- The allocation table is the source of truth. Do not improvise a different keyword distribution while writing.
- If a keyword is assigned to `T1`, `B1`, `B2`, `D1`, or `Search Terms`, it must appear in that exact assigned field unless marked unusable with a reason.
- Do not split a keyword phrase or reorder its words unless the target marketplace grammar absolutely requires inflection; record the changed surface form when this happens.
- Embed keywords naturally. The sentence must remain fluent, native, and non-mechanical.
- Keep the product subject explicit. Do not bury the main noun behind accessory-only words.

Duplicate control:

- avoid cross-layer reuse when possible
- if keyword inventory is rich, keep near-similar keywords
- the same word should not appear in the title more than twice

Required keyword decision columns:

- keyword
- Chinese meaning
- raw source or Amazon keyword source tool
- metrics available: search results, total sales, related products, monthly search volume, active listings, supply-demand ratio, click concentration, conversion rate, bid/CPC, and competitor repeat count
- **相关产品数 / `related_asin_count`** (required for manual review; this is direct Amazon keyword source data, not the same as `商品数` / active listings and must not be replaced by `商品数` or reverse-calculated from composite score)
- `相关产品占比` = `related_asin_count / asin_total_count` when `asin_total_count` is available; for a 20-competitor keyword expansion, this count must be between `0` and `20`
- keyword relevance estimate (top-5 ASIN average title relevance)
- **composite keyword relevance score** (the explicit 0-100 number from the formula above — required, not optional; the table is sorted by this column descending)
- decision: retained, removed, or diagnostic-only
- retention reason or removal reason
- assigned position: `T1`/`T2`/`T3`/`B1`/`B2`/`B3`/`B4`/`B5`/`D1`/`D2`/`Search Terms`
- embedded field
- embedded sentence or final search-term string
- exact-match status: exact, localized surface form, or not embedded
- character or byte check for the field
- over-limit status

## Listing writing rules

### Hard rule priority (do not violate, in this order)

The listing exists to feed the Amazon ranking algorithm first; readability is a *third-tier* concern. When the three goals conflict, follow this strict order:

1. **关键词原文完整,绝不拆散** — Each retained keyword must appear in the listing as a contiguous token sequence, exactly as it sits in the keyword decision table. Do not insert other words between its tokens, do not reorder its tokens, do not collapse spaces, do not split a multi-word phrase across punctuation, and do not change a hyphen to a space (or vice versa). Example: keyword `honigspender glas` must appear as `Honigspender Glas` / `honigspender glas`, never as `Glas Honigspender` or `Honigspender ... Glas`.
2. **埋词顺序严格按分配表** — `T1` precedes `T2` precedes `T3` in the title; `B1` keyword sits in bullet 1, `B2` in bullet 2, etc.; `D1` precedes `D2` in the description. Do not swap a `T2` keyword into the `T1` slot just because it reads better.
3. **句子通顺(最低优先级)** — Localize copy to be readable, but never at the cost of rules 1 or 2. If grammar would force breaking a keyword phrase, keep the keyword intact and accept slightly stiff phrasing. The only allowed surface variation is *inflection of the trailing token* (e.g. plural/dative ending) when the marketplace grammar absolutely requires it; record the surface form in the allocation table's exact-match column.

Casing is NOT considered a keyword break — Amazon search is case-insensitive, so `honigglas` and `Honigglas` count as the same keyword. Apply correct German noun capitalization in body copy regardless of the keyword's casing in the source data.

Spaces inside a Amazon keyword source-supplied keyword are part of the keyword. `honig glas` and `Honigglas` are *different* surface forms; if the keyword decision table holds `honig glas`, the body must contain `honig glas` (or `Honig Glas` if uppercased), NOT `Honigglas`. The decision is made once at allocation time and never overridden by a stylistic preference.

### Specificity

- listing must be concrete
- title uses centimeters only (UK title may include both cm and inches if marketplace convention requires; default cm-only)
- bullets use both centimeters and inches

### Title selling-point distillation

Before writing any title, distill core selling points from the Top-20 competitors and the VOC sheet for that marketplace:

1. Count selling-point frequency across Top-20 competitor titles (e.g., absorbent / non-scratch / reusable / dishwasher-safe / lint-free).
2. Cross-reference with VOC sheet "体验好的点" rows.
3. Pick the **1-2 highest-priority selling points** that match the source ASIN's true capability (do not invent — verify against source facts). These become required tokens in the title.
4. Record the selling-point choice + evidence (top-N competitor ASINs / VOC sheet rows) in the keyword decision table's "卖点证据来源" column.

### Title casing

Use **Sentence case** for titles in all 6 marketplaces: only the first word is capitalized; the rest stay lowercase, with these exceptions:

- proper nouns (brand names, place names) keep their natural capitalization
- DE: all nouns keep German noun capitalization rule (overrides sentence case for nouns)
- acronyms (e.g., `USB`, `BPA`) stay uppercase
- the brand token, if used, stays in its registered casing

Do NOT use Title Case (every word capitalized). The `locale_lint.py` sentence-case check enforces this per marketplace.

### Title structure

Chinese title:

- reference top competitors
- target `190-200` characters
- order: pack size + 核心卖点(1-2 个，from 卖点提炼步骤) + 精准长尾关键词(T1-T3) + 修饰词(≤3，**不含 size/material/pack**) + 品牌(可选)

Modifier discipline:

- "修饰词" here means descriptive adjectives like "ergonomic", "premium", "lightweight", "easy-clean", "multipurpose"
- size / material / pack-size attribute words are NOT counted as modifiers and have their own dedicated slots — they are mandatory if known
- cap modifiers at 2-3 across the entire title; avoid stacking ("premium ergonomic multipurpose lightweight" → choose 2)
- if a modifier overlaps with a chosen 核心卖点, count it once, not twice

Chinese bullets:

- summarize 5 core selling points from competitors plus source facts
- write Chinese first
- keep the bullet subject explicit so it can be replaced by keywords later

Translation:

- localize into the target marketplace language
- never mechanically translate titles across countries
- build each marketplace title independently from local keyword allocation (the per-marketplace keyword decision table), local marketplace grammar, local unit conventions, and local category phrase order
- replace bullet subject positions with selected keywords according to the per-marketplace allocation table
- process marketplaces independently — do not reuse one marketplace's title/bullet wording in another marketplace, even within the same source ASIN
- the only cross-marketplace shared artifact is the Chinese bridge draft + the source ASIN facts; everything else (competitors, keywords, VOC, bullets, title) is per-marketplace

Target-language title:

- title is not a literal translation of the Chinese, English, or another country title
- target `190-200` characters when the marketplace allows it; never exceed the marketplace cap
- enforces the Title casing rule (Sentence case) for the target language
- carries the 1-2 distilled 核心卖点 tokens identified for that marketplace
- modifier count ≤ 3 (excluding size / material / pack)
- keep the highest-priority `T` keywords in assigned order
- preserve exact keyword phrase order unless local grammar makes it unreadable
- keep the title fluent enough to read as native marketplace copy

Bullet structure:

- do not copy any one competitor's bullet order
- do not reuse the same five selling-point order from a competitor
- synthesize across multiple Top-20 competitors plus source-ASIN facts plus the VOC sheet
- **single selling-point per bullet**: each of the 5 bullets revolves around exactly one core selling point; the five selling points must be five distinct dimensions, no overlap
- recommended 5-dimension framework (adjust to the actual product, never force an irrelevant template):
  1. 材质触感 (material / texture / feel)
  2. 吸水去污 / 核心功能 (core function — varies by category, e.g., absorbency, cleaning power, dispensing precision)
  3. 干湿两用 / 多场景使用 (multi-mode / multi-scenario use)
  4. 可清洗 / 耐用 (washable / durable / reusable)
  5. 数量规格 / 包装内容 (pack size / package contents / set composition)
- each bullet leads with the selling point label in ALL CAPS (e.g., `ABSORBENT MICROFIBER:`, `MULTI-SURFACE USE:`) followed by a colon, then the localized prose
- each bullet must contain its assigned `B` keyword naturally and without splitting the phrase
- write Chinese bullets first, then localize into the target language

Multi-competitor similarity hard rule:

- Each finished bullet must have token Jaccard similarity `< 50%` against every adopted Top-20 competitor's bullets (compare drafted bullet against each competitor's full bullet text — any single competitor pair ≥ 50% fails the rule)
- Run `python scripts/bullet_similarity.py <draft_bullets.json> <top20_bullets.json>` before delivery; exit 1 if any pair ≥ 50%
- If a bullet fails similarity check, rewrite it — pull in VOC scenarios or shift the angle to break the overlap
- The similarity check is per-marketplace and uses that marketplace's Top-20 competitor bullets

VOC integration into bullets:

- at least 1-2 of the 5 bullets must cite a VOC-derived selling point or scenario (recorded in the VOC sheet's "是否采纳" column)
- VOC-derived bullets should fill scenario / use-case dimensions that the competitor official copy under-emphasizes

Description structure:

Write description after title and bullets, using a fixed template. Include product features, notes/cautions or usage method, product parameters, product name, material, dimensions, weight, package contents, and warm tips or usage steps.

Parameter rules:

- source ASIN remains the authority for name, material, dimensions, weight, capacity, pack size, and package contents
- supplement missing critical parameters only from allowed source/detail data
- if a critical parameter is unavailable, write `source data not provided` in the working sheet; do not invent it
- target-language description may use HTML `<p>` paragraph format when appropriate for Amazon upload
- Chinese and target-language descriptions must preserve the same facts

Character checks:

- show actual count, marketplace cap, and over-limit status for title, each bullet, description, and search terms
- use character count or byte count according to the marketplace field requirement

## Output contract

**Six workbooks per source ASIN** — one per target marketplace (UK / DE / IT / FR / ES / NL). If the user restricts to a subset of marketplaces, only output workbooks for that subset.

File name pattern:

- `<ASIN>_<简化中文产品名>_<MARKET>.xlsx`
- example: `B0XXXXXXXX_microfiber-cleaning-cloth_DE.xlsx`, `..._UK.xlsx`, `..._IT.xlsx`, `..._FR.xlsx`, `..._ES.xlsx`, `..._NL.xlsx`
- MARKET code is uppercase 2-letter (UK / DE / IT / FR / ES / NL)

Required sheets (in every workbook):

1. `竞品相关度过程表` or an equivalent 100-row competitor process table inside `关键词页` (the 100 rows for THAT marketplace, after sales/launch-date filter)
2. `关键词页` (per-marketplace keyword decision table)
3. `VOC证据表` (per-marketplace VOC review pool + extracted points)
4. `中文/英文草稿页` or `中文listing页` (Chinese bridge — copy may be reused across the 6 workbooks; English bridge differs per English vs non-English marketplace)
5. `目标站点语言listing页` (final localized listing for that marketplace)

Do not add a product-selection/supply-chain/profit sheet unless the user explicitly asks for it.

Cross-marketplace independence: do NOT generate a "combined" workbook covering all 6 marketplaces in one file. Six separate files is the contract.

## Sheet minimums

`关键词页`:

- retained top-20 competitors (with 月销量 / 上架时间 columns placed immediately after `标题相关度`; all retained rows must have confirmed 月销 > 5 and 上架时间 > 2023-01-01)
- post-filter competitor relevance process table if not placed on a dedicated sheet; rejected rows must be preserved in `竞品剔除记录`
- raw Amazon keyword source keyword appendices
- keyword decision table with retained keywords, removed keywords, removal reason, retention basis, assigned position, embedding evidence, character/byte check, over-limit status, and **卖点证据来源** column linking T1-T3 / B1-B5 to competitor ASIN or VOC sheet row
- title keywords
- bullet keywords
- description keywords
- search term keywords
- competitor keyword repeat/evidence table when available

`VOC证据表`:

- per-marketplace; pulled from `amazon.review_search` against the Top-20 competitor ASINs for that marketplace
- 20-100 reviews per competitor (helpfulness or recency sort), capped per the workflow rule
- columns: 来源竞对 ASIN / 评论原文节选 / 评分 / 评论日期 / 提炼卖点 / 类型 (使用场景 / 体验好的点 / 痛点) / 是否与竞对官方卖点重复 / 是否采纳进 bullet

`中文/英文草稿页` or `中文listing页`:

- Chinese title
- Chinese bullet 1-5
- Chinese description with the required description structure
- optional English bridge draft when useful for target-language localization

`目标站点语言listing页`:

- target-language title, bullet 1-5, description, search terms, and category path
- character counts, character limits, and over-limit status
- final embedded keyword audit for `T1`/`T2`/`T3`, `B1`/`B2`/`B3`/`B4`/`B5`, `D1`/`D2`, and `Search Terms`

## Capability map

Amazon product capabilities:

- `amazon.product_search` for each target marketplace's leaf category competitor table (pages 1+ until 100 filtered rows)
- `amazon.product_detail`
- `amazon.sales_history`
- `amazon.review_search` — REQUIRED per Top-20 competitor per marketplace for the VOC sheet (20-100 reviews each)

Amazon keyword capabilities:

- `amazon.keyword_research`
- `amazon.traffic_structure` only when needed

Image-similarity adapter:

- compare the source ASIN main image URL against each candidate ASIN main image URL
- configure a compatible script with `--image-match-script` or `IMAGE_MATCH_SCRIPT`
- keep that adapter's credential in its own local environment, never in this repository

`scripts/title_relevance.py`:

- compare the source ASIN title against each candidate title
- feeds the 40% title component of competitor relevance

`scripts/bullet_similarity.py`:

- token Jaccard between drafted bullets and Top-20 competitor bullets
- enforces the per-marketplace 50% similarity hard rule before delivery

## Fallbacks

- if one source misses an ASIN, use another compatible source or manual verification and record the change
- if source leaf category is missing, refetch the source ASIN before building competitors
- if a target marketplace's leaf category is missing, map by category path or query by product subject phrase; record the mapping decision
- if the image-similarity adapter is unavailable, stop or ask for explicit approval before using title-only degradation
- if keyword count stays too high, raise the related-ASIN-count threshold
- if keyword count drops too low, relax only the count threshold, not the `<60%` relevance cutoff
- if VOC reviews are unavailable for a competitor (no API response, no reviews on listing), mark that competitor as `voc_unavailable` in the VOC sheet and continue with the remaining competitors; do NOT fabricate review content
- if after pagination the competitor table still cannot reach 100 rows post-filter (small category or sparse verified data), accept the smaller table and record the exhaustion reason; never treat missing sales/date fields as passed, and never lower the `2023-01-01` threshold to pad the count
- if a marketplace consistently fails (e.g., NL category extremely sparse), ask the user before dropping that marketplace from the output
- never reuse or hardcode an unrelated image-match secret
- never relax the source physical fact rule
- never reuse one marketplace's keyword set, VOC analysis, or bullet copy in another marketplace as a shortcut

## Final checklist

Run this checklist **per marketplace workbook** (×6 by default).

Source / inputs:
- source product facts remain unchanged across all 6 workbooks
- target marketplaces explicit (default 6: UK / DE / IT / FR / ES / NL); subset only if user requested

Competitor pool:
- competitor candidate pool comes from THIS marketplace's leaf category via `amazon.product_search` (independent per marketplace)
- competitor table filtered to confirmed `月销量 > 5` AND `上架时间 > 2023-01-01`; rejected rows are preserved in `竞品剔除记录`
- `月销量` and `上架时间` columns present in the competitor process table, immediately after `标题相关度`
- the post-filter competitor relevance process table is preserved for human review
- every scored competitor has `综合相关度`, `主图相关度`, and `标题相关度`
- final competitor set is the top 20 non-source ASINs after sorting by `综合相关度`
- main image URL is present for source and retained competitors, or the missing image reason is recorded
- image-match score is recorded and used in `综合相关度`

VOC:
- VOC sheet exists, populated from `amazon.review_search` against this marketplace's Top-20 (20-100 reviews per competitor)
- VOC sheet categorizes each row as 使用场景 / 体验好的点 / 痛点
- VOC sheet marks 是否与竞对官方卖点重复 + 是否采纳进 bullet
- at least 1-2 bullets cite a VOC-derived selling point

Keywords:
- retained keyword list is `30-50`
- every retained keyword has a retention basis
- every removed keyword has a removal reason
- every retained keyword has an assigned position or a `diagnostic-only` reason
- keyword decision table contains an explicit `综合关键词相关度` / composite score column (formula: relevance×55% + asin_ratio×100×40% + purchase_rate×100×5%) and is sorted by it descending
- keyword decision table has `卖点证据来源` column linking T1-T3 / B1-B5 to competitor ASIN or VOC sheet row
- title embeds the highest-composite-score terms (top of the sorted list)
- bullets embed mid-composite-score terms (the next band)
- description embeds tail-composite-score retained terms (still ≥60% relevance, not diagnostic-only)

Listing copy:
- description follows the required product-features/usage/parameters/package/tips structure
- target-language title is localized for the target marketplace, not mechanically translated; not reused from any other marketplace
- title uses **Sentence case** (only first word capitalized, plus German nouns / proper nouns / acronyms as exceptions)
- title carries the 1-2 distilled 核心卖点 tokens identified for this marketplace
- title modifier count ≤ 3 (excluding size / material / pack)
- each of the 5 bullets revolves around exactly ONE core selling point; the 5 selling points are 5 distinct dimensions
- each bullet leads with an ALL-CAPS selling-point label + colon
- bullet structure is synthesized from multiple competitors + source facts + VOC, not copied from one competitor
- `bullet_similarity.py` reports every drafted bullet has token Jaccard `< 50%` against every Top-20 competitor's bullets
- assigned keywords are embedded in their assigned fields without phrase splitting unless a localized surface form is recorded
- title, bullets, description, and search terms include character/byte counts and over-limit status

Workbook + lint:
- 6 workbooks output (or the user-restricted subset), each named `<ASIN>_<简化产品名>_<MARKET>.xlsx`
- workbook includes the competitor process table, VOC sheet, keyword sheet, Chinese bridge sheet, and target-language listing sheet
- `scripts/locale_lint.py <workbook> --marketplace <code>` runs with zero ERROR-level issues for THAT marketplace; remaining WARN items are reviewed and either fixed or explicitly accepted

---
name: amz-xiyou-select0701
description: Convert Xiyou-style Amazon keyword radar workbooks or keyword pools into openability-ranked product-development shortlists, then run provider-agnostic representative-ASIN rescreening for traffic entrance count, high/mid/low traffic keyword distribution, cliff degree, standard vs non-standard classification, and Excel evidence workbooks. Use when the user asks for 西柚关键词选品, 开品指数, ASIN复筛, 标品/非标品判断, Halloween/seasonal keyword selection, or a data-source-decoupled Amazon selection workflow.
---

# AMZ Xiyou Select 0701

Default language: Chinese. Default marketplace: Amazon US unless the user specifies otherwise.

Use this skill to turn a Xiyou-style keyword workbook into a product-development workbook with:

- keyword semantic openability ranking;
- representative ASIN evidence;
- ASIN traffic-structure rescreening;
- standard / semi-standard / non-standard classification;
- a compact Excel output that the user can audit.

The skill defines the workflow and data contracts. It must not hard-code one MCP, API, website, or provider as the only data path. Use any available live data source, local export, MCP, CLI, workbook, or user-supplied dataset that satisfies the contracts in `references/data-contract.md`.

## When To Load References

- Read `references/data-contract.md` before using any external or local data source.
- Read `references/scoring-rules.md` before assigning `开品指数`, traffic cliff labels, or 标品/非标品 conclusions.

## Core Boundary

Do:

- Preserve the input workbook and create a new output workbook.
- Keep data-source evidence traceable without coupling the skill to the provider.
- Mark fields as `待查` / `数据不足` when required data is unavailable.
- Prefer product forms that are combinable, printable, lightweight-customizable, or easy to turn into 5+ SKU variants.

Do not:

- Invent live marketplace numbers.
- Force ASIN samples when fewer than 3 reliable ASINs are available.
- Treat a provider-specific field name as part of the skill contract.
- Use this workflow for pure listing generation, ad-upload workbook generation, or Amazon ad strategy.

## Workflow

### 1. Normalize Input

Accept one of:

- Xiyou-style workbook with keyword radar columns;
- keyword pool pasted in chat;
- workbook already containing `asin复筛` or similar shortlisted sheet;
- a previously generated openability workbook.

Identify these columns when present:

- `关键词`
- `中文翻译`
- `开品指数`
- `类目相关性`
- `所属类目`
- search/rank/CPC/conversion fields

If Chinese translation is missing or malformed, repair it with concise product-context Chinese. Do not word-for-word translate if the result is awkward.

### 2. Keyword Semantic Openability

For each keyword, classify whether it is worth product development before ASIN research.

Prioritize keywords with:

- clear product shape;
- specific Halloween/seasonal/person/use scene;
- combinable set, kit, bundle, party favor, decor, tag, bag, card, craft, banner, sticker, patch, cup, plate, napkin, box, or similar form;
- easy print / pattern / color / packaging / component variation;
- material compatible with light customization: paper, fabric, felt, canvas, wood, ceramic, glass, resin, sticker, tag, low-cost craft materials.

Downgrade or reject:

- pure apparel size terms unless print-on-demand is explicitly desired;
- cosmetics, fake blood, skin-contact products, weapons, sharp props, or high-compliance products;
- obvious brand/IP/movie/character terms;
- generic broad search-intent terms with weak product form.

Write or update `开品指数` immediately after `中文翻译`, then sort or shortlist by that column if requested.

### 3. Select ASIN Rescreen Scope

Before ASIN lookup, define the exact scope:

- sheet name, e.g. `asin复筛`;
- number of rows, e.g. 前50 / 前100;
- whether to rescreen all rows or only rows above a grade threshold.

If the user changes scope mid-run, honor the newest scope and do not spend live-data calls on rows outside it.

### 4. Get Representative ASINs

Use a data-source adapter that satisfies `keyword_to_representative_asins` in `references/data-contract.md`.

For each keyword:

- target 3-5 representative ASINs;
- prefer natural/search-result relevance over raw top-sales dominance;
- keep title, price, brand, seller, monthly sales, sales share, and source query when available;
- use fallback queries when the exact keyword is too long or sparse:
  - simplified keyword;
  - category English phrase;
  - core product phrase such as `halloween treat bags`, `halloween stickers`, `halloween party games`;
  - provider search by product title when search-result data is unavailable.

Sample rules:

- 5 ASINs: normal.
- 3-4 ASINs: usable with caution.
- 1-2 ASINs: `样本不足`, do not make a strong product-type conclusion.
- 0 ASINs: `待补数据`.

### 5. Reverse ASIN Traffic Structure

For each representative ASIN, use a data-source adapter that satisfies:

- `asin_traffic_summary`;
- `asin_traffic_keywords`.

Required metrics:

- traffic entrance count;
- natural-search keyword count;
- ad keyword count;
- traffic keyword list;
- each keyword's traffic share or comparable contribution score;
- top traffic words.

Compute high/mid/low traffic keyword counts and traffic cliff degree using `references/scoring-rules.md`.

### 6. Classify Standard vs Non-Standard

Classify at the keyword level, not only at the ASIN level:

- `标品`: few dominant words, steep cliff, homogeneous ASIN forms, weak design/component variation.
- `半标品`: recognizable fixed form, but can vary through theme, print, pack count, component mix, color, or packaging.
- `非标品`: many traffic entrances, dispersed traffic, multiple scenes/materials/forms, and strong combination/customization paths.
- `待判断`: insufficient ASIN sample or missing traffic data.

Keep the conclusion explainable in one short sentence: traffic structure + product form + differentiation path.

### 7. Output Workbook

Always output a new `.xlsx` workbook.

Preserve original sheets. Add or update:

- main shortlist / `asin复筛` sheet with compact rescreen columns;
- ASIN detail evidence sheet;
- rules sheet explaining the thresholds and data-source contracts used.

Recommended main-sheet columns:

- `ASIN复筛状态`
- `代表ASIN`
- `ASIN样本数`
- `代表ASIN价格区间`
- `ASIN入口数均值`
- `高/中/低流量词均值`
- `流量断崖程度`
- `标品/非标品`
- `ASIN复筛开品结论`
- `ASIN复筛说明`

Recommended detail-sheet columns:

- `关键词`
- `中文翻译`
- `ASIN`
- `标题`
- `价格`
- `品牌`
- `卖家`
- `月销量`
- `ASIN流量入口数`
- `自然词数`
- `广告词数`
- `高/中/低流量词数`
- `Top1/Top3/Top10流量占比`
- `断崖系数`
- `Top流量词`
- `数据状态`

### 8. Verification

Before final response:

- confirm the output workbook exists;
- inspect the appended columns and detail sheet row count;
- confirm rows outside requested scope were not filled;
- scan for spreadsheet formula errors;
- visually render at least the main added area and detail header area when using spreadsheet tooling.

Final response should be short and include only the output workbook link plus any important caveat such as `3个词样本不足`.

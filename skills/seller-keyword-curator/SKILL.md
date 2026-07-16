---
name: seller-keyword-curator
description: "Expand and filter traffic keywords from up to 20 Amazon competitor ASINs. Use when asked to get curated traffic words, keyword decision tables, retained keywords, or keyword expansion after competitor selection."
---

# Seller Keyword Curator

Expand Amazon traffic keywords from a competitor ASIN list and reduce them to a traceable retained keyword set. This skill is a standalone second-stage workflow: it stops after keyword expansion, filtering, ranking, and allocation-bucket output.

## Standalone Contract

Use this skill by itself when the user already has competitor ASINs and wants selected traffic keywords.

Do not find competitors in this skill. If the user only provides a source ASIN and no competitor list, ask to run `amazon-competitor-finder` first or request a competitor ASIN list.

Do not write final listing copy in this skill. Hand off to `listing-keyword-embedder` only when the user asks to embed the curated keywords into listing fields.

## Inputs

Required:

- marketplace code such as `US`, `UK`, `DE`, `FR`, `IT`, `ES`, `JP`, `CA`, `IN`, `MX`, `BR`, `AU`, or `AE`
- top competitor ASIN list, normally the 20 ASINs from `amazon-competitor-finder`
- `source_profile.json` from `amazon-competitor-finder`, or equivalent source facts

`source_profile.json` must include:

- source ASIN
- title
- product subject terms
- accessory terms when applicable
- source physical facts when available

Optional:

- output directory
- raw keyword JSON if already fetched
- include/exclude keywords
- historical month in `yyyyMM`

## Outputs

Produce these artifacts:

- `raw_keyword_source.json`
- `keyword_relevance_result.json`
- `keyword_decision_table.xlsx` or `.csv`
- `retained_keywords_allocatable.json`

The decision table must include retained and removed rows, not only final keywords.

Required keyword-decision columns:

- `keyword`
- `中文含义` when known or inferred
- `关键词相关度`
- `综合关键词相关度`
- monthly searches
- monthly purchases
- purchase rate
- related ASIN count
- subject alignment
- decision: retained, removed, or diagnostic-only
- retention reason or removal reason
- allocation bucket: title, bullet, description, or search_terms
- raw source/provider tool as the final column

## Workflow

Read [references/data-source.md](references/data-source.md). Start by checking for a configured source with `amazon.keyword_research` and `amazon.traffic_structure` capabilities. If unavailable or quota-blocked, stop and report the actual blocker.

1. Validate inputs.
   - Respect the configured provider's batch limit. If the limit is unknown, start with 20 ASINs or fewer and reduce on error.
   - Split larger lists into supported batches and merge/deduplicate results.
   - If source subject terms are missing, derive a conservative product subject from the source title and ask for confirmation only if the product type is ambiguous.

2. Expand keywords with the configured source.
   - Use the logical `amazon.keyword_research` capability.
   - Query intent: competitor ASINs, marketplace, pagination, time window, and optional filters. Map these to the provider's actual schema at runtime.
   - Save the raw MCP response before filtering.
   - Keep high-volume broad terms as diagnostic context when useful, but do not retain them for listing embedding if they violate the hard filters.

3. Normalize provider data for the pipeline.
   - Build a JSON object with a top-level `keywords` list.
   - Each keyword item should contain: `keyword`, `monthly_searches`, `monthly_purchases`, `purchase_rate`, `related_asin_count`, and `top_asins`.
   - `top_asins` should contain up to five related ASIN payloads with at least title fields, so the relevance script can calculate keyword relevance.

4. Filter and rank keywords.
   - Run `python scripts/keyword_relevance_pipeline.py source_profile.json keyword_results.json <competitor_asin_count>`.
   - Hard remove accessory-only keywords that do not name the product subject.
   - Hard remove selected keywords with monthly searches above `10000`; keep them only as diagnostic context when useful.
   - Hard remove keyword relevance below `60`.
   - Use the script's adaptive related-ASIN threshold to reduce broad or weakly shared words.

5. Preserve the scoring logic.
   - The composite score is:

```text
综合关键词相关度 = 关键词相关度 * 55%
                + (related_asin_count / asin_total_count) * 100 * 40%
                + purchase_rate * 100 * 5%
```

6. Produce allocation-ready keyword output.
   - Sort retained keywords by product-subject precision, composite keyword relevance, purchase rate, monthly search volume, and listing usability.
   - Preserve the script's `allocation_bucket`.
   - Do not invent final `T1/B1/Search Terms` slots here unless the user asks; this skill prepares the keyword pool for the embedding skill.

## Scripts

Bundled scripts:

- `scripts/keyword_relevance_pipeline.py`: filter, score, and bucket keywords.
- `scripts/relevance_estimate.py`: dependency used by the keyword pipeline.
- `scripts/title_relevance.py`: dependency used by relevance scoring.

Use the bundled copies first. They are intentionally duplicated here so this skill can run independently from the original `listing-generator0508` folder.

---
name: listing-keyword-embedder
description: "Embed curated Amazon keywords into localized listing copy and workbook fields. Use when given retained keywords or a keyword decision table and asked to write title, bullets, description, Search Terms, or a final listing workbook."
---

# Listing Keyword Embedder

Embed curated keywords into Amazon listing copy with strict slot allocation, source-fact protection, localization, and field-length validation. This skill is a standalone third-stage workflow: it does not find competitors or expand keywords.

## Standalone Contract

Use this skill by itself when the user already has curated keywords, a keyword decision table, or `retained_keywords_allocatable.json`.

Do not call Amazon keyword source keyword expansion here. Do not rerun competitor discovery here. If required inputs are missing, request the missing artifact or suggest running `amazon-competitor-finder` and `seller-keyword-curator` first.

## Inputs

Required:

- marketplace / target language
- `source_profile.json` or equivalent source-ASIN facts
- retained keyword list or keyword decision table from `seller-keyword-curator`

Optional:

- `top20_competitors.json` for selling-point evidence
- `competitors_100_scored.xlsx/json` for audit sheet reuse
- workbook template path
- target output workbook path
- user's own brand name, if the user wants it included

## Outputs

Produce a final listing workbook or structured listing artifact.

Required workbook sheets when creating `.xlsx`:

- target marketplace listing sheet
- Chinese listing sheet or bilingual draft sheet
- keyword sheet
- competitor relevance process sheet when provided

The keyword sheet must preserve:

- retained keywords
- removed or diagnostic keywords when provided
- explicit slot allocation
- embedding evidence
- exact-match or localized-surface status
- character or byte checks
- over-limit status

## Source-Fact Rules

The source ASIN is the authority for physical product facts. Never change these from competitor data unless the user gives verified replacement data:

- material
- dimensions
- pack size
- color family
- structure and shape
- core function
- target usage form

If a critical fact is missing, write `source data not provided` in the working sheet instead of inventing it.

Do not expose source-ASIN brand, competitor brands, store names, or trademark strings in title, bullets, description, or Search Terms. Only include a brand when the user explicitly provides their own brand name.

## Keyword Allocation

Create or validate a strict allocation table before writing copy.

Minimum slots:

- `T1`, `T2`, `T3`, optional `T4`, `T5`
- `B1`, `B2`, `B3`, `B4`, `B5`
- `D1`, `D2`, optional `D3`, `D4`, `D5`
- `Search Terms`

Default allocation when only buckets exist:

- Title: top 1-5 retained subject keywords by composite score.
- Bullets: next 5-20 retained keywords, assigned to specific bullet functions.
- Description: lower-priority retained keywords that fit naturally.
- Search Terms: top remaining terms after removing phrases already heavily used in title and bullets.

The allocation table is the source of truth. Do not improvise a different keyword distribution while writing.

## Embedding Rules

Hard priority order:

1. Keep every assigned keyword phrase intact as a contiguous token sequence.
2. Keep assigned slot order: `T1` before `T2`, `B1` in bullet 1, `B2` in bullet 2, and so on.
3. Make the sentence fluent and locally natural only after the first two rules are satisfied.

Do not split a keyword phrase, reorder its words, collapse spaces, or change hyphenation unless the target marketplace grammar absolutely requires a localized surface form. Record the changed surface form in the keyword sheet.

Casing does not count as a keyword break. Spaces do count: `honig glas` and `Honigglas` are different surfaces.

## Listing Writing

Write Chinese planning copy first when useful, then localize into the target marketplace language. Do not mechanically translate from another marketplace.

Title:

- Keep the highest-priority `T` keywords in assigned order.
- Target 190-200 characters when the marketplace allows it.
- Use centimeters only when size appears.
- Do not include source or competitor brands.

Bullets:

- Write five distinct selling-point functions based on source facts plus multi-competitor evidence.
- Do not copy any one competitor's five-bullet order.
- Each bullet must contain its assigned `B` keyword naturally and intact.
- Use both centimeters and inches when dimensions appear.

Description:

- Use a structured template.
- Include product features, notes or usage method, product parameters, product name, material, dimensions, weight, package contents, and warm tips or usage steps.
- Preserve the same facts in Chinese and target-language versions.

Search Terms:

- Use remaining high-value terms.
- Avoid repeating words already overused in title and bullets when inventory is rich.
- Check bytes or characters according to the marketplace requirement.

## Validation

Before delivery:

- check title, bullet, description, and Search Terms length
- verify every assigned slot is either embedded or marked unusable with a reason
- verify no competitor/source brand leaked into customer-facing copy
- verify missing source facts are not invented
- for German workbooks, run `python scripts/locale_lint.py <workbook.xlsx>` and fix ERROR-level issues

## Scripts

Bundled script:

- `scripts/locale_lint.py`: locale linting for finished German listing workbooks.

This skill intentionally carries only final-copy validation tooling; competitor and keyword scripts live in the first two skills so this skill remains independently callable at the embedding stage.

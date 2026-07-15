---
name: amz-ad-automation
description: Generate Amazon Sponsored Products bulk-upload XLSX files for SP keyword ads, ASIN product-targeting ads, and automatic ads. Use when the user asks for 亚马逊广告, Amazon ads, SP广告, 关键词广告, ASIN广告, 自动广告, 批量广告, 批量上传表, advertising bulk sheet, or to recommend and confirm S1-S27 ad strategies before filling a Sponsored Products upload workbook.
---

# AMZ Ad Automation

Use this skill to turn user-confirmed Amazon Sponsored Products ad plans into a clean upload-ready XLSX.

## Hard Rules

- Do not choose strategies from date or holiday stage alone. Recommendations must be based on ASIN evidence, available keyword/competitor data, selected ad type(s), and `references/strategy-library.md`.
- The first required gate is only: target `ASIN`, seller `SKU`, `Start Date`, and ad type(s): `sp_keyword`, `asin`, and/or `auto`.
- Strategy numbers are not a first-gate requirement. If missing, analyze the ASIN/context and recommend compatible S1-S27 strategies, then ask whether to use the recommendation or let the user choose.
- If the user already supplied every required field for generation, do not ask again; normalize and generate.
- If information is missing, guide the user in multiple short turns. Ask one decision group at a time after the first gate, and list all valid options every time.
- Treat `B0...` values as ASINs, not seller SKUs. If the SKU looks like an ASIN, ask for the real seller SKU unless the user explicitly confirms it is the seller SKU.
- S22 泛词分层 must use fewer than 50 total keywords. If the source table has 50+ eligible S22 keywords, select the top 49 by confirmed relevance/traffic/rank or ask the user to narrow the pool.
- Generate only the `Sponsored Products Campaigns` sheet using the original 25 template columns.
- Do not add audit columns to the upload workbook.
- Use the bundled script instead of hand-building rows when generating files.

## Workflow

1. First gate: require `ASIN`, seller `SKU`, `Start Date`, and ad type(s). Ask for these together if any are missing.
2. If strategy numbers are missing:
   - Read `references/strategy-library.md`.
   - Inspect available local ASIN reports, keyword tables, competitor ASIN tables, or user-supplied context.
   - Recommend only strategies compatible with the selected ad type(s), with a short reason for each.
   - Ask: use the recommendation, or self-select from the full compatible strategy list.
3. Ask remaining missing inputs one decision group per turn, always listing all valid options:
   - Keyword source for SP keyword ads: local table(s), pasted keywords, or other named file.
   - Competitor ASIN source for S20/S21/S27: local table(s), pasted ASINs, or other named file.
   - Bid source: strategy default, one fixed bid, table PPC/bid column, or explicit per-item bids.
   - Grouping rule: `none`, `rank` for pure ranking, or `root_rank` for root + rank.
   - Match type: `broad`, `exact`, `phrase`, or all strategy-default match types.
   - Top of Search: none, `30`, `50`, `900`, or custom percentage.
   - Bidding strategy: `fixed`, `down_only`, or `up_down`.
4. Before generating, summarize the normalized plan once and proceed if the user already confirmed or gave all required values explicitly.
5. Normalize user input into the JSON shape in `references/input-schema.md`.
6. Run:

```bash
python3 scripts/generate_bulk_xlsx.py input.json --output /path/to/output.xlsx
```

If `python3` cannot import `openpyxl`, use the Codex workspace Python returned by `load_workspace_dependencies`.

7. Inspect the generated workbook enough to confirm row counts, headers, SKU, date, targeting type, match type, and targeting expressions.

## Guided Question Style

Keep prompts concrete and seller-facing. Prefer one compact choice block per turn:

- Missing first gate: ask for `ASIN`, seller `SKU`, `Start Date`, and ad type(s). Ad type options are `sp_keyword` / SP关键词广告, `asin` / ASIN定投广告, and `auto` / 自动广告.
- Missing strategies: show a recommended strategy set first, then show the full compatible options from S1-S27 for the selected ad type(s).
- Missing execution settings: ask only the next needed setting and list all options from the workflow above.

Do not force a multi-turn flow when the user supplied everything in one message.

## Keyword Grouping

Use the confirmed grouping rule:

| Keyword traffic rank | Group size |
|---|---:|
| <= 10,000 | 3 keywords per campaign |
| 10,001-50,000 | 15 keywords per campaign |
| 50,001-150,000 | 20 keywords per campaign |
| > 150,000 | 30 keywords per campaign |

Grouping only controls campaign/ad group splitting. It does not automatically set bid.

## Ad-Type Mapping

- Auto ads: S1, S2, S3.
- SP keyword ads: S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, S22, S23, S24, S25, S26.
- ASIN product-targeting ads: S20, S27.
- S21 must be converted to an ASIN list before generation.

## Template Asset

Use `assets/sponsored_products_bulk_template.xlsx` as the source template. It contains one required worksheet:

`Sponsored Products Campaigns`

Output should remain an XLSX upload version unless the user explicitly asks for another artifact.

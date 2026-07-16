---
name: amz-easy-ad
description: Generate a simplified Amazon Sponsored Products bulk-upload XLSX for SP keyword ads, ASIN product-targeting ads, and automatic ads. Use when the user asks for 简化版亚马逊广告skill, easy Amazon ads, easy SP ads, amz easy ad, 简化广告批量表, or wants the same ad intake requirements without built-in numbered strategies.
---

# AMZ Easy Ad

Use this simplified skill to turn user-confirmed Amazon Sponsored Products ad plans into a clean upload-ready XLSX.

## Hard Rules

- Do not use built-in numbered advertising strategies or recommend preset strategy codes.
- The first required gate is only: target `ASIN`, seller `SKU`, `Start Date`, and ad type(s): `sp_keyword`, `asin`, and/or `auto`.
- If the user already supplied every required field for generation, do not ask again; normalize and generate.
- If information is missing, guide the user in multiple short turns. Ask one decision group at a time after the first gate, and list all valid options every time.
- Treat `B0...` values as ASINs, not seller SKUs. If the SKU looks like an ASIN, ask for the real seller SKU unless the user explicitly confirms it is the seller SKU.
- Generate only the `Sponsored Products Campaigns` sheet using the original 25 template columns.
- Do not add audit columns to the upload workbook.
- Use the bundled script instead of hand-building rows when generating files.

## Workflow

1. First gate: require `ASIN`, seller `SKU`, `Start Date`, and ad type(s). Ask for these together if any are missing.
2. Ask remaining missing inputs one decision group per turn, always listing all valid options:
   - Keyword source for SP keyword ads: local table(s), pasted keywords, or other named file.
   - Competitor ASIN source for ASIN ads: local table(s), pasted ASINs, or other named file.
   - Bid source: one fixed bid, table PPC/bid column, or explicit per-item bids.
   - Grouping rule: `none`, `rank` for pure ranking, or `root_rank` for root + rank.
   - Match type: `broad`, `exact`, `phrase`, or multiple selected match types.
   - Top of Search: none, `30`, `50`, `900`, or custom percentage.
   - Bidding strategy: `fixed`, `down_only`, or `up_down`.
3. Before generating, summarize the normalized plan once and proceed if the user already confirmed or gave all required values explicitly.
4. Normalize user input into the JSON shape in `references/input-schema.md`.
5. Run:

```bash
python3 scripts/generate_bulk_xlsx.py input.json --output /path/to/output.xlsx
```

If `python3` cannot import `openpyxl`, use the Codex workspace Python returned by `load_workspace_dependencies`.

6. Inspect the generated workbook enough to confirm row counts, headers, SKU, date, targeting type, match type, and targeting expressions.

## Guided Question Style

Keep prompts short and seller-facing:

- Missing first gate: ask for `ASIN`, seller `SKU`, `Start Date`, and ad type(s). Ad type options are `sp_keyword` / SP关键词广告, `asin` / ASIN定投广告, and `auto` / 自动广告.
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

- Auto ads: use `ad_type: "auto"` and optional `auto_targets`.
- SP keyword ads: use `ad_type: "sp_keyword"` and `keywords`.
- ASIN product-targeting ads: use `ad_type: "asin"` and `asins`.

## Template Asset

Use `assets/sponsored_products_bulk_template.xlsx` as the source template. It contains one required worksheet:

`Sponsored Products Campaigns`

Output should remain an XLSX upload version unless the user explicitly asks for another artifact.

---
name: amz-strategy-ad
description: Guide Amazon Sponsored Products advertising from strategy selection to upload-ready XLSX generation. Use when the user wants an Amazon ad strategy skill, amz strategy ad, 精品广告策略, 根据新品期/成长期/成熟期和打收录/打排名/拓流量/拓关联/打品牌曝光选择 S1-S27 策略, or wants strategy-guided SP keyword, ASIN product-targeting, and automatic bulk ad tables.
---

# AMZ Strategy Ad

Use this skill to first choose the advertising strategy, then generate a clean Amazon Sponsored Products bulk-upload XLSX using the bundled `amz-easy-ad` generation flow.

## Hard Rules

- Start with the strategy layer unless the user explicitly supplies a confirmed strategy plan and asks to generate directly.
- Ask one decision group at a time. Do not collect execution details before strategy confirmation.
- The first strategy gate is product stage: `新品期`, `成长期`, or `成熟期`.
- The second strategy gate is advertising objective: `打收录`, `打排名`, `拓流量`, `拓关联`, or `打品牌曝光`.
- Use `references/strategy-layer.md` when recommending strategy combinations or translating objectives into S1-S27.
- Recommend only Sponsored Products actions that this skill can generate: SP keyword ads, ASIN product-targeting ads, and automatic ads.
- For `打品牌曝光`, explain that SB/SBV/SD are out of this generator's scope. Translate only the SP-compatible part into brand keywords, related brand keywords, competitor ASINs, or self-ASIN defense.
- Do not let the old holiday Week 1-6 calendar drive recommendations. It can be mentioned only as a seasonal example if the user asks.
- After the user confirms the strategy combination, follow the same normalized generation flow as `amz-easy-ad`.
- If the user already supplied every required field for generation, do not ask again; normalize and generate.
- Treat `B0...` values as ASINs, not seller SKUs. If the SKU looks like an ASIN, ask for the real seller SKU unless the user explicitly confirms it is the seller SKU.
- Generate only the `Sponsored Products Campaigns` sheet using the original 25 template columns.
- Do not add audit columns to the upload workbook.
- Use the bundled script instead of hand-building rows when generating files.

## Workflow

1. Ask product stage:
   - `新品期`
   - `成长期`
   - `成熟期`
2. Ask advertising objective:
   - `打收录`
   - `打排名`
   - `拓流量`
   - `拓关联`
   - `打品牌曝光`
3. Read `references/strategy-layer.md` and produce a strategy proposal. Include:
   - Stage and objective.
   - Budget guidance from the stage/objective matrix.
   - Recommended S1-S27 strategy combination.
   - For each strategy: role, ad type, required material, default match/targeting, default bid/TOS if known, and whether it can be generated now.
   - Any out-of-scope items, especially SB/SBV/SD under `打品牌曝光`.
4. Ask the user to confirm the strategy combination or remove/add strategy codes. Do not generate the workbook before this confirmation.
5. After confirmation, require the execution first gate if missing: target `ASIN`, seller `SKU`, `Start Date`, and ad type(s): `sp_keyword`, `asin`, and/or `auto`.
6. Ask remaining missing execution inputs one decision group per turn, always listing valid options:
   - Keyword source for SP keyword ads: local table(s), pasted keywords, or other named file.
   - Competitor ASIN source for ASIN ads: local table(s), pasted ASINs, or other named file.
   - Bid source: one fixed bid, table PPC/bid column, or explicit per-item bids.
   - Grouping rule: `none`, `rank` for pure ranking, or `root_rank` for root + rank.
   - Match type: `broad`, `exact`, `phrase`, or multiple selected match types.
   - Top of Search: none, `30`, `50`, `900`, or custom percentage.
   - Bidding strategy: `fixed`, `down_only`, or `up_down`.
7. Before generating, summarize the normalized plan once and proceed if the user already confirmed or gave all required values explicitly.
8. Normalize user input into the JSON shape in `references/input-schema.md`.
9. Use ASCII campaign labels that include the strategy code and purpose, for example `S1_AUTO_SHOULU`, `S24_RANK_EXACT`, `S20_ASIN_ASSOC`.
10. Run:

```bash
python3 scripts/generate_bulk_xlsx.py input.json --output /path/to/output.xlsx
```

If `python3` cannot import `openpyxl`, use the Codex workspace Python returned by `load_workspace_dependencies`.

11. Inspect the generated workbook enough to confirm row counts, headers, SKU, date, targeting type, match type, and targeting expressions.

## Guided Question Style

Keep prompts short and seller-facing:

- First ask only: `这条产品现在是新品期、成长期，还是成熟期？`
- Then ask only: `这次广告目的更接近打收录、打排名、拓流量、拓关联，还是打品牌曝光？`
- After strategy proposal, ask: `确认按这些策略生成吗？也可以删掉或增加 S 编号。`
- Missing execution first gate: ask for `ASIN`, seller `SKU`, `Start Date`, and ad type(s). Ad type options are `sp_keyword` / SP关键词广告, `asin` / ASIN定投广告, and `auto` / 自动广告.
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
- For `拓关联`, default to `asins_per_campaign: 10` to match the boutique framework unless the user chooses another grouping size.
- S21 category targeting cannot be directly generated as category targeting. First convert the category into selected ASINs, then generate ASIN product-targeting rows.

## Template Asset

Use `assets/sponsored_products_bulk_template.xlsx` as the source template. It contains one required worksheet:

`Sponsored Products Campaigns`

Output should remain an XLSX upload version unless the user explicitly asks for another artifact.

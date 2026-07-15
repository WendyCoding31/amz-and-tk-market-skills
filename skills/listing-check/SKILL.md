---
name: listing-check
description: "Check and repair AI-generated Amazon listing workbooks produced by local listing-generator skills. Use when the user asks to inspect listing quality, validate a generated listing Excel, check competitor/keyword/listing pages, enforce keyword embedding order, remove brand terms, fix title length/casing, or decide whether to rerun listing-generator for the same ASIN and marketplace."
---

# listing-check

Check an AI-generated Amazon listing workbook in this exact order:

1. competitor page
2. keyword page
3. generated listing page

This skill is a quality gate for local `listing-generator0508` / `listing-generator0514` outputs. It does not replace listing generation. If the competitor quality fails the hard threshold, invoke the local listing-generator skill again for the same ASIN and same marketplace/site, export a new workbook, and stop this check flow.

## Local source of truth

Before checking a workbook, quickly read the current local listing-generator skill that produced it:

- Prefer `../listing-generator0514/SKILL.md` for current EU / multi-marketplace workbooks.
- Use `legacy listing generator documentation` for legacy single-marketplace workbooks. Note: that folder may still declare `name: listing-generator0420`.

Treat `listing-generator0514` as the higher quality contract: per-marketplace competitor mining, 100-row process evidence, image+title relevance, VOC evidence, strict keyword allocation, bullet similarity `< 50%`, and locale lint. Treat 0508/0420 as compatible but older.

Use the helper script first for mechanical workbook facts:

```bash
python3 scripts/listing_check_audit.py <workbook.xlsx> --json
```

Optional flags:

- `--brand <brand>`: scan generated listing copy for extra brand tokens. Repeat for multiple brands.
- `--competitor-bullets-json <path>`: compare generated bullets against Top-20 competitor bullets.
- `--fix-competitors --output <fixed.xlsx>`: delete zero-sale / pre-2023 competitor rows and sort the dedicated competitor sheet by `综合相关度` descending.

## Required inputs

Ask only if the answer cannot be inferred from the workbook path, workbook sheets, or user message:

- generated workbook path
- source ASIN
- target marketplace/site code
- source/competitor brand tokens if not visible in workbook evidence
- competitor bullet evidence if bullet similarity must be computed

Never invent missing source facts, brands, launch dates, sales values, keywords, or competitor bullets. Mark missing evidence as missing and decide from the rules below.

## Step 1: Competitor Page

Find `竞品相关度过程表`, or the equivalent competitor process table embedded inside `关键词页`.

Use `综合相关度` as the final competitor score. If both current order and sorted order are available, judge threshold quality from the correctly sorted Top-20, then fix workbook order if the visible sheet is unsorted.

Hard threshold:

- If Top-1 `综合相关度 < 70`, invoke listing-generator for this same ASIN and same marketplace/site, generate a new Excel workbook, and exit this skill flow.
- If sorted Top-20 `综合相关度 < 40`, invoke listing-generator for this same ASIN and same marketplace/site, generate a new Excel workbook, and exit this skill flow.
- If Top-1 `>= 70` and sorted Top-20 `>= 50`, continue the check.
- If sorted Top-20 is `40-49.99`, stop and report it as a borderline competitor pool. Do not rewrite keywords/listing until the user chooses rerun or accepts the risk.
- If fewer than 20 scored competitors exist, treat it as failing the competitor pool and rerun listing-generator.

Cleanup after the pool passes:

- Delete competitor rows where monthly sales is exactly `0`.
- Delete competitor rows where launch/listing date is before `2023-01-01`.
- Do not treat missing monthly sales or missing launch date as zero or pre-2023. Missing evidence is a separate issue.
- Preserve removed rows in `竞品剔除记录` when the workbook already has that sheet or when doing a substantial repair.
- Sort all remaining competitors by `综合相关度` descending, with the most relevant competitor first.
- Keep `综合相关度`, `主图相关度`, `标题相关度`, monthly sales, launch date, image URL, product URL, and relevance basis visible for audit.
- Re-evaluate the cleaned competitor table after deletion. If fewer than 20 scored competitors remain, or if the cleaned Top-20 falls below the threshold, invoke listing-generator again for the same ASIN/site instead of pretending the cleaned table passed.

If rerunning listing-generator:

1. Preserve the same marketplace/site, source ASIN, and product fact lock.
2. Generate a new workbook path instead of overwriting the old workbook.
3. Return the new workbook path and stop. Do not continue checking the old workbook.

## Step 2: Keyword Page

Find the keyword decision table in `关键词页`. The table should expose at least:

- keyword
- monthly search volume
- assigned position (`T1`/`T2`/`B1`.../`Search Terms`)
- decision / retention reason
- embedded field / embedded sentence
- exact-match status

Apply volume rules only to keywords already assigned to an embedded position:

- If a title-assigned keyword (`T1`-`T5`, or embedded field = title/标题) has monthly search volume from `10,000` to `20,000` inclusive, demote it: remove it from title allocation and place it at the end of `Search Terms`.
- If any embedded keyword in any position has monthly search volume `> 20,000`, delete it from the retained/embedded allocation and move lower keywords up in order.
- Keep a traceable reason such as `removed_monthly_search_over_20000` or `demoted_title_keyword_10000_20000`.
- Do not delete raw Amazon keyword source appendices. Only alter the retained/assigned decision surface.

After any keyword-page change, update the corresponding marketplace listing page:

- Recalibrate title keywords, bullet keywords, and search terms according to the revised keyword-page order.
- Re-embed by the new order. Preserve each keyword phrase as a contiguous token sequence.
- Do not split a keyword phrase, reorder words inside the phrase, or swap assigned positions for readability.
- Recalculate character/byte counts and over-limit status after rewriting content.

## Step 3: Listing Page

Check only the generated target-marketplace listing page, plus the Chinese bridge page when it feeds the target page. Do not spend time on product-selection, supply-chain, profit, ROI, or 1688 sheets.

### Brand cleanup

Generated title, bullets, description, and backend Search Terms must not contain:

- source ASIN brand
- competitor brands
- store names
- trademarked brand strings

If a brand token appears, remove it and rewrite the sentence around the gap. Then recalculate character/byte counts.

### Title rules

- Apply the target marketplace title capitalization rule. For current `listing-generator0514`, default to sentence case: first word uppercase, normal lowercase afterward, with German nouns, proper nouns, and acronyms preserved.
- Title length must be `>= 185` and `< 200` characters when the marketplace cap allows 200.
- If title is `< 185`, expand it to at least 185 characters without splitting embedded keyword phrases or breaking keyword order.
- If title is `>= 200`, compress it below 200 without deleting required title keywords unless the keyword page was revised first.
- The title should highlight only `1-2` core selling points.
- Keep only `2-3` descriptive modifiers across the whole title. Do not count size, material, pack size, or required product facts as modifiers.
- Use source ASIN facts only for material, dimensions, pack count, color, shape, and function.

### Bullet rules

- Each of the 5 bullet points must revolve around exactly one core selling point.
- The 5 bullets should cover distinct dimensions. Do not let the same promise repeat under different wording.
- Do not copy one competitor's bullet order or selling-point structure.
- Bullet similarity against every Top-20 competitor bullet must be `< 50%`. Prefer the local generator script when evidence exists:

```bash
python3 scripts/bullet_similarity.py <draft_bullets.json> <top20_bullets.json>
```

If this script cannot run because competitor bullet evidence is missing, mark the similarity check as unverified and do not claim it passed.

Rewrite bullets using listing-generator rules when:

- similarity is `>= 50%`
- one bullet contains multiple unrelated selling points
- bullets copy a competitor's order
- assigned `B` keywords are missing, split, or out of order
- source facts are invented or borrowed from competitors

## Output

Produce one of these outcomes:

- `rerun`: competitor threshold failed, listing-generator was invoked, a new Excel workbook was generated, and this flow stopped.
- `repaired`: workbook was checked and repaired; provide the repaired workbook path.
- `blocked`: required evidence is missing or Top-20 is borderline; report the exact blocker and do not silently continue.

The final report should be short and auditable:

- workbook path checked
- generator contract used: 0514 or 0508/0420
- competitor threshold result
- rows deleted/sorted on competitor page
- keyword rows demoted/deleted
- listing title length before/after
- brand terms removed
- bullet similarity status
- repaired or regenerated workbook path

## Do Not

- Do not continue keyword/listing checks after the competitor threshold triggers a rerun.
- Do not lower the competitor thresholds to make a workbook pass.
- Do not use title-only relevance as proof that competitor quality passed.
- Do not invent monthly sales, launch dates, brands, source facts, or VOC evidence.
- Do not remove the skill's extra evidence sheets just because the manual template is simpler.
- Do not overwrite the user's original workbook unless explicitly asked.

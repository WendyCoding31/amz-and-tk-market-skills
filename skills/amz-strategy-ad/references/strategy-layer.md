# Strategy Layer for AMZ Strategy Ad

Use this reference after the user confirms product stage and advertising objective. This layer chooses strategy combinations; the generator still only creates Sponsored Products rows.

## Layering

- 精品框架 = why/when/budget: product stage, advertising objective, budget share, monitoring target.
- S1-S27 = executable Sponsored Products strategy library.
- `generate_bulk_xlsx.py` = table generator after strategy confirmation.

## Stage Budget Matrix

| Product stage | 打收录 | 打排名 | 拓流量 | 拓关联 | 打品牌曝光 |
|---|---:|---:|---:|---:|---:|
| 新品期 | 60% | 10% | 30% | 0% | 0% |
| 成长期 | 30% | 15% | 50% | 5% | 0% |
| 成熟期 | 5% | 10% | 60% | 15% | 10% |

If the user chooses an objective with `0%` for the selected stage, do not block them. Warn briefly and suggest the nearest SP-compatible alternative.

## Objective to Strategy Map

| Objective | Main S codes | Optional S codes | Notes |
|---|---|---|---|
| 打收录 | S1, S2, S6, S12 | S3, S13 | Use auto + broad/phrase root coverage to increase indexed and discoverable terms. |
| 打排名 | S4, S18, S24, S26 | S11, S13, S25 | Push known core/high-converting terms. Prefer exact/phrase and controlled budgets. |
| 拓流量 | S22, S23, S17, S19 | S5, S7, S9, S14, S15, S16 | Expand traffic pools through broad/phrase, long tails, recombinations, and retesting. |
| 拓关联 | S20, S27 | S21 | Use competitor ASINs, weaker ASINs, complementary ASINs, and self-ASIN defense. S21 must be converted to ASINs first. |
| 打品牌曝光 | S8, S10 | S20, S27, self-ASIN defense | SP-only translation of brand exposure. SB/SBV/SD are out of scope for this generator. |

## Stage Presets

Use these as starting points. Adjust after seeing user constraints, existing data, and available materials.

| Stage + objective | Recommended combo | Rationale |
|---|---|---|
| 新品期 + 打收录 | S1 + S2 + S6 + S12 | Auto finds terms; SKU泛词 and root phrase coverage create early searchable surface. |
| 新品期 + 打排名 | S18 + S24, add S26 only for low-competition terms | Ranking spend is risky without data; keep it narrow. |
| 新品期 + 拓流量 | S6 + S12 + S15 + S20 | Expand cautiously through broad roots, competitor long tails, and low-bid ASINs. |
| 成长期 + 打收录 | S1 + S3 + S12 + S13 | Keep harvesting and fill missing roots after early data appears. |
| 成长期 + 打排名 | S4 + S11 + S24 + S26 | Move proven words into exact/phrase rank-push campaigns. |
| 成长期 + 拓流量 | S17 + S22 + S19 + S15 | Reuse historical winners and broaden by rank bucket and recombinations. |
| 成长期 + 拓关联 | S20 + S27 | Start competitor and weaker-ASIN targeting with controlled bids. |
| 成熟期 + 打收录 | S3 + S12 | Low-cost maintenance only; do not overfund collection. |
| 成熟期 + 打排名 | S4 + S24 + S25 | Maintain core positions and protect page-one terms. |
| 成熟期 + 拓流量 | S22 + S23 + S17 + S19 | Scale traffic while watching ACOS and organic order share. |
| 成熟期 + 拓关联 | S20 + S27 + self-ASIN defense | Increase product-page traffic and defend own detail-page placements. |
| 成熟期 + 打品牌曝光 | S8 + S10 + S20/S27 self-defense | Translate brand exposure into SP brand keywords and ASIN defense. |

## S1-S27 Execution Reference

| Code | Strategy | Ad type | Default targeting/match | Default bid/TOS | Required material |
|---|---|---|---|---|---|
| S1 | 自动捡漏 | auto | close-match + loose-match | bid 0.05 + TOS 900 | none |
| S2 | 自动固定 | auto | close-match + substitutes | fixed bid 0.25 | none |
| S3 | 自动广告低 Bid 兜底 | auto | all 4 auto targets | down_only bid 0.20 | none |
| S4 | 优质出单词固定竞价 | sp_keyword | exact, optional phrase | user-confirmed fixed bid | order keywords |
| S5 | 出单词捡漏玩法 2 | sp_keyword | broad | bid 0.02 + TOS 900 | order keywords |
| S6 | SKU 泛词 | sp_keyword | broad | bid 0.02 + TOS 900 | generic keywords |
| S7 | 高点击不出单词捡漏 | sp_keyword | broad | bid 0.15 | high-click no-order keywords |
| S8 | 相关品牌 | sp_keyword | broad/phrase | user-confirmed | major brand or category brand keywords |
| S9 | 错词/西语选词法 | sp_keyword | broad/exact | low-bid, user-confirmed | misspellings or Spanish keywords |
| S10 | 品牌法全覆盖 | sp_keyword | broad + phrase + exact | user-confirmed | brand keywords |
| S11 | 高频属性词根捡漏 | sp_keyword | phrase | bid 0.30 | high-frequency attribute roots |
| S12 | 词根全覆盖 | sp_keyword | phrase | bid 0.30-0.60 | attribute roots |
| S13 | 核心前 40 词根捡漏 | sp_keyword | broad/phrase | bid 0.20 starting point | top 40 roots |
| S14 | 属性词 + 大词组合捡漏 | sp_keyword | phrase/exact | below average CPC | attribute words, big words, recombined terms |
| S15 | 竞对长尾 | sp_keyword | broad | grouping by rank, bid confirmed | competitor long-tail keywords with ABA rank |
| S16 | 场景词 + 大词合成词 | sp_keyword | phrase/exact | below average CPC | scenario words, attribute words, big words |
| S17 | 再投放 | sp_keyword | exact/phrase | grouping or user-confirmed | historical order keywords |
| S18 | 大词梯度 | sp_keyword | phrase | bid 0.50 + TOS 50 | core big words |
| S19 | 组合捡漏 | sp_keyword | exact + phrase + broad | bid 0.05 + TOS 900 | core big words |
| S20 | 竞品 ASIN | asin | asin product targeting | bid 0.05-0.10 | competitor ASINs |
| S21 | 类目捡漏 | asin after translation | selected ASINs from category | user-confirmed | category ID or preselected ASINs |
| S22 | 泛词分层 | sp_keyword | broad | grouping by rank, bid confirmed | generic keywords with ABA rank |
| S23 | 泛词冲刺 Broad Rush | sp_keyword | broad | bid 0.50 + TOS 30 | attribute roots |
| S24 | 核心精准大词瀑布 | sp_keyword | exact + exact + phrase | tiered bids | high-competition core words |
| S25 | 核心守位 | sp_keyword | broad/phrase | low maintenance bid | page-one core words |
| S26 | 低竞争高价瀑布 | sp_keyword | SKAG exact | bid +30% | low-competition core words |
| S27 | 精准 ASIN 分层打法 | asin | asin product targeting | user-confirmed | competitor ASINs with BSR/price if possible |

## Proposal Format

When proposing a strategy, use this compact shape:

```text
阶段：新品期
目的：打收录
预算口径：打收录 60%，打排名 10%，拓流量 30%

推荐组合：
S1 自动捡漏：auto，close/loose，默认 0.05 + TOS 900，需要素材：无
S2 自动固定：auto，close/substitutes，默认 0.25，需要素材：无
S6 SKU 泛词：sp_keyword broad，默认 0.02 + TOS 900，需要素材：泛词
S12 词根全覆盖：sp_keyword phrase，默认 0.30-0.60，需要素材：属性词根

确认问题：
确认按 S1/S2/S6/S12 生成吗？也可以删掉或增加 S 编号。
```

After the user confirms, switch to execution intake and generation.

For `拓关联` ASIN campaigns, set `asins_per_campaign: 10` by default to match the boutique framework. If the user asks for fewer campaigns or follows the easy-ad default, 15 per campaign is acceptable after confirmation.

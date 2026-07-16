# Scoring Rules

Use these rules unless the user gives task-specific thresholds.

## Openability Index

Use concise labels that combine grade, action, product form, and reason:

```text
S｜优先开品｜纸质游戏套装｜多零件/可印刷，派对场景清晰
A｜可开品｜派对杯/可印刷｜杯子+吸管+贴纸可套装
B｜观察｜布料配饰｜可印花但偏单品，尺码/同质化需控
C｜不优先｜尺码服装｜偏标品，退换货风险高
```

Grade meanings:

| Grade | Meaning |
|---|---|
| `S` | strong combination/customization path, low development friction |
| `A` | viable but needs ASIN or category validation |
| `B` | possible but risk or differentiation is weaker |
| `C` | not priority due to standardization, compliance, IP, size, or weak product form |

## Semantic Productability

Strong signals:

- 3+ independent components in one set.
- 5+ easy SKU variations through color, print, pattern, pack count, theme, material, packaging, or components.
- Easy process: print, sticker, paper cutting, fabric sewing/cutting, laser-cut wood, decal, hand-paint, low-cost resin/silicone mold.
- Seasonal/scene clarity: party, classroom, trick-or-treat, boo bag, craft, tag, banner, tableware, decor kit.

Weak signals:

- single-size apparel or costume terms;
- skin-contact chemical/cosmetic products;
- IP/brand/media character terms;
- pure generic search phrases;
- one-piece commodity shapes with little print or bundle space.

## Traffic Keyword Tiers

Use ASIN traffic keyword share when available:

| Tier | Rule |
|---|---|
| high traffic word | `traffic_share >= 0.05` |
| mid traffic word | `0.01 <= traffic_share < 0.05` |
| low traffic word | all remaining traffic words |

At ASIN level:

```text
high_count = count(traffic_share >= 0.05)
mid_count = count(0.01 <= traffic_share < 0.05)
low_count = traffic_entrances - high_count - mid_count
```

At keyword level, average the valid representative ASIN metrics.

## Cliff Degree

Compute:

```text
top1_share = first traffic keyword share
top3_share = sum(top 3 traffic keyword shares)
top10_share = sum(top 10 traffic keyword shares)
cliff_ratio = top3_share / max(sum(rank 4-10 shares), 0.001)
```

Label:

| Label | Rule of thumb |
|---|---|
| `高断崖` | `top1_share >= 25%` or `top3_share >= 45%` or `cliff_ratio >= 2.5` |
| `中断崖` | `top1_share >= 12%` or `top3_share >= 28%` or `cliff_ratio >= 1.5` |
| `低断崖` | below the above thresholds |

## Standard / Semi-Standard / Non-Standard

Use both data and product semantics.

`标品`:

- high cliff;
- few meaningful mid-tail traffic words;
- representative ASINs have very similar titles/forms;
- weak bundle/print/component variation path.

`半标品`:

- recognizable fixed product form;
- some cliff or repeated core words;
- can still differentiate through theme, print, color, count, components, packaging, or gift set structure.

`非标品`:

- traffic is dispersed or has many mid-tail words;
- product forms/scenes/materials vary;
- clear combination, design, print, or light-customization paths.

`待判断`:

- fewer than 3 representative ASINs;
- traffic keyword list is missing;
- source data is too weak or mixed.

## Final Rescreen Conclusion

Recommended labels:

| Label | Use when |
|---|---|
| `S｜优先开品` | non-standard or strong semi-standard, clear differentiation, no hard risk |
| `A｜可测试` | semi-standard or moderate cliff, viable but needs narrower SKU plan |
| `B｜谨慎` | weak differentiation, high cliff, or incomplete evidence |
| `C｜谨慎/不建议` | standard product, high-risk category, IP/compliance/size issue |
| `待补样本` | fewer than 3 representative ASINs |
| `待补数据` | no usable ASIN or traffic data |

Each conclusion should include one short reason:

```text
5个ASIN均值：入口1367，高/中/低词≈2.4/11.2/1353；Top3流量23.7%，低断崖；可印刷/批量装，偏非标。
```

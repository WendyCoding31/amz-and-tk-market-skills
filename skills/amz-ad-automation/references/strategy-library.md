# AMZ Sponsored Products 27 个广告策略库

本文档整理自原“广告助手-批量广告-情人节限定版”的 27 个策略，并已改为通用广告策略库。

注意：这里的 S1-S27 是“投放策略”，不是广告类型。真正落表时，只投放三种 Sponsored Products 广告形式：

1. 手动广告 - SP 关键词广告：`broad` / `exact` / `phrase`
2. 手动广告 - ASIN 产品定投广告
3. 自动广告：`close-match` / `loose-match` / `substitutes` / `complements`

## 通用关键词流量分组规则

| 关键词流量排名 | 每组词数 |
|---|---:|
| 1 万以内 | 3 个词一组 |
| 1 万 - 5 万 | 10 - 15 个词一组 |
| 5 万 - 15 万 | 15 - 20 个词一组 |
| 15 万以上 | 30 个词一组 |

执行口径：`50,001-150,000` 统一归入 5 万 - 15 万档；`150,001+` 归入 15 万以上档。

出价 Bid 不由分组规则自动决定，必须按策略建议或用户输入单独确认。

分桶方式：

- A：纯按流量层级分桶
- B：按属性词根 + 流量层级分桶

## 策略总表

| 编号 | 策略名称 | 广告形式 | 匹配/定投方式 | 默认 Bid / TOS | 所需素材 | 监控指标 |
|---|---|---|---|---|---|---|
| S1 | 自动捡漏 | 自动广告 | `close-match` + `loose-match` | Bid `$0.05` + TOS `900%` | 无，自动广告 | CPC `< $0.50` |
| S2 | 自动固定 | 自动广告 | `close-match` + `substitutes` | 固定 Bid `$0.25` | 无，自动广告 | ACOS `< 40%` |
| S3 | 自动广告低 Bid 兜底 | 自动广告 | 4 个自动匹配均可开 | Down Only，Bid `$0.20` | 无，自动广告 | 低成本出单、ACOS |
| S4 | 优质出单词固定竞价 | SP 关键词广告 | `exact` 为主，可加 `phrase` | Fixed Bid，按用户确认 | 优质出单词列表 | CVR、ACOS |
| S5 | 出单词捡漏玩法 2 | SP 关键词广告 | `broad` | Bid `$0.02` + TOS `900%` | 优质出单词列表 | 低价出单、ACOS |
| S6 | SKU 泛词 | SP 关键词广告 | `broad` | Bid `$0.02` + TOS `900%` | SKU 列表、泛词列表 | CTR、CPC |
| S7 | 高点击不出单词捡漏 | SP 关键词广告 | `broad` | Bid `$0.15` | 高点击不出单词列表 | 是否捡漏出单、ACOS |
| S8 | 相关品牌 | SP 关键词广告 | `broad` / `phrase` | 按用户确认 | 大牌词/类目品牌词列表 | CPC、ACOS、转化 |
| S9 | 错词/西语选词法 | SP 关键词广告 | `broad` / `exact` | 低价捡漏，按用户确认 | 错词、西语词列表 | 低价出单、CPC |
| S10 | 品牌法全覆盖 | SP 关键词广告 | `broad` + `phrase` + `exact` | 按用户确认 | 品牌词列表 | 品牌词 ACOS、转化 |
| S11 | 高频属性词根捡漏 | SP 关键词广告 | `phrase` | Bid `$0.30` | 高频属性词根 | CVR、ACOS |
| S12 | 词根全覆盖 | SP 关键词广告 | `phrase` | Bid `$0.30-$0.60` | 属性词根列表 | 词根覆盖率、ACOS |
| S13 | 核心前 40 词根捡漏 | SP 关键词广告 | `broad` / `phrase` | Bid `$0.20` 起测 | 核心前 40 词根 | CVR、ACOS |
| S14 | 属性词 + 大词组合捡漏 | SP 关键词广告 | `phrase` / `exact` | Bid `< 平均 CPC` | 属性词、大词、人造组合词 | CPC、ACOS |
| S15 | 竞对长尾 | SP 关键词广告 | `broad` | 按关键词流量分组；Bid 单独确认 | 竞品长尾词列表，建议带 ABA 排名 | 长尾词出单率 |
| S16 | 场景词 + 大词合成词 | SP 关键词广告 | `phrase` / `exact` | Bid `< 平均 CPC` | 场景词、属性词、大词 | 出单量、ACOS |
| S17 | 再投放 | SP 关键词广告 | `exact` / `phrase` | 按关键词流量分组或用户确认 | 历史出单词列表 | ACOS、复投转化 |
| S18 | 大词梯度 | SP 关键词广告 | `phrase` | Bid `$0.50` + TOS `50%` | 核心大词列表 | 曝光、点击、排名 |
| S19 | 组合捡漏 | SP 关键词广告 | `exact` + `phrase` + `broad` | Bid `$0.05` + TOS `900%` | 核心大词列表 | CPC、ACOS |
| S20 | 竞品 ASIN | ASIN 广告 | Product Targeting，`asin="..."` | Bid `$0.05-$0.10` | 竞品 ASIN 列表 | 关联流量转化 |
| S21 | 类目捡漏 | ASIN 广告转译 | 从类目筛 ASIN 后定投 | 按用户确认 | 类目 ID 或已筛选 ASIN 列表 | ACOS、转化 |
| S22 | 泛词分层 | SP 关键词广告 | `broad` | 按关键词流量分组；Bid 单独确认；总词数 `<50` | 泛词列表 + ABA 排名，最多 49 个关键词 | S22 CVR、ACOS |
| S23 | 泛词冲刺 Broad Rush | SP 关键词广告 | `broad` | Bid `$0.50` + TOS `30%` | 属性词根列表 | S23 ACOS `< 利润率` |
| S24 | 核心精准大词瀑布 | SP 关键词广告 | `exact` + `exact` + `phrase` | 按层级出价 | 核心高竞争大词列表 | 核心词 Top 10 |
| S25 | 核心守位 | SP 关键词广告 | `broad` / `phrase` | 低价维护，按用户确认 | 已上首页核心词列表 | 排名不掉、ACOS |
| S26 | 低竞争高价瀑布 | SP 关键词广告 | SKAG `exact` | Bid `+30%` | 低竞争核心词列表 | 核心词 Top 10、ACOS |
| S27 | 精准 ASIN 分层打法 | ASIN 广告 | Product Targeting，`asin="..."` | 按用户确认 | 竞品 ASIN，建议带 BSR/价格 | CVR、ACOS |

## 按广告形式归类

### 自动广告

| 策略 | 自动匹配方式 | 说明 |
|---|---|---|
| S1 | `close-match` + `loose-match` | 低 Bid + 高 TOS，偏找词和捡漏 |
| S2 | `close-match` + `substitutes` | 固定 Bid，偏稳定测试转化 |
| S3 | `close-match` + `loose-match` + `substitutes` + `complements` | 低 Bid 兜底 |

### SP 关键词广告

| 策略 | 默认匹配方式 | 说明 |
|---|---|---|
| S4 | `exact` / `phrase` | 优质出单词复投 |
| S5 | `broad` | 出单词低价捡漏 |
| S6 | `broad` | SKU 泛词测款 |
| S7 | `broad` | 高点击不出单词降价再跑 |
| S8 | `broad` / `phrase` | 大牌词截流 |
| S9 | `broad` / `exact` | 错词、西语词捡漏 |
| S10 | `broad` / `phrase` / `exact` | 品牌词全覆盖 |
| S11 | `phrase` | 高频属性词根 |
| S12 | `phrase` | 属性词根全覆盖 |
| S13 | `broad` / `phrase` | 核心词根捡漏 |
| S14 | `phrase` / `exact` | 属性词 + 大词组合 |
| S15 | `broad` | 竞对长尾词 |
| S16 | `phrase` / `exact` | 场景词 + 大词合成词 |
| S17 | `exact` / `phrase` | 历史出单词再投放 |
| S18 | `phrase` | 核心大词梯度 |
| S19 | `exact` / `phrase` / `broad` | 大词组合捡漏 |
| S22 | `broad` | 泛词按 ABA 排名分层；总关键词数必须 `<50`，最多 49 个 |
| S23 | `broad` | 泛词冲刺 |
| S24 | `exact` / `phrase` | 核心大词瀑布 |
| S25 | `broad` / `phrase` | 核心词守位 |
| S26 | `exact` | 低竞争词 SKAG 强攻 |

### ASIN 广告

| 策略 | 定投方式 | 说明 |
|---|---|---|
| S20 | `asin="竞品ASIN"` | 竞品 ASIN 低价截流 |
| S27 | `asin="竞品ASIN"` | BSR 比你差的竞品精准定投 |
| S21 | 先从类目转成 ASIN，再 `asin="..."` | v1 不直接生成类目广告，先筛 ASIN 再投 |

## 填表注意事项

1. `SKU` 必须填写卖家后台 seller SKU，不能默认用 ASIN 替代。
2. `Start Date` 使用投广日期，格式为 `YYYYMMDD`。
3. SP 关键词广告写入 `Keyword Text` 和 `Match Type`。
4. ASIN 广告写入 `Product Targeting Expression`，格式为 `asin="B0XXXXXXXX"`。
5. 自动广告写入 `Product Targeting Expression`，值为 `close-match`、`loose-match`、`substitutes`、`complements`。
6. 若加 Top of Search，需要额外生成 `Bidding Adjustment` 行，并填写 `Placement` 与 `Percentage`。
7. 上传版只保留 Amazon 模板原始字段，不增加审核列。

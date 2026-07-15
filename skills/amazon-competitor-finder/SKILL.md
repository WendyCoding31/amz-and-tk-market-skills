---
name: amazon-competitor-finder
description: 亚马逊竞品查找与竞品排序。输入站点和源 ASIN 后，使用用户已配置的 Amazon 数据源拉取同叶子类目候选商品；执行前让用户选择完整 100 条或 Top20 精简模式，并按 60% 主图相关度 + 40% 标题相关度选出 Top20 竞品。
---

# 亚马逊 Top100 竞品查找

这个 Skill 只负责从源 ASIN 找到真正同类的竞品，并输出可复核的排序过程。它不扩展关键词，也不写 Listing。

## 输入

- Amazon 站点/marketplace。
- 源 ASIN。
- 输出模式：`完整 100 条` 或 `Top20 精简`。
- 可选：用户提供的候选商品 CSV/XLSX/JSON。

执行前必须让用户选择模式。完整模式保留候选池、字段映射、相关度分项和盘面分析；精简模式仍然执行相同评分，只缩短交付文件。

## 数据源预检

实时取数前阅读 [references/data-source.md](references/data-source.md)：

1. 检查当前会话可用的 Amazon MCP/连接器。
2. 确认它至少覆盖 `amazon.product_detail` 和 `amazon.product_search`。
3. 记录 provider、站点、查询时间、类目节点、分页口径和字段映射。
4. 如果没有兼容数据源，引导用户配置 MCP，或请求 CSV/XLSX/JSON。
5. 不要求用户在聊天中粘贴 Key，不读取仓库外的凭据文件。

Skill 不绑定固定 server name、tool name、CLI 或供应商。逻辑能力名不是实际 MCP 调用名。

## 工作流

### 1. 锁定源商品事实

查询源 ASIN 的：

- title、brand、main image、product URL。
- leaf category/category path/category id。
- 关键物理属性、变体、价格、评分和评论数。
- 需要时补充近 30 天销量/趋势，但销量不参与产品相关度造假。

如果 Agent 得到的是供应商原始 JSON，可先运行：

```bash
python3 scripts/fetch_listing_payload.py \
  --input provider-output.json \
  --asin B0XXXXXXXX \
  --marketplace US \
  --provider "configured-source" \
  --output source_profile.json
```

这个脚本只做字段标准化，不联网。

### 2. 获取候选池

使用源商品的真实叶子类目查询候选商品。目标是获得 100 条左右的同类目商品；如果数据源分页上限较低，逐页获取并按 ASIN 去重。

排除：

- 源 ASIN 自身。
- 明显不同产品主体。
- 只共享场景词但不是同一商品类型的产品。
- 缺标题且缺主图、无法判断相关度的记录。

候选不足 100 条时如实输出实际数量，不用其他类目凑数。

### 3. 主图相关度

主图相关度占最终分数 60%。优先使用兼容的图像相似度能力；不可用时运行本地启发式脚本，并明确标记为降级估算：

```bash
python3 scripts/relevance_estimate.py \
  --source source_profile.json \
  --candidates candidates.json \
  --output image_relevance.json
```

图像能力失败、URL 失效或缺图时保留失败原因，不能默认给高分。

### 4. 标题相关度

标题相关度占最终分数 40%。运行：

```bash
python3 scripts/title_relevance.py \
  --source source_profile.json \
  --candidates candidates.json \
  --output title_relevance.json
```

标题判断重点：

- 产品主体是否一致。
- 材质、功能、结构和用途是否相近。
- 配件与主体是否被混淆。
- 颜色、尺寸等变体词不能掩盖主体不一致。

### 5. 合并与排序

```text
综合相关度 = 主图相关度 * 60% + 标题相关度 * 40%
```

同分时依次参考：产品主体一致性、标题证据完整度、主图质量、评论与销量证据完整度。销量只能帮助理解盘面，不能把不相关的畅销品抬进 Top20。

### 6. 盘面分析

完整模式至少说明：

- 候选数量与有效评分数量。
- 价格带、评论门槛和品牌/卖家集中度。
- 头部商品与中腰部商品的差异。
- 数据缺口：缺图、缺标题、缺销量、分页不足、来源字段不一致。

## 输出

完整模式：

- `source_profile.json`
- `candidates_raw.json`
- `competitor_relevance_top100.xlsx` 或 CSV
- `top20_competitors.json`
- `market_summary.md`

精简模式：

- `top20_competitors.xlsx` 或 CSV
- `source_profile.json`
- 简短盘面结论

过程表至少包含：ASIN、title、image、price、rating、review count、source category、image score、title score、final score、removal reason、provider 和 query time。

## 边界

- 不编实时销量、评论、BSR 或类目数据。
- 不提交客户 ASIN 清单、账户数据、Key、Cookie 或 MCP 配置。
- 不在此 Skill 中扩词或写 Listing；需要时交给 `seller-keyword-curator` 和 `listing-keyword-embedder`。

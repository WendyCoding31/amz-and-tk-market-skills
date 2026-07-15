---
name: product-chart-get
description: 导入 Amazon 选品数据、生成 AI 复筛输入，并输出完整选品表与复筛通过表。支持任意兼容 MCP 导出的 JSON，不绑定固定 server、CLI 或供应商。
---

# Product Chart Get

## 目标

- 从兼容 Amazon 数据源导入批量商品数据。
- 标准化为本地 JSON，保留数据来源与原始文件。
- 让 AI 完成中文标题、复筛和季节性判断。
- 生成完整选品表与复筛通过表。

## 数据源

运行前阅读 [references/data-source.md](references/data-source.md)。Agent 负责调用当前可用 MCP，并把结果保存为 JSON；`fetch_raw_data.py` 只做字段映射，不联网、不读取 MCP 配置。

所需逻辑能力：

- `amazon.product_search`：批量商品池。
- `amazon.product_detail`：进入 Listing 前的单 ASIN 事实核验。
- `amazon.sales_history`：需要销量和趋势时补充。

如果没有兼容数据源，可以使用用户提供的 CSV/XLSX/JSON。缺失字段标记为空，不用模型知识补实时数字。

## 快速开始

### 1. 取得供应商原始 JSON

使用 Agent 当前已配置的 MCP 查询商品池，将完整响应保存为 `provider-output.json`。记录 provider、站点、查询时间、分页、筛选和排序口径。

### 2. 标准化

```bash
python3 scripts/fetch_raw_data.py \
  --input provider-output.json \
  --date 20260407 \
  --limit 20 \
  --provider "configured-source"
```

输出：

- `data-get-第1页数据.json`：完整标准化数据。
- `mini_products-第1页.json`：供 AI 复筛的精简字段。
- `meta-第1页.json`：来源、日期、数量和原始文件路径。

文件名保留 `data-get` 仅为兼容旧的 Excel 生成脚本，不代表固定服务商。

### 3. AI 复筛

读取 `mini_products-第1页.json`，为每条产品生成：

```json
{
  "SKU_ID": "B0XXXXXXXX",
  "中文标题": "透明桌垫",
  "复筛结论": "通过",
  "复筛备注": "",
  "季节性产品": "否",
  "季节性关键词": "",
  "节日月份": ""
}
```

将数组保存为 `ai_results.json`。不要让标题翻译或语义判断覆盖原始价格、销量、类目和商品标识。

### 4. 生成 Excel

```bash
python3 scripts/generate_excel.py --date 20260407
```

输出：

- `20260407选品.xlsx`
- `20260407选品复筛.xlsx`
- `已排查产品.xlsx`（追加记录）

## 输入契约

标准化器会尝试映射以下常见字段：

| 规范字段 | 可接受输入示例 |
| --- | --- |
| `SKU_ID` | `asin`, `sku_id`, `skuId`, `item_id` |
| `SPU_ID` | `parent_asin`, `spu_id`, `spuId` |
| `英文标题` | `title`, `product_title`, `name` |
| `商品链接` | `product_url`, `url`, `link` |
| `主图链接` | `image_url`, `main_image`, `image` |
| `类目路径` | `category_path`, `category` |
| `售价` | `price`, `sale_price` |
| `SKU月销量` | `sku_sales_30d`, `sales_30d`, `monthly_sales` |

不能确认口径时先补充字段映射，不要把不同时间窗或币种直接合并。

## 与 Listing 的边界

批量选品表不是最终 Listing 事实源。进入 Listing 生成前，应重新查询目标 ASIN 的 `amazon.product_detail` 与必要的销量、评论证据，并运行：

```bash
python3 ../listing-generator0514/scripts/fetch_listing_payload.py \
  --input provider-product.json \
  --asin B0XXXXXXXX \
  --marketplace DE \
  --output source_profile.json
```

## 安全

- 不提交客户货盘、账户导出、MCP 配置、Key、Cookie 或 `.env`。
- 原始数据与 AI 判断分文件保存，便于审计。
- 缺实时数据时输出字段清单，不编销量、BSR、评论或趋势。

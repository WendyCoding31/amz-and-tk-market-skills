# 数据源配置指南

## 为什么要解耦

Skill 的价值应当来自业务 SOP、判断顺序、证据要求和输出结构，而不是某个 MCP 的 server name 或 tool name。不同用户可以使用不同供应商、内部数据库、平台 API 或离线文件，只要能提供完成任务所需的数据能力。

## 运行前检查

当 Skill 需要实时市场数据时，Agent 必须先执行以下步骤：

1. 列出当前会话可用的数据工具或连接器。
2. 判断它们能否覆盖 Skill 声明的能力字段。
3. 如果有多个兼容来源，说明覆盖范围、时间窗口和限制，让用户选择或按证据质量组合使用。
4. 如果没有兼容来源，引导用户配置 MCP，或请求 CSV、XLSX、JSON 文件。
5. 未取得真实数据前，不输出销量、GMV、BSR、评论数、搜索量、CPC、达人转化等实时数字。

## 规范能力字段

下面是逻辑能力名，不是固定 MCP 调用名。

### Amazon

| 能力 | 最低字段 |
| --- | --- |
| `amazon.product_search` | marketplace、query/category、ASIN、title、price、image、category |
| `amazon.product_detail` | ASIN、title、brand、attributes、variants、category、image |
| `amazon.sales_history` | ASIN、date/window、sales、revenue、BSR 或可验证的趋势字段 |
| `amazon.review_search` | ASIN、rating、date、title/body、variant（若有） |
| `amazon.keyword_research` | keyword、search volume/rank、CPC、competition、trend、related ASINs |
| `amazon.traffic_structure` | ASIN、traffic keywords、rank/share、organic/ad signal |

### TikTok Shop

| 能力 | 最低字段 |
| --- | --- |
| `tiktok.product_search` | region、product id、title、price、sales/GMV、shop、category |
| `tiktok.product_detail` | product id、attributes、shop、images、first seen、status |
| `tiktok.sales_history` | product id、date/window、sales、GMV、trend |
| `tiktok.creator_search` | creator id、region、followers、category、sales/GMV signal |
| `tiktok.video_search` | video id、product id、publish time、views、engagement、sales signal |
| `tiktok.review_or_voice` | product id、rating/sentiment、topics、complaints、selling points |
| `tiktok.channel_mix` | product id、product-card/shop/affiliate contribution |

## 字段映射格式

Agent 调用具体 MCP 后，应先建立映射再进入业务判断：

```json
{
  "capability": "amazon.product_search",
  "provider": "user-configured-source",
  "queried_at": "2026-01-01T12:00:00+08:00",
  "marketplace": "US",
  "window": "30d",
  "field_map": {
    "asin": "provider_item_id",
    "title": "provider_title",
    "sales": "provider_sales_30d"
  },
  "missing_fields": []
}
```

不得把供应商字段名直接写成跨供应商通用事实。时间窗口、地区、币种或统计口径不同，也必须明确记录。

## MCP 配置提示模板

当数据源未配置时，Agent 应给出可执行提示，而不是冷报错：

> 这个流程需要实时的 Amazon/TikTok Shop 市场数据。当前会话没有发现覆盖所需字段的 MCP。请先在你的 Agent 客户端配置一个兼容的数据服务，并确认它能返回本 Skill 列出的能力字段；也可以上传 CSV、XLSX 或 JSON，我会先做字段映射再继续。配置完成后重新开始本任务即可。

不要要求用户把 Key 粘贴进聊天或写入仓库。凭据应保存到 Agent/MCP 客户端支持的本地安全配置或环境变量中。

## 降级规则

- 缺实时数据：只输出待验证框架和需要补查的字段。
- 缺单个平台：只做已获得数据的平台，不伪造跨平台结论。
- 缺时间序列：可以描述当前快照，但不能判断增长或下滑。
- 缺销量归因：不能把浏览量、达人数量或评论数直接等同于成交。
- 来源冲突：并列展示来源、时间与口径，不强行合并为一个数字。

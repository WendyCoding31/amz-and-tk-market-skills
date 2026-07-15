# 竞品数据采集指南

## 核心原则

- Agent 使用当前会话中兼容 `amazon.traffic_structure` 的数据工具。
- 逻辑能力名不是固定 MCP tool name；调用前完成字段映射。
- 每拿到一个 ASIN 的结果，立即追加写入 `mcp_results.json`，避免长任务中断后丢失进度。
- 并发量遵守数据源限流；不要假设每个供应商都支持批量 ASIN。

## 规范请求意图

```json
{
  "marketplace": "DE",
  "asins": ["B0XXXXXXXX"],
  "relation": "similar",
  "limit": 10,
  "sort": "purchases_desc"
}
```

Agent 应把这个意图翻译成当前供应商的真实字段。不要把示例字段直接当作 MCP schema。

## mcp_results.json

```json
{
  "B0XXXXXXXX": {
    "traffic_listing": {
      "items": [],
      "evidence": {
        "provider": "user-configured-source",
        "queried_at": "2026-01-01T12:00:00+08:00",
        "field_map": {}
      }
    }
  }
}
```

`traffic_listing` 是现有生成脚本使用的兼容键，不代表某个供应商工具名。

## 执行节奏

1. 从复筛表读取 SKU_ID/SPU_ID。
2. Agent 逐个或按供应商允许的批量调用获取竞品数据。
3. 每完成一批立即更新 `mcp_results.json`。
4. 运行 `collect_competitor_data.py --mode integrate`。
5. 运行 `generate_one_shot.py` 或 `generate_dev_sheets.py` 生成开发表格。

## 禁止事项

- 不把竞品、评论或 1688 数据覆盖成源产品事实。
- 不编造缺失销量、流量或评论字段。
- 不在脚本中读取 MCP Key 或调用固定供应商 endpoint。

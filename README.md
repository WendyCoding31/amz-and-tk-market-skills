# Proboost Market Skills

This repository contains two Codex skills that use `proboost-mcp` for Amazon and TikTok Shop market data.

## Skills

- `product-market-scout`: Analyze whether a product is selling well on Amazon/TikTok Shop and whether it is worth entering.
- `rising-seller-leads`: Find same-category rising Amazon/TikTok Shop sellers or shops worth contacting for factory supplier outreach.

## 中文说明

每个 skill 文件夹内都有 `中文说明.md`，用于给业务使用者快速理解该 skill 的用途、数据源、流程和输出格式。

## Data Source

Both skills require `proboost-mcp` for current Amazon/TikTok Shop data. If the MCP data source is unavailable, the skills instruct Codex not to invent platform metrics.

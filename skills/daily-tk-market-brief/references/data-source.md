# Data source contract

This skill is provider-agnostic. Before querying live marketplace facts, inspect the MCP tools or connectors available in the current agent session and map them to the required capabilities below.

## Setup flow

1. Discover configured marketplace data tools.
2. Confirm region, marketplace, time window, currency, and field coverage.
3. Map provider fields to the capability names used by this skill.
4. Record provider, query time, field mapping, and missing fields in the output.
5. If no compatible source is available, ask the user to configure one or provide CSV, XLSX, or JSON data.

Never ask the user to paste a credential into chat. Never store a credential in this skill folder.

## Capability names

- Amazon: `amazon.product_search`, `amazon.product_detail`, `amazon.sales_history`, `amazon.review_search`, `amazon.keyword_research`, `amazon.traffic_structure`.
- TikTok Shop: `tiktok.product_search`, `tiktok.product_detail`, `tiktok.sales_history`, `tiktok.creator_search`, `tiktok.video_search`, `tiktok.review_or_voice`, `tiktok.channel_mix`.

These are logical capabilities, not literal MCP tool names. Use any configured source that returns enough evidence. When a field is unavailable, mark it `data unavailable`; do not infer live numbers from model knowledge.

## Offline fallback

CSV, XLSX, and JSON are valid data sources when they include the required identifiers, marketplace/region, time window, and metric definitions. Preserve the original file and add a separate normalized mapping layer.

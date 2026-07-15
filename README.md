# Amazon & TikTok Shop Skills

这是一组面向跨境电商真实工作流的 Agent Skills，覆盖 Amazon 与 TikTok Shop 的选品、市场判断、竞品研究、Listing、广告、达人分析、视频脚本和商品视频生成。

仓库保留了原来的 `proboost-market-skills` 名称，但所有市场数据 Skill 均按**数据源可替换**原则整理：业务判断不绑定某个 MCP 服务商，运行前由 Agent 检查当前可用的数据源，并把返回字段映射为统一能力字段。

## 使用原则

1. **真实数据优先**：需要销量、GMV、BSR、评论、关键词、达人或视频数据时，必须使用已配置的数据源，不能让模型猜数字。
2. **先配置，再查询**：如果当前 Agent 没有兼容 MCP，可以先接入 Amazon/TikTok Shop 数据服务，也可以导入 CSV、XLSX 或 JSON。
3. **能力映射，不绑工具名**：Skill 描述需要哪些能力字段，不要求某个固定 server name 或 tool name。
4. **证据与结论分离**：输出应保留查询时间、市场、来源、原始字段和缺失项，方便复核。
5. **凭据只放本机**：API Key、Token、Cookie、客户文件和本机绝对路径不得提交到仓库。

详细配置方法见 [数据源配置指南](./DATA_SOURCE_GUIDE.md)。

## Skill 清单

### 双平台与线索

| Skill | 用途 |
| --- | --- |
| `product-market-scout` | 对比 Amazon 与 TikTok Shop 的需求、竞争、内容热度和进入建议 |
| `rising-seller-leads` | 找同类目、处于上升期的 Amazon/TikTok Shop 卖家与店铺线索 |

### Amazon 选品与开发

| Skill | 用途 |
| --- | --- |
| `amz-product-select0427` | 从关键词、ASIN、类目或约束条件开始做卖家视角选品 |
| `amz-keyword-select0610` | 从种子词或关键词池筛出可开发的精准关键词 |
| `amz-premium-select` | 对关键词、ASIN 和产品想法做高客单、半标品/非标品复筛 |
| `amz-xiyou-select0701` | 对关键词雷达表和代表 ASIN 做开品指数与流量结构复筛 |
| `product-chart-get` | 获取或导入选品数据并生成复筛表 |
| `development-sheet-factory` | 把复筛结果批量生成产品开发表格 |

### Amazon 竞品、关键词与 Listing

| Skill | 用途 |
| --- | --- |
| `amazon-competitor-finder` | 从源 ASIN 找同叶子类目竞品并做图文相关度排序 |
| `seller-keyword-curator` | 从竞品 ASIN 扩展、过滤和分配流量关键词 |
| `listing-keyword-embedder` | 把已筛关键词按位置完整埋入本地化 Listing |
| `listing-generator0514` | 从源 ASIN 到竞品、VOC、关键词、文案和多站点工作簿的完整链路 |
| `listing-check` | 审核并修复 AI 生成的 Listing 工作簿 |

### Amazon 广告

| Skill | 用途 |
| --- | --- |
| `amz-ad-automation` | 根据确认后的 SP 广告方案生成批量上传 XLSX |
| `amz-easy-ad` | 用较少策略层完成 SP 批量表生成 |
| `amz-strategy-ad` | 先选择广告阶段和目标，再生成批量上传表 |

### TikTok Shop 市场与内容

| Skill | 用途 |
| --- | --- |
| `tk-market` | 判断 TikTok Shop 产品、关键词或类目是否值得进入 |
| `tk-influencer-analysis` | 判断产品适合哪些达人，或达人是否匹配某个产品 |
| `tk-video-script` | 用商品、达人、视频和评论证据生成本地化短视频脚本 |
| `daily-tk-proboost` | 生成 TikTok 跨境日报海报；名称为历史兼容，数据源已解耦 |

### 电商视频

| Skill | 用途 |
| --- | --- |
| `amz-image-to-vedeo` | 从商品图生成 Amazon 风格商品短视频 |
| `tk-image-to-vedeo` | 从商品图或商品线索生成 TikTok Shop 风格短视频 |

## 安装

可将单个 Skill 文件夹复制到 Agent 的技能目录，也可以使用支持 GitHub Skill 安装的工具安装指定目录。安装后先阅读该 Skill 的 `SKILL.md`；如果涉及实时市场数据，再阅读其 `references/data-source.md` 或数据契约文档。

示例目录结构：

```text
skills/
  product-market-scout/
    SKILL.md
    agents/openai.yaml
    references/
```

## 数据源配置

数据型 Skill 运行前必须完成以下检查：

1. 识别当前 Agent 已加载的 Amazon、TikTok Shop、关键词或评论数据工具。
2. 按 `DATA_SOURCE_GUIDE.md` 映射为规范能力字段。
3. 记录数据来源、查询时间、地区和时间窗口。
4. 某项能力不可用时明确降级，不使用模型常识补齐实时数字。

可以接入任意满足字段要求的 MCP；也可以由用户提供 CSV、XLSX、JSON 作为离线数据源。仓库不会提交任何真实 Key 或账户配置。

## 安全与脱敏

- 不包含客户订单、ASIN 清单、广告账户数据、私有表格或聊天记录。
- 不包含 `.env`、Token、API Key、Cookie、MCP 配置文件和本机用户名路径。
- 示例 ASIN、SKU、关键词和 URL 仅作格式演示，不能当作实时市场结论。
- 推送前建议运行：

```bash
gitleaks dir . --redact
gitleaks git . --redact
```

## 版本说明

本仓库优先保留当前流程最完整的版本。旧 Listing 生成器副本、SellerSprite 27-pack、SellerSprite 日报与浅层 SEO Skill 未并入本仓库，避免重复和低深度内容干扰主流程。

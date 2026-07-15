---
name: development-sheet-factory
description: 处理选品复筛表,批量生成开发表格
---

# Development Sheet Factory（开发表格工厂）

## 目标

批量生成 SPU 开发表格：
- **输入**：`YYYYMMDD选品复筛.xlsx`（从 product-chart-get 输出）
- **处理**：MCP 获取竞品数据 → 生成 Excel 表格
- **输出**：`YYYYMMDD开发表格/` 目录下若干个 `{SPU}+{产品名}.xlsx` 文件

## 数据源口径

这个 skill 的主职责是生成开发表格和补竞品信息，不负责定义源产品的最终 listing 真相。

统一规则：

1. 竞品列表：使用 `amazon.traffic_structure` 或等价能力，每次按一个 ASIN 采集并保留来源。
2. 单 ASIN 详情：使用 `amazon.product_detail`。
3. 源产品销量与趋势：使用 `amazon.sales_history`。
4. 评论/差评：使用 `amazon.review_search`；失败时留空并说明，不用猜。
5. 1688 等供应链数据只能作为找商输入，不能覆盖 Amazon 源产品事实。
6. 脚本只整合 Agent 已写入本地 JSON 的结果，不假设固定 MCP CLI、server name 或 tool name。

运行前阅读 [references/data-source.md](references/data-source.md)。

如果开发表格流程需要落地到 listing 生成，请先标准化源 ASIN：

```bash
python3 ../listing-generator0514/scripts/fetch_listing_payload.py \
  --input provider-output.json --asin B0CRV4CSNW --marketplace UK --output source.json
```

---

## 快速开始

### 方式一：一键生成（推荐）

AI 逐个调用当前会话里的 `Amazon traffic data capability` 获取竞品数据，每拿到一个就追加到 `mcp_results.json`。全部完成后运行脚本一键生成所有开发表格。

```bash
# 1️⃣ AI 逐个调用 Amazon traffic data capability，增量写入 mcp_results.json
# （AI 在对话中完成，无需手动操作）

# 2️⃣ 一键生成所有开发表格
export WORKSPACE=~/Desktop
python3 scripts/generate_one_shot.py --date 20260328
```

### 方式二：分步执行

```bash
# 1️⃣ AI 调用 MCP 获取竞品数据，输出 mcp_results.json
# （用户与 Claude 对话，无需手动调用）

# 2️⃣ 脚本整合竞品数据
export WORKSPACE=~/Desktop
python3 scripts/collect_competitor_data.py --date 20260328 \
    --mcp-results $WORKSPACE/20260328选品/mcp_results.json

# 3️⃣ 脚本生成开发表格
python3 scripts/generate_dev_sheets.py --date 20260328 \
    --competitor $WORKSPACE/20260328选品/_competitor_data.json
```

### 测试模式（仅生成前 N 个）

```bash
python3 scripts/generate_one_shot.py --date 20260328 --limit 3
```

---

## 输入输出契约

### 输入：YYYYMMDD选品复筛.xlsx

| 列名 | 必需 | 说明 |
|------|------|------|
| `SKU_ID` | ✅ | 原始 ASIN |
| `SPU_ID` | ✅ | 合并变体后的 SPU（文件名用） |
| `中文标题` | ✅ | 产品中文名（6-18字） |
| `商品链接` | ✅ | 产品链接 |
| `主图链接` | ✅ | 主图 URL |
| `售价` | ✅ | 定价（欧元） |
| `类目ID路径` | ✅ | 亚马逊类目 ID 路径 |
| `季节性产品` | ✅ | 是/否 |
| `节日月份` | ✅ | 旺季月份（非季节性则空） |

### 输出：YYYYMMDD开发表格/

```
YYYYMMDD开发表格/
├── B0XXXXXX+产品中文名.xlsx      # 每个 SPU 一个文件
├── B0YYYYYY+另一个产品.xlsx
├── ...
└── _READY.json                    # 完成标志
```

| 文件 | 说明 |
|------|------|
| `{SPU}+{中文标题}.xlsx` | 开发表格（从模板复制生成） |
| `_READY.json` | 完成状态和统计信息 |

---

## 执行流程

### 推荐流程：一键生成

**阶段一：AI 逐个获取竞品数据**

1. AI 读取 `YYYYMMDD选品复筛.xlsx`，提取 SPU 列表
2. AI **逐个**调用当前会话 `Amazon traffic data capability`（每次只传 1 个 ASIN）
3. 每拿到一个结果就**立即追加**到 `mcp_results.json`，实现流式写入
4. 即使中途出错，已写入的数据不丢失

> 如果数据源不能稳定返回每个 ASIN 的归属，就按单 ASIN 查询；只有在供应商明确支持批量且返回结构可区分时才并发或批量。

`mcp_results.json` 推荐结构：

```json
{
  "B0XXXXXX": {
    "traffic_listing": {
      "items": [],
      "data": {}
    }
  }
}
```

补充说明：

- 竞品数据用于市场参考、价格带、差评和视觉相似性分析
- 不允许把竞品材质、尺寸、形状直接回写为源产品事实

**阶段二：一键生成开发表格**

```bash
python3 scripts/generate_one_shot.py --workspace <WORKSPACE> --date <YYYYMMDD>
```

脚本自动完成：读取复筛表 → 下载主图 → 匹配竞品数据 → 生成每个 SPU 的 xlsx → 输出 `_READY.json`

### 分步流程（旧方式，向后兼容）

**阶段一**：同上，AI 逐个获取竞品数据写入 `mcp_results.json`

**阶段二A**：脚本整合竞品数据
```bash
python3 scripts/collect_competitor_data.py --workspace <WORKSPACE> --date <YYYYMMDD> \
    --mcp-results <mcp_results.json>
```

**阶段二B**：脚本生成开发表格
```bash
python3 scripts/generate_dev_sheets.py --workspace <WORKSPACE> --date <YYYYMMDD> \
    --competitor <_competitor_data.json>
```

### 验收

### 第三阶段：验收

- 检查输出文件数 = `_READY.json` 中的 `total_spu`
- 查看执行统计（成功/失败、竞品填充比例）

---

## 表格自动填充规则

### 基础字段（脚本填充）

| 单元格 | 字段 | 数据来源 |
|--------|------|---------|
| C2 | 亚马逊链接 | 复筛表`商品链接` |
| F2 | 主图 | 复筛表`主图链接`（下载 → 嵌入） |
| O2 | 季节性判断 | 复筛表`季节性产品`（是/否） |
| P2 | 季节性月份 | 复筛表`节日月份` |
| B7 | 产品中文名 | 复筛表`中文标题` |
| I7 | 前期定价 | 复筛表`售价` |
| J7 | 后期定价 | 复筛表`售价`（初始值） |
| K7 | FBA 费用 | **Excel 公式**（保留模板，勿覆盖） |

### 竞品字段（MCP + 脚本填充）

| 单元格 | 字段 | 数据来源 | 示例 |
|--------|------|---------|------|
| D2 | 竞品链接1 | `traffic_listing` items[0] | `https://www.amazon.de/dp/{asin}` |
| E2 | 竞品链接2 | `traffic_listing` items[1] | 同上 |
| I2 | 竞品定价区间 | 所有竞品价格范围 | `€9.99 - €39.95` |
| S2 | 市场评分 | 竞品平均评分 | `4.2/5.0` |
| T2 | 差评分析 | 低评论关键词 | `主要问题：质量、尺寸（基于5条差评）` |

### 用户手动填写

| 单元格 | 字段 |
|--------|------|
| D7 | 重量（kg） |
| F7 | 长度（cm） |
| G7 | 宽度（cm） |
| H7 | 高度（cm） |

---

## _READY.json 格式

脚本完成后输出，记录执行结果：

```json
{
  "schema_version": "1.0",
  "date": "20260328",
  "status": "ready",
  "total_spu": 25,
  "generated": 25,
  "failed": 0,
  "generated_at": "2026-03-28 18:30:00",
  "competitor_filled": 23,
  "competitor_skipped": 2,
  "files": [
    {"sku": "B0XXXXXX", "file": "B0XXXXXX+产品中文名.xlsx"},
    ...
  ]
}
```

**字段说明**：
- `total_spu`：输入 SPU 总数
- `generated`：成功生成文件数
- `failed`：失败数
- `competitor_filled`：有竞品数据的 SPU 数
- `competitor_skipped`：无竞品数据的 SPU 数

---

## 补填竞品（开发表格已存在的情况）

若已生成开发表格但未填竞品数据，可单独补填：

```bash
# 批量补填整个目录
python3 scripts/fill_competitor.py \
    YYYYMMDD开发表格 \
    _competitor_data.json
```

> ⚠️ 补填每个文件需额外打开一次，性能不如一次性方案。

---

## 异常处理

| 情况 | 处理方式 |
|------|---------|
| 模板文件不存在 | 报错并输出模板路径，终止 |
| 复筛表缺失必需字段 | 跳过该 SPU，记录日志，继续 |
| 主图下载失败 | F2 写 URL 文本，不中断流程 |
| 主图尺寸过大 | 自动缩放到 F2 单元格，保持宽高比 |
| MCP 返回空结果 | D2/E2/I2/S2/T2 留空，`_READY.json` 记录 skipped |
| K7 公式丢失 | 检查是否从模板复制（禁止新建工作簿） |

---

## 质量检查清单

> 在 `_READY.json` 显示 `status: ready` 后，运行以下检查

- [ ] 输出文件数 = `total_spu`
- [ ] 文件命名格式：`{SPU_ID}+{中文标题}.xlsx`
- [ ] C2（亚马逊链接）：已填写产品链接
- [ ] F2（主图）：已嵌入图片或写 URL，宽高比正确
- [ ] O2/P2（季节性）：已正确填充
- [ ] B7（产品名）：已填写中文标题
- [ ] I7/J7（定价）：已填写数值
- [ ] K7（FBA）：保持 Excel 公式，未被覆盖
- [ ] D2/E2（竞品链接）：格式 `https://www.amazon.de/dp/{asin}` 或空
- [ ] I2（定价范围）：格式 `€xx.xx - €xx.xx` 或空
- [ ] S2（评分）：格式 `x.x/5.0` 或空
- [ ] T2（差评）：中文一句话或空

---

## FBA 费用公式

K7 单元格：保持以下 Excel 公式（从模板复制，勿手动编辑）

```excel
=IF(J7<=11,
  IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=2.5),
    LOOKUP(D7*1000,{0,41,61,81,101,211,461},{1.64,1.66,1.8,1.83,1.86,2.02,2.02}),
    IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=4),2.39,
      IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=6),2.78,
        IF(AND(MAX(F7:H7)<=35,MEDIAN(F7:H7)<=25,MIN(F7:H7)<=12),
          IF(D7*1000<=150,2.78,2.99),"尺寸超标")))),
  IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=2.5),
    LOOKUP(MAX(D7*1000,(F7*G7*H7)/5),{0,21,41,61,81,101,211,461},{2.07,2.11,2.13,2.26,2.28,2.31,2.42,2.42}),
    IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=4),2.78,
      IF(AND(MAX(F7:H7)<=33,MEDIAN(F7:H7)<=23,MIN(F7:H7)<=6),3.16,
        IF(AND(MAX(F7:H7)<=35,MEDIAN(F7:H7)<=25,MIN(F7:H7)<=12),
          LOOKUP(MAX(D7*1000,(F7*G7*H7)/5),{0,151,401,901,1401,1901,3901},{3.12,3.13,3.14,3.15,3.17,4.28,4.28}),
          IF(AND(MAX(F7:H7)<=45,MEDIAN(F7:H7)<=34,MIN(F7:H7)<=26),
            LOOKUP(MAX(D7*1000,(F7*G7*H7)/5),{0,151,401,901,1401,1901,2901,3901,5901,8901,11901},{3.13,3.16,3.18,3.67,3.69,4.29,4.83,4.96,5.77,6.39,6.39}),
            IF(AND(MAX(F7:H7)<=61,MEDIAN(F7:H7)<=46,MIN(F7:H7)<=46),4.3,
              IF(AND(MAX(F7:H7)<=101,MEDIAN(F7:H7)<=60,MIN(F7:H7)<=60),4.33,"超大件"))))))))
```

**计算逻辑**：
- J7 ≤ 11€：按实际重量计费（低价配送）
- J7 > 11€：取实际重与体积重的较大值计费（标准配送）

---

## 脚本参数

### collect_competitor_data.py

```bash
# 🌟 推荐方式：环境变量
export WORKSPACE=~/Desktop
python3 scripts/collect_competitor_data.py --date 20260328 \
    --mcp-results $WORKSPACE/20260328选品/mcp_results.json

# 方式2：新方式（显式指定 workspace）
python3 scripts/collect_competitor_data.py \
    --workspace <WORKSPACE> --date <YYYYMMDD> \
    --mcp-results <mcp_results.json> [--limit N]

# 方式3：旧方式（向后兼容）
python3 scripts/collect_competitor_data.py \
    --mode integrate \
    --source <复筛表.xlsx> \
    --mcp-results <mcp_results.json> \
    --output <输出目录> [--limit N]
```

### generate_dev_sheets.py

```bash
# 🌟 推荐方式：环境变量
export WORKSPACE=~/Desktop
python3 scripts/generate_dev_sheets.py --date 20260328 \
    --competitor $WORKSPACE/20260328选品/_competitor_data.json

# 方式2：新方式（显式指定 workspace）
python3 scripts/generate_dev_sheets.py \
    --workspace <WORKSPACE> --date <YYYYMMDD> \
    --competitor <_competitor_data.json> [--limit N]

# 方式3：旧方式（向后兼容）
python3 scripts/generate_dev_sheets.py \
    <复筛表.xlsx> <YYYYMMDD> \
    --competitor <_competitor_data.json> [--limit N]
```

**参数说明**：

| 参数 / 环境变量 | 说明 |
|---------------|------|
| `$WORKSPACE` | 环境变量，workspace 目录。未设置默认 `~/Desktop` |
| `--workspace` | 显式指定 workspace 目录（覆盖环境变量） |
| `--date` | 数据日期 YYYYMMDD（必需） |
| `--limit N` | 仅处理前 N 个 SKU（测试模式） |
| `--competitor` | 竞品数据 JSON 路径 |
| `--spu` | 指定 SPU 列表（增量生成，逗号分隔） |

---

## 依赖

```bash
pip3 install openpyxl Pillow
```

| 库 | 用途 |
|----|----|
| `openpyxl` | Excel 读写 |
| `Pillow` | 图片嵌入 |

---

## 典型工作流

假设已有 `20260328选品/20260328选品复筛.xlsx`

```bash
# 一次性设置 workspace（推荐）
export WORKSPACE=~/Desktop

# Step 1: AI 逐个调用 Amazon traffic data capability，增量写入 mcp_results.json
# （AI 在对话中逐个调用 MCP，每拿到结果就追加到 JSON 文件）

# Step 2: 一键生成所有开发表格
python3 scripts/generate_one_shot.py --date 20260328

# Step 3: 检查输出
ls -la $WORKSPACE/20260328选品/20260328开发表格/
cat $WORKSPACE/20260328选品/20260328开发表格/_READY.json | python3 -m json.tool
```

---

## 常见问题

**Q: 能只生成指定的几个 SPU 吗？**
A: 可以。用 `--spu B09L58CD4C,B0D3V9142Q` 指定 SPU 列表（逗号分隔）。

**Q: 如果主图下载失败会怎样？**
A: F2 单元格写入 URL 文本，不中断流程。用户可后期手动下载替换。

**Q: K7 公式丢失了怎么办？**
A: 检查脚本是否正确从模板复制（禁止从零新建工作簿）。若丢失，从 `assets/开发模版.xlsx` 复制正确公式。

**Q: 能一次性传多个产品给 traffic_listing 吗？**
A: 不能。必须单个产品调用。如需提速，用并发（ThreadPoolExecutor）而不是批量调用。

**Q: 并发调用会不会频繁超时？**
A: 建议从 5-8 个并发开始。如果频繁超时，降低到 3-5 个。可根据接口稳定性动态调整。加上重试机制（max_retries=3）会更稳定。

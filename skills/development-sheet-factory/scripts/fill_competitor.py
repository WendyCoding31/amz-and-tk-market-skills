#!/usr/bin/env python3
"""
竞品数据补填脚本 —— development-sheet-factory 独立工具
========================================================
⚠️  注意：推荐优先使用 generate_dev_sheets.py --competitor 参数一次性完成生成，
    每个 Excel 只打开一次，性能更好。

    本脚本适用于已存在开发表格、需要单独补充竞品数据的场景
    （例如：之前只跑了基础字段，事后补填竞品）。

用法:
  批量模式: python3 fill_competitor.py <开发表格目录> <竞品数据.json>
  单个模式: python3 fill_competitor.py <开发表格目录> --spu <SPU_ID> --items '<JSON>'

竞品数据 JSON 格式:
  {
    "B0XXXXXX": {
      "traffic_listing": {"items": [...], "data": {...}}
    }
  }
"""

import sys
import os
import json
import re
import glob
from datetime import datetime

try:
    import openpyxl
except ImportError:
    print("❌ 缺少依赖: openpyxl。请运行: pip3 install openpyxl")
    sys.exit(1)


# ── 竞品数据解析 ──────────────────────────────────────────────────────────────

def parse_competitor_data(data: dict) -> dict:
    """
    从 traffic_listing 竞品数据结构中提取 D2/E2/I2/S2/T2 所需数据。

    参数:
        data: {
            "traffic_listing": {"items": [...], "data": {...}}
        }

    返回:
        {
            "link1": "https://www.amazon.de/dp/B0XXXXXX",  # D2
            "link2": "https://www.amazon.de/dp/B0YYYYYY",  # E2
            "price_range": "€12.99 - €25.99",              # I2
            "avg_rating": "4.4/5.0",                       # S2
            "rating_summary": "整体口碑良好..."              # T2
        }
    """
    if not data:
        return {}
    
    items = data.get('traffic_listing', {}).get('items', [])
    if not items:
        return {}

    # 取前3个有效竞品
    valid = [it for it in items if it.get('asin')][:3]
    if not valid:
        return {}

    result = {}

    # D2 / E2：竞品链接
    base_url = "https://www.amazon.de/dp/"
    if len(valid) >= 1:
        result['link1'] = base_url + valid[0]['asin']
    if len(valid) >= 2:
        result['link2'] = base_url + valid[1]['asin']

    # I2：定价区间（基于所有竞品）
    all_items = [it for it in items if it.get('price')]
    if all_items:
        prices = [it.get('price') for it in all_items]
        lo, hi = min(prices), max(prices)
        if abs(hi - lo) < 0.01:
            result['price_range'] = f"€{lo:.2f}"
        else:
            result['price_range'] = f"€{lo:.2f} - €{hi:.2f}"

    # S2：市场评分（基于所有竞品的平均值）
    all_ratings = [it.get('rating') for it in items if it.get('rating')]
    if all_ratings:
        avg = round(sum(all_ratings) / len(all_ratings), 1)
        result['avg_rating'] = f"{avg}/5.0"

        # T2：评分描述
        low_count = sum(1 for r in all_ratings if r < 4.0)
        n = len(all_ratings)
        if low_count == 0:
            result['rating_summary'] = f"基于{n}个竞品，均分{avg}，整体口碑良好"
        else:
            result['rating_summary'] = f"基于{n}个竞品，均分{avg}，{low_count}个评分偏低"

    return result


# ── Excel 写入 ────────────────────────────────────────────────────────────────

def fill_excel(excel_path: str, competitor: dict) -> bool:
    """
    将竞品数据写入 Excel 文件的指定单元格。

    单元格映射:
        D2 ← competitor['link1']
        E2 ← competitor['link2']
        I2 ← competitor['price_range']
        S2 ← competitor['avg_rating']
        T2 ← competitor['rating_summary']
    """
    if not competitor:
        print(f"    ⚠️  无竞品数据，跳过写入")
        return False

    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    field_map = {
        'D2': competitor.get('link1', ''),
        'E2': competitor.get('link2', ''),
        'I2': competitor.get('price_range', ''),
        'S2': competitor.get('avg_rating', ''),
        'T2': competitor.get('rating_summary', ''),
    }

    written = []
    for cell, value in field_map.items():
        if value:
            ws[cell] = value
            written.append(cell)

    wb.save(excel_path)
    return bool(written)


# ── 主流程 ────────────────────────────────────────────────────────────────────

def load_ready_json(dev_dir: str) -> dict:
    ready_path = os.path.join(dev_dir, '_READY.json')
    if not os.path.exists(ready_path):
        print(f"❌ 找不到 _READY.json: {ready_path}")
        sys.exit(1)
    with open(ready_path, encoding='utf-8') as f:
        return json.load(f)


def save_ready_json(dev_dir: str, data: dict):
    ready_path = os.path.join(dev_dir, '_READY.json')
    with open(ready_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_excel_by_spu(dev_dir: str, spu_id: str) -> str | None:
    """在开发表格目录中根据 SPU_ID 前缀查找对应 Excel 文件"""
    pattern = os.path.join(dev_dir, f"{spu_id}+*.xlsx")
    matches = glob.glob(pattern)
    if matches:
        return matches[0]
    # 兼容：文件名中 SPU_ID 可能被截断
    for f in glob.glob(os.path.join(dev_dir, "*.xlsx")):
        if os.path.basename(f).startswith(spu_id[:10]):
            return f
    return None


def batch_fill(dev_dir: str, competitor_json_path: str):
    """
    批量模式：读取 AI agent 生成的竞品数据 JSON，批量写入所有 Excel。

    competitor_json 格式:
    {
      "B0XXXXXX": {
        "traffic_listing": {"items": [...], "data": {...}}
      },
      ...
    }
    """
    ready = load_ready_json(dev_dir)

    with open(competitor_json_path, encoding='utf-8') as f:
        all_data = json.load(f)

    success, skipped, failed = 0, 0, 0
    results = []

    files = ready.get('files', [])
    if not files:
        # 兼容旧格式（只有 total_spu，无 files 列表）
        xlsx_list = glob.glob(os.path.join(dev_dir, "*.xlsx"))
        files = [{"sku": os.path.basename(p).split('+')[0], "file": os.path.basename(p)}
                 for p in xlsx_list]

    total = len(files)
    print(f"📋 共 {total} 个 SPU 待处理\n")

    for i, entry in enumerate(files, 1):
        spu = entry.get('sku', '')
        fname = entry.get('file', '')
        excel_path = os.path.join(dev_dir, fname) if fname else find_excel_by_spu(dev_dir, spu)

        print(f"  [{i:02d}/{total}] {spu}")

        if not excel_path or not os.path.exists(excel_path):
            print(f"    ❌ 找不到 Excel 文件")
            failed += 1
            results.append({"spu": spu, "status": "failed", "reason": "file_not_found"})
            continue

        data = all_data.get(spu, {})
        # 兼容新旧格式
        if isinstance(data, dict) and 'traffic_listing' in data:
            # traffic_listing 格式
            competitor = parse_competitor_data(data)
        else:
            # 旧格式（直接是items列表）
            items = data.get('items', []) if isinstance(data, dict) else []
            competitor = parse_competitor_data({'traffic_listing': {'items': items, 'data': {}}})
        
        if not competitor.get('link1'):
            print(f"    ⚠️  无竞品数据")
            skipped += 1
            results.append({"spu": spu, "status": "skipped", "reason": "no_competitor_data"})
            continue
        ok = fill_excel(excel_path, competitor)

        if ok:
            print(f"    ✅ D2/E2/I2/S2/T2 已写入 ({', '.join(k for k,v in competitor.items() if v)})")
            success += 1
            results.append({"spu": spu, "status": "ok", "competitor": competitor})
        else:
            print(f"    ⚠️  写入失败（数据解析为空）")
            skipped += 1
            results.append({"spu": spu, "status": "skipped", "reason": "empty_parse"})

    # 更新 _READY.json
    ready['competitor_filled'] = success
    ready['competitor_skipped'] = skipped
    ready['competitor_failed'] = failed
    ready['competitor_filled_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ready['competitor_source'] = 'amazon_traffic_structure'
    ready['competitor_results'] = results
    save_ready_json(dev_dir, ready)

    print(f"\n{'='*50}")
    print(f"✅ 竞品数据填写完成")
    print(f"   成功: {success}  跳过: {skipped}  失败: {failed}")
    print(f"📄 _READY.json 已更新")


def single_fill(dev_dir: str, spu_id: str, items_json: str):
    """
    单个模式：填写单个 SPU 的竞品数据（供 AI agent 逐个调用）

    items_json: traffic_listing 格式 {"traffic_listing": {...}} 或旧格式 items 数组（JSON 字符串）
    """
    data = json.loads(items_json)
    excel_path = find_excel_by_spu(dev_dir, spu_id)

    if not excel_path:
        print(f"❌ 找不到 {spu_id} 对应的 Excel 文件")
        return False

    # 兼容新旧格式
    if isinstance(data, dict) and 'traffic_listing' in data:
        competitor = parse_competitor_data(data)
    else:
        # 旧格式：直接是 items 列表
        items = data if isinstance(data, list) else data.get('items', [])
        competitor = parse_competitor_data({'traffic_listing': {'items': items, 'data': {}}})
    ok = fill_excel(excel_path, competitor)

    if ok:
        print(f"✅ {spu_id}: D2/E2/I2/S2/T2 写入成功")
        for k, v in competitor.items():
            if v:
                cell = {'link1': 'D2', 'link2': 'E2', 'price_range': 'I2',
                        'avg_rating': 'S2', 'rating_summary': 'T2'}[k]
                print(f"   {cell}: {v}")
    else:
        print(f"⚠️  {spu_id}: 无有效竞品数据，跳过")

    return ok


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  批量模式: python3 fill_competitor.py <开发表格目录> <竞品数据.json>")
        print("  单个模式: python3 fill_competitor.py <开发表格目录> --spu <SPU_ID> --items '<JSON>'")
        sys.exit(1)

    dev_dir = sys.argv[1]
    if not os.path.isdir(dev_dir):
        print(f"❌ 目录不存在: {dev_dir}")
        sys.exit(1)

    # 解析参数
    if len(sys.argv) >= 3 and not sys.argv[2].startswith('--'):
        # 批量模式
        batch_fill(dev_dir, sys.argv[2])
    elif '--spu' in sys.argv:
        # 单个模式
        spu_idx = sys.argv.index('--spu') + 1
        items_idx = sys.argv.index('--items') + 1 if '--items' in sys.argv else None
        spu_id = sys.argv[spu_idx]
        items_json = sys.argv[items_idx] if items_idx else '[]'
        single_fill(dev_dir, spu_id, items_json)
    else:
        print("❌ 参数错误，请查看用法说明")
        sys.exit(1)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Bullet 多竞品相似度检查器。

硬规则：每条 drafted bullet 与任何一个 Top-20 竞对的任一 bullet 之间，
        token Jaccard 相似度必须 < 50%。

输入:
  - draft: 一个 JSON，结构 { "marketplace": "DE", "bullets": ["B1 文本", ..., "B5 文本"] }
  - top20: 一个 JSON，结构 { "marketplace": "DE",
                              "competitors": [
                                  { "asin": "B0...", "bullets": ["...", "..."] },
                                  ...
                              ] }

用法:
  python bullet_similarity.py <draft.json> <top20.json> [--threshold 0.5]

退出码:
  0 = 所有 bullet 都 < threshold（默认 0.5）
  1 = 至少一对 ≥ threshold —— 需要重写

输出: 表格 + 失败明细 + 汇总。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 多语言通用 tokenizer：抽取 unicode 字母/数字 token，统一小写。
# 不分词中文（CJK 不在 Top-20 marketplace 里），不剔除停用词
# —— bullet 相似度衡量的是"措辞撞车"，停用词重复也算撞车。
_TOKEN = re.compile(r"\w+", flags=re.UNICODE)


def tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return {t for t in (m.group(0).lower() for m in _TOKEN.finditer(text)) if t}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def check(draft: dict, top20: dict, threshold: float) -> tuple[list[dict], int]:
    bullets = draft.get("bullets") or []
    competitors = top20.get("competitors") or []
    rows: list[dict] = []
    fails = 0
    for i, bullet in enumerate(bullets, start=1):
        b_tokens = tokenize(bullet)
        worst_score = 0.0
        worst_asin = ""
        worst_idx = -1
        for comp in competitors:
            asin = comp.get("asin", "?")
            for j, cbullet in enumerate(comp.get("bullets") or [], start=1):
                score = jaccard(b_tokens, tokenize(cbullet))
                if score > worst_score:
                    worst_score = score
                    worst_asin = asin
                    worst_idx = j
        passed = worst_score < threshold
        if not passed:
            fails += 1
        rows.append({
            "bullet_idx": i,
            "worst_competitor_asin": worst_asin,
            "worst_competitor_bullet_idx": worst_idx,
            "worst_jaccard": round(worst_score, 4),
            "pass": passed,
        })
    return rows, fails


def render(rows: list[dict], threshold: float, marketplace: str | None) -> str:
    lines = []
    header = f"[bullet_similarity] marketplace={marketplace or '?'} threshold={threshold}"
    lines.append(header)
    lines.append("-" * len(header))
    lines.append(f"{'B#':<4} {'最像竞对':<16} {'其B#':<6} {'Jaccard':<10} {'判定':<6}")
    for r in rows:
        lines.append(
            f"{r['bullet_idx']:<4} "
            f"{r['worst_competitor_asin']:<16} "
            f"{r['worst_competitor_bullet_idx']:<6} "
            f"{r['worst_jaccard']:<10} "
            f"{'PASS' if r['pass'] else 'FAIL':<6}"
        )
    fails = sum(1 for r in rows if not r["pass"])
    lines.append("")
    lines.append(f"汇总: {len(rows)} 条 bullet, {fails} 条不通过 (≥ {threshold})")
    if fails:
        lines.append("→ 不通过的 bullet 必须重写，引入 VOC 场景或换角度打破撞车。")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Bullet 多竞品相似度硬规则检查器")
    parser.add_argument("draft", help="drafted bullets JSON 路径")
    parser.add_argument("top20", help="Top-20 竞品 bullets JSON 路径")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="Jaccard 阈值，默认 0.5；任一对 ≥ 阈值即失败")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    top20_path = Path(args.top20)
    if not draft_path.exists():
        print(f"找不到文件: {draft_path}", file=sys.stderr)
        return 2
    if not top20_path.exists():
        print(f"找不到文件: {top20_path}", file=sys.stderr)
        return 2

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    top20 = json.loads(top20_path.read_text(encoding="utf-8"))
    rows, fails = check(draft, top20, args.threshold)
    print(render(rows, args.threshold, draft.get("marketplace") or top20.get("marketplace")))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

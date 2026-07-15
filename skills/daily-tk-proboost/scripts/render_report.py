#!/usr/bin/env python3
"""Render a provider-agnostic, user-branded TikTok Shop daily report PNG."""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import sys
import textwrap
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


WIDTH = 1080
MIN_RATIO = 2.22
BLUE = (17, 76, 255)
CYAN = (0, 197, 224)
DARK = (35, 44, 62)
MUTED = (96, 111, 132)
PAPER = (250, 252, 255)
FOOTER = (222, 237, 255)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int | None = None,
) -> list[str]:
    lines: list[str] = []
    for raw in str(text).replace("\r", "").split("\n"):
        raw = raw.strip()
        if not raw:
            lines.append("")
            continue
        current = ""
        for ch in raw:
            trial = current + ch
            if text_size(draw, trial, font)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = ch
                if max_lines and len(lines) >= max_lines:
                    lines[-1] = lines[-1].rstrip("，。,. ") + "..."
                    return lines
        if current:
            lines.append(current)
            if max_lines and len(lines) >= max_lines:
                return lines
    return lines


def vertical_gradient(width: int, height: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    im = Image.new("RGB", (width, height), top)
    px = im.load()
    for y in range(height):
        t = y / max(1, height - 1)
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        for x in range(width):
            px[x, y] = color
    return im


def horizontal_gradient(width: int, height: int, left: tuple[int, int, int], right: tuple[int, int, int]) -> Image.Image:
    im = Image.new("RGB", (width, height), left)
    px = im.load()
    for x in range(width):
        t = x / max(1, width - 1)
        color = tuple(round(left[i] * (1 - t) + right[i] * t) for i in range(3))
        for y in range(height):
            px[x, y] = color
    return im


def rounded_gradient(
    base: Image.Image,
    box: tuple[int, int, int, int],
    radius: int,
    left: tuple[int, int, int],
    right: tuple[int, int, int],
) -> None:
    x0, y0, x1, y1 = box
    grad = horizontal_gradient(x1 - x0, y1 - y0, left, right).convert("RGBA")
    mask = Image.new("L", grad.size, 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((0, 0, grad.width - 1, grad.height - 1), radius=radius, fill=255)
    base.paste(grad, (x0, y0), mask)


def paste_fit(base: Image.Image, image: Image.Image, box: tuple[int, int, int, int], contain: bool = True) -> None:
    x0, y0, x1, y1 = box
    target = (x1 - x0, y1 - y0)
    im = image.convert("RGBA")
    im.thumbnail(target, Image.Resampling.LANCZOS)
    if not contain:
        im = ImageOps.fit(image.convert("RGBA"), target, method=Image.Resampling.LANCZOS)
    px = x0 + (target[0] - im.width) // 2
    py = y0 + (target[1] - im.height) // 2
    base.paste(im, (px, py), im)


def load_optional_image(value: str | None) -> Image.Image | None:
    if not value:
        return None
    try:
        if value.startswith(("http://", "https://")):
            req = urllib.request.Request(value, headers={"User-Agent": "daily-tk-proboost/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            return Image.open(io.BytesIO(data)).convert("RGBA")
        if value.startswith("file://"):
            value = value[7:]
        return Image.open(Path(value).expanduser()).convert("RGBA")
    except Exception as exc:
        print(f"Warning: could not load promo QR image: {exc}", file=sys.stderr)
        return None


def normalize_items(raw: Any) -> list[dict[str, str]]:
    data = raw.get("items", raw) if isinstance(raw, dict) else raw
    if not isinstance(data, list):
        raise ValueError("items JSON must be a list or an object with an items list")
    items: list[dict[str, str]] = []
    for idx, item in enumerate(data[:8], start=1):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or item.get("type") or ("macro" if idx <= 4 else "product"))
        title = str(item.get("title") or item.get("headline") or f"日报条目 {idx}").strip()
        body = str(item.get("body") or item.get("summary") or item.get("content") or "").strip()
        source = str(item.get("source") or item.get("evidence") or "").strip()
        items.append({"kind": kind, "title": title, "body": body, "source": source})
    while len(items) < 8:
        idx = len(items) + 1
        items.append(
            {
                "kind": "macro" if idx <= 4 else "product",
                "title": f"数据不足：第 {idx} 条日报待补充",
                "body": "当前检索或市场数据不足，发布前请替换为有来源支撑的新闻或产品信号。",
                "source": "data unavailable",
            }
        )
    return items[:8]


def demo_items() -> list[dict[str, str]]:
    return [
        {
            "kind": "macro",
            "title": "TikTok Shop 跨境合规更新进入集中观察期",
            "body": "平台政策、物流履约和商品资质仍是跨境卖家近期需要重点跟踪的三类变化，建议按目标市场逐项核对。",
            "source": "web search",
        },
        {
            "kind": "macro",
            "title": "东南亚消费旺季带动内容电商关注度",
            "body": "多个市场的促销节点临近，内容种草、达人带货和商品卡转化的组合打法更适合快速验证新品。",
            "source": "web search",
        },
        {
            "kind": "macro",
            "title": "物流时效仍影响跨境商品体验",
            "body": "配送承诺、退换货透明度和库存稳定性会直接影响商品评分，低客单高频品类尤其需要提前备货。",
            "source": "web search",
        },
        {
            "kind": "macro",
            "title": "平台治理继续向商品真实性倾斜",
            "body": "商品详情页、资质材料和达人口播承诺需要保持一致，避免因夸大效果或信息不全影响审核与转化。",
            "source": "web search",
        },
        {
            "kind": "product",
            "title": "类目大盘：近 7 日动销商品保持活跃",
            "body": "类目总览可用于判断销量、销售额、均价和新品贡献，适合先筛出增长市场再看单品。",
            "source": "configured marketplace source",
        },
        {
            "kind": "product",
            "title": "爆品观察：高销量商品需拆成交渠道",
            "body": "单品榜只能说明交易强度，进一步结合商品卡、店铺自营和达人带货占比，才能判断复制路径。",
            "source": "configured marketplace source",
        },
        {
            "kind": "product",
            "title": "黑马潜力：新品动量优先看趋势斜率",
            "body": "短期销量上升、达人数量扩张和视频供给增加同时出现时，更适合进入小批量测试池。",
            "source": "configured marketplace source",
        },
        {
            "kind": "product",
            "title": "用户声音：评论摘要帮助发现卖点缺口",
            "body": "好评点、反对意见和高频问题能转化为商品页优化、达人 brief 和短视频脚本的核心输入。",
            "source": "configured marketplace source",
        },
    ]


def read_items(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.demo:
        return demo_items()
    if args.items_json == "-":
        raw_text = sys.stdin.read().strip()
    else:
        raw_text = Path(args.items_json).expanduser().read_text(encoding="utf-8").strip()
    if not raw_text:
        raise ValueError("items JSON is empty")
    return normalize_items(json.loads(raw_text))


def category_theme(category: str) -> str:
    lowered = category.lower()
    if any(key in lowered for key in ["汽配", "五金", "机械", "工具", "auto", "hardware", "mechanic"]):
        return "mechanical"
    if any(key in lowered for key in ["美妆", "护肤", "彩妆", "beauty", "makeup", "cosmetic", "skincare"]):
        return "beauty"
    return "neutral"


def draw_motifs(draw: ImageDraw.ImageDraw, theme: str, card_box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = card_box
    pale = (226, 233, 244)
    if theme == "mechanical":
        for cx, cy, r in [(x1 - 165, y0 + 180, 42), (x0 + 135, y0 + 620, 30), (x1 - 210, y1 - 360, 48)]:
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=pale, width=5)
            draw.ellipse((cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2), outline=pale, width=4)
            for a in range(0, 360, 45):
                dx = math.cos(math.radians(a)) * (r + 14)
                dy = math.sin(math.radians(a)) * (r + 14)
                draw.line((cx, cy, cx + dx, cy + dy), fill=pale, width=4)
    elif theme == "beauty":
        for cx, cy in [(x1 - 160, y0 + 210), (x0 + 150, y1 - 520)]:
            draw.ellipse((cx - 42, cy - 42, cx + 42, cy + 42), outline=pale, width=5)
            draw.line((cx + 32, cy + 32, cx + 78, cy + 78), fill=pale, width=8)
        draw.rounded_rectangle((x1 - 245, y1 - 300, x1 - 205, y1 - 170), radius=14, outline=pale, width=5)
        draw.polygon([(x1 - 245, y1 - 300), (x1 - 225, y1 - 345), (x1 - 205, y1 - 300)], outline=pale)
    else:
        for bx, by in [(x1 - 220, y0 + 220), (x0 + 135, y1 - 480), (x1 - 260, y1 - 280)]:
            draw.rounded_rectangle((bx, by, bx + 92, by + 92), radius=18, outline=pale, width=5)
            draw.line((bx + 22, by + 48, bx + 70, by + 48), fill=pale, width=5)
            draw.line((bx + 48, by + 22, bx + 48, by + 70), fill=pale, width=5)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int,
) -> None:
    x, y = xy
    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        w, h = text_size(draw, line, font)
        draw.text((x - w // 2, y), line, font=font, fill=fill)
        y += h + 8


def draw_fit_center_text(
    draw: ImageDraw.ImageDraw,
    center_x: int,
    y: int,
    text: str,
    max_width: int,
    fill: tuple[int, int, int],
    max_size: int = 22,
    min_size: int = 14,
) -> None:
    for size in range(max_size, min_size - 1, -1):
        font = load_font(size)
        w, _ = text_size(draw, text, font)
        if w <= max_width or size == min_size:
            draw.text((center_x - w // 2, y), text, font=font, fill=fill)
            return


def draw_item(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    idx: int,
    item: dict[str, str],
    x: int,
    y: int,
    width: int,
    fonts: dict[str, ImageFont.ImageFont],
) -> int:
    title = f"{idx}. {item['title']}"
    title_lines = wrap_text(draw, title, fonts["item_title"], width - 70, max_lines=2)
    pill_h = max(62, 24 + len(title_lines) * 39)
    rounded_gradient(canvas, (x, y, x + width, y + pill_h), 30, BLUE, CYAN)
    ty = y + 14
    for line in title_lines:
        draw.text((x + 34, ty), line, font=fonts["item_title"], fill=(255, 255, 255))
        ty += 39

    body_y = y + pill_h + 24
    body_lines = wrap_text(draw, item["body"], fonts["body"], width - 20)
    for line in body_lines:
        draw.text((x + 2, body_y), line, font=fonts["body"], fill=DARK)
        body_y += 45

    source = item.get("source", "")
    if source:
        source_text = f"来源：{source}"
        source_lines = wrap_text(draw, source_text, fonts["source"], width - 20, max_lines=1)
        for line in source_lines:
            draw.text((x + 2, body_y + 6), line, font=fonts["source"], fill=MUTED)
            body_y += 31
    return body_y + 26


def compute_item_heights(items: list[dict[str, str]], fonts: dict[str, ImageFont.ImageFont]) -> list[int]:
    probe = Image.new("RGB", (WIDTH, 200), "white")
    draw = ImageDraw.Draw(probe)
    heights = []
    content_w = 820
    for idx, item in enumerate(items, start=1):
        title_lines = wrap_text(draw, f"{idx}. {item['title']}", fonts["item_title"], content_w - 70, max_lines=2)
        body_lines = wrap_text(draw, item["body"], fonts["body"], content_w - 20)
        source_lines = 1 if item.get("source") else 0
        heights.append(max(62, 24 + len(title_lines) * 39) + 24 + len(body_lines) * 45 + source_lines * 31 + 32)
    return heights


def render(args: argparse.Namespace) -> Path:
    items = read_items(args)
    fonts = {
        "hero": load_font(88, True),
        "subtitle": load_font(32, True),
        "section": load_font(45, True),
        "meta": load_font(24),
        "item_title": load_font(31, True),
        "body": load_font(31),
        "source": load_font(22),
        "footer": load_font(22),
    }
    item_heights = compute_item_heights(items, fonts)
    header_h = 430
    footer_h = 330
    card_top = 390
    card_pad_top = 54
    card_pad_bottom = 78
    item_gap = 18
    content_h = 100 + sum(item_heights) + item_gap * (len(items) - 1)
    card_h = card_pad_top + content_h + card_pad_bottom
    height = max(int(WIDTH * MIN_RATIO), header_h + card_h + footer_h - 70)

    canvas = vertical_gradient(WIDTH, height, (34, 72, 252), (232, 242, 255)).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Header
    logo = load_optional_image(args.logo)
    if logo is not None:
        paste_fit(canvas, logo, (105, 48, 285, 145))
    draw_fit_center_text(
        draw,
        WIDTH // 2,
        72,
        args.brand_name,
        820,
        (255, 255, 255),
        max_size=58,
        min_size=28,
    )
    draw_fit_center_text(
        draw,
        WIDTH // 2,
        168,
        "TikTok Shop 跨境日报",
        860,
        (255, 255, 255),
        max_size=72,
        min_size=36,
    )
    draw.rounded_rectangle((108, 292, 760, 360), radius=0, fill=(43, 57, 68))
    draw_fit_center_text(
        draw,
        434,
        310,
        args.tagline,
        600,
        (255, 255, 255),
        max_size=30,
        min_size=18,
    )

    # Main card
    card_left, card_right = 48, WIDTH - 48
    card_bottom = card_top + card_h
    draw.rounded_rectangle((card_left, card_top, card_right, card_bottom), radius=80, fill=(255, 255, 255))
    if not args.no_motifs:
        draw_motifs(draw, category_theme(args.category), (card_left, card_top, card_right, card_bottom))
    draw.rectangle((card_left, card_top + 64, card_left + 65, card_bottom - 80), fill=(255, 255, 255))
    draw.rectangle((card_right - 65, card_top, card_right, card_bottom - 65), fill=(255, 255, 255))

    section_y = card_top + 46
    draw.rounded_rectangle((118, section_y + 2, 136, section_y + 52), radius=2, fill=(62, 210, 231))
    draw.text((170, section_y - 8), f"{args.date_text}新闻快讯", font=fonts["section"], fill=BLUE)
    meta = f"{args.market}｜{args.category}"
    draw.text((172, section_y + 50), meta, font=fonts["meta"], fill=MUTED)

    y = section_y + 105
    item_x = 155
    item_w = 805
    for idx, item in enumerate(items, start=1):
        y = draw_item(canvas, draw, idx, item, item_x, y, item_w, fonts)
        if idx < len(items):
            y += item_gap

    # Footer
    footer_y = height - footer_h
    draw.rectangle((0, footer_y, WIDTH, height), fill=FOOTER)
    if logo is not None:
        paste_fit(canvas, logo, (105, footer_y + 72, 300, footer_y + 220))
    draw_fit_center_text(
        draw,
        345,
        footer_y + 105,
        args.brand_name,
        430,
        DARK,
        max_size=38,
        min_size=22,
    )
    draw_fit_center_text(
        draw,
        345,
        footer_y + 165,
        args.tagline,
        430,
        MUTED,
        max_size=22,
        min_size=15,
    )

    follow_qr = load_optional_image(args.follow_qr)
    follow_box = (575, footer_y + 42, 755, footer_y + 282)
    draw.rounded_rectangle(follow_box, radius=10, fill=(255, 255, 255))
    if follow_qr is not None:
        paste_fit(canvas, follow_qr, follow_box, contain=False)
    else:
        draw_fit_center_text(draw, 665, footer_y + 140, "关注二维码", 150, MUTED, max_size=20, min_size=14)

    promo_box = (790, footer_y + args.promo_top_offset, 970, footer_y + 282)
    draw.rounded_rectangle(promo_box, radius=10, fill=(255, 255, 255))
    promo = load_optional_image(args.promo_qr)
    if promo is not None:
        paste_fit(canvas, promo, (promo_box[0] + 15, promo_box[1] + 15, promo_box[2] - 15, promo_box[3] - 55))
    draw_fit_center_text(
        draw,
        (promo_box[0] + promo_box[2]) // 2,
        promo_box[3] - 39,
        args.promo_label,
        promo_box[2] - promo_box[0] - 14,
        DARK,
        max_size=20,
        min_size=14,
    )

    output = resolve_output(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output, quality=95)
    return output


def resolve_output(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    now = dt.datetime.now()
    out_dir = Path.cwd() / "daily-tk-proboost" / now.strftime("%Y-%m-%d")
    return (out_dir / f"daily-tk-proboost-{now.strftime('%Y%m%d-%H%M%S')}.png").resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-text", default=dt.datetime.now().strftime("%-m月%-d日"))
    parser.add_argument("--market", default="全球TK")
    parser.add_argument("--category", default="全部行业")
    parser.add_argument("--brand-name", default="TK跨境情报")
    parser.add_argument("--tagline", default="跨境市场与商品信号")
    parser.add_argument("--logo", default=None, help="Optional logo image URL or local path")
    parser.add_argument("--follow-qr", default=None, help="Optional follow QR image URL or local path")
    parser.add_argument("--promo-qr", default=None, help="Optional promo QR image URL or local path")
    parser.add_argument("--promo-label", default="领取完整数据")
    parser.add_argument("--no-motifs", action="store_true", help="Do not draw subtle background motifs in the content card")
    parser.add_argument("--promo-top-offset", type=int, default=42, help="Top offset for the promo QR slot")
    parser.add_argument("--items-json", default="-", help="Path to JSON payload, or '-' for stdin")
    parser.add_argument("--output", default=None, help="Output PNG path")
    parser.add_argument("--demo", action="store_true", help="Render with built-in demo items")
    return parser.parse_args()


def main() -> int:
    try:
        output = render(parse_args())
    except Exception as exc:
        print(f"render_report.py failed: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

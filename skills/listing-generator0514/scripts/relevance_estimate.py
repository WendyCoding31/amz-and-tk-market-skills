#!/usr/bin/env python3
"""
Estimate competitor relevance between a source ASIN and a candidate ASIN.

Input:
  python relevance_estimate.py source.json candidate.json
  python relevance_estimate.py source.json candidate.json --skip-image-match

Each JSON file should contain as many of these fields as possible:
{
  "asin": "B08S6WL5DS",
  "title": "...",
  "bullets": ["...", "..."],
  "description": "...",
  "color": "silver",
  "material": "18/8 stainless steel",
  "dimensions": "38.7 x 28.3 x 1.5 cm",
  "pack_size": "2 pack",
  "shape": "rectangular",
  "functions": ["cooling", "baking", "roasting"],
  "image_url": "https://..."
}

Output:
  JSON with final relevance, image relevance, title relevance, and image-match trace.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from title_relevance import calculate_title_relevance


DEFAULT_IMAGE_MATCH_SCRIPT = os.environ.get("IMAGE_MATCH_SCRIPT", "")
IMAGE_BLEND_WEIGHT = 0.6
TITLE_BLEND_WEIGHT = 0.4
URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")

COLOR_WORDS = {
    "black",
    "white",
    "silver",
    "gold",
    "grey",
    "gray",
    "red",
    "blue",
    "green",
    "pink",
    "clear",
    "transparent",
    "brown",
}

MATERIAL_GROUPS = {
    "glass": {"glass", "borosilicate glass", "crystal"},
    "stainless steel": {"stainless steel", "18/8 stainless steel", "18/0 stainless steel", "steel"},
    "carbon steel": {"carbon steel"},
    "silicone": {"silicone"},
    "aluminum": {"aluminium", "aluminum"},
    "plastic": {"plastic"},
    "wood": {"wood", "bamboo"},
    "iron": {"iron", "cast iron"},
}

SHAPE_WORDS = {
    "rectangular": {"rectangle", "rectangular", "oblong"},
    "round": {"round", "circle", "circular"},
    "square": {"square"},
    "oval": {"oval"},
    "folding": {"folding", "collapsible"},
    "grid": {"grid", "wire", "mesh"},
}

FUNCTION_WORDS = {
    "cooling": {"cooling", "cool"},
    "baking": {"baking", "bake"},
    "roasting": {"roasting", "roast"},
    "grilling": {"grilling", "grill", "bbq", "barbecue"},
    "drying": {"drying", "dry"},
    "draining": {"drain", "draining"},
    "serving": {"serving", "serve"},
    "storing": {"storing", "storage", "store"},
    "dispensing": {"dispensing", "dispenser", "dispense"},
}

USER_WORDS = {
    "home bakers": {"home baker", "home bakers"},
    "professional chefs": {"professional chef", "professional chefs", "chef", "chefs"},
    "beginners": {"beginner", "beginners"},
    "families": {"family", "families"},
}

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "your",
    "most",
    "will",
    "are",
    "can",
    "use",
    "set",
    "pack",
    "piece",
    "pieces",
    "inch",
    "inches",
    "cm",
}

WEIGHTS = {
    "material": 24,
    "dimensions": 22,
    "shape": 14,
    "function": 14,
    "color": 8,
    "target_user": 8,
    "pack_size": 6,
    "text_support": 4,
}

IMAGE_URL_KEYS = {
    "imageurl",
    "mainimageurl",
    "mainimage",
    "primaryimageurl",
    "primaryimage",
    "imgurl",
    "image",
}

IMAGE_URL_KEY_ALIASES = {
    "主图",
    "主图链接",
    "图片",
    "图片链接",
}

IMAGE_LIST_KEYS = {
    "images",
    "imageurls",
    "mainimages",
    "imagelist",
}


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def clean_image_url(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        for item in value:
            url = clean_image_url(item)
            if url:
                return url
        return ""
    if isinstance(value, dict):
        for key in ("large", "hiRes", "hi_res", "url", "link", "image_url", "main_image_url"):
            if key in value:
                url = clean_image_url(value.get(key))
                if url:
                    return url
        for item in value.values():
            url = clean_image_url(item)
            if url:
                return url
        return ""

    match = URL_PATTERN.search(str(value).strip())
    if not match:
        return ""
    return match.group(0).rstrip("),.;")


def find_image_url(value: Any, max_depth: int = 4) -> str:
    if max_depth < 0:
        return ""
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = normalize_key(str(key))
            if str(key) in IMAGE_URL_KEY_ALIASES or normalized in IMAGE_URL_KEYS:
                url = clean_image_url(child)
                if url:
                    return url
        for key, child in value.items():
            normalized = normalize_key(str(key))
            if normalized in IMAGE_LIST_KEYS:
                url = clean_image_url(child)
                if url:
                    return url
        for child in value.values():
            url = find_image_url(child, max_depth - 1)
            if url:
                return url
    elif isinstance(value, list):
        for item in value:
            url = find_image_url(item, max_depth - 1)
            if url:
                return url
    return ""


def extract_main_image_url(data: dict[str, Any]) -> str:
    return find_image_url(data)


def run_image_match(
    source_url: str,
    candidate_url: str,
    timeout: float,
    script_path: str | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": False,
        "source_image_url": source_url or None,
        "candidate_image_url": candidate_url or None,
        "score": None,
        "score_percent": None,
        "error": None,
    }

    if not source_url:
        result["error"] = "missing_source_image_url"
        return result
    if not candidate_url:
        result["error"] = "missing_candidate_image_url"
        return result
    if not script_path:
        result["error"] = "image_match_script_not_configured"
        return result
    image_match_script = Path(script_path).expanduser()
    if not image_match_script.exists():
        result["error"] = f"image_match_script_missing: {image_match_script}"
        return result

    command = [
        sys.executable,
        str(image_match_script),
        "--query-url",
        source_url,
        "--doc-url",
        candidate_url,
        "--sort",
        "none",
        "--timeout",
        str(timeout),
    ]

    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )
    except subprocess.TimeoutExpired:
        result["error"] = "image_match_timeout"
        return result

    if completed.returncode != 0:
        error_text = (completed.stderr or completed.stdout or "").strip()
        result["error"] = error_text[:500] or f"image_match_exit_{completed.returncode}"
        return result

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result["error"] = f"image_match_non_json_output: {completed.stdout[:500]}"
        return result

    rows = payload.get("result") or []
    if not rows:
        result["error"] = "image_match_empty_result"
        result["raw"] = payload
        return result

    try:
        score = float(rows[0].get("score"))
    except (TypeError, ValueError, AttributeError):
        result["error"] = f"image_match_invalid_score: {rows[0]}"
        result["raw"] = payload
        return result

    normalized = max(0.0, min(1.0, score))
    result.update(
        {
            "available": True,
            "score": score,
            "normalized_score": normalized,
            "score_percent": round(normalized * 100, 2),
            "matched_url": rows[0].get("url"),
            "raw_result": rows[0],
        }
    )
    return result


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    text = str(value).lower()
    text = text.replace("&amp;", "&")
    text = re.sub(r"[^a-z0-9.\s/+x-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def combined_text(data: dict[str, Any]) -> str:
    parts = [
        data.get("title", ""),
        " ".join(data.get("bullets", []) or []),
        data.get("description", ""),
        data.get("color", ""),
        data.get("material", ""),
        data.get("dimensions", ""),
        data.get("pack_size", ""),
        data.get("shape", ""),
        " ".join(data.get("functions", []) or []),
        " ".join(data.get("target_users", []) or []),
    ]
    return normalize_text(" ".join(str(p) for p in parts if p))


def extract_color(text: str) -> str:
    for word in COLOR_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", text):
            return word
    return ""


def normalize_material(text: str) -> set[str]:
    found = set()
    for canonical, variants in MATERIAL_GROUPS.items():
        for variant in variants:
            if re.search(rf"(?<![a-z0-9]){re.escape(variant)}(?![a-z0-9])", text):
                found.add(canonical)
    return found


def extract_shape(text: str) -> set[str]:
    found = set()
    for canonical, variants in SHAPE_WORDS.items():
        for variant in variants:
            if re.search(rf"\b{re.escape(variant)}\b", text):
                found.add(canonical)
    return found


def extract_functions(text: str) -> set[str]:
    found = set()
    for canonical, variants in FUNCTION_WORDS.items():
        for variant in variants:
            if re.search(rf"\b{re.escape(variant)}\b", text):
                found.add(canonical)
    return found


def extract_target_users(text: str) -> set[str]:
    found = set()
    for canonical, variants in USER_WORDS.items():
        for variant in variants:
            if variant in text:
                found.add(canonical)
    return found


def extract_pack_size(text: str) -> int | None:
    patterns = [
        r"\b(\d+)\s*(?:pack|packs)\b",
        r"\bset of\s*(\d+)\b",
        r"\b(\d+)\s*(?:piece|pieces|pcs)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def extract_dimensions_cm(text: str) -> list[float]:
    match = re.search(
        r"(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(?:[x×]\s*(\d+(?:\.\d+)?))?\s*(cm|inch|in|inches)?",
        text,
    )
    if not match:
        return []
    values = [float(group) for group in match.groups()[:3] if group is not None]
    unit = match.group(4) or "cm"
    factor = 2.54 if unit in {"inch", "in", "inches"} else 1.0
    return sorted(round(value * factor, 2) for value in values)


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text))
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def dimension_score(source_dims: list[float], candidate_dims: list[float]) -> float:
    if not source_dims and not candidate_dims:
        return 1.0
    if not source_dims or not candidate_dims:
        return 0.0
    pairs = min(len(source_dims), len(candidate_dims))
    if pairs == 0:
        return 0.0
    total = 0.0
    for src, cand in zip(source_dims[:pairs], candidate_dims[:pairs]):
        if max(src, cand) == 0:
            pair_score = 1.0
        else:
            ratio = min(src, cand) / max(src, cand)
            pair_score = max(0.0, min(1.0, ratio))
        total += pair_score
    length_penalty = pairs / max(len(source_dims), len(candidate_dims))
    return (total / pairs) * length_penalty


def material_score(source_material: set[str], candidate_material: set[str]) -> float:
    if not source_material and not candidate_material:
        return 1.0
    if not source_material or not candidate_material:
        return 0.0
    overlap = len(source_material & candidate_material)
    if not overlap:
        return 0.15
    return overlap / max(len(source_material), len(candidate_material))


def pack_size_score(source_pack: int | None, candidate_pack: int | None) -> float:
    if source_pack is None and candidate_pack is None:
        return 1.0
    if source_pack is None or candidate_pack is None:
        return 0.0
    return 1.0 if source_pack == candidate_pack else 0.2


def color_score(source_color: str, candidate_color: str) -> float:
    if not source_color and not candidate_color:
        return 1.0
    if not source_color or not candidate_color:
        return 0.0
    if source_color == candidate_color:
        return 1.0
    if {source_color, candidate_color} <= {"grey", "gray"}:
        return 0.9
    return 0.1


def text_support_score(source_text: str, candidate_text: str) -> float:
    return jaccard(tokenize(source_text), tokenize(candidate_text))


def build_features(data: dict[str, Any]) -> dict[str, Any]:
    text = combined_text(data)
    return {
        "text": text,
        "color": normalize_text(data.get("color", "")) or extract_color(text),
        "material": normalize_material(normalize_text(data.get("material", "")) or text),
        "shape": set(data.get("shape", [])) if isinstance(data.get("shape"), list) else extract_shape(text),
        "functions": set(data.get("functions", [])) if isinstance(data.get("functions"), list) else extract_functions(text),
        "target_users": set(data.get("target_users", []))
        if isinstance(data.get("target_users"), list)
        else extract_target_users(text),
        "pack_size": extract_pack_size(normalize_text(data.get("pack_size", "")) or text),
        "dimensions_cm": extract_dimensions_cm(normalize_text(data.get("dimensions", "")) or text),
    }


def calculate_relevance(
    source: dict[str, Any],
    candidate: dict[str, Any],
    use_image_match: bool = True,
    image_match_timeout: float = 60.0,
    image_match_script: str | None = DEFAULT_IMAGE_MATCH_SCRIPT,
) -> dict[str, Any]:
    title_relevance = calculate_title_relevance(source, candidate)
    title_score_percent = float(title_relevance["score_percent"])
    score_percent: float | None = title_score_percent
    component_percent = {
        "title_relevance": title_score_percent,
        "image_match": None,
    }
    image_match: dict[str, Any] = {
        "available": False,
        "source_image_url": extract_main_image_url(source) or None,
        "candidate_image_url": extract_main_image_url(candidate) or None,
        "score": None,
        "score_percent": None,
        "error": "image_match_disabled",
    }
    score_basis = "title_only_image_match_skipped"
    penalties: list[str] = []
    warnings: list[str] = []

    if use_image_match:
        image_match = run_image_match(
            image_match["source_image_url"] or "",
            image_match["candidate_image_url"] or "",
            image_match_timeout,
            image_match_script,
        )
        if image_match["available"]:
            image_score = float(image_match["normalized_score"])
            component_percent["image_match"] = image_match["score_percent"]
            score_percent = round(
                image_score * 100 * IMAGE_BLEND_WEIGHT
                + title_score_percent * TITLE_BLEND_WEIGHT,
                2,
            )
            score_basis = "title_plus_image_match"
        else:
            component_percent["image_match"] = None
            score_percent = None
            score_basis = "unscored_image_match_unavailable"
            warnings.append(f"image_match_not_used: {image_match.get('error')}")
    else:
        component_percent["image_match"] = None

    return {
        "source_asin": source.get("asin"),
        "candidate_asin": candidate.get("asin"),
        "score_percent": score_percent,
        "title_score_percent": title_score_percent,
        "attribute_score_percent": None,
        "score_basis": score_basis,
        "weights": {
            "image_match": IMAGE_BLEND_WEIGHT,
            "title_relevance": TITLE_BLEND_WEIGHT,
        },
        "component_scores": component_percent,
        "title_relevance": title_relevance,
        "image_match": image_match,
        "penalties": penalties,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate listing relevance between a source ASIN and a candidate ASIN."
    )
    parser.add_argument("source_json", help="Normalized source ASIN JSON.")
    parser.add_argument("candidate_json", help="Normalized candidate ASIN JSON.")
    parser.add_argument(
        "--skip-image-match",
        action="store_true",
        help="Disable image matching and return title-only scoring. Do not use this for competitor selection unless explicitly degrading.",
    )
    parser.add_argument(
        "--image-match-timeout",
        type=float,
        default=60.0,
        help="Timeout in seconds for the image-match API call. Default: 60.",
    )
    parser.add_argument(
        "--image-match-script",
        default=DEFAULT_IMAGE_MATCH_SCRIPT,
        help="Path to a compatible image-similarity adapter. May also be set with IMAGE_MATCH_SCRIPT.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = load_json(args.source_json)
    candidate = load_json(args.candidate_json)
    result = calculate_relevance(
        source,
        candidate,
        use_image_match=not args.skip_image_match,
        image_match_timeout=args.image_match_timeout,
        image_match_script=args.image_match_script,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

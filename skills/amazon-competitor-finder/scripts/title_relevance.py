#!/usr/bin/env python3
"""
Score title relevance between a source ASIN and a candidate ASIN.

Usage:
  python title_relevance.py source.json candidate.json
  python title_relevance.py --source-title "..." --candidate-title "..."

The score is title-only. Image relevance is handled by a user-configured
image-matching adapter and combined in relevance_estimate.py.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


TITLE_KEYS = ("title", "item_title", "标题", "product_title")

STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "without",
    "your",
    "one",
    "two",
    "three",
    "set",
    "piece",
    "pieces",
    "pack",
    "pcs",
    "pc",
    "stuck",
    "stueck",
    "satz",
    "saetze",
    "und",
    "oder",
    "mit",
    "ohne",
    "aus",
    "fur",
    "fuer",
    "der",
    "die",
    "das",
    "den",
    "dem",
    "des",
    "ein",
    "eine",
    "einer",
    "einem",
    "einen",
    "im",
    "am",
    "zum",
    "zur",
    "von",
    "home",
    "kitchen",
    "kuche",
    "kueche",
    "household",
    "haushalt",
    "use",
}

MATERIAL_GROUPS = {
    "glass": {"glass", "glas", "borosilicate", "borosilikat", "crystal", "kristall", "clear", "transparent", "klar", "durchsichtig"},
    "wood": {"wood", "wooden", "holz", "holzern", "hoelzern", "akazienholz", "acacia", "bamboo", "bambus"},
    "ceramic": {"ceramic", "keramik", "porcelain", "porzellan", "stoneware", "steingut"},
    "plastic": {"plastic", "kunststoff", "acrylic", "acryl", "pc"},
    "metal": {"metal", "metall", "stainless", "steel", "edelstahl", "iron", "eisen"},
    "silicone": {"silicone", "silikon"},
}

FUNCTION_GROUPS = {
    "lid": {"lid", "deckel", "screw", "schraubdeckel", "verschluss"},
    "spoon_or_dipper": {"spoon", "loffel", "loeffel", "honigloffel", "honigloeffel", "dipper", "ladle", "stirrer", "ruhrstab", "ruehrstab"},
    "dispensing": {"dispenser", "spender", "dosier", "dispense", "distributing", "distribute", "verteilen", "tropffrei", "no", "drip", "ausgiessen", "ausgie"},
    "storage": {"storage", "container", "jar", "pot", "behalter", "behaelter", "vorrat", "aufbewahrung", "sealed", "seal", "luftdicht"},
    "serving": {"serve", "serving", "servieren", "table", "tisch", "breakfast", "fruhstuck", "fruehstueck", "wide", "mouth"},
}

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
    "schwarz",
    "weiss",
    "weiss",
    "silber",
    "golden",
    "rot",
    "blau",
    "grun",
    "gruen",
    "klar",
    "transparent",
    "braun",
}


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def title_from_payload(payload: dict[str, Any]) -> str:
    for key in TITLE_KEYS:
        value = payload.get(key)
        if value:
            return str(value)
    return ""


def normalize_text(text: Any) -> str:
    text = "" if text is None else str(text).lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "&amp;": "&",
        "&": " and ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9./+\-\sx]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[a-z0-9]+", normalize_text(text))
    return [token for token in raw if token not in STOPWORDS and len(token) > 1]


def ngrams(items: list[str], n: int) -> set[str]:
    if len(items) < n:
        return set()
    return {" ".join(items[index : index + n]) for index in range(len(items) - n + 1)}


def grouped_matches(items: list[str], groups: dict[str, set[str]]) -> set[str]:
    item_set = set(items)
    found = set()
    for group, variants in groups.items():
        if item_set & variants:
            found.add(group)
    return found


def grouped_variant_tokens(groups: dict[str, set[str]]) -> set[str]:
    variants: set[str] = set()
    for group_variants in groups.values():
        variants.update(group_variants)
    return variants


def numeric_signals(text: str) -> set[str]:
    norm = normalize_text(text)
    signals = set()
    for pattern in [
        r"\b\d+(?:\.\d+)?\s*(?:ml|l|oz|g|kg)\b",
        r"\b\d+(?:\.\d+)?\s*x\s*\d+(?:\.\d+)?(?:\s*x\s*\d+(?:\.\d+)?)?\s*(?:cm|mm|inch|in)?\b",
        r"\b\d+\s*(?:pack|packs|pcs|pieces|piece|stuck|stueck|satz|saetze)\b",
    ]:
        signals.update(match.group(0).strip() for match in re.finditer(pattern, norm))
    return signals


def overlap_recall(source: set[str], candidate: set[str], default: float = 1.0) -> float:
    if not source:
        return default
    if not candidate:
        return 0.0
    return len(source & candidate) / len(source)


def overlap_jaccard(source: set[str], candidate: set[str], default: float = 1.0) -> float:
    if not source and not candidate:
        return default
    if not source or not candidate:
        return 0.0
    return len(source & candidate) / len(source | candidate)


def optional_source_match(source: set[str], candidate: set[str], default: float = 0.8) -> float:
    if not source:
        return default
    if not candidate:
        return 0.0
    return len(source & candidate) / len(source)


def score_title_relevance(source_title: str, candidate_title: str) -> dict[str, Any]:
    source_tokens = tokens(source_title)
    candidate_tokens = tokens(candidate_title)
    source_token_set = set(source_tokens)
    candidate_token_set = set(candidate_tokens)

    source_bigrams = ngrams(source_tokens, 2)
    candidate_bigrams = ngrams(candidate_tokens, 2)
    source_trigrams = ngrams(source_tokens, 3)
    candidate_trigrams = ngrams(candidate_tokens, 3)

    source_materials = grouped_matches(source_tokens, MATERIAL_GROUPS)
    candidate_materials = grouped_matches(candidate_tokens, MATERIAL_GROUPS)
    source_functions = grouped_matches(source_tokens, FUNCTION_GROUPS)
    candidate_functions = grouped_matches(candidate_tokens, FUNCTION_GROUPS)
    source_colors = source_token_set & COLOR_WORDS
    candidate_colors = candidate_token_set & COLOR_WORDS
    source_numbers = numeric_signals(source_title)
    candidate_numbers = numeric_signals(candidate_title)

    attribute_tokens = grouped_variant_tokens(MATERIAL_GROUPS) | grouped_variant_tokens(FUNCTION_GROUPS) | COLOR_WORDS
    source_subject_tokens = source_token_set - attribute_tokens
    candidate_subject_tokens = candidate_token_set - attribute_tokens

    subject_recall = optional_source_match(source_subject_tokens, candidate_subject_tokens, default=0.0)
    token_overlap = overlap_jaccard(source_token_set, candidate_token_set, default=0.0)
    matched_phrase_count = len((source_bigrams | source_trigrams) & (candidate_bigrams | candidate_trigrams))
    phrase_score = min(1.0, matched_phrase_count / 3)
    material_score = optional_source_match(source_materials, candidate_materials, default=0.7)
    function_score = optional_source_match(source_functions, candidate_functions, default=0.6)
    color_score = optional_source_match(source_colors, candidate_colors, default=0.8)
    numeric_score = optional_source_match(source_numbers, candidate_numbers, default=0.6)

    score = (
        subject_recall * 30
        + phrase_score * 20
        + material_score * 15
        + function_score * 25
        + token_overlap * 5
        + ((color_score + numeric_score) / 2) * 5
    )
    score = round(max(0.0, min(100.0, score)), 2)

    return {
        "score_percent": score,
        "matched_tokens": sorted(source_token_set & candidate_token_set),
        "matched_phrases": sorted((source_bigrams | source_trigrams) & (candidate_bigrams | candidate_trigrams)),
        "source_signals": {
            "materials": sorted(source_materials),
            "functions": sorted(source_functions),
            "colors": sorted(source_colors),
            "numeric": sorted(source_numbers),
        },
        "candidate_signals": {
            "materials": sorted(candidate_materials),
            "functions": sorted(candidate_functions),
            "colors": sorted(candidate_colors),
            "numeric": sorted(candidate_numbers),
        },
        "component_scores": {
            "subject_token_recall": round(subject_recall * 100, 2),
            "phrase_match": round(phrase_score * 100, 2),
            "material_match": round(material_score * 100, 2),
            "function_match": round(function_score * 100, 2),
            "token_overlap": round(token_overlap * 100, 2),
            "color_match": round(color_score * 100, 2),
            "numeric_match": round(numeric_score * 100, 2),
        },
    }


def calculate_title_relevance(source: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    return score_title_relevance(title_from_payload(source), title_from_payload(candidate))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score title relevance between a source and candidate product.")
    parser.add_argument("source_json", nargs="?", help="Source product JSON.")
    parser.add_argument("candidate_json", nargs="?", help="Candidate product JSON.")
    parser.add_argument("--source-title", help="Source title string.")
    parser.add_argument("--candidate-title", help="Candidate title string.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.source_title is not None or args.candidate_title is not None:
        source_title = args.source_title
        candidate_title = args.candidate_title
        if source_title is None and args.source_json:
            source_title = title_from_payload(load_json(args.source_json))
        if candidate_title is None and args.candidate_json:
            candidate_title = title_from_payload(load_json(args.candidate_json))
        if not source_title or not candidate_title:
            raise SystemExit("Provide both source and candidate titles, either as JSON files or --source-title/--candidate-title.")
        result = score_title_relevance(source_title, candidate_title)
    else:
        if not args.source_json or not args.candidate_json:
            raise SystemExit("Usage: python title_relevance.py source.json candidate.json")
        result = calculate_title_relevance(load_json(args.source_json), load_json(args.candidate_json))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

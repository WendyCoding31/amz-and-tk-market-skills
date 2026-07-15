#!/usr/bin/env python3
"""出文前的本地化合规检查器（支持 UK / DE / IT / FR / ES / NL 6 国站）。

用法:
  python locale_lint.py <workbook.xlsx> [--sheet 德] --marketplace DE
  python locale_lint.py <workbook.xlsx> --marketplace UK
  echo "<text>" | python locale_lint.py - --marketplace IT

退出码:
  0 = 无 ERROR（可能有 WARN）
  1 = 有 ERROR
  2 = 用法错误
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

SUPPORTED_MARKETS = ["UK", "DE", "IT", "FR", "ES", "NL"]

# ---------------------------------------------------------------- 德国站域词典
DE_NOUNS = {
    "honigglas", "honiggläser", "honigtopf", "honigtöpfe",
    "honigspender", "honigbehälter", "honiglöffel", "honigflasche",
    "honigkännchen", "honigvorratsglas", "glasgefäß", "glasbehälter",
    "akazienholzdeckel", "holzdeckel", "holzhoniglöffel", "holzuntersetzer",
    "borosilikatglas", "akazienholz", "spezifikationen", "fassungsvermögen",
    "abmessungen", "lieferumfang", "hinweis", "durchmesser", "öffnung",
    "höhe", "boden", "produktmerkmale", "material", "farbe", "frühstückstisch",
    "esstisch", "kaffeebar", "frühstückstheke",
}

# 复合词分写 → 连写（仅作 WARN）。关键词原词若为分写形式，必须保留原写法。
DE_COMPOUND_HINT = [
    (r"\bhonig\s+glas\b", "Honigglas"),
    (r"\bhonig\s+gläser\b", "Honiggläser"),
    (r"\bhonig\s+spender\b", "Honigspender"),
    (r"\bhonig\s+löffel\b", "Honiglöffel"),
    (r"\bhonig\s+topf\b", "Honigtopf"),
    (r"\bhonig\s+behälter\b", "Honigbehälter"),
    (r"\bhonig\s+flasche\b", "Honigflasche"),
    (r"\bhonig\s+sirup\s+spender\b", "Honig-Sirup-Spender"),
]

# 非英语站正文禁用的英文 SEO 词（Search Terms 段允许）
EN_SEO_FORBIDDEN = [
    "honey jar", "honey jars", "honey pot", "honey pots",
    "honey dispenser", "honey doser", "glass jar", "glass honey jar",
    "mini glass honey jars",
]

# 中国电商话术 —— 按目标语言列；ID 用于 dedup 检查
CN_ECOM_PHRASES = {
    "DE": [
        "aufgrund manueller messungen",
        "aufgrund von aufnahmewinkeln",
        "wir danken ihnen für ihr verständnis",
        "lichtverhältnissen leicht abweichen",
        "können die abmessungen um 1",
        "warme tipps",
        "warmer hinweis",
    ],
    "UK": [
        "due to manual measurement",
        "due to manual measurements",
        "due to different shooting angles",
        "due to lighting",
        "warm tips",
        "warm reminder",
        "kindly understand",
        "thank you for your understanding",
        "slight deviation",
    ],
    "IT": [
        "a causa della misurazione manuale",
        "a causa dell'angolazione",
        "ringraziamo per la sua comprensione",
        "consigli caldi",
        "promemoria caldo",
    ],
    "FR": [
        "en raison de la mesure manuelle",
        "en raison de l'angle de prise de vue",
        "merci de votre compréhension",
        "conseils chaleureux",
        "rappel chaleureux",
    ],
    "ES": [
        "debido a la medición manual",
        "debido al ángulo de disparo",
        "gracias por su comprensión",
        "consejos cálidos",
        "recordatorio cálido",
    ],
    "NL": [
        "vanwege handmatige meting",
        "vanwege de opnamehoek",
        "bedankt voor uw begrip",
        "warme tips",
        "warme herinnering",
    ],
}

# 翻译腔（DE，warning）
DE_AWKWARD = [
    ("einfach in anwendung", "Einfache Anwendung / Einfach in der Anwendung"),
    ("vintage-elegant", "nostalgisch-elegant / mit Vintage-Charme"),
    ("in den kleine honiggläser", "in den kleinen Honiggläsern（与格复数 + 形容词词尾，仅末位变格不破坏关键词）"),
]

# UK 英式拼写偏好（warning）
UK_AMERICAN_TO_BRITISH = [
    (r"\bcolor\b", "colour"),
    (r"\bcolors\b", "colours"),
    (r"\bcenter\b", "centre"),
    (r"\bcenters\b", "centres"),
    (r"\bfiber\b", "fibre"),
    (r"\bfibers\b", "fibres"),
    (r"\bgray\b", "grey"),
    (r"\borganize\b", "organise"),
    (r"\borganized\b", "organised"),
    (r"\baluminum\b", "aluminium"),
    (r"\bmold\b", "mould"),
    (r"\bmolds\b", "moulds"),
    (r"\blicense\b", "licence (n.) / license (v.)"),
]

PROSE_LABELS = {"标题", "五点1", "五点2", "五点3", "五点4", "五点5", "描述", "类目"}
SEARCH_TERM_LABELS = {"关键词", "search terms", "搜索词", "backend search terms"}
TITLE_LABELS = {"标题", "title"}

# Sentence case 校验白名单 —— 这些 token 即使作为第 2+ 个词，首字母大写也可接受
# （专有名词 / 缩写 / 常见品牌词。命中时不报 ERROR，避免误伤。）
SENTENCE_CASE_PROPER_NOUN_HINTS = {
    "amazon", "fba", "eu", "usb", "bpa", "fda", "lfgb", "iso", "ce",
    "led", "ml", "cm", "mm", "kg", "uk", "de", "it", "fr", "es", "nl",
    "us", "usa", "ed", "qty",
}


# -------------------------------------------------------------- 各市场单位/数字
def number_format_check(text: str, marketplace: str, location: str) -> list[tuple[str, str, str]]:
    """各市场对小数点的偏好：UK 用句点，DE/IT/FR/ES/NL 用逗号。"""
    out: list[tuple[str, str, str]] = []
    if marketplace == "UK":
        # UK 用句点；逗号当小数点应报错（区分千分位时较难，但电商正文中很少出现千位逗号）
        for m in re.finditer(r"\b\d+,\d{1,2}\b", text):
            num = m.group(0)
            out.append(("WARN", location,
                        f'UK 站建议用句点小数点: "{num}" → "{num.replace(",", ".")}"'))
    else:
        # 欧陆站点用逗号小数点
        for m in re.finditer(r"\b\d+\.\d+\b", text):
            num = m.group(0)
            out.append(("ERROR", location,
                        f'{marketplace} 站应使用逗号小数点: "{num}" → "{num.replace(".", ",")}"'))
    return out


def inch_check(text: str, marketplace: str, location: str) -> list[tuple[str, str, str]]:
    """欧陆 5 国（DE/IT/FR/ES/NL）正文不应出现英寸；UK 可双单位。"""
    out: list[tuple[str, str, str]] = []
    if marketplace in {"DE", "IT", "FR", "ES", "NL"}:
        for m in re.finditer(r"\b\d+(?:[.,]\d+)?\s*(in|inch|inches|\")\b",
                             text, flags=re.IGNORECASE):
            out.append(("ERROR", location,
                        f'{marketplace} 站不应出现英寸: "{m.group(0)}" 建议删除或仅保留 cm'))
    return out


# -------------------------------------------------------------- Sentence case 校验
_WORD_SPLIT = re.compile(r"\s+")


def is_sentence_case_violation(token: str) -> bool:
    """token 第 2+ 词大写首字母且非缩写/数字/白名单 → 违规。"""
    if not token:
        return False
    # 剥离前后标点
    stripped = token.strip("()[]{}<>,.:;!?\"'’“”‘ ")
    if not stripped:
        return False
    if stripped.isupper() and len(stripped) >= 2:
        return False  # 全大写当缩写处理
    if stripped[0].isdigit():
        return False
    if stripped.lower() in SENTENCE_CASE_PROPER_NOUN_HINTS:
        return False
    if not stripped[0].isalpha():
        return False
    return stripped[0].isupper()


def sentence_case_check(text: str, marketplace: str, location: str) -> list[tuple[str, str, str]]:
    """对标题字段执行 sentence case 校验；DE 站跳过（德语名词大小写规则覆盖）。"""
    out: list[tuple[str, str, str]] = []
    if marketplace == "DE":
        return out  # DE 用另一套名词大小写规则
    # 第一个 token 必须首字母大写
    tokens = _WORD_SPLIT.split(text.strip())
    if not tokens:
        return out
    first = tokens[0].strip("()[]{}<>,.:;!?\"'’“”‘ ")
    if first and first[0].isalpha() and first[0].islower():
        out.append(("ERROR", location,
                    f'{marketplace} 站标题应 sentence case: 首词首字母需大写 "{tokens[0]}"'))
    # 第 2+ 词大写首字母 → 违规（Title Case 倾向）
    violations = [t for t in tokens[1:] if is_sentence_case_violation(t)]
    if violations:
        # 只报一次，列出前 5 个例子
        sample = ", ".join(f'"{v}"' for v in violations[:5])
        out.append(("ERROR", location,
                    f'{marketplace} 站标题应 sentence case（仅首词大写）；以下后续词首字母大写违规: {sample}'))
    return out


# -------------------------------------------------------------- 检查器
def lint_text(text: str, location: str, marketplace: str,
              label: str, is_search_terms: bool = False) -> list[tuple[str, str, str]]:
    issues: list[tuple[str, str, str]] = []
    if not text:
        return issues

    is_title = label in TITLE_LABELS

    if not is_search_terms:
        # 1) DE：复合词分写提示
        if marketplace == "DE":
            for pattern, fix in DE_COMPOUND_HINT:
                for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                    issues.append((
                        "WARN", location,
                        f'分写形式 "{m.group(0)}": 若该串是关键词分配表里的原词，必须保留原写法（硬规则 1：关键词不拆散）；'
                        f'若仅为正文表达，建议连写为 "{fix}"'
                    ))

        # 2) DE：名词应大写
        if marketplace == "DE":
            for noun in DE_NOUNS:
                pattern = rf"(?<![A-Za-zäöüÄÖÜß]){re.escape(noun)}(?![A-Za-zäöüÄÖÜß])"
                for m in re.finditer(pattern, text):
                    matched = m.group(0)
                    if matched == noun and noun[0].islower():
                        cap = noun[0].upper() + noun[1:]
                        issues.append(("ERROR", location, f'德语名词应首字母大写: "{matched}" → "{cap}"'))

        # 3) 英文 SEO 词渗透 —— 非英语站
        if marketplace != "UK":
            for en in EN_SEO_FORBIDDEN:
                for m in re.finditer(rf"\b{re.escape(en)}\b", text, flags=re.IGNORECASE):
                    issues.append(("ERROR", location,
                                   f'英文 SEO 词不应在 {marketplace} 站正文,移至 Search Terms: "{m.group(0)}"'))

        # 4) UK：英式拼写偏好（WARN）
        if marketplace == "UK":
            for pattern, suggestion in UK_AMERICAN_TO_BRITISH:
                for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                    issues.append(("WARN", location,
                                   f'UK 站建议英式拼写: "{m.group(0)}" → "{suggestion}"'))

    # 5) 数字小数点（按站点）
    issues.extend(number_format_check(text, marketplace, location))

    # 6) 英寸残留（欧陆 5 国）
    issues.extend(inch_check(text, marketplace, location))

    # 7) 中国电商话术（按站点语言）
    lower = text.lower()
    for phrase in CN_ECOM_PHRASES.get(marketplace, []):
        if phrase in lower:
            issues.append(("ERROR", location,
                           f'中国电商话术: "{phrase}" 应删除,{marketplace} 站买家不期待此类免责声明'))

    if not is_search_terms:
        # 8) 翻译腔（DE，warning）
        if marketplace == "DE":
            for phrase, suggestion in DE_AWKWARD:
                if phrase in lower:
                    issues.append(("WARN", location, f'翻译腔: "{phrase}" → "{suggestion}"'))

        # 9) em dash → en dash 建议
        if "—" in text:
            issues.append(("WARN", location,
                           f'{marketplace} 站正式文案建议用带空格 en dash " – " 替代 em dash "—"'))

        # 10) Sentence case 校验（仅标题字段；DE 站内函数内跳过）
        if is_title:
            issues.extend(sentence_case_check(text, marketplace, location))

    return issues


# -------------------------------------------------------------- 输入适配
def lint_workbook(path: Path, sheet: str | None, marketplace: str) -> list[tuple[str, str, str]]:
    from openpyxl import load_workbook
    wb = load_workbook(path, data_only=True, read_only=True)
    # 默认 sheet 名按 marketplace 映射；找不到就回退到第一个 sheet
    default_sheet_hint = {
        "UK": ["英", "UK", "目标站点语言listing页"],
        "DE": ["德", "DE"],
        "IT": ["意", "IT"],
        "FR": ["法", "FR"],
        "ES": ["西", "ES"],
        "NL": ["荷", "NL"],
    }
    if sheet:
        sheet_name = sheet
    else:
        sheet_name = wb.sheetnames[0]
        for hint in default_sheet_hint.get(marketplace, []):
            for sn in wb.sheetnames:
                if hint in sn:
                    sheet_name = sn
                    break
            else:
                continue
            break
    ws = wb[sheet_name]
    issues: list[tuple[str, str, str]] = []
    for row in ws.iter_rows(values_only=False):
        if not row:
            continue
        label_cell = row[0]
        label = str(label_cell.value or "").strip()
        if not label:
            continue
        label_norm = label.lower()
        is_st = label_norm in SEARCH_TERM_LABELS
        if label not in PROSE_LABELS and not is_st:
            continue
        if len(row) < 2:
            continue
        cell = row[1]
        value = cell.value
        if not isinstance(value, str) or not value.strip():
            continue
        location = f"{sheet_name}!{cell.coordinate}  [{label}]"
        issues.extend(lint_text(value, location, marketplace=marketplace,
                                label=label, is_search_terms=is_st))
    return issues


def lint_stdin(marketplace: str) -> list[tuple[str, str, str]]:
    text = sys.stdin.read()
    return lint_text(text, location="stdin", marketplace=marketplace, label="标题")


# -------------------------------------------------------------- 报告
def render(issues: Iterable[tuple[str, str, str]]) -> tuple[str, int, int]:
    errors = warns = 0
    lines: list[str] = []
    for level, loc, msg in issues:
        if level == "ERROR":
            errors += 1
            lines.append(f"[ERROR] {loc}\n        {msg}")
        else:
            warns += 1
            lines.append(f"[WARN ] {loc}\n        {msg}")
    if not lines:
        lines.append("✓ 未发现问题。")
    lines.append(f"\n汇总: {errors} 错误, {warns} 警告")
    return "\n".join(lines), errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="出文前本地化合规检查器（6 国站）")
    parser.add_argument("input", help="工作簿路径,或 - 表示从 stdin 读入文本")
    parser.add_argument("--sheet", default=None, help="目标 sheet 名(默认按 marketplace 自动选)")
    parser.add_argument("--marketplace", required=True,
                        help=f"目标站点，支持 {'/'.join(SUPPORTED_MARKETS)}（大小写不敏感）")
    args = parser.parse_args()

    marketplace = args.marketplace.upper()
    if marketplace not in SUPPORTED_MARKETS:
        print(f"不支持的 marketplace: {args.marketplace}；支持 {SUPPORTED_MARKETS}",
              file=sys.stderr)
        return 2

    if args.input == "-":
        issues = lint_stdin(marketplace)
    else:
        path = Path(args.input)
        if not path.exists():
            print(f"找不到文件: {path}", file=sys.stderr)
            return 2
        issues = lint_workbook(path, args.sheet, marketplace)

    report, errors, _ = render(issues)
    print(report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

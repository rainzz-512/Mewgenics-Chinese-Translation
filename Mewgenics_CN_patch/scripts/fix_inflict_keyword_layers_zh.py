import argparse
import csv
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple


TARGET_FILES = [
    "abilities.csv",
    "items.csv",
    "misc.csv",
    "mutations.csv",
    "passives.csv",
    "units.csv",
]


@dataclass
class RowChange:
    file: str
    row: int
    key: str
    matched_keywords: str
    replacement_count: int
    en: str
    zh_before: str
    zh_after: str


def normalize_en_keyword(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def is_desc_row(key: str) -> bool:
    key = (key or "").strip()
    return "_DESC" in key


def has_inflict(en_text: str) -> bool:
    return bool(re.search(r"\binflicts?\b", en_text, flags=re.IGNORECASE))


def load_keyword_pairs(keyword_pairs_csv: str) -> List[Tuple[str, str]]:
    pairs: Dict[str, str] = {}

    with open(keyword_pairs_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        required = {"en", "zh"}
        missing = sorted(required - fields)
        if missing:
            raise ValueError(f"关键词对照文件缺少列: {', '.join(missing)}")

        for row in reader:
            en = (row.get("en") or "").strip()
            zh = (row.get("zh") or "").strip()
            if not en or not zh:
                continue

            en_norm = normalize_en_keyword(en)
            if en_norm and en_norm not in pairs:
                pairs[en_norm] = zh

    # 长关键词优先匹配，避免短关键词抢匹配
    return sorted(pairs.items(), key=lambda x: len(x[0]), reverse=True)


def find_inflict_keyword_hits(en_text: str, keyword_pairs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    hits: List[Tuple[str, str]] = []
    for en_kw_norm, zh_kw in keyword_pairs:
        en_kw_raw = re.escape(en_kw_norm)
        en_kw_pattern = en_kw_raw.replace(r"\ ", r"\s+")
        pattern = re.compile(rf"\b{en_kw_pattern}\s+\d+\b", flags=re.IGNORECASE)
        if pattern.search(en_text):
            hits.append((en_kw_norm, zh_kw))
    return hits


def move_number_before_zh_keyword(zh_text: str, zh_keyword: str) -> Tuple[str, int]:
    pattern = re.compile(rf"{re.escape(zh_keyword)}\s*([0-9]+)(?![0-9])")

    changed = 0

    def replacer(match: re.Match) -> str:
        nonlocal changed
        num = match.group(1)
        changed += 1
        return f"{num}层{zh_keyword}"

    new_text = pattern.sub(replacer, zh_text)
    return new_text, changed


def process_one_file(
    input_path: str,
    output_path: str,
    keyword_pairs: List[Tuple[str, str]],
) -> Tuple[int, int, List[RowChange]]:
    row_changed = 0
    replace_count = 0
    report_rows: List[RowChange] = []

    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()

        for idx, row in enumerate(rows, start=2):
            key = (row.get("KEY") or "").strip()
            en_text = row.get("en") or ""
            zh_text = row.get("zh") or ""

            if not key.startswith("//") and is_desc_row(key) and has_inflict(en_text):
                hits = find_inflict_keyword_hits(en_text, keyword_pairs)
                if hits and zh_text:
                    zh_before = zh_text
                    per_keyword_count: Dict[str, int] = defaultdict(int)

                    for _en_kw, zh_kw in hits:
                        zh_text, c = move_number_before_zh_keyword(zh_text, zh_kw)
                        if c > 0:
                            per_keyword_count[zh_kw] += c

                    if zh_text != zh_before:
                        row["zh"] = zh_text
                        row_changed += 1
                        changed_here = sum(per_keyword_count.values())
                        replace_count += changed_here

                        matched_keywords = "; ".join(
                            f"{kw}:{count}" for kw, count in sorted(per_keyword_count.items())
                        )
                        report_rows.append(
                            RowChange(
                                file=os.path.basename(input_path),
                                row=idx,
                                key=key,
                                matched_keywords=matched_keywords,
                                replacement_count=changed_here,
                                en=en_text,
                                zh_before=zh_before,
                                zh_after=zh_text,
                            )
                        )

            writer.writerow(row)

    return row_changed, replace_count, report_rows


def write_report(report_csv: str, rows: List[RowChange]) -> None:
    os.makedirs(os.path.dirname(report_csv), exist_ok=True) if os.path.dirname(report_csv) else None
    with open(report_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "row",
                "key",
                "matched_keywords",
                "replacement_count",
                "en",
                "zh_before",
                "zh_after",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "file": r.file,
                    "row": r.row,
                    "key": r.key,
                    "matched_keywords": r.matched_keywords,
                    "replacement_count": r.replacement_count,
                    "en": r.en,
                    "zh_before": r.zh_before,
                    "zh_after": r.zh_after,
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "在指定 CSV 的 DESC 行中，基于 en 列的 inflict/inflicts + keyword 数字，"
            "修复 zh 列中“关键词+数字”为“数字层关键词”，并输出修改报告。"
        )
    )
    parser.add_argument("input_dir", help="data/text 目录路径")
    parser.add_argument(
        "--keyword-pairs",
        default="",
        help="关键词中英对照文件（默认 input_dir/keyword_name_pairs.csv）",
    )
    parser.add_argument(
        "--output-dir",
        default="fixed_inflict_layers",
        help="输出子目录名（默认 fixed_inflict_layers）",
    )
    parser.add_argument(
        "--report",
        default="",
        help="报告路径（默认 output_dir/inflict_keyword_layer_report.csv）",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    if not os.path.isdir(input_dir):
        raise SystemExit(f"输入目录不存在: {input_dir}")

    keyword_pairs_csv = (
        os.path.abspath(args.keyword_pairs)
        if args.keyword_pairs
        else os.path.join(input_dir, "keyword_name_pairs.csv")
    )
    if not os.path.isfile(keyword_pairs_csv):
        raise SystemExit(f"关键词中英对照文件不存在: {keyword_pairs_csv}")

    keyword_pairs = load_keyword_pairs(keyword_pairs_csv)
    if not keyword_pairs:
        raise SystemExit("关键词中英对照为空，无法继续。")

    output_dir = os.path.join(input_dir, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    report_csv = (
        os.path.abspath(args.report)
        if args.report
        else os.path.join(output_dir, "inflict_keyword_layer_report.csv")
    )

    total_rows_changed = 0
    total_replacements = 0
    all_report_rows: List[RowChange] = []

    for name in TARGET_FILES:
        src = os.path.join(input_dir, name)
        dst = os.path.join(output_dir, name)

        if not os.path.isfile(src):
            print(f"{name}: skipped (not found)")
            continue

        rows_changed, rep_count, report_rows = process_one_file(src, dst, keyword_pairs)
        total_rows_changed += rows_changed
        total_replacements += rep_count
        all_report_rows.extend(report_rows)
        print(f"{name}: rows changed {rows_changed}, replacements {rep_count}")

    write_report(report_csv, all_report_rows)

    print("-" * 56)
    print(f"total rows changed: {total_rows_changed}")
    print(f"total replacements: {total_replacements}")
    print(f"report: {report_csv}")
    print(f"output dir: {output_dir}")


if __name__ == "__main__":
    main()

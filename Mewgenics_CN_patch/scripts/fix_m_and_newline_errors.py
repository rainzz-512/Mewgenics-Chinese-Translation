import argparse
import csv
import os
import re
from typing import Tuple

# 自动扫描目录内所有 CSV，仅排除 NPC 对话文件
EXCLUDED_FILES = {
    "npc_dialog.csv",
    "npc_dialogue.csv",
    "npcdialogue.csv",
    "m_newline_scan_report.csv",
}

# 可携带参数的标签（可按需扩展）
TAG_WITH_ARG_NAMES = ("img", "m", "s", "o", "c", "a", "pause")
TAG_WITH_ARG_GROUP = "|".join(TAG_WITH_ARG_NAMES)
# 无效 [tag:...]（字面量三个点）
INVALID_TAG_DOTS_PATTERN = re.compile(rf"\[(?:{TAG_WITH_ARG_GROUP}):\.\.\.\]")
# 匹配任意 [tag:XXXX]
TAG_WITH_ARG_PATTERN = re.compile(rf"\[({TAG_WITH_ARG_GROUP}):([^\]]*)\]")
# 裸写的 tag:value（如 m:shield / img:shield），修复为 [tag:value]
UNWRAPPED_TAG_PATTERN = re.compile(
    r"(?<![\[:\w])(img|m)\s*:\s*([A-Za-z0-9_]+(?:[\s-][A-Za-z0-9_]+)*)"
)
# 匹配花括号变量（允许内部有换行），用于修复变量内部的换行
BRACE_BLOCK_PATTERN = re.compile(r"\{[^{}]*\}", re.DOTALL)


def contains_cjk(text: str) -> bool:
    for ch in text:
        code = ord(ch)
        if (
            0x3400 <= code <= 0x4DBF
            or 0x4E00 <= code <= 0x9FFF
            or 0xF900 <= code <= 0xFAFF
            or 0x20000 <= code <= 0x2A6DF
            or 0x2A700 <= code <= 0x2B73F
            or 0x2B740 <= code <= 0x2B81F
            or 0x2B820 <= code <= 0x2CEAF
            or 0x2CEB0 <= code <= 0x2EBEF
            or 0x30000 <= code <= 0x3134F
        ):
            return True
    return False


def normalize_or_remove_invalid_tags(zh_text: str) -> Tuple[str, int]:
    changed = 0

    def sub_count(pattern: re.Pattern, repl, text: str) -> str:
        nonlocal changed
        new_text, n = pattern.subn(repl, text)
        changed += n
        return new_text

    cleaned = sub_count(INVALID_TAG_DOTS_PATTERN, "", zh_text)

    def replace_tag(match: re.Match) -> str:
        tag_name = match.group(1)
        inner = match.group(2)
        normalized = inner.strip()

        if not normalized:
            return ""

        if contains_cjk(inner):
            return ""
        return f"[{tag_name}:{normalized}]"

    def replace_and_count(match: re.Match) -> str:
        before = match.group(0)
        after = replace_tag(match)
        nonlocal changed
        if after != before:
            changed += 1
        return after

    cleaned = TAG_WITH_ARG_PATTERN.sub(replace_and_count, cleaned)
    return cleaned, changed


def wrap_unwrapped_img_m_tags(zh_text: str) -> Tuple[str, int]:
    changed = 0

    def replace_unwrapped(match: re.Match) -> str:
        nonlocal changed
        tag_name = match.group(1)
        inner = match.group(2).strip()
        if not inner or contains_cjk(inner):
            return match.group(0)
        changed += 1
        return f"[{tag_name}:{inner}]"

    fixed = UNWRAPPED_TAG_PATTERN.sub(replace_unwrapped, zh_text)
    return fixed, changed


def fix_newline_inside_braces(zh_text: str) -> Tuple[str, int]:
    fixed_count = 0

    def replace_block(match: re.Match) -> str:
        nonlocal fixed_count
        block = match.group(0)
        if "\n" not in block:
            return block

        repaired = block.replace("\n", "")
        if repaired != block:
            fixed_count += 1
        return repaired

    fixed_text = BRACE_BLOCK_PATTERN.sub(replace_block, zh_text)
    return fixed_text, fixed_count


def fix_zh_text(zh_text: str) -> Tuple[str, int]:
    if not zh_text:
        return zh_text, 0

    text1, c1 = normalize_or_remove_invalid_tags(zh_text)
    text2, c2 = wrap_unwrapped_img_m_tags(text1)
    text3, c3 = fix_newline_inside_braces(text2)
    return text3, c1 + c2 + c3


def process_file(input_path: str, output_path: str, zh_column: str) -> Tuple[int, int]:
    row_changed = 0
    fix_count = 0

    with open(input_path, "r", encoding="utf-8", newline="") as in_file:
        reader = csv.DictReader(in_file)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if fieldnames is None:
        fieldnames = []

    with open(output_path, "w", encoding="utf-8", newline="") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()

        for row in rows:
            if zh_column in row and row[zh_column] is not None:
                original = row[zh_column]
                fixed, cnt = fix_zh_text(original)
                if fixed != original:
                    row[zh_column] = fixed
                    row_changed += 1
                    fix_count += cnt

            writer.writerow(row)

    return row_changed, fix_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="修复 CSV 的 zh 列中的标签错误（img/m 等）与花括号变量换行错误。"
    )
    parser.add_argument("input_dir", help="CSV 所在目录（例如 data/text）")
    parser.add_argument("--zh-column", default="zh", help="语言列名，默认 zh")
    parser.add_argument(
        "--output-dir",
        default="fixed_m_newline",
        help="输出子目录名（默认 fixed_m_newline）",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    zh_column = args.zh_column

    if not os.path.isdir(input_dir):
        raise SystemExit(f"输入目录不存在: {input_dir}")

    output_dir = os.path.join(input_dir, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    total_rows_changed = 0
    total_fix_count = 0

    scan_files = sorted(
        name
        for name in os.listdir(input_dir)
        if name.lower().endswith(".csv") and name.lower() not in EXCLUDED_FILES
    )

    for file_name in scan_files:
        src = os.path.join(input_dir, file_name)
        dst = os.path.join(output_dir, file_name)

        if not os.path.isfile(src):
            print(f"{file_name}: skipped (not a file)")
            continue

        rows_changed, fix_count = process_file(src, dst, zh_column)
        total_rows_changed += rows_changed
        total_fix_count += fix_count
        print(f"{file_name}: rows changed {rows_changed}, fixes {fix_count}")

    print("-" * 48)
    print(f"total rows changed: {total_rows_changed}")
    print(f"total fixes: {total_fix_count}")
    print(f"output dir: {output_dir}")


if __name__ == "__main__":
    main()

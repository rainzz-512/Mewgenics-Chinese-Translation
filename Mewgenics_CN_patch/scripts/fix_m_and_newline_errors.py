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
}

# 无效 [m:...]（字面量三个点）
INVALID_M_DOTS_PATTERN = re.compile(r"\[m:\.\.\.\]")
# 匹配任意 [m:XXXX]
M_TAG_PATTERN = re.compile(r"\[m:([^\]]*)\]")
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


def remove_invalid_m_tags(zh_text: str) -> Tuple[str, int]:
    changed = 0

    def sub_count(pattern: re.Pattern, repl, text: str) -> str:
        nonlocal changed
        new_text, n = pattern.subn(repl, text)
        changed += n
        return new_text

    cleaned = sub_count(INVALID_M_DOTS_PATTERN, "", zh_text)

    def replace_m_tag(match: re.Match) -> str:
        inner = match.group(1)
        if contains_cjk(inner):
            return ""
        return match.group(0)

    def replace_and_count(match: re.Match) -> str:
        before = match.group(0)
        after = replace_m_tag(match)
        nonlocal changed
        if after != before:
            changed += 1
        return after

    cleaned = M_TAG_PATTERN.sub(replace_and_count, cleaned)
    return cleaned, changed


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

    text1, c1 = remove_invalid_m_tags(zh_text)
    text2, c2 = fix_newline_inside_braces(text1)
    return text2, c1 + c2


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
        description="修复 CSV 的 zh 列中的 m 标签错误与花括号变量换行错误。"
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

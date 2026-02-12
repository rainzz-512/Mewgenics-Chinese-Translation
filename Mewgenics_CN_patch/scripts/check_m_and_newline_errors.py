import argparse
import csv
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List

# 自动扫描目录内所有 CSV，仅排除 NPC 对话文件
EXCLUDED_FILES = {
    "npc_dialog.csv",
    "npc_dialogue.csv",
    "npcdialogue.csv",
}

# 无效 [m:...]（字面量三个点）
INVALID_M_DOTS_PATTERN = re.compile(r"\[m:\.\.\.\]")
# 所有 [m:XXXX] 标签
M_TAG_PATTERN = re.compile(r"\[m:([^\]]*)\]")
# 花括号变量中出现真实换行（如 {sta\ncks}）
BROKEN_VAR_NEWLINE_PATTERN = re.compile(r"\{[^{}\n]*\n[^{}]*\}")


@dataclass
class Issue:
    file: str
    row_number: int
    key: str
    issue_type: str
    snippet: str


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


def short_snippet(text: str, match_start: int, match_end: int, radius: int = 28) -> str:
    left = max(0, match_start - radius)
    right = min(len(text), match_end + radius)
    s = text[left:right].replace("\n", "\\n")
    if left > 0:
        s = "..." + s
    if right < len(text):
        s = s + "..."
    return s


def find_unclosed_m_tag_positions(text: str) -> List[int]:
    """查找 '[m:' 但后续找不到 ']' 的位置。"""
    positions: List[int] = []
    start = 0
    while True:
        idx = text.find("[m:", start)
        if idx == -1:
            break
        close_idx = text.find("]", idx + 3)
        if close_idx == -1:
            positions.append(idx)
            break
        start = idx + 3
    return positions


def analyze_zh_text(file_name: str, row_number: int, key: str, zh: str) -> List[Issue]:
    issues: List[Issue] = []

    # 1) [m:...] 字面量错误
    for m in INVALID_M_DOTS_PATTERN.finditer(zh):
        issues.append(
            Issue(
                file=file_name,
                row_number=row_number,
                key=key,
                issue_type="invalid_m_literal_dots",
                snippet=short_snippet(zh, m.start(), m.end()),
            )
        )

    # 2) [m:XXXX] 中 XXXX 含中文
    for m in M_TAG_PATTERN.finditer(zh):
        inner = m.group(1)
        if contains_cjk(inner):
            issues.append(
                Issue(
                    file=file_name,
                    row_number=row_number,
                    key=key,
                    issue_type="invalid_m_contains_cjk",
                    snippet=short_snippet(zh, m.start(), m.end()),
                )
            )

    # 3) [m: 未闭合
    for pos in find_unclosed_m_tag_positions(zh):
        issues.append(
            Issue(
                file=file_name,
                row_number=row_number,
                key=key,
                issue_type="invalid_m_unclosed",
                snippet=short_snippet(zh, pos, min(len(zh), pos + 3)),
            )
        )

    # 4) 花括号变量中被真实换行打断
    for m in BROKEN_VAR_NEWLINE_PATTERN.finditer(zh):
        issues.append(
            Issue(
                file=file_name,
                row_number=row_number,
                key=key,
                issue_type="broken_variable_newline",
                snippet=short_snippet(zh, m.start(), m.end()),
            )
        )

    return issues


def scan_csv_file(file_path: str, file_name: str, zh_column: str) -> List[Issue]:
    issues: List[Issue] = []
    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or zh_column not in reader.fieldnames:
            return issues

        for row_index, row in enumerate(reader, start=2):
            zh = row.get(zh_column)
            if not zh:
                continue

            key = row.get("KEY", "")
            if key.strip().startswith("//"):
                continue

            issues.extend(analyze_zh_text(file_name, row_index, key, zh))

    return issues


def write_report_csv(report_path: str, issues: List[Issue]) -> None:
    os.makedirs(os.path.dirname(report_path), exist_ok=True) if os.path.dirname(report_path) else None
    with open(report_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "row", "key", "issue_type", "snippet"],
        )
        writer.writeheader()
        for issue in issues:
            writer.writerow(
                {
                    "file": issue.file,
                    "row": issue.row_number,
                    "key": issue.key,
                    "issue_type": issue.issue_type,
                    "snippet": issue.snippet,
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="排查 CSV 中 zh 列的 m 标签错误与变量换行错误（仅检查，不改文件）。"
    )
    parser.add_argument("input_dir", help="CSV 所在目录（例如 data/text）")
    parser.add_argument(
        "--zh-column",
        default="zh",
        help="要检查的语言列名，默认 zh",
    )
    parser.add_argument(
        "--report",
        default="",
        help="可选：输出问题明细 CSV 路径（例如 data/text/scan_report.csv）",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    zh_column = args.zh_column

    if not os.path.isdir(input_dir):
        raise SystemExit(f"输入目录不存在: {input_dir}")

    all_issues: List[Issue] = []
    file_issue_count: Dict[str, int] = defaultdict(int)

    scan_files = sorted(
        name
        for name in os.listdir(input_dir)
        if name.lower().endswith(".csv") and name.lower() not in EXCLUDED_FILES
    )

    for file_name in scan_files:
        file_path = os.path.join(input_dir, file_name)
        if not os.path.isfile(file_path):
            print(f"{file_name}: skipped (not a file)")
            continue

        issues = scan_csv_file(file_path, file_name, zh_column)
        all_issues.extend(issues)
        file_issue_count[file_name] = len(issues)
        print(f"{file_name}: issues {len(issues)}")

    total = len(all_issues)
    print("-" * 48)
    print(f"total issues: {total}")

    type_counter = Counter(issue.issue_type for issue in all_issues)
    if type_counter:
        print("issue types:")
        for issue_type, count in sorted(type_counter.items()):
            print(f"  {issue_type}: {count}")

    if args.report:
        report_path = os.path.abspath(args.report)
    else:
        report_path = os.path.join(input_dir, "m_newline_scan_report.csv")

    write_report_csv(report_path, all_issues)
    print(f"report written: {report_path}")


if __name__ == "__main__":
    main()

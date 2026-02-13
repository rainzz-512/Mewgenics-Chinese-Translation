import argparse
import csv
import os
from typing import Dict, List


def is_keyword_name_row(row: Dict[str, str]) -> bool:
    key = (row.get("KEY") or "").strip()
    if not key or key.startswith("//"):
        return False
    return key.endswith("_NAME")


def extract_pairs(input_csv: str) -> List[Dict[str, str]]:
    pairs: List[Dict[str, str]] = []

    with open(input_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []

        required = {"KEY", "en", "zh"}
        missing = sorted(required - set(fieldnames))
        if missing:
            raise ValueError(f"输入文件缺少必要列: {', '.join(missing)}")

        for row in reader:
            if not is_keyword_name_row(row):
                continue

            pairs.append(
                {
                    "KEY": (row.get("KEY") or "").strip(),
                    "en": (row.get("en") or "").strip(),
                    "zh": (row.get("zh") or "").strip(),
                }
            )

    return pairs


def write_pairs(output_csv: str, pairs: List[Dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(output_csv), exist_ok=True) if os.path.dirname(output_csv) else None

    with open(output_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["KEY", "en", "zh"])
        writer.writeheader()
        writer.writerows(pairs)


def main() -> None:
    parser = argparse.ArgumentParser(description="提取 keyword_tooltips.csv 中所有 keyword_name 的中英对照。")
    parser.add_argument(
        "input_csv",
        help="输入 CSV 路径（例如 Mewgenics_CN_patch/data/text/keyword_tooltips.csv）",
    )
    parser.add_argument(
        "--output",
        default="",
        help="输出 CSV 路径（默认与输入同目录：keyword_name_pairs.csv）",
    )
    args = parser.parse_args()

    input_csv = os.path.abspath(args.input_csv)
    if not os.path.isfile(input_csv):
        raise SystemExit(f"输入文件不存在: {input_csv}")

    if args.output:
        output_csv = os.path.abspath(args.output)
    else:
        output_csv = os.path.join(os.path.dirname(input_csv), "keyword_name_pairs.csv")

    pairs = extract_pairs(input_csv)
    write_pairs(output_csv, pairs)

    print(f"keyword_name rows: {len(pairs)}")
    print(f"output: {output_csv}")


if __name__ == "__main__":
    main()

import argparse
import csv
from pathlib import Path


def normalize_multiline_text(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def load_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames


def apply_updates(
    combined_path: Path,
    diff_path: Path,
    updated_csv_path: Path | None = None,
) -> tuple[int, int, list[str]]:
    combined_rows, combined_fields = load_csv(combined_path)
    diff_rows, diff_fields = load_csv(diff_path)
    updated_map: dict[str, dict[str, str]] = {}

    if updated_csv_path is not None:
        updated_rows, updated_fields = load_csv(updated_csv_path)
        if "KEY" not in updated_fields or "en" not in updated_fields:
            raise ValueError(f"{updated_csv_path} is missing required columns: KEY/en")
        updated_map = {row["KEY"]: row for row in updated_rows}

    for required in ("KEY", "en", "zh"):
        if required not in combined_fields:
            raise ValueError(f"{combined_path} is missing required column: {required}")

    for required in ("KEY", "new_en", "zh", "status"):
        if required not in diff_fields:
            raise ValueError(f"{diff_path} is missing required column: {required}")

    combined_map = {row["KEY"]: row for row in combined_rows}
    inserted = 0
    updated = 0
    empty_zh_keys: list[str] = []

    for diff_row in diff_rows:
        key = diff_row["KEY"]
        status = diff_row["status"]
        if updated_map:
            source_row = updated_map.get(key)
            if source_row is None:
                raise ValueError(f"Missing key in updated source CSV: {key}")
            new_en = source_row.get("en", "")
        else:
            new_en = normalize_multiline_text(diff_row.get("new_en", ""))
        zh = normalize_multiline_text(diff_row.get("zh", ""))
        if not zh.strip():
            empty_zh_keys.append(key)

        target = combined_map.get(key)
        if target is None:
            if status != "new_key":
                raise ValueError(f"Missing existing key in combined.csv: {key}")
            new_row = {field: "" for field in combined_fields}
            new_row["KEY"] = key
            new_row["en"] = new_en
            new_row["zh"] = zh
            combined_rows.append(new_row)
            combined_map[key] = new_row
            inserted += 1
            continue

        target["en"] = new_en
        target["zh"] = zh
        updated += 1

    with combined_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=combined_fields)
        writer.writeheader()
        writer.writerows(combined_rows)

    return updated, inserted, empty_zh_keys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply updated English text and translated Chinese text back into combined.csv."
    )
    parser.add_argument("combined_csv", type=Path, help="Repository combined.csv")
    parser.add_argument("diff_csv", type=Path, help="Edited translation diff CSV")
    parser.add_argument(
        "--updated-csv",
        type=Path,
        default=None,
        help="Optional canonical updated combined.csv to source exact en values from",
    )
    args = parser.parse_args()

    updated, inserted, empty_zh_keys = apply_updates(
        args.combined_csv,
        args.diff_csv,
        args.updated_csv,
    )
    print(f"updated_existing={updated}")
    print(f"inserted_new={inserted}")
    print(f"empty_zh={len(empty_zh_keys)}")
    for key in empty_zh_keys:
        print(f"EMPTY_ZH\t{key}")


if __name__ == "__main__":
    main()

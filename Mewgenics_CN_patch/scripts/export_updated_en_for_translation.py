import argparse
import csv
from pathlib import Path


def load_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames


def export_diff(repo_path: Path, updated_path: Path, output_path: Path) -> tuple[int, int]:
    repo_rows, repo_fields = load_rows(repo_path)
    updated_rows, updated_fields = load_rows(updated_path)

    for required in ("KEY", "en", "zh"):
        if required not in repo_fields:
            raise ValueError(f"{repo_path} is missing required column: {required}")
        if required not in updated_fields:
            raise ValueError(f"{updated_path} is missing required column: {required}")

    repo_map = {row["KEY"]: row for row in repo_rows}
    updated_map = {row["KEY"]: row for row in updated_rows}

    changed_count = 0
    new_count = 0

    output_rows: list[dict[str, str]] = []
    for updated_row in updated_rows:
        key = updated_row["KEY"]
        repo_row = repo_map.get(key)

        if repo_row is None:
            output_rows.append(
                {
                    "status": "new_key",
                    "KEY": key,
                    "repo_en": "",
                    "new_en": updated_row.get("en", ""),
                    "zh": "",
                }
            )
            new_count += 1
            continue

        repo_en = repo_row.get("en", "")
        updated_en = updated_row.get("en", "")
        if repo_en != updated_en:
            output_rows.append(
                {
                    "status": "changed_en",
                    "KEY": key,
                    "repo_en": repo_en,
                    "new_en": updated_en,
                    "zh": repo_row.get("zh", ""),
                }
            )
            changed_count += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["status", "KEY", "repo_en", "new_en", "zh"],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    return changed_count, new_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export rows whose English text changed into a translation CSV."
    )
    parser.add_argument("repo_csv", type=Path, help="Current repository combined.csv path")
    parser.add_argument("updated_csv", type=Path, help="Updated game combined.csv path")
    parser.add_argument("output_csv", type=Path, help="Output CSV for translation edits")
    args = parser.parse_args()

    changed_count, new_count = export_diff(args.repo_csv, args.updated_csv, args.output_csv)
    print(f"exported changed_en={changed_count}, new_key={new_count} to {args.output_csv}")


if __name__ == "__main__":
    main()

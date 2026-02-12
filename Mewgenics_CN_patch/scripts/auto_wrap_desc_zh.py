import argparse
import csv
import os
import re
from typing import List, Set, Tuple

TARGET_FILES = [
    "abilities.csv",
    "enemy_abilities.csv",
    "passives.csv",
    "items.csv",
    "keyword_tooltips.csv",
    "mutations.csv",
    "units.csv",
]

PRIORITY_SPLIT_WORDS = ["并且", "同时", "然后", "因此", "因为", "等同于", "使得", "的"]
PUNCTUATION = set("，。；！？、,.;!?:：")

TAG_PATTERN = re.compile(r"\[/?[^\[\]]+\]|\{[^{}]*\}")
OPEN_TAG_NAME_PATTERN = re.compile(r"^\[([^\]/:\]]+)(?::[^\]]*)?\]$")
CLOSE_TAG_NAME_PATTERN = re.compile(r"^\[/([^\]]+)\]$")


def is_chinese_char(ch: str) -> bool:
    code = ord(ch)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
        or 0x20000 <= code <= 0x2A6DF
        or 0x2A700 <= code <= 0x2B73F
        or 0x2B740 <= code <= 0x2B81F
        or 0x2B820 <= code <= 0x2CEAF
    )


def tokenize_preserving_tags(text: str) -> List[Tuple[str, bool]]:
    tokens: List[Tuple[str, bool]] = []
    last = 0
    for m in TAG_PATTERN.finditer(text):
        if m.start() > last:
            for ch in text[last:m.start()]:
                tokens.append((ch, False))
        tokens.append((m.group(0), True))
        last = m.end()

    if last < len(text):
        for ch in text[last:]:
            tokens.append((ch, False))

    return tokens


def parse_open_tag_name(tag_text: str) -> str:
    m = OPEN_TAG_NAME_PATTERN.match(tag_text)
    return m.group(1) if m else ""


def parse_close_tag_name(tag_text: str) -> str:
    m = CLOSE_TAG_NAME_PATTERN.match(tag_text)
    return m.group(1) if m else ""


def find_protected_indices(tokens: List[Tuple[str, bool]]) -> Set[int]:
    protected: Set[int] = set()
    i = 0
    n = len(tokens)

    while i < n - 3:
        token_text, is_tag = tokens[i]
        if not is_tag or token_text.startswith("[/"):
            i += 1
            continue

        tag_name = parse_open_tag_name(token_text)
        if not tag_name:
            i += 1
            continue

        next_text, next_is_tag = tokens[i + 1]
        if next_is_tag or next_text != "(":
            i += 1
            continue

        close_paren_idx = -1
        close_tag_idx = -1
        j = i + 2
        while j < n - 1:
            t_text, t_is_tag = tokens[j]
            if t_is_tag:
                j += 1
                continue

            if t_text == ")":
                maybe_close_tag, maybe_is_tag = tokens[j + 1]
                if maybe_is_tag and parse_close_tag_name(maybe_close_tag) == tag_name:
                    close_paren_idx = j
                    close_tag_idx = j + 1
                    break
            j += 1

        if close_paren_idx != -1:
            for idx in range(i + 1, close_paren_idx + 1):
                protected.add(idx)
            i = close_tag_idx + 1
            continue

        i += 1

    return protected


def visible_token_indices(tokens: List[Tuple[str, bool]]) -> List[int]:
    return [i for i, (_, is_tag) in enumerate(tokens) if not is_tag]


def choose_split_token(
    tokens: List[Tuple[str, bool]],
    vis_indices: List[int],
    start_vis: int,
    max_len: int,
    protected_indices: Set[int],
) -> int:
    end_vis = min(len(vis_indices), start_vis + max_len)
    if end_vis >= len(vis_indices):
        return -1

    window_end = min(len(vis_indices), end_vis + 8)

    # 1) 标点优先：优先在 max_len 左右就近切
    best_idx = -1
    best_score = 10**9
    for i in range(start_vis, window_end):
        token_idx = vis_indices[i]
        if token_idx in protected_indices:
            continue
        token_text, _ = tokens[token_idx]
        if token_text in PUNCTUATION:
            dist = abs((i + 1) - end_vis)
            left_bonus = -0.25 if (i + 1) <= end_vis else 0.0
            score = dist + left_bonus
            if score < best_score:
                best_score = score
                best_idx = token_idx

    if best_idx != -1:
        return best_idx

    # 2) 语义词优先
    visible_text = "".join(tokens[vis_indices[i]][0] for i in range(start_vis, window_end))
    local_best_vis = -1
    local_score = 10**9
    target_local = end_vis - start_vis

    for word in PRIORITY_SPLIT_WORDS:
        search_from = 0
        while True:
            pos = visible_text.find(word, search_from)
            if pos == -1:
                break
            split_local = pos + len(word)
            split_vis = start_vis + split_local - 1
            if split_vis < start_vis or split_vis >= len(vis_indices):
                search_from = pos + 1
                continue

            token_idx = vis_indices[split_vis]
            if token_idx in protected_indices:
                search_from = pos + 1
                continue

            score = abs(split_local - target_local)
            if split_local <= target_local:
                score -= 0.2

            if score < local_score:
                local_score = score
                local_best_vis = split_vis

            search_from = pos + 1

    if local_best_vis != -1:
        return vis_indices[local_best_vis]

    # 3) 回退：在 end_vis 左侧最近可切点
    for i in range(end_vis - 1, start_vis, -1):
        token_idx = vis_indices[i]
        if token_idx in protected_indices:
            continue
        return token_idx

    # 4) 回退：在 end_vis 右侧最近可切点
    for i in range(end_vis, len(vis_indices)):
        token_idx = vis_indices[i]
        if token_idx in protected_indices:
            continue
        return token_idx

    return -1


def wrap_segment(segment: str, max_len: int) -> str:
    if not segment:
        return segment

    tokens = tokenize_preserving_tags(segment)
    protected = find_protected_indices(tokens)
    vis_indices = visible_token_indices(tokens)

    if len(vis_indices) <= max_len:
        return segment

    insert_after: Set[int] = set()
    start_vis = 0

    while start_vis + max_len < len(vis_indices):
        split_token_idx = choose_split_token(tokens, vis_indices, start_vis, max_len, protected)
        if split_token_idx == -1:
            break

        insert_after.add(split_token_idx)

        next_start_vis = -1
        for i, token_idx in enumerate(vis_indices):
            if token_idx == split_token_idx:
                next_start_vis = i + 1
                break

        if next_start_vis <= start_vis:
            break
        start_vis = next_start_vis

    if not insert_after:
        return segment

    out: List[str] = []
    for idx, (text, _) in enumerate(tokens):
        out.append(text)
        if idx in insert_after:
            out.append("\n")

    return "".join(out)


def wrap_zh_desc_text(text: str, max_len: int) -> Tuple[str, bool]:
    if not text:
        return text, False

    # 保留已有真实换行：逐行处理，避免破坏原有段落
    parts = text.split("\n")
    wrapped_parts = [wrap_segment(part, max_len) for part in parts]
    wrapped = "\n".join(wrapped_parts)
    return wrapped, wrapped != text


def should_process_row(row: dict) -> bool:
    key = (row.get("KEY") or "").strip()
    if not key or key.startswith("//"):
        return False
    return "DESC" in key.upper()


def process_file(input_path: str, output_path: str, max_len: int) -> Tuple[int, int]:
    rows_changed = 0
    wraps_added = 0

    with open(input_path, "r", encoding="utf-8", newline="") as in_file:
        reader = csv.DictReader(in_file)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    with open(output_path, "w", encoding="utf-8", newline="") as out_file:
        writer = csv.DictWriter(out_file, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()

        for row in rows:
            if "zh" in row and row["zh"] is not None and should_process_row(row):
                original = row["zh"]
                wrapped, changed = wrap_zh_desc_text(original, max_len)
                if changed:
                    row["zh"] = wrapped
                    rows_changed += 1
                    wraps_added += wrapped.count("\n") - original.count("\n")

            writer.writerow(row)

    return rows_changed, wraps_added


def main() -> None:
    parser = argparse.ArgumentParser(
        description="自动检测过长 DESC 文本并在 zh 列中添加合理换行（仅处理 7 个目标 CSV）。"
    )
    parser.add_argument("input_dir", help="包含本地化 CSV 的目录")
    parser.add_argument(
        "--max-len",
        type=int,
        default=14,
        help="每行可见字符长度阈值（默认 14）",
    )
    parser.add_argument(
        "--output-dir",
        default="wrapped_desc_output",
        help="输出子目录名（默认 wrapped_desc_output）",
    )
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    output_dir = os.path.join(input_dir, args.output_dir)

    if not os.path.isdir(input_dir):
        raise SystemExit(f"input dir not found: {input_dir}")

    os.makedirs(output_dir, exist_ok=True)

    total_files = 0
    total_rows_changed = 0
    total_wraps_added = 0

    for name in TARGET_FILES:
        src = os.path.join(input_dir, name)
        if not os.path.isfile(src):
            print(f"{name}: skipped (file not found)")
            continue

        dst = os.path.join(output_dir, name)
        rows_changed, wraps_added = process_file(src, dst, args.max_len)
        total_files += 1
        total_rows_changed += rows_changed
        total_wraps_added += wraps_added
        print(f"{name}: rows changed {rows_changed}, wraps added {wraps_added}")

    print("-" * 48)
    print(f"files processed: {total_files}")
    print(f"rows changed: {total_rows_changed}")
    print(f"wraps added: {total_wraps_added}")
    print(f"output dir: {output_dir}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Merge chunked SRT files from corrected/ into a single output SRT.

The chunk files preserve the original SRT block structure (index line,
speaker-inline timing line, one or more text lines). This script concatenates
them in order, preserving the original index numbering (no renumbering).
"""

from pathlib import Path

CHUNKS_DIR = Path(__file__).resolve().parent.parent / "project" / "01" / "corrected"
OUTPUT = Path(__file__).resolve().parent.parent / "project" / "01" / "output" / "剣持と天宮コラボまとめ_corrected.srt"


def main() -> None:
    chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.srt"))
    if not chunk_files:
        raise SystemExit("No chunk files found")

    parts: list[str] = []
    for path in chunk_files:
        text = path.read_text(encoding="utf-8")
        # Strip trailing blank lines only; preserve internal blanks.
        parts.append(text.rstrip() + "\n")

    # Join with a blank line between chunks (ensures block separation).
    merged = "\n".join(parts)
    # Ensure the final file ends with a single newline.
    if not merged.endswith("\n"):
        merged += "\n"

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(merged, encoding="utf-8")

    # Count blocks (each block starts with an index line that is digits only).
    block_count = 0
    for line in merged.splitlines():
        if line.strip().isdigit():
            block_count += 1

    print(f"Merged {len(chunk_files)} chunks into {OUTPUT}")
    print(f"Block count: {block_count}")


if __name__ == "__main__":
    main()

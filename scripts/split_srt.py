"""notta.ai形式のSRTを校正作業用チャンクに分割する。

各エントリの2行目は ``話者 HH:MM:SS,mmm --> HH:MM:SS,mmm`` という独自形式。
約 ``TARGET`` 件ずつに区切るが、境界は直近の無音ギャップ(>=1秒)で調整する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET = 150
FLEX = 30  # ± range to look for a good split point
MIN_GAP_SEC = 1.0

TS_RE = re.compile(
    r"^(?P<speaker>.*?)\s+"
    r"(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2},\d{3})\s*$"
)


def to_sec(ts: str) -> float:
    h, m, rest = ts.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse(raw: str) -> list[dict]:
    entries: list[dict] = []
    for block in re.split(r"\n\s*\n", raw.strip()):
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        m = TS_RE.match(lines[1])
        if not m:
            raise ValueError(f"unparsable header: {lines[1]!r}")
        entries.append(
            {
                "idx": lines[0].strip(),
                "speaker": m.group("speaker"),
                "start": m.group("start"),
                "end": m.group("end"),
                "text": "\n".join(lines[2:]).strip(),
            }
        )
    return entries


def choose_splits(entries: list[dict]) -> list[int]:
    """TARGET件ごとに分割境界を決める。境界は"次のエントリの直前"のindex(>=1)。"""
    splits: list[int] = []
    i = TARGET
    n = len(entries)
    while i < n:
        lo = max(splits[-1] + 1 if splits else 1, i - FLEX)
        hi = min(n - 1, i + FLEX)
        # 候補範囲でギャップが最大の位置を選ぶ(ただしMIN_GAP_SEC以上であれば)
        best_j = i
        best_gap = -1.0
        for j in range(lo, hi + 1):
            prev_end = to_sec(entries[j - 1]["end"])
            cur_start = to_sec(entries[j]["start"])
            gap = cur_start - prev_end
            if gap >= MIN_GAP_SEC and gap > best_gap:
                best_gap = gap
                best_j = j
        splits.append(best_j)
        i = best_j + TARGET
    # 末尾の残りが半端(< TARGET/2)なら最後の分割を取り下げて末端に吸収
    if splits and (n - splits[-1]) < TARGET // 2:
        splits.pop()
    return splits


def format_block(e: dict) -> str:
    return f"{e['idx']}\n{e['speaker']} {e['start']} --> {e['end']}\n{e['text']}\n"


def main() -> int:
    src = Path("project/01/input/剣持と天宮コラボまとめ.srt")
    dst_dir = Path("project/01/chunks")
    dst_dir.mkdir(parents=True, exist_ok=True)

    entries = parse(src.read_text(encoding="utf-8"))
    splits = choose_splits(entries)
    boundaries = [0, *splits, len(entries)]

    for existing in dst_dir.glob("chunk_*.srt"):
        existing.unlink()

    for chunk_no, (lo, hi) in enumerate(zip(boundaries, boundaries[1:]), start=1):
        chunk = entries[lo:hi]
        out = dst_dir / f"chunk_{chunk_no:02d}.srt"
        out.write_text("\n".join(format_block(e) for e in chunk), encoding="utf-8")
        head, tail = chunk[0], chunk[-1]
        print(
            f"chunk_{chunk_no:02d}: #{head['idx']}..#{tail['idx']} "
            f"({len(chunk)} entries, {head['start']} -> {tail['end']})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

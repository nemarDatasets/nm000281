#!/usr/bin/env python3
"""Make emg2pose BDF joint channels physically represent radians.

The original conversion stored radian-valued joints in BDF channels declared
as microvolts. MNE therefore returned values scaled by ``1e-6`` despite the
BIDS ``channels.tsv`` correctly saying ``rad``. This updates only the BDF
header's joint-channel physical dimensions. Digital samples and calibration
limits are untouched.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


HEADER_BYTES = 256
LABEL_WIDTH = 16
FIELD_WIDTH = 8
def _number(header: bytes, start: int, stop: int) -> int:
    return int(header[start:stop].decode("ascii").strip())


def patch_bdf(path: Path, write: bool) -> bool:
    """Patch *path* and return whether it needed a joint-unit correction."""
    with path.open("r+b" if write else "rb") as file:
        header = bytearray(file.read(HEADER_BYTES))
        n_signals = _number(header, 252, 256)
        expected_header_bytes = HEADER_BYTES * (n_signals + 1)
        if _number(header, 184, 192) != expected_header_bytes:
            raise ValueError(f"Unexpected BDF header size in {path}")
        header.extend(file.read(expected_header_bytes - HEADER_BYTES))

        transducer = HEADER_BYTES + LABEL_WIDTH * n_signals
        dimension = transducer + 80 * n_signals
        changed = False
        for index in range(n_signals):
            label = header[
                HEADER_BYTES + LABEL_WIDTH * index : HEADER_BYTES + LABEL_WIDTH * (index + 1)
            ].decode("ascii").strip()
            if not label.startswith("joint"):
                continue
            offset = dimension + FIELD_WIDTH * index
            unit = header[offset : offset + FIELD_WIDTH].decode("ascii").strip()
            if unit == "rad":
                continue
            if unit not in {"uV", "µV"}:
                raise ValueError(f"Unexpected unit {unit!r} for {label} in {path}")
            offset = dimension + FIELD_WIDTH * index
            header[offset : offset + FIELD_WIDTH] = b"rad".ljust(FIELD_WIDTH)
            changed = True
        if changed and write:
            file.seek(0)
            file.write(header)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    files = tuple(args.root.glob("sub-*/ses-*/emg/*_emg.bdf"))
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        changed = sum(executor.map(lambda path: patch_bdf(path, args.write), files))
    print(f"{'updated' if args.write else 'would update'} {changed}/{len(files)} BDF files")


if __name__ == "__main__":
    main()

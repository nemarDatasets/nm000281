#!/usr/bin/env python3
"""Give emg2pose BDF joint channels a physical range in radians.

The conversion stored joint angles as rad x 1e6 under a ``uV`` header, which
MNE scaled by 1e-6: correct. ``set_joint_angle_units.py`` (2026-08-31) then
relabelled the unit ``rad`` without rescaling the physical range, so MNE now
reads every joint 1e6 times too large (up to ~2e6 rad). This divides the joint
channels' physical minimum and maximum by 1e6 and labels them ``rad``.
Only the header changes: digital samples and digital limits are untouched.
A physical field holds 8 characters, so a value may lose its last digit
(-1.272543 -> -1.27254, an offset of a few µrad).
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LIMIT = 100.0  # no joint angle reaches 100 rad; a larger physical range is rad x 1e6


def _fit(value: float) -> bytes:
    for digits in range(8, 0, -1):
        text = f"{value:.{digits}g}"
        if len(text) <= 8:
            return text.ljust(8).encode("ascii")
    raise ValueError(value)


def patch_header(header: bytearray) -> int:
    """Rescale the joint channels of a full BDF header in place; return how many."""
    n = int(header[252:256])
    if int(header[184:192]) != 256 * (n + 1) or len(header) != 256 * (n + 1):
        raise ValueError("unexpected BDF header size")
    field = lambda at, width, i: slice(256 + at * n + width * i, 256 + at * n + width * (i + 1))
    changed = 0
    for i in range(n):
        if not header[field(0, 16, i)].decode("ascii").strip().startswith("joint"):
            continue
        unit = header[field(96, 8, i)].decode("latin-1").strip()
        lo, hi = (float(header[field(at, 8, i)]) for at in (104, 112))
        if max(abs(lo), abs(hi)) <= LIMIT:
            if unit != "rad":
                raise ValueError(f"small range under unit {unit!r}")
            continue
        if unit not in ("rad", "uV", "µV"):
            raise ValueError(f"unexpected unit {unit!r}")
        header[field(96, 8, i)] = b"rad".ljust(8)
        header[field(104, 8, i)] = _fit(lo / 1e6)
        header[field(112, 8, i)] = _fit(hi / 1e6)
        changed += 1
    return changed


def patch_bdf(path: Path, write: bool) -> int:
    with path.open("r+b" if write else "rb") as file:
        main = file.read(256)
        header = bytearray(main + file.read(256 * int(main[252:256])))
        changed = patch_header(header)
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
        changed = sum(bool(c) for c in executor.map(lambda p: patch_bdf(p, args.write), files))
    print(f"{'updated' if args.write else 'would update'} {changed}/{len(files)} BDF files")


if __name__ == "__main__":
    main()

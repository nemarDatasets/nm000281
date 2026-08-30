#!/usr/bin/env python3
"""Materialize BDF ``BAD_IK`` annotations in BIDS ``events.tsv`` files."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path

import mne
import pandas as pd


def events_path(bdf: Path) -> Path:
    return bdf.with_name(bdf.name.replace("_emg.bdf", "_events.tsv"))


def add_bad_ik_events(bdf: Path, write: bool) -> int:
    tsv = events_path(bdf)
    events = pd.read_csv(tsv, sep="\t")
    bad = mne.io.read_raw_bdf(bdf, preload=False, verbose="ERROR").annotations
    rows = [
        {
            "onset": onset,
            "duration": duration,
            "trial_type": "BAD_IK",
            "side": events.side.iloc[0],
        }
        for onset, duration, description in zip(
            bad.onset, bad.duration, bad.description, strict=True
        )
        if description == "BAD_IK"
    ]
    updated = pd.concat(
        [events.loc[events.trial_type != "BAD_IK"], pd.DataFrame(rows)],
        ignore_index=True,
    ).sort_values("onset", kind="stable")
    if write:
        updated.to_csv(tsv, sep="\t", index=False)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bids_root", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    bdfs = list(args.bids_root.rglob("*_emg.bdf"))
    with ProcessPoolExecutor(args.workers) as executor:
        counts = executor.map(partial(add_bad_ik_events, write=args.write), bdfs)
    action = "wrote" if args.write else "would write"
    print(f"{action} {sum(counts)} BAD_IK rows to {len(bdfs)} recordings")


if __name__ == "__main__":
    main()

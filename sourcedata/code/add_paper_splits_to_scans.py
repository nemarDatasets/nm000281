#!/usr/bin/env python3
"""Materialize EMG2Pose paper split columns in BIDS metadata tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


FIELDS = ("split", "generalization")


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=[*fields, *FIELDS], delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with (args.root / "sourcedata" / "emg2pose_metadata.csv").open(newline="") as file:
        splits = {
            row["filename"]: {field: row[field] for field in FIELDS}
            for row in csv.DictReader(file)
        }

    scans_updated = events_updated = 0
    for path in args.root.glob("sub-*/ses-*/*_scans.tsv"):
        fieldnames, rows = _read(path)
        fieldnames = [field for field in fieldnames if field not in FIELDS]
        for row in rows:
            split = splits[Path(row["source_file"]).stem]
            row.update(split)
            event = (path.parent / row["filename"]).with_name(
                Path(row["filename"]).name.replace("_emg.bdf", "_events.tsv")
            )
            event_fields, event_rows = _read(event)
            for event_row in event_rows:
                event_row.update(split)
            if args.write:
                _write(event, [field for field in event_fields if field not in FIELDS], event_rows)
            events_updated += 1
        if args.write:
            _write(path, fieldnames, rows)
        scans_updated += 1
    action = "updated" if args.write else "would update"
    print(f"{action} {scans_updated} scans files and {events_updated} events files")


if __name__ == "__main__":
    main()

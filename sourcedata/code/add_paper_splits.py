"""Materialize EMG2Pose's paper split in each BIDS ``scans.tsv``."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parents[2]
metadata = pd.read_csv(ROOT / "sourcedata" / "emg2pose_metadata.csv")
splits = metadata.set_index("filename")[["split", "generalization"]]

for scans_path in ROOT.glob("sub-*/ses-*/*_scans.tsv"):
    scans = pd.read_csv(scans_path, sep="\t", keep_default_na=False)
    names = scans.source_file.map(lambda value: Path(value).stem)
    try:
        scans[["split", "generalization"]] = splits.loc[names].to_numpy()
    except KeyError as error:
        raise ValueError(f"No paper split for {scans_path}") from error
    scans.to_csv(scans_path, sep="\t", index=False)

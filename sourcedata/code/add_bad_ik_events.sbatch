#!/usr/bin/env bash
# Materialize BDF BAD_IK annotations in the tracked BIDS event sidecars.
#SBATCH --job-name=nm281-bad-ik-events
#SBATCH --account=csd403
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=02:00:00

set -euo pipefail

readonly root=/expanse/projects/nemar/bruno/emg2pose_nemar/bids
readonly python_bin=/home/bpinto/.conda/envs/eegdash/bin/python3.12

"${python_bin}" "${root}/sourcedata/code/add_bad_ik_events.py" \
    "${root}" --write --workers "${SLURM_CPUS_PER_TASK}"

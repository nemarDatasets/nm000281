#!/bin/bash
#SBATCH --job-name=emg2pose-units
#SBATCH --account=csd403
#SBATCH --partition=shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=32G
#SBATCH --output=emg2pose-units-%j.out
#SBATCH --error=emg2pose-units-%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=16

set -euo pipefail

root=${1:?Pass the BIDS root as the first argument}
/home/bpinto/.conda/envs/eegdash/bin/python3.12 sourcedata/code/set_joint_angle_units.py "$root" --write --workers "$SLURM_CPUS_PER_TASK"

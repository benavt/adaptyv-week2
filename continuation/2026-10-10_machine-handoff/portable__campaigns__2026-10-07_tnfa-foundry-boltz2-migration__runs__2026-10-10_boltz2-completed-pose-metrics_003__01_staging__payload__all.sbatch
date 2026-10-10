#!/bin/bash
#SBATCH --job-name=TNFA_all_pose_metrics
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=32G
#SBATCH --time=04:00:00
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec MACHINE_CONFIGURED_PATH/software/2026-10-08_boltz2-anthropic_001/env/bin/python -B 01_staging/payload/score_pose.py --library 01_staging/payload/vendor --workers 24

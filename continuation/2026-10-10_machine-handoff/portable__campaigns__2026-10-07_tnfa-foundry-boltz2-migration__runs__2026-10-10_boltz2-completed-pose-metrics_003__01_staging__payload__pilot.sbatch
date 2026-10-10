#!/bin/bash
#SBATCH --job-name=TNFA_pose_pilot_v5
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:10:00
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
exec MACHINE_CONFIGURED_PATH/software/2026-10-08_boltz2-anthropic_001/env/bin/python -B 01_staging/payload/score_pose.py --library 01_staging/payload/vendor --pilot --workers 4

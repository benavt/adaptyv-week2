#!/bin/bash
#SBATCH --job-name=TNFA_score_transfer
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
set -euo pipefail
exec /usr/bin/python3 -B 01_staging/payload/pack.py

# TNFA BindCraft2 pocket runs — 2026-10-08

Four jobs submitted on Mimas with verified frozen input uploads and archive backup. Each requests 1,000 completed gradient trajectories; early stage failures are retained and retried. One GPU, four CPUs, 48 GB host memory and unlimited scheduler wall time per job.

Trajectory-only design uses ordinary residue-level hotspots against all three original target protomers, with a 60–100-residue single-chain binder and seed 0. Native optimization, stage checks and adaptive tuning remain enabled; ProteinMPNN and downstream acceptance are excluded. The pinned project adapter records exact terminal sequences and native structure hashes and stops at the completed-output budget. Sequence uniqueness is reported separately.

Status observed at `2026-10-08T08:25:09.067254-04:00`; this is a snapshot, not automatic monitoring.

| Input | Slurm job | Observed status | Startup verification |
| --- | --- | --- | --- |
| human-pocket-r1 | 8435 | running | GPU preflight and CPU/GPU resource logging passed |
| human-pocket-r2 | 8436 | running | GPU preflight and CPU/GPU resource logging passed |
| mouse-pocket-r1 | 8437 | pending | Queued; resource logging configured |
| mouse-pocket-r2 | 8438 | pending | Queued; resource logging configured |

Each immutable run links to its respective Foundry input predecessor. Source chemistry and atom-level selectors remain preserved as evidence; BC2 hotspot constraints are residue-level. Predictions do not certify affinity, pH response or competition eligibility.

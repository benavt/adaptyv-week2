# DD1 human and mouse RFD3 smoke runs

The researcher authorized two separate Mimas jobs with **100 requested RFD3 backbones each**, retaining the selected trimer targets, six hotspots and one 60–100-residue binder. MPNN and all refolding are excluded. The existing 50,000-backbone Empire packages remain preserved and unsubmitted.

| Target | Immutable child run | Slurm job | Queue entry (America/New_York) |
| --- | --- | --- | --- |
| Human 1TNF | `2026-10-06_160209-0400-dd1-human-1tnf-ac-pocket-rfd3-100-mimas_001` | **3963** | `2026-10-06T16:07:20-04:00` |
| Mouse 2TNF | `2026-10-06_160209-0400-dd1-mouse-2tnf-ac-pocket-rfd3-100-mimas_001` | **3964** | `2026-10-06T16:07:22-04:00` |

Both were pending for priority in the post-submission observation. This is a dated observation, not live status.

The runs link to their corresponding original `2026-10-06_150412-0400-...-rfd3-50000_001` frozen scientific snapshots. Inputs are frozen under each campaign's `runs/<run-id>/01_staging/`; matching upload folders are under `Designs/<run-id>/`. Scientific coordinates, numbering, fixed chain roles and hotspot atom selections are preserved. A specification identifier and the execution budget changed in the child runs.

Each job uses **25 batches of four = exactly 100** and explicit **seed 0**. Before submission, current installed package versions, parser/component/config source hashes and checkpoint hash matched the original Mimas runtime pins. Native input assembly and Hydra composition passed for both targets, including all three deposited target disulfides, all fixed target coordinates and the author-to-output residue mapping. The source-bond adapter is campaign-local and does not modify the shared Foundry installation. This validates preparation, not generated output chemistry or binding quality; inspect finished native outputs separately.

The allocation is one node, one task, one CPU, one GPU, up to four hours and 48 GiB memory. The initial scripts omitted an explicit memory directive, which resolved to the cluster's 1000 GiB full-node default. After acceptance, a recorded scheduler amendment reduced only these two jobs to 49152 MiB using `scontrol update JobId=3963,3964 MinMemoryNode=49152`; no jobs were cancelled or resubmitted, and scientific input bytes stayed unchanged. This update uses Slurm's documented [per-node memory adjustment](https://slurm.schedmd.com/scontrol.html).

Submission used the Fleet whole-job monitoring front door, pinned `2026-10-06_v1` runtime, 15-second CPU/RSS and allocated GPU sampling. Slurm's stored batch scripts matched the generated monitored wrappers. Pending tasks have configured telemetry; live coverage has not yet been verified.

Resolve private Mimas paths from the ignored run settings and submission receipts. Under the corresponding Foundry run folder:

- Outputs: `02_design/attempt-001/rfd3/`.
- Queue entry and memory amendment: `receipts/2026-10-06_queue-entry.json`.
- Native start/end and monotonic execution duration: `receipts/lifecycle/` and `slurm-<job-id>.out`.
- Whole-job resource logs: `receipts/2026-10-06_160209-0400_monitored-attempt_001/resources/`.
- Fleet intent, acceptance receipt and Slurm stored script: that monitored attempt directory.

No recurring monitor, completion alert, retry or downstream job was scheduled. Queue exit and execution duration remain unset while pending. Accounting is disabled on Mimas, so native lifecycle receipts and resource logs supply actual execution evidence. Existing unrelated jobs were inspected without modification.

Empire validation is separate. Five targeted parser/component/config files in its container match the validated Mimas sources, and its native seed default is null. A CPU-only container preflight was prepared under `drafts/02_design/2026-10-06_161256-0400_empire-dd1-seed-bond-preflight_001/`; it requests no GPU and generates no models. It has not been submitted. A passing validation result would support a new seed-0/bond-preserving Empire execution deployment; source comparison alone is not execution validation.

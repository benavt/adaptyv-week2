# DeltaForge KD protocol for the selected TNF-alpha candidates

Score each exact candidate sequence twice: **one complete candidate monomer
against the human TNF-alpha trimer**, and **one complete candidate monomer
against the mouse TNF-alpha trimer**. A two-domain fusion remains one intact
chain, including both domains and its linker.

Use receptor chains A/B/C and candidate chain D. If the source prediction
contains candidate copies D/E/F, retain D in its native pose and omit E/F;
apply the same rigid-body transform to all retained atoms if aligning for
display. Do not split fusion domains or interpret a three-copy complex as
the affinity-scoring input. Preserve the chosen species construct, native
chemistry, coordinates and per-atom confidence. Verify the complete D sequence
against the candidate record before a new scoring request.

The current 40 saved results use Boltz2-derived poses, DeltaForge `score-pdb`,
the `auto` scorer request and `boltzmann_parallel` aggregation. All report
`v10_2_unified_parallel_2026_05_08` with Boltz2 calibration
`v10_boltz2_gbr_2026_03_29`. Record and review any future scorer change before
combining results. Report the returned KD in nM as **DeltaForge KD**, with
human and mouse values separately. The prediction has no pH-specific input.

The completed receipt audit confirms four protein chains, A/B/C as the
receptor, D as the scored candidate, the expected species-specific target
length and full candidate length, agreement between request and response
input identities, exact candidate association, and unchanged published KD
values. The frozen selection's older `KD_scope` display-context string is
superseded by this receipt-based scope description; frozen evidence remains
unchanged.

Recheck the selected set offline with:

```bash
python3 scripts/tnfa_deltaforge_scope.py \
  --selection submissions/2026-10-19_final20-review_001/selected20.json \
  --output drafts/04_analysis/2026-10-19_final20-writeup_003
```

This command reads saved results and makes no external requests. Reuse the
completed predictions. Any new billable batch requires its own explicit
call-count and credit quote and user approval under the project policy.

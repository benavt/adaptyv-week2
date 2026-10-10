# TNFA Foundry sequence migration and first Boltz2 filtering

New paired prediction increment: [56,128 predictions for 28,064 new binders](runs/2026-10-08_boltz2-four-cohort-increment_001/README.md) submitted as CPU preflight 8466, GPU pilot 8467 and bulk array 8469. Together with the earlier 8,848 predictions, this covers every one of the 32,488 intake sequences against both Foundry trimers.

Incrementally copy verified RFD3 sequence and backbone outputs from both DD1 EmpireAI campaigns to Mimas, refold exact sequences with Boltz2, and freeze first-round evidence for branch selection.

Latest intake: **32,488 models and exact binder sequences** from original and revised human/mouse hotspots, hash-verified at the 2026-10-08 morning snapshot. The [four-cohort intake](runs/2026-10-08_empire-four-cohort-intake_001/README.md) links every native structure, cohort FASTA and the combined index. This expanded collection is distinct from the earlier paired Boltz2 inputs.

Previous refolding snapshot: all 4,424 snapshot sequences are registered and prepared against both Foundry trimers: 8,848 predictions. The [paired Boltz2 run](runs/2026-10-07_boltz2-paired-foundry-trimers_001/README.md) passed upload verification, native input validation and its four-complex GPU pilot. CPU job 6135 and pilot 6139 completed successfully; bulk array 6143 is running with 139 tasks and concurrency one. Whole-job CPU/RSS and GPU telemetry passed inspection. First-round quality ranking remains pending.

- [24 hour plan and campaign diagram](../../docs/2026-10-07_TNFA_MIGRATION_AND_BRANCH_PLAN.md)
- [Editable preparation](../../drafts/2026-10-07_tnfa-foundry-boltz2-migration/)
- [Draft settings](../../drafts/2026-10-07_tnfa-foundry-boltz2-migration/settings.draft.json)
- [Campaign record](campaign.json)

Editable inputs are in the four stage folders under `drafts/2026-10-07_tnfa-foundry-boltz2-migration/`. The full intake and paired Boltz2 successor preserve separate immutable inputs and parent links. Current execution progress and transport/submission/resource evidence live in the paired run's `state.json` and `receipts/`.

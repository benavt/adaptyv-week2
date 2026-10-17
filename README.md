# Week2 — TNF-alpha

Separate scientific project `TNFA` for Adaptyv Challenge 02. Local code is the
control surface: prepare hotspots locally, run Foundry and Boltz2 on Mimas, then
score and analyze selected results on the Mac. Mouse trimer sampling is defined in
`2026-10-06_mouse-tnfa-trimer`; binder-design constructs, hotspots and detailed
Foundry/Boltz2 settings remain unset.

Start with `python3 scripts/workspace.py show` and [overview.md](overview.md).
The shared workflow is pinned as `external/research-workflows`; run
`python3 scripts/workspace.py pin` to verify the effective release. After a
fresh clone, initialize the submodule with
`git submodule update --init -- external/research-workflows`.
Read [challenge requirements](docs/CHALLENGE.md) before scientific choices and
[workflow](docs/WORKSPACE.md) for preparation, transfer and sequence tracing.
Foundry/Boltz2 execution against the new paths has not yet been validated. The
2TNF AFSample3 sampling run uses its own validated native parser and submitted
Slurm launchers.

```text
project.json                   Target and four-stage recipe
workflow.lock.json             Shared code and guide version pins
campaigns/<campaign>/
  campaign.json                Scientific question and chosen recipe
  runs/<YYYY-MM-DD_label_NNN>/
    run.json                   Frozen inputs/settings identity and parent links
    01_staging/                Frozen native inputs
    02_design/                 Foundry results
    03_filtering/              Boltz2 results and local scores
    04_analysis/               Comparisons, plots and reports
    state.json                 Recorded progress
    receipts/                  Transport/execution observations
registry/candidates/           Exact sequences, native origins and parent candidates
registry/observations/         Source-linked scores and other evidence
drafts/                        Editable inputs and proposed provenance records
submissions/<dated-selection>/ Frozen ranked set with complete candidate traces
reference/                     Retained pre-adoption starter; historical references
local/                         Private location configuration
```

Each stage has one responsibility; execution location can differ by substep.
Campaigns share the pinned stages and standards rather than duplicate manuals.
Candidate traces explain how one final sequence arose across runs and campaigns;
a frozen selection preserves the ranking and evidence for the chosen set.

Git tracks portable source, reviewed campaign configs and requirements. Runs,
registry records, drafts, dated selection packages, private settings, weights,
predictions and references are currently ignored. Back these up with the actual
scientific artifacts; a Git clone alone cannot restore them. Publish nonsecret
provenance only through a deliberate reviewed allowlist change. Restore private
configuration and retained guides before creating runs in a fresh clone.

Original starter files remain under `reference/` with unchanged bytes and internal
relative layout. Its prior launchers retain their old path contracts. Shared
workflow code is pinned separately from upstream engines and retained guide
snapshots; those references are not installed prediction environments.

Reference structures and prior TNFA analyses are indexed in
[the reference intake](docs/2026-10-05_TNFA_REFERENCE_INTAKE.md). Campaign inputs
and hotspots remain unset.

Final October 5 TNFA trimer modeling deliverables for all eight targets are indexed
in [the successor modeling intake](docs/2026-10-06_TNFA_TRIMER_MODELING_INTAKE.md).

[Proposed TNFA species colors](docs/2026-10-06_TNFA_COLORS.md) use three human
blues and three mouse copper/amber shades, with separate atom-color conventions.

Human and mouse focus-region objects and charge/histidine stick conventions are
documented in [the TNFA color guide](docs/2026-10-06_TNFA_COLORS.md#focus-regions).

[The next 24 hour migration and branch plan](docs/2026-10-07_TNFA_MIGRATION_AND_BRANCH_PLAN.md)
prepares both DD1 EmpireAI RFD3 sequence/backbone cohorts for incremental Boltz2
refolding on Mimas, followed by ProtonPottsMPNN redesign and APNovo inputs focused
on epitope targeting. Three new campaigns and editable stage folders are prepared;
their scientific settings and downstream candidate assignments remain pending.

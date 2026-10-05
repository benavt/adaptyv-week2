# Week2 — TNF-alpha

Separate scientific project `TNFA` for Adaptyv Challenge 02. Local code is the
control surface: prepare hotspots locally, run Foundry and Boltz2 on Mimas, then
score and analyze selected results on the Mac. The first campaign name, constructs,
hotspots and detailed settings remain unset.

Start with `python3 scripts/workspace.py show` and [overview.md](overview.md).
Read [challenge requirements](docs/CHALLENGE.md) before scientific choices and
[workflow](docs/WORKSPACE.md) for preparation, transfer and sequence tracing.
Native execution against the new paths has not yet been validated; no scientific
jobs have been launched by this adoption.

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

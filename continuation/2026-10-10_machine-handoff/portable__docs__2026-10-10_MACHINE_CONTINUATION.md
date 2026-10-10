# Continue TNFA analysis on another machine

All 64,976 Boltz2 predictions are complete remotely. Full paired scoring for
32,488 exact designs completed in Slurm10460 with validated output and passing
finished CPU telemetry. Do not submit prediction jobs again.

The requested report is still pending: 44 slides (four cohort scatter slides and
ten designs per original-human, original-mouse, revised-human, revised-mouse).
Rank by mean human/mouse best-protomer IPSAE times binder pose TM after target
alignment. Pair human and mouse structures in each PyMOL session.

The user stopped bulk downloads. Collect the completed score files, then only
selected model files and supporting evidence. Never restart bulk collectors.
Existing native results remain canonical on Mimas; local partial downloads are
not in Git. Preserve all existing data.

## Dependencies and connection

Clone this repository, https://github.com/benavt/fleet and
https://github.com/benavt/research-workflows. Use the workflow commit pinned in
workflow.lock.json. Configure Fleet on the new machine using its instructions;
private machine/environment bindings and SSH credentials are intentionally not
in this repository. Configure the SSH alias mimas with strict host verification
and an active RPI network/VPN connection. Set WORKFLOWS_HOME to the workflow
checkout, or configure ignored local/fleet.json with the new machine paths.
The renderer requires a PyMOL Python environment. Presentation creation uses the
Codex bundled Node runtime and @oai/artifact-tool.

Run python3 scripts/workspace.py show and read AGENTS.md. Current state:
local/2026-10-09_boltz2-results-retrieval_001/handoff.json.
Absolute Mac paths in historical receipts are evidence, not new-machine paths;
run helpers from the repository root and adapt local dependencies deliberately.

## Resume score collection and selected models

Remote project root: MACHINE_CONFIGURED_PATH/research/projects/adaptyv-week2.
Campaign: 2026-10-07_tnfa-foundry-boltz2-migration.
Score run: 2026-10-10_boltz2-completed-pose-metrics_003.
Lossless transfer run: 2026-10-10_boltz2-score-transfer_002; CPU10461 validated,
finished CPU telemetry passed. Its four output files are under
04_analysis/2026-10-10_score-transfer_002: metrics.jsonl.gz, runtime.json.gz,
source-completion.json, transfer-validation.json. Collect with the pinned
workspace collect route and explicit file list. Inspect any running collectors
before starting another one. The old Mac may still be downloading these scores.

Use 2026-10-10_unpack_score_transfer_002.py, then
2026-10-10_select_top10_native.py under the handoff directory. The selector
validates full-cohort counts, ranks deterministically, and creates per-source
missing-selected-CIF file lists. Use workspace collect for those lists only;
verify native SHA256 values before rendering. The renderer consumes the selected
records, saved shared-camera002 and four-hotspot reference PSE included in Git.

Finalizer003 additionally validates candidate traces. The candidate trace backup is included in Git as
2026-10-10_candidate-traces-portable-backup.tar.gz under the handoff directory.
Verify its companion SHA256 record and extract it from the repository root
before final selection provenance validation. Registry records remain private
source data; recover their recorded backup if new observations are needed. Missing
provenance must stay explicit. Prior raw score001 can be recovered from its
recorded remote run for reused-score comparisons. Do not silently omit these
checks.

The previous V2 build-v4/build.mjs is included as the layout source. Adapt its
local runtime and source paths. Create a new dated report; preserve the original
V2. Read the presentations skill and common presentation standard, run the
new-operation authoring marker exactly once, inspect every slide, and package
paired human/mouse PSE sessions with source hashes. The 44-slide authoring marker
has not yet run. No new top10 PPTX has been generated.

The original top1% mean-IPSAE report remains an outstanding task after top10.
Hourly continuation on the original Mac is still active; avoid concurrent
report authorship and duplicate collection. Move or pause that automation when
starting continuation on the new machine.

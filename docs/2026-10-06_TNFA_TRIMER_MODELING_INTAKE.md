# TNFA trimer modeling intake — 2026-10-06

The eight final October 5 AIS_SC workflow runs are indexed in
[drafts/01_staging/2026-10-06_tnfa-trimer-modeling-intake_001/README.md](../drafts/01_staging/2026-10-06_tnfa-trimer-modeling-intake_001/README.md).
Each target has its final PowerPoint and PyMOL session, plus all non-distogram
supporting files from the supplied run folder. Targets: 1TNF, 4TSV, 5TSW, 6OOZ,
6OP0, 7JRA, 9OJO and 9OJS.

This is a new reference snapshot linked by path and manifest hash to the
[October 5 intake](2026-10-05_TNFA_REFERENCE_INTAKE.md). The earlier snapshot,
original AIS_SC files, historical run IDs and filenames remain intact.
No campaign, target construct or hotspot has been selected.

The intake manifest records original paths, sizes and SHA-256 hashes for copied
files and bulk distograms retained at source. Copy verification checks bytes;
it does not validate scientific interpretation. Native manifests and reports keep
historical absolute paths. Do not invoke capture/F5 helpers from copied sessions
without reviewed execution bindings. Display-aligned coordinates require explicit
mapping before selection as native campaign inputs.

The scientific material is ignored by Git. A separate local archive and verified
hash receipt live under `local/backups/`; source originals are also retained.
A remote archive has not been verified for this successor intake. The earlier
intake's Mimas backup does not establish coverage of these later deliverables.

## Medoid-only sessions

[Generated medoid-only sessions](../drafts/04_analysis/2026-10-06_tnfa-medoid-sessions_002/README.md)
provide one PSE per target and one per cluster. They use the existing full-cluster
medoids, as requested, rather than medoids recomputed from selected display models.
Single-state medoid objects come from the verified parent sessions; their atom,
bond, chain/residue identities and already-aligned coordinates are checked after
reopening each output. Historical raw CIF paths are currently unavailable.

The combined sessions have one scene per cluster and an overlay scene. Clean
sessions omit historical capture callbacks. The new derivation records source
hashes, settings, generator/runtime versions and a predecessor attempt whose
validation stopped on bond-list ordering. The successor compares bond connectivity
independently of list ordering. Prior inputs and failure evidence are preserved.

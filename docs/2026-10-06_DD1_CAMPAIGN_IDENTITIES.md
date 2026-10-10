# DD1 TNFa campaign identities

DD1 is the first TNFa lateral-pocket design brief for both human and mouse target variants. The label does not identify a generated sequence; exact candidates will be registered after generation. Species and PDB IDs distinguish target contexts.

Prepared `2026-10-06T15:04:12.448388-04:00` in America/New_York.

| Target | Immutable run and upload folder ID |
| --- | --- |
| Human | `2026-10-06_150412-0400-dd1-human-1tnf-ac-pocket-rfd3-50000_001` |
| Mouse | `2026-10-06_150412-0400-dd1-mouse-2tnf-ac-pocket-rfd3-50000_001` |

Use `YYYY-MM-DD_HHMMSS±HHMM-dd1-SPECIES-PDB-ac-pocket-rfd3-COUNT_NNN`. The timestamp is the preparation snapshot time, including UTC offset; actual job execution times belong in scheduler/resource receipts. Preserve the whole basename during upload.

The same ID appears in the local frozen run, local `Designs/` export, native YAML/JSON block, exported `RUN_ID`, and cluster Foundry run folder.

- [Human upload bundle](../campaigns/2026-10-06_dd1-human-tnfa-pocket/Designs/2026-10-06_150412-0400-dd1-human-1tnf-ac-pocket-rfd3-50000_001/README.md)
  → `<Empire-run-root>/2026-10-06_150412-0400-dd1-human-1tnf-ac-pocket-rfd3-50000_001`.

- [Mouse upload bundle](../campaigns/2026-10-06_dd1-mouse-tnfa-pocket/Designs/2026-10-06_150412-0400-dd1-mouse-2tnf-ac-pocket-rfd3-50000_001/README.md)
  → `<Empire-run-root>/2026-10-06_150412-0400-dd1-mouse-2tnf-ac-pocket-rfd3-50000_001`.

Requested settings remain one 60–100-residue binder and 50,000 RFD3 backbones per target (6,250 batches × 8), seed 0. Only RFD3 is configured; no MPNN or refolding. Target coordinates/chemistry, hotspots and colors are preserved.

Current Empire outputs are below `<run-folder>/outputs/`; submission and timing receipts are under `<run-folder>/receipts/<deployment-id>/`. The included Empire submission helper uses the authenticated login environment and retains queue-entry, queue-exit, execution start/end and elapsed durations. Original Mimas scientific preparation remains historical. Full machine-specific paths are recorded only in ignored deployment/package configuration.

Earlier naming is retired from current local campaign navigation, upload inputs and PyMOL views. Original frozen provenance is retained in verified local history, with SHA-256 predecessor links and a lineage index. Older remote preparation directories and contracts are preserved at their existing paths; these new DD1 folders are the current upload/run identities. No design jobs have been submitted.

Current host deployment: `2026-10-06_154453-0400_empire-dd1-timing_001`. Both upload/run basenames remain unchanged; immutable deployment snapshots distinguish environment/logging revisions. Configuration and transport are verified; no job has been submitted, and no Empire scientific inference is claimed.

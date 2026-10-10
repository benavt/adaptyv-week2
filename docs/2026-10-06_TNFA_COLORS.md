# TNFA molecular colors and focus-region conventions

The human cartoon palette uses distinct blue shades for the three copies. The
October 7 clarification restores this original convention; the intervening
uniform sky-blue session is superseded and preserved. The focus ranges
and residue-class colors below follow the researcher’s explicit October 6 instructions.
They supplement the pinned molecular-view standard; historical sessions are retained.

| Molecule | Protomer copy 1 | Protomer copy 2 | Protomer copy 3 |
| --- | --- | --- | --- |
| Human TNFα | Navy `#174A78` | Blue `#397FB7` | Light blue `#8BC6E8` |
| Mouse TNFα | Copper `#85451F` | Amber `#C67B35` | Sand `#EAC18B` |

Species determines the color family; three shades distinguish homomer copy slots.
For the 1TNF/2TNF reference previews, author chains A/B/C map to copies 1/2/3.
For later structures, record the molecule/copy mapping explicitly before coloring;
chain letters alone do not establish biological identity or correspondence.

Cartoons use the species/copy palette. Atom representations retain standard element
colors, with residue-class carbon colors: HIS **magenta**, ASP/GLU blue, ARG/LYS red,
and actual NAG yellow. Reserve green for original target hotspots and tv_orange
for editable interface hotspots. If overlapping annotations arise, editable
hotspots override original hotspots, then residue-class colors, then base carbon
colors. Cartoon colors remain independent. No hotspots are defined in these previews.

[Preview sessions and provenance](../drafts/04_analysis/2026-10-06_tnfa-species-colors_001/README.md)
include experimental human 1TNF and mouse 2TNF biological trimers. Native source
atoms, numbering and chemistry are retained; water is hidden, crystallization
molecules appear as sticks. The mouse object is aligned to human for display only;
the manifest records the transform, common camera, source hashes and runtime.
Changed palette proposals should create a new dated snapshot linked to this one.

## Focus regions

| Reference species/model | Range 1 | Range 2 | Chain copies |
| --- | --- | --- | --- |
| Human TNFα / 1TNF | 65–75 | 99–114 | A, B, C |
| Mouse TNFα / 2TNF | 62–74 | 99–116 | A, B, C |

Endpoints are inclusive **author residue numbers** from the supplied PyMOL click
records. Create two independent molecular objects per chain (six per species),
containing every modeled atom in that interval. Examples: `Human_TNFa_A_65_75`,
`Human_TNFa_A_99_114`, `Mouse_TNFa_A_62_74`, `Mouse_TNFa_A_99_116`.
The chain-specific objects are grouped as `Human_focus_chain_A` or
`Mouse_focus_chain_A`, with analogous groups for B/C. They are copied views of
existing atoms, not new molecules or modeled missing residues.

Within these objects, show whole residues as **sticks** using:

| Residue class | Residues | Color |
| --- | --- | --- |
| Positive | ARG, LYS | Red |
| Negative | ASP, GLU | Blue |
| Histidine | HIS | Magenta |

The uniform focus-stick residue color overrides elemental colors on all atoms
in the highlighted residues, as explicitly requested. In the earlier focus-only sessions, standard non-carbon element colors
remain outside the focus objects. Species/copy **cartoon** colors stay
independent, including in the focus objects. Neutral residues remain present,
with their species/copy colors; they are not shown as sticks by default.
These are residue-class visualization conventions, not calculated protonation
states or pH-dependent charge assignments. Histidine is kept separate.

**Project override:** use magenta for histidine in these TNFA views, replacing
the common standard’s purple. Focus-region class colors take precedence over
atom-element and base colors within the copied focus objects. The prior hotspot
palette remains available, but these inspection intervals have not been validated
or selected as design hotspots. If hotspot marks are added later, keep them in
separate annotation objects so these residue-class colors remain visible.

Human chains each highlight Lys65, His73, Arg103, Glu104, Glu107, Glu110 and Lys112.
Mouse chains each highlight Lys65, Asp71, Lys103, Asp104, Glu107, Glu110, Lys112
and Glu116. There are **no histidines in the specified mouse intervals**.
2TNF author numbering jumps from 72 to 74; author residue 73 is not invented.
Apply a source-backed author/sequence numbering map before transferring these
intervals to AFSample3 predictions or any renumbered structures. Identical integer
ranges are not automatically equivalent across species or coordinate files.

## Sessions and reproducibility

[Focus-region sessions and inventory](../drafts/04_analysis/2026-10-06_tnfa-focus-regions_002/README.md)
include human/mouse PSEs and a CSV of every highlighted residue. The default
`Overview` scene shows the complete species-colored trimer and highlighted sticks.
`Regions_only` shows focus cartoons and sticks without the remaining trimer.
`Chain_A`, `Chain_B` and `Chain_C` isolate that chain’s context and region sticks.
`Residue_labels` adds residue identity labels. Each region object can be toggled
independently in the PyMOL object panel. Original coordinates and prior sessions
remain intact; region coordinates and numbering match their parent object.

Use [scripts/tnfa_focus_regions.py](../scripts/tnfa_focus_regions.py) with the
PyMOL-equipped analysis interpreter and an unused dated output directory:

```sh
python scripts/tnfa_focus_regions.py \
  --human /absolute/path/to/human_palette.pse \
  --mouse /absolute/path/to/mouse_palette.pse \
  --output-dir drafts/04_analysis/YYYY-MM-DD_tnfa-focus-regions_NNN
```

The sources must contain `Human_TNFa_1TNF` and `Mouse_TNFa_2TNF`, respectively,
with author-numbered protein chains A/B/C. The helper checks parent/region atom
identities, coordinates, residue colors, stick visibility and saved-session
reopening. Inputs, generator hash, settings and output provenance are recorded.
Use `--prior-attempt /path/to/previous/snapshot` to record an explicit predecessor
when making a successor. The successful snapshot also retains `generator.py`,
the exact helper version used to generate its outputs.
If copying these conventions to another construct, first establish its molecule,
chain-copy and residue-number mapping, then create a new immutable snapshot.

A [combined human/mouse session](../drafts/04_analysis/2026-10-06_tnfa-combined-regions_003/README.md)
retains both trimers and all twelve region objects in separate species groups,
with side-by-side, individual-species, aligned-overlay and region-only scenes.
Grid display separates panels without translating coordinates.

## Complete-trimer charge/histidine sticks — October 6 update

The researcher extended the stick scope to **every modeled ARG/LYS, ASP/GLU and
HIS residue throughout both complete trimers**, including the twelve copied
region objects. Uniform whole-residue colors are POS red, NEG blue and HIS
magenta; this explicitly overrides elemental colors on these residues outside
the focus intervals as well. Neutral residues and existing species/copy cartoon
colors remain unchanged. No residue numbering, coordinates, bonds, molecule
identities or focus intervals were changed. This is a display convention, not a
protonation-state calculation.

The [validated full-trimer snapshot](../drafts/04_analysis/2026-10-06_tnfa-combined-regions_006/README.md)
updates all five stored scenes. Parent trimer inventories are human: POS 42, NEG
42, HIS 9; mouse: POS 33, NEG 54, HIS 9. Copied region objects are excluded from
these counts. Both species contain nine modeled histidines across their three
chains, although the earlier mouse focus intervals contain none.

At the researcher's request, the PSE in
`2026-10-06_tnfa-combined-regions_003` was updated in place after preserving its
original bytes and complete directory backup. The dated edit receipt links the
current hash to the immutable successor. Earlier focus-only generation records
remain historical. The [side-by-side preview](../drafts/04_analysis/2026-10-06_tnfa-charge-preview_002/2026-10-06_human_mouse_TNFa_regions.png)
uses separate species renders with explicit molecular-object visibility; it
does not alter the PSE's saved grid layout or coordinates.

## DD1 original-target hotspots

The first binder-design campaign, `2026-10-06_dd1-human-tnfa-pocket`, selects
**human 1TNF author chain A Lys65/Lys112/Glu146 and chain C His73/Lys90/Arg138**.
Show every modeled atom of each selected residue as **green sticks** in a separate
`DD1_Hotspots` annotation object. Clicked atoms establish residue/source identity;
they do not narrow the highlight or native design constraint to one atom. Chain B
remains full trimer context. Native numbering, coordinates and chemistry are retained.

Green original-target hotspot sticks override POS red, NEG blue and HIS magenta
on these six residues. Human blue copy cartoons remain independent. The default
scene uses a clean trimer overview; `DD1_Charge_context` restores all charged/HIS
sticks with the same hotspot precedence. Prior focus/charge sessions remain
separate. [DD1 campaign metadata and frozen review](../campaigns/2026-10-06_dd1-human-tnfa-pocket/README.md)
record the source evidence, palette, selected residues and confirmation status.

## DD1 mouse original-target hotspots

The mouse pocket campaign selects **2TNF author chain A Lys65/Lys112/Glu146
and chain C His78/Lys90/Lys140**. Highlight all modeled atoms of these residues
as green sticks in `DD1_Hotspots`, separately from `Mouse_TNFa_2TNF`. Keep mouse
A/B/C cartoons copper `#85451F`, amber `#C67B35`, sand `#EAC18B`; all other
ARG/LYS, ASP/GLU and HIS residues retain red, blue and magenta sticks. Green
overrides residue-class atom colors at the six selected hotspots, while cartoon
colors remain independent. No human target or old focus-region copies are included.

The default `DD1_Charge_context` scene shows the full charged/HIS context.
`DD1_Hotspots` offers a clean hotspot overview, plus labeled/close-up scenes.
Native 2TNF geometry and author numbering are retained; no display alignment
is used as a design source. The current Foundry target PDB retains author residue IDs, so current hotspot keys match the PSE numbers. Original mmCIF label indices remain separately recorded in the source numbering map.
[DD1 campaign metadata and full mapping](../campaigns/2026-10-06_dd1-mouse-tnfa-pocket/README.md)
record the distinction and validated input bundle.

## DD1 hotspot revision 2 — October 7

The latest researcher selections replace the original hotspot sets for these
new snapshots: human 1TNF A Glu104/Glu107/Ala109/Glu110 and C Arg103;
mouse 2TNF A Asp71/Asp104 and B Glu107/Glu110/Lys112. Author numbering and
whole-residue green-stick highlights remain unchanged conventions. The mouse
pocket now spans A/B, and the human pocket spans A/C. Prior snapshots retain
their earlier selected residues as historical evidence.

The researcher clarified that the requested October 7 cartoon correction applies
to **human**, superseding the earlier request to regenerate mouse. The
[human chain-blue session](../drafts/04_analysis/2026-10-07_104538-0400_human-tnfa-chain-blues_001/README.md)
uses A navy `#174A78`, B blue `#397FB7` and C light blue `#8BC6E8` cartoons
in all four saved scenes, following the final clarification that chain colors
must remain distinct. The interim uniform sky-blue session is historical. Whole-residue
hotspots remain green; ARG/LYS red, ASP/GLU blue and HIS magenta atom colors and
the existing scene-specific stick visibility are preserved. Mouse remains
copper/amber/sand. All four scenes were reopened and verified, with unchanged
atom identities, coordinates and bonds. This display-only successor preserves
the immutable Foundry input bundles and prior PSEs.

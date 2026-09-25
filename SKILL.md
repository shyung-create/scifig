---
name: scifig
description: Draft and spec-check a publication figure — mechanism schematic, workflow, experimental design, graphical abstract — against a named journal's requirements. Routes to BioRender when the figure needs real biological entities, otherwise writes vector SVG. Enforces a one-sentence purpose, a 3–5 element budget, single-axis revisions, and a script-run spec check before "done".
argument-hint: "[figure description]  (e.g. 'T cell killing a tumour cell, for Nature, double column')"
---

Figures fail review for structure and typography, not for prettiness. Work the gates in order; do not skip ahead because the first draft "looks fine".

## Gate 0 — Purpose

Write one sentence: what the reader must understand within five seconds of looking. Put it in the response. Do not draw anything until it exists. If the request is too vague to write that sentence, ask one question and stop.

Then fix the target: journal, column width, and figure type. Read `references/journal-specs.md`; a row whose **Verified** column is `—` must be confirmed against the journal's live author guide before you trust its numbers.

## Gate 0.5 — Backend route

- **BioRender** — the figure contains real biological entities: cells, organelles, receptors, animals, organs, tissue, lab instruments, anatomy. Hand-drawn SVG cells look amateurish; do not attempt them.
- **SVG** — the structure is abstract: experimental timelines, CONSORT and flow diagrams, decision trees, analysis pipelines, panel layout, anything whose "icons" are boxes.

Route by the figure, not by the machine. Check whether BioRender tools are present in this session; if the figure calls for BioRender and they are absent, say so, and either stop so the user can authorise the connector or proceed on the SVG backend with that limitation stated.

Mixed figures: build the biological part in BioRender and keep abstract annotation layers in BioRender too. Do not hand-edit a BioRender export — see Gate 4.

## Gate 1 — Element budget

The first draft carries **3–5 entities**. No exceptions, and the icon library makes this harder, not easier. List them explicitly before drawing. Additional elements are added one at a time in later turns, each justified by what the reader cannot understand without it.

State the reading axis (left→right for mechanisms, top→bottom for workflows) and hold every element on it.

Arrow semantics and palettes: `references/conventions.md`.

## Gate 2 — Single-axis revision

Each revision turn changes **structure, or labels, or style — never two**. Mixing them is what causes the figure to churn without converging. Announce which axis this turn is changing.

- **Structure only** — keep every label and colour exactly as-is; change element count, spacing, ordering, axis.
- **Labels only** — move and restyle nothing; change wording, delete text, move explanation to the legend.
- **Style only** — change no layout or wording; change colour, stroke weight, type size.

On the BioRender backend, all three happen in BioRender. The local file is output, not a working copy.

## Gate 3 — Spec check

Never eyeball this. Export SVG and run:

```
python scripts/check_svg.py FIGURE.svg --journal nature --column double --profile svg
```

Use `--profile biorender` for a BioRender export. Fix only the FAIL rows, one axis at a time per Gate 2. ADVISORY rows are judgement calls — report them to the user with a recommendation rather than silently acting.

The script cannot measure real glyph boxes, so its overlap check is an approximation. Text collision is the one thing that still needs human eyes.

## Gate 4 — Legend, licence, attribution

1. Explanation lives in the figure legend, not inside the figure. Hand back the legend as a separate paragraph.
2. **BioRender only:** confirm the account tier permits journal publication. A free account does not — publication needs a paid or institutional plan, which issues a publication licence. Confirm the attribution string is in the legend or acknowledgements, in BioRender's current required format (`references/conventions.md`; fetch and cache it if that section is still marked unverified).
3. Say plainly what you did not verify. Scientific accuracy — gene symbols, arrow direction, whether the mechanism matches the data — is the researcher's, not yours.

## Working notes

- `assets/canvas.svg` is a 1 unit = 1 mm skeleton with arrowhead and inhibition-bar markers. Start SVG figures from it.
- Never outline text to paths, never embed raster images, never reference an external font or stylesheet.
- On first BioRender use in a session, list the available tools and read their descriptions before calling one. Do not guess a tool name. Cache what you find in `references/biorender-tools.md`.
- BioRender is a cloud service: figure content leaves the machine. Flag that once if the work looks unpublished or sensitive.

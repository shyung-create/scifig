# Handoff — unfinished work

Written 2026-09-24 on the personal WSL laptop, where the BioRender MCP server is configured
(`https://mcp.services.biorender.com/mcp`, via the `bio-research` plugin) but **not
authenticated**. Everything BioRender-specific below was written against the design, never run.

Read this before extending the skill. Delete each item as you finish it.

## Why the BioRender parts look thin

By design. The tool surface of the BioRender MCP server was not visible from the machine that
built this, so nothing hard-codes a tool name. `SKILL.md` instructs discovery at runtime
instead. That is the correct design regardless — but it means the first real session has to do
the discovery once and write it down.

## Checklist for the work laptop

1. **Connect.** `/plugin install biorender@life-sciences` if absent, then `/mcp` in an
   interactive session to authorise. A corporate proxy may block the external HTTPS endpoint —
   find out now, not mid-figure. If blocked, the SVG backend still works; say so and move on.
2. **Cache the tool surface.** List the BioRender tools, read their descriptions, write them
   into `references/biorender-tools.md` — name, what it takes, what it returns, and anything
   surprising. Commit it.
3. **Attribution string.** `references/conventions.md` ends with an UNVERIFIED block. Fetch
   BioRender's current publication/licence requirement, paste the exact required attribution
   format in with the date you read it, delete the warning.
4. **Tune `--profile biorender`.** Export one real figure as SVG and run
   `python scripts/check_svg.py FIG.svg --journal <j> --column <c> --profile biorender`.
   The profile currently softens stroke weight, decoration, fonts and unit scale to ADVISORY
   and keeps raster content, type size, geometry, contrast and colour budget as FAIL. Real
   export will show whether that split is right. Two things to watch: whether BioRender emits
   labels as `<text>` or outlines them (if outlined, the type-size check is blind and the
   profile needs to say so loudly), and whether the export embeds raster `<image>` elements.
5. **Verify the journal rows.** Every row in `references/journal-specs.md` has `—` in its
   Verified column, meaning nobody has confirmed it. Confirm the journals you actually submit
   to against their live author guides and date the rows.
6. **Run the self-test after any change.** `python scripts/selftest.py` — 20 assertions, no
   dependencies, no network.

## Decisions already made, with reasons

- **Skill, not subagent.** The revision loop needs the user's eyes on each draft; a subagent's
  intermediate output never reaches them.
- **No rasterizer dependency.** The build machine has none (no rsvg-convert, inkscape,
  cairosvg, chromium). The text-overlap check is therefore a 0.6em-per-character approximation,
  labelled ADVISORY. BioRender exports at publication resolution server-side, so this only
  affects the pure-SVG path. `librsvg2-bin` would make it exact if that ever becomes worth a
  dependency.
- **Stdlib only, Python 3.9 syntax.** The build machine runs 3.14; the work laptop's version is
  unknown. Do not raise the floor without checking both.
- **Absolute units inside a scaled viewBox are reported, not modelled.** `7pt` inside
  `viewBox="0 0 183 90"` does not render at 7pt, and emulating the viewport resolution is not
  worth the code. The script tells you to convert to user units instead.

## Known gaps

- No `<tspan>`-relative font sizing beyond simple inheritance; `em`/`%` resolve only when the
  parent size is a plain number.
- Overlap detection skips any `<text>` carrying a `transform`.
- The colour census counts fills only, not strokes.
- No check that panel letters exist or are consistently placed — human judgement.

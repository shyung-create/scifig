# Drawing conventions

## Arrows and connectors

| Meaning | Mark |
|---|---|
| Activation, conversion, flow | solid line, filled arrowhead |
| Inhibition, blockade | solid line, blunt bar (⊣), no arrowhead |
| Translocation, movement | dashed line, filled arrowhead |
| Binding, physical contact | plain line, no head either end |
| Indirect / multi-step | solid line, open arrowhead, or a labelled break |

One visual grammar per figure. If activation is a filled head in panel A it is a filled head
in panel D. Label the arrow with a verb (`binds`, `phosphorylates`, `inhibits`), never with a
sentence.

## Colour

Two accent hues plus a neutral. More than that and the reader starts hunting for meaning that
is not there.

**Default pairing: `#0072B2` blue / `#E69F00` amber / `#4D4D4D` neutral grey on white.**
These two accents differ in relative luminance by 0.26, so they stay distinct in greyscale.

The conventional blue/red pairing (`#2166BD` / `#B2182B`) **collapses in greyscale** -- luminance
0.135 vs 0.103, a gap of 0.03. Both read as the same mid-grey in a black-and-white print or
photocopy. Use it only where the domain convention is worth the cost (immune blue / tumour red is
entrenched), and then only with a second cue carrying the same distinction. `check_svg.py` flags
this pair.

Okabe-Ito is the fallback when you need more than two:
`#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7`. Picking any two of these does not
guarantee luminance separation either -- check the pair, do not assume.

Amber `#E69F00` is a fill, never a text colour: at 2.3:1 on white it fails contrast.

**Every colour-coded distinction must also be carried by shape, position, or line style.**
Colour-only encoding fails for colour-blind readers and dies outright in greyscale print.
`check_svg.py` flags hue pairs that collapse to the same luminance, but it cannot tell whether
a second cue exists -- that check is yours.

No gradients, drop shadows, 3D bevels, glows, or decorative icons.

## Type and line weight

- Labels at the journal's recommended pt, not its minimum.
- One family, two sizes at most: labels, and bold panel letters one step up.
- Strokes ≥ 0.75 pt at final size. Anything thinner disappears in print.
- Sentence case for labels; keep gene and protein symbols in their correct official casing.

## Layout

- Declare one reading axis and keep every element on it.
- Margin ≥ 3 mm on all sides; ≥ 4 mm between adjacent shapes.
- Panel letters top-left of each panel, bold, consistent position across panels.
- Whitespace is not wasted space; crowding is the most common reason a schematic reads slowly.

## Legend

The figure carries entity names and arrow verbs. Everything else — abbreviation expansions,
conditions, n, statistics, species — goes in the legend. If a label needs a clause, it belongs
in the legend.

## BioRender attribution — UNVERIFIED

BioRender requires a **publication licence** for journal use; a free account does not grant one.
Published figures carry an attribution line, and journals increasingly ask for the agreement
number.

The exact required string is not recorded here because it has not been confirmed. Fetch it from
BioRender's own publication/licence help pages on first use, paste it in below with the date,
and delete this warning.

    (attribution format goes here — unverified)

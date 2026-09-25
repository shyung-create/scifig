# Journal figure specs

`scripts/check_svg.py` parses the table below — keep the column order and the `|` delimiters.
Use `—` for a value the journal does not state.

**A row whose `Verified` cell is `—` has not been confirmed against the live author guide.**
Confirm before trusting it, then write the ISO date and the URL you read into the row.
Publishers change these numbers; a stale row silently produces a wrong-width figure, which is
worse than having no table at all.

| Journal | Single (mm) | 1.5-col (mm) | Double (mm) | Max height (mm) | Min pt | Rec pt | Source | Verified |
|---|---|---|---|---|---|---|---|---|
| nature | 89 | 120 | 183 | 247 | 5 | 7 | nature.com/nature/for-authors/formatting-guide | — |
| science | 55 | 114 | 178 | — | 5 | 7 | science.org/content/page/instructions-preparing-initial-manuscript | — |
| cell | 85 | 114 | 174 | 235 | 5 | 7 | cell.com/cell/authors | — |
| pnas | 87 | 114 | 178 | 229 | 6 | 8 | pnas.org/author-center/submitting-your-manuscript | — |
| elife | 85 | 114 | 174 | 241 | 5 | 8 | reviewer.elifesciences.org/author-guide/full | — |
| plos-one | 83 | — | 173 | 233 | 8 | 10 | journals.plos.org/plosone/s/figures | — |
| default | 89 | 120 | 183 | 247 | 6 | 8 | conservative fallback, not a journal | — |

## Notes

- **Column choice is yours, not the tool's.** BioRender presets and this table both give you
  widths; neither tells you whether the figure earns a double-column slot.
- Height limits usually include the legend on the same page — leave headroom.
- `Min pt` is the absolute floor at final printed size. `Rec pt` is what to actually use;
  building at the floor leaves nothing for a copy-editor's rescale.
- Sans-serif throughout (Arial or Helvetica). Do not mix families across panels of one figure.

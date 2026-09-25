# scifig

A Claude Code skill for drafting and spec-checking publication figures.

Install by cloning into the skills directory:

```
git clone <this repo> ~/.claude/skills/scifig          # Linux / macOS / WSL
git clone <this repo> %USERPROFILE%\.claude\skills\scifig   # Windows
```

Then ask for a figure. The skill enforces a one-sentence purpose, a 3–5 element budget,
single-axis revisions, and a script-run spec check before calling anything finished.

Standalone use of the checker:

```
python scripts/check_svg.py FIGURE.svg --journal nature --column double --profile svg
python scripts/check_svg.py --list-journals
python scripts/selftest.py
```

Stdlib only, Python 3.9+. No network, no rasterizer.

`references/handoff.md` lists what is unfinished and why.

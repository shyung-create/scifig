#!/usr/bin/env python3
"""Offline check that check_svg.py's FAIL paths actually fire. Run: python scripts/selftest.py"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKER = os.path.join(HERE, "check_svg.py")
CANVAS = os.path.join(HERE, "..", "assets", "canvas.svg")

BAD = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="120mm" height="300mm" viewBox="0 0 120 300" font-family="Comic Sans MS">
  <defs><linearGradient id="g"><stop offset="0"/></linearGradient></defs>
  <rect x="0" y="0" width="120" height="300" fill="#FFFFFF"/>
  <image x="1" y="1" width="10" height="10" xlink:href="https://example.com/p.png"/>
  <text x="5" y="20" font-size="1.0" fill="#4D4D4D">too small</text>
  <text x="5" y="30" font-size="2.47" fill="#EEEEEE">low contrast</text>
  <text x="5" y="40" font-size="2.47" fill="#4D4D4D">overlapping label</text>
  <text x="8" y="40" font-size="2.47" fill="#4D4D4D">second one here</text>
  <line x1="5" y1="60" x2="60" y2="60" stroke="#4D4D4D" stroke-width="0.05"/>
  <circle cx="20" cy="80" r="5" fill="#0072B2"/>
  <circle cx="35" cy="80" r="5" fill="#E69F00"/>
  <circle cx="50" cy="80" r="5" fill="#009E73"/>
  <circle cx="65" cy="80" r="5" fill="#CC79A7"/>
  <circle cx="80" cy="80" r="5" fill="#D55E00"/>
</svg>
"""

NO_GEOMETRY = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400">
  <text x="5" y="20" font-size="12">no viewBox, no physical width</text>
</svg>
"""


def run(path, *extra):
    cmd = [sys.executable, CHECKER, path] + list(extra)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout


def rows(out):
    """-> {check: status} for the report lines."""
    found = {}
    for line in out.splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0] in ("PASS", "FAIL", "ADVISORY"):
            found.setdefault(parts[1].strip().split("  ")[0].strip(), parts[0])
    return found


def expect(condition, message):
    if not condition:
        print("FAILED: %s" % message)
        return 1
    print("  ok: %s" % message)
    return 0


def main():
    bad_count = 0
    tmp = tempfile.mkdtemp(prefix="scifig-selftest-")

    code, out = run(CANVAS, "--journal", "nature", "--column", "double")
    bad_count += expect(code == 0, "canvas.svg passes nature/double")
    bad_count += expect("0 FAIL" in out, "canvas.svg reports no FAIL rows")

    bad = os.path.join(tmp, "bad.svg")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write(BAD)
    code, out = run(bad, "--journal", "nature", "--column", "single")
    got = rows(out)
    bad_count += expect(code == 1, "bad.svg exits 1")
    for check in ("width", "height", "type size", "stroke weight", "raster content",
                  "external refs", "fonts", "decoration", "colour budget", "text contrast"):
        bad_count += expect(got.get(check) == "FAIL", "bad.svg FAILs on %r" % check)
    bad_count += expect(got.get("text overlap") == "ADVISORY",
                        "bad.svg flags overlapping labels")

    code, out = run(bad, "--journal", "nature", "--column", "single", "--profile", "biorender")
    got = rows(out)
    for check in ("stroke weight", "decoration", "fonts"):
        bad_count += expect(got.get(check) == "ADVISORY",
                            "biorender profile softens %r" % check)
    bad_count += expect(got.get("raster content") == "FAIL",
                        "biorender profile still FAILs raster content")
    bad_count += expect(got.get("type size") == "FAIL",
                        "biorender profile still FAILs type size")

    nogeo = os.path.join(tmp, "nogeo.svg")
    with open(nogeo, "w", encoding="utf-8") as fh:
        fh.write(NO_GEOMETRY)
    code, out = run(nogeo)
    bad_count += expect("FAIL      viewBox" in out, "missing viewBox is a FAIL")

    print("\n%s" % ("all checks passed" if bad_count == 0 else "%d check(s) failed" % bad_count))
    return 1 if bad_count else 0


if __name__ == "__main__":
    sys.exit(main())

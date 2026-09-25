#!/usr/bin/env python3
"""Spec-check an SVG figure against a journal's requirements.

Stdlib only, Python 3.9+. Prints a PASS / FAIL / ADVISORY table; exits 1 if anything FAILed.

Scope and honesty about it:

* Lengths written in user units (unitless, or `px`) are converted through the viewBox<->mm
  mapping, which is what `assets/canvas.svg` produces.
* Lengths written in absolute units (pt/mm/cm/in) *inside* a scaled viewBox do not render at
  their nominal size -- they are resolved against the viewport, then scaled. Rather than model
  that, the script reports them as an ADVISORY telling you to convert. Mixing absolute units
  into a scaled viewBox is a genuine footgun, so the advice stands on its own.
* Glyph boxes are approximated at 0.6em per character. The overlap check is advisory, +/-15%,
  and is not a substitute for looking at the figure.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
MM_PER_PT = 25.4 / 72.0
LEN_RE = re.compile(r"^\s*([+-]?(?:[0-9]*\.)?[0-9]+(?:[eE][+-]?[0-9]+)?)\s*([a-z%]*)\s*$")
HEX_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_RE = re.compile(r"^rgb\(\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*\)$", re.I)

ABS_UNIT_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": MM_PER_PT, "pc": 25.4 / 6.0}
WEBSAFE_FONTS = {"arial", "helvetica", "helvetica neue", "sans-serif",
                 "liberation sans", "nimbus sans", "arial, helvetica, sans-serif"}
NAMED_COLORS = {
    "black": (0, 0, 0), "white": (255, 255, 255), "grey": (128, 128, 128),
    "gray": (128, 128, 128), "red": (255, 0, 0), "green": (0, 128, 0),
    "blue": (0, 0, 255), "yellow": (255, 255, 0), "orange": (255, 165, 0),
    "purple": (128, 0, 128), "silver": (192, 192, 192), "navy": (0, 0, 128),
}
INHERITED = ("font-size", "stroke-width", "fill", "stroke", "font-family")

# --------------------------------------------------------------------------- parsing helpers


def tag(el):
    return el.tag.split("}")[-1] if "}" in el.tag else el.tag


def parse_length(value):
    """-> (number, unit) or (None, None). Unit '' means user units."""
    if value is None:
        return None, None
    m = LEN_RE.match(value)
    if not m:
        return None, None
    return float(m.group(1)), m.group(2)


def parse_color(value):
    """-> (r, g, b) or None for none/unparseable."""
    if not value:
        return None
    v = value.strip().lower()
    if v in ("none", "transparent", "inherit", "currentcolor"):
        return None
    if HEX_RE.match(v):
        h = v[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = RGB_RE.match(v)
    if m:
        return tuple(min(255, int(g)) for g in m.groups())
    return NAMED_COLORS.get(v)


def parse_style(el):
    out = {}
    raw = el.get("style")
    if raw:
        for part in raw.split(";"):
            if ":" in part:
                k, v = part.split(":", 1)
                out[k.strip().lower()] = v.strip()
    return out


def resolve_ctx(el, parent):
    """Presentation attributes, overridden by style=, inherited from parent."""
    ctx = dict(parent)
    style = parse_style(el)
    for key in INHERITED:
        val = style.get(key, el.get(key))
        if val is not None and val.strip().lower() != "inherit":
            ctx[key] = val.strip()
    return ctx


def relative_luminance(rgb):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b):
    la, lb = relative_luminance(a), relative_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def is_chromatic(rgb):
    return max(rgb) - min(rgb) > 20


def hexs(rgb):
    return "#%02X%02X%02X" % rgb

# --------------------------------------------------------------------------- spec table


def load_specs(path):
    specs = {}
    if not os.path.exists(path):
        return specs
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 9 or cells[0].lower() == "journal":
                continue
            if set(cells[0]) <= set("-: "):
                continue

            def num(cell):
                try:
                    return float(cell)
                except ValueError:
                    return None
            specs[cells[0].lower()] = {
                "single": num(cells[1]), "onehalf": num(cells[2]), "double": num(cells[3]),
                "max_height": num(cells[4]), "min_pt": num(cells[5]) or 5.0,
                "rec_pt": num(cells[6]), "source": cells[7], "verified": cells[8],
            }
    return specs

# --------------------------------------------------------------------------- report


class Report(object):
    def __init__(self):
        self.rows = []

    def add(self, status, check, detail):
        self.rows.append((status, check, detail))

    def fail(self, check, detail):
        self.add("FAIL", check, detail)

    def ok(self, check, detail=""):
        self.add("PASS", check, detail)

    def advise(self, check, detail):
        self.add("ADVISORY", check, detail)

    def soft(self, strict, check, detail):
        """FAIL when strict, ADVISORY otherwise."""
        self.add("FAIL" if strict else "ADVISORY", check, detail)

    def emit(self):
        width = max((len(r[1]) for r in self.rows), default=10)
        for status, check, detail in self.rows:
            print("%-9s %-*s  %s" % (status, width, check, detail))
        fails = sum(1 for r in self.rows if r[0] == "FAIL")
        advis = sum(1 for r in self.rows if r[0] == "ADVISORY")
        print("\n%d FAIL, %d ADVISORY, %d PASS"
              % (fails, advis, sum(1 for r in self.rows if r[0] == "PASS")))
        return fails

# --------------------------------------------------------------------------- checks


def walk(root):
    """Yield (element, resolved-context) depth-first."""
    base = {"font-size": None, "stroke-width": None, "fill": None,
            "stroke": None, "font-family": None}

    def rec(el, parent_ctx):
        ctx = resolve_ctx(el, parent_ctx)
        yield el, ctx
        for child in el:
            for pair in rec(child, ctx):
                yield pair
    return rec(root, base)


def text_content(el):
    return "".join(el.itertext()).strip()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Spec-check an SVG figure for a journal.")
    ap.add_argument("svg", nargs="?", help="path to the SVG file")
    ap.add_argument("--journal", default="default")
    ap.add_argument("--column", default="double", choices=("single", "onehalf", "double"))
    ap.add_argument("--profile", default="svg", choices=("svg", "biorender"))
    ap.add_argument("--colors", type=int, default=3,
                    help="budget of distinct chromatic hues (default 3)")
    ap.add_argument("--specs", default=os.path.join(here, "..", "references",
                                                    "journal-specs.md"))
    ap.add_argument("--list-journals", action="store_true")
    args = ap.parse_args()

    specs = load_specs(args.specs)
    if args.list_journals:
        for name in sorted(specs):
            print(name)
        return 0
    if not args.svg:
        ap.error("the following arguments are required: svg")

    spec = specs.get(args.journal.lower())
    rep = Report()
    if spec is None:
        rep.advise("journal", "%r not in %s -- geometry unchecked"
                   % (args.journal, os.path.normpath(args.specs)))
        spec = {"single": None, "onehalf": None, "double": None, "max_height": None,
                "min_pt": 5.0, "rec_pt": None, "source": "", "verified": "-"}
    elif spec["verified"] in ("-", "—", ""):
        rep.advise("journal", "%s row is UNVERIFIED -- confirm against %s before trusting it"
                   % (args.journal, spec["source"]))

    strict = args.profile == "svg"
    tree = ET.parse(args.svg)
    root = tree.getroot()

    # -- geometry -----------------------------------------------------------
    w_num, w_unit = parse_length(root.get("width"))
    h_num, h_unit = parse_length(root.get("height"))
    vb = root.get("viewBox")
    upmm = None
    width_mm = height_mm = None

    if w_num is not None and w_unit in ABS_UNIT_MM:
        width_mm = w_num * ABS_UNIT_MM[w_unit]
    if h_num is not None and h_unit in ABS_UNIT_MM:
        height_mm = h_num * ABS_UNIT_MM[h_unit]

    if not vb:
        rep.fail("viewBox", "missing -- the figure has no resolution-independent geometry")
    elif width_mm is None:
        rep.fail("width", "root width=%r is not in physical units; use mm"
                 % root.get("width"))
    else:
        parts = [p for p in re.split(r"[ ,]+", vb.strip()) if p]
        if len(parts) != 4:
            rep.fail("viewBox", "malformed: %r" % vb)
        else:
            upmm = float(parts[2]) / width_mm
            if abs(upmm - 1.0) < 0.01:
                rep.ok("unit scale", "1 user unit = 1 mm")
            else:
                rep.soft(strict, "unit scale",
                         "1 mm = %.3f user units; the skill's canvas uses 1:1" % upmm)

    target = spec[args.column]
    if width_mm is None:
        rep.advise("width", "not measurable without a physical root width")
    elif target is None:
        rep.advise("width", "%.1f mm (no %s target recorded for %s)"
                   % (width_mm, args.column, args.journal))
    elif abs(width_mm - target) <= 0.5:
        rep.ok("width", "%.1f mm matches %s %s-column" % (width_mm, args.journal, args.column))
    else:
        rep.fail("width", "%.1f mm, %s %s-column is %.1f mm"
                 % (width_mm, args.journal, args.column, target))

    if height_mm is not None and spec["max_height"]:
        if height_mm > spec["max_height"]:
            rep.fail("height", "%.1f mm exceeds %s max %.1f mm"
                     % (height_mm, args.journal, spec["max_height"]))
        else:
            rep.ok("height", "%.1f mm within %.1f mm" % (height_mm, spec["max_height"]))

    # -- traverse -----------------------------------------------------------
    texts = []            # (element, pt, content)
    abs_unit_hits = []
    strokes = []          # (pt, tag)
    fills = {}
    images = 0
    gradients = 0
    filters = 0
    external = []
    bad_fonts = set()
    page_bg = None

    for el, ctx in walk(root):
        name = tag(el)
        if name in ("linearGradient", "radialGradient"):
            gradients += 1
        elif name == "filter":
            filters += 1
        elif name == "image":
            images += 1
        elif name == "link":
            external.append("<link>")

        href = el.get("href") or el.get("{%s}href" % XLINK_NS)
        if href and href.startswith(("http://", "https://", "//")):
            external.append(href[:60])
        if name == "style" and "@import" in (el.text or ""):
            external.append("@import in <style>")

        fam = ctx.get("font-family")
        if fam and fam.strip().lower().strip("'\"") not in WEBSAFE_FONTS:
            bad_fonts.add(fam)

        if upmm:
            sw_num, sw_unit = parse_length(ctx.get("stroke-width"))
            if sw_num is not None and parse_color(ctx.get("stroke")):
                if sw_unit in ("", "px"):
                    strokes.append((sw_num / upmm / MM_PER_PT, name))
                elif sw_unit in ABS_UNIT_MM:
                    abs_unit_hits.append("stroke-width:%s" % ctx["stroke-width"])

        if name in ("text", "tspan") and text_content(el):
            fs_num, fs_unit = parse_length(ctx.get("font-size"))
            if fs_num is None:
                texts.append((el, None, text_content(el)))
            elif fs_unit in ("", "px"):
                if upmm:
                    texts.append((el, fs_num / upmm / MM_PER_PT, text_content(el)))
            elif fs_unit in ABS_UNIT_MM:
                abs_unit_hits.append("font-size:%s" % ctx["font-size"])
                texts.append((el, None, text_content(el)))

        f = parse_color(ctx.get("fill"))
        if f is not None and name not in ("svg", "g", "defs"):
            fills[f] = fills.get(f, 0) + 1
        if name == "rect" and page_bg is None and f is not None:
            rw, _ = parse_length(el.get("width"))
            if rw and upmm and width_mm and abs(rw - width_mm * upmm) < 1.0:
                page_bg = f

    if page_bg is None:
        page_bg = (255, 255, 255)

    # -- text ---------------------------------------------------------------
    if not texts:
        rep.fail("text as text", "no <text> elements -- labels are outlined or missing")
    else:
        rep.ok("text as text", "%d text elements" % len(texts))

    sized = [(pt, c) for _, pt, c in texts if pt is not None]
    if sized:
        too_small = sorted((pt, c) for pt, c in sized if pt < spec["min_pt"] - 0.05)
        if too_small:
            rep.fail("type size", "%d label(s) below %.1f pt: %s"
                     % (len(too_small), spec["min_pt"],
                        "; ".join("%.1fpt %r" % (pt, c[:24]) for pt, c in too_small[:5])))
        else:
            rep.ok("type size", "smallest %.1f pt (min %.1f)"
                   % (min(pt for pt, _ in sized), spec["min_pt"]))
        if spec["rec_pt"] and min(pt for pt, _ in sized) < spec["rec_pt"] - 0.05:
            rep.advise("type size", "below the %.1f pt recommendation; a rescale has no headroom"
                       % spec["rec_pt"])

    if abs_unit_hits:
        rep.advise("absolute units",
                   "%d use(s) inside a scaled viewBox render at viewport scale -- convert to "
                   "user units: %s" % (len(abs_unit_hits), ", ".join(sorted(set(abs_unit_hits))[:4])))

    # -- strokes ------------------------------------------------------------
    if strokes:
        thinnest, where = min(strokes)
        if thinnest < 0.75 - 0.01:
            rep.soft(strict, "stroke weight",
                     "thinnest %.2f pt on <%s>; below 0.75 pt vanishes in print" % (thinnest, where))
        else:
            rep.ok("stroke weight", "thinnest %.2f pt" % thinnest)

    # -- raster / external --------------------------------------------------
    if images:
        rep.fail("raster content", "%d <image> element(s) -- export is not fully vector" % images)
    else:
        rep.ok("raster content", "none")

    if external:
        rep.fail("external refs", "; ".join(sorted(set(external))[:4]))
    else:
        rep.ok("external refs", "none")

    if bad_fonts:
        rep.soft(strict, "fonts", "non-websafe: %s" % ", ".join(sorted(bad_fonts)[:3]))
    else:
        rep.ok("fonts", "websafe only")

    if gradients or filters:
        rep.soft(strict, "decoration",
                 "%d gradient(s), %d filter(s)" % (gradients, filters))
    else:
        rep.ok("decoration", "no gradients or filters")

    # -- colour -------------------------------------------------------------
    chromatic = [c for c in fills if is_chromatic(c)]
    if len(chromatic) > args.colors:
        rep.fail("colour budget", "%d chromatic fills (budget %d): %s"
                 % (len(chromatic), args.colors, " ".join(hexs(c) for c in chromatic[:6])))
    else:
        rep.ok("colour budget", "%d chromatic fill(s)" % len(chromatic))

    low = []
    for el, ctx in walk(root):
        if tag(el) in ("text", "tspan") and text_content(el):
            c = parse_color(ctx.get("fill")) or (0, 0, 0)
            ratio = contrast_ratio(c, page_bg)
            if ratio < 4.5:
                low.append((ratio, hexs(c), text_content(el)[:20]))
    if low:
        rep.fail("text contrast", "%d label(s) under 4.5:1 on %s: %s"
                 % (len(low), hexs(page_bg),
                    "; ".join("%.1f:1 %s %r" % r for r in sorted(low)[:4])))
    else:
        rep.ok("text contrast", "all labels >= 4.5:1 on %s" % hexs(page_bg))

    collapse = []
    for i, a in enumerate(chromatic):
        for b in chromatic[i + 1:]:
            d = abs(relative_luminance(a) - relative_luminance(b))
            if d < 0.15:
                collapse.append((d, hexs(a), hexs(b)))
    if collapse:
        rep.advise("greyscale",
                   "%s collapse to near-identical grey -- confirm shape or line style also "
                   "separates them" % "; ".join("%s/%s" % (a, b) for _, a, b in collapse[:3]))
    else:
        rep.ok("greyscale", "accent hues separate by luminance")

    # -- approximate overlap ------------------------------------------------
    boxes = []
    for el, ctx in walk(root):
        if tag(el) != "text" or not text_content(el) or el.get("transform"):
            continue
        x, xu = parse_length(el.get("x"))
        y, yu = parse_length(el.get("y"))
        fs, fsu = parse_length(ctx.get("font-size"))
        if None in (x, y, fs) or xu not in ("", "px") or fsu not in ("", "px"):
            continue
        content = text_content(el)
        w = len(content) * 0.6 * fs
        anchor = (ctx.get("text-anchor") or el.get("text-anchor") or "start").lower()
        x0 = x - w / 2 if anchor == "middle" else (x - w if anchor == "end" else x)
        boxes.append((x0, y - fs, x0 + w, y + fs * 0.25, content))
    hits = []
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                hits.append("%r/%r" % (a[4][:14], b[4][:14]))
    if hits:
        rep.advise("text overlap", "approx (+/-15%%), verify by eye: %s" % "; ".join(hits[:4]))
    else:
        rep.advise("text overlap", "none detected -- approximation only, verify by eye")

    fails = rep.emit()
    if args.profile == "biorender":
        print("profile=biorender: stroke weight, decoration, fonts and unit scale are advisory "
              "(icon libraries legitimately trip them).")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

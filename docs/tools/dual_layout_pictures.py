"""
dual_layout_pictures.py  -  the pictures and the combination sections of the wiki page Dual Layout, drawn from the
reference boards of the regression suite (regression/DualGenerator_regression).  For each of the 32 combinations of
what the dual layout is given, the picture is a cut along one radius of the reference board for that combination:
the copper is what the cut meets in the board's Stator.kicad_pcb, the radii and what was given come from its
record (Parameters.txt).  So every picture shows a board the generator really builds, and the regression tests,
which hold those boards byte for byte, keep it current.

    python docs/tools/dual_layout_pictures.py           write docs/images/dual_layout/combination_NN.svg and the
                                                         generated part of docs/wiki/Dual-Layout.md
    python docs/tools/dual_layout_pictures.py --check   only compare; exit 1 when a picture or the page is not what
                                                         the boards give (CI runs this check)

The reference board of combination n is the board folder named BoardNNN-layout-<n>-..., or Board001-default for
combination 1.  Standard library only.
"""

import argparse
import ast
import gzip
import math
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import svgfig as F                                                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BOARDS = os.path.join(REPO, "regression", "DualGenerator_regression")
IMAGES = os.path.join(REPO, "docs", "images", "dual_layout")
PAGE = os.path.join(REPO, "docs", "wiki", "Dual-Layout.md")
RAW = ("https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/"
       "dual_layout/")
BEGIN = "<!-- BEGIN: written by docs/tools/dual_layout_pictures.py from the reference boards; do not edit by hand -->"
END = "<!-- END: written by docs/tools/dual_layout_pictures.py -->"

BOARD_FILE = "Dual_Board_Parameters.py"
BAND_NAMES = ("INSIDE_RADIUS_MM", "OUTSIDE_RADIUS_MM", "RX_R_BASE_MM", "RX_A_MM")
BEFORE = {1: "DUAL_MODE 2", 7: "DUAL_MODE 4", 10: "DUAL_MODE 3", 18: "DUAL_MODE 3", 32: "DUAL_MODE 1"}
REFUSED = range(25, 31)
# the board edges the pictures of the refused rows show (the repository's default board)
EXAMPLE_EDGES = (7.25, 26.875)
# the generator's message for the refused rows (Dual_TrackLayout; a test of the Dual suite holds the two the same)
_BAND = "give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)"
_NONE = ("no RX band and no board edge is given: there is nothing to size the bands from. G" + _BAND[1:] + ", or both "
         "board edges (INNER_EDGE_RADIUS_MM and OUTER_EDGE_RADIUS_MM, Dual_Board_Parameters.py) to fit both bands "
         "between them")
_ONE = ("no RX band is given and of the board edges only the {given}: {missing} is missing to fit both bands between the "
        "edges. Set {missing} (Dual_Board_Parameters.py), or " + _BAND)
REFUSAL = {25: _NONE, 26: _NONE,
           27: _ONE.format(given="bore", missing="OUTER_EDGE_RADIUS_MM"),
           28: _ONE.format(given="bore", missing="OUTER_EDGE_RADIUS_MM"),
           29: _ONE.format(given="outline", missing="INNER_EDGE_RADIUS_MM"),
           30: _ONE.format(given="outline", missing="INNER_EDGE_RADIUS_MM")}

# colours: the KiCad-EM-Stackup-Exporter wiki's
COPPER, LAMINATE, AIR = "#cd803e", "#968a58", "#d5dce5"
BLUE, RED = "#1d5fa6", "#c62828"
W, M = 1400, 24


# ------------------------------------------------------------------------------------------------- the combinations
def given_of(n):
    """What combination n gives: dict(band1, band2, bore, outline, gap) of booleans."""
    group, rest = divmod(n - 1, 8)
    return dict(band1=group in (0, 1), band2=group in (0, 2), bore=bool(rest & 2), outline=bool(rest & 4),
                gap=bool(rest & 1))


def number(g):
    """The combination number of what is given (the inverse of given_of)."""
    group = 0 if g["band1"] and g["band2"] else 1 if g["band1"] else 2 if g["band2"] else 3
    return 8 * group + 4 * g["outline"] + 2 * g["bore"] + g["gap"] + 1


def title_of(n):
    g = given_of(n)
    parts = [w for w, k in (("RX1 band", "band1"), ("RX2 band", "band2"), ("bore", "bore"), ("outline", "outline"),
                            ("TRACK_GAP_MM", "gap")) if g[k]]
    if g["band1"] and g["band2"]:
        parts = ["both RX bands"] + parts[2:]
    if not parts:
        return "nothing given"
    words = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return words[0].upper() + words[1:] + " given"


def explanation(n):
    """What the generator does with combination n, in full."""
    g = given_of(n)
    gap = "TRACK_GAP_MM" if g["gap"] else "MIN_CLEARANCE_MM (TRACK_GAP_MM is None)"
    if n in REFUSED:
        if not g["bore"] and not g["outline"]:
            return ("Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX "
                    "band, or both board edges to fit both bands between them." +
                    (" TRACK_GAP_MM alone does not help: it is a distance, not a place." if g["gap"] else ""))
        missing, have = ("OUTER_EDGE_RADIUS_MM", "the bore") if g["bore"] else ("INNER_EDGE_RADIUS_MM", "the outline")
        return (f"Refused: no RX band and only {have}, so the room for the two bands has no other end. Give "
                f"{missing} too, and the bands are fitted between the edges, or give one RX band.")
    bore = ("The bore is used as given; the Single Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 "
            "band." if g["bore"] else "The bore is the RX1 band start less INNER_EDGE_INSET_MM.")
    outline = ("The outline is used as given; the Single Generator checks that it leaves room for the TX2 ring, its "
               "tail or fingers, and the margins." if g["outline"] else
               "The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.")
    if g["band1"] and g["band2"]:
        return (f"Both bands are used as given. {bore} {outline} The gap between set 1's outermost copper and set 2's "
                f"innermost copper is measured, and must be at least {gap}.")
    if g["band1"]:
        end = ("runs out to the outline, less the TX2 ring and the margins" if g["outline"] else
               "is as wide as the RX1 band")
        return (f"The RX2 band is placed so that set 2's innermost copper (its inner vias) sits {gap} out from set 1's "
                f"outermost copper (its TX ring, tail or fingers), and {end}. {bore} {outline}")
    if g["band2"]:
        start = ("starts at the bore plus INNER_EDGE_INSET_MM" if g["bore"] else "is as wide as the RX2 band")
        return (f"The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits {gap} "
                f"inside set 2's innermost copper (its inner vias), and {start}. {bore} {outline}")
    return (f"Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, "
            f"the TX1 ring, {gap}, set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the "
            f"outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths).")


# ------------------------------------------------------------------------------------------------- reading a board
def _literal(src):
    try:
        return ast.literal_eval(src)
    except (ValueError, SyntaxError):
        return src


def _floats(pattern, text, what):
    m = re.search(pattern, text)
    if m is None:
        raise ValueError(f"the record has no {what}")
    return tuple(float(v) for v in m.groups())


def read_record(path):
    """The values used, what was given and the radii the generator chose, from a board's Parameters.txt."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    values, file = {}, None
    for line in text.split("PARAMETER VALUES USED", 1)[1].split("THE TWO SETS AS HANDED", 1)[0].splitlines():
        m = re.match(r"\[(\S+\.py)\]$", line.strip())
        if m:
            file = m.group(1)
            values[file] = {}
            continue
        m = re.match(r"  ([A-Z][A-Z0-9_]*)\s+= (.*)$", line)
        if m and file:
            values[file][m.group(1)] = _literal(m.group(2))
    layout = text.split("LAYOUT (what the generator computed)", 1)[1].split("\nSTATOR", 1)[0]
    board = values[BOARD_FILE]
    rx = {k: values[f"Dual_RX{k}_Parameters.py"] for k in (1, 2)}
    g = dict(band1=any(rx[1].get(nm) is not None for nm in BAND_NAMES),
             band2=any(rx[2].get(nm) is not None for nm in BAND_NAMES),
             bore=board.get("INNER_EDGE_RADIUS_MM") is not None, outline=board.get("OUTER_EDGE_RADIUS_MM") is not None,
             gap=board.get("TRACK_GAP_MM") is not None)
    clearance = max(v for v in [board.get("MIN_CLEARANCE_MM")] + [rx[k].get("MIN_CLEARANCE_MM") for k in (1, 2)]
                    if v is not None)
    rec = dict(values=values, given=g, combination=number(g),
               band1=_floats(r"RX1 band r = ([\d.]+) \.\.\. ([\d.]+) mm", layout, "RX1 band"),
               band2=_floats(r"RX2 band r = ([\d.]+) \.\.\. ([\d.]+) mm", layout, "RX2 band"),
               edges=_floats(r"bore r = ([\d.]+) mm .*outline r = ([\d.]+) mm", layout, "edges"),
               copper=_floats(r"set 1 copper reaches r = ([\d.]+) mm; set 2 copper starts at r = ([\d.]+) mm", layout,
                              "gap"),
               gap_required=float(board["TRACK_GAP_MM"]) if g["gap"] else float(clearance),
               gap_name="TRACK_GAP_MM" if g["gap"] else "MIN_CLEARANCE_MM",
               thickness=float(board.get("PCB_THICKNESS_MM") or 1.6),
               prepreg=float(board.get("STACKUP_PREPREG_MM") or 0.2),
               terminals=(float(board.get("TERMINAL_1_DEG", 0.0)), float(board.get("TERMINAL_2_DEG", 0.0))),
               nets={k: {"rx": (rx[k].get("RX_NET_PHASE_0_2"), rx[k].get("RX_NET_PHASE_1_3")),
                         "tx": values[f"Dual_TX{k}_Parameters.py"].get("TX_NET")} for k in (1, 2)})
    m = re.search(r"\(combination (\d+) of 32\)", layout)
    if m and int(m.group(1)) != rec["combination"]:
        raise ValueError(f"{path}: the record says combination {m.group(1)}, its values give {rec['combination']}")
    return rec


_SEG = re.compile(r'\(segment \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(width ([\d.]+)\) '
                  r'\(layer "([^"]+)"\) \(net (\d+)\)\)')
_VIA = re.compile(r'\(via (?:\w+ )?\(at ([-\d.]+) ([-\d.]+)\) \(size ([\d.]+)\) \(drill [\d.]+\) '
                  r'\(layers "([^"]+)" "([^"]+)"\) \(net (\d+)\)\)')
_NET = re.compile(r'^\s*\(net (\d+) "([^"]*)"\)', re.M)
_EDGE = re.compile(r'\(gr_circle \(center ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(layer "Edge.Cuts"\)')
_LAYER = re.compile(r'\(\d+ "([^"]+\.Cu)" signal\)')


def read_stator(path):
    """The copper of a stator file the generator wrote: layers (top to bottom), nets, segments, vias, centre."""
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        text = fh.read()
    edges = [tuple(float(v) for v in m.groups()) for m in _EDGE.finditer(text)]
    if not edges:
        raise ValueError(f"{path}: no Edge.Cuts circle")
    return dict(layers=_LAYER.findall(text), nets={int(a): b for a, b in _NET.findall(text)},
                centre=edges[0][:2],
                segments=[(float(a), float(b), float(c), float(d), float(w), lay, int(net))
                          for a, b, c, d, w, lay, net in _SEG.findall(text)],
                vias=[(float(x), float(y), float(s), l1, l2, int(net)) for x, y, s, l1, l2, net in _VIA.findall(text)])


# ------------------------------------------------------------------------------------------------- the cut
def _disk(cx, cy, h, dx, dy):
    """The t interval of the line t * (dx, dy) inside the disk at (cx, cy), radius h, or None."""
    b = dx * cx + dy * cy
    disc = b * b - (cx * cx + cy * cy) + h * h
    if disc < 0:
        return None
    s = math.sqrt(disc)
    return (b - s, b + s)


def _capsule(ax, ay, bx, by, h, dx, dy):
    """The t interval of the line t * (dx, dy) inside a track from A to B, half width h (round ends), or None."""
    parts = [_disk(ax, ay, h, dx, dy), _disk(bx, by, h, dx, dy)]
    ln = math.hypot(bx - ax, by - ay)
    if ln > 0:
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        lo, hi = -math.inf, math.inf
        for coef, off, a, b in ((dx * ux + dy * uy, ax * ux + ay * uy, 0.0, ln),
                                (-dx * uy + dy * ux, -ax * uy + ay * ux, -h, h)):
            # coef * t - off must lie in [a, b]
            if abs(coef) < 1e-12:
                if not a <= -off <= b:
                    lo, hi = 1.0, 0.0
                continue
            t1, t2 = (a + off) / coef, (b + off) / coef
            lo, hi = max(lo, min(t1, t2)), min(hi, max(t1, t2))
        if lo <= hi:
            parts.append((lo, hi))
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    return (min(p[0] for p in parts), max(p[1] for p in parts))


def cut(stator, deg):
    """What a cut along the radius at `deg` meets: {layer: [(r0, r1, net name)]}, the pieces of one net merged."""
    cx, cy = stator["centre"]
    dx, dy = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    raw = {lay: [] for lay in stator["layers"]}
    for ax, ay, bx, by, w, lay, net in stator["segments"]:
        ax, ay, bx, by = ax - cx, ay - cy, bx - cx, by - cy
        # skip quickly what lies far from the ray's line or behind the centre
        if (ax * dx + ay * dy) < -w and (bx * dx + by * dy) < -w:
            continue
        da, db = -ax * dy + ay * dx, -bx * dy + by * dx
        if (da > w and db > w) or (da < -w and db < -w):
            continue
        iv = _capsule(ax, ay, bx, by, w / 2.0, dx, dy)
        if iv is not None and iv[1] > 0 and lay in raw:
            raw[lay].append((max(iv[0], 0.0), iv[1], stator["nets"].get(net, "")))
    order = stator["layers"]
    for x, y, size, l1, l2, net in stator["vias"]:
        iv = _disk(x - cx, y - cy, size / 2.0, dx, dy)
        if iv is None or iv[1] <= 0:
            continue
        i1, i2 = sorted((order.index(l1), order.index(l2)))
        for lay in order[i1:i2 + 1]:
            raw[lay].append((max(iv[0], 0.0), iv[1], stator["nets"].get(net, "")))
    out = {}
    for lay, pieces in raw.items():
        merged = []
        for r0, r1, net in sorted(pieces):
            if merged and merged[-1][2] == net and r0 <= merged[-1][1] + 1e-6:
                merged[-1] = (merged[-1][0], max(merged[-1][1], r1), net)
            else:
                merged.append((r0, r1, net))
        out[lay] = merged
    return out


def cut_angle(terminals):
    """The cut runs where it is farthest from both TX terminals (the leads and the exits): the 5 deg step with the
    largest distance to the nearer terminal, the smallest such angle when several tie."""
    def dist(a, b):
        d = abs(a - b) % 360.0
        return min(d, 360.0 - d)
    return max(range(0, 360, 5), key=lambda a: (min(dist(a, t) for t in terminals), -a))


# ------------------------------------------------------------------------------------------------- drawing
def f2(v):
    return f"{v:.3f}".rstrip("0").rstrip(".")


class Panel:
    """The cut through the board: the radius runs left to right (true scale), the board's thickness top to bottom."""

    def __init__(self, fig, r_min, r_max, rows=3):
        self.fig = fig
        self.x0, self.y0, self.pw = M, fig.y, W - 2 * M
        self.px0, self.px1 = self.x0 + 104, self.x0 + self.pw - 30
        self.r_min, self.r_max = r_min, r_max
        self.s = (self.px1 - self.px0) / (r_max - r_min)
        self.rows = [self.y0 + 92 + 60 * i for i in range(rows)]
        self.labels = {i: [] for i in range(rows)}
        self.xc = self.x0 + 34                         # the board centre, drawn left of a break in the axis

    def X(self, r):
        return self.px0 + (r - self.r_min) * self.s

    def place(self, row, cx, w):
        """The left x of a label box of width w wanted at cx in a row, kept off the row's other labels."""
        x = min(max(cx - w / 2.0, self.x0 + 8), self.x0 + self.pw - 8 - w)
        for a, b in sorted(self.labels[row]):
            if x < b + 8 and x + w > a - 8:
                x = b + 8
        x = min(x, self.x0 + self.pw - 8 - w)
        self.labels[row].append((x, x + w))
        return x

    def dimension(self, row, r0, r1, label, colour, x0=None):
        """A dimension line in `row` from r0 to r1 (x0: a pixel start instead of r0) with its value in a box."""
        fig, y = self.fig, self.rows[row]
        a, b = (self.X(r0) if x0 is None else x0), self.X(r1)
        fig.line(a, y, b, y, colour, 1.2)
        for x in (a, b):
            fig.line(x, y - 6, x, y + 6, colour, 1.2)
        w = F.text_width(label, 13) + 14
        bx = self.place(row, (a + b) / 2.0, w)
        if bx > max(a, b) or bx + w < min(a, b) or b - a < 6:
            fig.line(bx + w / 2.0, y - 8, (a + b) / 2.0, y, colour, 0.9, dash="3 2")
        fig.rect(bx, y - 30, w, 21, "#ffffff", BOX_EDGE_FOR[colour], 1.0, rx=3)
        fig.text(bx + w / 2.0, y - 15, label, 13, colour, anchor="middle")
        self.guides.update(x for x in (a, b) if x0 is None or x != x0)

    def marker(self, row, r, label, colour):
        """A board edge: its value in a box over the edge's line."""
        fig, y, x = self.fig, self.rows[row], self.X(r)
        w = F.text_width(label, 13) + 14
        bx = self.place(row, x, w)
        fig.line(x, y - 9, x, y + 6, colour, 1.2)
        fig.rect(bx, y - 30, w, 21, "#ffffff", BOX_EDGE_FOR[colour], 1.0, rx=3)
        fig.text(bx + w / 2.0, y - 15, label, 13, colour, anchor="middle")


BOX_EDGE_FOR = {F.INK: F.BOX_EDGE, BLUE: "#9db7d6", RED: RED}


def spread(boxes, lo, hi, pad=10):
    """Moves boxes [left, width, ...] (in order) apart so that none overlaps the next, all within lo ... hi."""
    for i, b in enumerate(boxes):
        b[0] = max(b[0], lo if i == 0 else boxes[i - 1][0] + boxes[i - 1][1] + pad)
    for i in range(len(boxes) - 1, -1, -1):
        b = boxes[i]
        b[0] = min(b[0], hi - b[1] if i == len(boxes) - 1 else boxes[i + 1][0] - pad - b[1])


def frame(fig, top, bottom, badge):
    fig.items.insert(0, "")                            # keeps the ordering stable for the frame drawn below
    fig.items[0] = (f'<rect x="{F.n(M)}" y="{F.n(top)}" width="{F.n(W - 2 * M)}" height="{F.n(bottom - top)}" '
                    f'fill="{AIR}" stroke="{F.FRAME}" stroke-width="1"/>')
    fig.badge(M + 22, top + 22, badge)


def legend(fig, panel):
    x, y = panel.x0 + panel.pw - 610, panel.y0 + 14
    fig.rect(x, y, 596, 30, "#ffffff", F.BOX_EDGE, 1.0, rx=3)
    fig.line(x + 12, y + 15, x + 42, y + 15, F.INK, 2.0)
    fig.text(x + 50, y + 20, "given in the parameter files", 13, F.INK)
    fig.line(x + 290, y + 15, x + 320, y + 15, BLUE, 2.0)
    fig.text(x + 328, y + 20, "placed or worked out by the generator", 13, BLUE)


def axis(fig, panel, y):
    """The radius axis under the board, with the break to the board centre."""
    fig.line(panel.xc, y, panel.px0 - 18, y, F.INK, 1.0, dash="4 3")
    fig.line(panel.px0 - 18, y - 7, panel.px0 - 24, y + 7, F.INK, 1.2)
    fig.line(panel.px0 - 12, y - 7, panel.px0 - 18, y + 7, F.INK, 1.2)
    fig.line(panel.px0 - 12, y, panel.px1, y, F.INK, 1.0)
    fig.line(panel.xc, y - 7, panel.xc, y + 7, F.INK, 1.4)
    fig.text(panel.xc, y + 22, "centre", 13, F.INK, anchor="middle")
    step = 5 if panel.r_max - panel.r_min > 12 else 1
    r = math.ceil(panel.r_min)
    while r <= panel.r_max:
        x = panel.X(r)
        major = r % step == 0
        fig.line(x, y, x, y + (8 if major else 4), F.INK, 1.0)
        if major:
            fig.text(x, y + 22, f"{r} mm", 13, F.INK, anchor="middle")
        r += 1
    fig.text(panel.px1, y - 8, "radius from the board centre (true scale)", 13, F.GREY, anchor="end")


def layer_z(layers, thickness, prepreg):
    """The depth of each copper layer below the top surface (mm)."""
    inner = layers[1:-1]
    z = {layers[0]: 0.0, layers[-1]: thickness}
    if len(inner) == 2:
        z[inner[0]], z[inner[1]] = prepreg, thickness - prepreg
    else:
        for i, lay in enumerate(inner):
            z[lay] = thickness * (i + 1) / (len(inner) + 1)
    return z


def part_of(net, nets):
    for k in (1, 2):
        if net == nets[k]["tx"]:
            return f"TX{k}"
        if net in nets[k]["rx"]:
            return f"RX{k}"
    return None


LAYER_WORDS = {"F.Cu": "Top", "B.Cu": "Bottom", "In1.Cu": "Inner 1", "In2.Cu": "Inner 2"}


def board_picture(n, name, rec, stator):
    g = rec["given"]
    bore, outline = rec["edges"]
    (ri1, ro1), (ri2, ro2) = rec["band1"], rec["band2"]
    reach1, inner2 = rec["copper"]
    deg = cut_angle(rec["terminals"])
    pieces = cut(stator, deg)
    fig = F.Figure(W, f"Combination {n}: {title_of(n)}")
    given_words = []
    for k, key in ((1, "band1"), (2, "band2")):
        if g[key]:
            given_words.append(f"the RX{k} band ({f2(rec[key][0])} ... {f2(rec[key][1])} mm, Dual_RX{k})")
    for key, word in (("bore", "the bore"), ("outline", "the outline")):
        if g[key]:
            given_words.append(f"{word} ({f2(rec['edges'][0 if key == 'bore' else 1])} mm)")
    if g["gap"]:
        given_words.append(f"TRACK_GAP_MM ({f2(rec['gap_required'])} mm)")
    fig.title(f"Combination {n}: {title_of(n)}",
              f"Drawn from the reference board {name} (regression/DualGenerator_regression), cut along the radius at "
              f"{deg} deg: the copper is what that cut meets in its Stator.kicad_pcb. Given: "
              + (", ".join(given_words) if given_words else "nothing") + ". Across the board true scale; through the "
              "board not to scale, the copper drawn thicker.")
    top = fig.y
    panel = Panel(fig, bore - 1.6, outline + 1.2)
    panel.guides = set()
    legend(fig, panel)
    ink = lambda given: F.INK if given else BLUE
    # ---- row 0: the bands
    for k, key, (ri, ro) in ((1, "band1", (ri1, ro1)), (2, "band2", (ri2, ro2))):
        panel.dimension(0, ri, ro, f"RX{k} band {f2(ri)} ... {f2(ro)} mm, " + ("given" if g[key] else "placed"),
                        ink(g[key]))
    # ---- row 1: the edges and the gap
    panel.marker(1, bore, f"bore r = {f2(bore)} mm" + (", given" if g["bore"] else ", from RX1"), ink(g["bore"]))
    gap = inner2 - reach1
    panel.dimension(1, reach1, inner2, f"gap {f2(round(gap, 3))} mm" + (f" = {rec['gap_name']}" if
                    not (g["band1"] and g["band2"]) else f", at least {rec['gap_name']} {f2(rec['gap_required'])}"),
                    ink(g["gap"]) if not (g["band1"] and g["band2"]) else BLUE)
    panel.marker(1, outline, f"outline r = {f2(outline)} mm" + (", given" if g["outline"] else ", from RX2"),
                 ink(g["outline"]))
    # ---- row 2: the spacings that follow from the sets' own settings
    panel.dimension(2, bore, ri1, f"inset {f2(round(ri1 - bore, 3))}", BLUE)
    panel.dimension(2, ro1, reach1, f"set 1 copper past RX1: {f2(round(reach1 - ro1, 3))}", BLUE)
    panel.dimension(2, ro2, outline, f"TX2 ring and margins: {f2(round(outline - ro2, 3))}", BLUE)

    # ---- the board
    layers = stator["layers"]
    thick = 150.0                                   # through the board not to scale: the layers' order and spacing
    vs = thick / rec["thickness"]
    yb = panel.rows[-1] + 44
    ct = 8.0
    z = layer_z(layers, rec["thickness"], rec["prepreg"])
    for x in sorted(panel.guides):
        fig.line(x, panel.rows[0] + 6, x, yb - ct - 2, "#8a96a3", 0.7, dash="3 3")
    fig.rect(panel.X(bore), yb, panel.X(outline) - panel.X(bore), thick, LAMINATE)
    targets = {}
    for lay in layers:
        if lay == layers[0]:
            y = yb - ct
        elif lay == layers[-1]:
            y = yb + thick
        else:
            y = yb + z[lay] * vs - ct / 2.0
        for r0, r1, net in pieces.get(lay, []):
            x0, x1 = panel.X(r0), panel.X(r1)
            fig.rect(x0, y, max(x1 - x0, 1.0), ct, COPPER)
            part = part_of(net, rec["nets"])
            if part is not None:
                targets.setdefault(part, {}).setdefault(lay, []).append(((x0 + x1) / 2.0, y + ct))
    fig.text(panel.X(bore) + 8, yb + thick - 10, "laminate", 13, "#f4f1e6")
    set_labels = (("set 1 (inner)", bore, reach1), ("set 2 (outer)", inner2, outline))
    for edge in (bore, outline):
        fig.line(panel.X(edge), panel.rows[1] + 6, panel.X(edge), yb + thick + ct + 10, F.INK, 1.0, dash="6 3")
    # ---- what the copper is
    yc = yb + thick + ct + 34
    calls = []
    for part in ("RX1", "TX1", "RX2", "TX2"):
        if part not in targets:
            continue
        by_layer = targets[part]
        lays = [lay for lay in layers if lay in by_layer]
        tx, ty = by_layer[lays[-1]][len(by_layer[lays[-1]]) // 2]
        names = [LAYER_WORDS.get(x, x) for x in lays]
        where = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        label = f"{part} " + ("coil traces" if part.startswith("RX") else "turns") + f" on {where}"
        calls.append([tx - (F.text_width(label, 13) + 16) / 2.0, F.text_width(label, 13) + 16, tx, ty, label])
    spread(calls, panel.x0 + 8, panel.x0 + panel.pw - 8)
    leaders = [tx for _bx, _w, tx, _ty, _label in calls]
    for word, a, b in set_labels:                 # inside the laminate, clear of the leaders that cross it
        w = F.text_width(word, 16, bold=True)
        lo, hi = panel.X(a) + 8, panel.X(b) - 8 - w
        for x in ((lo + hi) / 2.0, lo, hi, (lo + (lo + hi) / 2.0) / 2.0, (hi + (lo + hi) / 2.0) / 2.0):
            if not any(x - 6 <= t <= x + w + 6 for t in leaders):
                break
        fig.text(x, yb + thick / 2.0 + 6, word, 16, "#f4f1e6", bold=True)
    for bx, w, tx, ty, label in calls:
        fig.line(min(max(tx, bx + 6), bx + w - 6), yc, tx, ty + 1, F.INK, 0.9)
        fig.circle(tx, ty + 1, 2.6)
        fig.box(bx, yc, [label])
    ya = yc + 64
    axis(fig, panel, ya)
    bottom = ya + 34
    frame(fig, top, bottom, 1)
    fig.y = bottom
    built = (f"Here the RX1 band runs {f2(ri1)} ... {f2(ro1)} mm and the RX2 band {f2(ri2)} ... {f2(ro2)} mm; set 1's "
             f"copper reaches r = {f2(reach1)} mm and set 2's starts at r = {f2(inner2)} mm, {f2(round(gap, 3))} mm "
             f"apart; the bore is {f2(bore)} mm and the outline {f2(outline)} mm.")
    fig.caption(M, W - 2 * M, f"1  {title_of(n)}", explanation(n) + " " + built)
    return fig.svg()


def refused_picture(n):
    g = given_of(n)
    bore, outline = EXAMPLE_EDGES
    fig = F.Figure(W, f"Combination {n}: {title_of(n)}")
    fig.title(f"Combination {n}: {title_of(n)}",
              "Refused: nothing is built, so this picture shows only what is given, at the radii of the repository's "
              "default board, and the message the generator stops with at the parameter check.")
    top = fig.y
    panel = Panel(fig, bore - 1.6, outline + 1.2, rows=2)
    panel.guides = set()
    legend(fig, panel)
    yb = panel.rows[-1] + 44
    thick = 120.0
    a = panel.X(bore) if g["bore"] else panel.px0
    b = panel.X(outline) if g["outline"] else panel.px1
    fig.rect(a, yb, b - a, thick, "#ffffff", "#8a96a3", 1.2, dash="6 4")
    for key, r, word in (("bore", bore, "bore"), ("outline", outline, "outline")):
        if g[key]:
            panel.marker(1, r, f"{word} r = {f2(r)} mm, given", F.INK)
            fig.line(panel.X(r), panel.rows[1] + 6, panel.X(r), yb + thick + 10, F.INK, 1.2, dash="6 3")
    if g["gap"]:
        panel.dimension(0, (bore + outline) / 2.0 - 0.25, (bore + outline) / 2.0 + 0.25, "TRACK_GAP_MM given, "
                        "but between what?", F.INK)
    lines = F.wrap("ERROR  " + REFUSAL[n], 14, 760)
    w = max(F.text_width(x, 14) for x in lines) + 16
    fig.box((a + b) / 2.0 - w / 2.0, yb + 16, lines, size=14, edge=RED)
    ya = yb + thick + 48
    axis(fig, panel, ya)
    bottom = ya + 34
    frame(fig, top, bottom, 1)
    fig.y = bottom
    fig.caption(M, W - 2 * M, f"1  {title_of(n)}: refused", explanation(n))
    return fig.svg()


# ------------------------------------------------------------------------------------------------- the page
def reference_boards():
    """{combination: board folder name} of the reference boards in regression/DualGenerator_regression."""
    out = {}
    for name in sorted(os.listdir(BOARDS)):
        m = re.match(r"Board\d{3}-layout-(\d+)-", name)
        if m:
            out.setdefault(int(m.group(1)), name)
    if os.path.isdir(os.path.join(BOARDS, "Board001-default")):
        out.setdefault(1, "Board001-default")
    return out


def cell(v):
    return "given" if v else "–"


def heading(n):
    """The section heading of combination n on the page (chapter 34.3 of the wiki)."""
    words = " ".join(w if w.isupper() or "_" in w else w[0].upper() + w[1:] for w in title_of(n).split())
    return f"34.3.{n} Combination {n}: {words}"


def anchor(text):
    """GitHub's anchor for a heading."""
    return re.sub(r"[^a-z0-9 _-]", "", text.lower()).replace(" ", "-")


def page_block(records):
    """The generated part of Dual-Layout.md: the table and one section per combination."""
    out = [BEGIN, "", "| # | RX1 band | RX2 band | Bore | Outline | `TRACK_GAP_MM` | What the generator does | Before |",
           "|---|---|---|---|---|---|---|---|"]
    for n in range(1, 33):
        g = given_of(n)
        out.append(f"| [{n}](#{anchor(heading(n))}) | {cell(g['band1'])} | {cell(g['band2'])} | {cell(g['bore'])} | "
                   f"{cell(g['outline'])} | {cell(g['gap'])} | {explanation(n)} | {BEFORE.get(n, 'refused')} |")
    out.append("")
    for n in range(1, 33):
        alt = f"Combination {n}: {title_of(n)}. {explanation(n)}"
        out += [f"### {heading(n)}", "", explanation(n), "", f"![{alt}]({RAW}combination_{n:02d}.svg)", ""]
        if n in records:
            name, rec = records[n]
            (ri1, ro1), (ri2, ro2), (bore, outline) = rec["band1"], rec["band2"], rec["edges"]
            how = {k: "given" if v else "placed" if k.startswith("band") else "from the band"
                   for k, v in rec["given"].items()}
            out += ["| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |",
                    "|---|---|---|---|---|---|",
                    f"| `{name}` | {f2(ri1)} ... {f2(ro1)} mm, {how['band1']} | {f2(ri2)} ... {f2(ro2)} mm, "
                    f"{how['band2']} | {f2(bore)} mm, {how['bore']} | {f2(outline)} mm, {how['outline']} | "
                    f"{f2(round(rec['copper'][1] - rec['copper'][0], 3))} mm (at least {rec['gap_name']} "
                    f"{f2(rec['gap_required'])}) |", ""]
        else:
            out += ["```text", f"ERROR   {REFUSAL[n]}", "```", ""]
    out.append(END)
    return "\n".join(out) + "\n"


def build():
    """{path: text} of everything this script writes."""
    boards = reference_boards()
    records, files = {}, {}
    for n in range(1, 33):
        path = os.path.join(IMAGES, f"combination_{n:02d}.svg")
        if n in REFUSED:
            files[path] = refused_picture(n)
            continue
        if n not in boards:
            raise SystemExit(f"no reference board for combination {n}: add BoardNNN-layout-{n:02d}-... "
                             f"(regression/boards.py new dual)")
        name = boards[n]
        rec = read_record(os.path.join(BOARDS, name, "Parameters.txt"))
        if rec["combination"] != n:
            raise SystemExit(f"{name} gives combination {rec['combination']}, not {n}")
        stator = read_stator(os.path.join(BOARDS, name, "Stator.kicad_pcb.gz"))
        records[n] = (name, rec)
        files[path] = board_picture(n, name, rec, stator)
    with open(PAGE, encoding="utf-8") as fh:
        page = fh.read()
    if BEGIN not in page or END not in page:
        raise SystemExit(f"{PAGE} has no generated part ({BEGIN} ... {END})")
    head, rest = page.split(BEGIN, 1)
    tail = rest.split(END, 1)[1].lstrip("\n")
    files[PAGE] = head + page_block(records) + ("\n" + tail if tail else "")
    return files


def stale(files):
    out = []
    for path, text in files.items():
        try:
            with open(path, encoding="utf-8", newline="") as fh:
                if fh.read() == text:
                    continue
        except FileNotFoundError:
            pass
        out.append(os.path.relpath(path, REPO))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="only compare, exit 1 when something is not current")
    args = ap.parse_args(argv)
    files = build()
    old = stale(files)
    if args.check:
        for p in old:
            print(f"not current: {p}  (run python docs/tools/dual_layout_pictures.py)")
        return 1 if old else 0
    os.makedirs(IMAGES, exist_ok=True)
    for path, text in files.items():
        if os.path.relpath(path, REPO) in old:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print(f"wrote {os.path.relpath(path, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

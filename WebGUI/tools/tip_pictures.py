"""
tip_pictures.py  -  draws the pictures of the help boxes (tooltips), as SVG, from boards the generators really build.

    python WebGUI/tools/tip_pictures.py            write WebGUI/docs/tooltips/drawn/<name>.svg
    python WebGUI/tools/tip_pictures.py --check    only say whether the SVG files are the ones this script gives (exit 1 if not)
    python WebGUI/tools/tip_pictures.py loops band only these pictures

    node WebGUI/tools/render_tip_pictures.mjs      then turns each SVG into WebGUI/docs/tooltips/pictures/<name>.webp

Each picture runs the generator (through WebGUI/WebGenerator.py, in a temporary copy of Generators/) with the
published values and the one or two settings the picture is about, reads the Stator.kicad_pcb and Rotor.kicad_pcb it
wrote (Generators/resources/KiCadReader.py), and draws that copper.  So a picture shows what the generator builds,
and a change of the generator changes the picture.  Only tx_wiring is a diagram: how the layers are joined cannot
be seen on the copper.

A help box is 360 px wide, so a picture is 680 px wide (twice the box, for sharp screens) and its words are 20 px
or more in the file, which is 10 px in the box.  One idea per picture; choices side by side, each under its name.
The same input gives the same bytes.  Needs only Python 3.
"""

import argparse
import json
import math
import os
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
REPO = os.path.dirname(WEB)
OUT = os.path.join(WEB, "docs", "tooltips", "drawn")
sys.path.insert(0, WEB)
sys.path.insert(0, os.path.join(REPO, "Generators", "resources"))
import KiCadReader  # noqa: E402
import WebGenerator as WG  # noqa: E402

W = 680
FONT = "Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
BG, INK, INK2, FAINT, ACCENT = "#fbfaf8", "#333333", "#555555", "#c9c4bd", "#a93e33"
LAYER = {"F.Cu": "#D03B2F", "In1.Cu": "#2E9E4F", "In2.Cu": "#B8930A", "B.Cu": "#2F6FD0"}   # the page's layer colours
VIA, VIA_RIM, ROTOR, SLAB = "#FFC400", "#A87A00", "#B87333", "#e7e1d8"
ORDER = ["B.Cu", "In2.Cu", "In1.Cu", "F.Cu"]                                             # drawn bottom first: seen from the top


def n(v):
    """A number for the SVG text: at most 1 decimal, no trailing zeros."""
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


# ------------------------------------------------------------------------------------------------- the boards
class Boards:
    """Runs the generator and keeps what it wrote, once per set of values."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="tip_pictures_")
        shutil.copytree(os.path.join(REPO, "Generators"), os.path.join(self.root, "Generators"),
                        ignore=shutil.ignore_patterns("__pycache__", "Coil_*", "DualCoil_*"))
        WG.ROOT = self.root
        WG._published.clear()
        self.built = {}

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def get(self, mode="single", **values):
        """values: FILE__NAME=value, the file without _Parameters.py (RX__LOOPS=4)."""
        key = mode + json.dumps(values, sort_keys=True)
        if key not in self.built:
            edits = {}
            for k, v in values.items():
                f, name = k.split("__")
                edits.setdefault(f + "_Parameters.py", {})[name] = v
            r = json.loads(WG.run(mode, json.dumps(edits)))
            if not r["ok"] or not r.get("stator"):
                raise SystemExit(f"tip_pictures: the generator did not build {mode} {values}: {r.get('failed') or r['text'][-600:]}")
            self.built[key] = Built(r)
        return self.built[key]


class Built:
    def __init__(self, r):
        folder = r["folder"]
        with open(os.path.join(folder, r["stator"]), encoding="utf-8") as fh:
            text = fh.read()
        self.stator = KiCadReader.read(os.path.join(folder, r["stator"]))
        self.rotor = KiCadReader.read(os.path.join(folder, r["rotor"]))
        with open(os.path.join(folder, "Parameters.txt"), encoding="utf-8") as fh:
            self.record = fh.read()
        edges = sorted((c for c in self.stator.circles if c.layer == "Edge.Cuts"), key=lambda c: float(c.radius))
        self.centre = (float(edges[0].center[0]), float(edges[0].center[1]))
        self.edges = [float(c.radius) for c in edges]
        nets = self.stator.nets
        self.segs = [(float(s.start[0]), float(s.start[1]), float(s.end[0]), float(s.end[1]), float(s.width), s.layer,
                      nets.get(s.net, "")) for s in self.stator.segments]
        self.vias = [(float(v.at[0]), float(v.at[1]), float(v.size), nets.get(v.net, "")) for v in self.stator.vias]
        self.dots = [(float(c.center[0]), float(c.center[1]), float(c.radius)) for c in self.stator.circles
                     if c.layer == "F.SilkS" and c.filled]
        # the silkscreen's lines (the dashed boxes and the letters), which the reader leaves out
        self.silk = [(float(a), float(b), float(c), float(d), kind) for a, b, c, d, kind in re.findall(
            r'\(gr_line\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\)\s+\(stroke \(width [-\d.]+\) \(type (\w+)\)'
            r'[^\n]*?\(layer "F\.SilkS"\)', text)]

    def number(self, pattern):
        m = re.search(pattern, self.record)
        if not m:
            raise SystemExit(f"tip_pictures: the record has no line like {pattern}")
        return [float(x) for x in m.groups()]

    def radius(self, x, y):
        return math.hypot(x - self.centre[0], y - self.centre[1])

    def is_rx(self, net):
        return bool(net) and not net.startswith("TX")

    def reach(self, pick):
        """The least and the largest radius of the copper of the nets pick(net) chooses, track widths included."""
        lo, hi = math.inf, -math.inf
        for x1, y1, x2, y2, w, _layer, net in self.segs:
            if pick(net):
                for r in (self.radius(x1, y1), self.radius(x2, y2)):
                    lo, hi = min(lo, r - w / 2), max(hi, r + w / 2)
        return lo, hi

    def cut(self, deg, pick):
        """The tracks a ray from the centre at `deg` meets: [(radius, width, layer)], inside first."""
        cx, cy = self.centre
        dx, dy = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        out = []
        for x1, y1, x2, y2, w, layer, net in self.segs:
            if not pick(net):
                continue
            ex, ey = x2 - x1, y2 - y1
            det = ex * dy - ey * dx
            if abs(det) < 1e-12:
                continue
            t = ((cx - x1) * dy - (cy - y1) * dx) / det          # along the segment
            r = ((cx - x1) * ey - (cy - y1) * ex) / det          # along the ray
            if 0 <= t < 1 and r > 0:
                out.append((r, w, layer))
        return sorted(out)


# ------------------------------------------------------------------------------------------------- drawing
class View:
    """Millimetres of a board to pixels of the picture: (x0, y0) mm sits at (px, py), turned by `turn` degrees."""

    def __init__(self, px, py, scale, x0, y0, turn=0.0):
        self.px, self.py, self.s, self.x0, self.y0 = px, py, scale, x0, y0
        self.c, self.sn = math.cos(math.radians(turn)), math.sin(math.radians(turn))

    def pt(self, x, y):
        dx, dy = x - self.x0, y - self.y0
        return self.px + self.s * (dx * self.c - dy * self.sn), self.py + self.s * (dx * self.sn + dy * self.c)


class Picture:
    def __init__(self, name, height, label):
        self.name, self.h, self.label, self.items, self.clips = name, height, label, [], 0

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, s, size=20, bold=False, anchor="middle", fill=INK):
        self.add(f'<text x="{n(x)}" y="{n(y)}" font-size="{size}" font-weight="{700 if bold else 500}" text-anchor="{anchor}" '
                 f'fill="{fill}">{s}</text>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.5, dash=None, cap="butt"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" stroke="{stroke}" stroke-width="{n(sw)}" '
                 f'stroke-linecap="{cap}"{d}/>')

    def circle(self, x, y, r, fill="none", stroke="none", sw=1.5, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"{d}{o}/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=1.5, rx=0, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(rx)}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{n(sw)}"{d}{o}/>')

    def arrow(self, x1, y1, x2, y2, stroke=ACCENT, sw=2.5, head=8, both=True):
        """A dimension line with a head at (x2, y2), and at (x1, y1) too when both."""
        self.line(x1, y1, x2, y2, stroke, sw)
        a = math.atan2(y2 - y1, x2 - x1)
        for (x, y, back) in ((x2, y2, a + math.pi),) + (((x1, y1, a),) if both else ()):
            p = [(x + head * math.cos(back + t), y + head * math.sin(back + t)) for t in (0.45, -0.45)]
            self.add(f'<path d="M{n(p[0][0])} {n(p[0][1])}L{n(x)} {n(y)}L{n(p[1][0])} {n(p[1][1])}" fill="none" stroke="{stroke}" '
                     f'stroke-width="{n(sw)}" stroke-linecap="round" stroke-linejoin="round"/>')

    def window(self, x, y, w, h):
        """Start a group that is cut to this box; end it with self.add("</g>")."""
        self.clips += 1
        cid = f"{self.name}-w{self.clips}"
        self.add(f'<clipPath id="{cid}"><rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="8"/></clipPath>')
        self.add(f'<g clip-path="url(#{cid})">')

    def copper(self, b, view, pick, sw=None, colour=None, opacity=None, least=2.0, layers=None):
        """The tracks of the nets pick(net) chooses, one path for each layer.  sw None: their true width (at least
        `least` px); colour None: the layer's colour."""
        for layer in ORDER:
            if layers and layer not in layers:
                continue
            by_width = {}
            for x1, y1, x2, y2, w, lay, net in b.segs:
                if lay == layer and pick(net):
                    by_width.setdefault(w, []).append((x1, y1, x2, y2))
            for w in sorted(by_width):
                d, last = [], None
                for x1, y1, x2, y2 in by_width[w]:
                    a, e = view.pt(x1, y1), view.pt(x2, y2)
                    if last is None or math.hypot(a[0] - last[0], a[1] - last[1]) > 0.05:      # a new run of segments
                        d.append(f"M{n(a[0])} {n(a[1])}")
                    d.append(f"L{n(e[0])} {n(e[1])}")
                    last = e
                width = sw if sw is not None else max(least, w * view.s)
                o = f' opacity="{opacity}"' if opacity is not None else ""
                self.add(f'<path d="{"".join(_thin(d))}" fill="none" stroke="{colour or LAYER[layer]}" stroke-width="{n(width)}" '
                         f'stroke-linecap="round" stroke-linejoin="round"{o}/>')

    def vias(self, b, view, pick, least=3.0):
        for x, y, size, net in b.vias:
            if pick(net):
                p = view.pt(x, y)
                self.circle(p[0], p[1], max(least, size / 2 * view.s), VIA, VIA_RIM, 1.2)

    def edges(self, b, view, sw=2.0):
        p = view.pt(*b.centre)
        for r in b.edges:
            self.circle(p[0], p[1], r * view.s, "none", INK, sw)

    def svg(self):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" width="{W}" height="{self.h}" '
                f'font-family="{FONT}" role="img" aria-label="{self.label}">\n'
                f'<rect width="{W}" height="{self.h}" fill="{BG}"/>\n')
        return head + "\n".join(self.items) + "\n</svg>\n"


def _thin(d):
    """Leave out the points of a path that are less than 1.2 px from the one before (the last of each run is kept)."""
    out, kept = [], None
    for i, cmd in enumerate(d):
        x, y = (float(v) for v in cmd[1:].split(" "))
        final = i + 1 == len(d) or d[i + 1][0] == "M"
        if cmd[0] == "M" or final or kept is None or math.hypot(x - kept[0], y - kept[1]) >= 1.2:
            out.append(cmd)
            kept = (x, y)
    return out


def titles(pic, xs, names, subs=None, y=30, sub_y=None, size=22):
    for x, name in zip(xs, names, strict=True):
        pic.text(x, y, name, size, True)
    for x, sub in zip(xs, subs or [], strict=False):
        pic.text(x, sub_y if sub_y is not None else pic.h - 16, sub, 20, False, fill=INK2)


# ------------------------------------------------------------------------------------------------- the pictures
def loops(boards):
    pic = Picture("loops", 380, "1 loop and 4 loops on the same band")
    for x, b in ((170, boards.get()), (510, boards.get(RX__LOOPS=4))):
        view = View(x, 192, 138 / b.edges[-1], *b.centre)
        pic.edges(b, view)
        pic.copper(b, view, b.is_rx, sw=2.6)
    titles(pic, (170, 510), ("Loops 1", "Loops 4"), ("one period per turn", "four periods per turn"))
    return pic


def band(boards):
    """A strip of the board along one radius, away from the TX terminal: the band's three radii and the swing."""
    b = boards.get()
    r_in, r_out = b.number(r"RX band r = ([\d.]+) \.\.\. ([\d.]+) mm")
    r_base = (r_in + r_out) / 2
    pic = Picture("band", 380, "The RX band between R_in and R_out, with R_base and the swing A")
    lo, hi = b.edges[0] - 1.2, b.edges[-1] + 1.2
    s = (W - 40) / (hi - lo)
    top, bottom = 84, 276
    # the board is turned so that the radius opposite the TX terminal points to the right
    view = View(20 - lo * s, (top + bottom) / 2, s, *b.centre, turn=180)
    pic.window(20, top, W - 40, bottom - top)
    pic.rect(20, top, W - 40, bottom - top, "#ffffff")
    pic.rect(view.pt(b.centre[0] - b.edges[0], 0)[0], top, (b.edges[-1] - b.edges[0]) * s, bottom - top, "#f1ede6")
    pic.rect(view.pt(b.centre[0] - r_in, 0)[0], top, (r_out - r_in) * s, bottom - top, ACCENT, opacity=0.10)
    pic.copper(b, view, lambda net: net.startswith("TX"), colour=FAINT)
    pic.copper(b, view, b.is_rx)
    pic.edges(b, view, 2.5)
    pic.add("</g>")
    for r, name, dash in ((r_in, "R_in", None), (r_base, "R_base", "7 6"), (r_out, "R_out", None)):
        x = view.pt(b.centre[0] - r, 0)[0]
        pic.line(x, top - 8, x, bottom + 8, ACCENT, 2.5, dash)
        pic.text(x, top - 20, name, 22, True, fill=ACCENT)
    y = bottom + 34
    x_in, x_base, x_out = (view.pt(b.centre[0] - r, 0)[0] for r in (r_in, r_base, r_out))
    pic.arrow(x_in + 3, y, x_base - 3, y)
    pic.arrow(x_base + 3, y, x_out - 3, y)
    pic.text((x_in + x_base) / 2, y + 28, "A", 22, True, fill=ACCENT)
    pic.text((x_base + x_out) / 2, y + 28, "A", 22, True, fill=ACCENT)
    pic.text(view.pt(b.centre[0] - b.edges[0], 0)[0] + 8, y + 28, "hole", 20, anchor="start", fill=INK2)
    pic.text(view.pt(b.centre[0] - b.edges[-1], 0)[0] - 8, y + 28, "board edge", 20, anchor="end", fill=INK2)
    pic.text(view.pt(b.centre[0] - (r_out + b.edges[-1]) / 2, 0)[0] + 6, top - 20, "TX", 20, fill=INK2)
    return pic


def profile(boards):
    """Both profiles on one wide band, one coil of each: on the published band they differ by less than a line."""
    wide = dict(Board__INNER_EDGE_RADIUS_MM=5, RX__INSIDE_RADIUS_MM=7, RX__RX_TABS="none")
    ea, cr = boards.get(**wide), boards.get(RX__RX_PROFILE="cosine_r", **wide)
    r_in, r_out = ea.number(r"RX band r = ([\d.]+) \.\.\. ([\d.]+) mm")
    pic = Picture("profile", 380, "Equal Area and Cosine R on the same band")
    view = View(196, 190, 172 / ea.edges[-1], *ea.centre)
    one = sorted({net for *_s, net in ea.segs if ea.is_rx(net)})[0]
    pic.edges(ea, view)
    for r in (r_in, r_out):
        pic.circle(196, 190, r * view.s, "none", "#8a8f98", 2, "7 6")
    pic.copper(cr, view, lambda net: net == one, sw=4, colour=ACCENT)
    pic.copper(ea, view, lambda net: net == one, sw=4, colour=INK)
    for y, colour, name, sub in ((126, INK, "Equal Area", "r² follows a sine"), (214, ACCENT, "Cosine R", "r follows a sine")):
        pic.line(410, y - 8, 456, y - 8, colour, 5, cap="round")
        pic.text(470, y, name, 22, True, anchor="start", fill=colour)
        pic.text(410, y + 30, sub, 20, anchor="start", fill=INK2)
    pic.line(410, 296, 456, 296, "#8a8f98", 2, "7 6")
    pic.text(470, 303, "the RX band", 20, anchor="start", fill=INK2)
    pic.text(410, 333, "one coil of each", 20, anchor="start", fill=INK2)
    return pic


def subcoils(boards):
    pic = Picture("subcoils", 380, "One coil, and the same coil split in two")
    for x, b in ((170, boards.get()), (510, boards.get(RX__RX_SUBCOILS=2))):
        view = View(x, 192, 138 / b.edges[-1], *b.centre)
        one = sorted({net for *_s, net in b.segs if b.is_rx(net)})[0]
        pic.edges(b, view)
        pic.copper(b, view, lambda net, one=one: net == one, sw=2.8)
        pic.vias(b, view, lambda net, one=one: net == one, least=4)
    titles(pic, (170, 510), ("Sub-Coils 1", "Sub-Coils 2"), ("one coil", "two copies, shifted"))
    return pic


def fingers(boards):
    pic = Picture("fingers", 340, "RX fingers: All, Single and None")
    xs = (118, 340, 562)
    for x, tabs in zip(xs, ("all", "single", "none"), strict=True):
        b = boards.get(RX__LOOPS=4, RX__RX_TABS=tabs)
        view = View(x, 172, 106 / b.edges[-1], *b.centre)
        pic.copper(b, view, lambda net: net.startswith("TX"), colour=FAINT, sw=1.5)
        pic.copper(b, view, b.is_rx, sw=2.4)
        pic.edges(b, view)
    titles(pic, xs, ("All", "Single", "None"), ("every lobe tip", "two fingers", "no fingers"))
    return pic


def tx_shape(boards):
    pic = Picture("tx_shape", 380, "Stepped Diagonal, Stepped Arc and Spiral at the TX terminal")
    xs = (118, 340, 562)
    for x, shape in zip(xs, ("stepped_diagonal", "stepped_arc", "spiral"), strict=True):
        b = boards.get(TX__TX_SHAPE=shape, RX__RX_TAB_LENGTH_MM=3.5)                # the spiral needs the longer fingers
        tx = lambda net: net.startswith("TX")                                       # noqa: E731
        vx, vy = next((x_, y_) for x_, y_, _size, net in b.vias if tx(net))
        s = 204 / 7.6
        view = View(x - 102 + 1.9 * s, 190, s, vx, vy)
        pic.window(x - 102, 46, 204, 288)
        pic.rect(x - 102, 46, 204, 288, "#ffffff")
        pic.copper(b, view, tx)
        pic.vias(b, view, tx)
        pic.edges(b, view, 2.5)
        pic.add("</g>")
        pic.rect(x - 102, 46, 204, 288, "none", FAINT, 1.5, rx=8)
    titles(pic, xs, ("Stepped Diagonal", "Stepped Arc", "Spiral"), ("straight steps", "arcs round the via", "one smooth spiral"), size=21)
    return pic


def tx_wiring(_boards):
    """A diagram: the turns of Layer A and Layer B drawn as two straight bars, with the vias that join them."""
    pic = Picture("tx_wiring", 300, "Single, Series and Parallel: how Layer A and Layer B are joined")
    xs = (118, 340, 562)
    a, bcol = LAYER["F.Cu"], LAYER["B.Cu"]
    for x, kind in zip(xs, ("single", "series", "parallel"), strict=True):
        left, right, ya, yb = x - 70, x + 84, 118, 190
        pic.rect(left - 14, ya + 9, right - left + 28, yb - ya - 18, SLAB, rx=4)
        pic.line(left, ya, right, ya, a, 14, cap="round")
        if kind == "single":
            pic.line(left, yb, right, yb, FAINT, 3, "7 7")
        else:
            pic.line(left, yb, right, yb, bcol, 14, cap="round")
        for vx in ([right] if kind == "series" else [left, right] if kind == "parallel" else []):
            pic.rect(vx - 6, ya, 12, yb - ya, VIA, VIA_RIM, 1.5, rx=3)
        ends = {"single": ((left, ya), (right, ya)), "series": ((left, ya), (left, yb)), "parallel": ((left, ya), (right, ya))}[kind]
        for ex, ey in ends:
            pic.circle(ex, ey, 9, "#ffffff", INK, 3)
        pic.text(left - 34, ya + 7, "A", 20, True, fill=a)
        pic.text(left - 34, yb + 7, "B", 20, True, fill=bcol if kind != "single" else "#8a8f98")
    titles(pic, xs, ("Single", "Series", "Parallel"), ("turns on Layer A", "twice the turns", "same turns, both layers"), y=62, sub_y=246)
    pic.circle(196, 274, 7, "#ffffff", INK, 2.5)
    pic.text(210, 281, "the two ends", 20, anchor="start", fill=INK2)
    pic.rect(376, 264, 10, 20, VIA, VIA_RIM, 1.5, rx=3)
    pic.text(396, 281, "via", 20, anchor="start", fill=INK2)
    return pic


def rotor_reach(boards):
    """A cut along one radius, from the board hole to the board edge: the rotor's copper above the stator's."""
    pic = Picture("rotor_reach", 380, "The rotor copper over the RX band and the TX turns, cut along a radius")
    for x0, cover in ((14, True), (354, False)):
        b = boards.get(Rotor__ROTOR_AUTO_COVER_TX=cover)
        r_in, r_out = b.number(r"RX band r = ([\d.]+) \.\.\. ([\d.]+) mm")
        cx, cy = b.centre
        radii = [math.hypot(float(px) - cx, float(py) - cy) for poly in b.rotor.polygons for px, py in poly.points]
        lo_r, hi_r = min(radii), max(radii)
        lo, hi = b.edges[0], b.edges[-1]
        s = 312 / (hi - lo)
        X = lambda r, x0=x0, s=s, lo=lo: x0 + (r - lo) * s                          # noqa: E731,N806
        # the rotor board, its copper on the side that faces the stator
        pic.rect(X(lo), 96, (hi - lo) * s, 26, SLAB, rx=3)
        pic.rect(X(lo_r), 122, (hi_r - lo_r) * s, 14, ROTOR)
        # the stator board: the RX band and the TX turns on its top
        pic.rect(X(lo), 236, (hi - lo) * s, 26, SLAB, rx=3)
        pic.rect(X(r_in), 222, (r_out - r_in) * s, 14, LAYER["F.Cu"], opacity=0.85)
        turns = sorted({round(r, 2): w for r, w, _layer in b.cut(90, lambda net: net.startswith("TX"))}.items())
        for r, w in turns:
            pic.rect(X(r - w / 2), 222, w * s, 14, LAYER["B.Cu"])
        pic.text(X((r_in + r_out) / 2), 292, "RX band", 20, fill=INK2)
        pic.text(X(sum(r for r, _w in turns) / len(turns)), 292, "TX", 20, fill=INK2)
        pic.text(X(hi) - 8, 116, "Rotor", 20, anchor="end", fill=INK2)
        pic.text(X(hi) - 8, 256, "Stator", 20, anchor="end", fill=INK2)
        # how far the rotor copper reaches past the band, on the inside
        for r in (r_in, lo_r):
            pic.line(X(r), 140, X(r), 218, ACCENT, 1.5, "4 4")
        pic.arrow(X(lo_r), 178, X(r_in), 178, sw=2, head=6)
        if cover:
            pic.text(X(r_in) + 10, 185, "Extension", 20, True, anchor="start", fill=ACCENT)
        else:
            pic.line(X(r_out), 140, X(r_out), 218, ACCENT, 1.5, "4 4")
            pic.line(X(hi_r), 140, X(hi_r), 218, ACCENT, 1.5, "4 4")
            pic.arrow(X(r_out), 178, X(hi_r), 178, sw=2, head=6)
    titles(pic, (170, 510), ("True", "False"), ("copper over the TX turns", "copper ends inside the TX ring"), y=40, sub_y=336)
    pic.text(W / 2, 368, "drawn thicker than true scale", 20, fill="#6a6a6a")
    return pic


def break_(boards):
    """One RX break of the published board, enlarged: what the silkscreen step marks."""
    b = boards.get()
    pic = Picture("break", 380, "An RX break: two via sites, the dashed box, and the trace to cut")
    dots = sorted(b.dots, key=lambda d: (d[0], d[1]))
    # the two dots of one break are the closest pair
    pair = min(((p, q) for i, p in enumerate(dots) for q in dots[i + 1:]), key=lambda pq: math.hypot(pq[0][0] - pq[1][0], pq[0][1] - pq[1][1]))
    mx, my = (pair[0][0] + pair[1][0]) / 2, (pair[0][1] + pair[1][1]) / 2
    turn = -math.degrees(math.atan2(pair[1][1] - pair[0][1], pair[1][0] - pair[0][0]))
    near = [ln for ln in b.silk if max(math.hypot(ln[0] - mx, ln[1] - my), math.hypot(ln[2] - mx, ln[3] - my)) < 3.6]   # this break's box and letters
    flat = View(0, 0, 1, mx, my, turn)
    pts = [flat.pt(x, y) for ln in near for x, y in ((ln[0], ln[1]), (ln[2], ln[3]))]
    x_lo, x_hi, y_lo, y_hi = (f(p[k] for p in pts) for k in (0, 1) for f in (min, max))
    s = min(360 / (x_hi - x_lo), 270 / (y_hi - y_lo), 70)
    view = View(250 - s * (x_lo + x_hi) / 2, 190 - s * (y_lo + y_hi) / 2, s, mx, my, turn)
    pic.window(20, 20, 460, 340)
    pic.rect(20, 20, 460, 340, "#ffffff")
    pic.copper(b, view, lambda net: True)
    for x1, y1, x2, y2, kind in near:
        p, q = view.pt(x1, y1), view.pt(x2, y2)
        pic.line(p[0], p[1], q[0], q[1], INK, 3 if kind == "dash" else 2.5, "9 7" if kind == "dash" else None, "round")
    for x, y, r in pair:
        p = view.pt(x, y)
        pic.circle(p[0], p[1], max(7, r * s), INK)
    pic.add("</g>")
    pic.rect(20, 20, 460, 340, "none", FAINT, 1.5, rx=8)
    p, q = view.pt(pair[0][0], pair[0][1]), view.pt(pair[1][0], pair[1][1])
    marks = (((p, q), (500, 96), ("two dots:", "a via each")),
             ((((p[0] + q[0]) / 2, (p[1] + q[1]) / 2),), (500, 206), ("cut the trace", "between them")))
    for at, (tx, ty), words in marks:
        for x, y in at:
            pic.line(x, y, tx - 8, ty - 6, ACCENT, 2)
            pic.circle(x, y, 3.5, ACCENT)
        for k, wd in enumerate(words):
            pic.text(tx, ty + 26 * k, wd, 20, k == 0, anchor="start", fill=ACCENT if k == 0 else INK2)
    pic.line(500, 318, 546, 318, INK, 3, "9 7")
    pic.text(556, 325, "the box", 20, anchor="start", fill=INK2)
    return pic


def dual_layout(boards):
    """The copper of the published dual board along one radius, measured on the board."""
    b = boards.get("dual")
    pic = Picture("dual_layout", 300, "Set 1, the gap and set 2 along the radius")
    lo, hi = b.edges[0] - 0.6, b.edges[-1] + 0.6
    s = (W - 40) / (hi - lo)
    X = lambda r: 20 + (r - lo) * s                                                 # noqa: E731,N806
    y, h = 128, 62
    pic.rect(X(b.edges[0]), y - 12, (b.edges[-1] - b.edges[0]) * s, h + 24, SLAB, rx=4)
    spans = {}
    for name, pick in (("RX 1", lambda net: net in ("SIN_1", "COS_1")), ("TX 1", lambda net: net == "TX_1"),
                       ("RX 2", lambda net: net in ("SIN_2", "COS_2")), ("TX 2", lambda net: net == "TX_2")):
        if name.startswith("RX"):
            a, e = b.number(rf"RX{name[-1]} band r = ([\d.]+) \.\.\. ([\d.]+) mm")
        else:
            a, e = b.reach(pick)
        spans[name] = (a, e)
        pic.rect(X(a), y, (e - a) * s, h, "#5d6470" if name.startswith("RX") else "#9aa0aa", rx=3)
        pic.text(X((a + e) / 2), y + h / 2 + 8, name, 21, True, fill="#ffffff")
    set1 = (b.reach(lambda net: net.endswith("_1"))[0], b.reach(lambda net: net.endswith("_1"))[1])
    set2 = (b.reach(lambda net: net.endswith("_2"))[0], b.reach(lambda net: net.endswith("_2"))[1])
    for (a, e), name in ((set1, "Set 1"), (set2, "Set 2")):
        pic.add(f'<path d="M{n(X(a))} {n(y - 22)}v-10H{n(X(e))}v10" fill="none" stroke="{INK}" stroke-width="2"/>')
        pic.text(X((a + e) / 2), y - 46, name, 22, True)
    ga, ge = set1[1], set2[0]
    for r in (ga, ge):
        pic.line(X(r), y - 4, X(r), y + h + 34, ACCENT, 1.5, "4 4")
    pic.arrow(X(ga) + 2, y + h + 26, X(ge) - 2, y + h + 26)
    pic.text(X((ga + ge) / 2), y + h + 58, "Track Gap", 22, True, fill=ACCENT)
    pic.text(X(b.edges[0]), y + h + 96, "hole", 20, anchor="start", fill=INK2)
    pic.text(X(b.edges[-1]), y + h + 96, "board edge", 20, anchor="end", fill=INK2)
    pic.text(X((ga + ge) / 2), y + h + 96, "radius", 20, fill="#6a6a6a")
    pic.arrow(X((ga + ge) / 2) + 44, y + h + 89, X((ga + ge) / 2) + 84, y + h + 89, stroke="#6a6a6a", sw=1.8, head=6, both=False)
    return pic


PICTURES = {"loops": loops, "band": band, "profile": profile, "subcoils": subcoils, "fingers": fingers, "tx_shape": tx_shape,
            "tx_wiring": tx_wiring, "rotor_reach": rotor_reach, "break": break_, "dual_layout": dual_layout}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Draws the pictures of the help boxes as SVG, from boards the generators build.")
    ap.add_argument("names", nargs="*", help="only these pictures (default: all)")
    ap.add_argument("--check", action="store_true", help="only compare the files with what would be written")
    args = ap.parse_args(argv)
    unknown = [x for x in args.names if x not in PICTURES]
    if unknown:
        print(f"tip_pictures: no picture named {', '.join(unknown)} (there are: {', '.join(PICTURES)})")
        return 1
    boards, wrong = Boards(), []
    out, err = sys.stdout, sys.stderr
    try:
        os.makedirs(OUT, exist_ok=True)
        for name in args.names or PICTURES:
            text = PICTURES[name](boards).svg()
            path = os.path.join(OUT, name + ".svg")
            if args.check:
                try:
                    with open(path, encoding="utf-8") as fh:
                        same = fh.read() == text
                except OSError:
                    same = False
                if not same:
                    wrong.append(name)
            else:
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                print(f"{name}.svg  {len(text) // 1024} KB", file=out)
    finally:
        sys.stdout, sys.stderr = out, err
        boards.close()
    if args.check:
        print("the drawn pictures are up to date" if not wrong else f"not what tip_pictures.py gives: {', '.join(wrong)}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())

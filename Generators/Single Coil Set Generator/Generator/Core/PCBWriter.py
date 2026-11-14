"""
PCBWriter.py  -  writes a board as a KiCad 7 .kicad_pcb file (readable by KiCad 7, 8, 9 and 10): nets, track
segments, vias, circles and filled polygons, the title block and the page.  Used by the stator and the rotor.

Next to each board it writes the KiCad project file of the same name (Stator.kicad_pro next to Stator.kicad_pcb),
which holds the board's design rules: KiCad keeps them in the project file, not in the board, and without one its
design rule check (DRC) uses its own defaults (0.2 mm clearance, 0.3 mm holes, in KiCad 10 also 0.2 mm traces)
instead of the values the board was made with.  The rules are the parameters' MIN_CLEARANCE_MM and the smallest
track, via and drill the board holds, so that KiCad reports only what breaks the board's own rules.
Nothing to edit here.
"""

import json
import math
import os


class KiCadBoard:
    _COPPER2 = """\
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)"""
    _COPPER4 = """\
    (0 "F.Cu" signal)
    (1 "In1.Cu" signal)
    (2 "In2.Cu" signal)
    (31 "B.Cu" signal)"""
    _LAYERS = """\
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user "B.Mask")
    (39 "F.Mask" user "F.Mask")
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)"""

    def __init__(self, title="Inductive sensor", page=(200, 200), thickness=1.6, copper_layers=2, comments=None):
        """comments: up to 9 lines for the comment fields of the title block (KiCad: Comment1 ... Comment9;
        its default drawing sheet shows Comment1 ... Comment4, Comment1 at the bottom)."""
        self.copper_layers = int(copper_layers)
        self.title, self.page, self.thickness = title, page, thickness
        self.comments = list(comments) if comments else []
        self.nets = {"": 0}
        self.body = []
        self.track_widths, self.via_sizes = set(), set()     # for the design rules of the project file

    def net(self, name):
        """The number of the net `name`, which joins the board's net list the first time it is asked for."""
        if name not in self.nets:
            self.nets[name] = len(self.nets)
        return self.nets[name]

    @staticmethod
    def _q(s):
        """Text for the file: no double quotes, backslashes or line breaks."""
        return str(s).replace("\\", "/").replace('"', "'").replace("\n", " ")

    @staticmethod
    def _f(v):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("", "-0") else s

    def segment(self, p, q, width, layer, net):
        """Add a track from p to q on a copper layer, in the net named `net`."""
        f = self._f
        self.track_widths.add(float(f(width)))
        self.body.append(
            f'  (segment (start {f(p[0])} {f(p[1])}) (end {f(q[0])} {f(q[1])}) '
            f'(width {f(width)}) (layer "{layer}") (net {self.net(net)}))')

    def via(self, p, size, drill, net, layers=None, blind=False):
        """A via.  Through (the default) spans the board, written with the layers F.Cu and B.Cu whatever it joins.
        With blind=True and `layers` = the two layers it joins, it is written as a blind via between them (KiCad's
        `blind` token, used for buried vias too); a pair that is Top and Bottom is a through via all the same."""
        f = self._f
        pair = tuple(layers) if blind and layers else ("F.Cu", "B.Cu")
        kind = "" if set(pair) == {"F.Cu", "B.Cu"} else "blind "
        if not kind:
            pair = ("F.Cu", "B.Cu")
        self.via_sizes.add((float(f(size)), float(f(drill))))
        self.body.append(
            f'  (via {kind}(at {f(p[0])} {f(p[1])}) (size {f(size)}) (drill {f(drill)}) '
            f'(layers "{pair[0]}" "{pair[1]}") (net {self.net(net)}))')

    def circle(self, c, radius, layer, width):
        """Add an unfilled circle of `radius` around c on `layer` (the board outline and the bore)."""
        f = self._f
        self.body.append(
            f'  (gr_circle (center {f(c[0])} {f(c[1])}) (end {f(c[0])} {f(c[1] + radius)}) '
            f'(layer "{layer}") (width {f(width)}) (fill none))')

    def polygon(self, points, layer):
        """Add a filled polygon on `layer` (the rotor copper and its mask openings)."""
        f = self._f
        pts = " ".join(f"(xy {f(x)} {f(y)})" for x, y in points)
        self.body.append(f'  (gr_poly (pts {pts}) (layer "{layer}") (width 0) (fill solid))')

    def text(self):
        """The .kicad_pcb file as text: the header, page, title block, layers and nets, then every item added."""
        out = ["(kicad_pcb (version 20221018) (generator coil_generator)", "",
               f"  (general (thickness {self._f(self.thickness)}))", "",
               f'  (paper "User" {self.page[0]} {self.page[1]})',
               "  (title_block (title \"" + self._q(self.title) + "\")"
               + "".join(f' (comment {i} "{self._q(c)}")' for i, c in enumerate(self.comments[:9], 1)) + ")", "",
               "  (layers", self._COPPER4 if self.copper_layers == 4 else self._COPPER2,
               self._LAYERS, "  )", "",
               "  (setup (pad_to_mask_clearance 0))", ""]
        for name, idx in sorted(self.nets.items(), key=lambda kv: kv[1]):
            out.append(f'  (net {idx} "{name}")')
        out.append("")
        out.extend(self.body)
        out.append(")")
        return "\n".join(out) + "\n"

    def project(self, path, clearance):
        """The KiCad project file (.kicad_pro) of the board saved at `path`, as text: its design rules.  The
        clearance between nets is `clearance` (MIN_CLEARANCE_MM); the smallest track width, via diameter and via
        drill are the smallest on this board (a board without tracks or vias keeps KiCad's defaults for them).  Each
        rule is written twice, as the board's minimum (Board Setup > Constraints) and as the Default net class, which
        every net of the board is in."""
        c = float(self._f(clearance))
        rules = {"min_clearance": c}
        net_class = {"name": "Default", "clearance": c}
        if self.track_widths:
            rules["min_track_width"] = net_class["track_width"] = min(self.track_widths)
        if self.via_sizes:
            rules["min_via_diameter"] = net_class["via_diameter"] = min(s for s, _ in self.via_sizes)
            rules["min_through_hole_diameter"] = net_class["via_drill"] = min(d for _, d in self.via_sizes)
        project = {"board": {"design_settings": {"rules": rules}},
                   "meta": {"filename": os.path.basename(project_path(path)), "version": 1},
                   "net_settings": {"classes": [net_class], "meta": {"version": 3}}}
        return json.dumps(project, indent=2, sort_keys=True) + "\n"

    def save(self, path, clearance):
        """Write text() to `path`, and the project file with the board's design rules (project()) next to it, both
        with LF line endings."""
        with open(path, "w", newline="\n") as fh:
            fh.write(self.text())
        with open(project_path(path), "w", newline="\n") as fh:
            fh.write(self.project(path, clearance))


def project_path(path):
    """The KiCad project file that belongs to the board at `path`: the same name, ending in .kicad_pro (KiCad opens
    the board with the rules of the project file of its own name)."""
    return os.path.splitext(path)[0] + ".kicad_pro"


# KiCad's default drawing sheet (KiCad 7 ... 9): a frame 10 mm and 12 mm inside the page edge, and the title block
# 108 x 32 mm in the bottom right corner of the inner frame
SHEET_FRAME_MM = 12.0
TITLE_BLOCK_MM = (108.0, 32.0)
PAGE_GAP_MM = 3.0                   # free space between the board and the frame / the title block


def page_size(P, cx, cy, radius):
    """KiCad page size (width, height, mm) for a round board of `radius` (its outer edge) centred at (cx, cy) on the
    page: at least PAGE_SIZE_MM, grown (right and down, so the board keeps its position) until the board stays
    PAGE_GAP_MM clear of the right and bottom side of the drawing frame and of the title block.  Of the sizes that do
    that, the one with the smallest area.  Only the right and bottom sides are handled: the top and left side
    depend on CENTER_X_MM / CENTER_Y_MM, which DesignChecks.check_design checks (for the stator and the rotor)."""
    w0, h0 = (float(v) for v in P.PAGE_SIZE_MM)
    R = float(radius) + float(P.EDGE_LINE_WIDTH_MM) / 2.0 + PAGE_GAP_MM
    fr = SHEET_FRAME_MM
    tw, th = TITLE_BLOCK_MM
    w_min = max(w0, math.ceil(cx + R + fr))
    h_min = max(h0, math.ceil(cy + R + fr))

    def clear(w, h):
        # distance from the board centre to the title block rectangle
        x0, x1, y0, y1 = w - fr - tw, w - fr, h - fr - th, h - fr
        dx = max(x0 - cx, 0.0, cx - x1)
        dy = max(y0 - cy, 0.0, cy - y1)
        return math.hypot(dx, dy) >= R

    best = None
    w = w_min
    while True:
        h = h_min
        while not clear(w, h):
            h += 1.0
        if best is None or w * h < best[0] * best[1] - 1e-9:
            best = (w, h)
        if h == h_min:                     # (wider pages cannot make it any smaller)
            break
        w += 1.0
    return best

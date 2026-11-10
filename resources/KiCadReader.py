"""
KiCadReader.py  -  reads a KiCad board file (.kicad_pcb, as KiCad 7 to 10 write it) into plain Python values: the
copper layers, the nets, the track segments, the vias, the board-level circles and polygons, and the title block.

    import KiCadReader
    board = KiCadReader.read("Stator.kicad_pcb")
    board.copper_layers          ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]   in stack order, top to bottom
    board.nets                   {0: "", 1: "SIN_1", ...}               number -> name
    board.segments               [Segment(start, end, width, layer, net), ...]
    board.vias                   [Via(at, size, drill, layers, net, kind), ...]   kind: through, blind, buried, micro
    board.circles                [Circle(center, end, radius, width, layer, filled), ...]
    board.polygons               [Polygon(points, width, layer, filled), ...]
    board.title, board.comments  the title block: its title, and {comment number: text}
    board.skipped                the kinds of item present that are not read (arc tracks, zones, footprints), so a
                                 caller can say that its picture leaves something out

It is a parser, not a pattern match: the file is split into its brackets, quoted strings and words, and each item is
read by the names of its fields, in any order, with fields it does not know skipped.  So a board that KiCad has
opened and saved again, with its fields in another order, on lines of their own, or with fields the generators do
not write (uuid, locked, stroke styles), reads the same.  Every number keeps the text it has in the file (str(number)
and an f-string give it back exactly) and is a float for arithmetic.  A net is a number of board.nets.  KiCad 10 no
longer lists the nets and names the net of each track instead of numbering it: those names are numbered 1, 2, ... in
the order they first appear, so a net still has a number and a name.  A via's kind is through, micro, blind (from
the top or bottom layer to an inner one) or buried (between two inner layers): KiCad writes "blind" for both of the
last two, so the layers tell them apart.

Standard library only.  It reads the boards for the lead-cutting silkscreen step of both generators
(Single Generator/Generator/Stator/LeadCutting_SilkscreenSuggestion.py, which loads it by its path, as it loads the
font), for the two picture makers next to this file (RepresentativeSVGMaker.py, ActualSVGMaker.py) and for the
pictures of the wiki page Dual Layout (docs/tools/dual_layout_pictures.py).  The regression tests keep a reader of
their own (regression/RegressionTools.py) on purpose, so that the boards are not checked with the code that is being
tested, and a test holds the two readers to the same values on every reference board.
"""

import gzip
import math
import re
from collections import namedtuple

Segment = namedtuple("Segment", "start end width layer net")
Via = namedtuple("Via", "at size drill layers net kind")
Circle = namedtuple("Circle", "center end radius width layer filled")
Polygon = namedtuple("Polygon", "points width layer filled")

_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')
_NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\Z")
_NUMBER_START = frozenset("+-.0123456789")
_ESCAPE = re.compile(r"\\(.)")
NOT_READ = ("arc", "zone", "footprint")


class Number(float):
    """A number of the file: a float for arithmetic whose text (str, f-string) is exactly the text in the file."""
    __slots__ = ("text",)

    def __new__(cls, text):
        value = float.__new__(cls, text)
        value.text = text
        return value

    def __str__(self):
        return self.text

    __repr__ = __str__


class Text(str):
    """A quoted string of the file (as opposed to a bare word such as a keyword)."""
    __slots__ = ()


def parse(text):
    """The file as nested lists: each bracket a list whose first entry is its keyword.  Bare words that are numbers
    become Number, other bare words str, quoted strings Text (escapes resolved)."""
    stack, top = [], []
    current = top
    for tok in _TOKEN.findall(text):
        c = tok[0]
        if c == "(":
            new = []
            current.append(new)
            stack.append(current)
            current = new
        elif c == ")":
            if not stack:
                raise ValueError("a ')' with no '(' before it: is this a KiCad file?")
            current = stack.pop()
        elif c == '"':
            current.append(Text(_ESCAPE.sub(r"\1", tok[1:-1]) if "\\" in tok else tok[1:-1]))
        elif c in _NUMBER_START and _NUMBER.match(tok):
            current.append(Number(tok))
        else:
            current.append(tok)
    if stack:
        raise ValueError("the file ends inside a bracket: is it complete?")
    return top


def field(item, name):
    """The first sub-list of `item` with keyword `name`, or None."""
    for sub in item:
        if isinstance(sub, list) and sub and sub[0] == name:
            return sub
    return None


def fields(item, name):
    return [sub for sub in item if isinstance(sub, list) and sub and sub[0] == name]


def _xy(item, name):
    f = field(item, name)
    return None if f is None else (f[1], f[2])


def _width(item):
    """A width given as (width w) or, in newer files, as (stroke (width w) ...)."""
    f = field(item, "width")
    if f is None:
        stroke = field(item, "stroke")
        f = field(stroke, "width") if stroke is not None else None
    return None if f is None else f[1]


def _filled(item):
    f = field(item, "fill")
    return f is not None and len(f) > 1 and str(f[1]) in ("solid", "yes")


class Board:
    """What read() returns; see the module text."""

    def __init__(self, tree, path=""):
        if not tree or not isinstance(tree[0], list) or tree[0][:1] != ["kicad_pcb"]:
            raise ValueError(f"{path or 'the text'} is not a KiCad board file (it does not start with (kicad_pcb ...)")
        pcb = tree[0]
        self.path = path
        self.version = (field(pcb, "version") or [None, None])[1]
        self.thickness = None
        general = field(pcb, "general")
        if general is not None and field(general, "thickness") is not None:
            self.thickness = field(general, "thickness")[1]
        layers = field(pcb, "layers") or []
        named = [(str(e[1]), str(e[2]) if len(e) > 2 else "") for e in layers[1:] if isinstance(e, list) and len(e) > 1]
        self.copper_layers = sorted((n for n, _kind in named if n.endswith(".Cu")), key=_stack_order)
        self.nets = {int(e[1]): str(e[2]) for e in fields(pcb, "net") if len(e) > 2}
        self._by_name = {name: n for n, name in self.nets.items()}
        self.segments, self.vias, self.circles, self.polygons = [], [], [], []
        skipped = set()
        for item in pcb[1:]:
            if not isinstance(item, list) or not item:
                continue
            kind = item[0]
            if kind == "segment":
                self.segments.append(Segment(_xy(item, "start"), _xy(item, "end"), _width(item),
                                             str(field(item, "layer")[1]), self._net(item)))
            elif kind == "via":
                lay = field(item, "layers")
                layers = tuple(str(x) for x in lay[1:]) if lay else ()
                self.vias.append(Via(_xy(item, "at"), field(item, "size")[1], (field(item, "drill") or [None, None])[1],
                                     layers, self._net(item), _via_kind(item, layers)))
            elif kind == "gr_circle":
                c, e = _xy(item, "center"), _xy(item, "end")
                r = math.hypot(float(e[0]) - float(c[0]), float(e[1]) - float(c[1]))
                self.circles.append(Circle(c, e, r, _width(item), str(field(item, "layer")[1]), _filled(item)))
            elif kind == "gr_poly":
                pts = field(item, "pts") or []
                self.polygons.append(Polygon([(p[1], p[2]) for p in fields(pts, "xy")], _width(item),
                                             str(field(item, "layer")[1]), _filled(item)))
            elif kind in NOT_READ:
                skipped.add(kind)
        self.skipped = sorted(skipped)
        block = field(pcb, "title_block")
        self.title = str(field(block, "title")[1]) if block is not None and field(block, "title") else ""
        self.comments = {int(c[1]): str(c[2]) for c in fields(block, "comment")} if block is not None else {}

    def _net(self, item):
        """The net number of a track or via: (net 3), or (net "SIN_1") as KiCad 10 writes it, the name then numbered
        when the board does not list it; 0 when it has none."""
        f = field(item, "net")
        if f is None or len(f) < 2:
            return 0
        if not isinstance(f[1], Text):
            return int(f[1])
        name = str(f[1])
        if name not in self._by_name:
            n = 0 if name == "" else max(self.nets, default=0) + 1
            self.nets[n] = name
            self._by_name[name] = n
        return self._by_name[name]

    def __repr__(self):
        return (f"<Board {self.path or ''}: {len(self.copper_layers)} copper layers, {len(self.segments)} segments, "
                f"{len(self.vias)} vias, {len(self.circles)} circles, {len(self.polygons)} polygons>")


def _via_kind(item, layers):
    """through, micro, blind or buried; see the module text."""
    words = {str(w) for w in item[1:] if not isinstance(w, list)}
    if "micro" in words:
        return "micro"
    if not words & {"blind", "buried"}:
        return "through"
    return "blind" if {"F.Cu", "B.Cu"} & set(layers) else "buried"


def _stack_order(name):
    """F.Cu first, then In1.Cu, In2.Cu, ..., B.Cu last."""
    if name == "F.Cu":
        return 0
    if name == "B.Cu":
        return 1000
    m = re.match(r"In(\d+)\.Cu$", name)
    return int(m.group(1)) if m else 999


def read(source):
    """The board in `source`: a path to a .kicad_pcb file (or a .kicad_pcb.gz), or the text of one."""
    if "\n" in source or source.lstrip().startswith("("):
        return Board(parse(source))
    opener = gzip.open if source.endswith(".gz") else open
    with opener(source, "rt", encoding="utf-8") as fh:
        return Board(parse(fh.read()), source)

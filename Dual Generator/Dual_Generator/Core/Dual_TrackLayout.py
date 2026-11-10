"""
Dual_TrackLayout.py  -  where the two coil sets sit: the RX band of each set, the bore and the outline, and the
gap between the sets.  There is no mode to choose: the layout takes what is given and places the rest.

From the centre out, the board is a stack:

    bore | RX1 band | TX1 ring | gap | RX2 band | TX2 ring | outline

Five things can be given: the RX1 band (Dual_RX1_Parameters.py), the RX2 band (Dual_RX2_Parameters.py), the bore
and the outline (INNER_EDGE_RADIUS_MM, OUTER_EDGE_RADIUS_MM) and the gap (TRACK_GAP_MM, the last three in
Dual_Board_Parameters.py).  A band is given in one of the Single Generator's two ways (INSIDE_RADIUS_MM /
OUTSIDE_RADIUS_MM, or RX_R_BASE_MM / RX_A_MM) or not at all (all four None).  Of the 32 combinations, 26 build.
Four rules place what is not given, so every spacing follows from the sets' own settings:

  the gap   TRACK_GAP_MM, or the larger of the two sets' MIN_CLEARANCE_MM when it is None.  A band the generator
            places sits exactly that far from the other set; when both bands are given, it is the least the gap
            between them may be.
  a band    when one band is given, the other is placed across the gap: RX2 outwards from set 1's copper, or RX1
            inwards from set 2's.  Its far end goes to the board edge on that side when that edge is given (the
            outline less the TX2 ring and the margins, or the bore plus INNER_EDGE_INSET_MM); otherwise the band
            is as wide as the given one.
  an edge   not given: from the band, as in the Single Generator.  Given: used as given, and checked by the
            Single Generator's own rule when each set is checked (Dual_CheckParameters).
  no band   needs both edges: what is left between them is shared by BAND_SPLIT.

The other 6 combinations give no band and at most one edge: there is nothing to size a band from, and the check
stops with a message that says what to give.  combination() numbers the 32 in the order of the table on the wiki
page Dual Layout.

The radii between the bands come from the Single Generator's own rules, applied to each set's own values
(Dual_SetParameters.build: its own vias and clearance where the set file gives them), so that the sets it then
builds land exactly where this module put them:
    bore            = RX1 band start - INNER_EDGE_INSET_MM                     (BoardLayout.resolve)
    set 1 reach     = RX1 band end + how far set 1's copper reaches past it: the TX turns (a spiral one pitch
                      farther), the TX tail, the RX bridging fingers and the go-around brackets, widths included
                      (BoardLayout.outer_copper_reach)
    set 2 innermost copper = RX2 band start - max(half an RX trace, a via radius)  (the inner-tip vias)
    gap             = set 2 innermost copper - set 1 reach
    outline         = RX2 band end + outer_edge_room  (BoardLayout.outer_edge_room: OUTER_EDGE_OFFSET_MM, the
                      TX2 tail + OUTER_EDGE_TAIL_MARGIN_MM or set 2's fingers + the margin, whichever is larger)
Dual_DesignChecks measures the same radii on the built copper afterwards.

resolve(P) returns a Layout (below) or raises ParameterConflict in the Single Generator's style (the names of the
settings to change, and what to change).  Nothing to edit here.
"""

import math
import types

from Generator.Core import BoardLayout
from Generator.Rotor import RotorBuilder as RB
from Generator.Core.Conflict import ParameterConflict

from Dual_Generator.Core import Dual_SetParameters as SP

RX_FILES = {1: "Dual_RX1_Parameters.py", 2: "Dual_RX2_Parameters.py"}
BOARD_FILE = "Dual_Board_Parameters.py"
COMBINATIONS = 32
EDGE_WORDS = {(False, False): "bore and outline from the bands", (True, False): "bore as given, outline from the RX2 band",
              (False, True): "outline as given, bore from the RX1 band", (True, True): "bore and outline as given"}


class Layout(types.SimpleNamespace):
    """combination (1 ... 32, numbered as on the wiki page Dual Layout); band1, band2 (dict ri, ro, how = "radii" |
    "centre" | "placed", names = the single names to set); bore, outline (mm), where each came from (bore_from,
    outline_from) and whether it was given (bore_given, outline_given); gap_setting (TRACK_GAP_MM or None),
    gap_required (TRACK_GAP_MM, or the larger MIN_CLEARANCE_MM), gap_expected (mm, from the formulas); reach1 (set 1
    outermost copper), inner2 (set 2 innermost copper); room1, margin2, outer_room2."""

    def set_band(self, k):
        """{single name: value} for set k's RX band (Dual_SetParameters.build)."""
        return dict((self.band1 if k == 1 else self.band2)["names"])

    def edges(self):
        return (self.bore, self.outline)

    def gap_name(self):
        """The setting the gap comes from: TRACK_GAP_MM, or MIN_CLEARANCE_MM when that is None."""
        return "TRACK_GAP_MM" if self.gap_setting is not None else "MIN_CLEARANCE_MM"

    def placed(self, k):
        return (self.band1 if k == 1 else self.band2)["how"] == "placed"

    def describe(self):
        """What was given and what the generator placed, in words, with the combination number."""
        g = self.gap_name()
        if self.placed(1) and self.placed(2):
            bands = f"both RX bands fitted between the edges, split by BAND_SPLIT, {g} apart"
        elif self.placed(2):
            bands = f"RX1 band given, RX2 band placed {g} out and " + ("running to the outline" if self.outline_given
                                                                         else "as wide as RX1")
        elif self.placed(1):
            bands = f"RX2 band given, RX1 band placed {g} in and " + ("starting at the bore plus INNER_EDGE_INSET_MM"
                                                                        if self.bore_given else "as wide as RX2")
        else:
            bands = f"both RX bands given, at least {g} apart"
        return f"{bands}; {EDGE_WORDS[(self.bore_given, self.outline_given)]} (combination {self.combination} of " \
               f"{COMBINATIONS})"

    def fitted(self):
        """(what the generator fitted, what to change) when a placed band's width is the room an edge left, or
        None.  A set that then cannot be built most often had too little room for its vias."""
        w1, w2 = (self.band1["ro"] - self.band1["ri"]), (self.band2["ro"] - self.band2["ri"])
        if self.placed(1) and self.placed(2):
            return (f"both RX bands into the room between the board edges: RX1 came out {w1:.2f} mm wide, RX2 "
                    f"{w2:.2f} mm", "the bands are too narrow: raise OUTER_EDGE_RADIUS_MM, lower INNER_EDGE_RADIUS_MM, "
                    "or move BAND_SPLIT towards the set that failed")
        if self.placed(2) and self.outline_given:
            return (f"the RX2 band into the room up to the outline: it came out {w2:.2f} mm wide",
                    "the band is too narrow: raise OUTER_EDGE_RADIUS_MM, move the RX1 band in, or give the RX2 band")
        if self.placed(1) and self.bore_given:
            return (f"the RX1 band into the room from the bore: it came out {w1:.2f} mm wide",
                    "the band is too narrow: lower INNER_EDGE_RADIUS_MM, move the RX2 band out, or give the RX1 band")
        return None

    def lines(self):
        """Text lines for the summary and the record."""
        f = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
        how = {"radii": "INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM as given", "centre": "RX_R_BASE_MM / RX_A_MM as given",
               "placed": "placed by the generator"}
        out = [f"layout: {self.describe()}"]
        for k, b in ((1, self.band1), (2, self.band2)):
            a = (b["ro"] - b["ri"]) / 2.0
            out.append(f"  RX{k} band r = {f(b['ri'])} ... {f(b['ro'])} mm (RX_R_BASE_MM {f((b['ri'] + b['ro']) / 2)}, "
                       f"RX_A_MM {f(a)}): {how[b['how']]}")
        out.append(f"  bore r = {f(self.bore)} mm ({self.bore_from}), outline r = {f(self.outline)} mm ({self.outline_from})")
        g = self.gap_name()
        out.append(f"  set 1 copper reaches r = {f(self.reach1)} mm; set 2 copper starts at r = {f(self.inner2)} mm: "
                   f"gap {f(self.gap_expected)} mm"
                   + (f" ({g} = {f(self.gap_required)})" if self.placed(1) or self.placed(2)
                      else f" (measured; at least {g} = {f(self.gap_required)} needed)"))
        return out


def combination(b1, b2, bore, outline, gap):
    """The number (1 ... 32) of what is given, in the order of the table on the wiki page Dual Layout: the bands first
    (both, RX1 only, RX2 only, none), then the outline, the bore and TRACK_GAP_MM.  None = not given."""
    group = 0 if b1 is not None and b2 is not None else 1 if b1 is not None else 2 if b2 is not None else 3
    return 8 * group + 4 * (outline is not None) + 2 * (bore is not None) + (gap is not None) + 1


def _num(name, val, file):
    if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
        raise ParameterConflict((name,), f"{name} must be a number greater than 0, or None; it is {val!r} ({file})")
    return float(val)


def band_of(rx, k):
    """The RX band of set k as given in its file: None (all four None) or dict(ri, ro, how, names).  The Single
    Generator's own band rules (BoardLayout.given_band): raises ParameterConflict for a half pair, for both pairs and
    for values that do not make a band."""
    b = BoardLayout.given_band(lambda n: getattr(rx, n, None), f"RX{k} band", RX_FILES[k])
    return None if b is None else dict(ri=b["ri"], ro=b["ro"], how=b["mode"], names=b["given"])


def _placed(ri, ro):
    return dict(ri=ri, ro=ro, how="placed", names={"RX_R_BASE_MM": round((ri + ro) / 2.0, 9),
                                                    "RX_A_MM": round((ro - ri) / 2.0, 9)})


def tx_room(P1):
    """How far set 1's copper reaches past its RX band end (mm): the TX turns, the TX tail, the RX bridging fingers
    and the go-around brackets, widths included (BoardLayout.outer_copper_reach).  P1: set 1's namespace
    (Dual_SetParameters.build)."""
    return BoardLayout.outer_copper_reach(P1)


def _setting(module, name, default):
    """A rotor / board setting, the Single Generator's default when the line is missing or None."""
    v = getattr(module, name, None)
    return default if v is None else v


def ring_vertex_sag(Pk, r):
    """How far the outermost polygon vertices of a rotor ring of radius r reach past r (mm): the ring's arcs are
    chords whose vertices sit on a slightly larger circle (RotorBuilder.sector_polygon).  With
    ROTOR_ARC_STEPS_PER_SECTOR = "auto" that is ROTOR_CHORD_TOLERANCE_MM; with a number of steps it follows from
    the chord angle.  Pk: the set's namespace (Dual_SetParameters.build)."""
    steps = getattr(Pk, "ROTOR_ARC_STEPS_PER_SECTOR", "auto")
    if isinstance(steps, str) and steps.strip().lower() == "auto":
        return float(_setting(Pk, "ROTOR_CHORD_TOLERANCE_MM", 0.001))
    half = float(Pk.ROTOR_AUTO_DUTY) * 2.0 * math.pi / int(Pk.LOOPS) / max(8, int(steps)) / 2.0
    return float(r) * (1.0 / math.cos(half) - 1.0)


def outer_room(P2, board):
    """From the RX2 band end to the outline (mm): the Single Generator's own rule (BoardLayout.outer_edge_room: the
    TX turns and tail, the fingers, the margins), and, when ring 2 of the rotor covers the TX2 turns
    (ROTOR_AUTO_COVER_TX, according_to_stator), also room for its overhang past the outermost turn as RotorBuilder
    limits the ring: ROTOR_AUTO_EDGE_CLEARANCE_MM inside the outline, then LAYOUT_TOLERANCE_MM (board) of slack
    or, when they need more, half the edge line plus the polygon vertices (ring_vertex_sag), which the ring also
    keeps inside the outline (the disc has the stator's outline).  P2: set 2's namespace
    (Dual_SetParameters.build); the rotor settings default as in the Single Generator."""
    room = BoardLayout.outer_edge_room(P2)
    if str(getattr(P2, "ROTOR_MODE", "")).lower() == "according_to_stator" \
            and bool(_setting(P2, "ROTOR_AUTO_COVER_TX", RB.DEFAULT_COVER_TX)):
        ring = BoardLayout.tx_ring(P2, 0.0)
        overhang = _setting(P2, "ROTOR_AUTO_TX_OVERHANG_MM", RB.DEFAULT_TX_OVERHANG_MM)
        clearance = _setting(P2, "ROTOR_AUTO_EDGE_CLEARANCE_MM", 0.0)
        edge_line = _setting(P2, "EDGE_LINE_WIDTH_MM", 0.0)
        tol = _setting(board, "LAYOUT_TOLERANCE_MM", 0.0)
        try:
            edge = ring["outer_copper_edge"] + float(overhang)
            sag = ring_vertex_sag(P2, edge) if hasattr(P2, "LOOPS") else 0.0
            room = max(room, edge + float(clearance) + max(float(tol), float(edge_line) / 2.0 + sag))
        except (TypeError, ValueError):
            pass                                   # a bad value: the Single Generator's checks report it
    return room


def inner_margin(P2):
    """From the RX2 band start inwards to the set's innermost copper (mm): the inner-tip vias (set 2's own
    VIA_DIAMETER_MM), or half a trace."""
    return max(float(P2.RX_TRACE_WIDTH_MM) / 2.0, float(P2.VIA_DIAMETER_MM) / 2.0)


# ---------------------------------------------------------------------------------------------------- what is refused
def _refuse_no_band(bore, outline):
    """No band given and not both edges (combinations 25 ... 30): there is nothing to size the bands from."""
    names = SP.BAND_NAMES + SP.EDGE_NAMES
    band = ("give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or "
            "Dual_RX2_Parameters.py)")
    if bore is None and outline is None:
        raise ParameterConflict(names, f"no RX band and no board edge is given: there is nothing to size the bands "
                                f"from. {band[0].upper() + band[1:]}, or both board edges (INNER_EDGE_RADIUS_MM and "
                                f"OUTER_EDGE_RADIUS_MM, {BOARD_FILE}) to fit both bands between them")
    missing, given = ("OUTER_EDGE_RADIUS_MM", "the bore") if outline is None else ("INNER_EDGE_RADIUS_MM", "the outline")
    raise ParameterConflict(names, f"no RX band is given and of the board edges only {given}: {missing} is missing to "
                            f"fit both bands between the edges. Set {missing} ({BOARD_FILE}), or {band}")


def _refuse_order(b1, b2):
    raise ParameterConflict(SP.BAND_NAMES, f"the RX1 band ({b1['ri']:g} ... {b1['ro']:g} mm) must lie inside the RX2 "
                            f"band ({b2['ri']:g} ... {b2['ro']:g} mm): set 1 is the inner set. To have the coils "
                            f"of Dual_RX2 inside, swap the two sets' files: Dual_RX1 / TX1 / Rotor1 / "
                            f"IC1_Parameters.py with Dual_RX2 / TX2 / Rotor2 / IC2_Parameters.py, and "
                            f"TERMINAL_1_DEG with TERMINAL_2_DEG ({BOARD_FILE})")


# ---------------------------------------------------------------------------------------------- placing a band
def _fit_both(B, e_in, e_out, inset, room1, gap, g, margin2, room2):
    """No band given, both edges (combinations 31, 32): the room between the edges, less the inset, the TX1 ring,
    the gap, the RX2 vias and the TX2 ring with the outer margin, shared by BAND_SPLIT."""
    fixed = inset + room1 + gap + margin2 + room2
    free = e_out - e_in - fixed
    split = float(B.BAND_SPLIT)
    if not 0.0 < split < 1.0:
        raise ParameterConflict(("BAND_SPLIT",), f"BAND_SPLIT must be between 0 and 1 (both excluded); it is "
                                f"{split!r} ({BOARD_FILE})")
    if free <= 0.0:
        raise ParameterConflict(SP.EDGE_NAMES + (g,), f"the board is too small for two RX bands: from "
                                f"the bore ({e_in:g} mm) to the outline ({e_out:g} mm) there are {e_out - e_in:g} mm, "
                                f"and {fixed:.2f} mm of that go to INNER_EDGE_INSET_MM ({inset:g}), the TX1 ring "
                                f"({room1:.2f}), {g} ({gap:g}), the RX2 vias ({margin2:.2f}) and the TX2 "
                                f"ring with the outer margin ({room2:.2f}). Raise OUTER_EDGE_RADIUS_MM above "
                                f"{e_in + fixed:.2f} mm, lower the bore, or lower the TX turns, pitches, offsets "
                                f"and margins")
    w1 = split * free
    ri1 = e_in + inset
    ro1 = ri1 + w1
    ri2 = ro1 + room1 + gap + margin2
    ro2 = e_out - room2
    return _placed(ri1, ro1), _placed(ri2, ro2)


def _place_rx2(b1, e_out, room1, gap, g, margin2, room2):
    """RX1 given, RX2 not (combinations 9 ... 16): RX2 starts the gap past set 1's copper and its vias' room, and runs
    to the outline less the TX2 ring and the margins when the outline is given, else as wide as RX1."""
    ri2 = b1["ro"] + room1 + gap + margin2
    if e_out is None:
        a = (b1["ro"] - b1["ri"]) / 2.0
        return _placed(ri2, ri2 + 2.0 * a)
    ro2 = e_out - room2
    if ro2 <= ri2:
        raise ParameterConflict(("OUTER_EDGE_RADIUS_MM",) + tuple(b1["names"]) + (g,), f"the outline ({e_out:g} mm) "
                                f"leaves no room for the RX2 band: placed {g} ({gap:g} mm) past set 1's copper, which "
                                f"reaches r = {b1['ro'] + room1:.2f} mm, the band would start at r = {ri2:.2f} mm, and "
                                f"the TX2 ring with the outer margin needs {room2:.2f} mm inside the outline, so it would "
                                f"end at r = {ro2:.2f} mm. Raise OUTER_EDGE_RADIUS_MM well above {ri2 + room2:.2f} mm, "
                                f"move the RX1 band in, lower {g}, or give the RX2 band")
    return _placed(ri2, ro2)


def _place_rx1(b2, e_in, inset, room1, gap, g, margin2):
    """RX2 given, RX1 not (combinations 17 ... 24): RX1 ends the gap and set 1's TX ring inside set 2's copper, and
    starts at the bore plus INNER_EDGE_INSET_MM when the bore is given, else it is as wide as RX2."""
    ro1 = b2["ri"] - margin2 - gap - room1
    if e_in is None:
        a = (b2["ro"] - b2["ri"]) / 2.0
        ri1 = ro1 - 2.0 * a
        if ri1 - inset <= 0.0:
            raise ParameterConflict(SP.BAND_NAMES + (g,), f"the RX1 band placed inside the RX2 band ({b2['ri']:g} ... "
                                    f"{b2['ro']:g} mm, same half width {a:g} mm) across {g} ({gap:g}) and the TX1 ring "
                                    f"({room1:.2f} mm) would run from r = {ri1:.2f} to {ro1:.2f} mm: the bore would "
                                    f"have a zero or negative radius. Move the RX2 band out, lower the gap, give "
                                    f"INNER_EDGE_RADIUS_MM (the band then starts at the bore plus INNER_EDGE_INSET_MM), "
                                    f"or give both bands")
        return _placed(ri1, ro1)
    ri1 = e_in + inset
    if ri1 >= ro1:
        raise ParameterConflict(("INNER_EDGE_RADIUS_MM", "INNER_EDGE_INSET_MM") + tuple(b2["names"]) + (g,),
                                f"the bore ({e_in:g} mm) leaves no room for the RX1 band: it would start at r = "
                                f"{ri1:.2f} mm (the bore + INNER_EDGE_INSET_MM {inset:g}) and, placed {g} ({gap:g} mm) "
                                f"and the TX1 ring ({room1:.2f} mm) inside set 2's copper, end at r = {ro1:.2f} mm. "
                                f"Lower INNER_EDGE_RADIUS_MM well below {ro1 - inset:.2f} mm, move the RX2 band out, "
                                f"lower {g}, or give the RX1 band")
    return _placed(ri1, ro1)


def resolve(P):
    """The Layout for these parameters, or ParameterConflict.  Three steps: the bands, the edges, the gap."""
    B = P.BOARD
    e_in, e_out = getattr(B, "INNER_EDGE_RADIUS_MM", None), getattr(B, "OUTER_EDGE_RADIUS_MM", None)
    gap = getattr(B, "TRACK_GAP_MM", None)
    b1, b2 = band_of(P.RX1, 1), band_of(P.RX2, 2)
    if e_in is not None:
        e_in = _num("INNER_EDGE_RADIUS_MM", e_in, BOARD_FILE)
    if e_out is not None:
        e_out = _num("OUTER_EDGE_RADIUS_MM", e_out, BOARD_FILE)
    if e_in is not None and e_out is not None and e_in >= e_out:
        raise ParameterConflict(SP.EDGE_NAMES, f"the board's inner radius (the centre hole, {e_in:g} mm) cannot be "
                                f"larger than its outer radius ({e_out:g} mm)")
    if gap is not None:
        gap = _num("TRACK_GAP_MM", gap, BOARD_FILE)
    combo = combination(b1, b2, e_in, e_out, gap)
    if b1 is None and b2 is None and (e_in is None or e_out is None):
        _refuse_no_band(e_in, e_out)
    if b1 is not None and b2 is not None and b1["ri"] >= b2["ri"]:
        _refuse_order(b1, b2)
    inset = float(B.INNER_EDGE_INSET_MM)
    P1, P2 = SP.build(P, 1), SP.build(P, 2)      # each set in the Single Generator's names (its own vias, clearance)
    g = "TRACK_GAP_MM" if gap is not None else "MIN_CLEARANCE_MM"
    required = gap if gap is not None else max(float(P1.MIN_CLEARANCE_MM), float(P2.MIN_CLEARANCE_MM))
    room1 = tx_room(P1)                          # set 1's copper past the RX1 band end
    margin2 = inner_margin(P2)                   # set 2's copper inside its RX2 band start
    room2 = outer_room(P2, B)                    # from the RX2 band end to the outline (ring 2's overhang included)

    # ---- 1. the bands: one not given is placed across the gap from the other
    if b1 is None and b2 is None:
        b1, b2 = _fit_both(B, e_in, e_out, inset, room1, required, g, margin2, room2)
    elif b2 is None:
        b2 = _place_rx2(b1, e_out, room1, required, g, margin2, room2)
    elif b1 is None:
        b1 = _place_rx1(b2, e_in, inset, room1, required, g, margin2)

    # ---- 2. the edges: as given (the Single Generator checks each against its own set's band), or from the bands
    if e_in is not None:
        bore, bore_from = e_in, "INNER_EDGE_RADIUS_MM"
    else:
        bore, bore_from = b1["ri"] - inset, "RX1 band start - INNER_EDGE_INSET_MM"
        if bore <= 0.0:
            raise ParameterConflict(("INNER_EDGE_INSET_MM",) + tuple(b1["names"]), f"the inset ({inset:g} mm) is not "
                                    f"smaller than the RX1 band start ({b1['ri']:g} mm): the centre hole would have a "
                                    f"zero or negative radius. Lower INNER_EDGE_INSET_MM ({BOARD_FILE}) or move the RX1 "
                                    f"band out")
    if e_out is not None:
        outline, outline_from = e_out, "OUTER_EDGE_RADIUS_MM"
    else:
        outline, outline_from = b2["ro"] + room2, "RX2 band end + the TX2 ring and the margin"

    # ---- 3. the gap between the sets
    reach1 = b1["ro"] + room1
    inner2 = b2["ri"] - margin2
    expected = inner2 - reach1
    if expected < required - 1e-9:
        if b1["how"] == "placed" or b2["how"] == "placed":
            raise AssertionError("a placed band does not keep the gap")      # (cannot happen: it is placed so)
        need = b1["ro"] + room1 + required + margin2
        raise ParameterConflict(SP.BAND_NAMES + (g,), f"the two sets run into each other: set 1's copper reaches r = "
                                f"{reach1:.2f} mm (RX1 band end {b1['ro']:g} + its TX turns, tail and fingers) and set "
                                f"2's copper starts at r = {inner2:.2f} mm (RX2 band start {b2['ri']:g} - its vias), "
                                f"{expected:.2f} mm apart; at least {required:g} mm ({g}) must stay free. Move the RX2 "
                                f"band start to {need:.2f} mm or more, or the RX1 band in, or lower TX1's turns, pitch "
                                f"or offset")
    return Layout(combination=combo, band1=b1, band2=b2, bore=bore, outline=outline, bore_from=bore_from,
                  outline_from=outline_from, bore_given=e_in is not None, outline_given=e_out is not None,
                  gap_setting=gap, gap_required=required, gap_expected=expected, reach1=reach1, inner2=inner2,
                  room1=room1, margin2=margin2, outer_room2=room2)

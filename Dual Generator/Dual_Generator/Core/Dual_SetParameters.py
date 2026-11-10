"""
Dual_SetParameters.py  -  the parameter set of ONE coil set, in the Single Generator's own names.

The dual parameter files hold two sets of RX, TX, rotor and IC values and one board.  The Single Generator's
builders and checks take one namespace with its own names (LOOPS, TX_TURNS, INNER_EDGE_RADIUS_MM, ...), so for each
set the dual generator puts together exactly that:

    board names           from Dual_Board_Parameters.py (the same for both sets)
    RX, TX, rotor, IC     from Dual_RX<k>, Dual_TX<k>, Dual_Rotor<k>, Dual_IC<k>
    a set's own value     for a few board values (OVERRIDES): VIA_DIAMETER_MM, VIA_DRILL_MM, VIA_TYPE and
                          MIN_CLEARANCE_MM in Dual_RX<k>, TX_AC_RESISTANCE_FACTOR in Dual_TX<k>, TANK_CAP_SERIES in
                          Dual_IC<k>.  None there (or no line) = the board's value
    the band, the edges   as Dual_TrackLayout decided them

Which name lives in which dual file (NAMES_BY_FILE) is made from the Single Generator's own table
(ParameterRules.SPEC): a name of its Board_Parameters.py lives in Dual_Board_Parameters.py, one of its
RX_Parameters.py in Dual_RX1 and Dual_RX2, and so on, except the names in MOVED.  So a parameter the Single
Generator gains is a dual parameter at once, in the matching dual file.  The dual checker uses the table to spot a
missing name or a name in the wrong file.  Nothing to edit here.
"""

import re
import types

from Generator.Checks import ParameterRules as SingleRules          # read only: the Single Generator's table
from Generator.Core.Conflict import Report

BOARD_FILE = "Dual_Board_Parameters.py"
KINDS = ("BOARD", "RX", "TX", "ROTOR", "IC")
# the Single Generator's parameter file -> the kind of dual file that holds its names
SINGLE_KIND = {"Board_Parameters.py": "BOARD", "RX_Parameters.py": "RX", "TX_Parameters.py": "TX",
               "Rotor_Parameters.py": "ROTOR", "IC_Parameters.py": "IC"}
# the names whose dual file is not the one their Single Generator file says
MOVED = {
    "EXCITATION_FREQ_HZ": "TX",                     # each set has its own oscillator
    # one rotor disc carries both rings: its outline, bore, thickness, resolution and mask are the board's
    "ROTOR_MODE": "BOARD", "ROTOR_AUTO_EDGE_CLEARANCE_MM": "BOARD", "ROTOR_CUSTOM_OUTLINE_RADIUS_MM": "BOARD",
    "ROTOR_CUSTOM_BORE_RADIUS_MM": "BOARD", "ROTOR_PCB_THICKNESS_MM": "BOARD", "ROTOR_ARC_STEPS_PER_SECTOR": "BOARD",
    "ROTOR_CHORD_TOLERANCE_MM": "BOARD", "ROTOR_SOLDER_MASK_EXPANSION_MM": "BOARD",
}
# board values that a set file may set for its own set (None there = the board's value): name -> kind of set file
OVERRIDES = {"VIA_DIAMETER_MM": "RX", "VIA_DRILL_MM": "RX", "VIA_TYPE": "RX", "MIN_CLEARANCE_MM": "RX",
             "TX_AC_RESISTANCE_FACTOR": "TX", "TANK_CAP_SERIES": "IC"}
# the values only a dual board has (Dual_ParameterRules.DUAL_SPEC checks them), all in the board file
BOARD_DUAL = ("TRACK_GAP_MM", "BAND_SPLIT", "LAYOUT_TOLERANCE_MM", "TERMINAL_1_DEG", "TERMINAL_2_DEG",
              "TX_FREQ_SEPARATION_MIN", "TX_FREQ_RATIO_MAX_ORDER", "TX_FREQ_RATIO_TOLERANCE",
              "ROTOR_START_ANGLE_ZERO", "ROTOR_TRACK_GAP_MM", "ROTOR_1_TO_RX2_MM", "ROTOR_2_TO_RX1_MM")


def _single_names_by_kind():
    """{kind: (names, in the Single Generator's order)}, the exceptions of MOVED applied."""
    out = {kind: [] for kind in KINDS}
    for file, name, _kind, _opt, _active in SingleRules.SPEC:
        kind = MOVED.get(name, SINGLE_KIND.get(file))
        if kind is not None and name not in out[kind]:
            out[kind].append(name)
    return {kind: tuple(names) for kind, names in out.items()}


_BY_KIND = _single_names_by_kind()
BOARD_SHARED = _BY_KIND["BOARD"]                    # the Single Generator's names in the board file
RX_NAMES, TX_NAMES, ROTOR_NAMES, IC_NAMES = _BY_KIND["RX"], _BY_KIND["TX"], _BY_KIND["ROTOR"], _BY_KIND["IC"]
SET_OVERRIDES = {kind: tuple(n for n, k in OVERRIDES.items() if k == kind) for kind in ("RX", "TX", "IC")}

BAND_NAMES = ("INSIDE_RADIUS_MM", "OUTSIDE_RADIUS_MM", "RX_R_BASE_MM", "RX_A_MM")
EDGE_NAMES = ("INNER_EDGE_RADIUS_MM", "OUTER_EDGE_RADIUS_MM")


def set_file(kind, k):
    """The dual file of set k for a kind of names: set_file("RX", 1) = "Dual_RX1_Parameters.py"."""
    return BOARD_FILE if kind == "BOARD" else f"Dual_{kind.capitalize() if kind == 'ROTOR' else kind}{k}_Parameters.py"


NAMES_BY_FILE = {BOARD_FILE: BOARD_SHARED + BOARD_DUAL}
for _kind, _names in (("RX", RX_NAMES), ("TX", TX_NAMES), ("ROTOR", ROTOR_NAMES), ("IC", IC_NAMES)):
    for _k in (1, 2):
        NAMES_BY_FILE[set_file(_kind, _k)] = _names + SET_OVERRIDES.get(_kind, ())
PARAMETER_FILES = tuple(NAMES_BY_FILE)

# the Single Generator's file names in its messages -> the dual file of set k
SINGLE_FILE_WORDS = {k: {single: set_file(kind, k) for single, kind in SINGLE_KIND.items()} for k in (1, 2)}


def modules(P, k):
    """(RX, TX, ROTOR) parameter modules of set k (1 or 2)."""
    if k == 1:
        return P.RX1, P.TX1, P.ROTOR1
    if k == 2:
        return P.RX2, P.TX2, P.ROTOR2
    raise ValueError("a set is 1 (inner) or 2 (outer)")


def ic_module(P, k):
    """The IC parameter module of set k (Dual_IC<k>_Parameters.py), or None when it could not be loaded."""
    if k not in (1, 2):
        raise ValueError("a set is 1 (inner) or 2 (outer)")
    return getattr(P, f"IC{k}", None)


def set_modules(P, k):
    """{kind: the parameter module of set k} for RX, TX, ROTOR and IC (the IC module may be None)."""
    rx, tx, ro = modules(P, k)
    return {"RX": rx, "TX": tx, "ROTOR": ro, "IC": ic_module(P, k)}


def overridden(P, k):
    """{name: value} of the board values that set k sets for itself (OVERRIDES; a value of None is not one)."""
    mods = set_modules(P, k)
    out = {}
    for name, kind in OVERRIDES.items():
        mod = mods[kind]
        if mod is not None and getattr(mod, name, None) is not None:
            out[name] = getattr(mod, name)
    return out


def build(P, k, band=None, edges=None):
    """The namespace of set k for the Single Generator's builders and checks.
      band   : {single name: value} for the RX band, as Dual_TrackLayout decided it (the four band names not in
               it are set to None); None = the set's file values as they are
      edges  : (bore, outline) for INNER_EDGE_RADIUS_MM / OUTER_EDGE_RADIUS_MM; None = the board file's values
    A name missing from a dual file is left out, so that the Single Generator's checker reports it."""
    mods = set_modules(P, k)
    d = {}
    for n in BOARD_SHARED:
        if hasattr(P.BOARD, n):
            d[n] = getattr(P.BOARD, n)
    for kind, names in (("RX", RX_NAMES), ("TX", TX_NAMES), ("ROTOR", ROTOR_NAMES), ("IC", IC_NAMES)):
        src = mods[kind]
        for n in names:
            if src is not None and hasattr(src, n):
                d[n] = getattr(src, n)
    d.update(overridden(P, k))
    if band is not None:
        for n in BAND_NAMES:
            d[n] = None
        d.update(band)
    if edges is not None:
        d["INNER_EDGE_RADIUS_MM"], d["OUTER_EDGE_RADIUS_MM"] = edges
    return types.SimpleNamespace(**d)


_FILE_AT_END = re.compile(r"\((Dual_\w+_Parameters\.py)\)\s*$")


def dual_file_of(name, k, own=()):
    """The dual file of set k that holds the parameter `name`, or None.  own: the board values set k sets for itself
    (overridden), which are then in the set's file."""
    if name in OVERRIDES and name in own:
        return set_file(OVERRIDES[name], k)
    if name in BOARD_SHARED or name in BOARD_DUAL:
        return BOARD_FILE
    for kind, names in (("RX", RX_NAMES), ("TX", TX_NAMES), ("ROTOR", ROTOR_NAMES), ("IC", IC_NAMES)):
        if name in names:
            return set_file(kind, k)
    return None


def rename_single_files(text, k, own=()):
    """A Single Generator message with its file names replaced by the dual files of set k.  A few names live in
    another dual file than the Single's file suggests (MOVED, and a board value the set sets for itself): the file
    named at the end of a message follows the name the message starts with."""
    for old, new in SINGLE_FILE_WORDS[k].items():
        text = text.replace(old, new)
    m = re.match(r"([A-Z][A-Z0-9_]*)\b", text)
    file = dual_file_of(m.group(1), k, own) if m else None
    if file is not None:
        text = _FILE_AT_END.sub(f"({file})", text)
    return text


def for_set(rep, k, P=None):
    """A Single Generator report as findings of set k: each message with "set k: " in front and the Single
    Generator's file names replaced by set k's dual files (rename_single_files; with P, a board value that set k
    sets for itself is named in the set's file).  Returns a new Report."""
    own = tuple(overridden(P, k)) if P is not None else ()
    out = Report()
    out.items = [(level, f"set {k}: " + rename_single_files(msg, k, own), names) for level, msg, names in rep.items]
    return out

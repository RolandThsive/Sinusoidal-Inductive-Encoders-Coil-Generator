"""
Dual_LeadCutting_SilkscreenSuggestion.py  -  the last step of a dual generation: a silkscreen suggestion for cutting
the leads, drawn into the finished Stator.kicad_pcb (Dual_RunCoilGenerator.py calls it after the stator is written).

The work is done by the Single Coil Set Generator's own step (Generator/Stator/LeadCutting_SilkscreenSuggestion.py), run
on the two sets of the dual board.  This file only says what differs on a dual board:

    the sets        set 1 and set 2, each with its own RX and TX values and its own terminal angle (TERMINAL_1_DEG /
                    TERMINAL_2_DEG, Dual_Board_Parameters.py), so the lead names carry the set number:
                    SIN1_1, SIN1_2, ... and TX1_1 TOP, TX1_2 IN2 (each TX end with its layer)
    the settings    Parameters/Dual_SilkScreenSuggestion_Parameters.py, whose break layers default to Top and Inner 1
                    (the RX layers of a dual set), or to Top and Bottom on a 2-layer board (PCB_LAYERS = 2)
    the board       the board values are in Dual_Board_Parameters.py (P.BOARD); a set that sets its own
                    VIA_DIAMETER_MM or MIN_CLEARANCE_MM (Dual_RX<k>_Parameters.py) can only make the suggested vias
                    keep more room: the larger via and clearance of the two sets are used for every via

Every warning about one set starts with "set 1: " or "set 2: ".  No copper is changed; the step never fails a
generation.

    result = add_to_file(path, P)       path: the written Stator.kicad_pcb;  P: Dual_Parameters
    append_record(record_path, result)  adds the result to Parameters.txt
"""

import types

from Dual_Generator.Core import Dual_SetParameters as SP
from Generator.Stator import LeadCutting_SilkscreenSuggestion as _single
from Generator.Stator.LeadCutting_SilkscreenSuggestion import (  # noqa: F401   (the same functions, used by the tests)
    FONT_FILE, Result, _dang, find_rx_break, find_tx_end, find_tx_sites, load_font, record_lines)

PARAMETER_MODULE = "Dual_SilkScreenSuggestion_Parameters"
PARAMETER_FILE = PARAMETER_MODULE + ".py"

DEFAULTS = dict(_single.DEFAULTS, SILKSCREEN_BREAK_LAYERS=["F.Cu", "In1.Cu"])


def defaults(P=None):
    """DEFAULTS, with Top and Bottom as the break layers when P is a 2-layer board."""
    if P is not None and getattr(P.BOARD, "PCB_LAYERS", None) == 2:
        return dict(DEFAULTS, SILKSCREEN_BREAK_LAYERS=["F.Cu", "B.Cu"])
    return DEFAULTS


def Settings(P=None):
    """The values of Dual_SilkScreenSuggestion_Parameters.py, checked (the Single Coil Set Generator's Settings); a
    value that is missing or wrong falls back to defaults(P)."""
    return _single.Settings(PARAMETER_MODULE, defaults(P))


def board_values(P):
    """The board values for the step: Dual_Board_Parameters.py, with the larger VIA_DIAMETER_MM and MIN_CLEARANCE_MM
    of the two sets (a set may set its own, Dual_SetParameters.OVERRIDES)."""
    d = {n: getattr(P.BOARD, n) for n in dir(P.BOARD) if n.isupper()}
    for name in ("VIA_DIAMETER_MM", "MIN_CLEARANCE_MM"):
        values = [v for v in (SP.overridden(P, k).get(name, d.get(name)) for k in (1, 2)) if v is not None]
        if values:
            d[name] = max(values)
    return types.SimpleNamespace(**d)


def Board(text, P):
    """The copper of the written dual stator file (the Single Coil Set Generator's Board, with the dual board
    values)."""
    return _single.Board(text, board_values(P))


def sets(P):
    """The two coil sets of the dual board: (label, terminal angle, RX values, TX values).  The angles are read as
    numbers inside the step, so a bad value becomes one of its warnings and never stops the generation."""
    B = P.BOARD
    return [(1, getattr(B, "TERMINAL_1_DEG", None), P.RX1, P.TX1), (2, getattr(B, "TERMINAL_2_DEG", None), P.RX2, P.TX2)]


def suggest(text, P, settings, font=None):
    """The marks for the written dual stator text.  Returns (new text or None, Result)."""
    return _single.suggest(text, board_values(P), settings, font, sets(P))


def add_to_file(path, P, quiet=False):
    """Read the written dual stator file, add the suggestion, write it back.  Prints what it did.  Returns the Result."""
    return _single.add_to_file(path, board_values(P), quiet, sets(P), Settings(P))


def append_record(record_path, res):
    """Append the result and a verbatim copy of Dual_SilkScreenSuggestion_Parameters.py to Parameters.txt."""
    return _single.append_record(record_path, res, PARAMETER_MODULE)

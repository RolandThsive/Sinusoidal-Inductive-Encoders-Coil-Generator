"""
Dual_LeadCutting_SilkscreenSuggestion.py  -  the last step of a dual generation: a silkscreen suggestion for cutting
the leads, drawn into the finished Stator.kicad_pcb (Dual_RunCoilGenerator.py calls it after the stator is written).

The work is done by the Single Generator's own step (Generator/Stator/LeadCutting_SilkscreenSuggestion.py), run on
the two sets of the dual board.  This file only says what differs on a dual board:

    the sets        set 1 and set 2, each with its own RX and TX values and its own terminal angle (TERMINAL_1_DEG /
                    TERMINAL_2_DEG, Dual_Board_Parameters.py), so the lead names carry the set number:
                    SIN1_1, SIN1_2, ... and TX1_1 TOP, TX1_2 IN2 (each TX end with its layer)
    the settings    Parameters/Dual_SilkScreenSuggestion_Parameters.py, whose break layers default to Top and Inner 1
                    (the RX layers of a dual set)
    the board       the board values are in Dual_Board_Parameters.py (P.BOARD)

Every warning about one set starts with "set 1: " or "set 2: ".  No copper is changed; the step never fails a
generation.

    result = add_to_file(path, P)       path: the written Stator.kicad_pcb;  P: Dual_Parameters
    append_record(record_path, result)  adds the result to Parameters.txt
"""

from Generator.Stator import LeadCutting_SilkscreenSuggestion as _single
from Generator.Stator.LeadCutting_SilkscreenSuggestion import (  # noqa: F401   (the same functions, used by the tests)
    FONT_FILE, Result, _dang, find_rx_break, find_tx_end, find_tx_sites, load_font, record_lines)

PARAMETER_MODULE = "Dual_SilkScreenSuggestion_Parameters"
PARAMETER_FILE = PARAMETER_MODULE + ".py"

DEFAULTS = dict(_single.DEFAULTS, SILKSCREEN_BREAK_LAYERS=["F.Cu", "In1.Cu"])


def Settings():
    """The values of Dual_SilkScreenSuggestion_Parameters.py, checked (the Single Generator's Settings)."""
    return _single.Settings(PARAMETER_MODULE, DEFAULTS)


def Board(text, P):
    """The copper of the written dual stator file (the Single Generator's Board, with the dual board values)."""
    return _single.Board(text, P.BOARD)


def sets(P):
    """The two coil sets of the dual board: (label, terminal angle, RX values, TX values).  The angles are read as
    numbers inside the step, so a bad value becomes one of its warnings and never stops the generation."""
    B = P.BOARD
    return [(1, getattr(B, "TERMINAL_1_DEG", None), P.RX1, P.TX1), (2, getattr(B, "TERMINAL_2_DEG", None), P.RX2, P.TX2)]


def suggest(text, P, settings, font=None):
    """The marks for the written dual stator text.  Returns (new text or None, Result)."""
    return _single.suggest(text, P.BOARD, settings, font, sets(P))


def add_to_file(path, P, quiet=False):
    """Read the written dual stator file, add the suggestion, write it back.  Prints what it did.  Returns the Result."""
    return _single.add_to_file(path, P.BOARD, quiet, sets(P), Settings())


def append_record(record_path, res):
    """Append the result and a verbatim copy of Dual_SilkScreenSuggestion_Parameters.py to Parameters.txt."""
    return _single.append_record(record_path, res, PARAMETER_MODULE)

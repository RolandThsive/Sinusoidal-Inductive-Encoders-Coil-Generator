"""
harness.py  -  the Dual Generator's side of the regression plumbing (regression/RegressionHarness.py does the work):
it loads the Dual Generator once and runs it in this process, with parameter values that live only in memory (the
parameter files are never touched), writing boards into a temporary folder.

    run(overrides, args)      run Dual_RunCoilGenerator.main(args) with the overrides applied; returns Result
    check(overrides)          run(overrides, ["--check", "--no-color"])
    write(overrides, args)    a full run that writes into a fresh temporary folder; Result.folder holds the files
    BOARDS                    the test boards: the BoardNNN-... folders of DualGenerator_regression, in order
    board(name)               the board written from its folder's parameter files, made once per process and shared
                              by the tests (test_boards, test_invariants, test_silkscreen)
    board_values(name)        the overrides the board's parameter files amount to

Overrides name the dual parameter module and the value: {"BOARD.DUAL_MODE": 1, "RX2.LOOPS": 8,
"TX1.TX_WIRING": "parallel", "FIXED.PCB_LAYERS": 2, "SILK.SILKSCREEN_SIDES": "top", "BOARD.DUAL_MODE": DELETE}.
The modules are BOARD, RX1, RX2, TX1, TX2, ROTOR1, ROTOR2, IC1, IC2, FIXED (the ten Dual_..._Parameters.py files)
and SILK (Dual_SilkScreenSuggestion_Parameters.py).  DELETE removes the name, as if its line were missing from
the file.  Every run starts from the values of Board001-default (the suite's first board folder), whatever the
generator's own parameter files hold: nothing an earlier test set survives.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))               # .../DualGenerator_regression/tests
SUITE = os.path.dirname(HERE)                                    # .../DualGenerator_regression
REGRESSION = os.path.dirname(SUITE)                              # .../regression
REPO = os.path.dirname(REGRESSION)
PROJECT = os.path.join(REPO, "Dual Generator")
SINGLE = os.path.join(REPO, "Single Generator")
RESOURCES = os.path.join(REPO, "resources")

sys.dont_write_bytecode = True
for _p in (PROJECT, RESOURCES, REGRESSION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import Dual_Generator  # noqa: E402,F401   (puts the Parameters folder and the Single Generator on the path)
from Dual_Generator.Run import Dual_RunCoilGenerator as R  # noqa: E402
import Dual_Parameters as P  # noqa: E402
import Dual_SilkScreenSuggestion_Parameters as SILK  # noqa: E402
import RegressionHarness as RH  # noqa: E402

DELETE = RH.DELETE
UPDATE_REFERENCES = RH.UPDATE_REFERENCES
KEEP_OUTPUT = RH.KEEP_OUTPUT
MODULES = {"BOARD": P.BOARD, "RX1": P.RX1, "RX2": P.RX2, "TX1": P.TX1, "TX2": P.TX2, "ROTOR1": P.ROTOR1,
           "ROTOR2": P.ROTOR2, "IC1": P.IC1, "IC2": P.IC2, "FIXED": P.FIXED, "SILK": SILK}
PARAMETER_FILES = RH.SUITES["dual"]["files"]     # {parameter file: the module it feeds}


class Result(RH.Result):
    """What one run did (RegressionHarness.Result), with the parameter values as the run saw them."""

    PROJECT = PROJECT

    def __init__(self, rc, out, err, folder=None, params=None):
        super().__init__(rc, out, err, folder, params)
        self.params = self.snapshot         # {module: {name: value}} as the run saw it (the overrides applied)

    def p(self, module, name):
        """A parameter value as the run saw it, e.g. res.p("RX2", "LOOPS")."""
        return self.params[module][name]

    @property
    def stator_path(self):
        return self.path(self.p("BOARD", "STATOR_FILE"))

    @property
    def rotor_path(self):
        return self.path(self.p("BOARD", "ROTOR_FILE"))

    def silk_on(self):
        return bool(self.params["SILK"].get("SILKSCREEN_SUGGESTION", True))


S = RH.Suite("Dual", MODULES, PARAMETER_FILES, os.path.join(PROJECT, "Parameters"), R.main, "BOARD.OUTPUT_DIR", SUITE,
             Result)
restore, apply, run, check, write, temp_root = S.restore, S.apply, S.run, S.check, S.write, S.temp_root
board, board_values, reference_path, snapshot = S.board, S.board_values, S.reference_path, S.snapshot
BOARDS = list(S.boards())


# ---------------------------------------------------------------------------------------------- the checker cases' base
# Board001-default describes the R_145 board (DUAL_MODE 2).  MODE1_BASE is the earlier layout that most of the
# checker cases were written against: DUAL_MODE 1, the bands fitted between the edges 8.5 / 29.5 with a 0.5 mm gap,
# three TX turns per layer.
MODE1_BASE = {
    "BOARD.DUAL_MODE": 1, "BOARD.INNER_EDGE_RADIUS_MM": 8.5, "BOARD.OUTER_EDGE_RADIUS_MM": 29.5,
    "BOARD.TRACK_GAP_MM": 0.5, "BOARD.MIN_CLEARANCE_MM": 0.2, "BOARD.PCB_THICKNESS_MM": 1.6,
    "BOARD.PAGE_SIZE_MM": (200, 200),
    "RX1.INSIDE_RADIUS_MM": None, "RX1.OUTSIDE_RADIUS_MM": None, "RX1.RX_R_BASE_MM": None, "RX1.RX_A_MM": None,
    "RX2.INSIDE_RADIUS_MM": None, "RX2.OUTSIDE_RADIUS_MM": None, "RX2.RX_R_BASE_MM": None, "RX2.RX_A_MM": None,
    "RX1.RX_TRACE_WIDTH_MM": 0.2, "RX2.RX_TRACE_WIDTH_MM": 0.2,
    "TX1.TX_TURNS": 3, "TX1.TX_PITCH_MM": 0.6, "TX1.TX_TRACE_WIDTH_MM": 0.2, "TX1.TX_INSIDE_VIA_DISTANCE_MM": 0.1,
    "TX2.TX_TURNS": 3, "TX2.TX_PITCH_MM": 0.6, "TX2.TX_TRACE_WIDTH_MM": 0.2, "TX2.TX_INSIDE_VIA_DISTANCE_MM": 0.3,
    "TX2.TX_OFFSET_MM": 1.1,
}
BAND1 = {"RX1.INSIDE_RADIUS_MM": 9.7, "RX1.OUTSIDE_RADIUS_MM": 16.05}
BAND2_CENTRE = {"RX2.RX_R_BASE_MM": 22.725, "RX2.RX_A_MM": 3.175}
NO_EDGES = {"BOARD.INNER_EDGE_RADIUS_MM": None, "BOARD.OUTER_EDGE_RADIUS_MM": None}


def mode1(**extra):
    d = dict(MODE1_BASE)
    d.update(extra)
    return d

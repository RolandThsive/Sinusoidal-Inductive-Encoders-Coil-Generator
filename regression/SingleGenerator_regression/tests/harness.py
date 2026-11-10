"""
harness.py  -  the Single Generator's side of the regression plumbing (regression/RegressionHarness.py does the
work): it loads the generator once and runs it in this process, with parameter values that live only in memory (the
parameter files are never touched), writing boards into a temporary folder.

    run(overrides, args)      run RunCoilGenerator.main(args) with the overrides applied; returns Result
    check(overrides)          run(overrides, ["--check", "--no-color"])
    write(overrides, args)    a full run that writes into a fresh temporary folder; Result.folder holds the files
    BOARDS                    the test boards: the BoardNNN-... folders of SingleGenerator_regression, in order
    board(name)               the board written from its folder's parameter files, made once per process and shared
                              by the tests (test_boards, test_invariants, test_silkscreen)
    board_values(name)        the overrides the board's parameter files amount to

Overrides: {"LOOPS": 8, "RX_TABS": "none", "SILK.SILKSCREEN_SIDES": "top", "TX_TURNS": DELETE}.  A plain name
is a value of Parameters (the gathered module every part of the generator reads); "SILK." names a value of
SilkScreenSuggestion_Parameters.py; DELETE removes the name, as if its line were missing from the file.
Every run starts from the values of Board001-default (the suite's first board folder), whatever the generator's
own parameter files hold: nothing an earlier test set survives.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))               # .../SingleGenerator_regression/tests
SUITE = os.path.dirname(HERE)                                    # .../SingleGenerator_regression
REGRESSION = os.path.dirname(SUITE)                              # .../regression
REPO = os.path.dirname(REGRESSION)
PROJECT = os.path.join(REPO, "Generators", "Single Generator")
RESOURCES = os.path.join(REPO, "Generators", "resources")

sys.dont_write_bytecode = True                                   # the suite leaves no __pycache__ behind
for _p in (PROJECT, RESOURCES, REGRESSION):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import Generator  # noqa: E402,F401   (puts the Parameters folder on the path)
from Generator.Run import RunCoilGenerator as R  # noqa: E402
import Parameters as P  # noqa: E402
import SilkScreenSuggestion_Parameters as SILK  # noqa: E402
import RegressionHarness as RH  # noqa: E402

DELETE = RH.DELETE
UPDATE_REFERENCES = RH.UPDATE_REFERENCES
KEEP_OUTPUT = RH.KEEP_OUTPUT
MODULES = {"": P, "SILK": SILK}
PARAMETER_FILES = RH.SUITES["single"]["files"]     # {parameter file: the module it feeds}


class Result(RH.Result):
    """What one run did (RegressionHarness.Result), with the parameter values as the run saw them."""

    PROJECT = PROJECT

    def __init__(self, rc, out, err, folder=None, params=None):
        super().__init__(rc, out, err, folder, params)
        self.params = self.snapshot.get("", {})    # every value of Parameters as the run saw it (overrides applied)
        self.silk = self.snapshot.get("SILK", {})  # the same for SilkScreenSuggestion_Parameters.py

    @property
    def stator_path(self):
        return self.path(self.params.get("STATOR_FILE", P.STATOR_FILE)) if self.folder else None

    @property
    def rotor_path(self):
        return self.path(self.params.get("ROTOR_FILE", P.ROTOR_FILE)) if self.folder else None


S = RH.Suite("Single", MODULES, PARAMETER_FILES, os.path.join(PROJECT, "Parameters"), R.main, "OUTPUT_DIR", SUITE,
             Result)
restore, apply, run, check, write, temp_root = S.restore, S.apply, S.run, S.check, S.write, S.temp_root
board, board_values, reference_path = S.board, S.board_values, S.reference_path
BOARDS = list(S.boards())

# the RX band fitted between the board edges (the four band names None); used by the checker cases
FITTED = {"INSIDE_RADIUS_MM": None, "OUTSIDE_RADIUS_MM": None, "RX_R_BASE_MM": None, "RX_A_MM": None}

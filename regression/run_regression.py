"""
run_regression.py  -  runs the regression tests of both generators, or of one (from any folder):

    python regression/run_regression.py                      both suites, one after the other
    python regression/run_regression.py single               the Single Coil Set Generator's suite only
                                                             (dual: the Dual Coil Set Generator's)
    python regression/run_regression.py dual -v              one line per test
    python regression/run_regression.py single -k silkscreen only the tests whose name contains the text (-k may
                                                             be repeated: the tests that contain any of them)
    python regression/run_regression.py single --board Board007 --board Board012
                                                             the board tests on these boards only (by name or by
                                                             number), every other test as usual
    python regression/run_regression.py dual --update-references
                                                             write each board's Stator.kicad_pcb,
                                                             Rotor.kicad_pcb, their .kicad_pro and Parameters.txt anew from the
                                                             generator as it is now (only after reading the
                                                             differences the failing tests printed)
    python regression/run_regression.py single --keep        keep the temporary output folder (its path is printed)

Exit code 0 when every test passed, 1 otherwise.  Needs Python 3.11 or newer and numpy (see requirements.txt), like
the generators.  It writes nothing into the repository except, with --update-references, the board files.
"""

import argparse
import os
import platform
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SUITES = {"single": ("Single Coil Set Generator", os.path.join(HERE, "SingleCoilSetGenerator_regression", "tests")),
          "dual": ("Dual Coil Set Generator", os.path.join(HERE, "DualCoilSetGenerator_regression", "tests"))}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run the regression tests of the coil generators.")
    ap.add_argument("suite", nargs="?", choices=sorted(SUITES), help="one suite only (default: both)")
    ap.add_argument("-v", "--verbose", action="store_true", help="one line per test")
    ap.add_argument("-k", dest="patterns", action="append", default=[], metavar="TEXT",
                    help="run only the tests whose id contains this text; may be repeated (any of them)")
    ap.add_argument("--board", action="append", default=[], metavar="NAME",
                    help="the board tests on this board only (BoardNNN or the folder's whole name); may be repeated")
    ap.add_argument("--update-references", action="store_true", help="write the board files anew from this run")
    ap.add_argument("--keep", action="store_true", help="keep the temporary output folder")
    args = ap.parse_args(argv)
    if args.suite is None:                  # each suite in its own process: both have a module called harness
        rc = 0
        for name in SUITES:
            rc |= subprocess.call([sys.executable, os.path.abspath(__file__), name] + list(argv or sys.argv[1:]))
            print()
        return rc
    return run_suite(args)


def run_suite(args):
    title, tests = SUITES[args.suite]
    if args.update_references:
        os.environ["REGRESSION_UPDATE_REFERENCES"] = "1"
    if args.keep:
        os.environ["REGRESSION_KEEP_OUTPUT"] = "1"
    if args.board:
        os.environ["REGRESSION_BOARDS"] = ",".join(args.board)
    sys.dont_write_bytecode = True
    if tests not in sys.path:
        sys.path.insert(0, tests)

    import harness
    import numpy
    print(f"{title} regression tests  -  Python {platform.python_version()} ({platform.system()}), "
          f"numpy {numpy.__version__}")
    print(f"  generator   {harness.PROJECT}")
    print(f"  boards      {len(harness.BOARDS)} of {len(harness.S.boards(every=True))} in {harness.SUITE}")
    print(f"  output      {harness.temp_root()}" + ("  (kept)" if args.keep else "  (removed at the end)"))
    if args.update_references:
        print("  THE BOARD FILES ARE BEING WRITTEN ANEW from this run")
    print()

    suite = unittest.TestLoader().discover(tests, pattern="test_*.py", top_level_dir=tests)
    if args.patterns:
        suite = _filter(suite, args.patterns)
    t0 = time.time()
    result = unittest.TextTestRunner(verbosity=2 if args.verbose else 1, stream=sys.stdout).run(suite)
    print(f"\n{title}: {result.testsRun} tests in {time.time() - t0:.1f} s: "
          f"{len(result.failures)} failed, {len(result.errors)} errors, {len(result.skipped)} skipped")
    return 0 if result.wasSuccessful() else 1


def _filter(suite, patterns):
    out = unittest.TestSuite()
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            out.addTest(_filter(item, patterns))
        elif any(p.lower() in item.id().lower() for p in patterns):
            out.addTest(item)
    return out


if __name__ == "__main__":
    sys.exit(main())

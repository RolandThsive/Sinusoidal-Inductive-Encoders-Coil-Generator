"""
coverage_ratchet.py  -  a regression suite's coverage may not drop (run by the CI after a suite ran under coverage):

    python .github/scripts/coverage_ratchet.py single            compare the total of .coverage with the baseline
    python .github/scripts/coverage_ratchet.py single --update   write the baseline from .coverage

The baseline is .github/coverage-baseline.json: the total line and branch coverage of each suite, in percent.  The
check fails when the total is lower than the baseline (by more than 0.05, for rounding), and suggests raising the
baseline when the total is higher by half a point or more, so that the gain is kept.  There is no fixed target: the
number only ever goes up.

Needs coverage (requirements-dev.txt).
"""

import argparse
import io
import json
import os
import sys

import coverage

BASELINE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "coverage-baseline.json")
SLACK = 0.05
RAISE_AT = 0.5


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fail when a suite's coverage drops below its baseline.")
    ap.add_argument("suite", help="single or dual")
    ap.add_argument("--data", default=".coverage", help="the coverage data file")
    ap.add_argument("--update", action="store_true", help="write this total as the suite's baseline")
    args = ap.parse_args(argv)

    cov = coverage.Coverage(data_file=args.data, config_file=".coveragerc")
    cov.load()
    total = round(cov.report(file=io.StringIO(), precision=2), 2)
    base = {}
    if os.path.isfile(BASELINE):
        with open(BASELINE, encoding="utf-8") as fh:
            base = json.load(fh)
    was = base.get(args.suite)
    line = f"{args.suite} suite coverage: {total:.2f} % (baseline {was if was is not None else 'none'})"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"**Coverage** ({args.suite} suite, line and branch): {total:.2f} % "
                     f"(baseline {was if was is not None else 'none'})\n\n")
    print(line)
    if args.update:
        base[args.suite] = total
        with open(BASELINE, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(sorted(base.items())), fh, indent=1)
            fh.write("\n")
        print(f"baseline written to {BASELINE}")
        return 0
    if was is None:
        print(f"::error::no baseline for the {args.suite} suite in {os.path.relpath(BASELINE)}; run with --update")
        return 1
    if total < was - SLACK:
        print(f"::error::the {args.suite} suite's coverage dropped from {was:.2f} % to {total:.2f} %: add tests for "
              f"the new code, or remove the code no test reaches")
        return 1
    if total >= was + RAISE_AT:
        print(f"::notice::the {args.suite} suite's coverage rose to {total:.2f} %: raise its number in "
              f"{os.path.relpath(BASELINE)} to keep the gain")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
step_summary.py  -  one table row per regression run on the CI's run page (GITHUB_STEP_SUMMARY), read from the
suite's own output:

    python .github/scripts/step_summary.py LOG "Single Generator" ubuntu-latest

The row gives the system, Python and numpy versions, the number of tests, the time and the result, and the names of
the tests that failed.  Writes to standard output when GITHUB_STEP_SUMMARY is not set.
"""

import os
import re
import sys

HEAD = re.compile(r"regression tests\s+-\s+Python (\S+) \(([^)]*)\), numpy (\S+)")
TAIL = re.compile(r"^(\d+) tests in ([\d.]+) s: (\d+) failed, (\d+) errors, (\d+) skipped", re.M)
FAILED = re.compile(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", re.M)


def main(argv):
    log, suite, system = argv[1], argv[2], argv[3]
    text = ""
    if os.path.isfile(log):
        with open(log, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    head = HEAD.search(text)
    tails = list(TAIL.finditer(text))
    tail = tails[-1] if tails else None          # the suite's own last line
    python, numpy = (head.group(1), head.group(3)) if head else ("?", "?")
    if tail:
        n, secs, failed, errors, skipped = tail.groups()
        bad = int(failed) + int(errors)
        result = "passed" if bad == 0 else f"**{failed} failed, {errors} errors**"
        row = f"| {suite} | {system} | {python} | {numpy} | {n} | {float(secs) / 60:.1f} min | {result} | {skipped} |"
    else:
        row = f"| {suite} | {system} | {python} | {numpy} | ? | ? | **did not finish** | ? |"
    out = ["| Suite | System | Python | numpy | Tests | Time | Result | Skipped |", "|---|---|---|---|---|---|---|---|", row]
    names = sorted({".".join(m.group(2).split(".")[-2:]) for m in FAILED.finditer(text)})   # Class.test
    if names:
        out += ["", "Failed: " + ", ".join(f"`{x}`" for x in names[:30]) + (" ..." if len(names) > 30 else "")]
    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n\n")
    else:
        print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""
kicad_check.py  -  the boards as KiCad sees them.  Runs inside the official kicad/kicad Docker image (see
.github/workflows/kicad.yml), one KiCad version at a time:

    python3 .github/scripts/kicad_check.py --kicad 8.0 DIR [DIR ...]            check
    python3 .github/scripts/kicad_check.py --kicad 8.0 --update DIR [DIR ...]   write this version's baseline anew

Every Stator / Rotor board found under the folders (.kicad_pcb, or .kicad_pcb.gz as the regression references are
kept) is
  - loaded by KiCad:  `kicad-cli pcb export svg` must succeed and write a picture (every KiCad version), and
  - checked by KiCad's DRC:  `kicad-cli pcb drc --format json --severity-all` (KiCad 8 and newer; KiCad 7's
    command line has no DRC).  The number of reports of each type on each board must equal the committed baseline
    (.github/kicad-drc-baseline.json), so a new violation fails, and so does one that went away (then the baseline is
    written anew with --update, in the same pull request, so the improvement is kept).

The board's name in the baseline is its path below the folder it was found in, without .gz, e.g.
"Single Generator/default/Stator.kicad_pcb".  Needs only the standard library (Python 3.9 or newer) and kicad-cli.
"""

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BASELINE = os.path.join(os.path.dirname(HERE), "kicad-drc-baseline.json")
BOARD_NAMES = ("Stator.kicad_pcb", "Rotor.kicad_pcb")
DRC_FROM = 8                     # the first KiCad major version whose kicad-cli has `pcb drc`


def find_boards(roots):
    """[(name, path)] for every Stator / Rotor board below the folders, in a stable order."""
    found = []
    for label, root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for f in sorted(filenames):
                plain = f[:-3] if f.endswith(".gz") else f
                if plain in BOARD_NAMES:
                    rel = os.path.relpath(os.path.join(dirpath, plain), root).replace(os.sep, "/")
                    found.append((f"{label}/{rel}", os.path.join(dirpath, f)))
    return found


def unpack(path, work, n):
    """The board as a plain .kicad_pcb file in its own folder under work (KiCad writes nothing next to it)."""
    folder = os.path.join(work, f"{n:03d}")
    os.makedirs(folder)
    out = os.path.join(folder, os.path.basename(path)[:-3] if path.endswith(".gz") else os.path.basename(path))
    if path.endswith(".gz"):
        with gzip.open(path, "rb") as src, open(out, "wb") as dst:
            shutil.copyfileobj(src, dst)
    else:
        shutil.copyfile(path, out)
    return out


def cli(args):
    p = subprocess.run(["kicad-cli"] + args, capture_output=True, text=True, timeout=600)
    return p.returncode, (p.stdout + p.stderr).strip()


def load_test(board):
    """None when KiCad loads the board and writes its picture, else what went wrong."""
    svg = board[:-len(".kicad_pcb")] + ".svg"
    rc, out = cli(["pcb", "export", "svg", "--layers", "F.Cu,B.Cu,Edge.Cuts", "-o", svg, board])
    if rc != 0:
        return f"kicad-cli pcb export svg failed (exit code {rc}): {out[-600:]}"
    if not os.path.isfile(svg) or os.path.getsize(svg) < 200:
        return "kicad-cli pcb export svg wrote no picture"
    return None


def drc(board):
    """({report type: count}, None), or (None, what went wrong)."""
    report = board[:-len(".kicad_pcb")] + ".drc.json"
    rc, out = cli(["pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", report, board])
    if rc != 0 or not os.path.isfile(report):
        return None, f"kicad-cli pcb drc failed (exit code {rc}): {out[-600:]}"
    with open(report, encoding="utf-8") as fh:
        data = json.load(fh)
    counts = {}
    for v in data.get("violations", []):
        key = f"{v.get('type', '?')} ({v.get('severity', '?')})"
        counts[key] = counts.get(key, 0) + 1
    if data.get("unconnected_items"):
        counts["unconnected_items"] = len(data["unconnected_items"])
    return dict(sorted(counts.items())), None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Load every board in KiCad and compare its DRC with the baseline.")
    ap.add_argument("--kicad", required=True, help='the KiCad version of the image, e.g. "8.0"')
    ap.add_argument("--update", action="store_true", help="write this version's baseline from this run")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("folders", nargs="+", help='LABEL=FOLDER, e.g. "Single Generator=Single Generator/Regression '
                                               'Testing/References"')
    args = ap.parse_args(argv)
    roots = [tuple(f.split("=", 1)) if "=" in f else (os.path.basename(os.path.normpath(f)), f) for f in args.folders]
    for _label, root in roots:
        if not os.path.isdir(root):
            print(f"::error::no folder {root}")
            return 1
    major = int(args.kicad.split(".")[0])
    _rc, version = cli(["version"])
    print(f"KiCad {version} (image {args.kicad}); DRC {'on' if major >= DRC_FROM else 'not in this version'}")
    boards = find_boards(roots)
    if not boards:
        print("::error::no boards found")
        return 1

    baseline = {}
    if os.path.isfile(args.baseline):
        with open(args.baseline, encoding="utf-8") as fh:
            baseline = json.load(fh)
    expected = baseline.get(args.kicad, {})
    seen, problems, rows = {}, [], []
    work = tempfile.mkdtemp(prefix="kicad_check_")
    try:
        for n, (name, path) in enumerate(boards):
            board = unpack(path, work, n)
            why = load_test(board)
            if why:
                problems.append(f"{name}: KiCad {args.kicad} cannot load it: {why}")
                rows.append((name, "LOAD FAILED", ""))
                continue
            if major < DRC_FROM:
                rows.append((name, "loads", ""))
                continue
            counts, why = drc(board)
            if why:
                problems.append(f"{name}: {why}")
                rows.append((name, "loads", "DRC FAILED"))
                continue
            seen[name] = counts
            text = ", ".join(f"{k} x{c}" for k, c in counts.items()) or "clean"
            rows.append((name, "loads", text))
            if not args.update:
                if name not in expected:
                    problems.append(f"{name}: not in the KiCad {args.kicad} baseline (DRC: {text}); run with --update "
                                    f"and commit {os.path.relpath(args.baseline)}")
                elif expected[name] != counts:
                    was = ", ".join(f"{k} x{c}" for k, c in expected[name].items()) or "clean"
                    problems.append(f"{name}: KiCad {args.kicad} DRC changed: was {was}, now {text}")
        if major >= DRC_FROM and not args.update:
            for name in sorted(set(expected) - {b for b, _p in boards}):
                problems.append(f"{name}: in the KiCad {args.kicad} baseline but no longer found; run with --update")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    width = max(len(r[0]) for r in rows)
    for name, load, text in rows:
        print(f"  {name:{width}s}  {load:11s}  {text}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### KiCad {args.kicad}: {len(boards)} boards\n\n| Board | Loads | DRC |\n|---|---|---|\n")
            for name, load, text in rows:
                fh.write(f"| {name} | {load} | {text} |\n")
            fh.write("\n")

    if args.update and major >= DRC_FROM:
        baseline[args.kicad] = dict(sorted(seen.items()))
        with open(args.baseline, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(sorted(baseline.items())), fh, indent=1)
            fh.write("\n")
        print(f"baseline for KiCad {args.kicad} written to {args.baseline}")
    for p in problems:
        print(f"::error::{p}")
    print(f"{len(boards)} boards, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

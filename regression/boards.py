"""
boards.py  -  looks after the test board folders (BoardNNN-<what it tests>) of the two regression suites.

    python regression/boards.py new single "spiral-tx-8-turns" TX_SHAPE=spiral TX_TURNS=8
    python regression/boards.py new dual "rx2-cosine-r" RX2.RX_PROFILE=cosine_r --from Board005
    python regression/boards.py sync                  every board folder's parameter files written anew from the
                                                      generators' own files, with the board's values
    python regression/boards.py table                 the board table in each suite's README.md written anew

new: the first argument is the generator (single or dual), the second what the board tests (the folder becomes
BoardNNN-<what it tests>, NNN the next free number).  Each NAME=VALUE changes one value, VALUE written as in a
parameter file (a number, "text", None, True, [list], (tuple)); a dual NAME names its file's module first (BOARD.,
RX1., TX2., SILK., ...), a Single Generator silkscreen value SILK.  The files are copied from Board001-default, or
from another board with --from; each changed value is replaced in place, so the comments stay with it.  Then the
board is written and its files saved next to its parameter files, its tests run, and the README table written anew.
A board that does not build or fails its tests is removed again: read what the run printed.

sync is for after a change to a generator's own parameter files: each board file becomes the generator's file again,
with the board's values put in where they differ.  A parameter added there comes into every board folder with the
generator's value, one removed goes, and changed comments follow.  Then run run_regression.py, and
--update-references where the boards changed on purpose.
"""

import argparse
import ast
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import RegressionHarness as RH  # noqa: E402

SUITES = RH.SUITES


# ---------------------------------------------------------------------------------------------- parameter file text
def set_value(text, name, value):
    """`text` (a parameter file) with the value of `name` replaced in place; None when the file does not set it."""
    lines = text.split("\n")
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == name:
            v = node.value
            first, last = v.lineno - 1, v.end_lineno - 1
            head, tail = lines[first][:v.col_offset], lines[last][v.end_col_offset:]
            return "\n".join(lines[:first] + [head + RH.literal(value) + tail] + lines[last + 1:])
    return None


def change(folder, files, name, value):
    """Set `name` (KEY.NAME for a module other than "") to `value` in the parameter file of `folder` that sets it."""
    key, _, attr = name.rpartition(".")
    for f, k in files.items():
        if k != key:
            continue
        path = os.path.join(folder, f)
        text = read(path)
        new = set_value(text, attr, value)
        if new is not None:
            write(path, new)
            return f
    keys = sorted({k for k in files.values() if k})
    raise SystemExit(f"{name}: no parameter file of this board sets it" +
                     (f" (dual names start with the module: {', '.join(keys)})" if len(keys) > 1 else ""))


def _values(text):
    """{NAME: (value node, the value's source text)} of each top-level NAME = value of a parameter file."""
    out = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and RH.is_parameter_name(node.targets[0].id):
            out[node.targets[0].id] = (node.value, ast.get_source_segment(text, node.value))
    return out


def synced(board_text, own_text):
    """The generator's own parameter file with the board's values: each name the board's file sets to another value
    gets the board's value, written as the board's file writes it; a name the board's file lacks keeps the
    generator's value (added); a name only the board's file sets is left out (removed).  So a board file always has
    the generator's names, order and comments.  Returns (text, added, removed)."""
    own, mine = _values(own_text), _values(board_text)
    lines = own_text.split("\n")
    for name, (node, src) in sorted(own.items(), key=lambda it: (-it[1][0].lineno, -it[1][0].col_offset)):
        if name not in mine or mine[name][1] == src:
            continue
        first, last = node.lineno - 1, node.end_lineno - 1
        head, tail = lines[first][:node.col_offset], lines[last][node.end_col_offset:]
        lines[first:last + 1] = (head + mine[name][1] + tail).split("\n")
    added = [n for n in own if n not in mine]
    removed = [n for n in mine if n not in own]
    return "\n".join(lines), added, removed


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------------------------- commands
def cmd_new(args):
    s = SUITES[args.generator]
    if not all(c.isalnum() or c in "-_." for c in args.what):
        raise SystemExit(f"{args.what!r}: use letters, digits, - and _ only")
    boards = RH.find_boards(s["root"])
    source = next(iter(RH.select_boards(boards, [args.source]).values())) if args.source else \
        boards.get("Board001-default", s["parameters"])
    number = args.number or max([int(b[5:].split("-")[0]) for b in boards] or [0]) + 1
    folder = os.path.join(s["root"], f"Board{number:03d}-{args.what}")
    if os.path.exists(folder) or any(b.startswith(f"Board{number:03d}-") for b in boards):
        raise SystemExit(f"there is a Board{number:03d} already")
    os.makedirs(folder)
    try:
        for f in s["files"]:
            shutil.copyfile(os.path.join(source, f), os.path.join(folder, f))
        for item in args.values:
            name, eq, text = item.partition("=")
            if not eq:
                raise SystemExit(f"{item!r}: write NAME=VALUE")
            try:
                value = ast.literal_eval(text)
            except (ValueError, SyntaxError):
                value = text                                    # a bare word: text
            print(f"  {name.strip()} = {RH.literal(value)}   ({change(folder, s['files'], name.strip(), value)})")
    except BaseException:
        shutil.rmtree(folder)
        raise
    print(f"made {os.path.relpath(folder, REPO)}")
    write_table(args.generator)
    if args.no_write:
        return 0
    runner = [sys.executable, os.path.join(HERE, "run_regression.py"), args.generator,
              "--board", os.path.basename(folder)]
    rc = subprocess.call(runner + ["--update-references", "-k", "BoardReferences"])
    if rc == 0:
        rc = subprocess.call(runner + ["-k", "test_boards", "-k", "test_invariants", "-k", "test_silkscreen"])
    if rc != 0:
        shutil.rmtree(folder)
        write_table(args.generator)
        print(f"the board did not build or failed its tests; {os.path.relpath(folder, REPO)} was removed again")
    return rc


def cmd_sync(args):
    count = 0
    for g in [args.generator] if args.generator else SUITES:
        s = SUITES[g]
        for name, folder in RH.find_boards(s["root"]).items():
            for f in s["files"]:
                path = os.path.join(folder, f)
                before = read(path)
                text, added, removed = synced(before, read(os.path.join(s["parameters"], f)))
                if text != before:
                    write(path, text)
                    count += 1
                    for n in added:
                        print(f"  {name}/{f}: added {n}")
                    for n in removed:
                        print(f"  {name}/{f}: removed {n}")
                    if not added and not removed:
                        print(f"  {name}/{f}: comments brought up to date")
        write_table(g)
    print(f"{count} parameter file(s) changed" + ("; now run regression/run_regression.py" if count else ""))
    return 0


def write_table(generator):
    s = SUITES[generator]
    readme = os.path.join(s["root"], "README.md")
    table = RH.board_table(s["root"], s["files"])
    text = read(readme) if os.path.isfile(readme) else ""
    block = f"{RH.TABLE_START}\n{table}{RH.TABLE_END}"
    if RH.TABLE_START in text and RH.TABLE_END in text:
        head, rest = text.split(RH.TABLE_START, 1)
        text = head + block + rest.split(RH.TABLE_END, 1)[1]
    else:
        text = text.rstrip("\n") + ("\n\n" if text else "") + "## The boards\n\n" + block + "\n"
    write(readme, text)


def cmd_table(args):
    for g in [args.generator] if args.generator else SUITES:
        write_table(g)
        print(f"wrote the board table of {os.path.relpath(os.path.join(SUITES[g]['root'], 'README.md'), REPO)}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Look after the test board folders of the regression suites.")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("new", help="make a new test board")
    p.add_argument("generator", choices=sorted(SUITES))
    p.add_argument("what", help="what the board tests, e.g. spiral-tx-8-turns (letters, digits, - and _)")
    p.add_argument("values", nargs="*", help="NAME=VALUE, VALUE as in a parameter file")
    p.add_argument("--from", dest="source", help="copy the parameter files of this board instead of Board001-default")
    p.add_argument("--number", type=int, help="the board's number (default: the next free one)")
    p.add_argument("--no-write", action="store_true", help="only make the parameter files")
    p = sub.add_parser("sync", help="give every board folder the names the generators' parameter files set")
    p.add_argument("generator", nargs="?", choices=sorted(SUITES))
    p = sub.add_parser("table", help="write the board table of the suites' README.md anew")
    p.add_argument("generator", nargs="?", choices=sorted(SUITES))
    args = ap.parse_args(argv)
    return {"new": cmd_new, "sync": cmd_sync, "table": cmd_table}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

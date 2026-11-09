"""
boards.py  -  looks after the test board folders (BoardNNN-<what it tests>) of the two regression suites.

    python regression/boards.py new single "spiral-tx-8-turns" TX_SHAPE=spiral TX_TURNS=8
    python regression/boards.py new dual "rx2-cosine-r" RX2.RX_PROFILE=cosine_r --from Board005
    python regression/boards.py sync                  every board folder given the names the generators' own
                                                      parameter files set (added) and not those they no longer
                                                      set (removed)
    python regression/boards.py table                 the board table in each suite's README.md written anew
    python regression/boards.py unpack single Board007 [FOLDER]
                                                      the board's Stator and Rotor as plain .kicad_pcb files, to
                                                      open in KiCad

new: the first argument is the generator (single or dual), the second what the board tests (the folder becomes
BoardNNN-<what it tests>, NNN the next free number).  Each NAME=VALUE changes one value, VALUE written as in a
parameter file (a number, "text", None, True, [list], (tuple)); a dual NAME names its file's module first (BOARD.,
RX1., TX2., SILK., ...), a Single Generator silkscreen value SILK.  The files are copied from Board001-default, or
from another board with --from; each changed value is replaced in place, so the comments stay with it.  Then the
board is written and its files saved next to its parameter files, its tests run, and the README table written anew.
A board that does not build or fails its tests is removed again: read what the run printed.

sync is for after a change to the generators: a parameter added to a generator's own parameter file is added to every
board folder with the value it has there (with the comment lines right above it), one removed is removed.  Then run
run_regression.py, and --update-references where the boards changed on purpose.
"""

import argparse
import ast
import gzip
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import RegressionHarness as RH  # noqa: E402

SUITES = RH.SUITES


# ---------------------------------------------------------------------------------------------- parameter file text
def statements(text):
    """{NAME: (first line, last line)} (0-based, inclusive) of each top-level NAME = value of a parameter file."""
    out = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and RH.is_parameter_name(node.targets[0].id):
            out[node.targets[0].id] = (node.lineno - 1, node.end_lineno - 1)
    return out


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


def _block_start(lines, first):
    """The first line of a statement's block: the statement and the comment lines right above it."""
    while first > 0 and lines[first - 1].lstrip().startswith("#"):
        first -= 1
    return first


def synced(board_text, own_text):
    """The board's parameter file with the names of the generator's own file: a name it lacks is copied in, with the
    comment lines right above it, before the name that follows it in the generator's file; a name the generator's
    file does not set is removed, with the comment lines right above it.  Returns (text, added, removed)."""
    own, mine = statements(own_text), statements(board_text)
    own_lines, lines = own_text.split("\n"), board_text.split("\n")
    removed = [n for n in mine if n not in own]
    for n in sorted(removed, key=lambda n: -mine[n][0]):
        first, last = mine[n]
        del lines[_block_start(lines, first):last + 1]
    order = list(own)
    added = []
    for i, n in enumerate(order):
        mine = statements("\n".join(lines))
        if n in mine:
            continue
        block = own_lines[_block_start(own_lines, own[n][0]):own[n][1] + 1]
        after = next((m for m in order[i + 1:] if m in mine), None)
        before = next((m for m in reversed(order[:i]) if m in mine), None)
        at = _block_start(lines, mine[after][0]) if after else (mine[before][1] + 1 if before else len(lines))
        lines[at:at] = block
        added.append(n)
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
                text, added, removed = synced(read(path), read(os.path.join(s["parameters"], f)))
                if added or removed:
                    write(path, text)
                    count += 1
                    for n in added:
                        print(f"  {name}/{f}: added {n}")
                    for n in removed:
                        print(f"  {name}/{f}: removed {n}")
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


def cmd_unpack(args):
    s = SUITES[args.generator]
    name, folder = next(iter(RH.select_boards(RH.find_boards(s["root"]), [args.board]).items()))
    out = args.folder or tempfile.mkdtemp(prefix=f"{name}_")
    os.makedirs(out, exist_ok=True)
    for f in RH.STORED_FILES:
        src = os.path.join(folder, f)
        if f.endswith(".gz"):
            with gzip.open(src, "rb") as a, open(os.path.join(out, f[:-3]), "wb") as b:
                shutil.copyfileobj(a, b)
        else:
            shutil.copyfile(src, os.path.join(out, f))
    print(f"{name}: Stator.kicad_pcb, Rotor.kicad_pcb and Parameters.txt are in {out}")
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
    p = sub.add_parser("unpack", help="a board's files as plain .kicad_pcb files, to open in KiCad")
    p.add_argument("generator", choices=sorted(SUITES))
    p.add_argument("board", help="BoardNNN or the folder's whole name")
    p.add_argument("folder", nargs="?", help="where to put them (default: a new temporary folder)")
    args = ap.parse_args(argv)
    return {"new": cmd_new, "sync": cmd_sync, "table": cmd_table, "unpack": cmd_unpack}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

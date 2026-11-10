"""
RegressionHarness.py  -  the plumbing both regression suites share.  Each suite's tests/harness.py makes one Suite
for its generator (its parameter modules, its run script, its board folders) and exposes its methods by name, so the
tests read H.run(...), H.check(...), H.write(...), H.board(name) in both suites.

A Suite runs its generator in this process, with parameter values that live only in memory: no parameter file is
ever written, and every run starts again from the values of the suite's first board folder (Board001-default), so
what is in the generator's own Parameters folder (the values you are designing with) does not change any test.

    suite.run(overrides, args)       the run script's main(args) with the overrides applied; returns a Result
    suite.check(overrides)           run(overrides, ["--check", "--no-color"])
    suite.write(overrides, args)     a full run that writes into a fresh temporary folder (Result.folder)

Overrides: {"NAME": value} for the module whose key is "" (the Single Generator's gathered Parameters), {"KEY.NAME":
value} for the others (SILK.SILKSCREEN_SIDES, RX2.LOOPS, ...).  DELETE removes the name, as if its line were missing
from its file.

The board folders.  Each test board is a folder BoardNNN-<what it tests> next to the suite's tests folder, holding a
complete copy of the generator's parameter files with the board's own values, and the files the generator wrote from
them: Stator.kicad_pcb and Rotor.kicad_pcb, the KiCad project file of each (Stator.kicad_pro, Rotor.kicad_pro: the
board's design rules) and Parameters.txt (without the lines that change with every run).

    suite.boards()                   {board name: folder}, in the order of their numbers
    suite.board_values(name)         the overrides that the board's parameter files amount to
    suite.board(name)                the board written from its files (made once per process, shared by the tests)
    suite.reference_path(name, file) the file the written board must equal
    suite.check_reference(test, name, file)   the comparison test_boards.py runs for each board and file
    suite.folder_problems(name)      what is wrong with a board folder (missing names, stray files, ...)

The functions below the Suite need only the standard library; regression/boards.py uses them without loading a
generator.  Nothing to edit here.
"""

import atexit
import contextlib
import io
import json
import os
import re
import shutil
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))          # regression/
REPO = os.path.dirname(HERE)
DELETE = object()
BOARD_FOLDER = re.compile(r"^Board(\d{3,})-[A-Za-z0-9][A-Za-z0-9_.+-]*$")
RECORD = "Parameters.txt"
# what a run writes that a board folder keeps: each board with its KiCad project file (its design rules), the record
OUTPUT_FILES = ("Stator.kicad_pcb", "Stator.kicad_pro", "Rotor.kicad_pcb", "Rotor.kicad_pro", RECORD)
# what KiCad writes next to a board it opened (its window settings, a lock, backups); never committed (.gitignore)
KICAD_LOCAL_FILES = re.compile(r"(\.kicad_prl|\.lck|-backups|fp-info-cache)$|^_autosave-")
TABLE_START = "<!-- board table: written by `python regression/boards.py table`, do not edit by hand -->"
TABLE_END = "<!-- end of board table -->"
UPDATE_REFERENCES = os.environ.get("REGRESSION_UPDATE_REFERENCES") == "1"
KEEP_OUTPUT = os.environ.get("REGRESSION_KEEP_OUTPUT") == "1"
ONLY_BOARDS = [b.strip() for b in os.environ.get("REGRESSION_BOARDS", "").split(",") if b.strip()]

# the two suites: their folder, the generator's own Parameters folder, and which module each parameter file feeds
SUITES = {
    "single": dict(root=os.path.join(HERE, "SingleGenerator_regression"),
                   parameters=os.path.join(REPO, "Generators", "Single Generator", "Parameters"),
                   files={"Board_Parameters.py": "", "IC_Parameters.py": "", "RX_Parameters.py": "",
                          "Rotor_Parameters.py": "", "TX_Parameters.py": "",
                          "SilkScreenSuggestion_Parameters.py": "SILK"}),
    "dual": dict(root=os.path.join(HERE, "DualGenerator_regression"),
                 parameters=os.path.join(REPO, "Generators", "Dual Generator", "Parameters"),
                 files={"Dual_Board_Parameters.py": "BOARD", "Dual_RX1_Parameters.py": "RX1",
                        "Dual_RX2_Parameters.py": "RX2", "Dual_TX1_Parameters.py": "TX1",
                        "Dual_TX2_Parameters.py": "TX2", "Dual_Rotor1_Parameters.py": "ROTOR1",
                        "Dual_Rotor2_Parameters.py": "ROTOR2", "Dual_IC1_Parameters.py": "IC1",
                        "Dual_IC2_Parameters.py": "IC2",
                        "Dual_SilkScreenSuggestion_Parameters.py": "SILK"}),
}


class Result:
    """What one run did: the return code, everything it printed, and (after a write) where the files are.  Each
    suite's harness adds what is particular to its generator (where the board files are named, ...) and sets
    PROJECT, the generator's folder."""

    PROJECT = None

    def __init__(self, rc, out, err, folder=None, params=None):
        self.rc, self.out, self.err, self.folder = rc, out, err, folder
        self.snapshot = params or {}        # {key: {name: value}} as the run saw it (the overrides applied)
        self._boards = {}

    @property
    def lines(self):
        return self.out.splitlines()

    def _level(self, word):
        return [line.strip() for line in self.lines if re.match(r"\s*" + word + r"\b", line)]

    @property
    def errors(self):
        return self._level("ERROR")

    @property
    def warnings(self):
        return self._level("WARNING")

    @property
    def infos(self):
        return self._level("info")

    def has(self, pattern):
        return re.search(pattern, self.out) is not None

    @property
    def passed(self):
        return self.rc == 0

    def path(self, name):
        return os.path.join(self.folder, name) if self.folder else None

    def text(self, name):
        with open(self.path(name), encoding="utf-8", newline="") as fh:
            return fh.read()

    def board(self, name):
        """The file parsed (RegressionTools.Board), once."""
        if name not in self._boards:
            import RegressionTools as RT
            self._boards[name] = RT.Board(self.text(name))
        return self._boards[name]

    @property
    def stator(self):
        return self.board(os.path.basename(self.stator_path))

    @property
    def rotor(self):
        return self.board(os.path.basename(self.rotor_path))

    @property
    def record(self):
        return self.text(RECORD)

    @property
    def record_path(self):
        return self.path(RECORD)

    @property
    def normalised_record(self):
        """The record without what changes from run to run (RegressionTools.normalise_record), the temporary
        output folder replaced by <output> and the generator's folder (the class's PROJECT) by <project>."""
        import RegressionTools as RT
        text = self.record
        for d in (getattr(self, "out_dir", None), self.folder):
            if d:                       # as a path, as a path with forward slashes, and as repr() writes it (Windows)
                for form in (d, d.replace("\\", "/"), d.replace("\\", "\\\\")):
                    text = text.replace(form, "<output>")
        return RT.normalise_record(text, self.PROJECT)

    def __repr__(self):
        return f"Result(rc={self.rc}, folder={self.folder!r})"


class Suite:
    """One generator's regression plumbing.

        modules          {key: module}: the parameter modules the generator reads ("" for the gathered module of
                         the Single Generator, "SILK", "BOARD", "RX1", ...)
        files            {parameter file name: key}: which module each of the generator's parameter files feeds
        parameters_dir   the generator's own Parameters folder (the names every board folder must set)
        main             the run script's main(argv)
        output_key       the override that points OUTPUT_DIR somewhere ("OUTPUT_DIR", "BOARD.OUTPUT_DIR")
        root             the suite's folder (SingleGenerator_regression, DualGenerator_regression)
        result           the Result class to make
    """

    def __init__(self, name, modules, files, parameters_dir, main, output_key, root, result):
        self.name, self.modules, self.files = name, modules, files
        self.parameters_dir, self.main, self.output_key = parameters_dir, main, output_key
        self.root, self.result = root, result
        self._saved = {k: module_values(m) for k, m in modules.items()}
        self._tmp = None
        self._boards = {}
        self._values = {}
        self._base = None

    # ------------------------------------------------------------------ overrides
    def restore(self):
        """Every parameter module back to the values the generator imported (its own Parameters folder)."""
        for key, m in self.modules.items():
            for n in list(vars(m)):
                if is_parameter_name(n) and n not in self._saved[key]:
                    delattr(m, n)
            for n, v in self._saved[key].items():
                setattr(m, n, v)

    def apply(self, overrides):
        for name, value in (overrides or {}).items():
            key, _, attr = name.rpartition(".")
            if key not in self.modules:
                raise KeyError(f"override {name!r}: the module must be one of {', '.join(map(repr, self.modules))}")
            m = self.modules[key]
            if value is DELETE:
                if hasattr(m, attr):
                    delattr(m, attr)
            else:
                setattr(m, attr, value)

    def snapshot(self):
        """{key: {name: value}} of every parameter as the modules hold them now."""
        return {k: {n: getattr(m, n) for n in dir(m) if is_parameter_name(n)} for k, m in self.modules.items()}

    @property
    def base(self):
        """The values every run starts from: the suite's first board folder (Board001-default)."""
        if self._base is None:
            boards = self.boards(every=True)
            self._base = self.board_values(next(iter(boards))) if boards else {}
        return self._base

    # ------------------------------------------------------------------ runs
    def run(self, overrides=None, args=("--check", "--no-color")):
        self.restore()
        self.apply(self.base)
        self.apply(overrides)
        params = self.snapshot()
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = self.main(list(args))
        finally:
            self.restore()
        return self.result(rc, out.getvalue(), err.getvalue(), params=params)

    def check(self, overrides=None, extra_args=()):
        return self.run(overrides, ["--check", "--no-color"] + list(extra_args))

    def temp_root(self):
        if self._tmp is None:
            self._tmp = tempfile.mkdtemp(prefix=f"regression_{self.name.lower()}_")
            if not KEEP_OUTPUT:
                atexit.register(shutil.rmtree, self._tmp, True)
        return self._tmp

    def write(self, overrides=None, args=("--no-color",), subdir=None):
        """A run that writes.  OUTPUT_DIR is pointed at a fresh temporary folder (unless the overrides name one), so
        the generator's Output folder stays as it is; Result.folder is the folder the run made (None when it wrote
        nothing)."""
        ov = dict(overrides or {})
        out_dir = ov.setdefault(self.output_key, tempfile.mkdtemp(prefix=(subdir or "run") + "_", dir=self.temp_root()))
        res = self.run(ov, args)
        made = [d for d in sorted(os.listdir(out_dir)) if os.path.isdir(os.path.join(out_dir, d))]
        res.folder = os.path.join(out_dir, made[0]) if len(made) == 1 else None
        res.out_dir = out_dir
        res.made = made
        return res

    # ------------------------------------------------------------------ the board folders
    def boards(self, every=False):
        """{board name: folder} of the BoardNNN-... folders, in the order of their numbers.  When the run was asked
        for some boards only (run_regression.py --board), just those, unless every=True."""
        found = find_boards(self.root)
        return found if every or not ONLY_BOARDS else select_boards(found, ONLY_BOARDS)

    def board_values(self, name):
        """The board's parameter files as overrides: every name each file sets, on the module that file feeds.  A
        name the generator's files set but the board's files leave out is removed (DELETE), so the board's files
        are the whole truth.  OUTPUT_DIR is left out: a test run always writes into a temporary folder."""
        if name not in self._values:
            folder = self.boards(every=True)[name]
            given = {k: {} for k in self.modules}
            for f, key in self.files.items():
                given[key].update(read_parameter_file(os.path.join(folder, f)))
            ov = {}
            for key, values in given.items():
                prefix = f"{key}." if key else ""
                for n in self._saved[key]:
                    if n not in values:
                        ov[prefix + n] = DELETE
                for n, v in values.items():
                    ov[prefix + n] = v
            ov.pop(self.output_key, None)
            self._values[name] = ov
        return dict(self._values[name])

    def board(self, name):
        """The board written from its folder's parameter files (Result), made the first time it is asked for."""
        if name not in self._boards:
            res = self.write(self.board_values(name), subdir=name)
            if res.rc != 0 or res.folder is None:
                raise RuntimeError(f"board {name} did not write (rc = {res.rc}):\n{res.out}")
            self._boards[name] = res
        return self._boards[name]

    def reference_path(self, name, file):
        return os.path.join(self.boards(every=True)[name], file)

    def written(self, name, file):
        """The text of `file` as the board's run wrote it (Parameters.txt normalised)."""
        res = self.board(name)
        return res.normalised_record if file == RECORD else res.text(file)

    def check_reference(self, test, name, file):
        """`file` of the board, written again now, must equal the copy kept in its folder character for character.
        With --update-references the copy is written anew instead."""
        import RegressionTools as RT
        actual = self.written(name, file)
        path = self.reference_path(name, file)
        if UPDATE_REFERENCES:
            RT.write_reference(path, actual)
            return
        expected = RT.read_reference(path)
        test.assertIsNotNone(expected, f"no {os.path.relpath(path, REPO)}: run_regression.py "
                                       f"{self.name.lower()} --update-references --board {name} creates it")
        diff = RT.exact_differences(expected, actual)
        test.assertFalse(diff, f"{name}/{file} is not what the generator writes now ({len(diff)} shown):\n  "
                         + "\n  ".join(diff))

    def folder_problems(self, name):
        """What is wrong with the board folder: a parameter file missing, a name the generator's own file sets that
        the board's leaves out or the other way round (regression/boards.py sync mends both), a stray file, or a
        board file missing."""
        return folder_problems(self.boards(every=True)[name], self.files, self.parameters_dir)


# ---------------------------------------------------------------------------------------------- without a generator
def is_parameter_name(n):
    return n.isupper() and not n.startswith("_")


def module_values(m):
    return {n: v for n, v in vars(m).items() if is_parameter_name(n)}


def read_parameter_file(path):
    """The values a parameter file sets: {NAME: value}.  The file is run as Python, as the generator imports it."""
    with open(path, encoding="utf-8") as fh:
        code = compile(fh.read(), path, "exec")
    space = {"__file__": path, "__name__": os.path.splitext(os.path.basename(path))[0]}
    exec(code, space)                                       # noqa: S102   (a parameter file of this repository)
    return {n: v for n, v in space.items() if is_parameter_name(n)}


def literal(v):
    """A value as a parameter file writes it: strings in double quotes, the rest as Python writes it."""
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, list):
        return "[" + ", ".join(literal(x) for x in v) + "]"
    if isinstance(v, tuple):
        return "(" + ", ".join(literal(x) for x in v) + ("," if len(v) == 1 else "") + ")"
    return repr(v)


def find_boards(root):
    """{board name: folder} of every BoardNNN-... folder in root, in the order of their numbers."""
    found = []
    for d in os.listdir(root) if os.path.isdir(root) else []:
        m = BOARD_FOLDER.match(d)
        if m and os.path.isdir(os.path.join(root, d)):
            found.append((int(m.group(1)), d))
    return {d: os.path.join(root, d) for _n, d in sorted(found)}


def select_boards(found, wanted):
    """The boards of `found` named in `wanted`, each by its whole name, its BoardNNN part ("Board007") or its number
    ("7")."""
    out = {}
    for w in wanted:
        m = re.fullmatch(r"(?:Board)?(\d+)", w)
        if m:
            w = f"Board{int(m.group(1)):03d}"
        hits = [b for b in found if b == w or b.startswith(w + "-")]
        if not hits:
            raise SystemExit(f"no board folder {w!r}; there are: {', '.join(found)}")
        for b in hits:
            out[b] = found[b]
    return {b: found[b] for b in found if b in out}


def folder_problems(folder, files, parameters_dir):
    problems = []
    for f in files:
        own = read_parameter_file(os.path.join(parameters_dir, f))
        path = os.path.join(folder, f)
        if not os.path.isfile(path):
            problems.append(f"{f} is missing")
            continue
        mine = read_parameter_file(path)
        missing = sorted(set(own) - set(mine))
        extra = sorted(set(mine) - set(own))
        if missing:
            problems.append(f"{f} leaves out {', '.join(missing)} (the generator's own {f} sets them); "
                            f"python regression/boards.py sync adds them")
        if extra:
            problems.append(f"{f} sets {', '.join(extra)}, which the generator's own {f} does not; "
                            f"python regression/boards.py sync removes them")
    for f in OUTPUT_FILES:
        if not os.path.isfile(os.path.join(folder, f)):
            problems.append(f"{f} is missing (run_regression.py --update-references --board "
                            f"{os.path.basename(folder)} writes it)")
    stray = sorted(f for f in set(os.listdir(folder)) - set(files) - set(OUTPUT_FILES) if not KICAD_LOCAL_FILES.search(f))
    if stray:
        problems.append(f"files that do not belong in a board folder: {', '.join(stray)}")
    return problems


def board_differences(folder, base_folder, files):
    """[(KEY.NAME, value)] of every value the board sets differently from the base board, in file order."""
    out = []
    for f, key in files.items():
        prefix = f"{key}." if key else ""
        mine = read_parameter_file(os.path.join(folder, f))
        base = read_parameter_file(os.path.join(base_folder, f))
        for n, v in mine.items():
            if n not in base or base[n] != v or type(base[n]) is not type(v):
                out.append((prefix + n, v))
    return out


def board_table(root, files, width=70):
    """The Markdown table of the suite's boards: each board with the values it sets differently from the first."""
    boards = find_boards(root)
    if not boards:
        return "(no boards yet)\n"
    first = next(iter(boards))
    lines = [f"| Board | Values that differ from {first} |", "|---|---|"]
    for name, folder in boards.items():
        cells = []
        for n, v in board_differences(folder, boards[first], files):
            text = f"{n} = {literal(v)}"
            if len(text) > width:
                text = text[:width - 3] + "..."
            cells.append("`" + text.replace("|", "\\|").replace("`", "'") + "`")
        lines.append(f"| [{name}]({name}/) | {'<br>'.join(cells) if cells else 'the generator defaults'} |")
    return "\n".join(lines) + "\n"


def readme_table(readme):
    """The board table as it stands in the README (between TABLE_START and TABLE_END), or None."""
    if not os.path.isfile(readme):
        return None
    with open(readme, encoding="utf-8") as fh:
        text = fh.read()
    if TABLE_START not in text or TABLE_END not in text:
        return None
    return text.split(TABLE_START, 1)[1].split(TABLE_END, 1)[0].strip("\n") + "\n"

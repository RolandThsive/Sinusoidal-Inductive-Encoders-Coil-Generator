"""
WebGenerator.py  -  the web tool's entry into the two generators (runs inside the browser with Pyodide).

The web tool runs the desktop programs themselves:

    Single   Generators/Single Coil Set Generator/Generator/Run/RunCoilGenerator.py
    Dual     Generators/Dual Coil Set Generator/Dual_Generator/Run/Dual_RunCoilGenerator.py

exactly as `python RunCoilGenerator.py --no-color` runs them, on parameter files that carry the visitor's values.
Nothing of a run is repeated here: the checks, the steps, the estimate, the files and the pictures are the
program's own, and the page shows what the program prints.  This file only

    describes the settings      describe()        from ParameterRules.SPEC, Dual_SetParameters.NAMES_BY_FILE,
                                                  Dual_ParameterRules.DUAL_SPEC, the silkscreen step's DEFAULTS and
                                                  the comments of the parameter files
    says which are not used     inactive()        the `active` rules of ParameterRules.SPEC
    checks one value            check_values()    ParameterRules._check_value and the silkscreen step's own check
    writes the parameter files  (only the value of a changed line changes; comments and layout stay)
    runs the program            run()             and zips the folder it wrote
    packs the parameter files   export_zip()

Every function takes and returns JSON text, so the JavaScript side never sees a Python object.  The values travel as
{file name: {NAME: value}}, because the dual files repeat the names (LOOPS is in Dual_RX1 and in Dual_RX2).

The in-memory file system mirrors the repository: ROOT/Generators/... holds the generators' own files at their own
paths, so every path the programs work out for themselves (the Parameters folder, resources/, Output/) is right.
The published parameter files are remembered when first read and put back before every use.

Nothing here is needed to run a generator on a desktop, and nothing in the generators is changed.
"""

import ast
import importlib
import json
import os
import re
import runpy
import shutil
import sys
import time
import types
import zipfile

ROOT = "/coilgen"                                   # the folder that holds Generators/ (PyodideWorker.js sets it)

MODES = {
    "single": {"folder": "Single Coil Set Generator",
               "script": "Generator/Run/RunCoilGenerator.py",
               "aggregator": "Parameters",
               "silk_file": "SilkScreenSuggestion_Parameters.py",
               "silk_step": "Generator.Stator.LeadCutting_SilkscreenSuggestion"},
    "dual": {"folder": "Dual Coil Set Generator",
             "script": "Dual_Generator/Run/Dual_RunCoilGenerator.py",
             "aggregator": "Dual_Parameters",
             "silk_file": "Dual_SilkScreenSuggestion_Parameters.py",
             "silk_step": "Dual_Generator.Stator.Dual_LeadCutting_SilkscreenSuggestion"},
}
# Not settings of the page: they name the folder and the files of a run, and the page gives a run its own.
READ_ONLY = {"OUTPUT_DIR", "STATOR_FILE", "ROTOR_FILE"}
# The silkscreen step checks its own settings (Settings._check) and keeps no table of them.  These three are the
# ones that are not a plain switch or a number above 0; the tests hold this table against the step's own check.
SILK_KINDS = {"SILKSCREEN_SIDES": ("choice", {"values": ["both", "top", "bottom"], "ci": True}),
              "SILKSCREEN_COLOR": ("colour", {}),
              "SILKSCREEN_BREAK_LAYERS": ("layer_list", {"values": ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]})}

_published = {}                                     # {mode: {file name: text as published}}


# =============================================================================
# folders, modules
# =============================================================================
def _generators():
    return os.path.join(ROOT, "Generators")


def _mode_dir(mode):
    return os.path.join(_generators(), MODES[mode]["folder"])


def _parameter_dir(mode):
    return os.path.join(_mode_dir(mode), "Parameters")


def _paths():
    """Put the two generator folders on the import path (each package then adds its own Parameters folder)."""
    sys.dont_write_bytecode = True          # a parameter file rewritten within a second must never meet an old .pyc
    for mode in ("dual", "single"):
        p = _mode_dir(mode)
        if p not in sys.path and os.path.isdir(p):
            sys.path.insert(0, p)


def _forget_modules():
    """Drop every module that came from the generators' folders, so that the next import reads the parameter files as
    they are now - what a new `python` process does on the desktop."""
    importlib.invalidate_caches()
    root = _generators() + os.sep
    for name, module in list(sys.modules.items()):
        file = getattr(module, "__file__", None)
        if isinstance(file, str) and file.startswith(root):
            sys.modules.pop(name, None)
    for mode in MODES:
        shutil.rmtree(os.path.join(_parameter_dir(mode), "__pycache__"), ignore_errors=True)


def _published_files(mode):
    """{file name: text} of the mode's parameter files as published (read once, before anything is written)."""
    if mode not in _published:
        folder = _parameter_dir(mode)
        files = {}
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".py"):
                with open(os.path.join(folder, fname), encoding="utf-8") as fh:
                    files[fname] = fh.read()
        _published[mode] = files
    return _published[mode]


def _restore_published(mode):
    folder = _parameter_dir(mode)
    for fname, text in _published_files(mode).items():
        with open(os.path.join(folder, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def _jsonable(x):
    if isinstance(x, (tuple, list)):
        return [_jsonable(i) for i in x]
    if isinstance(x, float) and x != x:
        return None
    return x


# =============================================================================
# the parameter files as text
# =============================================================================
def _assignments(source):
    """{NAME: (line, col, end_line, end_col) of the value expression} of every top-level NAME = value."""
    out = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            v = node.value
            # these are UTF-8 byte offsets; the parameter files are ASCII, so they equal str indices
            out[node.targets[0].id] = (v.lineno, v.col_offset, v.end_lineno, v.end_col_offset)
    return out


def _help_texts(source):
    """{NAME: help text}: the comment block right above the assignment, its trailing comment and the
    comment-only lines that continue it below (the parameter files are written that way)."""
    lines = source.split("\n")
    out, prev_end = {}, {}
    spots = _assignments(source)
    for name, (ln, _col, end_ln, end_col) in sorted(spots.items(), key=lambda kv: kv[1]):
        i = ln - 1                                        # 0-based line of the assignment
        above = []
        j = i - 1
        while j >= 0 and lines[j].lstrip().startswith("#") and not set(lines[j].strip()) <= set("#= -") \
                and not lines[j].strip().startswith("# ----"):            # a section heading ends the block
            above.insert(0, lines[j].strip().lstrip("#").rstrip())
            j -= 1
        trailing = []
        first = lines[end_ln - 1]
        if "#" in first[end_col:]:
            trailing.append(first[first.index("#", end_col) + 1:].strip())
            k = end_ln
            col = first.index("#", end_col)
            # a continuation comment may start up to 2 columns left of the trailing '#'
            while k < len(lines) and lines[k].strip().startswith("#") and len(lines[k]) - len(lines[k].lstrip()) >= col - 2:
                trailing.append(lines[k].strip().lstrip("#").strip())
                k += 1
        text = "\n".join(t[1:] if t.startswith(" ") else t for t in above)
        if trailing:
            text = (text + "\n" if text else "") + " ".join(trailing)
        text = text.strip()
        # a parameter written right under another one, with no comment of its own, shares that one's text
        # (TX_WIRING / TX_LAYER_A / TX_LAYER_B)
        if not text and prev_end.get("line") == i - 1 and prev_end.get("name"):
            text = out[prev_end["name"]]
        # "... or set a fixed radius here" finishes the sentence of the parameter above ("... - this ...")
        if text.startswith("...") and prev_end.get("name") and out[prev_end["name"]].endswith("..."):
            text = out[prev_end["name"]] + " " + text[3:].lstrip()
        out[name] = text
        prev_end = {"line": end_ln - 1, "name": name}
    return out


def _headings(source):
    """{NAME: heading}: the section heading of the parameter file each parameter sits under
    ("# ===" + "# TITLE", or a "# ---- title ----" sub-heading)."""
    lines = source.split("\n")
    spots = _assignments(source)
    by_line = {ln: name for name, (ln, _c, _e, _ec) in spots.items()}
    out, title, sub = {}, "", ""
    for i, line in enumerate(lines):
        s = line.strip()
        if re.fullmatch(r"#\s*=+", s) and i + 1 < len(lines):
            t = lines[i + 1].strip()
            m = re.fullmatch(r"#\s+([A-Z][A-Z0-9 /,()+'_-]*[A-Z0-9)])\s*(\(.*\))?", t)
            if m:
                title, sub = m.group(1).strip().title(), ""
        m = re.fullmatch(r"#\s*-{2,}\s*(.+?)\s*-{2,}", s)
        if m:
            sub = m.group(1).strip()
            sub = sub[:1].upper() + sub[1:]
        if i + 1 in by_line:
            out[by_line[i + 1]] = sub or title or "General"
    return out


def _py_literal(value, kind=None):
    """A value of the page as it is written into a parameter file (ASCII, texts between double quotes as in the
    files)."""
    if kind == "pair" and isinstance(value, list):
        value = tuple(value)
    if value is None or isinstance(value, bool):
        return repr(value)
    if isinstance(value, str):
        # ASCII between double quotes.  A character beyond U+FFFF is written as \UXXXXXXXX (json.dumps would write the
        # two halves of its UTF-16 pair, which Python reads as two characters no file can hold); half a pair on its
        # own, which only a damaged text carries, becomes U+FFFD.
        value = value.encode("utf-16", "surrogatepass").decode("utf-16", "replace")
        return "".join(json.dumps(ch)[1:-1] if ord(ch) <= 0xFFFF else "\\U%08x" % ord(ch) for ch in value).join('""')
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"{value!r} is not a number a parameter file can hold")
        if value.is_integer() and kind in ("int", "steps", "auto_or_int"):
            return repr(int(value))
        return repr(value)
    if isinstance(value, int):
        return repr(value)
    if isinstance(value, tuple):
        inner = ", ".join(_py_literal(v) for v in value)
        return "(" + inner + ("," if len(value) == 1 else "") + ")"
    if isinstance(value, list):
        return "[" + ", ".join(_py_literal(v) for v in value) + "]"
    raise ValueError(f"{value!r} cannot be written into a parameter file")


def _write_parameter_files(mode, values):
    """The mode's parameter files: the published files with the visitor's values put in.  Only the value expression of
    a changed parameter is replaced; comments and layout stay as they are.  Returns ([file:NAME changed],
    [file:NAME the files do not hold])."""
    kinds = _kinds(mode)
    folder = _parameter_dir(mode)
    changed, unknown = [], []
    for fname, src in _published_files(mode).items():
        mine = values.get(fname) or {}
        spots = _assignments(src) if mine else {}
        unknown += [f"{fname}:{name}" for name in mine if name not in spots]
        lines = src.split("\n")
        # replace from the bottom up, so earlier positions stay valid
        for name, (ln, col, end_ln, end_col) in sorted(spots.items(), key=lambda kv: kv[1], reverse=True):
            if name not in mine or name in READ_ONLY:
                continue
            new = _py_literal(mine[name], kinds.get(fname, {}).get(name))
            old_expr = (lines[ln - 1][col:end_col] if ln == end_ln else
                        "\n".join([lines[ln - 1][col:]] + lines[ln:end_ln - 1] + [lines[end_ln - 1][:end_col]]))
            try:
                old_value, new_value = ast.literal_eval(old_expr), ast.literal_eval(new)
                same = old_value == new_value and type(old_value) is type(new_value) or \
                    (not isinstance(old_value, bool) and not isinstance(new_value, bool)
                     and isinstance(old_value, (int, float)) and isinstance(new_value, (int, float))
                     and old_value == new_value)
            except Exception:
                same = old_expr == new
            if same:
                continue
            head, tail = lines[ln - 1][:col], lines[end_ln - 1][end_col:]
            pad = " " * max(0, len(old_expr) - len(new)) if ln == end_ln and "#" in tail else ""
            lines[ln - 1:end_ln] = [head + new + pad + tail]
            changed.append(f"{fname}:{name}")
        with open(os.path.join(folder, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines))
    unknown += [f"{fname}:*" for fname in values if fname not in _published_files(mode)]
    return changed, unknown


# =============================================================================
# the generators' own tables
# =============================================================================
def _single_spec():
    """{NAME: (file, kind, options, active)} of the Single Coil Set Generator's table, in its order."""
    _paths()
    from Generator.Checks import ParameterRules as PR
    return {name: (file, kind, o, active) for file, name, kind, o, active in PR.SPEC}


def _silk_step(mode):
    _paths()
    return importlib.import_module(MODES[mode]["silk_step"])


def _silk_defaults(mode):
    return dict(_silk_step(mode).DEFAULTS)


def _silk_kind(name, default):
    if name in SILK_KINDS:
        return SILK_KINDS[name]
    if isinstance(default, bool):
        return "bool", {}
    return "num", {"lo": 0, "lo_ex": True}


def _layout(mode):
    """The mode's settings as the page shows them: [(file, label, group, set number, [(name, kind, options, active,
    flags)])] in the generator's order.  group: "" (single), "Board", "Set 1", "Set 2", "Silkscreen"."""
    spec = _single_spec()
    out = []
    if mode == "single":
        by_file = {}
        for name, (file, kind, o, active) in spec.items():
            by_file.setdefault(file, []).append((name, kind, o, active, {}))
        for file, rows in by_file.items():
            out.append((file, file.replace("_Parameters.py", ""), "", 0, rows))
    else:
        from Dual_Generator.Core import Dual_SetParameters as SP
        from Dual_Generator.Checks import Dual_ParameterRules as DR
        dual = {name: (kind, o) for name, kind, o in DR.DUAL_SPEC}
        for file, names in SP.NAMES_BY_FILE.items():
            m = re.fullmatch(r"Dual_([A-Za-z]+?)([12]?)_Parameters\.py", file)
            label, k = m.group(1), int(m.group(2) or 0)
            rows = []
            for name in names:
                if name in dual:
                    kind, o = dual[name]
                    rows.append((name, kind, o, None, {"dualOnly": True}))
                    continue
                _file, kind, o, active = spec[name]
                flags = {}
                if k and name in SP.OVERRIDES:                 # a board value the set may set for itself
                    flags["override"] = True
                rows.append((name, kind, o, active, flags))
            out.append((file, label if not k else f"{label} {k}", f"Set {k}" if k else "Board", k, rows))
    silk = MODES[mode]["silk_file"]
    rows = [(name,) + _silk_kind(name, default) + (None, {"silk": True}) for name, default in _silk_defaults(mode).items()]
    out.append((silk, "Silkscreen suggestion", "Silkscreen" if mode == "dual" else "", 0, rows))
    return out


def _kinds(mode):
    """{file: {NAME: kind}}"""
    return {file: {name: kind for name, kind, _o, _a, _f in rows} for file, _l, _g, _k, rows in _layout(mode)}


def _load_published(mode):
    """The mode's parameter module(s) with the published values: {file name: module}."""
    _paths()
    _restore_published(mode)
    _forget_modules()
    importlib.import_module(MODES[mode]["script"].split("/")[0])    # the package puts its Parameters folder on the path
    importlib.import_module(MODES[mode]["aggregator"])              # as the program loads them
    return {fname: importlib.import_module(fname[:-3]) for fname in _published_files(mode)
            if fname[:-3] != MODES[mode]["aggregator"]}


# =============================================================================
# what the page asks for
# =============================================================================
def describe(mode):
    """Every setting of the mode: file, group, name, kind, options, published value, the file's comment and heading."""
    modules = _load_published(mode)
    files = []
    for file, label, group, k, rows in _layout(mode):
        src = _published_files(mode).get(file, "")
        helps, heads = _help_texts(src), _headings(src)
        module = modules.get(file)
        params = []
        for name, kind, o, _active, flags in rows:
            opts = {key: _jsonable(v) for key, v in o.items()
                    if key in ("lo", "hi", "lo_ex", "hi_ex", "values", "ci", "optional", "default", "unit")}
            default = getattr(module, name, o.get("default")) if module is not None else o.get("default")
            if flags.get("silk") and module is None:
                default = _silk_defaults(mode)[name]
            params.append(dict({"name": name, "kind": kind, "options": opts, "default": _jsonable(default),
                                "help": helps.get(name, ""), "heading": heads.get(name, "General"),
                                "inFile": hasattr(module, name) if module is not None else False,
                                "readOnly": name in READ_ONLY}, **flags))
        # In the order of the parameter file itself, as the desktop user reads it.  A setting the file does not
        # hold (a set's own value of a board setting) stays behind the setting the rules name before it.
        spots, place, last = _assignments(src), {}, (0, 0)
        for i, p in enumerate(params):
            last = (spots[p["name"]][0], 0) if p["name"] in spots else (last[0], last[1] + 1)
            place[p["name"]] = last + (i,)
        params.sort(key=lambda p: place[p["name"]])
        files.append({"file": file, "label": label, "group": group, "set": k, "parameters": params})
    return json.dumps({"mode": mode, "files": files})


def _namespace(values, fname):
    d = dict(values.get(fname) or {})
    if isinstance(d.get("PAGE_SIZE_MM"), list):
        d["PAGE_SIZE_MM"] = tuple(d["PAGE_SIZE_MM"])
    return types.SimpleNamespace(**d)


def inactive(mode, values_json):
    """{file: [names the generator does not use with these values]} (shown greyed).  The rules are the `active`
    entries of ParameterRules.SPEC.  Dual: a set's names are judged with that set's own values
    (Dual_SetParameters.build); a board value is unused only when neither set uses it."""
    values = json.loads(values_json)
    spec = _single_spec()
    out = {}

    def unused(name, ns):
        active = spec[name][3] if name in spec else None
        if active is None:
            return False
        try:
            return not active(ns)
        except Exception:
            return False

    if mode == "single":
        flat = {}
        for fname in values:
            flat.update(vars(_namespace(values, fname)))
        ns = types.SimpleNamespace(**flat)
        for file, _label, _group, _k, rows in _layout(mode):
            names = [name for name, _kind, _o, _a, flags in rows if not flags.get("silk") and unused(name, ns)]
            if names:
                out[file] = names
        return json.dumps(out)

    from Dual_Generator.Core import Dual_SetParameters as SP
    P = types.SimpleNamespace(BOARD=_namespace(values, SP.BOARD_FILE))
    for k in (1, 2):
        for kind, attr in (("RX", "RX"), ("TX", "TX"), ("ROTOR", "ROTOR"), ("IC", "IC")):
            setattr(P, f"{attr}{k}", _namespace(values, SP.set_file(kind, k)))
    sets = {k: SP.build(P, k) for k in (1, 2)}
    for file, _label, _group, k, rows in _layout(mode):
        names = []
        for name, _kind, _o, _a, flags in rows:
            if flags.get("silk") or flags.get("dualOnly"):
                continue
            if (unused(name, sets[k]) if k else all(unused(name, sets[s]) for s in (1, 2))):
                names.append(name)
        if names:
            out[file] = names
    return json.dumps(out)


def _dual_layout_values(values, out):
    """The Dual Coil Set Generator works its layout out before it checks the sets, so a band radius or a board edge
    that is no number gets the layout's own words (Dual_TrackLayout.resolve: BoardLayout.given_band for the four
    band values of each RX file, _num for the two edges).  Adds them to `out`; returns the names it has judged."""
    from Generator.Core import BoardLayout
    from Generator.Core.Conflict import ParameterConflict
    from Dual_Generator.Core import Dual_SetParameters as SP
    from Dual_Generator.Core import Dual_TrackLayout as TL
    for k in (1, 2):
        file = TL.RX_FILES[k]
        mine = values.get(file) or {}
        try:
            BoardLayout.given_band(mine.get, f"RX{k} band", file)
        except ParameterConflict as e:
            if len(e.names) == 1 and e.names[0] in mine:      # one value on its own; a pair is a rule of the run
                out.setdefault(file, {})[e.names[0]] = e.message
        except Exception:
            pass
    board = values.get(SP.BOARD_FILE) or {}
    for name in SP.EDGE_NAMES:
        if board.get(name) is not None:
            try:
                TL._num(name, board[name], SP.BOARD_FILE)
            except ParameterConflict as e:
                out.setdefault(SP.BOARD_FILE, {})[name] = e.message
    return tuple(SP.BAND_NAMES) + tuple(SP.EDGE_NAMES)


def check_values(mode, values_json):
    """{file: {NAME: the generator's own message}} for every value that is wrong on its own: the type and range
    check of ParameterRules._check_value (the dual-only values with Dual_ParameterRules.DUAL_SPEC) and the
    silkscreen step's Settings._check.  A setting the generator does not use with these values is not checked, as
    in the program (ParameterRules.load_values).  Dual: the band radii and the board edges get the layout's words
    (_dual_layout_values).  The rules between values are the program's (run with check only)."""
    _paths()
    from Generator.Checks import ParameterRules as PR
    values = json.loads(values_json)
    out = {}
    silk = None
    try:
        unused = json.loads(inactive(mode, values_json))        # the generator does not check what it does not use
    except Exception:                                           # values too incomplete to tell: every value is checked
        unused = {}
    layout_names = _dual_layout_values(values, out) if mode == "dual" else ()
    for file, _label, _group, _k, rows in _layout(mode):
        mine = values.get(file) or {}
        for name, kind, o, _active, flags in rows:
            if name not in mine or name in unused.get(file, ()) or (name in layout_names and not flags.get("override")):
                continue
            value = mine[name]
            if kind == "pair" and isinstance(value, list):
                value = tuple(value)
            if flags.get("silk"):
                if silk is None:
                    step = _silk_step(mode)
                    single_step = importlib.import_module(MODES["single"]["silk_step"])
                    silk = single_step.Settings.__new__(single_step.Settings)
                    silk.file, silk.defaults = step.PARAMETER_FILE, _silk_defaults(mode)
                silk.warnings = []
                silk._check(name, value, silk.defaults[name])
                err = silk.warnings[0] if silk.warnings else None
            elif flags.get("override") and value is None:
                err = None                                      # None in a set file = the board's value
            else:
                err = PR._check_value(name, value, kind, o)[1]
            if err:
                out.setdefault(file, {})[name] = err
    return json.dumps(out)


# =============================================================================
# the run
# =============================================================================
class _Lines:
    """Stands in for sys.stdout / sys.stderr during a run: every finished line goes to `sink(text, stream)`."""

    def __init__(self, sink, stream):
        self.sink, self.stream, self.buf = sink, stream, ""

    def write(self, s):
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self.sink(line, self.stream)
        return len(s)

    def flush(self):
        pass

    def close(self):
        if self.buf:
            self.sink(self.buf, self.stream)
            self.buf = ""

    def isatty(self):
        return False


_STEP = re.compile(r"\[(\d+)/(\d+)\] (.*)")
_FINDING = re.compile(r"  (ERROR  |WARNING|info   ) (.*)")
_LEVEL = {"ERROR  ": "error", "WARNING": "warning", "info   ": "info"}
_NAME = re.compile(r"\b[A-Z][A-Z0-9_]{2,}\b")
_FILE = re.compile(r"\b(?:Dual_)?[A-Za-z0-9]+_Parameters\.py\b")


def findings(lines, known=()):
    """What the program printed, sorted for the page: the steps and the findings (Report.print's lines: a level word,
    the text, and the lines that continue it ten spaces in).  Nothing is added to the texts.  names / files: the
    settings and parameter files a finding mentions, so that the page can lead to them."""
    known = set(known)
    steps, items, failed, success = [], [], None, None
    cur = None
    for text in lines:
        m = _STEP.fullmatch(text)
        if m:
            steps.append({"n": int(m.group(1)), "total": int(m.group(2)), "text": m.group(3)})
            cur = None
            continue
        m = _FINDING.fullmatch(text)
        if m:
            cur = {"step": steps[-1]["n"] if steps else 0, "level": _LEVEL[m.group(1)], "lines": [m.group(2)]}
            items.append(cur)
            continue
        if cur is not None and text.startswith(" " * 10) and text[10:11].strip():
            cur["lines"].append(text[10:])
            continue
        cur = None
        if text.startswith("FAILED: "):
            failed = text[len("FAILED: "):]
        elif text.startswith("SUCCESS: "):
            success = text[len("SUCCESS: "):]
        elif text.startswith("CHECK PASSED"):
            success = text
    for it in items:
        whole = "\n".join(it["lines"])
        it["names"] = [n for n in dict.fromkeys(_NAME.findall(whole)) if n in known]
        it["files"] = list(dict.fromkeys(_FILE.findall(whole)))
    return {"steps": steps, "items": items, "failed": failed, "success": success}


def run(mode, values_json, check_only=False, on_line=None):
    """Run the mode's program with the visitor's values, as the desktop does.  on_line(text, stream) is called for
    every line the program prints (stream: "out" or "err").  Returns what it printed, sorted (findings), its exit
    code and, when it wrote files, their folder, their list and the zip of the folder."""
    _paths()
    values = json.loads(values_json)
    info = MODES[mode]
    result = {"mode": mode, "ok": False, "rc": None, "checkOnly": bool(check_only), "files": [], "name": None}
    lines = []

    def sink(text, stream):
        lines.append(text)
        if on_line is not None:
            on_line(text, stream)

    _restore_published(mode)
    try:
        changed, unknown = _write_parameter_files(mode, values)
    except Exception as e:                                    # a value that cannot be written as Python
        result["failed"] = f"the values cannot be written into the parameter files: {type(e).__name__}: {e}"
        result.update(findings([]))
        return json.dumps(result)
    result["changed"], result["unknown"] = changed, unknown
    out_dir = os.path.join(_mode_dir(mode), "Output")
    shutil.rmtree(out_dir, ignore_errors=True)                # every run starts with an empty Output folder
    os.makedirs(out_dir, exist_ok=True)
    _forget_modules()

    script = os.path.join(_mode_dir(mode), *info["script"].split("/"))
    argv = [script, "--no-color"] + (["--check"] if check_only else [])
    old = sys.argv, sys.stdout, sys.stderr, list(sys.path)
    out, err = _Lines(sink, "out"), _Lines(sink, "err")
    sys.argv, sys.stdout, sys.stderr = argv, out, err
    t0 = time.time()
    try:
        runpy.run_path(script, run_name="__main__")
        rc = 0
    except SystemExit as e:
        rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
        if isinstance(e.code, str):
            sink(e.code, "err")
    except BaseException as e:                                 # the program itself broke: say so, with its own words
        import traceback
        rc = 1
        result["crash"] = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        sink(f"{type(e).__name__}: {e}", "err")
    finally:
        out.close()
        err.close()
        sys.argv, sys.stdout, sys.stderr = old[0], old[1], old[2]
        sys.path[:] = old[3]
    result["seconds"] = time.time() - t0
    result["rc"] = rc
    known = {name for _f, _l, _g, _k, rows in _layout(mode) for name, *_rest in rows}
    result.update(findings(lines, known))
    result["text"] = "\n".join(lines)

    folders = sorted(d for d in os.listdir(out_dir) if os.path.isdir(os.path.join(out_dir, d)))
    if folders:
        name = folders[-1]
        folder = os.path.join(out_dir, name)
        zpath = os.path.join(ROOT, "out.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(os.listdir(folder)):
                z.write(os.path.join(folder, f), arcname=f"{name}/{f}")
                result["files"].append({"name": f, "size": os.path.getsize(os.path.join(folder, f)),
                                        "path": os.path.join(folder, f)})
        result.update(name=name, folder=folder, zip=zpath)
        aggregator = sys.modules.get(info["aggregator"])           # the parameter module the program loaded
        for key, attr, fallback in (("stator", "STATOR_FILE", "Stator.kicad_pcb"),
                                    ("rotor", "ROTOR_FILE", "Rotor.kicad_pcb")):
            fname = getattr(aggregator, attr, None) or fallback
            if os.path.isfile(os.path.join(folder, fname)):
                result[key] = fname
    result["ok"] = rc == 0 and result.get("failed") is None and (bool(folders) or bool(check_only))
    return json.dumps(result)


# =============================================================================
# export
# =============================================================================
def parameter_files(mode, values_json):
    """{file name: text} of the mode's parameter files with these values (Export)."""
    _paths()
    _restore_published(mode)
    _write_parameter_files(mode, json.loads(values_json))
    out = {}
    for fname in _published_files(mode):
        with open(os.path.join(_parameter_dir(mode), fname), encoding="utf-8") as fh:
            out[fname] = fh.read()
    _restore_published(mode)
    return json.dumps(out)


def export_zip(mode, values_json):
    """Zip of the parameter files with these values (Export).  The folder inside is named Parameters/, so it unpacks
    over the generator's own Parameters folder.  Returns the path of the zip."""
    files = json.loads(parameter_files(mode, values_json))
    zpath = os.path.join(ROOT, "parameters.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for fname, text in files.items():
            z.writestr(f"Parameters/{fname}", text)
    return json.dumps({"zip": zpath})


# =============================================================================
# import
# =============================================================================
IMPORT_MAX_BYTES = 8 * 1024 * 1024                  # of text, all files of one import together
IMPORT_MAX_FILES = 64
IMPORT_MAX_LINE = 4000                              # characters; the files' own lines are far shorter
IMPORT_MAX_TEXT = 1000                              # characters of one text value
_ASSIGN = re.compile(r"([A-Z][A-Z0-9_]*)\s*=\s*(.+)")
_COPY_HEAD = re.compile(r"#{6,}\s+(\S+\.py)\s+#{6,}")
_VALUES_HEAD = re.compile(r"\[(\S+\.py)\]")


def _holdable(x):
    """A value a setting can hold and the page can carry: None, a truth value, a finite number, a text, or a list of
    up to 16 numbers and texts (as a link's values, app/share.js)."""
    one = lambda v, n: (isinstance(v, str) and len(v) <= n) or (isinstance(v, (int, float)) and v == v
                                                              and v not in (float("inf"), float("-inf")))
    return x is None or one(x, IMPORT_MAX_TEXT) or (isinstance(x, list) and len(x) <= 16
                                                    and all(not isinstance(v, bool) and one(v, 200) for v in x))


def _literals(text, refused=None):
    """{NAME: value} of every line `NAME = literal` of a parameter file or of a record's value list (the literal
    is the longest start of the rest of the line that Python reads as one: a comment or a note after it is left).
    A literal no setting can hold (a set, bytes, 1e999, a list in a list ...) is not taken: its name goes to
    `refused`.  A line longer than IMPORT_MAX_LINE holds no setting and is not read."""
    out = {}
    for line in text.lstrip("\ufeff").split("\n"):
        m = _ASSIGN.fullmatch(line.rstrip()) if len(line) <= IMPORT_MAX_LINE else None
        if not m or line[:1] in " \t#":
            continue
        name, expr = m.group(1), m.group(2)
        for cut in range(len(expr), 0, -1):
            if cut < len(expr) and expr[cut - 1] not in " \t" and expr[cut] not in " \t#":
                continue                                   # only cut at a space or a comment
            try:
                value = _jsonable(ast.literal_eval(expr[:cut].strip()))
            except Exception:
                continue
            if _holdable(value):
                out[name] = value
            elif refused is not None:
                refused.append(name)
            break
    return out


def _record_parts(text):
    """The parameter files inside a Parameters.txt: [(file name, text)].  The verbatim copies ("##### File.py #####")
    are taken where the record has them, else the value lists ("[File.py]": indented lines `NAME = value`, up to
    the first empty line).  A reference board of regression/ holds the lists only."""
    lines = text.split("\n")
    copies, lists = {}, {}
    cur, bucket = None, None
    for line in lines:
        m = _COPY_HEAD.fullmatch(line.strip())
        if m:
            cur, bucket = m.group(1), copies
            bucket.setdefault(cur, [])
            continue
        m = _VALUES_HEAD.fullmatch(line.strip())
        if m and bucket is not copies:
            cur, bucket = m.group(1), lists
            bucket.setdefault(cur, [])
            continue
        if cur is None:
            continue
        if bucket is lists:
            if not line.strip():
                cur = None                                 # a value list ends at its first empty line
                continue
            line = line.strip()                            # its lines are indented; a parameter file's are not
        bucket[cur].append(line)
    parts = dict(lists)
    parts.update(copies)
    return [(name, "\n".join(body)) for name, body in parts.items()]


def read_import(items_json):
    """The values in the files a visitor gave: Parameters.txt of a run (web or desktop), parameter files (.py), or a
    zip of either.  items: [{name, text}] or, for a zip, [{name, path}] (a file of the in-memory file system).
    Returns {mode, values: {file: {NAME: value}}, ignored: [what was not taken, and why], files: [files read]}.
    The files are only read as text: nothing in them is run."""
    _paths()
    items = json.loads(items_json)
    texts, ignored, total = [], [], 0

    def take(name, data):
        nonlocal total
        name = os.path.basename(name.replace("\\", "/"))
        if not name.lower().endswith((".py", ".txt")):
            return
        if len(texts) >= IMPORT_MAX_FILES or total + len(data) > IMPORT_MAX_BYTES:
            ignored.append(f"{name}: too much to read (limit {IMPORT_MAX_FILES} files, {IMPORT_MAX_BYTES // 1024 // 1024} MB)")
            return
        total += len(data)
        texts.append((name, (data if isinstance(data, str) else data.decode("utf-8", "replace")).lstrip("\ufeff")))

    for item in items:
        if "path" in item:
            try:
                with zipfile.ZipFile(item["path"]) as z:
                    for info in z.infolist():
                        if info.is_dir() or not info.filename.lower().endswith((".py", ".txt")):
                            continue
                        if info.file_size > IMPORT_MAX_BYTES:
                            ignored.append(f"{os.path.basename(info.filename)}: too large")
                            continue
                        with z.open(info) as fh:
                            take(info.filename, fh.read(IMPORT_MAX_BYTES + 1))
            except zipfile.BadZipFile:
                ignored.append(f"{item.get('name', 'the zip')}: not a zip file")
            except Exception as e:
                ignored.append(f"{item.get('name', 'the zip')}: cannot be opened ({type(e).__name__})")
            finally:
                try:
                    os.remove(item["path"])
                except OSError:
                    pass
        else:
            take(item.get("name", ""), item.get("text", ""))

    parts, flat = [], []
    for name, text in texts:
        if name.lower().endswith(".py"):
            parts.append((name, text))
        else:
            found = _record_parts(text)
            parts += found
            if not found:
                flat.append((name, text))
    names = {name for name, _t in parts}
    mode = "dual" if any(n.startswith("Dual_") for n in names) else "single"
    layout = {file: {row[0] for row in rows} for file, _l, _g, _k, rows in _layout(mode)}
    values, files = {}, []
    for name, text in parts:
        if name[:-3] == MODES[mode]["aggregator"]:
            continue
        if name not in layout:
            ignored.append(f"{name}: not a parameter file of the {mode} generator")
            continue
        files.append(name)
        refused = []
        got = _literals(text, refused)
        ignored += [f"{key} in {name}: not a value a setting can hold" for key in refused if key in layout[name]]
        for key, value in got.items():
            if key in READ_ONLY:
                continue
            if key in layout[name]:
                values.setdefault(name, {})[key] = value
            else:
                ignored.append(f"{key} in {name}: not a setting of this version")
    # a text with values but no file names in it (a hand-made list): the names say where they belong (Single only)
    if flat and mode == "single":
        owner = {key: file for file, keys in layout.items() for key in keys}
        for name, text in flat:
            refused = []
            got = _literals(text, refused)
            ignored += [f"{key} in {name}: not a value a setting can hold" for key in refused if key in owner]
            if got:
                files.append(name)
            for key, value in got.items():
                if key in READ_ONLY:
                    continue
                if key in owner:
                    values.setdefault(owner[key], {})[key] = value
                else:
                    ignored.append(f"{key} in {name}: not a setting of this version")
    return json.dumps({"mode": mode, "values": values, "ignored": list(dict.fromkeys(ignored)), "files": files})

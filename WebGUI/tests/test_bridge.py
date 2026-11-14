"""
test_bridge.py  -  WebGenerator.py under plain Python, held against the desktop programs.

    python -m unittest WebGUI/tests/test_bridge.py            (from the repository's top folder)

The bridge works in a copy of Generators/ (a temporary folder), the desktop programs run in a second copy, so
nothing in the repository is written.  What is proven:

    the settings the page shows are the generators' own tables, nothing more and nothing less
    a run through the bridge writes the files the desktop program writes, byte for byte (the record's date and
    folder lines aside), with the published values and with changed ones, for Single and for Dual
    a wrong value gets the generator's own message, and a failed run writes nothing
    the bridge leaves the published parameter files as they were
    exported files and a run's record are read back as the values they were made from; nothing in them is run
    every setting the page shows has its words for the help box, and tips.json is the file those words give
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "WebGUI"))
sys.path.insert(0, os.path.join(REPO, "WebGUI", "tools"))
import WebGenerator as WG  # noqa: E402
import build_tips  # noqa: E402
import tips_words  # noqa: E402

IGNORE = shutil.ignore_patterns("__pycache__", "Coil_*", "DualCoil_*")
SCRIPT = {mode: os.path.join("Generators", info["folder"], *info["script"].split("/"))
          for mode, info in WG.MODES.items()}
# the two lines of Parameters.txt that name the moment and the place of a run
RECORD_LINES = ("generated ", "folder ")


def copy_tree(root):
    shutil.copytree(os.path.join(REPO, "Generators"), os.path.join(root, "Generators"), ignore=IGNORE)


def setUpModule():
    global BRIDGE_ROOT, DESKTOP_ROOT
    BRIDGE_ROOT, DESKTOP_ROOT = tempfile.mkdtemp(prefix="bridge_"), tempfile.mkdtemp(prefix="desktop_")
    copy_tree(BRIDGE_ROOT)
    copy_tree(DESKTOP_ROOT)
    WG.ROOT = BRIDGE_ROOT
    WG._published.clear()


def tearDownModule():
    shutil.rmtree(BRIDGE_ROOT, ignore_errors=True)
    shutil.rmtree(DESKTOP_ROOT, ignore_errors=True)


def defaults(mode):
    d = json.loads(WG.describe(mode))
    return {f["file"]: {p["name"]: p["default"] for p in f["parameters"]} for f in d["files"]}


def desktop_run(mode, edits=None):
    """Run the desktop program in its own copy, with `edits` {file: text} written over its parameter files.
    Returns (exit code, {file name: bytes} of the folder it wrote)."""
    folder = os.path.join(DESKTOP_ROOT, "Generators", WG.MODES[mode]["folder"])
    published = {}
    for fname, text in (edits or {}).items():
        path = os.path.join(folder, "Parameters", fname)
        with open(path, encoding="utf-8") as fh:
            published[path] = fh.read()
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    out = os.path.join(folder, "Output")
    for name in os.listdir(out) if os.path.isdir(out) else ():
        if os.path.isdir(os.path.join(out, name)):
            shutil.rmtree(os.path.join(out, name))
    try:
        done = subprocess.run([sys.executable, os.path.join(DESKTOP_ROOT, SCRIPT[mode]), "--no-color"],
                              capture_output=True, text=True)
    finally:
        for path, text in published.items():
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
    files = {}
    for name in sorted(os.listdir(out)) if os.path.isdir(out) else ():
        sub = os.path.join(out, name)
        if os.path.isdir(sub):
            for f in sorted(os.listdir(sub)):
                with open(os.path.join(sub, f), "rb") as fh:
                    files[f"{name}/{f}"] = fh.read()
    return done.returncode, files, done.stdout


def bridge_files(result):
    files = {}
    for f in result["files"]:
        with open(f["path"], "rb") as fh:
            files[f"{result['name']}/{f['name']}"] = fh.read()
    return files


def without_moment(data):
    """Parameters.txt without the lines that name the moment and the place of the run."""
    return b"\n".join(line for line in data.split(b"\n")
                      if not line.startswith(tuple(w.encode() for w in RECORD_LINES)))


class Describe(unittest.TestCase):
    def test_settings_come_in_the_order_of_their_parameter_file(self):
        for mode in ("single", "dual"):
            for f in json.loads(WG.describe(mode))["files"]:
                lines = WG._assignments(WG._published_files(mode).get(f["file"], ""))
                held = [p["name"] for p in f["parameters"] if p["name"] in lines]
                self.assertEqual(held, sorted(held, key=lambda n: lines[n][0]), f["file"])
                self.assertTrue(held, f["file"])

    def test_single_is_the_generators_table(self):
        from Generator.Checks import ParameterRules as PR
        d = json.loads(WG.describe("single"))
        shown = [(f["file"], p["name"], p["kind"]) for f in d["files"] for p in f["parameters"] if not p.get("silk")]
        self.assertEqual(sorted(shown), sorted((file, name, kind) for file, name, kind, _o, _a in PR.SPEC))
        silk = [p["name"] for f in d["files"] for p in f["parameters"] if p.get("silk")]
        self.assertEqual(sorted(silk), sorted(WG._silk_defaults("single")))

    def test_dual_is_the_generators_table(self):
        d = json.loads(WG.describe("dual"))
        from Dual_Generator.Core import Dual_SetParameters as SP
        shown = {f["file"]: tuple(p["name"] for p in f["parameters"]) for f in d["files"]
                 if f["file"] != WG.MODES["dual"]["silk_file"]}
        self.assertEqual({f: sorted(n) for f, n in shown.items()}, {f: sorted(n) for f, n in dict(SP.NAMES_BY_FILE).items()})
        for f in d["files"]:
            for p in f["parameters"]:
                self.assertEqual(bool(p.get("override")), f["set"] != 0 and p["name"] in SP.OVERRIDES, p["name"])

    def test_every_setting_has_its_line_in_the_published_file(self):
        for mode in WG.MODES:
            d = json.loads(WG.describe(mode))
            for f in d["files"]:
                for p in f["parameters"]:
                    self.assertTrue(p["inFile"], f"{f['file']}:{p['name']} has no line in the published file")
                    self.assertEqual(p["readOnly"], p["name"] in WG.READ_ONLY)

    def test_published_values_pass_the_value_check(self):
        for mode in WG.MODES:
            self.assertEqual(json.loads(WG.check_values(mode, json.dumps(defaults(mode)))), {})


class Values(unittest.TestCase):
    def test_wrong_value_gets_the_generators_message(self):
        from Generator.Checks import ParameterRules as PR
        spec = {name: (kind, o) for _f, name, kind, o, _a in PR.SPEC}
        values = {"RX_Parameters.py": {"LOOPS": 0}, "Board_Parameters.py": {"PCB_LAYERS": 3},
                  "SilkScreenSuggestion_Parameters.py": {"SILKSCREEN_SIDES": "left"}}
        got = json.loads(WG.check_values("single", json.dumps(values)))
        self.assertEqual(got["RX_Parameters.py"]["LOOPS"], PR._check_value("LOOPS", 0, *spec["LOOPS"])[1])
        self.assertEqual(got["Board_Parameters.py"]["PCB_LAYERS"],
                         PR._check_value("PCB_LAYERS", 3, *spec["PCB_LAYERS"])[1])
        self.assertIn('must be "both", "top" or "bottom"', got["SilkScreenSuggestion_Parameters.py"]["SILKSCREEN_SIDES"])

    def test_a_value_the_generator_does_not_use_is_not_checked(self):
        """As in the program (ParameterRules.load_values): the rotor's own sizes are checked only when ROTOR_MODE is
        "custom", and what the page shows under a setting is then the error line of a check-only run."""
        values = defaults("single")
        values["Rotor_Parameters.py"]["ROTOR_CUSTOM_SECTORS"] = 0
        self.assertEqual(json.loads(WG.check_values("single", json.dumps(values))), {})
        run = json.loads(WG.run("single", json.dumps(values), True))
        self.assertEqual([it for it in run["items"] if it["level"] == "error"], [])
        values["Rotor_Parameters.py"]["ROTOR_MODE"] = "custom"
        got = json.loads(WG.check_values("single", json.dumps(values)))
        self.assertEqual(list(got), ["Rotor_Parameters.py"])
        self.assertEqual(list(got["Rotor_Parameters.py"]), ["ROTOR_CUSTOM_SECTORS"])
        run = json.loads(WG.run("single", json.dumps(values), True))
        said = [it["lines"][0] for it in run["items"] if it["level"] == "error"]
        self.assertIn(got["Rotor_Parameters.py"]["ROTOR_CUSTOM_SECTORS"] + "   (Rotor_Parameters.py)", said)

    def test_dual_band_and_edge_values_get_the_layouts_words(self):
        """The Dual Coil Set Generator works out its layout before it checks the sets: a band radius or a board edge
        that is no number is refused there, in the layout's words.  The page shows those under the setting."""
        for file, name, value in (("Dual_RX1_Parameters.py", "INSIDE_RADIUS_MM", 0),
                                  ("Dual_RX2_Parameters.py", "OUTSIDE_RADIUS_MM", "abc"),
                                  ("Dual_Board_Parameters.py", "OUTER_EDGE_RADIUS_MM", -1)):
            values = defaults("dual")
            values[file][name] = value
            got = json.loads(WG.check_values("dual", json.dumps(values)))
            self.assertEqual(list(got), [file], name)
            self.assertEqual(list(got[file]), [name])
            self.assertIn("must be a number greater than 0, or None", got[file][name])
            run = json.loads(WG.run("dual", json.dumps(values), True))
            self.assertIn(got[file][name], [it["lines"][0] for it in run["items"] if it["level"] == "error"], name)
        # half a pair is a rule between two values: the run names it, nothing stands under one setting
        values = defaults("dual")
        values["Dual_RX2_Parameters.py"]["OUTSIDE_RADIUS_MM"] = None
        self.assertEqual(json.loads(WG.check_values("dual", json.dumps(values))), {})

    def test_a_sets_own_board_value_may_be_none(self):
        values = {"Dual_RX1_Parameters.py": {"VIA_TYPE": None, "LOOPS": None}}
        got = json.loads(WG.check_values("dual", json.dumps(values)))
        self.assertNotIn("VIA_TYPE", got.get("Dual_RX1_Parameters.py", {}))
        self.assertIn("LOOPS", got["Dual_RX1_Parameters.py"])

    def test_silkscreen_table_is_the_steps_own_check(self):
        step = WG._silk_step("single")
        for name, default in step.DEFAULTS.items():
            kind, o = WG._silk_kind(name, default)
            good = {"bool": [True, False], "num": [0.01, 1, 2.5], "colour": ["#FFFFFF", "#00ff00"],
                    "choice": o.get("values", []), "layer_list": [[v] for v in o.get("values", [])]}[kind]
            bad = {"bool": [1, "yes"], "num": [0, -1, "1", True], "colour": ["white", "#FFF"],
                   "choice": ["left"], "layer_list": [[], ["F.Cux"], "F.Cu"]}[kind]
            for value in good:
                self.assertEqual(json.loads(WG.check_values("single", json.dumps({step.PARAMETER_FILE: {name: value}}))),
                                 {}, f"{name} = {value!r}")
            for value in bad:
                got = json.loads(WG.check_values("single", json.dumps({step.PARAMETER_FILE: {name: value}})))
                self.assertIn(name, got.get(step.PARAMETER_FILE, {}), f"{name} = {value!r}")

    def test_inactive_follows_the_generators_rules(self):
        from Generator.Checks import ParameterRules as PR
        import types
        values = defaults("single")
        values["TX_Parameters.py"]["TX_WIRING"] = "series"
        flat = {}
        for part in values.values():
            flat.update(part)
        flat["PAGE_SIZE_MM"] = tuple(flat["PAGE_SIZE_MM"])
        ns = types.SimpleNamespace(**flat)
        want = {}
        for file, name, _kind, _o, active in PR.SPEC:
            if active is not None and not active(ns):
                want.setdefault(file, []).append(name)
        self.assertEqual(json.loads(WG.inactive("single", json.dumps(values))), want)

    def test_only_the_changed_value_changes_in_the_file(self):
        values = defaults("single")
        values["RX_Parameters.py"]["LOOPS"] = 4
        values["Board_Parameters.py"]["OUTPUT_DIR"] = "/somewhere/else"          # read only: never written
        files = json.loads(WG.parameter_files("single", json.dumps(values)))
        for fname, text in files.items():
            before, after = WG._published_files("single")[fname].split("\n"), text.split("\n")
            self.assertEqual(len(before), len(after))
            changed = [(a, b) for a, b in zip(before, after, strict=True) if a != b]
            if fname == "RX_Parameters.py":
                self.assertEqual(len(changed), 1)
                self.assertTrue(changed[0][1].startswith("LOOPS") and "4" in changed[0][1])
            else:
                self.assertEqual(changed, [])

    def test_text_values_are_written_safely(self):
        values = {"TX_Parameters.py": {"TX_NET": 'a"; import os; os.system("x") #'}}
        files = json.loads(WG.parameter_files("single", json.dumps(values)))
        import ast
        tree = ast.parse(files["TX_Parameters.py"])
        got = [n for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == "TX_NET"]
        self.assertEqual(ast.literal_eval(got[0].value), values["TX_Parameters.py"]["TX_NET"])
        self.assertFalse(any(isinstance(n, (ast.Import, ast.ImportFrom, ast.Expr)) and not
                             (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)) for n in tree.body))

    def test_a_text_beyond_the_basic_plane_reaches_the_board_as_it_was_typed(self):
        """A net name with a character beyond U+FFFF (an emoji) is one character in the parameter file, and the run
        writes it into the board; half a UTF-16 pair, which no file can hold, becomes U+FFFD."""
        import ast
        for typed, held in (("\U0001f600 net", "\U0001f600 net"), ("a\ud83db", "a\ufffdb"), ("\u03a9 \u2028", "\u03a9 \u2028")):
            lit = WG._py_literal(typed)
            self.assertTrue(lit.isascii())
            self.assertEqual(ast.literal_eval(lit), held)
        values = defaults("single")
        values["RX_Parameters.py"]["RX_NET_PHASE_0_2"] = "\U0001f600 net"
        run = json.loads(WG.run("single", json.dumps(values)))
        self.assertTrue(run["ok"], run.get("crash"))
        stator = next(f for f in run["files"] if f["name"].endswith("Stator.kicad_pcb"))
        with open(stator["path"], encoding="utf-8") as fh:
            self.assertIn('"\U0001f600 net"', fh.read())


class Runs(unittest.TestCase):
    def same_as_desktop(self, mode, values, edits=None):
        result = json.loads(WG.run(mode, json.dumps(values)))
        rc, desktop, _text = desktop_run(mode, edits)
        self.assertEqual(result["rc"], rc)
        mine = bridge_files(result)
        self.assertEqual(sorted(mine), sorted(desktop))
        for name in desktop:
            if name.endswith("Parameters.txt"):
                self.assertEqual(without_moment(mine[name]), without_moment(desktop[name]), name)
            else:
                self.assertEqual(mine[name], desktop[name], name)
        return result

    def test_single_published_values(self):
        result = self.same_as_desktop("single", defaults("single"))
        self.assertTrue(result["ok"])
        self.assertEqual([s["n"] for s in result["steps"]], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["changed"], [])
        self.assertEqual({result["stator"], result["rotor"]}, {"Stator.kicad_pcb", "Rotor.kicad_pcb"})
        self.assertEqual(len(result["files"]), 7)

    def test_single_changed_values(self):
        values = defaults("single")
        values["RX_Parameters.py"]["LOOPS"] = 4
        values["TX_Parameters.py"]["TX_TURNS"] = 2
        edits = json.loads(WG.parameter_files("single", json.dumps(values)))
        result = self.same_as_desktop("single", values, edits)
        self.assertTrue(result["ok"])
        self.assertEqual(sorted(result["changed"]), ["RX_Parameters.py:LOOPS", "TX_Parameters.py:TX_TURNS"])

    def test_dual_published_values(self):
        result = self.same_as_desktop("dual", defaults("dual"))
        self.assertTrue(result["ok"])
        self.assertTrue(result["name"].startswith("DualCoil_"))

    def test_runs_do_not_leak_into_each_other(self):
        values = defaults("single")
        first = json.loads(WG.run("single", json.dumps(values)))
        changed = json.loads(json.dumps(values))
        changed["RX_Parameters.py"]["LOOPS"] = 3
        other = json.loads(WG.run("single", json.dumps(changed)))
        self.assertNotEqual(first["name"], other["name"])
        json.loads(WG.run("dual", json.dumps(defaults("dual")), True))
        again = json.loads(WG.run("single", json.dumps(values)))
        self.assertEqual(first["name"], again["name"])
        self.assertEqual([(f["name"], f["size"]) for f in first["files"] if f["name"] != "Parameters.txt"],
                         [(f["name"], f["size"]) for f in again["files"] if f["name"] != "Parameters.txt"])
        for fname, text in WG._published_files("single").items():
            self.assertEqual(json.loads(WG.parameter_files("single", "{}"))[fname], text)

    def test_parameter_error_stops_the_run_and_writes_nothing(self):
        values = defaults("single")
        values["RX_Parameters.py"]["LOOPS"] = 0
        result = json.loads(WG.run("single", json.dumps(values)))
        rc, desktop, text = desktop_run("single", json.loads(WG.parameter_files("single", json.dumps(values))))
        self.assertEqual((result["rc"], rc), (1, 1))
        self.assertFalse(result["ok"])
        self.assertEqual(result["files"], [])
        self.assertEqual(desktop, {})
        self.assertTrue(result["failed"].startswith("1 parameter error"))
        errors = [it for it in result["items"] if it["level"] == "error"]
        self.assertEqual(len(errors), 1)
        self.assertIn("LOOPS", errors[0]["names"])
        self.assertIn("  ERROR   " + errors[0]["lines"][0], text)
        self.assertEqual(result["text"].split("\n"), text.rstrip("\n").split("\n"))

    def test_check_only_writes_nothing(self):
        result = json.loads(WG.run("single", json.dumps(defaults("single")), True))
        self.assertTrue(result["ok"])
        self.assertEqual(result["files"], [])
        self.assertTrue(result["success"].startswith("CHECK PASSED"))

    def test_the_printed_text_is_the_desktop_text(self):
        result = json.loads(WG.run("single", json.dumps(defaults("single"))))
        _rc, _files, text = desktop_run("single")
        mine = result["text"].replace(BRIDGE_ROOT, "<root>").split("\n")
        theirs = text.rstrip("\n").replace(DESKTOP_ROOT, "<root>").split("\n")
        self.assertEqual(mine, theirs)


class ImportExport(unittest.TestCase):
    def changed(self, mode):
        values = defaults(mode)
        rx = "RX_Parameters.py" if mode == "single" else "Dual_RX2_Parameters.py"
        values[rx]["LOOPS"] = 5
        values[rx]["RX_NET_PHASE_0_2"] = 'S"1'
        return values

    def test_exported_files_come_back_as_the_same_values(self):
        for mode in ("single", "dual"):
            values = self.changed(mode)
            zpath = json.loads(WG.export_zip(mode, json.dumps(values)))["zip"]
            got = json.loads(WG.read_import(json.dumps([{"name": "Parameter_Files.zip", "path": zpath}])))
            self.assertEqual(got["mode"], mode)
            self.assertEqual(got["ignored"], [])
            for file, names in got["values"].items():
                for name, value in names.items():
                    self.assertEqual(value, values[file][name], f"{mode} {file} {name}")
            rx = "RX_Parameters.py" if mode == "single" else "Dual_RX2_Parameters.py"
            self.assertEqual(got["values"][rx]["LOOPS"], 5)

    def test_a_runs_record_comes_back_as_its_values(self):
        values = defaults("single")
        values["RX_Parameters.py"]["LOOPS"] = 2
        result = json.loads(WG.run("single", json.dumps(values)))
        self.assertTrue(result["ok"])
        with open(os.path.join(result["folder"], "Parameters.txt"), encoding="utf-8") as fh:
            record = fh.read()
        got = json.loads(WG.read_import(json.dumps([{"name": "Parameters.txt", "text": record}])))
        self.assertEqual(got["mode"], "single")
        self.assertEqual(got["values"]["RX_Parameters.py"]["LOOPS"], 2)
        for file, names in got["values"].items():
            for name, value in names.items():
                self.assertEqual(value, values[file][name], f"{file} {name}")

    def test_a_record_without_its_copies_comes_back_from_its_value_lists(self):
        """A record that holds the value lists only ("[File.py]" and indented lines): the reference boards of
        regression/ are kept that way, and so is a record whose end was cut off."""
        for mode, board in (("single", "Board_Parameters.py"), ("dual", "Dual_Board_Parameters.py")):
            values = defaults(mode)
            values[board]["AIR_GAP_MM"] = 1.5
            result = json.loads(WG.run(mode, json.dumps(values)))
            self.assertTrue(result["ok"], mode)
            with open(os.path.join(result["folder"], "Parameters.txt"), encoding="utf-8") as fh:
                record = fh.read()
            lists = record[:record.index("PARAMETER FILES (verbatim copies)")]
            self.assertNotIn("#####", lists)
            got = json.loads(WG.read_import(json.dumps([{"name": "Parameters.txt", "text": lists}])))
            self.assertEqual(got["mode"], mode)
            self.assertEqual(got["ignored"], [], mode)
            self.assertEqual(got["values"][board]["AIR_GAP_MM"], 1.5)
            self.assertGreater(sum(len(v) for v in got["values"].values()), 60, mode)
            for file, names in got["values"].items():
                for name, value in names.items():
                    self.assertEqual(value, values[file][name], f"{mode} {file} {name}")
        board = os.path.join(REPO, "regression", "SingleCoilSetGenerator_regression",
                             "Board018-edges-90-150-loops-8-subcoils-2", "Parameters.txt")
        with open(board, encoding="utf-8") as fh:
            got = json.loads(WG.read_import(json.dumps([{"name": "Parameters.txt", "text": fh.read()}])))
        self.assertEqual(got["values"]["Board_Parameters.py"]["OUTER_EDGE_RADIUS_MM"], 75.0)
        self.assertEqual(got["values"]["RX_Parameters.py"]["LOOPS"], 8)
        self.assertIsNone(got["values"]["RX_Parameters.py"]["INSIDE_RADIUS_MM"])

    def test_a_name_of_another_version_is_reported_not_taken(self):
        text = "LOOPS = 3\nTX_START_ANGLE_DEG = 10\n"
        got = json.loads(WG.read_import(json.dumps([{"name": "RX_Parameters.py", "text": text}])))
        self.assertEqual(got["values"]["RX_Parameters.py"], {"LOOPS": 3})
        self.assertTrue(any("TX_START_ANGLE_DEG" in what for what in got["ignored"]), got["ignored"])

    def test_text_that_is_not_values_is_never_run(self):
        text = "LOOPS = __import__('os').getcwd()\nRX_SUBCOILS = 2\n"
        got = json.loads(WG.read_import(json.dumps([{"name": "RX_Parameters.py", "text": text}])))
        self.assertNotIn("LOOPS", got["values"].get("RX_Parameters.py", {}))
        self.assertEqual(got["values"]["RX_Parameters.py"]["RX_SUBCOILS"], 2)

    def test_a_value_no_setting_can_hold_is_named_not_taken(self):
        """What a parameter file can say but no setting can hold (1e999, a set, bytes, a list in a list, a very long
        text) is named and left out, and the rest of the file is read; the answer is always JSON a browser reads."""
        for bad in ("1e999", "-1e999", "{1, 2}", '{"a": 1}', 'b"x"', "1+2j", "...", "[[1, 2], [3]]", '"' + "x" * 1001 + '"',
                    str(list(range(17)))):
            text = f"LOOPS = {bad}\nRX_SUBCOILS = 2\n"
            out = WG.read_import(json.dumps([{"name": "RX_Parameters.py", "text": text}]))
            got = json.loads(out, parse_constant=self.fail)             # Infinity and NaN are no JSON a browser reads
            self.assertEqual(got["values"], {"RX_Parameters.py": {"RX_SUBCOILS": 2}}, bad[:20])
            self.assertEqual(got["ignored"], ["LOOPS in RX_Parameters.py: not a value a setting can hold"], bad[:20])

    def test_a_file_saved_by_notepad_and_a_line_too_long_to_be_a_setting(self):
        """A byte order mark before the first line does not hide that line (text and zip).  A line of more than
        4000 characters is no setting and is not read, however long it is."""
        import time
        import zipfile
        text = "\ufeffLOOPS = 5\r\nRX_SUBCOILS = 2\r\n"
        want = {"RX_Parameters.py": {"LOOPS": 5, "RX_SUBCOILS": 2}}
        self.assertEqual(json.loads(WG.read_import(json.dumps([{"name": "RX_Parameters.py", "text": text}])))["values"], want)
        path = os.path.join(tempfile.gettempdir(), "bridge_bom.zip")
        with zipfile.ZipFile(path, "w") as z:
            z.writestr("RX_Parameters.py", text.encode("utf-8"))
        self.assertEqual(json.loads(WG.read_import(json.dumps([{"name": "x.zip", "path": path}])))["values"], want)
        self.assertFalse(os.path.exists(path))                       # the zip is removed once it is read
        start = time.time()
        text = "LOOPS = " + "1 " * 200000 + "\nRX_SUBCOILS = 2\n"
        got = json.loads(WG.read_import(json.dumps([{"name": "RX_Parameters.py", "text": text}])))
        self.assertEqual(got["values"], {"RX_Parameters.py": {"RX_SUBCOILS": 2}})
        self.assertLess(time.time() - start, 5)


class Findings(unittest.TestCase):
    def test_findings_are_read_from_the_printed_lines(self):
        lines = ["[1/6] Checking the parameters",
                 "  ERROR   TX_TURNS conflicts with OUTSIDE_RADIUS_MM",
                 "          the turns do not fit",
                 "          second line",
                 "  WARNING RX_TRACE_WIDTH_MM = 0.05 mm is very fine   (RX_Parameters.py)",
                 "  info    something to know",
                 "              not a continuation",
                 "",
                 "FAILED: 1 parameter error(s). Nothing was written."]
        got = WG.findings(lines, {"TX_TURNS", "OUTSIDE_RADIUS_MM", "RX_TRACE_WIDTH_MM"})
        self.assertEqual(got["steps"], [{"n": 1, "total": 6, "text": "Checking the parameters"}])
        self.assertEqual([(i["level"], i["lines"]) for i in got["items"]],
                         [("error", ["TX_TURNS conflicts with OUTSIDE_RADIUS_MM", "the turns do not fit", "second line"]),
                          ("warning", ["RX_TRACE_WIDTH_MM = 0.05 mm is very fine   (RX_Parameters.py)"]),
                          ("info", ["something to know"])])
        self.assertEqual(got["items"][0]["names"], ["TX_TURNS", "OUTSIDE_RADIUS_MM"])
        self.assertEqual(got["items"][1]["files"], ["RX_Parameters.py"])
        self.assertEqual(got["failed"], "1 parameter error(s). Nothing was written.")


class Tips(unittest.TestCase):
    """The words of the help boxes (tools/tips_words.py, tips.json) against the generators' own tables."""

    def shown(self):
        out = {}
        for mode in ("single", "dual"):
            for f in json.loads(WG.describe(mode))["files"]:
                for p in f["parameters"]:
                    if not p["readOnly"] and p["name"] != "GENERATOR_MODE":
                        out.setdefault(p["name"], []).append(p)
        return out

    def test_every_setting_the_page_shows_has_its_words_and_no_other(self):
        shown = self.shown()
        self.assertEqual(sorted(set(shown) - set(tips_words.PARAMS)), [], "settings without words")
        self.assertEqual(sorted(set(tips_words.PARAMS) - set(shown)), [], "words for settings the page does not show")

    def test_a_choice_with_words_is_a_choice_the_generator_takes(self):
        wrong = []
        for name, variants in self.shown().items():
            for p in variants:
                values = (p.get("options") or {}).get("values") or ([True, False] if p["kind"] == "bool" else [])
                allowed = {str(v).lower() for v in values if v is not None} | {"none", "auto", "number"}
                wrong += [f"{name}: {key}" for key in tips_words.PARAMS[name].get("choices", {}) if key.lower() not in allowed]
        self.assertEqual(sorted(set(wrong)), [])

    def test_the_words_have_no_fault_and_tips_json_is_the_file_they_give(self):
        self.assertEqual(build_tips.problems(), [])
        self.assertTrue(build_tips.up_to_date(), "run WebGUI/tools/build_tips.py")
        with open(build_tips.OUT, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        tips = json.loads("\n".join(lines))
        self.assertEqual(len([ln for ln in lines if ln.startswith('"') and ": {" in ln and not ln.endswith("{")]),
                         len(tips["params"]) + len(tips["controls"]) + len(tips["presets"]), "one tip per line")


if __name__ == "__main__":
    unittest.main()

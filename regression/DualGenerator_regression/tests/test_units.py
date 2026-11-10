"""
test_units.py  -  the dual generator's own building blocks on their own: the set parameters handed to the Single
Generator (every name the Single Generator's rule table knows, each in its dual file, and a set's own values for a
few board values), the layout modes, the output folder names and the design checks between the sets.  Fast, no
board written.
"""

import math
import os
import re
import tempfile
import types
import unittest

import harness as H
from Generator.Core.Conflict import ParameterConflict, Report
from Generator.Stator import StatorAssembly
from Dual_Generator.Checks import Dual_DesignChecks as DDC
from Dual_Generator.Core import Dual_SetParameters as SP
from Dual_Generator.Core import Dual_TrackLayout as TL
from Dual_Generator.Run import Dual_OutputFolders as OF


class SetParameters(unittest.TestCase):
    def setUp(self):
        H.restore()

    def tearDown(self):
        H.restore()

    def test_every_single_name_has_a_dual_file(self):
        """The name table is made from the Single Generator's: each of its names lives in exactly one kind of dual
        file (the board file, or the set files of one kind), a board value a set may set for itself also in the
        set file, and the exceptions (MOVED) where they say."""
        from Generator.Checks import ParameterRules as SingleRules
        for name in SingleRules.KNOWN_NAMES:
            kinds = {f for f, names in SP.NAMES_BY_FILE.items() if name in names}
            if name in SP.OVERRIDES:
                self.assertEqual(kinds, {SP.BOARD_FILE, SP.set_file(SP.OVERRIDES[name], 1),
                                         SP.set_file(SP.OVERRIDES[name], 2)}, name)
            elif SP.dual_file_of(name, 1) == SP.BOARD_FILE:
                self.assertEqual(kinds, {SP.BOARD_FILE}, name)
            else:
                self.assertEqual(kinds, {SP.dual_file_of(name, 1), SP.dual_file_of(name, 2)}, name)
        self.assertEqual(SP.dual_file_of("EXCITATION_FREQ_HZ", 2), "Dual_TX2_Parameters.py")
        self.assertEqual(SP.dual_file_of("ROTOR_PCB_THICKNESS_MM", 2), SP.BOARD_FILE)
        self.assertEqual(SP.dual_file_of("PCB_LAYERS", 1), SP.BOARD_FILE)
        self.assertEqual(SP.dual_file_of("RX_TABS", 2), "Dual_RX2_Parameters.py")
        self.assertEqual(SP.dual_file_of("TX_SHAPE", 1), "Dual_TX1_Parameters.py")
        self.assertEqual(len(SP.MOVED), 9)
        self.assertEqual(SP.PARAMETER_FILES[0], SP.BOARD_FILE)
        self.assertEqual(len(SP.PARAMETER_FILES), 9)

    def test_the_repository_files_hold_exactly_the_table(self):
        """The generator's own parameter files set exactly the names of the table (and the board file the dual-only
        names too)."""
        mods = {SP.BOARD_FILE: H.P.BOARD, "Dual_RX1_Parameters.py": H.P.RX1, "Dual_RX2_Parameters.py": H.P.RX2,
                "Dual_TX1_Parameters.py": H.P.TX1, "Dual_TX2_Parameters.py": H.P.TX2,
                "Dual_Rotor1_Parameters.py": H.P.ROTOR1, "Dual_Rotor2_Parameters.py": H.P.ROTOR2,
                "Dual_IC1_Parameters.py": H.P.IC1, "Dual_IC2_Parameters.py": H.P.IC2}
        for file, mod in mods.items():
            present = {n for n in dir(mod) if n.isupper() and not n.startswith("_")}
            self.assertEqual(present, set(SP.NAMES_BY_FILE[file]), file)

    def test_build_takes_each_sets_own_values(self):
        s1, s2 = SP.build(H.P, 1), SP.build(H.P, 2)
        self.assertEqual((s1.LOOPS, s2.LOOPS), (H.P.RX1.LOOPS, H.P.RX2.LOOPS))
        self.assertEqual((s1.TX_NET, s2.TX_NET), ("TX_1", "TX_2"))
        self.assertEqual((s1.RX_NET_PHASE_0_2, s2.RX_NET_PHASE_1_3), ("SIN_1", "COS_2"))
        self.assertEqual(s1.ROTOR_AUTO_COVER_TX, H.P.ROTOR1.ROTOR_AUTO_COVER_TX)
        self.assertEqual(s2.ROTOR_AUTO_COVER_TX, H.P.ROTOR2.ROTOR_AUTO_COVER_TX)
        self.assertEqual(s1.IC_NAME, H.P.IC1.IC_NAME)
        self.assertEqual((s1.PCB_LAYERS, s2.PCB_LAYERS), (4, 4), "the board's layer count")
        self.assertEqual((s1.RX_TABS, s2.TX_SHAPE), (H.P.RX1.RX_TABS, H.P.TX2.TX_SHAPE))
        self.assertEqual(s1.VIA_DIAMETER_MM, H.P.BOARD.VIA_DIAMETER_MM, "None in the set file: the board's value")
        self.assertEqual((s1.VIA_TYPE, s2.VIA_TYPE), (H.P.BOARD.VIA_TYPE, H.P.BOARD.VIA_TYPE))
        self.assertFalse(hasattr(s1, "DUAL_MODE"), "dual-only names are not handed to the Single Generator")
        self.assertFalse(hasattr(s1, "TRACK_GAP_MM"))

    def test_build_with_band_and_edges(self):
        s = SP.build(H.P, 1, band={"RX_R_BASE_MM": 10.0, "RX_A_MM": 1.5}, edges=(7.0, 30.0))
        self.assertEqual((s.RX_R_BASE_MM, s.RX_A_MM), (10.0, 1.5))
        self.assertIsNone(s.INSIDE_RADIUS_MM)
        self.assertIsNone(s.OUTSIDE_RADIUS_MM)
        self.assertEqual((s.INNER_EDGE_RADIUS_MM, s.OUTER_EDGE_RADIUS_MM), (7.0, 30.0))

    def test_missing_name_is_left_out(self):
        H.apply({"TX2.TX_TURNS": H.DELETE})
        s = SP.build(H.P, 2)
        self.assertFalse(hasattr(s, "TX_TURNS"), "the Single Generator's checker reports it")
        self.assertTrue(hasattr(SP.build(H.P, 1), "TX_TURNS"))

    def test_a_set_may_set_board_values_for_itself(self):
        H.apply({"RX2.VIA_DIAMETER_MM": 0.8, "RX2.VIA_DRILL_MM": 0.4, "RX2.VIA_TYPE": "blind",
                 "RX1.MIN_CLEARANCE_MM": 0.2, "TX1.TX_AC_RESISTANCE_FACTOR": 3.0, "IC2.TANK_CAP_SERIES": "E24"})
        s1, s2 = SP.build(H.P, 1), SP.build(H.P, 2)
        self.assertEqual((s1.VIA_DIAMETER_MM, s2.VIA_DIAMETER_MM), (H.P.BOARD.VIA_DIAMETER_MM, 0.8))
        self.assertEqual((s1.VIA_DRILL_MM, s2.VIA_DRILL_MM), (H.P.BOARD.VIA_DRILL_MM, 0.4))
        self.assertEqual((s1.VIA_TYPE, s2.VIA_TYPE), ("through", "blind"))
        self.assertEqual((s1.MIN_CLEARANCE_MM, s2.MIN_CLEARANCE_MM), (0.2, H.P.BOARD.MIN_CLEARANCE_MM))
        self.assertEqual((s1.TX_AC_RESISTANCE_FACTOR, s2.TX_AC_RESISTANCE_FACTOR),
                         (3.0, H.P.BOARD.TX_AC_RESISTANCE_FACTOR))
        self.assertEqual((s1.TANK_CAP_SERIES, s2.TANK_CAP_SERIES), (H.P.BOARD.TANK_CAP_SERIES, "E24"))
        self.assertEqual(SP.overridden(H.P, 2), {"VIA_DIAMETER_MM": 0.8, "VIA_DRILL_MM": 0.4, "VIA_TYPE": "blind",
                                                 "TANK_CAP_SERIES": "E24"})
        # a message about such a value names the set's file; for the other set, the board file
        msg = "VIA_DRILL_MM = 0.9: too big   (Board_Parameters.py)"
        self.assertTrue(SP.rename_single_files(msg, 2, tuple(SP.overridden(H.P, 2))).endswith("(Dual_RX2_Parameters.py)"))
        self.assertTrue(SP.rename_single_files(msg, 1, tuple(SP.overridden(H.P, 1))).endswith("(Dual_Board_Parameters.py)"))
        rep = Report()
        rep.add("error", msg, ("VIA_DRILL_MM",))
        self.assertTrue(SP.for_set(rep, 2, H.P).items[0][1].endswith("(Dual_RX2_Parameters.py)"))

    def test_for_set(self):
        """A Single Generator report as findings of one set: 'set k: ' in front, the set's own dual file names."""
        rep = Report()
        rep.add("error", "LOOPS = 0: must be a whole number of 1 or more   (RX_Parameters.py)", ("LOOPS",))
        rep.add("warning", "TX_TURNS (TX_Parameters.py) and Board_Parameters.py")
        out = SP.for_set(rep, 2)
        self.assertEqual(out.items, [
            ("error", "set 2: LOOPS = 0: must be a whole number of 1 or more   (Dual_RX2_Parameters.py)", ("LOOPS",)),
            ("warning", "set 2: TX_TURNS (Dual_TX2_Parameters.py) and Dual_Board_Parameters.py", ())])
        self.assertEqual(rep.items[1][1], "TX_TURNS (TX_Parameters.py) and Board_Parameters.py", "the report is not changed")

    def test_modules_and_ic_module(self):
        self.assertEqual(SP.modules(H.P, 1), (H.P.RX1, H.P.TX1, H.P.ROTOR1))
        self.assertEqual(SP.modules(H.P, 2), (H.P.RX2, H.P.TX2, H.P.ROTOR2))
        self.assertIs(SP.ic_module(H.P, 2), H.P.IC2)
        with self.assertRaises(ValueError):
            SP.modules(H.P, 3)
        with self.assertRaises(ValueError):
            SP.ic_module(H.P, 0)

    def test_rename_single_files(self):
        text = "LOOPS (RX_Parameters.py) and TX_TURNS (TX_Parameters.py), Board_Parameters.py, IC_Parameters.py"
        self.assertEqual(SP.rename_single_files(text, 2),
                         "LOOPS (Dual_RX2_Parameters.py) and TX_TURNS (Dual_TX2_Parameters.py), Dual_Board_Parameters.py, Dual_IC2_Parameters.py")
        self.assertIn("Dual_Rotor1_Parameters.py", SP.rename_single_files("Rotor_Parameters.py", 1))
        # the file at the end follows the name the message starts with
        self.assertEqual(SP.rename_single_files("EXCITATION_FREQ_HZ = 'x': must be a number   (Board_Parameters.py)", 2),
                         "EXCITATION_FREQ_HZ = 'x': must be a number   (Dual_TX2_Parameters.py)")
        self.assertEqual(SP.rename_single_files("ROTOR_MODE = 3: must be one of ...   (Rotor_Parameters.py)", 1),
                         "ROTOR_MODE = 3: must be one of ...   (Dual_Board_Parameters.py)")
        self.assertEqual(SP.dual_file_of("LOOPS", 2), "Dual_RX2_Parameters.py")
        self.assertEqual(SP.dual_file_of("ROTOR_AUTO_DUTY", 1), "Dual_Rotor1_Parameters.py")
        self.assertEqual(SP.dual_file_of("TX_SHAPE", 1), "Dual_TX1_Parameters.py")
        self.assertIsNone(SP.dual_file_of("NOT_A_NAME", 1))


class TrackLayout(unittest.TestCase):
    def setUp(self):
        H.restore()

    def tearDown(self):
        H.restore()

    def test_default_layout(self):
        lay = TL.resolve(H.P)
        self.assertEqual(lay.mode, 2)
        self.assertAlmostEqual(lay.bore, 7.25)
        self.assertAlmostEqual(lay.outline, 26.875)
        self.assertEqual((lay.band1["ri"], lay.band1["ro"]), (8.45, 11.7))
        self.assertEqual((lay.band2["ri"], lay.band2["ro"]), (18.0, 23.9))
        self.assertAlmostEqual(lay.gap_expected, 3.725, 3)
        self.assertIsNone(lay.gap_setting)
        self.assertEqual(lay.set_band(1), lay.band1["names"])
        self.assertEqual(lay.edges(), (lay.bore, lay.outline))
        self.assertTrue(lay.lines()[0].startswith("layout: DUAL_MODE = 2"))

    def test_mode1_layout_fits_the_bands(self):
        H.apply(H.MODE1_BASE)
        lay = TL.resolve(H.P)
        self.assertEqual(lay.mode, 1)
        self.assertEqual((lay.bore, lay.outline), (8.5, 29.5))
        self.assertEqual(lay.gap_setting, 0.5)
        self.assertEqual((lay.band1["how"], lay.band2["how"]), ("placed", "placed"))
        self.assertLess(lay.band1["ro"], lay.band2["ri"])

    def test_mode_table(self):
        self.assertEqual(TL.MODE_NEEDS, {1: (True, True, 0), 2: (False, False, 2), 3: (True, False, 1), 4: (False, True, 2)})
        for m, needs in TL.MODE_NEEDS.items():
            self.assertEqual(TL.mode_matching(*needs), m)
        self.assertIsNone(TL.mode_matching(True, True, 2))

    def test_mode_of_errors(self):
        for bad in (0, 5, 2.5, "2", True, None):
            H.apply({"BOARD.DUAL_MODE": bad})
            with self.assertRaises(ParameterConflict, msg=repr(bad)):
                TL.mode_of(H.P)
        H.apply({"BOARD.DUAL_MODE": 3})
        self.assertEqual(TL.mode_of(H.P), 3)

    def test_band_of(self):
        self.assertIsNone(TL.band_of(types.SimpleNamespace(RX_TRACE_WIDTH_MM=0.2), 1))
        b = TL.band_of(types.SimpleNamespace(INSIDE_RADIUS_MM=9.7, OUTSIDE_RADIUS_MM=16.05), 1)
        self.assertEqual((b["ri"], b["ro"], b["how"]), (9.7, 16.05, "radii"))
        b = TL.band_of(types.SimpleNamespace(RX_R_BASE_MM=10.0, RX_A_MM=2.0), 2)
        self.assertEqual((b["ri"], b["ro"], b["how"]), (8.0, 12.0, "centre"))
        with self.assertRaises(ParameterConflict):
            TL.band_of(types.SimpleNamespace(INSIDE_RADIUS_MM=9.7), 1)
        with self.assertRaises(ParameterConflict):
            TL.band_of(types.SimpleNamespace(INSIDE_RADIUS_MM=9.7, OUTSIDE_RADIUS_MM=16.05, RX_R_BASE_MM=10.0, RX_A_MM=2.0), 1)
        with self.assertRaises(ParameterConflict):
            TL.band_of(types.SimpleNamespace(INSIDE_RADIUS_MM=16.05, OUTSIDE_RADIUS_MM=9.7), 1)
        with self.assertRaises(ParameterConflict, msg="the Single's rule: a band value must be finite"):
            TL.band_of(types.SimpleNamespace(INSIDE_RADIUS_MM=9.7, OUTSIDE_RADIUS_MM=float("inf")), 1)
        with self.assertRaises(ParameterConflict) as cm:
            TL.band_of(types.SimpleNamespace(RX_R_BASE_MM=2.0), 2)
        self.assertEqual(cm.exception.message, "the band centre and its swing go together, but RX_A_MM is None in "
                         "Dual_RX2_Parameters.py. Set both (the RX band is RX_R_BASE_MM - RX_A_MM ... RX_R_BASE_MM + "
                         "RX_A_MM), or both to None")

    def test_check_mode_names_the_hint(self):
        with self.assertRaises(ParameterConflict) as cm:
            TL.check_mode(H.P, 1, None, None, None, {"names": {"INSIDE_RADIUS_MM": 1, "OUTSIDE_RADIUS_MM": 2}},
                          {"names": {"RX_R_BASE_MM": 3, "RX_A_MM": 4}})
        self.assertIn("matches DUAL_MODE = 2", str(cm.exception))
        self.assertIn("DUAL_MODE", cm.exception.names)
        self.assertIsNone(TL.check_mode(H.P, 2, None, None, None, {"names": {}}, {"names": {}}))
        self.assertIsNone(TL.mode_matching(True, None, 0), "one edge alone matches no mode")

    def test_outer_room_as_rotor_builder_limits_ring_2(self):
        """With ring 2 over the TX2 turns the outline keeps: the overhang, ROTOR_AUTO_EDGE_CLEARANCE_MM, half the
        edge line, the polygon vertices and LAYOUT_TOLERANCE_MM; the rotor settings default as in the Single."""
        H.restore()
        B = H.P.BOARD
        P2 = SP.build(H.P, 2)

        def with_(**kw):
            return types.SimpleNamespace(**dict(vars(P2), **kw))

        def without(*names):
            return types.SimpleNamespace(**{n: v for n, v in vars(P2).items() if n not in names})

        ring = TL.BoardLayout.tx_ring(P2, 0.0)
        edge = ring["outer_copper_edge"] + P2.ROTOR_AUTO_TX_OVERHANG_MM + P2.ROTOR_AUTO_EDGE_CLEARANCE_MM
        fine = P2.EDGE_LINE_WIDTH_MM / 2.0 + P2.ROTOR_CHORD_TOLERANCE_MM
        self.assertLess(fine, B.LAYOUT_TOLERANCE_MM, "the repository's slack covers the edge line and the vertices")
        want = edge + B.LAYOUT_TOLERANCE_MM
        self.assertAlmostEqual(TL.outer_room(P2, B), want, 9)
        no_slack = types.SimpleNamespace(LAYOUT_TOLERANCE_MM=0.0)
        self.assertAlmostEqual(TL.outer_room(P2, no_slack), edge + fine, 9, "no slack: what the ring needs")
        self.assertAlmostEqual(TL.outer_room(with_(EDGE_LINE_WIDTH_MM=0.3), B),
                               edge + 0.15 + P2.ROTOR_CHORD_TOLERANCE_MM, 9)
        none = with_(ROTOR_AUTO_COVER_TX=None, ROTOR_AUTO_TX_OVERHANG_MM=None)
        self.assertAlmostEqual(TL.outer_room(none, B), want, 9, "None: the Single Generator's defaults")
        missing = without("ROTOR_AUTO_COVER_TX", "ROTOR_AUTO_TX_OVERHANG_MM")
        self.assertAlmostEqual(TL.outer_room(missing, B), want, 9, "missing: the same")
        self.assertEqual(TL.ring_vertex_sag(P2, 20.0), P2.ROTOR_CHORD_TOLERANCE_MM, "auto steps")
        steps = types.SimpleNamespace(ROTOR_ARC_STEPS_PER_SECTOR=8, ROTOR_CHORD_TOLERANCE_MM=0.001, ROTOR_AUTO_DUTY=0.5,
                                      LOOPS=16)
        self.assertAlmostEqual(TL.ring_vertex_sag(steps, 20.0),
                               20.0 * (1.0 / math.cos(0.5 * 2 * math.pi / 16 / 8 / 2) - 1.0), 12)
        self.assertLess(TL.outer_room(with_(ROTOR_AUTO_COVER_TX=False), B), want,
                        "no overhang room when ring 2 stays inside the TX ring")

    def test_the_reach_of_set_1_follows_its_copper(self):
        """Set 1's reach past its RX band (BoardLayout.outer_copper_reach): the TX turns and tail, a spiral's extra
        pitch, the fingers.  The defaults: a series TX with no tail, its two ends one pitch outside the last turn."""
        H.restore()
        P1 = SP.build(H.P, 1)
        base = P1.TX_OFFSET_MM + P1.TX_TURNS * P1.TX_PITCH_MM + P1.TX_TRACE_WIDTH_MM / 2.0
        self.assertAlmostEqual(TL.tx_room(P1), base, 9)
        tail = types.SimpleNamespace(**dict(vars(P1), TX_TAIL_EXTRA_MM=1.5))
        self.assertAlmostEqual(TL.tx_room(tail), base + 1.5, 9)
        fingers = types.SimpleNamespace(**dict(vars(P1), RX_TABS="all", RX_TAB_LENGTH_MM=4.0))
        self.assertGreaterEqual(TL.tx_room(fingers), 4.0 + P1.RX_TRACE_WIDTH_MM / 2.0)
        self.assertAlmostEqual(TL.inner_margin(SP.build(H.P, 2)), H.P.BOARD.VIA_DIAMETER_MM / 2.0, 9)
        H.apply({"RX2.VIA_DIAMETER_MM": 0.9, "RX2.VIA_DRILL_MM": 0.45})
        self.assertAlmostEqual(TL.inner_margin(SP.build(H.P, 2)), 0.45, 9, "set 2's own via")


class Assembler(unittest.TestCase):
    def test_folder_names(self):
        self.assertEqual(OF.folder_number(26.875), "26.875")
        self.assertEqual(OF.folder_number(8.5), "8.5")
        self.assertEqual(OF.folder_number(29.0), "29")
        dual = types.SimpleNamespace(bore=7.25, outline=26.875,
                                     sets=(types.SimpleNamespace(N=1, P=types.SimpleNamespace(TX_TURNS=4)),
                                           types.SimpleNamespace(N=16, P=types.SimpleNamespace(TX_TURNS=4))))
        self.assertEqual(OF.folder_name(dual, H.P), "DualCoil_7.25_26.875_1x16_4x4")
        self.assertEqual(OF.project_folder(), H.PROJECT)
        H.restore()
        self.assertEqual(OF.output_dir(H.P.BOARD), os.path.join(H.PROJECT, "Output"))
        d = tempfile.mkdtemp(dir=H.temp_root())
        H.apply({"BOARD.OUTPUT_DIR": d})
        try:
            a = OF.create_output_folder(dual, H.P)
            b = OF.create_output_folder(dual, H.P)
            self.assertEqual(os.path.basename(b), "DualCoil_7.25_26.875_1x16_4x4__1")
            OF.remove_if_empty(a)
            self.assertFalse(os.path.isdir(a))
        finally:
            H.restore()

    def test_output_dir_uses_the_single_rule(self):
        """The Dual checks OUTPUT_DIR with the Single Generator's own rule, so a folder that cannot be created or a link
        to nothing is refused before anything is built (the Dual's old copy of the rule let both through)."""
        root = tempfile.mkdtemp(dir=H.temp_root())
        f = os.path.join(root, "file.txt")
        open(f, "w").close()
        res = H.check({"BOARD.OUTPUT_DIR": os.path.join(f, "sub")})
        self.assertEqual(res.rc, 1)
        self.assertTrue(res.has(r"OUTPUT_DIR .* cannot be created: .* is not a folder"), res.out)
        link = os.path.join(root, "link")
        try:
            os.symlink(os.path.join(root, "nowhere"), link)
        except (OSError, NotImplementedError):
            return                                     # (no symbolic links here: the rest is the Single's own test)
        res = H.check({"BOARD.OUTPUT_DIR": link})
        self.assertEqual(res.rc, 1)
        self.assertTrue(res.has("is a link to something that does not exist"), res.out)

    def test_title_block_names_the_tx_layers_of_both_wirings(self):
        for case, word in (("Board001-default", "Series"), ("Board005-parallel-both-sets", "Parallel")):
            text = H.board(case).text("Stator.kicad_pcb")
            comments = re.findall(r'\(comment \d "(Set \d:[^"]*)"\)', text)
            self.assertEqual(len(comments), 2, case)
            for c in comments:
                self.assertIn(word, c)
                self.assertNotIn("None", c, "the TX layers are named for parallel wiring too")
                self.assertRegex(c, r"Turns: \d+ [\w-]+ \d+ [\w-]+, Ends at")

    def test_record_keeps_the_sets_values_as_given(self):
        """build_ring turns a copy of the set namespace: the record's set sections show the start angles as in
        the files, not shifted by the set's RX pattern zero."""
        rec = H.board("Board001-default").record
        angles = re.findall(r"START_ANGLE_DEG\s+= (\S+)", rec)
        self.assertGreaterEqual(len(angles), 4)
        self.assertEqual(set(angles), {"0.0"}, angles)

    def test_copper_extent_of_a_built_set(self):
        H.restore()
        lay = TL.resolve(H.P)
        s1 = StatorAssembly.build_stator(SP.build(H.P, 1, lay.set_band(1), lay.edges()), 180.0)
        lo, hi = DDC.copper_extent(s1)
        self.assertAlmostEqual(hi, lay.reach1, 3, "set 1 reaches where the layout said")
        self.assertGreater(lo, lay.bore)
        rlo, rhi = DDC.rx_extent(s1)
        self.assertLessEqual(rhi, hi)
        margin = max(H.P.RX1.RX_TRACE_WIDTH_MM, H.P.BOARD.VIA_DIAMETER_MM) / 2.0      # the inner tip vias sit on the band start
        self.assertAlmostEqual(rlo, lay.band1["ri"] - margin, 2)
        self.assertEqual(s1.terminal_deg, 180.0)
        self.assertEqual(s1.angle_deg, 180.0)
        self.assertAlmostEqual(s1.rotation_deg, (180.0 - s1.tx.angle_deg) % 360.0, 12)
        self.assertIn("so that it sits at 180 deg", s1.summary(), "the set's own angle in its summary")
        self.assertEqual(StatorAssembly.TERMINAL_DEG, 0.0, "the Single Generator's angle is never changed")


if __name__ == "__main__":
    unittest.main()

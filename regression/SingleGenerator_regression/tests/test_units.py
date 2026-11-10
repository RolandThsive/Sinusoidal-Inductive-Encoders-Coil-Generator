"""
test_units.py  -  the small building blocks of the Single Generator on their own: the output folder names, the
KiCad writer, the report and colour classes, the parameter helpers, the geometry helpers, and the shared files in
resources/ (the picture makers and the KiCad reader).  Fast, no board written.
"""

import collections
import io
import contextlib
import os
import tempfile
import types
import unittest

import numpy as np

import harness as H
import KiCadReader
import RegressionTools as RT
from Generator.Checks import DesignChecks, ParameterRules
from Generator.Core import BoardLayout, Geometry, Layers
from Generator.Core.Conflict import Colour, ParameterConflict, Report, conflict_title
from Generator.Core.PCBWriter import KiCadBoard, page_size
from Generator.Run import OutputFolders as OF


class OutputFolderNames(unittest.TestCase):
    def test_numbers_in_names(self):
        self.assertEqual(OF.folder_number(15.0), "15")
        self.assertEqual(OF.folder_number(36.8), "36.8")
        self.assertEqual(OF.folder_number(28.2), "28.2")
        self.assertEqual(OF.folder_number(8), "8")
        self.assertEqual(OF.folder_number(1.23456), "1.235")

    def test_folder_name_pattern(self):
        H.restore()
        stator = types.SimpleNamespace(inner_edge_radius=15.0, outer_edge_radius=27.0)
        self.assertEqual(OF.folder_name(stator, H.P), "Coil_15_27_1_1_3_Single_SteppedDiagonal")
        H.apply({"TX_WIRING": "parallel", "TX_SHAPE": "stepped_arc", "LOOPS": 16, "RX_SUBCOILS": 3, "TX_TURNS": 7})
        try:
            self.assertEqual(OF.folder_name(stator, H.P), "Coil_15_27_16_3_7_Parallel_SteppedArc")
            H.apply({"TX_SHAPE": "spiral", "TX_WIRING": "series"})
            self.assertEqual(OF.folder_name(stator, H.P), "Coil_15_27_16_3_7_Series_Spiral")
            H.apply({"TX_SHAPE": "weird", "TX_WIRING": "odd"})
            self.assertEqual(OF.tx_words(stator, H.P), ("Odd", "Weird"), "bad values still make a name; the checks report them")
        finally:
            H.restore()

    def test_output_dir_relative_and_absolute(self):
        H.restore()
        self.assertEqual(OF.output_dir(H.P), os.path.join(H.PROJECT, "Output"))
        self.assertEqual(OF.project_folder(), H.PROJECT)
        H.apply({"OUTPUT_DIR": tempfile.gettempdir()})
        try:
            self.assertEqual(OF.output_dir(H.P), tempfile.gettempdir())
        finally:
            H.restore()

    def test_create_output_folder_never_reuses(self):
        H.restore()
        d = tempfile.mkdtemp(dir=H.temp_root())
        H.apply({"OUTPUT_DIR": d})
        try:
            stator = types.SimpleNamespace(inner_edge_radius=15.0, outer_edge_radius=27.0)
            a = OF.create_output_folder(stator, H.P)
            b = OF.create_output_folder(stator, H.P)
            c = OF.create_output_folder(stator, H.P)
            self.assertEqual([os.path.basename(x) for x in (a, b, c)],
                             ["Coil_15_27_1_1_3_Single_SteppedDiagonal", "Coil_15_27_1_1_3_Single_SteppedDiagonal__1",
                              "Coil_15_27_1_1_3_Single_SteppedDiagonal__2"])
            OF.remove_if_empty(c)
            self.assertFalse(os.path.isdir(c))
            with open(os.path.join(b, "x.txt"), "w") as fh:
                fh.write("x")
            OF.remove_if_empty(b)
            self.assertTrue(os.path.isdir(b), "a folder with files is never removed")
        finally:
            H.restore()


class OutputDirRule(unittest.TestCase):
    """ParameterRules.check_output_dir: the OUTPUT_DIR rule of both generators, on the folder as a usable path."""

    def check(self, d, word="Coil_..."):
        rep = Report()
        ParameterRules.check_output_dir(d, rep, word)
        return rep

    def test_usable_and_new_folders(self):
        root = tempfile.mkdtemp(dir=H.temp_root())
        self.assertEqual(self.check(root).items, [], "an existing writable folder: nothing to say")
        rep = self.check(os.path.join(root, "a", "b"), "DualCoil_...")
        self.assertEqual(rep.errors, [])
        self.assertIn("will be created (the DualCoil_... folder goes inside it)", rep.items[0][1])

    def test_unusable_folders(self):
        root = tempfile.mkdtemp(dir=H.temp_root())
        f = os.path.join(root, "file.txt")
        open(f, "w").close()
        self.assertIn("exists but is not a folder", self.check(f).errors[0])
        self.assertIn(f"cannot be created: {f!r} is not a folder", self.check(os.path.join(f, "sub", "deeper")).errors[0])

    def test_link_to_nothing(self):
        root = tempfile.mkdtemp(dir=H.temp_root())
        link = os.path.join(root, "link")
        try:
            os.symlink(os.path.join(root, "nowhere"), link)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links cannot be made here")
        self.assertIn("is a link to something that does not exist", self.check(link).errors[0])


class Writer(unittest.TestCase):
    def test_number_format(self):
        f = KiCadBoard._f
        self.assertEqual(f(1.0), "1")
        self.assertEqual(f(0.1 + 0.2), "0.3")
        self.assertEqual(f(-0.0), "0")
        self.assertEqual(f(-0.0000001), "0")
        self.assertEqual(f(123.4567891), "123.456789")
        self.assertEqual(f(-15.25), "-15.25")

    def test_quoting(self):
        q = KiCadBoard._q
        self.assertEqual(q('a "b" c\\d\ne'), "a 'b' c/d e")

    def test_nets_and_body(self):
        b = KiCadBoard(title="t", page=(200, 200), thickness=1.6, copper_layers=2, comments=["c1", "c2"])
        self.assertEqual(b.net(""), 0)
        self.assertEqual(b.net("TX"), 1)
        self.assertEqual(b.net("1"), 2)
        self.assertEqual(b.net("TX"), 1, "a net keeps its number")
        b.segment((0, 0), (1, 1), 0.2, "F.Cu", "TX")
        b.via((1, 1), 0.8, 0.4, "1")
        b.circle((0, 0), 5, "Edge.Cuts", 0.05)
        b.polygon([(0, 0), (1, 0), (1, 1)], "F.Cu")
        text = b.text()
        self.assertTrue(text.startswith("(kicad_pcb (version 20221018) (generator coil_generator)"))
        self.assertIn('(paper "User" 200 200)', text)
        self.assertIn('(title_block (title "t") (comment 1 "c1") (comment 2 "c2"))', text)
        self.assertIn('(net 0 "")\n  (net 1 "TX")\n  (net 2 "1")', text)
        self.assertIn('(segment (start 0 0) (end 1 1) (width 0.2) (layer "F.Cu") (net 1))', text)
        self.assertIn('(via (at 1 1) (size 0.8) (drill 0.4) (layers "F.Cu" "B.Cu") (net 2))', text)
        self.assertIn('(gr_circle (center 0 0) (end 0 5) (layer "Edge.Cuts") (width 0.05) (fill none))', text)
        self.assertIn('(gr_poly (pts (xy 0 0) (xy 1 0) (xy 1 1)) (layer "F.Cu") (width 0) (fill solid))', text)
        self.assertIn('(0 "F.Cu" signal)\n    (31 "B.Cu" signal)', text)
        self.assertNotIn("In1.Cu", text)
        self.assertTrue(text.endswith(")\n"))
        four = KiCadBoard(copper_layers=4).text()
        self.assertIn('(1 "In1.Cu" signal)\n    (2 "In2.Cu" signal)', four)

    def test_blind_vias(self):
        b = KiCadBoard(copper_layers=4)
        b.via((1, 1), 0.4, 0.15, "TX")                                          # through: F.Cu B.Cu, no token
        b.via((2, 2), 0.4, 0.15, "TX", layers=("In1.Cu", "F.Cu"))               # layers given but not blind: the same
        b.via((3, 3), 0.4, 0.15, "TX", layers=("F.Cu", "In1.Cu"), blind=True)
        b.via((4, 4), 0.4, 0.15, "TX", layers=("B.Cu", "F.Cu"), blind=True)    # Top + Bottom: a through via after all
        b.via((5, 5), 0.4, 0.15, "TX", layers=None, blind=True)                 # no pair known: through
        b.via((6, 6), 0.4, 0.15, "TX", layers=("In1.Cu", "In2.Cu"), blind=True)  # buried: the same token
        vias = [l for l in b.text().splitlines() if "(via" in l]
        self.assertEqual(vias, [
            '  (via (at 1 1) (size 0.4) (drill 0.15) (layers "F.Cu" "B.Cu") (net 1))',
            '  (via (at 2 2) (size 0.4) (drill 0.15) (layers "F.Cu" "B.Cu") (net 1))',
            '  (via blind (at 3 3) (size 0.4) (drill 0.15) (layers "F.Cu" "In1.Cu") (net 1))',
            '  (via (at 4 4) (size 0.4) (drill 0.15) (layers "F.Cu" "B.Cu") (net 1))',
            '  (via (at 5 5) (size 0.4) (drill 0.15) (layers "F.Cu" "B.Cu") (net 1))',
            '  (via blind (at 6 6) (size 0.4) (drill 0.15) (layers "In1.Cu" "In2.Cu") (net 1))'])
        board = RT.Board(b.text())                                              # the regression parser reads both forms
        self.assertEqual(board.via_blind.tolist(), [False, False, True, False, False, True])
        self.assertEqual(board.via_layers[2], ("F.Cu", "In1.Cu"))
        self.assertEqual(board.unknown, [])

    def test_save_uses_lf(self):
        b = KiCadBoard()
        p = os.path.join(tempfile.mkdtemp(dir=H.temp_root()), "x.kicad_pcb")
        b.save(p)
        with open(p, "rb") as fh:
            raw = fh.read()
        self.assertNotIn(b"\r", raw)
        self.assertEqual(raw.decode(), b.text())

    def test_page_grows_for_large_boards(self):
        H.restore()
        self.assertEqual(page_size(H.P, 100, 100, 27), (200, 200), "the example board fits the smallest page")
        w, h = page_size(H.P, 100, 100, 85)
        self.assertGreater(w, 200)
        self.assertGreater(h, 200)
        w2, h2 = page_size(H.P, 100, 100, 86)
        self.assertGreaterEqual(w2 * h2, w * h, "a bigger board never gets a smaller page")


class Reports(unittest.TestCase):
    def test_titles(self):
        self.assertEqual(conflict_title(["A"]), "A")
        self.assertEqual(conflict_title(["A", "B"]), "A conflicts with B")
        self.assertEqual(conflict_title(["A", "B", "C"]), "A conflicts with B and C")
        self.assertEqual(conflict_title(["A", "B", "C", "D"]), "A conflicts with B, C and D")

    def test_report_levels_and_text(self):
        rep = Report()
        rep.error("e1")
        rep.warn("w1")
        rep.info("i1")
        rep.conflict(("A", "B"), "why")
        rep.conflict(("A", "B"), "soft", level="warning")
        self.assertEqual(rep.errors, ["e1", "A conflicts with B: why"])
        self.assertEqual(rep.warnings, ["w1", "A conflicts with B: soft"])
        other = Report()
        other.error("e2")
        rep.extend(other)
        self.assertEqual(len(rep.items), 6)
        Colour.setup(False)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rep.print()
        out = buf.getvalue()
        self.assertIn("  ERROR   e1\n", out)
        self.assertIn("  WARNING w1\n", out)
        self.assertIn("  info    i1\n", out)
        self.assertIn("  ERROR   A conflicts with B\n          why\n", out)
        self.assertNotIn("\x1b[", out)

    def test_exceptions_become_items(self):
        rep = Report()
        rep.add_exception(ParameterConflict(("X", "Y"), "no"))
        rep.add_exception(ValueError("plain"))
        self.assertEqual(rep.errors, ["X conflicts with Y: no", "plain"])
        e = ParameterConflict(("X", "Y"), "no")
        self.assertEqual(str(e), "X conflicts with Y: no")

    def test_classify_generator_output(self):
        rep = DesignChecks.classify_generator_output(
            "WARNING: a via sits only 0.150 mm from other copper\nWARNING: copper is only -0.1 mm from copper\nnote\n\n")
        self.assertEqual(len(rep.warnings), 1)
        self.assertEqual(len(rep.errors), 1)
        self.assertIn("would short", rep.errors[0])
        self.assertEqual([i for i in rep.items if i[0] == "info"], [("info", "note", ())])


class ParameterHelpers(unittest.TestCase):
    def setUp(self):
        H.restore()

    def tearDown(self):
        H.restore()

    def test_tx_wiring_and_shape(self):
        self.assertEqual(Layers.tx_wiring(H.P), "single")
        self.assertEqual(BoardLayout.tx_shape(H.P), "diagonal")
        H.apply({"TX_WIRING": " Series ", "TX_SHAPE": "STEPPED_ARC"})
        self.assertEqual(Layers.tx_wiring(H.P), "series")
        self.assertEqual(BoardLayout.tx_shape(H.P), "arc")
        H.apply({"TX_WIRING": "twisted"})
        with self.assertRaises(ValueError):
            Layers.tx_wiring(H.P)
        H.apply({"TX_SHAPE": "square"})
        with self.assertRaises(ValueError):
            BoardLayout.tx_shape(H.P)

    def test_rx_band_from_radii_and_from_centre(self):
        band = BoardLayout.rx_band(H.P)
        self.assertEqual((band["ri"], band["ro"]), (16.2, 21.4))
        H.apply({"INSIDE_RADIUS_MM": None, "OUTSIDE_RADIUS_MM": None, "RX_R_BASE_MM": 18.8, "RX_A_MM": 2.6})
        band = BoardLayout.rx_band(H.P)
        self.assertAlmostEqual(band["ri"], 16.2)
        self.assertAlmostEqual(band["ro"], 21.4)
        self.assertEqual(band["mode"], "centre")

    def test_given_band_rules(self):
        """BoardLayout.given_band: the RX band rules of the Single's layout, used for each set of the Dual too."""
        get = lambda **kw: (lambda n: kw.get(n))
        self.assertIsNone(BoardLayout.given_band(get()))
        b = BoardLayout.given_band(get(RX_R_BASE_MM=10.0, RX_A_MM=2.0))
        self.assertEqual((b["ri"], b["ro"], b["mode"], b["given"]),
                         (8.0, 12.0, "centre", {"RX_R_BASE_MM": 10.0, "RX_A_MM": 2.0}))
        b = BoardLayout.given_band(get(INSIDE_RADIUS_MM=9, OUTSIDE_RADIUS_MM=16.5))
        self.assertEqual((b["ri"], b["ro"], b["mode"]), (9.0, 16.5, "radii"))
        for kw in (dict(INSIDE_RADIUS_MM=9.7), dict(RX_A_MM=2.0), dict(RX_R_BASE_MM=2.0, RX_A_MM=3.0),
                   dict(INSIDE_RADIUS_MM=9.7, OUTSIDE_RADIUS_MM=16.0, RX_R_BASE_MM=10.0, RX_A_MM=2.0),
                   dict(INSIDE_RADIUS_MM=16.0, OUTSIDE_RADIUS_MM=9.7), dict(INSIDE_RADIUS_MM=float("inf"), OUTSIDE_RADIUS_MM=30.0),
                   dict(INSIDE_RADIUS_MM=True, OUTSIDE_RADIUS_MM=30.0), dict(RX_R_BASE_MM="10", RX_A_MM=2.0)):
            with self.assertRaises(ParameterConflict, msg=repr(kw)):
                BoardLayout.given_band(get(**kw))
        with self.assertRaises(ParameterConflict) as cm:
            BoardLayout.given_band(get(INSIDE_RADIUS_MM=16.0, OUTSIDE_RADIUS_MM=9.7), "RX2 band", "Dual_RX2_Parameters.py")
        self.assertEqual(cm.exception.message, "the RX2 band's inside radius (16 mm) must be smaller than its outside "
                                               "radius (9.7 mm) (Dual_RX2_Parameters.py)")

    def test_layer_names(self):
        self.assertEqual(Layers.LAYER_NAMES, {1: "F.Cu", 2: "In1.Cu", 3: "In2.Cu", 4: "B.Cu"})
        self.assertEqual(Layers.rx_layer_names(H.P), ("F.Cu", "B.Cu"))
        H.apply({"PCB_LAYERS": 4, "RX_LAYER_A": 2, "RX_LAYER_B": 3})
        self.assertEqual(Layers.rx_layer_names(H.P), ("In1.Cu", "In2.Cu"))

    def test_via_type_pair_and_kind(self):
        self.assertEqual(Layers.via_type(types.SimpleNamespace()), "through", "a missing line means through")
        self.assertEqual(Layers.via_type(types.SimpleNamespace(VIA_TYPE=" Blind ")), "blind")
        with self.assertRaises(ValueError):
            Layers.via_type(types.SimpleNamespace(VIA_TYPE="buried"))
        self.assertEqual(Layers.via_pair("B.Cu", "F.Cu"), ("F.Cu", "B.Cu"))
        self.assertEqual(Layers.via_pair("In2.Cu", "In1.Cu"), ("In1.Cu", "In2.Cu"))
        self.assertEqual([Layers.via_kind(p) for p in (("F.Cu", "B.Cu"), ("F.Cu", "In1.Cu"), ("In2.Cu", "B.Cu"),
                                                        ("In1.Cu", "In2.Cu"), ("F.Cu", "In2.Cu"), ("In1.Cu", "B.Cu"))],
                         ["through", "blind", "blind", "buried", "skip", "skip"])

    def test_chord_tolerance(self):
        self.assertEqual(Geometry.chord_tolerance(H.P, "RX"), 0.001)
        H.apply({"RX_CHORD_TOLERANCE_MM": 0.01})
        self.assertEqual(Geometry.chord_tolerance(H.P, "RX"), 0.01)


class GeometryHelpers(unittest.TestCase):
    def test_point_segment_distance(self):
        d = Geometry.point_segments_distance(np.array([0.0, 1.0]), np.array([[-1.0, 0.0]]), np.array([[1.0, 0.0]]))
        self.assertAlmostEqual(float(np.min(d)), 1.0)
        d = Geometry.point_segments_distance(np.array([3.0, 0.0]), np.array([[-1.0, 0.0]]), np.array([[1.0, 0.0]]))
        self.assertAlmostEqual(float(np.min(d)), 2.0)

    def test_segment_distance(self):
        self.assertAlmostEqual(Geometry.segment_distance((0, 0), (1, 0), (0, 1), (1, 1)), 1.0)
        self.assertAlmostEqual(Geometry.segment_distance((0, 0), (1, 1), (0, 1), (1, 0)), 0.0, msg="crossing segments touch")
        self.assertAlmostEqual(Geometry.segment_distance((0, 0), (1, 0), (2, 0), (3, 0)), 1.0)

    def test_regression_tools_agree_with_the_generator(self):
        """The suite's own distance code (RegressionTools) agrees with the generator's Geometry on random pairs."""
        import RegressionTools as RT
        rng = np.random.default_rng(1)
        A = rng.uniform(-5, 5, (200, 2))
        B = rng.uniform(-5, 5, (200, 2))
        C = rng.uniform(-5, 5, (200, 2))
        D = rng.uniform(-5, 5, (200, 2))
        ours = RT.segment_segment_distance(A, B, C, D)
        theirs = np.array([Geometry.segment_distance(a, b, c, d) for a, b, c, d in zip(A, B, C, D, strict=True)])
        self.assertTrue(np.allclose(ours, theirs, atol=1e-9), f"max difference {np.abs(ours - theirs).max()}")
        P = rng.uniform(-5, 5, (200, 2))
        ours = RT.point_segment_distance(P, A, B)
        theirs = np.array([float(np.min(Geometry.point_segments_distance(p, a[None, :], b[None, :]))) for p, a, b in zip(P, A, B, strict=True)])
        self.assertTrue(np.allclose(ours, theirs, atol=1e-9))

    def test_elliptic_integrals(self):
        K, E = Geometry.ellipk_ellipe(0.0)
        self.assertAlmostEqual(float(K), np.pi / 2, 6)
        self.assertAlmostEqual(float(E), np.pi / 2, 6)
        K, E = Geometry.ellipk_ellipe(0.5)
        self.assertAlmostEqual(float(K), 1.8540746773, 5)
        self.assertAlmostEqual(float(E), 1.3506438810, 5)


class SharedHooks(unittest.TestCase):
    """The hooks the Dual Generator builds each set with: the stator turned to any terminal angle, the rotor's
    start offset."""

    @classmethod
    def setUpClass(cls):
        H.restore()
        from Generator.Stator import StatorAssembly
        cls.SA = StatorAssembly
        with contextlib.redirect_stderr(io.StringIO()):
            cls.s0 = StatorAssembly.build_stator(H.P)
            cls.s90 = StatorAssembly.build_stator(H.P, 90.0)

    def tearDown(self):
        H.restore()

    def test_stator_turned_to_any_terminal_angle(self):
        s0, s90 = self.s0, self.s90
        self.assertEqual((s0.terminal_deg, s90.terminal_deg, s90.angle_deg), (0.0, 90.0, 90.0))
        self.assertEqual(self.SA.TERMINAL_DEG, 0.0, "the module's angle is never changed")
        self.assertAlmostEqual(s90.rotation_deg, (s0.rotation_deg + 90.0) % 360.0, 9)
        for name in ("rx_segments", "tx_segments"):
            turned, _vias = self.SA.rotate_copper(getattr(s0, name), [], s0.cx, s0.cy, 90.0)
            ours = np.array([(g.a, g.b) for g in turned])
            theirs = np.array([(g.a, g.b) for g in getattr(s90, name)])
            self.assertEqual(ours.shape, theirs.shape, name)
            self.assertTrue(np.allclose(ours, theirs, atol=1e-9), name)
        self.assertIn("so that it sits at 90 deg", s90.summary())
        self.assertEqual(s0.nets(), [H.P.TX_NET, H.P.RX_NET_PHASE_1_3, H.P.RX_NET_PHASE_0_2])

    def test_add_copper_is_the_copper_of_write(self):
        """Stator.add_copper puts on a board exactly the nets, segments and vias that Stator.write puts in its file,
        in the same order (the Dual Generator writes each set with it)."""
        board = KiCadBoard(title="t", comments=[], page=(297, 210), thickness=1.6, copper_layers=H.P.PCB_LAYERS)
        for net in self.s0.nets():
            board.net(net)
        self.s0.add_copper(board)
        path = os.path.join(tempfile.mkdtemp(dir=H.temp_root()), "s.kicad_pcb")
        self.s0.write(path)
        with open(path, encoding="utf-8") as fh:
            written = fh.read().splitlines()
        copper = lambda lines: [l for l in lines if l.startswith(("  (net ", "  (segment ", "  (via "))]
        ours = copper(board.text().splitlines())
        self.assertEqual(ours, copper(written))
        self.assertEqual(len(ours), 4 + len(self.s0.rx_segments) + len(self.s0.tx_segments) + len(self.s0.rx_vias)
                         + len(self.s0.tx_vias), "the empty net and the three nets, then every piece of copper")

    def test_rotor_start_offset(self):
        from Generator.Rotor import RotorBuilder as RB
        a = RB.RotorDesign(H.P, stator=self.s0, start_offset_deg=30.0)
        start = H.P.ROTOR_AUTO_START_ANGLE_DEG
        H.apply({"ROTOR_AUTO_START_ANGLE_DEG": start + 30.0})
        b = RB.RotorDesign(H.P, stator=self.s0)
        H.restore()
        self.assertEqual(a.start_angle, b.start_angle)
        self.assertEqual(a.sector_polygon(0), b.sector_polygon(0))
        self.assertEqual(a.P.ROTOR_AUTO_START_ANGLE_DEG, start, "the parameters are not changed")


class Pictures(unittest.TestCase):
    """resources/RepresentativeSVGMaker.py and ActualSVGMaker.py draw every rotor the generators can write, also a
    custom rotor without outline or bore (ROTOR_CUSTOM_OUTLINE_RADIUS_MM / ROTOR_CUSTOM_BORE_RADIUS_MM = None)."""

    OUTLINE, BORE = "(end 100 127)", "(end 100 115)"      # the rotor's two Edge.Cuts circles in Board001-default

    def test_rotor_with_and_without_its_edges(self):
        import ActualSVGMaker
        import RepresentativeSVGMaker as R
        board = os.path.join(H.SUITE, "Board001-default")
        with open(os.path.join(board, "Stator.kicad_pcb"), encoding="utf-8", newline="") as fh:
            stator = fh.read()
        with open(os.path.join(board, "Rotor.kicad_pcb"), encoding="utf-8", newline="") as fh:
            rotor = fh.read()
        self.assertEqual(sum(self.OUTLINE in l or self.BORE in l for l in rotor.splitlines()), 2)
        for keep, want in (((self.OUTLINE, self.BORE), (27.0, 15.0)), ((self.OUTLINE,), (27.0, None)),
                           ((self.BORE,), (None, 15.0)), ((), (None, None))):
            with self.subTest(keep=keep):
                folder = tempfile.mkdtemp(dir=H.temp_root())
                text = "".join(l for l in rotor.splitlines(keepends=True)
                               if not ('"Edge.Cuts"' in l and not any(k in l for k in keep)))
                for name, body in (("Stator.kicad_pcb", stator), ("Rotor.kicad_pcb", text)):
                    with open(os.path.join(folder, name), "w", encoding="utf-8", newline="") as fh:
                        fh.write(body)
                circles = R.read(os.path.join(folder, "Rotor.kicad_pcb"))
                cx, cy, outline, bore, reach = R.rotor_disc(circles[2], circles[3], (100.0, 100.0))
                self.assertEqual((cx, cy, outline, bore), (100.0, 100.0) + want)
                self.assertTrue(15.0 < reach < 27.0, reach)
                for maker in (R, ActualSVGMaker):
                    with contextlib.redirect_stderr(io.StringIO()):
                        svg = maker.make_svg(folder)
                    with open(svg, encoding="utf-8") as fh:
                        self.assertIn("<polygon", fh.read(), f"{maker.__name__}: the rotor copper is drawn")

    def test_a_board_saved_again_by_kicad_gives_the_same_pictures(self):
        """KiCad 7 and KiCad 10 write a board they saved again with their own field order, items over several lines
        and fields of their own (uuid, stroke): both makers draw the same items from it as from the board the
        generator wrote, only in KiCad's order.  (The patterns the makers used before the shared reader found no
        Edge.Cuts circle in either file.)"""
        import ActualSVGMaker
        import RepresentativeSVGMaker as R
        svgs = {}
        for kind in ("", "_saved_by_kicad7", "_saved_by_kicad10"):
            folder = tempfile.mkdtemp(dir=H.temp_root())
            for part in ("stator", "rotor"):
                with open(os.path.join(KiCadReading.FILES, f"board047_{part}{kind}.kicad_pcb"), encoding="utf-8",
                          newline="") as src, \
                        open(os.path.join(folder, part.capitalize() + ".kicad_pcb"), "w", encoding="utf-8",
                             newline="") as dst:
                    dst.write(src.read())
            for maker in (R, ActualSVGMaker):
                with contextlib.redirect_stderr(io.StringIO()):
                    path = maker.make_svg(folder)
                with open(path, encoding="utf-8") as fh:
                    svgs[(maker.__name__, kind)] = sorted(fh.read().splitlines())
        for maker in (R, ActualSVGMaker):
            for kind in ("_saved_by_kicad7", "_saved_by_kicad10"):
                with self.subTest(maker=maker.__name__, kind=kind):
                    self.assertEqual(svgs[(maker.__name__, kind)], svgs[(maker.__name__, "")])


class KiCadReading(unittest.TestCase):
    """resources/KiCadReader.py, which reads the boards for the silkscreen step, the two picture makers and the Dual
    Layout pictures.  It must read every reference board as the test parser (RegressionTools.Board, which shares no
    code with it) does, a board that KiCad saved again as the board itself, and every via kind.  The files in
    tests/kicad_files: Board047's stator and rotor as the generator wrote them and as KiCad 7 and KiCad 10 saved them
    again (pcbnew.LoadBoard and SaveBoard in the kicad/kicad images the CI uses), and a small 4-layer board with one
    via of each kind, by hand, with its KiCad 10 copy."""

    FILES = os.path.join(H.HERE, "kicad_files")

    @staticmethod
    def text(name):
        path = os.path.join(KiCadReading.FILES, name)
        with open(path, encoding="utf-8", newline="") as fh:
            return fh.read()

    @staticmethod
    def content(board):
        """What a board holds, independent of the order of its items and of its net numbers."""
        net = board.nets.get

        def num(pair):
            return tuple(float(v) for v in pair)

        return dict(
            layers=board.copper_layers, title=board.title, comments=board.comments, skipped=board.skipped,
            segments=collections.Counter((num(s.start), num(s.end), float(s.width), s.layer, net(s.net))
                                         for s in board.segments),
            vias=collections.Counter((num(v.at), float(v.size), float(v.drill), v.layers, net(v.net), v.kind)
                                     for v in board.vias),
            circles=collections.Counter((num(c.center), num(c.end), float(c.width), c.layer, c.filled)
                                        for c in board.circles),
            polygons=collections.Counter((tuple(num(p) for p in g.points), float(g.width), g.layer, g.filled)
                                         for g in board.polygons))

    def test_every_reference_board_reads_as_the_test_parser_reads_it(self):
        for name, folder in H.S.boards().items():
            for file in ("Stator.kicad_pcb", "Rotor.kicad_pcb"):
                with self.subTest(board=name, file=file):
                    with open(os.path.join(folder, file), encoding="utf-8", newline="") as fh:
                        text = fh.read()
                    self.assertEqual(RT.reader_differences(KiCadReader.read(text), RT.Board(text)), [])

    def test_a_board_saved_again_by_kicad_reads_the_same(self):
        for part in ("stator", "rotor"):
            written = KiCadReader.read(self.text(f"board047_{part}.kicad_pcb"))
            self.assertEqual(RT.reader_differences(written, RT.Board(self.text(f"board047_{part}.kicad_pcb"))), [])
            for version in (7, 10):
                with self.subTest(part=part, kicad=version):
                    text = self.text(f"board047_{part}_saved_by_kicad{version}.kicad_pcb")
                    self.assertIn("(uuid " if version == 10 else "(tstamp ", text, "the file is KiCad's own")
                    self.assertEqual(self.content(KiCadReader.read(text)), self.content(written))
        k10 = self.text("board047_stator_saved_by_kicad10.kicad_pcb")
        self.assertNotIn("\n\t(net 1 ", k10, "KiCad 10 lists no nets ...")
        self.assertIn('(net "TX")', k10, "... and names the net of each track")
        self.assertEqual(sorted(KiCadReader.read(k10).nets.values()), ["1", "2", "TX"])

    def test_every_via_kind(self):
        want = [("blind", ("F.Cu", "In2.Cu"), "SIN_1"), ("buried", ("In1.Cu", "In2.Cu"), "COS_1"),
                ("micro", ("F.Cu", "In1.Cu"), "COS_1"), ("through", ("F.Cu", "B.Cu"), "SIN_1")]
        for name in ("every_via_kind.kicad_pcb", "every_via_kind_saved_by_kicad10.kicad_pcb"):
            with self.subTest(file=name):
                board = KiCadReader.read(self.text(name))
                self.assertEqual(sorted((v.kind, v.layers, board.nets[v.net]) for v in board.vias), want)
                self.assertEqual(board.copper_layers, ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"])
                self.assertEqual(len(board.segments), 4)
        self.assertEqual(self.content(KiCadReader.read(self.text("every_via_kind_saved_by_kicad10.kicad_pcb"))),
                         self.content(KiCadReader.read(self.text("every_via_kind.kicad_pcb"))))

    def test_numbers_keep_their_text(self):
        item = KiCadReader.parse('(a 1.50 -0.0 1e-3 +4 .5 1.2.3 "7" word)')[0]
        self.assertEqual([str(v) for v in item[1:6]], ["1.50", "-0.0", "1e-3", "+4", ".5"])
        self.assertEqual([f"{v}" for v in item[1:3]], ["1.50", "-0.0"])
        self.assertEqual(item[1] + 1, 2.5, "a number is a float for arithmetic")
        self.assertTrue(all(isinstance(v, KiCadReader.Number) for v in item[1:6]))
        self.assertEqual([type(v) for v in item[6:]], [str, KiCadReader.Text, str], "not numbers: a bare word, a quoted string")

    def test_fields_in_any_order(self):
        head = '(kicad_pcb (version 20221018) (layers (0 "F.Cu" signal) (31 "B.Cu" signal)) (net 0 "") (net 1 "TX")\n'
        plain = KiCadReader.read(head + '(segment (start 1 2) (end 3 4) (width 0.25) (layer "B.Cu") (net 1)))')
        other = KiCadReader.read(head + '(segment locked (net 1) (uuid "x") (layer "B.Cu") (stroke (width 0.25))'
                                        ' (end 3 4) (start 1 2)))')
        self.assertEqual(plain.segments, other.segments)
        self.assertEqual(plain.segments[0], ((1, 2), (3, 4), 0.25, "B.Cu", 1))

    def test_nets_given_by_name_are_numbered(self):
        board = KiCadReader.read('(kicad_pcb (version 20260206)\n'
                                 ' (segment (start 0 0) (end 1 0) (width 0.2) (layer "F.Cu") (net "TX"))'
                                 ' (segment (start 0 0) (end 0 1) (width 0.2) (layer "F.Cu") (net "SIN_1"))'
                                 ' (via (at 0 0) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "TX"))'
                                 ' (segment (start 0 1) (end 1 1) (width 0.2) (layer "F.Cu") (net "")))')
        self.assertEqual(board.nets, {1: "TX", 2: "SIN_1", 0: ""})
        self.assertEqual([s.net for s in board.segments] + [v.net for v in board.vias], [1, 2, 0, 1])

    def test_what_is_not_read_and_what_is_not_a_board(self):
        board = KiCadReader.read('(kicad_pcb (version 20221018)\n (arc (start 0 0) (mid 1 1) (end 2 0))'
                                 ' (zone (net 0)) (footprint "R_0603"))')
        self.assertEqual(board.skipped, ["arc", "footprint", "zone"])
        for text, says in (('(kicad_sch (version 1)\n)', "not a KiCad board file"),
                           ('(kicad_pcb (version 1)\n', "ends inside a bracket"),
                           ('(kicad_pcb (version 1)))\n', "no '('")):
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as e:
                    KiCadReader.read(text)
                self.assertIn(says, str(e.exception))

    def test_a_path_and_the_text_read_alike(self):
        path = os.path.join(self.FILES, "board047_rotor.kicad_pcb")
        boards = [KiCadReader.read(self.text("board047_rotor.kicad_pcb")), KiCadReader.read(path)]
        self.assertEqual(self.content(boards[1]), self.content(boards[0]))
        self.assertEqual(boards[1].path, path)


class Harness(unittest.TestCase):
    def test_delete_and_restore(self):
        H.apply({"LOOPS": 5, "NEW_NAME": 1, "TX_TURNS": H.DELETE})
        self.assertEqual(H.P.LOOPS, 5)
        self.assertTrue(hasattr(H.P, "NEW_NAME"))
        self.assertFalse(hasattr(H.P, "TX_TURNS"))
        H.restore()
        self.assertEqual(H.P.LOOPS, 1)
        self.assertFalse(hasattr(H.P, "NEW_NAME"))
        self.assertEqual(H.P.TX_TURNS, 3)

    def test_no_pycache_is_written(self):
        """The suite, the generator and the regression tools leave no __pycache__ folders (new files only: untracked,
        or ignored by .gitignore, which keeps bytecode out of git and so would hide it from a plain git status)."""
        import subprocess
        try:
            out = subprocess.run(["git", "status", "--porcelain", "--ignored", "--", H.PROJECT, H.RESOURCES,
                                  H.REGRESSION], capture_output=True, text=True, cwd=H.REPO, timeout=30).stdout
        except (OSError, subprocess.SubprocessError):
            self.skipTest("git is not available")
        strays = [l for l in out.splitlines() if l[:2] in ("??", "!!") and ("__pycache__" in l or l.endswith(".pyc"))]
        self.assertEqual(strays, [])


if __name__ == "__main__":
    unittest.main()

"""
test_boards.py  -  the test boards.  Each folder BoardNNN-<what it tests> next to this tests folder holds a complete
set of the generator's parameter files and the files the generator wrote from them: Stator.kicad_pcb and
Rotor.kicad_pcb, their project files Stator.kicad_pro and Rotor.kicad_pro, and Parameters.txt (without the lines that
change with every run).  Every board is written again from its own parameter files, and each of the five files must
equal the copy in the folder character for character.

Also checked: every board folder sets exactly the names that the generator's own parameter files set (a parameter
added to the generator has to be added to every board: python regression/boards.py sync), holds nothing else, and
is listed in the table of ../README.md (python regression/boards.py table writes it).

When a difference is intended (the generator was changed on purpose), read the printed differences, then run
    python regression/run_regression.py single --update-references
and commit the new files together with the change that caused it.  A new board:  python regression/boards.py new.
"""

import os
import unittest

import harness as H
import RegressionHarness as RH

PICTURES = ("_Representative.svg", "_Actual.svg")   # resources/RepresentativeSVGMaker.py, ActualSVGMaker.py


class BoardReferences(unittest.TestCase):
    """One test per board and file: test_Board007-spiral-tx__Stator, test_Board007-spiral-tx__Stator_project (its
    Stator.kicad_pro) and so on."""


def _make(board, file):
    def test(self):
        H.S.check_reference(self, board, file)
    test.__doc__ = f"{board}: {file} equals the copy in its folder"
    return test


for _board in H.BOARDS:
    for _file in RH.OUTPUT_FILES:
        _stem, _ext = _file.split(".")
        setattr(BoardReferences, f"test_{_board}__{_stem}" + ("_project" if _ext == "kicad_pro" else ""),
                _make(_board, _file))


class BoardFolders(unittest.TestCase):
    EXPECTED_NAMES = {
        "Board001-default": "Coil_15_27_1_1_3_Single_SteppedDiagonal",
        "Board002-loops-4-subcoils-2": "Coil_15_27_4_2_3_Single_SteppedDiagonal",
        "Board003-loops-16-tabs-single": "Coil_15_27_16_1_3_Single_SteppedDiagonal",
        "Board004-four-layer-series": "Coil_15_27_1_1_3_Series_SteppedDiagonal",
        "Board005-four-layer-parallel-staggered": "Coil_15_27_1_1_3_Parallel_SteppedDiagonal",
        "Board007-spiral-tx": "Coil_15_28.2_1_1_5_Single_Spiral",
        "Board008-stepped-arc-tx": "Coil_15_27_1_1_2_Single_SteppedArc",
        "Board010-band-from-centre": "Coil_15_27_1_1_3_Single_SteppedDiagonal",
    }

    def test_folder_names(self):
        """The output folder is named after the board (Coil_<inner>_<outer>_<loops>_...)."""
        for case, name in self.EXPECTED_NAMES.items():
            if case not in H.BOARDS:
                continue
            with self.subTest(case=case):
                self.assertEqual(os.path.basename(H.board(case).folder), name)

    def test_every_board_writes_its_files(self):
        for case in H.BOARDS:
            with self.subTest(case=case):
                res = H.board(case)
                name = os.path.basename(res.folder)
                self.assertEqual(sorted(os.listdir(res.folder)),
                                 sorted(RH.OUTPUT_FILES + tuple(name + s for s in PICTURES)))
                self.assertTrue(res.has(r"SUCCESS: Stator\.kicad_pcb, Stator\.kicad_pro, Rotor\.kicad_pcb, Rotor\.kicad_pro and "
                                         r"Parameters\.txt written"), res.out[-400:])
                self.assertEqual(res.made, [os.path.basename(res.folder)], "exactly one folder per run")

    def test_board_folders_are_complete(self):
        """Each board folder: every parameter file, with exactly the names the generator's own file sets, the five
        written files, and nothing else."""
        self.assertTrue(H.S.boards(every=True), "no board folders")
        for case in H.S.boards(every=True):
            with self.subTest(case=case):
                problems = H.S.folder_problems(case)
                self.assertFalse(problems, f"{case}:\n  " + "\n  ".join(problems))

    def test_first_board_is_the_default(self):
        """Every run of the suite starts from the first board's values, so it is the generator's defaults."""
        self.assertEqual(next(iter(H.S.boards(every=True))), "Board001-default")

    def test_readme_lists_every_board(self):
        readme = os.path.join(H.SUITE, "README.md")
        self.assertEqual(RH.readme_table(readme), RH.board_table(H.SUITE, H.PARAMETER_FILES),
                         "the board table in README.md is out of date: python regression/boards.py table")


class BoardTool(unittest.TestCase):
    """regression/boards.py, which both suites' board folders are made and kept with (tested here once)."""

    OWN = ('"""a parameter file"""\n\nA = 1          # the first\n\n# about B\n# more about B\nB = [1,\n     2]\n'
           'C = "x"        # the third\n')

    @classmethod
    def setUpClass(cls):
        import importlib
        cls.B = importlib.import_module("boards")

    def test_set_value_keeps_the_comment(self):
        text = self.B.set_value(self.OWN, "C", "y z")
        self.assertIn('C = "y z"        # the third\n', text)
        self.assertEqual(self.B.set_value(self.OWN, "B", (3,)).count("B = (3,)\n"), 1)
        self.assertIsNone(self.B.set_value(self.OWN, "D", 1))

    def test_sync_adds_a_missing_name_with_its_comment(self):
        board = self.OWN.replace("# about B\n# more about B\nB = [1,\n     2]\n", "").replace('"x"', '"mine"')
        text, added, removed = self.B.synced(board, self.OWN)
        self.assertEqual((added, removed), (["B"], []))
        self.assertIn("A = 1          # the first\n\n# about B\n# more about B\nB = [1,\n     2]\nC = \"mine\"", text)

    def test_sync_removes_a_name_the_generator_dropped(self):
        board = self.OWN + "# about D\nD = 4\n"
        text, added, removed = self.B.synced(board, self.OWN)
        self.assertEqual((added, removed), ([], ["D"]))
        self.assertEqual(text, self.OWN)

    def test_sync_leaves_a_complete_file_alone(self):
        board = self.OWN.replace("1          #", "7          #")
        self.assertEqual(self.B.synced(board, self.OWN), (board, [], []))

    def test_board_folders_are_found_by_name_and_number(self):
        found = RH.find_boards(H.SUITE)
        self.assertEqual(list(RH.select_boards(found, ["1"])), ["Board001-default"])
        self.assertEqual(list(RH.select_boards(found, ["Board001", "Board001-default"])), ["Board001-default"])
        with self.assertRaises(SystemExit):
            RH.select_boards(found, ["Board999"])


if __name__ == "__main__":
    unittest.main()

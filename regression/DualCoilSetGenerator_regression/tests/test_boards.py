"""
test_boards.py  -  the test boards.  Each folder BoardNNN-<what it tests> next to this tests folder holds a complete
set of the Dual Coil Set Generator's parameter files and the files the generator wrote from them: Stator.kicad_pcb and
Rotor.kicad_pcb, their project files Stator.kicad_pro and Rotor.kicad_pro, and Parameters.txt (without the lines that
change with every run).  Every board is written again from its own parameter files, and each of the five files must
equal the copy in the folder character for character.

Also checked: every board folder sets exactly the names that the generator's own parameter files set (a parameter
added to the generator has to be added to every board: python regression/boards.py sync), holds nothing else, and
is listed in the table of ../README.md (python regression/boards.py table writes it).

When a difference is intended (the generator was changed on purpose), read the printed differences, then run
    python regression/run_regression.py dual --update-references
and commit the new files together with the change that caused it.  A new board:  python regression/boards.py new.
"""

import os
import unittest

import harness as H
import RegressionHarness as RH

PICTURES = ("_Representative.svg", "_Actual.svg")   # Generators/resources/RepresentativeSVGMaker.py, ActualSVGMaker.py


class BoardReferences(unittest.TestCase):
    """One test per board and file: test_Board007-custom-rotor__Stator, test_Board007-custom-rotor__Stator_project
    (its Stator.kicad_pro) and so on."""


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
        "Board001-default": "DualCoil_7.25_26.875_1x16_4x4",
        "Board002-layout-32-fitted-bands": "DualCoil_8.5_29.5_1x16_3x3",
        "Board003-layout-10-rx1-band-and-gap": "DualCoil_8.5_29.5_1x16_3x3",
        "Board004-layout-07-all-given": "DualCoil_8.5_29.5_1x16_3x3",
        "Board005-parallel-both-sets": "DualCoil_8.5_29.5_1x16_3x3",
        "Board006-loops-2x8-rotor-from-board": "DualCoil_7.25_26.875_2x8_4x4",
    }

    def test_folder_names(self):
        """The output folder is named after the board (DualCoil_<inner>_<outer>_<loops>_<turns>)."""
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


if __name__ == "__main__":
    unittest.main()

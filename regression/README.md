# Regression testing

The regression tests of both generators live here, each suite next to its test boards.  A test board is a folder
with a complete set of parameter files and the boards the generator wrote from them, so a board can be read, opened
in KiCad, copied into a generator's `Parameters` folder and run again by hand.

```
regression/
  run_regression.py               runs the tests (both suites, or one)
  boards.py                       makes a new test board, keeps the board folders in step with the generators
  RegressionHarness.py            the plumbing both suites share (runs a generator in memory, reads the boards)
  RegressionTools.py              reads a written .kicad_pcb back and measures it, independently of the generators
  SingleGenerator_regression/
    README.md                     what each test checks, and the table of the boards
    tests/                        the test files
    Board001-default/              the generator's defaults
      Board_Parameters.py  IC_Parameters.py  RX_Parameters.py  Rotor_Parameters.py  TX_Parameters.py
      SilkScreenSuggestion_Parameters.py
      Stator.kicad_pcb.gz  Rotor.kicad_pcb.gz  Parameters.txt
    Board002-loops-4-subcoils-2/
    ...
  DualGenerator_regression/
    README.md
    tests/
    Board001-default/              the ten Dual_..._Parameters.py files, and the three written files
    ...
```

## Running the tests

    python regression/run_regression.py                        both suites (about 30 minutes)
    python regression/run_regression.py single                 the Single Generator's suite only
    python regression/run_regression.py dual -v                the Dual Generator's, one line per test
    python regression/run_regression.py single -k checker      only the tests whose name contains "checker"
    python regression/run_regression.py dual --board Board007   the board tests on Board007 only
    python regression/run_regression.py single --update-references
                                                               write every board's files anew (see below)

Needs what the generators need: Python 3.11 to 3.15 and numpy (`pip install -r requirements.txt`).  The exit code is
0 when every test passed.  The tests write their boards into a temporary folder; `--keep` keeps it and prints where.
The pull request checks run both suites on Windows, macOS and Linux
([Regression Testing on the wiki](../docs/wiki/Regression-Testing.md) has the details).

## How a board is tested

Each board folder is written again from its own parameter files, in memory (no parameter file is touched), and the
three files that come out must equal the ones in the folder character for character:

- `Stator.kicad_pcb.gz` and `Rotor.kicad_pcb.gz`, the boards (kept gzipped: they are large and nobody edits them;
  `python regression/boards.py unpack single Board007` puts plain copies in a folder for KiCad),
- `Parameters.txt`, the record of the run, without the lines that change with every run (the time, the folder and
  the command, and the verbatim copies of the parameter files, whose comments are not a regression).

Besides the comparison, every board is measured with `RegressionTools.py`: copper inside the edges, the clearance
between nets, closed coils, the rotor sectors, and the rest of `tests/test_invariants.py`.  And every board folder
must set exactly the names that the generator's own parameter files set, and hold nothing else.

Every other test (the checker cases, the units, the silkscreen) starts from the values of `Board001-default`, so the
values in a generator's own `Parameters` folder, the ones you design with, never change a test.

When a comparison fails, the generator writes something different from what it wrote when the board was saved: the
test prints the lines that differ.  If the change is intended, write the files anew and commit them with the change
that caused it:

    python regression/run_regression.py single --update-references

## Adding a board

    python regression/boards.py new single "spiral-tx-8-turns" TX_SHAPE=spiral TX_TURNS=8
    python regression/boards.py new dual "rx2-cosine-r" RX2.RX_PROFILE=cosine_r
    python regression/boards.py new dual "terminals-45-225-blind" BOARD.TERMINAL_1_DEG=45.0 --from Board010

The first argument is the generator, the second what the board tests: the folder becomes `BoardNNN-<what it tests>`,
with the next free number.  Each `NAME=VALUE` changes one value, written as in a parameter file; a Dual Generator
name starts with its file (`BOARD.`, `RX1.`, `RX2.`, `TX1.`, `TX2.`, `ROTOR1.`, `ROTOR2.`, `IC1.`, `IC2.`,
`SILK.`), a Single Generator silkscreen value with `SILK.`.  The parameter files are copied from
`Board001-default` (or from the board named with `--from`) and each value is replaced where it stands, so its comment
stays with it.  Then the board is written, its files saved, its tests run and the table in the suite's README
written anew.  A board that does not build, or fails its tests, is removed again; read what the run printed.

A board can also be made by hand: copy a board folder, edit its parameter files, then

    python regression/run_regression.py single --update-references --board Board042 -k BoardReferences
    python regression/boards.py table

## When a generator gains or loses a parameter

Every board folder must set the same names as the generator's own parameter files.  After adding or removing a
parameter in a generator:

    python regression/boards.py sync

copies the new name, with its value and its comment, from the generator's file into every board folder (after the
name that comes before it there), and removes a name the generator no longer has.  Then run the tests; where the
boards changed on purpose, `--update-references`.

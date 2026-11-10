# 30. Regression Testing

Both generators have a regression test suite that runs the generator the way a user does, with parameter values set in
memory, and checks what it prints and what it writes. Both suites live in the [`regression`](https://github.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/tree/main/regression) folder at the root
of the repository, each next to its test boards: a test board is a folder with a complete set of parameter files and
the boards the generator wrote from them. No test run touches the parameter files, the `Output` folders or the
generators. The suites need what the generators need: Python 3.11 to 3.15 and NumPy (see requirements.txt).

## 30.1 Running The Tests

From the root of the repository:

```bash
python regression/run_regression.py                # both suites, about 45 minutes
python regression/run_regression.py single         # the Single Generator's suite only
python regression/run_regression.py dual           # the Dual Generator's suite only
```

| Option | Effect |
|---|---|
| `-v` | One line per test |
| `-k <word>` | Only the tests whose name contains the word, for example `-k checker` or `-k silkscreen` (may be given more than once) |
| `--board <name>` | The board tests on this board only, for example `--board Board007`; the other tests as usual |
| `--update-references` | Write each board's saved files anew from the generator as it is now |
| `--keep` | Keep the temporary output folder the boards are written to |

The exit code is 0 when every test passed.

## 30.2 The Test Boards

```
regression/
├── run_regression.py             Runs the tests
├── boards.py                     Makes a new test board; keeps the board folders in step with the generators
├── RegressionHarness.py          What both suites share: runs a generator in memory, finds the board folders
├── RegressionTools.py            Reads a written .kicad_pcb back and measures it, independently of the generators
├── SingleGenerator_regression/
│   ├── README.md                 What each test checks, and the table of the boards
│   ├── tests/                    The test files
│   ├── Board001-default/          The six parameter files, the two boards and their .kicad_pro, Parameters.txt
│   ├── Board002-loops-4-subcoils-2/
│   └── ...
└── DualGenerator_regression/
    ├── README.md
    ├── tests/
    ├── Board001-default/          The ten Dual_..._Parameters.py files and the same five written files
    └── ...
```

Each board folder is named `BoardNNN-<what it tests>`. Its parameter files are a complete copy of the generator's own,
with the board's values, so a board can be read, copied into the generator's `Parameters` folder and run by hand.
Each suite's README has a table of its boards with the values each one sets differently from `Board001-default`.

Every board is written again from its own parameter files, and the five files that come out must equal the ones in
its folder character for character: `Stator.kicad_pcb` and `Rotor.kicad_pcb` (plain text, so KiCad opens them as they
are), their project files `Stator.kicad_pro` and `Rotor.kicad_pro` (the design rules KiCad checks them against) and
`Parameters.txt` (without the lines that change with every run: the time, the folder, the command and the verbatim
copies of the parameter files). The same boards are measured by the invariant tests, and opened by KiCad 7 to 10 in the
CI. Every other test starts from the values of `Board001-default`, so the values in a generator's own `Parameters`
folder, the ones you design with, never change a test.

A new board:

```bash
python regression/boards.py new single "spiral-tx-8-turns" TX_SHAPE=spiral TX_TURNS=8
python regression/boards.py new dual "rx2-cosine-r" RX2.RX_PROFILE=cosine_r
```

The folder gets the next free number. Each `NAME=VALUE` is written as in a parameter file; a Dual Generator name starts
with its file (`BOARD.`, `RX1.`, `TX2.`, `ROTOR1.`, `SILK.` and so on). The parameter files are copied from
`Board001-default` (or from another board with `--from`), each value is replaced where it stands, then the board is
written, its files saved, its tests run and the README table written anew. A board that does not build, or fails its
tests, is removed again.

| Command | What it does |
|---|---|
| `python regression/boards.py new ...` | Makes a new test board, as above |
| `python regression/boards.py sync` | After a generator gained or lost a parameter: copies the new name, with its value and comment, into every board folder, and removes a name the generator no longer has |
| `python regression/boards.py table` | Writes the board table of each suite's README anew |

## 30.3 What Is Tested

Each suite has the same files in its `tests` folder:

| File | Single Generator | Dual Generator |
|---|---|---|
| `test_checker.py` | One value of every kind set wrongly, missing and unknown names, inactive values left alone, the conflicts between values (vias, layers, nets, edges, fingers, rotor), the geometry that stops a run, strict mode. Each case states the return code and the lines the run must print | The 32 combinations of what the layout is given (builds or refused, with the radii it places), the layout's refusals, the names of each dual file, the values a set sets for itself, the dual rules (nets, frequencies, layers, rings), the Single Generator's own checks on each set, strict mode |
| `test_boards.py` | Every board folder written again and compared with the files saved in it (stator, rotor, their project files, record), character for character; the run's output folder must hold exactly these three files and the two [output pictures](Output-Pictures.md); every board folder must set exactly the generator's parameter names, hold nothing else and be in the README table | The same, for the dual boards |
| `test_invariants.py` | What every written board must obey: the file format, the layer table, the nets, copper inside the edges with the right widths, the clearance between nets, closed RX coils, the TX in one piece with its terminal at 0°, the rotor sectors, the record; the same values written twice are identical | The same for a dual board, each set with its own values (layers, fingers, vias, clearance): six nets, set 1 inside set 2 by the recorded gap, the TX ends at `TERMINAL_1_DEG` / `TERMINAL_2_DEG`, the two rotor rings |
| `test_silkscreen.py` | The lead-cutting silkscreen: three suggestions on both sides, via sites with room, lettering off the vias and mirrored on the bottom, the settings with their fallbacks, the font, the name placer, a board KiCad saved again, a missing KiCad reader | Six suggestions, names with the set number, breaks near each set's terminal, sides and labels options |
| `test_cli.py` | The generator started as a script in a fresh Python process, from its folder and from elsewhere, with `--check`, `--help` and a bad option | The same, plus the checker on its own and the promise that a dual run leaves no `__pycache__` in the Single Generator |
| `test_units.py` | The folder names, the OUTPUT_DIR rule, the KiCad writer, the report and colour classes, the parameter and geometry helpers, the hooks the Dual Generator builds on, and the KiCad reader of `resources/`: every reference board read as the test parser reads it, boards KiCad 7 and 10 saved again (in `tests/kicad_files/`), every via kind, the pictures of a board saved again | The set parameters handed to the Single Generator and the "set k:" findings, the layout combinations, the folder names, the Single's OUTPUT_DIR rule, a guard that the dual files supply every name the Single Generator knows, and the KiCad reader on every dual reference board |

`harness.py` loads the generator, applies the overrides, runs it, and writes each board once per run for all the tests
that need it.

The parsing and measuring code both suites share is `regression/RegressionTools.py`. It reads the written `.kicad_pcb`
back and measures it independently of the generator: the smallest clearance between nets on a cell grid, the
connectivity of each net, the copper extent of each layer, and the comparison with the saved files. It shares no code
with the reader the generators' own tools use, `resources/KiCadReader.py`, on purpose: a test in each suite holds the
two to the same values on every reference board, so each checks the other.

## 30.4 On Every Pull Request (CI)

The workflow `.github/workflows/ci.yml` runs on every pull request, after every push to `main` and every night (so a new
Python, NumPy or runner image that breaks the generators is noticed even while no one is changing them). A new push to a
pull request cancels the run still going for it.

| Check | What it runs | What it catches |
|---|---|---|
| Lint | `ruff check .` with the rules in `ruff.toml` (undefined and unused names, likely bugs, Python errors; no formatter), and actionlint on the workflow files | Mistakes in the code and in the workflows |
| Install | `requirements.txt` installed from wheels alone on Python 3.11, 3.12, 3.13, 3.14 and 3.15, on Ubuntu, Windows and macOS, then both generators' `--check` | A pin with no wheel for a supported Python, a generator that no longer starts there |
| Tests | Both suites on Python 3.15, on Ubuntu, Windows and macOS. On Ubuntu they run under coverage (line and branch), which may not drop below `.github/coverage-baseline.json` | A changed board or record on any system, code no test reaches. A failed run keeps its boards as a downloadable artifact for 14 days |
| KiCad | Every test board and a fresh default board of each generator opened by KiCad 7, 8, 9 and 10 in the official `kicad/kicad` Docker images; KiCad's DRC (8 and newer) compared with `.github/kicad-drc-baseline.json` | A board KiCad cannot open, a DRC report that appears or goes away ([KiCad Compatibility](KiCad-Compatibility.md)) |
| Repo guard | `.github/scripts/repo_guard.py`: no `__pycache__` or `.pyc`, no generated files in an `Output` folder, no file over 5 MB, no AI session links or session trailers in a file, a commit message or the pull request text | Files that never belong in git |
| Docs | `.github/scripts/check_docs.py`: every relative link and image of the Markdown files resolves, and every wiki page is in `_Sidebar.md`. `docs/tools/dual_layout_pictures.py --check`: the pictures and combination sections of [Dual Layout](Dual-Layout.md) are what the reference boards give | Broken wiki links before they reach the wiki; a Dual Layout picture that no longer shows what the generator builds |

Two more workflows check the dependencies and the code's security: `security.yml` (pip-audit on the pins, and GitHub's
dependency review on pull requests) and `codeql.yml` (GitHub's CodeQL analysis). Dependabot (`.github/dependabot.yml`)
proposes updates of NumPy, the CI tools and the actions once a week. Every action is pinned to a full commit hash and
the workflows get a read-only token.

The same checks run locally:

```bash
python -m pip install -r requirements-dev.txt
ruff check .                                   # the lint (or: pip install pre-commit; pre-commit install)
python .github/scripts/repo_guard.py           # the repo guard
python .github/scripts/check_docs.py           # the docs links
python docs/tools/dual_layout_pictures.py --check   # the Dual Layout pictures
```

When a change adds code that no test reaches, the coverage check fails: add a test, or remove the code. When a change
raises the coverage by half a point or more, the check suggests raising the number in `.github/coverage-baseline.json`
so the gain is kept. When KiCad's DRC changes on purpose, the KiCad check is run with `--update` inside the KiCad image
(the command is in `.github/scripts/kicad_check.py`) and the new baseline is committed with the change. When a board
that a Dual Layout picture is drawn from changes on purpose, run `python docs/tools/dual_layout_pictures.py` and commit
the pictures and the page section it writes.

## 30.5 When A Test Fails

When a test in `test_boards.py` fails, the generator writes something different from what it wrote when the board was
saved; the test prints the lines that differ. Read them; if the change is intended, run `--update-references` and
commit the new files with the change. The other tests do not depend on the saved files.

A change that adds a feature brings its tests with it, in the same commit:

1. A case in `test_checker.py` for every new rule and every new error or warning text (one case that triggers it, one
   that does not). A new parameter gets a case with it set and one with it missing.
2. `python regression/boards.py sync` when the change adds or removes a parameter, so every board folder has it.
3. A new test board (`python regression/boards.py new ...`) when the feature changes the copper, the rotor or the
   record, so its output is kept from then on.
4. An invariant in `test_invariants.py` when there is a rule the written files must always obey.
5. A unit test in `test_units.py` for a new helper.
6. `--update-references` last, after every printed difference has been read and found intended.

The suite cannot notice a feature that arrived without a test; that part is the review's job.

[<img align="right" src="https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2.png" alt="Sinusoidal Coil Generator logo, click to see it spin" width="72">](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2_rotor_spin_400px.webp)

| Previous | Next |
|:---|---:|
| [KiCad Compatibility](KiCad-Compatibility.md) | [Glossary](Glossary.md) |

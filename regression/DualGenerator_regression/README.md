# Dual Generator regression suite

Runs the Dual Generator the way a user does, in this process, with parameter values set in memory, and checks what
it prints and what it writes.  The generator's own parameter files, its Output folder and the Single Generator are
never touched, and nothing in the parameter files changes a test: every run starts from the values of
[Board001-default](Board001-default/).

    python regression/run_regression.py dual                 everything (about 35 minutes)
    python regression/run_regression.py dual -v              one line per test
    python regression/run_regression.py dual -k checker      only the checker cases (-k silkscreen, ...)
    python regression/run_regression.py dual --board Board007 the board tests on one board only
    python regression/run_regression.py dual --update-references
                                                             write every board's files anew from the generator

Needs what the generator needs: Python 3.11 to 3.15 and numpy (see requirements.txt).  Exit code 0 when every test
passed.  [../README.md](../README.md) explains the board folders and how to add one.

## The tests

| file | what it tests |
|---|---|
| `tests/test_checker.py` | the layout: every one of the 32 combinations of what is given (built with its radii, or refused with its message), the refusals a placed band can meet, a DUAL_MODE left in an old file; the names of each dual file, the values a set sets for itself, the dual rules (nets, frequencies, layers, rings), the Single Generator's own checks on each set, strict mode; each case says the return code and the lines the run must print |
| `tests/test_boards.py` | every board folder written again from its own parameter files and compared with the files kept in it (stator, rotor, their project files, record), character for character; every board folder complete (the generator's parameter names, the three files, nothing else) and listed below |
| `tests/test_invariants.py` | what must hold for every dual board: the file format, the layers of PCB_LAYERS, six nets, copper inside the edges on the layers each set asked for (RX, fingers, TX turns and tail), each set's via size, drill and type, the clearance between nets (each set's own), set 1 inside set 2 by the recorded gap, closed RX coils, TX terminals at TERMINAL_1_DEG / TERMINAL_2_DEG, the two rotor rings, the record with every value as used; the same values written twice are identical |
| `tests/test_silkscreen.py` | the lead-cutting silkscreen of both sets: six suggestions, names with the set number, breaks near each set's terminal, via sites with room, lettering off the vias, sides and labels options |
| `tests/test_units.py` | the set parameters handed to the Single Generator and the "set k:" findings, the layout (combination numbers, every combination built or refused, the hint for a fitted band, the wiki picture script's numbers and messages the same as the generator's), folder names, the Single's OUTPUT_DIR rule, the guard that the dual files supply every name the Single Generator knows, the KiCad reader of `resources/` on every dual reference board |
| `tests/test_cli.py` | the run script started the way a user starts it, in a fresh Python process, from its own folder and from elsewhere, with --check, --help and a bad option; the checker on its own; no `__pycache__` left in the Single Generator |
| `tests/harness.py` | loads the generator, applies overrides, runs it, writes each board once per run and shares it between the tests |

The shared plumbing is [../RegressionHarness.py](../RegressionHarness.py) and the shared parser and measuring code
[../RegressionTools.py](../RegressionTools.py) (both used by the two suites).

When a test in `test_boards.py` fails, the generator writes something different from what it wrote when the board's
files were saved.  Read the printed differences; if the change is intended, run `--update-references` and commit the
new files with the change.  The other tests do not depend on the saved files.

When a change adds a feature, it brings its tests with it, in the same commit:
  1. a case in `test_checker.py` for every new rule and every new error or warning text (one case that triggers it,
     one that does not); a new parameter gets a case with it set and one with it missing (`DELETE`),
  2. `python regression/boards.py sync` when the change adds or removes a parameter, so every board folder has it,
  3. a new board (`python regression/boards.py new dual ...`) when the feature changes the copper, the rotor or the
     record, so that its output is kept from then on,
  4. an invariant in `test_invariants.py` when there is a rule the written files must always obey,
  5. a unit test in `test_units.py` for a new helper,
  6. `--update-references` last, after every printed difference has been read and found intended.
The suite cannot notice a feature that arrived without a test: that part is the review's job.

## The boards

Each board folder holds the ten parameter files and the five files the generator wrote from them.  The
table lists what each board sets differently from Board001-default (a name starts with its file: BOARD., RX1., TX2.,
ROTOR1., SILK. and so on).

<!-- board table: written by `python regression/boards.py table`, do not edit by hand -->
| Board | Values that differ from Board001-default |
|---|---|
| [Board001-default](Board001-default/) | the generator defaults |
| [Board002-layout-32-fitted-bands](Board002-layout-32-fitted-bands/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board003-layout-10-rx1-band-and-gap](Board003-layout-10-rx1-band-and-gap/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = 9.7`<br>`RX1.OUTSIDE_RADIUS_MM = 16.05`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board004-layout-07-all-given](Board004-layout-07-all-given/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = 9.7`<br>`RX1.OUTSIDE_RADIUS_MM = 16.05`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_R_BASE_MM = 22.725`<br>`RX2.RX_A_MM = 3.175`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board005-parallel-both-sets](Board005-parallel-both-sets/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_WIRING = "parallel"`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_WIRING = "parallel"`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board006-loops-2x8-rotor-from-board](Board006-loops-2x8-rotor-from-board/) | `BOARD.ROTOR_START_ANGLE_ZERO = "board"`<br>`RX1.LOOPS = 2`<br>`RX2.LOOPS = 8`<br>`ROTOR2.ROTOR_AUTO_DUTY = 0.45` |
| [Board007-custom-rotor](Board007-custom-rotor/) | `BOARD.ROTOR_MODE = "custom"` |
| [Board008-silkscreen-bottom-no-labels](Board008-silkscreen-bottom-no-labels/) | `SILK.SILKSCREEN_SIDES = "bottom"`<br>`SILK.SILKSCREEN_LABELS = False`<br>`SILK.SILKSCREEN_DOT_ON_ALL_VIAS = True` |
| [Board009-silkscreen-off](Board009-silkscreen-off/) | `SILK.SILKSCREEN_SUGGESTION = False` |
| [Board010-blind-vias](Board010-blind-vias/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.VIA_DIAMETER_MM = 0.4`<br>`BOARD.VIA_DRILL_MM = 0.15`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.VIA_TYPE = "blind"`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board011-terminals-90-270](Board011-terminals-90-270/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.TERMINAL_1_DEG = 90.0`<br>`BOARD.TERMINAL_2_DEG = 270.0`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.LOOPS = 4`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board012-edges-30-60](Board012-edges-30-60/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 15.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 30.0`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board013-edges-90-150-loops-4x16-parallel](Board013-edges-90-150-loops-4x16-parallel/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 45.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 75.0`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.LOOPS = 4`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_WIRING = "parallel"`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_WIRING = "parallel"`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board014-vias-0-5-drill-0-25](Board014-vias-0-5-drill-0-25/) | `BOARD.VIA_DIAMETER_MM = 0.5`<br>`BOARD.VIA_DRILL_MM = 0.25` |
| [Board015-inset-offset-tail-margin](Board015-inset-offset-tail-margin/) | `BOARD.INNER_EDGE_INSET_MM = 1.5`<br>`BOARD.OUTER_EDGE_OFFSET_MM = 3.0`<br>`BOARD.OUTER_EDGE_TAIL_MARGIN_MM = 1.0`<br>`BOARD.EDGE_LINE_WIDTH_MM = 0.1` |
| [Board016-band-split-0-4](Board016-band-split-0-4/) | `BOARD.INNER_EDGE_RADIUS_MM = 7.25`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 26.875`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`BOARD.BAND_SPLIT = 0.4`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board017-band-split-0-6](Board017-band-split-0-6/) | `BOARD.INNER_EDGE_RADIUS_MM = 7.25`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 26.875`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`BOARD.BAND_SPLIT = 0.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board018-terminals-45-225](Board018-terminals-45-225/) | `BOARD.TERMINAL_1_DEG = 45.0`<br>`BOARD.TERMINAL_2_DEG = 225.0` |
| [Board019-terminals-0-0](Board019-terminals-0-0/) | `BOARD.TERMINAL_1_DEG = 0.0` |
| [Board020-frequencies-2-5-and-5-1-mhz](Board020-frequencies-2-5-and-5-1-mhz/) | `TX1.EXCITATION_FREQ_HZ = 2500000.0`<br>`TX2.EXCITATION_FREQ_HZ = 5100000.0` |
| [Board021-frequency-rules-strict](Board021-frequency-rules-strict/) | `BOARD.TX_FREQ_SEPARATION_MIN = 0.3`<br>`BOARD.TX_FREQ_RATIO_MAX_ORDER = 6`<br>`BOARD.TX_FREQ_RATIO_TOLERANCE = 0.01`<br>`TX1.EXCITATION_FREQ_HZ = 2600000.0` |
| [Board022-ic-limits-per-set](Board022-ic-limits-per-set/) | `IC1.IC_NAME = None`<br>`IC1.IC_OSC_MIN_MHZ = 1.0`<br>`IC2.IC_NAME = "OTHER_IC"`<br>`IC2.IC_OSC_MAX_MHZ = 8.0`<br>`IC2.IC_MIN_RP_OHM = 150`<br>`IC2.IC_SPLIT_TANK_CAPS = False` |
| [Board023-loops-4x12](Board023-loops-4x12/) | `RX1.LOOPS = 4`<br>`RX2.LOOPS = 12` |
| [Board024-loops-3x5](Board024-loops-3x5/) | `RX1.LOOPS = 3`<br>`RX2.LOOPS = 5` |
| [Board025-loops-2x2](Board025-loops-2x2/) | `RX1.LOOPS = 2`<br>`RX2.LOOPS = 2` |
| [Board026-rx1-cosine-r](Board026-rx1-cosine-r/) | `RX1.RX_PROFILE = "cosine_r"` |
| [Board027-rx2-cosine-r](Board027-rx2-cosine-r/) | `RX2.RX_PROFILE = "cosine_r"` |
| [Board028-rx2-subcoils-2](Board028-rx2-subcoils-2/) | `RX2.LOOPS = 4`<br>`RX2.RX_SUBCOILS = 2` |
| [Board029-rx-via-80-and-100-deg](Board029-rx-via-80-and-100-deg/) | `RX1.RX_VIA_ELECTRICAL_DEG = 80.0`<br>`RX2.RX_VIA_ELECTRICAL_DEG = 100.0` |
| [Board030-rx-steps-and-chord](Board030-rx-steps-and-chord/) | `RX1.STEPS_PER_LOOP = 256`<br>`RX2.RX_CHORD_TOLERANCE_MM = 0.005` |
| [Board031-rx-net-names](Board031-rx-net-names/) | `RX1.RX_NET_PHASE_0_2 = "A_SIN"`<br>`RX1.RX_NET_PHASE_1_3 = "A_COS"`<br>`RX2.RX_NET_PHASE_0_2 = "B_SIN"`<br>`RX2.RX_NET_PHASE_1_3 = "B_COS"`<br>`TX1.TX_NET = "A_TX"`<br>`TX2.TX_NET = "B_TX"` |
| [Board032-rx-traces-0-2](Board032-rx-traces-0-2/) | `RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2` |
| [Board033-rx2-base-amplitude](Board033-rx2-base-amplitude/) | `RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_R_BASE_MM = 20.95`<br>`RX2.RX_A_MM = 2.95` |
| [Board034-rx2-layers-3-4](Board034-rx2-layers-3-4/) | `RX2.RX_LAYER_A = 3`<br>`RX2.RX_LAYER_B = 4` |
| [Board035-rx1-layers-2-1](Board035-rx1-layers-2-1/) | `RX1.RX_LAYER_A = 2`<br>`RX1.RX_LAYER_B = 1` |
| [Board036-tx-turns-3x6](Board036-tx-turns-3x6/) | `TX1.TX_TURNS = 3`<br>`TX2.TX_TURNS = 6` |
| [Board037-tx2-turns-2-pitch-0-5](Board037-tx2-turns-2-pitch-0-5/) | `TX2.TX_TURNS = 2`<br>`TX2.TX_PITCH_MM = 0.5`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2` |
| [Board038-tx-offset-1-0](Board038-tx-offset-1-0/) | `TX1.TX_OFFSET_MM = 1.0`<br>`TX2.TX_OFFSET_MM = 1.0` |
| [Board039-tx-stepped-angle-30-60](Board039-tx-stepped-angle-30-60/) | `TX1.TX_STEPPED_ANGLE_DEG = 30`<br>`TX2.TX_STEPPED_ANGLE_DEG = 60` |
| [Board040-tx-steps-720-chord](Board040-tx-steps-720-chord/) | `TX1.TX_STEPS = 720`<br>`TX2.TX_CHORD_TOLERANCE_MM = 0.005` |
| [Board041-tx-layers-2-4](Board041-tx-layers-2-4/) | `TX1.TX_LAYER_A = 2`<br>`TX1.TX_LAYER_B = 4`<br>`TX2.TX_LAYER_A = 2`<br>`TX2.TX_LAYER_B = 4` |
| [Board042-tx2-layers-3-1](Board042-tx2-layers-3-1/) | `TX2.TX_LAYER_A = 3`<br>`TX2.TX_LAYER_B = 1` |
| [Board043-tx1-parallel-pitch-0-6](Board043-tx1-parallel-pitch-0-6/) | `TX1.TX_WIRING = "parallel"`<br>`TX1.TX_PITCH_MM = 0.6` |
| [Board044-tx2-parallel-pitch-0-6](Board044-tx2-parallel-pitch-0-6/) | `TX2.TX_WIRING = "parallel"`<br>`TX2.TX_PITCH_MM = 0.6` |
| [Board045-rotor-track-gap-and-distances](Board045-rotor-track-gap-and-distances/) | `BOARD.ROTOR_TRACK_GAP_MM = 1.5`<br>`BOARD.ROTOR_1_TO_RX2_MM = 4.0`<br>`BOARD.ROTOR_2_TO_RX1_MM = 3.0` |
| [Board046-rotor-mask-thickness-steps](Board046-rotor-mask-thickness-steps/) | `BOARD.ROTOR_PCB_THICKNESS_MM = 1.0`<br>`BOARD.ROTOR_ARC_STEPS_PER_SECTOR = 32`<br>`BOARD.ROTOR_CHORD_TOLERANCE_MM = 0.005`<br>`BOARD.ROTOR_SOLDER_MASK_EXPANSION_MM = 0.05` |
| [Board047-rotor-edge-clearance-1-0](Board047-rotor-edge-clearance-1-0/) | `BOARD.ROTOR_AUTO_EDGE_CLEARANCE_MM = 1.0` |
| [Board048-rotor-start-angle-board](Board048-rotor-start-angle-board/) | `BOARD.ROTOR_START_ANGLE_ZERO = "board"` |
| [Board049-rotor-duty-0-4-0-6-start-angles](Board049-rotor-duty-0-4-0-6-start-angles/) | `ROTOR1.ROTOR_AUTO_DUTY = 0.4`<br>`ROTOR1.ROTOR_AUTO_START_ANGLE_DEG = 20.0`<br>`ROTOR2.ROTOR_AUTO_DUTY = 0.6`<br>`ROTOR2.ROTOR_AUTO_START_ANGLE_DEG = 5.0` |
| [Board050-rotor1-covers-tx](Board050-rotor1-covers-tx/) | `ROTOR1.ROTOR_AUTO_COVER_TX = True` |
| [Board051-rotor2-no-cover](Board051-rotor2-no-cover/) | `ROTOR2.ROTOR_AUTO_COVER_TX = False`<br>`ROTOR2.ROTOR_AUTO_EXTENSION_OUTER_MM = 0.3` |
| [Board052-rotor-extensions](Board052-rotor-extensions/) | `ROTOR1.ROTOR_AUTO_EXTENSION_MM = 0.5`<br>`ROTOR1.ROTOR_AUTO_TX_CLEARANCE_MM = 0.2`<br>`ROTOR2.ROTOR_AUTO_TX_OVERHANG_MM = 0.2`<br>`ROTOR2.ROTOR_AUTO_EXTENSION_INNER_MM = 0.8` |
| [Board053-rotor-copper-layers](Board053-rotor-copper-layers/) | `ROTOR1.ROTOR_AUTO_COPPER_LAYERS = ["F.Cu", "B.Cu"]`<br>`ROTOR2.ROTOR_AUTO_COPPER_LAYERS = ["B.Cu"]` |
| [Board054-custom-rotor-sectors-2-8](Board054-custom-rotor-sectors-2-8/) | `BOARD.ROTOR_MODE = "custom"`<br>`ROTOR1.ROTOR_CUSTOM_SECTORS = 2`<br>`ROTOR1.ROTOR_CUSTOM_DUTY = 0.4`<br>`ROTOR2.ROTOR_CUSTOM_SECTORS = 8`<br>`ROTOR2.ROTOR_CUSTOM_START_ANGLE_DEG = 10.0` |
| [Board055-custom-rotor-no-outline-both-layers](Board055-custom-rotor-no-outline-both-layers/) | `BOARD.ROTOR_MODE = "custom"`<br>`BOARD.ROTOR_CUSTOM_OUTLINE_RADIUS_MM = None`<br>`BOARD.ROTOR_CUSTOM_BORE_RADIUS_MM = None`<br>`ROTOR1.ROTOR_CUSTOM_COPPER_LAYERS = ["F.Cu", "B.Cu"]` |
| [Board056-silkscreen-top](Board056-silkscreen-top/) | `SILK.SILKSCREEN_SIDES = "top"` |
| [Board057-silkscreen-style](Board057-silkscreen-style/) | `SILK.SILKSCREEN_COLOR = "#00FF00"`<br>`SILK.SILKSCREEN_LINE_WIDTH_MM = 0.2`<br>`SILK.SILKSCREEN_TEXT_SIZE_MM = 0.7`<br>`SILK.SILKSCREEN_TEXT_STROKE_MM = 0.12`<br>`SILK.SILKSCREEN_DOT_RADIUS_MM = 0.2` |
| [Board058-silkscreen-search](Board058-silkscreen-search/) | `SILK.SILKSCREEN_BOX_MARGIN_MM = 0.7`<br>`SILK.SILKSCREEN_BREAK_VIA_GAP_MM = 1.6`<br>`SILK.SILKSCREEN_SEARCH_SPAN_DEG = 40.0`<br>`SILK.SILKSCREEN_BREAK_SEPARATION_MM = 5.0` |
| [Board059-silkscreen-break-layer-in1-cu](Board059-silkscreen-break-layer-in1-cu/) | `SILK.SILKSCREEN_BREAK_LAYERS = ["In1.Cu"]`<br>`SILK.SILKSCREEN_VIA_EDGE_CLEARANCE_MM = 0.35`<br>`SILK.SILKSCREEN_TX_SITE_REACH_MM = 2.5` |
| [Board060-copper-70um-e24-conductivity](Board060-copper-70um-e24-conductivity/) | `BOARD.COPPER_THICKNESS_UM = 70`<br>`BOARD.COPPER_CONDUCTIVITY_S_M = 50000000.0`<br>`BOARD.TX_AC_RESISTANCE_FACTOR = 3.0`<br>`BOARD.TANK_CAP_SERIES = "E24"` |
| [Board061-strict-mode](Board061-strict-mode/) | `BOARD.GENERATOR_MODE = "strict"` |
| [Board062-centre-120-90-air-gap-prepreg](Board062-centre-120-90-air-gap-prepreg/) | `BOARD.CENTER_X_MM = 120.0`<br>`BOARD.CENTER_Y_MM = 90.0`<br>`BOARD.AIR_GAP_MM = 0.5`<br>`BOARD.STACKUP_PREPREG_MM = 0.3` |
| [Board063-rx-via-80-100-layout-tolerance-0-1](Board063-rx-via-80-100-layout-tolerance-0-1/) | `BOARD.LAYOUT_TOLERANCE_MM = 0.1`<br>`RX1.RX_VIA_ELECTRICAL_DEG = 80.0`<br>`RX2.RX_VIA_ELECTRICAL_DEG = 100.0` |
| [Board064-ic1-limits-ic2-osc-min](Board064-ic1-limits-ic2-osc-min/) | `IC1.IC_OSC_MAX_MHZ = 6.0`<br>`IC1.IC_MIN_RP_OHM = 200`<br>`IC1.IC_SPLIT_TANK_CAPS = False`<br>`IC2.IC_OSC_MIN_MHZ = 1.5` |
| [Board065-rx1-base-amplitude](Board065-rx1-base-amplitude/) | `RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_R_BASE_MM = 10.075`<br>`RX1.RX_A_MM = 1.625` |
| [Board066-chords-and-steps-other-set](Board066-chords-and-steps-other-set/) | `RX1.RX_CHORD_TOLERANCE_MM = 0.005`<br>`RX2.STEPS_PER_LOOP = 64`<br>`TX1.TX_CHORD_TOLERANCE_MM = 0.005`<br>`TX2.TX_STEPS = 720` |
| [Board067-rotor1-covers-tx-overhang-0-2](Board067-rotor1-covers-tx-overhang-0-2/) | `ROTOR1.ROTOR_AUTO_COVER_TX = True`<br>`ROTOR1.ROTOR_AUTO_TX_OVERHANG_MM = 0.2` |
| [Board068-rotor-extensions-tx-clearance](Board068-rotor-extensions-tx-clearance/) | `ROTOR1.ROTOR_AUTO_EXTENSION_INNER_MM = 0.3`<br>`ROTOR1.ROTOR_AUTO_EXTENSION_OUTER_MM = 0.2`<br>`ROTOR2.ROTOR_AUTO_COVER_TX = False`<br>`ROTOR2.ROTOR_AUTO_EXTENSION_MM = 0.3`<br>`ROTOR2.ROTOR_AUTO_TX_CLEARANCE_MM = 0.2` |
| [Board069-custom-rotor-radii-start-duty-layers](Board069-custom-rotor-radii-start-duty-layers/) | `BOARD.ROTOR_MODE = "custom"`<br>`ROTOR1.ROTOR_CUSTOM_START_ANGLE_DEG = 15.0`<br>`ROTOR1.ROTOR_CUSTOM_INNER_RADIUS_MM = 7.9`<br>`ROTOR1.ROTOR_CUSTOM_OUTER_RADIUS_MM = 12.0`<br>`ROTOR2.ROTOR_CUSTOM_DUTY = 0.4`<br>`ROTOR2.ROTOR_CUSTOM_INNER_RADIUS_MM = 17.6`<br>`ROTOR2.ROTOR_CUSTOM_OUTER_RADIUS_MM = 26.0`<br>`ROTOR2.ROTOR_CUSTOM_COPPER_LAYERS = ["B.Cu"]` |
| [Board070-two-layer-board](Board070-two-layer-board/) | `BOARD.PCB_LAYERS = 2`<br>`RX2.RX_RISING_EDGE_LAYER = "B.Cu"`<br>`TX1.TX_LAYER_B = 4`<br>`TX2.TX_LAYER_B = 4`<br>`SILK.SILKSCREEN_BREAK_LAYERS = ["F.Cu", "B.Cu"]` |
| [Board071-fingers-set1-all](Board071-fingers-set1-all/) | `RX1.RX_TABS = "all"` |
| [Board072-fingers-set2-single-length-width](Board072-fingers-set2-single-length-width/) | `RX2.RX_TABS = "single"`<br>`RX2.RX_TAB_LENGTH_MM = 2.5`<br>`RX2.RX_TAB_WIDTH_MM = 0.8` |
| [Board073-fingers-set1-tx-goes-around](Board073-fingers-set1-tx-goes-around/) | `RX1.RX_TABS = "all"`<br>`RX1.RX_TAB_LAYER = 1`<br>`RX1.RX_TAB_LENGTH_MM = 4.2` |
| [Board074-fingers-set2-parallel-stitched](Board074-fingers-set2-parallel-stitched/) | `RX2.RX_TABS = "single"`<br>`RX2.RX_TAB_LAYER = 1`<br>`RX2.RX_TAB_LENGTH_MM = 3.2`<br>`TX2.TX_WIRING = "parallel"`<br>`TX2.TX_PITCH_MM = 0.6` |
| [Board075-fingers-set1-parallel-staggered](Board075-fingers-set1-parallel-staggered/) | `RX1.RX_TABS = "all"`<br>`RX1.RX_TAB_LAYER = 1`<br>`RX1.RX_TAB_LENGTH_MM = 5.4`<br>`TX1.TX_WIRING = "parallel"`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_PARALLEL_BREAK_STYLE = "staggered"` |
| [Board076-spiral-tx-both-tx2-tail](Board076-spiral-tx-both-tx2-tail/) | `TX1.TX_SHAPE = "spiral"`<br>`TX2.TX_SHAPE = "spiral"`<br>`TX2.TX_TAIL_EXTRA_MM = 1.0` |
| [Board077-stepped-arc-tx1-tail](Board077-stepped-arc-tx1-tail/) | `TX1.TX_SHAPE = "stepped_arc"`<br>`TX1.TX_TAIL_EXTRA_MM = 1.5` |
| [Board078-single-layer-tx-both-underpass-4](Board078-single-layer-tx-both-underpass-4/) | `TX1.TX_WIRING = "single"`<br>`TX2.TX_WIRING = "single"`<br>`TX2.TX_LAYER_A = 3`<br>`TX2.TX_SERIES_UNDERPASS_LAYER = 4` |
| [Board079-vias-per-set-blind-set1](Board079-vias-per-set-blind-set1/) | `RX1.VIA_DIAMETER_MM = 0.4`<br>`RX1.VIA_DRILL_MM = 0.15`<br>`RX1.VIA_TYPE = "blind"`<br>`RX2.VIA_DIAMETER_MM = 0.7`<br>`RX2.VIA_DRILL_MM = 0.35`<br>`TX1.TX_LAYER_B = 2`<br>`TX2.TX_PITCH_MM = 0.4` |
| [Board080-clearance-set2-0-25](Board080-clearance-set2-0-25/) | `RX2.MIN_CLEARANCE_MM = 0.25`<br>`TX2.TX_OFFSET_MM = 0.9`<br>`TX2.TX_PITCH_MM = 0.45` |
| [Board081-tank-caps-ac-factor-per-set](Board081-tank-caps-ac-factor-per-set/) | `TX1.TX_AC_RESISTANCE_FACTOR = 3.0`<br>`IC2.TANK_CAP_SERIES = "E24"` |
| [Board082-fitted-bands-fingers-both-sets](Board082-fitted-bands-fingers-both-sets/) | `BOARD.PAGE_SIZE_MM = (200, 200)`<br>`BOARD.MIN_CLEARANCE_MM = 0.2`<br>`BOARD.INNER_EDGE_RADIUS_MM = 8.5`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 29.5`<br>`BOARD.TRACK_GAP_MM = 0.5`<br>`BOARD.PCB_THICKNESS_MM = 1.6`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX1.RX_TRACE_WIDTH_MM = 0.2`<br>`RX1.RX_TABS = "all"`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None`<br>`RX2.RX_TRACE_WIDTH_MM = 0.2`<br>`RX2.RX_TABS = "all"`<br>`TX1.TX_TURNS = 3`<br>`TX1.TX_PITCH_MM = 0.6`<br>`TX1.TX_TRACE_WIDTH_MM = 0.2`<br>`TX1.TX_INSIDE_VIA_DISTANCE_MM = 0.1`<br>`TX2.TX_TURNS = 3`<br>`TX2.TX_OFFSET_MM = 1.1`<br>`TX2.TX_PITCH_MM = 0.6`<br>`TX2.TX_TRACE_WIDTH_MM = 0.2`<br>`TX2.TX_INSIDE_VIA_DISTANCE_MM = 0.3` |
| [Board083-layout-02-both-bands-and-gap](Board083-layout-02-both-bands-and-gap/) | `BOARD.TRACK_GAP_MM = 3.0` |
| [Board084-layout-03-both-bands-and-bore](Board084-layout-03-both-bands-and-bore/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0` |
| [Board085-layout-04-both-bands-bore-and-gap](Board085-layout-04-both-bands-bore-and-gap/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.TRACK_GAP_MM = 3.0` |
| [Board086-layout-05-both-bands-and-outline](Board086-layout-05-both-bands-and-outline/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0` |
| [Board087-layout-06-both-bands-outline-and-gap](Board087-layout-06-both-bands-outline-and-gap/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 3.0` |
| [Board088-layout-08-everything-given](Board088-layout-08-everything-given/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 3.0` |
| [Board089-layout-09-rx1-band](Board089-layout-09-rx1-band/) | `RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board090-layout-11-rx1-band-and-bore](Board090-layout-11-rx1-band-and-bore/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board091-layout-12-rx1-band-bore-and-gap](Board091-layout-12-rx1-band-bore-and-gap/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board092-layout-13-rx1-band-and-outline](Board092-layout-13-rx1-band-and-outline/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board093-layout-14-rx1-band-outline-and-gap](Board093-layout-14-rx1-band-outline-and-gap/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board094-layout-15-rx1-band-bore-and-outline](Board094-layout-15-rx1-band-bore-and-outline/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board095-layout-16-rx1-band-bore-outline-and-gap](Board095-layout-16-rx1-band-bore-outline-and-gap/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
| [Board096-layout-17-rx2-band](Board096-layout-17-rx2-band/) | `RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board097-layout-18-rx2-band-and-gap](Board097-layout-18-rx2-band-and-gap/) | `BOARD.TRACK_GAP_MM = 1.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board098-layout-19-rx2-band-and-bore](Board098-layout-19-rx2-band-and-bore/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board099-layout-20-rx2-band-bore-and-gap](Board099-layout-20-rx2-band-bore-and-gap/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board100-layout-21-rx2-band-and-outline](Board100-layout-21-rx2-band-and-outline/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board101-layout-22-rx2-band-outline-and-gap](Board101-layout-22-rx2-band-outline-and-gap/) | `BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board102-layout-23-rx2-band-bore-and-outline](Board102-layout-23-rx2-band-bore-and-outline/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board103-layout-24-rx2-band-bore-outline-and-gap](Board103-layout-24-rx2-band-bore-outline-and-gap/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`BOARD.TRACK_GAP_MM = 1.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None` |
| [Board104-layout-31-both-edges](Board104-layout-31-both-edges/) | `BOARD.INNER_EDGE_RADIUS_MM = 6.0`<br>`BOARD.OUTER_EDGE_RADIUS_MM = 28.0`<br>`RX1.INSIDE_RADIUS_MM = None`<br>`RX1.OUTSIDE_RADIUS_MM = None`<br>`RX2.INSIDE_RADIUS_MM = None`<br>`RX2.OUTSIDE_RADIUS_MM = None` |
<!-- end of board table -->

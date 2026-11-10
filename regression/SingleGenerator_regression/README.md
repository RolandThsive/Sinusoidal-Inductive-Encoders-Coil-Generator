# Single Generator regression suite

Runs the Single Generator the way a user does, in this process, with parameter values set in memory, and checks what
it prints and what it writes.  The generator's own parameter files and its Output folder are never touched, and
nothing in them changes a test: every run starts from the values of [Board001-default](Board001-default/).

    python regression/run_regression.py single                 everything (about 7 minutes)
    python regression/run_regression.py single -v              one line per test
    python regression/run_regression.py single -k checker      only the checker cases (-k silkscreen, ...)
    python regression/run_regression.py single --board Board007 the board tests on one board only
    python regression/run_regression.py single --update-references
                                                               write every board's files anew from the generator

Needs what the generator needs: Python 3.11 to 3.15 and numpy (see requirements.txt).  Exit code 0 when every test
passed.  [../README.md](../README.md) explains the board folders and how to add one.

## The tests

| file | what it tests |
|---|---|
| `tests/test_checker.py` | one value of every kind set wrongly, missing and unknown names, inactive values left alone, the conflicts between values (vias, layers, nets, edges, fingers, rotor), the geometry that stops a run, strict mode; each case says the return code and the lines the run must print |
| `tests/test_boards.py` | every board folder written again from its own parameter files and compared with the files kept in it (stator, rotor, their project files, record), character for character; every board folder complete (the generator's parameter names, the three files, nothing else) and listed below |
| `tests/test_invariants.py` | what must hold for every board: the file format, the layer table, the nets, copper inside the edges with the right widths, the clearance between nets, closed RX coils, the TX in one piece with its terminal at 0 deg, the rotor sectors (count, angle, radii, mask, edges), the record with every value as used; the same values written twice are identical; --stator and --rotor |
| `tests/test_silkscreen.py` | the lead-cutting silkscreen: three suggestions on both sides, via sites with room, lettering off the vias and mirrored on the bottom, the settings with their fallbacks, the font, the name placer, a board KiCad saved again, a missing KiCad reader |
| `tests/test_units.py` | the folder names, the OUTPUT_DIR rule, the KiCad writer, the report and colour classes, the parameter helpers, the geometry helpers (checked against the suite's own), and the hooks the Dual Generator builds on (a stator turned to any terminal angle, its copper on a shared board, the rotor's start offset), and the shared files of `resources/`: the picture makers, and the KiCad reader (every reference board read as the test parser reads it, Board047 as KiCad 7 and KiCad 10 saved it again, a board with one via of each kind; the files are in `tests/kicad_files/`) |
| `tests/test_cli.py` | the run script started the way a user starts it, in a fresh Python process, from its own folder and from elsewhere, with --check, --help and a bad option (the in-process tests cannot see the script's own import-path setup) |
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
  3. a new board (`python regression/boards.py new single ...`) when the feature changes the copper, the rotor or
     the record, so that its output is kept from then on,
  4. an invariant in `test_invariants.py` when there is a rule the written files must always obey,
  5. a unit test in `test_units.py` for a new helper,
  6. `--update-references` last, after every printed difference has been read and found intended.
The suite cannot notice a feature that arrived without a test: that part is the review's job.

## The boards

Each board folder holds the six parameter files and the five files the generator wrote from them.  The table
lists what each board sets differently from Board001-default.

<!-- board table: written by `python regression/boards.py table`, do not edit by hand -->
| Board | Values that differ from Board001-default |
|---|---|
| [Board001-default](Board001-default/) | the generator defaults |
| [Board002-loops-4-subcoils-2](Board002-loops-4-subcoils-2/) | `VIA_DIAMETER_MM = 0.6`<br>`VIA_DRILL_MM = 0.3`<br>`LOOPS = 4`<br>`RX_SUBCOILS = 2`<br>`RX_TABS = "none"` |
| [Board003-loops-16-tabs-single](Board003-loops-16-tabs-single/) | `LOOPS = 16`<br>`RX_TABS = "single"` |
| [Board004-four-layer-series](Board004-four-layer-series/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`RX_TABS = "none"`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board005-four-layer-parallel-staggered](Board005-four-layer-parallel-staggered/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_WIRING = "parallel"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4`<br>`TX_PARALLEL_BREAK_STYLE = "staggered"` |
| [Board006-series-two-layers-no-fingers](Board006-series-two-layers-no-fingers/) | `RX_TABS = "none"`<br>`TX_WIRING = "series"` |
| [Board007-spiral-tx](Board007-spiral-tx/) | `OUTER_EDGE_RADIUS_MM = None`<br>`RX_TABS = "none"`<br>`TX_TURNS = 5`<br>`TX_SHAPE = "spiral"` |
| [Board008-stepped-arc-tx](Board008-stepped-arc-tx/) | `TX_TURNS = 2`<br>`TX_SHAPE = "stepped_arc"` |
| [Board009-cosine-r-loops-4](Board009-cosine-r-loops-4/) | `LOOPS = 4`<br>`RX_PROFILE = "cosine_r"`<br>`STEPS_PER_LOOP = 64` |
| [Board010-band-from-centre](Board010-band-from-centre/) | `INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None`<br>`RX_R_BASE_MM = 18.8`<br>`RX_A_MM = 2.6` |
| [Board011-custom-rotor-no-cover](Board011-custom-rotor-no-cover/) | `ROTOR_MODE = "custom"`<br>`ROTOR_AUTO_COVER_TX = False`<br>`ROTOR_SOLDER_MASK_EXPANSION_MM = 0.1` |
| [Board012-rotor-two-layers-mask-open](Board012-rotor-two-layers-mask-open/) | `ROTOR_AUTO_DUTY = 0.4`<br>`ROTOR_AUTO_COPPER_LAYERS = ["F.Cu", "B.Cu"]`<br>`ROTOR_PCB_THICKNESS_MM = 0.8`<br>`ROTOR_SOLDER_MASK_EXPANSION_MM = 0.0` |
| [Board013-silkscreen-top-dots-on-all](Board013-silkscreen-top-dots-on-all/) | `SILK.SILKSCREEN_SIDES = "top"`<br>`SILK.SILKSCREEN_COLOR = "#FFCC00"`<br>`SILK.SILKSCREEN_DOT_ON_ALL_VIAS = True` |
| [Board014-silkscreen-off](Board014-silkscreen-off/) | `SILK.SILKSCREEN_SUGGESTION = False` |
| [Board015-four-layer-blind-vias](Board015-four-layer-blind-vias/) | `PCB_LAYERS = 4`<br>`VIA_DIAMETER_MM = 0.4`<br>`VIA_DRILL_MM = 0.15`<br>`VIA_TYPE = "blind"`<br>`RX_LAYER_A = 3`<br>`RX_LAYER_B = 4`<br>`RX_TABS = "none"`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 2` |
| [Board016-four-layer-blind-parallel-fingers](Board016-four-layer-blind-parallel-fingers/) | `PCB_LAYERS = 4`<br>`VIA_DIAMETER_MM = 0.4`<br>`VIA_DRILL_MM = 0.15`<br>`VIA_TYPE = "blind"`<br>`TX_WIRING = "parallel"`<br>`TX_LAYER_A = 3`<br>`TX_LAYER_B = 4` |
| [Board017-edges-20-40-loops-4](Board017-edges-20-40-loops-4/) | `INNER_EDGE_RADIUS_MM = 10.0`<br>`OUTER_EDGE_RADIUS_MM = 20.0`<br>`LOOPS = 4`<br>`INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None` |
| [Board018-edges-90-150-loops-8-subcoils-2](Board018-edges-90-150-loops-8-subcoils-2/) | `INNER_EDGE_RADIUS_MM = 45.0`<br>`OUTER_EDGE_RADIUS_MM = 75.0`<br>`LOOPS = 8`<br>`INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None`<br>`RX_SUBCOILS = 2` |
| [Board019-strict-mode](Board019-strict-mode/) | `GENERATOR_MODE = "strict"` |
| [Board020-tank-caps-e6](Board020-tank-caps-e6/) | `TANK_CAP_SERIES = "E6"` |
| [Board021-tank-caps-e24-copper-70um](Board021-tank-caps-e24-copper-70um/) | `COPPER_THICKNESS_UM = 70`<br>`TX_AC_RESISTANCE_FACTOR = 3.0`<br>`TANK_CAP_SERIES = "E24"` |
| [Board022-excitation-2-5mhz-conductivity](Board022-excitation-2-5mhz-conductivity/) | `EXCITATION_FREQ_HZ = 2500000.0`<br>`COPPER_CONDUCTIVITY_S_M = 50000000.0` |
| [Board023-ic-unnamed-wide-limits-one-tank-cap](Board023-ic-unnamed-wide-limits-one-tank-cap/) | `IC_NAME = None`<br>`IC_OSC_MIN_MHZ = 1.0`<br>`IC_OSC_MAX_MHZ = 8.0`<br>`IC_MIN_RP_OHM = 150`<br>`IC_SPLIT_TANK_CAPS = False` |
| [Board024-page-300x250-centre-150-120](Board024-page-300x250-centre-150-120/) | `CENTER_X_MM = 150.0`<br>`CENTER_Y_MM = 120.0`<br>`PAGE_SIZE_MM = (300, 250)` |
| [Board025-page-grown-for-big-board](Board025-page-grown-for-big-board/) | `PAGE_SIZE_MM = (100, 100)`<br>`INNER_EDGE_RADIUS_MM = 40.0`<br>`OUTER_EDGE_RADIUS_MM = 60.0`<br>`INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None` |
| [Board026-vias-0-6-drill-0-3](Board026-vias-0-6-drill-0-3/) | `VIA_DIAMETER_MM = 0.6`<br>`VIA_DRILL_MM = 0.3` |
| [Board027-clearance-0-15-traces-0-15](Board027-clearance-0-15-traces-0-15/) | `MIN_CLEARANCE_MM = 0.15`<br>`RX_TRACE_WIDTH_MM = 0.15`<br>`TX_PITCH_MM = 0.45`<br>`TX_TRACE_WIDTH_MM = 0.15` |
| [Board028-thin-board-air-gap-0-5](Board028-thin-board-air-gap-0-5/) | `EDGE_LINE_WIDTH_MM = 0.1`<br>`AIR_GAP_MM = 0.5`<br>`PCB_THICKNESS_MM = 0.8` |
| [Board029-edges-from-band-inset-offset](Board029-edges-from-band-inset-offset/) | `INNER_EDGE_INSET_MM = 2.0`<br>`INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_OFFSET_MM = 5.0`<br>`OUTER_EDGE_RADIUS_MM = None` |
| [Board030-outer-edge-tail-margin-1-5](Board030-outer-edge-tail-margin-1-5/) | `OUTER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_TAIL_MARGIN_MM = 1.5` |
| [Board031-loops-2](Board031-loops-2/) | `LOOPS = 2` |
| [Board032-loops-3](Board032-loops-3/) | `LOOPS = 3` |
| [Board033-loops-5-tabs-single](Board033-loops-5-tabs-single/) | `LOOPS = 5`<br>`RX_TABS = "single"` |
| [Board034-loops-8-tabs-all](Board034-loops-8-tabs-all/) | `LOOPS = 8` |
| [Board035-loops-12-tabs-none](Board035-loops-12-tabs-none/) | `LOOPS = 12`<br>`RX_TABS = "none"` |
| [Board036-subcoils-2-loops-1-small-vias](Board036-subcoils-2-loops-1-small-vias/) | `VIA_DIAMETER_MM = 0.5`<br>`VIA_DRILL_MM = 0.25`<br>`RX_SUBCOILS = 2` |
| [Board037-subcoils-3-wide-band-small-vias](Board037-subcoils-3-wide-band-small-vias/) | `VIA_DIAMETER_MM = 0.5`<br>`VIA_DRILL_MM = 0.25`<br>`INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`INSIDE_RADIUS_MM = 12.0`<br>`OUTSIDE_RADIUS_MM = 24.0`<br>`RX_SUBCOILS = 3`<br>`RX_SUBCOIL_SPLIT_ELEC_DEG = 30.0`<br>`RX_TABS = "none"` |
| [Board038-subcoils-3-loops-4-band-30-42](Board038-subcoils-3-loops-4-band-30-42/) | `VIA_DIAMETER_MM = 0.5`<br>`VIA_DRILL_MM = 0.25`<br>`INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`LOOPS = 4`<br>`INSIDE_RADIUS_MM = 30.0`<br>`OUTSIDE_RADIUS_MM = 42.0`<br>`RX_SUBCOILS = 3`<br>`RX_SUBCOIL_SPLIT_ELEC_DEG = 30.0`<br>`RX_TABS = "none"` |
| [Board039-cosine-r-loops-8-subcoils-2-edges-90-150](Board039-cosine-r-loops-8-subcoils-2-edges-90-150/) | `INNER_EDGE_RADIUS_MM = 45.0`<br>`OUTER_EDGE_RADIUS_MM = 75.0`<br>`LOOPS = 8`<br>`INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None`<br>`RX_PROFILE = "cosine_r"`<br>`RX_SUBCOILS = 2`<br>`RX_TABS = "none"` |
| [Board040-cosine-r-loops-1](Board040-cosine-r-loops-1/) | `RX_PROFILE = "cosine_r"` |
| [Board041-tab-layer-1](Board041-tab-layer-1/) | `RX_TAB_LAYER = 1` |
| [Board042-tab-length-3-5-width-1-5](Board042-tab-length-3-5-width-1-5/) | `OUTER_EDGE_RADIUS_MM = None`<br>`RX_TAB_LENGTH_MM = 3.5`<br>`RX_TAB_WIDTH_MM = 1.5` |
| [Board043-rising-edge-b-cu](Board043-rising-edge-b-cu/) | `RX_RISING_EDGE_LAYER = "B.Cu"` |
| [Board044-rx-via-60-deg](Board044-rx-via-60-deg/) | `RX_VIA_ELECTRICAL_DEG = 60.0` |
| [Board045-rx-via-120-deg-loops-4](Board045-rx-via-120-deg-loops-4/) | `LOOPS = 4`<br>`RX_VIA_ELECTRICAL_DEG = 120.0` |
| [Board046-steps-per-loop-128-chord-0-005](Board046-steps-per-loop-128-chord-0-005/) | `STEPS_PER_LOOP = 128`<br>`RX_CHORD_TOLERANCE_MM = 0.005` |
| [Board047-chord-tolerance-0-01-auto-steps](Board047-chord-tolerance-0-01-auto-steps/) | `RX_CHORD_TOLERANCE_MM = 0.01`<br>`TX_CHORD_TOLERANCE_MM = 0.01` |
| [Board048-net-names-sin-cos-exc](Board048-net-names-sin-cos-exc/) | `RX_NET_PHASE_0_2 = "SIN"`<br>`RX_NET_PHASE_1_3 = "COS"`<br>`TX_NET = "EXC"` |
| [Board049-wide-band-12-24-edges-free](Board049-wide-band-12-24-edges-free/) | `INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`INSIDE_RADIUS_MM = 12.0`<br>`OUTSIDE_RADIUS_MM = 24.0` |
| [Board050-band-base-amplitude-edges-fixed](Board050-band-base-amplitude-edges-fixed/) | `INSIDE_RADIUS_MM = None`<br>`OUTSIDE_RADIUS_MM = None`<br>`RX_R_BASE_MM = 18.5`<br>`RX_A_MM = 2.3` |
| [Board051-four-layer-rx-1-2-tx-3-4-parallel](Board051-four-layer-rx-1-2-tx-3-4-parallel/) | `PCB_LAYERS = 4`<br>`TX_WIRING = "parallel"`<br>`TX_LAYER_A = 3`<br>`TX_LAYER_B = 4` |
| [Board052-four-layer-rx-1-4-tx-2-3-series](Board052-four-layer-rx-1-4-tx-2-3-series/) | `PCB_LAYERS = 4`<br>`RX_LAYER_B = 4`<br>`RX_TABS = "none"`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 2`<br>`TX_LAYER_B = 3` |
| [Board053-four-layer-tx-inner-2-3-parallel](Board053-four-layer-tx-inner-2-3-parallel/) | `PCB_LAYERS = 4`<br>`RX_LAYER_B = 4`<br>`RX_TABS = "none"`<br>`TX_WIRING = "parallel"`<br>`TX_LAYER_A = 2`<br>`TX_LAYER_B = 3` |
| [Board054-four-layer-tab-layer-3](Board054-four-layer-tab-layer-3/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`RX_TAB_LAYER = 3`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board055-four-layer-single-tx-layer-1](Board055-four-layer-single-tx-layer-1/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board056-four-layer-prepreg-0-3](Board056-four-layer-prepreg-0-3/) | `PCB_LAYERS = 4`<br>`STACKUP_PREPREG_MM = 0.3`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board057-four-layer-blind-series-loops-4](Board057-four-layer-blind-series-loops-4/) | `PCB_LAYERS = 4`<br>`VIA_DIAMETER_MM = 0.4`<br>`VIA_DRILL_MM = 0.15`<br>`VIA_TYPE = "blind"`<br>`LOOPS = 4`<br>`RX_LAYER_A = 3`<br>`RX_LAYER_B = 4`<br>`RX_TABS = "none"`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 2` |
| [Board058-four-layer-cosine-r-loops-2](Board058-four-layer-cosine-r-loops-2/) | `PCB_LAYERS = 4`<br>`LOOPS = 2`<br>`RX_PROFILE = "cosine_r"`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board059-arc-tx-series](Board059-arc-tx-series/) | `RX_TABS = "none"`<br>`TX_SHAPE = "stepped_arc"`<br>`TX_WIRING = "series"` |
| [Board060-arc-tx-parallel](Board060-arc-tx-parallel/) | `TX_SHAPE = "stepped_arc"`<br>`TX_WIRING = "parallel"` |
| [Board061-arc-tx-radius-1-0](Board061-arc-tx-radius-1-0/) | `TX_SHAPE = "stepped_arc"`<br>`TX_STEPPED_ARC_RADIUS_MM = 1.0` |
| [Board062-arc-tx-four-layer-parallel-staggered](Board062-arc-tx-four-layer-parallel-staggered/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_SHAPE = "stepped_arc"`<br>`TX_WIRING = "parallel"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4`<br>`TX_PARALLEL_BREAK_STYLE = "staggered"` |
| [Board063-spiral-tx-series](Board063-spiral-tx-series/) | `OUTER_EDGE_RADIUS_MM = None`<br>`RX_TABS = "none"`<br>`TX_SHAPE = "spiral"`<br>`TX_WIRING = "series"` |
| [Board064-spiral-tx-parallel-long-tabs](Board064-spiral-tx-parallel-long-tabs/) | `OUTER_EDGE_RADIUS_MM = None`<br>`RX_TAB_LENGTH_MM = 5.0`<br>`TX_SHAPE = "spiral"`<br>`TX_WIRING = "parallel"` |
| [Board065-spiral-tx-four-layer-series](Board065-spiral-tx-four-layer-series/) | `PCB_LAYERS = 4`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`RX_TABS = "none"`<br>`TX_SHAPE = "spiral"`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
| [Board066-diagonal-tx-parallel-two-layers](Board066-diagonal-tx-parallel-two-layers/) | `TX_WIRING = "parallel"` |
| [Board067-diagonal-tx-parallel-staggered](Board067-diagonal-tx-parallel-staggered/) | `RX_TABS = "none"`<br>`TX_WIRING = "parallel"`<br>`TX_PARALLEL_BREAK_STYLE = "staggered"` |
| [Board068-parallel-tab-layer-1](Board068-parallel-tab-layer-1/) | `RX_TAB_LAYER = 1`<br>`TX_WIRING = "parallel"` |
| [Board069-tx-turns-1](Board069-tx-turns-1/) | `TX_TURNS = 1` |
| [Board070-tx-turns-6-long-tabs](Board070-tx-turns-6-long-tabs/) | `INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`RX_TAB_LENGTH_MM = 5.0`<br>`TX_TURNS = 6` |
| [Board071-tx-turns-10-spiral](Board071-tx-turns-10-spiral/) | `INNER_EDGE_RADIUS_MM = None`<br>`OUTER_EDGE_RADIUS_MM = None`<br>`RX_TABS = "none"`<br>`TX_TURNS = 10`<br>`TX_SHAPE = "spiral"` |
| [Board072-stepped-angle-30](Board072-stepped-angle-30/) | `TX_STEPPED_ANGLE_DEG = 30` |
| [Board073-stepped-angle-90](Board073-stepped-angle-90/) | `TX_STEPPED_ANGLE_DEG = 90` |
| [Board074-inside-via-distance-0](Board074-inside-via-distance-0/) | `TX_INSIDE_VIA_DISTANCE_MM = 0.0` |
| [Board075-tx-steps-720](Board075-tx-steps-720/) | `TX_STEPS = 720` |
| [Board076-tx-tail-0](Board076-tx-tail-0/) | `TX_TAIL_EXTRA_MM = 0.0` |
| [Board077-tx-tail-4-edges-free](Board077-tx-tail-4-edges-free/) | `OUTER_EDGE_RADIUS_MM = None`<br>`TX_TAIL_EXTRA_MM = 4.0` |
| [Board078-tx-offset-1-5-pitch-0-8](Board078-tx-offset-1-5-pitch-0-8/) | `OUTER_EDGE_RADIUS_MM = None`<br>`RX_TAB_LENGTH_MM = 4.0`<br>`TX_OFFSET_MM = 1.5`<br>`TX_PITCH_MM = 0.8` |
| [Board079-tx-on-top-layer](Board079-tx-on-top-layer/) | `TX_LAYER_A = 1` |
| [Board080-underpass-layer-1-two-layer](Board080-underpass-layer-1-two-layer/) | `TX_SERIES_UNDERPASS_LAYER = 1` |
| [Board081-underpass-layer-2-four-layer-series](Board081-underpass-layer-2-four-layer-series/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4`<br>`TX_SERIES_UNDERPASS_LAYER = 2` |
| [Board082-underpass-layer-3-four-layer-single](Board082-underpass-layer-3-four-layer-single/) | `PCB_LAYERS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4`<br>`TX_SERIES_UNDERPASS_LAYER = 3` |
| [Board083-rotor-duty-0-7-loops-4](Board083-rotor-duty-0-7-loops-4/) | `LOOPS = 4`<br>`ROTOR_AUTO_DUTY = 0.7` |
| [Board084-rotor-start-15-deg](Board084-rotor-start-15-deg/) | `ROTOR_AUTO_START_ANGLE_DEG = 15.0` |
| [Board085-rotor-overhang-minus-0-2](Board085-rotor-overhang-minus-0-2/) | `ROTOR_AUTO_TX_OVERHANG_MM = -0.2` |
| [Board086-rotor-overhang-1-0](Board086-rotor-overhang-1-0/) | `ROTOR_AUTO_TX_OVERHANG_MM = 1.0` |
| [Board087-rotor-extension-0-5](Board087-rotor-extension-0-5/) | `ROTOR_AUTO_EXTENSION_MM = 0.5` |
| [Board088-rotor-no-cover-extensions-inner-outer](Board088-rotor-no-cover-extensions-inner-outer/) | `ROTOR_AUTO_COVER_TX = False`<br>`ROTOR_AUTO_EXTENSION_INNER_MM = 0.3`<br>`ROTOR_AUTO_EXTENSION_OUTER_MM = 0.8` |
| [Board089-rotor-no-cover-tx-clearance-0-3](Board089-rotor-no-cover-tx-clearance-0-3/) | `ROTOR_AUTO_COVER_TX = False`<br>`ROTOR_AUTO_TX_CLEARANCE_MM = 0.3` |
| [Board090-rotor-edge-clearance-1-0](Board090-rotor-edge-clearance-1-0/) | `ROTOR_AUTO_EDGE_CLEARANCE_MM = 1.0` |
| [Board091-rotor-arc-steps-32-chord-0-005](Board091-rotor-arc-steps-32-chord-0-005/) | `ROTOR_ARC_STEPS_PER_SECTOR = 32`<br>`ROTOR_CHORD_TOLERANCE_MM = 0.005` |
| [Board092-rotor-mask-open-0-05-thickness-1-0](Board092-rotor-mask-open-0-05-thickness-1-0/) | `ROTOR_PCB_THICKNESS_MM = 1.0`<br>`ROTOR_SOLDER_MASK_EXPANSION_MM = 0.05` |
| [Board093-rotor-b-cu-only](Board093-rotor-b-cu-only/) | `ROTOR_AUTO_COPPER_LAYERS = ["B.Cu"]` |
| [Board094-custom-rotor-4-sectors-both-layers](Board094-custom-rotor-4-sectors-both-layers/) | `ROTOR_MODE = "custom"`<br>`ROTOR_CUSTOM_SECTORS = 4`<br>`ROTOR_CUSTOM_DUTY = 0.4`<br>`ROTOR_CUSTOM_START_ANGLE_DEG = 10.0`<br>`ROTOR_CUSTOM_COPPER_LAYERS = ["F.Cu", "B.Cu"]` |
| [Board095-custom-rotor-no-outline-no-bore](Board095-custom-rotor-no-outline-no-bore/) | `ROTOR_MODE = "custom"`<br>`ROTOR_CUSTOM_OUTLINE_RADIUS_MM = None`<br>`ROTOR_CUSTOM_BORE_RADIUS_MM = None` |
| [Board096-custom-rotor-radii-12-25-outline-30](Board096-custom-rotor-radii-12-25-outline-30/) | `ROTOR_MODE = "custom"`<br>`ROTOR_CUSTOM_INNER_RADIUS_MM = 12.0`<br>`ROTOR_CUSTOM_OUTER_RADIUS_MM = 25.0`<br>`ROTOR_CUSTOM_OUTLINE_RADIUS_MM = 30.0`<br>`ROTOR_CUSTOM_BORE_RADIUS_MM = 10.0` |
| [Board097-silkscreen-bottom-only](Board097-silkscreen-bottom-only/) | `SILK.SILKSCREEN_SIDES = "bottom"` |
| [Board098-silkscreen-no-labels](Board098-silkscreen-no-labels/) | `SILK.SILKSCREEN_LABELS = False` |
| [Board099-silkscreen-big-text-thick-lines](Board099-silkscreen-big-text-thick-lines/) | `SILK.SILKSCREEN_LINE_WIDTH_MM = 0.2`<br>`SILK.SILKSCREEN_TEXT_SIZE_MM = 0.8`<br>`SILK.SILKSCREEN_TEXT_STROKE_MM = 0.15`<br>`SILK.SILKSCREEN_DOT_RADIUS_MM = 0.25` |
| [Board100-silkscreen-box-margin-break-gap](Board100-silkscreen-box-margin-break-gap/) | `SILK.SILKSCREEN_BOX_MARGIN_MM = 0.8`<br>`SILK.SILKSCREEN_BREAK_VIA_GAP_MM = 2.0` |
| [Board101-silkscreen-search-span-separation](Board101-silkscreen-search-span-separation/) | `SILK.SILKSCREEN_SEARCH_SPAN_DEG = 45.0`<br>`SILK.SILKSCREEN_BREAK_SEPARATION_MM = 6.0` |
| [Board102-silkscreen-break-layer-f-cu](Board102-silkscreen-break-layer-f-cu/) | `SILK.SILKSCREEN_BREAK_LAYERS = ["F.Cu"]` |
| [Board103-silkscreen-via-clearance-tx-reach](Board103-silkscreen-via-clearance-tx-reach/) | `SILK.SILKSCREEN_VIA_EDGE_CLEARANCE_MM = 0.4`<br>`SILK.SILKSCREEN_TX_SITE_REACH_MM = 3.0` |
| [Board104-silkscreen-loops-4-four-layer](Board104-silkscreen-loops-4-four-layer/) | `PCB_LAYERS = 4`<br>`LOOPS = 4`<br>`RX_LAYER_A = 2`<br>`RX_LAYER_B = 3`<br>`TX_WIRING = "series"`<br>`TX_LAYER_A = 1`<br>`TX_LAYER_B = 4` |
<!-- end of board table -->

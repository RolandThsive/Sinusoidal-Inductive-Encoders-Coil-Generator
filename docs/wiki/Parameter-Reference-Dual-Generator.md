# 22. Parameter Reference Dual Generator

Every setting of the Dual Generator lives in a parameter file in `Dual Generator/Parameters/`. These are the only files
you edit; `Dual_Parameters.py` only gathers them. Units are millimetres, degrees and hertz unless a name says otherwise.

Every name is the Single Generator's own wherever the meaning is the same, so the
[Parameter Reference Single Generator](Parameter-Reference-Single-Generator.md) describes it, with its range. The Dual
Generator builds two parameter sets from these files, one per coil set, in the Single Generator's names, and runs the
Single Generator's own checks on each. This page lists every dual file with its defaults, describes the names that only
a dual board has, and says where a name differs from the single one.

Which file holds a name follows the Single Generator's files: a name of its `Board_Parameters.py` is in
`Dual_Board_Parameters.py`, one of its `RX_Parameters.py` in `Dual_RX1` and `Dual_RX2`, and so on. Nine names are the
exceptions: `EXCITATION_FREQ_HZ` is in `Dual_TX1` / `Dual_TX2` (each set has its own oscillator), and the eight rotor-disc
names (22.2.6) are in the board file (one disc carries both rings). The generator makes this table from the Single
Generator's own, so a parameter the Single Generator gains is a dual parameter at once, in the matching file.

> [!NOTE]
> Defaults are those of the parameter files in `Dual Generator/Parameters/` on `main`. A name put in the wrong dual file
> is ignored with a warning that names the file it belongs in. The silkscreen names are the exception: in another file
> the warning only says the name is not a parameter of this program, and it is ignored too.

## 22.1 The Files

| File | What It Sets |
|---|---|
| `Dual_Board_Parameters.py` | The one board both sets share: output, layer count, vias, clearance, bore and outline, the gap between the sets, where each set's TX ends go, the frequency rules, the stack-up, the electrical estimate, and the rotor disc (mode, edges, the distances between the rings, arc resolution, mask) |
| `Dual_RX1_Parameters.py`, `Dual_RX2_Parameters.py` | The RX coils of set 1 (inner) and set 2 (outer): loops, band, nets, profile, sub-coils, layers, bridging fingers, and the set's own vias and clearance |
| `Dual_TX1_Parameters.py`, `Dual_TX2_Parameters.py` | The TX ring of each set: excitation frequency, net, wiring, turns, pitch, shape, tail, layers, and the set's own AC resistance factor |
| `Dual_Rotor1_Parameters.py`, `Dual_Rotor2_Parameters.py` | Ring 1 (faces set 1) and ring 2 (faces set 2) of the rotor disc |
| `Dual_IC1_Parameters.py`, `Dual_IC2_Parameters.py` | The IC of each set: the limits the electrical estimate checks that set against, and the set's own capacitor series |
| `Dual_SilkScreenSuggestion_Parameters.py` | The lead-cutting suggestion on the silkscreen |

## 22.2 Board (`Dual_Board_Parameters.py`)

### 22.2.1 Output

| Name | Default | Meaning |
|---|---|---|
| `OUTPUT_DIR` | `"Output"` | Folder in which each run's `DualCoil_...` folder is made. A relative path is taken from the `Dual Generator` folder; a full path is used as it is. The folder is `DualCoil_<bore radius>_<outline radius>_<set 1 loops>x<set 2 loops>_<set 1 TX turns>x<set 2 TX turns>`, with `__1`, `__2`, ... added if it exists |
| `STATOR_FILE`, `ROTOR_FILE` | `Stator.kicad_pcb`, `Rotor.kicad_pcb` | Names of the two boards inside each run folder |
| `GENERATOR_MODE` | `"normal"` | `"normal"`: a clearance warning on the finished boards is printed and the boards are written. `"strict"`: every such warning is an error. A short, and copper of one set inside the other set's ring, are always errors |
| `CENTER_X_MM`, `CENTER_Y_MM` | 100, 100 | Sensor axis position on the KiCad page |
| `PAGE_SIZE_MM` | (150, 150) | Smallest KiCad "User" page size; grown as needed |

### 22.2.2 Stator Board

| Name | Default | Meaning |
|---|---|---|
| `PCB_LAYERS` | 4 | 4 (1 = Top, 2 = Inner 1, 3 = Inner 2, 4 = Bottom; each set's RX on `RX_LAYER_A` / `B`, its TX on `TX_LAYER_A` / `B`) or 2 (Top and Bottom: each set's RX rising edges on `RX_RISING_EDGE_LAYER`, its TX layers 1 and 4). Two layers leave no layer free for set 1's leads to cross set 2, which the checker warns about |
| `VIA_DIAMETER_MM`, `VIA_DRILL_MM` | 0.6, 0.3 | Via size (the Single Generator's example uses 0.8 / 0.4; 0.6 / 0.3 leaves room in the inner set's tight TX ring). A set may have its own (22.3) |
| `MIN_CLEARANCE_MM` | 0.15 | Copper-to-copper rule. A through via of one set is checked against the other set's copper on every layer. A set may have its own (22.3); between the sets the larger of the two applies |
| `VIA_TYPE` | `"through"` | `"through"` or `"blind"`. Blind: every via is written as a blind via between the two layers it joins. The checker warns about a pair that skips a layer and about a drill wider than about 0.15 mm; the clearance checks treat every via as a through via. A set may have its own (22.3) |

### 22.2.3 Layout: Edges And Gap

Give any of the two RX bands (22.3), the bore, the outline and the gap, each one or not (`None`): the generator places
what is not given. [Dual Layout](Dual-Layout.md) has the rules and all 32 combinations, each with a picture.

| Name | Default | Range | Meaning |
|---|---|---|---|
| `INNER_EDGE_RADIUS_MM` | None | > 0 or None | The centre hole. Must sit `INNER_EDGE_INSET_MM` inside the RX1 band. None: the RX1 band start minus `INNER_EDGE_INSET_MM`. Given with no RX1 band, a placed RX1 band starts at the bore plus `INNER_EDGE_INSET_MM` |
| `OUTER_EDGE_RADIUS_MM` | None | > 0 or None | The board edge. Must leave `OUTER_EDGE_OFFSET_MM` past the RX2 band and `OUTER_EDGE_TAIL_MARGIN_MM` past the TX2 ring. None: worked out from the RX2 band. Given with no RX2 band, a placed RX2 band runs out to it, less that room |
| `INNER_EDGE_INSET_MM` | 1.2 | ≥ 0 | Bore = RX1 band start minus this (the RX1 inner-tip vias sit on the band start) |
| `OUTER_EDGE_OFFSET_MM` | 2.0 | ≥ 0 | Outline = RX2 band end plus this, at least |
| `OUTER_EDGE_TAIL_MARGIN_MM` | 0.7 | ≥ 0 | Outline = the end of the TX2 tail plus this, at least (with `TX_TAIL_EXTRA_MM = 0` the ring ends one pitch outside its last turn), and set 2's fingers plus this |
| `EDGE_LINE_WIDTH_MM` | 0.05 | > 0 up to 1 | Line width of the `Edge.Cuts` circles |
| `TRACK_GAP_MM` | None | > 0 or None | The copper-free ring between the sets, from the outermost copper of set 1 (its TX ring and tail, or its fingers and the go-around brackets, whichever reach farther) to the innermost copper of set 2 (the RX2 band start minus half an RX trace or a via radius, whichever is larger). A band the generator places sits exactly this far from the other set; when both bands are given, the measured gap must be at least this. None: `MIN_CLEARANCE_MM` (the larger of the two sets') in its place |
| `LAYOUT_TOLERANCE_MM` | 0.05 | 0 to 1 | The rounding allowance: the built copper may differ from the layout formulas by this much before the run warns. When the outline is worked out (or a placed RX2 band runs out to a given one) and ring 2 covers the TX2 turns, it is also the room left between ring 2 and the outline beyond `ROTOR_AUTO_EDGE_CLEARANCE_MM` (half the edge line plus the polygon sag, when that is more). 0 = no allowance |
| `BAND_SPLIT` | 0.5 | between 0 and 1, both excluded | Read only when no RX band is given (both bands fitted between the edges): set 1's share of the free radial width. 0.5 = equal band widths; a 1x / 16x board is usually near 0.5 |

### 22.2.4 TX Ends And Frequencies

| Name | Default | Range | Meaning |
|---|---|---|---|
| `TERMINAL_1_DEG` | 180.0 | any number | Set 1 is turned so that its TX ends sit at this angle. Angles run from the +x axis of the page towards +y (down the page): 0 = right, 90 = bottom, 180 = left, 270 = top |
| `TERMINAL_2_DEG` | 0.0 | any number | The same for set 2. Different angles keep the two sets' breakouts apart |
| `TX_FREQ_SEPARATION_MIN` | 0.2 | 0 up to 1 (1 excluded) | The two `EXCITATION_FREQ_HZ` must differ by at least this share of the lower one; closer is a warning |
| `TX_FREQ_RATIO_MAX_ORDER` | 4 | 1 to 100 | A frequency ratio within `TX_FREQ_RATIO_TOLERANCE` of any p:q with p, q up to this is a warning (4 covers 2:1, 3:1, 4:1, 3:2, 4:3). 1 turns the ratio warning off |
| `TX_FREQ_RATIO_TOLERANCE` | 0.02 | 0 up to 1 (1 excluded) | How close to p:q counts (0.02 = 2 %) |

### 22.2.5 Stack-Up And Electrical Estimate

These hold for both sets, as on a single board (see 21.1.3 and 21.1.4 of the
[single reference](Parameter-Reference-Single-Generator.md#2114-electrical-estimate)). `EXCITATION_FREQ_HZ` is not here:
each set has its own, in `Dual_TX1` / `Dual_TX2`. A set may have its own `TX_AC_RESISTANCE_FACTOR` (in `Dual_TX<k>`) and
`TANK_CAP_SERIES` (in `Dual_IC<k>`).

| Name | Default |
|---|---|
| `AIR_GAP_MM` | 1.0 (one rotor, one air gap) |
| `PCB_THICKNESS_MM` | 3.2 |
| `COPPER_THICKNESS_UM` | 35 |
| `COPPER_CONDUCTIVITY_S_M` | 5.8e7 |
| `TX_AC_RESISTANCE_FACTOR` | 2.0 |
| `STACKUP_PREPREG_MM` | 0.2 |
| `TANK_CAP_SERIES` | `"E12"` |

### 22.2.6 Rotor Disc

| Name | Default | Range | Meaning |
|---|---|---|---|
| `ROTOR_MODE` | `"according_to_stator"` | `according_to_stator`, `custom` | Once for the disc. `according_to_stator`: each ring follows its own set (`LOOPS` sectors, extent from its RX band and TX ring); the disc's bore and outline are the stator's. `custom`: each ring from its `ROTOR_CUSTOM_*` values, the disc's edges from the two lines below |
| `ROTOR_AUTO_EDGE_CLEARANCE_MM` | 0.5 | ≥ 0 | `according_to_stator`: ring copper stays this far from the bore and the outline |
| `ROTOR_START_ANGLE_ZERO` | `"rx_zero"` | `rx_zero`, `board` | Where each ring's start angle is measured from. `rx_zero`: from its own set's RX pattern zero (the set's turn is added), so both tracks read 0 at the same shaft angle. `board`: from the board's +x axis, as the Single Generator measures it |
| `ROTOR_CUSTOM_OUTLINE_RADIUS_MM` | 26.875 | > 0 or None | `custom`: outer edge of the disc (None = no outline) |
| `ROTOR_CUSTOM_BORE_RADIUS_MM` | 7.25 | > 0 or None | `custom`: centre hole (None = no hole) |
| `ROTOR_TRACK_GAP_MM` | 2.0 | ≥ 0 | Bare ring that must stay between ring 1's outer radius and ring 2's inner radius. Smaller is an error naming the extension to change |
| `ROTOR_1_TO_RX2_MM` | 3.0 | ≥ 0 | Least distance from ring 1's outer radius to the innermost RX2 copper; smaller is a warning. Use 5.0 when the radius allows it |
| `ROTOR_2_TO_RX1_MM` | 2.0 | ≥ 0 | Least distance from ring 2's inner radius to the outermost RX1 copper; smaller is a warning |
| `ROTOR_PCB_THICKNESS_MM` | None | > 0 up to 20, or None | Rotor thickness written into the KiCad file; None = `PCB_THICKNESS_MM` |
| `ROTOR_ARC_STEPS_PER_SECTOR` | `"auto"` | `"auto"` or 8 to 5000 | Points on every arc of a sector |
| `ROTOR_CHORD_TOLERANCE_MM` | 0.001 | ≥ 0.001 | How far the polygon may lie outside the true circle |
| `ROTOR_SOLDER_MASK_EXPANSION_MM` | −1 | −1, or 0 to 5 | Mask opening over the rotor copper, the same for both rings (−1 = the mask stays over the copper) |

## 22.3 RX (`Dual_RX1_Parameters.py`, `Dual_RX2_Parameters.py`)

The two files have the same names, those of the Single Generator's `RX_Parameters.py`, and at the end the set's own
vias and clearance.

| Name | Set 1 | Set 2 | Meaning |
|---|---|---|---|
| `LOOPS` | 1 | 16 | Electrical periods per turn, 1 to 16. Set 1 is the coarse, absolute track; set 2 the fine one. Set 1's angle error must stay below 180 / `LOOPS` of set 2 degrees |
| `INSIDE_RADIUS_MM`, `OUTSIDE_RADIUS_MM` | 8.45, 11.7 | 18.0, 23.9 | The band as a radii pair (with `RX_R_BASE_MM`, `RX_A_MM` = None) |
| `RX_R_BASE_MM`, `RX_A_MM` | None, None | None, None | The band as centre and half width: `RX_R_BASE_MM ± RX_A_MM` (with the radii pair = None). All four None: the generator places the band ([Dual Layout](Dual-Layout.md)) |
| `RX_TRACE_WIDTH_MM` | 0.15 | 0.15 | RX trace width |
| `RX_NET_PHASE_0_2` | `"SIN_1"` | `"SIN_2"` | Net of phases 0 and 2 (sine). Every net of the two sets must have its own name |
| `RX_NET_PHASE_1_3` | `"COS_1"` | `"COS_2"` | Net of phases 1 and 3 (cosine) |
| `RX_PROFILE` | `"equal_area"` | `"equal_area"` | `"equal_area"` or `"cosine_r"`; see [RX Profiles](RX-Profiles.md) |
| `STEPS_PER_LOOP`, `RX_CHORD_TOLERANCE_MM` | `"auto"`, 0.001 | `"auto"`, 0.001 | Polyline resolution of one period |
| `RX_SUBCOILS`, `RX_SUBCOIL_SPLIT_ELEC_DEG` | 1, 45.0 | 1, 45.0 | Sub-coils per RX coil (1, 2 or 3) and their spacing |
| `RX_LAYER_A`, `RX_LAYER_B` | 1, 2 | 1, 2 | 4 layers: the two RX layers (1 = Top, 2 = Inner 1, 3 = Inner 2, 4 = Bottom); they must differ. Keep one layer free of both sets' copper across set 2 for set 1's leads |
| `RX_RISING_EDGE_LAYER` | `"F.Cu"` | `"F.Cu"` | 2 layers: the layer of the rising edges, `"F.Cu"` or `"B.Cu"` |
| `RX_VIA_ELECTRICAL_DEG` | 90.0 | 90.0 | Electrical angle of the outer-tip via (about 50 to 130) |
| `RX_TABS` | `"none"` | `"none"` | Bridging fingers: `"none"` (plain bands broken out by hand, the usual dual board), `"all"` or `"single"`. Set 1's fingers push set 2 outwards: the layout places set 2 past them and past the go-around brackets where the TX makes way for them. Set 2's fingers push the outline out |
| `RX_TAB_LAYER`, `RX_TAB_LENGTH_MM`, `RX_TAB_WIDTH_MM` | `"auto"`, 3.0, 1.0 | `"auto"`, 3.0, 1.0 | The fingers' layer, how far they reach past the band, and the spacing of their legs (as in the Single Generator) |
| `VIA_DIAMETER_MM`, `VIA_DRILL_MM`, `VIA_TYPE`, `MIN_CLEARANCE_MM` | None | None | This set's own vias and clearance; None = the board's value (22.2.2). The KiCad file holds each via with its own size; between the sets the larger clearance applies |

## 22.4 TX (`Dual_TX1_Parameters.py`, `Dual_TX2_Parameters.py`)

The two files have the same names, those of the Single Generator's `TX_Parameters.py`, with `EXCITATION_FREQ_HZ` and,
at the end, the set's own `TX_AC_RESISTANCE_FACTOR`.

| Name | Set 1 | Set 2 | Meaning |
|---|---|---|---|
| `EXCITATION_FREQ_HZ` | 3.0e6 | 4.3e6 | This set's TX oscillator frequency with the rotor in place. Give the two sets different frequencies (22.2.4) |
| `TX_NET` | `"TX_1"` | `"TX_2"` | Net of the TX ring |
| `TX_WIRING` | `"series"` | `"series"` | `"series"` (2 × `TX_TURNS` turns, joined by one via at the inner end, both ends at the terminal angle one on each layer), `"parallel"` (the same turns on both layers, stitched at the terminal; its inner end comes out on an inner tail that ends one pitch outside the last turn) or `"single"` (`TX_TURNS` turns on `TX_LAYER_A`, the inner end out on a tail on another layer) |
| `TX_TURNS` | 4 | 4 | Complete turns per TX layer. Every turn of the inner ring pushes set 2 outwards |
| `TX_OFFSET_MM` | 0.8 | 0.8 | First turn radius = RX outside radius plus this |
| `TX_PITCH_MM` | 0.35 | 0.35 | Radial pitch between turns. A parallel ring needs at least 0.43 mm with 0.6 mm vias |
| `TX_TRACE_WIDTH_MM` | 0.15 | 0.15 | TX trace width |
| `TX_STEPS`, `TX_CHORD_TOLERANCE_MM` | `"auto"`, 0.001 | `"auto"`, 0.001 | Polyline resolution of a turn |
| `TX_SHAPE` | `"stepped_diagonal"` | `"stepped_diagonal"` | `"stepped_diagonal"`, `"stepped_arc"` (needs a tail longer than its arcs) or `"spiral"` (its last turn ends one pitch farther out), as in the Single Generator |
| `TX_STEPPED_ARC_RADIUS_MM` | `"auto"` | `"auto"` | `stepped_arc` only: radius of the innermost arc |
| `TX_TAIL_EXTRA_MM` | 0.0 | 0.0 | How far the TX ends run on past one pitch outside the last turn. A tail on set 1 pushes set 2 outwards; on set 2, the outline |
| `TX_STEPPED_ANGLE_DEG` | 45 | 45 | Angle of the steps to the turns |
| `TX_INSIDE_VIA_DISTANCE_MM` | 0.2 | 0.2 | The via that joins the two TX layers, this far inside the first turn (at most `TX_OFFSET_MM` minus the via radius, half an RX trace and `MIN_CLEARANCE_MM`) |
| `TX_LAYER_A`, `TX_LAYER_B` | 1, 3 | 1, 3 | The two TX layers; they must differ (on 2 layers: 1 and 4). Both sets may use the same layers |
| `TX_SERIES_UNDERPASS_LAYER`, `TX_PARALLEL_BREAK_STYLE` | `"auto"`, `"stitched"` | `"auto"`, `"stitched"` | How the TX makes way for this set's fingers, as in the Single Generator; unused without fingers |
| `TX_AC_RESISTANCE_FACTOR` | None | None | This set's own factor for the electrical estimate; None = the board's (22.2.5) |

## 22.5 Rotor Rings (`Dual_Rotor1_Parameters.py`, `Dual_Rotor2_Parameters.py`)

The two files have the same names, those of the Single Generator's `Rotor_Parameters.py`; the disc itself is set in
22.2.6. See [Rotor Features - Dual Generator](Rotor-Features-Dual-Generator.md).

| Name | Ring 1 | Ring 2 | Meaning |
|---|---|---|---|
| `ROTOR_AUTO_DUTY` | 0.5 | 0.5 | Metal fraction of each period |
| `ROTOR_AUTO_START_ANGLE_DEG` | 0.0 | 0.0 | Angle of the first sector edge, from the set's RX pattern zero (with `ROTOR_START_ANGLE_ZERO = "rx_zero"`). Keep the two equal |
| `ROTOR_AUTO_COVER_TX` | False | True | False: the ring ends inside its TX ring. True: over its TX turns, ending `ROTOR_AUTO_TX_OVERHANG_MM` past the outermost one. True on ring 1 is a warning |
| `ROTOR_AUTO_TX_OVERHANG_MM` | 0.5 | 0.5 | `ROTOR_AUTO_COVER_TX = True` only |
| `ROTOR_AUTO_EXTENSION_MM` | None | None | Past the RX band, both edges. None = `AIR_GAP_MM` |
| `ROTOR_AUTO_EXTENSION_INNER_MM` | None | 0.5 | Inner edge only. None = `ROTOR_AUTO_EXTENSION_MM`. Ring 2's is kept short so it stays `ROTOR_TRACK_GAP_MM` away from ring 1 |
| `ROTOR_AUTO_EXTENSION_OUTER_MM` | 0.0 | None | Outer edge only, when `ROTOR_AUTO_COVER_TX = False`. 0 = the ring ends at the band end |
| `ROTOR_AUTO_TX_CLEARANCE_MM` | 0.1 | 0.1 | `ROTOR_AUTO_COVER_TX = False` only: copper stays this far inside the TX ring |
| `ROTOR_AUTO_COPPER_LAYERS` | `["F.Cu"]` | `["F.Cu"]` | Layers carrying the ring's sectors |
| `ROTOR_CUSTOM_SECTORS` | 1 | 16 | `custom`: number of sectors |
| `ROTOR_CUSTOM_DUTY`, `ROTOR_CUSTOM_START_ANGLE_DEG` | 0.5, 0.0 | 0.5, 0.0 | `custom`: metal fraction and start angle |
| `ROTOR_CUSTOM_INNER_RADIUS_MM`, `ROTOR_CUSTOM_OUTER_RADIUS_MM` | 7.77, 11.7 | 17.5, 26.32 | `custom`: the ring's radii (the defaults are what `according_to_stator` computes for the default board) |
| `ROTOR_CUSTOM_COPPER_LAYERS` | `["F.Cu"]` | `["F.Cu"]` | `custom`: layers carrying the sectors |

## 22.6 IC (`Dual_IC1_Parameters.py`, `Dual_IC2_Parameters.py`)

One file per set, because a dual board has one IC per set (the two may be the same type or different ones). The names
and ranges are those of the single `IC_Parameters.py` (21.5); both files default to the IPS2550: `IC_NAME` `"IPS2550"`,
`IC_OSC_MIN_MHZ` 2.0, `IC_OSC_MAX_MHZ` 5.6, `IC_MIN_RP_OHM` 250, `IC_SPLIT_TANK_CAPS` True. At the end, `TANK_CAP_SERIES`
(None = the board's, 22.2.5): the capacitor series the estimate suggests this set's tank capacitor from. They never
change a board.

## 22.7 Silkscreen Suggestion (`Dual_SilkScreenSuggestion_Parameters.py`)

The same names, defaults and ranges as the single `SilkScreenSuggestion_Parameters.py`
([21.6](Parameter-Reference-Single-Generator.md#216-silkscreen-suggestion-silkscreensuggestion_parameterspy)), with these
differences: `SILKSCREEN_BREAK_LAYERS` is `["F.Cu", "In1.Cu"]` (on a 2-layer board, set it to `["F.Cu", "B.Cu"]`, which
is also what a missing or wrong value falls back to there), and `SILKSCREEN_SEARCH_SPAN_DEG` is measured from each
set's own terminal angle (`TERMINAL_1_DEG`, `TERMINAL_2_DEG`). The suggested vias keep the room of the larger via and
clearance of the two sets (a set may have its own, 22.3). The lead names are `SIN1_1`, `SIN1_2`, `COS1_1`, ..., `TX1_1 TOP`, `TX1_2 IN2` for set 1 and the same with 2 for set 2. See
[Silkscreen - Dual Generator](Silkscreen-Dual-Generator.md).

[<img align="right" src="https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2.png" alt="Sinusoidal Coil Generator logo, click to see it spin" width="72">](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2_rotor_spin_400px.webp)

| Previous | Next |
|:---|---:|
| [Parameter Reference Single Generator](Parameter-Reference-Single-Generator.md) | [Checks, Errors And Warnings](Checks-Errors-And-Warnings.md) |

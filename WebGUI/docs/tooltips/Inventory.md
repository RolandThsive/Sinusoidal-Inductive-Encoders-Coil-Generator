# Tooltip inventory

Every help box (tooltip) of the web tool, numbered, with where it shows and what its text is made from today.
The proposed words of each one are in `WebGUI/tools/tips_words.py`. A tip that changes with the page's state
(a hidden layer, a locked switch, a run that is out of date) is listed once per state.

178 tips: 113 settings, 59 buttons, switches and other controls, and the 6 TX layout cards.

## Where the texts come from today

| Source | What it holds |
|---|---|
| `WebGUI/app/paramtips.js` | A text written for the page, for 74 settings |
| The comment beside a setting in its parameter file | Shown for the 39 settings `paramtips.js` does not name, with the comment's own line breaks |
| `TIPS` in `WebGUI/app/tips.js` | The fixed texts of buttons and switches (`data-tip-id`) |
| Strings built in `app/fields.js`, `app/pages.js`, `app/preview.js`, `app/run.js` | Texts that change with the page's state (`data-tip`) |

Each setting's tip opens from the (i) beside its name, in Basic and in Advanced. The settings the page does not list
(the Output block and `GENERATOR_MODE`) have no tip.

## Settings

| No. | Name on the page | Name in the file | Shows in | Today | Picture |
|---|---|---|---|---|---|
| 1 | Board Layers | `PCB_LAYERS` | Single · Board; Dual · Board | written |  |
| 2 | Via Diameter (mm) | `VIA_DIAMETER_MM` | Single · Board; Dual · Board; Dual · RX 1; Dual · RX 2 | written |  |
| 3 | Via Drill (mm) | `VIA_DRILL_MM` | Single · Board; Dual · Board; Dual · RX 1; Dual · RX 2 | written |  |
| 4 | Via Type | `VIA_TYPE` | Single · Board; Dual · Board; Dual · RX 1; Dual · RX 2 | file comment |  |
| 5 | Min Clearance (mm) | `MIN_CLEARANCE_MM` | Single · Board; Dual · Board; Dual · RX 1; Dual · RX 2 | written |  |
| 6 | Inner Edge Inset (mm) | `INNER_EDGE_INSET_MM` | Single · Board; Dual · Board | written |  |
| 7 | Board Inner Radius (mm) | `INNER_EDGE_RADIUS_MM` | Single · Board; Dual · Board | written |  |
| 8 | Outer Edge Offset (mm) | `OUTER_EDGE_OFFSET_MM` | Single · Board; Dual · Board | written |  |
| 9 | Board Outer Radius (mm) | `OUTER_EDGE_RADIUS_MM` | Single · Board; Dual · Board | written |  |
| 10 | Outer Edge Tail Margin (mm) | `OUTER_EDGE_TAIL_MARGIN_MM` | Single · Board; Dual · Board | written |  |
| 11 | Edge Line Width (mm) | `EDGE_LINE_WIDTH_MM` | Single · Board; Dual · Board | written |  |
| 12 | Air Gap (mm) | `AIR_GAP_MM` | Single · Board; Dual · Board | written |  |
| 13 | PCB Thickness (mm) | `PCB_THICKNESS_MM` | Single · Board; Dual · Board | written |  |
| 14 | Excitation Freq (Hz) | `EXCITATION_FREQ_HZ` | Single · Board; Dual · TX 1; Dual · TX 2 | written |  |
| 15 | Copper Thickness (µm) | `COPPER_THICKNESS_UM` | Single · Board; Dual · Board | file comment |  |
| 16 | Copper Conductivity (S/m) | `COPPER_CONDUCTIVITY_S_M` | Single · Board; Dual · Board | file comment |  |
| 17 | TX AC Resistance Factor | `TX_AC_RESISTANCE_FACTOR` | Single · Board; Dual · Board; Dual · TX 1; Dual · TX 2 | file comment |  |
| 18 | Stackup Prepreg (mm) | `STACKUP_PREPREG_MM` | Single · Board; Dual · Board | file comment |  |
| 19 | Tank Cap Series | `TANK_CAP_SERIES` | Single · Board; Dual · Board; Dual · IC 1; Dual · IC 2 | file comment |  |
| 20 | Loops | `LOOPS` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 21 | RX Inside Radius (mm) | `INSIDE_RADIUS_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 22 | RX Outside Radius (mm) | `OUTSIDE_RADIUS_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 23 | RX R Base (mm) | `RX_R_BASE_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 24 | RX Swing A (mm) | `RX_A_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 25 | RX Trace Width (mm) | `RX_TRACE_WIDTH_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 26 | RX Net SIN (Phases 0 / 2) | `RX_NET_PHASE_0_2` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 27 | RX Net COS (Phases 1 / 3) | `RX_NET_PHASE_1_3` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 28 | RX Profile | `RX_PROFILE` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 29 | Steps Per Loop | `STEPS_PER_LOOP` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 30 | RX Chord Tolerance (mm) | `RX_CHORD_TOLERANCE_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 31 | RX Sub-Coils | `RX_SUBCOILS` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 32 | RX Subcoil Split Elec (deg) | `RX_SUBCOIL_SPLIT_ELEC_DEG` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 33 | RX Layer A | `RX_LAYER_A` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 34 | RX Layer B | `RX_LAYER_B` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 35 | RX Rising Edge Layer | `RX_RISING_EDGE_LAYER` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 36 | RX Via Electrical (deg) | `RX_VIA_ELECTRICAL_DEG` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 37 | RX Tabs | `RX_TABS` | Single · RX; Dual · RX 1; Dual · RX 2 | written | yes |
| 38 | RX Tab Length (mm) | `RX_TAB_LENGTH_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 39 | RX Tab Width (mm) | `RX_TAB_WIDTH_MM` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 40 | RX Tab Layer | `RX_TAB_LAYER` | Single · RX; Dual · RX 1; Dual · RX 2 | written |  |
| 41 | TX Net | `TX_NET` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 42 | TX Turns Per Layer | `TX_TURNS` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 43 | TX Offset (mm) | `TX_OFFSET_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 44 | TX Pitch (mm) | `TX_PITCH_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 45 | TX Trace Width (mm) | `TX_TRACE_WIDTH_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 46 | TX Steps | `TX_STEPS` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 47 | TX Chord Tolerance (mm) | `TX_CHORD_TOLERANCE_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 48 | TX Tail Extra (mm) | `TX_TAIL_EXTRA_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 49 | TX Shape | `TX_SHAPE` | Single · TX; Dual · TX 1; Dual · TX 2 | written | yes |
| 50 | TX Inside Via Distance (mm) | `TX_INSIDE_VIA_DISTANCE_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 51 | TX Stepped Angle (deg) | `TX_STEPPED_ANGLE_DEG` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 52 | TX Stepped Arc Radius (mm) | `TX_STEPPED_ARC_RADIUS_MM` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 53 | TX Wiring | `TX_WIRING` | Single · TX; Dual · TX 1; Dual · TX 2 | written | yes |
| 54 | TX Layer A | `TX_LAYER_A` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 55 | TX Layer B | `TX_LAYER_B` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 56 | TX Series Underpass Layer | `TX_SERIES_UNDERPASS_LAYER` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 57 | TX Parallel Break Style | `TX_PARALLEL_BREAK_STYLE` | Single · TX; Dual · TX 1; Dual · TX 2 | written |  |
| 58 | Rotor Mode | `ROTOR_MODE` | Single · Rotor; Dual · Board | written |  |
| 59 | Rotor Metal Fraction | `ROTOR_AUTO_DUTY` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 60 | Rotor Auto Start Angle (deg) | `ROTOR_AUTO_START_ANGLE_DEG` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 61 | Rotor Auto Extension (mm) | `ROTOR_AUTO_EXTENSION_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written | yes |
| 62 | Rotor Auto Extension Inner (mm) | `ROTOR_AUTO_EXTENSION_INNER_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 63 | Rotor Auto Extension Outer (mm) | `ROTOR_AUTO_EXTENSION_OUTER_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 64 | Rotor Auto TX Clearance (mm) | `ROTOR_AUTO_TX_CLEARANCE_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 65 | Copper Over The TX Turns | `ROTOR_AUTO_COVER_TX` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written | yes |
| 66 | Rotor Auto TX Overhang (mm) | `ROTOR_AUTO_TX_OVERHANG_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 67 | Rotor Auto Edge Clearance (mm) | `ROTOR_AUTO_EDGE_CLEARANCE_MM` | Single · Rotor; Dual · Board | written |  |
| 68 | Rotor Auto Copper Layers | `ROTOR_AUTO_COPPER_LAYERS` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 69 | Rotor Metal Sectors | `ROTOR_CUSTOM_SECTORS` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 70 | Rotor Metal Fraction | `ROTOR_CUSTOM_DUTY` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 71 | Rotor Custom Start Angle (deg) | `ROTOR_CUSTOM_START_ANGLE_DEG` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 72 | Rotor Custom Inner Radius (mm) | `ROTOR_CUSTOM_INNER_RADIUS_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 73 | Rotor Custom Outer Radius (mm) | `ROTOR_CUSTOM_OUTER_RADIUS_MM` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 74 | Rotor Custom Copper Layers | `ROTOR_CUSTOM_COPPER_LAYERS` | Single · Rotor; Dual · Rotor 1; Dual · Rotor 2 | written |  |
| 75 | Rotor Custom Outline Radius (mm) | `ROTOR_CUSTOM_OUTLINE_RADIUS_MM` | Single · Rotor; Dual · Board | written |  |
| 76 | Rotor Custom Bore Radius (mm) | `ROTOR_CUSTOM_BORE_RADIUS_MM` | Single · Rotor; Dual · Board | written |  |
| 77 | Rotor PCB Thickness (mm) | `ROTOR_PCB_THICKNESS_MM` | Single · Rotor; Dual · Board | written |  |
| 78 | Rotor Arc Steps Per Sector | `ROTOR_ARC_STEPS_PER_SECTOR` | Single · Rotor; Dual · Board | written |  |
| 79 | Rotor Chord Tolerance (mm) | `ROTOR_CHORD_TOLERANCE_MM` | Single · Rotor; Dual · Board | written |  |
| 80 | Rotor Solder Mask Expansion (mm) | `ROTOR_SOLDER_MASK_EXPANSION_MM` | Single · Rotor; Dual · Board | written |  |
| 81 | IC Name | `IC_NAME` | Single · IC; Dual · IC 1; Dual · IC 2 | file comment |  |
| 82 | IC Osc Min (MHz) | `IC_OSC_MIN_MHZ` | Single · IC; Dual · IC 1; Dual · IC 2 | file comment |  |
| 83 | IC Osc Max (MHz) | `IC_OSC_MAX_MHZ` | Single · IC; Dual · IC 1; Dual · IC 2 | file comment |  |
| 84 | IC Min Rp (ohm) | `IC_MIN_RP_OHM` | Single · IC; Dual · IC 1; Dual · IC 2 | file comment |  |
| 85 | IC Split Tank Caps | `IC_SPLIT_TANK_CAPS` | Single · IC; Dual · IC 1; Dual · IC 2 | file comment |  |
| 86 | Silkscreen Suggestion | `SILKSCREEN_SUGGESTION` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 87 | Silkscreen Sides | `SILKSCREEN_SIDES` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 88 | Silkscreen Color | `SILKSCREEN_COLOR` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 89 | Silkscreen Labels | `SILKSCREEN_LABELS` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 90 | Silkscreen Dot On All Vias | `SILKSCREEN_DOT_ON_ALL_VIAS` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 91 | Silkscreen Line Width (mm) | `SILKSCREEN_LINE_WIDTH_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 92 | Silkscreen Text Size (mm) | `SILKSCREEN_TEXT_SIZE_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 93 | Silkscreen Text Stroke (mm) | `SILKSCREEN_TEXT_STROKE_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 94 | Silkscreen Dot Radius (mm) | `SILKSCREEN_DOT_RADIUS_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 95 | Silkscreen Box Margin (mm) | `SILKSCREEN_BOX_MARGIN_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 96 | Silkscreen Break Via Gap (mm) | `SILKSCREEN_BREAK_VIA_GAP_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment | yes |
| 97 | Silkscreen Search Span (deg) | `SILKSCREEN_SEARCH_SPAN_DEG` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 98 | Silkscreen Break Separation (mm) | `SILKSCREEN_BREAK_SEPARATION_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 99 | Silkscreen Break Layers | `SILKSCREEN_BREAK_LAYERS` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 100 | Silkscreen Via Edge Clearance (mm) | `SILKSCREEN_VIA_EDGE_CLEARANCE_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 101 | Silkscreen TX Site Reach (mm) | `SILKSCREEN_TX_SITE_REACH_MM` | Single · Silkscreen suggestion; Dual · Silkscreen suggestion | file comment |  |
| 102 | Track Gap (mm) | `TRACK_GAP_MM` | Dual · Board | file comment | yes |
| 103 | Band Split | `BAND_SPLIT` | Dual · Board | file comment | yes |
| 104 | Layout Tolerance (mm) | `LAYOUT_TOLERANCE_MM` | Dual · Board | file comment |  |
| 105 | Terminal 1 (deg) | `TERMINAL_1_DEG` | Dual · Board | file comment |  |
| 106 | Terminal 2 (deg) | `TERMINAL_2_DEG` | Dual · Board | file comment |  |
| 107 | TX Freq Separation Min | `TX_FREQ_SEPARATION_MIN` | Dual · Board | file comment |  |
| 108 | TX Freq Ratio Max Order | `TX_FREQ_RATIO_MAX_ORDER` | Dual · Board | file comment |  |
| 109 | TX Freq Ratio Tolerance | `TX_FREQ_RATIO_TOLERANCE` | Dual · Board | file comment |  |
| 110 | Rotor Start Angle Zero | `ROTOR_START_ANGLE_ZERO` | Dual · Board | file comment |  |
| 111 | Rotor Track Gap (mm) | `ROTOR_TRACK_GAP_MM` | Dual · Board | file comment |  |
| 112 | Rotor 1 To Rx2 (mm) | `ROTOR_1_TO_RX2_MM` | Dual · Board | file comment |  |
| 113 | Rotor 2 To Rx1 (mm) | `ROTOR_2_TO_RX1_MM` | Dual · Board | file comment |  |

## Buttons, switches and other controls

| No. | Control | Tip id | Area | Text today |
|---|---|---|---|---|
| 114 | Back | `nav-back` | Top bar | Back to the page you came from |
| 115 | Home | `nav-home` | Top bar | The blog's front page |
| 116 | The generator menu | `gen-menu` | Top bar | Which generator the page runs. Your settings of each generator are kept when you switch. Arc and Linear are not available. |
| 117 | The generator menu, its Single line | `gen-single` | Top bar | The Single Coil Set Generator: one sine and cosine RX pair with one TX coil. Your settings of each generator are kept when you switch. |
| 118 | The generator menu, its Dual line | `gen-dual` | Top bar | The Dual Coil Set Generator: two coil sets on one board, an inner and an outer one, each with its own rotor ring (a coarse and a fine track). Your settings of each generator are kept when you switch. |
| 119 | Basic | `mode-basic` | Top bar | The main settings of each category, with sliders |
| 120 | Advanced | `mode-advanced` | Top bar | Every setting of every parameter file, as the desktop generator has them |
| 121 | Help | `btn-help` | Top bar | Open the quick guide to choosing the parameters (a new tab) |
| 122 | Import | `btn-import` | Top bar | Load a design from files: parameter files (.py), a zip of them, or the Parameters.txt of a run. Single and Dual designs are both read. |
| 123 | Export | `btn-export` | Top bar | Download the parameter files with your settings, ready for the desktop generator |
| 124 | Share | `btn-share` | Top bar | Copy a link that opens this page with your settings |
| 125 | The tabs (Board, RX, TX, Rotor, IC, Silk) | `tab` | Settings | The main settings of the RX coils (2 settings changed) |
| 126 | The Set 1 / Set 2 switch (Dual) | `set` | Settings | The RX settings of coil set 1 (the inner one) |
| 127 | Advanced · the Automatic Rotor and Custom Rotor headings | `rotor-fold` | Settings | Show or hide the automatic rotor settings (used when Rotor Mode is according_to_stator) |
| 128 | Advanced · Find A Setting | `find` | Settings | Type a part of a setting's name, its Python name or a word of its help: every match of every file is listed |
| 129 | The arrow beside a changed setting | `reset-one` | Settings | Back to the starting value |
| 130 | The None switch of a setting | `none` | Settings | None: the centre hole follows the RX band (the band start minus the inset) |
| 131 | A locked None switch | `none-locked` | Settings | Locked: the RX band is set by RX R Base and RX Swing A. Set those to None first to use this pair |
| 132 | Strict | `strict` | Under the settings | Strict: every warning stops the run, as --strict does on the desktop (GENERATOR_MODE) |
| 133 | Reset | `btn-reset` | Under the settings | Put every setting of this generator back to its published value |
| 134 | Check Only | `btn-check` | Under the settings | Run only the generator's checks of the settings: quick, and nothing is built |
| 135 | Generate | `btn-generate` | Under the settings | Run the generator with these settings (Ctrl + Enter) |
| 136 | Range | `result-range` | Results box | The unique angle range: one electrical period of the RX pattern |
| 137 | R | `result-R` | Results box | Resistance of the TX coil at DC (the generator's estimate) |
| 138 | L | `result-L` | Results box | Inductance of the TX coil without the rotor (the generator's estimate) |
| 139 | C | `result-C` | Results box | The tank capacitors for the TX frequency below (the generator's estimate) |
| 140 | F | `result-f` | Results box | The TX frequency the tank capacitors are sized for |
| 141 | Stator | `view-stator` | Preview | The stator board alone |
| 142 | Rotor | `view-rotor` | Preview | The rotor board alone |
| 143 | Overlay | `view-overlay` | Preview | The rotor's copper drawn over the stator, at the Rotor Angle below |
| 144 | Pictures | `view-pictures` | Preview | The two pictures the generator draws of the board (SVG files of the run) |
| 145 | Full screen | `btn-fullscreen` | Preview | Show the preview full screen (Esc to leave) |
| 146 | Full screen, while it is on | `btn-fullscreen-on` | Preview | Leave full screen (Esc) |
| 147 | Fit | `btn-fit` | Preview | Fit the board to the preview (also: double-click, or the 0 key) |
| 148 | Measure | `btn-measure` | Preview | Measure a distance: click two points on the board |
| 149 | The position readout | `readout` | Preview | The position of the mouse on the board, from the board centre |
| 150 | Rotor Angle | `rotor-angle` | Preview | Turn the rotor over the stator (the preview only) |
| 151 | A copper layer's chip | `layer` | Preview | Hover to highlight the Top copper (F.Cu), click to hide it (the preview only) |
| 152 | A hidden copper layer's chip | `layer-off` | Preview | Show the Top copper (F.Cu) |
| 153 | The chip of a layer this board does not have | `layer-missing` | Preview | This board has no copper on the Inner-1 layer (In1.Cu) |
| 154 | Vias | `vias` | Preview | Show or hide the vias. Hover to enlarge small vias to at least 6 px (the preview only, the boards are unchanged) |
| 155 | Vias, hidden | `vias-off` | Preview | Show the vias |
| 156 | Silk Top / Silk Bottom | `silk` | Preview | Hide the silkscreen suggestion on the top side (F.SilkS; the preview only) |
| 157 | Silk Top / Silk Bottom, hidden | `silk-off` | Preview | Show the silkscreen suggestion on the top side (F.SilkS) |
| 158 | Silk chip of a side without marks | `silk-missing` | Preview | This board has no silkscreen marks on its bottom side (B.SilkS) |
| 159 | Sin Loops, Cos Loops, TX Loops, Set 1, Set 2 | `net` | Preview | Hover to highlight the SIN coil (RX phases 0 / 2), click to hide it (the preview only) |
| 160 | The same buttons, hidden | `net-off` | Preview | Show the SIN coil (RX phases 0 / 2) |
| 161 | Origin | `origin` | Preview | The board centre (origin). Hover to highlight it, click to hide it |
| 162 | Origin, hidden | `origin-off` | Preview | Show the board centre (origin) |
| 163 | Pictures · a picture | `picture-open` | Preview | Open this picture in a new tab |
| 164 | Show Info | `show-info` | Checks | Also list the generator's notes (info), not only its warnings and errors |
| 165 | A setting's name in a finding | `param-link` | Checks | Show this setting |
| 166 | Run Text | `btn-runtext` | Checks | Everything the generator printed in this run, as on the desktop |
| 167 | All Files | `btn-files` | Checks | Every file of this run, to download one by one |
| 168 | Cancel | `btn-cancel` | Run box | Stop this run. Python starts again, which takes a few seconds |
| 169 | Download | `btn-download` | Downloads | Download this run as one zip, the same folder the desktop generator writes: Stator.kicad_pcb, Rotor.kicad_pcb, their .kicad_pro files, Parameters.txt and the two pictures. This run: Coil_15_27_1_1_3_Single_SteppedDiagonal.zip |
| 170 | Any button, after a setting changed | `btn-download-stale` | Downloads | The settings changed: press Generate first |
| 171 | Stator | `btn-dl-stator` | Downloads | Download only the stator board of this run (Coil_15_27_1_1_3_Single_SteppedDiagonal_Stator.kicad_pcb), ready to open in KiCad |
| 172 | Rotor | `btn-dl-rotor` | Downloads | Download only the rotor board of this run (Coil_15_27_1_1_3_Single_SteppedDiagonal_Rotor.kicad_pcb), ready to open in KiCad |

In the texts above, a run name, a layer, a count or a setting's name is an example of what the page fills in.

## TX layout cards

| No. | Card | Id | Shows in | Text today |
|---|---|---|---|---|
| 173 | Single On Bottom | `2-bottom` | Settings · TX · the layout cards of a 2-layer board | Single On Bottom: The original, proven layout |
| 174 | Single On Top | `2-top` | Settings · TX · the layout cards of a 2-layer board | Single On Top: Next to the rotor: more signal in the model |
| 175 | Series Top + Bottom | `2-series` | Settings · TX · the layout cards of a 2-layer board | Series Top + Bottom: The fingers go around the Top turns |
| 176 | Single On Bottom | `4-bottom` | Settings · TX · the layout cards of a 4-layer board | Single On Bottom: RX on Top + Inner-1 |
| 177 | Series Top + Inner-2 | `4-renesas` | Settings · TX · the layout cards of a 4-layer board | Series Top + Inner-2: The Renesas IPS2200 reference |
| 178 | Series Top + Inner-1 | `4-inner1` | Settings · TX · the layout cards of a 4-layer board | Series Top + Inner-1: Series on Top and Inner-1, the fingers go around the Top turns |

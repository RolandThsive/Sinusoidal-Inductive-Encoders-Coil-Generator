# Tooltip inventory

Every help box (tooltip) of the web tool, numbered: where it shows and its first sentence. This file is written
by `WebGUI/tools/build_tips.py` from the words in `WebGUI/tools/tips_words.py`, together with `WebGUI/tips.json`,
which the page reads. Change the words there, not here.

181 tips: 116 settings, 59 buttons, switches and other controls, and the 6 TX layout cards. 15 settings show a picture.

A tip is shown in one layout: where the setting is, its name and unit, its name in the file, the first sentence,
the choices (the file's one marked), facts, the formula, a note, the keys, a picture, the value in the file and a
link to the reference page. The page fills in what it knows itself (the value, the unit, the place); the words
below are the part that is written by hand. A tip that changes with the page's state (a hidden layer, a locked
switch, a run that is out of date) is listed once per state.

## Settings

Each setting's tip opens from the (i) beside its name, in Basic and in Advanced. The settings the page does not
list (the folder and file names of a run, and `GENERATOR_MODE`, which is the Strict switch) have no tip.

| No. | Name in the file | Parameter files | First sentence | Picture |
|---|---|---|---|---|
| 1 | `PCB_LAYERS` | Single · Board; Dual · Board | Number of copper layers of the stator board. |  |
| 2 | `VIA_DIAMETER_MM` | Single · Board; Dual · Board; Dual · RX1; Dual · RX2 | Outer diameter of every via's copper ring. |  |
| 3 | `VIA_DRILL_MM` | Single · Board; Dual · Board; Dual · RX1; Dual · RX2 | Drill hole diameter of every via. |  |
| 4 | `VIA_TYPE` | Single · Board; Dual · Board; Dual · RX1; Dual · RX2 | What every via the generator places is. |  |
| 5 | `MIN_CLEARANCE_MM` | Single · Board; Dual · Board; Dual · RX1; Dual · RX2 | Smallest copper-to-copper gap the generator keeps between traces and vias. |  |
| 6 | `INNER_EDGE_INSET_MM` | Single · Board; Dual · Board | Gap between the centre hole and the start of the RX band. |  |
| 7 | `INNER_EDGE_RADIUS_MM` | Single · Board; Dual · Board | Radius of the centre hole, R_hole. |  |
| 8 | `OUTER_EDGE_OFFSET_MM` | Single · Board; Dual · Board | Minimum gap from the end of the RX band to the outer board edge. |  |
| 9 | `OUTER_EDGE_RADIUS_MM` | Single · Board; Dual · Board | Radius of the outer board edge, R_edge. |  |
| 10 | `OUTER_EDGE_TAIL_MARGIN_MM` | Single · Board; Dual · Board | Copper-free margin between the outermost copper and the outer board edge. |  |
| 11 | `EDGE_LINE_WIDTH_MM` | Single · Board; Dual · Board | Line width of the board outline (Edge.Cuts) in the KiCad file. |  |
| 12 | `CENTER_X_MM` | Single · Board; Dual · Board | Where the sensor's axis lies on the KiCad page: the distance from the page's left edge. |  |
| 13 | `CENTER_Y_MM` | Single · Board; Dual · Board | Where the sensor's axis lies on the KiCad page: the distance from the page's top edge. |  |
| 14 | `PAGE_SIZE_MM` | Single · Board; Dual · Board | Size of the KiCad "User" page the boards are drawn on: its width and its height. |  |
| 15 | `AIR_GAP_MM` | Single · Board; Dual · Board | Distance from the stator's top copper to the rotor copper. |  |
| 16 | `PCB_THICKNESS_MM` | Single · Board; Dual · Board | Thickness of the stator board. |  |
| 17 | `EXCITATION_FREQ_HZ` | Single · Board; Dual · TX1; Dual · TX2 | Planned TX drive frequency with the rotor in place. |  |
| 18 | `COPPER_THICKNESS_UM` | Single · Board; Dual · Board | Thickness of the stator copper. |  |
| 19 | `COPPER_CONDUCTIVITY_S_M` | Single · Board; Dual · Board | Conductivity of the copper. |  |
| 20 | `TX_AC_RESISTANCE_FACTOR` | Single · Board; Dual · Board; Dual · TX1; Dual · TX2 | How far skin and proximity effects may raise the TX resistance above its DC value. |  |
| 21 | `STACKUP_PREPREG_MM` | Single · Board; Dual · Board | 4-layer stator: distance from an outer copper layer to its inner neighbour. |  |
| 22 | `TANK_CAP_SERIES` | Single · Board; Dual · Board; Dual · IC1; Dual · IC2 | Standard capacitor values the estimate suggests for the tank. |  |
| 23 | `LOOPS` | Single · RX; Dual · RX1; Dual · RX2 | Sine periods per full turn. | `loops.webp` |
| 24 | `INSIDE_RADIUS_MM` | Single · RX; Dual · RX1; Dual · RX2 | Inner radius of the RX band, R_in. | `band.webp` |
| 25 | `OUTSIDE_RADIUS_MM` | Single · RX; Dual · RX1; Dual · RX2 | Outer radius of the RX band, R_out. | `band.webp` |
| 26 | `RX_R_BASE_MM` | Single · RX; Dual · RX1; Dual · RX2 | Centre radius of the RX band, R_base. | `band.webp` |
| 27 | `RX_A_MM` | Single · RX; Dual · RX1; Dual · RX2 | Swing A: half the width of the RX band. | `band.webp` |
| 28 | `RX_TRACE_WIDTH_MM` | Single · RX; Dual · RX1; Dual · RX2 | Trace width of the RX coils. |  |
| 29 | `RX_NET_PHASE_0_2` | Single · RX; Dual · RX1; Dual · RX2 | KiCad net name of the sine coil. |  |
| 30 | `RX_NET_PHASE_1_3` | Single · RX; Dual · RX1; Dual · RX2 | KiCad net name of the cosine coil. |  |
| 31 | `RX_PROFILE` | Single · RX; Dual · RX1; Dual · RX2 | Shape of the RX curves. | `profile.webp` |
| 32 | `STEPS_PER_LOOP` | Single · RX; Dual · RX1; Dual · RX2 | Points per loop of the RX curves. |  |
| 33 | `RX_CHORD_TOLERANCE_MM` | Single · RX; Dual · RX1; Dual · RX2 | Largest allowed gap between the true curve and the straight segment between two points. |  |
| 34 | `RX_SUBCOILS` | Single · RX; Dual · RX1; Dual · RX2 | Splits each RX coil into copies, shifted by the split angle. | `subcoils.webp` |
| 35 | `RX_SUBCOIL_SPLIT_ELEC_DEG` | Single · RX; Dual · RX1; Dual · RX2 | Electrical angle between the sub-coils. |  |
| 36 | `RX_LAYER_A` | Single · RX; Dual · RX1; Dual · RX2 | 4-layer boards: the layer carrying the RX rising edges. |  |
| 37 | `RX_LAYER_B` | Single · RX; Dual · RX1; Dual · RX2 | 4-layer boards: the layer carrying the RX falling edges. |  |
| 38 | `RX_RISING_EDGE_LAYER` | Single · RX; Dual · RX1; Dual · RX2 | 2-layer boards: the side that carries the RX rising edges. |  |
| 39 | `RX_VIA_ELECTRICAL_DEG` | Single · RX; Dual · RX1; Dual · RX2 | Where the RX coils change layer near each lobe tip, as an electrical angle. |  |
| 40 | `RX_TABS` | Single · RX; Dual · RX1; Dual · RX2 | Fingers that bring the RX coils out past the TX ring, so you can connect to them. | `fingers.webp` |
| 41 | `RX_TAB_LENGTH_MM` | Single · RX; Dual · RX1; Dual · RX2 | How far each finger reaches beyond the RX band. |  |
| 42 | `RX_TAB_WIDTH_MM` | Single · RX; Dual · RX1; Dual · RX2 | Spacing between the two legs of a finger. |  |
| 43 | `RX_TAB_LAYER` | Single · RX; Dual · RX1; Dual · RX2 | Layer the fingers run on. |  |
| 44 | `TX_NET` | Single · TX; Dual · TX1; Dual · TX2 | KiCad net name of the TX coil. |  |
| 45 | `TX_TURNS` | Single · TX; Dual · TX1; Dual · TX2 | Number of complete TX turns on each TX layer. |  |
| 46 | `TX_OFFSET_MM` | Single · TX; Dual · TX1; Dual · TX2 | Distance from the outer edge of the RX band to the first TX turn. |  |
| 47 | `TX_PITCH_MM` | Single · TX; Dual · TX1; Dual · TX2 | Centre-to-centre spacing between neighbouring TX turns. |  |
| 48 | `TX_TRACE_WIDTH_MM` | Single · TX; Dual · TX1; Dual · TX2 | Trace width of the TX turns. |  |
| 49 | `TX_STEPS` | Single · TX; Dual · TX1; Dual · TX2 | Points per TX turn. |  |
| 50 | `TX_CHORD_TOLERANCE_MM` | Single · TX; Dual · TX1; Dual · TX2 | Largest allowed gap between the true curve and the straight segment between two points. |  |
| 51 | `TX_TAIL_EXTRA_MM` | Single · TX; Dual · TX1; Dual · TX2 | Length of the radial tail that brings the TX connection out past the turns. |  |
| 52 | `TX_SHAPE` | Single · TX; Dual · TX1; Dual · TX2 | How the TX turns are joined into one coil. | `tx_shape.webp` |
| 53 | `TX_INSIDE_VIA_DISTANCE_MM` | Single · TX; Dual · TX1; Dual · TX2 | Moves the TX terminal via this far towards the centre, so it clears the next turn. |  |
| 54 | `TX_STEPPED_ANGLE_DEG` | Single · TX; Dual · TX1; Dual · TX2 | Slope of the steps between TX turns, measured from the turn. |  |
| 55 | `TX_STEPPED_ARC_RADIUS_MM` | Single · TX; Dual · TX1; Dual · TX2 | Stepped Arc only: radius of the innermost arc around the terminal via. |  |
| 56 | `TX_WIRING` | Single · TX; Dual · TX1; Dual · TX2 | How many layers carry TX turns, and how they are joined. | `tx_wiring.webp` |
| 57 | `TX_LAYER_A` | Single · TX; Dual · TX1; Dual · TX2 | The first layer carrying the TX turns. |  |
| 58 | `TX_LAYER_B` | Single · TX; Dual · TX1; Dual · TX2 | The second layer carrying the TX turns. |  |
| 59 | `TX_SERIES_UNDERPASS_LAYER` | Single · TX; Dual · TX1; Dual · TX2 | Layer of the TX inner tail and of the brackets that carry the turns around the fingers. |  |
| 60 | `TX_PARALLEL_BREAK_STYLE` | Single · TX; Dual · TX1; Dual · TX2 | Parallel TX only: how the turns make way for a finger. |  |
| 61 | `ROTOR_MODE` | Single · Rotor; Dual · Board | Whether the rotor is sized from the stator or set by you. |  |
| 62 | `ROTOR_AUTO_DUTY` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Share of each period that is copper. |  |
| 63 | `ROTOR_AUTO_START_ANGLE_DEG` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Mechanical angle of the first sector edge. |  |
| 64 | `ROTOR_AUTO_EXTENSION_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | How far the rotor copper reaches past the RX band, on both sides. | `rotor_reach.webp` |
| 65 | `ROTOR_AUTO_EXTENSION_INNER_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | How far the rotor copper reaches past the RX band at the inner edge only. |  |
| 66 | `ROTOR_AUTO_EXTENSION_OUTER_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | How far the rotor copper reaches past the RX band at the outer edge only. |  |
| 67 | `ROTOR_AUTO_TX_CLEARANCE_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | The rotor copper stops this far inside the TX ring. |  |
| 68 | `ROTOR_AUTO_COVER_TX` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Whether the rotor copper runs over the TX turns. | `rotor_reach.webp` |
| 69 | `ROTOR_AUTO_TX_OVERHANG_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | How far the rotor copper runs past the outermost TX turn. |  |
| 70 | `ROTOR_AUTO_EDGE_CLEARANCE_MM` | Single · Rotor; Dual · Board | Gap kept between the rotor copper and the rotor's hole and outer edge. |  |
| 71 | `ROTOR_AUTO_COPPER_LAYERS` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Rotor layers carrying the copper sectors. |  |
| 72 | `ROTOR_CUSTOM_SECTORS` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Number of copper sectors around the rotor. |  |
| 73 | `ROTOR_CUSTOM_DUTY` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Share of each sector period that is copper. |  |
| 74 | `ROTOR_CUSTOM_START_ANGLE_DEG` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Mechanical angle where the first sector starts. |  |
| 75 | `ROTOR_CUSTOM_INNER_RADIUS_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Inner radius of the copper sectors. |  |
| 76 | `ROTOR_CUSTOM_OUTER_RADIUS_MM` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Outer radius of the copper sectors. |  |
| 77 | `ROTOR_CUSTOM_COPPER_LAYERS` | Single · Rotor; Dual · Rotor1; Dual · Rotor2 | Rotor layers carrying the copper sectors. |  |
| 78 | `ROTOR_CUSTOM_OUTLINE_RADIUS_MM` | Single · Rotor; Dual · Board | Radius of the rotor's outer board edge. |  |
| 79 | `ROTOR_CUSTOM_BORE_RADIUS_MM` | Single · Rotor; Dual · Board | Radius of the rotor's centre hole. |  |
| 80 | `ROTOR_PCB_THICKNESS_MM` | Single · Rotor; Dual · Board | Thickness of the rotor board, written into the KiCad file. |  |
| 81 | `ROTOR_ARC_STEPS_PER_SECTOR` | Single · Rotor; Dual · Board | Points per curved edge of a rotor sector. |  |
| 82 | `ROTOR_CHORD_TOLERANCE_MM` | Single · Rotor; Dual · Board | Largest allowed gap between the true curve and the straight segment between two points. |  |
| 83 | `ROTOR_SOLDER_MASK_EXPANSION_MM` | Single · Rotor; Dual · Board | Solder mask over the rotor copper. |  |
| 84 | `IC_NAME` | Single · IC; Dual · IC1; Dual · IC2 | Name of the receiver IC, shown in the electrical estimate. |  |
| 85 | `IC_OSC_MIN_MHZ` | Single · IC; Dual · IC1; Dual · IC2 | Lowest LC oscillator frequency of the receiver IC. |  |
| 86 | `IC_OSC_MAX_MHZ` | Single · IC; Dual · IC1; Dual · IC2 | Highest LC oscillator frequency of the receiver IC. |  |
| 87 | `IC_MIN_RP_OHM` | Single · IC; Dual · IC1; Dual · IC2 | Smallest parallel (loss) resistance of the TX tank that the oscillator can drive. |  |
| 88 | `IC_SPLIT_TANK_CAPS` | Single · IC; Dual · IC1; Dual · IC2 | How the tank capacitance C is placed. |  |
| 89 | `SILKSCREEN_SUGGESTION` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Whether the stator gets the silkscreen marks of the lead-cutting suggestion. |  |
| 90 | `SILKSCREEN_SIDES` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | The board sides that get the marks. |  |
| 91 | `SILKSCREEN_COLOR` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Colour of every mark: lines, boxes, dots and the lettering. |  |
| 92 | `SILKSCREEN_LABELS` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Whether the lead names are written next to the via sites. |  |
| 93 | `SILKSCREEN_DOT_ON_ALL_VIAS` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Which vias get a dot. |  |
| 94 | `SILKSCREEN_LINE_WIDTH_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Line width of the boxes, lines and dot outlines. |  |
| 95 | `SILKSCREEN_TEXT_SIZE_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Height of a capital letter of the lead names. |  |
| 96 | `SILKSCREEN_TEXT_STROKE_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Line width of the lettering. |  |
| 97 | `SILKSCREEN_DOT_RADIUS_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Radius of the filled dot at a via site. |  |
| 98 | `SILKSCREEN_BOX_MARGIN_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | How far the dashed box around an RX break reaches past its two via sites. |  |
| 99 | `SILKSCREEN_BREAK_VIA_GAP_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Distance between the two vias of an RX break, centre to centre along the trace. | `break.webp` |
| 100 | `SILKSCREEN_SEARCH_SPAN_DEG` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | The break is looked for on the coil within this many degrees of the TX terminal. |  |
| 101 | `SILKSCREEN_BREAK_SEPARATION_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Least distance between the two breaks and the TX end, centre to centre. |  |
| 102 | `SILKSCREEN_BREAK_LAYERS` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | The coil layers tried for the break, in this order. |  |
| 103 | `SILKSCREEN_VIA_EDGE_CLEARANCE_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | Distance a via of the suggestion keeps from the bore and the outline. |  |
| 104 | `SILKSCREEN_TX_SITE_REACH_MM` | Single · SilkScreenSuggestion; Dual · SilkScreenSuggestion | How far from the stacked TX end its two via sites are looked for. |  |
| 105 | `TRACK_GAP_MM` | Dual · Board | The copper-free ring between the two coil sets. | `dual_layout.webp` |
| 106 | `BAND_SPLIT` | Dual · Board | Set 1's share of the free radial width. | `dual_layout.webp` |
| 107 | `LAYOUT_TOLERANCE_MM` | Dual · Board | How far the built copper may differ from the layout formulas before the run warns. |  |
| 108 | `TERMINAL_1_DEG` | Dual · Board | Angle at which the TX ends of set 1, the inner set, end up. |  |
| 109 | `TERMINAL_2_DEG` | Dual · Board | Angle at which the TX ends of set 2, the outer set, end up. |  |
| 110 | `TX_FREQ_SEPARATION_MIN` | Dual · Board | Least difference between the two TX frequencies, as a share of the lower one. |  |
| 111 | `TX_FREQ_RATIO_MAX_ORDER` | Dual · Board | The two TX frequencies must not sit on a ratio p:q of whole numbers up to this. |  |
| 112 | `TX_FREQ_RATIO_TOLERANCE` | Dual · Board | How near a whole-number ratio the two TX frequencies may come before the run warns. |  |
| 113 | `ROTOR_START_ANGLE_ZERO` | Dual · Board | Where each ring's start angle is measured from. |  |
| 114 | `ROTOR_TRACK_GAP_MM` | Dual · Board | The bare ring that must stay between rotor ring 1 and rotor ring 2. |  |
| 115 | `ROTOR_1_TO_RX2_MM` | Dual · Board | Least distance from the outer radius of rotor ring 1 to the innermost RX2 copper. |  |
| 116 | `ROTOR_2_TO_RX1_MM` | Dual · Board | Least distance from the inner radius of rotor ring 2 to the outermost RX1 copper. |  |

## Buttons, switches and other controls

| No. | Tip id | First sentence | Keys |
|---|---|---|---|
| 117 | `gen-menu` | Which generator the page runs. |  |
| 118 | `gen-single` | The Single Coil Set Generator: one sine and cosine RX pair with one TX coil. |  |
| 119 | `gen-dual` | The Dual Coil Set Generator: two coil sets on one board, an inner and an outer one, each with its own rotor ring (a coarse and a fine track). |  |
| 120 | `mode-basic` | The main settings of each category, with sliders. |  |
| 121 | `mode-advanced` | Every setting of every parameter file, as the desktop generator has them. |  |
| 122 | `btn-help` | Open the quick guide to choosing the parameters, in a new tab. |  |
| 123 | `btn-import` | Load a design from files. |  |
| 124 | `btn-export` | Download the parameter files with your settings, ready for the desktop generator. |  |
| 125 | `btn-share` | Copy a link that opens this page with your settings. |  |
| 126 | `nav-back` | Back to the page you came from. |  |
| 127 | `nav-home` | The blog's front page. |  |
| 128 | `find` | Type part of a setting's name, its name in the file, or a word of its help. |  |
| 129 | `strict` | Every warning about the finished boards stops the run, and nothing is written. |  |
| 130 | `btn-reset` | Put every setting of this generator back to its published value. |  |
| 131 | `btn-check` | Run only the generator's checks of the settings. |  |
| 132 | `btn-generate` | Run the generator with these settings. | Ctrl + Enter |
| 133 | `view-stator` | The stator board alone. |  |
| 134 | `view-rotor` | The rotor board alone. |  |
| 135 | `view-overlay` | The rotor's copper drawn over the stator, at the angle of the Rotor Angle slider. |  |
| 136 | `view-pictures` | The two pictures the generator draws of the board. |  |
| 137 | `btn-fullscreen` | Show the preview full screen. | Esc (leaves it) |
| 138 | `btn-fullscreen-on` | Leave full screen. | Esc |
| 139 | `btn-fit` | Fit the board to the preview. | 0 (or a double click) |
| 140 | `btn-measure` | Measure a distance: click two points on the board. | S (locks the line, Z removes the last one) |
| 141 | `readout` | The position of the mouse on the board, from the board centre. |  |
| 142 | `rotor-angle` | Turn the rotor over the stator. |  |
| 143 | `show-info` | Also list the generator's notes, not only its warnings and errors. |  |
| 144 | `btn-runtext` | Everything the generator printed in this run, as on the desktop. |  |
| 145 | `btn-files` | Every file of this run, to download one by one. |  |
| 146 | `btn-cancel` | Stop this run. |  |
| 147 | `btn-download` | Download this run as one zip: the same folder the desktop generator writes. |  |
| 148 | `btn-download-stale` | The settings changed: press Generate first. |  |
| 149 | `btn-dl-stator` | Download only the stator board of this run, ready to open in KiCad. |  |
| 150 | `btn-dl-rotor` | Download only the rotor board of this run, ready to open in KiCad. |  |
| 151 | `reset-one` | Back to the starting value. |  |
| 152 | `param-link` | Show this setting. |  |
| 153 | `picture-open` | Open this picture in a new tab. |  |
| 154 | `origin` | The board centre (origin). |  |
| 155 | `origin-off` | Show the board centre (origin). |  |
| 156 | `vias` | Show or hide the vias. |  |
| 157 | `vias-off` | Show the vias. |  |
| 158 | `layer` | Hover to highlight the {layer} copper ({cu}), click to hide it. |  |
| 159 | `layer-off` | Show the {layer} copper ({cu}). |  |
| 160 | `layer-missing` | This board has no copper on the {layer} layer ({cu}). |  |
| 161 | `silk` | Hide the silkscreen suggestion on the {side} side ({cu}). |  |
| 162 | `silk-off` | Show the silkscreen suggestion on the {side} side ({cu}). |  |
| 163 | `silk-missing` | This board has no silkscreen marks on its {side} side ({cu}). |  |
| 164 | `net` | Hover to highlight {what}, click to hide it. |  |
| 165 | `net-off` | Show {what}. |  |
| 166 | `tab` | {what} of {file}. |  |
| 167 | `set` | The {cat} settings of coil set {set}, the {which} one. |  |
| 168 | `rotor-fold` | Show or hide the {kind} rotor settings. |  |
| 169 | `none` | {line} |  |
| 170 | `none-locked` | Locked: the RX band is set by {pair}. |  |
| 171 | `result-range` | The unique angle range: one electrical period of the RX pattern. |  |
| 172 | `result-R` | Resistance of the TX coil at DC. |  |
| 173 | `result-L` | Inductance of the TX coil without the rotor. |  |
| 174 | `result-C` | The tank capacitors for the TX frequency f. |  |
| 175 | `result-f` | The TX frequency the tank capacitors are sized for. |  |

In these texts a word in braces, such as {layer} or {name}, is filled in by the page.

## TX layout cards

| No. | Card id | First sentence |
|---|---|---|
| 176 | `2-bottom` | The original, proven layout: all TX turns on the bottom layer. |
| 177 | `2-top` | All TX turns on the top layer, next to the rotor: more signal in the model. |
| 178 | `2-series` | TX turns on both layers, in series. The fingers go around the Top turns. |
| 179 | `4-bottom` | All TX turns on the bottom layer, with the RX on Top and Inner-1. |
| 180 | `4-renesas` | TX turns on Top and Inner-2, in series: the Renesas IPS2200 reference. |
| 181 | `4-inner1` | TX turns on Top and Inner-1, in series. The fingers go around the Top turns. |

Under every card: Only these change. Every other setting keeps its value.

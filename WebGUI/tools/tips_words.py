"""
tips_words.py  -  the words of every help box (tooltip) of the web tool.  build_tips.py writes them into
WebGUI/tips.json, one tip per line; the page never reads this file.

A tip is shown in one layout (WebGUI/docs/tooltips/Inventory.md).  The page itself adds what it knows of a setting:
the file and group (the small line on top), the name as on the page with its unit, the name in the file, the range,
"In the file: value" and the link to the wiki.  Here are only the words:

    lead      one plain sentence: what the setting does (always present)
    choices   {value: one line on its effect}; "None", "auto" and "number" name those states of a setting
    facts     [[label, value], ...]: typical values, sizes, the meaning of a special number
    formula   [line, ...]: shown in the mono font
    note      the one caveat worth knowing
    picture   {file, caption}: a file of WebGUI/docs/tooltips/pictures

The words are the generators' own: each tip shortens and orders the comment of its setting in the parameter file
(and the text the page showed before); nothing is claimed that the file does not say.
"""

ROOM = "Room = max(Offset, TX Offset + TX Turns × TX Pitch + Tail Extra + Tail Margin, Finger Reach + RX Trace / 2 + Tail Margin)"
CHORD = "Largest allowed gap between the true curve and the straight segment between two points."
CHORD_NOTE = "Used only when Steps is Auto: smaller gives more points and smoother copper."

PARAMS = {
    # ------------------------------------------------------------------------------------------------ Board
    "PCB_LAYERS": {
        "lead": "Number of copper layers of the stator board.",
        "choices": {"2": "Top and Bottom.", "4": "Adds Inner-1 and Inner-2. You choose which layers the RX and TX coils use."},
        "note": "Keep unused layers free of copper under the coils: a copper plane weakens the signal."},
    "VIA_DIAMETER_MM": {"lead": "Outer diameter of every via's copper ring."},
    "VIA_DRILL_MM": {"lead": "Drill hole diameter of every via.", "note": "Must be smaller than the via diameter."},
    "VIA_TYPE": {
        "lead": "What every via the generator places is.",
        "choices": {"through": "A plated hole through the whole board, on 2 and on 4 layers.",
                    "blind": "4-layer boards only. Each via joins just the two copper layers it connects."},
        "note": "Common fabs laser-drill blind vias only between an outer layer and its neighbour, at most about 0.15 mm wide: "
                "set the via drill and diameter to such sizes. The clearance checks treat every via as a through via."},
    "MIN_CLEARANCE_MM": {"lead": "Smallest copper-to-copper gap the generator keeps between traces and vias.",
                         "note": "Match it to your PCB maker's rule."},
    "INNER_EDGE_INSET_MM": {
        "lead": "Gap between the centre hole and the start of the RX band.",
        "formula": ["R_hole = R_in − Inset"],
        "note": "Used when Board Inner Radius is None, and as the minimum gap when it is set."},
    "INNER_EDGE_RADIUS_MM": {
        "lead": "Radius of the centre hole, R_hole.",
        "choices": {"None": "Calculated from the RX band: R_hole = R_in − Inset.",
                    "number": "The hole is exactly this. It must leave the inset: R_hole ≤ R_in − Inset."},
        "note": "If the whole RX band is None, the band starts from the hole: R_in = R_hole + Inset."},
    "OUTER_EDGE_OFFSET_MM": {
        "lead": "Minimum gap from the end of the RX band to the outer board edge.",
        "formula": [ROOM],
        "note": "It is the first term of the room the outer edge needs. The finger term counts only with fingers."},
    "OUTER_EDGE_RADIUS_MM": {
        "lead": "Radius of the outer board edge, R_edge.",
        "choices": {"None": "Calculated: R_edge = R_out + Room.",
                    "number": "The edge is exactly this. It must leave that room: R_edge ≥ R_out + Room."},
        "formula": [ROOM],
        "note": "If the whole RX band is None, the band ends from the edge: R_out = R_edge − Room."},
    "OUTER_EDGE_TAIL_MARGIN_MM": {
        "lead": "Copper-free margin between the outermost copper and the outer board edge.",
        "note": "The outermost copper is the TX tail or the finger tips. Part of the room the edge needs (Board Outer Radius)."},
    "EDGE_LINE_WIDTH_MM": {"lead": "Line width of the board outline (Edge.Cuts) in the KiCad file.",
                           "note": "Does not change the board size."},
    "AIR_GAP_MM": {"lead": "Distance from the stator's top copper to the rotor copper."},
    "PCB_THICKNESS_MM": {"lead": "Thickness of the stator board.",
                         "note": "Used in the field model and written to the KiCad file."},
    "EXCITATION_FREQ_HZ": {"lead": "Planned TX drive frequency with the rotor in place.",
                           "facts": [["Example", "3.5 MHz = 3500000"]],
                           "note": "Used for the copper skin depth in the rotor summary."},
    "COPPER_THICKNESS_UM": {"lead": "Thickness of the stator copper.",
                            "facts": [["1 oz copper", "35 µm"]],
                            "note": "Used for the TX resistance and Q of the electrical estimate."},
    "COPPER_CONDUCTIVITY_S_M": {
        "lead": "Conductivity of the copper.",
        "facts": [["Annealed copper at 20 °C", "5.8e7 S/m"]],
        "note": "It drops about 0.39 % per K above 20 °C. Used for the TX resistance, and for the rotor's skin depth "
                "and screening in the rotor summary."},
    "TX_AC_RESISTANCE_FACTOR": {
        "lead": "How far skin and proximity effects may raise the TX resistance above its DC value.",
        "note": "The estimate allows for up to this times the DC value: Q, tank resistance and the IC check use the worst case."},
    "STACKUP_PREPREG_MM": {
        "lead": "4-layer stator: distance from an outer copper layer to its inner neighbour.",
        "note": "It gives the depth of the inner layers for the TX inductance. On a board thinner than twice this, "
                "a third of the board thickness is used."},
    "TANK_CAP_SERIES": {
        "lead": "Standard capacitor values the estimate suggests for the tank.",
        "choices": {"E6": "6 values per decade.", "E12": "12 values per decade.", "E24": "24 values per decade."}},

    # --------------------------------------------------------------------------------------------------- RX
    "LOOPS": {
        "lead": "Sine periods per full turn.",
        "facts": [["Unique range", "360° / Loops"]],
        "note": "1 gives a true 0 to 360° reading; more loops give finer resolution. The rotor gets the same number of metal sectors.",
        "picture": {"file": "loops.webp", "caption": "1 loop and 4 loops on the same band"}},
    "INSIDE_RADIUS_MM": {
        "lead": "Inner radius of the RX band, R_in.",
        "choices": {"number": "Set together with RX Outside Radius.",
                    "None": "From R Base and Swing A: R_in = R_base − A. If those are None too, from the board: R_in = R_hole + Inset."},
        "note": "Locked while R Base and Swing A have numbers.",
        "picture": {"file": "band.webp", "caption": "The RX band between R_in and R_out, with R_base and the swing A"}},
    "OUTSIDE_RADIUS_MM": {
        "lead": "Outer radius of the RX band, R_out.",
        "choices": {"number": "Set together with RX Inside Radius.",
                    "None": "From R Base and Swing A: R_out = R_base + A. If those are None too, from the board: R_out = R_edge − Room."},
        "note": "Locked while R Base and Swing A have numbers. Room is explained at Board Outer Radius.",
        "picture": {"file": "band.webp", "caption": "The RX band between R_in and R_out, with R_base and the swing A"}},
    "RX_R_BASE_MM": {
        "lead": "Centre radius of the RX band, R_base.",
        "choices": {"number": "Set together with Swing A: R_in = R_base − A and R_out = R_base + A.",
                    "None": "The band comes from the RX radii, or from the board edges if those are None too."},
        "note": "Locked while the RX radii have numbers.",
        "picture": {"file": "band.webp", "caption": "The RX band between R_in and R_out, with R_base and the swing A"}},
    "RX_A_MM": {
        "lead": "Swing A: half the width of the RX band.",
        "formula": ["A = (R_out − R_in) / 2"],
        "choices": {"number": "Set together with R Base.",
                    "None": "The band comes from the RX radii, or from the board edges if those are None too."},
        "note": "Locked while the RX radii have numbers.",
        "picture": {"file": "band.webp", "caption": "The RX band between R_in and R_out, with R_base and the swing A"}},
    "RX_TRACE_WIDTH_MM": {"lead": "Trace width of the RX coils."},
    "RX_NET_PHASE_0_2": {"lead": "KiCad net name of the sine coil."},
    "RX_NET_PHASE_1_3": {"lead": "KiCad net name of the cosine coil."},
    "RX_PROFILE": {
        "lead": "Shape of the RX curves.",
        "choices": {"equal_area": "r² = (R_in² + R_out²) / 2 + (R_out² − R_in²) / 2 · sin φ",
                    "cosine_r": "r = R_base + A · sin φ. The shape of the Renesas IPS2200 reference."},
        "note": "φ is the electrical angle.",
        "picture": {"file": "profile.webp", "caption": "Equal Area and Cosine R on the same band"}},
    "STEPS_PER_LOOP": {
        "lead": "Points per loop of the RX curves.",
        "choices": {"auto": "The fewest that keep the chord error within RX Chord Tolerance: a multiple of 8, up to 1024.",
                    "number": "Used exactly: a multiple of 8, from 48 to 4096."}},
    "RX_CHORD_TOLERANCE_MM": {"lead": CHORD, "facts": [["Lowest", "0.001 mm (1 micron)"]], "note": CHORD_NOTE},
    "RX_SUBCOILS": {
        "lead": "Splits each RX coil into copies, shifted by the split angle.",
        "choices": {"1": "One coil, not split.", "2": "Two copies of each coil.", "3": "Three copies of each coil."},
        "note": "More sub-coils give more signal and cancel some harmonics, but need more room for the vias.",
        "picture": {"file": "subcoils.webp", "caption": "One coil, and the same coil split in two"}},
    "RX_SUBCOIL_SPLIT_ELEC_DEG": {
        "lead": "Electrical angle between the sub-coils.",
        "facts": [["45°", "the roomiest"], ["60°", "removes the 3rd harmonic"], ["36°", "removes the 5th harmonic"]],
        "note": "Only used with 2 or 3 sub-coils."},
    "RX_LAYER_A": {"lead": "4-layer boards: the layer carrying the RX rising edges.",
                   "note": "Must differ from RX Layer B. Top + Inner-1 is the usual choice."},
    "RX_LAYER_B": {"lead": "4-layer boards: the layer carrying the RX falling edges.",
                   "note": "Must differ from RX Layer A."},
    "RX_RISING_EDGE_LAYER": {
        "lead": "2-layer boards: the side that carries the RX rising edges.",
        "choices": {"F.Cu": "Rising edges on Top, falling edges on Bottom.",
                    "B.Cu": "Rising edges on Bottom, falling edges on Top."}},
    "RX_VIA_ELECTRICAL_DEG": {
        "lead": "Where the RX coils change layer near each lobe tip, as an electrical angle.",
        "facts": [["Exactly on the tip", "90°"], ["Accepted", "50° to 130°"],
                  ["Keeps the clearance on the default board", "about 58° to 122°"]],
        "note": "Stay near 90: further away the vias come close to the neighbouring curves. A value too far out for "
                "the resolution is moved inside, with a warning."},
    "RX_TABS": {
        "lead": "Fingers that bring the RX coils out past the TX ring, so you can connect to them.",
        "choices": {"all": "A finger at every lobe tip.",
                    "single": "Two fixed fingers: the sin+ tip of loop 1 and the cos+ tip after it.",
                    "none": "No fingers."},
        "picture": {"file": "fingers.webp", "caption": "All, Single and None"}},
    "RX_TAB_LENGTH_MM": {
        "lead": "How far each finger reaches beyond the RX band.",
        "note": "Exactly this: it is never lengthened. If it is too short to clear the TX turns, the check names the "
                "length needed. A longer TX pitch needs longer fingers, and a spiral TX needs them one pitch longer."},
    "RX_TAB_WIDTH_MM": {"lead": "Spacing between the two legs of a finger.",
                        "note": "Narrower disturbs the signal less. Keep at least about 0.6 mm for etching."},
    "RX_TAB_LAYER": {
        "lead": "Layer the fingers run on.",
        "choices": {"auto": "The top-most RX layer without TX turns."},
        "note": "If the fingers share a layer with TX turns, the TX turns go around them."},

    # --------------------------------------------------------------------------------------------------- TX
    "TX_NET": {"lead": "KiCad net name of the TX coil."},
    "TX_TURNS": {"lead": "Number of complete TX turns on each TX layer."},
    "TX_OFFSET_MM": {"lead": "Distance from the outer edge of the RX band to the first TX turn."},
    "TX_PITCH_MM": {"lead": "Centre-to-centre spacing between neighbouring TX turns."},
    "TX_TRACE_WIDTH_MM": {"lead": "Trace width of the TX turns."},
    "TX_STEPS": {
        "lead": "Points per TX turn.",
        "choices": {"auto": "The fewest that keep the chord error within TX Chord Tolerance: a multiple of 8, at least 48.",
                    "number": "Used exactly: from 12 to 20000."}},
    "TX_CHORD_TOLERANCE_MM": {"lead": CHORD, "facts": [["Lowest", "0.001 mm (1 micron)"]], "note": CHORD_NOTE},
    "TX_TAIL_EXTRA_MM": {"lead": "Length of the radial tail that brings the TX connection out past the turns."},
    "TX_SHAPE": {
        "lead": "How the TX turns are joined into one coil.",
        "choices": {"stepped_diagonal": "Circles joined by short straight steps.",
                    "stepped_arc": "Circles joined by arcs centred on the terminal via, as on the Renesas reference boards.",
                    "spiral": "One smooth spiral with an even gap. Better when the pitch is tight."},
        "picture": {"file": "tx_shape.webp", "caption": "Stepped Diagonal, Stepped Arc and Spiral at the TX terminal"}},
    "TX_INSIDE_VIA_DISTANCE_MM": {
        "lead": "Moves the TX terminal via this far towards the centre, so it clears the next turn.",
        "facts": [["0", "the via sits on the trace ends"]],
        "note": "Keep it small enough not to reach the RX coils. Not used by Stepped Arc."},
    "TX_STEPPED_ANGLE_DEG": {
        "lead": "Slope of the steps between TX turns, measured from the turn.",
        "facts": [["90°", "straight out"], ["45°", "diagonal"], ["Smaller", "a longer, gentler slope"]],
        "note": "Only used by Stepped Diagonal."},
    "TX_STEPPED_ARC_RADIUS_MM": {
        "lead": "Stepped Arc only: radius of the innermost arc around the terminal via.",
        "choices": {"auto": "The smallest radius that clears the via, plus 0.02 mm.",
                    "number": "Must be larger than the TX pitch and smaller than the pitch plus the tail extra."},
        "note": "The other arcs follow one pitch apart."},
    "TX_WIRING": {
        "lead": "How many layers carry TX turns, and how they are joined.",
        "choices": {"single": "All turns on TX Layer A.",
                    "series": "Two spirals on Layer A and Layer B joined by a via: twice the turns. Both run the same way, so the fields add.",
                    "parallel": "The same turns on both layers, stitched through vias around the terminal. Put Layer A on Top."},
        "note": "Parallel gives about 6 % more signal than Top alone (still to be verified), and a Q about 1.3 to 1.8 "
                "times higher in the electrical estimate.",
        "picture": {"file": "tx_wiring.webp", "caption": "Single, Series and Parallel, seen in section"}},
    "TX_LAYER_A": {"lead": "The first layer carrying the TX turns."},
    "TX_LAYER_B": {"lead": "The second layer carrying the TX turns.",
                   "note": "Only used when TX Wiring is Series or Parallel."},
    "TX_SERIES_UNDERPASS_LAYER": {
        "lead": "Layer of the TX inner tail and of the brackets that carry the turns around the fingers.",
        "choices": {"auto": "A free layer is picked."}},
    "TX_PARALLEL_BREAK_STYLE": {
        "lead": "Parallel TX only: how the turns make way for a finger.",
        "choices": {"stitched": "The turns on that layer stop at vias, and the other layer carries the current.",
                    "staggered": "The turns go around the finger."}},

    # ------------------------------------------------------------------------------------------------ Rotor
    "ROTOR_MODE": {
        "lead": "Whether the rotor is sized from the stator or set by you.",
        "choices": {"according_to_stator": "Sized from the stator: as many sectors as Loops, radii from the RX band and the TX ring.",
                    "custom": "You set the sectors and the radii yourself."}},
    "ROTOR_AUTO_DUTY": {
        "lead": "Share of each period that is copper.",
        "facts": [["0.5", "half copper, half gap"]],
        "note": "Other values can reduce harmonics. Check on a test rotor."},
    "ROTOR_AUTO_START_ANGLE_DEG": {"lead": "Mechanical angle of the first sector edge."},
    "ROTOR_AUTO_EXTENSION_MM": {
        "lead": "How far the rotor copper reaches past the RX band, on both sides.",
        "choices": {"None": "Equal to the air gap.", "number": "That far. A negative value stops short of the band."},
        "picture": {"file": "rotor_reach.webp", "caption": "The rotor copper over the RX band and the TX turns, in section"}},
    "ROTOR_AUTO_EXTENSION_INNER_MM": {
        "lead": "How far the rotor copper reaches past the RX band at the inner edge only.",
        "choices": {"None": "The value of Extension is used."}},
    "ROTOR_AUTO_EXTENSION_OUTER_MM": {
        "lead": "How far the rotor copper reaches past the RX band at the outer edge only.",
        "choices": {"None": "The value of Extension is used."},
        "note": "Only used when Copper Over The TX Turns is off."},
    "ROTOR_AUTO_TX_CLEARANCE_MM": {
        "lead": "The rotor copper stops this far inside the TX ring.",
        "note": "Only used when Copper Over The TX Turns is off."},
    "ROTOR_AUTO_COVER_TX": {
        "lead": "Whether the rotor copper runs over the TX turns.",
        "choices": {"True": "The copper runs over the TX turns, as in the Renesas designs: about 5 to 8 % more signal.",
                    "False": "The copper ends inside the TX ring."},
        "picture": {"file": "rotor_reach.webp", "caption": "The rotor copper over the RX band and the TX turns, in section"}},
    "ROTOR_AUTO_TX_OVERHANG_MM": {
        "lead": "How far the rotor copper runs past the outermost TX turn.",
        "facts": [["Negative", "the copper ends on top of the turns"]],
        "note": "Only used when Copper Over The TX Turns is on."},
    "ROTOR_AUTO_EDGE_CLEARANCE_MM": {"lead": "Gap kept between the rotor copper and the rotor's hole and outer edge."},
    "ROTOR_AUTO_COPPER_LAYERS": {"lead": "Rotor layers carrying the copper sectors.",
                                 "note": "Mount the copper side facing the stator."},
    "ROTOR_CUSTOM_SECTORS": {"lead": "Number of copper sectors around the rotor."},
    "ROTOR_CUSTOM_DUTY": {"lead": "Share of each sector period that is copper.",
                          "facts": [["0.5", "half copper, half gap"]]},
    "ROTOR_CUSTOM_START_ANGLE_DEG": {"lead": "Mechanical angle where the first sector starts."},
    "ROTOR_CUSTOM_INNER_RADIUS_MM": {"lead": "Inner radius of the copper sectors."},
    "ROTOR_CUSTOM_OUTER_RADIUS_MM": {"lead": "Outer radius of the copper sectors."},
    "ROTOR_CUSTOM_COPPER_LAYERS": {"lead": "Rotor layers carrying the copper sectors.",
                                   "note": "Mount the copper side facing the stator."},
    "ROTOR_CUSTOM_OUTLINE_RADIUS_MM": {"lead": "Radius of the rotor's outer board edge.",
                                       "choices": {"None": "No outline is drawn."}},
    "ROTOR_CUSTOM_BORE_RADIUS_MM": {"lead": "Radius of the rotor's centre hole.",
                                    "choices": {"None": "No hole."}},
    "ROTOR_PCB_THICKNESS_MM": {"lead": "Thickness of the rotor board, written into the KiCad file.",
                               "choices": {"None": "The stator's board thickness."},
                               "note": "It changes nothing in the copper."},
    "ROTOR_ARC_STEPS_PER_SECTOR": {
        "lead": "Points per curved edge of a rotor sector.",
        "choices": {"auto": "The fewest that keep the chord error within Rotor Chord Tolerance: at least 8.",
                    "number": "Used exactly: from 8 to 5000."}},
    "ROTOR_CHORD_TOLERANCE_MM": {
        "lead": CHORD, "facts": [["Lowest", "0.001 mm (1 micron)"]],
        "note": CHORD_NOTE + " The points sit just outside the arc, so the copper is never smaller than asked."},
    "ROTOR_SOLDER_MASK_EXPANSION_MM": {
        "lead": "Solder mask over the rotor copper.",
        "facts": [["Above 0", "bare copper, with the opening this much wider"], ["0", "bare copper, the opening exactly the copper"],
                  ["-1", "the copper stays covered by mask"]]},

    # --------------------------------------------------------------------------------------------------- IC
    "IC_NAME": {"lead": "Name of the receiver IC, shown in the electrical estimate.",
                "choices": {"None": "Shown as \"the receiver IC\"."}},
    "IC_OSC_MIN_MHZ": {"lead": "Lowest LC oscillator frequency of the receiver IC.",
                       "facts": [["IPS2550", "2.0 MHz"]],
                       "choices": {"None": "With the highest frequency also None, the frequency check is skipped."},
                       "note": "The limits never change a board. Take them from the datasheet of your IC and keep a margin."},
    "IC_OSC_MAX_MHZ": {"lead": "Highest LC oscillator frequency of the receiver IC.",
                       "facts": [["IPS2550", "5.6 MHz"]],
                       "choices": {"None": "With the lowest frequency also None, the frequency check is skipped."},
                       "note": "The limits never change a board. Take them from the datasheet of your IC and keep a margin."},
    "IC_MIN_RP_OHM": {"lead": "Smallest parallel (loss) resistance of the TX tank that the oscillator can drive.",
                      "formula": ["R_Peq = L / (C × R_series)"],
                      "facts": [["IPS2550", "250 Ω"]],
                      "choices": {"None": "The resistance check is skipped."}},
    "IC_SPLIT_TANK_CAPS": {
        "lead": "How the tank capacitance C is placed.",
        "choices": {"True": "In two halves: 2 C from TX1 and 2 C from TX2 to ground. Recommended for EMC on the IPS2550.",
                    "False": "One C across the coil."}},

    # ------------------------------------------------------------------------------------------- Silkscreen
    "SILKSCREEN_SUGGESTION": {
        "lead": "Whether the stator gets the silkscreen marks of the lead-cutting suggestion.",
        "choices": {"True": "The marks are drawn.", "False": "The stator is left without silkscreen."}},
    "SILKSCREEN_SIDES": {
        "lead": "The board sides that get the marks.",
        "choices": {"both": "Top and bottom silkscreen.", "top": "Top silkscreen only.", "bottom": "Bottom silkscreen only."}},
    "SILKSCREEN_COLOR": {
        "lead": "Colour of every mark: lines, boxes, dots and the lettering.",
        "facts": [["Written as", "#RRGGBB"]],
        "note": "KiCad keeps the colour with each mark. The fab prints the silkscreen in its own ink regardless."},
    "SILKSCREEN_LABELS": {
        "lead": "Whether the lead names are written next to the via sites.",
        "choices": {"True": "Names such as SIN_1, SIN_2, TX_1 and TX_2 are written.", "False": "No names."}},
    "SILKSCREEN_DOT_ON_ALL_VIAS": {
        "lead": "Which vias get a dot.",
        "choices": {"True": "Every via the generator placed, on both sides.", "False": "Only the via sites of the suggestion."}},
    "SILKSCREEN_LINE_WIDTH_MM": {"lead": "Line width of the boxes, lines and dot outlines."},
    "SILKSCREEN_TEXT_SIZE_MM": {
        "lead": "Height of a capital letter of the lead names.",
        "facts": [["Glyph width", "2/3 of the height"], ["Letter pitch", "5/6 of the height"]],
        "note": "The names are drawn as lines with the generator's own stroke font, each placed where it covers no "
                "other mark, name or via."},
    "SILKSCREEN_TEXT_STROKE_MM": {
        "lead": "Line width of the lettering.",
        "note": "Most fabs print silkscreen lines down to about 0.1 to 0.15 mm and text down to about 0.8 mm height. "
                "Smaller may come out unreadable."},
    "SILKSCREEN_DOT_RADIUS_MM": {"lead": "Radius of the filled dot at a via site."},
    "SILKSCREEN_BOX_MARGIN_MM": {"lead": "How far the dashed box around an RX break reaches past its two via sites."},
    "SILKSCREEN_BREAK_VIA_GAP_MM": {
        "lead": "Distance between the two vias of an RX break, centre to centre along the trace.",
        "note": "The trace between them is what you cut. At least the via diameter plus the minimum clearance.",
        "picture": {"file": "break.webp", "caption": "An RX break: two via sites, the dashed box, and the trace to cut"}},
    "SILKSCREEN_SEARCH_SPAN_DEG": {
        "lead": "The break is looked for on the coil within this many degrees of the TX terminal.",
        "note": "The TX ends are there, so all leads come together. Larger gives more candidates, further from the TX ends."},
    "SILKSCREEN_BREAK_SEPARATION_MM": {
        "lead": "Least distance between the two breaks and the TX end, centre to centre.",
        "note": "It keeps the marks and the lead names from landing on each other."},
    "SILKSCREEN_BREAK_LAYERS": {
        "lead": "The coil layers tried for the break, in this order.",
        "note": "The first layer with a spot that has room is used."},
    "SILKSCREEN_VIA_EDGE_CLEARANCE_MM": {
        "lead": "Distance a via of the suggestion keeps from the bore and the outline.",
        "note": "From copper on every layer it keeps the board's minimum clearance."},
    "SILKSCREEN_TX_SITE_REACH_MM": {"lead": "How far from the stacked TX end its two via sites are looked for."},

    # ---------------------------------------------------------------------------- Dual Coil Set Generator only
    "TRACK_GAP_MM": {
        "lead": "The copper-free ring between the two coil sets.",
        "choices": {"number": "A band the generator places sits exactly this far from the other set. When you give "
                              "both bands, the gap between them must be at least this.",
                    "None": "The same, with the minimum clearance in its place."},
        "note": "It is measured from the outermost copper of set 1 to the innermost copper of set 2. The gap is for "
                "copper clearance and solder mask: it is not what isolates the two sets.",
        "picture": {"file": "dual_layout.webp", "caption": "Set 1, the gap and set 2 along the radius"}},
    "BAND_SPLIT": {
        "lead": "Set 1's share of the free radial width.",
        "facts": [["0.5", "equal RX band widths"], ["1x / 16x board", "usually near 0.5"],
                  ["1x / 32x board", "near 0.35: the fine track gets the width"]],
        "note": "Read only when no RX band is given.",
        "picture": {"file": "dual_layout.webp", "caption": "Set 1, the gap and set 2 along the radius"}},
    "LAYOUT_TOLERANCE_MM": {
        "lead": "How far the built copper may differ from the layout formulas before the run warns.",
        "facts": [["0.05", "enough for every board tried"], ["0", "no allowance"]],
        "note": "The outline also gets this much extra room when ring 2 of the rotor covers the TX2 turns."},
    "TERMINAL_1_DEG": {
        "lead": "Angle at which the TX ends of set 1, the inner set, end up.",
        "facts": [["0°", "the right"], ["90°", "the bottom of the page"], ["180°", "the left"], ["270°", "the top"]],
        "note": "Each set is turned on its own. Different angles keep the breakouts of the two sets apart."},
    "TERMINAL_2_DEG": {
        "lead": "Angle at which the TX ends of set 2, the outer set, end up.",
        "facts": [["0°", "the right"], ["90°", "the bottom of the page"], ["180°", "the left"], ["270°", "the top"]],
        "note": "Each set is turned on its own. Different angles keep the breakouts of the two sets apart."},
    "TX_FREQ_SEPARATION_MIN": {
        "lead": "Least difference between the two TX frequencies, as a share of the lower one.",
        "facts": [["0.2", "20 %, the usual rule for neighbouring LC sensors"]],
        "note": "Closer than this is a warning. Two free-running carriers over one coil area are unproven."},
    "TX_FREQ_RATIO_MAX_ORDER": {
        "lead": "The two TX frequencies must not sit on a ratio p:q of whole numbers up to this.",
        "facts": [["4", "covers 2:1, 3:1, 4:1, 3:2 and 4:3"], ["1", "the ratio warning is off"]],
        "note": "3.0 and 4.5 MHz are 2:3, which is a warning. 3.0 and 4.3 MHz are not."},
    "TX_FREQ_RATIO_TOLERANCE": {
        "lead": "How near a whole-number ratio the two TX frequencies may come before the run warns.",
        "facts": [["0.02", "2 %"]]},
    "ROTOR_START_ANGLE_ZERO": {
        "lead": "Where each ring's start angle is measured from.",
        "choices": {"rx_zero": "From its own set's RX pattern zero. Both tracks then read 0 at the same shaft angle.",
                    "board": "From the board's +x axis, as the Single Coil Set Generator measures it."},
        "note": "The record file prints each set's zero."},
    "ROTOR_TRACK_GAP_MM": {
        "lead": "The bare ring that must stay between rotor ring 1 and rotor ring 2.",
        "facts": [["Dual boards in practice", "2.3 to 3.0 mm"]],
        "note": "Smaller is an error, which names the extension to change."},
    "ROTOR_1_TO_RX2_MM": {
        "lead": "Least distance from the outer radius of rotor ring 1 to the innermost RX2 copper.",
        "facts": [["Usual layout rule", "3 mm, 5 mm if the design allows"], ["Dual 1x / 16x boards in practice", "about 3 mm"]],
        "note": "Smaller is a warning. Field of ring 1 that reaches the RX2 band adds an error once per turn that no "
                "fine-track calibration removes."},
    "ROTOR_2_TO_RX1_MM": {
        "lead": "Least distance from the inner radius of rotor ring 2 to the outermost RX1 copper.",
        "note": "Smaller is a warning. Ring 2 may come closer than ring 1 may: its ripple is rejected by a 1x RX."},
}

# A set's own copy of a board value (Dual): the same tip, with this choice added.
OVERRIDE_CHOICE = "This set uses the board's value."

# The six TX layout cards: name, what it is for, and what it sets (in the page's words).
PRESETS = {
    "2-bottom": {"lead": "The original, proven layout: all TX turns on the bottom layer."},
    "2-top": {"lead": "All TX turns on the top layer, next to the rotor: more signal in the model."},
    "2-series": {"lead": "TX turns on both layers, in series. The fingers go around the Top turns."},
    "4-bottom": {"lead": "All TX turns on the bottom layer, with the RX on Top and Inner-1."},
    "4-renesas": {"lead": "TX turns on Top and Inner-2, in series: the Renesas IPS2200 reference."},
    "4-inner1": {"lead": "TX turns on Top and Inner-1, in series. The fingers go around the Top turns."},
}
PRESET_FOOT = "Only these change. Every other setting keeps its value."

# Buttons, switches and other controls: {tip id: text}, or a tip with a title, keys and a note.
CONTROLS = {
    "gen-menu": {"lead": "Which generator the page runs.",
                 "note": "Your settings of each generator are kept when you switch. Arc and Linear are not available."},
    "gen-single": {"lead": "The Single Coil Set Generator: one sine and cosine RX pair with one TX coil."},
    "gen-dual": {"lead": "The Dual Coil Set Generator: two coil sets on one board, an inner and an outer one, each with "
                         "its own rotor ring (a coarse and a fine track)."},
    "mode-basic": {"lead": "The main settings of each category, with sliders."},
    "mode-advanced": {"lead": "Every setting of every parameter file, as the desktop generator has them."},
    "btn-help": {"lead": "Open the quick guide to choosing the parameters, in a new tab."},
    "btn-import": {"lead": "Load a design from files.",
                   "facts": [["Reads", "parameter files (.py), a zip of them, or the Parameters.txt of a run"]],
                   "note": "Single and Dual designs are both read."},
    "btn-export": {"lead": "Download the parameter files with your settings, ready for the desktop generator."},
    "btn-share": {"lead": "Copy a link that opens this page with your settings."},
    "nav-back": {"lead": "Back to the page you came from."},
    "nav-home": {"lead": "The blog's front page."},
    "find": {"lead": "Type part of a setting's name, its name in the file, or a word of its help.",
             "note": "Every match of every file is listed."},
    "strict": {"lead": "Every warning about the finished boards stops the run, and nothing is written.",
               "note": "The same as --strict on the desktop."},
    "btn-reset": {"lead": "Put every setting of this generator back to its published value."},
    "btn-check": {"lead": "Run only the generator's checks of the settings.", "note": "Quick: nothing is built."},
    "btn-generate": {"lead": "Run the generator with these settings.", "keys": ["Ctrl", "Enter"]},
    "view-stator": {"lead": "The stator board alone."},
    "view-rotor": {"lead": "The rotor board alone."},
    "view-overlay": {"lead": "The rotor's copper drawn over the stator, at the angle of the Rotor Angle slider."},
    "view-pictures": {"lead": "The two pictures the generator draws of the board."},
    "btn-fullscreen": {"lead": "Show the preview full screen.", "keys": ["Esc"], "keysNote": "leaves it"},
    "btn-fullscreen-on": {"lead": "Leave full screen.", "keys": ["Esc"]},
    "btn-fit": {"lead": "Fit the board to the preview.", "keys": ["0"], "keysNote": "or a double click"},
    "btn-measure": {"lead": "Measure a distance: click two points on the board.",
                    "keys": ["S"], "keysNote": "locks the line, Z removes the last one"},
    "readout": {"lead": "The position of the mouse on the board, from the board centre."},
    "rotor-angle": {"lead": "Turn the rotor over the stator.", "note": "The preview only: the boards are unchanged."},
    "show-info": {"lead": "Also list the generator's notes, not only its warnings and errors."},
    "btn-runtext": {"lead": "Everything the generator printed in this run, as on the desktop."},
    "btn-files": {"lead": "Every file of this run, to download one by one."},
    "btn-cancel": {"lead": "Stop this run.", "note": "Python starts again, which takes a few seconds."},
    "btn-download": {"lead": "Download this run as one zip: the same folder the desktop generator writes.",
                     "facts": [["Holds", "Stator.kicad_pcb, Rotor.kicad_pcb, their .kicad_pro files, Parameters.txt and the two pictures"],
                               ["This run", "{name}.zip"]]},
    "btn-download-stale": {"lead": "The settings changed: press Generate first."},
    "btn-dl-stator": {"lead": "Download only the stator board of this run, ready to open in KiCad.",
                      "facts": [["File", "{name}_Stator.kicad_pcb"]]},
    "btn-dl-rotor": {"lead": "Download only the rotor board of this run, ready to open in KiCad.",
                     "facts": [["File", "{name}_Rotor.kicad_pcb"]]},
    "reset-one": {"lead": "Back to the starting value."},
    "param-link": {"lead": "Show this setting."},
    "picture-open": {"lead": "Open this picture in a new tab."},
    "origin": {"lead": "The board centre (origin).", "note": "Hover to highlight it, click to hide it."},
    "origin-off": {"lead": "Show the board centre (origin)."},
    "vias": {"lead": "Show or hide the vias.",
             "note": "Hover to enlarge small vias to at least 6 px. The preview only: the boards are unchanged."},
    "vias-off": {"lead": "Show the vias."},
    "layer": {"lead": "Hover to highlight the {layer} copper ({cu}), click to hide it.", "note": "The preview only."},
    "layer-off": {"lead": "Show the {layer} copper ({cu})."},
    "layer-missing": {"lead": "This board has no copper on the {layer} layer ({cu})."},
    "silk": {"lead": "Hide the silkscreen suggestion on the {side} side ({cu}).", "note": "The preview only."},
    "silk-off": {"lead": "Show the silkscreen suggestion on the {side} side ({cu})."},
    "silk-missing": {"lead": "This board has no silkscreen marks on its {side} side ({cu})."},
    "net": {"lead": "Hover to highlight {what}, click to hide it.", "note": "The preview only."},
    "net-off": {"lead": "Show {what}."},
    "tab": {"lead": "{what} of {file}.", "facts": [["Changed", "{changed}"]]},
    "set": {"lead": "The {cat} settings of coil set {set}, the {which} one."},
    "rotor-fold": {"lead": "Show or hide the {kind} rotor settings.", "note": "Used when Rotor Mode is {mode}."},
    "none": {"lead": "{line}"},                              # the None or Auto line of the setting's own tip
    "none-locked": {"lead": "Locked: the RX band is set by {pair}.", "note": "Set those to None first to use this pair."},
    "result-range": {"lead": "The unique angle range: one electrical period of the RX pattern."},
    "result-R": {"lead": "Resistance of the TX coil at DC.", "note": "The generator's estimate."},
    "result-L": {"lead": "Inductance of the TX coil without the rotor.", "note": "The generator's estimate."},
    "result-C": {"lead": "The tank capacitors for the TX frequency f.", "note": "The generator's estimate."},
    "result-f": {"lead": "The TX frequency the tank capacitors are sized for."},
}

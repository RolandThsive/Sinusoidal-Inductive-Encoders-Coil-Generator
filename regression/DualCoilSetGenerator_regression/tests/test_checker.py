"""
test_checker.py  -  the dual parameter checks (the 32 combinations of what the layout is given, the settings a dual
board used to fix, a set's own vias and clearance, the dual rules, the Single Coil Set Generator's checks on each set)
and the decision of Dual_RunCoilGenerator.py, run with --check (nothing is written).  Every case sets a few values in
memory and says what the generator must print and return.

A case is (name, overrides, return code, must-match patterns, must-not-match patterns).  Most cases start from
harness.BASE (both bands fitted between the edges 8.5 / 29.5 with a 0.5 mm gap, three TX turns: combination 32),
the layout they were written against; the cases named default_... use the repository's files as they are (the
R_145 board, both bands given: combination 1).  The combination cases (harness.combination) give exactly what the
row of the table on the wiki page Dual Layout gives.
"""

import unittest

import harness as H
from harness import BAND1, BAND2_CENTRE, NO_EDGES, DELETE, base, combination

B1_CENTRE_TOO = {"RX1.RX_R_BASE_MM": 12.875, "RX1.RX_A_MM": 3.175}
CASES = [
    # ------------------------------------------------------------------ the repository's own files
    ("default_passes", {}, 0, [r"layout: both RX bands given, at least MIN_CLEARANCE_MM apart; bore and outline from "
                               r"the bands \(combination 1 of 32\)", r"bore r = 7\.25 mm", r"outline r = 26\.875 mm",
                               r"gap 3\.725 mm", r"5\.80 mm bare", r"no warnings", r"CHECK PASSED"], [r"WARNING", r"ERROR"]),
    ("default_stator_only", {}, 0, [r"rotor built", r"CHECK PASSED"], [r"--stator: the rotor is not written"], ["--stator"]),
    ("default_parallel_wiring_does_not_fit", {"TX2.TX_WIRING": "parallel"}, 1,
     [r"ERROR   TX_PITCH_MM conflicts with VIA_DIAMETER_MM and TX_WIRING", r"set 2: a pitch of 0\.35 mm is too small"], []),
    ("default_rotor_only", {}, 0, [r"rotor built", r"CHECK PASSED"], [], ["--rotor"]),
    ("default_strict_passes", {"BOARD.GENERATOR_MODE": "strict"}, 0, [r"CHECK PASSED"], [r"ERROR"]),
    # ------------------------------------------------------------------ the layout: refusals and edge cases
    ("err_half_a_band_pair", base(**{"RX1.INSIDE_RADIUS_MM": 9.7}), 1, [r"ERROR"], []),
    ("err_both_pairs_in_rx1", base(**BAND1, **B1_CENTRE_TOO), 1, [r"ERROR"], []),
    ("err_both_bands_too_close", base(**BAND1, **NO_EDGES, **{"RX2.RX_R_BASE_MM": 21.0, "RX2.RX_A_MM": 3.0, "BOARD.TRACK_GAP_MM": None}), 1,
     [r"ERROR", r"run into each other", r"at least 0\.2 mm \(MIN_CLEARANCE_MM\) must stay free"], []),
    ("err_both_bands_closer_than_track_gap", base(**BAND1, **NO_EDGES, **{"RX2.RX_R_BASE_MM": 22.725, "RX2.RX_A_MM": 3.175, "BOARD.TRACK_GAP_MM": 0.8}), 1,
     [r"ERROR", r"0\.50 mm apart; at least 0\.8 mm \(TRACK_GAP_MM\) must stay free"], []),
    ("err_rx1_band_outside_rx2", base(**NO_EDGES, **{"RX1.INSIDE_RADIUS_MM": 19.55, "RX1.OUTSIDE_RADIUS_MM": 25.9, "RX2.RX_R_BASE_MM": 12.875, "RX2.RX_A_MM": 3.175}), 1,
     [r"ERROR", r"must lie inside the RX2 band .*: set 1 is the inner set. .*swap the two sets' files"], [r"run into each other"]),
    ("err_both_edges_given_too_tight", base(**BAND1, **BAND2_CENTRE, **{"BOARD.TRACK_GAP_MM": None, "BOARD.OUTER_EDGE_RADIUS_MM": 28.0}), 1,
     [r"ERROR", r"set 2: the outer board edge \(28 mm\) is too small"], []),
    ("err_given_bore_too_large", combination(11) | {"BOARD.INNER_EDGE_RADIUS_MM": 9.0}, 1,
     [r"ERROR", r"set 1: the centre hole \(9 mm\) does not leave INNER_EDGE_INSET_MM"], []),
    ("err_outline_leaves_rx2_no_room", combination(14) | {"BOARD.OUTER_EDGE_RADIUS_MM": 22.0}, 1,
     [r"ERROR", r"the outline \(22 mm\) leaves no room for the RX2 band: placed TRACK_GAP_MM \(0\.5 mm\) past set 1's copper"], []),
    ("err_outline_leaves_rx2_too_narrow", combination(14) | {"BOARD.OUTER_EDGE_RADIUS_MM": 23.5}, 1,
     [r"ERROR", r"set 2: the RX band \(0\.35 mm wide\) is narrower than one via",
      r"hint    the generator fitted the RX2 band into the room up to the outline: it came out 0\.35 mm wide"], []),
    ("err_bore_leaves_rx1_no_room", combination(20) | {"BOARD.INNER_EDGE_RADIUS_MM": 15.5}, 1,
     [r"ERROR", r"the bore \(15\.5 mm\) leaves no room for the RX1 band"], []),
    ("err_placed_rx1_pushes_the_bore_to_zero", combination(18) | {"RX2.RX_R_BASE_MM": 10.0, "RX2.RX_A_MM": 3.0}, 1,
     [r"ERROR", r"the RX1 band placed inside the RX2 band .* the bore would have a zero or negative radius"], []),
    ("err_board_too_small_narrow_bands", base(**{"BOARD.OUTER_EDGE_RADIUS_MM": 20.0}), 1,
     [r"ERROR", r"hint    the generator fitted both RX bands into the room between the board edges"], []),
    ("err_board_far_too_small", base(**{"BOARD.OUTER_EDGE_RADIUS_MM": 16.0}), 1, [r"ERROR", r"too small for two RX bands"], []),
    ("err_one_edge_none_with_no_band", base(**{"BOARD.OUTER_EDGE_RADIUS_MM": None}), 1,
     [r"ERROR", r"no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing"], []),
    ("dual_mode_of_an_old_file_is_ignored", base(**{"BOARD.DUAL_MODE": 4}), 0,
     [r"WARNING DUAL_MODE in Dual_Board_Parameters\.py is no longer used and is ignored: there are no layout modes",
      r"\(combination 32 of 32\)", r"CHECK PASSED"], [r"ERROR"]),
    # ------------------------------------------------------------------ what a dual board used to fix (Dual_Fixed_Parameters.py)
    ("two_layer_board", base(**{"BOARD.PCB_LAYERS": 2, "TX1.TX_LAYER_B": 4, "TX2.TX_LAYER_B": 4}), 0,
     [r"WARNING a 2-layer dual board \(PCB_LAYERS = 2", r"CHECK PASSED"], [r"ERROR"]),
    ("err_two_layers_with_an_inner_tx_layer", base(**{"BOARD.PCB_LAYERS": 2}), 1,
     [r"ERROR   set 1: TX_LAYER_B must be one of 1, 4", r"ERROR   set 2: TX_LAYER_B must be one of 1, 4"], []),
    ("fingers_on_set_1_push_set_2_out", base(**{"RX1.RX_TABS": "all"}), 0,
     [r"set 1 copper reaches r = 18\.95 mm", r"0\.500 mm free", r"CHECK PASSED"], [r"ERROR", r"differs from the layout"]),
    ("fingers_on_set_2", {"RX2.RX_TABS": "single"}, 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("tail_on_tx1_pushes_set_2_out", {"TX1.TX_TAIL_EXTRA_MM": 1.0}, 0,
     [r"set 1 copper reaches r = 14\.975 mm", r"2\.725 mm free", r"CHECK PASSED"], [r"ERROR", r"differs from the layout"]),
    ("spiral_tx2_with_a_tail", {"TX2.TX_SHAPE": "spiral", "TX2.TX_TAIL_EXTRA_MM": 1.0}, 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("stepped_arc_tx1", {"TX1.TX_SHAPE": "stepped_arc", "TX1.TX_TAIL_EXTRA_MM": 1.5}, 0,
     [r"set 1 copper reaches r = 15\.475 mm", r"CHECK PASSED"], [r"ERROR", r"differs from the layout"]),
    ("err_stepped_arc_without_a_tail", {"TX1.TX_SHAPE": "stepped_arc"}, 1, [r"ERROR.*TX_STEPPED_ARC_RADIUS_MM"], []),
    ("err_a_moved_name_missing", base(**{"RX1.RX_TABS": DELETE}), 1,
     [r"ERROR", r"RX_TABS is missing - add it to Dual_RX1_Parameters.py"], []),
    ("warn_tx_shape_in_the_board_file", base(**{"BOARD.TX_SHAPE": "spiral"}), 0,
     [r"WARNING TX_SHAPE in Dual_Board_Parameters.py is ignored: it belongs in Dual_TX1_Parameters.py / Dual_TX2_Parameters.py"],
     [r"ERROR"]),
    ("warn_pcb_layers_in_a_set_file", base(**{"RX1.PCB_LAYERS": 2}), 0,
     [r"WARNING PCB_LAYERS in Dual_RX1_Parameters.py is ignored: it belongs in Dual_Board_Parameters.py"], [r"ERROR"]),
    ("warn_cover_tx_in_the_board_file", base(**{"BOARD.ROTOR_AUTO_COVER_TX": False}), 0,
     [r"WARNING ROTOR_AUTO_COVER_TX in Dual_Board_Parameters.py is ignored: it belongs in Dual_Rotor1_Parameters.py / Dual_Rotor2_Parameters.py"], [r"ERROR"]),
    ("warn_ic_name_in_board_file", base(**{"BOARD.IC_MIN_RP_OHM": 100}), 0,
     [r"WARNING", r"IC_MIN_RP_OHM in Dual_Board_Parameters.py is ignored: it belongs in Dual_IC1_Parameters.py / Dual_IC2_Parameters.py", r"CHECK PASSED"], [r"ERROR"]),
    ("warn_unknown_name_in_rx1", base(**{"RX1.FOO_BAR": 1}), 0, [r"WARNING", r"FOO_BAR"], [r"ERROR"]),
    ("warn_receiver_ic_retired", base(**{"TX1.RECEIVER_IC": "IPS2550"}), 0,
     [r"WARNING", r"RECEIVER_IC in Dual_TX1_Parameters.py is no longer used", r"Dual_IC1_Parameters.py", r"CHECK PASSED"], [r"ERROR"]),
    # ------------------------------------------------------------------ the rotor rings
    ("warn_then_err_ring1_covers_tx1", base(**{"ROTOR1.ROTOR_AUTO_COVER_TX": True}), 1,
     [r"WARNING", r"ROTOR_AUTO_COVER_TX = True in Dual_Rotor1_Parameters.py", r"ROTOR_1_TO_RX2_MM", r"ERROR", r"rotor rings are too close"], []),
    ("ring1_covers_tx1_ring2_moved_out", base(**{"ROTOR1.ROTOR_AUTO_COVER_TX": True, "BOARD.TRACK_GAP_MM": 3.5, "BOARD.OUTER_EDGE_RADIUS_MM": 31.0}), 0,
     [r"WARNING", r"ROTOR_AUTO_COVER_TX = True", r"CHECK PASSED"], [r"ERROR"]),
    ("err_ring1_cover_with_bad_overhang", base(**{"ROTOR1.ROTOR_AUTO_COVER_TX": True, "ROTOR1.ROTOR_AUTO_TX_OVERHANG_MM": -1}), 1,
     [r"ERROR", r"ROTOR_AUTO_TX_OVERHANG_MM"], []),
    ("warn_ring1_too_close_to_rx2", base(**{"ROTOR1.ROTOR_AUTO_EXTENSION_OUTER_MM": 1.0}), 0, [r"WARNING", r"ROTOR_1_TO_RX2_MM"], [r"ERROR"]),
    ("err_ring2_too_close_to_ring1", base(**{"ROTOR2.ROTOR_AUTO_EXTENSION_INNER_MM": 2.0}), 1, [r"ERROR", r"rotor rings are too close"], []),
    ("rotor_zero_from_the_board", base(**{"BOARD.ROTOR_START_ANGLE_ZERO": "Board"}), 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("err_rotor_zero_bad", base(**{"BOARD.ROTOR_START_ANGLE_ZERO": "shaft"}), 1,
     [r"ERROR", r"ROTOR_START_ANGLE_ZERO = 'shaft': must be one of 'rx_zero', 'board'"], []),
    ("err_rotor_zero_missing", base(**{"BOARD.ROTOR_START_ANGLE_ZERO": DELETE}), 1, [r"ERROR", r"ROTOR_START_ANGLE_ZERO is missing"], []),
    ("custom_rotor_mode", base(**{"BOARD.ROTOR_MODE": "custom"}), 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("custom_rotor_no_outline_no_bore", base(**{"BOARD.ROTOR_MODE": "custom", "BOARD.ROTOR_CUSTOM_OUTLINE_RADIUS_MM": None,
                                                "BOARD.ROTOR_CUSTOM_BORE_RADIUS_MM": None}), 1,
     [r"ERROR.*ROTOR_CUSTOM_OUTLINE_RADIUS_MM.*ROTOR_CUSTOM_BORE_RADIUS_MM", r"set 1: a custom rotor needs an outline or a bore"],
     []),
    # ------------------------------------------------------------------ the dual rules
    ("single_layer_tx1", {"TX1.TX_WIRING": "single"}, 0, [r"CHECK PASSED"], [r"ERROR", r"no place"]),
    ("single_layer_tx2", base(**{"TX2.TX_WIRING": "single"}), 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("parallel_wiring_set_1", base(**{"TX1.TX_WIRING": "parallel"}), 0, [r"CHECK PASSED", r"0\.500 mm free"], [r"ERROR"]),
    ("parallel_wiring_both_sets", base(**{"TX1.TX_WIRING": "parallel", "TX2.TX_WIRING": "parallel"}), 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("warn_duplicate_net", base(**{"RX2.RX_NET_PHASE_0_2": "SIN_1"}), 0,
     [r"WARNING the net name 'SIN_1' is used twice", r"the copper is not shorted", r"CHECK PASSED"], [r"ERROR"]),
    ("err_rx1_outside_rx2_says_swap", {"RX1.INSIDE_RADIUS_MM": 18.0, "RX1.OUTSIDE_RADIUS_MM": 23.9,
                                       "RX2.INSIDE_RADIUS_MM": 8.45, "RX2.OUTSIDE_RADIUS_MM": 11.7}, 1,
     [r"ERROR", r"must lie inside the RX2 band", r"swap the two sets' files"], [r"run into each other"]),
    ("warn_set2_on_all_four_layers", base(**{"TX2.TX_LAYER_A": 3, "TX2.TX_LAYER_B": 4}), 0, [r"WARNING", r"all four layers"], [r"ERROR"]),
    ("warn_frequencies_10_percent_apart", base(**{"TX2.EXCITATION_FREQ_HZ": 3.3e6}), 0, [r"WARNING", r"differ by 10\.0 %"], [r"ERROR"]),
    ("warn_frequencies_3_to_2", base(**{"TX2.EXCITATION_FREQ_HZ": 4.5e6}), 0,
     [r"WARNING", r"ratio 3:2", r"TX_FREQ_RATIO_TOLERANCE = 2 %", r"TX_FREQ_RATIO_MAX_ORDER = 4"], [r"ERROR"]),
    ("ratio_warning_off_with_order_1", base(**{"TX2.EXCITATION_FREQ_HZ": 4.5e6, "BOARD.TX_FREQ_RATIO_MAX_ORDER": 1}), 0,
     [r"no warnings", r"CHECK PASSED"], [r"WARNING"]),
    ("warn_5_to_4_found_with_order_5", base(**{"TX2.EXCITATION_FREQ_HZ": 3.75e6, "BOARD.TX_FREQ_RATIO_MAX_ORDER": 5}), 0, [r"WARNING", r"ratio 5:4"], [r"ERROR"]),
    ("5_to_4_not_found_with_order_4", base(**{"TX2.EXCITATION_FREQ_HZ": 3.75e6}), 0, [r"no warnings", r"CHECK PASSED"], [r"WARNING"]),
    ("warn_within_8_percent_tolerance", base(**{"BOARD.TX_FREQ_RATIO_TOLERANCE": 0.08}), 0,
     [r"WARNING", r"ratio 3:2", r"TX_FREQ_RATIO_TOLERANCE = 8 %"], [r"ERROR"]),
    ("err_ratio_order_0", base(**{"BOARD.TX_FREQ_RATIO_MAX_ORDER": 0}), 1, [r"ERROR", r"TX_FREQ_RATIO_MAX_ORDER"], []),
    ("err_ratio_tolerance_1", base(**{"BOARD.TX_FREQ_RATIO_TOLERANCE": 1.0}), 1, [r"ERROR", r"TX_FREQ_RATIO_TOLERANCE"], []),
    ("err_layout_tolerance_negative", base(**{"BOARD.LAYOUT_TOLERANCE_MM": -0.1}), 1, [r"ERROR", r"LAYOUT_TOLERANCE_MM"], []),
    ("layout_tolerance_0_passes", base(**{"BOARD.LAYOUT_TOLERANCE_MM": 0}), 0, [r"CHECK PASSED"], [r"ERROR"]),
    ("err_missing_tx_turns", base(**{"TX1.TX_TURNS": DELETE}), 1, [r"ERROR", r"TX_TURNS"], []),
    ("err_band_split_1", base(**{"BOARD.BAND_SPLIT": 1.0}), 1, [r"ERROR", r"BAND_SPLIT"], []),
    ("err_gap_negative", base(**{"BOARD.TRACK_GAP_MM": -1}), 1, [r"ERROR", r"TRACK_GAP_MM"], []),
    ("strict_mode_with_a_board_warning", base(**{"BOARD.GENERATOR_MODE": "strict", "ROTOR1.ROTOR_AUTO_EXTENSION_OUTER_MM": 1.0}), 1,
     [r"WARNING", r'GENERATOR_MODE = "strict"', r"board warning\(s\) in strict mode"], []),
    # ------------------------------------------------------------------ the ICs and the estimate
    ("err_ic2_oscillator_range_empty", base(**{"IC2.IC_OSC_MIN_MHZ": 6.0, "IC2.IC_OSC_MAX_MHZ": 5.0}), 1,
     [r"ERROR", r"IC_OSC_MIN_MHZ conflicts with IC_OSC_MAX_MHZ", r"set 2: the IC.s oscillator range 6 ... 5 MHz is empty"], []),
    ("different_ics_per_set", base(**{"IC1.IC_NAME": "IPS2200", "IC1.IC_OSC_MIN_MHZ": 1.7, "IC1.IC_OSC_MAX_MHZ": 5.8, "IC1.IC_MIN_RP_OHM": 100,
                                       "IC2.IC_NAME": None, "IC2.IC_OSC_MIN_MHZ": None, "IC2.IC_OSC_MAX_MHZ": None, "IC2.IC_MIN_RP_OHM": None}), 0,
     [r"receiver IC IPS2200", r"no IC limits set", r"CHECK PASSED"], [r"ERROR"]),
    ("e24_caps_one_cap_across_the_coil", base(**{"BOARD.TANK_CAP_SERIES": "e24", "IC1.IC_SPLIT_TANK_CAPS": False}), 0,
     [r"\(E24\)", r"across the coil \(or", r"CHECK PASSED"], [r"ERROR"]),
    ("err_tank_cap_series_e48", base(**{"BOARD.TANK_CAP_SERIES": "e48"}), 1, [r"ERROR", r"TANK_CAP_SERIES"], []),
    ("info_ic_name_missing_in_ic1", base(**{"IC1.IC_NAME": DELETE}), 0, [r"IC_NAME is not in Dual_IC1_Parameters.py", r"CHECK PASSED"], [r"ERROR"]),
    # --------------------------------------------------------- the Single Coil Set Generator's checks on each set
    ("err_set2_loops_17", base(**{"RX2.LOOPS": 17}), 1, [r"ERROR.*set 2: LOOPS", r"Dual_RX2_Parameters\.py"], []),
    ("err_set1_tx_pitch_text", base(**{"TX1.TX_PITCH_MM": "0.6"}), 1, [r"ERROR.*set 1: TX_PITCH_MM", r"Dual_TX1_Parameters\.py"], []),
    ("err_set1_rx_layers_equal", base(**{"RX1.RX_LAYER_A": 2, "RX1.RX_LAYER_B": 2}), 1, [r"ERROR   RX_LAYER_A conflicts with RX_LAYER_B\n\s+set 1: the two RX layers must be different"], []),
    ("err_set2_drill_too_big", base(**{"BOARD.VIA_DRILL_MM": 0.8}), 1, [r"ERROR   VIA_DRILL_MM conflicts with VIA_DIAMETER_MM\n\s+set 1: the drill",
                                                                        r"ERROR   VIA_DRILL_MM conflicts with VIA_DIAMETER_MM\n\s+set 2: the drill"], []),
    ("set2_duty_low_warns", base(**{"ROTOR2.ROTOR_AUTO_DUTY": 0.2}), 0, [r"WARNING.*set 2: rotor metal fraction 0\.2", r"CHECK PASSED"], [r"ERROR"]),
    # the file named in a Single Coil Set Generator message is the dual file that holds the name
    ("err_excitation_names_the_tx_file", base(**{"TX1.EXCITATION_FREQ_HZ": "x"}), 1,
     [r"ERROR   set 1: EXCITATION_FREQ_HZ = 'x': must be a number greater than 0   \(Dual_TX1_Parameters\.py\)"],
     [r"EXCITATION_FREQ_HZ.*Dual_Board_Parameters"]),
    ("err_rotor_arc_steps_names_the_board_file", base(**{"BOARD.ROTOR_ARC_STEPS_PER_SECTOR": 3}), 1,
     [r"ERROR   set 1: ROTOR_ARC_STEPS_PER_SECTOR = 3: must be .*\(Dual_Board_Parameters\.py\)"],
     [r"ROTOR_ARC_STEPS_PER_SECTOR.*Dual_Rotor1_Parameters"]),
    # a None where the layout needs a number is named, not reported as "a setting is not a number"
    ("err_tx_turns_none_is_named", base(**{"TX1.TX_TURNS": None}), 1,
     [r"ERROR   set 1: TX_TURNS = None: must be a whole number between 1 and 50   \(Dual_TX1_Parameters\.py\)"],
     [r"a setting is not a number", r"set 2: TX_TURNS"]),
    ("err_inset_none_is_named", base(**{"BOARD.INNER_EDGE_INSET_MM": None}), 1,
     [r"ERROR   set 1: INNER_EDGE_INSET_MM = None: must be a number at least 0   \(Dual_Board_Parameters\.py\)"],
     [r"a setting is not a number"]),
    # the rotor settings default as in the Single Coil Set Generator (ROTOR_AUTO_COVER_TX True, overhang 0.5): the
    # outline keeps room for ring 2's overhang, with the edge line and the polygon vertices
    # as RotorBuilder limits the ring
    ("rotor2_cover_missing_uses_the_default", base(**{"ROTOR2.ROTOR_AUTO_COVER_TX": DELETE}), 0,
     [r"ROTOR_AUTO_COVER_TX is not in Dual_Rotor2_Parameters\.py: using the default True", r"CHECK PASSED"],
     [r"ERROR", r"does not fit"]),
    ("rotor2_overhang_missing_uses_the_default", base(**{"ROTOR2.ROTOR_AUTO_TX_OVERHANG_MM": DELETE}), 0,
     [r"ROTOR_AUTO_TX_OVERHANG_MM is not in Dual_Rotor2_Parameters\.py: using the default 0\.5", r"CHECK PASSED"],
     [r"ERROR", r"does not fit"]),
    ("default_no_layout_tolerance_still_fits_ring_2", {"BOARD.LAYOUT_TOLERANCE_MM": 0}, 0, [r"CHECK PASSED"],
     [r"ERROR", r"does not fit"]),
    ("default_wide_edge_line_still_fits_ring_2", {"BOARD.EDGE_LINE_WIDTH_MM": 0.3}, 0, [r"CHECK PASSED"],
     [r"ERROR", r"does not fit"]),
    ("fitted_bands_odd_edges_keep_the_gap", base(**{"BOARD.INNER_EDGE_RADIUS_MM": 8.1234567, "BOARD.OUTER_EDGE_RADIUS_MM": 29.7654321}), 0,
     [r"0\.500 mm free", r"CHECK PASSED"], [r"ERROR"]),
    ("custom_rotor_ring_2_over_tx1_names_the_custom_radius", base(**{"BOARD.ROTOR_MODE": "custom", "ROTOR2.ROTOR_CUSTOM_INNER_RADIUS_MM": 17.0}), 0,
     [r"Shorten ring 2's inner extension \(ROTOR_CUSTOM_INNER_RADIUS_MM in Dual_Rotor2_Parameters\.py\)", r"CHECK PASSED"],
     [r"ROTOR_AUTO_EXTENSION_INNER_MM in Dual_Rotor2", r"ERROR"]),
    # ------------------------------------------------------------------ VIA_TYPE (shared by both sets)
    ("via_type_blind_default_layers", base(**{"BOARD.VIA_TYPE": "blind", "BOARD.VIA_DIAMETER_MM": 0.4, "BOARD.VIA_DRILL_MM": 0.15}), 0,
     [r"info    VIA_TYPE conflicts with RX_LAYER_A and RX_LAYER_B\n\s+set 1: the RX tip vias are blind vias between Top and Inner-1",
      r"info    VIA_TYPE conflicts with RX_LAYER_A and RX_LAYER_B\n\s+set 2: the RX tip vias are blind vias between Top and Inner-1",
      r"WARNING VIA_TYPE conflicts with TX_LAYER_A and TX_LAYER_B\n\s+set 1: the TX vias join Top and Inner-2, skipping the layer between",
      r"WARNING VIA_TYPE conflicts with TX_LAYER_A and TX_LAYER_B\n\s+set 2: the TX vias join Top and Inner-2, skipping the layer between",
      r"CHECK PASSED"], [r"ERROR", r"VIA_TYPE conflicts with VIA_DRILL_MM"]),
    ("via_type_blind_large_drill_warns", base(**{"BOARD.VIA_TYPE": "blind"}), 0,
     [r"WARNING VIA_TYPE conflicts with VIA_DRILL_MM\n\s+set 1: blind vias are laser-drilled, at most about 0\.15 mm wide at "
      r"common fabs; VIA_DRILL_MM = 0\.3 is a mechanical drill", r"CHECK PASSED"], [r"ERROR"]),
    ("via_type_bad_value", base(**{"BOARD.VIA_TYPE": "micro"}), 1,
     [r"ERROR   set 1: VIA_TYPE = 'micro': must be one of 'through', 'blind'   \(Dual_Board_Parameters\.py\)", r"FAILED: 2 parameter error"], []),
    ("via_type_missing_uses_through", base(**{"BOARD.VIA_TYPE": DELETE}), 0,
     [r"VIA_TYPE is not in Dual_Board_Parameters\.py: using the default 'through'", r"CHECK PASSED"], [r"ERROR", r"blind vias"]),
    # ------------------------------------------------------------------ a set's own vias, clearance, tank capacitors, AC factor
    ("via_type_blind_in_set_1_only", base(**{"RX1.VIA_TYPE": "blind", "RX1.VIA_DIAMETER_MM": 0.4, "RX1.VIA_DRILL_MM": 0.15}), 0,
     [r"set 1: the RX tip vias are blind vias between Top and Inner-1", r"CHECK PASSED"],
     [r"ERROR", r"set 2: the RX tip vias are blind", r"VIA_TYPE in Dual_RX1_Parameters\.py is ignored"]),
    ("via_type_in_a_tx_file_is_ignored", base(**{"TX1.VIA_TYPE": "blind"}), 0,
     [r"WARNING VIA_TYPE in Dual_TX1_Parameters\.py is ignored: it belongs in Dual_Board_Parameters\.py / "
      r"Dual_RX1_Parameters\.py / Dual_RX2_Parameters\.py", r"CHECK PASSED"], [r"ERROR", r"blind vias between"]),
    ("bigger_vias_in_set_2_move_its_copper_in", {"RX2.VIA_DIAMETER_MM": 0.8, "RX2.VIA_DRILL_MM": 0.4}, 0,
     [r"set 2 copper starts at r = 17\.6 mm", r"3\.625 mm free", r"CHECK PASSED"], [r"ERROR"]),
    ("err_set_1_drill_names_its_rx_file", base(**{"RX1.VIA_DRILL_MM": 0.8}), 1,
     [r"ERROR   VIA_DRILL_MM conflicts with VIA_DIAMETER_MM\n\s+set 1: the drill"], [r"set 2: the drill"]),
    ("err_set_2_via_type_bad", base(**{"RX2.VIA_TYPE": "micro"}), 1,
     [r"ERROR   set 2: VIA_TYPE = 'micro': must be one of 'through', 'blind'   \(Dual_RX2_Parameters\.py\)"],
     [r"set 1: VIA_TYPE"]),
    ("larger_clearance_of_set_2_between_the_sets", {"RX2.MIN_CLEARANCE_MM": 0.18}, 0,
     [r"at least MIN_CLEARANCE_MM = 0\.18 needed", r"CHECK PASSED"], [r"ERROR"]),
    ("info_a_set_value_not_in_its_file", base(**{"RX2.MIN_CLEARANCE_MM": DELETE}), 0,
     [r"MIN_CLEARANCE_MM is not in Dual_RX2_Parameters\.py: the board's value is used", r"CHECK PASSED"], [r"ERROR"]),
    ("tank_caps_e24_in_set_2_only", base(**{"IC2.TANK_CAP_SERIES": "E24"}), 0,
     [r"set 1 \(inner\)[\s\S]*\(E12\)[\s\S]*set 2 \(outer\)[\s\S]*\(E24\)", r"CHECK PASSED"], [r"ERROR"]),
    ("ac_factor_3_in_set_1_only", base(**{"TX1.TX_AC_RESISTANCE_FACTOR": 3.0}), 0,
     [r"set 1 \(inner\)[\s\S]*up to about 3x that[\s\S]*set 2 \(outer\)[\s\S]*up to about 2x that", r"CHECK PASSED"],
     [r"ERROR"]),
]


# ------------------------------------------------------------------------------------- the 32 combinations
# What the layout must make of each row of the table on the wiki page Dual Layout (harness.combination gives exactly
# what the row gives: RX1 9.7 ... 16.05, RX2 19.55 ... 25.9, bore 8, outline 30, TRACK_GAP_MM 0.5; MIN_CLEARANCE_MM
# 0.2).  A row that builds: (RX1 band, RX2 band, bore, outline, the gap on the built copper).  A row that is refused:
# the message.
LAYOUTS = {
    1: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "29.5", "0.5"),
    2: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "29.5", "0.5"),
    3: ("9.7 ... 16.05", "19.55 ... 25.9", "8", "29.5", "0.5"),
    4: ("9.7 ... 16.05", "19.55 ... 25.9", "8", "29.5", "0.5"),
    5: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "30", "0.5"),
    6: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "30", "0.5"),
    7: ("9.7 ... 16.05", "19.55 ... 25.9", "8", "30", "0.5"),
    8: ("9.7 ... 16.05", "19.55 ... 25.9", "8", "30", "0.5"),
    9: ("9.7 ... 16.05", "19.25 ... 25.6", "8.5", "29.2", "0.2"),
    10: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "29.5", "0.5"),
    11: ("9.7 ... 16.05", "19.25 ... 25.6", "8", "29.2", "0.2"),
    12: ("9.7 ... 16.05", "19.55 ... 25.9", "8", "29.5", "0.5"),
    13: ("9.7 ... 16.05", "19.25 ... 26.4", "8.5", "30", "0.2"),
    14: ("9.7 ... 16.05", "19.55 ... 26.4", "8.5", "30", "0.5"),
    15: ("9.7 ... 16.05", "19.25 ... 26.4", "8", "30", "0.2"),
    16: ("9.7 ... 16.05", "19.55 ... 26.4", "8", "30", "0.5"),
    17: ("10 ... 16.35", "19.55 ... 25.9", "8.8", "29.5", "0.2"),
    18: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "29.5", "0.5"),
    19: ("9.2 ... 16.35", "19.55 ... 25.9", "8", "29.5", "0.2"),
    20: ("9.2 ... 16.05", "19.55 ... 25.9", "8", "29.5", "0.5"),
    21: ("10 ... 16.35", "19.55 ... 25.9", "8.8", "30", "0.2"),
    22: ("9.7 ... 16.05", "19.55 ... 25.9", "8.5", "30", "0.5"),
    23: ("9.2 ... 16.35", "19.55 ... 25.9", "8", "30", "0.2"),
    24: ("9.2 ... 16.05", "19.55 ... 25.9", "8", "30", "0.5"),
    25: r"no RX band and no board edge is given: there is nothing to size the bands from",
    26: r"no RX band and no board edge is given: there is nothing to size the bands from",
    27: r"no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing",
    28: r"no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing",
    29: r"no RX band is given and of the board edges only the outline: INNER_EDGE_RADIUS_MM is missing",
    30: r"no RX band is given and of the board edges only the outline: INNER_EDGE_RADIUS_MM is missing",
    31: ("9.2 ... 16.2", "19.4 ... 26.4", "8", "30", "0.2"),
    32: ("9.2 ... 16.05", "19.55 ... 26.4", "8", "30", "0.5"),
}
# the first line of the layout, in full, for one row of each kind
LAYOUT_WORDS = {
    1: "both RX bands given, at least MIN_CLEARANCE_MM apart; bore and outline from the bands",
    8: "both RX bands given, at least TRACK_GAP_MM apart; bore and outline as given",
    10: "RX1 band given, RX2 band placed TRACK_GAP_MM out and as wide as RX1; bore and outline from the bands",
    13: "RX1 band given, RX2 band placed MIN_CLEARANCE_MM out and running to the outline; outline as given, bore from the RX1 band",
    19: "RX2 band given, RX1 band placed MIN_CLEARANCE_MM in and starting at the bore plus INNER_EDGE_INSET_MM; bore as given, "
        "outline from the RX2 band",
    21: "RX2 band given, RX1 band placed MIN_CLEARANCE_MM in and as wide as RX2; outline as given, bore from the RX1 band",
    31: "both RX bands fitted between the edges, split by BAND_SPLIT, MIN_CLEARANCE_MM apart; bore and outline as given",
}


def _combination_case(n):
    import re
    want = LAYOUTS[n]
    if isinstance(want, str):
        return (f"combination_{n:02d}_refused", combination(n), 1, [r"ERROR", want], [r"layout:"])
    group, rest = divmod(n - 1, 8)
    b1, b2, bore, outline, gap = want
    how1 = "placed by the generator" if group in (2, 3) else "INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM as given"
    how2 = "placed by the generator" if group in (1, 3) else "RX_R_BASE_MM / RX_A_MM as given"
    words = re.escape(LAYOUT_WORDS[n]) if n in LAYOUT_WORDS else ".*"
    must = [rf"layout: {words} \(combination {n} of 32\)",
            rf"RX1 band r = {re.escape(b1)} mm .*: {how1}", rf"RX2 band r = {re.escape(b2)} mm .*: {how2}",
            rf"bore r = {re.escape(bore)} mm \(" + ("INNER_EDGE_RADIUS_MM" if rest & 2 else "RX1 band start") + r"",
            rf"outline r = {re.escape(outline)} mm \(" + ("OUTER_EDGE_RADIUS_MM" if rest & 4 else "RX2 band end") + r"",
            rf"{float(gap):.3f} mm free \(at least {0.5 if rest & 1 else 0.2:g} needed\)", r"CHECK PASSED"]
    return (f"combination_{n:02d}", combination(n), 0, must, [r"ERROR"])


CASES += [_combination_case(n) for n in range(1, 33)]


class CheckerCases(unittest.TestCase):
    pass


def _make(name, overrides, rc, must, must_not, extra_args):
    def test(self):
        res = H.check(overrides, extra_args)
        tail = "\n".join(res.lines[-25:])
        self.assertEqual(res.rc, rc, f"return code {res.rc}, expected {rc}:\n{tail}")
        for pat in must:
            self.assertTrue(res.has(pat), f"the output does not match {pat!r}:\n{tail}")
        for pat in must_not:
            self.assertFalse(res.has(pat), f"the output matches {pat!r} but must not:\n{tail}")
        self.assertEqual(res.err, "", f"the run wrote to stderr:\n{res.err}")
        if rc == 1:
            self.assertTrue(res.has(r"FAILED: .*Nothing was written"), f"a failed run must say so:\n{tail}")
        else:
            self.assertTrue(res.has(r"CHECK PASSED"), f"a passed check must say so:\n{tail}")
    test.__name__ = "test_" + name
    test.__doc__ = f"{name} -> rc {rc}"
    return test


for _case in CASES:
    _name, _ov, _rc, _must, _not = _case[:5]
    _args = _case[5] if len(_case) > 5 else ()
    setattr(CheckerCases, "test_" + _name, _make(_name, _ov, _rc, _must, _not, _args))


class CheckerBehaviour(unittest.TestCase):
    def test_overrides_do_not_leak_between_runs(self):
        H.check(base(**{"RX2.LOOPS": 0}))
        self.assertEqual(H.P.RX2.LOOPS, 16)
        self.assertIsNone(H.P.BOARD.TRACK_GAP_MM)
        res = H.check()
        self.assertEqual(res.rc, 0)
        self.assertFalse(res.has("WARNING"))

    def test_single_generator_is_left_as_it_was(self):
        """A dual run turns each set to its own terminal angle without touching the Single Coil Set Generator's own
        setting (still 0 deg), and the Single's parameter module still holds the Single Coil Set Generator's values."""
        from Generator.Stator import StatorAssembly
        import Parameters as SingleP
        H.check()
        self.assertEqual(StatorAssembly.TERMINAL_DEG, 0.0)
        self.assertEqual((SingleP.LOOPS, SingleP.PCB_LAYERS, SingleP.OUTER_EDGE_RADIUS_MM), (1, 2, 27.0))

    def test_no_color_output_is_plain(self):
        self.assertNotIn("\x1b[", H.check().out)

    def test_every_error_names_its_dual_file(self):
        res = H.check(base(**{"RX1.LOOPS": 0, "TX2.TX_TURNS": 0, "ROTOR1.ROTOR_AUTO_DUTY": 2, "IC2.IC_MIN_RP_OHM": -1}))
        self.assertEqual(res.rc, 1)
        for f in ("Dual_RX1_Parameters.py", "Dual_TX2_Parameters.py", "Dual_Rotor1_Parameters.py", "Dual_IC2_Parameters.py"):
            self.assertIn(f, res.out)
        self.assertNotIn("RX_Parameters.py", res.out.replace("Dual_RX1_Parameters.py", "").replace("Dual_RX2_Parameters.py", ""),
                         "the Single Coil Set Generator's file names are translated into the dual ones")


if __name__ == "__main__":
    unittest.main()

"""
Dual_TX1_Parameters.py  -  the transmitter (TX) ring of set 1, the inner set, and the IC that drives it and reads
the set.  Dual_TX2_Parameters.py has the same names for set 2.

The names are the Single Generator's own (TX_Parameters.py; EXCITATION_FREQ_HZ from its Board_Parameters.py,
since each set has its own oscillator).  The IC of this set is in Dual_IC1_Parameters.py.  At the end, this
set's own TX_AC_RESISTANCE_FACTOR: None = the board's value (Dual_Board_Parameters.py).

Units: millimetres, degrees, hertz.  Nothing in this file is computed - edit values only.
Layers are numbered 1 = Top, 2 = Inner 1, 3 = Inner 2, 4 = Bottom.
"""

# =============================================================================
# THE OSCILLATOR OF THIS SET  (the electrical estimate; its IC's limits: Dual_IC1_Parameters.py)
# =============================================================================
EXCITATION_FREQ_HZ  = 3.0e6         # TX oscillator frequency aimed for, with the rotor in place (hertz).  Give
                                    # the two sets different frequencies (TX_FREQ_SEPARATION_MIN,
                                    # Dual_Board_Parameters.py).  The generator draws two TX rings; whether both
                                    # ICs drive their own, or one IC drives both tanks in parallel and the other
                                    # has its TX current set to 0 (one carrier), is decided
                                    # on the schematic, not here

# =============================================================================
# THE TX RING  (TX_TURNS turns on TX_LAYER_A and TX_TURNS turns on TX_LAYER_B, series or parallel)
# =============================================================================
TX_NET             = "TX_1"

# TX_WIRING = how the TX turns are wired:
#   "single"   : TX_TURNS turns on TX_LAYER_A only; its inner end comes out on a tail on another layer
#                (TX_SERIES_UNDERPASS_LAYER) that ends past one pitch outside the last turn
#   "series"   : the turns on TX_LAYER_A and on TX_LAYER_B in series, joined by one via at the inner end
#                (2 x TX_TURNS turns; both terminals leave at the terminal angle, one on each layer)
#   "parallel" : the same turns on both layers in parallel, stitched through vias at the terminal: about
#                6 % more receiver signal and twice the Q in the model, half the inductance; its inner end
#                comes out on an inner tail that ends one pitch outside the last turn (no further)
TX_WIRING          = "single"

TX_TURNS           = 4              # complete turns PER TX LAYER.  The inner ring sits between the sets: every turn and every mm of pitch pushes set 2 outwards
                                    # (2 turns at 3 MHz leave the tank below the IC's least parallel resistance: the estimate says so)
TX_OFFSET_MM       = 0.8            # first turn radius = RX outside radius + this
TX_PITCH_MM        = 0.35            # radial pitch between turns
TX_TRACE_WIDTH_MM  = 0.15
TX_STEPS           = "auto"
TX_CHORD_TOLERANCE_MM = 0.001

# TX_SHAPE = shape of the turns (the wiki: Parameter Reference, TX_SHAPE):
#   "stepped_diagonal" : concentric turns joined by straight steps at TX_STEPPED_ANGLE_DEG (the usual dual board)
#   "stepped_arc"      : concentric turns joined by arcs around the terminal via; it needs a tail
#                        (TX_TAIL_EXTRA_MM larger than the arcs, TX_STEPPED_ARC_RADIUS_MM)
#   "spiral"           : one smooth spiral; its last turn ends one pitch farther out
TX_SHAPE           = "stepped_diagonal"
TX_STEPPED_ARC_RADIUS_MM = "auto"   # (stepped_arc only) radius of the innermost arc, or "auto"
# TX_TAIL_EXTRA_MM = how far the TX ends run on past one pitch outside the last turn (0 = they end there).
# Set 1's tail reaches into the gap between the sets: a band the generator places keeps the gap past the tail,
# and where both RX bands are given the tail has to fit in the gap.
TX_TAIL_EXTRA_MM   = 0.0
TX_STEPPED_ANGLE_DEG = 45           # angle of the steps to the turns
TX_INSIDE_VIA_DISTANCE_MM = 0.2    # the via that joins the two TX layers, moved this far inside the first turn
                                    # (at most TX_OFFSET_MM - via radius - half an RX trace - MIN_CLEARANCE_MM)

# The two TX layers (they must differ).  The wiki's Recommended Combination: TX on Top + Inner 2, RX on
# Top + Inner 1.  Both sets may use the same layers.
TX_LAYER_A = 1
TX_LAYER_B = 3

# How the TX makes way for this set's RX fingers (RX_TABS, Dual_RX1_Parameters.py); not used without fingers:
#   TX_SERIES_UNDERPASS_LAYER ("single" or "series"): "auto" or the layer of the go-around brackets (and of the
#     inner tail of a one-layer TX)
#   TX_PARALLEL_BREAK_STYLE ("parallel"): "stitched" (the turns on the finger's layer stop at a via on each side
#     of the finger) or "staggered" (they go around it, with brackets outside the turns)
TX_SERIES_UNDERPASS_LAYER = "auto"
TX_PARALLEL_BREAK_STYLE = "stitched"

# This set's own TX_AC_RESISTANCE_FACTOR (the electrical estimate; None = the board's value)
TX_AC_RESISTANCE_FACTOR = None

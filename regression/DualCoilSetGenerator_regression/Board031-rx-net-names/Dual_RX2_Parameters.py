"""
Dual_RX2_Parameters.py  -  the receiver (RX) coils of set 2, the outer set.  Dual_RX1_Parameters.py has the
same names for set 1.

The names are the Single Coil Set Generator's own (RX_Parameters.py), so the wiki's Parameter Reference describes each
one.  At the end, this set's own vias and clearance: None = the board's values (Dual_Board_Parameters.py).

Units: millimetres, degrees.  Nothing in this file is computed - edit values only.
Layers are numbered 1 = Top, 2 = Inner 1, 3 = Inner 2, 4 = Bottom (PCB_LAYERS, Dual_Board_Parameters.py).
"""

# LOOPS = electrical periods per mechanical turn (1 ... 16).  The outer set is the fine one: its LOOPS
# periods set the resolution, and the inner set's absolute angle says which period the rotor is in.  The inner
# set's angle error must stay below half an outer period (180 / LOOPS mechanical degrees).
LOOPS = 16

# Radial band occupied by the RX copper (centre line of the traces).  Give it in ONE of two ways, or not at all
# (the generator then places it, Dual_Board_Parameters.py says how):
#   INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM : the two radii of the band          (RX_R_BASE_MM / RX_A_MM = None)
#   RX_R_BASE_MM / RX_A_MM               : its centre and how far the coils swing in and out from it:
#                                          band = RX_R_BASE_MM - RX_A_MM ... RX_R_BASE_MM + RX_A_MM
#                                          (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM = None)
#   all four None                        : the generator places this band, across the gap from the other band
#                                          or between the board edges; the record file prints the values it chose
# Each pair goes together (both numbers or both None); both pairs set is an error (the band would be given twice).
INSIDE_RADIUS_MM  = 18.0
OUTSIDE_RADIUS_MM = 23.9
RX_R_BASE_MM      = None
RX_A_MM           = None

RX_TRACE_WIDTH_MM = 0.15

# Net names of this set.  They must differ from the other set's (KiCad would merge equal names).
RX_NET_PHASE_0_2 = "B_SIN"      # phases 0 and 2 (sine, +/-)
RX_NET_PHASE_1_3 = "B_COS"      # phases 1 and 3 (cosine, +/-)

# "equal_area" (the default) or "cosine_r" (a limacon): see the wiki, RX Profiles.
RX_PROFILE = "equal_area"

# Polyline resolution of one electrical period: "auto" or a multiple of 8 (48 ... 4096).
STEPS_PER_LOOP         = "auto"
RX_CHORD_TOLERANCE_MM  = 0.001

# Sub-coils per RX coil (1, 2 or 3) and their spacing in electrical degrees.
RX_SUBCOILS               = 1
RX_SUBCOIL_SPLIT_ELEC_DEG = 45.0

# The two layers of this set's RX coils on a 4-layer board (they must differ).  Both sets may use the same two
# layers: their copper never overlaps radially.  Keep one layer free of both sets' copper across set 2 (the
# recommended RX on 1 + 2 and TX on 1 + 3 leave Bottom free), so that set 1's six leads can be routed out by hand.
RX_LAYER_A = 1
RX_LAYER_B = 2

# On a 2-layer board (PCB_LAYERS = 2): the layer of the rising edges, "F.Cu" (Top) or "B.Cu" (Bottom); the
# falling edges go on the other one.  Not used on a 4-layer board.
RX_RISING_EDGE_LAYER = "F.Cu"

# Electrical angle of the outer-tip via (90 = on the tip, about 50 ... 130).
RX_VIA_ELECTRICAL_DEG = 90.0


# =============================================================================
# BRIDGING FINGERS  (the wiki: Parameter Reference, RX_TABS)
# =============================================================================
# A finger takes the coil from the outer tip of a lobe radially out across this set's TX ring, so that the coil
# can be broken out outside the TX turns:
#   "none"   = plain RX band, no fingers: the usual dual board, both RX rings broken out by hand
#   "all"    = a finger at every outer tip of every phase
#   "single" = one finger per RX coil, on two neighbouring outer tips
# Set 2's fingers reach towards the outline: the generator moves the outline out past them
# (OUTER_EDGE_TAIL_MARGIN_MM past their ends).
RX_TABS           = "none"
RX_TAB_LAYER      = "auto"      # the layer of the fingers: "auto" (the RX layer nearest the top without TX turns)
                                # or 1 ... 4; on a layer with TX turns the TX makes way for every finger
RX_TAB_LENGTH_MM  = 3.0         # a finger reaches OUTSIDE_RADIUS_MM + this; it must clear the outermost TX turn
                                # (and the go-around brackets): the checks say how long
RX_TAB_WIDTH_MM   = 1.0         # spacing of the two legs of a finger (snapped to the polyline nodes)


# =============================================================================
# THIS SET'S VIAS AND CLEARANCE  (None = the board's value, Dual_Board_Parameters.py)
# =============================================================================
# The Single Coil Set Generator's board values, for this set only.  Between the two sets the larger MIN_CLEARANCE_MM
# applies.  The KiCad file holds each via with its own size.
VIA_DIAMETER_MM   = None
VIA_DRILL_MM      = None
VIA_TYPE          = None        # "through" or "blind"
MIN_CLEARANCE_MM  = None

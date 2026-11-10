"""
Dual_StatorAssembler.py  -  puts the dual stator together from two finished Single Coil Set Generator stators: set 1
(inner) and set 2 (outer), each built by the Single Coil Set Generator's own chain from its own parameter set
(Dual_SetParameters), on one board with one bore and one outline.

    stator1 = StatorAssembly.build_stator(P1, TERMINAL_1_DEG)   the Single Coil Set Generator's RX -> TX -> assemble
    stator2 = StatorAssembly.build_stator(P2, TERMINAL_2_DEG)   -> clearances, each set turned to its own angle
    dual = assemble(P, layout, stator1, stator2)  the gap between the sets measured on the copper (Dual_DesignChecks)
    dual.write(path)                              one KiCad file: six nets, both sets' copper, bore and outline

Each set's nets and copper are put on the one board by the Single Coil Set Generator's own Stator.nets and
Stator.add_copper; this file adds only the bore, the outline and the dual title block.
Nothing to edit here.
"""

from Generator.Core import Layers
from Generator.Core.PCBWriter import KiCadBoard, page_size

from Dual_Generator.Checks import Dual_DesignChecks


def assemble(P, layout, stator1, stator2):
    """The dual stator: the two built sets on one board."""
    return DualStator(P, layout, stator1, stator2)


class DualStator:
    """The finished dual stator: the two sets, the one bore and outline, and what was measured between them."""

    def __init__(self, P, layout, stator1, stator2):
        self.P, self.layout = P, layout
        self.sets = (stator1, stator2)
        self.cx, self.cy = stator1.cx, stator1.cy
        self.bore, self.outline = float(layout.bore), float(layout.outline)
        self.extent1 = Dual_DesignChecks.copper_extent(stator1)      # (innermost, outermost) copper of set 1
        self.extent2 = Dual_DesignChecks.copper_extent(stator2)
        self.gap = self.extent2[0] - self.extent1[1]                 # free ring between the sets (built copper)
        self.page_mm = page_size(P.BOARD, self.cx, self.cy, self.outline)

    def nets(self):
        """The net names of both sets, set 1 first."""
        return [net for st in self.sets for net in st.nets()]

    # ------------------------------------------------------------- output
    def write(self, path):
        """Write the dual stator to `path` (Dual_RunCoilGenerator.py chooses it: Dual_OutputFolders.py)."""
        B = self.P.BOARD
        if not path:
            raise ValueError("DualStator.write needs the file path; boards are written by Dual_RunCoilGenerator.py")
        title, comments = self.title_block()
        board = KiCadBoard(title=title, comments=comments, page=self.page_mm, thickness=B.PCB_THICKNESS_MM,
                           copper_layers=int(B.PCB_LAYERS))
        for net in self.nets():                    # all six nets first, then each set's copper
            board.net(net)
        for st in self.sets:
            st.add_copper(board)
        board.circle((self.cx, self.cy), self.bore, "Edge.Cuts", B.EDGE_LINE_WIDTH_MM)
        board.circle((self.cx, self.cy), self.outline, "Edge.Cuts", B.EDGE_LINE_WIDTH_MM)
        board.save(path, B.MIN_CLEARANCE_MM)
        return path

    def title_block(self):
        """(title, comment lines) for the KiCad title block: one line per set, the radii, the generator."""
        w = lambda l: Layers.LAYER_WORDS.get(l, l)
        f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
        s1, s2 = self.sets
        title = f"Dual stator {s1.N}x{s2.N} loops"
        lines = []
        for k, st in ((1, s1), (2, s2)):
            Pk = st.P
            fingers = st.finger_words()           # the Single Coil Set Generator's own words for the TX and the fingers
            lines.append(f"Set {k}: Loops: {st.N}, RX Band: {f(st.ri)} ... {f(st.ro)} mm, SIN: Net {Pk.RX_NET_PHASE_0_2}, "
                         f"COS: Net {Pk.RX_NET_PHASE_1_3}, Rising: {w(st.rising_layer)}, Falling: {w(st.falling_layer)}, "
                         + (f"{fingers}, " if not fingers.endswith("None") else "")
                         + f"TX: Net {Pk.TX_NET}, {st.tx_words()}, Ends at {f(st.terminal_deg)} deg")
        comments = [
            lines[0],                                                                          # Comment1 (bottom)
            lines[1],
            f"Radius-Outer: {f(self.outline)} mm, Radius-Inner: {f(self.bore)} mm, Gap between the sets: "
            f"{f(self.gap)} mm (r = {f(self.extent1[1])} ... {f(self.extent2[0])} mm)",
            f"Width-TX: {f(float(s1.P.TX_TRACE_WIDTH_MM))} / {f(float(s2.P.TX_TRACE_WIDTH_MM))} mm, Width-RX: "
            f"{f(float(s1.P.RX_TRACE_WIDTH_MM))} / {f(float(s2.P.RX_TRACE_WIDTH_MM))} mm, "
            f"Layers: {int(s1.P.PCB_LAYERS)}",                                                     # Comment4
            "Generator: Dual_StatorAssembler.py (each set built by the Single Coil Set Generator)",
        ]
        return title, comments

    def summary(self):
        """The stator's lines for the run's output and for Parameters.txt: the sets, the layout and the gap measured
        on the built copper."""
        f = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
        lines = [f"Dual stator: set 1 (inner) {self.sets[0].N} loop(s), set 2 (outer) {self.sets[1].N} loop(s); "
                 f"bore r = {f(self.bore)} mm, outline r = {f(self.outline)} mm"]
        lines += ["  " + ln for ln in self.layout.lines()]
        lines.append(f"  on the built copper: set 1 r = {f(self.extent1[0])} ... {f(self.extent1[1])} mm, set 2 r = "
                     f"{f(self.extent2[0])} ... {f(self.extent2[1])} mm, {f(self.gap)} mm free between them")
        for k, st in ((1, self.sets[0]), (2, self.sets[1])):
            lines.append(f"Set {k} ({'inner' if k == 1 else 'outer'}), TX ends at {st.terminal_deg:g} deg, RX pattern "
                         f"zero at {st.rotation_deg:.2f} deg:")
            lines += ["  " + ln for ln in st.summary().split("\n")]
        return "\n".join(lines)

"""
test_loops_sweep.py  -  set 2's loop count up to 32 against the radius its RX band starts at.  Each case writes only the
stator (--stator) for one loop count and one radius (RX2 band 6 mm wide, RX1 band below it, TX 2 + 3 turns per layer,
Board001-default's other values) and holds the generator to one of two outcomes:

    refused   return code 1, an ERROR, and no file;
    written   return code 0, both coils of each set closed through their vias, set 2's tip vias repeating every period
              with the cosine a quarter period from the sine, and every place where two nets come closer than
              MIN_CLEARANCE_MM announced by a clearance warning in the run (as the invariants ask of every board).

A written board that hides a clearance problem, or a run that neither refuses nor writes, fails.  The radii bracket
the 32-loop limit measured when the limit was raised from 16 to 32: the tip vias of the four phases need about 1.2 mm
of arc per quarter loop at the band start, so 32 loops need a band from about r = 24 mm; inside about 20 mm the vias
touch the other phases and the run stops.
"""

import time
import unittest

import harness as H
import RegressionTools as RT

# (loops, RX2 band start in mm, what must happen)
CASES = (
    (16, 18.0, "written"), (24, 18.0, "written"), (32, 18.0, "refused"),
    (32, 22.0, "written"), (24, 24.0, "written"), (32, 24.0, "written"), (32, 30.0, "written"),
)
SECONDS = 240          # one case, built from nothing (a 32-loop stator takes about 20 ... 60 s)


def overrides(loops, r):
    return {"RX2.LOOPS": loops, "TX1.TX_TURNS": 2, "TX2.TX_TURNS": 3,
            "RX1.INSIDE_RADIUS_MM": r - 7.5, "RX1.OUTSIDE_RADIUS_MM": r - 2.1,
            "RX2.INSIDE_RADIUS_MM": r, "RX2.OUTSIDE_RADIUS_MM": r + 6.0, "BOARD.PAGE_SIZE_MM": (200, 200),
            "SILK.SILKSCREEN_SUGGESTION": False}


class LoopsAgainstRadius(unittest.TestCase):
    def test_refused_or_written_clean(self):
        for loops, r, want in CASES:
            with self.subTest(loops=loops, r=r):
                t0 = time.time()
                res = H.write(overrides(loops, r), ["--no-color", "--stator"])
                self.assertLess(time.time() - t0, SECONDS, "the case took too long")
                tail = res.out[-1500:]
                if want == "refused":
                    self.assertEqual(res.rc, 1, tail)
                    self.assertTrue(res.has(r"ERROR"), tail)
                    self.assertTrue(res.has(r"Nothing was written"), tail)
                    continue
                self.assertEqual(res.rc, 0, tail)
                b = res.stator
                need = res.p("BOARD", "MIN_CLEARANCE_MM")
                d, where = RT.min_clearance(b, max_interest=need + 0.5)
                if d < need - 1e-6:
                    self.assertTrue(res.has(r"WARNING.*(clearance|from other copper)"),
                                    f"{d:.4f} mm between {where}, below {need} mm, and the run did not warn")
                for k in (1, 2):
                    for name in ("RX_NET_PHASE_0_2", "RX_NET_PHASE_1_3"):
                        c = RT.connectivity(b, b.net_id[res.p(f"RX{k}", name)])
                        self.assertEqual(c["components"], 1, f"set {k} {name} in pieces")
                        self.assertEqual(c["loose_ends"], [], f"set {k} {name}: free ends not on a via")
                period, tips = 360.0 / loops, {}
                for coil in ("RX_NET_PHASE_0_2", "RX_NET_PHASE_1_3"):
                    pat = RT.tip_via_pattern(b.via[b.via_net == b.net_id[res.p("RX2", coil)]], b.centre, loops)
                    for edge in ("inner", "outer"):
                        full = sorted(a for a, c in pat[edge] if c == loops)
                        self.assertEqual(len(full), 2, f"{coil} {edge}: {pat[edge]}")
                        tips[coil, edge] = full[0]
                for edge in ("inner", "outer"):
                    d = RT.period_offset(tips["RX_NET_PHASE_0_2", edge], tips["RX_NET_PHASE_1_3", edge], period / 2)
                    self.assertAlmostEqual(min(d, period / 2 - d), period / 4, delta=0.05)

    def test_record_and_summary_name_the_loops(self):
        res = H.write(overrides(32, 30.0), ["--no-color", "--stator"])
        self.assertEqual(res.rc, 0, res.out[-1500:])
        self.assertTrue(res.has(r"set 2 \(outer\) 32 loop\(s\)"))
        self.assertTrue(res.has(r"32 loop\(s\) -> 32 electrical period\(s\) per turn, unique range 11\.25 deg"))
        self.assertTrue(res.has(r"DualCoil_[0-9.]+_[0-9.]+_1x32_"), "the folder name carries the loops")


if __name__ == "__main__":
    unittest.main()

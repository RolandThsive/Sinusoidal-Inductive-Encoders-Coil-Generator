"""
test_loops_sweep.py  -  LOOPS up to 32 against the radius the RX band starts at.  Each case writes only the stator
(--stator) for one loop count and one radius (RX band 7 mm wide, board edges 2 mm inside it and 7 mm past it, one
finger per coil, Board001-default's other values: 2 layers, 0.8 mm vias, 0.2 mm traces and clearance) and holds
the generator to one of two outcomes:

    refused   return code 1, an ERROR, and no file;
    written   return code 0, both coils closed through their vias, the tip vias repeating every period with the
              cosine a quarter period from the sine, and every place where two nets come closer than MIN_CLEARANCE_MM
              announced by a clearance warning in the run (as the invariants ask of every board).

A written board that hides a clearance problem, or a run that neither refuses nor writes, fails.  The tip vias need
about twice the radius at 32 loops that they need at 16: with these settings 32 loops are refused at 26 mm (a tip
via touches the next phase) and build clean from about 32 mm.
"""

import time
import unittest

import harness as H
import RegressionTools as RT

# (loops, RX band start in mm, what must happen)
CASES = ((16, 16.2, "written"), (32, 16.2, "refused"), (24, 26.0, "written"), (32, 26.0, "refused"),
         (32, 32.0, "written"))
SECONDS = 240


def overrides(loops, r):
    return {"LOOPS": loops, "INSIDE_RADIUS_MM": r, "OUTSIDE_RADIUS_MM": r + 7.0, "INNER_EDGE_RADIUS_MM": r - 2.0,
            "OUTER_EDGE_RADIUS_MM": r + 14.0, "RX_TABS": "single", "SILK.SILKSCREEN_SUGGESTION": False}


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
                need = res.params["MIN_CLEARANCE_MM"]
                d, where = RT.min_clearance(b, max_interest=need + 0.5)
                if d < need - 1e-6:
                    self.assertTrue(res.has(r"WARNING.*(clearance|from other copper)"),
                                    f"{d:.4f} mm between {where}, below {need} mm, and the run did not warn")
                period, tips = 360.0 / loops, {}
                for name in ("RX_NET_PHASE_0_2", "RX_NET_PHASE_1_3"):
                    nid = b.net_id[res.params[name]]
                    c = RT.connectivity(b, nid)
                    self.assertEqual(c["components"], 1, f"{name} in pieces")
                    self.assertEqual(c["loose_ends"], [], f"{name}: free ends not on a via")
                    pat = RT.tip_via_pattern(b.via[b.via_net == nid], b.centre, loops)
                    full = sorted(a for a, n in pat["inner"] if n == loops)     # the finger vias lie past the band
                    self.assertEqual(len(full), 2, f"{name} inner tips: {pat['inner']}")
                    tips[name] = full[0]
                d = RT.period_offset(tips["RX_NET_PHASE_0_2"], tips["RX_NET_PHASE_1_3"], period / 2)
                self.assertAlmostEqual(min(d, period / 2 - d), period / 4, delta=0.05)

    def test_record_and_summary_name_the_loops(self):
        res = H.write(overrides(32, 32.0), ["--no-color", "--stator"])
        self.assertEqual(res.rc, 0, res.out[-1500:])
        self.assertTrue(res.has(r"32 loop\(s\) -> 32 electrical period\(s\) per turn, unique range 11\.25 deg"))


if __name__ == "__main__":
    unittest.main()

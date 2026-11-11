# 19. Dual Layout

A dual board is two Single Coil Set Generator boards on one PCB, one inside the other. Before either set is built, the
generator decides where each sits: the RX band of each set, the bore, the outline and the gap between the sets. There
is no mode to choose. You give what you know, and the generator places the rest. This page gives the rules, all 32
combinations of what can be given, and for each one a picture of a board the generator really builds.

## 19.1 How A Dual Board Is Made From Two Single Boards

The Dual Coil Set Generator does not have its own coil builder. Each set of a dual board is a Single Coil Set Generator
board, built by the Single Coil Set Generator's own code:

1. **The layout.** From the dual parameter files, the layout (`Dual_TrackLayout.py`, the rules on this page) decides
   the two RX bands, the bore and the outline. It uses the Single Coil Set Generator's own formulas on each set's own
   values: how far set 1's copper reaches past its RX band (the TX turns, the TX tail, the RX bridging fingers and the
   TX's go-around brackets, `BoardLayout.outer_copper_reach`), where set 2's copper starts inside its band (its inner
   vias, where the RX builder puts them: on the band start at `RX_VIA_ELECTRICAL_DEG` = 90, a little inside the band at
   any other angle, `RX_Builder.inner_via_radius`), and how much room the outline needs past the RX2 band
   (`BoardLayout.outer_edge_room`, plus the overhang of ring 2 of the rotor when it covers the TX2 turns).
2. **Two Single parameter sets.** For each set, `Dual_SetParameters.build` puts together exactly the parameter set of
   a Single Coil Set Generator board: the board values of `Dual_Board_Parameters.py`, the set's own RX, TX, rotor and IC
   files, the vias and clearance the set gives itself, and the band and edges the layout decided.
3. **The Single Coil Set Generator's checks and builders.** Each set is checked by the Single Coil Set Generator's
   checker, which also checks a given edge against its own set's band, and built by the Single Coil Set Generator's
   builders, turned so that its TX ends sit at `TERMINAL_1_DEG` or `TERMINAL_2_DEG`.
4. **One board.** Both sets are written into one `Stator.kicad_pcb`, with one rotor disc carrying both rings. Then
   the checks between the sets run on the built copper: the gap between the sets, different nets too close, the layer
   left free for set 1's leads and the distances between the rotor rings.

So whatever a Single board can do, each set of a dual board can do. The Dual refuses only what the Single refuses for
that set, plus what two sets on one board cannot share.

## 19.2 The Four Rules

From the centre out, the board is a stack:

```text
bore | RX1 band | TX1 ring | gap | RX2 band | TX2 ring | outline
```

The TX rings always follow from their RX bands, so five things can be given, each one or not (`None`): the RX1 band
(`Dual_RX1_Parameters.py`), the RX2 band (`Dual_RX2_Parameters.py`), the bore (`INNER_EDGE_RADIUS_MM`), the outline
(`OUTER_EDGE_RADIUS_MM`) and the gap (`TRACK_GAP_MM`, all three in `Dual_Board_Parameters.py`). A band is given in one
of the Single Coil Set Generator's two ways, as `INSIDE_RADIUS_MM` / `OUTSIDE_RADIUS_MM` or as `RX_R_BASE_MM` /
`RX_A_MM`; a half given pair stays an error, as in the Single Coil Set Generator. Four rules place what is not given, so
every spacing in the stack follows from the sets' own settings:

| What | Rule |
|---|---|
| The gap | `TRACK_GAP_MM`, or the larger of the two sets' `MIN_CLEARANCE_MM` when it is `None`. A band the generator places sits exactly that far from the other set. When both bands are given, it is the least the gap between them may be. |
| A band not given | Placed across the gap from the band that is given: RX2 outwards from set 1's copper, or RX1 inwards from set 2's. Its far end goes to the board edge on that side when that edge is given (the outline less the TX2 ring and the margins, or the bore plus `INNER_EDGE_INSET_MM`). Otherwise the band is as wide as the given one. |
| An edge not given | Comes from the band, as in the Single Coil Set Generator: the bore is the RX1 band start less `INNER_EDGE_INSET_MM`, the outline the RX2 band end plus the TX2 ring and the margins. An edge that is given is used as given and checked by the Single Coil Set Generator's own rule. |
| No band at all | Needs both edges. Both bands are fitted between them, and `BAND_SPLIT` shares the width that is left. |

Of the 32 combinations, 26 build. The other 6 give no band and at most one edge, so there is nothing to size a band
from, and the checker says what to give. A combination that builds can still be refused for a real reason, with a
message that names what to change: a given outline may leave a placed band no width, a placed RX1 band may push the bore
to zero, or the Single Coil Set Generator may refuse a set.

The record (`Parameters.txt`) and the console name the combination a run used, with every radius, for example:

```text
layout: RX1 band given, RX2 band placed TRACK_GAP_MM out and as wide as RX1; bore and outline from the bands (combination 10 of 32)
  RX1 band r = 9.7 ... 16.05 mm (RX_R_BASE_MM 12.875, RX_A_MM 3.175): INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM as given
  RX2 band r = 19.55 ... 25.9 mm (RX_R_BASE_MM 22.725, RX_A_MM 3.175): placed by the generator
  bore r = 8.5 mm (RX1 band start - INNER_EDGE_INSET_MM), outline r = 29.5 mm (RX2 band end + the TX2 ring and the margin)
  set 1 copper reaches r = 18.75 mm; set 2 copper starts at r = 19.25 mm: gap 0.5 mm (TRACK_GAP_MM = 0.5)
```

## 19.3 The 32 Combinations

The table lists every combination. The last column says what the dual parameter files had to say for it before the
layout modes were removed; a combination marked "refused" could not be built at all. Under the table, each combination
has its own section, with a picture of its reference board in the regression suite cut along one radius: the copper is
what that cut meets in the board's `Stator.kicad_pcb`, and the radii and what was given come from its `Parameters.txt`.
Black marks what was given, blue what the generator placed or worked out.

<!-- BEGIN: written by docs/tools/dual_layout_pictures.py from the reference boards; do not edit by hand -->

| # | RX1 band | RX2 band | Bore | Outline | `TRACK_GAP_MM` | What the generator does | Before |
|---|---|---|---|---|---|---|---|
| [1](#1931-combination-1-both-rx-bands-given) | given | given | – | – | – | Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None). | DUAL_MODE 2 |
| [2](#1932-combination-2-both-rx-bands-and-track_gap_mm-given) | given | given | – | – | given | Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM. | refused |
| [3](#1933-combination-3-both-rx-bands-and-bore-given) | given | given | given | – | – | Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None). | refused |
| [4](#1934-combination-4-both-rx-bands-bore-and-track_gap_mm-given) | given | given | given | – | given | Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM. | refused |
| [5](#1935-combination-5-both-rx-bands-and-outline-given) | given | given | – | given | – | Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None). | refused |
| [6](#1936-combination-6-both-rx-bands-outline-and-track_gap_mm-given) | given | given | – | given | given | Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM. | refused |
| [7](#1937-combination-7-both-rx-bands-bore-and-outline-given) | given | given | given | given | – | Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None). | DUAL_MODE 4 |
| [8](#1938-combination-8-both-rx-bands-bore-outline-and-track_gap_mm-given) | given | given | given | given | given | Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM. | refused |
| [9](#1939-combination-9-rx1-band-given) | given | – | – | – | – | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [10](#19310-combination-10-rx1-band-and-track_gap_mm-given) | given | – | – | – | given | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | DUAL_MODE 3 |
| [11](#19311-combination-11-rx1-band-and-bore-given) | given | – | given | – | – | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [12](#19312-combination-12-rx1-band-bore-and-track_gap_mm-given) | given | – | given | – | given | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [13](#19313-combination-13-rx1-band-and-outline-given) | given | – | – | given | – | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [14](#19314-combination-14-rx1-band-outline-and-track_gap_mm-given) | given | – | – | given | given | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [15](#19315-combination-15-rx1-band-bore-and-outline-given) | given | – | given | given | – | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [16](#19316-combination-16-rx1-band-bore-outline-and-track_gap_mm-given) | given | – | given | given | given | The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [17](#19317-combination-17-rx2-band-given) | – | given | – | – | – | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [18](#19318-combination-18-rx2-band-and-track_gap_mm-given) | – | given | – | – | given | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | DUAL_MODE 3 |
| [19](#19319-combination-19-rx2-band-and-bore-given) | – | given | given | – | – | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [20](#19320-combination-20-rx2-band-bore-and-track_gap_mm-given) | – | given | given | – | given | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. | refused |
| [21](#19321-combination-21-rx2-band-and-outline-given) | – | given | – | given | – | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [22](#19322-combination-22-rx2-band-outline-and-track_gap_mm-given) | – | given | – | given | given | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [23](#19323-combination-23-rx2-band-bore-and-outline-given) | – | given | given | given | – | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [24](#19324-combination-24-rx2-band-bore-outline-and-track_gap_mm-given) | – | given | given | given | given | The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. | refused |
| [25](#19325-combination-25-nothing-given) | – | – | – | – | – | Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them. | refused |
| [26](#19326-combination-26-track_gap_mm-given) | – | – | – | – | given | Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them. TRACK_GAP_MM alone does not help: it is a distance, not a place. | refused |
| [27](#19327-combination-27-bore-given) | – | – | given | – | – | Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band. | refused |
| [28](#19328-combination-28-bore-and-track_gap_mm-given) | – | – | given | – | given | Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band. | refused |
| [29](#19329-combination-29-outline-given) | – | – | – | given | – | Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band. | refused |
| [30](#19330-combination-30-outline-and-track_gap_mm-given) | – | – | – | given | given | Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band. | refused |
| [31](#19331-combination-31-bore-and-outline-given) | – | – | given | given | – | Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, MIN_CLEARANCE_MM (TRACK_GAP_MM is None), set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths). | refused |
| [32](#19332-combination-32-bore-outline-and-track_gap_mm-given) | – | – | given | given | given | Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, TRACK_GAP_MM, set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths). | DUAL_MODE 1 |

### 19.3.1 Combination 1: Both RX Bands Given

Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).

![Combination 1: Both RX bands given. Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_01.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board001-default` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 7.25 mm, from the band | 26.875 mm, from the band | 3.725 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.2 Combination 2: Both RX Bands And TRACK_GAP_MM Given

Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.

![Combination 2: Both RX bands and TRACK_GAP_MM given. Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_02.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board083-layout-02-both-bands-and-gap` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 7.25 mm, from the band | 26.875 mm, from the band | 3.725 mm (at least TRACK_GAP_MM 3) |

### 19.3.3 Combination 3: Both RX Bands And Bore Given

Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).

![Combination 3: Both RX bands and bore given. Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_03.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board084-layout-03-both-bands-and-bore` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 6 mm, given | 26.875 mm, from the band | 3.725 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.4 Combination 4: Both RX Bands, Bore And TRACK_GAP_MM Given

Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.

![Combination 4: Both RX bands, bore and TRACK_GAP_MM given. Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_04.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board085-layout-04-both-bands-bore-and-gap` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 6 mm, given | 26.875 mm, from the band | 3.725 mm (at least TRACK_GAP_MM 3) |

### 19.3.5 Combination 5: Both RX Bands And Outline Given

Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).

![Combination 5: Both RX bands and outline given. Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_05.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board086-layout-05-both-bands-and-outline` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 7.25 mm, from the band | 28 mm, given | 3.725 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.6 Combination 6: Both RX Bands, Outline And TRACK_GAP_MM Given

Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.

![Combination 6: Both RX bands, outline and TRACK_GAP_MM given. Both bands are used as given. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_06.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board087-layout-06-both-bands-outline-and-gap` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 7.25 mm, from the band | 28 mm, given | 3.725 mm (at least TRACK_GAP_MM 3) |

### 19.3.7 Combination 7: Both RX Bands, Bore And Outline Given

Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).

![Combination 7: Both RX bands, bore and outline given. Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least MIN_CLEARANCE_MM (TRACK_GAP_MM is None).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_07.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board004-layout-07-all-given` | 9.7 ... 16.05 mm, given | 19.55 ... 25.9 mm, given | 8.5 mm, given | 29.5 mm, given | 0.5 mm (at least MIN_CLEARANCE_MM 0.2) |

### 19.3.8 Combination 8: Both RX Bands, Bore, Outline And TRACK_GAP_MM Given

Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.

![Combination 8: Both RX bands, bore, outline and TRACK_GAP_MM given. Both bands are used as given. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins. The gap between set 1's outermost copper and set 2's innermost copper is measured, and must be at least TRACK_GAP_MM.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_08.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board088-layout-08-everything-given` | 8.45 ... 11.7 mm, given | 18 ... 23.9 mm, given | 6 mm, given | 28 mm, given | 3.725 mm (at least TRACK_GAP_MM 3) |

### 19.3.9 Combination 9: RX1 Band Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 9: RX1 band given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_09.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board089-layout-09-rx1-band` | 8.45 ... 11.7 mm, given | 14.425 ... 17.675 mm, placed | 7.25 mm, from the band | 20.65 mm, from the band | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.10 Combination 10: RX1 Band And TRACK_GAP_MM Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 10: RX1 band and TRACK_GAP_MM given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_10.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board003-layout-10-rx1-band-and-gap` | 9.7 ... 16.05 mm, given | 19.55 ... 25.9 mm, placed | 8.5 mm, from the band | 29.5 mm, from the band | 0.5 mm (at least TRACK_GAP_MM 0.5) |

### 19.3.11 Combination 11: RX1 Band And Bore Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 11: RX1 band and bore given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_11.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board090-layout-11-rx1-band-and-bore` | 8.45 ... 11.7 mm, given | 14.425 ... 17.675 mm, placed | 6 mm, given | 20.65 mm, from the band | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.12 Combination 12: RX1 Band, Bore And TRACK_GAP_MM Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 12: RX1 band, bore and TRACK_GAP_MM given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and is as wide as the RX1 band. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_12.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board091-layout-12-rx1-band-bore-and-gap` | 8.45 ... 11.7 mm, given | 15.275 ... 18.525 mm, placed | 6 mm, given | 21.5 mm, from the band | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.13 Combination 13: RX1 Band And Outline Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 13: RX1 band and outline given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_13.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board092-layout-13-rx1-band-and-outline` | 8.45 ... 11.7 mm, given | 14.425 ... 25.025 mm, placed | 7.25 mm, from the band | 28 mm, given | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.14 Combination 14: RX1 Band, Outline And TRACK_GAP_MM Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 14: RX1 band, outline and TRACK_GAP_MM given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_14.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board093-layout-14-rx1-band-outline-and-gap` | 8.45 ... 11.7 mm, given | 15.275 ... 25.025 mm, placed | 7.25 mm, from the band | 28 mm, given | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.15 Combination 15: RX1 Band, Bore And Outline Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 15: RX1 band, bore and outline given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_15.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board094-layout-15-rx1-band-bore-and-outline` | 8.45 ... 11.7 mm, given | 14.425 ... 25.025 mm, placed | 6 mm, given | 28 mm, given | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.16 Combination 16: RX1 Band, Bore, Outline And TRACK_GAP_MM Given

The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 16: RX1 band, bore, outline and TRACK_GAP_MM given. The RX2 band is placed so that set 2's innermost copper (its inner vias) sits TRACK_GAP_MM out from set 1's outermost copper (its TX ring, tail or fingers), and runs out to the outline, less the TX2 ring and the margins. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_16.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board095-layout-16-rx1-band-bore-outline-and-gap` | 8.45 ... 11.7 mm, given | 15.275 ... 25.025 mm, placed | 6 mm, given | 28 mm, given | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.17 Combination 17: RX2 Band Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 17: RX2 band given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_17.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board096-layout-17-rx2-band` | 9.375 ... 15.275 mm, placed | 18 ... 23.9 mm, given | 8.175 mm, from the band | 26.875 mm, from the band | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.18 Combination 18: RX2 Band And TRACK_GAP_MM Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 18: RX2 band and TRACK_GAP_MM given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_18.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board097-layout-18-rx2-band-and-gap` | 8.525 ... 14.425 mm, placed | 18 ... 23.9 mm, given | 7.325 mm, from the band | 26.875 mm, from the band | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.19 Combination 19: RX2 Band And Bore Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 19: RX2 band and bore given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_19.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board098-layout-19-rx2-band-and-bore` | 7.2 ... 15.275 mm, placed | 18 ... 23.9 mm, given | 6 mm, given | 26.875 mm, from the band | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.20 Combination 20: RX2 Band, Bore And TRACK_GAP_MM Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.

![Combination 20: RX2 band, bore and TRACK_GAP_MM given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is the RX2 band end plus the room the TX2 ring, its tail or fingers, and the margins need.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_20.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board099-layout-20-rx2-band-bore-and-gap` | 7.2 ... 14.425 mm, placed | 18 ... 23.9 mm, given | 6 mm, given | 26.875 mm, from the band | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.21 Combination 21: RX2 Band And Outline Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 21: RX2 band and outline given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_21.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board100-layout-21-rx2-band-and-outline` | 9.375 ... 15.275 mm, placed | 18 ... 23.9 mm, given | 8.175 mm, from the band | 28 mm, given | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.22 Combination 22: RX2 Band, Outline And TRACK_GAP_MM Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 22: RX2 band, outline and TRACK_GAP_MM given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and is as wide as the RX2 band. The bore is the RX1 band start less INNER_EDGE_INSET_MM. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_22.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board101-layout-22-rx2-band-outline-and-gap` | 8.525 ... 14.425 mm, placed | 18 ... 23.9 mm, given | 7.325 mm, from the band | 28 mm, given | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.23 Combination 23: RX2 Band, Bore And Outline Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 23: RX2 band, bore and outline given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits MIN_CLEARANCE_MM (TRACK_GAP_MM is None) inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_23.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board102-layout-23-rx2-band-bore-and-outline` | 7.2 ... 15.275 mm, placed | 18 ... 23.9 mm, given | 6 mm, given | 28 mm, given | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.24 Combination 24: RX2 Band, Bore, Outline And TRACK_GAP_MM Given

The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.

![Combination 24: RX2 band, bore, outline and TRACK_GAP_MM given. The RX1 band is placed so that set 1's outermost copper (its TX ring, tail or fingers) sits TRACK_GAP_MM inside set 2's innermost copper (its inner vias), and starts at the bore plus INNER_EDGE_INSET_MM. The bore is used as given; the Single Coil Set Generator checks that it leaves INNER_EDGE_INSET_MM inside the RX1 band. The outline is used as given; the Single Coil Set Generator checks that it leaves room for the TX2 ring, its tail or fingers, and the margins.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_24.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board103-layout-24-rx2-band-bore-outline-and-gap` | 7.2 ... 14.425 mm, placed | 18 ... 23.9 mm, given | 6 mm, given | 28 mm, given | 1 mm (at least TRACK_GAP_MM 1) |

### 19.3.25 Combination 25: Nothing Given

Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them.

![Combination 25: nothing given. Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_25.svg)

```text
ERROR   no RX band and no board edge is given: there is nothing to size the bands from. Give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py), or both board edges (INNER_EDGE_RADIUS_MM and OUTER_EDGE_RADIUS_MM, Dual_Board_Parameters.py) to fit both bands between them
```

### 19.3.26 Combination 26: TRACK_GAP_MM Given

Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them. TRACK_GAP_MM alone does not help: it is a distance, not a place.

![Combination 26: TRACK_GAP_MM given. Refused: no RX band and no board edge, so there is nothing to size the bands from. Give one RX band, or both board edges to fit both bands between them. TRACK_GAP_MM alone does not help: it is a distance, not a place.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_26.svg)

```text
ERROR   no RX band and no board edge is given: there is nothing to size the bands from. Give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py), or both board edges (INNER_EDGE_RADIUS_MM and OUTER_EDGE_RADIUS_MM, Dual_Board_Parameters.py) to fit both bands between them
```

### 19.3.27 Combination 27: Bore Given

Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.

![Combination 27: Bore given. Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_27.svg)

```text
ERROR   no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing to fit both bands between the edges. Set OUTER_EDGE_RADIUS_MM (Dual_Board_Parameters.py), or give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)
```

### 19.3.28 Combination 28: Bore And TRACK_GAP_MM Given

Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.

![Combination 28: Bore and TRACK_GAP_MM given. Refused: no RX band and only the bore, so the room for the two bands has no other end. Give OUTER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_28.svg)

```text
ERROR   no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing to fit both bands between the edges. Set OUTER_EDGE_RADIUS_MM (Dual_Board_Parameters.py), or give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)
```

### 19.3.29 Combination 29: Outline Given

Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.

![Combination 29: Outline given. Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_29.svg)

```text
ERROR   no RX band is given and of the board edges only the outline: INNER_EDGE_RADIUS_MM is missing to fit both bands between the edges. Set INNER_EDGE_RADIUS_MM (Dual_Board_Parameters.py), or give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)
```

### 19.3.30 Combination 30: Outline And TRACK_GAP_MM Given

Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.

![Combination 30: Outline and TRACK_GAP_MM given. Refused: no RX band and only the outline, so the room for the two bands has no other end. Give INNER_EDGE_RADIUS_MM too, and the bands are fitted between the edges, or give one RX band.](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_30.svg)

```text
ERROR   no RX band is given and of the board edges only the outline: INNER_EDGE_RADIUS_MM is missing to fit both bands between the edges. Set INNER_EDGE_RADIUS_MM (Dual_Board_Parameters.py), or give one RX band (INSIDE_RADIUS_MM / OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)
```

### 19.3.31 Combination 31: Bore And Outline Given

Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, MIN_CLEARANCE_MM (TRACK_GAP_MM is None), set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths).

![Combination 31: Bore and outline given. Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, MIN_CLEARANCE_MM (TRACK_GAP_MM is None), set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_31.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board104-layout-31-both-edges` | 7.2 ... 14.75 mm, placed | 17.475 ... 25.025 mm, placed | 6 mm, given | 28 mm, given | 0.15 mm (at least MIN_CLEARANCE_MM 0.15) |

### 19.3.32 Combination 32: Bore, Outline And TRACK_GAP_MM Given

Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, TRACK_GAP_MM, set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths).

![Combination 32: Bore, outline and TRACK_GAP_MM given. Both bands are fitted between the two edges as given: from the bore, INNER_EDGE_INSET_MM, the RX1 band, the TX1 ring, TRACK_GAP_MM, set 2's inner vias, the RX2 band, and the TX2 ring with the margins up to the outline. BAND_SPLIT shares what is left between the two bands (0.5: equal widths).](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_layout/combination_32.svg)

| Reference board | RX1 band | RX2 band | Bore | Outline | Gap between the sets |
|---|---|---|---|---|---|
| `Board002-layout-32-fitted-bands` | 9.7 ... 16.05 mm, placed | 19.55 ... 25.9 mm, placed | 8.5 mm, given | 29.5 mm, given | 0.5 mm (at least TRACK_GAP_MM 0.5) |

<!-- END: written by docs/tools/dual_layout_pictures.py -->

## 19.4 Files From Before: `DUAL_MODE`

A parameter file written for the layout modes still works. `DUAL_MODE` is no longer read: the checker warns that it is
no longer used, and the layout follows from what the file gives, which is what the mode needed anyway. Every board of
the regression suite built with a mode is byte for byte the same board without it:

| `DUAL_MODE` | What It Needed | Now |
|---|---|---|
| 1 | `TRACK_GAP_MM` and both edges, no band | Combination 32 |
| 2 | Both bands, no gap, no edges | Combination 1 |
| 3 | One band and `TRACK_GAP_MM`, no edges | Combination 10 (RX1 given) or 18 (RX2 given) |
| 4 | Both bands and both edges, no gap | Combination 7 |

The other 27 combinations used to be refused because no mode matched them.

## 19.5 How The Pictures Are Made

The pictures and the combination sections above are written by `docs/tools/dual_layout_pictures.py` (standard
library only) from the reference boards in `regression/DualCoilSetGenerator_regression`: the board named
`BoardNNN-layout-<n>-...` for combination n, or `Board001-default` for combination 1. The regression tests hold those
boards byte for byte against what the generator builds, so the pictures always show what it builds today. CI runs
`python docs/tools/dual_layout_pictures.py --check`, which fails when a picture or this page is not what the boards
give; after a change that moves a board, run the script without `--check` and commit what it writes.

## 19.6 Related Pages

- [Board Features - Dual Coil Set Generator](Board-Features-Dual-Coil-Set-Generator.md): the stack from the centre out,
  and the checks on the finished board.
- [Quick Guide To Parameters Selections - Dual Coil Set Generator](Quick-Guide-To-Parameters-Selections-Dual-Coil-Set-Generator.md):
  which combination to start from.
- [Parameter Reference Dual Coil Set Generator](Parameter-Reference-Dual-Coil-Set-Generator.md): every dual parameter.
- [Board Features](Board-Features.md): the Single Coil Set Generator's edges and margins, which each set of a dual board
  keeps.

[<img align="right" src="https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2.png" alt="Sinusoidal Coil Generator logo, click to see it spin" width="72">](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2_rotor_spin_400px.webp)

| Previous | Next |
|:---|---:|
| [Board Features - Dual Coil Set Generator](Board-Features-Dual-Coil-Set-Generator.md) | [Silkscreen - Dual Coil Set Generator](Silkscreen-Dual-Coil-Set-Generator.md) |

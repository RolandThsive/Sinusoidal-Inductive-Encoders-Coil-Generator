# 21. Quick Guide To Parameters Selections - Dual Generator

A dual board is two coil sets on one board, so before it is built the generator decides where each sits: the two RX
bands, the two board edges and the gap between the sets. You give what you know and the generator places the rest;
there is no mode to choose. This page shows what to give, the two settings that only some layouts use (`BAND_SPLIT`
when no band is given, `TRACK_GAP_MM`), and a starting point for the rest. Every picture is a run of the Dual Generator
with only the named settings changed, silkscreen off; colour shows the copper layer (Top red, Inner-1 green, Inner-2
dark yellow). Each parameter is described in full in the
[Parameter Reference Dual Generator](Parameter-Reference-Dual-Generator.md).

## 21.1 What You Give

From the centre out the stator is `bore | RX1 band | TX1 ring | gap | RX2 band | TX2 ring | outline`. The TX rings
always follow from their RX bands (`TX_OFFSET_MM`, `TX_TURNS`, `TX_PITCH_MM`), so five things can be given, each one or
not (`None`): the RX1 band, the RX2 band, the bore (`INNER_EDGE_RADIUS_MM`), the outline (`OUTER_EDGE_RADIUS_MM`) and the
gap (`TRACK_GAP_MM`). The generator places what is not given by four rules:

| What | Rule |
|---|---|
| The gap | `TRACK_GAP_MM`, or the larger of the two sets' `MIN_CLEARANCE_MM` when it is `None`. A band the generator places sits exactly that far from the other set; when you give both bands, the gap between them must be at least that |
| A band you leave out | Placed across the gap from the band you give: RX2 outwards, RX1 inwards. It runs to the board edge on its side when you give that edge, and is as wide as the other band when you do not |
| An edge you leave out | Follows from its band, as in the Single Generator: the bore is the RX1 band start less `INNER_EDGE_INSET_MM`, the outline the RX2 band end plus the TX2 ring and the margins. An edge you give is used as given and checked |
| No band at all | Needs both edges: both bands are fitted between them, and `BAND_SPLIT` shares the width |

Of the 32 combinations, 26 build. The other 6 give no band and at most one edge, so there is nothing to size a band
from. [Dual Layout](Dual-Layout.md) lists all 32, each with a picture of a board the generator builds.

![Dual Parameters 1: Four Of The 32 Combinations](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_params_1_combinations.png)

*Dual Parameters 1. The same two sets (inner 1 loop, outer 16 loops, 4 + 4 series TX turns per set, pitch 0.35 mm) laid
out four ways, at the same scale. Next to each board: what was given and what the generator computed, read from the
run's `Parameters.txt` (radii in mm). Bore 7.25, outline 30, gap 3 and `BAND_SPLIT` 0.5 (combination 32) give RX1 8.45
to 14.95 and RX2 20.525 to 27.025. The default bands alone (combination 1) give bore 7.25, outline 26.875 and a measured
gap of 3.725. RX1 8.45 to 11.7 and a gap of 3 (combination 10) give RX2 17.275 to 20.525 (the same half width, 1.625)
and outline 23.5. The default bands with bore 6.5 and outline 28 (combination 7) are built as given.*

What to give:

- **Both edges** (with `TRACK_GAP_MM`, or not) when the board outline and the shaft hole are fixed (a housing, a
  bearing) and you want the largest bands that fit.
- **Both bands** when both bands matter, for example to match a known design; the board grows to suit them, unless
  you give the edges too, which are then checked.
- **One band** when one track is fixed and the other may go wherever the gap puts it. Give the edge on the other side
  as well, and the placed band runs out to it.
- **Everything** when everything is fixed and you only want it built and checked.

### 21.1.1 What The Checker Says

A combination with nothing to size a band from is refused with a message that says what to give. For example, with no
band and only the bore:

```text
ERROR   INSIDE_RADIUS_MM conflicts with OUTSIDE_RADIUS_MM, RX_R_BASE_MM, RX_A_MM, INNER_EDGE_RADIUS_MM and OUTER_EDGE_RADIUS_MM
        no RX band is given and of the board edges only the bore: OUTER_EDGE_RADIUS_MM is missing to fit both bands
        between the edges. Set OUTER_EDGE_RADIUS_MM (Dual_Board_Parameters.py), or give one RX band (INSIDE_RADIUS_MM /
        OUTSIDE_RADIUS_MM or RX_R_BASE_MM / RX_A_MM in Dual_RX1 or Dual_RX2_Parameters.py)
```

A combination that builds can still be refused for a real reason, and the message names what to change: a given
outline that leaves a placed band no room, a placed RX1 band that would push the bore to zero, or a set the Single
Generator refuses. When a band fitted to an edge comes out too narrow for its vias, a hint names the edge to move. A
parameter file from before that still has `DUAL_MODE` gets a warning that it is no longer used, and builds as before.

## 21.2 Giving A Band

Each set's band is the ring of radii its RX curves weave in, given in its own file (`Dual_RX1_Parameters.py`,
`Dual_RX2_Parameters.py`) in one of two ways, or not at all:

| Way | Parameters | The Band |
|---|---|---|
| Radii pair | `INSIDE_RADIUS_MM`, `OUTSIDE_RADIUS_MM` (with `RX_R_BASE_MM`, `RX_A_MM` = `None`) | From the inside radius to the outside radius |
| R base and A pair | `RX_R_BASE_MM`, `RX_A_MM` (with `INSIDE_RADIUS_MM`, `OUTSIDE_RADIUS_MM` = `None`) | `RX_R_BASE_MM - RX_A_MM` to `RX_R_BASE_MM + RX_A_MM` |
| Not given | All four `None` | Placed by the generator (21.1); `Parameters.txt` prints the values it chose |

Each pair goes together: a pair with only one value set is an error, and so is a band given by both pairs at once.

## 21.3 Sharing The Width: `BAND_SPLIT` (No Band Given)

When no band is given, the free radial width between the edges, after both TX rings and the gap, is shared between the two bands.
`BAND_SPLIT` is set 1's share, strictly between 0 and 1: 0.5 gives both bands the same width. A 1x / 16x board is
usually near 0.5; the more loops the fine track has, the more width it should get (a smaller `BAND_SPLIT`).

![Dual Parameters 2: BAND_SPLIT](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_params_2_band_split.png)

*Dual Parameters 2. `BAND_SPLIT` = 0.35, 0.5 (the default) and 0.65 with the bore at 7.25 mm, the outline at 30 mm and
`TRACK_GAP_MM` at 3 mm. The two bands always share 13 mm: 4.55 + 8.45, 6.5 + 6.5 and 8.45 + 4.55 mm.*

## 21.4 The Gap Between The Sets: `TRACK_GAP_MM`

`TRACK_GAP_MM` is the copper-free ring between the sets: from the outermost copper of set 1 (its TX1 ring) to the
innermost copper of set 2 (the RX2 band start minus half an RX trace or a via radius, whichever is larger). When the generator
places a band, it is the gap to leave; when both bands are given, the measured gap must be at least this. When it is
`None`, `MIN_CLEARANCE_MM` (the larger of the two sets') takes its place.

![Dual Parameters 3: TRACK_GAP_MM](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/dual_params_3_gap.png)

*Dual Parameters 3. The RX1 band given (8.45 to 11.7 mm, combination 10) and `TRACK_GAP_MM` = 0.5, 2 and 4 mm. RX2 is placed
across the gap with the same half width (1.625 mm), and the outline follows it: 21, 22.5 and 24.5 mm.*

The gap does not isolate the two sets electrically: a balanced RX band sees no net flux from a round TX ring, however
close, and what is left falls only slowly with distance. Keep the gap for the copper clearance and the solder mask. What
keeps the fine track clean is the distance from ring 1 of the rotor to the RX2 band, `ROTOR_1_TO_RX2_MM` (see
[Rotor Features - Dual Generator](Rotor-Features-Dual-Generator.md#173-distances-between-the-rings)). The rotor needs
room too: `ROTOR_TRACK_GAP_MM` (2 mm) must stay bare between the two rings, so a very small gap between the sets can
make the rotor the limit.

## 21.5 A Starting Point

The defaults are a complete 1x / 16x board on a 53.75 mm disc, built without warnings. Start from them and change one
thing at a time:

| Choice | Default | Why |
|---|---|---|
| Loops | Set 1: 1, set 2: 16 | The coarse track gives the absolute angle; its error must stay below 180 / `LOOPS` of set 2 degrees (±11.25° for 16 loops) |
| Layers | RX on Top + Inner-1, TX on Top + Inner-2, both sets | Leaves Bottom free for set 1's leads to cross set 2 |
| TX | Series, 4 turns per layer, pitch 0.35 mm, traces 0.15 mm | Enough inductance at 3 MHz for the inner tank; every turn of TX1 pushes set 2 out. A parallel ring needs a pitch of at least 0.43 mm with 0.6 mm vias |
| TX ends | `TERMINAL_1_DEG` 180, `TERMINAL_2_DEG` 0 | Opposite sides, so the two sets' breakouts stay apart |
| Frequencies | 3.0 MHz and 4.3 MHz | 43 % apart and on no small integer ratio |
| Rotor | Ring 1 inside TX1 (`ROTOR_AUTO_COVER_TX = False`), ring 2 over TX2 | Keeps the half-moon ring 1 well away from the fine band |
| Vias and clearance | 0.6 / 0.3 mm, 0.15 mm | Leave room in the inner set's tight TX ring |
| Board thickness | 3.2 mm | |

Check before generating, then generate, from the `Generators/Dual Generator` folder:

```bash
python Dual_Generator/Checks/Dual_CheckParameters.py
python Dual_Generator/Run/Dual_RunCoilGenerator.py
```

## 21.6 Related Pages

- [Quick Guide To Parameters Selections](Quick-Guide-To-Parameters-Selections.md): the band, TX and rotor choices of each
  set, which hold for each set of a dual board too, the RX fingers and the TX tail included.
- [Board Features - Dual Generator](Board-Features-Dual-Generator.md): the layout and the checks.
- [Choosing A Rotor And Stator](Choosing-A-Rotor-And-Stator.md): coarse and fine tracks.

[<img align="right" src="https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2.png" alt="Sinusoidal Coil Generator logo, click to see it spin" width="72">](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2_rotor_spin_400px.webp)

| Previous | Next |
|:---|---:|
| [Silkscreen - Dual Generator](Silkscreen-Dual-Generator.md) | [Parameter Reference Single Generator](Parameter-Reference-Single-Generator.md) |

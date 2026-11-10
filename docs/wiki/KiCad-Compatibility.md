# 28. KiCad Compatibility

| Item | Detail |
|---|---|
| File Format | KiCad 7 board format (`version 20221018`) |
| Opens In | KiCad 7, 8, 9 and 10. Newer versions convert the file when it is saved |
| Contents | Tracks, vias, board outline (`Edge.Cuts`), rotor copper polygons and solder mask openings, and on the stator the lead-cutting suggestion: lines and circles on `F.SilkS` and `B.SilkS` (no KiCad text; the lead names are drawn as strokes) |
| Libraries | None needed: no footprints, symbols or 3D models are referenced |
| Nets | `TX`, SIN (`2`) and COS (`1`), so KiCad's ratsnest and DRC understand the coils. A dual stator has six: `SIN_1`, `COS_1`, `TX_1`, `SIN_2`, `COS_2`, `TX_2` by default |
| Layers | `F.Cu` and `B.Cu` (Top, Bottom); a 4-layer stator (every dual stator) also has `In1.Cu` and `In2.Cu` (Inner-1, Inner-2) |
| Vias | Through vias, or with `VIA_TYPE = "blind"` KiCad's blind via between the two layers each via joins (a buried pair uses the same token) |
| Title Block | Filled in automatically on every board |
| Saved Again | A board opened and saved again in KiCad 7 to 10 still reads the same in the repository's own tools (the output pictures): `resources/KiCadReader.py` parses KiCad's format and does not depend on the order or line layout of what KiCad writes, nor on KiCad 10 naming the nets instead of numbering them |
| DRC | Clean apart from the expected `track_dangling` reports at the TX ends (two per coil set: the coils have no terminals yet), when the board's design rules allow the sizes the parameters ask for (see below). The CI checks this in KiCad 8, 9 and 10 on every board |

![KiCad 1: Title Blocks](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/images/kicad_1_title_block.png)

*KiCad 1. The title blocks of a generated stator and rotor, filled in `Keyword: Value` style.*

Because every TX turn is on the same net, KiCad's DRC cannot detect a TX turn touching another TX
turn. The generator runs this check itself near the vias of go-around and stitched windows, and reports the smallest gap it found between different turns. A TX without such vias (such as the default single-layer TX) has nothing to measure there: the summary says "not measured" and gives the gap of the nominal pitch (pitch minus trace width).

The board files carry no design rules, so KiCad's DRC checks them against its own defaults: a clearance of 0.2 mm
between nets, vias of at least 0.5 mm with holes of at least 0.3 mm, and in KiCad 10 tracks of at least 0.2 mm. A board
built with smaller sizes than these (blind vias of 0.4 / 0.15 mm, the Dual Generator's 0.15 mm traces, a
`MIN_CLEARANCE_MM` below 0.2) shows DRC errors for them until the board's rules are set to what the board house can
make (in KiCad: File > Board Setup > Design Rules > Constraints and Net Classes). The generator checks its own
clearances against `MIN_CLEARANCE_MM` and reports the smallest gap it found.

Every pull request opens every reference board, and a fresh board of each generator, in KiCad 7, 8, 9 and 10, and runs
KiCad's DRC in 8, 9 and 10 (KiCad 7's command line has no DRC). The number of reports of each kind on each board must
stay as recorded in `.github/kicad-drc-baseline.json`; see [Regression Testing](Regression-Testing.md).

A KiCad plugin built on the same code is planned (see [Future Upgrades](Future-Upgrades-And-Planning.md)).

[<img align="right" src="https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2.png" alt="Sinusoidal Coil Generator logo, click to see it spin" width="72">](https://raw.githubusercontent.com/RolandThsive/Inductive-Encoder-Sinusoidal-Coil-Generator/main/docs/logo/Logo_1_V2_rotor_spin_400px.webp)

| Previous | Next |
|:---|---:|
| [Output Pictures](Output-Pictures.md) | [Regression Testing](Regression-Testing.md) |

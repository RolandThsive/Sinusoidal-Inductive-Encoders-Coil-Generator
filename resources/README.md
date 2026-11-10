# resources

Files that more than one generator uses, outside the generator folders.

- `KiCadReader.py`: reads a `.kicad_pcb` file into plain Python values (copper layers, nets, tracks, vias, circles,
  polygons, the title block), as KiCad 7 to 10 write it: a parser of KiCad's bracket format, not a pattern match, so a
  board that KiCad has opened and saved again reads the same.  Standard library only.  The lead-cutting silkscreen
  step, the two picture makers below and the Dual Layout pictures of the wiki (`docs/tools/dual_layout_pictures.py`)
  read their boards with it; the regression tests keep a reader of their own (`regression/RegressionTools.py`), and a
  test holds the two to the same values on every reference board.
- `SilkscreenFont.py`: the stroke font of the silkscreen suggestions (lead names drawn as lines, no KiCad text).
  Capitals, digits and a few signs on a 4 x 6 grid, drawn for this repository; see the docstring for the two
  functions (`layout`, `width`).  Used by the lead-cutting silkscreen step
  (`Single Generator/Generator/Stator/LeadCutting_SilkscreenSuggestion.py`), which both generators run.
- `RepresentativeSVGMaker.py`: a picture of a generated board for people: the stator on the left, the rotor on the
  right, layer colours, a title and a legend.  Copper under another layer is made visible (wider stator traces,
  dashed rotor outlines).  Writes `<folder name>_Representative.svg`.
- `ActualSVGMaker.py`: the copper of a generated board as it is, 1:1 in mm, with no text and nothing widened; one
  group per layer (`F_Cu`, `Inner_1`, `Inner_2`, `B_Cu`, plus `Edge_Cuts`) for the stator and for the rotor.  Writes
  `<folder name>_Actual.svg`.

  Both read only `Stator.kicad_pcb` and `Rotor.kicad_pcb` (with `KiCadReader.py`), need nothing but Python 3, and
  run on a folder:
  `python resources/ActualSVGMaker.py "Single Generator/Output/<folder>"`.  The Single and Dual generators call both
  at the end of every run that writes the two boards; when one is missing or fails, the run prints a warning and the
  boards are not affected.

# Future Considerations

Ideas kept for later versions of the Web GUI. Nothing here is active now.

## The Folder And File Names Of A Run

Three settings of the Board file are not on the page: `OUTPUT_DIR`, `STATOR_FILE` and `ROTOR_FILE`. A run in the
browser has no folder of the visitor's to write to: the page gives every run its own folder in memory, names the
zip after the run, and the boards are `Stator.kicad_pcb` and `Rotor.kicad_pcb`. An imported file's values for
these three are left out, and an exported file keeps the published ones (`READ_ONLY` in `WebGenerator.py`).

To put them on the page later: take the names out of `READ_ONLY`, and decide how a custom `STATOR_FILE` or
`ROTOR_FILE` names the files in the zip and on the Stator and Rotor download buttons.

The other three settings the first page kept fixed, `CENTER_X_MM`, `CENTER_Y_MM` and `PAGE_SIZE_MM`, are settings
of the page since version 2.0.

## Arc And Linear

The generator menu lists Arc and Linear, greyed out. They become choices when the repository has those
generators: `MODES` in `WebGenerator.py` names a generator's folder and files, and the page reads everything else
(settings, rules, tabs) from the generator itself.

## Left For Later By The Bug Rounds

`docs/BugRounds.md` lists what the rounds found and left as it is, with the reason.

"""
Dual_RunCoilGenerator.py  -  checks the dual parameters, then writes the dual stator and the rotor disc.
This is the only program of the dual generator that writes boards.

    python Dual_RunCoilGenerator.py              check, then write Stator + Rotor
    python Dual_RunCoilGenerator.py --check      check only, write nothing
    python Dual_RunCoilGenerator.py --stator     only the stator
    python Dual_RunCoilGenerator.py --rotor      only the rotor (needs the stator geometry, but does not write it)
    python Dual_RunCoilGenerator.py --no-color   plain text

Colours: red = error (nothing is written), yellow = warning, green = success.

Steps (the same six as the Single Generator's RunCoilGenerator.py, each done twice where there are two sets)
  1. Dual_CheckParameters.check_parameters   the dual rules, the layout (Dual_TrackLayout), then the Single
                                             Generator's own parameter checks on each set
  2. the Single Generator's chain for each set (RX -> TX -> assemble -> clearances, DesignChecks), set 1 turned
     so that its TX ends sit at TERMINAL_1_DEG and set 2 at TERMINAL_2_DEG; then Dual_StatorAssembler puts the
     two sets on one board and Dual_DesignChecks measures the gap between them on the built copper
  3. the Single Generator's rotor for each set (its ring), then Dual_RotorBuilder puts the two rings on one disc
     and Dual_DesignChecks measures the gap between the rings
  4. TX_Electrics.estimate for each set (each set with its own TX, rotor ring and IC; the other set is not in
     the estimate)
  5. decide (GENERATOR_MODE, --check)
  6. write the files - only if no step reported an error.  Dual_OutputFolders.py makes a new folder for every
     run inside OUTPUT_DIR and writes Stator.kicad_pcb, Rotor.kicad_pcb and Parameters.txt into it.
     Last, Dual_LeadCutting_SilkscreenSuggestion.py draws the lead-cutting suggestion (where to break each RX
     coil, where the TX ends get their vias) on the silkscreen of the written stator file and adds it to the record.
     When both boards were written, resources/RepresentativeSVGMaker.py and resources/ActualSVGMaker.py draw them
     as <folder name>_Representative.svg and <folder name>_Actual.svg in the same folder; a missing file or a failed
     picture is only a warning.

All settings are in the Dual_..._Parameters.py files (the Parameters folder; Dual_Parameters.py lists them).  Run
it from any folder, e.g.
from the "Dual Generator" folder:
    python Dual_Generator/Run/Dual_RunCoilGenerator.py
The Single Generator's code does every piece of geometry; nothing in it is changed.  The command line, the step
headings, the estimate, the deciding and the writing are the Single Generator's own (Generator/Run/RunSteps.py);
this file holds the two-set loops of steps 2 to 4 and the dual summary.
"""

import os
import sys

sys.dont_write_bytecode = True                      # no __pycache__ anywhere, in the Single Generator least of all

if __package__ in (None, ""):                      # started as a script: make the Dual_Generator package importable
    _DUAL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _DUAL not in sys.path:
        sys.path.insert(0, _DUAL)

import Dual_Generator  # noqa: E402,F401   (puts the Parameters folder and the Single Generator on the path)
from Generator.Checks import DesignChecks                                           # noqa: E402
from Generator.Core.Conflict import Colour, Report                                  # noqa: E402
from Generator.Run import RunSteps as RS                                            # noqa: E402
from Generator.Run.RunSteps import step, stop                                       # noqa: E402

from Dual_Generator.Checks import Dual_DesignChecks as DDC                          # noqa: E402
from Dual_Generator.Checks.Dual_CheckParameters import check_parameters             # noqa: E402
from Dual_Generator.Core import Dual_SetParameters as SP                            # noqa: E402
from Dual_Generator.Run import Dual_OutputFolders as OF                             # noqa: E402


SET_WORD = {1: "set 1 (inner)", 2: "set 2 (outer)"}


def narrow_band_hint(layout):
    """A band the generator fitted to a board edge gets whatever room is left; when a set cannot be built, the usual
    reason is that the room was too little for its vias (Dual_TrackLayout.Layout.fitted)."""
    fitted = layout.fitted()
    if fitted is None:
        return
    what, change = fitted
    print("  " + Colour.yellow(f"hint    the generator fitted {what}. If the errors above are about the vias of a "
                               f"fitted band (narrower than a via, a via touching copper), {change}"))


def electrical(Pk, k, stator, rotor):
    """The electrical estimate of one set (TX_Electrics.py).  Returns (warning texts, summary or None, record lines).
    It never stops a generation."""
    el, e = RS.estimate(Pk, stator, rotor)
    if el is None:
        return RS.not_estimated(e, f" of {SET_WORD[k]}")
    print("  " + Colour.bold(f"{SET_WORD[k]}: {el.heading()}"))
    warnings, summary, record = RS.show_estimate(el, indent="  ", prefix=f"set {k}: ")
    record.append("  (each set is estimated on its own: the other set's TX ring and rotor ring are not in the estimate)")
    return warnings, summary, record


def main(argv=None):
    """Check the dual parameters, build both sets and the rotor, write the files.  argv: the command line (None =
    sys.argv).  Returns the exit code."""
    args = RS.parse_args("Check the dual parameters, then generate the dual stator and the rotor disc.", argv)
    want_stator, want_rotor = args.want_stator, args.want_rotor
    total = 6

    # ---------------------------------------------------------------- 1. parameters
    step(1, total, "Checking the parameters")
    P = RS.load_parameters("Dual_Parameters")
    if P is None:
        return stop("parameter files cannot be loaded")
    rep, layout = check_parameters(P)
    rep.print()
    warn_texts = list(rep.warnings)
    if rep.errors or layout is None:
        if layout is not None:
            narrow_band_hint(layout)
        return stop(f"{len(rep.errors)} parameter error(s)")
    print("  " + Colour.green("parameters OK"))
    strict = RS.is_strict(P.BOARD)
    sets = {k: SP.build(P, k, layout.set_band(k), layout.edges()) for k in (1, 2)}
    terminal = {1: float(P.BOARD.TERMINAL_1_DEG), 2: float(P.BOARD.TERMINAL_2_DEG)}

    # ---------------------------------------------------------------- 2. stator
    from Generator.Stator import StatorAssembly
    from Dual_Generator.Stator import Dual_StatorAssembler as DSA
    from Dual_Generator.Stator import Dual_LeadCutting_SilkscreenSuggestion as LCS
    from Dual_Generator.Rotor import Dual_RotorBuilder as DRB
    step(2, total, "Building the stator: the two sets, each by the Single Generator, then the board")
    stators, gen_rep = {}, Report()
    for k in (1, 2):
        try:
            stators[k], r = RS.captured(StatorAssembly.build_stator, sets[k], terminal[k])
        except (ValueError, RuntimeError) as e:
            SP.for_set(RS.failed(e), k, P).print()
            narrow_band_hint(layout)
            return stop(f"{SET_WORD[k]} cannot be built")
        r.extend(DesignChecks.check_design(sets[k], stators[k]))
        gen_rep.extend(SP.for_set(r, k, P))
    dual = DSA.assemble(P, layout, stators[1], stators[2])
    sets_rep, _gap = DDC.check_sets(P, layout, stators[1], stators[2])
    gen_rep.extend(sets_rep)
    gen_rep.print()
    all_warn = len(rep.warnings) + len(gen_rep.warnings)
    board_warn = len(gen_rep.warnings)
    warn_texts += gen_rep.warnings
    if gen_rep.errors:
        narrow_band_hint(layout)
        return stop(f"{len(gen_rep.errors)} geometry error(s)")
    print("  " + Colour.green("stator built"))

    # ---------------------------------------------------------------- 3. rotor
    step(3, total, "Building the rotor: the two rings, each by the Single Generator, then the disc")
    rings, disc = {}, None
    if want_rotor or args.check:
        rot_rep = Report()
        for k in (1, 2):
            try:
                rings[k] = DRB.build_ring(sets[k], stators[k], getattr(P.BOARD, "ROTOR_START_ANGLE_ZERO", "rx_zero"))
            except (ValueError, RuntimeError) as e:
                SP.for_set(RS.failed(e), k, P).print()
                return stop(f"ring {k} of the rotor cannot be built")
            r = SP.for_set(DesignChecks.check_design(sets[k], stators[k], rings[k]), k, P)
            r.items = [it for it in r.items if it not in gen_rep.items]      # only the rotor's own notes are new
            rot_rep.extend(r)
        disc = DRB.assemble(P, dual, rings[1], rings[2])
        rot_rep.extend(DDC.check_rings(P, layout, rings[1], rings[2], stators[1], stators[2]))
        rot_rep.print()
        all_warn += len(rot_rep.warnings)
        board_warn += len(rot_rep.warnings)
        warn_texts += rot_rep.warnings
        if rot_rep.errors:
            return stop(f"{len(rot_rep.errors)} rotor error(s)")
        print("  " + Colour.green("rotor built"))
    else:
        print("  " + Colour.dim("--stator: the rotor is not written"))

    # ---------------------------------------------------------------- 4. electrical estimate
    step(4, total, "Electrical estimate, each set on its own")
    el_record, el_summary, el_warn = {}, {}, []
    for k in (1, 2):
        w, s, lines = electrical(sets[k], k, stators[k], rings.get(k))
        el_warn += w
        el_summary[k] = s
        el_record[k] = lines
    all_warn += len(el_warn)

    # ---------------------------------------------------------------- 5. strict / check-only
    rc = RS.decide(strict, board_warn, all_warn, args.check, 5, total)
    if rc is not None:
        return rc

    # ---------------------------------------------------------------- 6. write
    rc, folder, written, warned = RS.write_files(
        lambda: OF.create_output_folder(dual, P), dual if want_stator else None, disc if want_rotor else None,
        P.BOARD.STATOR_FILE, P.BOARD.ROTOR_FILE, lambda path: LCS.add_to_file(path, P), LCS.append_record,
        lambda folder, written: OF.write_record(
            folder, P, written, dual=dual, disc=disc if want_rotor else None, layout=layout, sets=sets,
            electrical_lines=el_record, warnings=warn_texts + list(el_warn),
            command=RS.command("python Dual_RunCoilGenerator.py", argv)),
        OF.remove_if_empty, 6, total)
    if rc is not None:
        return rc
    all_warn += warned

    print()
    if want_stator:
        print(dual.summary())
    if want_rotor:
        print(disc.summary())
    for k in (1, 2):
        if el_summary.get(k):
            print(f"Electrical of {SET_WORD[k]} (estimate, step 4): {el_summary[k]}")
    return RS.success(written, folder, all_warn)


if __name__ == "__main__":
    sys.exit(main())

"""
RunCoilGenerator.py  -  checks the parameters, then writes the stator and the rotor.
This is the only program that writes boards.

    python Generator/Run/RunCoilGenerator.py              check, then write Stator + Rotor
    python Generator/Run/RunCoilGenerator.py --check      check only, write nothing (with --stator: as the
                                                          --stator run, the rotor is not checked)
    python Generator/Run/RunCoilGenerator.py --stator     only the stator
    python Generator/Run/RunCoilGenerator.py --rotor      only the rotor (needs the stator geometry, but does not
                                                          write it)
    python Generator/Run/RunCoilGenerator.py --no-color   plain text
(from the "Single Coil Set Generator" folder)

Colours: red = error (nothing is written), yellow = warning, green = success.

Steps (the chain: every step reads only what the steps before it made)
  1. CheckParameters.check_parameters    rules on the parameter values (ParameterRules.py, ConflictRules.py)
  2. RX_Builder.build_rx                 the RX coils and their fingers (from the parameters alone)
     TX_Builder.build_tx                 the TX coil, its terminal where it keeps the largest gap from the RX
     StatorAssembly.assemble             the board, turned so that the TX terminal sits at 0 deg (the right)
     DesignChecks                        the clearances of the finished copper, the outline, the page
  3. build the rotor, check again
  4. TX_Electrics.estimate              TX inductance, tank capacitors and oscillator frequency,
                                         checked against IC_Parameters.py (an estimate: it never changes
                                         the boards, its warnings count like the others)
  5. decide (GENERATOR_MODE, --check): in "strict" mode every warning about the finished boards (steps 2
     and 3) counts as an error and nothing is written
  6. write the files - only if no step reported an error.  OutputFolders.py makes a new
     folder for every run inside OUTPUT_DIR (the Output folder in "Single Coil Set Generator"),
         Coil_<board inside radius>_<board outside radius>_<RX loops>_<RX sub-coils>_<TX turns>_<TX wiring>_<TX shape>
     e.g. Coil_15_27_1_1_3_Single_SteppedDiagonal (TX wiring: Single, Series or Parallel; TX shape:
     SteppedDiagonal, SteppedArc or Spiral), with __1, __2, ... added when that name exists already, and writes Stator.kicad_pcb,
     Rotor.kicad_pcb (each with its KiCad project file, Stator.kicad_pro / Rotor.kicad_pro: the board's design
     rules) and Parameters.txt (every value used, the summaries, the electrical estimate
     and copies of the parameter files) into it.  Nothing is ever overwritten.
     Last, LeadCutting_SilkscreenSuggestion.py draws the suggestion for cutting the leads (where to break each RX
     coil, where the TX ends get their vias) on the silkscreen of the written stator file and adds it to the record.
     When both boards were written, resources/RepresentativeSVGMaker.py and resources/ActualSVGMaker.py draw them
     as <folder name>_Representative.svg and <folder name>_Actual.svg in the same folder; a missing file or a failed
     picture is only a warning.

The command line, the step headings, the estimate, the deciding and the writing are in RunSteps.py, which the
Dual Coil Set Generator's run script uses as well; this file holds the order of the steps and what is built in each.

All settings are in Board_Parameters.py, RX_Parameters.py, TX_Parameters.py, Rotor_Parameters.py and
IC_Parameters.py (the Parameters folder).  Run it from any folder, e.g. from the "Single Coil Set Generator" folder:
    python Generator/Run/RunCoilGenerator.py
(project layout: wiki page "Project Output Organization", docs/wiki/Project-Output-Organization.md;
overview in README.md in the top folder).
"""

import os
import sys

if __package__ in (None, ""):                      # started as a script: make the Generator package importable
    _SINGLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _SINGLE not in sys.path:
        sys.path.insert(0, _SINGLE)

from Generator.Checks import DesignChecks                               # noqa: E402
from Generator.Core.Conflict import Colour                              # noqa: E402
from Generator.Run import OutputFolders as OF                           # noqa: E402
from Generator.Run import RunSteps as RS                                # noqa: E402
from Generator.Run.CheckParameters import check_parameters              # noqa: E402
from Generator.Run.RunSteps import step, stop                           # noqa: E402


def electrical(P, stator, rotor, n, total):
    """Step n: print the electrical estimate (TX_Electrics.py).  Returns (warning texts, one-line summary or
    None, report lines for Parameters.txt).  It never stops a generation: if it cannot be made, a note says why
    and the boards are written."""
    el, e = RS.estimate(P, stator, rotor)            # (--stator: the rotor is built only for the estimate)
    if el is None:
        step(n, total, "Electrical estimate")
        return RS.not_estimated(e)
    step(n, total, f"Electrical estimate  ({el.heading()})")
    return RS.show_estimate(el)


def main(argv=None):
    """Check the parameters, build the stator and the rotor, write the files.  argv: the command line (None =
    sys.argv).  Returns the exit code."""
    args = RS.parse_args("Check the parameters, then generate the stator and rotor.", argv)
    want_stator, want_rotor = args.want_stator, args.want_rotor
    total = 6

    # ---------------------------------------------------------------- 1. parameters
    step(1, total, "Checking the parameters")
    P = RS.load_parameters("Parameters")
    if P is None:                                                      # syntax error, missing file ...
        return stop("parameter files cannot be loaded")
    rep = check_parameters(P)
    rep.print()
    warn_texts = list(rep.warnings)                                    # for the record in the output folder
    if rep.errors:
        return stop(f"{len(rep.errors)} parameter error(s)")
    print("  " + Colour.green("parameters OK"))
    strict = RS.is_strict(P)

    # ---------------------------------------------------------------- 2. stator
    from Generator.Stator import StatorAssembly
    from Generator.Rotor import RotorBuilder as RB
    from Generator.Stator import LeadCutting_SilkscreenSuggestion as LCS
    step(2, total, "Building the stator")
    try:
        # THE CHAIN (StatorAssembly.build_stator).  THE RX READS ONLY THE PARAMETERS; THE TX READS THE RX (ITS
        # FINGERS AND ITS COPPER, TO FIND THE PLACE FOR ITS TERMINAL); THE ASSEMBLY TURNS THE BOARD SO THAT THE
        # TERMINAL SITS AT 0 DEG (THE RIGHT); THE CHECKS MEASURE THE RESULT.  NOTHING GOES BACKWARDS AND NOTHING
        # IS ESTIMATED.  (Their warnings are caught from stderr.)
        stator, gen_rep = RS.captured(StatorAssembly.build_stator, P)
    except (ValueError, RuntimeError) as e:
        RS.failed(e).print()
        return stop("the stator cannot be built")
    gen_rep.extend(DesignChecks.check_design(P, stator))
    gen_rep.print()
    all_warn = len(rep.warnings) + len(gen_rep.warnings)
    board_warn = len(gen_rep.warnings)                                  # warnings about the finished boards
    warn_texts += gen_rep.warnings
    if gen_rep.errors:
        return stop(f"{len(gen_rep.errors)} geometry error(s)")
    print("  " + Colour.green("stator built"))

    # ---------------------------------------------------------------- 3. rotor
    step(3, total, "Building the rotor")
    try:
        # (--stator --check follows the --stator run: the rotor is not built or checked; the estimate in step 4
        # still builds one for itself)
        rotor = RB.RotorDesign(P, stator=stator) if want_rotor else None
    except (ValueError, RuntimeError) as e:
        RS.failed(e).print()
        return stop("the rotor cannot be built")
    if rotor is not None:
        rot_rep = DesignChecks.check_design(P, stator, rotor)
        # only the rotor's own notes are new here (the stator findings were shown above)
        rot_rep.items = [it for it in rot_rep.items if it not in gen_rep.items]
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
    el_warn, el_summary, el_record = electrical(P, stator, rotor, 4, total)
    all_warn += len(el_warn)

    # ---------------------------------------------------------------- 5. strict / check-only
    rc = RS.decide(strict, board_warn, all_warn, args.check, 5, total)
    if rc is not None:
        return rc

    # ---------------------------------------------------------------- 6. write
    rc, folder, written, warned = RS.write_files(
        lambda: OF.create_output_folder(stator, P), stator if want_stator else None, rotor if want_rotor else None,
        P.STATOR_FILE, P.ROTOR_FILE, lambda path: LCS.add_to_file(path, P), LCS.append_record,
        lambda folder, written: OF.write_record(
            folder, P, written, stator=stator, rotor=rotor if want_rotor else None, electrical_lines=el_record,
            warnings=warn_texts + list(el_warn), command=RS.command("python Generator/Run/RunCoilGenerator.py", argv)),
        OF.remove_if_empty, 6, total)
    if rc is not None:
        return rc
    all_warn += warned

    print()
    if want_stator:
        print(stator.summary())
    if want_rotor:
        print(rotor.summary())
    if el_summary:
        print(f"Electrical (estimate, step 4): {el_summary}")
    return RS.success(written, folder, all_warn)


if __name__ == "__main__":
    sys.exit(main())

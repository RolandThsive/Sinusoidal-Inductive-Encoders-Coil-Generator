"""
RunSteps.py  -  the pieces of a run that RunCoilGenerator.py shares with the Dual Coil Set Generator's
Dual_RunCoilGenerator.py: the command line, the step headings, the stop, the electrical estimate, the deciding step (5),
the write step (6) and the last line.  Each run script keeps only what is its own: which boards it builds, and how.

    args = parse_args(description, argv)   --check, --stator, --rotor, --no-color; sets the colours up and adds
                                           args.want_stator / args.want_rotor
    P = load_parameters("Parameters")      the parameter module, or None (the error is printed)
    step(n, total, text)                   "[n/total] text"
    return stop(why)                       "FAILED: why. Nothing was written."  (returns 1)
    failed(e).print()                      a builder's ValueError / RuntimeError as a report
    result, rep = captured(build, ...)     build(...) with its WARNING: lines on stderr caught as a report
    el, e = estimate(P, stator, rotor)     TX_Electrics.estimate, or the exception that stopped it
    rc = decide(strict, board_warn, all_warn, check_only)   step 5: None = go on and write, else the exit code
    rc, folder, written, warned = write_files(...)          step 6: the boards, the record, the pictures
    return success(written, folder, all_warn)               the last line (returns 0)

Nothing to edit here.
"""

import argparse
import contextlib
import importlib
import importlib.util
import io
import os
import sys

from Generator.Checks import DesignChecks
from Generator.Core.Conflict import Colour, Report
from Generator.Core.PCBWriter import project_path
from Generator.Run.OutputFolders import RECORD_FILE

RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                         "resources")
SVG_MAKERS = ("RepresentativeSVGMaker.py", "ActualSVGMaker.py")       # each has make_svg(folder)


def parse_args(description, argv=None):
    """The command line of a run script.  Sets the colours up; adds want_stator and want_rotor."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--check", action="store_true", help="check the parameters and the geometry, write nothing")
    ap.add_argument("--stator", action="store_true", help="write only the stator")
    ap.add_argument("--rotor", action="store_true", help="write only the rotor")
    ap.add_argument("--no-color", action="store_true", help="no colours")
    args = ap.parse_args(argv)
    Colour.setup(False if args.no_color else None)
    args.want_stator = args.stator or not args.rotor
    args.want_rotor = args.rotor or not args.stator
    return args


def command(script, argv=None):
    """The command line as the record shows it: `script` and the arguments it was run with."""
    return script + " " + " ".join(sys.argv[1:] if argv is None else argv)


def step(n, total, text):
    """Print the heading of step n of `total`."""
    print(Colour.bold(f"[{n}/{total}] {text}"))


def stop(why):
    """Print the FAILED line (nothing was written).  Returns the exit code, 1."""
    print()
    print(Colour.red(f"FAILED: {why}. Nothing was written."))
    return 1


def load_parameters(name):
    """The parameter module `name` (Parameters, Dual_Parameters), or None when it cannot be loaded (a syntax error, a
    missing file ...): the error is printed."""
    try:
        return importlib.import_module(name)
    except Exception as e:
        print("  " + Colour.red(f"ERROR   the parameter files cannot be loaded: {type(e).__name__}: {e}"))
        return None


def is_strict(B):
    """GENERATOR_MODE = "strict" in the board values B: every warning about the finished boards counts as an error."""
    return str(getattr(B, "GENERATOR_MODE", "normal")).strip().lower() == "strict"


def failed(e):
    """A builder's ValueError / RuntimeError as a report (print it, then stop)."""
    rep = Report()
    rep.add_exception(e)
    return rep


def captured(build, *args, **kwargs):
    """build(*args, **kwargs) with its stderr caught: (its result, the report of its 'WARNING: ...' lines
    (DesignChecks.classify_generator_output)).  A ValueError or RuntimeError of the builder passes through."""
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        out = build(*args, **kwargs)
    return out, DesignChecks.classify_generator_output(buf.getvalue())


# ---------------------------------------------------------------- 4. electrical estimate
def estimate(P, stator, rotor):
    """TX_Electrics.estimate for the stator and rotor (when the rotor was not built, it is built here only for the
    estimate).  Returns (the estimate, None), or (None, the exception) when it cannot be made: it never stops a
    generation."""
    if rotor is None:
        try:
            from Generator.Rotor import RotorBuilder    # (here: it reads the parameter files when imported)
            rotor = RotorBuilder.RotorDesign(P, stator=stator)
        except Exception:
            rotor = None
    try:
        from Generator.Stator.TX import TX_Electrics
        return TX_Electrics.estimate(stator, rotor, P), None
    except Exception as e:
        return None, e


def not_estimated(e, whose=""):
    """Print why the estimate could not be made.  Returns (warning texts, summary, record lines) = ([], None, ...)."""
    why = f"the electrical estimate{whose} could not be made ({type(e).__name__}: {e}); the boards are not affected"
    print("  " + Colour.yellow(why))
    return [], None, ["ELECTRICAL ESTIMATE", "  " + why]


def show_estimate(el, indent="", prefix=""):
    """Print the estimate's lines (each after `indent`) and its findings (each after `prefix`).  Returns (warning
    texts, one-line summary, record lines for Parameters.txt)."""
    for line in el.lines(title=False):
        print(indent + line)
    rep = Report()
    rep.items = [(level, prefix + msg, ()) for level, _code, msg in el.findings]
    rep.print()
    record = el.lines(title=True) + [f"  {level.upper():8s}{msg}" for level, _code, msg in el.findings]
    return rep.warnings, el.summary(), record


# ---------------------------------------------------------------- 5. strict / check-only
def decide(strict, board_warn, all_warn, check_only, n=5, total=6):
    """Step 5.  Returns None when the files are to be written, else the exit code (1: strict mode and warnings about
    the boards; 0: --check)."""
    step(n, total, "Deciding")
    if strict and board_warn:
        print("  " + Colour.red(f'GENERATOR_MODE = "strict": {board_warn} warning(s) about the boards count as errors'))
        return stop(f"{board_warn} board warning(s) in strict mode")
    if all_warn:
        print("  " + Colour.yellow(f"{all_warn} warning(s) - the files can still be written; read them first"))
    else:
        print("  " + Colour.green("no warnings"))
    if check_only:
        print()
        print(Colour.green("CHECK PASSED") + " (--check: no files written)")
        return 0
    return None


# ---------------------------------------------------------------- 6. write
def draw_pictures(folder):
    """The SVG pictures of the written board (resources/RepresentativeSVGMaker.py and ActualSVGMaker.py).  Extras: when
    a file is missing or anything goes wrong, a yellow warning is printed and the run goes on.  Returns the number of
    warnings printed."""
    warned = 0
    for name in SVG_MAKERS:
        try:
            path = os.path.join(RESOURCES, name)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"{name} not found in resources")
            spec = importlib.util.spec_from_file_location(os.path.splitext(name)[0], path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            print("  " + Colour.green(f"picture -> {mod.make_svg(folder)}"))
        except Exception as e:
            print("  " + Colour.yellow(f"WARNING picture not made by {name}: {e}; the boards are not affected"))
            warned += 1
    return warned


def write_files(make_folder, stator, rotor, stator_file, rotor_file, add_silkscreen, append_silkscreen, write_record,
                remove_if_empty, n=6, total=6):
    """Step 6: a new output folder, the stator (then its lead-cutting silkscreen suggestion), the rotor, each with
    its KiCad project file (the board's design rules, PCBWriter.py), the record, and the pictures when both boards
    were written.
      make_folder()                    makes the new output folder, returns its path
      stator, rotor                    the boards to write (each has write(path)); None = not written
      add_silkscreen(path)             the lead-cutting step on the written stator file; returns its result
      append_silkscreen(record, result)    adds that result to Parameters.txt
      write_record(folder, written)    writes Parameters.txt, returns its path
      remove_if_empty(folder)          removes the folder again when nothing could be written
    Returns (exit code or None, folder, written paths, picture warnings); the exit code is 1 when a file could not
    be written."""
    step(n, total, "Writing the files")
    written, folder, silk, warned = [], None, None, 0
    try:
        folder = make_folder()
        print(f"  folder  {folder}")
        if stator is not None:
            path = stator.write(os.path.join(folder, stator_file))
            written += [path, project_path(path)]
            print("  " + Colour.green(f"stator  -> {path}  (and {os.path.basename(project_path(path))}: its design rules)"))
            silk = add_silkscreen(path)                  # the lead-cutting silkscreen suggestion, drawn into the file
        if rotor is not None:
            path = rotor.write(os.path.join(folder, rotor_file))
            written += [path, project_path(path)]
            print("  " + Colour.green(f"rotor   -> {path}  (and {os.path.basename(project_path(path))}: its design rules)"))
        path = write_record(folder, written)
        if silk is not None:
            append_silkscreen(path, silk)
        print("  " + Colour.green(f"record  -> {path}"))
        if stator is not None and rotor is not None:
            warned = draw_pictures(folder)
    except OSError as e:
        print("  " + Colour.red(f"ERROR   cannot write: {e}"))
        if not written:
            remove_if_empty(folder)
            return stop("cannot write the files"), folder, written, warned
        print()
        print(Colour.red(f"FAILED: only {', '.join(os.path.basename(p) for p in written)} was written to {folder}."))
        return 1, folder, written, warned
    return None, folder, written, warned


def success(written, folder, all_warn):
    """Print the SUCCESS line: the files written and the number of warnings.  Returns the exit code, 0."""
    print()
    names = [os.path.basename(p) for p in written]
    print(Colour.green(f"SUCCESS: {', '.join(names)} and {RECORD_FILE} written to {folder}")
          + (Colour.yellow(f"  ({all_warn} warning(s) above)") if all_warn else ""))
    return 0

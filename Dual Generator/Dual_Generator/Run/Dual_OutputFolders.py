"""
Dual_OutputFolders.py  -  where Dual_RunCoilGenerator.py puts every generation, and the record it leaves there.

Every generation gets its own folder inside OUTPUT_DIR (Dual_Board_Parameters.py; "Output" = the Output folder in
"Dual Generator", next to Parameters and Dual_Generator):

    DualCoil_<bore radius>_<outline radius>_<set 1 loops>x<set 2 loops>_<set 1 TX turns>x<set 2 TX turns>

for example  DualCoil_7.25_26.875_1x16_4x4.  If that folder already exists, the next free one of
DualCoil_..._4x4__1, __2, ... is used, so nothing is ever overwritten.

A relative OUTPUT_DIR is taken from the "Dual Generator" folder, not from the folder the program is run from.

Inside the folder:
    Stator.kicad_pcb, Rotor.kicad_pcb   (STATOR_FILE / ROTOR_FILE)
    Parameters.txt                      what was generated, with which values: the mode and every value the
                                        generator computed (bands, edges, gap, zeros), the summaries and the
                                        electrical estimate of each set, the value of every parameter by dual
                                        file, each set as handed to the Single Generator, and a verbatim copy of
                                        every parameter file

The numbers in the name, the new folder (never reused), the record's head, its value lines and its file copies are
the Single Generator's own (OutputFolders.py); only the dual name and the dual record sections are here.
"""

import os

from Generator.Checks import ParameterRules as SingleRules
from Generator.Run import OutputFolders as _single
from Generator.Run.OutputFolders import RECORD_FILE, folder_number, remove_if_empty  # noqa: F401   (used by the run script)

from Dual_Generator import DUAL_GENERATOR
from Dual_Generator.Core import Dual_SetParameters as SP

FOLDER_PREFIX = "DualCoil"
FOLDER_PATTERN = "DualCoil_<bore radius>_<outline radius>_<set 1 loops>x<set 2 loops>_<set 1 TX turns>x<set 2 TX turns>"


def folder_name(dual, P):
    s1, s2 = dual.sets
    return "_".join((FOLDER_PREFIX, folder_number(dual.bore), folder_number(dual.outline), f"{int(s1.N)}x{int(s2.N)}",
                     f"{int(s1.P.TX_TURNS)}x{int(s2.P.TX_TURNS)}"))


def project_folder():
    """The "Dual Generator" folder (it holds Parameters, Dual_Generator and Output)."""
    return DUAL_GENERATOR


def output_dir(B):
    """OUTPUT_DIR as a usable path: an absolute one as it is, a relative one from "Dual Generator"."""
    return _single.output_dir(B, project_folder())


def create_output_folder(dual, P):
    """Create the folder for this generation inside OUTPUT_DIR and return its path (never reused: __1, __2, ...)."""
    return _single.new_folder(output_dir(P.BOARD), folder_name(dual, P))


def _parameter_dir():
    return os.path.join(project_folder(), "Parameters")


def _values_by_file(P):
    """[(file, [(name, value text), ...]), ...]: every parameter of every dual file, in the order of
    Dual_SetParameters.NAMES_BY_FILE, with the value in the file (or 'not set')."""
    attrs = {"Dual_Board_Parameters.py": P.BOARD, "Dual_RX1_Parameters.py": P.RX1, "Dual_RX2_Parameters.py": P.RX2,
             "Dual_TX1_Parameters.py": P.TX1, "Dual_TX2_Parameters.py": P.TX2,
             "Dual_Rotor1_Parameters.py": P.ROTOR1, "Dual_Rotor2_Parameters.py": P.ROTOR2,
             "Dual_IC1_Parameters.py": getattr(P, "IC1", None), "Dual_IC2_Parameters.py": getattr(P, "IC2", None)}
    out = []
    for file, names in SP.NAMES_BY_FILE.items():
        mod = attrs[file]
        if mod is None:
            out.append((file, [("(file not loaded)", "")]))
            continue
        items = [(n, repr(getattr(mod, n)) if hasattr(mod, n) else "(not set: the default is used)") for n in names]
        extra = [(n, repr(getattr(mod, n)) + "   (not a parameter of this file: ignored)")
                 for n in sorted(dir(mod)) if n.isupper() and not n.startswith("_") and n not in names]
        out.append((file, items + extra))
    return out


def write_record(folder, P, written, dual=None, disc=None, layout=None, sets=None, electrical_lines=None,
                 warnings=None, command=None):
    """Write Parameters.txt into the generation folder: what was made and every value it was made with.
    sets: the two set namespaces (Dual_SetParameters.build) as used; electrical_lines: {1: [...], 2: [...]}."""
    lines = _single.record_head("DUAL COIL GENERATION RECORD", folder, written, command)
    if dual is not None:
        lines.append(f"name        {folder_name(dual, P)}  = {FOLDER_PATTERN}")
        for k, st in ((1, dual.sets[0]), (2, dual.sets[1])):
            lines.append(f"set {k}       turned by {st.rotation_deg:.2f} deg so that its TX ends sit at {st.terminal_deg:g} deg; "
                         f"its RX pattern's zero is at {st.rotation_deg:.2f} deg")
    lines.append("")
    if layout is not None:
        lines += ["LAYOUT (what the generator computed)", "-" * 36] + layout.lines() + [""]
    if warnings:
        lines += ["WARNINGS OF THIS RUN", "-" * 20] + [f"  {w}" for w in warnings] + [""]
    if dual is not None:
        lines += ["STATOR", "-" * 6, dual.summary(), ""]
    if disc is not None:
        lines += ["ROTOR", "-" * 5, disc.summary(), ""]
    if electrical_lines:
        for k in (1, 2):
            if electrical_lines.get(k):
                lines += [f"SET {k}: " + electrical_lines[k][0]] + list(electrical_lines[k][1:]) + [""]
    lines += _single.value_lines(_values_by_file(P))
    if sets:
        lines += ["THE TWO SETS AS HANDED TO THE SINGLE GENERATOR (its names)", "-" * 58]
        order = [name for _f, name, _k, _o, _a in SingleRules.SPEC]
        for k, Pk in sorted(sets.items()):
            lines.append(f"[set {k}]")
            width = max(len(n) for n in order)
            lines += [f"  {n:<{width}s} = {getattr(Pk, n)!r}" for n in order if hasattr(Pk, n)]
            lines.append("")
    lines += _single.file_copies(_parameter_dir(), SP.PARAMETER_FILES)
    return _single.save_record(folder, lines)

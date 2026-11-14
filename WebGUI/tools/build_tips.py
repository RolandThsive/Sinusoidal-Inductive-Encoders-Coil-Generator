"""
build_tips.py  -  writes WebGUI/tips.json, the words of every help box (tooltip) of the page.

    python WebGUI/tools/build_tips.py            write tips.json and docs/tooltips/Inventory.md
    python WebGUI/tools/build_tips.py --check    only say whether both are the ones tips_words.py gives (exit 1 if not)

The words are written in tips_words.py; the page reads only tips.json (WebGUI/app/tips.js).  The file has one tip
per line, so a change of words shows as one changed line:

    {"params":   {NAME: {lead, choices, facts, formula, note, picture}},     the settings, by their name in the file
     "controls": {tip id: {lead, facts, note, keys, keysNote}},              buttons, switches and other controls
     "presets":  {card id: {lead}},                                         the TX layout cards
     "presetFoot": "...", "overrideChoice": "..."}

A tip that names a picture must find it in WebGUI/docs/tooltips/pictures (build_site.py copies that folder).
Inventory.md is the same words as a list a person can read: every tip with its number, where it shows and its first
sentence.
Needs only Python 3.
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.dirname(HERE)
OUT = os.path.join(WEB, "tips.json")
PICTURES = os.path.join(WEB, "docs", "tooltips", "pictures")
INVENTORY = os.path.join(WEB, "docs", "tooltips", "Inventory.md")
PARAMETER_FOLDERS = (("Single", os.path.join(os.path.dirname(WEB), "Generators", "Single Coil Set Generator", "Parameters")),
                     ("Dual", os.path.join(os.path.dirname(WEB), "Generators", "Dual Coil Set Generator", "Parameters")))
sys.path.insert(0, HERE)
import tips_words as words  # noqa: E402

# words that point at a neighbour on the page: "the value above", "see below"
LEANS = re.compile(r"\b(value|setting|one|parameter|block|switch|button)s? (above|below)\b|\bsee (above|below)\b", re.I)
PARTS = {"params": ("lead", "choices", "facts", "formula", "note", "picture"),
         "controls": ("lead", "facts", "note", "keys", "keysNote"),
         "presets": ("lead",)}


def _line(value):
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def problems():
    """What is wrong with the words, as lines (none: [])."""
    out = []
    for group, source in (("params", words.PARAMS), ("controls", words.CONTROLS), ("presets", words.PRESETS)):
        for name, tip in source.items():
            where = f"{group} {name}"
            extra = sorted(set(tip) - set(PARTS[group]))
            if extra:
                out.append(f"{where}: unknown part {', '.join(extra)}")
            lead = tip.get("lead", "")
            if not lead or not isinstance(lead, str):
                out.append(f"{where}: no lead sentence")
            for part in ("lead", "note"):
                if LEANS.search(tip.get(part, "")):
                    out.append(f"{where}: its {part} leans on a neighbour (each tip is read alone)")
            for row in tip.get("facts", []):
                if not (isinstance(row, list) and len(row) == 2 and all(isinstance(x, str) and x for x in row)):
                    out.append(f"{where}: a fact is not [label, value]")
            pic = tip.get("picture")
            if pic and not os.path.isfile(os.path.join(PICTURES, pic.get("file", ""))):
                out.append(f"{where}: its picture {pic.get('file')} is not in docs/tooltips/pictures")
            if pic and not pic.get("caption"):
                out.append(f"{where}: its picture has no caption (it is also the text for screen readers)")
            if pic and not (isinstance(pic.get("width"), int) and isinstance(pic.get("height"), int)):
                out.append(f"{where}: its picture has no width and height (the box keeps its place while the picture loads)")
    return out


def text():
    """tips.json as text: one tip per line."""
    lines = ["{"]
    for group, source in (("params", words.PARAMS), ("controls", words.CONTROLS), ("presets", words.PRESETS)):
        lines.append(f'"{group}": {{')
        rows = [f"{json.dumps(name)}: {_line(tip)}" for name, tip in source.items()]
        lines.append(",\n".join(rows))
        lines.append("},")
    lines.append(f'"presetFoot": {_line(words.PRESET_FOOT)},')
    lines.append(f'"overrideChoice": {_line(words.OVERRIDE_CHOICE)}')
    lines.append("}")
    return "\n".join(lines) + "\n"


def _shows_in():
    """{NAME: "Single · Board; Dual · RX1; ..."}: the parameter files that hold each setting, in the files' order."""
    out = {}
    for gen, folder in PARAMETER_FOLDERS:
        for name in sorted(os.listdir(folder)):
            m = re.match(r"(?:Dual_)?(\w+)_Parameters\.py$", name)
            if not m:
                continue
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                for setting in re.findall(r"^([A-Z][A-Z0-9_]*)\s*=", fh.read(), re.M):
                    places = out.setdefault(setting, [])
                    place = f"{gen} · {m.group(1)}"
                    if place not in places:
                        places.append(place)
    return {k: "; ".join(v) for k, v in out.items()}


def _cell(words_):
    return " ".join(str(words_).split()).replace("|", "\\|")


def inventory():
    """docs/tooltips/Inventory.md as text."""
    shows = _shows_in()
    n = len(words.PARAMS) + len(words.CONTROLS) + len(words.PRESETS)
    pictures = sum(1 for tip in words.PARAMS.values() if tip.get("picture"))
    lines = ["# Tooltip inventory", "",
             "Every help box (tooltip) of the web tool, numbered: where it shows and its first sentence. This file is written",
             "by `WebGUI/tools/build_tips.py` from the words in `WebGUI/tools/tips_words.py`, together with `WebGUI/tips.json`,",
             "which the page reads. Change the words there, not here.", "",
             f"{n} tips: {len(words.PARAMS)} settings, {len(words.CONTROLS)} buttons, switches and other controls, and the "
             f"{len(words.PRESETS)} TX layout cards. {pictures} settings show a picture.", "",
             "A tip is shown in one layout: where the setting is, its name and unit, its name in the file, the first sentence,",
             "the choices (the file's one marked), facts, the formula, a note, the keys, a picture, the value in the file and a",
             "link to the reference page. The page fills in what it knows itself (the value, the unit, the place); the words",
             "below are the part that is written by hand. A tip that changes with the page's state (a hidden layer, a locked",
             "switch, a run that is out of date) is listed once per state.", "",
             "## Settings", "",
             "Each setting's tip opens from the (i) beside its name, in Basic and in Advanced. The settings the page does not",
             "list (the folder and file names of a run, and `GENERATOR_MODE`, which is the Strict switch) have no tip.", "",
             "| No. | Name in the file | Parameter files | First sentence | Picture |", "|---|---|---|---|---|"]
    k = 0
    for name, tip in words.PARAMS.items():
        k += 1
        pic = tip.get("picture", {}).get("file", "")
        lines.append(f"| {k} | `{name}` | {shows.get(name, '')} | {_cell(tip['lead'])} | {('`' + pic + '`') if pic else ''} |")
    lines += ["", "## Buttons, switches and other controls", "", "| No. | Tip id | First sentence | Keys |", "|---|---|---|---|"]
    for name, tip in words.CONTROLS.items():
        k += 1
        keys = " + ".join(tip.get("keys", [])) + (f" ({tip['keysNote']})" if tip.get("keysNote") else "")
        lines.append(f"| {k} | `{name}` | {_cell(tip['lead'])} | {_cell(keys)} |")
    lines += ["", "In these texts a word in braces, such as {layer} or {name}, is filled in by the page.", "",
              "## TX layout cards", "", "| No. | Card id | First sentence |", "|---|---|---|"]
    for name, tip in words.PRESETS.items():
        k += 1
        lines.append(f"| {k} | `{name}` | {_cell(tip['lead'])} |")
    lines += ["", f"Under every card: {_cell(words.PRESET_FOOT)}", ""]
    return "\n".join(lines)


def up_to_date():
    """Are WebGUI/tips.json and docs/tooltips/Inventory.md the files tips_words.py gives?"""
    try:
        with open(OUT, encoding="utf-8") as fh:
            if fh.read() != text():
                return False
        with open(INVENTORY, encoding="utf-8") as fh:
            return fh.read() == inventory()
    except OSError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Writes WebGUI/tips.json and docs/tooltips/Inventory.md from tips_words.py.")
    ap.add_argument("--check", action="store_true", help="only compare the two files with what would be written")
    args = ap.parse_args(argv)
    wrong = problems()
    for p in wrong:
        print(f"build_tips: {p}")
    if wrong:
        return 1
    new = text()
    json.loads(new)                                             # the file must be JSON
    if args.check:
        same = up_to_date()
        print("tips.json and Inventory.md are up to date" if same else "tips.json or Inventory.md is not the one tips_words.py gives: run build_tips.py")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    with open(INVENTORY, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(inventory())
    n = len(words.PARAMS) + len(words.CONTROLS) + len(words.PRESETS)
    pictures = {tip["picture"]["file"] for tip in words.PARAMS.values() if tip.get("picture")}
    print(f"tips.json: {n} tips ({len(words.PARAMS)} settings, {len(words.CONTROLS)} controls, {len(words.PRESETS)} cards), "
          f"{len(pictures)} pictures")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
build_tips.py  -  writes WebGUI/tips.json, the words of every help box (tooltip) of the page.

    python WebGUI/tools/build_tips.py            write tips.json
    python WebGUI/tools/build_tips.py --check    only say whether tips.json is the one tips_words.py gives (exit 1 if not)

The words are written in tips_words.py; the page reads only tips.json (WebGUI/app/tips.js).  The file has one tip
per line, so a change of words shows as one changed line:

    {"params":   {NAME: {lead, choices, facts, formula, note, picture}},     the settings, by their name in the file
     "controls": {tip id: {lead, facts, note, keys, keysNote}},              buttons, switches and other controls
     "presets":  {card id: {lead}},                                         the TX layout cards
     "presetFoot": "...", "overrideChoice": "..."}

A tip that names a picture must find it in WebGUI/docs/tooltips/pictures (build_site.py copies that folder).
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


def up_to_date():
    """Is WebGUI/tips.json the file tips_words.py gives?"""
    try:
        with open(OUT, encoding="utf-8") as fh:
            return fh.read() == text()
    except OSError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description="Writes WebGUI/tips.json from tips_words.py.")
    ap.add_argument("--check", action="store_true", help="only compare tips.json with what would be written")
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
        print("tips.json is up to date" if same else "tips.json is not the one tips_words.py gives: run build_tips.py")
        return 0 if same else 1
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(new)
    n = len(words.PARAMS) + len(words.CONTROLS) + len(words.PRESETS)
    pictures = {tip["picture"]["file"] for tip in words.PARAMS.values() if tip.get("picture")}
    print(f"tips.json: {n} tips ({len(words.PARAMS)} settings, {len(words.CONTROLS)} controls, {len(words.PRESETS)} cards), "
          f"{len(pictures)} pictures")
    return 0


if __name__ == "__main__":
    sys.exit(main())

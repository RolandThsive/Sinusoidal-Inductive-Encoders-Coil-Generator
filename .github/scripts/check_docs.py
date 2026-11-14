"""
check_docs.py  -  the documentation's own links (run by the CI on every pull request and push):

    python .github/scripts/check_docs.py

Every tracked Markdown file is read.  Each relative link and image, in Markdown ([text](target), ![alt](target)) or in
HTML (<a href>, <img src>), must point at a file or folder that exists in the repository; a wiki page may also be
named without its .md, as the GitHub wiki does.  Links to web addresses, e-mail and anchors on the same page are not
followed (no network in this check).  Every page in docs/wiki must be listed in docs/wiki/_Sidebar.md, so no page is
left out of the wiki's navigation.

Needs only Python and git.  Exit code 0 when every link resolves.
"""

import os
import re
import subprocess
import sys
from urllib.parse import unquote

WIKI = "docs/wiki"
SIDEBAR = os.path.join(WIKI, "_Sidebar.md")
NOT_PAGES = ("_Sidebar.md", "_Footer.md", "Home.md")

FENCE = re.compile(r"^\s*(```|~~~)")
CODE = re.compile(r"`[^`]*`")
MD_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
REF_DEF = re.compile(r"^\s*\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+\"[^\"]*\")?\s*$")
HTML = re.compile(r"<(?:a|img|source)\b[^>]*?\s(?:href|src|srcset)\s*=\s*[\"']([^\"']+)[\"']", re.I)
EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)


def links(text):
    """(line number, target) of every link outside code."""
    out, fenced = [], False
    for n, line in enumerate(text.split("\n"), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        line = CODE.sub("", line)
        for rx in (MD_LINK, HTML):
            for m in rx.finditer(line):
                out.append((n, m.group(1)))
        m = REF_DEF.match(line)
        if m:
            out.append((n, m.group(1)))
    return out


def resolves(page, target, tracked_dirs, tracked):
    path = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path:
        return True
    base = "" if path.startswith("/") else os.path.dirname(page)
    full = os.path.normpath(os.path.join(base, path.lstrip("/"))).replace(os.sep, "/")
    if full in tracked or full in tracked_dirs:
        return True
    return page.startswith(WIKI + "/") and "." not in os.path.basename(full) and full + ".md" in tracked


def main():
    tracked = {f for f in subprocess.run(["git", "ls-files", "-z"], capture_output=True, text=True, check=True,
                                         encoding="utf-8").stdout.split("\0") if f}
    tracked_dirs = {os.path.dirname(f) for f in tracked}
    for d in list(tracked_dirs):
        while d:
            d = os.path.dirname(d)
            tracked_dirs.add(d)
    problems, count = [], 0
    pages = sorted(f for f in tracked if f.lower().endswith(".md"))
    for page in pages:
        with open(page, encoding="utf-8") as fh:
            text = fh.read()
        for n, target in links(text):
            if EXTERNAL.match(target):
                continue
            count += 1
            if not resolves(page, target, tracked_dirs, tracked):
                problems.append(f"{page}:{n}: the link {target!r} points at nothing in the repository")

    with open(SIDEBAR, encoding="utf-8") as fh:
        listed = {os.path.basename(unquote(t.split("#", 1)[0])) for _n, t in links(fh.read())}
    listed |= {t + ".md" for t in listed if not t.endswith(".md")}
    for page in pages:
        if page.startswith(WIKI + "/") and page.count("/") == 2 and os.path.basename(page) not in NOT_PAGES \
                and os.path.basename(page) not in listed:
            problems.append(f"{page}: not listed in {SIDEBAR}, so the wiki's navigation never reaches it")

    for p in problems:
        print(f"::error::{p}")
    print(f"{len(pages)} Markdown files, {count} relative links checked: "
          + ("all resolve" if not problems else f"{len(problems)} problem(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

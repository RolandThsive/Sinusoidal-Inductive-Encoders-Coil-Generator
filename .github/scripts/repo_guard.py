"""
repo_guard.py  -  what must never be committed (run by the CI on every pull request and push):

    python .github/scripts/repo_guard.py                      the tracked files
    python .github/scripts/repo_guard.py --commits A..B       also the messages of the commits A..B
    PR_TEXT="..." python .github/scripts/repo_guard.py        also a pull request's title and description

It fails on
  - Python bytecode (__pycache__ folders, .pyc / .pyo files): Python makes them on every machine, they never belong
    in git;
  - files in an Output folder other than its placeholder: what a run writes stays on the machine that ran it;
  - files over 5 MB: the repository stays small enough to clone quickly;
  - session details of an AI assistant (a link to a session, a session trailer) in a tracked file, a commit message
    or the pull request text: the project's rule is that commits name only "Co-Authored-By: Claude".

Needs only Python and git.  Exit code 0 when nothing was found.
"""

import argparse
import os
import re
import subprocess
import sys

MAX_BYTES = 5 * 1024 * 1024
OUTPUT_FOLDERS = ("Generators/Single Coil Set Generator/Output/", "Generators/Dual Coil Set Generator/Output/")
OUTPUT_PLACEHOLDER = "Output Folders Show Up Here.txt"
BINARY = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".gz", ".pdf", ".ttf", ".otf", ".woff", ".woff2", ".ico")

# Built from pieces, so that this file does not match itself.
_SESSION = [re.compile(re.escape("claude.ai/code/" + "session_"), re.I),
            re.compile(r"^\s*" + "Claude-" + r"Session\s*:", re.I | re.M)]


def git(*args):
    return subprocess.run(["git"] + list(args), capture_output=True, text=True, check=True, encoding="utf-8").stdout


def session_hits(text):
    return [m.group(0).strip() for rx in _SESSION for m in rx.finditer(text)]


def check_files(problems):
    files = [f for f in git("ls-files", "-z").split("\0") if f]
    for f in files:
        low = f.lower()
        if "__pycache__/" in f or low.endswith((".pyc", ".pyo")):
            problems.append(f"{f}: Python bytecode is committed (it is made on every machine; .gitignore keeps it out)")
            continue
        if f.startswith(OUTPUT_FOLDERS) and os.path.basename(f) != OUTPUT_PLACEHOLDER:
            problems.append(f"{f}: a generated file in an Output folder is committed")
        if not os.path.isfile(f):
            continue                                    # deleted in the working tree, or a link to nothing
        size = os.path.getsize(f)
        if size > MAX_BYTES:
            problems.append(f"{f}: {size / 1048576:.1f} MB, over the 5 MB limit")
        if not low.endswith(BINARY):
            with open(f, encoding="utf-8", errors="replace") as fh:
                hits = session_hits(fh.read())
            if hits:
                problems.append(f"{f}: holds session details ({hits[0]!r})")
    return len(files)


def check_commits(rng, problems):
    shas = [s for s in git("rev-list", rng).split() if s]
    for sha in shas:
        hits = session_hits(git("log", "-1", "--format=%B", sha))
        if hits:
            problems.append(f"commit {sha[:9]}: its message holds session details ({hits[0]!r}); "
                            f"reword it before merging")
    return len(shas)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fail on files and texts that must never be committed.")
    ap.add_argument("--commits", help="also check the messages of these commits, e.g. origin/main..HEAD")
    args = ap.parse_args(argv)
    problems = []
    n = check_files(problems)
    print(f"{n} tracked files checked")
    if args.commits:
        print(f"{check_commits(args.commits, problems)} commit messages checked ({args.commits})")
    pr_text = os.environ.get("PR_TEXT")
    if pr_text:
        hits = session_hits(pr_text)
        if hits:
            problems.append(f"the pull request title or description holds session details ({hits[0]!r})")
        print("pull request title and description checked")
    for p in problems:
        print(f"::error::{p}")
    print("OK: nothing that must not be committed" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

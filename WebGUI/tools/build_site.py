"""
build_site.py  -  makes the folder that GitHub Pages serves.

    python WebGUI/tools/build_site.py [--out site] [--commit <hash>]

    site/index.html                     sends the visitor on to WebGUI/
    site/WebGUI/...                     the page: every file of WebGUI/ that a browser needs
    site/WebGUI/py/generators.zip       the generators' own .py files at their own paths (Generators/...) and
                                        WebGUI/WebGenerator.py; PyodideWorker.js unpacks it
    site/WebGUI/version.json            the commit, the date, and the SHA-256 of generators.zip

Nothing of the repository is changed.  The zip is the same byte for byte for the same files (sorted names, one fixed
date), so its hash only changes when a generator file does.  Tests, tools, documents and this script are not copied.
Needs only Python 3.
"""

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEB = os.path.join(REPO, "WebGUI")
# folders of WebGUI/ that are not part of the page
NOT_SERVED_DIRS = {"tests", "tools", "docs", "node_modules", "__pycache__", "test-results", "playwright-report"}
# files of WebGUI/ that are not part of the page (WebGenerator.py travels inside the zip)
NOT_SERVED_FILES = {"WebGenerator.py", "FutureConsiderations.md", "package.json", "package-lock.json",
                    "playwright.config.js", "README.md", "CHANGELOG.md"}
SERVED_TYPES = {".html", ".js", ".mjs", ".css", ".json", ".woff2", ".webp", ".png", ".svg", ".ico", ".txt", ".md",
                ".wasm", ".zip", ".whl"}
REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Sinusoidal Inductive Encoder Coil Generator</title>
<meta http-equiv="refresh" content="0; url=WebGUI/">
<link rel="canonical" href="WebGUI/">
</head>
<body>
<p><a href="WebGUI/">Sinusoidal Inductive Encoder Coil Generator</a></p>
</body>
</html>
"""


def generator_files():
    """[(path in the repository, path in the zip)] of every generator file, sorted."""
    out = []
    top = os.path.join(REPO, "Generators")
    for folder, dirs, files in os.walk(top):
        dirs[:] = sorted(d for d in dirs if d not in ("__pycache__", "Output"))
        for f in sorted(files):
            if f.endswith(".py"):
                full = os.path.join(folder, f)
                out.append((full, os.path.relpath(full, REPO).replace(os.sep, "/")))
    out.append((os.path.join(WEB, "WebGenerator.py"), "WebGUI/WebGenerator.py"))
    return sorted(out, key=lambda pair: pair[1])


def write_bundle(path):
    """The zip of the generator files.  Returns (its SHA-256, the number of files)."""
    files = generator_files()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for full, name in files:
            with open(full, "rb") as fh:
                data = fh.read()
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest(), len(files)


def copy_page(dest):
    """Copy the files of WebGUI/ that a browser needs.  Returns their number."""
    n = 0
    for folder, dirs, files in os.walk(WEB):
        dirs[:] = sorted(d for d in dirs if d not in NOT_SERVED_DIRS and not d.startswith("."))
        rel = os.path.relpath(folder, WEB)
        for f in sorted(files):
            if rel == "." and f in NOT_SERVED_FILES:
                continue
            if os.path.splitext(f)[1].lower() not in SERVED_TYPES:
                continue
            target = os.path.join(dest, rel, f) if rel != "." else os.path.join(dest, f)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(folder, f), target)
            n += 1
    return n


def commit_of(repo):
    try:
        return subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Make the folder that GitHub Pages serves.")
    ap.add_argument("--out", default=os.path.join(REPO, "site"), help="the folder to make (emptied first)")
    ap.add_argument("--commit", default=None, help="the commit to stamp (default: the checkout's HEAD)")
    args = ap.parse_args(argv)
    out = os.path.abspath(args.out)
    if os.path.exists(out):
        if not os.path.isfile(os.path.join(out, ".built-by-build_site")):
            print(f"{out} exists and was not made by this script: it is left alone. Give another --out.")
            return 1
        shutil.rmtree(out)
    page = os.path.join(out, "WebGUI")
    os.makedirs(os.path.join(page, "py"))
    with open(os.path.join(out, ".built-by-build_site"), "w") as fh:
        fh.write("made by WebGUI/tools/build_site.py; safe to delete\n")
    with open(os.path.join(out, ".gitignore"), "w") as fh:        # the built folder is never committed
        fh.write("*\n")
    with open(os.path.join(out, ".nojekyll"), "w") as fh:
        fh.write("")
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(REDIRECT)
    copied = copy_page(page)
    sha, count = write_bundle(os.path.join(page, "py", "generators.zip"))
    version = {"commit": args.commit or commit_of(REPO),
               "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               "generators": {"file": "py/generators.zip", "sha256": sha, "files": count}}
    with open(os.path.join(page, "version.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(version, fh, indent=2)
        fh.write("\n")
    print(f"{out}: {copied} page files, {count} generator files in py/generators.zip ({sha[:12]}), "
          f"commit {version['commit'][:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

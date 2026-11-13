"""
build_site.py  -  makes the folder that GitHub Pages serves.

    python WebGUI/tools/build_site.py [--out site] [--commit <hash>] [--fetch-vendor | --vendor <folder>]

    site/index.html                     sends the visitor on to WebGUI/
    site/WebGUI/...                     the page: every file of WebGUI/ that a browser needs
    site/WebGUI/py/generators.zip       the generators' own .py files at their own paths (Generators/...) and
                                        WebGUI/WebGenerator.py; PyodideWorker.js unpacks it
    site/WebGUI/vendor/pyodide/         the site's own backup copy of Pyodide, each file checked against its SHA-256
                                        (vendor_lock.py): downloaded with --fetch-vendor, or taken from a folder with
                                        --vendor; without either the site has no backup and the page knows it
    site/WebGUI/version.json            the commit, the date, the SHA-256 of generators.zip, and where Pyodide comes from

The security policy of every page is written here: the <!--CSP--> line of an .html file becomes its
Content-Security-Policy meta tag (the tool's page: scripts from the site and from the one CDN folder of Pyodide; the
text pages: no script at all).

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vendor_lock  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEB = os.path.join(REPO, "WebGUI")
# folders of WebGUI/ that are not part of the page
NOT_SERVED_DIRS = {"tests", "tools", "docs", "node_modules", "__pycache__", "test-results", "playwright-report"}
# files of WebGUI/ that are not part of the page (WebGenerator.py travels inside the zip)
NOT_SERVED_FILES = {"WebGenerator.py", "FutureConsiderations.md", "package.json", "package-lock.json",
                    "playwright.config.js", "README.md", "CHANGELOG.md", "vendor.json", "BloggerPage.html"}
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


def policies(cdn):
    """{placeholder: Content-Security-Policy meta tag}.  The tool's page may load scripts from the site and from the
    one CDN folder of this Pyodide version (the Python worker's import), run WebAssembly, and read from those two
    places; pictures of a run are shown from memory (blob:).  The text pages load a style sheet and fonts only."""
    tool = ("default-src 'none'; "
            f"script-src 'self' {cdn} 'wasm-unsafe-eval'; worker-src 'self'; connect-src 'self' {cdn}; "
            "style-src 'self'; font-src 'self'; img-src 'self' blob:; "
            "base-uri 'none'; form-action 'none'; object-src 'none'")
    text = "default-src 'none'; style-src 'self'; font-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'"
    tag = '<meta http-equiv="Content-Security-Policy" content="{}">'
    return {"<!--CSP-->": tag.format(tool), "<!--CSP-TEXT-->": tag.format(text)}


def write_policies(page, cdn):
    """Put the policy into every .html file of the built page.  Returns the number of files; a file without a
    placeholder stops the build (a page must never go out without its policy)."""
    n = 0
    for folder, _dirs, files in os.walk(page):
        if os.path.join(page, "vendor") in folder:
            continue
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(folder, f)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            hits = [(mark, tag) for mark, tag in policies(cdn).items() if text.count(mark) == 1]
            if len(hits) != 1:
                raise ValueError(f"{os.path.relpath(path, page)}: one <!--CSP--> or <!--CSP-TEXT--> line is needed")
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text.replace(*hits[0]))
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
    ap.add_argument("--fetch-vendor", action="store_true", help="download the backup copy of Pyodide into the site")
    ap.add_argument("--vendor", default=None, help="take the backup copy of Pyodide from this folder")
    args = ap.parse_args(argv)
    pyodide = vendor_lock.lock()
    with open(os.path.join(WEB, "app", "main.js"), encoding="utf-8") as fh:
        if f'"{pyodide["cdn"]}"' not in fh.read():
            print(f"WebGUI/app/main.js does not name the CDN folder of vendor.json ({pyodide['cdn']}): nothing is built.")
            return 1
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
    backup = False
    try:
        pages = write_policies(page, pyodide["cdn"])
        if args.vendor or args.fetch_vendor:
            vendor_lock.place(os.path.join(page, "vendor", "pyodide"), args.vendor)
            backup = True
    except (OSError, ValueError, KeyError) as e:
        print(f"{e}\nNothing is published from {out}.")
        shutil.rmtree(out)
        return 1
    version = {"commit": args.commit or commit_of(REPO),
               "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
               "generators": {"file": "py/generators.zip", "sha256": sha, "files": count},
               "pyodide": {"version": pyodide["version"], "cdn": pyodide["cdn"], "backup": "vendor/pyodide/" if backup else None}}
    with open(os.path.join(page, "version.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(version, fh, indent=2)
        fh.write("\n")
    print(f"{out}: {copied} page files ({pages} with their security policy), {count} generator files in "
          f"py/generators.zip ({sha[:12]}), Pyodide {pyodide['version']} "
          f"{'with the backup copy' if backup else 'WITHOUT a backup copy'}, commit {version['commit'][:7]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
vendor_lock.py  -  the site's own backup copy of Pyodide, every file checked against its SHA-256.

    python WebGUI/tools/vendor_lock.py --out <folder>                  download the files, check them, write them
    python WebGUI/tools/vendor_lock.py --out <folder> --from <folder>  take them from a folder instead (no network)
    python WebGUI/tools/vendor_lock.py --check <folder>                only check a folder

WebGUI/vendor.json names the version, where the page loads Pyodide from first (the CDN), and the six files the page
needs, each with its size and SHA-256.  The page loads Python from the CDN; when the CDN does not answer, it loads
this copy from the site itself (WebGUI/app/engine.js).

The Python runtime's files come from the pyodide package of the npm registry (one .tgz); the numpy wheel, which that
package does not hold, from the CDN.  Its hash is also the one pyodide-lock.json names, so the runtime itself would
refuse another wheel.  A file whose hash differs is never written: the build stops and says which file.

A new Pyodide version: change "version", "cdn" and "npm" in vendor.json, run with --update <folder of the new files>,
and change PYODIDE_CDN in WebGUI/app/main.js (build_site.py refuses to build while the two differ).
Needs only Python 3.
"""

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK = os.path.join(os.path.dirname(HERE), "vendor.json")
LIMIT = 64 * 1024 * 1024                                       # no file of Pyodide is near this size


def lock():
    with open(LOCK, encoding="utf-8") as fh:
        return json.load(fh)["pyodide"]


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _get(url):
    """The bytes at an https address (three tries)."""
    if not url.startswith("https://"):
        raise ValueError(f"{url}: only https addresses are downloaded")
    last = None
    for _try in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:      # noqa: S310 - https only, checked above
                data = r.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise ValueError(f"{url}: larger than {LIMIT} bytes")
            return data
        except OSError as e:
            last = e
    raise OSError(f"{url} could not be downloaded: {last}")


def _checked(name, data, want):
    if len(data) != want["bytes"] or sha256(data) != want["sha256"]:
        raise ValueError(f"{name}: {len(data)} bytes, SHA-256 {sha256(data)}; vendor.json names {want['bytes']} bytes, "
                         f"{want['sha256']}.  The file is not written.")
    return data


def from_folder(folder):
    """{name: bytes} of the six files, read from a folder and checked."""
    out = {}
    for name, want in lock()["files"].items():
        with open(os.path.join(folder, name), "rb") as fh:
            out[name] = _checked(name, fh.read(), want)
    return out


def from_network():
    """{name: bytes} of the six files, downloaded and checked."""
    info, out = lock(), {}
    with tarfile.open(fileobj=io.BytesIO(_get(info["npm"])), mode="r:gz") as tar:
        for name, want in info["files"].items():
            if want["from"] != "npm":
                continue
            member = tar.extractfile("package/" + name)
            if member is None:
                raise ValueError(f"{name} is not in {info['npm']}")
            out[name] = _checked(name, member.read(), want)
    for name, want in info["files"].items():
        if want["from"] == "cdn":
            out[name] = _checked(name, _get(info["cdn"] + name), want)
    return out


def place(dest, source=None):
    """Write the checked files into dest (made if missing).  Returns their names."""
    files = from_folder(source) if source else from_network()
    os.makedirs(dest, exist_ok=True)
    for name, data in files.items():
        with open(os.path.join(dest, name), "wb") as fh:
            fh.write(data)
    return sorted(files)


def update(folder):
    """Write the sizes and hashes of the files in `folder` into vendor.json (a new Pyodide version)."""
    with open(LOCK, encoding="utf-8") as fh:
        whole = json.load(fh)
    for name, want in whole["pyodide"]["files"].items():
        with open(os.path.join(folder, name), "rb") as fh:
            data = fh.read()
        want["sha256"], want["bytes"] = sha256(data), len(data)
    with open(LOCK, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(whole, fh, indent=2)
        fh.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="The site's own backup copy of Pyodide, checked against vendor.json.")
    ap.add_argument("--out", help="the folder to write the files into")
    ap.add_argument("--from", dest="source", help="take the files from this folder instead of downloading them")
    ap.add_argument("--check", help="only check the files of this folder")
    ap.add_argument("--update", help="write the hashes of the files of this folder into vendor.json")
    args = ap.parse_args(argv)
    try:
        if args.update:
            update(args.update)
            print(f"vendor.json now names the files of {args.update}")
        elif args.check:
            print(f"{args.check}: {len(from_folder(args.check))} files are the ones vendor.json names")
        elif args.out:
            names = place(args.out, args.source)
            print(f"{args.out}: {len(names)} files of Pyodide {lock()['version']}, each checked against its SHA-256")
        else:
            ap.error("give --out, --check or --update")
    except (OSError, ValueError, KeyError) as e:
        print(f"vendor_lock: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

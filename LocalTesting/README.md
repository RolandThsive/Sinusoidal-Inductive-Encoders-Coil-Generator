# Local Testing

This branch (`WebUI_LocalTesting`) is how the Web GUI is tried out on a desktop before it goes live.
It replaces the old test zip: the branch itself is the tester, and it always holds the latest Web GUI.

## Try it

1. Download or clone this branch.
2. Windows: double-click `LocalTesting/Start-Windows.bat`.
   Mac / Linux: run `LocalTesting/Start-Mac-Linux.command` (double-click, or in a terminal).
3. A small local web server starts (needs Python 3) and the page opens in your browser at `http://localhost:8000/WebGUI/`.
   If port 8000 is busy it uses the next free one; the window shows the address.
4. The first start downloads Python for the browser (Pyodide, about 20 MB) from the internet; later starts are cached.

Caching is switched off in the test server, so the browser always loads the files of this branch.

Why a server instead of double-clicking `WebGUI/index.html`: browsers block the background Python thread and file
loading on `file://` pages, so the page has to come from `http://`.

## How the tester is made

The tester is the repository itself.

- `serve.py` first makes the site the way GitHub Pages gets it: it runs `WebGUI/tools/build_site.py`, which copies the
  page and packs the generators' own `.py` files (`Generators/`) into one zip, into `LocalTesting/_site/`. That folder
  is made new at every start and is never committed. Then it serves that folder.
- The Start scripts only run `serve.py`.
- Python for the browser (Pyodide) is loaded from a CDN, as on the live site.

The generators and their parameter files are Roland's, unchanged; only the Web GUI (`WebGUI/`) and this folder are ours.

## Keeping it current

This branch is kept equal to the newest Web GUI work:

1. Pull the working branch into it: `git checkout WebUI_LocalTesting && git merge origin/WebUI_modifs`
   (and `origin/main` when the generator changes), then push.
2. Nothing else: the site is made at every start.
3. Changes to `LocalTesting/` are made on this branch only; they never go into `WebUI` or `main`.

## How the screenshots were made

Screenshots for review are taken with Playwright and its Chromium:

1. Start the tester (above), or any static server on a folder made by `WebGUI/tools/build_site.py`.
2. Open `/WebGUI/` in a headless Chromium at the wanted window size (for example 1440 x 900, or 1080 x 1920 for a
   screen standing upright) and wait until `document.documentElement.dataset.state` is `ready`: Python has loaded
   and the first board stands. Then call `page.screenshot`. The Dual generator is the address with `#dual=` at
   its end.
3. To show a state, click the controls first: Advanced is `#mode-switch [data-mode="advanced"]`, its tabs are
   `#adv-tabs [data-key]`, a setting is `#advanced-panel .field[data-name="NAME"]`, the layer buttons are
   `.layer-chip`, the views of the preview are `#preview [data-view]`.
4. A help box opens when the mouse rests on a control, at once on an (i) (`.info-dot`), and closes when the page
   scrolls: move the mouse onto the control after the last scroll and wait about a second.

## Checks before a design goes live

- The tests pass: `python -m unittest WebGUI/tests/test_bridge.py` from the repository folder, and
  `npx playwright test` inside `WebGUI/` (after `npm ci`). The slower rounds are listed in
  `WebGUI/docs/BugRounds.md`, "How to run a round again".
- The starting design of both generators builds with no warnings (Single in about 3 s, Dual in about 20 s).
- Import, then Export, gives back the same parameter files.
- The page keeps its layout from 2560 x 1440 down to 320 x 256:
  `LAYOUT=all npx playwright test layout --project=chromium`.

# Changelog of the web tool

What changed on the page a visitor sees. The newest version is on top. The generator's own changes are in the
repository's releases.

## 2.0.1

- The grey line beside the note of a help box stands clear of the note's text again.
- The Pictures view is put away for now. The two pictures are still in the zip and in All Files.

## 2.0: the remake

The page was written again from the start. It now runs the desktop program itself, for both generators.

### New

- **The Dual generator.** The menu beside the title chooses Single or Dual (Arc and Linear are listed, greyed
  out, for later). Each generator keeps its own settings, its own board and its own view while the other is
  open.
- **The desktop program, unchanged.** The page runs the same Python files as a desktop run and gets the same
  files, byte for byte: both boards, their `.kicad_pro` files, `Parameters.txt` and the two pictures. This
  includes the electrical estimate, the receiver IC file and the silkscreen suggestion, which the old page left
  out.
- **Every setting of every parameter file** in Advanced, in the order of the file: 104 for Single, 187 for Dual (all but the
  folder and file names of a run, which the page gives itself, and the Strict switch, which stands beside Generate).
  The 16 silkscreen settings have their own tab. **Find A Setting** searches all of them by name.
- **The run box.** While the generator runs, the preview shows its steps, the line it is printing, the time,
  and a Cancel button.
- **Check Only** runs the generator's checks without making boards.
- **Run Text** shows everything the generator printed, as on the desktop. **All Files** lists every file of the
  run for download one by one. The **Pictures** view shows the two pictures of the run.
- **Results under the settings**: range, inductance, resistance, frequency, capacitors and board size of the
  board on show; for Dual, of both coil sets side by side.
- **Help boxes in one layout** on every control and every setting: where the setting is, its name and unit, its
  name in the file, one sentence, the choices, the value in the file and a link to the reference page. Fifteen
  settings show a picture drawn from generated boards.
- **Import** takes `Parameters.txt`, parameter files and zips of either generator, several at once. Files of the
  other generator switch the page to it. What is not taken is named, with the reason.
- **The keyboard reaches everything**: Tab goes through the page in its order, menus and dialogs give the focus
  back, the preview moves, zooms and measures with keys.
- **Smaller windows.** The page keeps its layout from 2560 × 1440 down to 1024 × 768 and reflows into one
  column below 1000 px, down to 320 × 256 (400 % zoom).
- **Privacy and licences pages**, a build stamp in the footer, and Report A Problem.

### Changed

- **Where Python comes from.** Pyodide is pinned by version. It loads from the CDN and, when the CDN does not
  answer within 15 seconds, from the site's own checked copy. The fonts are on the site too: the page asks no
  other server for anything.
- **A security policy** in every page: scripts only from the site and the one CDN folder, no inline code.
- **The site is built** by a build step (`tools/build_site.py`) and published by GitHub Actions. The address is
  the same.
- **Share links** start with `#single=` or `#dual=`. Links of the old page (`#d=`) still open.
- **Strict, Reset, Generate** and the downloads work as before. A changed setting marks the board as old until
  the next Generate.
- The three settings that place the board on the KiCad page (`CENTER_X_MM`, `CENTER_Y_MM`, `PAGE_SIZE_MM`) can be
  set, as in the parameter file. The old page kept them fixed.

### Fixed

The bug rounds before the release found and fixed 41 faults of the new page. They are listed, each with its
test, in [docs/BugRounds.md](docs/BugRounds.md).

### Removed

- **Summary.** Run Text shows the generator's whole report instead.
- The web tool's own copy of the generator's rules: the page now reads them from the generator.

## Before 2.0

Versions V12 to V18 of the first page followed the generator's versions. Their changes are in the history of the
`WebUI` branch.

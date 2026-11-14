# Inductive Encoder Coil Generator: Web Tool

Design the stator and rotor boards of a sinusoidal inductive encoder in your browser, see them straight away,
and download them as KiCad files. No installation and no account: everything runs on your own computer, and
nothing is sent to a server. The web tool runs the same generator as the desktop version, so the same settings
give the same boards.

**[Open The Web Tool](https://ro-h-bots.blogspot.com/p/inductive-encoder-sinusoidal-coil.html)**

## Features

- **Two generators.** The menu beside the title chooses the Single or the Dual generator (two coil sets on one
  board). Each keeps its own settings and its own board while the other is open.
- **The desktop program itself.** The page runs the same Python files as a desktop run and writes the same
  files, byte for byte.
- **Basic and Advanced.** Basic has the main settings on four tabs: Board, RX, TX and Rotor. Advanced has every
  setting of every parameter file, in the order of the file, and a box to find a setting by name. A change in
  one shows in the other.
- **Live board preview** of the stator, the rotor, or both together, with each copper layer in its own colour
  (Top red, Bottom blue, Inner-1 green, Inner-2 dark yellow), and the pictures of the run.
- **The run, step by step.** While the generator works the page shows its steps, the line it is printing and
  the time, with a Cancel button.
- **Design checks** before every board is made: errors and warnings that say what is wrong, why it matters and
  which settings to change. A setting named in a message is a link to that setting.
- **KiCad downloads:** one zip with the folder a desktop run writes, the stator or the rotor alone, or any file
  of the run.
- **Help on every setting and every button:** rest the mouse on it, or press the **i** next to a name. Some
  settings show a picture.
- **Save and share:** export your settings, import them later (also from the desktop version), or copy a link
  that opens the page with your design.
- **Measuring and inspection tools** in the preview: zoom, highlight a layer or a coil, hide parts, measure
  distances, turn the rotor.
- **Keyboard and screen reader:** everything on the page can be reached and used without a mouse.

## Getting Started

1. Open the tool at [ro-h-bots.blogspot.com](https://ro-h-bots.blogspot.com/p/inductive-encoder-sinusoidal-coil.html). The first visit downloads the browser's Python engine (about 20 MB); later visits are quick.
2. The page starts with the published design, already generated.
3. Change settings in **Basic**, then press **Generate** (or Ctrl+Enter / Cmd+Enter).
4. Check the result in the preview and the **Checks** panel.
5. Press **Download Zip** to get your boards.

The tool needs a computer with a mouse or trackpad. Phones and tablets see a short message instead.

## Setting Up A Design

### Single Or Dual

The menu beside the title switches between the two generators. Dual puts two coil sets on one board, an inner
and an outer one: its RX, TX, Rotor and IC settings exist once for each set, and a **Set 1 · Inner | Set 2 ·
Outer** switch under the tabs says whose settings are shown. Arc and Linear are listed for later.

### Basic

| Tab | Settings |
| --- | --- |
| Board | Board inner and outer radius, 2 or 4 copper layers, air gap to the rotor |
| RX | Loops (sine periods per turn), RX sub-coils, and the RX band |
| TX | TX turns per layer, and the TX layout, picked from picture cards |
| Rotor | Automatic (sized from the stator) or Custom, with the metal fraction and sectors |

Every Basic setting is also in Advanced, under the same name.

### Advanced

Every setting of the generator, one tab for each parameter file (Board, RX, TX, Rotor, IC and Silkscreen
suggestion), in the order of the file. Each one shows its name in the file, and the **↺** button puts it back to
its starting value. Settings the current design does not use are greyed out. A changed setting gets a dot before
its name, and its tab gets a dot too. **Find A Setting** lists the matches of every file.

### The RX Band And The None Switches

The RX band is the ring the receiver coils swing across. You can give it in one of three ways:

| How | Set | Leave None |
| --- | --- | --- |
| By its radii | RX Inside Radius and RX Outside Radius | R Base and Swing A |
| By its centre and width | R Base and Swing A | RX Inside Radius and RX Outside Radius |
| From the board | Board Inner Radius and Board Outer Radius | all four RX band values |

- Turn a **None** switch on to leave that value to the generator.
- The two values of a pair always change together.
- While one pair has numbers, the other pair is **locked** at None. To switch from one way to the other, set the
  pair in use to None first; both pairs are then unlocked.
- A board edge set to None is worked out from the RX band. A board edge with a number is used exactly, and the
  checks tell you if it leaves too little room.

## Generating And Downloading

- **Generate** makes the boards and runs the checks. After you change a setting, the board on show is marked as
  old until you generate again; the downloads always match the last generated board.
- **Check Only** runs the generator's checks and makes no boards.
- **Cancel**, in the box that shows the run, stops it. Python starts again, which takes a few seconds.
- **Strict** turns every warning about the finished boards into an error (`GENERATOR_MODE = "strict"` on the
  desktop), so such a design is not generated.
- **Checks** lists the errors and warnings. Turn on **Info** to also see the generator's notes.
- **Run Text** shows everything the generator printed in the run, as on the desktop.
- Under the settings the page shows the **results** of the board on show: range, inductance, resistance,
  frequency, capacitors and board size. For Dual, of both coil sets.
- **Download Zip** gives the folder a desktop run writes: both boards, their `.kicad_pro` files,
  `Parameters.txt` and the two pictures. **Stator** and **Rotor** give one `.kicad_pcb` each, and **All Files**
  lists every file of the run.

## Errors And Warnings

The checks do more than say that something is wrong: each message tells you what to change to fix it.

- **What is wrong, with the numbers.** A message names the setting, its value and the limit it broke, for
  example that OUTER_EDGE_RADIUS_MM is too small, and the radius the board needs instead.
- **Why it matters.** It says what would go wrong on the board, such as vias overlapping, traces too close
  together, or no room left for the TX turns.
- **What to change.** It lists the settings that fix it and which way to move them, for example "raise
  OUTER_EDGE_RADIUS_MM, move the RX band in, or lower OUTER_EDGE_OFFSET_MM". The names are the parameter names
  shown in Advanced, so each one is easy to find.
- **Where it came from.** Each line is marked Error, Warning or Info, with the step that found it: the
  settings check, the stator or the rotor.

**Errors** stop the run. No board is made, the preview keeps the last board marked out of date, and the downloads
stay off until a run works. **Warnings** still make the boards but point at something to look at, often a
manufacturing limit such as a very fine trace or a small via ring. Turn on **Strict** to treat every warning about the
finished boards as an error.

Some mistakes are blocked before they can happen: the RX band pairs lock each other, settings the design does not
use are greyed out, and a pair that must change together always does.

## The Preview

- **Stator, Rotor, Overlay, Pictures:** choose what to show. Overlay puts the rotor over the stator, and the
  **Rotor Angle** slider turns it. Pictures shows the two pictures the generator drew.
- **Layer buttons** (Top, Inner-1, Inner-2, Bottom, Vias): hover to highlight, click to hide or show. Hovering
  Vias makes small vias easier to see. **Silk Top** and **Silk Bottom** do the same for the silkscreen.
- **Sin Loops, Cos Loops, TX Loops:** the same for each coil. Dual also has **Set 1** and **Set 2**.
- **Zoom and move:** the mouse wheel zooms, dragging moves the board, and **Fit** (or a double-click) shows the
  whole board again. The centre marker button shows or hides the board centre.
- **Full screen:** the preview fills the screen; Esc leaves.
- **Measure:** click two points to see the distance. Press **S** to keep the line and draw another, **Z** to
  undo the last line or point.
- **With the keyboard,** on the drawing: the arrow keys move the board, **+** and **-** zoom, **0** fits it.
  While Measure is on the arrow keys move a cross instead (Shift for small steps) and Enter sets a point.

The preview tools only change what you see, never the boards.

## Saving, Sharing And Starting Over

- **Export** downloads the parameter files as a zip, ready for the desktop version.
- **Help** opens the [Quick Guide To Parameters Selections](https://github.com/RolandThsive/Sinusoidal-Inductive-Encoders-Coil-Generator/wiki/Quick-Guide-To-Parameters-Selections) on the project wiki in a new tab.
- **Import** loads a `Parameters.txt` from any run (web or desktop), your own parameter files, or a zip of
  them, several at once. Files of the other generator switch the page to it. Whatever is not taken is named with
  the reason: a setting this version no longer has, a value no setting can hold, a file that is too large.
- **Share** copies a link that opens the tool with your design. Only your changes are in the link, and nothing
  is uploaded. Links made with the page before version 2.0 still open.
- **Reset** goes back to the published design, after asking.

## Privacy

Everything runs in your browser. The page stores nothing on your computer, sets no cookies and sends nothing
anywhere. It loads Python (Pyodide) from the jsDelivr CDN and, when that does not answer, from its own copy; the
fonts are on the site. See the Privacy and Licences pages linked in the page's footer.

## For Developers

The page is in `WebGUI/`. It is built into a site folder and published by GitHub Actions from the `WebUI`
branch; changes come in from `WebUI_modifs` by pull request.

```
python WebGUI/tools/build_site.py --out site --fetch-vendor     # build the site (downloads and checks Pyodide)
cd WebGUI && npm ci && npx playwright install
npx playwright test                                             # the browser tests, on three browsers
python -m unittest WebGUI/tests/test_bridge.py                  # from the repository folder: the bridge to the generator
npm run serve                                                   # the built site on http://localhost:4173/WebGUI/
```

| Document | What it holds |
| --- | --- |
| [WebGUI/CHANGELOG.md](WebGUI/CHANGELOG.md) | What changed for a visitor, version by version |
| [WebGUI/docs/BugRounds.md](WebGUI/docs/BugRounds.md) | The bug rounds before version 2.0: what was checked, found and fixed |
| [WebGUI/docs/WCAG-EM.md](WebGUI/docs/WCAG-EM.md) | Accessibility: the page against WCAG 2.2, level AA |
| [WebGUI/docs/ASVS-L1.md](WebGUI/docs/ASVS-L1.md) | Security: the page against ASVS 5.0, level 1 |
| [WebGUI/docs/tooltips/Inventory.md](WebGUI/docs/tooltips/Inventory.md) | Every help box of the page |
| [WebGUI/FutureConsiderations.md](WebGUI/FutureConsiderations.md) | Ideas kept for later |

### Publishing On The Blog

1. On GitHub: Settings > Pages > Source: **GitHub Actions**. The workflow **Web GUI On GitHub Pages** builds and
   publishes the site on every push to `WebUI`. The tool is then at
   `https://rolandthsive.github.io/Sinusoidal-Inductive-Encoders-Coil-Generator/WebGUI/`.
2. On Blogger: Pages > New Page, switch the editor to **HTML view**, paste all of `WebGUI/BloggerPage.html`,
   and publish.

## License

The web tool is under the PolyForm Strict License 1.0.0, separate from the generator's license: see
[WebGUI/LICENSE.md](WebGUI/LICENSE.md). It may be used for noncommercial purposes only, and may not be changed or
redistributed. The core generator it runs stays under the repository's own [LICENSE.md](LICENSE.md).

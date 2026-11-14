# Accessibility report: WCAG 2.2, levels A and AA

The web tool gone through against the Web Content Accessibility Guidelines 2.2, in the order of the WCAG-EM
method: what is in scope, what was looked at, how, and the result for every success criterion of levels A and AA.
The criterion texts here are shortened: the guidelines' own words decide.

## 1. Scope

| | |
|---|---|
| What | The web tool at `…/WebGUI/`: the tool page (`index.html`), the Privacy page and the Licences page |
| Target | WCAG 2.2, level AA |
| Used with | A computer with a keyboard, and a mouse or trackpad. A phone or tablet gets a short message instead of the tool (it needs a pointer for the drawing and too much memory for most phones): the message itself is plain text and a link |
| Browsers | Chromium, Firefox and WebKit, the three the tests run on |
| Not in scope | The blog page that frames the tool on Blogger (only its two buttons and the frame's title are ours), the project's wiki, GitHub |

## 2. What the tool is made of

One page that changes with what the visitor does. Its states, all looked at:

- Loading Python, a run under way (the box with the steps and Cancel), a board made, a run refused, Python failed.
- Single and Dual generator; Basic (four tabs) and Advanced (six tabs for Single, six tabs with two coil sets for
  Dual); Find A Setting with matches and with none.
- The preview showing Stator, Rotor, Overlay and Pictures; Measure on; full screen.
- The open generator menu, a setting's menu, the help box of a control (181 of them), the four dialogs (Sure / No,
  Run Text, All Files, the error dialog), the short message at the bottom.
- Windows from 2560 × 1440 down to 320 × 256, which is 1280 × 1024 at 400 % zoom.

## 3. How it was looked at

| Way | What it covers | Where |
|---|---|---|
| axe-core, rules of WCAG 2.0 to 2.2 A and AA | Every tab of both generators in both views, the open menu, the dialogs, Pictures, full screen, an open help box | `tests/a11y.spec.js`, `tests/tips.spec.js`, on three browsers on every pull request |
| Keyboard only | Tab reaches every control once, in the order of the page; runs, menus and dialogs give the focus back; Measure with the keys | `tests/keyboard.spec.js` |
| A probe of names and roles | Every control has a name, no name twice in a group, every `aria-` reference resolves, headings and landmarks, the live regions | Bug round 16 (`docs/BugRounds.md`) |
| A probe of sizes | Target sizes, the focus ring, focus not covered, text spacing | Bug round 16 |
| The layout audit | No text cut off, nothing overlapping, at 13 computer sizes and 9 small ones | `tests/layout.spec.js`, `tests/audit.mjs`, bug rounds 13 and 14 |
| Every help box at five window sizes | Inside the window, readable, filled in | `tests/tips-sweep.spec.js`, bug rounds 17 and 18 |

Not done: a pass with a real screen reader by a person who uses one daily, and a pass on a real Safari. Both
are worth doing before the tool is called conformant; this report says what the code and the tests show.

## 4. Result, criterion by criterion

Of the 55 criteria of levels A and AA: met 42, met in part 3 (1.4.11, 2.2.1, 2.5.7), not applicable 10.

### Perceivable

| # | Criterion | Level | Result | How |
|---|---|---|---|---|
| 1.1.1 | Non-text content | A | Met | Icon buttons have names (Fullscreen, Fit, Origin, Measure), their drawings are hidden from screen readers. The board drawing is `role="img"` with a label that also tells its keys; what it shows in numbers is under the settings (range, R, L, C, f, board size) and in Run Text. The generator's two pictures and the pictures in help boxes have `alt` texts. |
| 1.2.1 to 1.2.5 | Audio and video | A, AA | Not applicable | The tool has no audio and no video. |
| 1.3.1 | Info and relationships | A | Met | Headings, landmarks (`header`, `nav`, `main`, `aside`, named sections, `footer`), tab lists with `aria-selected`, radio groups, switches, labels on every box, the Dual results as a table with headers. A message about a value is tied to its box with `aria-describedby` and `aria-invalid`. |
| 1.3.2 | Meaningful sequence | A | Met | The order in the page's code is the order on screen: tested as the Tab order (`keyboard.spec.js`). |
| 1.3.3 | Sensory characteristics | A | Met | No instruction leans on shape, colour or place alone: controls are named by their words. |
| 1.3.4 | Orientation | AA | Met | Nothing is locked to landscape or portrait; 768 × 1024 is one of the tested sizes. |
| 1.3.5 | Identify input purpose | AA | Not applicable | No box asks for anything about the visitor. |
| 1.4.1 | Use of colour | A | Met | A finding carries the word ERROR, WARNING or INFO. A changed setting has a dot, and its tab a dot. A layer or coil switched off is struck through, a locked one is struck corner to corner, and both say so to a screen reader (`aria-checked`, `aria-disabled`). Every copper colour has its named chip. |
| 1.4.2 | Audio control | A | Not applicable | No sound. |
| 1.4.3 | Contrast (minimum) | AA | Met | axe finds no text under 4.5:1 in any state. The lightest text colour (`--text-3`, #6a6a6a) was chosen for it. On the drawing, the label of a measured line is the accent red on white (6.1:1). |
| 1.4.4 | Resize text | AA | Met | At 200 % (640 × 512 for a 1280 × 1024 window) everything is there and works: `tips.spec.js`, the layout audit. |
| 1.4.5 | Images of text | AA | Met | Text is text. The lettering in the generator's pictures is SVG text. |
| 1.4.10 | Reflow | AA | Met | Below 1000 px the page is one column; at 320 × 256 nothing needs scrolling sideways except the board drawing and the pictures, which are two-dimensional by nature. |
| 1.4.11 | Non-text contrast | AA | Met in part | Controls, their states and the 2 px focus ring have 3:1 and more. On the drawing, Top (4.8:1), Bottom (4.9:1), Inner-1 (3.4:1), the board edge (12.6:1), the silkscreen marks (3.3:1) and the rim of a via (3.9:1) have it; Inner-2 (2.9:1), the fill of a via (1.6:1, inside its darker rim) and the translucent rotor of Overlay (1.5:1; 2.6:1 in the Rotor view) do not. These are the colours the project uses for its layers everywhere. Hover or focus on a chip brings one layer or coil out: drawn thicker, the rest faded. |
| 1.4.12 | Text spacing | AA | Met | With line height 1.5, letter spacing 0.12 em, word spacing 0.16 em and paragraph spacing 2 em set from outside, no text is cut off or covered, in any tab of both generators (bug round 16; the counts line of Checks was cut off and now goes on to a second line). |
| 1.4.13 | Content on hover or focus | AA | Met | A help box closes with Esc without moving the focus, the mouse can move onto it, and it stays until the mouse or the focus leaves: `tips.spec.js` "keyboard and mouse". |

### Operable

| # | Criterion | Level | Result | How |
|---|---|---|---|---|
| 2.1.1 | Keyboard | A | Met | Everything can be done with keys: `keyboard.spec.js`. On the drawing the arrow keys move the board, + and - zoom, 0 fits it; with Measure on the arrows move a cross and Enter sets a point. What the mouse shows by hovering (a layer or a coil brought out, a help box) the focus shows too. |
| 2.1.2 | No keyboard trap | A | Met | Tab goes through the page and comes round again; a dialog closes with Esc and hands the focus back. |
| 2.1.4 | Character key shortcuts | A | Met | S and Z work only while Measure is on, which its button switches off, and never while a box is typed in. +, - and 0 work only while the drawing has the focus. |
| 2.2.1 | Timing adjustable | A | Met in part | Nothing has a time limit. The short message at the bottom goes away by itself: it stays at least 2.6 s, longer for a longer text (70 ms a letter), and as long as the mouse rests on it, and a screen reader is told it (`role="status"`). What matters for a board never stands only there: findings are in Checks, a refused value under its setting. A reader who needs more time than that for a message about an import has no way to ask for it. |
| 2.2.2 | Pause, stop, hide | A | Met | The only movement that lasts is the spinner of a run, which is the sign that work is under way and ends with it. `prefers-reduced-motion` stops every animation and transition. |
| 2.3.1 | Three flashes | A | Met | Nothing flashes. |
| 2.4.1 | Bypass blocks | A | Met | Landmarks and headings; the page has one short top bar before its main part. |
| 2.4.2 | Page titled | A | Met | "Sinusoidal Inductive Encoder Coil Generator"; Privacy and Licences have their own titles. |
| 2.4.3 | Focus order | A | Met | The order of the page: `keyboard.spec.js` "Tab reaches every control once, in the order of the page". A menu or dialog gives the focus back to the control that opened it; a run gives it back to its button. |
| 2.4.4 | Link purpose | A | Met | Help, Privacy, Licences, Report A Problem, the name of a setting in a finding ("Show this setting"), a picture ("Open this picture in a new tab"). |
| 2.4.5 | Multiple ways | AA | Met | The site is three pages, each one link away from the others in the footer. Inside the tool, a setting is reached by its tab or by Find A Setting. |
| 2.4.6 | Headings and labels | AA | Met | Every setting has its name and unit; the panels have headings. |
| 2.4.7 | Focus visible | AA | Met | A 2 px ring in the accent colour on every control (on the thumb of a slider and the knob of a switch). |
| 2.4.11 | Focus not obscured (minimum) | AA | Met | Nothing on the page is fixed over the controls; a help box is placed beside its control where there is room. Probed by tabbing through both views of both generators. |
| 2.5.1 | Pointer gestures | A | Met | No gesture with several fingers or along a path. |
| 2.5.2 | Pointer cancellation | A | Met | Buttons act when the mouse button is let go. A point of Measure is set when it is pressed: Z takes it back. |
| 2.5.3 | Label in name | A | Met | The name a screen reader gets holds the words on screen ("RX Inside Radius: None" for the switch that shows "None"). |
| 2.5.4 | Motion actuation | A | Not applicable | Nothing is worked by moving the device. |
| 2.5.7 | Dragging movements | AA | Met in part | The board is moved by dragging. Without dragging it can be moved with the arrow keys, brought back with Fit, and any part can be shown by zooming with the wheel about the place the mouse points at. There are no buttons on screen for moving and zooming, so a reader with a pointer that only clicks cannot do it. The rotor angle is a slider of the browser's own, which takes clicks on its track and keys. |
| 2.5.8 | Target size (minimum) | AA | Met | Every target is 24 × 24 px or has that much room to itself (the (i) and the ↺ of a setting are 16 px and 15 px with free space around them); sliders are 24 px high. Probed in every tab, view, menu and dialog (bug round 16). |

### Understandable

| # | Criterion | Level | Result | How |
|---|---|---|---|---|
| 3.1.1 | Language of page | A | Met | `lang="en"` on all three pages. |
| 3.1.2 | Language of parts | AA | Met | Everything is English. Names of settings in capitals (`OUTER_EDGE_RADIUS_MM`) are names of the parameter files and are shown as such. |
| 3.2.1 | On focus | A | Met | Focus opens a help box and nothing else. |
| 3.2.2 | On input | A | Met | A changed setting changes that setting, marks the board as old, and, where the generator ties values together (a TX layout card, the pairs of the RX band), the values it names in its help box. Nothing moves the visitor elsewhere. Importing files of the other generator switches to it and says so. |
| 3.2.3 | Consistent navigation | AA | Met | The footer is the same on the three pages. |
| 3.2.4 | Consistent identification | AA | Met | The same control has the same name in Basic and Advanced, and in both generators. |
| 3.2.6 | Consistent help | A | Met | Help is in the top bar, Report A Problem in the footer, on every state of the page. |
| 3.3.1 | Error identification | A | Met | A value the generator refuses is named under its setting, in words, and announced (`role="alert"`). The findings of a run are a list with their level in words. |
| 3.3.2 | Labels or instructions | A | Met | Name, unit, the name in the file and a help box on every setting. |
| 3.3.3 | Error suggestion | AA | Met | The generator's messages say what to change and which way; a setting named in a message is a link to it. |
| 3.3.4 | Error prevention (legal, financial, data) | AA | Not applicable | Nothing is bought, sent or stored. Reset asks first all the same. |
| 3.3.7 | Redundant entry | A | Met | Nothing is asked for twice: each generator keeps its settings while the other is open. |
| 3.3.8 | Accessible authentication (minimum) | AA | Not applicable | No sign-in. |

### Robust

| # | Criterion | Level | Result | How |
|---|---|---|---|---|
| 4.1.2 | Name, role, value | A | Met | Every control has a role and a name, switches and tabs their state, menus `aria-expanded`: the probe of bug round 16 and axe. |
| 4.1.3 | Status messages | AA | Met | The steps of a run ("Step 2 of 6: Building the stator"), its end ("Generated …", "Not generated: …"), the short messages, the number of matches of Find A Setting, the note that the board is old and the length of a measured line are told to a screen reader without moving the focus. |

## 5. What is left

| What | Criterion | What it would take |
|---|---|---|
| Inner-2, the fill of a via and the rotor of Overlay are under 3:1 against the background of the drawing | 1.4.11 | Darker colours for the drawing only. They are the project's layer colours, so this is the owner's choice. |
| The board can be moved and zoomed with the mouse only by dragging and the wheel | 2.5.7 | Small buttons on the drawing for zoom in, zoom out and the four directions. |
| A short message cannot be kept longer by a keyboard user | 2.2.1 | A list of the last messages, or a message that stays until closed. |
| No pass with a real screen reader, none on a real Safari | | A person and a Mac. |

## 6. How to check again

```
cd WebGUI
npx playwright test a11y keyboard tips layout          # axe, the keyboard, the help boxes, the layout audit
SWEEP=1 npx playwright test tips-sweep --project=chromium
LAYOUT=all npx playwright test layout --project=chromium
```

# Bug rounds before version 2.0

The rounds the remade web tool went through before it replaced the old page. One subject a round. A round was run
by a script where a script could do it. Every fault got a number, a test that fails on it, the fix, and the whole
suite again. A round that found something was run again until it found nothing.

Rounds 27 and 28 (the owner's own trial, and the look at the live site after the first deploy) come after this
file was written.

## The rounds

| # | Round | What was gone through | Found |
|---|---|---|---|
| 1 | Single against the desktop | The starting design and one board for each of the six TX layout cards: every file of the run byte for byte equal to a desktop run. Two cards are refused by the generator, with the same words as on the desktop | Nothing |
| 2 | Dual against the desktop | The starting design and all 32 combinations of the two sets' layouts: 26 build and are equal, 6 are refused with the generator's message | Nothing |
| 3 | Reference boards | All 104 Single and 105 Dual reference boards of `regression/` made in the browser from their parameter files and compared with the reference files (`BOARDS=all`) | F24 |
| 4 | Every Single setting | 907 values: lowest, highest, just outside, None, each choice, text where a number belongs. The page says what the generator says | F1 |
| 5 | Every Dual setting | The same for Dual, one setting at a time, with the values a set takes from the board | F2, and five matters of the generator (below) |
| 6 | Settings the design does not use | Every combination of the switches: greyed out exactly where the generator ignores the value; the boards are the same with any value in a greyed setting | Nothing |
| 7 | The generator menu | Switched while Python loads, during a run, with a result, with a dialog or a help box open | F10, F11, F12 |
| 8 | Share links | There and back for both generators, links of the old page (`#d=`), broken, too long and hostile links | F3, F19 |
| 9 | Import and export | `.txt`, `.py` and `.zip` of both generators, files of the other generator, damaged and very large files, values no setting can hold | F14, F15, F16, F17 |
| 10 | What is typed | Letters, pasted text, exponents, decimal commas, minus signs, very long text, empty boxes, text beyond the basic plane | F4, F13, F18 |
| 11 | Run states | Generate twice, Cancel at each step, a change or Reset during a run, a crash of the generator and what follows | F36 |
| 12 | Loading | CDN refused, never answering, sending a changed file; no source at all; offline after loading; a reload in the middle of a run | Nothing new (tests added) |
| 13 | Layout | 13 computer window sizes in both views of both generators, measured: common lines, nothing cut off, nothing overlapping | F5, F6, F7, F34, and the four the owner reported before it |
| 14 | Zoom and reflow | 200 % and 400 %, nine small and low windows | F8, F9 |
| 15 | Keyboard only | The whole work with keys in both views: order, no traps, where the focus goes after a run, a menu, a dialog | F20, F21, F22, F23, F35 |
| 16 | Screen reader and axe | Names and roles of every control in every state, live messages, axe in every state; target sizes, focus ring, text spacing | F25, F26, F27, F28 |
| 17 | Help boxes, Single | Every help box opened at five window sizes: inside the window, not over its control, filled in, its picture loaded | F33 |
| 18 | Help boxes, Dual | The same for Dual: each box names its own coil set; the plain texts when `tips.json` is missing | Nothing |
| 19 | The preview | Zoom about the mouse, moving, Fit, every layer, coil and set button, the silkscreen, the rotor angle, Measure with its 256 lines, Pictures, full screen, very small and very large boards | F30, F32 |
| 20 | Downloads | The zip against the folder of a desktop run; one board alone; every file of All Files | Nothing |
| 21 | Extremes | The longest names, the most loops, the smallest and the largest board, two and four layers | Nothing: the generator's checker answers each |
| 22 | Browsers | The whole suite on Chromium, Firefox and WebKit, in CI | F37, F38, F39; the rest is under "Round 22" below |
| 23 | The blog page | The tool in the frame of `BloggerPage.html` on another site: its size, Share, a link through the blog, the security policy inside the frame, a phone | F29, F31 |
| 24 | Security | The ASVS list point by point (`ASVS-L1.md`), no violation of the policy in any test, the link lock, hostile names and contents | Nothing new |
| 25 | Performance | First view, cold and warm load, run times, memory after 20 runs | Nothing; the numbers are under "Round 25" below |
| 26 | Earlier bugs | What versions V1 to V18 of the old page fixed, tried on the new one | Nothing |
| 27 | The owner's trial of the live page | The help boxes and the Pictures view, as the owner used them after the release | F40, F41; Pictures put away for now |

## The faults, each with its test

| No. | Round | What was wrong | What it is now | Test |
|---|---|---|---|---|
| F1 | 4 | A setting the design does not use showed an error for its value, though the generator never reads it | The check leaves out what the generator leaves out | `test_bridge.py` `test_a_value_the_generator_does_not_use_is_not_checked` |
| F2 | 5 | Dual: a wrong band radius or board edge got a bare message, not the words the generator's layout check gives | The layout's own words, under the setting | `test_bridge.py` `test_dual_band_and_edge_values_get_the_layouts_words` |
| F3 | 8 | A design link pasted into the address bar of the open page did nothing | The page opens it, as on a first visit | `share.spec.js` "a link pasted into the address bar of the open page opens its design" |
| F4 | 10 | "1,5" was read as 1 and "12abc" as 12 | A decimal comma is a decimal point; what is not a number changes nothing and is named | `settings.spec.js` "a number box: a decimal comma is a decimal point …" |
| F5 | 13 | Check Only was 35 px high beside Generate's 39 px | One height | `layout.spec.js` |
| F6 | 13 | In a narrow Checks panel the title line ran into the download buttons | The counts go to a second line by the panel's own width | `layout.spec.js` |
| F7 | 13 | At some sizes the buttons on the drawing lay over the board | Fit gives the board the largest free circle | `layout.spec.js` |
| F8 | 14 | Below 1000 px the three panels were squeezed side by side | One column | `layout.spec.js`, `tips.spec.js` at 640 × 512 and 320 × 256 |
| F9 | 14 | A low window squeezed the list of settings to a few lines | The page keeps a least height and scrolls | `layout.spec.js` |
| F10 | 7 | While the other generator's settings were being read, the menu and Generate could still be used | Locked for that moment | `states.spec.js` "a switch of generator: nothing else starts meanwhile …" |
| F11 | 7 | Share, pressed before the settings were read, copied a link without the design | Share waits for them | `states.spec.js` "while Python loads …" |
| F12 | 7 | Ctrl + Enter started a run behind an open dialog | It does not | `states.spec.js` "Ctrl + Enter behind an open dialog starts no run" |
| F13 | 10 | A net name with an emoji stopped the run | Written into the parameter file as Python writes it | `test_bridge.py` `test_a_text_beyond_the_basic_plane_reaches_the_board_as_it_was_typed` |
| F14 | 9 | A file with `1e999`, a set, bytes, a dict or a nested list broke the import or left wrong values | Named as "not a value a setting can hold" and left out | `test_bridge.py`, `share.spec.js` "a value no setting can hold is named and left out …" |
| F15 | 9 | A file with one very long line took minutes to read | A line over 4000 characters is not a setting | `test_bridge.py` `test_a_file_saved_by_notepad_and_a_line_too_long_to_be_a_setting` |
| F16 | 9 | A file saved by Notepad (with a byte order mark) lost its first setting when it came in a zip | Read whole | the same test |
| F17 | 9 | A value of the wrong kind (text where a list belongs) broke the page | Shown as it is, named by the generator's check | `share.spec.js` "files whose values are of the wrong kind …" |
| F18 | 10 | A box showed 1.23456 as 1.235 while the generator got 1.23456 | The box shows the number whole | `settings.spec.js` "a box shows its number whole …" |
| F19 | 8 | A link could name things every object has (`constructor`, `__proto__`) and have them taken as settings | Only the generator's own names | `share.spec.js` "a link with names every object has …" |
| F20 | 15 | After Generate, Check Only or Cancel by key the focus was lost to the page | It stays on the button | `keyboard.spec.js` "a run started with a key hands the focus back …" |
| F21 | 15 | After a choice in the generator menu the focus was lost | Back on the menu's button | `keyboard.spec.js` "the generator menu, a setting's menu and the dialogs …" |
| F22 | 15 | After a choice in a setting's menu the focus was lost | Back on that menu's button | the same test |
| F23 | 15 | Sure / No asked twice within a moment (No, then Reset again at once): the first asking's late end answered the second, whose real answer was lost | Each asking takes its own answer | `keyboard.spec.js` (it failed once in nine runs before, never in forty after) |
| F24 | 3 | The three settings that place the board on the KiCad page were fixed and not shown: two reference boards could not be made, and an import dropped the values without a word | They are settings like the others | `settings.spec.js` "the board's place on the KiCad page …", `boards.spec.js` |
| F25 | 16 | Measure worked with the mouse only | With Measure on the arrow keys move a cross, Enter sets a point, the length is spoken | `keyboard.spec.js` "Measure with the keys …" |
| F26 | 16 | Sliders were 22 px high: under the 24 px a target needs, and the rotor angle lies on the drawing | 24 px | probe of round 16 |
| F27 | 16 | With letter spacing widened by the reader the counts line of Checks was cut off | It goes on to a second line | probe of round 16 |
| F28 | 16 | A long message at the bottom of the page was gone as fast as a short one | It stays by its length, and while the mouse rests on it | |
| F29 | 23 | A design link pasted into the address bar of the blog page, while it was open, did not reach the tool | The blog page hands it on | `embed.spec.js` |
| F30 | 19 | A layer or coil button that was clicked kept its layer brought out after the mouse had left: the click had left the focus on the button | Only a focus reached with the keys brings a layer out | `preview.spec.js` "layers, vias and coils …" |
| F31 | 23 | Inside the blog's frame the browser refused the `autofocus` of the No button of Sure / No and wrote an error in its console on every visit | The page gives No the focus itself when the question opens | `embed.spec.js` (nothing in the console), `keyboard.spec.js` (the question starts on No) |
| F32 | 19 | A `Parameters.txt` that holds its value lists but not the copies of the parameter files (the reference boards of `regression/` are kept that way) gave "No parameter values found" | The value lists are read | `test_bridge.py` `test_a_record_without_its_copies_comes_back_from_its_value_lists` |
| F33 | 17 | A help box taller than its room (at 200 % zoom, the boxes with a picture) scrolls inside: with the mouse wheel only | Alt + ↓ and Alt + ↑ scroll it, and a box opened with the keyboard says so | `tips.spec.js` "a box taller than its room, opened with the keyboard …" |
| F34 | 13 | A folded group of Advanced (Automatic Rotor, Custom Rotor) that opens showed all its settings at once, over the group under it, for the third of a second its card takes to grow | The settings are cut to the card until it has grown | `layout.spec.js` "a group that opens does not lie over the block under it while it grows" |
| F35 | 15 | A menu opened with the mouse (the generator menu, a setting's menu) did not close with Esc, and stayed open when Tab took the focus on | Esc closes an open menu wherever the focus is; a menu closes when the focus leaves it | `keyboard.spec.js` "a menu opened with the mouse closes with Esc, and when the focus goes on" |
| F36 | 11 | Cancel ends Python in the middle of a call. About once in a hundred cancels the ending Python still threw an error (`NoGilError`), and the page showed it as an error of its own, "Something Went Wrong", though the cancel had worked | What an ended Python still throws is taken and dropped | `states.spec.js` "an error the cancelled Python still throws while it ends is not an error of the page" |
| F37 | 22 | Where the drawing starts between two pixels of the window (WebKit laid it out so), the readout of the pointer, the point the wheel zooms about and Measure were up to half a pixel off: the browser gives the pointer's place inside the drawing in whole pixels | The place is taken from the pointer's place in the window less the drawing's own edge | `preview.spec.js` "the wheel zooms about the place the mouse points at …", with the drawing moved by 0.4 px |
| F38 | 22 | Where a scrollbar takes room (Windows, Linux, WebKit), a settings list that scrolls ended 12 px before the row with Basic and Advanced above it and the results and buttons under it. No test and no picture had shown it: Playwright hides Chromium's scrollbars | The page measures the list's scrollbar (in the frame after a change); the settings column is that much wider, and the rows above and under the list end where the settings end | `layout.spec.js`, every test of it: `playwright.config.js` now keeps Chromium's scrollbars |
| F39 | 22 | In a window 320 px wide, with the window's and the list's scrollbars taking their room, the page was 4 px wider than the window and scrolled sideways (Dual), and a setting's None switch stood past the edge (Single) | Under 1000 px the slider of a number shrinks further, a None switch goes under the setting's name, and the results stand closer | `layout.spec.js` "… in a 640, a 360 and a 320 px window: one column, nothing scrolls sideways, nothing is broken or cut" |
| F40 | 27 | The grey line beside a help box's note touched the note's text: the box's own rule that clears the room of its paragraphs outweighed the note's 8 px | That rule no longer outweighs any rule of a part of the box (`:where`) | `tips.spec.js` "a setting's tip shows its name …": the note keeps 8 px from its line |
| F41 | 27 | Pictures: the two pictures of a run stood at different heights with their captions on different lines (the Representative picture is taller), and in a portrait window they stood side by side, small | The two pictures share one row and stand in its middle, the captions share one line; in a portrait window they stand one above the other | `preview.spec.js` "Overlay turns the rotor; Pictures shows …" |

The four faults the owner reported while round 13 was being prepared (the search box out of line, the two button
rows of the Dual preview broken, the results of the two sets not in columns, the silkscreen buttons) were fixed the
same way and are held by `layout.spec.js`.

## Round 22: the three browsers

Only Chromium is on the computer the page was written on; Firefox and WebKit run in CI ("Web Tool Tests"). The
first run of the whole suite there failed in 1 test on Chromium, 6 on Firefox and 9 on WebKit; the second, after
the fixes, in 2 on Firefox and 6 on WebKit; the third in 2 on Firefox; the fourth in 1 on WebKit. What they were:

| What the run showed | Where | What it was |
|---|---|---|
| The readout half a pixel off | WebKit, and Chromium on the CI machine | F37 |
| The right edges of the settings panel 12 px apart | WebKit | F38 |
| A group still cut to its card 450 ms after it opened | WebKit | The cut of F34 was ended by a clock; it now ends when the card has grown |
| No word from a Python that was ended | WebKit | WebKit hands an ended worker's error to nobody, so F36 cannot happen there; the test takes both |
| Shift + Tab from the page itself went to the text box used last | Firefox | The browser's way; the test starts at the last stop and goes back from there |
| "Skipping unsupported feature name clipboard-write", "downloadable font: glyf: Glyph bbox was incorrect" | Firefox | Notes of the browser, on the frame of the blog page and on a font; the tests let them through by name |
| The page crashed while the accessibility check read it with the help box of Generate or of Share open | Firefox on the CI machine only, every time | Tried rule by rule: only axe's rules `hidden-content` and `label` end the page, and only with one of those two boxes open. Firefox leaves the two rules out of that test; the page without a box is read with every rule |
| "ResizeObserver loop completed with undelivered notifications" | WebKit, Dual | The measuring of F38 widened the column inside the observer, which then saw it again; it now measures in the next frame. The page had already passed this notice over |
| The help box the keyboard opened on the Top chip lay over the silkscreen chips the test clicked next | WebKit | The test puts the box away with Esc, as a visitor would |
| A measure of a small window taken while WebKit was still laying out the new size | WebKit, once | The small-window test measures again for up to 4 s while something is wrong |
| An opened group, and the column after a scrollbar came, measured while WebKit was still moving them | WebKit | The layout tests wait for the page's transitions to end. The column no longer slides when a scrollbar comes, and an opening group is cut until its growing has ended, however long that takes |
| The "Cancelled" message was gone before a slow browser had its new Python | Firefox, once | The test reads the message at once |

The fifth run passed in all three browsers, with no test that passed only on its second try.

Since this round Chromium keeps its scrollbars in every test (`playwright.config.js`), and a click or a hover that
cannot be done is named after 30 seconds.

## Round 25: the numbers

Measured in Chromium on a computer with four cores, the site and Python served from the same machine (so a first
and a second visit differ only by the browser's cache; on the live site a first visit also downloads Python, 16 MB
of files before the server packs them).

| What | Single | Dual |
|---|---|---|
| Largest paint of the first view | 164 ms (second visit 116 ms) | 152 ms |
| Layout shift until the first board stands | 0.009 | 0.011 |
| From the address to the first board | 6.5 s | 25 s |
| One run, 20 in a row | 2.6 to 3.1 s | 19.5 to 22.5 s |
| Memory of the whole browser, before and after the 20 runs | 1033 and 1028 MB | 1044 and 1037 MB |
| The page's own memory, before and after | 9 and 9 MB | 10 and 13 MB |

The suite holds the first two on every run (`perf.spec.js`: largest paint at most 2.5 s, layout shift at most 0.1).
Dual's time is the generator's: its silkscreen suggestion step takes most of a run. The 20 runs ended with no
error and the memory did not grow.

## Matters of the generator

Found in round 5. The page survives each of them and says what happened; the fix belongs in the generator. They
are listed for `main`.

1. Dual checks its layout before the values of the sets: `LOOPS = -1` in set 2 ends in an `IndexError`, not in a
   message.
2. `RX_LAYER_A`, `RX_LAYER_B`, `TX_LAYER_A` or `TX_LAYER_B` given None or a text end in a `KeyError`; given a list,
   in a `TypeError`.
3. A very large `TX_TURNS`, `TX_PITCH_MM`, `TX_OFFSET_MM` or `TX_TAIL_EXTRA_MM`, and a very large `LOOPS` or
   `STEPS_PER_LOOP` of set 2, run for up to 45 seconds and end in a `MemoryError`.

## Known and left

| What | Why it is left |
|---|---|
| The help box of a control inside an open dialog shows behind the dialog | A dialog lies over everything by the browser's rule; the controls in dialogs are few and say what they do |
| A setting at None in Dual's Basic view shows the number 1 in its greyed box | The number is not used; Advanced shows the same |
| The box that shows a run grows as its steps arrive | It lies on the drawing, which shows nothing new during a run |
| During a second run the counts line still shows the result before | It changes when the run ends; the board is marked as old meanwhile |
| A link longer than 20000 characters is ignored without a word | A link the page made is never that long |
| A help box can cover the control below the one it belongs to | It closes when the mouse or the focus leaves |
| On a board several hundred millimetres wide the copper is thinner than a pixel at Fit, and faint | Traces are drawn at their true width at every zoom; the wheel shows them |
| Where scrollbars take room, a help box with a picture that is as tall as its room to a few pixels shows a scrollbar with nothing to scroll | The scrollbar makes the picture narrower and so shorter; the browser keeps the scrollbar it has laid out |
| The points of `WCAG-EM.md`, section 5 | They are the owner's choices |

## Where the work left the plan

| Plan | What was done | Why |
|---|---|---|
| Lighthouse budgets in CI | The same two numbers (largest paint, layout shift) as a test of the suite, `perf.spec.js` | One tool fewer in CI, and the numbers are measured on the same built site as every other test |
| Screenshot comparisons ("visual") | The measured layout audit, `layout.spec.js` with `audit.mjs` | A picture differs between browsers and fonts; a measured line does not |
| The boards opened and rule-checked with KiCad in CI | Held by equality: the browser's boards are the reference boards (round 3), and `main` opens and rule-checks every reference board in KiCad 7 to 10 | The same check twice would only cost time |
| Round 22, a hand pass on Edge and a real Safari | The suite on Chromium, Firefox and WebKit | No Edge and no Mac here |

## How to run a round again

```
cd WebGUI
npx playwright test                                              # the suite: rounds 7 to 16, 19, 20, 23, 24, 26
python -m unittest tests/test_bridge.py                          # from the repository folder: rounds 4, 5, 9, 10
BOARDS=all npx playwright test boards --project=chromium         # round 3, both suites (about two hours)
BOARDS=all BOARDS_SUITE=dual BOARDS_FROM=56 npx playwright test boards --project=chromium   # one suite, from a board on
LAYOUT=all npx playwright test layout --project=chromium         # round 13, all 13 sizes
SWEEP=1 npx playwright test tips-sweep --project=chromium        # rounds 17 and 18 (about two hours)
```

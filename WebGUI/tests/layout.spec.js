/* layout: the blocks of the page stand on common lines, and nothing lies over anything else.  Measured in the browser,
   for Single and Dual, Basic and Advanced, every tab and coil set, at three window sizes: the left and right edges
   of the settings panel's blocks, the preview's rows of buttons, the rows of Advanced, and the general checks of
   audit.mjs.  Bug round 13 runs the same at thirteen sizes:

       LAYOUT=all npx playwright test layout --project=chromium            (inside WebGUI/) */
import { test, expect } from "./frame.js";
import { audit } from "./audit.mjs";

const SIZES = process.env.LAYOUT === "all"
  ? [[1024, 768], [1152, 864], [1280, 720], [1280, 800], [1280, 1024], [1366, 768], [1440, 900], [1536, 864], [1600, 900], [1680, 1050], [1920, 1080], [2560, 1440], [1080, 1920]]
  : [[1440, 900], [1280, 720], [1024, 768]];
const NEAR = 0.75;                                         // px two edges may differ by and still be one line

/* left, right, top, bottom of the first shown element of a selector; null when none is shown */
const boxes = (page, list) => page.evaluate((list) => {
  const out = {};
  for (const [name, sel] of Object.entries(list)) {
    const e = [...document.querySelectorAll(sel)].find((x) => x.offsetParent && x.getBoundingClientRect().width);
    if (!e) { out[name] = null; continue; }
    const b = e.getBoundingClientRect();
    out[name] = { l: b.left, r: b.right, t: b.top, b: b.bottom };
  }
  return out;
}, list);
/* the names of the boxes that do not stand on the line of the first one */
function off(got, side, names) {
  const have = names.filter((n) => got[n]), line = got[have[0]][side];
  return have.filter((n) => Math.abs(got[n][side] - line) > NEAR).map((n) => `${n} ${side} ${got[n][side].toFixed(1)}, ${have[0]} ${line.toFixed(1)}`);
}

const PANEL = { title: "#controls-title", mode: "#mode-switch", find: "#find", tabs: "#basic-tabs, #adv-tabs", set: "#basic-set, #adv-set",
  card: "#advanced-controls .group-card", field: "#basic-controls .field", results: "#results", strict: ".generate-row .switch-row", check: "#btn-check",
  reset: "#btn-reset", generate: "#btn-generate" };
const PREVIEW = { tabs: "#view-tabs", copper: "#layer-toggles", silk: "#silk-toggles", canvas: "#canvas-wrap", icons: "#canvas-tools .tool-pair",
  tools: "#canvas-tools", measure: "#btn-measure", nets: "#net-toggles", angle: "#rotor-angle-box", checks: "#checks h2", zip: "#btn-download", files: "#btn-files" };

/* Until every transition of the page has ended: a slow browser may still be growing a group or moving a column. */
const moved = (page) => page.evaluate(() => Promise.all(document.getAnimations().filter((a) => a instanceof CSSTransition).map((a) => a.finished.catch(() => {}))));

for (const [w, h] of SIZES) {
  for (const gen of ["single", "dual"]) {
    test(`${gen} at ${w} x ${h}: the blocks of the settings panel and of the preview stand on common lines`, async ({ app, page }) => {
      await page.setViewportSize({ width: w, height: h });
      await app.open(gen === "dual" ? "#dual=" : "");
      const wrong = [];
      for (const mode of ["basic", "advanced"]) {
        if (mode === "advanced") await app.mode("advanced");
        await page.waitForTimeout(700);                      // the panel has its new width
        await moved(page);
        const p = await boxes(page, PANEL), v = await boxes(page, PREVIEW);
        const say = (list) => wrong.push(...list.map((x) => `${mode}: ${x}`));
        say(off(p, "l", ["title", "find", "tabs", "set", "card", "field", "results", "strict", "check"]));
        say(off(p, "r", ["mode", "find", "tabs", "set", "card", "field", "results", "reset", "generate"]));
        say(off(p, "l", ["reset", "generate"]));
        say(off(v, "l", ["tabs", "tools", "measure"]));      // the view tabs stand over the Fullscreen button and the ruler
        say(off(v, "r", ["copper", "silk", "nets", "angle"]));
        say(off(v, "l", ["canvas", "checks"]));
        if (v.files.r > v.zip.r) v.zip = v.files;             // a narrow Checks panel: the four download buttons in one line, All Files last
        say(off(v, "r", ["canvas", "zip"]));
        // the layer chips: the copper layers and the vias on the line of the view tabs; the two silkscreen sides under
        // them, on the line of the Fullscreen button; the Sin / Cos / TX buttons under those
        const rows = await page.evaluate(() => ["#layer-toggles", "#silk-toggles"].map((s) => [...document.querySelector(s).children].map((c) => Math.round(c.getBoundingClientRect().top))));
        expect(rows.map((r) => r.length), "copper layers and vias, then the two silkscreen sides").toEqual([5, 2]);
        for (const r of rows) if (new Set(r).size !== 1) wrong.push(`${mode}: a line of layer chips is broken`);
        const mid = (b) => (b.t + b.b) / 2;
        if (Math.abs(mid(v.silk) - mid(v.icons)) > NEAR) wrong.push(`${mode}: the silkscreen chips are not on the line of the Fullscreen button`);
        if (v.copper.r - v.copper.l < v.tabs.r - v.tabs.l || Math.abs(mid(v.copper) - mid(v.tabs)) > NEAR) { if (w >= 1440) wrong.push(`${mode}: the copper chips are not on the line of the view tabs`); }
        if (v.silk.t < v.copper.b || v.nets.t < v.silk.b) wrong.push(`${mode}: copper chips, silkscreen chips and coil buttons are not one under the other`);
        if (v.tools.t - Math.max(v.tabs.b, v.copper.b) > 24) wrong.push(`${mode}: a gap between the view tabs (or the chips under them) and the Fullscreen button`);
        // nothing of the panel sticks out of it, and the title row does not lie over the list
        const out = await page.evaluate(() => {
          const c = document.getElementById("controls").getBoundingClientRect();
          return [...document.querySelectorAll("#controls *")].filter((e) => e.offsetParent && e.getBoundingClientRect().width && (e.getBoundingClientRect().right > c.right + 0.5 || e.getBoundingClientRect().left < c.left - 0.5)).length;
        });
        if (out) wrong.push(`${mode}: ${out} element(s) stick out of the settings panel`);
        if (p.mode.b > (p.find || p.tabs).t) wrong.push(`${mode}: the title row lies over the list`);
        // the general checks, on every tab and coil set, with the folded groups open, the list at its start and at its end
        const view = mode === "basic" ? "basic" : "adv";
        for (const k of await page.locator(`#${view}-tabs [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key))) {
          await page.click(`#${view}-tabs [data-key="${k}"]`);
          const sets = await page.locator(`#${view}-set:not([hidden]) [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key));
          for (const s of sets.length ? sets : [null]) {
            if (s) await page.click(`#${view}-set [data-key="${s}"]`);
            for (const fold of await page.locator(".group-title.foldable.collapsed:visible").all()) await fold.click();
            await page.waitForTimeout(450);                  // an opened group has its full height
            await moved(page);
            await expect(page.locator(".group-card.opening")).toHaveCount(0);
            for (const end of [0, 1]) {
              await page.evaluate((end) => { const l = document.querySelector("#controls :is(#basic-panel, #advanced-panel):not([hidden])"); l.scrollTop = end * l.scrollHeight; }, end);
              say((await page.evaluate(audit)).map((x) => `${k}${s ? " set " + s : ""}: ${x}`));
            }
          }
        }
        for (const v of ["stator", "rotor", "overlay"]) {      // Pictures is put away for now
          await page.click(`#preview [data-view="${v}"]`);
          await page.waitForTimeout(150);
          say((await page.evaluate(audit)).map((x) => `view ${v}: ${x}`));
        }
      }
      if (wrong.length) wrong.push(await page.evaluate(() => {   // to read a failure by: the scrollbar the page measured, and the list's own
        const l = document.querySelector("#controls :is(#basic-panel, #advanced-panel):not([hidden])");
        return `(--bar ${getComputedStyle(document.documentElement).getPropertyValue("--bar")}, the list's scrollbar ${l.offsetWidth - l.clientWidth} px)`;
      }));
      expect([...new Set(wrong)]).toEqual([]);
    });
  }
}

test("Advanced: no setting's name is broken, its file name and its arrow stay together, the title row stays while the list scrolls", async ({ app, page }) => {
  await app.open("#dual=");
  await app.mode("advanced");
  const wrong = [];
  const keys = await page.locator("#adv-tabs [data-key]").evaluateAll((l) => l.map((b) => b.dataset.key));
  for (const k of keys) {
    await page.click(`#adv-tabs [data-key="${k}"]`);
    for (const fold of await page.locator(".group-title.foldable.collapsed:visible").all()) await fold.click();
    wrong.push(...await page.evaluate((k) => [...document.querySelectorAll("#advanced-panel .field-head")].filter((h) => h.offsetParent).flatMap((h) => {
      const bad = [], label = h.querySelector(".field-label"), name = h.querySelector(".mono-name"), arrow = h.querySelector(".reset-one");
      if (label && label.getClientRects().length > 1 && label.getBoundingClientRect().height > 26) bad.push(`${k} ${h.dataset.help}: the name is broken`);
      if (name && arrow && Math.abs(name.getBoundingClientRect().bottom - arrow.getBoundingClientRect().bottom) > 8) bad.push(`${k} ${h.dataset.help}: the arrow is not beside the file name`);
      if (arrow && Math.abs(arrow.getBoundingClientRect().right - h.getBoundingClientRect().right) > 3) bad.push(`${k} ${h.dataset.help}: the arrow is not at the right end`);
      return bad;
    }), k));
  }
  expect(wrong).toEqual([]);
  // the list scrolled to its end: the title and Basic | Advanced are where they were, and the list is under them
  const before = await boxes(page, { title: "#controls-title", mode: "#mode-switch" });
  await page.locator("#advanced-panel").evaluate((p) => { p.scrollTop = p.scrollHeight; });
  const after = await boxes(page, { title: "#controls-title", mode: "#mode-switch", list: "#advanced-panel" });
  expect(after.title.t).toBe(before.title.t);
  expect(after.mode.t).toBe(before.mode.t);
  expect(after.list.t).toBeGreaterThanOrEqual(after.mode.b);
  await expect(page.locator("#mode-switch [data-mode=basic]")).toBeVisible();
});

test("Dual: the results are three columns at equal distances, from the panel's left edge to its right edge", async ({ app, page }) => {
  await app.open("#dual=");
  for (const mode of ["basic", "advanced"]) {
    if (mode === "advanced") { await app.mode("advanced"); await page.waitForTimeout(700); }
    const got = await page.evaluate(() => {
      const words = (e) => { const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); return { l: b.left, r: b.right, m: (b.left + b.right) / 2 }; };
      const box = document.getElementById("results").getBoundingClientRect();
      const names = [...document.querySelectorAll("#results tbody th")].map(words), heads = [...document.querySelectorAll("#results thead th")].map(words);
      const rows = [...document.querySelectorAll("#results tbody tr")].map((r) => [...r.querySelectorAll("td:not(.room)")].map(words));
      return { box: { l: box.left, r: box.right }, names, heads, rows, strict: document.querySelector(".generate-row .switch-row").getBoundingClientRect().left,
        generate: document.getElementById("btn-generate").getBoundingClientRect().right };
    });
    const near = (a, b, what) => expect(Math.abs(a - b), `${mode}: ${what} (${a.toFixed(1)}, ${b.toFixed(1)})`).toBeLessThanOrEqual(1);
    const nameRight = Math.max(...got.names.map((n) => n.r));
    for (const n of got.names) near(n.l, got.strict, "a row's name starts on the panel's left line");
    near(got.heads[1].r, got.generate, "Set 2 ends on the panel's right line");
    near(got.heads[0].l - nameRight, got.heads[1].l - got.heads[0].r, "the room before Set 1 is the room before Set 2");
    const sets = got.rows.filter((r) => r.length === 2), board = got.rows.filter((r) => r.length === 1);
    expect(sets.length).toBeGreaterThanOrEqual(1);
    for (const row of sets) for (const i of [0, 1]) near(row[i].m, got.heads[i].m, "a value is centred under its set's name");
    for (const row of board) near(row[0].m, (got.heads[0].l + got.heads[1].r) / 2, "the board's line is centred under the two sets");
  }
});

test("Single: the results are two pairs of name and value, from the panel's left edge to its right edge", async ({ app, page }) => {
  await app.open();
  for (const mode of ["basic", "advanced"]) {
    if (mode === "advanced") { await app.mode("advanced"); await page.waitForTimeout(700); }
    const got = await page.evaluate(() => {
      const words = (e) => { const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); return { l: b.left, r: b.right, t: Math.round(b.top) }; };
      return { names: [...document.querySelectorAll("#results dt")].map(words), values: [...document.querySelectorAll("#results dd")].map(words),
        strict: document.querySelector(".generate-row .switch-row").getBoundingClientRect().left, generate: document.getElementById("btn-generate").getBoundingClientRect().right };
    });
    expect(got.names.length).toBe(6);                          // Range, R, L, C, f, Board: three lines of two
    expect(new Set(got.names.map((n) => n.t)).size, `${mode}: three lines`).toBe(3);
    for (const i of [0, 2, 4]) expect(Math.abs(got.names[i].l - got.strict), `${mode}: the first name of a line starts on the left line`).toBeLessThanOrEqual(1);
    for (const i of [1, 3, 5]) expect(Math.abs(got.names[i].l - got.names[1].l), `${mode}: the second names stand under each other`).toBeLessThanOrEqual(1);
    expect(Math.abs(Math.max(...got.values.map((v) => v.r)) - got.generate), `${mode}: the widest value ends on the right line`).toBeLessThanOrEqual(1);
    for (let i = 0; i < 6; i++) expect(got.values[i].t, `${mode}: a value on the line of its name`).toBe(got.names[i].t);
  }
});

test("a group that opens does not lie over the block under it while it grows", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await page.click('#adv-tabs [data-key="Rotor"]');
  const fold = page.locator(".group-title.foldable.collapsed:visible").first();
  await fold.scrollIntoViewIfNeeded();
  await fold.click();
  const wrong = [];
  for (let i = 0; i < 6; i++) {                              // six looks during the third of a second the card takes to open
    wrong.push(...await page.evaluate(audit));
    await page.waitForTimeout(40);
  }
  expect([...new Set(wrong)]).toEqual([]);
  await expect(page.locator(".group-card.opening"), "the cut ends with the opening").toHaveCount(0);
  await page.waitForTimeout(100);
  expect(await page.evaluate(audit)).toEqual([]);
});

/* The smallest windows, with the scrollbars a visitor's browser shows: the window's own takes 15 px of the width and
   the list's 12 px more (a 1280 px screen at 400 % zoom is 320 px wide). */
for (const gen of ["single", "dual"]) {
  test(`${gen} in a 640, a 360 and a 320 px window: one column, nothing scrolls sideways, nothing is broken or cut`, async ({ app, page }) => {
    await app.open(gen === "dual" ? "#dual=" : "");
    const wrong = [];
    for (const mode of ["basic", "advanced"]) {
      await app.mode(mode);
      for (const [w, h] of [[640, 512], [360, 640], [320, 256]]) {
        await page.setViewportSize({ width: w, height: h });
        // measured again for up to 4 s while something is wrong: a slow browser may still be laying out the new size
        let found = [];
        for (let i = 0; i < 9 && (i === 0 || found.length); i++) {
          await page.waitForTimeout(i === 0 ? 700 : 400);
          const sideways = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
          found = [...(sideways > 0 ? [`the page is ${sideways} px wider than the window`] : []), ...(await page.evaluate(audit))];
        }
        wrong.push(...found.map((x) => `${mode} at ${w} x ${h}: ${x}`));
      }
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.waitForTimeout(400);
    }
    expect(wrong).toEqual([]);
  });
}

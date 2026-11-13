/* settings: the page lists what the parameter files hold, and a setting behaves the same in Basic and in Advanced. */
import fs from "node:fs";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";

/* The names a parameter file assigns at the start of a line, read from the file itself. */
function namesIn(file) {
  const out = [];
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = /^([A-Z][A-Z0-9_]*)\s*=/.exec(line);
    if (m && !out.includes(m[1])) out.push(m[1]);
  }
  return out;
}
/* Not listed on the page: the Output block (fixed on the web) and Strict (the switch beside Generate). */
const FIXED = ["OUTPUT_DIR", "STATOR_FILE", "ROTOR_FILE", "CENTER_X_MM", "CENTER_Y_MM", "PAGE_SIZE_MM", "GENERATOR_MODE"];
const FOLDER = { single: "Single Coil Set Generator", dual: "Dual Coil Set Generator" };
const AGGREGATE = { single: "Parameters.py", dual: "Dual_Parameters.py" };

/* {file: [names]} of every setting Advanced shows, tab by tab and set by set. */
async function shown(page) {
  const out = {};
  const keys = await page.locator("#adv-tabs [data-key]").evaluateAll((l) => l.map((b) => b.dataset.key));
  for (const k of keys) {
    await page.click(`#adv-tabs [data-key="${k}"]`);
    const sets = await page.locator("#adv-set:not([hidden]) [data-key]").evaluateAll((l) => l.map((b) => b.dataset.key));
    for (const s of sets.length ? sets : [null]) {
      if (s) await page.click(`#adv-set [data-key="${s}"]`);
      const fields = await page.locator("#advanced-controls .field[data-name]").evaluateAll((l) => l.map((f) => [f.dataset.file, f.dataset.name,
        !!f.querySelector(".info-dot"), (f.querySelector(".mono-name") || {}).textContent]));
      for (const [file, name, dot, mono] of fields) {
        expect(dot, `${name} has its help dot`).toBe(true);
        expect(mono, `${name} shows its name in the file`).toBe(name);
        (out[file] = out[file] || []).push(name);
      }
    }
  }
  return out;
}

for (const gen of ["single", "dual"]) {
  test(`${gen}: Advanced lists every setting of every parameter file, in the files' order`, async ({ app, page }) => {
    await app.open(gen === "dual" ? "#dual=" : "");
    await app.mode("advanced");
    const got = await shown(page);
    const dir = path.join(REPO, "Generators", FOLDER[gen], "Parameters");
    const files = fs.readdirSync(dir).filter((n) => n.endsWith("_Parameters.py") && n !== AGGREGATE[gen]).sort();
    expect(Object.keys(got).sort()).toEqual(files);
    for (const f of files) {
      const inFile = namesIn(path.join(dir, f)).filter((n) => !FIXED.includes(n));
      // a set's file may also list a board setting it does not hold ("the board's value"); those are not compared
      expect(got[f].filter((n) => inFile.includes(n)), f).toEqual(inFile);
    }
  });
}

test("a value typed in Advanced shows in Basic, and back; the arrow puts one setting back", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await app.type("AIR_GAP_MM", 1.5);
  const field = app.field("AIR_GAP_MM");
  await expect(field.locator(".reset-one")).toBeVisible();
  await expect(page.locator('#adv-tabs [data-key="Board"] .tab-dot')).toHaveCount(1);
  await expect(page.locator("#btn-download")).toBeDisabled();                         // the board on show is of the old settings

  await app.mode("basic");
  const basic = app.field("AIR_GAP_MM");
  await expect(basic.locator("input[type=text]")).toHaveValue("1.5");
  await basic.locator(".stepper button").last().click();                             // + in Basic
  await app.settled();
  const now = await basic.locator("input[type=text]").inputValue();
  expect(Number(now)).toBeGreaterThan(1.5);

  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe(now);
  await app.field("AIR_GAP_MM").locator(".reset-one").click();
  await app.settled();
  expect(await app.value("AIR_GAP_MM")).toBe("1");
  await expect(page.locator("#adv-tabs .tab-dot")).toHaveCount(0);
});

test("a value the generator refuses is named under its setting, in the generator's words", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await app.tab("RX");
  await app.type("LOOPS", 0);
  const error = app.field("LOOPS").locator(".field-error");
  await expect(error).toBeVisible();
  await expect(error).toContainText("LOOPS");
  await app.generate();                                                               // the run says the same and makes no board
  await expect(app.findings("error")).not.toHaveCount(0);
  await expect(page.locator("#btn-download")).toBeDisabled();

  await app.type("LOOPS", "abc");                                                     // not a number: the box keeps the value it had
  expect(await app.value("LOOPS")).toBe("0");
  await app.type("LOOPS", 2);
  await expect(error).toBeHidden();
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  await expect(page.locator("#results")).toContainText("180°");
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("None: the switch of Board Inner Radius hands the value to the generator, in both views", async ({ app, page }) => {
  await app.open();
  const basic = app.field("INNER_EDGE_RADIUS_MM");
  const none = basic.locator(".none-switch input");
  await none.check({ force: true });
  await app.settled();
  await expect(basic.locator("input[type=text]")).toBeDisabled();
  await expect(basic.locator("input[type=text]")).toHaveValue("None");
  await app.mode("advanced");
  const adv = app.field("INNER_EDGE_RADIUS_MM");
  await expect(adv.locator("input[type=text]")).toBeDisabled();
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  await app.mode("basic");
  await none.uncheck({ force: true });
  await app.settled();
  await expect(basic.locator("input[type=text]")).toHaveValue("15");                  // back to the number it had
});

test("Find A Setting lists the matches of every file, and clearing it brings the tabs back", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await page.fill("#find", "chord_tol");                                              // a part of three Python names
  await expect(page.locator("#find-count")).toHaveText("3 settings");                 // of RX, TX and Rotor
  await expect(page.locator("#advanced-controls .field[data-name]")).toHaveCount(3);
  await expect(page.locator('#advanced-controls .field[data-name="RX_CHORD_TOLERANCE_MM"]')).toBeVisible();
  await page.fill("#find", "RX_TAB_LEN");                                             // a part of a Python name
  await expect(page.locator("#advanced-controls .field[data-name]")).toHaveCount(1);
  await page.fill("#find", "zzzz");
  await expect(page.locator("#advanced-controls")).toContainText("No setting matches");
  await page.fill("#find", "");
  await expect(page.locator('#advanced-controls .field[data-name="PCB_LAYERS"]')).toBeVisible();
});

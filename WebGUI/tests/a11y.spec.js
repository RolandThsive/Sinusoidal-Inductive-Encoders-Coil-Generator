/* a11y: axe-core finds no WCAG 2.2 A or AA failure on any view of the page (the checks a machine can make). */
import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "./frame.js";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];

/* Two findings of axe that are not failures of the page (docs/Accessibility.md says the same):
   label-title-only   axe takes a label that is scrolled out of the settings column for a hidden one, so the rule's
                      result follows the scroll position; every input is named by its visible label (rule "label").
   the Measure button its picture is a ruler with the digits 0 to 3; they are part of the picture, not a label. */
const OFF = ["label-title-only"];
const PICTURE = (v, n) => v.id === "label-content-name-mismatch" && n.target.join(" ") === "#btn-measure";

/* The failures axe finds now, as short lines: rule, impact, the elements. */
async function failures(page, where) {
  const r = await new AxeBuilder({ page }).withTags(TAGS).disableRules(OFF).analyze();
  return r.violations.map((v) => ({ v, nodes: v.nodes.filter((n) => !PICTURE(v, n)) })).filter((x) => x.nodes.length)
    .map(({ v, nodes }) => `${where}: ${v.id} (${v.impact}) ${v.help} -> ${nodes.slice(0, 4).map((n) => n.target.join(" ")).join(" | ")}`);
}
/* Every tab of the settings column that is shown, scanned in turn. */
async function everyTab(page, app, view, where) {
  const found = [];
  const keys = await page.locator(`#${view}-tabs [data-key]`).evaluateAll((list) => list.map((b) => b.dataset.key));
  for (const key of keys) {
    await page.click(`#${view}-tabs [data-key="${key}"]`);
    const sets = await page.locator(`#${view}-set:not([hidden]) [data-key]`).evaluateAll((list) => list.map((b) => b.dataset.key));
    for (const set of sets.length ? sets : [null]) {
      if (set) await page.click(`#${view}-set [data-key="${set}"]`);
      found.push(...await failures(page, `${where} ${key}${set ? " set " + set : ""}`));
    }
  }
  await app.settled();
  return found;
}

for (const gen of ["single", "dual"]) {
  test(`${gen}: Basic and Advanced, every tab`, async ({ app, page }) => {
    await app.open();
    if (gen === "dual") await app.generator("dual");
    const found = await everyTab(page, app, "basic", `${gen} Basic`);
    await app.mode("advanced");
    found.push(...await everyTab(page, app, "adv", `${gen} Advanced`));
    expect(found).toEqual([]);
  });
}

test("the open menu, the dialogs, the pictures and full screen", async ({ app, page }) => {
  await app.open();
  const found = [];
  await page.click("#gen-btn");
  found.push(...await failures(page, "generator menu"));
  await page.keyboard.press("Escape");
  await page.click("#btn-runtext");
  await expect(page.locator("#text-dialog")).toBeVisible();
  found.push(...await failures(page, "run text"));
  await page.keyboard.press("Escape");
  await page.click("#btn-files");
  found.push(...await failures(page, "all files"));
  await page.keyboard.press("Escape");
  await page.click('[data-view="pictures"]');
  found.push(...await failures(page, "pictures"));
  await page.click('[data-view="overlay"]');
  found.push(...await failures(page, "overlay"));
  await page.locator("#show-info").check({ force: true });
  found.push(...await failures(page, "with the info lines"));
  await page.click("#layer-toggles .layer-chip >> nth=0");            // a layer, a coil and the origin switched off
  await page.click("#net-toggles .net-btn >> nth=0");
  await page.click('[data-focus="origin"]');
  found.push(...await failures(page, "parts switched off"));
  expect(found).toEqual([]);
});

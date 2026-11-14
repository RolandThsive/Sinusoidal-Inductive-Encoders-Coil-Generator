/* tips: the help boxes (tooltips).  Their words are in tips.json; these tests hold the page to it. */
import fs from "node:fs";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { test, expect, REPO } from "./frame.js";

const TIPS = JSON.parse(fs.readFileSync(path.join(REPO, "WebGUI", "tips.json"), "utf8"));
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];

/* Close the box that is open, then rest the mouse on a control and wait for its box. */
async function closeTip(page) {
  await page.keyboard.press("Escape");
  await page.mouse.move(1, 1);
  await expect(page.locator("#popover")).toBeHidden();
}
async function openTip(page, target) {
  await closeTip(page);
  await target.scrollIntoViewIfNeeded();
  await page.waitForTimeout(150);                            // the scroll itself closes a box
  await target.hover({ timeout: 15000 });                    // a control that cannot be reached is named at once, not after the test's six minutes
  const pop = page.locator("#popover");
  await expect(pop).toBeVisible();
  return pop;
}
/* The box is inside the window, and no wider or taller than it. */
async function insideWindow(page, pop, where) {
  const b = await pop.boundingBox();
  const win = await page.evaluate(() => ({ w: document.documentElement.clientWidth, h: document.documentElement.clientHeight }));
  expect(b.x, `${where}: left edge`).toBeGreaterThanOrEqual(0);
  expect(b.y, `${where}: top edge`).toBeGreaterThanOrEqual(0);
  expect(b.x + b.width, `${where}: right edge`).toBeLessThanOrEqual(win.w + 0.5);
  expect(b.y + b.height, `${where}: bottom edge`).toBeLessThanOrEqual(win.h + 0.5);
}
/* Every tip the page asks for now: ["param:NAME" | tip id], with those that have only a plain text. */
const asked = (page) => page.evaluate(() => ({
  ids: [...document.querySelectorAll("[data-tip-id], [data-help]")].map((n) => (n.dataset.help ? "param:" + n.dataset.help : n.dataset.tipId)),
  bare: [...document.querySelectorAll("[data-tip]:not([data-tip-id]):not([data-help])")].map((n) => n.outerHTML.slice(0, 120)),
}));
/* Walk every tab and set of the settings column that is shown, collecting what asked() finds. */
async function everyTab(page, view, into) {
  const keys = await page.locator(`#${view}-tabs [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key));
  for (const k of keys) {
    await page.click(`#${view}-tabs [data-key="${k}"]`);
    const sets = await page.locator(`#${view}-set:not([hidden]) [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key));
    for (const s of sets.length ? sets : [null]) {
      if (s) await page.click(`#${view}-set [data-key="${s}"]`);
      const a = await asked(page);
      a.ids.forEach((id) => into.ids.add(id));
      a.bare.forEach((b) => into.bare.add(b));
    }
  }
}
const known = (id) => (id.startsWith("param:") ? id.slice(6) in TIPS.params : id.startsWith("preset:") ? id.slice(7) in TIPS.presets : id in TIPS.controls);

test("every control the page shows has its tip in tips.json, and tips.json holds no setting the page lacks", async ({ app, page }) => {
  const seen = { ids: new Set(), bare: new Set() };
  await app.open();
  for (const gen of ["single", "dual"]) {
    if (gen === "dual") await app.generator("dual");
    await app.mode("basic");
    await everyTab(page, "basic", seen);
    for (const v of ["stator", "rotor", "pictures", "overlay"]) {           // the views of the preview, with their chips
      await page.click(`#preview [data-view="${v}"]`);
      (await asked(page)).ids.forEach((id) => seen.ids.add(id));
    }
    await app.mode("advanced");
    await everyTab(page, "adv", seen);
    await page.fill("#find", "radius");                                       // the list of Find A Setting
    (await asked(page)).ids.forEach((id) => seen.ids.add(id));
    await page.fill("#find", "");
  }
  expect([...seen.bare], "controls with a plain text only").toEqual([]);
  expect([...seen.ids].filter((id) => !known(id)).sort(), "asked for, not in tips.json").toEqual([]);
  const params = [...seen.ids].filter((id) => id.startsWith("param:")).map((id) => id.slice(6));
  expect(Object.keys(TIPS.params).filter((n) => !params.includes(n)).sort(), "in tips.json, not on the page").toEqual([]);
  const cards = [...seen.ids].filter((id) => id.startsWith("preset:")).map((id) => id.slice(7));
  expect(Object.keys(TIPS.presets).filter((n) => !cards.includes(n)).sort(), "cards in tips.json, not on the page").toEqual([]);
});

test("a setting's tip shows its name, unit, the marked file value, the value in the file and the reference link", async ({ app, page }) => {
  await app.open();
  const dot = () => app.field("INNER_EDGE_RADIUS_MM").locator(".info-dot");
  let pop = await openTip(page, dot());
  await expect(pop).toHaveAttribute("role", "tooltip");
  await expect(pop.locator(".tip-eyebrow")).toHaveText(/^Board · /);
  await expect(pop.locator(".tip-title")).toHaveText(/^Board Inner Radius\s*mm$/);
  await expect(pop.locator(".tip-key")).toHaveText("INNER_EDGE_RADIUS_MM");
  await expect(pop.locator(".tip-lead")).toHaveText(TIPS.params.INNER_EDGE_RADIUS_MM.lead);
  await expect(pop.locator(".tip-chip")).toHaveText(["None", "A number"]);
  await expect(pop.locator(".tip-chip.file")).toHaveText("A number");
  await expect(pop.locator(".tip-chip.file")).toHaveAttribute("title", "The value in the file");
  await expect(pop.locator(".tip-foot")).toContainText("In the file: 15");
  await expect(pop.locator(".tip-foot a")).toHaveAttribute("href", /\/wiki\/Parameter-Reference-Single-Coil-Set-Generator$/);
  await expect(pop.locator(".tip-foot a")).toHaveCSS("text-decoration-line", "underline");

  // the value in the file is the published one, whatever the page holds now
  await app.mode("advanced");
  await app.type("INNER_EDGE_RADIUS_MM", 14);
  pop = await openTip(page, dot());
  await expect(pop.locator(".tip-foot")).toContainText("In the file: 15");

  // a setting with named choices: one chip per choice, the file's one marked
  await app.tab("RX");
  pop = await openTip(page, app.field("RX_TABS").locator(".info-dot"));
  await expect(pop.locator(".tip-choices li")).toHaveCount(3);
  await expect(pop.locator(".tip-chip.file")).toHaveCount(1);

  await app.generator("dual");
  await app.mode("advanced");
  pop = await openTip(page, page.locator("#advanced-controls .info-dot").first());
  await expect(pop.locator(".tip-foot a")).toHaveAttribute("href", /\/wiki\/Parameter-Reference-Dual-Coil-Set-Generator$/);
});

test("every picture a tip names is a file of the site, and it loads when its tip opens", async ({ app, page }) => {
  const named = Object.entries(TIPS.params).filter(([, t]) => t.picture);
  for (const [name, t] of named) {
    expect(fs.existsSync(path.join(REPO, "WebGUI", "docs", "tooltips", "pictures", t.picture.file)), `${name}: ${t.picture.file}`).toBe(true);
    expect(fs.existsSync(path.join(REPO, "WebGUI", "docs", "tooltips", "drawn", t.picture.file.replace(/\.webp$/, ".svg"))), `${name}: the drawing of ${t.picture.file}`).toBe(true);
    expect(t.picture.caption.length, `${name}: a caption`).toBeGreaterThan(8);
  }
  test.skip(!TIPS.params.LOOPS.picture, "no tip names a picture yet");
  await app.open();
  await app.tab("RX");
  expect(await page.locator("#popover img").count(), "no picture is fetched before a tip opens").toBe(0);
  const pop = await openTip(page, app.field("LOOPS").locator(".info-dot"));
  const img = pop.locator(".tip-picture img");
  await expect(img).toHaveAttribute("alt", TIPS.params.LOOPS.picture.caption);
  await expect(img).toHaveAttribute("width", String(TIPS.params.LOOPS.picture.width));
  await expect.poll(() => img.evaluate((i) => i.complete && i.naturalWidth)).toBe(2 * TIPS.params.LOOPS.picture.width);
  await expect(pop.locator(".tip-picture figcaption")).toHaveText(TIPS.params.LOOPS.picture.caption);
  await insideWindow(page, pop, "LOOPS with its picture");
});

test("every tip of the first page is filled in: no place left open, inside the window, in the new layout", async ({ app, page }) => {
  await app.open();
  const owners = page.locator("[data-tip-id]:visible:not(:disabled), .info-dot[data-help]:visible");
  // those the mouse can reach now (not the lines of a closed menu)
  const reach = await owners.evaluateAll((list) => list.map((n, i) => {
    const r = n.getBoundingClientRect(), at = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    return at && n.contains(at) ? i : -1;
  }).filter((i) => i >= 0));
  expect(reach.length).toBeGreaterThan(30);
  const wrong = [];
  for (const i of reach) {
    const node = owners.nth(i);
    const id = await node.evaluate((x) => x.dataset.help || x.dataset.tipId);
    const pop = await openTip(page, node);
    const text = await pop.innerText();
    if (/[{}]|undefined|NaN|\[object|null/.test(text)) wrong.push(`${id}: "${text.slice(0, 80)}"`);
    if (!text.trim()) wrong.push(`${id}: empty`);
    if (await pop.evaluate((p) => p.classList.contains("plain"))) wrong.push(`${id}: only its plain text`);
    if (await pop.evaluate((p) => p.scrollWidth > p.clientWidth + 1)) wrong.push(`${id}: something sticks out of the box`);
    await insideWindow(page, pop, id);
  }
  expect(wrong).toEqual([]);
});

test("a tip in a list names its own item: the TX layout cards, the layer chips, the tabs", async ({ app, page }) => {
  await app.open();
  await app.tab("TX");
  const cards = page.locator('#basic-controls [data-tip-id^="preset:"]');
  expect(await cards.count()).toBeGreaterThanOrEqual(3);
  for (let i = 0; i < await cards.count(); i++) {
    const name = (await cards.nth(i).innerText()).replace(/\s+/g, " ").trim();
    const pop = await openTip(page, cards.nth(i));
    await expect(pop.locator(".tip-title")).toHaveText(name);
    await expect(pop.locator(".tip-facts dt").first()).toBeVisible();
    await expect(pop.locator(".tip-small")).toHaveText(TIPS.presetFoot);
  }
  for (const chip of await page.locator('#preview [data-tip-id="layer"]:visible').all()) {
    const name = (await chip.innerText()).trim();
    const pop = await openTip(page, chip);
    await expect(pop.locator(".tip-lead")).toContainText(`the ${name} copper`);
  }
  await app.mode("advanced");
  const tabs = page.locator("#adv-tabs [data-key]");
  for (let i = 0; i < await tabs.count(); i++) {
    const args = JSON.parse(await tabs.nth(i).getAttribute("data-tip-args"));
    const pop = await openTip(page, tabs.nth(i));
    await expect(pop.locator(".tip-lead")).toHaveText(`${args.what} of ${args.file}.`);
  }
});

test("without tips.json every tip falls back to its plain text", async ({ app, page, problems }) => {
  problems.allow(/404/);
  await page.route("**/tips.json", (r) => r.fulfill({ status: 404, body: "not found" }));
  await app.open();
  let pop = await openTip(page, page.locator("#btn-share"));
  await expect(pop).toHaveClass(/plain/);
  await expect(pop).toHaveText("Copy a link that opens this page with your settings");
  pop = await openTip(page, app.field("INNER_EDGE_RADIUS_MM").locator(".info-dot"));
  await expect(pop.locator(".mono-name")).toHaveText("INNER_EDGE_RADIUS_MM");
  await expect(pop.locator(".tip-foot")).toContainText("In the file: 15");
  expect((await pop.innerText()).length).toBeGreaterThan(60);                 // the comment of the parameter file
  await app.tab("TX");
  const card = page.locator('#basic-controls [data-tip-id^="preset:"]').first();
  pop = await openTip(page, card);
  await expect(pop).toContainText((await card.innerText()).replace(/\s+/g, " ").trim());
  // every control still has a text
  const none = await page.evaluate(() => [...document.querySelectorAll("[data-tip-id]")].filter((n) => !n.dataset.tip && !n.id.startsWith("btn-")
    && !["gen-", "mode-", "view-", "nav-"].some((p) => n.dataset.tipId.startsWith(p)) && !["find", "strict", "readout", "rotor-angle", "show-info"].includes(n.dataset.tipId))
    .map((n) => n.dataset.tipId));
  expect(none).toEqual([]);
});

test("keyboard and mouse: focus opens the tip, Esc closes it and keeps the focus, the mouse can move onto it", async ({ app, page }) => {
  await app.open();
  const pop = page.locator("#popover");
  await page.locator("#btn-export").focus();
  await page.keyboard.press("Tab");
  await expect(page.locator("#btn-share")).toBeFocused();
  await expect(pop).toBeVisible();
  await expect(pop).toContainText(TIPS.controls["btn-share"].lead);
  await expect(page.locator("#btn-share")).toHaveAttribute("aria-describedby", "popover");
  await page.keyboard.press("Escape");
  await expect(pop).toBeHidden();
  await expect(page.locator("#btn-share")).toBeFocused();
  await expect(page.locator("#btn-share")).not.toHaveAttribute("aria-describedby", "popover");

  // from the control onto the box: it stays, and its link can be reached with the mouse
  await openTip(page, app.field("INNER_EDGE_RADIUS_MM").locator(".info-dot"));
  const link = await pop.locator(".tip-foot a").boundingBox();
  await page.mouse.move(link.x + link.width / 2, link.y + link.height / 2, { steps: 12 });
  await page.waitForTimeout(700);
  await expect(pop).toBeVisible();
  await page.mouse.move(1, 1, { steps: 6 });
  await expect(pop).toBeHidden();

  // a click on the control closes it
  await openTip(page, page.locator("#btn-share"));
  await page.mouse.down();
  await expect(pop).toBeHidden();
  await page.mouse.up();
});

test("a scroll of the page closes the tip; a control scrolled into view shows its tip", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  const last = page.locator("#advanced-controls .info-dot").last();
  const pop = await openTip(page, last);
  await page.mouse.wheel(0, -200);
  await expect(pop).toBeHidden();
});

for (const [w, h] of [[640, 512], [320, 256]]) {
  test(`the tip stays inside a ${w} x ${h} window (${w === 640 ? 200 : 400} % zoom), scrolling inside when it is taller`, async ({ app, page }) => {
    await page.setViewportSize({ width: w, height: h });
    await app.open();
    for (const target of [app.field("INNER_EDGE_RADIUS_MM").locator(".info-dot"), page.locator("#btn-generate"), page.locator("#btn-share")]) {
      const pop = await openTip(page, target);
      await insideWindow(page, pop, `${w} x ${h}`);
      expect(await pop.evaluate((p) => p.scrollWidth <= p.clientWidth + 1), "nothing sticks out sideways").toBe(true);
      if (await pop.evaluate((p) => p.scrollHeight > p.clientHeight + 1)) {    // taller than the room: it scrolls inside, and stays open
        await pop.evaluate((p) => { p.scrollTop = 30; });
        await page.waitForTimeout(200);
        await expect(pop).toBeVisible();
      }
    }
  });
}

test("a box taller than its room, opened with the keyboard: it names its keys, and Alt + the arrows scroll it", async ({ app, page }) => {
  await page.setViewportSize({ width: 640, height: 512 });
  await app.open();
  await page.click('#basic-tabs [data-key="RX"]');
  const dot = app.field("INSIDE_RADIUS_MM").locator(".info-dot"), pop = page.locator("#popover");
  // with the mouse the box has no line about keys
  await openTip(page, dot);
  expect(await pop.evaluate((p) => p.scrollHeight > p.clientHeight + 1), "the box with its picture is taller than a 512 px window").toBe(true);
  await expect(pop.locator(".tip-scroll")).toHaveCount(0);
  await closeTip(page);
  // with the keyboard it has, and the keys work
  await dot.focus();
  await page.keyboard.press("Shift+Tab"); await page.keyboard.press("Tab");
  await expect(dot).toBeFocused();
  await expect(pop).toBeVisible();
  await expect(pop.locator(".tip-scroll")).toHaveText(/Alt\s*\+\s*↓\s*scrolls this box/);
  await insideWindow(page, pop, "640 x 512, by the keyboard");
  await page.keyboard.press("Alt+ArrowDown"); await page.keyboard.press("Alt+ArrowDown");
  expect(await pop.evaluate((p) => p.scrollTop)).toBeGreaterThan(60);
  await expect(pop).toBeVisible();
  await expect(dot).toBeFocused();
  for (let i = 0; i < 12; i++) await page.keyboard.press("Alt+ArrowUp");
  expect(await pop.evaluate((p) => p.scrollTop)).toBe(0);
  await page.keyboard.press("Escape");
  await expect(pop).toBeHidden();
});

test("axe finds nothing with a tip open", async ({ app, page }) => {
  await app.open();
  const found = [];
  for (const target of [app.field("INNER_EDGE_RADIUS_MM").locator(".info-dot"), page.locator("#btn-generate"), page.locator("#btn-share")]) {
    await openTip(page, target);
    const r = await new AxeBuilder({ page }).withTags(TAGS).disableRules(["label-title-only"]).analyze();
    found.push(...r.violations.filter((v) => !(v.id === "label-content-name-mismatch" && v.nodes.every((x) => x.target.join(" ") === "#btn-measure"))).map((v) => `${v.id} (${v.impact}) ${v.help} -> ${v.nodes.slice(0, 3).map((x) => x.target.join(" ")).join(" | ")}`));
  }
  expect(found).toEqual([]);
});

test("a dialog that closes opens no tip: not for the focus it hands back, not for the mouse resting on the button", async ({ app, page }) => {
  await app.open();
  const pop = page.locator("#popover");
  await page.click("#btn-runtext");
  await expect(page.locator("#text-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("#text-dialog")).toBeHidden();
  await page.waitForTimeout(800);                            // longer than a tip waits
  await expect(pop).toBeHidden();
  const box = await page.locator("#btn-runtext").boundingBox();
  await page.mouse.move(box.x + box.width / 2 + 2, box.y + box.height / 2);   // the mouse moves on the button: now its tip opens
  await expect(pop).toBeVisible();
  await closeTip(page);
  await page.focus("#btn-share");
  await page.keyboard.press("Tab");                          // and the keyboard opens tips as before
  await expect(pop).toBeVisible();
});

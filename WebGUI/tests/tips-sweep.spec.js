/* tips-sweep: every help box of the page, opened in turn at five window sizes.  Slow (many minutes), so it is not part
   of the suite: it runs only when asked, before a merge.

       SWEEP=1 npx playwright test tips-sweep --project=chromium           (inside WebGUI/)
       SWEEP=1 SWEEP_SIZES=1280x720,320x256 npx playwright test tips-sweep  (only some sizes)

   After a real run, with every tab, every coil set and the folded rotor settings open, the mouse rests on every
   control that has a help box.  For each box: it is inside the window and no taller than it, it does not lie over its
   control (where a side has room), nothing sticks out of it, no {name}, "undefined" or "NaN" is left in it, its
   picture has loaded, and it has the new layout wherever tips.json has its words.  What it finds is printed as a
   list and fails the test. */
import fs from "node:fs";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";

const TIPS = JSON.parse(fs.readFileSync(path.join(REPO, "WebGUI", "tips.json"), "utf8"));
const SIZES = (process.env.SWEEP_SIZES || "1280x720,1024x768,768x1024,640x512,320x256").split(",").map((s) => s.split("x").map(Number));
const OWNERS = "[data-tip-id]:visible:not(:disabled), .info-dot[data-help]:visible";

async function rest(page) {
  await page.keyboard.press("Escape");                       // a big box may lie over the next control: close it first
  await page.mouse.move(1, 1);
  await expect(page.locator("#popover")).toBeHidden();
}
/* Open the box of every control that is shown now; returns what is wrong, as lines. */
async function sweep(page, where, seen) {
  const wrong = [], pop = page.locator("#popover"), owners = page.locator(OWNERS);
  const n = await owners.count();
  for (let i = 0; i < n; i++) {
    const node = owners.nth(i);
    const id = await node.evaluate((x) => x.dataset.help || x.dataset.tipId);
    const at = `${where} · ${id}`;
    await rest(page);
    await node.scrollIntoViewIfNeeded();
    await page.waitForTimeout(120);
    const reach = await node.evaluate((x) => {
      const r = x.getBoundingClientRect(), hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
      return !!hit && x.contains(hit);
    });
    if (!reach) continue;                                     // a line of a closed menu, a control behind another
    await node.hover();
    try { await expect(pop).toBeVisible({ timeout: 3000 }); } catch (e) { wrong.push(`${at}: no box opened`); continue; }
    seen.add(id);
    const got = await pop.evaluate((p, x) => {
      const b = p.getBoundingClientRect(), c = x.getBoundingClientRect(), W = document.documentElement.clientWidth, H = document.documentElement.clientHeight;
      const out = [...p.querySelectorAll("*")].filter((e) => { const r = e.getBoundingClientRect(); return r.width && (r.right > b.right + 1 || r.left < b.left - 1); }).length;
      const img = p.querySelector("img");
      return { text: p.innerText, plain: p.classList.contains("plain"), rich: p.classList.contains("rich"),
        inside: b.left >= 0 && b.top >= 0 && b.right <= W + 0.5 && b.bottom <= H + 0.5,
        over: !(b.right <= c.left || b.left >= c.right || b.bottom <= c.top || b.top >= c.bottom),
        room: Math.max(c.top, H - c.bottom),                  // the larger room above or below the control
        wide: p.scrollWidth > p.clientWidth + 1, out, scrolls: p.scrollHeight > p.clientHeight + 1, cut: !!p.style.maxHeight,
        picture: img ? img.complete && img.naturalWidth > 0 : null };
    }, await node.elementHandle());
    if (!got.text.trim()) wrong.push(`${at}: empty`);
    if (/\{\w*\}|undefined|NaN|\[object|\bnull\b/.test(got.text)) wrong.push(`${at}: a value is missing in "${got.text.replace(/\s+/g, " ").slice(0, 90)}"`);
    if (!got.inside) wrong.push(`${at}: outside the window`);
    if (got.over && got.room >= 96 + 14) wrong.push(`${at}: lies over its control`);
    if (got.wide || got.out) wrong.push(`${at}: something sticks out of the box`);
    if (got.scrolls && !got.cut) wrong.push(`${at}: scrolls inside though it was not cut to the room`);
    if (got.picture === false) wrong.push(`${at}: its picture did not load`);
    const inFile = ((await node.getAttribute("data-help")) ? id in TIPS.params : id.startsWith("preset:") ? id.slice(7) in TIPS.presets : id in TIPS.controls);
    if (inFile && got.plain) wrong.push(`${at}: tips.json has its words, the box shows only the plain text`);
    if (inFile && (await node.getAttribute("data-help")) && !got.rich) wrong.push(`${at}: a setting without the new layout`);
  }
  await rest(page);
  return wrong;
}
/* Every tab and coil set of the settings column that is shown, with the folded groups open. */
async function everyTab(page, view, where, seen) {
  const wrong = [];
  const keys = await page.locator(`#${view}-tabs [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key));
  for (const k of keys) {
    await page.click(`#${view}-tabs [data-key="${k}"]`);
    const sets = await page.locator(`#${view}-set:not([hidden]) [data-key]`).evaluateAll((l) => l.map((b) => b.dataset.key));
    for (const s of sets.length ? sets : [null]) {
      if (s) await page.click(`#${view}-set [data-key="${s}"]`);
      for (const fold of await page.locator(".group-title.foldable.collapsed:visible").all()) await fold.click();
      wrong.push(...await sweep(page, `${where} ${k}${s ? " set " + s : ""}`, seen));
    }
  }
  return wrong;
}

for (const [w, h] of SIZES) {
  for (const gen of ["single", "dual"]) {
    test(`sweep ${gen} at ${w} x ${h}`, async ({ app, page }) => {
      test.skip(!process.env.SWEEP, "the slow sweep of every tip: SWEEP=1 npx playwright test tips-sweep");
      test.setTimeout(45 * 60 * 1000);
      await page.setViewportSize({ width: w, height: h });
      await app.open(gen === "dual" ? "#dual=" : "");
      const seen = new Set(), where = `${gen} ${w}x${h}`;
      const wrong = await everyTab(page, "basic", `${where} Basic`, seen);
      for (const v of ["stator", "rotor", "pictures", "overlay"]) {
        await page.click(`#preview [data-view="${v}"]`);
        wrong.push(...await sweep(page, `${where} view ${v}`, new Set()));
      }
      await app.mode("advanced");
      wrong.push(...await everyTab(page, "adv", `${where} Advanced`, seen));
      console.log(`${where}: ${seen.size} different tips opened, ${wrong.length} to look at`);
      for (const line of wrong) console.log("  " + line);
      expect(wrong).toEqual([]);
    });
  }
}

/* preview: the drawing of the boards.  Zoom and moving, the buttons that show, hide and bring out layers and coils,
   Measure, the rotor angle and the generator's pictures.  Nothing here changes a board (bug round 19). */
import { test, expect } from "./frame.js";

/* the view as app/boardview.js holds it */
const view = (page) => page.evaluate(async () => {
  const { view: v } = await import("./app/preview.js");
  return { scale: v.view.scale, ox: v.view.ox, oy: v.view.oy, dpr: devicePixelRatio, hidden: [...v.hidden].sort(), nets: [...v.hiddenNets].sort(),
    sets: [...v.hiddenSets].sort(), layer: v.highlightLayer, role: v.highlight, set: v.highlightSet, lines: v.mLocked.length,
    a: v.mA, b: v.mB, circle: v.canvas.dataset.circle.split(" ").map(Number), angle: v.rotorAngle };
});
/* how many pixels of the drawing have each layer's colour */
const ink = (page) => page.evaluate(() => {
  // read from a copy: the page's own canvas is not made for reading, and the browser would say so in the console
  const c = document.getElementById("board-canvas"), copy = Object.assign(document.createElement("canvas"), { width: c.width, height: c.height });
  const g = copy.getContext("2d", { willReadFrequently: true }); g.drawImage(c, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height).data;
  const rgb = (name) => { const x = document.createElement("canvas").getContext("2d"); x.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(name).trim(); x.fillRect(0, 0, 1, 1); return x.getImageData(0, 0, 1, 1).data; };
  const colours = { top: rgb("--top"), bottom: rgb("--bottom"), via: rgb("--via") }, n = { any: 0, top: 0, bottom: 0, via: 0 };
  for (let i = 0; i < d.length; i += 4) {
    if (d[i + 3] < 200) continue;
    n.any++;
    for (const k in colours) { const q = colours[k]; if (Math.abs(d[i] - q[0]) < 14 && Math.abs(d[i + 1] - q[1]) < 14 && Math.abs(d[i + 2] - q[2]) < 14) { n[k]++; break; } }
  }
  return n;
});
const chip = (page, text) => page.locator("#layer-toggles .layer-chip, #silk-toggles .layer-chip").filter({ hasText: new RegExp(`^${text}$`) });
const net = (page, text) => page.locator("#net-toggles .net-btn").filter({ hasText: new RegExp(`^${text}$`) });
const away = (page) => page.mouse.move(3, 3, { steps: 3 });

test("the wheel zooms about the place the mouse points at, dragging moves the board, a double click and Fit bring it back", async ({ app, page }) => {
  await app.open();
  // the drawing starts between two pixels, as it does with some fonts and zoom steps
  await page.evaluate(() => Object.assign(document.getElementById("preview").style, { position: "relative", left: "0.4px", top: "0.4px" }));
  await page.click('#view-tabs [data-view="stator"]');
  const box = await page.locator("#board-canvas").boundingBox(), fit = await view(page);
  expect(box.x % 1, "the drawing's left edge is between two pixels").not.toBe(0);
  // Fit: the whole board in the drawing, clear of the buttons that lie on it
  const [cx, cy, r] = fit.circle;
  expect(cx - r).toBeGreaterThanOrEqual(0); expect(cy - r).toBeGreaterThanOrEqual(0);
  expect(cx + r).toBeLessThanOrEqual(box.width + 0.5); expect(cy + r).toBeLessThanOrEqual(box.height + 0.5);
  for (const id of ["canvas-tools", "silk-toggles", "net-toggles", "readout"]) {
    const b = await page.locator("#" + id).boundingBox();
    if (!b || !b.width) continue;
    const l = b.x - box.x, t = b.y - box.y;
    expect(Math.hypot(Math.max(l - cx, 0, cx - (l + b.width)), Math.max(t - cy, 0, cy - (t + b.height))), `#${id} keeps out of the board's circle`).toBeGreaterThan(r - 0.6);
  }
  // the readout: millimetres from the board's centre, right and up counted positive
  const mouse = [Math.round(box.x + cx + 30), Math.round(box.y + cy - 30)];                   // whole pixels, as the mouse gives them
  await page.mouse.move(...mouse);
  const [, x, y] = /X: (-?[\d.]+) mm, Y: (-?[\d.]+) mm/.exec(await page.locator("#readout").innerText());
  expect(+x).toBeCloseTo((mouse[0] - box.x - cx) * fit.dpr / fit.scale, 1);
  expect(+y).toBeCloseTo((box.y + cy - mouse[1]) * fit.dpr / fit.scale, 1);
  // the wheel: the place under the mouse stays where it is
  const at = [Math.round(box.x + box.width * 0.3), Math.round(box.y + box.height * 0.4)];    // whole pixels, as the mouse gives them
  const onBoard = (v) => [((at[0] - box.x) * v.dpr - v.ox) / v.scale, ((at[1] - box.y) * v.dpr - v.oy) / v.scale];
  await page.mouse.move(...at);
  await page.mouse.wheel(0, -300);
  await expect.poll(async () => (await view(page)).scale).toBeGreaterThan(fit.scale * 1.3);
  const zoomed = await view(page);
  expect(onBoard(zoomed)[0]).toBeCloseTo(onBoard(fit)[0], 3);
  expect(onBoard(zoomed)[1]).toBeCloseTo(onBoard(fit)[1], 3);
  // dragging moves it by what the mouse moved
  await page.mouse.down(); await page.mouse.move(at[0] + 60, at[1] - 40, { steps: 4 }); await page.mouse.up();
  const moved = await view(page);
  expect(moved.ox - zoomed.ox).toBeCloseTo(60 * zoomed.dpr, 0);
  expect(moved.oy - zoomed.oy).toBeCloseTo(-40 * zoomed.dpr, 0);
  // a double click, and Fit, show the whole board again
  await page.mouse.dblclick(...at);
  expect((await view(page)).scale).toBeCloseTo(fit.scale, 6);
  await page.mouse.wheel(0, 500);
  await expect.poll(async () => (await view(page)).scale).toBeLessThan(fit.scale * 0.8);
  await page.click("#btn-fit");
  expect(await view(page)).toMatchObject({ scale: fit.scale, ox: fit.ox, oy: fit.oy });
  // the Info switch of Checks is not about the drawing: a zoom stays
  await page.mouse.move(...at); await page.mouse.wheel(0, -300);
  await expect.poll(async () => (await view(page)).scale).toBeGreaterThan(fit.scale * 1.3);
  const kept = await view(page);
  await page.locator("#show-info").check({ force: true });
  await page.waitForTimeout(300);
  expect((await view(page)).scale).toBe(kept.scale);
});

test("layers, vias and coils: a click hides and shows, the mouse and the keyboard's focus bring one out, a click leaves nothing brought out", async ({ app, page }) => {
  await app.open();
  await page.click('#view-tabs [data-view="stator"]');
  await away(page);
  const all = await ink(page);
  expect(all.top).toBeGreaterThan(500); expect(all.bottom).toBeGreaterThan(500); expect(all.via).toBeGreaterThan(20);
  // a click hides the layer, the next shows it again
  for (const [text, key, layer] of [["Top", "top", "F.Cu"], ["Bottom", "bottom", "B.Cu"], ["Vias", "via", "Vias"]]) {
    await chip(page, text).click();
    await away(page);
    expect((await view(page)).hidden).toContain(layer);
    await expect(chip(page, text)).toHaveAttribute("aria-checked", "false");
    expect((await ink(page))[key], `${text} hidden`).toBeLessThan(all[key] * 0.25);
    await chip(page, text).click();
    await away(page);
    await expect(chip(page, text)).toHaveAttribute("aria-checked", "true");
    const again = await view(page);
    expect(again.hidden).not.toContain(layer);
    expect(again.layer, "the click left the focus on the chip, and nothing is brought out").toBeNull();
    expect((await ink(page))[key], `${text} shown again`).toBeGreaterThan(all[key] * 0.95);
  }
  // the mouse on a chip brings its layer out: the others fade
  await chip(page, "Top").hover();
  expect((await view(page)).layer).toBe("F.Cu");
  expect((await ink(page)).bottom).toBeLessThan(all.bottom * 0.3);
  await away(page);
  expect((await view(page)).layer).toBeNull();
  // the keyboard's focus does the same, and Space hides
  await page.locator("#view-tabs [aria-checked=true]").focus();
  await page.keyboard.press("Tab");
  await expect(chip(page, "Top")).toBeFocused();
  expect((await view(page)).layer).toBe("F.Cu");
  await page.keyboard.press("Space");
  expect((await view(page)).hidden).toContain("F.Cu");
  await expect(chip(page, "Top")).toBeFocused();
  await page.keyboard.press("Space");
  expect((await view(page)).hidden).not.toContain("F.Cu");
  // Esc puts away the help box the focus opened: in WebKit it lies over the silkscreen chips
  await page.keyboard.press("Escape");
  await expect(page.locator("#popover")).toBeHidden();
  // the silkscreen: its bottom side starts hidden, as it repeats the top side mirrored
  await expect(chip(page, "Silk Top")).toHaveAttribute("aria-checked", "true");
  await expect(chip(page, "Silk Bottom")).toHaveAttribute("aria-checked", "false");
  await chip(page, "Silk Top").click();
  expect((await view(page)).hidden).toEqual(["B.SilkS", "F.SilkS"]);
  await chip(page, "Silk Top").click();
  // the coils
  await away(page);
  await expect(page.locator("#net-toggles .net-btn")).toHaveText(["Sin Loops", "Cos Loops", "TX Loops"]);
  for (const [text, role] of [["Sin Loops", "sin"], ["Cos Loops", "cos"], ["TX Loops", "tx"]]) {
    await net(page, text).hover();
    expect((await view(page)).role).toBe(role);
    await net(page, text).click();
    await away(page);
    expect((await view(page)).nets).toEqual([role]);
    expect((await ink(page)).any).toBeLessThan(all.any - 200);
    await net(page, text).click();
    await away(page);
    expect(await view(page)).toMatchObject({ nets: [], role: null });
  }
  expect((await ink(page)).any).toBeGreaterThan(all.any * 0.98);
  // the rotor has no coils: their buttons go
  await page.click('#view-tabs [data-view="rotor"]');
  await expect(page.locator("#net-toggles .net-btn")).toHaveCount(0);
});

test("Measure: two clicks give a line and its length, S keeps it, Z takes the last away, 256 kept lines are the limit", async ({ app, page }) => {
  await app.open();
  const box = await page.locator("#board-canvas").boundingBox(), fit = await view(page);
  const [cx, cy] = fit.circle, a = [box.x + cx - 50, box.y + cy], b = [box.x + cx + 50, box.y + cy], mm = 100 * fit.dpr / fit.scale;
  await page.click("#btn-measure");
  await expect(page.locator("#btn-measure")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#measure-help")).toBeVisible();
  await page.mouse.click(...a);
  await page.mouse.move(...b);
  const [, shown] = /Distance: ([\d.]+) mm/.exec(await page.locator("#readout").innerText());
  expect(+shown).toBeCloseTo(mm, 2);
  await page.mouse.click(...b);
  await expect(page.locator("#sr-status")).toHaveText(/^Line 1: \d+\.\d{3} mm$/);
  let v = await view(page);
  expect(Math.hypot(v.b[0] - v.a[0], v.b[1] - v.a[1])).toBeCloseTo(mm, 6);
  await page.keyboard.press("s");
  v = await view(page);
  expect([v.lines, v.a]).toEqual([1, null]);
  await page.mouse.click(...a);                                   // a point of the next line: Z takes it away, then the kept line
  await page.keyboard.press("z");
  expect(await view(page)).toMatchObject({ lines: 1, a: null });
  await page.keyboard.press("z");
  expect((await view(page)).lines).toBe(0);
  // the limit: the 257th line is not kept, and the page says so
  await page.evaluate(async () => {
    const { view: w } = await import("./app/preview.js");
    for (let i = 0; i < 255; i++) w.mLocked.push([[90, 90 + i / 10], [110, 90 + i / 10]]);
  });
  for (let i = 0; i < 2; i++) { await page.mouse.click(...a); await page.mouse.click(...b); await page.keyboard.press("s"); }
  expect((await view(page)).lines).toBe(256);
  await expect(app.toast()).toHaveText("256 lines kept: that is the limit");
  // Measure off: every line goes
  await page.click("#btn-measure");
  expect(await view(page)).toMatchObject({ lines: 0, a: null, b: null });
  await expect(page.locator("#measure-help")).toBeHidden();
});

test("Overlay turns the rotor; Pictures shows the generator's two pictures and puts the drawing's tools away", async ({ app, page, context }) => {
  await app.open();
  await expect(page.locator('#view-tabs [data-view="overlay"]')).toHaveAttribute("aria-checked", "true");
  const at0 = await ink(page);
  await page.locator("#rotor-angle").fill("37.5");
  await expect(page.locator("#rotor-angle-out")).toHaveText("37.5°");
  expect((await view(page)).angle).toBe(37.5);
  await page.locator("#rotor-angle").fill("360");
  expect(Math.abs((await ink(page)).any - at0.any), "a full turn is the drawing at 0").toBeLessThan(80);
  await page.click('#view-tabs [data-view="stator"]');
  await expect(page.locator("#rotor-angle-box")).toBeHidden();

  await expect(page.locator('#view-tabs [data-view="pictures"]'), "Pictures is put away for now").toBeHidden();
  await page.evaluate(() => { document.querySelector('[data-view="pictures"]').hidden = false; });   // put away on the page, its code still tested
  await page.click('#view-tabs [data-view="pictures"]');
  const pictures = page.locator("#pictures img");
  await expect(pictures).toHaveCount(2);
  await pictures.evaluateAll((imgs) => Promise.all(imgs.map((i) => i.complete || new Promise((done) => { i.onload = i.onerror = done; }))));
  expect(await pictures.evaluateAll((imgs) => imgs.map((i) => i.naturalWidth > 0 && /^(Representative|Actual) picture of Coil_/.test(i.alt)))).toEqual([true, true]);
  // side by side in a wide window: the two pictures share one row, centred on the same line, and the captions stand on one line
  const boxes = () => page.locator("#pictures figure").evaluateAll((fs) => fs.map((f) => {
    const a = f.querySelector("img").getBoundingClientRect(), c = f.querySelector("figcaption").getBoundingClientRect();
    return { top: a.top, bottom: a.bottom, mid: (a.top + a.bottom) / 2, caption: c.top };
  }));
  let [one, two] = await boxes();
  expect(Math.abs(one.mid - two.mid), "the pictures are centred on one line").toBeLessThan(2);
  expect(Math.abs(one.caption - two.caption), "the captions stand on one line").toBeLessThan(2);
  for (const id of ["board-canvas", "canvas-tools", "readout", "layer-toggles", "silk-toggles", "rotor-angle-box"]) await expect(page.locator("#" + id)).toBeHidden();
  await expect(page.locator("#net-toggles .net-btn")).toHaveCount(0);
  // a picture opens in a new tab, as the file the generator wrote
  const [tab] = await Promise.all([context.waitForEvent("page"), page.locator("#pictures a").first().click()]);
  await tab.waitForLoadState();
  expect(await tab.evaluate(() => document.documentElement.tagName)).toBe("svg");
  await tab.close();
  await page.click('#view-tabs [data-view="overlay"]');
  await expect(page.locator("#board-canvas")).toBeVisible();
  await expect(page.locator("#rotor-angle-box")).toBeVisible();
  // a portrait window: the pictures one above the other
  await page.click('#view-tabs [data-view="pictures"]');
  await page.setViewportSize({ width: 900, height: 1500 });
  await expect.poll(async () => { [one, two] = await boxes(); return two.top >= one.bottom; }, { message: "the second picture under the first" }).toBe(true);
});

test("Dual: Set 1 and Set 2 hide and bring out their own coils", async ({ app, page }) => {
  await app.open("#dual=");
  await page.click('#view-tabs [data-view="stator"]');
  await away(page);
  await expect(page.locator("#net-toggles .net-btn")).toHaveText(["Sin Loops", "Cos Loops", "TX Loops", "Set 1", "Set 2"]);
  const all = await ink(page);
  await net(page, "Set 1").hover();
  expect((await view(page)).set).toBe(1);
  await net(page, "Set 1").click();
  await away(page);
  const one = await ink(page);
  expect(one.any).toBeLessThan(all.any - 500);
  await net(page, "Set 2").click();
  await away(page);
  const none = await ink(page);
  expect((await view(page)).sets).toEqual([1, 2]);
  expect(none.top + none.bottom, "no copper of either set is drawn").toBeLessThan(50);
  await net(page, "Set 1").click(); await net(page, "Set 2").click();
  await away(page);
  expect(await view(page)).toMatchObject({ sets: [], set: null });
  expect((await ink(page)).any).toBeGreaterThan(all.any * 0.98);
});

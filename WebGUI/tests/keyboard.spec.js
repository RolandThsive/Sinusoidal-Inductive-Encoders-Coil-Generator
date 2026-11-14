/* The page used with the keyboard alone: Tab goes through everything once, in the order of the page; the focus is
   never lost and never caught; what a key starts hands the focus back when it is done. */
import { test, expect } from "./frame.js";

/* the element that has the focus, named so that two runs of the page give the same name */
const focused = (page) => page.evaluate(() => {
  const e = document.activeElement;
  if (!e || e === document.body) return "the page";
  return e.id ? "#" + e.id : `${e.tagName.toLowerCase()}[${e.dataset.focus || e.dataset.key || e.dataset.view || e.getAttribute("aria-label") || e.textContent.trim().slice(0, 30)}]`;
});
const tipShown = (page) => page.evaluate(() => !document.getElementById("popover").hidden);

for (const mode of ["basic", "advanced"]) {
  test(`${mode}: Tab reaches every control once, in the order of the page, and comes round again`, async ({ app, page }) => {
    await app.open();
    await app.mode(mode);
    // what Tab should stop at: everything shown that takes the focus (of a row of choices, the one that is on)
    const expected = await page.evaluate(() => {
      const name = (e) => (e.id ? "#" + e.id : `${e.tagName.toLowerCase()}[${e.dataset.focus || e.dataset.key || e.dataset.view || e.getAttribute("aria-label") || e.textContent.trim().slice(0, 30)}]`);
      const all = [...document.querySelectorAll("a[href], button, input, select, textarea, [tabindex]")];
      const wrong = all.filter((e) => e.tabIndex > 0).map(name);
      const stops = all.filter((e) => e.tabIndex === 0 && !e.disabled && e.type !== "hidden" && !e.closest("[hidden], dialog:not([open]), [inert]")
        && e.checkVisibility({ visibilityProperty: true }) && (e.offsetParent !== null || getComputedStyle(e).position === "fixed"));
      return { wrong, stops: stops.map(name) };
    });
    expect(expected.wrong, "no control jumps the queue with a tabindex above 0").toEqual([]);
    expect(expected.stops.length).toBeGreaterThan(30);
    await page.focus("#gen-btn");                                     // the first control of the page
    const seen = [await focused(page)];
    for (let i = 0; i < expected.stops.length + 5; i++) {
      await page.keyboard.press("Tab");
      const at = await focused(page);
      if (at === "the page") break;                                   // past the last control: the browser's own bar
      seen.push(at);
    }
    expect(seen).toEqual(expected.stops);                             // all of them, once each, in the page's order
    // and backwards: from the last control to the one before it (not from "the page": where Shift+Tab goes from
    // there is the browser's own matter, and Firefox goes to the text box the cursor was in last)
    const last = expected.stops[expected.stops.length - 1];
    expect(last).toBe("#report-link");
    await page.focus(last);
    await page.keyboard.press("Shift+Tab");
    expect(await focused(page)).toBe(expected.stops[expected.stops.length - 2]);
  });
}

test("a run started with a key hands the focus back: Generate, Check Only, Cancel", async ({ app, page }) => {
  await app.open();
  await page.focus("#btn-generate");
  await page.keyboard.press("Enter");
  await expect(page.locator("#run-card")).toBeVisible();
  await app.settled();
  expect(await focused(page)).toBe("#btn-generate");
  await page.waitForTimeout(400);
  expect(await tipShown(page)).toBe(false);                           // the focus the page puts back opens no help box
  await page.keyboard.press("Enter");                                 // so Enter runs it again
  await expect(page.locator("#run-card")).toBeVisible();
  await page.focus("#btn-cancel");
  await page.keyboard.press("Enter");
  await app.settled();
  await expect(app.toast()).toHaveText("Cancelled");
  expect(await focused(page)).toBe("#btn-generate");
  await page.keyboard.press("Shift+Tab");
  expect(await focused(page)).toBe("#btn-check");
  await page.keyboard.press("Space");
  await app.settled();
  expect(await focused(page)).toBe("#btn-check");
  expect(await app.counts()).toContain("Check Passed");
  // someone who moves on during the run stays where they went
  await page.focus("#btn-generate");
  await page.keyboard.press("Enter");
  await page.focus("#btn-share");
  await app.settled();
  expect(await focused(page)).toBe("#btn-share");
});

test("the generator menu, a setting's menu and the dialogs give the focus back to where it came from", async ({ app, page }) => {
  test.setTimeout(400000);
  await app.open();
  await app.mode("advanced");
  // the dialogs (asked for while the board on show is the one of the settings: All Files is live only then): Esc
  // closes each, and the button that opened it has the focus again
  for (const [button, dialog] of [["#btn-reset", "#confirm-dialog"], ["#btn-runtext", "#text-dialog"], ["#btn-files", "#files-dialog"]]) {
    await page.focus(button);
    await page.keyboard.press("Enter");
    await expect(page.locator(dialog)).toBeVisible();
    expect(await page.evaluate((d) => document.querySelector(d).contains(document.activeElement), dialog), dialog).toBe(true);
    await page.keyboard.press("Escape");
    await expect(page.locator(dialog)).toBeHidden();
    expect(await focused(page), dialog).toBe(button);
  }
  // a menu of a setting: the arrow keys open it and move in it, Enter chooses, the focus is on the menu's button again
  await app.tab("TX");
  const menu = page.locator("#advanced-panel .dropdown-btn").first();
  await menu.focus();
  const before = await focused(page);
  await page.keyboard.press("ArrowDown");
  await expect(page.locator("#advanced-panel .dropdown.open")).toHaveCount(1);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await app.settled();
  await expect(page.locator("#advanced-panel .dropdown.open")).toHaveCount(0);
  expect(await focused(page)).toBe(before);
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Escape");                                // Esc closes it and changes nothing
  expect(await focused(page)).toBe(before);
  // Reset answered with the keyboard: the dialog starts on No, Sure is one Shift+Tab away
  await app.tab("Board");
  await app.type("AIR_GAP_MM", "1.5");
  await page.focus("#btn-reset");
  await page.keyboard.press("Enter");
  expect(await focused(page)).not.toBe("#confirm-yes");
  await page.keyboard.press("Enter");                                 // No
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await page.keyboard.press("Enter");
  await page.keyboard.press("Shift+Tab");
  expect(await focused(page)).toBe("#confirm-yes");
  await page.keyboard.press("Enter");
  await expect(app.toast()).toHaveText("Back to the starting design");
  await app.settled();
  expect(await app.value("AIR_GAP_MM")).toBe("1");
  expect(await focused(page)).toBe("#btn-reset");
  // the generator menu: Dual chosen with the keys; when its first board is there the focus is on the menu again
  await page.focus("#gen-btn");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Enter");
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await app.settled();
  expect(await focused(page)).toBe("#gen-btn");
  expect(await app.counts()).toContain("DualCoil_");
});

test("a menu opened with the mouse closes with Esc, and when the focus goes on", async ({ app, page }) => {
  await app.open();
  // the generator menu: a click opens it, the focus is not in its list
  await page.click("#gen-btn");
  await expect(page.locator(".dropdown.open")).toHaveCount(1);
  expect(await page.evaluate(() => !!document.activeElement.closest('[role="listbox"]'))).toBe(false);
  await page.keyboard.press("Escape");
  await expect(page.locator(".dropdown.open")).toHaveCount(0);
  await expect(page.locator("#gen-btn")).toHaveAttribute("aria-expanded", "false");
  // with the focus nowhere, as in a browser that does not focus a clicked button
  await page.click("#gen-btn");
  await page.evaluate(() => document.activeElement.blur());
  await page.keyboard.press("Escape");
  await expect(page.locator(".dropdown.open")).toHaveCount(0);
  // Tab from the open menu's button: the focus goes on, the menu closes
  await page.click("#gen-btn");
  await expect(page.locator(".dropdown.open")).toHaveCount(1);
  await page.focus("#gen-btn");                                       // where a click leaves it in most browsers
  await page.keyboard.press("Tab");
  await expect(page.locator(".dropdown.open")).toHaveCount(0);
  // a setting's menu, the same
  await app.mode("advanced");
  await app.tab("TX");
  const menu = page.locator("#advanced-panel .dropdown-btn").first();
  await menu.click();
  await expect(page.locator("#advanced-panel .dropdown.open")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.locator("#advanced-panel .dropdown.open")).toHaveCount(0);
  await expect(page.locator("#checks-list .check.error")).toHaveCount(0);
});

test("Measure with the keys: the arrows move a cross over the board, Enter sets the two points of a line", async ({ app, page }) => {
  await app.open();
  await page.focus("#btn-measure");
  await page.keyboard.press("Enter");
  await expect(page.locator("#btn-measure")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator("#board-canvas")).toHaveAttribute("aria-label", /Measure is on/);
  await page.focus("#board-canvas");
  await page.keyboard.press("Enter");                                 // the first point, in the middle of the drawing
  await expect(page.locator("#sr-status")).toHaveText("First point set");
  const distance = async () => +/Distance: ([\d.]+) mm/.exec(await page.locator("#readout").innerText())[1];
  expect(await distance()).toBe(0);
  for (let i = 0; i < 5; i++) await page.keyboard.press("ArrowRight");
  const five = await distance();
  expect(five).toBeGreaterThan(0);
  await page.keyboard.press("Shift+ArrowRight");                      // a small step: a tenth of a step
  expect(await distance()).toBeCloseTo(five * 51 / 50, 2);
  await page.keyboard.press("Shift+ArrowLeft");
  for (let i = 0; i < 5; i++) await page.keyboard.press("ArrowDown"); // 5 right and 5 down: the diagonal
  expect(await distance()).toBeCloseTo(five * Math.SQRT2, 2);
  await page.keyboard.press("Enter");                                 // the second point: the line is measured
  await expect(page.locator("#sr-status")).toHaveText(/^Line 1: \d+\.\d{3} mm$/);
  expect(+/Line 1: ([\d.]+) mm/.exec(await page.locator("#sr-status").innerText())[1]).toBeCloseTo(five * Math.SQRT2, 2);
  await page.keyboard.press("s");                                     // kept; the next line is line 2
  await page.keyboard.press("Enter");
  await page.keyboard.press("ArrowUp");
  await page.keyboard.press("Enter");
  await expect(page.locator("#sr-status")).toHaveText(/^Line 2: /);
  await page.focus("#btn-measure");
  await page.keyboard.press("Enter");                                 // Measure off: the arrows move the board again
  await expect(page.locator("#board-canvas")).toHaveAttribute("aria-label", /Arrow keys move the board/);
});

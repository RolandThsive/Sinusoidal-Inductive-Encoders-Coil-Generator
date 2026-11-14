/* What the page lets one do in each of its states: while Python loads, while the generator runs, while the other
   generator's settings are read, and with a dialog open. */
import { test, expect } from "./frame.js";

const view = (page) => page.evaluate(() => (document.getElementById("advanced-panel").hidden ? "basic" : "advanced"));

test("while Python loads: no run can start, Reset and Share do nothing, Basic | Advanced already works", async ({ app, page }) => {
  await app.open("", { settle: false });
  await expect(page.locator("#run-title")).toHaveText("Loading");
  expect(await app.state()).toBe("loading");
  await expect(page.locator("#btn-generate")).toBeDisabled();
  await expect(page.locator("#btn-check")).toBeDisabled();
  await expect(page.locator("#btn-download")).toBeDisabled();
  await page.keyboard.press("Control+Enter");
  await page.click("#btn-reset");
  await expect(page.locator("#confirm-dialog")).toBeHidden();              // nothing to put back yet
  await page.click("#btn-share");
  await expect(page.locator("#text-dialog")).toBeHidden();                 // no design to link to yet
  await expect(app.toast()).toBeHidden();
  await page.click('#mode-switch [data-mode="advanced"]');
  await expect.poll(() => view(page)).toBe("advanced");
  await expect(page.locator("#run-title")).toHaveText("Loading");
  await app.settled();
  expect(await view(page)).toBe("advanced");                               // the view chosen while it loaded is kept
  await expect(page.locator("#advanced-panel .field").first()).toBeVisible();
  await expect(app.findings("error")).toHaveCount(0);
});

test("during a run: no second run and no other generator; the views switch; a changed setting marks the board as old", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  const before = await app.counts();
  await page.click("#btn-generate");
  await expect(page.locator("#run-card")).toBeVisible();
  await expect(page.locator("#gen-btn")).toBeDisabled();
  await expect(page.locator("#btn-generate")).toBeDisabled();
  await expect(page.locator("#btn-check")).toBeDisabled();
  await page.keyboard.press("Control+Enter");                              // a second Generate: nothing
  await page.click('#mode-switch [data-mode="basic"]');
  await expect.poll(() => view(page)).toBe("basic");
  await page.click('#mode-switch [data-mode="advanced"]');
  await expect.poll(() => view(page)).toBe("advanced");
  expect(await app.state()).toBe("busy");
  // a setting typed while the generator runs: the run ends with the values it started with, and the board is old
  const box = app.field("AIR_GAP_MM").locator("input[type=text]").first();
  await box.fill("1.25");
  await box.press("Tab");
  await app.settled();
  await expect(page.locator("#run-card")).toBeHidden();
  await expect(page.locator("#stale-badge")).toBeVisible();
  await expect(page.locator("#stale-badge")).toContainText("Settings changed");
  await expect(page.locator("#btn-download")).toBeDisabled();
  expect((await app.counts()).replace(/ · [\d.]+ s$/, "")).toBe(before.replace(/ · [\d.]+ s$/, ""));
  await app.generate();
  await expect(page.locator("#stale-badge")).toBeHidden();
  await expect(page.locator("#btn-download")).toBeEnabled();

  // Reset while the generator runs: the settings go back at once, the board of the run is old
  await app.type("AIR_GAP_MM", "1.5");
  await page.click("#btn-generate");
  await expect(page.locator("#run-card")).toBeVisible();
  await page.click("#btn-reset");
  await page.click("#confirm-yes");
  await expect(app.toast()).toHaveText("Back to the starting design");
  expect(await app.state()).toBe("busy");
  await app.settled();
  expect(await app.value("AIR_GAP_MM")).not.toBe("1.5");
  await expect(page.locator("#stale-badge")).toBeVisible();
  await app.generate();
  await expect(page.locator("#stale-badge")).toBeHidden();
  await expect(app.findings("error")).toHaveCount(0);
});

test("a switch of generator: nothing else starts meanwhile; each generator keeps its board, its settings and its view", async ({ app, page }) => {
  test.setTimeout(400000);
  await app.open();
  await app.mode("advanced");
  await app.type("AIR_GAP_MM", "1.5");
  await app.generate();
  const single = await app.counts();
  // the moment after Dual is chosen: the menu and both run buttons are off until its settings are there
  await page.click("#gen-btn");
  const locked = await page.evaluate(() => {
    document.querySelector('#gen-list [data-gen="dual"]').click();
    const off = (id) => document.getElementById(id).disabled;
    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", ctrlKey: true, bubbles: true }));
    return { menu: off("gen-btn"), generate: off("btn-generate"), check: off("btn-check"), state: document.documentElement.dataset.state,
      open: document.getElementById("gen-btn").getAttribute("aria-expanded") };
  });
  expect(locked).toEqual({ menu: true, generate: true, check: true, state: "busy", open: "false" });
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await expect(page.locator("#run-title")).toHaveText("Generating");         // Dual's first board, by itself
  expect(await view(page)).toBe("advanced");
  // Cancel that first run: Dual is left without a board, and says nothing of Single's
  await page.click("#btn-cancel");
  await app.settled();
  await expect(app.toast()).toHaveText("Cancelled");
  expect(await app.counts()).toBe("");
  await expect(page.locator("#btn-download")).toBeDisabled();
  // back to Single: its board, its changed setting and its counts are as they were, and nothing runs
  await app.generator("single");
  await expect(page.locator("#run-card")).toBeHidden();
  expect(await app.counts()).toBe(single);
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await expect(page.locator("#btn-download")).toBeEnabled();
  await expect(page.locator("#stale-badge")).toBeHidden();
  // Find A Setting is each generator's own
  await page.fill("#find", "gap");
  await expect(page.locator("#find-count")).not.toHaveText("");
  await app.generator("dual");                                               // no board yet: it makes one now
  await expect(page.locator("#find")).toHaveValue("");
  await expect(app.findings("error")).toHaveCount(0);
  expect(await app.counts()).toContain("DualCoil_");
  await app.generator("single");
  await expect(page.locator("#find")).toHaveValue("gap");
  expect(await app.counts()).toBe(single);
});

test("Ctrl + Enter behind an open dialog starts no run", async ({ app, page }) => {
  await app.open();
  await page.click("#btn-runtext");
  await expect(page.locator("#text-dialog")).toBeVisible();
  await page.keyboard.press("Control+Enter");
  await page.waitForTimeout(300);
  expect(await app.state()).toBe("ready");
  await expect(page.locator("#run-card")).toBeHidden();
  await page.keyboard.press("Escape");
  await expect(page.locator("#text-dialog")).toBeHidden();
  await page.keyboard.press("Control+Enter");
  await expect(page.locator("#run-card")).toBeVisible();
  await app.settled();
});

test("Cancel at each step of a run: the page comes back every time, and the next run is whole", async ({ app, page }) => {
  test.setTimeout(400000);
  await app.open();
  const before = await app.counts();
  for (let step = 1; step <= 6; step++) {
    await page.click("#btn-generate");
    await expect(page.locator("#run-card")).toBeVisible();
    // wait for that step's line (a run that is over before it can be cancelled is a run that went through)
    await page.waitForFunction((n) => document.querySelectorAll("#run-steps li").length >= n || document.getElementById("run-card").hidden, step, { timeout: 60000 });
    const cancelled = await page.evaluate(() => { const b = document.getElementById("btn-cancel"); if (document.getElementById("run-card").hidden || b.disabled) return false; b.click(); return true; });
    await app.settled();
    await expect(page.locator("#run-card")).toBeHidden();
    if (cancelled) await expect(app.toast(), `step ${step}`).toHaveText("Cancelled");
    await expect(page.locator("#btn-generate")).toBeEnabled();
    await expect(page.locator("#btn-generate")).toHaveText("Generate");
    await expect(page.locator("#btn-download"), `step ${step}`).toBeEnabled();          // the board of before is still there
  }
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  expect((await app.counts()).replace(/ · [\d.]+ s$/, "")).toBe(before.replace(/ · [\d.]+ s$/, ""));
  expect((await app.download("#btn-download")).bytes.length).toBeGreaterThan(10000);
});

test("an error the cancelled Python still throws while it ends is not an error of the page", async ({ app, page }) => {
  await page.addInitScript(() => {                           // every worker the page starts is kept, to speak for it later
    window.__workers = [];
    const Real = window.Worker;
    window.Worker = class extends Real { constructor(...a) { super(...a); window.__workers.push(this); } };
  });
  await app.open();
  await page.click("#btn-generate");
  await expect(page.locator("#run-card")).toBeVisible();
  await page.click("#btn-cancel");
  // the worker that was ended, cut off inside Python (seen once in a few hundred cancels: "NoGilError")
  const taken = await page.evaluate(() => {
    const e = new ErrorEvent("error", { message: "Uncaught NoGilError: Attempted to use PyProxy when Python GIL not held", cancelable: true });
    window.__workers[0].dispatchEvent(e);
    return e.defaultPrevented;                               // taken by the page: the browser does not report it to the window
  });
  expect(await page.evaluate(() => window.__workers.length)).toBe(2);
  expect(taken).toBe(true);
  await app.settled();
  await expect(page.locator("#crash-dialog")).toBeHidden();
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
});

test("offline after the page has loaded: runs, the other view and Export need no network", async ({ app, page, context }) => {
  await app.open();
  await context.setOffline(true);
  await app.mode("advanced");
  await app.type("AIR_GAP_MM", "1.5");
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  expect((await app.download("#btn-download")).name).toMatch(/^Coil_.*\.zip$/);
  expect((await app.download("#btn-export")).name).toBe("Parameter_Files.zip");
  await page.click("#btn-check");
  await app.settled();
  expect(await app.counts()).toContain("Check Passed");
  await context.setOffline(false);
});

test("a reload in the middle of a run starts the page again, with the design of its link", async ({ app, page }) => {
  await app.open("#single=eyJCb2FyZCI6eyJBSVJfR0FQX01NIjoxLjV9fQ");            // {"Board":{"AIR_GAP_MM":1.5}}
  await page.click("#btn-generate");
  await expect(page.locator("#run-card")).toBeVisible();
  await page.reload();
  await expect(page.locator("#run-title")).toHaveText("Loading");
  await app.settled();
  await expect(app.findings("error")).toHaveCount(0);
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("a value that makes the generator stop with an error of its own: the page says so, shows the details and works on", async ({ app, page }) => {
  test.setTimeout(400000);
  // the Dual generator works its layout out before it checks the sets: Loops = -1 in set 2 ends it with an IndexError
  const design = Buffer.from(JSON.stringify({ RX2: { LOOPS: -1 } })).toString("base64").replace(/=+$/, "");
  await app.open("#dual=" + design);
  expect(await app.counts()).toContain("Not Generated: the generator stopped");
  const row = app.findings("error").filter({ hasText: "The generator stopped with an error of its own" });
  await expect(row).toHaveCount(1);
  await row.locator("button", { hasText: "Show the details" }).click();
  await expect(page.locator("#crash-dialog")).toBeVisible();
  await expect(page.locator("#crash-details")).toContainText("IndexError");
  await expect(page.locator("#crash-report")).toHaveAttribute("href", /issues\/new\?title=/);
  await page.locator("#crash-dialog button[value=close]").click();
  await expect(page.locator("#crash-dialog")).toBeHidden();
  // the setting itself carries the generator's words for its value
  await app.mode("advanced");
  await app.tab("RX", 2);
  await expect(app.field("LOOPS").locator(".field-error")).toContainText("must be between 1 and 16");
  // put right, the generator runs again: Python has not been harmed
  await app.type("LOOPS", "4");
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  expect(await app.counts()).toContain("DualCoil_");
});

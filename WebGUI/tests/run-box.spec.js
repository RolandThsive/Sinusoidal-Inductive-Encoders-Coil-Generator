/* The box on the preview: what is loading, then the steps of a run, its time and Cancel. */
import { test, expect } from "./frame.js";

test("the box shows the loading, then each run's steps, and is gone when the board is there", async ({ app, page }) => {
  await app.open("", { settle: false });
  const box = page.locator("#canvas-wrap #run-card");
  await expect(box).toBeVisible();
  await expect(page.locator("#run-title")).toHaveText("Loading");
  await expect(page.locator("#btn-cancel")).toBeHidden();                  // loading cannot be cancelled
  await expect(page.locator("#run-title")).toHaveText("Generating", { timeout: 120000 });
  await expect(page.locator("#run-steps li").first()).toBeVisible();
  await expect(page.locator("#btn-cancel")).toBeVisible();
  await app.settled();
  await expect(box).toBeHidden();
  await expect(page.locator("#checks-list")).toBeVisible();

  await page.click("#btn-check");
  await expect(page.locator("#run-title")).toHaveText("Checking");
  await app.settled();
  await expect(box).toBeHidden();
});

test("Cancel in the box ends a run and the page works again", async ({ app, page }) => {
  await app.open();
  const before = await app.counts();
  await page.click("#btn-generate");
  await expect(page.locator("#run-card")).toBeVisible();
  await page.click("#btn-cancel");
  await expect(app.toast()).toHaveText("Cancelled");                       // at once: it is gone before a slow browser has its new Python
  await app.settled();
  await expect(page.locator("#run-card")).toBeHidden();
  expect(await app.counts()).toBe(before);                                 // the last board is still the one shown
  await expect(page.locator("#btn-download")).toBeEnabled();
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
});

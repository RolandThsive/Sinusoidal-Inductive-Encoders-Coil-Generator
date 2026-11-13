/* The generator menu beside the title: Single and Dual can be chosen; Arc and Linear are listed greyed out. */
import { test, expect } from "./frame.js";

test("the menu lists Single, Dual and, greyed out, Arc and Linear", async ({ app, page }) => {
  await app.open();
  await expect(page.locator("#gen-now")).toHaveText("Single");
  await expect(page.locator("#gen-list")).not.toHaveClass(/open/);
  await page.click("#gen-btn");
  await expect(page.locator("#gen-btn")).toHaveAttribute("aria-expanded", "true");
  const options = page.locator('#gen-list [role="option"]');
  await expect(options).toHaveText(["Single", "Dual", "Arc", "Linear"]);
  for (const name of ["Arc", "Linear"]) {
    const o = options.filter({ hasText: name });
    await expect(o).toBeDisabled();
    await expect(o).toHaveAttribute("aria-disabled", "true");
    await o.click({ force: true });                                  // a click on a greyed-out line does nothing
  }
  await expect(page.locator("#gen-btn")).toHaveAttribute("aria-expanded", "true");
  await expect(page.locator("#gen-now")).toHaveText("Single");
  await page.keyboard.press("Escape");
  await page.mouse.click(700, 500);                                  // a click elsewhere closes the menu
  await expect(page.locator("#gen-btn")).toHaveAttribute("aria-expanded", "false");
  expect(await app.state()).toBe("ready");
});

test("the menu works from the keyboard and skips the greyed-out lines", async ({ app, page }) => {
  await app.open();
  await page.focus("#gen-btn");
  await page.keyboard.press("ArrowDown");                            // opens, on the generator that is on
  await expect(page.locator('#gen-list [data-gen="single"]')).toBeFocused();
  await page.keyboard.press("ArrowDown");
  await expect(page.locator('#gen-list [data-gen="dual"]')).toBeFocused();
  await page.keyboard.press("ArrowDown");                            // Arc and Linear are passed over
  await expect(page.locator('#gen-list [data-gen="single"]')).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("#gen-btn")).toBeFocused();
  await expect(page.locator("#gen-btn")).toHaveAttribute("aria-expanded", "false");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("End");
  await page.keyboard.press("Enter");
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await expect(page.locator("#gen-btn")).toBeDisabled();             // no switching while the first Dual board is made
  await app.settled();
  await expect(page.locator("#gen-btn")).toBeEnabled();
});

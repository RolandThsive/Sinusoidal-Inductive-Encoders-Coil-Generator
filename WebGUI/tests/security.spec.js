/* security: the page's policy, where Python may come from, and what happens when the CDN fails. */
import { test, expect } from "./frame.js";
import { CDN } from "./site.mjs";

test("the page carries the policy the build wrote, and a full visit breaks none of it", async ({ app, page }) => {
  await app.open();
  const policy = await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content");
  expect(policy).toContain("default-src 'none'");
  expect(policy).toContain(`script-src 'self' ${CDN} 'wasm-unsafe-eval'`);
  expect(policy).toContain("style-src 'self'");
  expect(policy).toContain("object-src 'none'");
  expect(policy).toContain("base-uri 'none'");
  expect(policy).not.toMatch(/'unsafe-inline'|'unsafe-eval'|\*|data:/);
  expect(await page.locator("script:not([src])").count()).toBe(0);         // no script written into the page
  expect(await page.locator("style").count()).toBe(0);
  expect(await page.locator("[onclick], [onload], [onerror]").count()).toBe(0);
  // a walk through the page: every part is used once (the frame fails the test on any violation)
  await app.mode("advanced");
  await page.fill("#find", "via");
  await page.fill("#find", "");
  await page.click('#view-tabs [data-view="pictures"]');
  await expect(page.locator("#pictures img").first()).toBeVisible();
  await page.click("#btn-files");
  await expect(page.locator("#files-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.click("#btn-runtext");
  await expect(page.locator("#text-dialog")).toBeVisible();
  await page.keyboard.press("Escape");
});

test("a link cannot point the page at another copy of Python", async ({ app, page, cdn }) => {
  await app.open("?pyodide=https://example.com/pyodide/");
  expect(cdn.asked).toContain("pyodide.mjs");                                // the CDN of vendor.json was used
  expect(cdn.outside).toEqual([]);
  await expect(page.locator("#build-stamp")).toContainText("Python 3.14");
});

test("the CDN refuses the connection: Python comes from the site's own copy", async ({ app, page, cdn, problems }) => {
  cdn.mode = "blocked";
  problems.allow(/Failed to load resource|net::ERR_|NetworkError|could not be loaded|Load failed|Loading module from|error loading dynamically imported module/i);
  await app.open();
  await expect(page.locator("#build-stamp")).toContainText("this site's own copy");
  await expect(app.findings("error")).toHaveCount(0);
  await expect(page.locator("#btn-download")).toBeEnabled();
  expect(cdn.asked).toContain("pyodide.mjs");
});

test("the CDN never answers: after 15 s Python comes from the site's own copy", async ({ app, page, cdn }) => {
  cdn.mode = "stalled";
  const t0 = Date.now();
  await app.open();
  expect(Date.now() - t0).toBeGreaterThan(15000);
  await expect(page.locator("#build-stamp")).toContainText("this site's own copy");
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("the CDN sends a numpy that is not the one Pyodide names: it is refused, the site's own copy is used", async ({ app, page, cdn, problems }) => {
  const wheel = Object.keys((await import("./site.mjs")).LOCK.files).find((n) => n.endsWith(".whl"));
  cdn.change[wheel] = (bytes) => { const b = Buffer.from(bytes); b[b.length - 40] ^= 0xff; return b; };
  problems.allow(/integrity|digest|sha-?256|Failed to load|Failed to fetch|numpy/i);
  await app.open();
  await expect(page.locator("#build-stamp")).toContainText("this site's own copy");
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("no source of Python answers: the page says so and offers a report", async ({ app, page, cdn, context, problems }) => {
  cdn.mode = "blocked";
  await context.route("**/vendor/pyodide/**", (route) => route.abort("connectionrefused"));
  problems.allow(/Failed to load resource|net::ERR_|NetworkError|could not be loaded|Load failed|Loading module from|error loading dynamically imported module/i);
  await app.open("", { settle: false });
  await expect(page.locator("#crash-dialog")).toBeVisible({ timeout: 60000 });
  await expect(page.locator("#crash-text")).toContainText("Python could not be loaded");
  expect(await app.state()).toBe("failed");
  await expect(page.locator("#btn-generate")).toBeDisabled();
  await expect(page.locator("#btn-generate")).toHaveText("Python Did Not Start");
  await expect(page.locator("#run-card")).toBeHidden();
  const report = await page.locator("#crash-report").getAttribute("href");
  expect(report).toMatch(/^https:\/\/github\.com\/RolandThsive\/Sinusoidal-Inductive-Encoders-Coil-Generator\/issues\/new\?/);
});

/* smoke: the page opens, makes a board with each generator, and hands the files over. */
import { test, expect } from "./frame.js";
import { unzip } from "./zip.mjs";
import { CDN, LOCK } from "./site.mjs";

test("Single: the page opens, makes its first board by itself, and the zip downloads", async ({ app, page, cdn }) => {
  await app.open();
  await expect(page).toHaveTitle("Sinusoidal Inductive Encoder Coil Generator");
  await expect(page.locator("#btn-generate")).toHaveText("Generate");
  await expect(page.locator("#build-stamp")).toContainText(`Python 3.14`);
  await expect(page.locator("#build-stamp")).not.toContainText("own copy");          // Python came from the CDN
  expect(cdn.asked).toContain("pyodide.mjs");
  await expect(app.findings("error")).toHaveCount(0);
  expect(await app.counts()).toMatch(/Coil_/);
  await expect(page.locator("#btn-download")).toBeEnabled();

  const zip = await app.download("#btn-download");
  expect(zip.name).toMatch(/^Coil_.*\.zip$/);
  const files = unzip(zip.bytes);
  const names = Object.keys(files).map((n) => n.split("/").pop()).sort();
  expect(names).toEqual(expect.arrayContaining(["Stator.kicad_pcb", "Rotor.kicad_pcb", "Stator.kicad_pro", "Rotor.kicad_pro", "Parameters.txt"]));
  const stator = Object.entries(files).find(([n]) => n.endsWith("Stator.kicad_pcb"))[1].toString("utf8");
  expect(stator.startsWith("(kicad_pcb")).toBe(true);

  const one = await app.download("#btn-dl-stator");
  expect(one.name).toMatch(/Stator\.kicad_pcb$/);
  expect(one.bytes.toString("utf8")).toBe(stator);

  // the numbers under the controls: the range and the generator's electrical estimate, with unit signs only
  const results = page.locator("#results");
  await expect(results.locator("dt")).toHaveText(["Range", "R", "L", "C", "f", "Board"]);
  await expect(results).toContainText("360°");
  await expect(results).toContainText(/R\s*[\d.]+ Ω/);
  await expect(results).toContainText(/L\s*[\d.]+ µH/);
  await expect(results).not.toContainText(/IPS|RX Band|TX Ring|with the rotor/);
  expect(CDN).toContain(LOCK.version);
});

test("Dual: the switch makes the Dual generator's first board, and the zip downloads", async ({ app, page }) => {
  await app.open();
  await app.generator("dual");
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await expect(page.locator('#gen-list [data-gen="dual"]')).toHaveAttribute("aria-selected", "true");
  await expect(app.findings("error")).toHaveCount(0);
  expect(await app.counts()).toMatch(/DualCoil_/);
  await expect(page.locator("#preview")).not.toContainText("built copper");       // no line of text above the board
  const results = page.locator("#results");
  await expect(results.locator("thead th")).toHaveText(["Set 1 · Inner", "Set 2 · Outer"]);
  await expect(results.locator("tbody th")).toHaveText(["Range", "R", "L", "C", "f", "Board"]);
  await expect(results.locator("tbody tr").first().locator("td:not(.room)")).toHaveText(["360°", "22.5°"]);
  await expect(results).not.toContainText(/IPS|RX Band|TX Ring|with the rotor/);
  await expect(page.locator("#btn-files")).toHaveText("All Files");
  const zip = await app.download("#btn-download");
  const names = Object.keys(unzip(zip.bytes)).map((n) => n.split("/").pop());
  expect(names).toEqual(expect.arrayContaining(["Stator.kicad_pcb", "Rotor.kicad_pcb", "Parameters.txt"]));
  // Single is still there as it was left
  await app.generator("single");
  await expect(page.locator("#btn-download")).toBeEnabled();
  expect(await app.state()).toBe("ready");
});

for (const name of ["privacy.html", "licenses.html"]) {
  test(`${name} opens, with no script on it`, async ({ page }) => {
    await page.goto("./" + name);
    await expect(page.locator("h1")).toBeVisible();
    expect(await page.locator("script").count()).toBe(0);
    expect(await page.locator('meta[http-equiv="Content-Security-Policy"]').getAttribute("content")).toContain("default-src 'none'");
    await page.click('a[href="./"]');
    await expect(page).toHaveTitle("Sinusoidal Inductive Encoder Coil Generator");
  });
}

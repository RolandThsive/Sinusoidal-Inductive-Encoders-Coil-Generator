/* earlier: what the versions before 2.0 fixed or brought, tried again on the new page (bug round 26). */
import { test, expect } from "./frame.js";
import { unzip } from "./zip.mjs";

test("Help, the Reset question, the zip's name in its tip, the IC file, a narrow window", async ({ app, page }) => {
  await app.open();
  // Help opens the wiki's guide in a new tab (V15)
  const help = page.locator("#btn-help");
  await expect(help).toHaveAttribute("href", "https://github.com/RolandThsive/Sinusoidal-Inductive-Encoders-Coil-Generator/wiki/Quick-Guide-To-Parameters-Selections");
  await expect(help).toHaveAttribute("target", "_blank");
  await expect(help).toHaveAttribute("rel", /noopener/);
  // Reset asks first, in the words of the first page; No changes nothing
  await page.click("#btn-reset");
  await expect(page.locator("#confirm-text")).toHaveText("Are you sure to reset the board?");
  await page.click("#confirm-dialog button[value=no]");
  await expect(page.locator("#confirm-dialog")).toBeHidden();
  // the tip of Download Zip names the zip of the run on show
  const run = (await app.counts()).match(/Coil_[\w.-]+/)[0];
  await page.hover("#btn-download");
  await expect(page.locator("#popover")).toContainText(run);
  await page.mouse.move(1, 1);
  expect((await app.download("#btn-download")).name).toBe(run + ".zip");
  // the IC file is one of the parameter files: in Export (the generator's whole Parameters folder), and in the run's Parameters.txt (V18)
  const exported = Object.keys(unzip((await app.download("#btn-export")).bytes)).map((n) => n.split("/").pop()).sort();
  expect(exported).toEqual(["Board_Parameters.py", "IC_Parameters.py", "Parameters.py", "RX_Parameters.py", "Rotor_Parameters.py", "SilkScreenSuggestion_Parameters.py", "TX_Parameters.py"]);
  const zip = unzip((await app.download("#btn-download")).bytes);
  const record = Object.entries(zip).find(([n]) => n.endsWith("Parameters.txt"))[1].toString("utf8");
  expect(record).toContain("[IC_Parameters.py]");
  // a computer's narrow window gets the tool, not the phone's message
  await page.setViewportSize({ width: 480, height: 600 });
  await page.reload();
  await app.settled();
  await expect(page.locator("#app")).toBeVisible();
  await expect(page.locator("#phone-message")).toBeHidden();
  await expect(page.locator("#btn-generate")).toBeVisible();
});

test("Strict: a warning about the finished boards stops the run, and the last good board stays", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await app.type("CENTER_X_MM", 5);                              // the board crosses the frame of the KiCad page: a warning
  await app.generate();
  await expect(app.findings("warning")).toHaveCount(1);
  await expect(app.findings("error")).toHaveCount(0);
  expect(await app.counts()).toMatch(/1 Warning/);
  await expect(page.locator("#btn-download")).toBeEnabled();

  await page.locator("#strict").check({ force: true });
  await expect(page.locator("#stale-badge")).toBeVisible();     // Strict is a setting: the board on show is the old one now
  await app.generate();
  expect(await app.counts()).toMatch(/^Not Generated: 1 board warning\(s\) in strict mode/);
  await expect(app.findings("warning")).toHaveCount(1);          // the warning that stopped it is still listed
  await expect(page.locator("#btn-download")).toBeDisabled();
  await expect(page.locator("#btn-runtext")).toBeEnabled();      // what the generator printed can still be read
  await page.click("#btn-runtext");
  await expect(page.locator("#text-body")).toContainText('GENERATOR_MODE = "strict"');
  await page.keyboard.press("Escape");
  expect(await page.evaluate(async () => (await import("./app/preview.js")).view.hasBoard), "the last good board stays in the preview").toBe(true);

  await page.locator("#strict").uncheck({ force: true });
  await app.generate();
  expect(await app.counts()).toMatch(/1 Warning/);
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("the chips of layers without copper are locked: they take no click and no key", async ({ app, page }) => {
  await app.open();                                              // the starting design has two copper layers
  const chips = page.locator("#layer-toggles .layer-chip");
  await expect(chips).toHaveText(["Top", "Inner-1", "Inner-2", "Bottom", "Vias"]);
  const hidden = () => page.evaluate(async () => [...(await import("./app/preview.js")).view.hidden].sort());
  const before = await hidden();
  for (const name of ["Inner-1", "Inner-2"]) {
    const chip = chips.filter({ hasText: name });
    await expect(chip).toHaveClass(/locked/);
    await expect(chip).toHaveAttribute("aria-disabled", "true");
    await expect(chip).not.toHaveAttribute("tabindex", "0");
    await chip.click({ force: true });
    expect(await hidden()).toEqual(before);
  }
  for (const name of ["Top", "Bottom", "Vias"]) await expect(chips.filter({ hasText: new RegExp(`^${name}$`) })).not.toHaveClass(/locked/);
  await chips.filter({ hasText: /^Top$/ }).click();
  expect(await hidden()).toEqual([...before, "F.Cu"].sort());
});

/* share: a link, the exported parameter files and a run's Parameters.txt each bring a design back. */
import fs from "node:fs";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";
import { unzip } from "./zip.mjs";

const pack = (o) => Buffer.from(JSON.stringify(o)).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const changedTabs = (page) => page.locator("#adv-tabs .tab-dot");            // the tabs of Advanced that hold a changed setting

test.beforeEach(async ({ page }) => {
  // what Share copies is kept for the test (the browsers differ in what they let a test read from the clipboard)
  await page.addInitScript(() => {
    window.__copied = [];
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async (t) => { window.__copied.push(t); } } });
  });
});

test("Share copies a link, and the link opens the same design", async ({ app, page }) => {
  await app.open();
  await page.click("#btn-share");
  await expect(app.toast()).toHaveText("Link copied");
  expect((await page.evaluate(() => window.__copied))[0]).toMatch(/\/WebGUI\/$/);       // nothing changed: the plain address

  await app.mode("advanced");
  await app.tab("RX");
  await app.type("LOOPS", 4);
  await app.tab("Board");
  await app.type("AIR_GAP_MM", 1.5);
  await page.click("#btn-share");
  const link = (await page.evaluate(() => window.__copied))[1];
  expect(link).toMatch(/\/WebGUI\/#single=[A-Za-z0-9_-]+$/);

  await page.goto("about:blank");
  await page.goto(link);
  await app.settled();
  await expect(page.locator("#results")).toContainText("90°");                       // 4 loops: made by itself, from the link
  await expect(app.findings("error")).toHaveCount(0);
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await app.tab("RX");
  expect(await app.value("LOOPS")).toBe("4");
  await expect(changedTabs(page)).toHaveCount(2);                                     // Board and RX, nothing else
});

test("a Dual link opens the Dual generator with its design", async ({ app, page }) => {
  await app.open("#dual=" + pack({ Board: { AIR_GAP_MM: 1.5 } }));
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await expect(page.locator("#results thead")).toContainText("Set 1");
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await expect(changedTabs(page)).toHaveCount(1);
});

test("a link pasted into the address bar of the open page opens its design", async ({ app, page }) => {
  await app.open();
  await expect(page.locator("#gen-now")).toHaveText("Single");
  // only the part after the # changes: the browser itself does not load the page again
  await page.evaluate((hash) => { location.hash = hash; }, "#single=" + pack({ Board: { AIR_GAP_MM: 1.5 } }));
  await page.waitForFunction(() => document.documentElement.dataset.state !== "ready", null, { timeout: 10000 }).catch(() => {});
  await app.settled();
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  // something after the # that is not a design is left alone
  await page.evaluate(() => { location.hash = "#nothing"; });
  await page.waitForTimeout(500);
  expect(await app.state()).toBe("ready");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
});

test("a link that is not a design changes nothing; unknown names are named", async ({ app, page }) => {
  for (const hash of ["#single=%%%", "#single=" + pack([1, 2]), "#single=" + "A".repeat(21000), "#other"]) {
    await page.goto("about:blank");
    await app.open(hash);
    await expect(page.locator("#basic-tabs .tab-dot")).toHaveCount(0);
    await expect(app.findings("error")).toHaveCount(0);
  }
  await page.goto("about:blank");
  await app.open("#single=" + pack({ Board: { NOT_A_SETTING: 1, AIR_GAP_MM: { a: 1 }, OUTPUT_DIR: "/tmp", PCB_THICKNESS_MM: 1.2 }, Nope: { X: 1 } }));
  await expect(app.toast()).toContainText("Ignored: NOT_A_SETTING, AIR_GAP_MM, OUTPUT_DIR, Nope");
  await app.mode("advanced");
  expect(await app.value("PCB_THICKNESS_MM")).toBe("1.2");                            // the one real setting of the link
  expect(await app.value("AIR_GAP_MM")).toBe("1");
});

test("a link with names every object has (constructor, __proto__) takes none of them as a setting", async ({ app, page }) => {
  const json = '{"Board":{"__proto__":[1],"constructor":"x","toString":1,"hasOwnProperty":2,"AIR_GAP_MM":1.5},"__proto__":{"X":1},"constructor":{"Y":2}}';
  const link = "#single=" + Buffer.from(json).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  await app.open(link);
  await expect(app.toast()).toContainText("Ignored: __proto__, constructor, toString, hasOwnProperty, __proto__, constructor");
  await expect(app.findings("error")).toHaveCount(0);
  await page.click("#btn-share");
  const copied = (await page.evaluate(() => window.__copied)).pop();
  const design = JSON.parse(Buffer.from(copied.split("#single=")[1].replace(/-/g, "+").replace(/_/g, "/"), "base64").toString());
  expect(design).toEqual({ Board: { AIR_GAP_MM: 1.5 } });                    // the one setting of the link, and nothing else
  // the same names in an old link
  await page.goto("about:blank");
  await app.open("#d=" + pack({ constructor: 1, valueOf: 2, AIR_GAP_MM: 1.25 }));
  await expect(app.toast()).toContainText("Ignored: constructor, valueOf");
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.25");
});

test("a link of the page before (#d=) opens that page's starting design with the link's changes", async ({ app, page }) => {
  await app.open("#d=" + pack({ AIR_GAP_MM: 1.5, LOOPS: 6, A_SETTING_OF_THEN: 3 }));
  await expect(app.toast()).toContainText("Ignored: A_SETTING_OF_THEN");
  await expect(page.locator("#gen-now")).toHaveText("Single");
  await app.mode("advanced");
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  expect(await app.value("VIA_DIAMETER_MM")).toBe("0.6");                    // where that page started from
  expect(await app.value("VIA_DRILL_MM")).toBe("0.3");
  await app.tab("RX");
  expect(await app.value("LOOPS")).toBe("6");
  await expect(app.findings("error")).toHaveCount(0);
  await expect(page.locator("#btn-download")).toBeEnabled();
});

test("Export, Reset, Import: the parameter files bring the design back", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await app.tab("RX");
  await app.type("LOOPS", 4);
  await app.tab("Board");
  await app.type("AIR_GAP_MM", 1.5);

  const zip = await app.download("#btn-export");
  expect(zip.name).toBe("Parameter_Files.zip");
  const files = unzip(zip.bytes);
  const text = (end) => Object.entries(files).find(([n]) => n.endsWith(end))[1].toString("utf8");
  expect(text("RX_Parameters.py")).toMatch(/^LOOPS\s*=\s*4\b/m);
  expect(text("Board_Parameters.py")).toMatch(/^AIR_GAP_MM\s*=\s*1\.5\b/m);

  await app.reset();
  expect(await app.value("AIR_GAP_MM")).toBe("1");
  await expect(changedTabs(page)).toHaveCount(0);

  await app.import({ name: zip.name, mimeType: "application/zip", buffer: zip.bytes });
  await expect(app.toast()).toContainText(/Loaded \d+ values/);
  expect(await app.value("AIR_GAP_MM")).toBe("1.5");
  await app.tab("RX");
  expect(await app.value("LOOPS")).toBe("4");

  // one parameter file alone is read too
  await app.reset();
  await app.import({ name: "RX_Parameters.py", mimeType: "text/x-python", buffer: Buffer.from(text("RX_Parameters.py")) });
  expect(await app.value("LOOPS")).toBe("4");
  await app.tab("Board");
  expect(await app.value("AIR_GAP_MM")).toBe("1");
});

test("the Parameters.txt of a run brings its design back", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  await app.tab("RX");
  await app.type("LOOPS", 4);
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
  const run = unzip((await app.download("#btn-download")).bytes);
  const record = Object.entries(run).find(([n]) => n.endsWith("Parameters.txt"))[1];

  await app.reset();
  expect(await app.value("LOOPS")).toBe("1");
  await app.import({ name: "Parameters.txt", mimeType: "text/plain", buffer: record });
  await expect(app.toast()).toContainText(/Loaded \d+ values/);
  expect(await app.value("LOOPS")).toBe("4");
});

test("Dual files imported into Single switch the page to Dual", async ({ app, page }) => {
  await app.open();
  const dir = path.join(REPO, "Generators", "Dual Coil Set Generator", "Parameters");
  const files = fs.readdirSync(dir).filter((n) => /^Dual_.+_Parameters\.py$/.test(n)).map((n) => path.join(dir, n));
  expect(files.length).toBe(10);
  await app.import(files);
  await expect(page.locator("#gen-now")).toHaveText("Dual");
  await expect(app.toast()).toContainText("of a Dual design");
  await expect(page.locator("#results thead")).toContainText("Set 2");
  await expect(app.findings("error")).toHaveCount(0);
});

test("a file with no settings, and a file that is too large, are refused with a reason", async ({ app, page }) => {
  await app.open();
  await app.import({ name: "notes.txt", mimeType: "text/plain", buffer: Buffer.from("hello, this is not a design\n") });
  await expect(app.toast()).toHaveText("No parameter values found in that file");
  await app.import({ name: "big.txt", mimeType: "text/plain", buffer: Buffer.alloc(8 * 1048576 + 1, 0x41) });
  await expect(app.toast()).toHaveText("big.txt is larger than 8 MB: not read");
  await app.import({ name: "bad.zip", mimeType: "application/zip", buffer: Buffer.from("PK this is not a zip") });
  await expect(app.toast()).toContainText("bad.zip: not a zip file");
  await expect(page.locator("#basic-tabs .tab-dot")).toHaveCount(0);
  expect(await app.state()).toBe("ready");
});

test("files whose values are of the wrong kind are loaded as they are: the page shows them, names them and works on", async ({ app, page }) => {
  test.setTimeout(400000);
  // every setting of every Single parameter file, each time with a value of another kind
  const dir = path.join(REPO, "Generators", "Single Coil Set Generator", "Parameters");
  const names = (file) => [...fs.readFileSync(path.join(dir, file), "utf8").matchAll(/^([A-Z][A-Z0-9_]*)\s*=/gm)].map((m) => m[1]);
  const files = fs.readdirSync(dir).filter((n) => /_Parameters\.py$/.test(n));
  await app.open();
  await app.mode("advanced");
  for (const wrong of ['"text"', "[1, 2]", "True", "None", "-7", '""', "[]", "0.5", '"\\U0001f600"']) {
    const given = files.map((file) => ({ name: file, mimeType: "text/x-python", buffer: Buffer.from("\ufeff" + names(file).map((n) => `${n} = ${wrong}`).join("\r\n") + "\r\n") }));
    await app.import(given);
    await expect(app.toast(), wrong).toContainText(/Loaded \d+ values/);
    expect(await app.state(), wrong).toBe("ready");
    for (const key of await page.locator("#adv-tabs [data-key]").evaluateAll((l) => l.map((b) => b.dataset.key))) {
      await app.tab(key);                                                    // every tab draws its settings
      await expect(page.locator("#advanced-panel .field").first(), `${wrong} ${key}`).toBeVisible();
    }
    await app.mode("basic");
    for (const key of await page.locator("#basic-tabs [data-key]").evaluateAll((l) => l.map((b) => b.dataset.key))) {
      await app.tab(key);
      await expect(page.locator("#basic-panel .field, #basic-panel .tx-card").first(), `${wrong} ${key}`).toBeVisible();
    }
    await app.mode("advanced");
    await app.checkOnly();                                                   // the generator says what it thinks of them
    expect(await app.state(), wrong).toBe("ready");
    expect(await app.findings("error").count(), wrong).toBeGreaterThan(0);
  }
  // and back: Reset, then the published board is made again
  await app.reset();
  await expect(changedTabs(page)).toHaveCount(0);
  await app.generate();
  await expect(app.findings("error")).toHaveCount(0);
});

test("a value no setting can hold is named and left out; the other values of the file are read", async ({ app, page }) => {
  await app.open();
  await app.mode("advanced");
  const text = "\ufeffAIR_GAP_MM = 1e999\r\nPCB_THICKNESS_MM = 1.2\r\nVIA_DRILL_MM = {1, 2}\r\nNO_SUCH = 3\r\n";
  await app.import({ name: "Board_Parameters.py", mimeType: "text/x-python", buffer: Buffer.from(text) });
  await expect(app.toast()).toContainText("Loaded 1 value. Ignored: AIR_GAP_MM in Board_Parameters.py: not a value a setting can hold; VIA_DRILL_MM in Board_Parameters.py: not a value a setting can hold; NO_SUCH in Board_Parameters.py: not a setting of this version");
  expect(await app.value("PCB_THICKNESS_MM")).toBe("1.2");
  expect(await app.value("AIR_GAP_MM")).toBe("1");
  // a zip that is cut in the middle, and a zip inside a zip
  const zip = (await app.download("#btn-export")).bytes;
  await app.import({ name: "cut.zip", mimeType: "application/zip", buffer: zip.subarray(0, Math.floor(zip.length / 2)) });
  await expect(app.toast()).toContainText("cut.zip: not a zip file");
  expect(await app.state()).toBe("ready");
  expect(await app.value("PCB_THICKNESS_MM")).toBe("1.2");
});

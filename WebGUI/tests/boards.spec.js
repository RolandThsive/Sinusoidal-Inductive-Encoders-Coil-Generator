/* boards: reference boards of the generators' own regression suites (regression/), made in the browser from the
   board's parameter files and compared with the reference files the desktop generator wrote.  The comparison is the
   regression suite's own: numbers within 1e-5, everything else exactly.  A few boards per generator run here on
   every browser.  Every board of both suites (bug round 3, about an hour):

       BOARDS=all npx playwright test boards --project=chromium            (inside WebGUI/)
       BOARDS=all BOARDS_SUITE=dual npx playwright test boards              (one suite only)

   With BOARDS=all the two KiCad project files of the zip are compared as well, character for character. */
import fs from "node:fs";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";
import { differences } from "./compare.mjs";
import { unzip } from "./zip.mjs";

const ALL = process.env.BOARDS === "all";

const SUITES = {
  single: { folder: "SingleCoilSetGenerator_regression", boards: ["Board001", "Board004", "Board005"] },
  dual: { folder: "DualCoilSetGenerator_regression", boards: ["Board001"] },
};

function boardFolder(suite, id) {
  const top = path.join(REPO, "regression", SUITES[suite].folder);
  const name = fs.readdirSync(top).find((n) => n.startsWith(id + "-"));
  if (!name) throw new Error(`${id} is not in ${top}`);
  return path.join(top, name);
}

function everyBoard(suite) {
  return fs.readdirSync(path.join(REPO, "regression", SUITES[suite].folder)).filter((n) => /^Board\d+-/.test(n)).sort().map((n) => n.split("-")[0]);
}

for (const [suite, { boards }] of Object.entries(SUITES)) {
  if (ALL && process.env.BOARDS_SUITE && process.env.BOARDS_SUITE !== suite) continue;
  for (const id of ALL ? everyBoard(suite) : boards) {
    const folder = boardFolder(suite, id);
    test(`${suite} ${path.basename(folder)}: the browser makes the reference board`, async ({ app, page }) => {
      if (ALL) test.setTimeout(1500000);                            // a board of 16 loops takes minutes in a browser that shares its computer
      await app.open();
      const files = fs.readdirSync(folder).filter((n) => n.endsWith("_Parameters.py")).map((n) => path.join(folder, n));
      await page.setInputFiles("#import-file", files);              // a Dual board's files switch the page to Dual
      await page.waitForFunction(() => document.documentElement.dataset.state !== "ready", null, { timeout: 5000 }).catch(() => {});
      await app.settled(ALL ? 600000 : undefined);
      await page.click("#btn-generate");
      await app.settled(ALL ? 1200000 : undefined);
      await expect(app.findings("error")).toHaveCount(0);
      for (const [part, button] of [["Stator", "#btn-dl-stator"], ["Rotor", "#btn-dl-rotor"]]) {
        const made = await app.download(button);
        const reference = fs.readFileSync(path.join(folder, `${part}.kicad_pcb`), "utf8");
        expect(differences(reference, made.bytes.toString("utf8")), `${part}.kicad_pcb against ${path.basename(folder)}`).toEqual([]);
      }
      if (!ALL) return;
      const zip = unzip((await app.download("#btn-download")).bytes);
      for (const name of ["Stator.kicad_pro", "Rotor.kicad_pro"]) {
        const made = Object.entries(zip).find(([n]) => n.split("/").pop() === name);
        expect(made, `${name} is in the zip`).toBeTruthy();
        expect(made[1].toString("utf8").replace(/\r\n/g, "\n"), `${name} against ${path.basename(folder)}`).toBe(fs.readFileSync(path.join(folder, name), "utf8").replace(/\r\n/g, "\n"));
      }
    });
  }
}

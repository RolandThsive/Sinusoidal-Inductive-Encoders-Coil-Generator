/* boards: reference boards of the generators' own regression suites (regression/), made in the browser from the
   board's parameter files and compared with the reference files the desktop generator wrote.  The comparison is the
   regression suite's own: numbers within 1e-5, everything else exactly.  A few boards per generator run here on
   every browser; bug round 3 runs all of them once. */
import fs from "node:fs";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";
import { differences } from "./compare.mjs";

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

for (const [suite, { boards }] of Object.entries(SUITES)) {
  for (const id of boards) {
    const folder = boardFolder(suite, id);
    test(`${suite} ${path.basename(folder)}: the browser makes the reference board`, async ({ app }) => {
      await app.open();
      const files = fs.readdirSync(folder).filter((n) => n.endsWith("_Parameters.py")).map((n) => path.join(folder, n));
      await app.import(files);                                      // a Dual board's files switch the page to Dual
      await app.generate();
      await expect(app.findings("error")).toHaveCount(0);
      for (const [part, button] of [["Stator", "#btn-dl-stator"], ["Rotor", "#btn-dl-rotor"]]) {
        const made = await app.download(button);
        const reference = fs.readFileSync(path.join(folder, `${part}.kicad_pcb`), "utf8");
        expect(differences(reference, made.bytes.toString("utf8")), `${part}.kicad_pcb against ${path.basename(folder)}`).toEqual([]);
      }
    });
  }
}

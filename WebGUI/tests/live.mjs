/* live.mjs - one look at the published page, after a deploy:

       node WebGUI/tests/live.mjs <address of the page> [<commit that was built>]

   The address must serve the build of that commit (version.json; a deploy takes a moment, so this waits up to three
   minutes for it), the page must start Python from the real CDN and make its first board, with no error on the way.
   Exit code 0 when all of that held, 1 otherwise. */
import { chromium } from "@playwright/test";

const [url, commit] = process.argv.slice(2);
if (!url || !/^https?:\/\//.test(url)) { console.error("usage: node live.mjs <address of the page> [<commit>]"); process.exit(1); }
const page_url = url.endsWith("/") ? url : url + "/";

async function version() {
  const r = await fetch(page_url + "version.json?t=" + Date.now(), { cache: "no-store" });
  if (!r.ok) throw new Error(`version.json: HTTP ${r.status}`);
  return r.json();
}

let built = null;
for (let i = 0; i < 36; i++) {
  try { built = await version(); } catch (e) { built = { error: e.message }; }
  if (!commit || built.commit === commit) break;
  await new Promise((done) => setTimeout(done, 5000));
}
if (commit && built.commit !== commit) {
  console.error(`${page_url} does not serve commit ${commit}: version.json says ${JSON.stringify(built)}`);
  process.exit(1);
}
console.log(`${page_url} serves commit ${built.commit}, built ${built.built}, Pyodide ${built.pyodide && built.pyodide.version}`);

const browser = await chromium.launch(process.env.WEBGUI_CHROMIUM ? { executablePath: process.env.WEBGUI_CHROMIUM } : {});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const problems = [];
page.on("console", (m) => { if (m.type() === "error") problems.push("console error: " + m.text()); });
page.on("pageerror", (e) => problems.push("page error: " + e.message));
let ok = false;
try {
  await page.goto(page_url);
  await page.waitForFunction(() => ["ready", "failed"].includes(document.documentElement.dataset.state), null, { timeout: 180000 });
  const state = await page.evaluate(() => document.documentElement.dataset.state);
  const counts = await page.locator("#counts").innerText();
  const stamp = await page.locator("#build-stamp").innerText();
  const errors = await page.locator("#checks-list .check.error").count();
  const download = await page.locator("#btn-download").isEnabled();
  console.log(`state: ${state}\nchecks: ${counts}\nstamp: ${stamp}`);
  if (state !== "ready") problems.push(`the page ended in the state "${state}"`);
  if (errors) problems.push(`${errors} error(s) in the checks of the first board`);
  if (!download) problems.push("Download Zip is not enabled after the first board");
  ok = problems.length === 0;
} catch (e) {
  problems.push(String(e.message || e));
}
await browser.close();
for (const p of problems) console.error(p);
console.log(ok ? "The live page works." : "The live page does NOT work.");
process.exit(ok ? 0 : 1);

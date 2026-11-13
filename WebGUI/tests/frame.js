/* frame.js - what every browser test starts from.

   cdn        a stand-in for the CDN: every request to the CDN folder of vendor.json is answered from the site's own
              checked copy of Pyodide, so no test needs the real CDN.  A test can break it: cdn.mode = "blocked"
              (connection refused), "stalled" (never answers), or cdn.change = {file name: (bytes) => other bytes}.
              cdn.asked lists the files the page asked the CDN for.
   problems   every console error or warning, page error and violation of the security policy fails the test, and so
              does any request to a server other than the site and the CDN.  problems.allow(/text/) lets a test
              expect one.
   app        the page, with the steps the tests repeat (open, settled, generator, mode, field, download ...).

   The page says what it is doing in <html data-state>: loading, busy, ready, failed (app/core.js). */
import { test as base, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { CDN, ORIGIN, VENDOR, REPO, typeOf } from "./site.mjs";

export { expect, REPO };

class App {
  constructor(page) { this.page = page; }

  /* Open the tool ("" or "?x=1#single=...") and wait until its first board is made. */
  async open(rest = "", { settle = true } = {}) {
    await this.page.goto("./" + rest);
    if (settle) await this.settled();
  }
  /* Wait until nothing is under way any more (a run, a switch, an import, the checks of a typed value). */
  async settled(timeout = 200000) {
    await this.page.waitForFunction(() => document.documentElement.dataset.state === "ready", null, { timeout });
  }
  state() { return this.page.evaluate(() => document.documentElement.dataset.state); }

  /* Choose a generator in the menu beside the title. */
  async generator(gen) {
    await this.page.click("#gen-btn");
    await this.page.click(`#gen-list [data-gen="${gen}"]`);
    await this.settled();
  }
  async mode(mode) { await this.page.click(`#mode-switch [data-mode="${mode}"]`); await this.settled(); }
  async tab(key, set) {
    const view = await this.page.evaluate(() => (document.getElementById("advanced-panel").hidden ? "basic" : "adv"));
    await this.page.click(`#${view}-tabs [data-key="${key}"]`);
    if (set) await this.page.click(`#${view}-set [data-key="${set}"]`);
  }
  /* A setting's box on the page that is shown now. */
  field(name) {
    return this.page.locator(`#controls :is(#basic-panel, #advanced-panel):not([hidden]) .field[data-name="${name}"]`).first();
  }
  /* Type a value into a setting's text box (Advanced) and leave the box. */
  async type(name, text) {
    const box = this.field(name).locator("input[type=text]").first();
    await box.fill(String(text));
    await box.press("Tab");
    await this.settled();
  }
  async generate() { await this.page.click("#btn-generate"); await this.settled(); }
  async checkOnly() { await this.page.click("#btn-check"); await this.settled(); }
  counts() { return this.page.locator("#counts").innerText(); }
  findings(level) { return this.page.locator(`#checks-list .check${level ? "." + level : ""}`); }

  /* Click something that downloads a file.  Returns {name, bytes}. */
  async download(selector) {
    const [dl] = await Promise.all([this.page.waitForEvent("download"), this.page.click(selector)]);
    const file = await dl.path();
    return { name: dl.suggestedFilename(), bytes: fs.readFileSync(file) };
  }
  /* Import files given as paths or as {name, mimeType, buffer}. */
  async import(files) {
    await this.page.setInputFiles("#import-file", files);
    await this.page.waitForFunction(() => document.documentElement.dataset.state !== "ready", null, { timeout: 5000 }).catch(() => {});
    await this.settled();
  }
  toast() { return this.page.locator("#toast"); }
}

/* What each browser itself writes in the console when a file cannot be fetched (the tests that cut the CDN allow it). */
export const UNREACHED = /Failed to load resource|Failed to fetch|net::ERR_|NetworkError|Cross-Origin Request Blocked|could not be loaded|Load failed|Loading module from|error loading dynamically imported module/i;
/* Firefox's notice about the way Pyodide's own WebAssembly file was compiled: about that file, not about the page. */
const BROWSER_NOTICES = [/WebAssembly exception handling 'try' instruction is deprecated/];

export const test = base.extend({
  cdn: [async ({ context }, use) => {
    const cdn = { mode: "ok", change: {}, asked: [], outside: [] };
    await context.route((url) => url.href.startsWith(CDN), async (route) => {
      const name = decodeURIComponent(new URL(route.request().url()).pathname.split("/").pop());
      cdn.asked.push(name);
      if (cdn.mode === "blocked") { await route.abort("connectionrefused"); return; }
      if (cdn.mode === "stalled") return;                              // never answered
      let body;
      try { body = fs.readFileSync(path.join(VENDOR, name)); }
      catch (e) { await route.fulfill({ status: 404, body: "not found", headers: { "access-control-allow-origin": "*" } }); return; }
      if (cdn.change[name]) body = cdn.change[name](body);
      await route.fulfill({ status: 200, body, headers: { "content-type": typeOf(name), "access-control-allow-origin": "*",
        "cross-origin-resource-policy": "cross-origin" } });
    });
    // the page asks nothing of any other server
    await context.route((url) => /^https?:$/.test(url.protocol) && url.origin !== ORIGIN && !url.href.startsWith(CDN), async (route) => {
      cdn.outside.push(route.request().url());
      await route.abort("blockedbyclient");
    });
    await use(cdn);
  }, { auto: true }],

  problems: [async ({ page, cdn }, use) => {
    const found = [], allowed = [...BROWSER_NOTICES];
    page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") found.push(`console ${m.type()}: ${m.text()}`); });
    page.on("pageerror", (e) => found.push(`page error: ${e.message}`));
    await page.addInitScript(() => {
      window.__policy = [];
      document.addEventListener("securitypolicyviolation", (e) => window.__policy.push(`${e.violatedDirective} blocked ${e.blockedURI}`));
    });
    await use({ allow: (...re) => allowed.push(...re), found });
    let policy = [];
    try { policy = await page.evaluate(() => window.__policy || []); } catch (e) { /* the page is gone */ }
    const left = [...found, ...policy.map((p) => "policy: " + p)].filter((t) => !allowed.some((re) => re.test(t)));
    expect(left, "console errors and warnings, page errors, violations of the security policy").toEqual([]);
    expect(cdn.outside, "requests to a server that is neither the site nor the CDN").toEqual([]);
  }, { auto: true }],

  app: async ({ page }, use) => { await use(new App(page)); },
});

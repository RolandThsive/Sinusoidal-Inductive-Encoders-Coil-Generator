/* A diagnosis, not a test, to be removed: which axe rule ends a Firefox page on the CI runners when the help box of
   Generate is open.  Each try is a page of its own; a page that crashes is only written down. */
import { createRequire } from "node:module";
import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "./frame.js";

const axe = createRequire(import.meta.url)("axe-core");
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];
const RULES = axe.getRules(TAGS).map((r) => r.ruleId).filter((r) => r !== "label-title-only");

test("diagnosis: the axe rules that end a Firefox page with the box of Generate open", async ({ context, browserName }) => {
  test.skip(browserName !== "firefox" && !process.env.DIAG_ANY, "Firefox only");
  test.setTimeout(25 * 60000);
  const open = async (box) => {
    const p = await context.newPage();
    await p.goto("./");
    await p.waitForFunction(() => document.documentElement.dataset.state === "ready", null, { timeout: 200000 });
    await p.mouse.move(3, 3);
    if (box) {
      await p.locator(box).focus();
      await p.keyboard.press("Shift+Tab"); await p.keyboard.press("Tab");
      await expect(p.locator("#popover")).toBeVisible();
    }
    return p;
  };
  const tries = async (rules, { box = "#btn-generate", include = null } = {}) => {
    const p = await open(box);
    try {
      let b = new AxeBuilder({ page: p }).withRules(rules);
      if (include) b = b.include(include);
      await b.analyze();
      await p.close();
      return true;
    } catch (e) {
      await p.close().catch(() => {});
      return false;
    }
  };
  const say = (t) => console.log(`DIAG ${t}`);
  say(`axe ${axe.version}, ${RULES.length} rules`);
  say(`all rules, no box open: ${(await tries(RULES, { box: null })) ? "ok" : "crash"}`);
  say(`all rules, box of Generate open, only #popover: ${(await tries(RULES, { include: "#popover" })) ? "ok" : "crash"}`);
  say(`all rules, box of Generate open: ${(await tries(RULES)) ? "ok" : "crash"}`);
  const find = async (rules) => {
    if (await tries(rules)) return [];
    if (rules.length === 1) return rules;
    const half = Math.ceil(rules.length / 2);
    return [...(await find(rules.slice(0, half))), ...(await find(rules.slice(half)))];
  };
  const bad = await find(RULES);
  say(`rules that crash alone with the box of Generate open: ${bad.join(", ") || "none"}`);
  for (const r of bad) say(`${r} with the box of a setting open: ${(await tries([r], { box: '#basic-panel .field[data-name="INNER_EDGE_RADIUS_MM"] .info-dot' })) ? "ok" : "crash"}`);
});

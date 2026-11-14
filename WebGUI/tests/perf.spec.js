/* perf: the first view, measured the way Lighthouse measures it, on the built site the other tests use.

   Largest paint: when the largest thing of the first view (the title, a panel) is on screen.  The budget is 2.5 s.
   Layout shift: how much what is on screen jumps while the page fills in, from the first paint until the first
   board is made (Python has loaded, the settings are read, the checks and the results have come).  The budget is 0.1.
   Only Chromium reports the two numbers. */
import { test, expect } from "./frame.js";

test("the first view: the largest paint within 2.5 s, a layout shift of at most 0.1 until the first board is there", async ({ app, page, browserName }) => {
  test.skip(browserName !== "chromium", "only Chromium reports the largest paint and the layout shifts");
  await page.addInitScript(() => {
    window.__perf = { paint: 0, shift: 0, shifts: [] };
    new PerformanceObserver((list) => { for (const e of list.getEntries()) window.__perf.paint = e.startTime; })
      .observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) {
        if (e.hadRecentInput) continue;
        window.__perf.shift += e.value;
        window.__perf.shifts.push(`${Math.round(e.startTime)} ms: ${e.value.toFixed(4)} ${(e.sources || []).map((s) => s.node && (s.node.id || s.node.className || s.node.nodeName)).join(", ")}`);
      }
    }).observe({ type: "layout-shift", buffered: true });
  });
  await app.open();
  const perf = await page.evaluate(() => window.__perf);
  console.log(`largest paint ${Math.round(perf.paint)} ms, layout shift ${perf.shift.toFixed(4)}${perf.shifts.length ? "\n  " + perf.shifts.join("\n  ") : ""}`);
  expect(perf.paint, "the largest paint, in ms").toBeGreaterThan(0);
  expect(perf.paint, "the largest paint, in ms").toBeLessThanOrEqual(2500);
  expect(perf.shift, "the layout shift:\n" + perf.shifts.join("\n")).toBeLessThanOrEqual(0.1);
});

/* embed: the tool inside the blog page.  The code of BloggerPage.html is put into a page of another site, as Blogger
   does, with the tool's address changed to the test server's (bug round 23). */
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { test, expect, REPO } from "./frame.js";
import { PAGE } from "./site.mjs";

const LIVE = "https://rolandthsive.github.io/Sinusoidal-Inductive-Encoders-Coil-Generator/WebGUI/";
const pack = (o) => Buffer.from(JSON.stringify(o)).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

/* The blog: a small server of its own, on another port than the tool's, so the two are different origins as
   blogspot.com and github.io are. */
let server, BLOG, POST;
test.beforeAll(async () => {
  const code = fs.readFileSync(path.join(REPO, "WebGUI", "BloggerPage.html"), "utf8");
  expect(code.split(LIVE).length - 1, "the tool's address stands twice in BloggerPage.html: the font and APP_URL").toBe(2);
  const html = `<!doctype html><html><head><meta charset="utf-8"><title>The blog</title><link rel="icon" href="data:,"></head><body>
    <div class="theme"><h1 id="blog-header">The blog's own header</h1><div class="post">${code.replaceAll(LIVE, PAGE)}</div>
    <div id="blog-comments" style="height: 3000px">The blog's comments and footer, far longer than a window</div></div></body></html>`;
  // the code that is pasted in the blog until the owner pastes the new one: #d= links only, nothing on a hashchange
  const before = html.replace('/^#(single|dual|d)=/.test(location.hash)', 'location.hash.indexOf("#d=") === 0').replace(/\n\s*window\.addEventListener\("hashchange"[^\n]*/, "");
  expect(before.length, "the two lines the code of before 2.0 differs in are found").toBeLessThan(html.length - 100);
  expect(before).toContain('indexOf("#d=")');
  server = http.createServer((req, res) => {
    res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" });
    res.end(req.url.startsWith("/before/") ? before : html);
  });
  await new Promise((done) => server.listen(0, "localhost", done));
  BLOG = `http://localhost:${server.address().port}`;
  POST = `${BLOG}/p/inductive-encoder-sinusoidal-coil.html`;
});
test.afterAll(async () => { await new Promise((done) => server.close(done)); });

async function blog(page, problems) {
  await page.route(BLOG + "/**", (route) => route.continue());                 // the one other server a test may ask
  problems.allow(/Allow attribute will take precedence over 'allowfullscreen'/);   // Chromium's note on the frame's two attributes: both stay, for older browsers
  problems.allow(/Skipping unsupported feature name .clipboard-write./);           // Firefox's note on the frame's allow list: it copies without being allowed to
  await page.addInitScript(() => {
    window.__copied = [];
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText: async (t) => { window.__copied.push(t); } } });
  });
}
const tool = (page) => page.frames().find((f) => f.url().startsWith(PAGE));
async function settled(page) {
  await expect.poll(() => !!tool(page), { timeout: 30000 }).toBe(true);
  await tool(page).waitForFunction(() => document.documentElement.dataset.state === "ready", null, { timeout: 200000 });
  return tool(page);
}

test("in the blog page: the tool fills the window, the blog's parts are unseen, Share gives the blog's address", async ({ page, problems }) => {
  await blog(page, problems);
  await page.goto(POST);
  let frame = await settled(page);
  // the frame is the whole window; of the blog only the Back and Home buttons show
  const size = page.viewportSize();
  expect(await page.locator("#coilgen-frame").boundingBox()).toEqual({ x: 0, y: 0, width: size.width, height: size.height });
  await expect(page.locator("#blog-header")).toBeHidden();
  await expect(page.locator("#coilgen-back")).toBeVisible();
  await expect(page.locator("#coilgen-home")).toHaveAttribute("href", BLOG + "/");
  // the blog under it is long, and does not scroll
  await page.mouse.move(size.width - 40, 31); await page.mouse.wheel(0, 600);
  await page.waitForTimeout(300);
  expect(await page.evaluate(() => [scrollX, scrollY])).toEqual([0, 0]);
  // the tool knows it is framed: its own Back and Home are gone, and the top bar leaves room for the blog's
  expect(await frame.evaluate(() => document.documentElement.classList.contains("embedded"))).toBe(true);
  await expect(frame.locator("#nav-back")).toBeHidden();
  const [share, back] = [await frame.locator("#btn-share").boundingBox(), await page.locator("#coilgen-back").boundingBox()];
  expect(share.x + share.width, "Share ends left of the blog's Back button").toBeLessThan(back.x);
  await expect(frame.locator("#checks-list .check.error")).toHaveCount(0);

  // Share: the blog's address, and the design after the #
  await frame.click("#btn-share");
  await expect(frame.locator("#toast")).toHaveText("Link copied");
  expect(await frame.evaluate(() => window.__copied)).toEqual([POST]);
  await frame.click('#mode-switch [data-mode="advanced"]');
  await frame.click('#adv-tabs [data-key="RX"]');
  const loops = frame.locator('#advanced-panel .field[data-name="LOOPS"] input[type=text]').first();
  await loops.fill("4"); await loops.press("Tab");
  await frame.waitForFunction(() => document.documentElement.dataset.state === "ready");
  await frame.click("#btn-share");
  const link = (await frame.evaluate(() => window.__copied))[1];
  expect(link.startsWith(POST + "#single=")).toBe(true);

  // the link opens the blog page, which hands the design to the tool
  await page.goto("about:blank");
  await page.goto(link);
  frame = await settled(page);
  await expect(frame.locator("#results")).toContainText("90°");
  // a link pasted into the address bar while the page is open
  await page.evaluate((h) => { location.hash = h; }, "#single=" + pack({ RX: { LOOPS: 2 } }));
  await expect(frame.locator("#results")).toContainText("180°", { timeout: 200000 });
  frame = await settled(page);
  expect(await frame.evaluate(() => window.__policy), "violations of the security policy inside the frame").toEqual([]);
});

test("a phone opens the blog page: the message only, and nothing of the tool is fetched", async ({ page, cdn, problems }) => {
  await blog(page, problems);
  await page.addInitScript(() => {
    const real = window.matchMedia.bind(window);
    window.matchMedia = (q) => (q === "(pointer: coarse)" ? { matches: true } : q === "(any-pointer: fine)" ? { matches: false } : real(q));
  });
  const asked = [];
  page.on("request", (r) => { if (r.url().startsWith(PAGE)) asked.push(r.url()); });
  await page.goto(POST);
  await expect(page.locator("#coilgen-phone")).toBeVisible();
  await expect(page.locator("#coilgen-phone")).toContainText("needs a computer");
  await expect(page.locator("#coilgen-frame")).toBeHidden();
  expect(asked.filter((u) => !u.endsWith(".woff2"))).toEqual([]);

  // the tool itself, opened on a phone: its own message, and Python is never asked for
  await page.goto("./");
  await expect(page.locator("#phone-message")).toBeVisible();
  await expect(page.locator("#app")).toBeHidden();
  await page.waitForTimeout(1500);
  expect(await page.evaluate(() => document.documentElement.dataset.state)).toBe("phone");
  expect(cdn.asked).toEqual([]);
});

test("the blog code of before 2.0, still pasted in the blog: the tool runs in it and a new design link reaches it", async ({ page, problems }) => {
  await blog(page, problems);
  await page.goto(BLOG + "/before/p/inductive-encoder-sinusoidal-coil.html#single=" + pack({ RX: { LOOPS: 2 } }));
  const frame = await settled(page);
  await expect(frame.locator("#results")).toContainText("180°");
  await expect(frame.locator("#checks-list .check.error")).toHaveCount(0);
  await frame.click("#btn-share");
  expect((await frame.evaluate(() => window.__copied))[0].startsWith(BLOG + "/before/p/inductive-encoder-sinusoidal-coil.html#single=")).toBe(true);
});

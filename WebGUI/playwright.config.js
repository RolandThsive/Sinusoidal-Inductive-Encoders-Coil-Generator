/* The browser tests of the web tool:   cd WebGUI && npm ci && npx playwright install && npx playwright test

   tests/serve.mjs builds the site and serves it on localhost; tests/frame.js gives every test a stand-in for the CDN
   (the checked backup copy of Pyodide, so no test needs the real CDN) and fails a test on any console error, page
   error, policy violation or request to another server.  One test at a time per worker.  On a computer nothing is
   retried: a test that fails once has found something.  On a CI runner a failed test gets one more try (a runner's
   browser now and then crashes under Pyodide), and a test that passes only then is listed as flaky. */
import { defineConfig, devices } from "@playwright/test";
import { PAGE, PORT } from "./tests/site.mjs";

/* Chromium keeps its scrollbars, as a visitor's Chrome on Windows or Linux has them (Playwright would hide them): a
   list that scrolls is then 12 px narrower, which the layout tests are there to see. */
const chromium = { launchOptions: { ignoreDefaultArgs: ["--hide-scrollbars"], ...(process.env.WEBGUI_CHROMIUM ? { executablePath: process.env.WEBGUI_CHROMIUM } : {}) } };

export default defineConfig({
  testDir: "tests",
  testMatch: "*.spec.js",
  outputDir: "test-results",
  timeout: 360000,                                   // a Dual board test: about 45 s in Chromium, up to 3 minutes in Firefox on a CI runner
  expect: { timeout: 20000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,                    // a runner's browser now and then crashes under Pyodide: one more try there; a test that passes only then is listed as flaky
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [["github"], ["list"], ["html", { open: "never", outputFolder: "playwright-report" }]] : [["list"]],
  webServer: { command: "node tests/serve.mjs", port: PORT, reuseExistingServer: !process.env.CI, timeout: 180000 },
  // actionTimeout: a click or a hover that cannot be done is named after 30 s, not when the whole test runs out
  use: { baseURL: PAGE, viewport: { width: 1440, height: 900 }, trace: "off", screenshot: "only-on-failure", actionTimeout: 30000 },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 }, ...chromium } },
    { name: "firefox", use: { ...devices["Desktop Firefox"], viewport: { width: 1440, height: 900 } } },
    { name: "webkit", use: { ...devices["Desktop Safari"], viewport: { width: 1440, height: 900 } } },
  ],
});

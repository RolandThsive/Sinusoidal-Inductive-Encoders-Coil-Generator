/* The browser tests of the web tool:   cd WebGUI && npm ci && npx playwright install && npx playwright test

   tests/serve.mjs builds the site and serves it on localhost; tests/frame.js gives every test a stand-in for the CDN
   (the checked backup copy of Pyodide, so no test needs the real CDN) and fails a test on any console error, page
   error, policy violation or request to another server.  One test at a time per worker; nothing is retried: a test
   that fails once has found something. */
import { defineConfig, devices } from "@playwright/test";
import { PAGE, PORT } from "./tests/site.mjs";

const chromium = process.env.WEBGUI_CHROMIUM ? { launchOptions: { executablePath: process.env.WEBGUI_CHROMIUM } } : {};

export default defineConfig({
  testDir: "tests",
  testMatch: "*.spec.js",
  outputDir: "test-results",
  timeout: 240000,                                   // a Dual board alone takes about 30 s in a browser
  expect: { timeout: 20000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI ? [["github"], ["list"], ["html", { open: "never", outputFolder: "playwright-report" }]] : [["list"]],
  webServer: { command: "node tests/serve.mjs", port: PORT, reuseExistingServer: !process.env.CI, timeout: 180000 },
  use: { baseURL: PAGE, viewport: { width: 1440, height: 900 }, trace: "off", screenshot: "only-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 }, ...chromium } },
    { name: "firefox", use: { ...devices["Desktop Firefox"], viewport: { width: 1440, height: 900 } } },
    { name: "webkit", use: { ...devices["Desktop Safari"], viewport: { width: 1440, height: 900 } } },
  ],
});

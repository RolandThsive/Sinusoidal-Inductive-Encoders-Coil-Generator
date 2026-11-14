/* render_tip_pictures.mjs - turns the drawn pictures of the help boxes into the files the page shows.

       node WebGUI/tools/render_tip_pictures.mjs [name ...]

   Each WebGUI/docs/tooltips/drawn/<name>.svg (written by tip_pictures.py) is drawn by a headless Chromium at its own
   size (680 px wide: twice the help box, for sharp screens) and saved as WebGUI/docs/tooltips/pictures/<name>.webp
   at quality 0.82.  It prints each picture's size: tips_words.py names half of it as the picture's width and height.
   WEBGUI_CHROMIUM names another Chromium to use. */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const WEB = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const DRAWN = path.join(WEB, "docs", "tooltips", "drawn"), OUT = path.join(WEB, "docs", "tooltips", "pictures");
const names = process.argv.slice(2).length ? process.argv.slice(2) : fs.readdirSync(DRAWN).filter((f) => f.endsWith(".svg")).map((f) => f.slice(0, -4)).sort();
fs.mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch(process.env.WEBGUI_CHROMIUM ? { executablePath: process.env.WEBGUI_CHROMIUM } : {});
const page = await browser.newPage();
for (const name of names) {
  const svg = fs.readFileSync(path.join(DRAWN, name + ".svg"), "utf8");
  const got = await page.evaluate(async (text) => {
    const img = new Image();
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(text);
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    c.getContext("2d").drawImage(img, 0, 0);
    return { w: c.width, h: c.height, data: c.toDataURL("image/webp", 0.82) };
  }, svg);
  if (!got.data.startsWith("data:image/webp;base64,")) { console.error(`${name}: this browser cannot write WebP`); process.exitCode = 1; continue; }
  const bytes = Buffer.from(got.data.slice(23), "base64");
  fs.writeFileSync(path.join(OUT, name + ".webp"), bytes);
  console.log(`${name}.webp  ${got.w} x ${got.h} px, ${(bytes.length / 1024).toFixed(1)} KB  (in the help box: ${got.w / 2} x ${got.h / 2})`);
}
await browser.close();

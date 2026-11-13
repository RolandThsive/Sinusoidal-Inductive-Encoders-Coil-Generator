/* site.mjs - where the tests find the built site, and the address they open it at.

   WEBGUI_SITE     a folder that tools/build_site.py already made (the CI builds once and hands it to every browser);
                   without it, serve.mjs builds tests/.site itself
   WEBGUI_VENDOR   a folder that holds the six files of Pyodide (vendor.json), for a build without the network
   WEBGUI_PORT     the port of the test server (4173) */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const HERE = path.dirname(fileURLToPath(import.meta.url));
export const WEB = path.dirname(HERE);
export const REPO = path.dirname(WEB);
export const SITE = path.resolve(process.env.WEBGUI_SITE || path.join(HERE, ".site"));
export const PORT = +(process.env.WEBGUI_PORT || 4173);
export const ORIGIN = `http://localhost:${PORT}`;
export const PAGE = `${ORIGIN}/WebGUI/`;
export const VENDOR = path.join(SITE, "WebGUI", "vendor", "pyodide");
export const LOCK = JSON.parse(fs.readFileSync(path.join(WEB, "vendor.json"), "utf8")).pyodide;
export const CDN = LOCK.cdn;

export const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json", ".svg": "image/svg+xml", ".woff2": "font/woff2", ".webp": "image/webp",
  ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8", ".md": "text/markdown; charset=utf-8",
  ".wasm": "application/wasm", ".zip": "application/zip", ".whl": "application/zip" };
export const typeOf = (file) => TYPES[path.extname(file).toLowerCase()] || "application/octet-stream";

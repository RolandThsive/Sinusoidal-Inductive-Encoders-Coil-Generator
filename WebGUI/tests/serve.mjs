/* serve.mjs - the built site on http://localhost:4173/ , for the tests and for a look by hand.

       node WebGUI/tests/serve.mjs          (npm run serve, inside WebGUI/)

   Without WEBGUI_SITE it first builds the site into tests/.site with tools/build_site.py: with the backup copy of
   Pyodide downloaded and checked (--fetch-vendor), or taken from the folder WEBGUI_VENDOR.  It serves files only,
   never caches, and answers nothing outside the site's folder. */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { SITE, PORT, WEB, HERE, typeOf } from "./site.mjs";

if (!process.env.WEBGUI_SITE) {
  const python = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
  const vendor = process.env.WEBGUI_VENDOR ? ["--vendor", process.env.WEBGUI_VENDOR] : ["--fetch-vendor"];
  const r = spawnSync(python, [path.join(WEB, "tools", "build_site.py"), "--out", path.join(HERE, ".site"), ...vendor], { stdio: "inherit" });
  if (r.status !== 0) { console.error("The site could not be built: no tests are run."); process.exit(1); }
}
if (!fs.existsSync(path.join(SITE, "WebGUI", "index.html"))) { console.error(`${SITE} holds no built site.`); process.exit(1); }

const server = http.createServer((req, res) => {
  let name;
  try { name = decodeURIComponent(new URL(req.url, "http://localhost").pathname); }
  catch (e) { res.writeHead(400); res.end(); return; }
  if (name.endsWith("/")) name += "index.html";
  const file = path.join(SITE, name);
  if (file !== SITE && !file.startsWith(SITE + path.sep)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404, { "content-type": "text/plain" }); res.end("not found"); return; }
    // access-control-allow-origin: as GitHub Pages sends it, so the blog page can load the title's font from the tool's site
    res.writeHead(200, { "content-type": typeOf(file), "cache-control": "no-store", "x-content-type-options": "nosniff", "access-control-allow-origin": "*" });
    res.end(data);
  });
});
server.listen(PORT, "localhost", () => console.log(`The site ${SITE} is on http://localhost:${PORT}/WebGUI/`));

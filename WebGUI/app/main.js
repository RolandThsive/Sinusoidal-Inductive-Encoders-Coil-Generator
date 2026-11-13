/* main.js - starts the page and joins its parts.

   core      helpers and the page's state            engine   the Python worker
   model     the settings and their values           pages    Basic and Advanced
   run       Generate, the checks, the downloads     preview  the boards and pictures
   share     links, Import, Export                   tips     the help boxes        crash   when something breaks

   The order of a visit: Python is loaded (the CDN first, this site's own copy if the CDN does not answer), the
   chosen generator's tables are read, a design from the link is put on them, and the generator runs once. */

import { $, state, M, toast, confirmBox, copyText, closeOnOutsideClick, wireChoices, markChoices, el, clear } from "./core.js";
import { configure, start } from "./engine.js";
import { loadMode, onChange, where, val, setOne, resetAll, refreshChecks } from "./model.js";
import { initPages, showGenerator } from "./pages.js";
import { initRun, generate, showRun } from "./run.js";
import { initPreview, showBoards } from "./preview.js";
import { share, exportFiles, importFiles, readHash, applyDesign } from "./share.js";
import { initTips } from "./tips.js";
import { initCrash, showCrash } from "./crash.js";

const BLOG_HOME = "https://ro-h-bots.blogspot.com/";
const PYODIDE_CDN = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";
const PYODIDE_OWN = new URL("../vendor/pyodide/", import.meta.url).href;          // this site's backup copy
const LOCAL = ["localhost", "127.0.0.1", "[::1]"].includes(location.hostname);

/* Where Python comes from.  A link cannot point the page at another copy of Python: ?pyodide= is read only on a
   developer's own computer (localhost), and only for an address of that same computer. */
function pythonSources() {
  const asked = new URLSearchParams(location.search).get("pyodide");
  if (asked && LOCAL) {
    const url = new URL(asked, location.href);
    if (url.origin === location.origin) return [url.href];
  }
  // the site's own copy is the second source, when the build put one there (version.json says so)
  const backup = state.build && state.build.pyodide && state.build.pyodide.backup;
  return backup ? [PYODIDE_CDN, PYODIDE_OWN] : [PYODIDE_CDN];
}

function progressText(text) {
  if (!state.ready) $("btn-generate").textContent = text.replace("…", "") + "…";
  clear($("checks-list")).append(el("p", { class: "hint" }, text));
}
function fatal(text, details) {
  $("progress").classList.remove("busy");
  $("btn-generate").textContent = "Python Did Not Start";
  clear($("checks-list")).append(el("div", { class: "check error" }, el("span", { class: "lvl" }, "ERROR"), el("span", { class: "stage" }, "Start"), el("span", { class: "msg" }, text)));
  showCrash(text, details);
}

/* the Strict switch is the setting GENERATOR_MODE ("strict" / "normal"), so Share, Export and Reset carry it too */
const strictFile = () => where("GENERATOR_MODE", 0);
function syncStrict() { $("strict").checked = String(val(strictFile(), "GENERATOR_MODE")).toLowerCase() === "strict"; }

/* everything the page shows of the chosen generator */
function showAll() {
  markChoices($("gen-switch"), (b) => b.dataset.gen === state.gen);
  syncStrict();
  showGenerator();
  showRun();
  showBoards();
}
async function switchGen(gen, run = true) {
  if (gen === state.gen || state.busy || !state.ready) return;
  try { await loadMode(gen); }
  catch (e) { showCrash(`The ${gen} generator's settings could not be read.`, String(e.message || e)); return; }
  state.gen = gen;
  showAll();
  await refreshChecks();
  if (run && !M().result) generate();                // its first board, as the page does for Single when it opens
}

function wire() {
  wireChoices($("gen-switch"), (b) => switchGen(b.dataset.gen));
  $("btn-share").addEventListener("click", share);
  $("btn-export").addEventListener("click", exportFiles);
  $("btn-import").addEventListener("click", () => $("import-file").click());
  $("import-file").addEventListener("change", async (e) => {
    const files = [...e.target.files];
    e.target.value = "";
    await importFiles(files, (gen) => switchGen(gen, false));
    if (state.ready && !state.busy && !M().result) generate();          // a generator that has not run yet shows the imported design
  });
  $("btn-reset").addEventListener("click", async () => {
    if (!state.ready || !(await confirmBox("Are you sure to reset the board?"))) return;
    resetAll();
    toast("Back to the starting design");
  });
  $("strict").addEventListener("change", () => setOne(strictFile(), "GENERATOR_MODE", $("strict").checked ? "strict" : "normal", "strict"));
  $("nav-back").addEventListener("click", (e) => { e.preventDefault(); if (history.length > 1) history.back(); else location.href = BLOG_HOME; });
  $("text-copy").addEventListener("click", () => copyText($("text-body").textContent));
  for (const id of ["text-dialog", "files-dialog"]) closeOnOutsideClick($(id));
  document.addEventListener("keydown", (e) => { if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); generate(); } });
  onChange(syncStrict);
}

async function readBuild() {
  try {
    const r = await fetch("version.json", { cache: "no-cache" });
    if (r.ok) state.build = await r.json();
  } catch (e) { /* a page opened without the build step has no version.json */ }
}
function stamp(info) {
  const b = state.build, parts = [];
  if (b && b.commit) parts.push(`Build ${String(b.commit).slice(0, 7)}`, b.built);
  if (info) parts.push(`Python ${info.python}, numpy ${info.numpy}` + (info.backup ? " (this site's own copy)" : ""));
  $("build-stamp").textContent = parts.join(" · ");
}

async function main() {
  if (window.COILGEN.phone) return;                       // computers only: nothing loads on a phone
  initCrash();
  initTips();
  initPages();
  initPreview();
  initRun({ onGood: (gen) => { if (gen === state.gen) showBoards(); },
    onBusy: (on) => document.querySelectorAll("#gen-switch button").forEach((b) => (b.disabled = on)) });
  wire();
  $("progress").classList.add("busy");
  await readBuild();
  stamp(null);
  const sha = state.build && state.build.generators ? `?v=${state.build.generators.sha256.slice(0, 16)}` : "";
  configure({ sources: pythonSources(), bundle: new URL(`../py/generators.zip${sha}`, import.meta.url).href, stallMs: 15000,
    onProgress: progressText,
    onCrash: (e) => showCrash("Python stopped working. Reload the page to start it again.", String(e.message || e)) });
  let info;
  try { info = await start(); }
  catch (e) {
    fatal("Python could not be loaded. Check the internet connection and reload the page.", String(e.message || e));
    return;
  }
  stamp(info);
  // a design from the link (the blog page hands its own #... on before Python is ready)
  const shared = readHash(location.hash);
  state.gen = shared ? shared.gen : "single";
  try { await loadMode(state.gen); }
  catch (e) { fatal("The generator's settings could not be read.", String(e.message || e)); return; }
  if (shared) {
    const unknown = applyDesign(shared.design);
    // a link made by an older version can name settings this version no longer has: those are left out
    if (unknown.length) setTimeout(() => toast(`Ignored: ${unknown.join(", ")} (not settings of this version)`, 6000), 800);
  }
  state.ready = true;
  $("progress").classList.remove("busy");
  $("btn-generate").disabled = false; $("btn-check").disabled = false;
  $("btn-generate").textContent = "Generate";
  showAll();
  await refreshChecks();
  await generate();
}

window.addEventListener("message", (e) => {
  // the blog page passes its address and its share link on to the tool
  if (e.source !== window.parent || e.source === window || !e.data || typeof e.data !== "object") return;
  if (typeof e.data.coilgenPage === "string" && /^https?:\/\//.test(e.data.coilgenPage)) state.hostPage = e.data.coilgenPage.slice(0, 500);
  if (typeof e.data.coilgenHash === "string" && !state.ready && readHash(e.data.coilgenHash)) history.replaceState(null, "", e.data.coilgenHash);
});

main();

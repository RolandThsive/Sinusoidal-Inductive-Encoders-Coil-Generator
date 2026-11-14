/* main.js - starts the page and joins its parts.

   core      helpers and the page's state            engine   the Python worker
   model     the settings and their values           pages    Basic and Advanced
   run       Generate, the checks, the downloads     preview  the boards and pictures
   share     links, Import, Export                   tips     the help boxes        crash   when something breaks

   The order of a visit: Python is loaded (the CDN first, this site's own copy if the CDN does not answer), the
   chosen generator's tables are read, a design from the link is put on them, and the generator runs once. */

import { $, keepFocus, state, M, toast, confirmBox, copyText, closeOnOutsideClick, wireMenu, closeMenus, el, clear, setPhase, during } from "./core.js";
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
  if (state.ready) return;
  $("btn-generate").textContent = text.replace("…", "") + "…";
  // the box on the preview, the one a run uses: what is being loaded
  $("run-title").textContent = "Loading";
  $("run-line").textContent = text;
  $("btn-cancel").hidden = true;
  $("run-card").hidden = false;
}
function fatal(text, details) {
  $("progress").classList.remove("busy");
  $("btn-generate").textContent = "Python Did Not Start";
  $("run-card").hidden = true;
  setPhase("failed");
  clear($("checks-list")).append(el("div", { class: "check error" }, el("span", { class: "lvl" }, "ERROR"), el("span", { class: "stage" }, "Start"), el("span", { class: "msg" }, text)));
  showCrash(text, details);
}

/* the Strict switch is the setting GENERATOR_MODE ("strict" / "normal"), so Share, Export and Reset carry it too */
const strictFile = () => where("GENERATOR_MODE", 0);
function syncStrict() { $("strict").checked = String(val(strictFile(), "GENERATOR_MODE")).toLowerCase() === "strict"; }

/* everything the page shows of the chosen generator */
function showAll() {
  for (const o of $("gen-list").children) {
    const on = o.dataset.gen === state.gen;
    o.classList.toggle("on", on);
    o.setAttribute("aria-selected", String(on));
    if (on) $("gen-now").textContent = o.textContent;
  }
  syncStrict();
  showGenerator();
  showRun();
  showBoards();
}
/* While the other generator's settings are read nothing else can be started: not a second switch, not a run. */
let switching = false, focusBack = null;
function lockForSwitch(on) {
  if (on) focusBack = keepFocus();                 // the menu's button, which is switched off meanwhile
  switching = on;
  for (const id of ["gen-btn", "btn-generate", "btn-check"]) $(id).disabled = on || state.busy || !state.ready;
  if (on) closeMenus();
  else if (focusBack) { focusBack(); focusBack = null; }
}
function switchGen(gen, run = true) {
  if (gen === state.gen || state.busy || !state.ready || switching) return Promise.resolve();
  return during(async () => {
    lockForSwitch(true);
    try {
      try { await loadMode(gen); }
      catch (e) { showCrash(`The ${gen} generator's settings could not be read.`, String(e.message || e)); return; }
      state.gen = gen;
      showAll();
      await refreshChecks();
    } finally { lockForSwitch(false); }
    if (run && !M().result) await generate();        // its first board, as the page does for Single when it opens
  });
}

/* The room the list's scrollbar takes: 12 px while the list scrolls in a browser that shows scrollbars, 0 otherwise
   (a short list, or a browser whose scrollbars lie over the page).  The style sheet makes the panel that much wider
   and ends its title row and its bottom block that much earlier, so that everything in the panel ends on the line of
   the list's cards, with the scrollbar alone to the right of them, and the cards keep their width. */
function watchScrollbar() {
  const lists = [$("basic-panel"), $("advanced-panel")];
  let bar = -1, asked = false;
  const set = () => {
    asked = false;
    const list = lists.find((l) => !l.hidden && l.offsetWidth);
    const w = list ? list.offsetWidth - list.clientWidth : bar;
    if (w === bar) return;
    // at once: the column does not slide by a scrollbar's width as it does from Basic to Advanced
    const ws = $("workspace");
    ws.style.transition = "none";
    bar = w;
    document.documentElement.style.setProperty("--bar", `${w}px`);
    void ws.offsetWidth;
    ws.style.removeProperty("transition");
  };
  // in the next frame, not inside the observer: a column made wider there would be seen again in the same frame
  // (Safari then reports "ResizeObserver loop completed with undelivered notifications")
  const watch = new ResizeObserver(() => { if (!asked) { asked = true; requestAnimationFrame(set); } });
  lists.forEach((l) => watch.observe(l));
  set();
}

function wire() {
  watchScrollbar();
  wireMenu($("gen-switch"), (o) => switchGen(o.dataset.gen));
  $("btn-share").addEventListener("click", share);
  $("btn-export").addEventListener("click", exportFiles);
  $("btn-import").addEventListener("click", () => $("import-file").click());
  $("import-file").addEventListener("change", async (e) => {
    const files = [...e.target.files];
    e.target.value = "";
    await during(async () => {
      await importFiles(files, (gen) => switchGen(gen, false));
      if (state.ready && !state.busy && !M().result) await generate();  // a generator that has not run yet shows the imported design
    });
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
  document.addEventListener("keydown", (e) => {
    if (!(e.ctrlKey || e.metaKey) || e.key !== "Enter") return;
    e.preventDefault();
    if (!switching && !document.querySelector("dialog[open]")) generate();      // not behind an open dialog
  });
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
    onBusy: (on) => { $("gen-btn").disabled = on; if (on) closeMenus(); } });
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
  setPhase("ready");
}

window.addEventListener("message", (e) => {
  // the blog page passes its address and its share link on to the tool
  if (e.source !== window.parent || e.source === window || !e.data || typeof e.data !== "object") return;
  if (typeof e.data.coilgenPage === "string" && /^https?:\/\//.test(e.data.coilgenPage)) state.hostPage = e.data.coilgenPage.slice(0, 500);
  if (typeof e.data.coilgenHash === "string" && !state.ready && readHash(e.data.coilgenHash)) history.replaceState(null, "", e.data.coilgenHash);
});

// a design link pasted into the address bar of the open page changes only the part after the #, and the browser does
// not load the page again by itself: the page does, and opens the link as on a first visit
window.addEventListener("hashchange", () => { if (readHash(location.hash)) location.reload(); });

main();

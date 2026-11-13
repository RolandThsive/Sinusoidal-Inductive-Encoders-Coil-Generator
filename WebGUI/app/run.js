/* run.js - Generate and Check Only, and what a run leaves: the checks, the numbers under the controls, the downloads.

   A run is the generator's own program (WebGenerator.run): the page shows its six steps as it prints them, the line it
   printed last and the seconds, and afterwards its findings in its own words.  A run cannot be stopped from outside,
   so Cancel ends the Python worker and starts a new one. */

import { $, el, clear, state, M, fmt, plural, same, clone, toast, say, textBox, download } from "./core.js";
import { ask, cancel as cancelEngine } from "./engine.js";
import { onChange, scheduleChecks, where, v, hasSets } from "./model.js";
import { reveal, canReveal } from "./pages.js";
import { showCrash } from "./crash.js";

const STAGE = { 0: "Start", 1: "Parameters", 2: "Stator", 3: "Rotor", 4: "Electrical", 5: "Deciding", 6: "Files" };
const TYPICAL_SECONDS = { single: 4, dual: 30 };
const BOARD_FILE = { stator: "Stator", rotor: "Rotor" };       // the part's name in its downloaded file name
const TYPES = { ".svg": "image/svg+xml", ".txt": "text/plain", ".zip": "application/zip" };
const hooks = { onGood: null, onBusy: null };

/* ---- the run card ------------------------------------------------------------------------------- */
let ticker = null, runStart = 0, cancelling = false;
function setBusy(on, word) {
  state.busy = on;
  $("progress").classList.toggle("busy", on);
  $("btn-generate").disabled = on || !state.ready;
  $("btn-check").disabled = on || !state.ready;
  if (word) $("btn-generate").textContent = word;
  if (hooks.onBusy) hooks.onBusy(on);
}
function openRunCard(gen, checkOnly) {
  clear($("run-steps"));
  $("run-line").textContent = checkOnly ? "Checking the settings…" : "Starting the generator…";
  $("run-card").hidden = false;
  $("checks-list").hidden = true;
  $("btn-cancel").disabled = false;
  $("progress").setAttribute("aria-valuenow", "0");
  runStart = performance.now();
  const about = state.modes[gen].lastSeconds || (checkOnly ? 0 : TYPICAL_SECONDS[gen]);
  const tick = () => { $("run-time").textContent = `${((performance.now() - runStart) / 1000).toFixed(1)} s` + (about ? ` of about ${Math.round(about)} s` : ""); };
  tick();
  ticker = setInterval(tick, 100);
}
function closeRunCard() {
  clearInterval(ticker); ticker = null;
  $("run-card").hidden = true;
  $("checks-list").hidden = false;
}
/* a line the generator printed: a new step ("[2/6] Building the stator"), or the latest news of the step */
function onLine(text) {
  const m = /^\[(\d+)\/(\d+)\] (.*)$/.exec(text);
  if (m) {
    const list = $("run-steps");
    for (const li of list.children) { li.classList.remove("now"); li.classList.add("done"); }
    list.append(el("li", { class: "now" }, m[3]));
    $("progress").setAttribute("aria-valuenow", m[1]);
    $("progress").setAttribute("aria-valuemax", m[2]);
    $("run-line").textContent = "";
    say(`Step ${m[1]} of ${m[2]}: ${m[3]}`);
  } else if (text.trim()) $("run-line").textContent = text.trim().slice(0, 160);
}

/* ---- Generate, Check Only, Cancel --------------------------------------------------------------- */
export async function generate(checkOnly = false) {
  if (!state.ready || state.busy) return;
  const gen = state.gen, m = state.modes[gen], sent = clone(m.values);
  setBusy(true, checkOnly ? "Checking…" : "Generating…");
  openRunCard(gen, checkOnly);
  try {
    const r = await ask("run", { mode: gen, values: sent, checkOnly }, onLine);
    m.result = r;
    if (r.ok && !r.checkOnly && r.zipBytes) {
      dropPictures(m);
      m.good = { name: r.name, zipBytes: r.zipBytes, bytes: r.bytes, files: r.files.map((f) => ({ name: f.name, size: f.size })),
        stator: r.stator, rotor: r.rotor, text: r.text, values: sent };
      m.lastSeconds = r.seconds;
      m.stale = !same(sent, m.values);                       // a setting changed while the generator ran
      delete r.zipBytes; delete r.bytes;
      if (hooks.onGood) hooks.onGood(gen);
    }
    say(r.ok ? (r.checkOnly ? "The check passed" : `Generated ${r.name}`) : `Not generated: ${r.failed || "the generator stopped"}`);
  } catch (e) {
    if (cancelling) return;                                  // cancel() tidies up
    m.result = { ok: false, checkOnly, items: [{ step: 0, level: "error", lines: [String(e.message || e)], names: [], files: [] }],
      failed: "Python stopped", text: "", steps: [] };
  } finally {
    if (!cancelling) {
      closeRunCard();
      setBusy(false, "Generate");
      if (gen === state.gen) showRun();
      scheduleChecks(0);
    }
  }
}
export async function cancelRun() {
  if (!state.busy || cancelling) return;
  cancelling = true;
  $("btn-cancel").disabled = true;
  $("run-line").textContent = "Cancelling: Python is starting again…";
  clearInterval(ticker);
  state.ready = false;
  try {
    await cancelEngine();
    state.ready = true;
    toast("Cancelled");
  } catch (e) {
    showCrash("Python could not be started again after Cancel. Reload the page.", String(e.message || e));
  } finally {
    cancelling = false;
    closeRunCard();
    setBusy(false, state.ready ? "Generate" : "Python Did Not Start");
    showRun();
    scheduleChecks(0);
  }
}

/* ---- the checks ----------------------------------------------------------------------------------- */
/* The words of a finding, with every setting it names made a way to that setting. */
function message(item) {
  const box = el("span", { class: "msg" });
  const names = new Set(item.names || []);
  const hint = /\b(?:set|ring) ([12])\b|\b(?:RX|TX)([12])\b/i.exec(item.lines[0] || "");
  const set = hint ? +(hint[1] || hint[2]) : M().set;
  item.lines.forEach((line, i) => {
    if (i) box.append("\n");
    for (const part of line.split(/\b([A-Z][A-Z0-9_]{2,})\b/)) {
      const file = names.has(part) ? where(part, set) : null;
      if (file && canReveal(file, part)) {
        box.append(el("button", { type: "button", class: "param-link", "data-tip": "Show this setting", onclick: () => reveal(file, part) }, part));
      } else if (part) box.append(part);
    }
  });
  return box;
}
function checkRow(item) {
  const row = el("div", { class: "check " + item.level, role: "listitem" },
    el("span", { class: "lvl" }, item.level.toUpperCase()), el("span", { class: "stage" }, STAGE[item.step] || `Step ${item.step}`), message(item));
  return row;
}
export function renderChecks() {
  const r = M().result, list = clear($("checks-list")), counts = clear($("counts"));
  $("btn-runtext").disabled = !(r && r.text);
  if (!r) return;
  const items = r.items || [];
  const n = (l) => items.filter((i) => i.level === l).length;
  const ne = n("error"), nw = n("warning"), ni = n("info");
  const time = r.seconds ? ` · ${r.seconds.toFixed(1)} s` : "";
  if (r.ok) {
    counts.append(el("span", { class: nw ? "w" : "ok" }, r.checkOnly ? (nw ? `Check Passed, ${plural(nw, "Warning")}` : "Check Passed") : (nw ? plural(nw, "Warning") : "No Warnings")),
      ` · ${ni} Info` + (r.name ? ` · ${r.name}` : "") + time);
  } else {
    counts.append(el("span", { class: "e" }, `Not Generated: ${r.failed || "the generator stopped"}`),
      ne ? ` · ${plural(ne, "Error")}` : "", nw ? ` · ${plural(nw, "Warning")}` : "");
  }
  const order = { error: 0, warning: 1, info: 2 };
  const shown = items.filter((i) => state.showInfo || i.level !== "info").sort((a, b) => order[a.level] - order[b.level]);
  for (const i of shown) list.append(checkRow(i));
  if (r.crash) {
    list.append(el("div", { class: "check error", role: "listitem" }, el("span", { class: "lvl" }, "ERROR"), el("span", { class: "stage" }, "Python"),
      el("span", { class: "msg" }, "The generator stopped with an error of its own. ",
        el("button", { type: "button", class: "param-link", onclick: () => showCrash("The generator stopped with an error of its own.", r.crash) }, "Show the details"))));
  }
  if (!shown.length && !r.crash) list.append(el("p", { class: "hint" }, r.ok ? (ni ? "Nothing to report. Turn on Info to see the generator's notes." : "Nothing to report.") : "See Run Text for what the generator printed."));
}

/* ---- the numbers under the controls ------------------------------------------------------------- */
/* Read from the generator's own summary of the last good run; before a run only the range, which follows Loops. */
function summaryRows(text) {
  const sets = {};
  let k = 0;
  const of = (i) => (sets[i] = sets[i] || {});
  for (const line of text.split("\n")) {
    let m;
    if ((m = /^Set (\d) /.exec(line))) k = +m[1];
    else if (/^(Dual rotor|Rotor|Ring \d)/.test(line)) k = -1;                  // the rotor's part of the summary
    else if ((m = /^Electrical(?: of set (\d).*?)? \(estimate, step 4\): (.*)$/.exec(line))) of(m[1] ? +m[1] : 0).electrical = m[2];
    else if (k >= 0 && (m = /unique range ([\d.]+) deg/.exec(line))) of(k).range = `${m[1]}° per period`;
    else if (k >= 0 && (m = /^\s+RX band r = ([\d.]+) \.\.\. ([\d.]+) mm, profile/.exec(line))) of(k).band = `${m[1]} to ${m[2]} mm`;
    else if (k >= 0 && (m = /^\s+TX ring r = ([\d.]+) \.\.\. ([\d.]+) mm/.exec(line))) of(k).ring = `${m[1]} to ${m[2]} mm`;
    else if (k >= 0 && (m = /^\s+board edge: bore r = ([\d.]+) mm, outer r = ([\d.]+) mm/.exec(line))) of(-1).board = `${m[1]} to ${m[2]} mm`;
  }
  return sets;
}
export function renderResults() {
  const m = M(), box = clear($("results"));
  const row = (label, text) => { if (text) box.append(el("div", {}, el("b", {}, `${label}: `), text)); };
  const sets = hasSets() ? [1, 2] : [0];
  if (m.good && !m.stale) {
    const s = summaryRows(m.good.text);
    row("Board", (s[-1] || {}).board);
    for (const k of sets) {
      const x = s[k] || {}, pre = k ? `Set ${k} ` : "";
      row(`${pre}Range`, x.range); row(`${pre}RX Band`, x.band); row(`${pre}TX Ring`, x.ring); row(`${pre}Electrical`, x.electrical);
    }
  } else {
    for (const k of sets) { const n = v("LOOPS", k || 1); row(k ? `Set ${k} Range` : "Range", n ? `${fmt(360 / n)}° per period` : ""); }
  }
}

/* ---- stale notice and downloads ------------------------------------------------------------------ */
const ZIP_TIP = "Download this run as one zip, the same folder the desktop generator writes: Stator.kicad_pcb, Rotor.kicad_pcb, their .kicad_pro files, Parameters.txt and the two pictures.";
export function updateStale() {
  const m = M(), r = m.result, good = m.good, badge = $("stale-badge");
  const failed = r && !r.ok && !r.checkOnly && good;
  badge.hidden = !((m.stale && good) || failed);
  placeBadge();
  const ready = !!good && !m.stale;
  for (const part of ["stator", "rotor"]) {
    const b = $(`btn-dl-${part}`);
    b.disabled = !(ready && good[part]);
    b.dataset.tip = m.stale ? "The settings changed: press Generate first"
      : `Download only the ${part} board of this run (${good ? good.name + "_" : ""}${BOARD_FILE[part]}.kicad_pcb), ready to open in KiCad`;
  }
  $("btn-download").disabled = !ready;
  $("btn-download").dataset.tip = m.stale ? "The settings changed: press Generate first" : ZIP_TIP + (good ? `\nThis run: ${good.name}.zip` : "");
  $("btn-files").disabled = !ready;
}
/* The notice sits in the Checks header, centred between the run name (the counts) and the Info switch.  It is one
   line if it fits, else two short lines; when the panel is narrow and the counts wrap to a second line it is
   centred between the Checks title and the Info switch instead. */
function placeBadge() {
  const badge = $("stale-badge"), panel = $("checks"), head = panel.querySelector(".checks-head");
  badge.classList.remove("two-line"); badge.style.left = "";
  if (badge.hidden) return;
  const stale = M().stale;
  const full = stale ? "Settings changed: press Generate to update the board" : "Not generated: this is the last board that worked";
  const mid = stale ? "Settings changed: press Generate" : "Not generated: last good board shown";
  const pr = panel.getBoundingClientRect();
  const title = head.querySelector("h2").getBoundingClientRect(), counts = $("counts"), cr = counts.getBoundingClientRect();
  const info = head.querySelector(".switch-row").getBoundingClientRect();
  let left = title.right;
  if (Math.abs(cr.top - title.top) < 20 && counts.textContent.trim()) {      // counts on the heading's line: start after their text
    const range = document.createRange(); range.selectNodeContents(counts);
    left = Math.min(range.getBoundingClientRect().right, cr.right);
  }
  const room = info.left - left - 16;
  for (const [text, two] of [[full, false], [mid, false], [mid, true]]) {
    badge.textContent = text; badge.classList.toggle("two-line", two);
    if (badge.getBoundingClientRect().width <= room) break;
  }
  badge.style.left = `${(left + info.left) / 2 - pr.left}px`;
  badge.style.top = `${title.top + title.height / 2 - pr.top}px`;
}

function dropPictures(m) {
  if (m.pictures) for (const url of Object.values(m.pictures)) URL.revokeObjectURL(url);
  m.pictures = null;
}
const typeOf = (name) => TYPES[name.slice(name.lastIndexOf("."))] || "application/octet-stream";
function showFiles() {
  const good = M().good, list = clear($("files-list"));
  if (!good) return;
  for (const f of good.files) {
    list.append(el("div", { class: "file-row" }, el("span", { class: "file-name" }, f.name),
      el("span", { class: "file-size" }, f.size >= 1048576 ? `${(f.size / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(f.size / 1024))} KB`),
      el("button", { type: "button", class: "glass-btn small", "aria-label": `Download ${f.name}`, onclick: () => download(good.bytes[f.name], f.name, typeOf(f.name)) }, "Download")));
  }
  $("files-dialog").showModal();
}

/* ---- everything a run shows, for the generator that is chosen ----------------------------------- */
export function showRun() {
  renderChecks();
  renderResults();
  updateStale();
}

export function initRun(h) {
  Object.assign(hooks, h);
  $("btn-generate").addEventListener("click", () => generate(false));
  $("btn-check").addEventListener("click", () => generate(true));
  $("btn-cancel").addEventListener("click", cancelRun);
  $("show-info").addEventListener("change", (e) => { state.showInfo = e.target.checked; renderChecks(); });
  $("btn-runtext").addEventListener("click", () => { const r = M().result; if (r && r.text) textBox("Run Text", r.text); });
  $("btn-download").addEventListener("click", () => { const g = M().good; if (g && !M().stale) download(g.zipBytes, `${g.name}.zip`, "application/zip"); });
  for (const part of ["stator", "rotor"]) {
    $(`btn-dl-${part}`).addEventListener("click", () => {
      const g = M().good;
      if (g && !M().stale && g[part]) download(g.bytes[g[part]], `${g.name}_${BOARD_FILE[part]}.kicad_pcb`);
    });
  }
  $("btn-files").addEventListener("click", showFiles);
  window.addEventListener("resize", placeBadge);
  onChange(() => { updateStale(); renderResults(); });
}

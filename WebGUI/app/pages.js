/* pages.js - the settings column: Basic (the main settings of each category) and Advanced (every setting of every
   parameter file), for the generator that is chosen.

   Basic is a hand-picked subset with its own sliders (BASIC_NAMES and the page functions below; keep them in step with
   the parameter files by hand).  Advanced is built from the generator's own tables: a setting the generator gets
   tomorrow shows up here without a change to the page.

   Dual has two coil sets: the tabs are the same categories, and a Set 1 | Set 2 switch says whose RX, TX, Rotor and IC
   settings are shown. */

import { $, el, clear, state, M, fmt, plural, wireChoices, markChoices } from "./core.js";
import { CATS, onChange, onChecked, hasSets, fileOf, catHasSets, where, v, isChanged, changedIn, BAND_RADII, BAND_CENTRE } from "./model.js";
import { groupTitle, labelOf, ROTOR_MODE_GROUPS } from "./labels.js";
import { numberField, segmentedField, boolField, txLayoutField, advancedField } from "./fields.js";
import { TOOLTIPS } from "./paramtips.js";

const BASIC_CATS = ["Board", "RX", "TX", "Rotor"];
// every setting Basic can change (Advanced lists all of them, these included); the others are counted in the note
// under Basic's controls
const BASIC_NAMES = new Set(["INNER_EDGE_RADIUS_MM", "OUTER_EDGE_RADIUS_MM", "PCB_LAYERS", "AIR_GAP_MM",
  "LOOPS", "RX_SUBCOILS", "INSIDE_RADIUS_MM", "OUTSIDE_RADIUS_MM", "RX_R_BASE_MM", "RX_A_MM",
  "RX_LAYER_A", "RX_LAYER_B", "TX_TURNS", "TX_WIRING", "TX_LAYER_A", "TX_LAYER_B",
  "ROTOR_MODE", "ROTOR_AUTO_DUTY", "ROTOR_AUTO_COVER_TX", "ROTOR_CUSTOM_SECTORS", "ROTOR_CUSTOM_DUTY", "GENERATOR_MODE"]);
const SET_WORDS = { 1: "Set 1 · Inner", 2: "Set 2 · Outer" };
const TAB_WORDS = { Board: "the board", RX: "the RX coils", TX: "the TX coil", Rotor: "the rotor", IC: "the receiver IC", Silk: "the silkscreen suggestion" };

/* a setting the settings column shows (the Output block is fixed on the web; Strict is the switch beside Generate) */
const listed = (p) => !p.readOnly && p.name !== "GENERATOR_MODE";
export function canReveal(file, name) { const p = (M().params[file] || {})[name]; return !!p && listed(p); }

/* ---- tabs and the Set switch -------------------------------------------------------------------- */
function drawTabs(box, cats, current, panel, what) {
  const m = M();
  clear(box);
  for (const cat of cats) {
    const n = m.files.filter((f) => f.cat === cat).reduce((a, f) => a + f.parameters.filter((p) => listed(p) && isChanged(f.file, p.name)).length, 0);
    box.append(el("button", { type: "button", role: "tab", "data-key": cat, "aria-controls": panel,
      "data-tip": `${what} of ${TAB_WORDS[cat]}` + (n ? ` (${plural(n, "setting")} changed)` : "") },
      cat, n ? el("span", { class: "tab-dot", "aria-label": `${plural(n, "setting")} changed` }) : null));
  }
  markChoices(box, (b) => b.dataset.key === current);
}
function drawSetSwitch(box, cat) {
  const show = hasSets() && catHasSets(cat);
  box.hidden = !show;
  if (!show) return;
  clear(box);
  for (const k of [1, 2]) {
    const n = changedIn(fileOf(cat, k));
    box.append(el("button", { type: "button", role: "radio", "data-key": k,
      "data-tip": `The ${cat} settings of coil set ${k} (the ${k === 1 ? "inner" : "outer"} one)` },
      SET_WORDS[k], n ? el("span", { class: "tab-dot", "aria-label": `${plural(n, "setting")} changed` }) : null));
  }
  markChoices(box, (b) => +b.dataset.key === M().set);
}

/* ---- Basic ---------------------------------------------------------------------------------------- */
function noteFor(name) {
  if (name === "LOOPS") { const n = v("LOOPS"); return `Range: ${fmt(n ? 360 / n : 360)}°`; }
  if (name === "RX_SUBCOILS") return v("RX_SUBCOILS") > 1 ? `Split: ${fmt(v("RX_SUBCOIL_SPLIT_ELEC_DEG"))}° el` : "";
  if (name === "TX_TURNS") return `Total: ${String(v("TX_WIRING")).toLowerCase() === "series" ? v("TX_TURNS") * 2 : v("TX_TURNS")}`;
  if (name === "RX_BAND") {                                    // which of the three ways the band is given (BandLayout.py)
    if (BAND_RADII.every((n) => v(n) !== null)) return "From the radii";
    if (BAND_CENTRE.every((n) => v(n) !== null)) return "From R Base and A";
    if (hasSets()) return "Placed by the generator";
    return v("INNER_EDGE_RADIUS_MM") === null || v("OUTER_EDGE_RADIUS_MM") === null ? "Needs both board edges" : "From the board edges";
  }
  return "";
}
function updateBasicNotes() {
  document.querySelectorAll("#basic-controls [data-note]").forEach((n) => (n.textContent = noteFor(n.dataset.note)));
}
const num = (name, o) => numberField({ file: where(name), name, ...o });
const seg = (name, o) => segmentedField({ file: where(name), name, ...o });

const BASIC_PAGES = {
  Board: () => [
    num("INNER_EDGE_RADIUS_MM", { label: "Board Inner Radius", unit: "mm", min: 0.1, max: 250, step: 0.001, sliderStep: 0.1, slider: [5, 120], none: true }),
    num("OUTER_EDGE_RADIUS_MM", { label: "Board Outer Radius", unit: "mm", min: 0.1, max: 250, step: 0.001, sliderStep: 0.1, slider: [10, 150], none: true }),
    seg("PCB_LAYERS", { label: "Board Layers", options: [[2, "2 Layers"], [4, "4 Layers"]], from: "basic-layers" }),     // the TX cards follow it
    num("AIR_GAP_MM", { label: "Air Gap", unit: "mm", min: 0.1, max: 10, step: 0.001, sliderStep: 0.1, slider: [0.2, 5] }),
  ],
  RX: () => [
    num("LOOPS", { label: "Loops", min: 1, max: 16, step: 1, slider: [1, 16], note: noteFor("LOOPS"), ticks: ["1", "4", "8", "12", "16"] }),
    seg("RX_SUBCOILS", { label: "RX Sub-Coils", options: [[1, "1 (None)"], [2, "2"], [3, "3"]], note: noteFor("RX_SUBCOILS") }),
    el("div", { class: "group-title with-note" }, "RX Band", el("span", { class: "field-note", "data-note": "RX_BAND" }, noteFor("RX_BAND"))),
    num("INSIDE_RADIUS_MM", { label: "RX Inside Radius", unit: "mm", min: 0.1, max: 250, step: 0.001, sliderStep: 0.1, slider: [5, 150], none: true }),
    num("OUTSIDE_RADIUS_MM", { label: "RX Outside Radius", unit: "mm", min: 0.1, max: 250, step: 0.001, sliderStep: 0.1, slider: [5, 150], none: true }),
    num("RX_R_BASE_MM", { label: "RX R Base", unit: "mm", min: 0.1, max: 250, step: 0.001, sliderStep: 0.1, slider: [5, 150], none: true }),
    num("RX_A_MM", { label: "RX Swing A", unit: "mm", min: 0.1, max: 125, step: 0.001, sliderStep: 0.1, slider: [0.5, 40], none: true }),
  ],
  TX: () => [
    num("TX_TURNS", { label: "TX Turns Per Layer", min: 1, max: 12, step: 1, note: noteFor("TX_TURNS") }),
    txLayoutField("b"),
  ],
  Rotor: () => {
    const mode = String(v("ROTOR_MODE") || "").toLowerCase();
    const picker = seg("ROTOR_MODE", { label: "Rotor Mode", value: mode, from: "basic-mode",       // the fields below depend on the mode
      options: [["according_to_stator", "Automatic"], ["custom", "Custom"]] });
    if (mode === "custom") return [picker,
      num("ROTOR_CUSTOM_SECTORS", { label: "Rotor Metal Sectors", min: 1, max: 64, step: 1 }),
      num("ROTOR_CUSTOM_DUTY", { label: "Rotor Metal Fraction", min: 0.05, max: 0.95, step: 0.01, slider: [0.05, 0.95] })];
    return [picker,
      num("ROTOR_AUTO_DUTY", { label: "Rotor Metal Fraction", min: 0.05, max: 0.95, step: 0.01, slider: [0.05, 0.95] }),
      boolField({ file: where("ROTOR_AUTO_COVER_TX"), name: "ROTOR_AUTO_COVER_TX", label: "Copper Over The TX Turns" })];
  },
};

function renderBasic() {
  const m = M();
  if (!BASIC_CATS.includes(m.basicTab)) m.basicTab = "Board";
  drawTabs($("basic-tabs"), BASIC_CATS, m.basicTab, "basic-controls", "The main settings");
  drawSetSwitch($("basic-set"), m.basicTab);
  const box = clear($("basic-controls"));
  box.append(...BASIC_PAGES[m.basicTab]());
  updateAdvNote();
}
function updateAdvNote() {
  const m = M();
  let n = 0;
  for (const f of m.files) for (const p of f.parameters) if (listed(p) && !BASIC_NAMES.has(p.name) && isChanged(f.file, p.name)) n++;
  $("basic-adv-note").textContent = n ? `Advanced: ${plural(n, "more setting")} changed.` : "";
}

/* ---- Advanced ------------------------------------------------------------------------------------- */
const cats = () => CATS.filter((c) => M().files.some((f) => f.cat === c));

/* the settings of one file, in their groups (a heading that comes twice in the file is one group) */
function groupsOf(f) {
  const groups = new Map();
  for (const p of f.parameters.filter(listed)) {
    const g = groupTitle(p.heading, f.cat);
    if (!groups.has(g)) groups.set(g, []);
    groups.get(g).push(p);
  }
  return groups;
}
function groupBlock(box, title, params, foldable, withCards) {
  const m = M(), folded = foldable && m.folded.has(title);
  const inner = el("div", { class: "group-inner" });
  if (foldable) {
    box.append(el("button", { type: "button", class: "group-title foldable" + (folded ? " collapsed" : ""), "data-group": title, "aria-expanded": String(!folded),
      "data-focus": `group|${title}`,
      "data-tip": `Show or hide the ${title.startsWith("Custom") ? "custom" : "automatic"} rotor settings (used when Rotor Mode is ${ROTOR_MODE_GROUPS[title]})`,
      onclick: () => { if (m.folded.has(title)) m.folded.delete(title); else m.folded.add(title); applyFolds(); } },
      el("span", { class: "chevron", "aria-hidden": "true" }), title));
  } else box.append(el("div", { class: "group-title" }, title));
  box.append(el("div", { class: "group-card" + (folded ? " collapsed" : ""), "data-group": title }, inner));
  for (const p of params) {
    if (withCards && p.name === "TX_WIRING") inner.append(txLayoutField("a", p.set || M().set));    // the layout cards, above the settings they set
    inner.append(advancedField(p));
  }
}
// Opens the blocks of the chosen Rotor Mode and folds the others.
function foldRotorBlocks(mode) {
  for (const [g, m] of Object.entries(ROTOR_MODE_GROUPS)) { if (m === mode) M().folded.delete(g); else M().folded.add(g); }
}
// Shows each group block as folded or open, as the mode's `folded` says.
function applyFolds() {
  document.querySelectorAll("#advanced-controls [data-group]").forEach((n) => {
    const folded = M().folded.has(n.dataset.group);
    n.classList.toggle("collapsed", folded);
    if (n.tagName === "BUTTON") n.setAttribute("aria-expanded", String(!folded));
  });
}

/* what a setting is found by: its Python name, its label, its group and its help text */
function haystack(f, p) {
  const l = labelOf(p.name);
  return `${p.name} ${p.name.replace(/_/g, " ")} ${l.text} ${groupTitle(p.heading, f.cat)} ${TOOLTIPS[p.name] || p.help || ""}`.toLowerCase();
}
function renderFound(box, words) {
  const m = M();
  let total = 0;
  for (const f of m.files) {
    const hits = f.parameters.filter((p) => listed(p) && words.every((w) => haystack(f, p).includes(w)));
    if (!hits.length) continue;
    total += hits.length;
    groupBlock(box, f.set ? `${f.cat} · Set ${f.set}` : f.cat === "Silk" ? "Silkscreen Suggestion" : f.cat, hits, false, false);
  }
  if (!total) box.append(el("p", { class: "hint" }, "No setting matches. Try a shorter word, or a part of its Python name."));
  $("find-count").textContent = total ? plural(total, "setting") : "";
}

function renderAdvanced() {
  const m = M(), box = clear($("advanced-controls"));
  if (!cats().includes(m.advTab)) m.advTab = "Board";
  const words = m.find.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const finding = words.length > 0;
  $("adv-tabs").hidden = finding;
  drawTabs($("adv-tabs"), cats(), m.advTab, "advanced-controls", "Every setting");
  drawSetSwitch($("adv-set"), m.advTab);
  if (finding) { $("adv-set").hidden = true; renderFound(box, words); return; }
  $("find-count").textContent = "";
  // a new rotor mode opens its own blocks and folds the other mode's, after the page is drawn (so it animates)
  const mode = String(v("ROTOR_MODE") || "").toLowerCase(), modeChanged = mode !== m.rotorModeSeen;
  if (m.rotorModeSeen === undefined) foldRotorBlocks(mode);
  m.rotorModeSeen = mode;
  const f = m.files.find((x) => x.file === fileOf(m.advTab));
  for (const [title, params] of groupsOf(f)) groupBlock(box, title, params, f.cat === "Rotor" && !!ROTOR_MODE_GROUPS[title], true);
  if (modeChanged) requestAnimationFrame(() => { foldRotorBlocks(mode); applyFolds(); });
}

/* ---- drawing, and marking what the generator says ----------------------------------------------- */
/* Draw the settings column again.  The scroll position and the keyboard's place are kept. */
export function render() {
  clearTimeout(renderTimer); renderTimer = null;
  if (!M().loaded) return;
  const basic = state.view === "basic", panel = $(basic ? "basic-panel" : "advanced-panel");
  const scroll = panel.scrollTop, focused = document.activeElement && panel.contains(document.activeElement) ? document.activeElement.dataset.focus : null;
  if (basic) renderBasic(); else renderAdvanced();
  panel.scrollTop = scroll;
  if (focused) {
    const again = [...panel.querySelectorAll("[data-focus]")].find((n) => n.dataset.focus === focused);
    if (again && !again.disabled) again.focus({ preventScroll: true });
  }
  markFields();
}
/* Draw again after the event that is being handled: a Tab that leaves a field has then moved the keyboard on. */
let renderTimer = null;
function renderSoon() { if (renderTimer === null) renderTimer = setTimeout(render, 0); }

/* Mark every field shown: changed from the published value, not used by the generator now, and what the generator
   says about its value (nothing is drawn again, so it can run while a field is being used). */
export function markFields() {
  const m = M();
  document.querySelectorAll("#controls .field[data-name]").forEach((f) => {
    const { file, name } = f.dataset;
    if (!m.params[file]) return;
    f.classList.toggle("inactive", m.inactive[file].has(name));
    f.classList.toggle("changed", isChanged(file, name));
    const text = m.errors[file][name] || "", slot = f.querySelector(".field-error");
    f.classList.toggle("invalid", !!text);
    if (slot && slot.textContent !== text) { slot.textContent = text; slot.hidden = !text; }
    f.querySelectorAll("input[type=text], input:not([type])").forEach((i) => { if (text) i.setAttribute("aria-invalid", "true"); else i.removeAttribute("aria-invalid"); });
  });
}

/* ---- Basic | Advanced ---------------------------------------------------------------------------- */
let viewTimer = null;
export function setView(view, animate = true) {
  if (view === state.view) return;
  state.view = view;
  markChoices($("mode-switch"), (b) => b.dataset.mode === view);
  const show = () => {
    $("basic-panel").hidden = state.view !== "basic";
    $("advanced-panel").hidden = state.view !== "advanced";
    render();
  };
  $("app").classList.toggle("advanced", view === "advanced");
  if (!animate) { show(); return; }
  // the panel widens (Advanced) or narrows (Basic) while the old controls fade out and the new ones fade in
  const ctr = $("controls"), adv = $("advanced-panel"), advW = adv.getBoundingClientRect().width;
  // Advanced -> Basic: the Advanced controls keep their width while they fade out, so the panel narrowing under them
  // clips them instead of squeezing them onto more lines; the width is released when they are hidden
  if (view === "basic" && !adv.hidden && advW) adv.style.setProperty("width", `${advW}px`);
  ctr.classList.remove("enter");
  ctr.classList.add("leave");
  clearTimeout(viewTimer);
  viewTimer = setTimeout(() => {
    adv.style.removeProperty("width");
    show();
    ctr.classList.remove("leave");
    void ctr.offsetWidth;                                  // restart the fade-in
    ctr.classList.add("enter");
  }, 180);
}

/* Show one setting in Advanced: its tab, its coil set, its block opened, the field scrolled into view and marked. */
export function reveal(file, name) {
  const m = M(), f = m.files.find((x) => x.file === file);
  if (!f || !m.params[file][name] || !listed(m.params[file][name])) return false;
  m.find = ""; $("find").value = "";
  m.advTab = f.cat;
  if (f.set) m.set = f.set;
  m.folded.delete(groupTitle(m.params[file][name].heading, f.cat));
  setView("advanced", false);
  render();
  const field = [...document.querySelectorAll("#advanced-controls .field[data-name]")].find((x) => x.dataset.file === file && x.dataset.name === name);
  if (!field) return false;
  field.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  field.classList.remove("flash"); void field.offsetWidth; field.classList.add("flash");
  const first = field.querySelector("input:not(:disabled), button.dropdown-btn, .segmented button[tabindex='0']");
  if (first) first.focus({ preventScroll: true });
  return true;
}

/* ---- wiring ---------------------------------------------------------------------------------------- */
export function initPages() {
  wireChoices($("mode-switch"), (b) => setView(b.dataset.mode));
  wireChoices($("basic-tabs"), (b) => { M().basicTab = b.dataset.key; render(); });
  wireChoices($("adv-tabs"), (b) => { M().advTab = b.dataset.key; render(); });
  for (const id of ["basic-set", "adv-set"]) wireChoices($(id), (b) => { M().set = +b.dataset.key; render(); });
  const find = $("find");
  find.addEventListener("input", () => { M().find = find.value; render(); });
  find.addEventListener("keydown", (e) => { if (e.key === "Escape" && find.value) { e.preventDefault(); find.value = ""; M().find = ""; render(); } });
  onChange((from) => {
    // Basic leaves its own controls alone while one of them is being used; everything else is drawn again
    if (state.view === "basic" && from === "basic") {
      updateBasicNotes(); updateAdvNote();
      drawTabs($("basic-tabs"), BASIC_CATS, M().basicTab, "basic-controls", "The main settings");
      drawSetSwitch($("basic-set"), M().basicTab);
      markFields();
    } else renderSoon();
  });
  onChecked(markFields);
}
/* the generator was changed (Single | Dual): show its settings, where the visitor left them */
export function showGenerator() {
  $("find").value = M().find;
  $("basic-title").textContent = hasSets() ? "Controls · Dual" : "Controls";
  $("adv-title").textContent = hasSets() ? "All Parameters · Dual" : "All Parameters";
  render();
}

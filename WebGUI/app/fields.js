/* fields.js - the controls a setting is shown with, in Basic and in Advanced.

   A control never decides what a value may be: it sends what the visitor chose to model.setValues, and the generator
   says what it thinks of it (model.refreshChecks, shown under the field by pages.markFields).  Every control that can
   take the keyboard carries data-focus, a name that stays the same when the page is drawn again, so the keyboard stays
   where it was. */

import { el, svg, same, fmt, boxText, M, wireChoices, markChoices, closeMenus, tipOf, toast, typedNumber } from "./core.js";
import { val, startVal, where, setValues, setOne, bandLock, numberFor } from "./model.js";
import { labelOf, choiceText, stepOf, LAYER_NUM_CU, CU_NAME, COPPER } from "./labels.js";
import { LAYER_INFO } from "./boardview.js";

const NONE_TIPS = {
  INNER_EDGE_RADIUS_MM: "None: the centre hole follows the RX band (the band start minus the inset)",
  OUTER_EDGE_RADIUS_MM: "None: the outer edge is calculated from the finished stator",
  INSIDE_RADIUS_MM: "None: the RX band is given by its centre and swing, or fitted to the board edges. Inside and outside radius go together",
  OUTSIDE_RADIUS_MM: "None: the RX band is given by its centre and swing, or fitted to the board edges. Inside and outside radius go together",
  RX_R_BASE_MM: "None: the RX band is given by its inside and outside radius, or fitted to the board edges. R Base and A go together",
  RX_A_MM: "None: the RX band is given by its inside and outside radius, or fitted to the board edges. R Base and A go together",
};

/* The help box of a None or Auto switch: that line of the setting's own help; of a locked one, why it is locked. */
function switchTip(name, choice, lock) {
  if (lock) return tipOf("none-locked", lock, { pair: (/set by (.+?)\. /.exec(lock) || [])[1] });
  return tipOf("none", choice === "None" ? NONE_TIPS[name] : null, { setting: name, choice });
}

const key = (file, name, part) => `${file}|${name}|${part}`;
const idOf = (view, file, name) => `${view}-${file.replace(/_Parameters\.py$/, "")}-${name}`;

/* ---- the parts every field has ----------------------------------------------------------------- */
/* The name of a field, its unit, the (i) that shows its help, and whatever stands at the right of the name. */
export function fieldHead(view, file, name, label, unit, ...right) {
  const id = idOf(view, file, name);
  const head = el("div", { class: "field-head" },
    el("span", { class: "field-label", id: `${id}-label` }, label, unit ? el("span", { class: "unit" }, ` ${unit}`) : null),
    el("button", { type: "button", class: "info-dot", "aria-label": `Help: ${label}`, "data-help": name, "data-help-file": file,
      "data-focus": key(file, name, "help") }, "i"));
  head.dataset.help = name; head.dataset.helpFile = file;
  head.append(...right.filter(Boolean));
  return head;
}
/* The field: its head, its control, and the place the generator's message about its value is shown in. */
export function fieldBox(view, file, name, head, body, cls = "") {
  const id = idOf(view, file, name);
  return el("div", { class: `field ${cls}`.trim(), "data-file": file, "data-name": name, id },
    head, body, el("p", { class: "field-error", id: `${id}-error`, role: "alert", hidden: true }));
}
const labelled = (view, file, name) => ({ "aria-labelledby": `${idOf(view, file, name)}-label`, "aria-describedby": `${idOf(view, file, name)}-error` });

/* a switch with a word beside it */
function switchRow({ on, word, focus, cls = "", disabled = false, tip = null, label = null, change }) {   // tip: tipOf(...)
  const cb = el("input", { type: "checkbox", role: "switch", "data-focus": focus, disabled, "aria-label": label });
  cb.checked = !!on;
  const text = el("span", {}, typeof word === "function" ? word(cb.checked) : word);
  cb.addEventListener("change", () => { if (typeof word === "function") text.textContent = word(cb.checked); change(cb.checked); });
  return el("label", { class: `switch-row ${cls}`.trim(), ...(tip || {}) }, el("span", { class: "switch" }, cb, el("span", { class: "knob" })), text);
}

/* a row of choices of which one is on */
function segmented({ view, file, name, options, value, focus = "seg", pick }) {
  const seg = el("div", { class: "segmented", role: "radiogroup", ...labelled(view, file, name) });
  options.forEach(([, text], i) => seg.append(el("button", { type: "button", role: "radio", "data-key": i, "data-focus": key(file, name, `${focus}${i}`) }, text)));
  markChoices(seg, (b) => same(options[+b.dataset.key][0], value));
  wireChoices(seg, (b) => { const x = options[+b.dataset.key][0]; markChoices(seg, (o) => o === b); pick(x); });
  return seg;
}

/* a menu of choices (more than three, or long words): a button that opens a list; arrow keys, Enter and Esc work */
function dropdown({ view, file, name, options, value, pick }) {
  const dd = el("div", { class: "dropdown" });
  const menu = el("div", { class: "dropdown-content", role: "listbox", ...labelled(view, file, name) });
  const names = labelled(view, file, name), valueId = `${idOf(view, file, name)}-value`;
  // the button is named by the setting's label and by the choice it shows ("TX Shape Stepped Diagonal")
  const btn = el("button", { type: "button", class: "dropdown-btn", "aria-haspopup": "listbox", "aria-expanded": "false",
    "data-focus": key(file, name, "menu"), ...names, "aria-labelledby": `${names["aria-labelledby"]} ${valueId}` },
    el("span", { id: valueId }, choiceText(name, value)), el("span", { class: "arrow", "aria-hidden": "true" }, "▾"));
  const items = options.map((o) => el("button", { type: "button", role: "option", tabindex: -1, class: same(o, value) ? "on" : "",
    "aria-selected": String(same(o, value)), onclick: () => { open(false); pick(o); } }, choiceText(name, o)));
  menu.append(...items);
  function open(on, focusItem) {
    closeMenus(dd);
    dd.classList.toggle("open", on);
    btn.setAttribute("aria-expanded", String(on));
    if (on && focusItem) (items.find((i) => i.classList.contains("on")) || items[0]).focus();
  }
  btn.addEventListener("click", (e) => { e.stopPropagation(); open(!dd.classList.contains("open"), e.detail === 0); });
  btn.addEventListener("keydown", (e) => { if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); open(true, true); } });
  menu.addEventListener("keydown", (e) => {
    const i = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); items[(i + 1) % items.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); items[(i - 1 + items.length) % items.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); items[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); items[items.length - 1].focus(); }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); open(false); btn.focus(); }
    else if (e.key === "Tab") open(false);
  });
  dd.append(btn, menu);
  return dd;
}

/* A number box with something typed into it that is not a number: the value stays, and the page says so. */
function notNumber(input, back) {
  const typed = input.value.trim();
  input.value = back;
  if (typed) toast(`“${typed.slice(0, 24)}” is not a number: the value stays ${back}`, 4000);
}

/* ---- Basic -------------------------------------------------------------------------------------- */
/* Basic's fields change a value with from = "basic": the page then leaves the Basic controls as they are (a slider
   being dragged must not be drawn again under the mouse). */
function noneSwitch(file, name, on) {
  const lock = bandLock(file, name);
  return switchRow({ on, word: lock ? "None · Locked" : "None", focus: key(file, name, "none"), cls: "small none-switch" + (lock ? " locked" : ""),
    disabled: !!lock, tip: switchTip(name, "None", lock), label: `${labelOf(name).text}: None`,
    change: (checked) => {
      if (checked) M().lastNumbers[file][name] = val(file, name);
      setOne(file, name, checked ? null : numberFor(file, name), "basic-none");
    } });
}

export function numberField({ file, name, label, unit, min, max, step, sliderStep = step, slider, ticks, note, none }) {
  const v = val(file, name), isNone = v === null;
  const shown = isNone ? numberFor(file, name) : v;            // a None field keeps showing the number it would return to
  const aria = labelled("b", file, name);
  const input = el("input", { type: "text", inputmode: "decimal", value: isNone ? "None" : boxText(v), disabled: isNone, autocomplete: "off",
    "data-focus": key(file, name, "text"), ...aria });
  const range = slider ? el("input", { type: "range", min: slider[0], max: slider[1], step: sliderStep, value: shown, disabled: isNone,
    "data-focus": key(file, name, "range"), ...aria }) : null;
  const clamp = (x) => Math.min(max, Math.max(min, x));
  const fit = () => { if (input.value.length > 7) input.style.setProperty("width", `${input.value.length + 1}ch`); else input.style.removeProperty("width"); };
  fit();                                                       // a value with more places than Basic's steps (typed in Advanced) is shown whole
  const now = () => { const x = val(file, name); return typeof x === "number" ? x : min; };       // a value of another kind (from a file): count from the lowest
  const commit = (x, src) => {
    if (!Number.isFinite(x)) { notNumber(input, boxText(val(file, name))); return; }
    x = clamp(Math.round(x / step) * step);
    x = Math.round(x * 1000) / 1000;
    input.value = boxText(x);
    fit();
    if (range && src !== "range") range.value = x;
    setOne(file, name, x, "basic");
  };
  input.addEventListener("change", () => commit(typedNumber(input.value), "change"));
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowUp" || e.key === "ArrowDown") { e.preventDefault(); commit((typedNumber(input.value) || 0) + (e.key === "ArrowUp" ? step : -step)); }
  });
  if (range) range.addEventListener("input", () => commit(parseFloat(range.value), "range"));
  const stepper = el("span", { class: "stepper" },
    el("button", { type: "button", "aria-label": `${label}: less`, disabled: isNone, "data-focus": key(file, name, "less"), onclick: () => commit(now() - step) }, "−"),
    input,
    el("button", { type: "button", "aria-label": `${label}: more`, disabled: isNone, "data-focus": key(file, name, "more"), onclick: () => commit(now() + step) }, "+"));
  const head = fieldHead("b", file, name, label, unit ? `(${unit})` : "",
    note !== undefined ? el("span", { class: "field-note", "data-note": name }, note) : null,
    none ? noneSwitch(file, name, isNone) : null);
  // tick labels sit under the track itself, each at its value (the thumb is 20 px, so the track runs 10 px in)
  const withTicks = !!(range && ticks);
  const track = withTicks ? el("div", { class: "range-wrap" }, range, el("div", { class: "ticks", "aria-hidden": "true" }, ticks.map((t) =>
    el("span", { style: { left: `calc(10px + (100% - 20px) * ${(parseFloat(t) - slider[0]) / (slider[1] - slider[0])})` } }, t)))) : range;
  return fieldBox("b", file, name, head, el("div", { class: "num-row" }, stepper, track), withTicks ? "has-ticks" : "");
}

export function segmentedField({ file, name, label, options, note, value = val(file, name), from = "basic" }) {
  const head = fieldHead("b", file, name, label, "", note !== undefined ? el("span", { class: "field-note", "data-note": name }, note) : null);
  return fieldBox("b", file, name, head, segmented({ view: "b", file, name, options, value, pick: (x) => setOne(file, name, x, from) }));
}

export function boolField({ file, name, label }) {
  return fieldBox("b", file, name, fieldHead("b", file, name, label, ""),
    switchRow({ on: !!val(file, name), word: (on) => (on ? "On" : "Off"), focus: key(file, name, "switch"), label,
      change: (on) => setOne(file, name, on, "basic") }));
}

/* ---- the TX layout cards (approved by Roland) -------------------------------------------------- */
/* TX layouts offered as cards (from the examples in TX_Parameters.py).  A card sets only the TX and layer settings.  A
   series TX goes around the RX fingers on its layer, so the fingers must run out past the go-around brackets; RX Tab
   Length is exact and a card leaves it alone, so when it is too short the check names the length the design needs. */
export const PRESETS = [
  { id: "2-bottom", layers: 2, name: "Single On Bottom", note: "The original, proven layout",
    set: { PCB_LAYERS: 2, TX_WIRING: "single", TX_LAYER_A: 4, TX_LAYER_B: 1 } },
  { id: "2-top", layers: 2, name: "Single On Top", note: "Next to the rotor: more signal in the model",
    set: { PCB_LAYERS: 2, TX_WIRING: "single", TX_LAYER_A: 1, TX_LAYER_B: 4 } },
  { id: "2-series", layers: 2, name: "Series Top + Bottom", note: "The fingers go around the Top turns",
    set: { PCB_LAYERS: 2, TX_WIRING: "series", TX_LAYER_A: 1, TX_LAYER_B: 4 } },
  { id: "4-bottom", layers: 4, name: "Single On Bottom", note: "RX on Top + Inner-1",
    set: { PCB_LAYERS: 4, TX_WIRING: "single", TX_LAYER_A: 4, TX_LAYER_B: 1, RX_LAYER_A: 1, RX_LAYER_B: 2 } },
  { id: "4-renesas", layers: 4, name: "Series Top + Inner-2", note: "The Renesas IPS2200 reference",
    set: { PCB_LAYERS: 4, TX_WIRING: "series", TX_LAYER_A: 1, TX_LAYER_B: 3, RX_LAYER_A: 1, RX_LAYER_B: 2 } },
  { id: "4-inner1", layers: 4, name: "Series Top + Inner-1", note: "Series on Top and Inner-1, the fingers go around the Top turns",
    set: { PCB_LAYERS: 4, TX_WIRING: "series", TX_LAYER_A: 1, TX_LAYER_B: 2, RX_LAYER_A: 1, RX_LAYER_B: 2 } },
];
const PRESET_NAMES = ["PCB_LAYERS", "TX_WIRING", "TX_LAYER_A", "TX_LAYER_B", "RX_LAYER_A", "RX_LAYER_B"];
function presetValues(set) {
  const v = {};
  for (const n of PRESET_NAMES) { const f = where(n, set); v[n] = f ? val(f, n) : undefined; }
  if (typeof v.TX_WIRING === "string") v.TX_WIRING = v.TX_WIRING.toLowerCase();
  return v;
}
function presetOf(v) {
  for (const p of PRESETS) {
    if (Object.entries(p.set).every(([k, x]) => {
      if (k === "TX_LAYER_B" && v.TX_WIRING === "single") return true;     // not used by a one-layer TX
      if ((k === "RX_LAYER_A" || k === "RX_LAYER_B") && v.PCB_LAYERS === 2) return true;
      return same(v[k], x);
    })) return p.id;
  }
  return null;
}
function presetCard(p, v, selected, i, set) {
  const w = Object.assign({}, v, p.set);
  const layers = p.layers === 2 ? [1, 4] : [1, 2, 3, 4];
  const rx = p.layers === 2 ? [1, 4] : [w.RX_LAYER_A, w.RX_LAYER_B];
  const tx = w.TX_WIRING !== "single" ? [w.TX_LAYER_A, w.TX_LAYER_B] : [w.TX_LAYER_A];
  const W = 100, H = 54, gap = H / (layers.length + 1);
  const pic = svg("svg", { viewBox: `0 0 ${W} ${H}`, "aria-hidden": "true" },
    svg("rect", { x: 2, y: gap / 2, width: W - 4, height: H - gap, rx: 3, class: "card-board" }));
  layers.forEach((n, k) => {
    const y = gap * (k + 1), colour = { "--c": `var(${LAYER_INFO[LAYER_NUM_CU[n]].css})` };
    if (rx.includes(n)) pic.append(svg("path", { d: `M8 ${y} q8 -5 16 0 t16 0 t16 0`, class: "card-rx", style: colour }));
    if (tx.includes(n)) for (let j = 0; j < 3; j++) pic.append(svg("rect", { x: 64 + j * 10, y: y - 2.2, width: 7, height: 4.4, rx: 1, class: "card-tx", style: colour }));
  });
  return el("button", { type: "button", class: "slide" + (selected ? " selected" : ""), role: "radio", "aria-checked": String(selected),
    ...tipOf(`preset:${p.id}`, `${p.name}: ${p.note}`, { name: p.name, layers: p.layers, sets: Object.entries(p.set).map(([k, x]) =>
      [labelOf(k).text, choiceText(k, x) + (k === "TX_LAYER_B" && p.set.TX_WIRING === "single" ? " (not used by a one-layer TX)" : "")]) }),
    "data-key": i, "data-focus": key(`set${set}`, "TX_LAYOUT", p.id) },
    pic, el("span", { class: "slide-name" }, p.name));
}
/* The cards of the board's layer count, for one coil set; view: "b" (Basic) or "a" (Advanced). */
export function txLayoutField(view, set = M().set) {
  const v = presetValues(set), current = presetOf(v), file = where("TX_WIRING", set);
  const shown = PRESETS.filter((p) => p.layers === v.PCB_LAYERS);
  const head = el("div", { class: "field-head", "data-help": "TX_WIRING", "data-help-file": file },
    el("span", { class: "field-label", id: `${view}-txlayout-label` }, "TX Layout"),
    el("button", { type: "button", class: "info-dot", "aria-label": "Help: TX Layout", "data-help": "TX_WIRING", "data-help-file": file }, "i"),
    el("span", { class: "field-note" }, current ? PRESETS.find((p) => p.id === current).note : view === "a" ? "Custom (set below)" : "Custom (set in Advanced)"));
  const cards = el("div", { class: "slider", role: "radiogroup", "aria-labelledby": `${view}-txlayout-label` },
    shown.map((p, i) => presetCard(p, v, p.id === current, i, set)));
  markChoices(cards, (b) => b.classList.contains("selected"));
  wireChoices(cards, (b) => {
    const p = shown[+b.dataset.key];
    setValues(Object.entries(p.set).map(([n, x]) => [where(n, set), n, x]).filter((c) => c[0]), "preset");
  });
  return el("div", { class: "field" }, head, cards);
}

/* ---- Advanced ------------------------------------------------------------------------------------ */
function stepper({ file, name, value, step = 0.001, integer = false, disabled = false, min = null, commit }) {
  const text = value == null ? "" : boxText(value), num = typeof value === "number" ? value : 0;   // a text from a file: − and + count from 0
  const input = el("input", { type: "text", inputmode: "decimal", value: text, disabled, autocomplete: "off", "data-focus": key(file, name, "text"), ...labelled("a", file, name) });
  if (text.length > 5) input.style.setProperty("width", `${text.length + 2}ch`);       // 3500000 Hz fits
  const done = (x) => {
    if (!Number.isFinite(x)) { notNumber(input, text); return; }
    if (integer) x = Math.round(x);
    commit(Math.round(x * 1e6) / 1e6);
  };
  input.addEventListener("change", () => done(typedNumber(input.value)));
  const label = labelOf(name).text;
  return el("span", { class: "stepper" },
    el("button", { type: "button", disabled, "aria-label": `${label}: less`, "data-focus": key(file, name, "less"),
      onclick: () => done(min == null ? num - step : Math.max(min, num - step)) }, "−"), input,
    el("button", { type: "button", disabled, "aria-label": `${label}: more`, "data-focus": key(file, name, "more"),
      onclick: () => done(num + step) }, "+"));
}

// the number a step setting shows when its Auto switch is turned off (the values before the chord tolerances)
const STEPS_WHEN_NOT_AUTO = { TX_STEPS: 300, ROTOR_ARC_STEPS_PER_SECTOR: 48 };

function choiceWidget(p, v, set, disabled = false) {
  const { file, name } = p, values = (p.options || {}).values || [];
  const current = typeof v === "string" && p.options.ci ? v.toLowerCase() : v;
  if (values.length <= 3 && values.every((x) => choiceText(name, x).length <= 12)) {
    const seg = segmented({ view: "a", file, name, options: values.map((x) => [x, choiceText(name, x)]), value: current, pick: set });
    if (disabled) seg.querySelectorAll("button").forEach((b) => (b.disabled = true));
    return seg;
  }
  const dd = dropdown({ view: "a", file, name, options: values, value: current, pick: set });
  if (disabled) dd.firstChild.disabled = true;
  return dd;
}

function layerSwitches(p, v, layers, set) {
  const box = el("div", { class: "auto-row wrap", role: "group", ...labelled("a", p.file, p.name) });
  const list = Array.isArray(v) ? v : [];                      // a value of another kind (from a file) shows as no layer
  for (const cu of layers) {
    box.append(switchRow({ on: list.includes(cu), word: CU_NAME[cu], focus: key(p.file, p.name, cu),
      change: (on) => { const now = new Set(list); if (on) now.add(cu); else now.delete(cu); set(layers.filter((x) => now.has(x))); } }));
  }
  return box;
}

/* The control of one setting in Advanced, by the kind the generator's table gives it. */
export function advancedWidget(p) {
  const { file, name } = p, v = val(file, name), k = p.kind, o = p.options || {};
  const set = (x) => setOne(file, name, x, "advanced");
  const m = M();

  if (p.override) {
    /* a Dual set's own copy of a board value: None means "as the board", shown as a switch (Board Value) */
    const board = where(name, 0), boardVal = board ? val(board, name) : undefined, isBoard = v === null;
    const shown = isBoard ? boardVal : v;
    const body = k === "choice" ? choiceWidget(p, shown, set, isBoard)
      : stepper({ file, name, value: shown, step: stepOf(p), integer: k === "int", disabled: isBoard, commit: set });
    return el("div", { class: "auto-row" },
      switchRow({ on: isBoard, word: "Board Value", focus: key(file, name, "board"), label: `${labelOf(name).text}: use the board's value`,
        change: (on) => { if (on) { m.lastNumbers[file][name] = v; set(null); } else set(m.lastNumbers[file][name] ?? boardVal); } }),
      body);
  }
  if (k === "bool") return switchRow({ on: !!v, word: (on) => (on ? "On" : "Off"), focus: key(file, name, "switch"), label: labelOf(name).text, change: set });
  if (k === "choice" || k === "ic") return choiceWidget(p, v, set);
  if (k === "num" || k === "int" || k === "mask_expansion") {
    // the chord tolerances stop at their lowest value (0.001 mm) when stepped down; a typed lower value gets the generator's message
    return stepper({ file, name, value: v, step: stepOf(p), integer: k === "int", min: /CHORD_TOLERANCE_MM$/.test(name) ? o.lo : null, commit: set });
  }
  if (k === "num_or_none" || k === "auto_or_num" || k === "steps" || k === "auto_or_int") {
    const none = k === "num_or_none";
    const isAuto = none ? v === null : (typeof v === "string" && v.toLowerCase() === "auto");
    const word = none ? "None" : "Auto";
    const lock = none ? bandLock(file, name) : null;
    const fallback = typeof p.default === "number" ? p.default : (k === "steps" ? 200 : (STEPS_WHEN_NOT_AUTO[name] ?? o.lo ?? 1));
    const back = isAuto ? (none ? numberFor(file, name) : (m.lastNumbers[file][name] ?? fallback)) : v;
    return el("div", { class: "auto-row" },
      switchRow({ on: isAuto, word: lock ? `${word} · Locked` : word, focus: key(file, name, "auto"), cls: lock ? "locked" : "", disabled: !!lock,
        tip: switchTip(name, none ? "None" : "auto", lock), label: `${labelOf(name).text}: ${word}`,
        change: (on) => { if (on) { m.lastNumbers[file][name] = typeof v === "number" ? v : back; set(none ? null : "auto"); } else set(back); } }),
      stepper({ file, name, value: isAuto ? null : v, step: stepOf(p), integer: k === "steps" || k === "auto_or_int", disabled: isAuto, commit: set }));
  }
  if (k === "str_or_none") {
    const isNone = v === null;
    const t = el("input", { class: "text-input", value: isNone ? "" : boxText(v), disabled: isNone, autocomplete: "off", spellcheck: "false",
      "data-focus": key(file, name, "text"), ...labelled("a", file, name) });
    t.addEventListener("change", () => set(t.value));
    return el("div", { class: "auto-row" },
      switchRow({ on: isNone, word: "None", focus: key(file, name, "auto"), label: `${labelOf(name).text}: None`,
        change: (on) => { if (on) { m.lastNumbers[file][name] = v; set(null); } else set(m.lastNumbers[file][name] ?? (typeof startVal(file, name) === "string" ? startVal(file, name) : "")); } }),
      t);
  }
  if (k === "rotor_layers") return layerSwitches(p, v, ["F.Cu", "B.Cu"], set);
  if (k === "layer_list") return layerSwitches(p, v, COPPER.filter((cu) => (o.values || COPPER).includes(cu)), set);
  if (k === "colour") {
    const ok = typeof v === "string" && /^#[0-9a-f]{6}$/i.test(v);
    const picker = el("input", { type: "color", class: "colour-input", value: ok ? v.toLowerCase() : "#ffffff", "data-focus": key(file, name, "pick"), ...labelled("a", file, name) });
    const t = el("input", { class: "text-input short", value: v == null ? "" : boxText(v), autocomplete: "off", spellcheck: "false", "data-focus": key(file, name, "text"), ...labelled("a", file, name) });
    picker.addEventListener("change", () => set(picker.value.toUpperCase()));
    t.addEventListener("change", () => set(/^#[0-9a-f]{6}$/i.test(t.value.trim()) ? t.value.trim().toUpperCase() : t.value));
    return el("div", { class: "auto-row" }, picker, t);
  }
  // str, net, file
  const t = el("input", { class: "text-input", value: v == null ? "" : boxText(v), autocomplete: "off", spellcheck: "false", "data-focus": key(file, name, "text"), ...labelled("a", file, name) });
  t.addEventListener("change", () => set(t.value));
  return t;
}

/* One setting of Advanced: its name, its Python name, the way back to the published value, and its control. */
export function advancedField(p) {
  const lab = labelOf(p.name);
  // the name in the file and the arrow are one piece: on a narrow panel they go to the next line together
  const head = fieldHead("a", p.file, p.name, lab.text, lab.unit, el("span", { class: "field-side" },
    el("span", { class: "field-note" }, el("span", { class: "mono-name" }, p.name)),
    el("button", { type: "button", class: "reset-one", "aria-label": `${lab.text}: back to the starting value`, ...tipOf("reset-one", "Back to the starting value"),
      "data-focus": key(p.file, p.name, "reset"), onclick: () => setOne(p.file, p.name, startVal(p.file, p.name), "advanced") }, "↺")));
  return fieldBox("a", p.file, p.name, head, advancedWidget(p));
}

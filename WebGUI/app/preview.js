/* preview.js - the preview panel: the boards of the last good run (Stator, Rotor, Overlay), the generator's two
   pictures, and the buttons that show, hide and highlight layers, coils and coil sets.

   Everything here changes only what is shown: the boards and the downloads stay as the generator made them. */

import { $, el, svg, clear, M, toast, markChoices, wireChoices, tipOf } from "./core.js";
import { BoardView, LAYER_INFO, SILK_LAYERS } from "./boardview.js";
import { hasSets, where } from "./model.js";
import { COPPER, CU_NAME } from "./labels.js";

export let view = null;
let shows = "overlay";                       // what the panel shows: stator | rotor | overlay | pictures

const swatch = (css) => el("span", { class: "sw", style: { background: `var(${css})` } });
const chipKey = (e, act) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); act(); } };

/* ---- layer chips: the copper layers, the vias, the silkscreen marks ----------------------------- */
function chip({ off, locked, tip, icon, text, toggle, enter, leave }) {
  if (locked) return el("span", { class: "layer-chip locked", role: "switch", "aria-checked": "false", "aria-disabled": "true", ...tip }, icon, text);
  return el("span", { class: "layer-chip" + (off ? " off" : ""), role: "switch", tabindex: 0, "aria-checked": String(!off), ...tip,
    "data-focus": `chip|${text}`, onclick: toggle, onkeydown: (e) => chipKey(e, toggle), onmouseenter: enter, onmouseleave: leave, onfocus: enter, onblur: leave }, icon, text);
}
function renderLayerToggles() {
  const box = $("layer-toggles"), focused = document.activeElement && box.contains(document.activeElement) ? document.activeElement.dataset.focus : null;
  clear(box);
  const present = view.layersPresent();                     // null before the first board: every chip works
  for (const cu of COPPER) {
    const name = CU_NAME[cu], off = view.hidden.has(cu);
    box.append(chip({ off, locked: present && !present.has(cu), icon: swatch(LAYER_INFO[cu].css), text: name,
      tip: present && !present.has(cu) ? tipOf("layer-missing", `This board has no copper on the ${name} layer (${cu})`, { layer: name, cu })
        : off ? tipOf("layer-off", `Show the ${name} copper (${cu})`, { layer: name, cu })
          : tipOf("layer", `Hover to highlight the ${name} copper (${cu}), click to hide it (the preview only)`, { layer: name, cu }),
      toggle: () => { view.toggleLayer(cu); view.setLayerHighlight(null); renderLayerToggles(); },
      enter: () => { if (!view.hidden.has(cu)) view.setLayerHighlight(cu); }, leave: () => view.setLayerHighlight(null) }));
  }
  // vias: hide / show like a layer; hovering makes tiny vias big enough to see (preview only)
  const viasOff = view.hidden.has("Vias");
  box.append(chip({ off: viasOff, icon: el("span", { class: "via-icon" }), text: "Vias",
    tip: viasOff ? tipOf("vias-off", "Show the vias")
      : tipOf("vias", "Show or hide the vias. Hover to enlarge small vias to at least 6 px (the preview only, the boards are unchanged)"),
    toggle: () => { view.setViaBoost(false); view.toggleLayer("Vias"); renderLayerToggles(); },
    enter: () => { if (!view.hidden.has("Vias")) view.setViaBoost(true); }, leave: () => view.setViaBoost(false) }));
  // the silkscreen suggestion: where to cut the traces and place the lead vias (drawn on the board's silkscreen)
  for (const layer of SILK_LAYERS) {
    const side = layer === "F.SilkS" ? "Top" : "Bottom", off = view.hidden.has(layer), none = view.hasBoard && !view.hasSilk(layer);
    box.append(chip({ off, locked: none, icon: swatch("--silk"), text: `Silk ${side}`,
      tip: none ? tipOf("silk-missing", `This board has no silkscreen marks on its ${side.toLowerCase()} side (${layer})`, { side: side.toLowerCase(), cu: layer })
        : off ? tipOf("silk-off", `Show the silkscreen suggestion on the ${side.toLowerCase()} side (${layer})`, { side: side.toLowerCase(), cu: layer })
          : tipOf("silk", `Hide the silkscreen suggestion on the ${side.toLowerCase()} side (${layer}; the preview only)`, { side: side.toLowerCase(), cu: layer }),
      toggle: () => { view.toggleLayer(layer); renderLayerToggles(); } }));
  }
  if (focused) { const again = [...box.querySelectorAll("[data-focus]")].find((n) => n.dataset.focus === focused); if (again) again.focus(); }
}

/* ---- Sin / Cos / TX Loops, Set 1 / Set 2 (top right) and Origin (beside Fit) -------------------- */
const NET_BUTTONS = [
  { role: "sin", text: "Sin Loops", what: "the SIN coil (RX phases 0 / 2)", icon: "M1 7 C4 -1 6 -1 9 7 S14 15 17 7" },
  { role: "cos", text: "Cos Loops", what: "the COS coil (RX phases 1 / 3)", icon: "M1 3 C3 3 4 11 9 11 S15 3 17 3" },
  { role: "tx", text: "TX Loops", what: "the TX coil (the outer ring)", icon: "M9 1.5 A5.5 5.5 0 1 1 8.99 1.5 M9 4 A3 3 0 1 1 8.99 4" },
];
const SET_ICON = { 1: "M9 4.5 A2.5 2.5 0 1 1 8.99 4.5", 2: "M9 1 A6 6 0 1 1 8.99 1" };
function netButton({ off, text, icon, tip, toggle, enter, leave, focus }) {
  return el("button", { type: "button", class: "net-btn" + (off ? " off" : ""), role: "switch", "aria-checked": String(!off), ...tip, "data-focus": focus,
    onclick: toggle, onmouseenter: enter, onmouseleave: leave, onfocus: enter, onblur: leave },
    svg("svg", { viewBox: "0 0 18 14", "aria-hidden": "true" }, svg("path", { d: icon })), text);
}
function renderNetToggles() {
  const box = $("net-toggles"), focused = document.activeElement && (box.contains(document.activeElement) || $("origin-slot").contains(document.activeElement)) ? document.activeElement.dataset.focus : null;
  clear(box);
  if (shows !== "rotor" && shows !== "pictures") {             // the rotor has no coils
    for (const n of NET_BUTTONS) {
      const off = view.hiddenNets.has(n.role);
      box.append(netButton({ off, text: n.text, icon: n.icon, focus: `net|${n.role}`,
        tip: off ? tipOf("net-off", `Show ${n.what}`, { what: n.what }) : tipOf("net", `Hover to highlight ${n.what}, click to hide it (the preview only)`, { what: n.what }),
        toggle: () => { view.toggleNet(n.role); view.setHighlight(null); renderNetToggles(); },
        enter: () => { if (!view.hiddenNets.has(n.role)) view.setHighlight(n.role); }, leave: () => view.setHighlight(null) }));
    }
    if (hasSets()) for (const k of [1, 2]) {
      const off = view.hiddenSets.has(k), what = `coil set ${k} (the ${k === 1 ? "inner" : "outer"} one)`;
      box.append(netButton({ off, text: `Set ${k}`, icon: SET_ICON[k], focus: `set|${k}`,
        tip: off ? tipOf("net-off", `Show ${what}`, { what }) : tipOf("net", `Hover to highlight ${what}, click to hide it (the preview only)`, { what }),
        toggle: () => { view.toggleSet(k); view.setSetHighlight(null); renderNetToggles(); },
        enter: () => { if (!view.hiddenSets.has(k)) view.setSetHighlight(k); }, leave: () => view.setSetHighlight(null) }));
    }
  }
  // the board centre (an icon beside Fit): hover colours the marker, click hides it
  const slot = clear($("origin-slot"));
  slot.append(el("button", { type: "button", class: "glass-btn small icon-btn" + (view.showOrigin ? "" : " off"), role: "switch",
    "aria-checked": String(view.showOrigin), "aria-label": "Origin", "data-focus": "origin",
    ...(view.showOrigin ? tipOf("origin", "The board centre (origin). Hover to highlight it, click to hide it") : tipOf("origin-off", "Show the board centre (origin)")),
    onclick: () => { view.toggleOrigin(); view.setOriginBoost(false); renderNetToggles(); },
    onmouseenter: () => { if (view.showOrigin) view.setOriginBoost(true); }, onmouseleave: () => view.setOriginBoost(false) },
    svg("svg", { viewBox: "0 0 24 24", "aria-hidden": "true" }, svg("circle", { cx: 12, cy: 12, r: 2.6, class: "origin-dot" }), svg("circle", { cx: 12, cy: 12, r: 6.5 }))));
  if (focused) { const again = [...document.querySelectorAll("#net-toggles [data-focus], #origin-slot [data-focus]")].find((n) => n.dataset.focus === focused); if (again) again.focus(); }
}

/* ---- the generator's two pictures ------------------------------------------------------------------ */
const PICTURES = [
  { end: "_Representative.svg", title: "Representative", note: "The idea of the board: a few thick turns, easy to read" },
  { end: "_Actual.svg", title: "Actual", note: "The copper as it is on the board" },
];
function renderPictures() {
  const m = M(), g = m.good, box = clear($("pictures"));
  if (!g) { box.append(el("p", { class: "hint" }, "Press Generate: the generator draws two pictures of every board it makes.")); return; }
  if (!m.pictures) {
    m.pictures = {};
    for (const f of g.files) if (f.name.endsWith(".svg")) m.pictures[f.name] = URL.createObjectURL(new Blob([g.bytes[f.name]], { type: "image/svg+xml" }));
  }
  let any = false;
  for (const p of PICTURES) {
    const f = g.files.find((x) => x.name.endsWith(p.end));
    if (!f) continue;
    any = true;
    box.append(el("figure", { class: "picture" },
      el("a", { href: m.pictures[f.name], target: "_blank", rel: "noopener", ...tipOf("picture-open", "Open this picture in a new tab") },
        el("img", { src: m.pictures[f.name], alt: `${p.title} picture of ${g.name}: ${p.note.toLowerCase()}` })),
      el("figcaption", {}, el("b", {}, p.title), ` · ${p.note}`)));
  }
  if (!any) box.append(el("p", { class: "hint" }, "This run wrote no pictures."));
}

/* ---- what the panel shows --------------------------------------------------------------------------- */
function pickView(mode) {
  shows = mode;
  const pictures = mode === "pictures";
  markChoices($("view-tabs"), (b) => b.dataset.view === mode);
  $("board-canvas").hidden = pictures;
  $("pictures").hidden = !pictures;
  for (const id of ["canvas-tools", "readout", "layer-toggles"]) $(id).hidden = pictures;
  $("rotor-angle-box").hidden = mode !== "overlay";
  if (pictures) renderPictures();
  else view.setMode(mode);
  renderNetToggles();
  if (!pictures) { renderLayerToggles(); view.fit(); }
}

/* Show the boards of the chosen generator's last good run (none yet: an empty preview). */
export function showBoards(fit = true) {
  const m = M(), g = m.good;
  if (!g) view.clearBoards();
  else {
    const text = (name) => (name && g.bytes[name] ? new TextDecoder().decode(g.bytes[name]) : null);
    const board = where("CENTER_X_MM", 0), b = board ? g.values[board] : {};
    const roles = {}, sets = {};
    for (const f of m.files) {
      const vals = g.values[f.file] || {};
      for (const [name, role] of [["RX_NET_PHASE_0_2", "sin"], ["RX_NET_PHASE_1_3", "cos"], ["TX_NET", "tx"]]) {
        if (typeof vals[name] === "string") { roles[vals[name]] = role; if (f.set) sets[vals[name]] = f.set; }
      }
    }
    view.setBoards(text(g.stator), text(g.rotor), [b.CENTER_X_MM ?? 100, b.CENTER_Y_MM ?? 100]);
    view.setNetRoles(roles, sets);
  }
  if (shows === "pictures") renderPictures();
  renderLayerToggles();
  renderNetToggles();
  if (fit) view.fit();
}

export function initPreview() {
  view = new BoardView($("board-canvas"), $("readout"));     // opens on Overlay
  wireChoices($("view-tabs"), (b) => pickView(b.dataset.view));
  markChoices($("view-tabs"), (b) => b.dataset.view === shows);
  renderLayerToggles();
  renderNetToggles();
  $("btn-fit").addEventListener("click", () => view.fit());
  $("btn-measure").addEventListener("click", (e) => {
    view.measure = !view.measure; view.clearMeasure();     // switching Measure off or on clears every line
    e.currentTarget.classList.toggle("on", view.measure);
    e.currentTarget.setAttribute("aria-pressed", String(view.measure));
    $("measure-help").hidden = !view.measure;              // the S / Z keys, while measuring
    $("board-canvas").classList.toggle("measuring", view.measure);
    view.draw();
  });
  $("btn-fullscreen").addEventListener("click", () => {
    const w = $("canvas-wrap");
    if (document.fullscreenElement) document.exitFullscreen();
    else if (w.requestFullscreen) w.requestFullscreen();
    else if (w.webkitRequestFullscreen) w.webkitRequestFullscreen();
    else toast("This browser cannot show the preview full screen");
  });
  document.addEventListener("fullscreenchange", () => {
    const on = !!document.fullscreenElement, b = $("btn-fullscreen");      // corner brackets out, or in to leave
    b.querySelector("path").setAttribute("d", on ? "M8 3v5H3M16 3v5h5M21 16h-5v5M3 16h5v5" : "M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5");
    b.setAttribute("aria-label", on ? "Exit Fullscreen" : "Fullscreen");
    b.dataset.tip = on ? "Leave full screen (Esc)" : "";
    b.dataset.tipId = on ? "btn-fullscreen-on" : "btn-fullscreen";
    setTimeout(() => view.resize(), 100);
  });
  $("rotor-angle").addEventListener("input", (e) => { view.setRotorAngle(+e.target.value); $("rotor-angle-out").textContent = `${e.target.value}°`; });
  document.addEventListener("keydown", (e) => {
    // Measure: S keeps the finished line and starts a new one, Z removes the last line (not while typing in a field)
    const t = e.target, typing = t.isContentEditable || /^(TEXTAREA|SELECT)$/.test(t.tagName)
      || (t.tagName === "INPUT" && !/^(range|checkbox|radio|button|color)$/.test(t.type));
    if (!view.measure || typing || e.ctrlKey || e.metaKey || e.altKey) return;
    const key = e.key.toLowerCase();
    if (key === "s") {
      if (view.mLocked.length >= BoardView.MAX_LOCKED) { toast(`${BoardView.MAX_LOCKED} lines kept: that is the limit`); return; }
      view.lockMeasure();                                  // quiet: a message only at the limit
    }
    if (key === "z") view.undoMeasure();
  });
}

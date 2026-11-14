/* tips.js - the help box (tooltip) that opens beside a control.

   The words are in tips.json (written by tools/build_tips.py from tools/tips_words.py); this file only draws them.
   A control asks for its box with:
     data-tip-id="name"        a tip of tips.json ("controls"); data-tip-args='{"name": "value"}' fills its {name} places
     data-tip-id="preset:id"   a TX layout card ("presets"); its name and what it sets come in data-tip-args
     data-help="NAME"          a setting ("params"), with data-help-file: the page adds the setting's own name, unit,
                               choices, allowed range, its value in the file and the link to the reference
     data-tip="text"           the plain text, shown while tips.json is not there or has no such tip
   A setting tips.json does not name shows the comment beside it in its parameter file.

   One layout, top to bottom, and only the parts a tip has: where it is, the name with its unit, the name in the
   file, one sentence, the choices (the file's one marked), facts, formulas, the caveat, keys, a picture, the value
   in the file with the link.

   It opens when the mouse rests on the control (at once on an (i)) or the keyboard reaches it; the mouse may move
   onto the box; it closes with Esc (the focus stays), a click, a scroll of the page, or when the mouse and the
   keyboard have left.  Values are set as text, never as HTML. */

import { $, el, clear, M, state, same } from "./core.js";
import { labelOf, groupTitle, choiceText, showValue } from "./labels.js";

const WIKI = "https://github.com/RolandThsive/Sinusoidal-Inductive-Encoders-Coil-Generator/wiki/";
const REFERENCE = { single: "Parameter-Reference-Single-Coil-Set-Generator", dual: "Parameter-Reference-Dual-Coil-Set-Generator" };
const PICTURES = "docs/tooltips/pictures/";

/* the plain texts of the fixed controls: shown when tips.json cannot be read */
const PLAIN = {
  "gen-menu": "Which generator the page runs. Your settings of each generator are kept when you switch. Arc and Linear are not available.",
  "gen-single": "The Single Coil Set Generator: one sine and cosine RX pair with one TX coil.",
  "gen-dual": "The Dual Coil Set Generator: two coil sets on one board, an inner and an outer one, each with its own rotor ring (a coarse and a fine track).",
  "mode-basic": "The main settings of each category, with sliders",
  "mode-advanced": "Every setting of every parameter file, as the desktop generator has them",
  "btn-help": "Open the quick guide to choosing the parameters (a new tab)",
  "btn-import": "Load a design from files: parameter files (.py), a zip of them, or the Parameters.txt of a run. Single and Dual designs are both read.",
  "btn-export": "Download the parameter files with your settings, ready for the desktop generator",
  "btn-share": "Copy a link that opens this page with your settings",
  "nav-back": "Back to the page you came from",
  "nav-home": "The blog's front page",
  "find": "Type a part of a setting's name, its Python name or a word of its help: every match of every file is listed",
  "strict": "Strict: every warning stops the run, as --strict does on the desktop (GENERATOR_MODE)",
  "btn-reset": "Put every setting of this generator back to its published value",
  "btn-check": "Run only the generator's checks of the settings: quick, and nothing is built",
  "btn-generate": "Run the generator with these settings (Ctrl + Enter)",
  "view-stator": "The stator board alone",
  "view-rotor": "The rotor board alone",
  "view-overlay": "The rotor's copper drawn over the stator, at the angle of the Rotor Angle slider",
  "view-pictures": "The two pictures the generator draws of the board (SVG files of the run)",
  "btn-fullscreen": "Show the preview full screen (Esc to leave)",
  "btn-fit": "Fit the board to the preview (also: double-click, or the 0 key)",
  "btn-measure": "Measure a distance: click two points on the board",
  "readout": "The position of the mouse on the board, from the board centre",
  "rotor-angle": "Turn the rotor over the stator (the preview only)",
  "show-info": "Also list the generator's notes (info), not only its warnings and errors",
  "btn-runtext": "Everything the generator printed in this run, as on the desktop",
  "btn-files": "Every file of this run, to download one by one",
  "btn-cancel": "Stop this run. Python starts again, which takes a few seconds",
};

let TIPS = null;                                            // tips.json, once it is read
/* Read tips.json.  The page works without it: every tip then shows its plain text. */
export async function loadTips() {
  try {
    const r = await fetch("tips.json", { cache: "no-cache" });
    const t = r.ok ? await r.json() : null;
    if (t && t.params && t.controls && t.presets) TIPS = t;
  } catch (e) { /* no tips.json: the plain texts */ }
  return !!TIPS;
}
/* The words of a setting's help, for Find A Setting. */
export function tipWords(p) {
  const t = TIPS && TIPS.params[p.name];
  if (!t) return p.help || "";
  return [t.lead, t.note, ...Object.values(t.choices || {}), ...(t.facts || []).flat(), ...(t.formula || [])].filter(Boolean).join(" ");
}

/* ---- the parts of a box ----------------------------------------------------------------------- */
/* text with its {name} places filled from args; null when a place has no value (the part is then left out) */
function filled(text, args) {
  let missing = false;
  const out = String(text).replace(/\{(\w+)\}/g, (all, k) => {
    const x = args ? args[k] : undefined;
    if (x === undefined || x === null || x === "") { missing = true; return ""; }
    return String(x);
  });
  return missing ? null : out;
}
function plain(pop, text) {                                  // \n starts a line, **text** is bold
  pop.classList.add("plain");
  text.split("\n").forEach((line, n) => {
    if (n) pop.append(el("br"));
    line.split("**").forEach((part, i) => part && pop.append(i % 2 ? el("b", {}, part) : part));
  });
}
function facts(rows, args) {
  const list = el("dl", { class: "tip-facts" });
  for (const [label, value] of rows) {
    const text = filled(value, args);
    if (text !== null) list.append(el("dt", {}, label), el("dd", {}, text));
  }
  return list.children.length ? list : null;
}
function parts(pop, t, args) {
  if (t.facts) pop.append(facts(t.facts, args) || "");
  if (t.formula) pop.append(el("div", { class: "tip-formula" }, t.formula.map((f) => el("div", {}, f))));
  const note = t.note ? filled(t.note, args) : null;
  if (note) pop.append(el("p", { class: "tip-note" }, note));
  if (t.keys) pop.append(el("div", { class: "tip-keys" }, t.keys.flatMap((k, i) => [i ? "+" : null, el("kbd", {}, k)]), t.keysNote ? el("span", {}, t.keysNote) : null));
}
function picture(pop, pic) {
  if (!pic || !pic.file) return;
  // made only now, when the box opens; its width and height keep the box's place while it loads
  pop.append(el("figure", { class: "tip-picture" },
    el("img", { src: PICTURES + pic.file, alt: pic.caption, width: pic.width || 340, height: pic.height || 190, decoding: "async" }),
    el("figcaption", {}, pic.caption)));
}

/* ---- the three kinds of box ------------------------------------------------------------------- */
const fileValue = (p) => (p.override && p.default === null ? "the board's value" : showValue(p.default));
/* the allowed range of a number, in words */
function range(o, unit) {
  if (!o) return null;
  const has = (x) => x !== undefined && x !== null, u = unit ? ` ${unit}` : "";
  if (has(o.lo) && has(o.hi)) return `${o.lo_ex ? "more than " : ""}${showValue(o.lo)} to ${o.hi_ex ? "less than " : ""}${showValue(o.hi)}${u}`;
  if (has(o.lo)) return `${o.lo_ex ? "more than" : "at least"} ${showValue(o.lo)}${u}`;
  if (has(o.hi)) return `${o.hi_ex ? "less than" : "at most"} ${showValue(o.hi)}${u}`;
  return null;
}
/* the choices of a setting: [{word, line, file}], file = the value in the parameter file */
function choices(p, t) {
  const ch = t.choices || {}, d = p.default, out = [];
  const vals = (p.options && p.options.values) || (p.kind === "bool" ? [true, false] : null);
  const key = (v) => Object.keys(ch).find((k) => k.toLowerCase() === (typeof v === "boolean" ? (v ? "true" : "false") : String(v).toLowerCase()));
  const isFile = (v) => same(v, d) || (typeof v === "string" && typeof d === "string" && v.toLowerCase() === d.toLowerCase());
  if (p.override) out.push({ word: "None", line: TIPS.overrideChoice, file: d === null });
  else if ("None" in ch) out.push({ word: "None", line: ch.None, file: d === null });
  if (vals) {
    for (const v of vals) if (v !== null) out.push({ word: choiceText(p.name, v), line: (key(v) && ch[key(v)]) || "", file: isFile(v) });
  } else if ("auto" in ch) out.push({ word: "Auto", line: ch.auto, file: d === "auto" });
  if ("number" in ch) out.push({ word: "A number", line: ch.number, file: typeof d === "number" });
  return out;
}
function chip(c) {
  return el("span", { class: "tip-chip" + (c.file ? " file" : ""), title: c.file ? "The value in the file" : null }, c.word);
}
function settingTip(pop, name, file) {
  const m = M(), p = (m.params[file] || {})[name], t = TIPS && TIPS.params[name];
  if (!p || !t) {                                            // not in tips.json: the comment of the parameter file
    pop.append(el("span", { class: "mono-name" }, name));
    plain(pop, (p && p.help) || "No notes in the parameter file.");
    if (p) pop.append(el("span", { class: "tip-foot" }, el("span", {}, "In the file: ", el("b", {}, fileValue(p)))));
    return;
  }
  const lab = labelOf(name), unit = lab.unit.replace(/[()]/g, "");
  const where = `${p.cat === "Silk" ? "Silkscreen" : p.cat}${p.set ? " " + p.set : ""}`;
  pop.classList.add("rich");
  pop.append(el("div", { class: "tip-eyebrow" }, `${where} · ${groupTitle(p.heading, p.cat)}`),
    el("div", { class: "tip-title" }, el("span", {}, lab.text), unit ? el("span", { class: "tip-pill" }, unit) : null),
    el("div", { class: "tip-key" }, name),
    el("p", { class: "tip-lead" }, t.lead));
  const list = choices(p, t), lines = list.filter((c) => c.line), bare = list.filter((c) => !c.line);
  if (lines.length) pop.append(el("ul", { class: "tip-choices" }, lines.map((c) => el("li", {}, chip(c), el("span", {}, c.line)))));
  if (bare.length) pop.append(el("div", { class: "tip-chips" }, bare.map(chip)));
  const allowed = range(p.options, unit);
  parts(pop, Object.assign({}, t, { facts: [...(t.facts || []), ...(allowed ? [["Allowed", allowed]] : [])] }), null);
  picture(pop, t.picture);
  pop.append(el("div", { class: "tip-foot" }, el("span", {}, "In the file: ", el("b", {}, fileValue(p))),
    el("a", { href: WIKI + REFERENCE[state.gen], target: "_blank", rel: "noopener" }, "Reference")));
}
function presetTip(pop, id, args) {
  const t = TIPS.presets[id];
  if (!t || !args || !args.name) return false;
  pop.classList.add("rich");
  pop.append(el("div", { class: "tip-eyebrow" }, `TX · Layout · ${args.layers} Layers`), el("div", { class: "tip-title" }, el("span", {}, args.name)),
    el("p", { class: "tip-lead" }, t.lead), facts(args.sets || [], null) || "", el("p", { class: "tip-small" }, TIPS.presetFoot));
  return true;
}
function controlTip(pop, id, args) {
  const t = TIPS.controls[id], lead = t ? filled(t.lead, args) : null;
  if (lead === null) return false;                           // no such tip, or a value it needs is missing
  pop.append(el("p", { class: "tip-lead" }, lead));
  parts(pop, t, args);
  if (pop.children.length > 1) pop.classList.add("parts");
  return true;
}
function argsOf(node) {
  try { return node.dataset.tipArgs ? JSON.parse(node.dataset.tipArgs) : null; } catch (e) { return null; }
}
function fill(pop, node) {
  pop.className = "popover";
  if (node.dataset.help) { settingTip(pop, node.dataset.help, node.dataset.helpFile); return true; }
  const id = node.dataset.tipId || "", args = argsOf(node);
  if (TIPS && id === "none" && args) {                       // the None or Auto switch: that line of its setting's own help
    const t = TIPS.params[args.setting];
    const over = args.choice === "None" && Object.values(M().params).some((f) => f[args.setting] && f[args.setting].override);
    args.line = (t && t.choices && t.choices[args.choice]) || (over ? TIPS.overrideChoice : null);
  }
  if (TIPS && id && (id.startsWith("preset:") ? presetTip(pop, id.slice(7), args) : controlTip(pop, id, args))) return true;
  clear(pop);
  const text = node.dataset.tip || PLAIN[id];
  if (text) plain(pop, text);
  return !!text;
}

/* ---- where the box goes ----------------------------------------------------------------------- */
/* Below the control, else above, else beside it; else on the larger side, cut to the room there (it scrolls inside);
   only when no side has room, over the control (Esc shows the control again). */
function place(pop, node) {
  pop.style.removeProperty("max-height");
  const W = document.documentElement.clientWidth, H = document.documentElement.clientHeight, G = 8, E = 6;
  const r = node.getBoundingClientRect(), w = pop.offsetWidth, h = pop.offsetHeight;
  const x = (left) => Math.max(E, Math.min(W - w - E, left)), y = (top) => Math.max(E, Math.min(H - h - E, top));
  let left = x(r.left), top;
  const list = node.closest(".dropdown-content");
  if (list) {                                                // a line of an open menu: beside the menu, never over its lines
    const m = list.getBoundingClientRect();
    top = y(r.top);
    left = m.right + G + w <= W - E ? m.right + G : Math.max(E, m.left - w - G);
  } else if (r.bottom + G + h <= H - E) top = r.bottom + G;
  else if (r.top - G - h >= E) top = r.top - G - h;
  else if (h <= H - 2 * E && r.right + G + w <= W - E) { left = r.right + G; top = y(r.top); }
  else if (h <= H - 2 * E && r.left - G - w >= E) { left = r.left - G - w; top = y(r.top); }
  else {
    const below = H - E - (r.bottom + G), above = r.top - G - E, room = Math.max(below, above);
    if (room >= 96) {
      pop.style.setProperty("max-height", `${room}px`);
      top = below >= above ? r.bottom + G : r.top - G - Math.min(h, room);
    } else top = y(r.top);
  }
  pop.style.setProperty("top", `${Math.max(E, top)}px`);
  // a box cut to the room may have grown a scroll bar: its width is taken again
  pop.style.setProperty("left", `${Math.max(E, Math.min(W - pop.offsetWidth - E, left))}px`);
}

/* ---- when it opens and closes ------------------------------------------------------------------ */
const REST = 450, GRACE = 300;                              // ms: the mouse rests before it opens; the way from the control to the box
let showTimer = null, hideTimer = null, shownFor = null, pending = null, closedAt = 0;
let quiet = false;                                          // after a click, until the mouse moves again
function hide() {
  clearTimeout(showTimer); clearTimeout(hideTimer); showTimer = hideTimer = null; pending = null;
  if (shownFor) { shownFor.removeAttribute("aria-describedby"); closedAt = Date.now(); }
  shownFor = null;
  const pop = $("popover");
  pop.hidden = true;
  pop.scrollTop = 0;
}
function show(node) {
  const pop = clear($("popover"));
  pending = null;
  if (!node.isConnected || !fill(pop, node)) { hide(); return; }
  if (shownFor && shownFor !== node) shownFor.removeAttribute("aria-describedby");
  const home = document.fullscreenElement || $("workspace");   // inside the page's main part; in full screen, inside what is shown
  if (pop.parentNode !== home) home.append(pop);
  pop.hidden = false;
  shownFor = node;
  if (!node.hasAttribute("aria-describedby")) node.setAttribute("aria-describedby", "popover");
  place(pop, node);
  // taller than its room, it scrolls inside: the mouse has its wheel; opened by the keyboard's focus, the box says its keys
  const at = document.activeElement;
  if (scrolls(pop) && at && node.contains(at) && at.matches(":focus-visible")) {
    pop.prepend(el("div", { class: "tip-keys tip-scroll" }, el("kbd", {}, "Alt"), "+", el("kbd", {}, "↓"), el("span", {}, "scrolls this box")));
    place(pop, node);
  }
}
const scrolls = (pop) => pop.scrollHeight > pop.clientHeight + 1;
function owner(t) {
  const node = t && t.closest ? t.closest("[data-tip], [data-tip-id], [data-help]") : null;
  return node && node.classList.contains("dropdown-btn") && node.closest(".dropdown.open") ? null : node;   // not under an open menu
}
function ask(node, delay) {
  if (node === shownFor) { clearTimeout(hideTimer); hideTimer = null; return; }
  if (node && node === pending) return;
  clearTimeout(showTimer); showTimer = null; pending = null;
  if (!node) {                                               // the mouse left: time to reach the box
    if (shownFor && !hideTimer) hideTimer = setTimeout(hide, GRACE);
    return;
  }
  pending = node;
  // a box was open a moment ago: the next one follows quickly, as the eye is already there
  showTimer = setTimeout(() => show(node), shownFor || Date.now() - closedAt < GRACE ? Math.min(delay, 120) : delay);
}

export function initTips() {
  const inBox = (t) => !!(t && t.closest && t.closest("#popover"));
  const over = (e) => {
    if (inBox(e.target)) { clearTimeout(hideTimer); hideTimer = null; return; }       // the mouse is on the box: it stays
    ask(owner(e.target), e.target.closest && e.target.closest(".info-dot") ? 0 : REST);
  };
  // a click often redraws the control under the mouse: that alone opens no box, only the next move of the mouse does
  document.addEventListener("mouseover", (e) => { if (!quiet) over(e); });
  document.addEventListener("mousemove", (e) => { if (quiet) { quiet = false; over(e); } });
  document.documentElement.addEventListener("mouseleave", () => ask(null));
  // A dialog that closes hands the focus back to the button that opened it, and leaves the mouse resting where it
  // was: neither opens a box.  (afterDialog: a dialog was open at the last key or click.)
  let afterDialog = false;
  const dialogOpen = () => { afterDialog = !!document.querySelector("dialog[open]"); };
  document.addEventListener("keydown", dialogOpen, true);
  document.addEventListener("mousedown", dialogOpen, true);
  document.addEventListener("close", (e) => { if (e.target instanceof HTMLDialogElement) { hide(); quiet = true; } }, true);
  document.addEventListener("focusin", (e) => {
    if (inBox(e.target)) return;
    if ((afterDialog && !e.target.closest("dialog")) || state.handingFocus) { hide(); return; }    // nor the focus the page itself puts back
    const node = owner(e.target);
    if (node && e.target.matches(":focus-visible")) ask(node, e.target.closest(".info-dot") ? 0 : 200); else hide();
  });
  document.addEventListener("focusout", (e) => { if (!inBox(e.relatedTarget) && !inBox(e.target)) hide(); });
  document.addEventListener("mousedown", (e) => { if (!inBox(e.target)) { hide(); quiet = true; } });
  document.addEventListener("scroll", (e) => { if (!inBox(e.target)) hide(); }, true);   // a scroll inside the box keeps it
  window.addEventListener("resize", hide);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && (shownFor || pending)) { hide(); return; }
    const pop = $("popover");                                // Alt + an arrow scrolls a box that is taller than its room
    if (shownFor && e.altKey && (e.key === "ArrowDown" || e.key === "ArrowUp") && scrolls(pop)) {
      e.preventDefault(); e.stopPropagation();
      pop.scrollTop += e.key === "ArrowDown" ? 60 : -60;
    }
  }, true);
  loadTips();
}

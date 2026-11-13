/* tips.js - the small help box that opens beside a control.

   A control asks for it with one of:
     data-tip-id="name"       a fixed text of TIPS below
     data-tip="text"          a text that changes with the page's state (it wins over data-tip-id)
     data-help="NAME"         a setting's help (with data-help-file): app/paramtips.js, else the comment beside the
                              setting in its parameter file, and its published value
   It opens when the mouse rests on the control or the keyboard reaches it, stays while the mouse is on the box
   itself, and closes with Esc, a click, a scroll, or when the mouse or the keyboard leaves.
   In a text, \n starts a new line and **text** is bold. */

import { $, el, clear, M } from "./core.js";
import { TOOLTIPS } from "./paramtips.js";
import { showValue } from "./labels.js";

const TIPS = {
  "gen-single": "The Single Coil Set Generator: one sine and cosine RX pair with one TX coil. Your settings of each generator are kept when you switch.",
  "gen-dual": "The Dual Coil Set Generator: two coil sets on one board, an inner and an outer one, each with its own rotor ring (a coarse and a fine track). Your settings of each generator are kept when you switch.",
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
  "view-overlay": "The rotor's copper drawn over the stator, at the Rotor Angle below",
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

let timer = null, shownFor = null;
function hide() {
  clearTimeout(timer); timer = null;
  if (shownFor) shownFor.removeAttribute("aria-describedby");
  shownFor = null;
  $("popover").hidden = true;
}
function rich(box, text) {
  text.split("\n").forEach((line, n) => {
    if (n) box.append(el("br"));
    line.split("**").forEach((part, i) => part && box.append(i % 2 ? el("b", {}, part) : part));
  });
}
function fill(pop, node) {
  if (node.dataset.tip) { rich(pop, node.dataset.tip); return true; }
  if (node.dataset.help) {
    const name = node.dataset.help, file = node.dataset.helpFile, m = M(), p = (m.params[file] || {})[name];
    pop.append(el("span", { class: "mono-name" }, name));
    rich(pop, TOOLTIPS[name] || (p && p.help) || "No notes in the parameter file.");
    if (p) pop.append(el("span", { class: "tip-foot" }, `Starting Value: ${p.override && p.default === null ? "the board's value" : showValue(p.default)}`));
    return true;
  }
  const text = TIPS[node.dataset.tipId];
  if (text) rich(pop, text);
  return !!text;
}
function show(node) {
  const pop = clear($("popover"));
  if (!node.isConnected || !fill(pop, node)) return;
  pop.hidden = false;
  shownFor = node;
  if (!node.hasAttribute("aria-describedby")) node.setAttribute("aria-describedby", "popover");
  const r = node.getBoundingClientRect(), h = pop.offsetHeight, w = pop.offsetWidth;
  const below = r.bottom + 8, above = r.top - h - 8;
  pop.style.top = `${below + h < window.innerHeight - 6 || above < 6 ? Math.max(6, Math.min(below, window.innerHeight - h - 6)) : above}px`;
  pop.style.left = `${Math.max(6, Math.min(window.innerWidth - w - 6, r.left))}px`;
}
const owner = (t) => (t && t.closest ? t.closest("[data-tip], [data-tip-id], [data-help]") : null);

export function initTips() {
  let pending = null;
  const ask = (node, delay) => {
    if (node === shownFor || node === pending) return;
    hide();
    pending = node;
    if (!node) return;
    timer = setTimeout(() => { pending = null; show(node); }, delay);
  };
  document.addEventListener("mouseover", (e) => {
    if (e.target.closest && e.target.closest("#popover")) return;          // the mouse is on the box: it stays
    ask(owner(e.target), e.target.closest && e.target.closest(".info-dot") ? 0 : 450);
  });
  document.addEventListener("focusin", (e) => {
    const node = owner(e.target);
    if (node && e.target.matches(":focus-visible")) ask(node, 450); else { pending = null; hide(); }
  });
  document.addEventListener("focusout", () => { pending = null; hide(); });
  document.addEventListener("mousedown", () => { pending = null; hide(); });
  document.addEventListener("scroll", () => { pending = null; hide(); }, true);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !$("popover").hidden) { pending = null; hide(); } }, true);
}

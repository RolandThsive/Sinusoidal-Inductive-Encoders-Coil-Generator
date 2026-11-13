/* core.js - what every part of the page uses: small helpers, the page's state, the toast and the confirm box.

   The page is built with DOM calls only (el, svg): no text is ever turned into HTML, so nothing a visitor types, a
   link carries or a file holds can become markup. */

export const $ = (id) => document.getElementById(id);

/* A new element.  attrs: "class", "on<event>" handlers, "style" as an object of properties (set through the style
   object, never as an attribute: the page's security policy forbids inline style text), true / false / null as
   usual; kids: nodes or texts. */
export function el(tag, attrs = {}, ...kids) { return fill(document.createElement(tag), attrs, kids); }
export function svg(tag, attrs = {}, ...kids) {
  return fill(document.createElementNS("http://www.w3.org/2000/svg", tag), attrs, kids);
}
function fill(e, attrs, kids) {
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") { if (v) e.setAttribute("class", v); }
    else if (k === "style") { for (const [p, x] of Object.entries(v)) e.style.setProperty(p, x); }
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, "");
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const k of kids.flat(Infinity)) if (k != null && k !== false) e.append(k.nodeType ? k : document.createTextNode(String(k)));
  return e;
}
export function clear(node) { node.replaceChildren(); return node; }

export function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
export function clone(x) { return JSON.parse(JSON.stringify(x)); }
export function fmt(x) { return typeof x === "number" ? String(Math.round(x * 1000) / 1000) : String(x); }
export function plural(n, word) { return `${n} ${word}${n === 1 ? "" : "s"}`; }

/* ---- state ------------------------------------------------------------------------------------- */
function modeState() {
  return {
    loaded: false,                // describe() has been read
    files: [],                    // [{file, label, group, set, cat, parameters}] as the generator's tables give them
    params: {},                   // {file: {NAME: parameter}}
    values: {}, start: {},        // {file: {NAME: value}}: now, and as published
    inactive: {},                 // {file: Set of names the generator does not use now}
    errors: {},                   // {file: {NAME: the generator's message about that value}}
    result: null,                 // the last run of any kind (Generate or Check Only): what the Checks panel shows
    good: null,                   // the last run that wrote files: {name, zipBytes, files, bytes, stator, rotor, text}
    stale: false,                 // the settings changed since `good` was made
    pictures: null,               // {file name: object URL} of good's SVG pictures, made when Pictures is first opened
    lastNumbers: {},              // {file: {NAME: the last number of an Auto / None setting}}
    folded: new Set(),            // Advanced group blocks that are folded away
    rotorModeSeen: undefined,     // the Rotor Mode the Advanced page last drew
    basicTab: "Board", advTab: "Board", set: 1, find: "",
  };
}
/* What the page is doing, as <html data-state>: "loading" until the first board is made, then "busy" while anything
   is under way (a run, a switch of generator, an import, the generator's checks of typed values) and "ready" when
   the page has settled; "failed" when Python did not start.  The style sheet and the tests read it. */
let phase = "loading", jobs = 0;
function showState() { document.documentElement.dataset.state = phase === "ready" && jobs > 0 ? "busy" : phase; }
export function setPhase(p) { phase = p; showState(); }
export function job(n) { jobs = Math.max(0, jobs + n); showState(); }
export async function during(fn) { job(1); try { return await fn(); } finally { job(-1); } }

export const state = {
  gen: "single",                  // which generator: "single" or "dual"
  view: "basic",                  // which settings are shown: "basic" or "advanced"
  ready: false, busy: false,
  showInfo: false,
  hostPage: undefined,            // the address the blog page sent us, used by Share
  modes: { single: modeState(), dual: modeState() },
  build: null,                    // version.json
};
export const M = () => state.modes[state.gen];

/* ---- messages ---------------------------------------------------------------------------------- */
let toastTimer;
/* A short message at the bottom of the page; a screen reader hears it too (#sr-status). */
export function toast(text, ms = 2600) {
  const t = $("toast");
  t.textContent = text; t.hidden = false;
  say(text);
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (t.hidden = true), ms);
}
export function say(text) {
  const s = $("sr-status");
  s.textContent = "";
  requestAnimationFrame(() => (s.textContent = text));
}

/* "Are you sure?" with Sure / No; the keyboard starts on No, and Esc answers no. */
export function confirmBox(text, yes = "Sure") {
  const d = $("confirm-dialog");
  $("confirm-text").textContent = text;
  $("confirm-yes").textContent = yes;
  d.returnValue = "";
  d.showModal();
  return new Promise((resolve) => d.addEventListener("close", () => resolve(d.returnValue === "yes"), { once: true }));
}

/* A dialog with a long text (the run's text) and a Copy button. */
export function textBox(title, text) {
  $("text-title").textContent = title;
  $("text-body").textContent = text;
  $("text-dialog").showModal();
}

export async function copyText(text, done = "Copied") {
  try { await navigator.clipboard.writeText(text); toast(done); return true; }
  catch (e) { textBox("Copy This Text", text); return false; }
}

export function download(bytes, name, type = "application/octet-stream") {
  const url = URL.createObjectURL(new Blob([bytes], { type }));
  const a = el("a", { href: url, download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/* A click on the dimmed page beside a dialog closes it. */
export function closeOnOutsideClick(dialog) {
  dialog.addEventListener("click", (e) => {
    const r = dialog.getBoundingClientRect();
    if (e.target === dialog && (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom)) dialog.close();
  });
}

/* A row of choices of which one is on (role radiogroup or tablist): the arrow keys move between them and choose, Tab
   enters and leaves the row once.  `pick(button)` is called for a click and for an arrow key. */
export function wireChoices(box, pick) {
  const items = () => [...box.querySelectorAll("button:not(:disabled)")];
  box.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b && box.contains(b) && !b.disabled) pick(b); });
  box.addEventListener("keydown", (e) => {
    const list = items(), i = list.indexOf(document.activeElement);
    if (i < 0) return;
    let j = null;
    if (e.key === "ArrowRight" || e.key === "ArrowDown") j = (i + 1) % list.length;
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") j = (i - 1 + list.length) % list.length;
    else if (e.key === "Home") j = 0;
    else if (e.key === "End") j = list.length - 1;
    if (j === null) return;
    e.preventDefault();
    pick(list[j]);
    const again = items().find((b) => b.dataset.key === list[j].dataset.key && b.dataset.key !== undefined) || list[j];
    if (again.isConnected) again.focus();
  });
}
/* Close every open menu (but `keep`).  A click anywhere else on the page closes them all. */
export function closeMenus(keep) {
  document.querySelectorAll(".dropdown.open").forEach((d) => {
    if (d === keep) return;
    d.classList.remove("open");
    d.querySelector(".dropdown-btn").setAttribute("aria-expanded", "false");
  });
}
document.addEventListener("click", () => closeMenus());

/* A menu that is written in the page: a .dropdown with its button and a listbox of option buttons.  pick(option) is
   called for a choice; options that are disabled are shown greyed out and cannot be reached. */
export function wireMenu(dd, pick) {
  const btn = dd.querySelector(".dropdown-btn"), list = dd.querySelector('[role="listbox"]');
  const items = () => [...list.querySelectorAll('[role="option"]:not(:disabled)')];
  function open(on, focusItem) {
    closeMenus(dd);
    dd.classList.toggle("open", on);
    btn.setAttribute("aria-expanded", String(on));
    if (on && focusItem) (items().find((i) => i.classList.contains("on")) || items()[0]).focus();
  }
  btn.addEventListener("click", (e) => { e.stopPropagation(); open(!dd.classList.contains("open"), e.detail === 0); });
  btn.addEventListener("keydown", (e) => { if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); open(true, true); } });
  list.addEventListener("click", (e) => {
    e.stopPropagation();                                       // a greyed-out line leaves the menu open
    const o = e.target.closest('[role="option"]');
    if (!o || o.disabled) return;
    open(false); btn.focus(); pick(o);
  });
  list.addEventListener("keydown", (e) => {
    const all = items(), i = all.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); all[(i + 1) % all.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); all[(i - 1 + all.length) % all.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); all[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); all[all.length - 1].focus(); }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); open(false); btn.focus(); }
    else if (e.key === "Tab") open(false);
  });
}

/* Mark which choice of a row is on: the class, the ARIA state and the one tab stop. */
export function markChoices(box, isOn) {
  const tabs = box.getAttribute("role") === "tablist";
  for (const b of box.querySelectorAll("button")) {
    const on = !!isOn(b);
    b.classList.toggle("on", on);
    b.setAttribute(tabs ? "aria-selected" : "aria-checked", String(on));
    b.tabIndex = on ? 0 : -1;
  }
  if (!box.querySelector("button.on")) { const first = box.querySelector("button"); if (first) first.tabIndex = 0; }
}

/* audit.mjs - the general checks of the page's layout, run inside the page (page.evaluate(audit)): whatever is shown
   now is measured, and what is wrong comes back as lines of text.  layout.spec.js runs it in every state it visits.

   - the page does not scroll sideways, and nothing of a panel sticks out of it
   - no two things that are shown lie over each other (buttons, boxes, names, values)
   - no button's or tab's words are broken into two lines, and no words are cut off
   - the names of a card's settings start on one line and their boxes end on one line
   - the buttons of a row have one height and stand on one line
   - the list of settings, the drawing and the list of findings keep a size one can work with */
export function audit() {
  const out = [], NEAR = 0.75;
  const R = (e) => e.getBoundingClientRect();
  const shown = (e) => e.offsetParent !== null && R(e).width > 0 && R(e).height > 0
    && (e.checkVisibility ? e.checkVisibility({ opacityProperty: true, visibilityProperty: true }) : getComputedStyle(e).visibility !== "hidden");   // a closed menu is not shown
  const words = (e) => (e.getAttribute("aria-label") || e.textContent || e.value || e.placeholder || "").trim().replace(/\s+/g, " ").slice(0, 24);
  const name = (e) => (e.id ? "#" + e.id : (e.dataset.name || e.dataset.tipId || e.dataset.key || e.dataset.help || String(e.className).split(" ")[0] || e.tagName.toLowerCase())) + (words(e) ? ` "${words(e)}"` : "");
  /* what of an element can be seen: its box cut to every scrolling or clipping box around it */
  const seen = (e) => {
    let { left: l, top: t, right: r, bottom: b } = R(e);
    for (let p = e.parentElement; p; p = p.parentElement) {
      const s = getComputedStyle(p);
      if (s.overflowX === "visible" && s.overflowY === "visible") continue;
      const q = R(p);
      if (s.overflowX !== "visible") { l = Math.max(l, q.left); r = Math.min(r, q.right); }
      if (s.overflowY !== "visible") { t = Math.max(t, q.top); b = Math.min(b, q.bottom); }
    }
    return r - l > 1 && b - t > 1 ? { l, t, r, b } : null;
  };
  /* on how many lines an element's words stand: the boxes of its text, without what only a screen reader gets */
  const lines = (e) => {
    const boxes = [], walk = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) {
      if (!n.textContent.trim() || n.parentElement.closest(".sr-only, [aria-hidden=true], svg")) continue;
      const r = document.createRange(); r.selectNodeContents(n);
      boxes.push(...[...r.getClientRects()].filter((x) => x.width > 1));
    }
    boxes.sort((p, q) => p.top - q.top);
    let n = 0, bottom = -Infinity;
    for (const x of boxes) { if (x.top >= bottom - 3) n++; bottom = Math.max(bottom, x.bottom); }
    return n;
  };

  // the page and its panels
  const de = document.documentElement, small = de.clientWidth < 1000;     // a zoomed-in window: one column, some rows stacked
  if (de.scrollWidth > de.clientWidth + 1) out.push(`the page scrolls sideways (${de.scrollWidth} in ${de.clientWidth})`);
  for (const id of ["topbar", "controls", "preview", "checks", "foot"]) {
    const p = document.getElementById(id);
    if (!p || !shown(p)) continue;
    const box = R(p);
    if (box.right > de.clientWidth + 0.5 || box.left < -0.5) out.push(`#${id} is not inside the window`);
    for (const e of p.querySelectorAll("*")) {
      if (!shown(e) || e.closest("#popover, .sr-only, #measure-help")) continue;
      const r = R(e);
      if (r.right > box.right + 0.5 || r.left < box.left - 0.5) out.push(`${name(e)} sticks out of #${id} (${r.left.toFixed(1)} to ${r.right.toFixed(1)}, the panel ${box.left.toFixed(1)} to ${box.right.toFixed(1)})`);
    }
  }

  // nothing lies over anything else
  const things = [...document.querySelectorAll("#app :is(button, a, select, output, h1, h2, input:not([type=checkbox]):not([type=radio]):not([type=file]), .switch, .field-label, .mono-name, .field-unit, .field-error, #counts, #readout, #build-stamp, .results dt, .results dd, .results th, .results td:not(.room), .group-title, .hint)")]
    .filter((e) => shown(e) && !e.closest("#popover, dialog, .sr-only, [hidden]")).map((e) => ({ e, s: seen(e) })).filter((x) => x.s);
  for (let i = 0; i < things.length; i++) {
    for (let j = i + 1; j < things.length; j++) {
      const a = things[i], b = things[j];
      if (a.e.contains(b.e) || b.e.contains(a.e)) continue;
      const w = Math.min(a.s.r, b.s.r) - Math.max(a.s.l, b.s.l), h = Math.min(a.s.b, b.s.b) - Math.max(a.s.t, b.s.t);
      if (w > 1.5 && h > 1.5) out.push(`${name(a.e)} and ${name(b.e)} lie over each other (${w.toFixed(0)} x ${h.toFixed(0)} px)`);
    }
  }

  // words: one line in a button or a tab, nothing cut off
  for (const e of document.querySelectorAll("#app :is(button, a.glass-btn, .layer-chip, h1, h2, .results dt, .results dd, .results th, .results td, .mono-name)")) {
    if (!shown(e) || !seen(e) || e.closest("#popover, dialog, .slider") || (small && e.tagName === "H1")) continue;   // a TX layout card's name may take two lines
    if (lines(e) > 1) out.push(`${name(e)}: its words are broken into ${lines(e)} lines`);
  }
  for (const e of document.querySelectorAll("#app :is(button, a, .field-label, .mono-name, .results *, h1, h2, #counts, .hint, select, .field-error)")) {
    if (!shown(e) || e.closest("#popover, dialog")) continue;
    if (e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== "visible" && e.clientWidth) out.push(`${name(e)}: its words are cut off (${e.scrollWidth} in ${e.clientWidth})`);
  }

  // the settings of a card: names on one line at the left, boxes on one line at the right
  for (const card of document.querySelectorAll("#controls :is(#basic-controls, #advanced-controls) :is(.group-card, .group-body)")) {
    if (!shown(card)) continue;
    const fields = [...card.querySelectorAll(":scope > .field, :scope > .group-body > .field")].filter(shown);
    if (fields.length < 2) continue;
    const lefts = fields.map((f) => f.querySelector(".field-label")).filter(Boolean).map((l) => R(l).left);
    if (lefts.length && Math.max(...lefts) - Math.min(...lefts) > NEAR) out.push(`${name(card)}: the names of its settings start at ${[...new Set(lefts.map((x) => x.toFixed(1)))].join(", ")}`);
    const rights = fields.map((f) => Math.max(...[...f.querySelectorAll("input:not([type=checkbox]):not([type=radio]), select, .switch, .reset-one, .segmented, output")].filter(shown).map((c) => R(c).right), -1)).filter((x) => x > 0);
    if (rights.length && Math.max(...rights) - Math.min(...rights) > NEAR) out.push(`${name(card)}: its settings end at ${[...new Set(rights.map((x) => x.toFixed(1)))].join(", ")}`);
    const outer = [...new Set(fields.map((f) => `${R(f).left.toFixed(1)}-${R(f).right.toFixed(1)}`))];
    if (outer.length > 1) out.push(`${name(card)}: its settings have different widths (${outer.join(", ")})`);
  }

  // the buttons of a row: one height, one line
  const ROWS = { "the top buttons": ".top-actions > :is(a, button)", "the view tabs": "#view-tabs > button", "the drawing's buttons": "#canvas-tools :is(.tool-pair > *, #origin-slot > *)",
    "the copper chips": "#layer-toggles > *", "the silkscreen chips": "#silk-toggles > *", "the board buttons": ".download-row > button",
    "Basic | Advanced": "#mode-switch > button", "the tabs": "#controls :is(#basic-panel, #advanced-panel):not([hidden]) > .segmented:not(.set-switch) > button",
    "the coil sets": "#controls :is(#basic-panel, #advanced-panel):not([hidden]) > .set-switch > button", "Strict and Reset": ".generate-row > :is(.switch-row, #btn-reset)",
    "Check Only and Generate": ".generate-row > :is(#btn-check, #btn-generate)", "the Checks line": ".checks-head > :is(h2, label, #btn-runtext)" };
  for (const [what, sel] of Object.entries(ROWS)) {
    const row = [...document.querySelectorAll(sel)].filter(shown);
    if (row.length < 2 || (small && /chips|top buttons/.test(what))) continue;
    const tops = new Set(row.map((e) => Math.round(R(e).top)));
    const mids = row.map((e) => (R(e).top + R(e).bottom) / 2);
    if (tops.size > 1 && Math.max(...mids) - Math.min(...mids) > 1.5) out.push(`${what} are not on one line (centres ${[...new Set(mids.map((m) => m.toFixed(1)))].join(", ")})`);
    if (!/Checks line|Strict/.test(what)) { const hs = new Set(row.map((e) => Math.round(R(e).height))); if (hs.size > 1) out.push(`${what} have different heights (${[...hs].join(", ")})`); }
  }

  // the drawing as Fit leaves it: no button that lies on it covers the board
  const circle = (document.getElementById("board-canvas").dataset.circle || "").split(" ").map(Number);
  if (circle.length === 3 && shown(document.getElementById("board-canvas"))) {
    const c = R(document.getElementById("board-canvas")), [x, y, r] = circle;
    for (const id of ["canvas-tools", "silk-toggles", "net-toggles", "rotor-angle-box"]) {
      const e = document.getElementById(id);
      if (!shown(e)) continue;
      const b = R(e), d = Math.hypot(Math.max(b.left - c.left - x, 0, x - (b.right - c.left)), Math.max(b.top - c.top - y, 0, y - (b.bottom - c.top)));
      if (d < r - 1) out.push(`#${id} covers ${Math.round(r - d)} px of the board`);
    }
    if (r < (small ? 60 : 80)) out.push(`the board is drawn ${Math.round(2 * r)} px wide`);
  }

  // room to work in
  const list = document.querySelector("#controls :is(#basic-panel, #advanced-panel):not([hidden])");
  if (list && R(list).height < 130) out.push(`the list of settings is ${Math.round(R(list).height)} px high`);
  const canvas = document.getElementById("canvas-wrap");
  if (shown(canvas) && (R(canvas).height < 230 || R(canvas).width < (small ? 260 : 320))) out.push(`the drawing is ${Math.round(R(canvas).width)} x ${Math.round(R(canvas).height)} px`);
  const finds = document.getElementById("checks-list");
  if (shown(finds) && R(finds).height < 60) out.push(`the list of findings is ${Math.round(R(finds).height)} px high`);
  for (const id of ["controls", "preview", "checks"]) { const p = document.getElementById(id); if (shown(p) && R(p).bottom > Math.max(de.clientHeight, de.scrollHeight) + 0.5) out.push(`#${id} ends under the page`); }
  return out;
}

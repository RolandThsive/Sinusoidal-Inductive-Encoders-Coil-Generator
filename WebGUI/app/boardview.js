/* boardview.js - draws the generated KiCad boards on a canvas.

   parseBoard(text) reads the few things the generators write: nets, segments, vias (through and blind, with the
   two layers they join), gr_circle (the Edge.Cuts circles; the dots of the silkscreen suggestion), gr_line (the
   silkscreen suggestion: boxes, lines and lettering) and filled polygons (rotor copper).  BoardView draws them with
   one colour per copper layer, with zoom, pan, an X / Y readout from the origin and a rotor angle for the overlay.
   The canvas is sized by devicePixelRatio so it stays sharp on HiDPI screens.  Hovering a loop set or a layer chip
   highlights it (the rest is faded); layers, loop sets, coil sets (Dual), the silkscreen and the vias can be hidden;
   the vias can be boosted and the origin marker coloured.  The two-click measure tool keeps its finished lines with
   S (at most 256) and removes them with Z.  Nothing here changes a board: it only draws what the files hold. */

const FADED = 0.18;                                                    // alpha of everything not highlighted
const LAYER_ORDER = ["B.Cu", "In2.Cu", "In1.Cu", "F.Cu"];              // drawn bottom first
const STACK = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"];                    // top to bottom: the layers a via passes
export const SILK_LAYERS = ["F.SilkS", "B.SilkS"];
export const LAYER_INFO = {
  "F.Cu": { name: "Top", css: "--top" },
  "In1.Cu": { name: "Inner-1", css: "--in1" },
  "In2.Cu": { name: "Inner-2", css: "--in2" },
  "B.Cu": { name: "Bottom", css: "--bottom" },
};

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

// the copper layers a via passes through: from the first to the second layer it joins, in the stack
export function viaSpan(a, b) {
  const i = STACK.indexOf(a), j = STACK.indexOf(b);
  if (i < 0 || j < 0) return STACK.slice();
  return STACK.slice(Math.min(i, j), Math.max(i, j) + 1);
}

export function parseBoard(text) {
  const board = { segments: {}, vias: [], circles: [], polys: [], silk: [], dots: [], nets: [] };
  const num = "(-?[\\d.]+)";
  // net names: (net 3 "SIN_Signal"); segments and vias carry the number, (net 3)
  const nets = {};
  let m;
  const netRe = /^\s*\(net (\d+) "([^"]*)"\)/gm;
  while ((m = netRe.exec(text))) { nets[m[1]] = m[2]; if (m[2]) board.nets.push(m[2]); }
  const segRe = new RegExp(`\\(segment \\(start ${num} ${num}\\) \\(end ${num} ${num}\\) \\(width ${num}\\) \\(layer "([^"]+)"\\)(?: \\(net (\\d+)\\))?`, "g");
  while ((m = segRe.exec(text))) {
    const [_, x1, y1, x2, y2, w, layer, n] = m;
    const net = nets[n] ?? "";
    const key = layer + "|" + w + "|" + net;
    (board.segments[key] = board.segments[key] || { layer, width: +w, net, pts: [] }).pts.push(+x1, +y1, +x2, +y2);
  }
  const viaRe = new RegExp(`\\(via (blind )?\\(at ${num} ${num}\\) \\(size ${num}\\) \\(drill ${num}\\)(?: \\(layers "([^"]+)" "([^"]+)"\\))?[^\\n]*?(?:\\(net (\\d+)\\))?\\)\\s*$`, "gm");
  while ((m = viaRe.exec(text))) {
    board.vias.push({ x: +m[2], y: +m[3], d: +m[4], drill: +m[5], blind: !!m[1],
      layers: viaSpan(m[6] || "F.Cu", m[7] || "B.Cu"), net: nets[m[8]] ?? "" });
  }
  const circRe = new RegExp(`\\(gr_circle \\(center ${num} ${num}\\) \\(end ${num} ${num}\\)([^\\n]*)`, "g");
  while ((m = circRe.exec(text))) {
    const cx = +m[1], cy = +m[2], rest = m[5];
    const layer = (/\(layer "([^"]+)"\)/.exec(rest) || [])[1];
    if (!layer) continue;
    const r = Math.hypot(+m[3] - cx, +m[4] - cy);
    if (SILK_LAYERS.includes(layer)) board.dots.push({ cx, cy, r, layer, solid: /\(fill solid\)/.test(rest) });
    else board.circles.push({ cx, cy, r, layer });
  }
  // the silkscreen suggestion: (gr_line (start x y) (end x y) (stroke (width w) (type dash) ...) (layer "F.SilkS"))
  const lineRe = new RegExp(`\\(gr_line \\(start ${num} ${num}\\) \\(end ${num} ${num}\\)([^\\n]*)`, "g");
  while ((m = lineRe.exec(text))) {
    const rest = m[5];
    const layer = (/\(layer "([^"]+)"\)/.exec(rest) || [])[1];
    if (!SILK_LAYERS.includes(layer)) continue;
    const w = +((/\(width (-?[\d.]+)\)/.exec(rest) || [])[1] || 0.12);
    board.silk.push({ x1: +m[1], y1: +m[2], x2: +m[3], y2: +m[4], w, dash: /\(type dash\)/.test(rest), layer });
  }
  // filled polygons: (gr_poly (pts (xy ..) ...) ... (layer "F.Cu") ...)
  let i = 0;
  while ((i = text.indexOf("(gr_poly", i)) >= 0) {
    let depth = 0, j = i;
    for (; j < text.length; j++) {
      if (text[j] === "(") depth++;
      else if (text[j] === ")" && --depth === 0) break;
    }
    const body = text.slice(i, j + 1);
    const lm = /\(layer "([^"]+)"\)/.exec(body);
    const pts = [];
    const xyRe = new RegExp(`\\(xy ${num} ${num}\\)`, "g");
    let p;
    while ((p = xyRe.exec(body))) pts.push(+p[1], +p[2]);
    if (lm && pts.length) board.polys.push({ layer: lm[1], pts });
    i = j + 1;
  }
  return board;
}

/* ------------------------------------------------------------------------------------------------ */
export class BoardView {
  static MAX_LOCKED = 256;          // measured lines the S key can keep
  constructor(canvas, readout) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.readout = readout;
    this.mode = "overlay";           // stator | rotor | overlay
    this.stator = null; this.rotor = null;
    this.center = [100, 100];
    this.hidden = new Set(["B.SilkS"]);   // layers switched off (the bottom silkscreen repeats the top one, mirrored)
    this.netRole = {};               // net name -> "sin" | "cos" | "tx" (from the parameters of the run)
    this.netSet = {};                // net name -> 1 | 2, the coil set it belongs to (Dual)
    this.hiddenNets = new Set();     // roles switched off with the Sin / Cos / TX Loops buttons
    this.hiddenSets = new Set();     // coil sets switched off with the Set 1 / Set 2 buttons (Dual)
    this.highlightSet = null;        // the coil set under the mouse
    this.highlight = null;           // the role under the mouse: drawn thicker, the rest faded
    this.highlightLayer = null;      // the copper layer under the mouse (Top / Inner-1 / Inner-2 / Bottom chips), the same way
    this.showOrigin = true;          // the board centre marker (Origin button); originBoost = hovered, drawn in the accent colour
    this.rotorAngle = 0;
    this.view = { scale: 4, ox: 0, oy: 0 };
    this.measure = false; this.mA = null; this.mB = null;
    this.mLocked = [];               // measured lines kept with the S key: [[A, B], ...], at most MAX_LOCKED
    this.hasBoard = false;           // true once setBoards has run (WebGUI.js tests it to tell a failed run from no run)
    this.originBoost = false;        // the Origin button is hovered
    this.viaBoost = false;           // the Vias chip is hovered
    this._wire();
    new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
  }

  setBoards(statorText, rotorText, center) {
    this.hasBoard = true;
    this.stator = statorText ? parseBoard(statorText) : null;
    this.rotor = rotorText ? parseBoard(rotorText) : null;
    if (center) this.center = center;
    this.draw();
  }
  /* no boards: the generator was changed and that one has not run yet */
  clearBoards() { this.stator = this.rotor = null; this.hasBoard = false; this.clearMeasure(); this.draw(); }
  setMode(mode) { this.mode = mode; this.draw(); }
  setNetRoles(roles, sets = {}) { this.netRole = roles; this.netSet = sets; this.draw(); }
  toggleSet(k) { this.hiddenSets.has(k) ? this.hiddenSets.delete(k) : this.hiddenSets.add(k); this.draw(); }
  setSetHighlight(k) { if (this.highlightSet !== k) { this.highlightSet = k; this.draw(); } }
  /* true when the board the view shows has silkscreen marks on `layer` (the chips of the others are locked) */
  hasSilk(layer) {
    const b = this.mode === "rotor" ? this.rotor : this.stator;
    return !!b && (b.silk.some((s) => s.layer === layer) || b.dots.some((d) => d.layer === layer));
  }
  toggleNet(role) { this.hiddenNets.has(role) ? this.hiddenNets.delete(role) : this.hiddenNets.add(role); this.draw(); }
  setHighlight(role) { if (this.highlight !== role) { this.highlight = role; this.draw(); } }
  /* the layers with traces or fills in the board(s) the view shows (the layer chips of the others are locked; the
     rotor's mask openings are polygons too, so mask layers can appear, but the chips only ask about copper);
     null before the first board.  Overlay: the stator's, since the rotor drawn over it does not follow the chips. */
  layersPresent() {
    const b = this.mode === "rotor" ? this.rotor : this.stator;
    if (!b) return null;
    const s = new Set();
    for (const g of Object.values(b.segments)) s.add(g.layer);
    for (const p of b.polys) s.add(p.layer);
    return s;
  }
  setLayerHighlight(cu) { if (this.highlightLayer !== cu) { this.highlightLayer = cu; this.draw(); } }
  toggleOrigin() { this.showOrigin = !this.showOrigin; this.draw(); }
  setOriginBoost(on) { if (this.originBoost !== on) { this.originBoost = on; this.draw(); } }
  setViaBoost(on) { if (this.viaBoost !== on) { this.viaBoost = on; this.draw(); } }
  toggleLayer(layer) { this.hidden.has(layer) ? this.hidden.delete(layer) : this.hidden.add(layer); this.draw(); }
  setRotorAngle(deg) { this.rotorAngle = deg; this.draw(); }

  /* radius of everything shown, for Fit */
  extent() {
    let r = 0;
    const take = (b) => b && b.circles.forEach((c) => (r = Math.max(r, c.r + Math.hypot(c.cx - this.center[0], c.cy - this.center[1]))));
    take(this.stator); take(this.rotor);
    return r || 50;
  }
  /* Fit: the whole board in the middle of the drawing.  Where a button that lies on the drawing would cover part of
     it (keepClear() gives their boxes, in canvas pixels), the board takes the largest free circle instead, the one
     nearest the middle.  The circle it was given stands in data-circle (x, y, radius in CSS pixels). */
  fit() {
    const W = this.canvas.width, H = this.canvas.height, dpr = window.devicePixelRatio || 1;
    let r = Math.min(W, H) / 2 / 1.08, cx = W / 2, cy = H / 2;
    const boxes = this.keepClear ? this.keepClear() : [];
    const free = (x, y) => Math.min(x, y, W - x, H - y, ...boxes.map((b) => Math.hypot(Math.max(b.l - x, 0, x - b.r), Math.max(b.t - y, 0, y - b.b))));
    if (boxes.length && free(cx, cy) < r) {
      const step = Math.max(2, Math.round(Math.min(W, H) / 80)), spots = [];
      let best = 0;
      for (let y = step; y < H; y += step) for (let x = step; x < W; x += step) { const f = free(x, y); spots.push([f, x, y]); if (f > best) best = f; }
      let near = Infinity;
      for (const [f, x, y] of spots) {
        const d = Math.hypot(x - W / 2, y - H / 2);
        if (f >= best * 0.985 && d < near) { near = d; cx = x; cy = y; }
      }
      r = Math.min(r, free(cx, cy) / 1.03);
    }
    this.view.scale = r / this.extent();
    this.view.ox = cx - this.center[0] * this.view.scale;
    this.view.oy = cy - this.center[1] * this.view.scale;
    this.canvas.dataset.circle = [cx / dpr, cy / dpr, r / dpr].map((x) => x.toFixed(1)).join(" ");
    this.draw();
  }
  resize() {
    const dpr = window.devicePixelRatio || 1, el = this.canvas;
    const w = Math.max(10, Math.floor(el.clientWidth * dpr)), h = Math.max(10, Math.floor(el.clientHeight * dpr));   // whole pixels, as the canvas stores them
    if (el.width !== w || el.height !== h) { el.width = w; el.height = h; }
    this.fit();
  }

  toBoard(px, py) {
    const dpr = window.devicePixelRatio || 1;
    return [(px * dpr - this.view.ox) / this.view.scale, (py * dpr - this.view.oy) / this.view.scale];
  }

  _wire() {
    const c = this.canvas;
    let drag = null;
    c.addEventListener("wheel", (e) => {
      e.preventDefault();
      const dpr = window.devicePixelRatio || 1, x = e.offsetX * dpr, y = e.offsetY * dpr;
      const k = Math.exp(-e.deltaY * 0.0015);
      this.view.ox = x - (x - this.view.ox) * k;
      this.view.oy = y - (y - this.view.oy) * k;
      this.view.scale *= k;
      this.draw();
    }, { passive: false });
    c.addEventListener("mousedown", (e) => {
      if (this.measure) {
        const p = this.toBoard(e.offsetX, e.offsetY);
        if (!this.mA || this.mB) { this.mA = p; this.mB = null; } else this.mB = p;
        this.draw();
        return;
      }
      drag = { x: e.clientX, y: e.clientY, ox: this.view.ox, oy: this.view.oy };
      c.classList.add("dragging");
    });
    window.addEventListener("mousemove", (e) => {
      if (drag) {
        const dpr = window.devicePixelRatio || 1;
        this.view.ox = drag.ox + (e.clientX - drag.x) * dpr;
        this.view.oy = drag.oy + (e.clientY - drag.y) * dpr;
        this.draw();
      }
    });
    window.addEventListener("mouseup", () => { drag = null; c.classList.remove("dragging"); });
    c.addEventListener("mousemove", (e) => {
      const [x, y] = this.toBoard(e.offsetX, e.offsetY);
      // X right and Y up, from the origin (the board centre); KiCad's y points down
      const dx = x - this.center[0], dy = this.center[1] - y;
      const f = (v) => (Math.abs(v) < 0.005 ? 0 : v).toFixed(2);       // no "-0.00"
      let text = `X: ${f(dx)} mm, Y: ${f(dy)} mm`;
      if (this.measure && this.mA && !this.mB) text += `, Distance: ${Math.hypot(x - this.mA[0], y - this.mA[1]).toFixed(3)} mm`;
      this.readout.textContent = text;
    });
    c.addEventListener("mouseleave", () => (this.readout.textContent = ""));
    c.addEventListener("dblclick", () => this.fit());
    // the keyboard: arrows move the board, + and - zoom about the middle, 0 fits it
    c.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const step = 40 * (window.devicePixelRatio || 1), move = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] }[e.key];
      if (move) { this.view.ox += move[0]; this.view.oy += move[1]; }
      else if (e.key === "+" || e.key === "=" || e.key === "-") {
        const k = e.key === "-" ? 1 / 1.25 : 1.25, x = c.width / 2, y = c.height / 2;
        this.view.ox = x - (x - this.view.ox) * k; this.view.oy = y - (y - this.view.oy) * k; this.view.scale *= k;
      } else if (e.key === "0") { this.fit(); e.preventDefault(); return; }
      else return;
      e.preventDefault();
      this.draw();
    });
  }

  /* ---- drawing ------------------------------------------------------------------------------- */
  draw() {
    const ctx = this.ctx, { scale, ox, oy } = this.view;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    ctx.setTransform(scale, 0, 0, scale, ox, oy);
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    // one canvas (device) pixel in mm; these marks are not multiplied by devicePixelRatio, unlike the measure label
    const px = 1 / scale;
    if (this.mode === "stator" || this.mode === "overlay") this._drawBoard(this.stator, px);
    if (this.mode === "rotor") this._drawBoard(this.rotor, px, true);
    if (this.mode === "overlay") this._drawRotorOverlay();
    if (this.showOrigin) this._drawOrigin(px);
    this._drawMeasure(px);
  }

  _layerColour(layer) {
    const info = LAYER_INFO[layer];
    return info ? cssVar(info.css) : "#999";
  }

  _drawBoard(b, px, rotorAlone) {
    if (!b) return;
    const ctx = this.ctx;
    const hlCu = this.highlightLayer && !this.hidden.has(this.highlightLayer) ? this.highlightLayer : null;
    // rotor copper as filled polygons
    for (const p of b.polys) {
      if (!LAYER_INFO[p.layer]) continue;
      if (this.hidden.has(p.layer)) continue;
      ctx.globalAlpha = hlCu && p.layer !== hlCu ? FADED : 1;
      ctx.fillStyle = rotorAlone ? "rgba(184, 115, 51, 0.75)" : cssVar("--rotor");
      ctx.beginPath(); this._polyPath(p.pts, 0); ctx.fill();
    }
    ctx.globalAlpha = 1;
    // traces: true width from the file (no minimum).  A loop set or a layer under the mouse (highlight,
    // highlightLayer) is drawn last, thicker, over the others faded; a set switched off (hiddenNets) is not
    // drawn, nor are its vias.
    const role = (net) => this.netRole[net];
    const off = (net) => this.hiddenNets.has(role(net)) || this.hiddenSets.has(this.netSet[net]);
    const hlRole = this.highlight && !this.hiddenNets.has(this.highlight) ? this.highlight : null;
    const hlSet = this.highlightSet && !this.hiddenSets.has(this.highlightSet) ? this.highlightSet : null;
    const hl = hlRole || hlSet || hlCu;
    const lit = (g) => hlRole ? role(g.net) === hlRole : hlSet ? this.netSet[g.net] === hlSet : g.layer === hlCu;
    const segs = Object.values(b.segments);
    for (const pass of hl ? ["rest", "hl"] : ["all"]) {
      ctx.globalAlpha = pass === "rest" ? FADED : 1;
      for (const layer of LAYER_ORDER) {
        if (this.hidden.has(layer)) continue;
        ctx.strokeStyle = this._layerColour(layer);
        for (const g of segs) {
          if (g.layer !== layer || off(g.net)) continue;
          if (pass !== "all" && lit(g) !== (pass === "hl")) continue;
          ctx.lineWidth = pass === "hl" ? Math.max(2.5 * g.width, g.width + 2.5 * px) : g.width;
          ctx.beginPath();
          const q = g.pts;
          for (let k = 0; k < q.length; k += 4) { ctx.moveTo(q[k], q[k + 1]); ctx.lineTo(q[k + 2], q[k + 3]); }
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    // vias: bright gold at their true size (pad = size, hole = drill); the darker rim is drawn inside the pad.
    // "Vias" in the layer chips hides them; hovering that chip (viaBoost) shows small ones at least 6 px across.
    const viaFill = cssVar("--via"), viaRim = cssVar("--via-rim");
    for (const v of this.hidden.has("Vias") ? [] : b.vias) {
      if (off(v.net)) continue;
      if (v.layers.every((l) => this.hidden.has(l))) continue;                // a via shows while one of its layers does
      ctx.globalAlpha = hlRole ? (role(v.net) === hlRole ? 1 : FADED) : hlSet ? (this.netSet[v.net] === hlSet ? 1 : FADED)
        : hlCu ? (v.layers.includes(hlCu) ? 1 : FADED) : 1;
      const k = this.viaBoost ? Math.max(1, 3 * px / (v.d / 2)) : 1;          // scale up only if smaller than 6 px
      const d = v.d * k, drill = v.drill * k;
      const r = d / 2, rim = (d - drill) / 2 * 0.3;
      ctx.fillStyle = viaFill;
      ctx.beginPath(); ctx.arc(v.x, v.y, r, 0, 2 * Math.PI); ctx.fill();
      ctx.strokeStyle = viaRim; ctx.lineWidth = rim;
      ctx.beginPath(); ctx.arc(v.x, v.y, r - rim / 2, 0, 2 * Math.PI); ctx.stroke();
      ctx.fillStyle = "#f4f1ea";
      ctx.beginPath(); ctx.arc(v.x, v.y, drill / 2, 0, 2 * Math.PI); ctx.fill();
    }
    ctx.globalAlpha = 1;
    this._drawSilk(b, px, hl);
    ctx.strokeStyle = cssVar("--edge");
    for (const c of b.circles) {
      if (c.layer !== "Edge.Cuts") continue;
      ctx.lineWidth = 2.5 * px;                          // the one exception to true scale: always a visible 2.5 px
      ctx.beginPath(); ctx.arc(c.cx, c.cy, c.r, 0, 2 * Math.PI); ctx.stroke();
    }
  }

  /* the silkscreen suggestion, at its true widths, in one grey (the file's own colour is the ink, usually white).
     The bottom silkscreen holds the same marks with mirrored lettering; it is off until its chip is switched on. */
  _drawSilk(b, px, faded) {
    const ctx = this.ctx;
    for (const layer of SILK_LAYERS) {
      if (this.hidden.has(layer)) continue;
      ctx.globalAlpha = faded ? FADED : 1;
      ctx.strokeStyle = ctx.fillStyle = cssVar("--silk") || "#6b6b6b";
      for (const dashed of [false, true]) {
        ctx.setLineDash(dashed ? [0.35, 0.3] : []);
        for (const s of b.silk) {
          if (s.layer !== layer || s.dash !== dashed) continue;
          ctx.lineWidth = Math.max(s.w, px);
          ctx.beginPath(); ctx.moveTo(s.x1, s.y1); ctx.lineTo(s.x2, s.y2); ctx.stroke();
        }
      }
      ctx.setLineDash([]);
      for (const d of b.dots) {
        if (d.layer !== layer) continue;
        ctx.beginPath(); ctx.arc(d.cx, d.cy, d.r, 0, 2 * Math.PI);
        if (d.solid) ctx.fill(); else { ctx.lineWidth = Math.max(0.12, px); ctx.stroke(); }
      }
    }
    ctx.globalAlpha = 1;
  }

  _polyPath(pts, angleDeg) {
    const ctx = this.ctx, [cx, cy] = this.center;
    // KiCad y points down: -angle turns the rotor counter-clockwise on screen (like the Y-up readout)
    const a = -angleDeg * Math.PI / 180, ca = Math.cos(a), sa = Math.sin(a);
    for (let k = 0; k < pts.length; k += 2) {
      const dx = pts[k] - cx, dy = pts[k + 1] - cy;
      const x = cx + dx * ca - dy * sa, y = cy + dx * sa + dy * ca;
      k ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.closePath();
  }

  _drawRotorOverlay() {
    const b = this.rotor; if (!b) return;
    const ctx = this.ctx;
    for (const p of b.polys) {
      if (!LAYER_INFO[p.layer]) continue;
      ctx.fillStyle = cssVar("--rotor");
      ctx.beginPath(); this._polyPath(p.pts, this.rotorAngle); ctx.fill();   // filled only, like the file
    }
  }

  /* the origin, Onshape style: a black dot inside a thin black ring, with a small gap between them.  Like the board
     edge it keeps one size on screen at any zoom; hovering the Origin button colours it (no size change). */
  _drawOrigin(px) {
    const ctx = this.ctx, [cx, cy] = this.center;
    ctx.fillStyle = ctx.strokeStyle = this.originBoost ? cssVar("--accent") : "#000";
    ctx.beginPath(); ctx.arc(cx, cy, 1.7 * px, 0, 2 * Math.PI); ctx.fill();         // dot: 3.4 px across
    ctx.lineWidth = 0.9 * px;
    ctx.beginPath(); ctx.arc(cx, cy, 3.9 * px, 0, 2 * Math.PI); ctx.stroke();        // ring: about 9 px across
  }

  /* S key: keep the finished line on screen and start a new one.  Returns the number kept, or 0 if there was no
     finished line or the limit is reached. */
  lockMeasure() {
    if (!this.measure || !this.mA || !this.mB || this.mLocked.length >= BoardView.MAX_LOCKED) return 0;
    this.mLocked.push([this.mA, this.mB]);
    this.mA = this.mB = null;
    this.draw();
    return this.mLocked.length;
  }
  /* Z key: remove the line being drawn (finished or only started); with none, remove the last kept line */
  undoMeasure() {
    if (!this.measure) return;
    if (this.mA) this.mA = this.mB = null; else this.mLocked.pop();
    this.draw();
  }
  clearMeasure() { this.mA = this.mB = null; this.mLocked = []; }

  _drawMeasure(px) {
    if (!this.measure) return;
    this.mLocked.forEach(([a, b], i) => this._drawLine(px, a, b, i + 1));
    if (this.mA) this._drawLine(px, this.mA, this.mB, this.mLocked.length + 1);   // the line being drawn is the next one
  }
  _drawLine(px, a, b, n) {                                // line n: end dots, the line, "Ln: length"
    const ctx = this.ctx;
    ctx.fillStyle = cssVar("--accent"); ctx.strokeStyle = cssVar("--accent"); ctx.lineWidth = 1.5 * px;
    for (const p of [a, b].filter(Boolean)) { ctx.beginPath(); ctx.arc(p[0], p[1], 3 * px, 0, 2 * Math.PI); ctx.fill(); }
    if (b) {
      ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.stroke();
      const d = Math.hypot(b[0] - a[0], b[1] - a[1]);
      ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
      const dpr = window.devicePixelRatio || 1;
      const sx = b[0] * this.view.scale + this.view.ox, sy = b[1] * this.view.scale + this.view.oy;
      ctx.font = `${13 * dpr}px ${cssVar("--ui-font")}`;
      const label = `L${n}: ${d.toFixed(3)} mm`;
      ctx.fillStyle = "rgba(255,255,255,0.9)";
      ctx.fillRect(sx + 8 * dpr, sy - 18 * dpr, ctx.measureText(label).width + 12 * dpr, 20 * dpr);
      ctx.fillStyle = cssVar("--accent"); ctx.fillText(label, sx + 14 * dpr, sy - 3 * dpr);
      ctx.restore();
    }
  }
}

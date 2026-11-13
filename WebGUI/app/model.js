/* model.js - the settings of the two generators, as the page holds them.

   Every value lives in state.modes[gen].values as {file: {NAME: value}}, the way the generators keep them: one
   object per parameter file, since the dual files repeat the names (LOOPS is in Dual_RX1 and in Dual_RX2).  The list
   of files and settings, their kinds, ranges and published values come from the generator's own tables
   (WebGenerator.describe).

   A category ("Board", "RX", "TX", "Rotor", "IC", "Silk") is what a tab shows.  Single has one file per category;
   Dual has one board file, one silkscreen file and, for RX, TX, Rotor and IC, one file per coil set. */

import { state, M, same, clone } from "./core.js";
import { ask } from "./engine.js";

export const CATS = ["Board", "RX", "TX", "Rotor", "IC", "Silk"];
export const CAT_TITLE = { Board: "Board", RX: "RX", TX: "TX", Rotor: "Rotor", IC: "IC", Silk: "Silk" };
const listeners = [];
/* fn(from) is called after values changed; from says who changed them ("basic", "advanced", "import", ...) */
export function onChange(fn) { listeners.push(fn); }

export async function loadMode(gen) {
  const m = state.modes[gen];
  if (m.loaded) return m;
  const d = await ask("describe", { mode: gen });
  m.files = d.files.map((f) => Object.assign(f, { cat: f.label.replace(/ [12]$/, "").replace(/^Silkscreen suggestion$/, "Silk") }));
  for (const f of m.files) {
    m.params[f.file] = {}; m.start[f.file] = {}; m.inactive[f.file] = new Set(); m.errors[f.file] = {}; m.lastNumbers[f.file] = {};
    for (const p of f.parameters) { p.file = f.file; p.set = f.set; p.cat = f.cat; m.params[f.file][p.name] = p; m.start[f.file][p.name] = p.default; }
  }
  m.values = clone(m.start);
  m.loaded = true;
  return m;
}

export const hasSets = (gen = state.gen) => gen === "dual";
/* the file a category's tab shows (Dual: of the coil set chosen) */
export function fileOf(cat, set = M().set) {
  const files = M().files.filter((f) => f.cat === cat);
  return (files.find((f) => f.set === set) || files.find((f) => f.set === 0) || files[0] || {}).file;
}
export const catHasSets = (cat) => M().files.some((f) => f.cat === cat && f.set > 0);
/* the file that holds a setting, looked for in the files of the coil set first, then in the others
   (Dual: ROTOR_MODE is the board's, ROTOR_AUTO_DUTY is each rotor ring's) */
export function where(name, set = M().set) {
  const m = M();
  const own = m.files.find((f) => f.set === set && name in m.params[f.file]);
  const any = own || m.files.find((f) => f.set === 0 && name in m.params[f.file]);
  return any ? any.file : null;
}
export const param = (file, name) => (M().params[file] || {})[name];
export const val = (file, name) => (M().values[file] || {})[name];
export const startVal = (file, name) => (M().start[file] || {})[name];
export const isChanged = (file, name) => !same(val(file, name), startVal(file, name));
export function changedIn(file) {
  const p = M().params[file] || {};
  return Object.keys(p).filter((n) => !p[n].readOnly && isChanged(file, n)).length;
}
export function changedTotal() { return M().files.reduce((n, f) => n + changedIn(f.file), 0); }
/* a look-up by name alone, for the code that knows a setting only by its name (v("PCB_LAYERS")) */
export function v(name, set) { const f = where(name, set); return f ? val(f, name) : undefined; }

/* ---- the RX band rule (approved by Roland) --------------------------------------------------- */
/* The RX band is given as an inside and outside radius, or as a centre (R Base) and a swing (A), or by neither (both
   pairs None: the generator places it).  The two members of a pair go together (both numbers or both None) and only
   one pair may be given: setValues keeps to that, so a change never leaves the checker an error it could have been
   spared.  The rule works inside one RX file (Dual: each set's own). */
export const BAND_RADII = ["INSIDE_RADIUS_MM", "OUTSIDE_RADIUS_MM"];
export const BAND_CENTRE = ["RX_R_BASE_MM", "RX_A_MM"];
const NUMBER_FALLBACK = { RX_R_BASE_MM: 18.8, RX_A_MM: 2.6 };          // when a None setting has no number to go back to
export function pairOf(name) { return BAND_RADII.includes(name) ? BAND_RADII : BAND_CENTRE.includes(name) ? BAND_CENTRE : null; }

/* A band pair that is None is locked while the other pair has numbers.  Both None = both unlocked. */
export function bandLock(file, name) {
  const pair = pairOf(name), vals = M().values[file];
  if (!pair || pair.some((n) => vals[n] !== null)) return null;
  const other = pair === BAND_RADII ? BAND_CENTRE : BAND_RADII;
  if (other.every((n) => vals[n] === null)) return null;
  return `Locked: the RX band is set by ${other === BAND_RADII ? "RX Inside Radius and RX Outside Radius" : "RX R Base and RX Swing A"}. Set those to None first to use this pair`;
}

/* The number a None setting goes back to when its switch is turned off.  A band member follows the other pair, so
   switching between "radii" and "centre and swing" keeps the same band; otherwise the last number it had, then its
   published value. */
export function numberFor(file, name, vals = M().values[file]) {
  const num = (x) => typeof x === "number", round = (x) => Math.round(x * 1000) / 1000;
  const [ri, ro, base, a] = [...BAND_RADII, ...BAND_CENTRE].map((n) => vals[n]);
  if (name === "INSIDE_RADIUS_MM" && num(base) && num(a)) return round(base - a);
  if (name === "OUTSIDE_RADIUS_MM" && num(base) && num(a)) return round(base + a);
  if (name === "RX_R_BASE_MM" && num(ri) && num(ro)) return round((ri + ro) / 2);
  if (name === "RX_A_MM" && num(ri) && num(ro)) return round((ro - ri) / 2);
  const last = M().lastNumbers[file][name];
  if (num(last)) return last;
  if (num(startVal(file, name))) return startVal(file, name);
  const p = param(file, name) || {}, o = p.options || {};
  if (num(o.default)) return o.default;
  return NUMBER_FALLBACK[name] ?? (num(o.lo) && !o.lo_ex ? o.lo : 1);
}

function withBandRules(changes) {
  const out = changes.map((c) => c.slice());
  const m = M();
  for (const file of new Set(changes.map((c) => c[0]))) {
    const mine = changes.filter((c) => c[0] === file && pairOf(c[1]));
    if (!mine.length) continue;
    const vals = Object.assign({}, m.values[file]);
    for (const [, n, x] of changes.filter((c) => c[0] === file)) vals[n] = x;
    const put = (n, x) => { vals[n] = x; const i = out.findIndex((c) => c[0] === file && c[1] === n); if (i >= 0) out[i][2] = x; else out.push([file, n, x]); };
    const remember = (n) => { if (typeof vals[n] === "number") m.lastNumbers[file][n] = vals[n]; };
    for (const [, name, x] of mine) {
      const pair = pairOf(name), partner = pair.find((n) => n !== name), other = pair === BAND_RADII ? BAND_CENTRE : BAND_RADII;
      if (x === null) {
        if (vals[partner] !== null) { remember(partner); put(partner, null); }
      } else {
        if (vals[partner] === null) put(partner, numberFor(file, partner, vals));       // read the other pair before it is cleared
        for (const n of other) if (vals[n] !== null) { remember(n); put(n, null); }
      }
    }
  }
  return out;
}

/* ---- changing values -------------------------------------------------------------------------- */
/* changes: [[file, NAME, value], ...].  A loaded or reset design is taken as it is; every other change goes through
   the RX band rule.  Returns true when something changed. */
export function setValues(changes, from) {
  const m = M();
  if (from !== "import" && from !== "reset" && from !== "share") changes = withBandRules(changes);
  let any = false;
  for (const [file, name, x] of changes) {
    if (!m.params[file] || !(name in m.params[file]) || m.params[file][name].readOnly) continue;
    if (!same(m.values[file][name], x)) { m.values[file][name] = x; any = true; }
  }
  if (!any) return false;
  if (m.good) m.stale = true;
  for (const fn of listeners) fn(from);
  scheduleChecks();
  return true;
}
export const setOne = (file, name, x, from) => setValues([[file, name, x]], from);
export function resetAll() {
  const m = M(), changes = [];
  for (const f of m.files) for (const p of f.parameters) changes.push([f.file, p.name, clone(m.start[f.file][p.name])]);
  return setValues(changes, "reset");
}

/* ---- what the generator says about the values, as they are typed ------------------------------- */
let checkTimer = null, checkListeners = [];
export function onChecked(fn) { checkListeners.push(fn); }
export function scheduleChecks(delay = 150) {
  clearTimeout(checkTimer);
  checkTimer = setTimeout(refreshChecks, delay);
}
export async function refreshChecks() {
  if (!state.ready || state.busy) return;
  const gen = state.gen, m = state.modes[gen];
  try {
    const [inactive, errors] = await Promise.all([
      ask("inactive", { mode: gen, values: m.values }), ask("check", { mode: gen, values: m.values })]);
    for (const f of m.files) { m.inactive[f.file] = new Set(inactive[f.file] || []); m.errors[f.file] = errors[f.file] || {}; }
    if (gen === state.gen) for (const fn of checkListeners) fn();
  } catch (e) { /* the next change tries again */ }
}

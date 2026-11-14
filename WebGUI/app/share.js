/* share.js - a design as a link, as files to keep, and back from files.

   A link carries only the settings that differ from the published design, as {file: {NAME: value}}:
     #single=...   a design of the Single Coil Set Generator
     #dual=...     a design of the Dual Coil Set Generator
     #d=...        a link made before the two generators were one page: a flat {NAME: value} that counted from the
                   starting design of that page (LEGACY_START), so it still opens the board it was made for.
   Export gives the parameter files as the desktop generator reads them; Import reads those files, the zip, or the
   Parameters.txt record a run writes (WebGenerator.read_import). */

import { state, M, toast, download, copyText, plural, has } from "./core.js";
import { ask } from "./engine.js";
import { setValues, isChanged, val } from "./model.js";

const BLOG_HOME = "https://ro-h-bots.blogspot.com/";
const MAX_LINK = 20000, MAX_FILE = 8 * 1048576;
/* where the page of before started from, for the settings whose published value has changed since */
const LEGACY_START = { VIA_DIAMETER_MM: 0.6, VIA_DRILL_MM: 0.3, INNER_EDGE_RADIUS_MM: 30, OUTER_EDGE_RADIUS_MM: 50, LOOPS: 4,
  INSIDE_RADIUS_MM: null, OUTSIDE_RADIUS_MM: null, RX_NET_PHASE_0_2: "SIN_Signal", RX_NET_PHASE_1_3: "COS_Signal", RX_TAB_LENGTH_MM: 5,
  TX_WIRING: "series", TX_LAYER_A: 1, TX_LAYER_B: 4, ROTOR_SOLDER_MASK_EXPANSION_MM: 0.05 };

const short = (file) => file.replace(/^Dual_/, "").replace(/_Parameters\.py$/, "");
function pack(obj) {
  const bytes = new TextEncoder().encode(JSON.stringify(obj));
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function unpack(text) {
  const s = atob(text.replace(/-/g, "+").replace(/_/g, "/"));
  return JSON.parse(new TextDecoder().decode(Uint8Array.from(s, (c) => c.charCodeAt(0))));
}
const plain = (x) => x === null || ["number", "string", "boolean"].includes(typeof x) || (Array.isArray(x) && x.length <= 16 && x.every((y) => ["number", "string"].includes(typeof y)));

/* the changed settings of the chosen generator: {short file name: {NAME: value}} */
function changed() {
  const out = {};
  for (const f of M().files) for (const p of f.parameters) {
    if (!p.readOnly && isChanged(f.file, p.name)) (out[short(f.file)] = out[short(f.file)] || {})[p.name] = val(f.file, p.name);
  }
  return out;
}
export function designLink(base) {
  const d = changed();
  return Object.keys(d).length ? `${base}#${state.gen}=${pack(d)}` : state.gen === "dual" ? `${base}#dual=` : base;
}

/* What a link asks for: {gen, design} or null.  design is {short file: {NAME: value}}, or for an old link
   {legacy: {NAME: value}}.  Nothing of it is trusted: applyDesign takes only values of settings that exist. */
export function readHash(hash) {
  const m = /^#(single|dual|d)=([A-Za-z0-9_-]*)$/.exec(hash || "");
  if (!m || hash.length > MAX_LINK) return null;
  const gen = m[1] === "dual" ? "dual" : "single";
  if (!m[2]) return { gen, design: {} };
  try {
    const d = unpack(m[2]);
    if (!d || typeof d !== "object" || Array.isArray(d)) return null;
    return { gen, design: m[1] === "d" ? { legacy: d } : d };
  } catch (e) { return null; }
}
/* Put a link's design onto the chosen generator's published values.  Returns the names it could not use. */
export function applyDesign(design) {
  const m = M(), changes = [], unknown = [];
  const take = (file, name, x) => {
    if (file && has(m.params[file], name) && !m.params[file][name].readOnly && plain(x)) changes.push([file, name, x]);
    else unknown.push(name);
  };
  if (design.legacy) {
    const flat = Object.assign({}, LEGACY_START, design.legacy);
    for (const [name, x] of Object.entries(flat)) take((m.files.find((f) => has(m.params[f.file], name)) || {}).file, name, x);
  } else {
    for (const [key, values] of Object.entries(design)) {
      const f = m.files.find((x) => short(x.file) === key);
      if (!f || !values || typeof values !== "object") { unknown.push(key); continue; }
      for (const [name, x] of Object.entries(values)) take(f.file, name, x);
    }
  }
  setValues(changes, "share");
  return unknown;
}

export async function share() {
  if (!M().files.length) return;                 // the settings are not read yet: there is no design to link to
  // embedded: the blog page tells us its address (a cross-origin referrer carries only the site)
  const base = window.self !== window.top ? (state.hostPage || document.referrer.split("#")[0] || BLOG_HOME) : location.href.split("#")[0];
  await copyText(designLink(base), "Link copied");
}

export async function exportFiles() {
  if (!state.ready) return;
  try {
    const r = await ask("exportZip", { mode: state.gen, values: M().values });
    download(r.zipBytes, state.gen === "dual" ? "Dual_Parameter_Files.zip" : "Parameter_Files.zip", "application/zip");
  } catch (e) { toast("Export failed: " + e.message, 6000); }
}

/* Read parameter files, a zip of them, or a Parameters.txt record.  switchTo(gen) is asked for when the files are
   of the other generator. */
export async function importFiles(files, switchTo) {
  if (!state.ready || !files.length) return;
  const items = [];
  for (const f of files) {
    if (f.size > MAX_FILE) { toast(`${f.name} is larger than 8 MB: not read`, 6000); return; }
    if (/\.zip$/i.test(f.name)) items.push({ name: f.name, bytes: await f.arrayBuffer() });
    else items.push({ name: f.name, text: await f.text() });
  }
  let r;
  try { r = await ask("readImport", { items }); }
  catch (e) { toast("Import failed: " + e.message, 7000); return; }
  const changes = [];
  for (const [file, values] of Object.entries(r.values || {})) for (const [name, x] of Object.entries(values)) changes.push([file, name, x]);
  const ignored = r.ignored || [];
  if (!changes.length) {
    toast(ignored.length ? `No values taken. Ignored: ${ignored.join("; ")}` : "No parameter values found in that file", 6000);
    return;
  }
  if (r.mode && r.mode !== state.gen) {
    await switchTo(r.mode);
    if (r.mode !== state.gen) { toast(`These are ${r.mode === "dual" ? "Dual" : "Single"} files: wait for the run to end, then import them again`, 6000); return; }
  }
  setValues(changes, "import");
  // what was not taken is named with its reason (a setting of another version, a value no setting can hold)
  toast(`Loaded ${plural(changes.length, "value")}` + (r.mode === "dual" ? " of a Dual design" : "") +
    (ignored.length ? `. Ignored: ${ignored.join("; ")}` : ""), ignored.length ? 7000 : 2600);
}

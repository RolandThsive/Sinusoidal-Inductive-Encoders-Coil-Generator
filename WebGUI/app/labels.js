/* labels.js - the words the page shows for the generators' names: settings, their groups, their choices.

   Nothing here changes a value: a setting keeps the name, the choices and the limits its generator gives it. */

import { fmt } from "./core.js";

export const LAYER_NUM_NAME = { 1: "Top", 2: "Inner-1", 3: "Inner-2", 4: "Bottom" };
export const LAYER_NUM_CU = { 1: "F.Cu", 2: "In1.Cu", 3: "In2.Cu", 4: "B.Cu" };
export const CU_NAME = { "F.Cu": "Top", "In1.Cu": "Inner-1", "In2.Cu": "Inner-2", "B.Cu": "Bottom" };
export const COPPER = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"];

/* names the word rule in labelOf would make unclear, and the Basic labels (keep these in step with the Basic pages) */
const LABELS = { RX_NET_PHASE_0_2: "RX Net SIN (Phases 0 / 2)", RX_NET_PHASE_1_3: "RX Net COS (Phases 1 / 3)",
  INNER_EDGE_RADIUS_MM: "Board Inner Radius", OUTER_EDGE_RADIUS_MM: "Board Outer Radius", PCB_LAYERS: "Board Layers",
  RX_SUBCOILS: "RX Sub-Coils", INSIDE_RADIUS_MM: "RX Inside Radius", OUTSIDE_RADIUS_MM: "RX Outside Radius", RX_A_MM: "RX Swing A",
  TX_TURNS: "TX Turns Per Layer", ROTOR_AUTO_DUTY: "Rotor Metal Fraction", ROTOR_AUTO_COVER_TX: "Copper Over The TX Turns",
  ROTOR_CUSTOM_SECTORS: "Rotor Metal Sectors", ROTOR_CUSTOM_DUTY: "Rotor Metal Fraction",
  COPPER_CONDUCTIVITY_S_M: "Copper Conductivity (S/m)", IC_MIN_RP_OHM: "IC Min Rp (ohm)",
  IC_OSC_MIN_MHZ: "IC Osc Min (MHz)", IC_OSC_MAX_MHZ: "IC Osc Max (MHz)" };
const UNITS = { MM: "(mm)", DEG: "(deg)", HZ: "(Hz)", UM: "(µm)" };
const UPPER = ["RX", "TX", "PCB", "IC", "AC"];

/* the setting's name in capitalised words, with its unit split off: {text, unit} */
export function labelOf(name) {
  const parts = name.split("_");
  let unit = "";
  if (UNITS[parts[parts.length - 1]]) unit = UNITS[parts.pop()];
  if (LABELS[name]) return { text: LABELS[name], unit: /\)$/.test(LABELS[name]) ? "" : unit };
  const words = parts.map((w) => (UPPER.includes(w) ? w : /^\d+$/.test(w) ? w : w[0] + w.slice(1).toLowerCase()));
  return { text: words.join(" "), unit };
}
export function labelText(name) { const l = labelOf(name); return l.unit ? `${l.text} ${l.unit}` : l.text; }

/* nicer names for the parameter files' section headings */
const GROUP_TITLES = {
  "Board outline (Edge.Cuts circles)": "Board Outline",
  "Board edges (Edge.Cuts circles) and the gap between the sets": "Board Edges And The Gap Between The Sets",
  'SERIES block (TX_WIRING = "single" or "series")': "Series TX",
  'PARALLEL block (TX_WIRING = "parallel")': "Parallel TX",
  "According_to_stator": "Automatic Rotor",
  "Outer edge of the copper: over the TX turns (default)": "Automatic Rotor: Edges",
  "Custom": "Custom Rotor",
  'ROTOR_MODE = "custom"': "Custom Rotor",
  "Both modes": "Both Rotor Modes",
};
const GENERAL = { TX: "TX Turns", Rotor: "Rotor Mode" };
export function groupTitle(heading, cat) {
  if (GROUP_TITLES[heading]) return GROUP_TITLES[heading];
  if (/^ROTOR_MODE = "according_to_stator"/.test(heading)) return "Automatic Rotor";
  if (heading === "General") return GENERAL[cat] || "General";
  return heading.replace(/\bTx\b/g, "TX").replace(/\bRx\b/g, "RX").replace(/\bIc\b/g, "IC").replace(/'S\b/g, "'s");
}
/* the rotor blocks that belong to one Rotor Mode fold away when the other mode is chosen (the arrow opens them again) */
export const ROTOR_MODE_GROUPS = { "Automatic Rotor": "according_to_stator", "Automatic Rotor: Edges": "according_to_stator", "Custom Rotor": "custom" };

const CHOICE_WORDS = { according_to_stator: "Automatic", rx_zero: "RX Zero", e6: "E6", e12: "E12", e24: "E24" };
/* the word shown for one choice of a setting */
export function choiceText(name, val) {
  if (val === null) return "None";
  if (val === "auto") return "Auto";
  // layer numbers (TX_LAYER_A, RX_TAB_LAYER, ...) read as layer names; the layer count (PCB_LAYERS) as a count
  if (typeof val === "number" && /LAYERS$/.test(name)) return `${val} Layer${val === 1 ? "" : "s"}`;
  if (typeof val === "number" && /LAYER(_[AB])?$/.test(name) && LAYER_NUM_NAME[val]) return LAYER_NUM_NAME[val];
  if (CU_NAME[val]) return CU_NAME[val];
  if (typeof val === "boolean") return val ? "True" : "False";
  if (typeof val === "string" && CHOICE_WORDS[val.toLowerCase()]) return CHOICE_WORDS[val.toLowerCase()];
  if (typeof val === "string") return val.split("_").map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w)).join(" ");
  return String(val);
}

/* how far one press of + or − moves a number setting */
export function stepOf(p) {
  const d = p.default;
  if (p.kind === "int") return 1;
  if (p.kind === "steps" || p.kind === "auto_or_int") return 8;
  if (/CHORD_TOLERANCE_MM$/.test(p.name)) return 0.001;
  if (/HZ$/.test(p.name)) return 100000;
  if (/S_M$/.test(p.name)) return 1000000;
  if (/DEG$/.test(p.name)) return 1;
  if (typeof d === "number" && Math.abs(d) >= 100) return 1;
  if (typeof d === "number" && String(d).includes(".") && String(d).split(".")[1].length >= 2) return 0.05;
  return 0.001;
}

/* a value as the parameter files write it, for tooltips and messages */
export function showValue(v) {
  if (v === null || v === undefined) return "None";
  if (typeof v === "boolean") return v ? "True" : "False";
  if (Array.isArray(v)) return `(${v.map(showValue).join(", ")})`;
  if (typeof v === "string") return v;
  return fmt(v);
}

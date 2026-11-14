/* crash.js - when something breaks, say so: a dialog with what happened, the details to copy, and a link that opens
   a GitHub issue already filled in (the browser, the build, the details).  Nothing is sent anywhere by the page
   itself: the visitor sees the text and sends it, or does not.

   boot.js keeps the errors that happen before this module runs (COILGEN.errors). */

import { $, state, copyText } from "./core.js";

const ISSUES = "https://github.com/RolandThsive/Sinusoidal-Inductive-Encoders-Coil-Generator/issues/new";
const QUIET = /ResizeObserver loop/;                // a browser notice, not a fault of the page
const errors = [];
let shown = false;

function about() {
  const b = state.build;
  return [`Browser: ${navigator.userAgent}`, `Build: ${b ? `${b.commit} (${b.built})` : "unknown"}`,
    `Page: ${location.origin}${location.pathname}`, `Generator: ${state.gen}, ${state.view}`].join("\n");
}
export function reportUrl(text = "", details = "") {
  const body = `What happened:\n${text}\n\nWhat I did before it happened:\n\n\n---\n${about()}\n\n${details ? "Details:\n```\n" + details.slice(0, 2500) + "\n```\n" : ""}`;
  return `${ISSUES}?title=${encodeURIComponent("Web tool: " + (text || "a problem").slice(0, 80))}&body=${encodeURIComponent(body)}`;
}
/* Show the dialog.  text: one or two plain sentences; details: what a developer needs (a traceback, a message). */
export function showCrash(text, details = "") {
  const earlier = errors.length ? "\n\nErrors of the page:\n" + errors.slice(-8).map((e) => `[${e.kind}] ${e.message} ${e.where}`.trim()).join("\n") : "";
  const full = `${details}${earlier}\n\n${about()}`.trim();
  $("crash-text").textContent = text;
  $("crash-details").textContent = full;
  $("crash-report").href = reportUrl(text, `${details}${earlier}`);
  const d = $("crash-dialog");
  if (!d.open) d.showModal();
}

export function initCrash() {
  const take = (item) => {
    errors.push(item);
    if (errors.length > 50) errors.shift();
    if ((item.kind === "error" || item.kind === "promise") && !QUIET.test(item.message) && !shown) {
      shown = true;                                   // one dialog: the first fault is the one that matters
      showCrash("The page hit an error it did not expect. Your settings are still here; if something looks wrong, reload the page.", `${item.message} ${item.where}`.trim());
    }
  };
  for (const item of window.COILGEN.errors.splice(0)) take(item);
  window.COILGEN.onError = take;
  $("crash-copy").addEventListener("click", () => copyText(`${$("crash-text").textContent}\n\n${$("crash-details").textContent}`, "Details copied"));
  $("crash-reload").addEventListener("click", () => location.reload());
  $("report-link").addEventListener("click", (e) => { e.currentTarget.href = reportUrl(); });
}

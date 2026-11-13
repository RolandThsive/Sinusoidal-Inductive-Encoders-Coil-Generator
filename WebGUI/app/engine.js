/* engine.js - the page's side of PyodideWorker.js: start it, ask it, cancel it.

   ask(cmd, args, onLine) sends {id, cmd, args} and resolves with the worker's result; onLine(text, stream) is called
   for every line the generator prints during that request.  start() loads Python from the first source that answers:
   the CDN first, the site's own backup copy when the CDN does not send Pyodide's script within 15 s or fails.
   cancel() ends the worker (a running generator cannot be stopped from outside) and starts a new one. */

let worker = null, nextId = 1, config = null, base = null;
const pending = new Map();
let onProgress = null, onStage = null, onCrash = null;

export function configure(c) { config = c; onProgress = c.onProgress || null; onCrash = c.onCrash || null; }
export const source = () => base;

function failAll(error) {
  for (const p of pending.values()) p.reject(error);
  pending.clear();
}

function spawn() {
  worker = new Worker(new URL("../PyodideWorker.js", import.meta.url), { type: "module" });
  const mine = worker;
  worker.onmessage = (ev) => {
    if (mine !== worker) return;                                   // a worker that was cancelled
    const m = ev.data;
    if (m.type === "progress") { if (onProgress) onProgress(m.text); return; }
    if (m.type === "stage") { if (onStage) onStage(m.stage); return; }
    if (m.type === "line") { const p = pending.get(m.id); if (p && p.onLine) p.onLine(m.text, m.stream); return; }
    const p = pending.get(m.id); if (!p) return;
    pending.delete(m.id);
    if (m.ok) p.resolve(m.result);
    else p.reject(new Error(m.error));
  };
  worker.onerror = (e) => {
    if (mine !== worker) return;
    const error = new Error("The Python worker stopped: " + (e.message || "it could not be started"));
    failAll(error);
    if (onCrash) onCrash(error);
  };
}

export function ask(cmd, args, onLine) {
  return new Promise((resolve, reject) => {
    if (!worker) { reject(new Error("Python is not running")); return; }
    const id = nextId++;
    pending.set(id, { resolve, reject, onLine });
    worker.postMessage({ id, cmd, args });
  });
}

function stop() {
  if (worker) { worker.onmessage = worker.onerror = null; worker.terminate(); worker = null; }
}

/* Load Python from `from`.  Rejects when the worker fails, or (wait > 0) when Pyodide's own script has not arrived
   after `wait` ms. */
function initFrom(from, wait) {
  stop();
  spawn();
  return new Promise((resolve, reject) => {
    let timer = null;
    if (wait > 0) {
      timer = setTimeout(() => { onStage = null; reject(new Error(`no answer from ${from} after ${wait / 1000} s`)); }, wait);
      onStage = (stage) => { if (stage === "runtime-js") { clearTimeout(timer); onStage = null; } };
    }
    ask("init", { pyodideBase: from, bundle: config.bundle }).then(
      (r) => { clearTimeout(timer); onStage = null; resolve(r); },
      (e) => { clearTimeout(timer); onStage = null; reject(e); });
  });
}

/* Start Python.  Returns {seconds, python, numpy, source, backup}: backup is true when the CDN was not used. */
export async function start() {
  const tried = [];
  for (let i = 0; i < config.sources.length; i++) {
    const from = config.sources[i], last = i === config.sources.length - 1;
    try {
      const r = await initFrom(from, last ? 0 : config.stallMs);
      base = from;
      return Object.assign(r, { source: from, backup: i > 0, tried });
    } catch (e) {
      failAll(new Error("starting again from another source"));
      tried.push(`${from}: ${e.message}`);
      if (last) { stop(); throw new Error(tried.join("; ")); }
      if (onProgress) onProgress("The CDN did not answer: loading Python from this site's own copy…");
    }
  }
  throw new Error("no source for Python is configured");
}

/* End the running worker and start a new one from the source that worked. */
export async function cancel() {
  failAll(new Error("cancelled"));
  return initFrom(base || config.sources[config.sources.length - 1], 0);
}

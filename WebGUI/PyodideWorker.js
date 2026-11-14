/* PyodideWorker.js - runs the two generators in a background thread, so the page never freezes.

   The page sends {id, cmd, args}; the worker answers {id, ok: true, result} or {id, ok: false, error}.
   While it works it also sends, without an id of their own:
     {type: "progress", text}                  what init is doing
     {type: "stage", stage: "runtime-js"}      Pyodide's own script has arrived (the page waits 15 s for this before
                                               it starts again from the site's backup copy)
     {type: "line", id, text, stream}          a line the generator printed during the run `id` ("out" or "err")

   The commands (mode is "single" or "dual"; values are {file name: {NAME: value}}):
     init        {pyodideBase, bundle}         ->  {seconds, python, numpy}
     describe    {mode}                        ->  {mode, files: [{file, label, group, set, parameters: [...]}]}
     inactive    {mode, values}                ->  {file: [names the generator does not use]}
     check       {mode, values}                ->  {file: {NAME: the generator's message}}
     run         {mode, values, checkOnly}     ->  what the program printed, sorted, and the files it wrote
                                                  (WebGenerator.run); zipBytes: the zip of its folder; bytes: {file
                                                  name: its bytes} of every file in that folder
     exportZip   {mode, values}                ->  {zipBytes}
     readImport  {items: [{name, text | bytes}]}  ->  {mode, values, ignored, files}   (WebGenerator.read_import)

   A run cannot be stopped from outside: to cancel, the page ends this worker and starts a new one.

   On "init" the worker loads Pyodide and numpy from pyodideBase, then one zip (bundle) that the site's build made
   from the repository: the generators' own .py files at their own paths and WebGenerator.py.  It is unpacked into
   the in-memory file system at ROOT. */

let pyodide = null;
let WG = null;
const ROOT = "/coilgen";

let step = "";                                   // what init is doing now, named in the message if it fails
function progress(text) { step = text; postMessage({ type: "progress", text }); }

// A dropped connection is tried again (twice) before it is reported, and the report names the file.
async function fetchBytes(url) {
  for (let tries = 1; ; tries++) {
    let r;
    try { r = await fetch(url, { cache: "no-cache" }); }
    catch (e) {
      if (tries < 3) { await new Promise((done) => setTimeout(done, 400 * tries)); continue; }
      throw new Error(`${url} could not be downloaded (${e.message})`);
    }
    if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
    return r.arrayBuffer();
  }
}

async function init({ pyodideBase, bundle }) {
  const t0 = performance.now();
  try {
    progress("Loading Python (Pyodide)…");
    const { loadPyodide } = await import(pyodideBase + "pyodide.mjs");   // Pyodide 314 runs in module workers only
    postMessage({ type: "stage", stage: "runtime-js" });                  // the source answers: the page stops its timer
    pyodide = await loadPyodide({ indexURL: pyodideBase });
    progress("Loading numpy…");
    await pyodide.loadPackage("numpy");
    progress("Loading the generators…");
    const zip = await fetchBytes(bundle);
    pyodide.FS.mkdirTree(ROOT);
    pyodide.unpackArchive(zip, "zip", { extractDir: ROOT });
    progress("Starting the generators…");
    pyodide.runPython(`
import sys
sys.path.insert(0, "${ROOT}/WebGUI")
import WebGenerator as WG
WG.ROOT = "${ROOT}"
`);
    WG = pyodide.globals.get("WG");
    const versions = pyodide.runPython("import sys, numpy; [sys.version.split()[0], numpy.__version__]").toJs();
    return { seconds: (performance.now() - t0) / 1000, python: versions[0], numpy: versions[1] };
  } catch (e) {
    const early = /^Loading (Python|numpy)/.test(step) ? ` from ${pyodideBase}` : "";
    throw new Error(`${e && e.message || e} [${step.replace("…", "")}${early}]`);
  }
}

// Reads a file of the in-memory file system as a copy of exactly its bytes, so it can be transferred to the page.
function readFileBuffer(path) {
  const bytes = pyodide.FS.readFile(path);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function call(fn, ...args) {
  return JSON.parse(WG[fn](...args));
}

onmessage = async (ev) => {
  const { id, cmd, args } = ev.data;
  try {
    let result;
    const transfer = [];
    if (cmd === "init") result = await init(args);
    else if (!WG) throw new Error("the generators are not loaded yet");
    else if (cmd === "describe") result = call("describe", args.mode);
    else if (cmd === "inactive") result = call("inactive", args.mode, JSON.stringify(args.values));
    else if (cmd === "check") result = call("check_values", args.mode, JSON.stringify(args.values));
    else if (cmd === "run") {
      const t0 = performance.now();
      const onLine = (text, stream) => postMessage({ type: "line", id, text, stream });
      result = call("run", args.mode, JSON.stringify(args.values), !!args.checkOnly, onLine);
      result.seconds = (performance.now() - t0) / 1000;
      if (result.zip) {                       // the run wrote files: the page gets them all, so nothing is asked for later
        result.zipBytes = readFileBuffer(result.zip); transfer.push(result.zipBytes);
        result.bytes = {};
        for (const f of result.files) { result.bytes[f.name] = readFileBuffer(f.path); transfer.push(result.bytes[f.name]); }
      }
    } else if (cmd === "exportZip") {
      const r = call("export_zip", args.mode, JSON.stringify(args.values));
      result = { zipBytes: readFileBuffer(r.zip) };
      transfer.push(result.zipBytes);
    } else if (cmd === "readImport") {
      const items = [];
      args.items.forEach((item, i) => {
        if (item.bytes) {                       // a zip: Python opens it from the in-memory file system
          const path = `${ROOT}/import_${i}.zip`;
          pyodide.FS.writeFile(path, new Uint8Array(item.bytes));
          items.push({ name: item.name, path });
        } else items.push({ name: item.name, text: item.text });
      });
      result = call("read_import", JSON.stringify(items));
    } else throw new Error("unknown command " + cmd);
    postMessage({ id, ok: true, result }, transfer);
  } catch (e) {
    postMessage({ id, ok: false, error: String(e && e.message || e) });
  }
};

// Runs HumanLang in a background thread so a stuck program can be stopped.
importScripts("config.js");
const indexURL = new URL(self.HL_CONFIG.pyodideUrl, self.location.href).href;
importScripts(indexURL + "pyodide.js");

let run = null, host = null, live = null, debug = null;

async function init() {
  const py = await loadPyodide({ indexURL });
  const files = await (await fetch("humanlang_src.json")).json();
  py.FS.mkdirTree("/hl/humanlang");
  for (const [name, text] of Object.entries(files)) py.FS.writeFile("/hl/humanlang/" + name, text);
  py.FS.writeFile("/hl/hl_runner.py", await (await fetch("hl_runner.py")).text());
  py.runPython("import sys; sys.path.insert(0, '/hl')");
  const runner = py.pyimport("hl_runner");
  run = runner.run; debug = runner.debug;
  host = py.pyimport("humanlang.gamehost");
  live = py.pyimport("humanlang.livehost");
  postMessage({ type: "ready" });
}

onmessage = (e) => {
  if (e.data.type === "gamestart" && host) { postMessage({ type: "gameinfo", ...JSON.parse(host.start(e.data.code, undefined, e.data.store || undefined, e.data.assets || undefined)) }); return; }
  if (e.data.type === "gameframe" && host) { postMessage({ type: "gameframe", json: host.frame(JSON.stringify(e.data.input)) });
    const mem = host.take_memory(); if (mem) postMessage({ type: "memory", json: mem }); return; }
  if (e.data.type === "debug" && debug) {
    try { postMessage({ type: "debugged", ...JSON.parse(debug(e.data.code, e.data.inputs)) }); }
    catch (err) { postMessage({ type: "debugged", error: "Something went wrong inside the playground: " + err, steps: [] }); }
    return;
  }
  if (e.data.type === "livestart" && live) {
    try { postMessage({ type: "livestarted", ...JSON.parse(live.start(e.data.code, undefined, e.data.store || undefined)) }); }
    catch (err) { postMessage({ type: "livestarted", error: "Something went wrong inside the playground: " + err }); }
    const mem = live.take_memory(); if (mem) postMessage({ type: "memory", json: mem }); return;
  }
  if (e.data.type === "liveevent" && live) {
    try { postMessage({ type: "liveupdate", ...JSON.parse(live.event(JSON.stringify(e.data.msg))) }); }
    catch (err) { postMessage({ type: "liveupdate", error: "Something went wrong inside the playground: " + err }); }
    const mem = live.take_memory(); if (mem) postMessage({ type: "memory", json: mem }); return;
  }
  if (e.data.type !== "run" || !run) return;
  try {
    postMessage({ type: "result", ...JSON.parse(run(e.data.code, e.data.inputs, e.data.seed, e.data.store || undefined)) });
  } catch (err) {
    postMessage({ type: "result", out: "", err: "Something went wrong inside the playground: " + err });
  }
};

init().catch((err) => postMessage({ type: "error", message: String(err) }));

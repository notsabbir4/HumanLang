// Runs HumanLang in a background thread so a stuck program can be stopped.
importScripts("config.js");
const indexURL = new URL(self.HL_CONFIG.pyodideUrl, self.location.href).href;
importScripts(indexURL + "pyodide.js");

let run = null;

async function init() {
  const py = await loadPyodide({ indexURL });
  const files = await (await fetch("humanlang_src.json")).json();
  py.FS.mkdirTree("/hl/humanlang");
  for (const [name, text] of Object.entries(files)) py.FS.writeFile("/hl/humanlang/" + name, text);
  py.FS.writeFile("/hl/hl_runner.py", await (await fetch("hl_runner.py")).text());
  py.runPython("import sys; sys.path.insert(0, '/hl')");
  run = py.pyimport("hl_runner").run;
  postMessage({ type: "ready" });
}

onmessage = (e) => {
  if (e.data.type !== "run" || !run) return;
  try {
    postMessage({ type: "result", ...JSON.parse(run(e.data.code, e.data.inputs)) });
  } catch (err) {
    postMessage({ type: "result", out: "", err: "Something went wrong inside the playground: " + err });
  }
};

init().catch((err) => postMessage({ type: "error", message: String(err) }));

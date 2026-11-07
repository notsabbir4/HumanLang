"""Turn a game program into ONE web page you can put on any website (hl build FILE.hum).

The page carries the game's code and HumanLang itself; it loads Pyodide (Python for the browser) from the internet
the first time it opens, so it needs a connection, but nothing else.
"""
import glob
import html
import json
import os
import re

PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
HERE = os.path.dirname(os.path.abspath(__file__))


def source_dir():
    """Where HumanLang's own files are: next to this file, or (inside the single-file hl program) in humanlang_src."""
    if glob.glob(os.path.join(HERE, "*.py")):
        return HERE
    return os.path.join(os.path.dirname(HERE), "humanlang_src")

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>
html,body{margin:0;height:100%;background:#0b0d14;color:#e8eaf2;font:16px system-ui,sans-serif}
body{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px}
#screen{display:block;image-rendering:pixelated;background:#000;outline:none;border-radius:4px;box-shadow:0 0 0 2px #2a2f45,0 12px 40px #0008}
#note{min-height:1.4em;text-align:center;max-width:90vw;white-space:pre-wrap;color:#9aa3c0;font-size:14px}
#note.bad{color:#ff9a9a;text-align:left;font-family:ui-monospace,Menlo,Consolas,monospace}
button{font:inherit;background:#1b2036;color:inherit;border:1px solid #3a4163;border-radius:8px;padding:.3em .9em;cursor:pointer}
footer{font-size:12px;color:#6c7494}
</style></head><body>
<canvas id="screen" tabindex="0" width="10" height="10"></canvas>
<div id="note">Loading the game... (the first time takes a few seconds)</div>
<div><button id="mute">Sound: on</button> <button id="again" hidden>Play again</button></div>
<footer>Made with HumanLang</footer>
<script src="__PYODIDE__pyodide.js"></script>
<script>__ARCADE__</script>
<script>
const FILES = __FILES__;
const CODE = __CODE__;
const note = document.getElementById("note"), canvas = document.getElementById("screen");
let game = null, py = null, muted = false;
function fit(info) {
  const k = Math.max(1, Math.floor(Math.min((innerWidth - 24) / info.w, (innerHeight - 140) / info.h)));
  canvas.style.width = info.w * k + "px"; canvas.style.height = info.h * k + "px";
}
function bad(text) { note.className = "bad"; note.textContent = text; }
async function boot() {
  py = await loadPyodide({ indexURL: "__PYODIDE__" });
  py.FS.mkdirTree("/hl/humanlang");
  for (const [n, t] of Object.entries(FILES)) py.FS.writeFile("/hl/humanlang/" + n, t);
  py.runPython("import sys; sys.path.insert(0, '/hl')");
  const host = py.pyimport("humanlang.gamehost");
  begin(host);
  document.getElementById("again").onclick = () => { document.getElementById("again").hidden = true; begin(host); };
}
function begin(host) {
  if (game) game.stop();
  const r = JSON.parse(host.start(CODE));
  if (r.error) return bad(r.error);
  document.title = r.info.title;
  fit(r.info); addEventListener("resize", () => fit(r.info));
  note.className = ""; note.textContent = "Click the game, then use the keys. " + (r.info.title || "");
  game = Arcade(canvas, r.info, async (input) => {
    const f = JSON.parse(host.frame(JSON.stringify(input)));
    if (f.error) throw new Error(f.error);
    return f;
  }, {
    muted,
    onError: bad,
    onOver: () => { note.textContent = "Game over."; document.getElementById("again").hidden = false; },
  });
  canvas.focus(); game.start();
}
document.getElementById("mute").onclick = (e) => {
  muted = !muted; e.target.textContent = "Sound: " + (muted ? "off" : "on"); if (game) game.setMuted(muted);
};
boot().catch((e) => bad("The game couldn't start. Are you online? (" + e + ")"));
</script></body></html>
"""


def package_files():
    out = {}
    for p in glob.glob(os.path.join(source_dir(), "*.py")):
        with open(p, encoding="utf-8") as f:
            out[os.path.basename(p)] = f.read()
    return out


def arcade_js():
    with open(os.path.join(source_dir(), "arcade.js"), encoding="utf-8") as f:
        return f.read()


def safe(text):  # inside a <script>: nothing may close it early
    return text.replace("</", "<\\/").replace("<!--", "<\\!--")


def game_to_html(code, title="HumanLang game"):
    parts = {"__TITLE__": html.escape(title), "__PYODIDE__": PYODIDE, "__ARCADE__": safe(arcade_js()),
             "__FILES__": safe(json.dumps(package_files())), "__CODE__": safe(json.dumps(code))}
    return re.sub("__[A-Z]+__", lambda m: parts.get(m.group(0), m.group(0)), TEMPLATE)

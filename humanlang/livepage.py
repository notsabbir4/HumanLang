"""A live page (buttons that run code) as ONE web page: hl build FILE.hum

The page carries the program's code and HumanLang itself. It loads Pyodide (Python for the browser) the first time
it opens, so it needs a connection, unless it was built with --offline, which packs Pyodide into the page.
"""
import json
import re

from .gamepage import package_files, pyload, safe
from .render import to_html

BOOT = """
<div id="hl-live-note" style="position:fixed;left:0;right:0;bottom:0;padding:.5em 1em;font:14px system-ui,sans-serif;background:#1b2036;color:#e8eaf2;white-space:pre-wrap">Starting the page...</div>
<script>
(function(){
var FILES = __FILES__, CODE = __CODE__, MEMKEY = "hl-memory:" + location.pathname + document.title;
var note = document.getElementById("hl-live-note");
function say(t, bad){ note.style.display = t ? "block" : "none"; note.textContent = t; note.style.background = bad ? "#5a1a1a" : "#1b2036"; }
function store(){ try { return localStorage.getItem(MEMKEY) || ""; } catch (e) { return ""; } }
function keep(host){ var m = host.take_memory(); if (m) { try { localStorage.setItem(MEMKEY, m); } catch (e) {} } }
(async function(){
  var py = await loadPyodide({ indexURL: "__PYODIDE__" });
  py.FS.mkdirTree("/hl/humanlang");
  for (var n in FILES) py.FS.writeFile("/hl/humanlang/" + n, FILES[n]);
  py.runPython("import sys; sys.path.insert(0, '/hl')");
  var host = py.pyimport("humanlang.livehost");
  var r = JSON.parse(host.start(CODE, undefined, store()));
  if (r.error) { say(r.error, true); return; }
  var d = new DOMParser().parseFromString(r.page, "text/html");
  window.hlUpdate(d.querySelector("main.hl-page").innerHTML);
  window.hlSend = function(m){
    var e = JSON.parse(host.event(JSON.stringify(m)));
    if (e.error) { say(e.error, true); return; }
    say(""); window.hlUpdate(e.html); keep(host);
  };
  keep(host); say("");
})().catch(function(e){ say("The page couldn't start. Are you online? (" + e + ")", true); });
})();
</script>
"""


def live_to_html(page, keys, code, offline=False, say=None):
    """page: the page the program showed; keys: what its "when" lines listen to (Interpreter.live_keys())."""
    load, where = pyload(offline, say)
    parts = {"__FILES__": safe(json.dumps(package_files())), "__CODE__": safe(json.dumps(code)), "__PYODIDE__": where}
    boot = re.sub("__[A-Z]+__", lambda m: parts.get(m.group(0), m.group(0)), BOOT)  # one pass: the files may contain these words
    html = to_html(page, keys)
    return html.replace("</body>", load + boot + "</body>", 1)

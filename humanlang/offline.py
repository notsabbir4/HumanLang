"""Pages that work without internet: Pyodide (Python for the browser) packed INTO the page.

A normal built page loads Pyodide from the internet when it opens. `hl build --offline` packs it inside the one
HTML file instead (about 18 MB), so the page opens anywhere: from a USB stick, with no connection at all.
The files are downloaded once (needs internet that one time) and kept in a cache folder.
"""
import base64
import os
import urllib.request

VERSION = "0.26.4"
CDN = f"https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/"
FILES = ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")
TYPES = {"pyodide.asm.wasm": "application/wasm", "python_stdlib.zip": "application/zip", "pyodide-lock.json": "application/json"}


class OfflineError(Exception):
    pass


def cache_dir():
    base = os.environ.get("HL_PYODIDE_DIR")
    if base:
        return base
    root = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(root, "humanlang", "pyodide-" + VERSION)


def ensure_files(say=None):
    """Make sure every Pyodide file is in the cache folder (downloading what is missing); returns the folder."""
    d = cache_dir()
    os.makedirs(d, exist_ok=True)
    for name in FILES:
        path = os.path.join(d, name)
        if os.path.isfile(path) and os.path.getsize(path) > 0:
            continue
        if say:
            say(f"Downloading {name} (one time only)...")
        try:
            with urllib.request.urlopen(CDN + name, timeout=60) as r, open(path + ".part", "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(path + ".part", path)
        except OSError as e:
            raise OfflineError(f"I couldn't download {name}. An offline page needs internet one time, to get Python for the browser "
                               f"({e}).\nTry again when you are online.")
    return d


def read_text(d, name):
    with open(os.path.join(d, name), encoding="utf-8") as f:
        return f.read()


def safe(text):
    return text.replace("</", "<\\/").replace("<!--", "<\\!--")


def inline_head(say=None):
    """The <script> tags that put Pyodide inside the page, and the folder-less index URL to use with it."""
    d = ensure_files(say)
    blobs = {}
    for name, kind in TYPES.items():
        with open(os.path.join(d, name), "rb") as f:
            blobs[name] = (kind, base64.b64encode(f.read()).decode())
    patch = ["const HL_BLOBS = {"]
    for name, (kind, data) in blobs.items():
        patch.append(f'{name!r}: [{kind!r}, "{data}"],')
    patch.append("};")
    patch.append("""const hlFetch = window.fetch.bind(window);
window.fetch = (url, opts) => {
  const name = String(url && url.url || url).split("?")[0].split("/").pop();
  const b = HL_BLOBS[name];
  if (!b) return hlFetch(url, opts);
  const bin = atob(b[1]), bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return Promise.resolve(new Response(bytes, { status: 200, headers: { "Content-Type": b[0] } }));
};""")
    return ("<script>" + safe(read_text(d, "pyodide.js")) + "</script>\n<script>" + safe(read_text(d, "pyodide.asm.js"))
            + "</script>\n<script>" + "\n".join(patch) + "</script>")

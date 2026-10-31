"""Builds the HumanLang website into website/dist/.

    python website/build.py                      # for publishing (Pyodide from a CDN)
    python website/build.py --pyodide-url pyodide/ --out /tmp/site   # for local testing

Needs:  pip install markdown
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from humanlang import __version__  # noqa: E402

CDN_PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"

# ---- syntax colouring for HL code -----------------------------------------
CONTROL = ["if that fails", "otherwise", "give back", "for each", "if", "repeat", "while", "in", "try",
           "stop", "skip", "define", "then", "else"]
STATEMENT = ["say", "set", "change", "add", "subtract", "remove", "ask", "save it as", "use", "write",
             "with", "to", "from", "by", "file"]
OPERATORS = ["and", "or", "not", "is", "less than", "greater than", "at least", "at most", "contains",
             "plus", "minus", "times", "divided by", "mod", "to the power of"]
BUILTINS = ["list of", "empty list", "item", "how many items in", "length of", "uppercase of", "lowercase of",
            "number of", "text of", "random number from", "random item from", "square root of",
            "absolute value of", "round of", "floor of", "ceiling of", "sum of", "largest of", "smallest of",
            "sorted of", "reversed of", "trim of", "read file", "split", "join", "replace",
            "the date today", "the time now"]
CONSTANTS = ["yes", "no", "nothing", "problem"]


def alternation(words):
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


TOKEN = re.compile(
    r"(?P<c>^[ \t]*note:.*$)"
    r'|(?P<s>"(?:\\.|[^"\\])*")'
    r"|(?P<n>\b\d+(?:\.\d+)?\b)"
    r"|\b(?P<k>" + alternation(CONTROL + STATEMENT) + r")\b"
    r"|\b(?P<o>" + alternation(OPERATORS) + r")\b"
    r"|\b(?P<f>" + alternation(BUILTINS) + r")\b"
    r"|\b(?P<v>" + alternation(CONSTANTS) + r")\b",
    re.M,
)


def highlight(code):
    out, pos = [], 0
    for m in TOKEN.finditer(code):
        out.append(html.escape(code[pos:m.start()]))
        kind = m.lastgroup
        text = html.escape(m.group())
        if kind == "s":
            text = re.sub(r"(\{[^{}]*\})", r'<span class="i">\1</span>', text)
        out.append(f'<span class="{kind}">{text}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:]))
    return "".join(out)


# ---- markdown -> html --------------------------------------------------------
FENCE = re.compile(r"^```([\w-]*)[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)


def box(kind, label, inner, extra="", copy=False):
    button = '<button class="copy" type="button" onclick="copyCode(this)">Copy</button>' if copy else ""
    cls = f"box {kind}{' copyable' if copy else ''}{extra}"
    return f'<div class="{cls}"><span class="tag">{label}</span>{button}<pre><code>{inner}</code></pre></div>'


def render_markdown(text):
    """Returns (html, [(id, title), ...]) for the h2 headings."""
    stash, prev = [], {"kind": None}

    def take(m):
        info, body = m.group(1), m.group(2).rstrip("\n")
        if info.startswith("hum"):
            html_ = box("code", "HumanLang", highlight(body), copy=True)
        elif info == "input":
            html_ = box("input", "You type", html.escape(body))
        elif info == "output":
            was_error = prev["kind"] == "hum-error"
            html_ = box("output", "What HL says" if was_error else "Output", html.escape(body),
                        " error" if was_error else "")
        else:
            html_ = box("code", info or "", html.escape(body), copy=True)
        prev["kind"] = info if info.startswith("hum") or info == "input" else None
        if info == "input":
            prev["kind"] = prev.get("last_hum")
        if info.startswith("hum"):
            prev["last_hum"] = info
        stash.append(html_)
        return f"\n\n@@BOX{len(stash) - 1}@@\n\n"

    text = FENCE.sub(take, text)
    md = markdown.Markdown(extensions=["tables", "toc"], extension_configs={"toc": {"toc_depth": "2"}})
    body = md.convert(text)
    for i, h in enumerate(stash):
        body = body.replace(f"<p>@@BOX{i}@@</p>", h)
    toc = [(t["id"], t["name"]) for t in md.toc_tokens[0].get("children", [])] if md.toc_tokens else []
    # h1 is the page title; h2 are chapters
    toc = [(c["id"], c["name"]) for t in md.toc_tokens for c in ([t] if t["level"] == 2 else t.get("children", []))]
    return body, toc


# ---- page template -----------------------------------------------------------
NAV = [("index.html", "Home"), ("tutorial.html", "Tutorial"), ("reference.html", "Reference"),
       ("playground.html", "Playground"), ("install.html", "Install")]


def page(title, body, active, extra_head="", extra_body=""):
    links = "".join(f'<a href="{h}"{" class=on" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="HumanLang (HL): a beginner-friendly programming language that reads like English.">
<link rel="stylesheet" href="style.css">
{extra_head}
</head>
<body>
<header class="site"><div class="in"><a class="brand" href="index.html">Human<span>Lang</span></a>
<nav class="main">{links}</nav></div></header>
<main>
{body}
</main>
<footer>HumanLang {__version__} &middot; MIT licensed &middot; code that reads like you talk</footer>
<script>
function copyCode(b){{var t=b.parentNode.querySelector('code').innerText;
(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){{b.textContent='Copied';setTimeout(function(){{b.textContent='Copy'}},1500)}},function(){{b.textContent='Select + copy'}})}}
</script>
{extra_body}
</body>
</html>
"""


def doc_page(title, md_text, active):
    body, toc = render_markdown(md_text)
    side = "".join(f'<a href="#{i}">{html.escape(n)}</a>' for i, n in toc)
    layout = f'<div class="doc"><aside class="toc"><b>On this page</b>{side}</aside><article>{body}</article></div>'
    return page(f"{title} - HumanLang", layout, active)


HERO_CODE = '''note: ask, decide, repeat
ask "What is your name?" and save it as name
ask number "How old are you?" and save it as age

if age is at least 18
    say "Welcome, {name}!"
otherwise
    say "Hi {name}, come back in {18 - age} years."'''


def index_page():
    body = f"""
<section class="hero">
<div>
<h1>Code that reads like you talk.</h1>
<p class="lead">HumanLang is a programming language for people who have never programmed.
Write instructions in plain English sentences. Get error messages that actually help.</p>
<div class="btns"><a class="btn" href="playground.html">Try it in your browser</a>
<a class="btn ghost" href="tutorial.html">Start the tutorial</a></div>
</div>
<div>{box("code", "HumanLang", highlight(HERO_CODE), copy=True)}
{box("output", "Output", html.escape("What is your name? Sam" + chr(10) + "How old are you? 15" + chr(10) + "Hi Sam, come back in 3 years."))}</div>
</section>
<section class="cards">
<div class="card"><h3>Reads like English</h3><p>No braces, no semicolons, no type declarations.
<code>set age to 20</code>, <code>if age is at least 18</code>, <code>repeat 3 times</code>.</p></div>
<div class="card"><h3>Errors that help</h3><p>Every message says what went wrong, where, and how to fix it,
with a &ldquo;Did you mean&hellip;?&rdquo; for typos.</p></div>
<div class="card"><h3>Never guesses</h3><p>Text and numbers are never silently mixed, and every phrase has exactly
one meaning, so you can trust what you read.</p></div>
</section>
<h2>See the difference an error can make</h2>
{box("code", "HumanLang", highlight('set name to "Sam"' + chr(10) + 'say "Hello {nmae}"'))}
{box("output", "What HL says", html.escape('Line 2: I don' + chr(39) + 't know "nmae".' + chr(10) + '    say "Hello {nmae}"' + chr(10) + 'Did you mean "name"?'), " error")}
<h2>Made for learning</h2>
<ul>
<li>A one-hour <a href="tutorial.html">tutorial</a> where every example is tested to really run.</li>
<li>A <a href="playground.html">playground</a> that works in your browser, nothing to install.</li>
<li>A <a href="reference.html">reference</a> with every word HL knows.</li>
<li>An <a href="install.html">installer</a> for Windows, macOS and Linux, plus editor support for VS Code.</li>
</ul>
"""
    return page("HumanLang - code that reads like you talk", body, "index.html")


def playground_page(examples):
    body = """
<h1>Playground</h1>
<p>Write HumanLang and run it right here. Nothing is sent anywhere: it all runs in your browser.</p>
<div class="bar"><div><label for="examples" style="font-weight:700;font-size:.85rem;color:var(--muted)">Examples</label>
<select id="examples" style="min-width:12em;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--fg)"></select></div>
<button class="btn" id="run" type="button" disabled>Run</button>
<button class="btn ghost" id="stop" type="button" disabled>Stop</button>
<button class="btn ghost" id="share" type="button">Share link</button>
<span id="status">Loading...</span></div>
<div class="pg">
<div><label for="code">Your program</label><textarea id="code" spellcheck="false" autocapitalize="off" autocomplete="off"></textarea>
<label for="inputs" style="margin-top:10px">Answers for <code>ask</code> (one per line)</label><textarea id="inputs" spellcheck="false"></textarea></div>
<div><label for="out">Output</label><pre id="out" aria-live="polite"></pre></div>
</div>
<p style="color:var(--muted);font-size:.92rem">Tip: when a program uses <code>ask</code>, a small box pops up for each answer. To skip the pop-ups, type the answers in the Answers box instead, one line each, in order.
Press Stop if a program never finishes.</p>
"""
    script = f'<script>window.HL_EXAMPLES = {json.dumps(examples)};</script>\n<script src="playground.js"></script>'
    return page("Playground - HumanLang", body, "playground.html", extra_body=script)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pyodide-url", default=CDN_PYODIDE)
    ap.add_argument("--out", default=os.path.join(HERE, "dist"))
    args = ap.parse_args()
    out = args.out
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)

    for f in glob.glob(os.path.join(HERE, "static", "*")):
        if os.path.isfile(f):
            shutil.copy(f, out)
    write(os.path.join(out, "config.js"),
          f"self.HL_CONFIG = {json.dumps({'pyodideUrl': args.pyodide_url, 'version': __version__})};\n")

    # the interpreter itself, for the in-browser playground
    src = {os.path.basename(p): read(p) for p in glob.glob(os.path.join(ROOT, "humanlang", "*.py"))}
    write(os.path.join(out, "humanlang_src.json"), json.dumps(src))

    answers = {"greet.hum": "Sam\n20", "guess.hum": "5\n3\n8\n1\n2\n4\n6\n7\n9\n10"}
    examples = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "examples", "*.hum"))):
        name = os.path.basename(p)
        examples[name] = {"code": read(p), "inputs": answers.get(name, "")}

    write(os.path.join(out, "index.html"), index_page())
    write(os.path.join(out, "tutorial.html"), doc_page("Tutorial", read(os.path.join(ROOT, "docs", "tutorial.md")), "tutorial.html"))
    write(os.path.join(out, "reference.html"), doc_page("Reference", read(os.path.join(ROOT, "docs", "reference.md")), "reference.html"))
    write(os.path.join(out, "install.html"), doc_page("Install", read(os.path.join(HERE, "install_page.md")), "install.html"))
    write(os.path.join(out, "playground.html"), playground_page(examples))
    write(os.path.join(out, ".nojekyll"), "")
    print(f"Built {len(os.listdir(out))} files in {out}")


if __name__ == "__main__":
    main()

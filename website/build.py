"""Builds the HumanLang website into website/dist/.

    python website/build.py                      # for publishing (Pyodide from a CDN)
    python website/build.py --pyodide-url pyodide/ --out /tmp/site   # for local testing

Needs:  pip install markdown
"""
import argparse
import datetime
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
import courses  # noqa: E402
from humanlang import __version__  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402
from humanlang.render import to_html  # noqa: E402

CDN_PYODIDE = "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"

# ---- syntax colouring for HL code -----------------------------------------
CONTROL = ["if that fails", "otherwise", "give back", "for each", "if", "repeat", "while", "in", "try",
           "stop", "skip", "define", "then", "else", "stop the program", "fail with", "forever"]
STATEMENT = ["say", "set", "change", "add", "subtract", "remove", "ask", "save it as", "use", "write",
             "with", "to", "from", "by", "file", "write csv", "places", "place", "decimals", "as rows"]
OPERATORS = ["and", "or", "not", "is", "less than", "greater than", "at least", "at most", "contains", "has field",
             "plus", "minus", "times", "divided evenly by", "divided by", "mod", "to the power of"]
BUILTINS = ["list of", "empty list", "empty record", "record with", "field", "keys of", "by field", "file exists",
            "first", "last", "letters", "find", "item", "how many items in", "length of", "uppercase of", "lowercase of",
            "number of", "text of", "random number from", "random item from", "square root of",
            "absolute value of", "round of", "floor of", "ceiling of", "sum of", "largest of", "smallest of",
            "sorted of", "reversed of", "trim of", "read csv", "read file", "split", "join", "replace",
            "the date today", "the time now"]
DESIGN_KINDS = ["box", "row", "text", "heading", "button", "input", "drawing", "circle", "oval", "rectangle",
                "square", "triangle", "line", "polygon", "pixel art"]
DESIGN = ["show a page", "titled", "called", "where", "make a sprite", "make a map", "play a game", "when the game starts",
          "every frame", "when the key", "is pressed", "when the mouse is clicked", "draw the sprite", "draw the map",
          "move the camera to", "play the sound", "play the video", "play video", "stop the game", "change the tile", "touches", "facing left",
          "is down", "frame number", "game time"] + ['remember', 'forget', 'recall', 'calculate', 'when the button', 'is clicked', 'when the input', 'changes', 'the text in', 'the number in', 'play the music', 'stop the music', 'draw the picture', 'make a body', 'make the body', 'update the body', 'move the body', 'run left', 'run right', 'bounce', 'is on the ground'] + [
    f"put {'an' if k[0] in 'aeiou' else 'a'} {k}" for k in DESIGN_KINDS] + ["put some"]
CONSTANTS = ["yes", "no", "nothing", "problem_line", "problem_kind", "problem"]


def alternation(words):
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


TOKEN = re.compile(
    r"(?P<c>^[ \t]*note:.*$)"
    r'|(?P<s>"(?:\\.|[^"\\])*")'
    r"|(?P<n>\b\d+(?:\.\d+)?\b)"
    r"|\b(?P<k>" + alternation(CONTROL + STATEMENT + DESIGN) + r")\b"
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


def page_preview(code):
    """What a design example looks like: the real page, in a frame that can't run scripts."""
    interp = Interpreter(out=lambda _t: None, inp=lambda _p: "")
    interp.run(code)  # a mistake in a docs example stops the build (the docs tests catch it first)
    doc = to_html(interp.designs[-1])
    return (f'<div class="box result"><span class="tag">What it looks like</span>'
            f'<iframe sandbox="" loading="lazy" title="Result of the example above" srcdoc="{html.escape(doc, quote=True)}"></iframe></div>')


def render_markdown(text):
    """Returns (html, [(id, title), ...]) for the h2 headings."""
    stash, prev = [], {"kind": None}

    def take(m):
        info, body = m.group(1), m.group(2).rstrip("\n")
        if info == "hum-page":
            html_ = box("code", "HumanLang", highlight(body), copy=True) + page_preview(body)
        elif info.startswith("hum"):
            html_ = box("code", "HumanLang", highlight(body), copy=True)
        elif info == "terminal":
            html_ = box("code", "Type this in the terminal", html.escape(body), copy=True)
        elif info == "config":
            html_ = box("code", "Copy this", html.escape(body), copy=True)
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
       ("playground.html", "Playground"), ("sprites.html", "Sprites"), ("games.html", "Games"), ("community.html", "Community"), ("editors.html", "Editors"),
       ("install.html", "Download")]
REPO = "https://github.com/notsabbir4/HumanLang"
# The website's accounts, saved programs and shared coding live on a Supabase project. These two values are PUBLIC by design
# (the publishable key can only do what the database's row rules allow); the secret keys never appear here.
SUPABASE = {"url": "https://xfzfebklugcppbgxtahz.supabase.co", "key": "sb_publishable_fcriRm2B0njFO5Q3qEceeQ_nVn54xCb"}
SITE = "https://notsabbir4.github.io/HumanLang/"
LATEST = REPO + "/releases/latest/download/"


def page(title, body, active, extra_head="", extra_body="", main_class=""):
    links = "".join(f'<a href="{h}"{" class=on" if h == active else ""}>{t}</a>' for h, t in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="HumanLang (HL): a beginner-friendly programming language that reads like English.">
<link rel="icon" type="image/png" sizes="32x32" href="icon-32.png">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="icon-180.png">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="HumanLang (HL): code that reads like you talk.">
<meta property="og:image" content="social-preview.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="style.css">
<script>window.HL_SUPABASE = {json.dumps(SUPABASE)};</script>
{extra_head}
</head>
<body>
<header class="site"><div class="in"><a class="brand" href="index.html" aria-label="HumanLang home"><img src="logo.png" alt="HumanLang" width="181" height="46"></a>
<nav class="main" id="mainnav">{links}</nav><a class="acct" id="acct" href="account.html">Sign in</a>
<button class="menubtn" id="menubtn" type="button" aria-label="Pages menu" aria-expanded="false" aria-controls="mainnav"><span></span><span></span><span></span></button></div></header>
<main{(" class=" + main_class) if main_class else ""}>
{body}
</main>
<footer><div class="fl"><a href="install.html">Download</a><a href="editors.html">Editors</a><a href="changelog.html">What&rsquo;s new</a>
<a href="{REPO}">GitHub</a><a href="{REPO}/issues">Report a problem</a></div>
HumanLang {__version__} &middot; free to use &middot; <a href="https://github.com/notsabbir4/HumanLang/blob/main/LICENSE">licence</a> &middot; code that reads like you talk</footer>
<script src="account.js"></script>
<script>
(function(){{var b=document.getElementById('menubtn'),h=b.closest('header');
function set(o){{h.classList.toggle('open',o);b.setAttribute('aria-expanded',o?'true':'false')}}
b.onclick=function(e){{e.stopPropagation();set(!h.classList.contains('open'))}};
document.addEventListener('click',function(e){{if(!h.contains(e.target))set(false)}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape')set(false)}})}})();
</script>
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


def download_panel():
    """The big download area (like python.org). Works without JavaScript; download.js picks the visitor's system."""
    def card(key, name, sub, href, label):
        return (f'<div class="dl-card" data-os="{key}"><h3>{name}</h3><p>{sub}</p>'
                f'<a class="btn" href="{href}" data-asset="{label}">Download</a></div>')
    cards = (
        card("windows", "Windows", "Windows 10 or 11 &middot; installer", LATEST + "HumanLang-Setup.exe", "HumanLang-Setup.exe")
        + card("mac", "Mac", "Apple chip (M1 or newer) &middot; one program", LATEST + "hl-macos", "hl-macos")
        + card("linux", "Linux", "64-bit Intel/AMD &middot; one program", LATEST + "hl-linux", "hl-linux")
    )
    return f"""
<section class="dl">
<div class="dl-main">
<p class="dl-ver"><span id="dl-version">Latest version</span> &middot; free &middot; no Python needed</p>
<h1 id="dl-title">Download HumanLang</h1>
<p class="lead" id="dl-sub">Pick your computer below. The step-by-step guide is right underneath.</p>
<div class="btns"><a class="btn big" id="dl-main-btn" href="{LATEST}HumanLang-Setup.exe">Download for Windows</a>
<a class="btn ghost" href="#steps">Show me how</a></div>
<p class="dl-note" id="dl-note">Windows may say &ldquo;Windows protected your PC&rdquo;. That is normal: click <b>More info</b>, then <b>Run anyway</b>.</p>
</div>
<div class="dl-grid">{cards}
<div class="dl-card" data-os="editor"><h3>VS Code</h3><p>Colours, live errors and a Run button</p>
<a class="btn ghost" href="{LATEST}HumanLang-VSCode.vsix">Download extension</a></div></div>
<p class="dl-small">Not sure which? <a href="playground.html">Try HumanLang in your browser first</a>. &middot;
<a href="changelog.html">What&rsquo;s new</a> &middot; <a href="{REPO}/releases">All versions</a></p>
</section>
<script src="download.js"></script>
"""


def download_page():
    body, toc = render_markdown(read(os.path.join(HERE, "install_page.md")))
    body = body.replace("<h1", "<h1 hidden", 1)  # the big heading above takes its place
    body = body.replace("<h2 id=\"step-by-step-windows\"", "<h2 id=\"steps\"", 1)
    side = "".join(f'<a href="#{i}">{html.escape(n)}</a>' for i, n in toc)
    layout = (download_panel()
              + f'<div class="doc"><aside class="toc"><b>On this page</b>{side}</aside><article>{body}</article></div>')
    return page("Download HumanLang", layout, "install.html")



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
<div class="btns"><a class="btn big" href="install.html">Download HumanLang</a>
<a class="btn ghost" href="playground.html">Try it in your browser</a>
<a class="btn ghost" href="tutorial.html">Start the tutorial</a></div>
<p class="dl-small">Version {__version__} &middot; free &middot; Windows, Mac and Linux</p>
<div id="home-course" class="homecourse" data-total="10" hidden></div>
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
<li>Short <a href="tutorial.html">courses</a> (Beginner+, Designer Go, Game Maker, Master 2.0): pick what you want to make. Every example is tested to really run.</li>
<li>A <a href="playground.html">playground</a> that works in your browser, nothing to install.</li>
<li>A <a href="reference.html">reference</a> with every word HL knows.</li>
<li>A one-click <a href="install.html">installer</a> for Windows, and one-line installs for Mac and Linux.</li>
<li><b>Design:</b> make pages, buttons, drawings and pixel art in plain words, with a live preview. See the <a href="course-designer-go.html">Designer Go course</a>.</li>
<li><a href="editors.html">Editor support</a>: colours, live error messages and a Run button in VS Code, and setup guides for other editors.</li>
<li>A <a href="changelog.html">changelog</a> that says what is new in every version.</li>
</ul>
"""
    return page("HumanLang - code that reads like you talk", body, "index.html", extra_body='<script src="learn-core.js"></script><script src="home-course.js"></script>')


def playground_page(examples):
    body = """
<div class="ide">
<div class="ide-top">
<div class="tb-left">
<label class="tb-pick"><span>Examples</span><select id="examples" aria-label="Example programs"></select></label>
<div class="tb-group run-group">
<button class="tb run" id="run" type="button" title="Run your program (Ctrl+Enter)" disabled><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 4l13 8-13 8z" fill="currentColor" stroke="none"/></svg><span class="t">Run</span></button>
<button class="tb" id="stop" type="button" title="Stop the program" disabled><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="1.5" fill="currentColor" stroke="none"/></svg><span class="t">Stop</span></button>
<button class="tb" id="stepbtn" type="button" title="Go through the program one line at a time and see what each line does" disabled><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4v16M10 5l10 7-10 7z"/></svg><span class="t">Step through</span></button>
</div>
</div>
<div class="tb-right">
<div class="tb-group" role="group" aria-label="File">
<button class="tb" id="upbtn" type="button" title="Open a .hum file from your computer in the editor"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 16V4M7 9l5-5 5 5M4 20h16"/></svg><span class="t">Upload</span></button>
<button class="tb" id="dlbtn" type="button" title="Download your program as a .hum file"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v12M7 11l5 5 5-5M4 20h16"/></svg><span class="t">Download</span></button>
<button class="tb" id="savebtn" type="button" title="Save your program to your account (sign in with GitHub)"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 4h11l3 3v13H5zM8 4v5h7V4M8 20v-6h8v6"/></svg><span class="t">Save</span></button>
<input type="file" id="upfile" accept=".hum,.txt,text/plain" hidden>
</div>
<div class="tb-group" role="group" aria-label="Share">
<button class="tb" id="share" type="button" title="Copy a link to your program"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg><span class="t">Share link</span></button>
<button class="tb" id="collabbtn" type="button" title="Code on the same program with other people, live"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M17 5a3 3 0 0 1 0 6M21 20c0-2.6-1.6-4.8-4-5.6"/></svg><span class="t">Collaborate</span></button>
<button class="tb" id="postbtn" type="button" title="Open the Community post form with your program already filled in"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v11H9l-5 4z"/></svg><span class="t">Post to Community</span></button>
</div>
<button class="tb solo" id="theme" type="button" aria-label="Switch between light and dark"><svg class="ic" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M5 19l2-2M17 7l2-2"/></svg><span class="t">Light</span></button>
</div>
</div>
<div class="ide-main">
<section class="ide-edit" aria-label="Your program">
<div class="ide-tabs"><span class="tab on" id="filetab">main.hum</span><span class="drophint">Tip: drop a .hum file here to open it</span><span id="collab-bar" hidden aria-live="polite"></span></div>
<div class="ide-code">
<pre class="gutter" id="gutter" aria-hidden="true">1</pre>
<div class="ed"><pre class="hl" id="hl" aria-hidden="true"></pre>
<div class="remote" id="remote" aria-hidden="true"></div>
<textarea id="code" spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off" aria-label="HumanLang program"></textarea></div>
</div>
</section>
<section class="ide-side" aria-label="Results">
<div class="ide-tabs" role="tablist">
<button class="tab on" id="tab-console" role="tab" type="button">Console</button>
<button class="tab" id="tab-preview" role="tab" type="button" hidden>Preview</button>
<button class="tab" id="tab-input" role="tab" type="button">Answers</button>
<button class="tab" id="tab-steps" role="tab" type="button" hidden>Steps</button>
<button class="tab" id="tab-files" role="tab" type="button">Files</button>
<span class="grow"></span><span id="took"></span>
</div>
<pre id="out" aria-live="polite"></pre>
<div id="prepane" hidden><div id="pnote" hidden></div><iframe id="preview" sandbox="allow-scripts" title="Preview of your page"></iframe><div id="gamebox" hidden><canvas id="screen" tabindex="0" aria-label="The game. Click it, then use the keyboard."></canvas></div></div>
<div id="stepspane" hidden>
<div class="stepbar"><button class="btn ghost" id="stepback" type="button">&#9664; Back</button><button class="btn run" id="stepnext" type="button">Next &#9654;</button>
<input type="range" id="steprange" min="0" max="0" value="0" aria-label="Step"><span id="stepcount"></span></div>
<p id="stepsays"></p>
<div class="stepgrid"><pre id="stepcode" aria-label="Your program, with the current line marked"></pre>
<div><h4>What the variables hold</h4><table id="stepvars"></table><h4>Output so far</h4><pre id="stepout"></pre></div></div>
</div>
<div id="filespane" hidden><p>Add your own <b>pictures</b> (png, jpg, gif, webp), <b>sounds or music</b> (wav, mp3, ogg, m4a) and <b>videos</b> (mp4, webm) to use in a game.
They stay in this browser only. Use them by name, for example <code>draw the picture "face.png" at 10, 10</code>,
<code>play the music "theme.mp3"</code> or <code>play the video "intro.mp4"</code>. Up to 3 MB each.</p>
<label class="btn ghost" id="addfiles-label">Add files<input type="file" id="addfiles" multiple accept="image/png,image/jpeg,image/gif,image/webp,audio/*,video/mp4,video/webm,.wav,.mp3,.ogg,.m4a,.mp4,.webm" hidden></label>
<ul id="filelist" aria-live="polite"></ul><p id="filenote"></p></div>
<div id="inpane" hidden><p>Optional. If your program uses <code>ask</code>, type all its answers here, one per line, and it will not stop to ask.</p>
<textarea id="inputs" spellcheck="false" aria-label="Answers, one per line"></textarea></div>
</section>
</div>
<aside id="collab" class="drawer" hidden aria-label="Collaborate"></aside>
<div class="ide-status"><span id="status">Loading...</span><span class="grow"></span><span id="pos">Ln 1, Col 1</span><span>Spaces: 4</span><span>HumanLang</span></div>
</div>
"""
    words = {"k": CONTROL + STATEMENT + DESIGN, "o": OPERATORS, "f": BUILTINS, "v": CONSTANTS}
    script = (f'<script>window.HL_REPO = {json.dumps(REPO)}; window.HL_EXAMPLES = {json.dumps(examples)}; window.HL_WORDS = {json.dumps(words)};</script>\n'
              '<script src="arcade.js"></script><script src="community-lib.js"></script><script src="playground.js"></script>'
              '<script src="collab-core.js"></script><script src="collab.js"></script><script src="save.js"></script>')
    return page("Playground - HumanLang", body, "playground.html", extra_body=script, main_class="ide-page")


def account_page():
    body = """<section class="doc account">
<h1>Your account</h1>
<div id="acct-out" hidden>
<p>Sign in with your GitHub account to <b>code together</b> with other people on the same program,
save your programs, and have your own <b>profile</b>. We only get your public GitHub name and photo. We never see your GitHub password, and we cannot
change anything on your GitHub.</p>
<button class="btn run" id="signin" type="button">Sign in with GitHub</button>
<p class="muted" id="acct-note"></p>
</div>
<div id="acct-in" hidden>
<div class="profile-card" id="pcard"></div>
<form id="pform" class="pform">
<label>Display name <input id="p-name" maxlength="40" required></label>
<label>About you <textarea id="p-bio" maxlength="280" rows="3" placeholder="What do you make with HumanLang?"></textarea></label>
<label>Favourite thing in HumanLang <input id="p-fav" maxlength="60" placeholder="e.g. games, pages, calculate"></label>
<fieldset><legend>Your colour (your cursor and name show in it when you code with others)</legend><div id="p-colours" class="swatches"></div></fieldset>
<fieldset><legend>Your badge</legend><div id="p-badges" class="swatches"></div></fieldset>
<label class="check"><input type="checkbox" id="p-photo"> Show my GitHub photo</label>
<div class="row"><button class="btn run" type="submit">Save profile</button><span id="p-status" role="status"></span></div>
</form>
<h2>Your courses</h2>
<div id="courses" class="coursebox"><p class="muted">Loading...</p></div>
<h2>Your saved programs</h2>
<p class="muted">Save from the Playground with the <b>Save</b> button. Only you can see these.</p>
<ul id="saved" class="rooms"><li class="muted">Loading...</li></ul>
<h2>Your shared programs</h2>
<ul id="rooms" class="rooms"><li class="muted">Loading...</li></ul>
<p><button class="btn ghost" id="signout" type="button">Sign out</button></p>
</div>
</section>"""
    return page("Account - HumanLang", body, "account.html", extra_body='<script src="learn-core.js"></script><script src="account-page.js"></script>')


def inspect_html(code, how, game_id):
    """The Inspect panel: the explanation steps on the left, the code with line numbers on the right.
    Each step lights up its own lines of code."""
    lines = code.split("\n")
    starts = []
    for step in how:
        found = next((i for i, l in enumerate(lines) if l.strip().startswith(step["at"])), None)
        if found is None:
            raise SystemExit(f'{game_id}: the Inspect step "{step["title"]}" starts at "{step["at"]}", which is not in the game')
        starts.append(found)
    if starts != sorted(set(starts)):
        raise SystemExit(f"{game_id}: the Inspect steps must be in the order they appear in the code")
    ends = starts[1:] + [len(lines)]
    steps = "".join(
        f'<li><button type="button" class="step" data-from="{a + 1}" data-to="{b}">'
        f'<strong>{html.escape(st["title"])}</strong>'
        f'<span>{re.sub(r"`([^`]+)`", lambda m: "<code>" + m.group(1) + "</code>", html.escape(st["text"]))}</span></button></li>'
        for st, a, b in zip(how, starts, ends))
    code_html = "".join(f'<li id="L{i + 1}">{highlight(l) or " "}</li>' for i, l in enumerate(lines))
    return (f'<div class="inspect-grid"><div><h3>How it works</h3><p class="hint">Press a step to see its lines in the code.</p>'
            f'<ol class="steps">{steps}</ol></div>'
            f'<div><h3>The code</h3><ol class="listing" id="listing">{code_html}</ol></div></div>')


def community_snapshot():
    """The published community posts as of this build (the page also asks GitHub live, this is the fallback)."""
    import urllib.request
    posts = []
    try:
        for page_no in range(1, 6):
            req = urllib.request.Request(
                f"https://api.github.com/repos/notsabbir4/HumanLang/issues?labels=community,verified-hl&state=open&per_page=100&page={page_no}",
                headers={"Accept": "application/vnd.github+json"})
            if os.environ.get("GITHUB_TOKEN"):
                req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
            with urllib.request.urlopen(req, timeout=20) as r:
                batch = json.load(r)
            for i in batch:
                if "pull_request" in i:
                    continue
                posts.append({k: i.get(k) for k in ("number", "title", "body", "created_at", "updated_at", "html_url", "comments")}
                             | {"user": {"login": i["user"]["login"], "avatar_url": i["user"]["avatar_url"]},
                                "labels": [{"name": l["name"]} for l in i.get("labels", [])]})
            if len(batch) < 100:
                break
    except Exception as e:  # no internet while building: the page still works, it asks GitHub when opened
        print(f"(community snapshot skipped: {e})", file=sys.stderr)
    return posts


def sprites_page():
    """The Visual Sprite Editor: draw a sprite with the mouse, get the HumanLang sprite code."""
    tool = lambda key, title, tip: f'<button class="sp-tool" type="button" data-tool="{key}" title="{tip}" aria-label="{title}"><i data-icon="{key}"></i><span>{title}</span></button>'
    body = f"""
<div class="sp-app" id="sp">
<div class="sp-top">
 <div class="sp-brand"><span class="sp-badge">HL</span> Sprite Editor</div>
 <label class="sp-name">Name <input id="sp-name" type="text" maxlength="40" spellcheck="false" autocomplete="off" aria-label="Sprite name" title="The name your game uses: draw the sprite NAME at ..."></label>
 <div class="sp-group">
  <button class="sp-btn" id="b-new" type="button" title="Start a new sprite"><i data-icon="new"></i>New</button>
  <button class="sp-btn" id="b-open" type="button" title="Open a sprite you saved"><i data-icon="open"></i>Open</button>
  <button class="sp-btn" id="b-save" type="button" title="Save in this browser (Ctrl+S)"><i data-icon="save"></i>Save</button>
 </div>
 <div class="sp-group">
  <button class="sp-btn icon" id="b-undo" type="button" title="Undo (Ctrl+Z)" aria-label="Undo"><i data-icon="undo"></i></button>
  <button class="sp-btn icon" id="b-redo" type="button" title="Redo (Ctrl+Y)" aria-label="Redo"><i data-icon="redo"></i></button>
 </div>
 <div class="sp-group">
  <button class="sp-btn" id="b-preview" type="button" title="See it move, as it will look in a game"><i data-icon="play"></i>Preview</button>
  <button class="sp-btn" id="b-import" type="button" title="Turn a sprite you wrote in HumanLang into a picture you can edit"><i data-icon="import"></i>Import code</button>
 </div>
 <span class="sp-grow"></span>
 <button class="sp-btn icon" id="b-help" type="button" title="Help: the quick tour and the keys" aria-label="Help"><i data-icon="help"></i></button>
 <button class="sp-btn primary" id="b-export" type="button" title="Get the HumanLang code for this sprite"><i data-icon="code"></i>Export to HumanLang</button>
</div>
<div class="sp-main">
 <div class="sp-tools" id="sp-tools" role="toolbar" aria-label="Drawing tools">
  {tool("pencil", "Draw", "Draw (P): click or drag to colour pixels")}
  {tool("eraser", "Erase", "Erase (E): make pixels see-through again")}
  {tool("bucket", "Fill", "Fill (F): colour a whole connected area")}
  {tool("picker", "Pick", "Pick a colour (I): click a pixel to use its colour")}
  {tool("line", "Line", "Line (L): drag from one point to another")}
  {tool("rect", "Box", "Rectangle (R): drag a box")}
  {tool("oval", "Circle", "Circle or oval (C): drag the box it fits in")}
  {tool("hand", "Move", "Move the picture around (H). You can also hold Space, or use the middle mouse button")}
 </div>
 <div class="sp-stage">
  <div class="sp-opts" id="sp-opts">
   <span id="o-shape" hidden><span class="sp-lbl">Shape</span>
    <button class="sp-seg on" id="o-outline" type="button">Outline</button><button class="sp-seg" id="o-filled" type="button">Filled</button></span>
   <label class="sp-chk"><input type="checkbox" id="o-onion"> Show the frame before (faint)</label>
   <label class="sp-chk"><input type="checkbox" id="o-grid" checked> Grid</label>
   <span class="sp-grow"></span>
   <button class="sp-btn icon" id="z-out" type="button" title="Zoom out (-)" aria-label="Zoom out"><i data-icon="minus"></i></button>
   <span class="sp-zoom" id="z-val" title="Zoom">1&times;</span>
   <button class="sp-btn icon" id="z-in" type="button" title="Zoom in (+)" aria-label="Zoom in"><i data-icon="plus"></i></button>
   <button class="sp-btn" id="z-fit" type="button" title="Fit the picture in the window (0)">Fit</button>
  </div>
  <div class="sp-wrap" id="sp-wrap"><canvas id="sp-canvas" aria-label="Drawing area" tabindex="0"></canvas><div class="sp-toast" id="sp-toast" role="status" aria-live="polite"></div></div>
  <div class="sp-status"><span id="sp-info"></span><span id="s-pos">&nbsp;</span><span class="sp-grow"></span><span id="s-tip"></span></div>
 </div>
 <aside class="sp-side">
  <section class="sp-panel" id="p-colour"><h3>Colour</h3>
   <div class="sp-cur"><button class="sp-big" id="c-swatch" type="button" title="Pick any colour" aria-label="Current colour"></button>
    <input type="color" id="c-input" aria-label="Pick a colour" value="#e43a4c">
    <input type="text" id="c-hex" maxlength="24" spellcheck="false" autocomplete="off" aria-label="Colour code or name" title="Type a code like #ff8800 or a colour name like sky blue"></div>
   <h4>Recent</h4><div class="sp-sw" id="c-recent"></div>
   <h4>My palette <button class="sp-mini" id="c-add" type="button" title="Add the current colour to the palette">+ Add</button></h4>
   <div class="sp-sw" id="c-pal"></div>
   <p class="sp-hint">Click a colour to use it. Right-click (or long-press) a palette colour to remove it.</p>
  </section>
  <section class="sp-panel" id="p-props"><h3>Sprite</h3>
   <div class="sp-row"><label>Width <input type="number" id="p-w" min="1" max="256" step="1"></label><label>Height <input type="number" id="p-h" min="1" max="256" step="1"></label>
    <button class="sp-mini" id="p-resize" type="button" title="Change the size of the picture (it keeps the top-left)">Resize</button></div>
    <div class="sp-chips" id="p-chips"></div>
   <div class="sp-row"><label>Pixel size <input type="number" id="p-ps" min="1" max="64" step="1" title="How big each pixel is in the game"></label></div>
   <p class="sp-hint" id="p-note"></p>
  </section>
 </aside>
</div>
<div class="sp-time">
 <div class="sp-tl-head"><b>Frames</b>
  <button class="sp-btn small" id="f-add" type="button" title="Add an empty frame after this one"><i data-icon="plus"></i>Add</button>
  <button class="sp-btn small" id="f-dup" type="button" title="Copy this frame"><i data-icon="copy"></i>Copy</button>
  <button class="sp-btn small" id="f-del" type="button" title="Delete this frame"><i data-icon="trash"></i>Delete</button>
  <button class="sp-btn small icon" id="f-left" type="button" title="Move this frame earlier" aria-label="Move frame earlier"><i data-icon="left"></i></button>
  <button class="sp-btn small icon" id="f-right" type="button" title="Move this frame later" aria-label="Move frame later"><i data-icon="right"></i></button>
  <span class="sp-grow"></span>
  <button class="sp-btn small primary" id="f-play" type="button" title="Play the animation (Enter)"><i data-icon="play"></i><span>Play</span></button>
  <label class="sp-speed">Speed <input type="range" id="f-speed" min="1" max="24" value="6" aria-label="Animation speed"><span id="f-fps">6/s</span></label>
 </div>
 <div class="sp-tl-body"><div class="sp-frames" id="sp-frames" role="listbox" aria-label="Frames"></div>
  <div class="sp-mini-prev" title="The animation"><canvas id="sp-mini"></canvas></div></div>
</div>

<dialog class="sp-dlg" id="d-new"><form method="dialog" id="f-new"><h2>New sprite</h2>
 <label class="sp-field">Name <input id="n-name" type="text" maxlength="40" value="player" spellcheck="false" autocomplete="off"></label>
 <div class="sp-field"><span>Size (pixels)</span><div class="sp-chips" id="n-chips"></div>
  <div class="sp-row"><label>Width <input type="number" id="n-w" min="1" max="256" value="16"></label><label>Height <input type="number" id="n-h" min="1" max="256" value="16"></label>
  <label>Pixel size <input type="number" id="n-ps" min="1" max="64" value="4"></label></div></div>
 <p class="sp-hint">A 16 &times; 16 sprite with pixel size 4 is drawn 64 &times; 64 on the game screen.</p>
 <div class="sp-actions"><button class="sp-btn" value="cancel" type="button" data-close>Cancel</button><button class="sp-btn primary" id="n-go" type="submit">Start drawing</button></div></form></dialog>

<dialog class="sp-dlg wide" id="d-open"><div><h2>Open a sprite</h2>
 <p class="sp-hint">These are saved in this browser. <label class="sp-btn small" for="o-file">Open a file&hellip;</label><input type="file" id="o-file" accept=".json,.hum,.txt,text/plain,application/json" hidden>
  A file can be a sprite saved from here (.json) or a HumanLang program (.hum).</p>
 <div class="sp-lib" id="o-list"></div><p class="sp-hint" id="o-none" hidden>Nothing saved yet. Press Save to keep a sprite here.</p>
 <h3 class="sp-h3">In your account</h3>
 <p class="sp-hint" id="o-acc-msg">Sign in to keep your sprites in your account, on any device.</p>
 <div class="sp-actions" id="o-acc-in" hidden><button class="sp-btn small primary" type="button" id="o-signin">Sign in with GitHub</button></div>
 <div class="sp-lib" id="o-cloud"></div>
 <div class="sp-actions"><button class="sp-btn" type="button" data-close>Close</button></div></div></dialog>

<dialog class="sp-dlg" id="d-saveas"><form method="dialog" id="f-saveas"><h2>Save as</h2>
 <label class="sp-field">Name <input id="sa-name" type="text" maxlength="40" spellcheck="false" autocomplete="off"></label>
 <div class="sp-actions"><button class="sp-btn" type="button" data-close>Cancel</button><button class="sp-btn primary" type="submit">Save</button></div></form></dialog>

<dialog class="sp-dlg wide" id="d-export"><div><h2>HumanLang code</h2>
 <div class="sp-seg" role="group" aria-label="What to copy"><button type="button" class="on" id="e-m-run" aria-pressed="true">Ready to run</button><button type="button" id="e-m-sprite" aria-pressed="false">Just the sprite</button></div>
 <p class="sp-hint" id="e-hint-run">A complete program: paste it into the Playground and press Run, and your sprite appears (it animates if it has more than one frame).</p>
 <p class="sp-hint" id="e-hint-sprite" hidden>Only the sprite. Copy this into your own program, above the game. Then draw it with <code id="e-use"></code></p>
 <div class="sp-warn" id="e-warn" hidden></div>
 <pre class="sp-code" id="e-code" tabindex="0"></pre>
 <div class="sp-actions"><button class="sp-btn" type="button" id="e-reduce" hidden>Fewer colours&hellip;</button><span class="sp-grow"></span>
  <button class="sp-btn" type="button" id="e-play"><i data-icon="play"></i>Try it in the Playground</button>
  <button class="sp-btn" type="button" id="e-dl"><i data-icon="save"></i>Download .hum</button>
  <button class="sp-btn primary" type="button" id="e-copy"><i data-icon="copy"></i>Copy code</button>
  <button class="sp-btn" type="button" data-close>Close</button></div></div></dialog>

<dialog class="sp-dlg wide" id="d-import"><div><h2>Import a sprite</h2>
 <p class="sp-hint">Paste a sprite you wrote in HumanLang (it starts with <code>make a sprite called</code>) and it becomes a picture you can edit.
  <label class="sp-btn small" for="i-file">Open a .hum file&hellip;</label><input type="file" id="i-file" accept=".hum,.txt,text/plain" hidden></p>
 <textarea id="i-text" spellcheck="false" rows="12" aria-label="Sprite code" placeholder='make a sprite called heart with pixel size 4&#10;    where "r" is red&#10;    ".rr.rr."&#10;    ...'></textarea>
 <div class="sp-warn" id="i-err" hidden></div><div class="sp-pick" id="i-pick" hidden></div>
 <div class="sp-actions"><button class="sp-btn" type="button" data-close>Cancel</button><button class="sp-btn primary" type="button" id="i-go">Import</button></div></div></dialog>

<dialog class="sp-dlg" id="d-reduce"><form method="dialog" id="f-reduce"><h2>Fewer colours</h2>
 <p class="sp-hint">HumanLang gives every colour one letter. This joins the colours that look most alike until only the number you choose is left.
  You can undo it.</p>
 <label class="sp-field">Keep at most <input type="number" id="r-n" min="1" max="200" value="40"></label>
 <div class="sp-actions"><button class="sp-btn" type="button" data-close>Cancel</button><button class="sp-btn primary" type="submit">Join colours</button></div></form></dialog>

<dialog class="sp-dlg wide" id="d-preview"><div><h2>Preview</h2>
 <p class="sp-hint">This is how the sprite looks in a game (each pixel is the size you chose).</p>
 <div class="sp-pv-bg" id="pv-bg"><canvas id="pv-canvas"></canvas></div>
 <div class="sp-row"><span class="sp-lbl">Background</span>
  <button class="sp-seg on" data-bg="dark" type="button">Dark</button><button class="sp-seg" data-bg="light" type="button">Light</button><button class="sp-seg" data-bg="sky" type="button">Sky</button><button class="sp-seg" data-bg="check" type="button">Checker</button>
  <label class="sp-speed">Speed <input type="range" id="pv-speed" min="1" max="24" value="6" aria-label="Preview speed"></label></div>
 <div class="sp-actions"><button class="sp-btn primary" type="button" data-close>Close</button></div></div></dialog>

<div class="sp-coach" id="sp-coach" hidden role="dialog" aria-label="Quick tour"><div class="sp-coach-n" id="co-n"></div><h4 id="co-t"></h4><p id="co-p"></p>
 <div class="sp-actions"><button class="sp-btn small" type="button" id="co-skip">Skip tour</button><span class="sp-grow"></span>
  <button class="sp-btn small" type="button" id="co-back">Back</button><button class="sp-btn small primary" type="button" id="co-next">Next</button></div></div>

<dialog class="sp-dlg wide" id="d-help"><div><h2>Help</h2>
 <p>Draw with the mouse (or your finger). When you are happy, press <b>Export to HumanLang</b> and copy the code into your program.</p>
 <div class="sp-keys"><div><b>P</b> Draw</div><div><b>E</b> Erase</div><div><b>F</b> Fill</div><div><b>I</b> Pick a colour</div><div><b>L</b> Line</div><div><b>R</b> Box</div><div><b>C</b> Circle</div><div><b>H</b> Move</div>
 <div><b>Space</b> + drag: move</div><div><b>Scroll</b> zoom</div><div><b>+ / -</b> zoom</div><div><b>0</b> fit</div><div><b>Ctrl+Z</b> undo</div><div><b>Ctrl+Y</b> redo</div><div><b>Ctrl+S</b> save</div><div><b>, / .</b> frame before / after</div><div><b>Enter</b> play</div></div>
 <p class="sp-hint">You can still write sprites by hand in HumanLang. This editor makes the same code, and <b>Import code</b> turns hand-written sprites into pictures.</p>
 <div class="sp-actions"><button class="sp-btn" type="button" id="h-tour">Show the quick tour</button><span class="sp-grow"></span><button class="sp-btn primary" type="button" data-close>Close</button></div></div></dialog>
</div>
"""
    from humanlang.design import CSS, EXTRA_COLOURS
    from humanlang.parser import RESERVED
    data = {"colours": {**CSS, **EXTRA_COLOURS}, "reserved": sorted(RESERVED)}
    head = '<link rel="stylesheet" href="sprites.css">'
    script = f'<script>window.HL_SPRITE_DATA = {json.dumps(data)};</script><script src="sprites-core.js"></script><script src="sprites.js"></script>'
    return page("Sprite Editor - HumanLang", body, "sprites.html", extra_head=head, extra_body=script, main_class="sp-page")


def community_page():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import community_check
    rules, _ = render_markdown(read(os.path.join(ROOT, "community", "RULES.md")))
    data = {
        "official": community_check.load_json("official.json", {}).get("accounts", []),
        "banned": [b["login"] for b in community_check.load_json("banned.json", {}).get("banned", [])],
        "categories": community_check.CATEGORIES,
        "keywords": sorted({w for w in re.findall(r"[a-z]+(?: [a-z]+)*", " ".join(DESIGN + CONTROL + STATEMENT + OPERATORS).lower())}),
        "snapshot": community_snapshot(),
    }
    new_post = f"{REPO}/issues/new?template=community-post.yml"
    rules_list = re.sub(r"</?(ol)>", "", rules)
    body = f"""
<div class="community">
<section id="browse">
<h1>Community</h1>
<p class="lead">Things people made with HumanLang: games, stories, pages, tools and more. Every post is 100% HumanLang
and has its own <strong>Post ID</strong>. Run any post in the Playground, read its code, and learn from it.</p>
<div class="comm-top">
<a class="btn run" href="{new_post}" rel="noopener">Post your work</a>
<a class="btn ghost" href="#rules">Read the rules</a>
<form id="find" class="find"><label for="findid">Find a post by ID</label>
<input id="findid" inputmode="numeric" placeholder="#42" autocomplete="off"><button class="btn ghost" type="submit">Go</button></form>
</div>
<div class="comm-filter"><input id="q" type="search" placeholder="Search posts" aria-label="Search posts"><span id="count" class="count"></span></div>
<div id="chips" class="chips"></div>
<p id="note" class="status"></p>
<div id="posts" class="posts"></div>
<section id="rules" class="rules"><h2>Rules</h2>
<p>To post you need a free GitHub account. Press <strong>Post your work</strong>, fill in the form and submit. You get your Post ID right away,
and a bot checks the program (it only reads it, it never runs it). If it is 100% HumanLang it shows up here within a few minutes.
If something needs fixing the bot tells you what, and checks again when you edit your post.</p>
<ol>{rules_list}</ol>
</section>
</section>
<section id="detail" hidden></section>
</div>"""
    data_js = json.dumps(data).replace("</", "<\\/")
    script = (f'<script>window.HL_COMMUNITY = {data_js};</script>\n'
              '<script src="community-lib.js"></script>\n<script src="community.js"></script>')
    return page("Community - HumanLang", body, "community.html", extra_body=script)


def games_page(games):
    body = """
<div class="games">
<section id="lobby">
<h1>Games</h1>
<p class="lead">Games written in HumanLang. Pick one and play it right here, nothing to install.
Want to see how one works? Press <strong>Inspect</strong> on any game to read its code, with every part explained. Every game is a plain <code>.hum</code> file in the
<a href="https://github.com/notsabbir4/HumanLang/tree/main/games">games folder</a>.</p>
<div id="grid"></div>
</section>
<section id="stage" hidden>
<div class="stage-top">
<button class="btn ghost" id="back" type="button">&larr; All games</button>
<span class="grow"></span>
<button class="btn ghost" id="inspect-btn" type="button" aria-expanded="false" aria-controls="inspect">Inspect</button>
<button class="btn run" id="restart" type="button">Restart</button>
</div>
<img class="banner" id="gbanner" alt="" hidden>
<h1 id="gtitle"></h1>
<p class="gtags" id="gtags"></p>
<div class="screen-tools">
<label for="speed">Typing speed</label>
<select id="speed"><option value="slow">Slow</option><option value="normal" selected>Normal</option>
<option value="fast">Fast</option><option value="instant">Instant</option></select>
<button class="btn ghost" id="skip" type="button" hidden>Skip ahead</button>
</div>
<div id="arcade-box" hidden>
<div class="arcade-frame"><canvas id="arcade-screen" tabindex="0" aria-label="The game. Click it, then use the keyboard."></canvas></div>
<p class="keys" id="arcade-keys"></p>
</div>
<pre id="screen" aria-live="polite"></pre>
<p id="gstatus" class="gstatus"></p>
<section id="inspect" class="inspect" hidden aria-label="Inspect: how this game was made">
<h2>Inspect</h2>
<p class="lead">This is the real program, written in HumanLang. Nothing is hidden: the game you just played is exactly this code.
<a id="inspect-edit" href="playground.html" hidden>Open it in the Playground and change it.</a></p>
<div id="inspect-body"></div>
</section>
</section>
</div>
"""
    script = (f'<script>window.HL_GAMES = {json.dumps(games)};</script>\n<script src="arcade.js"></script>\n<script src="games.js"></script>')
    return page("Games - HumanLang", body, "games.html", extra_body=script)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def stamp_assets(out):
    """style.css?v=abc123: a changed script or style gets a new address, so browsers never show an old copy of it."""
    import hashlib
    def stamp(m):
        path = os.path.join(out, m.group(2))
        if not os.path.isfile(path):
            return m.group(0)
        with open(path, "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()[:8]
        return f'{m.group(1)}{m.group(2)}?v={digest}"'
    for name in os.listdir(out):
        if name.endswith(".html"):
            p = os.path.join(out, name)
            text = read(p)
            write(p, re.sub(r'((?:src|href)=")([\w.-]+\.(?:js|css))"', stamp, text))


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
    if os.path.isdir(os.path.join(HERE, "static", "mascot")):
        shutil.copytree(os.path.join(HERE, "static", "mascot"), os.path.join(out, "mascot"))
    shutil.copy(os.path.join(ROOT, "humanlang", "arcade.js"), out)
    for name in ("logo.png", "certificate-template.jpg", "certificate-signature.png", "icon-32.png", "icon-180.png", "social-preview.png"):
        shutil.copy(os.path.join(ROOT, "assets", name), out)
    shutil.copy(os.path.join(ROOT, "assets", "icon.ico"), os.path.join(out, "favicon.ico"))
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
    games = []
    with open(os.path.join(ROOT, "games", "index.json"), encoding="utf-8") as f:
        for g in json.load(f):
            entry = {k: v for k, v in g.items() if k not in ("test_runs", "image", "files")}
            if g.get("files"):
                # the game's own pictures, sounds and videos: served as files next to the pages, named in "files" in games/index.json
                from humanlang.assets import kind_of
                os.makedirs(os.path.join(out, "game-files"), exist_ok=True)
                entry["files"] = {}
                for fname in g["files"]:
                    shutil.copy(os.path.join(ROOT, "games", "files", fname), os.path.join(out, "game-files", fname))
                    entry["files"][fname] = {"kind": kind_of(fname), "url": "game-files/" + fname, "size": os.path.getsize(os.path.join(ROOT, "games", "files", fname))}
            entry["code"] = read(os.path.join(ROOT, "games", g["file"]))
            if g.get("how"):
                entry["inspect"] = inspect_html(entry["code"], g["how"], g["id"])
            entry.pop("how", None)
            if g.get("kind") == "arcade":
                examples[g["file"]] = {"code": entry["code"], "inputs": ""}
                if entry.get("files"):
                    examples[g["file"]]["files"] = entry["files"]
            if g.get("image"):
                entry["image"] = "game-" + g["id"] + os.path.splitext(g["image"])[1]
                shutil.copy(os.path.join(ROOT, "games", g["image"]), os.path.join(out, entry["image"]))
            games.append(entry)

    write(os.path.join(out, "index.html"), index_page())
    tutorial_md = read(os.path.join(ROOT, "docs", "tutorial.md"))
    courses.build(out, tutorial_md, render_markdown, page, write, highlight)       # tutorial.html (pick a course), course-*.html, lesson-*.html
    write(os.path.join(out, "tutorial-all.html"), doc_page("Tutorial: all chapters", tutorial_md, "tutorial.html"))
    write(os.path.join(out, "reference.html"), doc_page("Reference", read(os.path.join(ROOT, "docs", "reference.md")), "reference.html"))
    write(os.path.join(out, "install.html"), download_page())
    write(os.path.join(out, "editors.html"), doc_page("Editors", read(os.path.join(HERE, "editors_page.md")), "editors.html"))
    write(os.path.join(out, "changelog.html"), doc_page("What's new", read(os.path.join(ROOT, "CHANGELOG.md")), "changelog.html"))
    write(os.path.join(out, "playground.html"), playground_page(examples))
    write(os.path.join(out, "games.html"), games_page(games))
    write(os.path.join(out, "sprites.html"), sprites_page())
    write(os.path.join(out, "community.html"), community_page())
    write(os.path.join(out, "account.html"), account_page())
    write(os.path.join(out, ".nojekyll"), "")
    stamp_assets(out)
    print(f"Built {len(os.listdir(out))} files in {out}")


if __name__ == "__main__":
    main()

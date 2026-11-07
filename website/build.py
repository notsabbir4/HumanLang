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
          "move the camera to", "play the sound", "stop the game", "change the tile", "touches", "facing left",
          "is down", "frame number", "game time"] + [
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
       ("playground.html", "Playground"), ("games.html", "Games"), ("community.html", "Community"), ("editors.html", "Editors"),
       ("install.html", "Download")]
REPO = "https://github.com/notsabbir4/HumanLang"
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
{extra_head}
</head>
<body>
<header class="site"><div class="in"><a class="brand" href="index.html" aria-label="HumanLang home"><img src="logo.png" alt="HumanLang" width="181" height="46"></a>
<nav class="main">{links}</nav></div></header>
<main{(" class=" + main_class) if main_class else ""}>
{body}
</main>
<footer><div class="fl"><a href="install.html">Download</a><a href="editors.html">Editors</a><a href="changelog.html">What&rsquo;s new</a>
<a href="{REPO}">GitHub</a><a href="{REPO}/issues">Report a problem</a></div>
HumanLang {__version__} &middot; MIT licensed &middot; code that reads like you talk</footer>
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
<li>A one-click <a href="install.html">installer</a> for Windows, and one-line installs for Mac and Linux.</li>
<li><b>Design:</b> make pages, buttons, drawings and pixel art in plain words, with a live preview. See the <a href="tutorial.html#13-design-pages-buttons-and-drawings">tutorial chapter</a>.</li>
<li><a href="editors.html">Editor support</a>: colours, live error messages and a Run button in VS Code, and setup guides for other editors.</li>
<li>A <a href="changelog.html">changelog</a> that says what is new in every version.</li>
</ul>
"""
    return page("HumanLang - code that reads like you talk", body, "index.html")


def playground_page(examples):
    body = """
<div class="ide">
<div class="ide-top">
<select id="examples" aria-label="Example programs"></select>
<button class="btn run" id="run" type="button" disabled>&#9654; Run</button>
<button class="btn ghost" id="stop" type="button" disabled>Stop</button>
<span class="grow"></span>
<button class="btn ghost" id="share" type="button">Share link</button>
<button class="btn ghost" id="theme" type="button" aria-label="Switch between light and dark">Light</button>
</div>
<div class="ide-main">
<section class="ide-edit" aria-label="Your program">
<div class="ide-tabs"><span class="tab on">main.hum</span></div>
<div class="ide-code">
<pre class="gutter" id="gutter" aria-hidden="true">1</pre>
<div class="ed"><pre class="hl" id="hl" aria-hidden="true"></pre>
<textarea id="code" spellcheck="false" autocapitalize="off" autocomplete="off" wrap="off" aria-label="HumanLang program"></textarea></div>
</div>
</section>
<section class="ide-side" aria-label="Results">
<div class="ide-tabs" role="tablist">
<button class="tab on" id="tab-console" role="tab" type="button">Console</button>
<button class="tab" id="tab-preview" role="tab" type="button" hidden>Preview</button>
<button class="tab" id="tab-input" role="tab" type="button">Answers</button>
<span class="grow"></span><span id="took"></span>
</div>
<pre id="out" aria-live="polite"></pre>
<div id="prepane" hidden><div id="pnote" hidden></div><iframe id="preview" sandbox="" title="Preview of your page"></iframe><div id="gamebox" hidden><canvas id="screen" tabindex="0" aria-label="The game. Click it, then use the keyboard."></canvas></div></div>
<div id="inpane" hidden><p>Optional. If your program uses <code>ask</code>, type all its answers here, one per line, and it will not stop to ask.</p>
<textarea id="inputs" spellcheck="false" aria-label="Answers, one per line"></textarea></div>
</section>
</div>
<div class="ide-status"><span id="status">Loading...</span><span class="grow"></span><span id="pos">Ln 1, Col 1</span><span>Spaces: 4</span><span>HumanLang</span></div>
</div>
"""
    words = {"k": CONTROL + STATEMENT + DESIGN, "o": OPERATORS, "f": BUILTINS, "v": CONSTANTS}
    script = (f'<script>window.HL_EXAMPLES = {json.dumps(examples)}; window.HL_WORDS = {json.dumps(words)};</script>\n'
              '<script src="arcade.js"></script><script src="community-lib.js"></script><script src="playground.js"></script>')
    return page("Playground - HumanLang", body, "playground.html", extra_body=script, main_class="ide-page")


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
<div class="game-grid" id="grid"></div>
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
    shutil.copy(os.path.join(ROOT, "humanlang", "arcade.js"), out)
    for name in ("logo.png", "icon-32.png", "icon-180.png", "social-preview.png"):
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
            entry = {k: v for k, v in g.items() if k not in ("test_runs", "image")}
            entry["code"] = read(os.path.join(ROOT, "games", g["file"]))
            if g.get("how"):
                entry["inspect"] = inspect_html(entry["code"], g["how"], g["id"])
            entry.pop("how", None)
            if g.get("kind") == "arcade":
                examples[g["file"]] = {"code": entry["code"], "inputs": ""}
            if g.get("image"):
                entry["image"] = "game-" + g["id"] + os.path.splitext(g["image"])[1]
                shutil.copy(os.path.join(ROOT, "games", g["image"]), os.path.join(out, entry["image"]))
            games.append(entry)

    write(os.path.join(out, "index.html"), index_page())
    write(os.path.join(out, "tutorial.html"), doc_page("Tutorial", read(os.path.join(ROOT, "docs", "tutorial.md")), "tutorial.html"))
    write(os.path.join(out, "reference.html"), doc_page("Reference", read(os.path.join(ROOT, "docs", "reference.md")), "reference.html"))
    write(os.path.join(out, "install.html"), download_page())
    write(os.path.join(out, "editors.html"), doc_page("Editors", read(os.path.join(HERE, "editors_page.md")), "editors.html"))
    write(os.path.join(out, "changelog.html"), doc_page("What's new", read(os.path.join(ROOT, "CHANGELOG.md")), "changelog.html"))
    write(os.path.join(out, "playground.html"), playground_page(examples))
    write(os.path.join(out, "games.html"), games_page(games))
    write(os.path.join(out, "community.html"), community_page())
    write(os.path.join(out, ".nojekyll"), "")
    print(f"Built {len(os.listdir(out))} files in {out}")


if __name__ == "__main__":
    main()

"""The tutorial as short courses.

docs/tutorial.md stays the one place where every chapter lives (and the docs tests run every example in it).
Here each COURSE picks the chapters it needs, in order. A course page lists its lessons, and every lesson is its own page
with Back and Next, so nobody has to face 19 chapters at once.
"""
import html
import re

COURSES = [
    {
        "id": "beginner-plus", "name": "Beginner+", "emoji": "1",
        "tagline": "Never coded before? Start here.",
        "for": "Anyone. No experience needed.",
        "time": "about 60 minutes, like a game",
        "interactive": True, "units": 10,
        "learn": ["Make the computer talk, ask questions and remember answers",
                  "Make decisions with if, and repeat things with loops",
                  "Keep lists, write your own steps (functions), build a small program and fix its mistakes",
                  "Finish with an exam, a grade (A+ to F) and a certificate"],
        "lessons": [1, 2, 3, 4, 5, 6, 7, 8, 12, 18],
        "next": ["designer-go", "game-maker", "master-2"],
    },
    {
        "id": "designer-go", "name": "Designer Go", "emoji": "2",
        "tagline": "Make pages, buttons and pixel art in plain words.",
        "for": "People who want to make things that look good.",
        "time": "about 60 minutes",
        "learn": ["Build web pages with headings, pictures, buttons and text boxes",
                  "Draw shapes and pixel-art sprites",
                  "Make pages that react when someone clicks or types"],
        "lessons": [1, 2, 3, 5, 6, 7, 8, 13, 16],
        "next": ["game-maker", "master-2"],
    },
    {
        "id": "game-maker", "name": "Game Maker", "emoji": "3",
        "tagline": "Sprites, keys and a game loop: make your own 2D game.",
        "for": "People who want to make games.",
        "time": "about 70 minutes",
        "learn": ["Draw sprites and maps, and move things with the keys",
                  "Use physics for platformers, your own pictures, sounds and music",
                  "Make a game that works on phones too"],
        "lessons": [1, 2, 3, 5, 6, 7, 8, 13, 14, 17, 18],
        "next": ["designer-go", "master-2"],
    },
    {
        "id": "master-2", "name": "Master 2.0", "emoji": "4",
        "tagline": "You know the basics. Go deep.",
        "for": "People who finished Beginner+, or already know variables, if, loops and lists.",
        "time": "about 50 minutes",
        "learn": ["Write your own functions and split a program into files",
                  "Handle mistakes without crashing, and read spreadsheets",
                  "Calculate formulas, remember things between runs, and step through a program"],
        "lessons": [8, 9, 10, 11, 15, 18],
        "next": ["game-maker", "designer-go"],
    },
]

BLURB = {
    1: "Make HumanLang say things.",
    2: "Keep a value with a name, like a box with a label.",
    3: "Words, numbers and how to put them together.",
    4: "Ask the person a question and use the answer.",
    5: "Do one thing or another with if.",
    6: "Do something again and again without copying it.",
    7: "Keep many values together and walk through them.",
    8: "Give a set of steps a name and use it anywhere.",
    9: "What the messages mean, and how to carry on when something fails.",
    10: "Extra tools that come with HL: maths, dates, random and more.",
    11: "Read a spreadsheet, and split a program into files.",
    12: "A small whole program, made from everything so far.",
    13: "Pages, buttons, drawings and pixel art.",
    14: "Sprites, maps, keys and a game loop.",
    15: "Work out formulas from text, and remember things between runs.",
    16: "Buttons and text boxes that really do something.",
    17: "Physics, your own pictures and sounds, and touch controls.",
    18: "Watch a program run one line at a time.",
}


def split(md_text):
    """(intro, {number: (title, body)}) from the tutorial markdown."""
    parts = re.split(r"(?m)^(?=## \d+\. )", md_text)
    chapters = {}
    for p in parts[1:]:
        m = re.match(r"## (\d+)\. ([^\n]*)\n", p)
        chapters[int(m.group(1))] = (m.group(2).strip(), p[m.end():].strip("\n") + "\n")
    return parts[0], chapters


def by_id():
    return {c["id"]: c for c in COURSES}


def lesson_file(course, k):
    return f"lesson-{course['id']}-{k}.html"


def course_file(course):
    return f"course-{course['id']}.html"


def _e(s):
    return html.escape(s)


def picker(chapters_count):
    cards = ""
    for c in COURSES:
        cards += (f'<a class="course" href="{course_file(c)}" data-course="{c["id"]}" data-total="{c.get("units", len(c["lessons"]))}">'
                  f'<span class="cnum">{c["emoji"]}</span><h3>{_e(c["name"])}</h3><p class="ctag">{_e(c["tagline"])}</p>'
                  f'<p class="cmeta">{c["units"] if c.get("interactive") else len(c["lessons"])} {"interactive units" if c.get("interactive") else "lessons"} &middot; {_e(c["time"])}</p>'
                  f'<p class="cfor">{_e(c["for"])}</p>'
                  f'<span class="cprog" data-prog></span><span class="cgo">Start &rarr;</span></a>')
    return f"""<section class="coursehead">
<h1>Choose your course</h1>
<p class="lead">You do not need to learn everything. Pick the course that fits what you want to make.
Each course is a few short lessons, one page each.</p>
<p class="cnote">Not sure? Take <b>Beginner+</b>. You can always take another course later.</p>
</section>
<div class="courses">{cards}</div>
<div class="callout">
<p><b>Already know how to program?</b> The <a href="reference.html">Reference</a> lists every word HL understands, or read
<a href="tutorial-all.html">all {chapters_count} chapters on one page</a>.</p>
</div>
<script src="courses.js"></script>"""


def overview(c, chapters, shared_intro, where_next):
    items = ""
    for k, n in enumerate(c["lessons"], 1):
        items += (f'<li data-lesson="{k}"><a href="{lesson_file(c, k)}"><span class="ln">{k}</span>'
                  f'<span class="lt"><b>{_e(chapters[n][0])}</b><br><small>{_e(BLURB[n])}</small></span>'
                  f'<span class="tick" aria-hidden="true"></span></a></li>')
    learn = "".join(f"<li>{_e(x)}</li>" for x in c["learn"])
    nxt = ""
    for cid in c["next"]:
        o = by_id()[cid]
        nxt += f'<a class="course small" href="{course_file(o)}"><h3>{_e(o["name"])}</h3><p class="ctag">{_e(o["tagline"])}</p></a>'
    return f"""<nav class="crumbs"><a href="tutorial.html">All courses</a> &rsaquo; {_e(c["name"])}</nav>
<section class="coursehead">
<h1>{_e(c["name"])}</h1>
<p class="lead">{_e(c["tagline"])}</p>
<p class="cmeta">{len(c["lessons"])} lessons &middot; {_e(c["time"])} &middot; {_e(c["for"])}</p>
<h2>You will learn to</h2><ul>{learn}</ul>
<p><a class="btn big" id="continue" href="{lesson_file(c, 1)}">Start lesson 1</a></p>
</section>
<ol class="lessons" id="lessons" data-course="{c["id"]}" data-total="{len(c["lessons"])}">{items}</ol>
<div class="done" id="done" hidden>
<h2>You finished {_e(c["name"])}!</h2>
<p>Well done. Share what you made: press <b>Post to Community</b> in the Playground. Then pick your next course:</p>
<div class="courses">{nxt}</div>
</div>
<details class="follow"><summary>How to follow along</summary>{shared_intro}{where_next}</details>
<script src="courses.js"></script>"""


def lesson(c, k, chapters, body_html):
    n = c["lessons"][k - 1]
    total = len(c["lessons"])
    title = chapters[n][0]
    side = ""
    for j, m in enumerate(c["lessons"], 1):
        cls = ' class="on"' if j == k else ""
        side += f'<a{cls} href="{lesson_file(c, j)}" data-lesson="{j}">{j}. {_e(chapters[m][0])}</a>'
    prev = (f'<a class="btn ghost" href="{lesson_file(c, k - 1)}">&larr; Back</a>' if k > 1
            else f'<a class="btn ghost" href="{course_file(c)}">&larr; Course page</a>')
    if k < total:
        nxt_title = chapters[c["lessons"][k]][0]
        nxt = (f'<a class="btn big" id="next" data-done="{k}" href="{lesson_file(c, k + 1)}">'
               f'Next: {_e(nxt_title)} &rarr;</a>')
    else:
        nxt = f'<a class="btn big" id="next" data-done="{k}" href="{course_file(c)}#done">Finish the course &rarr;</a>'
    pct = round(100 * (k - 1) / total)
    layout = f"""<nav class="crumbs"><a href="tutorial.html">All courses</a> &rsaquo; <a href="{course_file(c)}">{_e(c["name"])}</a> &rsaquo; Lesson {k} of {total}</nav>
<div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="{k - 1}"><i style="width:{pct}%"></i></div>
<div class="doc" id="lesson" data-course="{c["id"]}" data-total="{total}" data-k="{k}">
<aside class="toc"><b>{_e(c["name"])}</b>{side}</aside>
<article><p class="lno">Lesson {k} of {total}</p><h1>{_e(title)}</h1>{body_html}
<div class="lessonnav">{prev}{nxt}</div></article></div>
<script src="courses.js"></script>"""
    return title, layout


def app(c, data_json):
    """The interactive course: one page, played by learn.js (the exercises are data, built from website/beginner.py)."""
    learn = "".join(f"<li>{_e(x)}</li>" for x in c["learn"])
    return f"""<nav class="crumbs"><a href="tutorial.html">All courses</a> &rsaquo; {_e(c["name"])}</nav>
<div id="learn" class="learnapp"><noscript><p>This course needs JavaScript. You can read the same lessons as plain pages:
<a href="tutorial-all.html">all chapters</a>.</p></noscript>
<p class="tiny">Loading the course...</p></div>
<script type="application/json" id="learn-data">{data_json}</script>
<script src="learn-core.js"></script><script src="learn.js"></script>
<script src="courses.js"></script>"""


def build(out, md_text, render_markdown, page, write, highlight=None):
    import os
    intro, chapters = split(md_text)
    for c in COURSES:
        for n in c["lessons"]:
            assert n in chapters, (c["id"], n)
    # what is said at the top of the tutorial, without "an hour": it is now the "How to follow along" box
    shared = intro[intro.index("**Two ways"):]
    shared_html, _ = render_markdown(shared)
    where_html, _ = render_markdown("### Where next\n\n" + chapters[19][1].replace("Welcome to programming!", "").strip())
    write(os.path.join(out, "tutorial.html"), page("Tutorial - HumanLang", picker(len(chapters)), "tutorial.html", main_class=""))
    for c in COURSES:
        if c.get("interactive"):
            import beginner
            write(os.path.join(out, course_file(c)), page(f'{c["name"]} course - HumanLang',
                  app(c, beginner.export_json(render_markdown, highlight)), "tutorial.html"))
            continue
        write(os.path.join(out, course_file(c)), page(f'{c["name"]} course - HumanLang', overview(c, chapters, shared_html, where_html), "tutorial.html"))
        for k, n in enumerate(c["lessons"], 1):
            body_html, _ = render_markdown(chapters[n][1])
            title, layout = lesson(c, k, chapters, body_html)
            write(os.path.join(out, lesson_file(c, k)),
                  page(f'{title} - {c["name"]}, lesson {k} - HumanLang', layout, "tutorial.html"))

"""The community bot's checks: is this post 100% HumanLang, and is it someone else's work?

Runs in GitHub Actions when a community post (an issue made with the "Community post" form) is opened or edited.
It NEVER runs the posted program: it only reads it (syntax and safety checks), so a bad post cannot do anything.

    python tools/community_check.py            (in Actions: reads $GITHUB_EVENT_PATH, uses $GITHUB_TOKEN)
    python tools/community_check.py --file post.hum    (try the checks on a file on your own computer)
"""
import difflib
import json
import os
import re
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "notsabbir4/HumanLang")
MAX_CODE = 60000
COPY_LIMIT = 0.88          # how alike two programs are (0 to 1) before a person looks at it
CATEGORIES = ["Games", "Stories", "Design (pages and pictures)", "Tools and utilities", "Learning (lessons and puzzles)",
              "Data and files", "Other"]
ALLOWED_FENCES = {"", "hum", "text", "output", "txt"}
OTHER_LANGUAGE = [
    (r"<\s*script\b", "a <script> tag (JavaScript)"), (r"<\?php", "PHP"), (r"#\s*include\s*<", "C or C++"),
    (r"\bpublic\s+static\s+void\b", "Java"), (r"\bconsole\.log\s*\(", "JavaScript"),
    (r"^\s*def\s+\w+\s*\(.*\)\s*:", "Python"), (r"^\s*import\s+\w+(\s*,\s*\w+)*\s*$", "Python"),
    (r"^\s*from\s+\w+\s+import\b", "Python"), (r"\bfunction\s+\w+\s*\(", "JavaScript"),
    (r"\bSystem\.out\.print", "Java"), (r"\bprintf\s*\(", "C"), (r"<\s*html\b", "HTML"), (r"<\s*style\b", "CSS or HTML"),
    (r"\bSELECT\s+.+\s+FROM\b", "SQL"), (r"\bfn\s+main\s*\(", "Rust"), (r"\bpackage\s+main\b", "Go"),
    (r"=>\s*\{", "JavaScript"), (r"^\s*#!/", "a shell script"),
]
PRIVATE_INFO = [
    (r"[\w.+-]+@[\w-]+\.[\w.-]+", "an email address"), (r"\b(?:\+?\d[\s-]?){10,}\b", "a phone number"),
    (r"(?i)\b(?:password|passwd|api[_ ]?key|secret|token)\s*[:=]\s*\S+", "a password or key"),
]
WRITES = re.compile(r"^\s*(write|append|delete|remove file|save)\b.*\bfile\b|^\s*(write|append) ", re.I | re.M)


def load_json(name, default):
    try:
        with open(os.path.join(ROOT, "community", name), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


# ---- reading the issue form -----------------------------------------------------------------------------
def fields(body):
    """GitHub issue forms write '### Label' then the answer. Returns {label: answer}."""
    out, name, buf = {}, None, []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        m = re.match(r"^###\s+(.*?)\s*$", line)
        if m:
            if name is not None:
                out[name] = "\n".join(buf).strip()
            name, buf = m.group(1), []
        else:
            buf.append(line)
    if name is not None:
        out[name] = "\n".join(buf).strip()
    return out


def code_of(text):
    """The program inside the ```hum fence (or the whole answer if there is no fence)."""
    m = re.search(r"```[ \t]*\w*[ \t]*\n(.*?)\n?```", text or "", re.S)
    return (m.group(1) if m else text or "").strip("\n")


def people(text):
    """GitHub names in 'Made together with': @ada, grace and so on."""
    found = re.findall(r"@?([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))", re.sub(r"_No response_", "", text or ""))
    return [p.lower() for p in found if p.lower() not in ("and", "no", "none", "nobody", "me")]


# ---- the checks -----------------------------------------------------------------------------------------------
def blank_strings(code):
    return re.sub(r'"(?:\\.|[^"\\\n])*"', '""', code)


def check_syntax(code):
    """(ok, message). Reads the program only; never runs it."""
    if not code.strip():
        return False, "There is no code in the post."
    if len(code) > MAX_CODE:
        return False, f"The code is longer than {MAX_CODE} letters. Please post a smaller project (or split it)."
    old = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            interp = Interpreter(out=lambda t: None, inp=lambda p: "")
            interp.set_time_limit(5)
            interp.check(code, "post.hum")
        except HLError as e:
            return False, e.format(code.splitlines())
        except RecursionError:
            return False, "The program is nested too deeply to read."
        finally:
            os.chdir(old)
    return True, ""


def other_languages(texts):
    """Names of other languages that show up in the text (outside of strings for code)."""
    found = []
    for what, text, is_code in texts:
        body = blank_strings(text) if is_code else text
        for pattern, name in OTHER_LANGUAGE:
            if re.search(pattern, body, re.M | re.I if name in ("SQL", "HTML", "CSS or HTML") else re.M):
                found.append(f"{name} in the {what}")
        if not is_code:
            for lang in re.findall(r"^```[ \t]*([\w+#.-]*)", text, re.M):
                if lang.lower() not in ALLOWED_FENCES:
                    found.append(f'a code block marked "{lang}" in the {what}')
    return sorted(set(found))


def private_info(texts):
    found = []
    for what, text in texts:
        for pattern, name in PRIVATE_INFO:
            if re.search(pattern, text):
                found.append(f"{name} in the {what}")
    return sorted(set(found))


def tokens(code):
    """The shape of a program: words stay, names become _, strings and numbers become one marker each, notes vanish."""
    code = re.sub(r"^\s*note:.*$", "", code, flags=re.M)
    out = []
    for t in re.findall(r'"(?:\\.|[^"\\\n])*"|\d+(?:\.\d+)?|[A-Za-z_]\w*|[^\sA-Za-z_\d]', code):
        out.append("S" if t[0] == '"' else "N" if t[0].isdigit() else t)
    return out


def is_copy(a, b):
    """How alike two programs are, 0 to 1. Renaming variables or changing words and numbers does not hide a copy."""
    ta, tb = tokens(a), tokens(b)
    if min(len(ta), len(tb)) < 25:
        return 0.0
    names = set(re.findall(r"[A-Za-z_]\w*", a)) | set(re.findall(r"[A-Za-z_]\w*", b))
    common = {w for w in names if w.lower() in KEYWORDS}
    ta = [t if (t in common or not re.match(r"[A-Za-z_]", t)) else "_" for t in ta]
    tb = [t if (t in common or not re.match(r"[A-Za-z_]", t)) else "_" for t in tb]
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    if sm.real_quick_ratio() < COPY_LIMIT or sm.quick_ratio() < COPY_LIMIT:
        return 0.0
    return sm.ratio()


def _keywords():
    from humanlang import lsp
    words = set()
    for entry in lsp.KEYWORDS:
        words.update(re.findall(r"[a-z_]+", entry.lower()))
    return words


KEYWORDS = _keywords()


def analyse(issue, others, official_code=(), banned=(), officials=()):
    """issue: {number, user, body}. others: [{number, user, code, coauthors}] earlier posts that passed.
    Returns {labels_add, labels_remove, comment, ok}."""
    n, user = issue["number"], issue["user"].lower()
    f = fields(issue.get("body"))
    code = code_of(f.get("Your HumanLang code", ""))
    desc = f.get("What is it? (describe your work)", "")
    category = f.get("Category", "")
    together = people(f.get("Made together with (optional)", ""))
    problems, notes = [], []

    if user in [b.lower() for b in banned]:
        return {"ok": False, "ban": True, "labels_add": ["banned", "removed"], "labels_remove": ["verified-hl"],
                "comment": f"**Post ID: #{n}**\n\nThis account cannot post in the community (see the rules). This post was removed."}

    if "[x]" not in f.get("Rules", "").lower():
        problems.append("You need to tick the box saying you read the rules and agree to them.")
    if category and category not in CATEGORIES:
        problems.append(f'The category "{category}" is not one of the choices.')
    ok, msg = check_syntax(code)
    if not ok:
        problems.append("The program can't be read as HumanLang:\n```text\n" + msg.strip() + "\n```")
    other = other_languages([("code", code, True), ("description", desc, False)])
    if other:
        problems.append("Posts must be 100% HumanLang, but I found " + ", ".join(other) + ".")
    priv = private_info([("code", code), ("description", desc)])
    if priv:
        problems.append("Please remove private details (" + ", ".join(priv) + ").")
    if len(desc) < 10:
        problems.append("Please write at least a sentence about what your work is and how to use it.")

    copy_of = None
    for o in others:
        if o["number"] == n:
            continue
        same_team = o["user"].lower() in together or user in o.get("coauthors", [])
        if same_team or o["user"].lower() == user:
            continue
        if is_copy(code, o["code"]) >= COPY_LIMIT:
            copy_of = o["number"]
            break
    if not copy_of:
        for name, c in official_code:
            if user not in officials and is_copy(code, c) >= COPY_LIMIT:
                copy_of = name
                break

    labels_add, labels_remove = [], []
    if WRITES.search(blank_strings(code)):
        labels_add.append("writes-files")
        notes.append("This program writes to files. People who run it will see a warning on the post.")
    else:
        labels_remove.append("writes-files")

    if copy_of:
        labels_add.append("possible-copy")
        labels_remove.append("verified-hl")
        verdict = (f"A maintainer needs to look at this post: it is very much like {'post #' + str(copy_of) if isinstance(copy_of, int) else copy_of}. "
                   "If you built it together, list that person under **Made together with**. If it is yours, a maintainer will approve it soon. "
                   "Copying someone else's work breaks rule 2.")
        ok = False
    elif problems:
        labels_add.append("needs-fix")
        labels_remove += ["verified-hl", "possible-copy"]
        verdict = "**Not published yet.** Please fix this and save your post (edit it). I check again by myself.\n\n" + "\n\n".join(f"- {p}" for p in problems)
        ok = False
    else:
        labels_add.append("verified-hl")
        labels_remove += ["needs-fix", "possible-copy"]
        verdict = "**Published.** It is 100% HumanLang and now shows on the Community page (it can take a few minutes)."
        ok = True
    comment = f"**Post ID: #{n}**  (this number is yours for good; tell a friend, or search it on the Community page)\n\n{verdict}"
    if notes:
        comment += "\n\n" + "\n".join(f"- {x}" for x in notes)
    comment += "\n\n<sub>Checked by the HumanLang community bot. It reads your program; it never runs it.</sub>"
    return {"ok": ok, "labels_add": labels_add, "labels_remove": labels_remove, "comment": comment}


# ---- talking to GitHub (only used by the Action) ------------------------------------------------------------
def api(path, method="GET", data=None):
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/{path}", method=method,
                                 data=json.dumps(data).encode() if data is not None else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", "Bearer " + os.environ["GITHUB_TOKEN"])
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        if method == "DELETE" and e.code == 404:
            return None
        raise


def earlier_posts():
    posts, page = [], 1
    while page <= 10:
        batch = api(f"issues?labels=verified-hl&state=all&per_page=100&page={page}") or []
        for it in batch:
            f = fields(it.get("body"))
            posts.append({"number": it["number"], "user": it["user"]["login"], "code": code_of(f.get("Your HumanLang code", "")),
                          "coauthors": people(f.get("Made together with (optional)", ""))})
        if len(batch) < 100:
            break
        page += 1
    return posts


def official_programs():
    out = []
    for folder in ("games", "examples"):
        base = os.path.join(ROOT, folder)
        for name in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            if name.endswith(".hum"):
                with open(os.path.join(base, name), encoding="utf-8") as fh:
                    out.append((f"the official example {name}", fh.read()))
    return out


def main(argv):
    if "--file" in argv:
        code = open(argv[argv.index("--file") + 1], encoding="utf-8").read()
        ok, msg = check_syntax(code)
        print("Reads as HumanLang." if ok else msg)
        other = other_languages([("code", code, True)])
        print("Other languages found: " + ", ".join(other) if other else "No other languages found.")
        return 0 if ok and not other else 1
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
        event = json.load(f)
    issue = event["issue"]
    labels = {l["name"] for l in issue.get("labels", [])}
    if "community" not in labels:
        print("Not a community post.")
        return 0
    banned = [b["login"] for b in load_json("banned.json", {}).get("banned", [])]
    officials = [a["login"].lower() for a in load_json("official.json", {}).get("accounts", [])]
    result = analyse({"number": issue["number"], "user": issue["user"]["login"], "body": issue.get("body") or ""},
                     earlier_posts(), official_programs(), banned, officials)
    n = issue["number"]
    for name in result["labels_remove"]:
        if name in labels:
            api(f"issues/{n}/labels/{urllib.request.quote(name)}", "DELETE")
    if result["labels_add"]:
        api(f"issues/{n}/labels", "POST", {"labels": result["labels_add"]})
    # one comment, updated each time, so the post doesn't fill up with bot messages
    mine = None
    for c in api(f"issues/{n}/comments?per_page=100") or []:
        if "Checked by the HumanLang community bot" in c["body"]:
            mine = c
    if mine:
        api(f"issues/comments/{mine['id']}", "PATCH", {"body": result["comment"]})
    else:
        api(f"issues/{n}/comments", "POST", {"body": result["comment"]})
    if result.get("ban"):
        api(f"issues/{n}", "PATCH", {"state": "closed", "state_reason": "not_planned"})
    print(json.dumps({"post": n, "ok": result["ok"], "labels": result["labels_add"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

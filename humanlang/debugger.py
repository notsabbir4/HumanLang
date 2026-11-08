"""A step-by-step debugger for learners: run a program and record, line by line, what happens.

    steps = record(code)       # a list of steps; each says which line, what it does, and what every variable holds

The Playground shows the steps with Back / Next buttons; `hl debug FILE.hum` walks through them in the terminal.
"""
import re

from .errors import HLError
from .interpreter import Function, Interpreter

MAX_STEPS = 3000
MAX_VALUE = 80
MAX_VARS = 40

EXPLAIN = (
    (r"^set (\S+) to (.*)$", "Works out {1} and stores the answer in {0}."),
    (r"^change (\S+) to (.*)$", "Works out {1} and puts the answer in {0}, replacing what it held."),
    (r"^add (.*) to (.*)$", "Adds {0} to {1}."),
    (r"^subtract (.*) from (.*)$", "Takes {0} away from {1}."),
    (r"^say (.*)$", "Shows {0} on the screen."),
    (r"^ask (.*)$", "Asks the person a question and waits for the answer."),
    (r"^if (.*)$", "Checks whether {0} is true. If it is, the indented lines below run."),
    (r"^otherwise if (.*)$", "Only checked when the lines above didn't run: is {0} true?"),
    (r"^otherwise$", "Runs only when the checks above were all false."),
    (r"^repeat (.*)$", "Starts a loop: the lines below run {0}."),
    (r"^for each (\S+) (in|from) (.*)$", "Starts a loop: the lines below run once for every value of {0} ({1} {2})."),
    (r"^while (.*)$", "Keeps running the lines below for as long as {0} is true."),
    (r"^define (\S+)(.*)$", "Teaches the computer a new function called {0}. Nothing runs yet: it runs when something calls it."),
    (r"^give back (.*)$", "Finishes the function and hands back {0}."),
    (r"^try$", "Tries the lines below. If one of them goes wrong, the program carries on with the \"if that fails\" part."),
    (r"^if that fails$", "Runs only because something above went wrong."),
    (r"^remember (.*)$", "Saves {0} so it is still there next time the program runs."),
    (r"^show a page(.*)$", "Builds a web page."),
    (r"^put (.*)$", "Puts {0} on the page (or in the game)."),
    (r"^draw (.*)$", "Draws {0} on the game screen."),
    (r"^stop$", "Leaves the loop."),
    (r"^skip$", "Jumps to the next round of the loop."),
)


def explain(text):
    t = text.strip()
    for pattern, said in EXPLAIN:
        m = re.match(pattern, t)
        if m:
            return said.format(*[g.strip() for g in m.groups()])
    return "Runs this line."


def short(v):
    if isinstance(v, Function):
        return "(a function)"
    try:
        text = repr_value(v)
    except Exception:
        text = "?"
    return text if len(text) <= MAX_VALUE else text[:MAX_VALUE - 1] + "..."


def repr_value(v):
    if v is None:
        return "nothing"
    if v is True:
        return "yes"
    if v is False:
        return "no"
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, list):
        return "list of " + ", ".join(repr_value(x) for x in v[:8]) + (", ..." if len(v) > 8 else "")
    if isinstance(v, dict):
        return "record with " + ", ".join(f"{k} {repr_value(x)}" for k, x in list(v.items())[:6])
    return str(v)


def snapshot(env):
    """{name: text} for the variables the current line can see (inner ones first, functions left out)."""
    out, e, seen = {}, env, set()
    while e is not None:
        for k, v in e.vars.items():
            if k not in seen and not isinstance(v, Function) and len(out) < MAX_VARS:
                out[k] = short(v)
                seen.add(k)
        e = e.parent
    return out


def record(code, max_steps=MAX_STEPS, inputs=()):
    """Run the program, noting every line. Returns {"steps": [...], "output": "...", "error": text or None, "truncated": bool}.
    Each step: {"line", "text", "says", "vars", "out" (how much output exists before this line runs)}."""
    out, steps = [], []
    answers = list(inputs)

    def write(t):
        out.append(t)

    def ask(prompt):
        if not answers:
            raise HLError("The debugger ran out of answers for \"ask\".",
                          hint="Put the answers in the Answers tab, one per line, and step through again.")
        a = answers.pop(0)
        write(prompt + a + "\n")
        return a

    class Stop(BaseException):
        pass

    interp = Interpreter(out=write, inp=ask)

    def step(line, text, env, stmt=None):
        if len(steps) >= max_steps:
            raise Stop()
        steps.append({"line": line, "text": text.strip(), "says": explain(text), "vars": snapshot(env), "out": len("".join(out))})

    interp.on_step = step
    interp.set_time_limit(10)
    err, truncated = None, False
    try:
        interp.run(code)
    except Stop:
        truncated = True
    except HLError as e:
        err = e.format(code.splitlines())
    except RecursionError:
        err = "This program calls itself too deeply."
    return {"steps": steps, "output": "".join(out), "error": err, "truncated": truncated}


def walk(path, source, show=print, read=input):
    """The terminal version: press Enter for the next line, c to run to the end, q to quit, v for every variable."""
    result = record(source)
    steps = result["steps"]
    lines = source.splitlines()
    if not steps and not result["error"]:
        show("There is nothing to step through.")
        return 0
    shown = 0
    last = {}
    for n, st in enumerate(steps, 1):
        changed = {k: v for k, v in st["vars"].items() if last.get(k) != v}
        if shown < st["out"]:
            text = result["output"][shown:st["out"]]
            show("   output:" + "".join("\n     " + ln for ln in text.rstrip("\n").split("\n")))
            shown = st["out"]
        if changed:
            show("   now: " + ", ".join(f"{k} = {v}" for k, v in changed.items()))
        last = st["vars"]
        show(f"\nStep {n}, line {st['line']}:  {st['text']}\n   {st['says']}")
        try:
            answer = read("   [Enter = next, c = finish, v = all variables, q = quit] ").strip().lower()
        except EOFError:
            answer = "c"
        if answer == "q":
            return 0
        if answer == "v":
            show("   variables: " + (", ".join(f"{k} = {v}" for k, v in st["vars"].items()) or "none yet"))
        if answer == "c":
            break
    if shown < len(result["output"]):
        text = result["output"][shown:]
        show("   output:" + "".join("\n     " + ln for ln in text.rstrip("\n").split("\n")))
    if result["error"]:
        show("\n" + result["error"])
        return 1
    show("\nThe program finished." + (" (I stopped recording after %d steps.)" % MAX_STEPS if result["truncated"] else ""))
    return 0

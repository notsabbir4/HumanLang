"""The thin layer between a live page and a screen that is not Python (the browser, via Pyodide).

    start(code, seed, store) -> JSON {"page": "<html>", "live": true|false, "out": "...", "warnings": [...]} or {"error": ...}
    event(json)              -> JSON {"html": "<inner html>", "out": "..."} or {"error": ...}
    take_memory()            -> JSON of what the program remembered if it changed, else None
"""
import json
import random
import sys

from .errors import HLError, format_warning
from .interpreter import Interpreter
from .memory import Memory
from .render import inner_html, to_html

sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
_state = {}
LIMIT = 100000


def start(code, seed=None, store=None):
    if seed is not None:
        random.seed(seed)
    out = []

    def no_answers(prompt):
        raise HLError('A live page can\'t stop to "ask" a question.',
                      hint="Use an input: put an input called name  and read it with: the text in name")

    def write(text):
        if sum(map(len, out)) < LIMIT:
            out.append(text)

    lines = code.splitlines()
    memory = Memory(store)
    interp = Interpreter(out=write, inp=no_answers, memory=memory)
    try:
        interp.run(code)
    except HLError as e:
        return json.dumps({"error": e.format(lines)})
    except RecursionError:
        return json.dumps({"error": "This program calls itself too deeply."})
    _state.update(interp=interp, lines=lines, memory=memory)
    warnings = [format_warning(w, lines) for w in interp.warnings]
    if not interp.designs:
        return json.dumps({"page": None, "live": False, "out": "".join(out), "warnings": warnings})
    return json.dumps({"page": to_html(interp.designs[-1], interp.live_keys() if interp.live_handlers else None),
                       "live": bool(interp.live_handlers), "out": "".join(out), "warnings": warnings})


def event(msg_json):
    interp = _state.get("interp")
    if interp is None:
        return json.dumps({"error": "The page hasn't started."})
    m = json.loads(msg_json)
    out = []
    interp.out = out.append
    try:
        page = interp.live_event(m.get("type"), str(m.get("name", "")), str(m.get("text", "")), m.get("values"))
    except HLError as e:
        return json.dumps({"error": e.format(_state["lines"]), "out": "".join(out)})
    except RecursionError:
        return json.dumps({"error": "This page calls something that keeps calling itself."})
    if page is None:
        return json.dumps({"error": "There is no page to update."})
    return json.dumps({"html": inner_html(page), "out": "".join(out)})


def take_memory():
    m = _state.get("memory")
    return m.take_changes() if m else None

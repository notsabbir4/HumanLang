"""The thin layer between a game and a screen that is not Python: the browser (Pyodide) talks to these two functions.

    start(code)        -> JSON {"info": ...} (what the screen needs once) or {"error": "..."}
    frame(input_json)  -> JSON {"cmds": [...], "sounds": [...], "maps": {...}, "over": bool} or {"error": "..."}
"""
import json
import random
import sys

from .errors import HLError
from .interpreter import Interpreter

sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
_state = {}


def start(code, seed=None):
    if seed is not None:
        random.seed(seed)

    def no_answers(prompt):
        raise HLError("A game can't ask questions with \"ask\" while it runs.",
                      hint="Use keys and the mouse instead: when the key \"space\" is pressed")

    lines = code.splitlines()
    interp = Interpreter(out=lambda text: None, inp=no_answers)
    interp.max_output = 200000
    try:
        interp.run(code)
        info = interp.game_info()
    except HLError as e:
        return json.dumps({"error": e.format(lines)})
    except RecursionError:
        return json.dumps({"error": "This program calls itself too deeply."})
    if info is None:
        return json.dumps({"error": 'This program doesn\'t have a game in it.\nStart one with:  play a game titled "My game" with size 320 by 240'})
    _state.update(interp=interp, lines=lines)
    return json.dumps({"info": info, "warnings": [w[2] and f"Line {w[0]}: {w[1]}" for w in interp.warnings]})


def frame(input_json):
    interp = _state.get("interp")
    if interp is None:
        return json.dumps({"error": "The game hasn't started."})
    d = json.loads(input_json)
    try:
        out = interp.game_frame(down=d.get("down", ()), pressed=d.get("pressed", ()), clicked=bool(d.get("clicked")),
                                mouse=d.get("mouse"))
    except HLError as e:
        interp.frame_cmds = None
        return json.dumps({"error": e.format(_state["lines"])})
    except RecursionError:
        interp.frame_cmds = None
        return json.dumps({"error": "This game calls a function that keeps calling itself."})
    return json.dumps(out)

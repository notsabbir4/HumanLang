"""The thin layer between a game and a screen that is not Python: the browser (Pyodide) talks to these two functions.

    start(code)        -> JSON {"info": ...} (what the screen needs once) or {"error": "..."}
    frame(input_json)  -> JSON {"cmds": [...], "sounds": [...], "maps": {...}, "over": bool} or {"error": "..."}
"""
import json
import random
import sys

from .errors import HLError
from .interpreter import Interpreter
from .memory import Memory

sys.setrecursionlimit(max(sys.getrecursionlimit(), 5000))
_state = {}


def start(code, seed=None, store=None, assets=None):
    """assets: {file name: 'picture' or 'audio'} (JSON text or a dict): the files the person added."""
    if seed is not None:
        random.seed(seed)

    def no_answers(prompt):
        raise HLError("A game can't ask questions with \"ask\" while it runs.",
                      hint="Use keys and the mouse instead: when the key \"space\" is pressed")

    lines = code.splitlines()
    memory = Memory(store)
    interp = Interpreter(out=lambda text: None, inp=no_answers, memory=memory)
    interp.max_output = 200000
    interp.assets = _asset_kinds(assets)
    try:
        interp.run(code)
        info = interp.game_info()
    except HLError as e:
        return json.dumps({"error": e.format(lines)})
    except RecursionError:
        return json.dumps({"error": "This program calls itself too deeply."})
    if info is None:
        return json.dumps({"error": 'This program doesn\'t have a game in it.\nStart one with:  play a game titled "My game" with size 320 by 240'})
    _state.update(interp=interp, lines=lines, memory=memory)
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


def take_memory():
    """What the game remembered (as JSON) if it changed since the last call, else None. The host saves it."""
    m = _state.get("memory")
    return m.take_changes() if m else None


def _asset_kinds(assets):
    if isinstance(assets, str):
        try:
            assets = json.loads(assets)
        except ValueError:
            assets = None
    if hasattr(assets, "to_py"):
        assets = assets.to_py()
    return {str(k): v for k, v in assets.items() if v in ("picture", "audio")} if isinstance(assets, dict) else {}

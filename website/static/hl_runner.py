"""Runs a HumanLang program inside the browser (Pyodide). Called from worker.js."""
import json
import random
import sys

from humanlang.errors import HLError, format_warning
from humanlang.interpreter import Interpreter
from humanlang.memory import Memory
from humanlang.render import to_html

sys.setrecursionlimit(20000)
LIMIT = 200000  # characters of output before the program is stopped


class Flood(BaseException):
    pass


class NeedInput(BaseException):
    """The program asked a question and no answer is ready; the page will ask the person and run again."""
    def __init__(self, prompt):
        self.prompt = prompt


def run(code, inputs, seed=None, store=None, path=None):
    if seed is not None:
        random.seed(seed)  # the page re-runs the program for every answer; a fixed seed keeps dice rolls the same each time
    out, plain, size, answers = [], [], [0], list(inputs)  # plain = what the program says, without the questions and answers

    def write(text):
        size[0] += len(text)
        if size[0] > LIMIT:
            raise Flood()
        out.append(text)
        plain.append(text)

    def ask(prompt):
        if not answers:
            raise NeedInput(prompt)
        answer = answers.pop(0)
        size[0] += len(prompt) + len(answer)
        out.append(prompt + answer + "\n")
        return answer

    err = None
    memory = Memory(store)
    interp = Interpreter(out=write, inp=ask, memory=memory)
    try:
        interp.run(code, path)
    except HLError as e:
        err = e.format(code.splitlines())
    except NeedInput as n:
        return json.dumps({"out": "".join(out), "need": n.prompt})
    except Flood:
        err = "The program printed too much, so I stopped it."
    heads_up = [format_warning(w, code.splitlines()) for w in interp.warnings]
    page = to_html(interp.designs[-1]) if interp.designs else None  # a design: shown in the Preview tab
    return json.dumps({"out": "".join(out), "plain": "".join(plain), "err": err, "warnings": heads_up, "page": page, "memory": memory.take_changes(),
                       "kind": "game" if interp.game is not None else ("page" if page else "program")})


def debug(code, inputs):
    """Step-by-step: every line that ran, what it does, and what the variables held (for the Steps tab)."""
    from humanlang.debugger import record
    return json.dumps(record(code, inputs=list(inputs)))


# ---- Nina's project: a folder of files a program can `use` ----
PROJECT = "/proj"


def _project(files_json):
    import os
    import re
    import shutil
    shutil.rmtree(PROJECT, ignore_errors=True)
    os.makedirs(PROJECT, exist_ok=True)
    for name, text in json.loads(files_json or "{}").items():
        if re.fullmatch(r"[\w\- .]{1,60}", name) and isinstance(text, str):
            with open(os.path.join(PROJECT, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)


def project_check(code, files_json, name):
    """Check a program for mistakes without running it: {"err": ..., "warnings": [...]}"""
    import os
    _project(files_json)
    interp = Interpreter(out=lambda t: None)
    err = None
    try:
        interp.check(code, os.path.join(PROJECT, name))
    except HLError as e:
        err = e.format(code.splitlines())
    return json.dumps({"err": err, "warnings": [format_warning(w, code.splitlines()) for w in interp.warnings]})


def project_run(code, inputs, files_json, name):
    import os
    _project(files_json)
    return run(code, inputs, 1, None, os.path.join(PROJECT, name))

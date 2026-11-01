"""Runs a HumanLang program inside the browser (Pyodide). Called from worker.js."""
import json
import random
import sys

from humanlang.errors import HLError, format_warning
from humanlang.interpreter import Interpreter

sys.setrecursionlimit(20000)
LIMIT = 200000  # characters of output before the program is stopped


class Flood(BaseException):
    pass


class NeedInput(BaseException):
    """The program asked a question and no answer is ready; the page will ask the person and run again."""
    def __init__(self, prompt):
        self.prompt = prompt


def run(code, inputs, seed=None):
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
    interp = Interpreter(out=write, inp=ask)
    try:
        interp.run(code)
    except HLError as e:
        err = e.format(code.splitlines())
    except NeedInput as n:
        return json.dumps({"out": "".join(out), "need": n.prompt})
    except Flood:
        err = "The program printed too much, so I stopped it."
    heads_up = [format_warning(w, code.splitlines()) for w in interp.warnings]
    return json.dumps({"out": "".join(out), "plain": "".join(plain), "err": err, "warnings": heads_up})

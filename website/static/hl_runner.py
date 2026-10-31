"""Runs a HumanLang program inside the browser (Pyodide). Called from worker.js."""
import json
import sys

from humanlang.errors import HLError
from humanlang.interpreter import Interpreter

sys.setrecursionlimit(20000)
LIMIT = 200000  # characters of output before the program is stopped


class Flood(BaseException):
    pass


class NeedInput(BaseException):
    """The program asked a question and no answer is ready; the page will ask the person and run again."""
    def __init__(self, prompt):
        self.prompt = prompt


def run(code, inputs):
    out, size, answers = [], [0], list(inputs)

    def write(text):
        size[0] += len(text)
        if size[0] > LIMIT:
            raise Flood()
        out.append(text)

    def ask(prompt):
        if not answers:
            raise NeedInput(prompt)
        answer = answers.pop(0)
        write(prompt + answer + "\n")
        return answer

    err = None
    try:
        Interpreter(out=write, inp=ask).run(code)
    except HLError as e:
        err = e.format(code.splitlines())
    except NeedInput as n:
        return json.dumps({"out": "".join(out), "need": n.prompt})
    except Flood:
        err = "The program printed too much, so I stopped it."
    return json.dumps({"out": "".join(out), "err": err})

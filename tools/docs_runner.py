"""Runs the code blocks in docs/*.md.

Block kinds (the word after the three backticks):
  hum           must run without error; an `output` block right after it must match exactly
  hum-error     must stop with an error; the `output` block after it shows what is printed
  hum-random    must run without error; output varies, so none is compared
  hum-fragment  shown only (needs a real person or file); not run
  input         lines typed in answer to `ask`, for the block before it
  output        expected result of the block before it
"""
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.setrecursionlimit(50000)
from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

FENCE = re.compile(r"^```([\w-]*)[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
RUNNABLE = ("hum", "hum-error", "hum-random")


class Example:
    def __init__(self, kind, code, line, inputs, out_span, out_text):
        self.kind, self.code, self.line = kind, code, line
        self.inputs, self.out_span, self.out_text = inputs, out_span, out_text


def find_examples(text):
    blocks = [(m.group(1), m.group(2), m.span()) for m in FENCE.finditer(text)]
    examples = []
    for i, (info, body, span) in enumerate(blocks):
        if info not in RUNNABLE:
            continue
        inputs, out_span, out_text, j, prev_end = [], None, None, i + 1, span[1]
        if j < len(blocks) and blocks[j][0] == "input" and not text[prev_end:blocks[j][2][0]].strip():
            inputs = blocks[j][1].splitlines()
            prev_end = blocks[j][2][1]
            j += 1
        if j < len(blocks) and blocks[j][0] == "output" and not text[prev_end:blocks[j][2][0]].strip():
            out_span, out_text = blocks[j][2], blocks[j][1]
        examples.append(Example(info, body, text[:span[0]].count("\n") + 1, inputs, out_span, out_text))
    return examples


def run_example(ex):
    """Returns (transcript, error_text_or_None), as the terminal would show them."""
    out, answers = [], list(ex.inputs)

    def inp(prompt):
        if not answers:
            raise EOFError
        answer = answers.pop(0)
        out.append(prompt + answer + "\n")
        return answer

    interp = Interpreter(out=out.append, inp=inp)
    err = None
    old = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            interp.run(ex.code)
        except HLError as e:
            err = e.format(ex.code.splitlines())
        finally:
            os.chdir(old)
    return "".join(out), err


def transcript(ex):
    out, err = run_example(ex)
    return out + (err + "\n" if err else "")


def fill(path):
    """Rewrite the `output` blocks of one markdown file from real runs. Returns how many changed."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    changed = 0
    for ex in reversed(find_examples(text)):
        if ex.out_span is None or ex.kind == "hum-random":
            continue
        new = transcript(ex)
        if new != ex.out_text:
            start, end = ex.out_span
            text = text[:start] + "```output\n" + new + "```" + text[end:]
            changed += 1
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return changed

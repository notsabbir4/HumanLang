"""Tree-walking interpreter for HumanLang."""
import csv
import decimal
import io
import math
import os
import random
import re
import sys
import time
import unicodedata
from decimal import Decimal

from .designrun import DesignRun
from .errors import HLError, suggest
from .hints import for_word
from .lexer import lex
from .lint import assigned_names, lint
from .parser import STATEMENT_WORDS, parse, parse_expression, parse_with_warnings

MAX_DEPTH = 1000
BOXES = (list, dict)  # values that hold other values, and so are copied rather than shared
NUMBER_RE = re.compile(r"\s*-?[0-9]+(?:\.[0-9]+)?\s*$")
NUMS = (int, Decimal, float)
# Numbers are exact: whole numbers are Python ints, fractions are Decimals with 40 digits of room, so 0.1 + 0.2 is 0.3.
CONTEXT = decimal.Context(prec=40, Emax=99999, Emin=-99999, rounding=decimal.ROUND_HALF_EVEN,
                          traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow])
MAX_TEXT = 50_000_000    # letters in one text made by joining texts together
MAX_ITEMS = 10_000_000   # items in one list made by joining lists together
MAX_OUTPUT = 20_000_000  # letters one program may print before it is stopped (hl run --max-output changes it)
MODULE_FNS = {"sqrt": "math", "abs": "math", "round": "math", "floor": "math",
              "ceiling": "math", "sum": "math", "largest": "math", "smallest": "math",
              "readfile": "files", "split": "text", "join": "text", "replace": "text",
              "trim": "text", "today": "dates", "now": "dates", "pick": "random",
              "first": "text", "last": "text", "slice": "text", "find": "text", "fileexists": "files",
              "readcsv": "files", "readrows": "files", "roundto": "math"}
CMP_PHRASE = {"lt": "is less than", "gt": "is greater than",
              "ge": "is at least", "le": "is at most"}
VERBS = {"-": "subtract", "*": "multiply", "/": "divide", "//": "divide", "%": "use mod on", "**": "raise"}


class StopSignal(Exception):
    pass


class SkipSignal(Exception):
    pass


class ProgramExit(Exception):
    """"stop the program": ends everything, quietly."""


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        e = self
        while e is not None:
            if name in e.vars:
                return e
            e = e.parent
        return None

    def names(self):
        out, e = [], self
        while e is not None:
            out.extend(e.vars)
            e = e.parent
        return out


class Function:
    def __init__(self, name, params, body, env, source=None):
        self.name, self.params, self.body, self.env = name, params, body, env
        self.source = source  # the file it was written in (a Source), so errors can say where


def is_num(v):
    return isinstance(v, NUMS) and not isinstance(v, bool)


def norm(x):
    """A whole-valued number becomes an int; floats from outside are turned into exact decimals."""
    if type(x) is float:
        x = Decimal(repr(x))
    if type(x) is Decimal:
        if x == x.to_integral_value() and x.adjusted() < 40:  # past 40 digits a result is rounded, so it stays a decimal
            return int(x)
        return x.normalize()
    return x


def show_number(v):
    """How a number is shown: whole numbers in full; fractions exactly, up to 10 significant digits."""
    if type(v) is not Decimal:
        v = Decimal(v)
    ctx = decimal.Context(prec=10, rounding=decimal.ROUND_HALF_EVEN)
    r = ctx.plus(v) if len(v.as_tuple().digits) > 10 else v
    if r.adjusted() >= 40:  # a rounded, enormous result: write it as 2.5e+407 rather than 400 digits
        return format(r, "e").replace("E", "e").replace("+", "+")
    out = format(r, "f")
    if "." in out:
        out = out.rstrip("0").rstrip(".")
    return "0" if out in ("-0", "") else out


def round_places(v, places):
    """Round half up (2.5 becomes 3, -2.5 becomes -2) to a number of decimal places, exactly."""
    shift = Decimal(10) ** places
    return (Decimal(v) * shift + Decimal("0.5")).to_integral_value(rounding=decimal.ROUND_FLOOR) / shift


def floor_div(a, b):
    if type(a) is int and type(b) is int:
        return a // b
    return int((Decimal(a) / Decimal(b)).to_integral_value(rounding=decimal.ROUND_FLOOR))


def modulo(a, b):
    if type(a) is int and type(b) is int:
        return a % b
    return norm(Decimal(a) - Decimal(b) * floor_div(a, b))


def desc(v):
    if isinstance(v, bool):
        return "yes/no"
    if is_num(v):
        return "a number"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "a list"
    if isinstance(v, dict):
        return "a record"
    if v is None:
        return "nothing"
    return "a function"


def copy_val(v):
    t = type(v)
    if t is list:
        return [copy_val(x) if type(x) in BOXES else x for x in v]
    if t is dict:
        return {k: copy_val(x) if type(x) in BOXES else x for k, x in v.items()}
    return v


def human_key(v):
    """Sort text the way people expect: ignore capital letters and accents (apple, Banana, Émile, Zoe)."""
    if isinstance(v, str):
        plain = "".join(c for c in unicodedata.normalize("NFKD", v) if not unicodedata.combining(c))
        return (plain.casefold(), v)
    if isinstance(v, list):
        return [human_key(x) for x in v]
    return v


def hl_eq(a, b):
    if is_num(a) and is_num(b):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(hl_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(hl_eq(a[k], b[k]) for k in a)
    if type(a) is not type(b):
        return False
    return a == b


class Source:
    """One file of a program: its name (None for the main program) and its lines."""
    def __init__(self, name, lines, path=None):
        self.name, self.lines, self.path = name, lines, path


class Interpreter(DesignRun):
    def __init__(self, out=None, inp=None):
        self.design_init()
        self.out = out or sys.stdout.write
        self.inp = inp or input
        self.globals = Env()
        self.modules = set()
        self.line = 0
        self.depth = 0
        self.source_lines = []
        self.main_source = None
        self.source = Source(None, [])  # the file that is running now
        self.base_dir = os.getcwd()  # where "use" looks for other files: next to the program
        self.max_text, self.max_items, self.max_output = MAX_TEXT, MAX_ITEMS, MAX_OUTPUT
        self.printed = 0
        self.deadline = None  # a time (time.monotonic) after which the program is stopped
        self.warnings = []
        self.nothing_from = {}  # variable name -> (function, line) for values that came back as nothing
        self.trace = None  # set to a function(line_number, text) to watch every statement run
        # look each statement/expression handler up once, not on every step
        self._ex = {k[2:]: getattr(self, k) for k in dir(self) if k.startswith("x_")}
        self._ev = {k[2:]: getattr(self, k) for k in dir(self) if k.startswith("e_")}

    # ---- running ---------------------------------------------------------
    def prepare(self, source, path=None):
        """Parse the program, and every file it uses, and collect heads-up warnings
        (things that work, but may not mean what you hoped). path is where the program lives (for "use")."""
        main = self.main_source = self.source = Source(None, source.splitlines(), os.path.abspath(path) if path else None)
        if path:
            self.base_dir = os.path.dirname(main.path)
        lex_warnings = []
        stmts, parse_warnings = parse_with_warnings(lex(source, lex_warnings))
        found = []  # (line, message, hint) for the main program; (line, message, hint, file, text) for another file
        state = {"seen": {main.path} if path else set(), "names": set()}
        stmts = self.expand(stmts, self.base_dir, found, state)
        try:
            found += lint(stmts, state["names"])
            found += self.name_clashes(stmts, main, {})
        except Exception:  # a heads-up check must never stop a program from running
            pass
        self.warnings = sorted(set(found + parse_warnings + lex_warnings),
                               key=lambda w: (len(w) > 3, w[3] if len(w) > 3 else "", w[0], w[1]))
        return stmts

    def expand(self, stmts, base, found, state):
        """Replace each `use "file.hum"` by the statements of that file. A file is used once, however often it is named."""
        out = []
        for s in stmts:
            if s[0] != "include":
                out.append(s)
                continue
            self.line = s[1]
            path = os.path.abspath(os.path.join(base, s[2]))
            if path in state["seen"]:
                continue  # already used, or being used (which would otherwise go round in circles)
            state["seen"].add(path)
            text = self.read_text(path, s[2], using=True)
            shown = os.path.relpath(path, self.base_dir) if path.startswith(self.base_dir + os.sep) else path
            src = Source(shown.replace(os.sep, "/"), text.splitlines(), path)
            lex_warn = []
            try:
                inner, parse_warn = parse_with_warnings(lex(text, lex_warn))
                inner = self.expand(inner, os.path.dirname(path), found, state)
            except HLError as e:
                if e.file is None:  # a mistake in that file: say which file
                    e.file = src.name
                    e.source_text = src.lines[e.line - 1] if e.line and e.line <= len(src.lines) else None
                raise
            try:
                lint_warn = lint(inner, state["names"])
            except Exception:
                lint_warn = []
            state["names"] |= assigned_names(inner)
            for w in lint_warn + parse_warn + lex_warn:
                found.append((w[0], w[1], w[2], src.name, src.lines[w[0] - 1] if 1 <= w[0] <= len(src.lines) else ""))
            out.append(("module", s[1], src, inner))
        return out

    def name_clashes(self, stmts, src, seen):
        """Heads-ups for a name that two parts of the program both make: a later one replaces the earlier one."""
        found = []

        def add(line, message, hint):
            if src.name:
                found.append((line, message, hint, src.name, src.lines[line - 1] if 1 <= line <= len(src.lines) else ""))
            else:
                found.append((line, message, hint))

        for s in stmts:
            if s[0] == "module":
                found += self.name_clashes(s[3], s[2], seen)
                continue
            name = s[2] if s[0] in ("define", "set") else s[4] if s[0] == "ask" else None
            if name is None:
                continue
            before = seen.get(name)
            if before:
                kind, line, file = before
                where = f"line {line}" + (f" of {file}" if file else "")
                if s[0] == "define":
                    add(s[1], f'"{name}" is already {"a function" if kind == "define" else "a variable"} ({where}); this "define" replaces it.',
                        "Two parts of the program use the same name and would break each other. Give one of them another name.")
                elif kind == "define":
                    add(s[1], f'"{name}" is already a function ({where}); this makes a variable with the same name.',
                        "Give one of them another name.")
            if s[0] == "define" or not before:
                seen[name] = (s[0], s[1], src.name)
        return found

    def run(self, source, path=None):
        self.run_statements(self.prepare(source, path), source)

    def run_statements(self, stmts, source):
        """Run a program that prepare() has already parsed."""
        self.source_lines = source.splitlines()
        if self.main_source is None or self.main_source.lines != self.source_lines:
            self.main_source = Source(None, self.source_lines)
        self.source = self.main_source
        with decimal.localcontext(CONTEXT):
            try:
                self.exec_block(stmts, self.globals)
            except ProgramExit:
                pass
            except RecursionError:
                raise self.err("This went too many levels deep, so I stopped it.",
                               "A function may be calling itself without a way to stop.")
            except MemoryError:
                raise self.err("The computer ran out of memory here, so I stopped.",
                               "A text or a list may be growing without end. Look for a loop that keeps making it bigger.")
            except HLError as e:
                self.explain_nothing(e)
                raise

    def set_time_limit(self, seconds):
        """Stop the program (with a friendly error) once it has run for this many seconds."""
        self.time_limit = seconds
        self.deadline = time.monotonic() + seconds if seconds else None

    def tick(self):
        if time.monotonic() > self.deadline:
            raise self.err(f"The program ran for more than {self.time_limit:g} seconds, so I stopped it.",
                           'Check that every "repeat while" loop can end. (hl run --time-limit SECONDS changes this; 0 means no limit.)')

    def check(self, source, path=None):
        self.prepare(source, path)

    def explain_nothing(self, e):
        """If an error mentions "nothing", say which function gave it back (the cause is often far from the error)."""
        if "nothing" not in e.message or not e.line or e.line > len(self.source_lines):
            return
        words = set(re.findall(r"[^\W\d]\w*", self.source_lines[e.line - 1]))
        notes = [f'"{n}" is nothing because "{fn}" finished without giving back a value (line {ln}).'
                 for n, (fn, ln) in self.nothing_from.items() if n in words]
        if notes:
            e.hint = (e.hint + "\n" if e.hint else "") + "\n".join(notes)

    def run_repl(self, source):
        """Like run(), but a lone expression prints its value."""
        self.source_lines = source.splitlines()
        first = source.split(None, 1)[0] if source.strip() else ""
        if "\n" not in source and first not in STATEMENT_WORDS:
            try:
                node = parse_expression(source)
            except HLError:
                node = None
            if node is not None:
                with decimal.localcontext(CONTEXT):
                    value = self.ev(node, self.globals)
                if value is not None:
                    self.out(self.fmt(value) + "\n")
                return
        try:
            with decimal.localcontext(CONTEXT):
                self.exec_block(self.prepare(source), self.globals)
        except ProgramExit:
            pass

    def err(self, msg, hint=None):
        e = HLError(msg, self.line, hint)
        src = self.source
        if src.name:  # the mistake is in a file other than the main program
            e.file = src.name
            e.source_text = src.lines[self.line - 1] if 1 <= self.line <= len(src.lines) else ""
        return e

    def show(self, v):
        """A value for an error message: text is quoted so it can't be mistaken for a word."""
        return f'"{v}"' if isinstance(v, str) else self.fmt(v)

    def emit(self, text):
        """Everything a program prints goes through here, so a runaway program can be stopped."""
        self.printed += len(text)
        if self.max_output and self.printed > self.max_output:
            raise self.err(f"The program printed more than {self.max_output:,} letters, so I stopped it.",
                           'Check that every "repeat while" loop can end. (hl run --max-output LETTERS changes this; 0 means no limit.)')
        self.out(text)

    # ---- values ----------------------------------------------------------
    def fmt(self, v):
        t = type(v)
        if t is str:
            return v
        if v is None:
            return "nothing"
        if isinstance(v, bool):
            return "yes" if v else "no"
        if isinstance(v, int):
            if v.bit_length() > 14000:  # about 4200 digits: show the same thing on every Python version
                try:
                    return "%.10g" % float(v)
                except OverflowError:
                    return "infinity" if v > 0 else "-infinity"
            return str(v)
        if t is Decimal or isinstance(v, float):
            return show_number(v if t is Decimal else Decimal(repr(v)))
        if isinstance(v, list):
            if not v:
                return "empty list"
            # a list inside a list is bracketed, so the text reads back the way it is written
            return "list of " + ", ".join(self.fmt_in(x) for x in v)
        if isinstance(v, dict):
            if not v:
                return "empty record"
            return "record with " + " and ".join(f"{k} {self.fmt_in(x)}" for k, x in v.items())
        if isinstance(v, Function):
            return f"a function called {v.name}"
        return v

    def truth(self, v):
        if isinstance(v, bool):
            return v
        hint = 'Use a comparison such as "is", "is greater than" or "is at least".'
        if is_num(v):
            hint += " To ask whether a number is anything but zero, write: if x is not 0"
        raise self.err(f"I expected yes or no here, but got {desc(v)}.", hint)

    # ---- statements ------------------------------------------------------
    def exec_block(self, stmts, env):
        ex, trace = self._ex, self.trace
        for s in stmts:
            self.line = s[1]
            if trace:
                lines = self.source.lines
                trace(s[1], lines[s[1] - 1].strip() if s[1] <= len(lines) else "")
            ex[s[0]](s, env)

    def x_say(self, s, env):
        self.emit(self.fmt(self.ev(s[2], env)) + "\n")

    def fmt_in(self, x):
        """A value shown inside a list or record: lists and records get brackets."""
        return "(" + self.fmt(x) + ")" if type(x) in BOXES else self.fmt(x)

    def x_set(self, s, env):
        v = self.ev(s[3], env)
        env.vars[s[2]] = copy_val(v) if type(v) in BOXES else v
        if v is None or self.nothing_from:
            self.note_nothing(s[2], s[3], v, s[1], env)

    def note_nothing(self, name, node, v, line, env):
        if v is not None:
            self.nothing_from.pop(name, None)
        elif node[0] in ("call", "var"):
            holder = env.find(node[1])
            if holder is not None and isinstance(holder.vars[node[1]], Function):
                self.nothing_from[name] = (node[1], line)

    def unknown(self, name, env, creating=False, command=False):
        cands = env.names() + (STATEMENT_WORDS if command else [])
        hint = suggest(name, cands)
        if creating:
            extra = f'To make a new variable, use: set {name} to ...'
            hint = f'{hint} {extra}' if hint else extra
        elif not hint:
            hint = for_word(name) or f'Create it first with: set {name} to ...'
        return self.err(f'I don\'t know "{name}".', hint)

    def target(self, name, env):
        e = env.find(name)
        if e is None:
            raise self.unknown(name, env, creating=True)
        return e

    def x_change(self, s, env):
        e = self.target(s[2], env)
        v = self.ev(s[3], env)
        e.vars[s[2]] = copy_val(v) if type(v) in BOXES else v
        if v is None or self.nothing_from:
            self.note_nothing(s[2], s[3], v, s[1], env)

    def index(self, seq, idx):
        if not is_num(idx) or int(idx) != idx:
            raise self.err(f"An item number must be a whole number, but got {self.fmt(idx)}.")
        i, n = int(idx), len(seq)
        if i < 1 or i > n:
            raise self.err(f"You asked for item {i}, but there {'is' if n == 1 else 'are'} only {n} "
                           f"{'item' if n == 1 else 'items'}.", "Item numbers start at 1.")
        return i - 1

    def key_of(self, node, env):
        k = self.ev(node, env)
        if not isinstance(k, str):
            raise self.err(f"A field name must be text, but got {desc(k)}.")
        return k

    def no_field(self, key, rec, name, can_add=False):
        hint = suggest(key, list(rec)) or (f"It has: {', '.join(rec)}." if rec else "It has no fields yet.")
        if can_add:
            hint += f"  To add a new field, write: set field {key} of {name} to ..."
        return self.err(f'{name if name.startswith("this") or name.startswith("one") else chr(34) + name + chr(34)} '
                        f'has no field called "{key}".', hint)

    def place_text(self, place):
        if isinstance(place, str):
            return place
        if place[0] == "pfield":
            key = place[1][1] if place[1][0] in ("lit", "var") else "..."
            return f"field {key} of {self.place_text(place[2])}"
        idx = place[1]
        n = f"item {idx[1]}" if idx[0] == "lit" else f"item {idx[1]}" if idx[0] == "var" else "an item"
        return f"{n} of {self.place_text(place[2])}"

    def place_slot(self, place, env):
        """Find where a place lives: gives back (container, key). A name lives in its scope; an item in a list."""
        if isinstance(place, str):
            return self.target(place, env).vars, place
        holder, key = self.place_slot(place[2], env)
        seq = holder[key]
        if place[0] == "pfield":
            if not isinstance(seq, dict):
                raise self.err(f'"{self.place_text(place[2])}" is {desc(seq)}, not a record.')
            k = self.key_of(place[1], env)
            if k not in seq:
                raise self.no_field(k, seq, self.place_text(place[2]))
            return seq, k
        if not isinstance(seq, list):
            raise self.err(f'"{self.place_text(place[2])}" is {desc(seq)}, not a list.')
        return seq, self.index(seq, self.ev(place[1], env))

    def x_changeitem(self, s, env):
        if isinstance(s[2], str):
            e = self.target(s[2], env)
            seq = e.vars[s[2]]
            if not isinstance(seq, list):
                raise self.err(f'"{s[2]}" is {desc(seq)}, not a list.')
        else:
            holder, key = self.place_slot(s[2], env)
            seq = holder[key]
            if not isinstance(seq, list):
                raise self.err(f'"{self.place_text(s[2])}" is {desc(seq)}, not a list.')
        i = self.index(seq, self.ev(s[3], env))
        seq[i] = copy_val(self.ev(s[4], env))

    def record_at(self, place, env):
        if isinstance(place, str):
            holder, key = self.target(place, env).vars, place
        else:
            holder, key = self.place_slot(place, env)
        rec = holder[key]
        if not isinstance(rec, dict):
            raise self.err(f'"{self.place_text(place)}" is {desc(rec)}, not a record.',
                           'To make a record, write: set person to record with name "Ann" and age 30')
        return rec

    def x_setfield(self, s, env):
        """set field KEY of PLACE to VALUE: makes the field, or replaces it."""
        rec = self.record_at(s[2], env)
        key = self.key_of(s[3], env)
        rec[key] = copy_val(self.ev(s[4], env))

    def x_changefield(self, s, env):
        """change field KEY of PLACE to VALUE: the field must already exist (this catches typos)."""
        rec = self.record_at(s[2], env)
        key = self.key_of(s[3], env)
        if key not in rec:
            raise self.no_field(key, rec, self.place_text(s[2]), can_add=True)
        rec[key] = copy_val(self.ev(s[4], env))

    def x_addplace(self, s, env):
        val = self.ev(s[2], env)
        holder, key = self.place_slot(s[3], env)
        cur, name = holder[key], self.place_text(s[3])
        if isinstance(cur, list):
            cur.append(copy_val(val))
        elif is_num(cur) and is_num(val):
            holder[key] = norm(cur + val)
        elif isinstance(cur, str) and isinstance(val, str):
            if len(cur) + len(val) > self.max_text:
                raise self.too_long("text", self.max_text)
            holder[key] = cur + val
        else:
            raise self.err(f'You can\'t add {desc(val)} to "{name}", which holds {desc(cur)}.',
                           "Numbers add to numbers, text to text, and anything can be added to a list.")

    def x_subtractplace(self, s, env):
        val = self.ev(s[2], env)
        holder, key = self.place_slot(s[3], env)
        cur = holder[key]
        if not (is_num(cur) and is_num(val)):
            raise self.err(f'You can\'t subtract {desc(val)} from "{self.place_text(s[3])}", which holds {desc(cur)}.',
                           "Only numbers can be subtracted.")
        holder[key] = norm(cur - val)

    def x_removeplace(self, s, env):
        val = self.ev(s[2], env)
        holder, key = self.place_slot(s[3], env)
        cur, name = holder[key], self.place_text(s[3])
        if not isinstance(cur, list):
            raise self.err(f'"{name}" is {desc(cur)}, not a list.')
        for i, x in enumerate(cur):
            if hl_eq(x, val):
                del cur[i]
                return
        raise self.err(f"{self.fmt(val)} isn't in the list \"{name}\".")

    def x_removeat(self, s, env):
        """remove item N from PLACE"""
        if isinstance(s[3], str):
            holder, key = self.target(s[3], env).vars, s[3]
        else:
            holder, key = self.place_slot(s[3], env)
        seq = holder[key]
        if not isinstance(seq, list):
            raise self.err(f'"{self.place_text(s[3])}" is {desc(seq)}, not a list.')
        del seq[self.index(seq, self.ev(s[2], env))]

    def x_add(self, s, env):
        name = s[3]
        e = env
        while e is not None and name not in e.vars:
            e = e.parent
        if e is None:
            raise self.unknown(name, env, creating=True)
        cur, val = e.vars[name], self.ev(s[2], env)
        tc, tv = type(cur), type(val)
        if tc is int and tv is int:
            e.vars[name] = cur + val
            return
        if isinstance(cur, list):
            cur.append(copy_val(val))
        elif is_num(cur) and is_num(val):
            e.vars[s[3]] = norm(cur + val)
        elif isinstance(cur, str) and isinstance(val, str):
            if len(cur) + len(val) > self.max_text:
                raise self.too_long("text", self.max_text)
            e.vars[s[3]] = cur + val
        else:
            raise self.err(f'You can\'t add {desc(val)} to "{s[3]}", which holds {desc(cur)}.',
                           "Numbers add to numbers, text to text, and anything can be added to a list.")

    def x_subtract(self, s, env):
        e = self.target(s[3], env)
        cur, val = e.vars[s[3]], self.ev(s[2], env)
        if not (is_num(cur) and is_num(val)):
            raise self.err(f'You can\'t subtract {desc(val)} from "{s[3]}", which holds {desc(cur)}.',
                           "Only numbers can be subtracted.")
        e.vars[s[3]] = norm(cur - val)

    def x_remove(self, s, env):
        e = self.target(s[3], env)
        cur, val = e.vars[s[3]], self.ev(s[2], env)
        if not isinstance(cur, list):
            raise self.err(f'"{s[3]}" is {desc(cur)}, not a list.')
        for i, x in enumerate(cur):
            if hl_eq(x, val):
                del cur[i]
                return
        raise self.err(f"{self.fmt(val)} isn't in the list \"{s[3]}\".")

    def x_ask(self, s, env):
        _, _, numeric, prompt, name = s
        text = self.fmt(self.ev(prompt, env)) + " "
        while True:
            try:
                raw = self.inp(text)
            except EOFError:
                raise self.err("The program asked a question, but there was no answer to read.")
            if not numeric:
                env.vars[name] = raw
                return
            if NUMBER_RE.match(raw):
                env.vars[name] = norm(Decimal(raw)) if "." in raw else int(raw)
                return
            self.emit(f'"{raw.strip()}" isn\'t a number. Please type a number.\n')

    def x_if(self, s, env):
        for cond, body in s[2]:
            self.line = s[1]
            v = self._ev[cond[0]](cond, env)
            if v is not True and v is not False:
                self.truth(v)  # raises the friendly error
            if v:
                self.exec_block(body, env)
                return
        if s[3] is not None:
            self.exec_block(s[3], env)

    def run_loop_body(self, body, env):
        """Returns False if the loop should stop."""
        try:
            self.exec_block(body, env)
        except SkipSignal:
            pass
        except StopSignal:
            return False
        return True

    def x_times(self, s, env):
        n = self.ev(s[2], env)
        if not is_num(n) or int(n) != n or n < 0:
            raise self.err(f"\"repeat\" needs a whole number of times (0 or more), but got {self.show(n)}.")
        body, run = s[3], self.exec_block
        for _ in range(int(n)):
            if self.deadline:
                self.tick()
            try:
                run(body, env)
            except SkipSignal:
                continue
            except StopSignal:
                break

    def x_while(self, s, env):
        body, run, line = s[3], self.exec_block, s[1]
        while True:
            self.line = line
            if self.deadline:
                self.tick()
            v = self.ev(s[2], env)
            if v is not True and v is not False:
                self.truth(v)  # raises the friendly error
            if not v:
                break
            try:
                run(body, env)
            except SkipSignal:
                continue
            except StopSignal:
                break

    def x_for(self, s, env):
        seq = self.ev(s[3], env)
        if isinstance(seq, str):
            seq = list(seq)
        elif isinstance(seq, list):
            seq = list(seq)
        else:
            raise self.err(f'"for each" needs a list or text to go through, but got {desc(seq)}.')
        body, run, name = s[4], self.exec_block, s[2]
        for item in seq:
            if self.deadline:
                self.tick()
            env.vars[name] = copy_val(item) if type(item) in BOXES else item
            try:
                run(body, env)
            except SkipSignal:
                continue
            except StopSignal:
                break

    def x_define(self, s, env):
        env.vars[s[2]] = Function(s[2], s[3], s[4], env, self.source)

    def x_module(self, s, env):
        """The statements of another file, which `use "file.hum"` brought in: they run in the shared global space."""
        saved = self.source
        self.source = s[2]
        try:
            self.exec_block(s[3], self.globals)
        finally:
            self.source = saved

    def x_include(self, s, env):
        raise self.err('"use" with a file name only works at the very top level of a program.')

    def x_give(self, s, env):
        if s[2] is None:
            raise ReturnSignal(None)
        v = self._ev[s[2][0]](s[2], env)
        raise ReturnSignal(copy_val(v) if type(v) in BOXES else v)

    def x_stop(self, s, env):
        raise StopSignal()

    def x_fail(self, s, env):
        msg = self.ev(s[2], env)
        if not isinstance(msg, str):
            raise self.err(f'"fail with" needs a message in text, but got {desc(msg)}.',
                           'Example: fail with "That is not allowed"')
        e = self.err(msg)
        e.own = True
        raise e

    def x_exit(self, s, env):
        raise ProgramExit()

    def x_skip(self, s, env):
        raise SkipSignal()

    def require(self, module):
        if module not in self.modules:
            raise self.err(f'This needs the "{module}" module.',
                           f'Write "use {module}" near the top of your program.')

    def x_use(self, s, env):
        self.modules.add(s[2])

    def x_write(self, s, env):
        self.require("files")
        text, path = self.ev(s[2], env), self.ev(s[3], env)
        if not isinstance(path, str):
            raise self.err(f"A file name must be text, but got {desc(path)}.")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.fmt(text))
        except OSError as e:
            raise self.err(self.file_problem(path, e, "write"))

    def x_append(self, s, env):
        self.require("files")
        text, path = self.ev(s[2], env), self.ev(s[3], env)
        if not isinstance(path, str):
            raise self.err(f"A file name must be text, but got {desc(path)}.")
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(self.fmt(text))
        except OSError as e:
            raise self.err(self.file_problem(path, e, "add to"))

    def read_text(self, path, shown=None, newline=None, using=False):
        """The text of a file, with a friendly error for each thing that can go wrong."""
        shown = shown or path
        try:
            with open(path, encoding="utf-8-sig", newline=newline) as f:  # "-sig": an invisible mark some editors put first is skipped
                return f.read()
        except FileNotFoundError:
            if using:
                raise self.err(f'There is no file called "{shown}".',
                               'Check the spelling. The name is looked up from the folder of the file that has this "use" line.')
            raise self.err(f'There is no file called "{shown}".',
                           f'Check the spelling and the folder. To test first, write: file exists "{shown}"')
        except (IsADirectoryError, PermissionError) as e:  # Windows says "permission" for a folder
            raise self.err(self.file_problem(path, e, "read"))
        except UnicodeDecodeError:
            raise self.err(f'"{shown}" doesn\'t look like a text file.',
                           "HumanLang reads text saved as UTF-8 (the usual choice).")
        except OSError as e:
            raise self.err(f'I can\'t open the file "{shown}": {e.strerror}.')

    def read_csv(self, path, as_rows):
        """read csv PATH: a list of records (one per row, named by the header row), or a list of lists with `as rows`."""
        text = self.read_text(path, newline="")
        reader = csv.reader(io.StringIO(text, newline=""))
        rows, starts, last = [], [], 0
        try:
            for row in reader:
                if row:  # a blank line is not a row
                    rows.append(row)
                    starts.append(last + 1)
                last = reader.line_num
        except csv.Error as e:
            raise self.err(f'I couldn\'t read "{path}" as a CSV file: {e}.',
                           "A single value may be bigger than a million letters, or the file isn't really CSV.")
        if as_rows:
            return rows
        if not rows:
            return []
        header = [h.strip() for h in rows[0]]
        if "" in header:
            raise self.err(f'The first line of "{path}" has an empty column name.',
                           "The first line of a CSV file must name every column. To read it without names, write: read csv PATH as rows")
        for k, h in enumerate(header):
            if h in header[:k]:
                raise self.err(f'The first line of "{path}" has the column "{h}" twice.',
                               "Each column needs its own name. To read it without names, write: read csv PATH as rows")
        out = []
        for row, line in zip(rows[1:], starts[1:]):
            if len(row) != len(header):
                raise self.err(f'Line {line} of "{path}" has {len(row)} value{"s" if len(row) != 1 else ""}, '
                               f'but the first line names {len(header)} column{"s" if len(header) != 1 else ""}.',
                               "Fix that line, or read every line as a list with: read csv PATH as rows")
            out.append(dict(zip(header, row)))
        return out

    def x_writecsv(self, s, env):
        """write csv LIST to file PATH: a list of records (the field names become the first line) or a list of lists."""
        self.require("files")
        rows, path = self.ev(s[2], env), self.ev(s[3], env)
        if not isinstance(path, str):
            raise self.err(f"A file name must be text, but got {desc(path)}.")
        if not isinstance(rows, list):
            raise self.err(f'"write csv" needs a list of records or a list of lists, but got {desc(rows)}.')
        table = []
        if rows and all(isinstance(r, dict) for r in rows):
            header = []
            for r in rows:
                header += [k for k in r if k not in header]
            table.append(header)
            table += [[self.fmt(r[k]) if k in r else "" for k in header] for r in rows]
        elif all(isinstance(r, list) for r in rows):
            table = [[self.fmt(x) for x in r] for r in rows]
        else:
            raise self.err('"write csv" needs every item to be a record, or every item to be a list.')
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                csv.writer(f, lineterminator="\n").writerows(table)
        except OSError as e:
            raise self.err(self.file_problem(path, e, "write"))

    def file_problem(self, path, e, verb):
        if os.path.isdir(path):
            return f'I can\'t {verb} "{path}" because it is a folder, not a file.'
        if isinstance(e, PermissionError):
            return f'I\'m not allowed to {verb} the file "{path}".'
        return f'I couldn\'t {verb} the file "{path}": {e.strerror}.'

    def x_try(self, s, env):
        try:
            self.exec_block(s[2], env)
        except HLError as e:
            env.vars["problem"] = e.message
            env.vars["problem_line"] = e.line or 0
            env.vars["problem_kind"] = "fail" if e.own else "error"
            self.line = s[1]
            self.exec_block(s[3], env)

    def x_callstmt(self, s, env):
        node = s[2]
        if not node[2] and env.find(node[1]) is not None and \
                not isinstance(env.find(node[1]).vars[node[1]], Function):
            raise self.err(f'"{node[1]}" on its own doesn\'t do anything.',
                           f'To show it, write: say {node[1]}')
        self.ev(node, env)

    # ---- expressions -----------------------------------------------------
    def ev(self, n, env):
        return self._ev[n[0]](n, env)

    def e_lit(self, n, env):
        return n[1]

    def e_str(self, n, env):
        fmt, ev = self.fmt, self.ev
        return "".join(p if type(p) is str else fmt(ev(p, env)) for p in n[1])

    def e_var(self, n, env):
        name, e = n[1], env
        while e is not None:
            vs = e.vars
            if name in vs:
                v = vs[name]
                break
            e = e.parent
        else:
            raise self.unknown(name, env)
        if type(v) is not Function:
            return v
        if v.params:
            raise self.err(f'"{n[1]}" is a function that needs {len(v.params)} '
                           f'value{"s" if len(v.params) != 1 else ""}.',
                           f'Use it like: {n[1]} with ' + " and ".join(v.params))
        return self.call_fn(v, [])

    def e_list(self, n, env):
        return [copy_val(self.ev(x, env)) for x in n[1]]

    def e_item(self, n, env):
        seq = self.ev(n[2], env)
        idx = self.ev(n[1], env)
        if not isinstance(seq, (list, str)):
            raise self.err(f'"item ... of" needs a list or text, but got {desc(seq)}.')
        return seq[self.index(seq, idx)]

    def e_neg(self, n, env):
        v = self.ev(n[1], env)
        if not is_num(v):
            raise self.err(f"I can only put a minus sign in front of a number, not {desc(v)}.")
        return -v if type(v) is int else norm(-v)

    def e_not(self, n, env):
        return not self.truth(self.ev(n[1], env))

    def e_and(self, n, env):
        return self.truth(self.ev(n[1], env)) and self.truth(self.ev(n[2], env))

    def e_or(self, n, env):
        return self.truth(self.ev(n[1], env)) or self.truth(self.ev(n[2], env))

    def e_cmp(self, n, env):
        _, op, ln, rn = n
        ev = self._ev
        a, b = ev[ln[0]](ln, env), ev[rn[0]](rn, env)
        ta, tb = type(a), type(b)
        if ((ta is int or ta is Decimal) and (tb is int or tb is Decimal)) or (ta is str and tb is str):
            if op == "eq":
                return a == b
            if op == "lt":
                return a < b
            if op == "gt":
                return a > b
            if op == "ge":
                return a >= b
            return a <= b
        if op == "eq":
            return hl_eq(a, b)
        if (is_num(a) and is_num(b)) or (isinstance(a, str) and isinstance(b, str)):
            return {"lt": a < b, "gt": a > b, "ge": a >= b, "le": a <= b}[op]
        hint = "Both sides must be numbers, or both must be text."
        if (isinstance(a, str) and is_num(b)) or (is_num(a) and isinstance(b, str)):
            hint += ' To read a number from the user, write: ask number "Question?" and save it as x'
        raise self.err(f'I can\'t compare {desc(a)} with {desc(b)} using "{CMP_PHRASE[op]}".', hint)

    def too_long(self, what, limit):
        unit = "letters" if what == "text" else "items"
        return self.err(f"That {what} would have more than {limit:,} {unit}, which is more than HumanLang allows.",
                        "Check for a loop or a calculation that keeps making it bigger.")

    def e_bin(self, n, env):
        _, op, ln, rn = n
        ev = self._ev
        a, b = ev[ln[0]](ln, env), ev[rn[0]](rn, env)
        ta, tb = type(a), type(b)
        if ta is int and tb is int and op in "+-*":
            return a + b if op == "+" else a - b if op == "-" else a * b
        if (ta is int or ta is Decimal) and (tb is int or tb is Decimal) and op in "+-*":
            try:
                return norm(a + b if op == "+" else a - b if op == "-" else a * b)
            except ArithmeticError:
                raise self.err("That number is too big for me to work with.")
        if op == "+":
            if is_num(a) and is_num(b):
                return norm(a + b)
            if isinstance(a, str) and isinstance(b, str):
                if len(a) + len(b) > self.max_text:
                    raise self.too_long("text", self.max_text)
                return a + b
            if isinstance(a, list) and isinstance(b, list):
                if len(a) + len(b) > self.max_items:
                    raise self.too_long("list", self.max_items)
                return a + b
            if (isinstance(a, str) and is_num(b)) or (is_num(a) and isinstance(b, str)):
                what = "a number to text" if isinstance(a, str) else "text to a number"
                raise self.err(f"You tried to add {what}.",
                               'Use number of "5" to turn text into a number, or build text with '
                               'braces, like "Total: {x}".')
            raise self.err(f"You can't add {desc(a)} and {desc(b)}.")
        if not (is_num(a) and is_num(b)):
            raise self.err(f"I can only {VERBS[op]} numbers, but this has {desc(a)} and {desc(b)}.",
                           'To turn text into a number, use: number of "5"')
        try:
            if op == "-":
                return norm(a - b)
            if op == "*":
                return norm(a * b)
            if op == "**":
                return self.power(a, b)
            if b == 0:
                raise self.err("You can't divide by zero.", "Check the number you are dividing by first.")
            if op == "//":
                return floor_div(a, b)
            if op == "/":
                if type(a) is int and type(b) is int:
                    return a // b if a % b == 0 else norm(Decimal(a) / Decimal(b))
                return norm(Decimal(a) / Decimal(b))
            return modulo(a, b)
        except (ArithmeticError, ValueError):
            raise self.err("That number is too big for me to work with.")

    def power(self, a, b):
        if type(a) is int and type(b) is int and b >= 0:
            if b > 10000:
                raise self.err("That power is too big for me to work with.")
            return a ** b
        if a == 0 and b < 0:
            raise self.err("You can't divide by zero.", "Zero to a negative power means 1 / 0.")
        if a < 0 and b != int(b):
            raise self.err("A negative number to a fractional power has no real answer.")
        if abs(b) > 10000:
            raise self.err("That power is too big for me to work with.")
        return norm(Decimal(a) ** (int(b) if b == int(b) else Decimal(b)))

    def e_typeis(self, n, env):
        v = self.ev(n[2], env)
        if n[1] == "number":
            return is_num(v)
        if n[1] == "record":
            return isinstance(v, dict)
        return isinstance(v, str) if n[1] == "text" else isinstance(v, list)

    def e_record(self, n, env):
        return {k: copy_val(self.ev(v, env)) for k, v in n[1]}

    def e_field(self, n, env):
        rec = self.ev(n[2], env)
        key = self.key_of(n[1], env)
        if not isinstance(rec, dict):
            raise self.err(f"\"field {key} of\" needs a record, but got {desc(rec)}.",
                           'To make a record, write: set person to record with name "Ann" and age 30')
        if key not in rec:
            raise self.no_field(key, rec, "this record")
        return rec[key]

    def e_hasfield(self, n, env):
        rec = self.ev(n[1], env)
        if not isinstance(rec, dict):
            raise self.err(f'"has field" needs a record, but got {desc(rec)}.')
        return self.key_of(n[2], env) in rec

    def e_contains(self, n, env):
        a, b = self.ev(n[1], env), self.ev(n[2], env)
        if isinstance(a, str) and isinstance(b, str):
            return b in a
        if isinstance(a, list):
            return any(hl_eq(x, b) for x in a)
        raise self.err(f'"contains" needs text or a list on the left, but got {desc(a)}.',
                       'Examples: name contains "a"   or   colors contains "red"')

    def e_call(self, n, env):
        name = n[1]
        e = env.find(name)
        if e is None:
            raise self.unknown(name, env, command=True)
        fn = e.vars[name]
        if not isinstance(fn, Function):
            raise self.err(f'"{name}" holds {desc(fn)}, not a function, so I can\'t use "with" on it.')
        if len(n[2]) != len(fn.params):
            need = len(fn.params)
            raise self.err(f'"{name}" needs {need} value{"s" if need != 1 else ""}'
                           f'{" (" + " and ".join(fn.params) + ")" if need else ""}, '
                           f"but you gave {len(n[2])}.")
        ev, args = self._ev, []
        for a in n[2]:
            v = ev[a[0]](a, env)
            args.append(copy_val(v) if type(v) in BOXES else v)
        return self.call_fn(fn, args)

    def call_fn(self, fn, args):
        if self.depth >= MAX_DEPTH:
            raise self.err(f'"{fn.name}" kept calling itself more than {MAX_DEPTH} times.',
                           "Check that it has a way to stop (an if that gives back a value).")
        local = Env(fn.env)
        local.vars.update(zip(fn.params, args))
        call_line, call_source = self.line, self.source
        self.depth += 1
        if fn.source is not None:
            self.source = fn.source
        try:
            self.exec_block(fn.body, local)
            result = None
        except ReturnSignal as r:
            result = r.value
        except HLError as e:
            e.trace.append((fn.name, call_line, call_source.name))  # so the error can say how it got here
            raise
        finally:
            self.depth -= 1
            self.source = call_source
        self.line = call_line
        return result

    def text_phrase(self, name, args):
        """first/last N letters, letters A to B, find X in: for text, and the same for lists (items)."""
        if name == "find":
            what, where = args
            if isinstance(where, str):
                if not isinstance(what, str):
                    raise self.err(f"I can only look for text inside text, not {desc(what)}.")
                return where.find(what) + 1
            if isinstance(where, list):
                for i, x in enumerate(where):
                    if hl_eq(x, what):
                        return i + 1
                return 0
            raise self.err(f'"find ... in" needs text or a list to look in, but got {desc(where)}.')
        kind = args[-1]
        seq = args[-2]
        if not isinstance(seq, str if kind == "letters" else list):
            raise self.err(f'"{kind} of" needs {"text" if kind == "letters" else "a list"}, but got {desc(seq)}.',
                           "Use letters for text and items for a list.")
        nums = args[:-2]
        for x in nums:
            if not is_num(x) or int(x) != x:
                raise self.err(f"I need whole numbers here, but got {self.fmt(x)}.")
        if name == "first":
            if nums[0] < 0:
                raise self.err(f"I can't take {self.fmt(nums[0])} {kind}.")
            return seq[:int(nums[0])]
        if name == "last":
            if nums[0] < 0:
                raise self.err(f"I can't take {self.fmt(nums[0])} {kind}.")
            return seq[len(seq) - int(nums[0]):] if nums[0] < len(seq) else seq[:]
        a, b = int(nums[0]), int(nums[1])
        if a < 1:
            raise self.err(f"{kind.capitalize()} are numbered from 1, but you asked to start at {a}.")
        return seq[a - 1:max(b, 0)]  # asking past the end just stops at the end

    def e_fn(self, n, env):
        name = n[1]
        args = [self.ev(a, env) for a in n[2]]
        if name in MODULE_FNS:
            self.require(MODULE_FNS[name])
        if name in ("today", "now"):
            import datetime
            t = datetime.datetime.now()
            return t.strftime("%Y-%m-%d") if name == "today" else t.strftime("%H:%M")
        if name == "replace":
            old, new, text = args
            if not all(isinstance(x, str) for x in args):
                raise self.err("\"replace\" needs text for all three parts.",
                               'Example: replace "a" by "b" in name')
            if old == "":
                raise self.err("I can't replace nothing: the part to look for is empty.",
                               "To put something between every letter, build it with a loop: for each letter in text")
            result = text.replace(old, new)
            if len(result) > self.max_text:
                raise self.too_long("text", self.max_text)
            return result
        if name in ("first", "last", "slice", "find"):
            return self.text_phrase(name, args)
        if name == "keys":
            if not isinstance(args[0], dict):
                raise self.err(f'"keys of" needs a record, but got {desc(args[0])}.')
            return list(args[0])
        if name == "sortby":
            seq, key = args
            if not isinstance(seq, list):
                raise self.err(f'"sorted of ... by field" needs a list of records, but got {desc(seq)}.')
            if not isinstance(key, str):
                raise self.err(f"A field name must be text, but got {desc(key)}.")
            for r in seq:
                if not isinstance(r, dict):
                    raise self.err(f'"sorted of ... by field" needs every item to be a record, but one is {desc(r)}.')
                if key not in r:
                    raise self.no_field(key, r, "one of the records")
            vals = [r[key] for r in seq]
            if not (all(is_num(x) for x in vals) or all(isinstance(x, str) for x in vals)):
                raise self.err(f'I can only sort by "{key}" when it is a number in every record, or text in every record.')
            return sorted(seq, key=lambda r: human_key(r[key]))
        if name in ("split", "join"):
            first, sep = args
            if not isinstance(sep, str):
                raise self.err(f"The separator must be text, but got {desc(sep)}.")
            if name == "split":
                if not isinstance(first, str):
                    raise self.err(f"I can only split text, not {desc(first)}.")
                if not sep:
                    raise self.err("I can't split text by nothing: the separator is empty.",
                                   "To go through the letters of a text, write: for each letter in text")
                return first.split(sep)
            if not isinstance(first, list):
                raise self.err(f"I can only join a list, not {desc(first)}.")
            result = sep.join(self.fmt(x) for x in first)
            if len(result) > self.max_text:
                raise self.too_long("text", self.max_text)
            return result
        v = args[0]
        if name == "pick":
            if not isinstance(v, list) or not v:
                raise self.err("I can only pick from a list that has something in it.")
            return random.choice(v)
        if name in ("sum", "largest", "smallest", "sorted"):
            if not isinstance(v, list):
                raise self.err(f"This needs a list, but got {desc(v)}.")
            nums = all(is_num(x) for x in v)
            texts = all(isinstance(x, str) for x in v)
            if name == "sorted":
                if nums:
                    return sorted(v)
                if texts:
                    return sorted(v, key=human_key)
                if v and all(isinstance(x, list) for x in v):
                    try:  # lists compare item by item, so put the sort key first: list of score, name
                        return sorted(v, key=human_key)
                    except TypeError:
                        raise self.err("I can't sort these lists: items in the same position must be all numbers or all text.")
                raise self.err("I can only sort a list of numbers, a list of text, or a list of lists, not a mix.")
            if not nums:
                raise self.err(f'"{name} of" needs a list of numbers.')
            if name == "sum":
                return norm(sum(v))
            if not v:
                raise self.err(f"The list is empty, so there is no {name} item.")
            return max(v) if name == "largest" else min(v)
        if name == "reversed":
            if not isinstance(v, (list, str)):
                raise self.err(f"I can only reverse a list or text, not {desc(v)}.")
            return v[::-1]
        if name == "trim":
            if not isinstance(v, str):
                raise self.err(f"I can only trim text, not {desc(v)}.")
            return v.strip()
        if name == "length":
            if not isinstance(v, (list, str)):
                raise self.err(f"I can only count the items of a list or the letters of text, not {desc(v)}.")
            return len(v)
        if name in ("upper", "lower"):
            if not isinstance(v, str):
                raise self.err(f"I can only change the case of text, not {desc(v)}.")
            return v.upper() if name == "upper" else v.lower()
        if name == "totext":
            return self.fmt(v)
        if name == "tonumber":
            if is_num(v):
                return v
            if isinstance(v, str) and NUMBER_RE.match(v):
                return norm(Decimal(v)) if "." in v else int(v)
            raise self.err(f"I can't turn {self.show(v) if isinstance(v, str) else desc(v)} into a number.",
                           'Only text that looks like a number works, such as "42" or "3.5".')
        if name == "random":
            a, b = args
            if not (is_num(a) and is_num(b) and int(a) == a and int(b) == b):
                raise self.err("A random number needs whole numbers for its range, like: random number from 1 to 10")
            if a > b:
                raise self.err(f"The range is backwards: {self.fmt(a)} is bigger than {self.fmt(b)}.")
            return random.randint(int(a), int(b))
        if name in ("readfile", "readcsv", "readrows"):
            if not isinstance(v, str):
                raise self.err(f"A file name must be text, but got {desc(v)}.")
            if name == "readfile":
                return self.read_text(v)
            return self.read_csv(v, name == "readrows")
        if name == "fileexists":
            if not isinstance(v, str):
                raise self.err(f"A file name must be text, but got {desc(v)}.")
            return os.path.isfile(v)
        if not is_num(v):
            raise self.err(f"This needs a number, but got {desc(v)}.")
        if name == "sqrt":
            if v < 0:
                raise self.err("You can't take the square root of a negative number.")
            return norm(Decimal(v).sqrt())
        if name == "abs":
            return norm(abs(v))
        if name == "round":
            return int(round_places(v, 0))
        if name in ("roundto", "fixed"):
            places = args[1]
            if not (is_num(places) and places == int(places) and 0 <= places <= 30):
                raise self.err(f"The number of places must be a whole number from 0 to 30, but got {self.show(places)}.")
            places = int(places)
            try:
                rounded = round_places(v, places)
                if name == "roundto":
                    return norm(rounded)
                return format(rounded.quantize(Decimal(1).scaleb(-places)), "f")
            except ArithmeticError:
                raise self.err("That number is too big for me to work with.")
        if name == "floor":
            return int(math.floor(v))
        if name == "ceiling":
            return int(math.ceil(v))
        raise self.err(f"Unknown built-in {name}.")

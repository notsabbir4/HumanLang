"""Tree-walking interpreter for HumanLang."""
import math
import random
import re
import sys

from .errors import HLError, suggest
from .hints import for_word
from .lexer import lex
from .parser import STATEMENT_WORDS, parse, parse_expression

MAX_DEPTH = 1000
NUMBER_RE = re.compile(r"\s*-?\d+(?:\.\d+)?\s*$")
MODULE_FNS = {"sqrt": "math", "abs": "math", "round": "math", "floor": "math",
              "ceiling": "math", "sum": "math", "largest": "math", "smallest": "math",
              "readfile": "files", "split": "text", "join": "text", "replace": "text",
              "trim": "text", "today": "dates", "now": "dates", "pick": "random"}
CMP_PHRASE = {"lt": "is less than", "gt": "is greater than",
              "ge": "is at least", "le": "is at most"}
VERBS = {"-": "subtract", "*": "multiply", "/": "divide", "%": "use mod on", "**": "raise"}


class StopSignal(Exception):
    pass


class SkipSignal(Exception):
    pass


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
    def __init__(self, name, params, body, env):
        self.name, self.params, self.body, self.env = name, params, body, env


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def norm(x):
    if isinstance(x, float) and x.is_integer() and abs(x) < 1e15:
        return int(x)
    return x


def desc(v):
    if isinstance(v, bool):
        return "yes/no"
    if is_num(v):
        return "a number"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "a list"
    if v is None:
        return "nothing"
    return "a function"


def copy_val(v):
    return [copy_val(x) for x in v] if isinstance(v, list) else v


def hl_eq(a, b):
    if is_num(a) and is_num(b):
        return a == b
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(hl_eq(x, y) for x, y in zip(a, b))
    if type(a) is not type(b):
        return False
    return a == b


class Interpreter:
    def __init__(self, out=None, inp=None):
        self.out = out or sys.stdout.write
        self.inp = inp or input
        self.globals = Env()
        self.modules = set()
        self.line = 0
        self.depth = 0
        self.source_lines = []
        self.trace = None  # set to a function(line_number, text) to watch every statement run
        # look each statement/expression handler up once, not on every step
        self._ex = {k[2:]: getattr(self, k) for k in dir(self) if k.startswith("x_")}
        self._ev = {k[2:]: getattr(self, k) for k in dir(self) if k.startswith("e_")}

    # ---- running ---------------------------------------------------------
    def run(self, source):
        self.source_lines = source.splitlines()
        stmts = parse(lex(source))
        try:
            self.exec_block(stmts, self.globals)
        except RecursionError:
            raise self.err("This went too many levels deep, so I stopped it.",
                           "A function may be calling itself without a way to stop.")

    def check(self, source):
        parse(lex(source))

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
                value = self.ev(node, self.globals)
                if value is not None:
                    self.out(self.fmt(value) + "\n")
                return
        self.exec_block(parse(lex(source)), self.globals)

    def err(self, msg, hint=None):
        return HLError(msg, self.line, hint)

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
        if isinstance(v, float):
            if v != v:
                return "not a number"
            if v in (math.inf, -math.inf):
                return "infinity" if v > 0 else "-infinity"
            return "%.10g" % v
        if isinstance(v, list):
            return "empty list" if not v else "list of " + ", ".join(self.fmt(x) for x in v)
        if isinstance(v, Function):
            return f"a function called {v.name}"
        return v

    def truth(self, v):
        if isinstance(v, bool):
            return v
        raise self.err(f"I expected yes or no here, but got {desc(v)}.",
                       'Use a comparison such as "is", "is greater than" or "is at least".')

    # ---- statements ------------------------------------------------------
    def exec_block(self, stmts, env):
        ex, trace = self._ex, self.trace
        for s in stmts:
            self.line = s[1]
            if trace:
                trace(s[1], self.source_lines[s[1] - 1].strip() if s[1] <= len(self.source_lines) else "")
            ex[s[0]](s, env)

    def x_say(self, s, env):
        self.out(self.fmt(self.ev(s[2], env)) + "\n")

    def x_set(self, s, env):
        v = self.ev(s[3], env)
        env.vars[s[2]] = copy_val(v) if type(v) is list else v

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
        e.vars[s[2]] = copy_val(v) if type(v) is list else v

    def index(self, seq, idx):
        if not is_num(idx) or int(idx) != idx:
            raise self.err(f"An item number must be a whole number, but got {self.fmt(idx)}.")
        i, n = int(idx), len(seq)
        if i < 1 or i > n:
            raise self.err(f"You asked for item {i}, but there {'is' if n == 1 else 'are'} only {n} "
                           f"{'item' if n == 1 else 'items'}.", "Item numbers start at 1.")
        return i - 1

    def x_changeitem(self, s, env):
        e = self.target(s[2], env)
        seq = e.vars[s[2]]
        if not isinstance(seq, list):
            raise self.err(f'"{s[2]}" is {desc(seq)}, not a list.')
        i = self.index(seq, self.ev(s[3], env))
        seq[i] = copy_val(self.ev(s[4], env))

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
                env.vars[name] = float(raw) if "." in raw else int(raw)
                return
            self.out(f'"{raw.strip()}" isn\'t a number. Please type a number.\n')

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
            raise self.err(f"\"repeat\" needs a whole number of times (0 or more), but got {self.fmt(n)}.")
        body, run = s[3], self.exec_block
        for _ in range(int(n)):
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
            env.vars[name] = copy_val(item) if type(item) is list else item
            try:
                run(body, env)
            except SkipSignal:
                continue
            except StopSignal:
                break

    def x_define(self, s, env):
        env.vars[s[2]] = Function(s[2], s[3], s[4], env)

    def x_give(self, s, env):
        if s[2] is None:
            raise ReturnSignal(None)
        v = self._ev[s[2][0]](s[2], env)
        raise ReturnSignal(copy_val(v) if type(v) is list else v)

    def x_stop(self, s, env):
        raise StopSignal()

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
            raise self.err(f'I couldn\'t write the file "{path}": {e.strerror}.')

    def x_try(self, s, env):
        try:
            self.exec_block(s[2], env)
        except HLError as e:
            env.vars["problem"] = e.message
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
        return -v

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
        if ((ta is int or ta is float) and (tb is int or tb is float)) or (ta is str and tb is str):
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

    def e_bin(self, n, env):
        _, op, ln, rn = n
        ev = self._ev
        a, b = ev[ln[0]](ln, env), ev[rn[0]](rn, env)
        ta, tb = type(a), type(b)
        if (ta is int or ta is float) and (tb is int or tb is float) and op in "+-*":
            try:
                r = a + b if op == "+" else a - b if op == "-" else a * b
            except OverflowError:
                raise self.err("That number is too big for me to work with.")
            return r if type(r) is int else norm(r)
        if op == "+":
            if is_num(a) and is_num(b):
                return norm(a + b)
            if isinstance(a, str) and isinstance(b, str):
                return a + b
            if isinstance(a, list) and isinstance(b, list):
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
            return norm(a / b) if op == "/" else norm(a % b)
        except (OverflowError, ValueError):
            raise self.err("That number is too big for me to work with.")

    def power(self, a, b):
        if isinstance(a, int) and isinstance(b, int) and b >= 0:
            if b > 10000:
                raise self.err("That power is too big for me to work with.")
            return a ** b
        if a == 0 and b < 0:
            raise self.err("You can't divide by zero.", "Zero to a negative power means 1 / 0.")
        if a < 0 and int(b) != b:
            raise self.err("A negative number to a fractional power has no real answer.")
        return norm(math.pow(a, b))

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
            args.append(copy_val(v) if type(v) is list else v)
        return self.call_fn(fn, args)

    def call_fn(self, fn, args):
        if self.depth >= MAX_DEPTH:
            raise self.err(f'"{fn.name}" kept calling itself more than {MAX_DEPTH} times.',
                           "Check that it has a way to stop (an if that gives back a value).")
        local = Env(fn.env)
        local.vars.update(zip(fn.params, args))
        call_line = self.line
        self.depth += 1
        try:
            self.exec_block(fn.body, local)
            result = None
        except ReturnSignal as r:
            result = r.value
        finally:
            self.depth -= 1
        self.line = call_line
        return result

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
            return text.replace(old, new)
        if name in ("split", "join"):
            first, sep = args
            if not isinstance(sep, str):
                raise self.err(f"The separator must be text, but got {desc(sep)}.")
            if name == "split":
                if not isinstance(first, str):
                    raise self.err(f"I can only split text, not {desc(first)}.")
                return first.split(sep) if sep else list(first)
            if not isinstance(first, list):
                raise self.err(f"I can only join a list, not {desc(first)}.")
            return sep.join(self.fmt(x) for x in first)
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
                if not (nums or texts):
                    raise self.err("I can only sort a list of numbers or a list of text, not a mix.")
                return sorted(v)
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
                return float(v) if "." in v else int(v)
            raise self.err(f"I can't turn {self.fmt(v) if isinstance(v, str) else desc(v)} into a number.",
                           'Only text that looks like a number works, such as "42" or "3.5".')
        if name == "random":
            a, b = args
            if not (is_num(a) and is_num(b) and int(a) == a and int(b) == b):
                raise self.err("A random number needs whole numbers for its range, like: random number from 1 to 10")
            if a > b:
                raise self.err(f"The range is backwards: {self.fmt(a)} is bigger than {self.fmt(b)}.")
            return random.randint(int(a), int(b))
        if name == "readfile":
            if not isinstance(v, str):
                raise self.err(f"A file name must be text, but got {desc(v)}.")
            try:
                with open(v, encoding="utf-8") as f:
                    return f.read()
            except OSError:
                raise self.err(f'I can\'t open the file "{v}".', "Check the spelling and the folder.")
        if not is_num(v):
            raise self.err(f"This needs a number, but got {desc(v)}.")
        if name == "sqrt":
            if v < 0:
                raise self.err("You can't take the square root of a negative number.")
            return norm(math.sqrt(v))
        if name == "abs":
            return abs(v)
        if name == "round":
            return int(math.floor(v + 0.5))
        if name == "floor":
            return int(math.floor(v))
        if name == "ceiling":
            return int(math.ceil(v))
        raise self.err(f"Unknown built-in {name}.")

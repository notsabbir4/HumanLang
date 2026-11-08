"""Formulas from text: calculate "2 * (3 + 4)" gives 14.

A small, safe reader of maths. It never runs the text as a program: it only understands numbers, + - * / ^ %,
brackets and a short list of functions, so it can safely take whatever a person types into a calculator.
"""
import decimal
import math
from decimal import Decimal

CONTEXT = decimal.Context(prec=40, Emax=99999, Emin=-99999, rounding=decimal.ROUND_HALF_EVEN,
                          traps=[decimal.InvalidOperation, decimal.DivisionByZero, decimal.Overflow])
MAX_LENGTH = 2000
MAX_DEPTH = 60
CONSTANTS = {"pi": Decimal("3.141592653589793238462643383279502884197"), "e": Decimal("2.718281828459045235360287471352662497757")}
FUNCTIONS = ("sqrt", "abs", "round", "floor", "ceil", "ceiling", "sin", "cos", "tan", "asin", "acos", "atan", "log", "ln",
             "exp", "min", "max", "root", "factorial")
WORDS_FOR_SYMBOLS = {"×": "*", "÷": "/", "−": "-", "–": "-", "x": "*", "·": "*"}


class FormulaError(Exception):
    def __init__(self, message, hint=None):
        super().__init__(message)
        self.message, self.hint = message, hint


def tokens(text):
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit()):
            j = i
            while j < n and text[j].isdigit():
                j += 1
            if j < n and text[j] == ".":
                j += 1
                while j < n and text[j].isdigit():
                    j += 1
            raw = text[i:j]
            if j < n and text[j] in "eE" and j + 1 < n and (text[j + 1].isdigit() or (text[j + 1] in "+-" and j + 2 < n and text[j + 2].isdigit())):
                k = j + 2
                while k < n and text[k].isdigit():
                    k += 1
                raw, j = text[i:k], k
            try:
                out.append(("num", Decimal(raw), i))
            except decimal.InvalidOperation:
                raise FormulaError(f'I can\'t read "{text[i:j]}" as a number.')
            i = j
        elif c.isalpha():
            j = i
            while j < n and text[j].isalpha():
                j += 1
            word = text[i:j].lower()
            out.append(("op", "*", i) if word == "x" else ("name", word, i))
            i = j
        elif c in "+-*/^%(),!" or c in WORDS_FOR_SYMBOLS:
            if c == "*" and text[i:i + 2] == "**":
                out.append(("op", "^", i))
                i += 2
                continue
            out.append(("op", WORDS_FOR_SYMBOLS.get(c, c), i))
            i += 1
        else:
            raise FormulaError(f'I don\'t understand "{c}" in this formula.',
                               "I can read numbers, + - * / ^ %, brackets, and functions like sqrt(16).")
    return out


class Reader:
    def __init__(self, text):
        if len(text) > MAX_LENGTH:
            raise FormulaError(f"That formula is too long (more than {MAX_LENGTH} characters).")
        self.text, self.toks, self.i, self.depth = text, tokens(text), 0, 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def op(self, *ops):
        t = self.peek()
        if t is not None and t[0] == "op" and t[1] in ops:
            self.i += 1
            return t[1]
        return None

    def fail_here(self, what):
        t = self.peek()
        if t is None:
            raise FormulaError(f"The formula ended too early: {what}.")
        shown = t[1] if t[0] != "num" else self.text[t[2]:t[2] + 12].strip()
        raise FormulaError(f'I did not expect "{shown}" here: {what}.')

    def run(self):
        if not self.toks:
            raise FormulaError("There is no formula to calculate.", 'Example: calculate "2 * (3 + 4)"')
        value = self.expr()
        if self.peek() is not None:
            self.fail_here("the formula should end here (is a + - * / missing?)")
        return value

    def expr(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise FormulaError("That formula has too many brackets inside each other.")
        v = self.term()
        while True:
            o = self.op("+", "-")
            if o is None:
                break
            r = self.term()
            v = CONTEXT.add(v, r) if o == "+" else CONTEXT.subtract(v, r)
        self.depth -= 1
        return v

    def term(self):
        v = self.unary()
        while True:
            o = self.op("*", "/")
            if o is None:
                t = self.peek()  # 2(3+4), 2pi, 3sqrt(4): a number or bracket right after a value means "times"
                if t is not None and ((t[0] == "op" and t[1] == "(") or t[0] == "name"):
                    o = "*"
                else:
                    break
            r = self.unary()
            if o == "*":
                v = CONTEXT.multiply(v, r)
            else:
                if r == 0:
                    raise FormulaError("You can't divide by zero.")
                v = CONTEXT.divide(v, r)
        return v

    def unary(self):
        o = self.op("-", "+")
        if o == "-":
            return -self.unary()
        if o == "+":
            return self.unary()
        return self.power()

    def power(self):
        base = self.postfix()
        if self.op("^"):
            exp = self.unary()  # right to left: 2^3^2 is 2^(3^2); and -2^2 is -(2^2) because unary wraps power
            return self.raise_to(base, exp)
        return base

    def raise_to(self, base, exp):
        if abs(exp) > 100000:
            raise FormulaError("That power is too big for me to work out.")
        try:
            if base == 0 and exp < 0:
                raise FormulaError("You can't divide by zero (zero to a negative power).")
            if exp == exp.to_integral_value():
                return CONTEXT.power(base, int(exp))
            if base < 0:
                raise FormulaError("A negative number can't be raised to a fraction.")
            return CONTEXT.power(base, exp)
        except (decimal.Overflow, decimal.InvalidOperation):
            raise FormulaError("That result is too big for me to work with.")

    def postfix(self):
        v = self.primary()
        while True:
            if self.op("%"):
                v = CONTEXT.divide(v, Decimal(100))
            elif self.op("!"):
                v = factorial(v)
            else:
                return v

    def primary(self):
        t = self.peek()
        if t is None:
            self.fail_here("I expected a number")
        if t[0] == "num":
            self.i += 1
            return t[1]
        if t[0] == "op" and t[1] == "(":
            self.i += 1
            v = self.expr()
            if not self.op(")"):
                self.fail_here('I expected ")" to close the bracket')
            return v
        if t[0] == "name":
            self.i += 1
            name = t[1]
            if name in CONSTANTS:
                return CONSTANTS[name]
            if name not in FUNCTIONS:
                from .errors import suggest
                hint = suggest(name, list(FUNCTIONS) + list(CONSTANTS))
                raise FormulaError(f'I don\'t know "{name}" in a formula.',
                                   (hint + "  " if hint else "") + "Functions: " + ", ".join(FUNCTIONS[:11]) + ", ... and the numbers pi and e.")
            if not self.op("("):
                self.fail_here(f'after "{name}" I expected a bracket, like {name}(16)')
            args = [self.expr()]
            while self.op(","):
                args.append(self.expr())
            if not self.op(")"):
                self.fail_here('I expected ")" to close the bracket')
            return call(name, args)
        self.fail_here("I expected a number")


def factorial(v):
    if v != v.to_integral_value() or v < 0:
        raise FormulaError("A factorial (!) needs a whole number that is not negative.")
    if v > 400:
        raise FormulaError("That factorial is too big for me to work out (the limit is 400!).")
    return Decimal(math.factorial(int(v)))


def float_fn(fn, x, what="that"):
    try:
        r = fn(float(x))
    except (ValueError, OverflowError, ZeroDivisionError):
        raise FormulaError(f"{what} has no answer for {x.normalize() if isinstance(x, Decimal) else x}.")
    return Decimal(repr(round(r, 12)))


def call(name, a):
    def need(n):
        if len(a) != n:
            raise FormulaError(f"{name}() needs {n} number{'s' if n != 1 else ''} inside the brackets, but got {len(a)}.")
    if name in ("min", "max"):
        return min(a) if name == "min" else max(a)
    if name == "round":
        if len(a) not in (1, 2):
            raise FormulaError("round() needs a number, and maybe how many decimals: round(2.567, 1).")
        digits = int(a[1]) if len(a) == 2 else 0
        if not -30 <= digits <= 30:
            raise FormulaError("round() can keep 0 to 30 decimals.")
        return a[0].quantize(Decimal(1).scaleb(-digits), rounding=decimal.ROUND_HALF_UP, context=CONTEXT)
    if name == "root":
        need(2)
        if a[1] == 0:
            raise FormulaError("root(x, 0) has no answer.")
        if a[0] < 0 and a[1] % 2 == 0:
            raise FormulaError("An even root of a negative number has no answer.")
        sign = -1 if a[0] < 0 else 1
        return sign * CONTEXT.power(abs(a[0]), CONTEXT.divide(Decimal(1), a[1]))
    need(1)
    x = a[0]
    if name == "sqrt":
        if x < 0:
            raise FormulaError("You can't take the square root of a negative number.")
        return CONTEXT.sqrt(x)
    if name == "abs":
        return abs(x)
    if name == "floor":
        return x.to_integral_value(rounding=decimal.ROUND_FLOOR)
    if name in ("ceil", "ceiling"):
        return x.to_integral_value(rounding=decimal.ROUND_CEILING)
    if name == "factorial":
        return factorial(x)
    if name == "ln":
        if x <= 0:
            raise FormulaError("ln() needs a number above zero.")
        return CONTEXT.ln(x)
    if name == "log":
        if x <= 0:
            raise FormulaError("log() needs a number above zero.")
        return CONTEXT.log10(x)
    if name == "exp":
        try:
            return CONTEXT.exp(x)
        except (decimal.Overflow, decimal.InvalidOperation):
            raise FormulaError("That result is too big for me to work with.")
    # angles are in degrees, the way people think of them
    if name in ("sin", "cos", "tan"):
        deg = float(x) % 360
        if name == "tan" and deg in (90.0, 270.0):
            raise FormulaError("tan() has no answer at 90 or 270 degrees.")
        return float_fn(getattr(math, name), Decimal(repr(math.radians(deg))), name + "()")
    if name in ("asin", "acos", "atan"):
        r = float_fn(getattr(math, name), x, name + "()")
        return Decimal(repr(round(math.degrees(float(r)), 10)))
    raise FormulaError(f'I don\'t know "{name}".')


def evaluate(text):
    """The value of a formula as a Decimal. Raises FormulaError with a plain-words reason."""
    try:
        return Reader(str(text)).run()
    except RecursionError:
        raise FormulaError("That formula is too deeply nested.")
    except (decimal.Overflow, decimal.InvalidOperation):
        raise FormulaError("That result is too big for me to work with.")

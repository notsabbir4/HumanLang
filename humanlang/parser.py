"""Parser: turns lines of tokens into a tree (AST) made of plain tuples.

Statements:  (kind, line, ...)      Expressions:  (kind, ...)
"""
from .errors import HLError, suggest
from .hints import for_word
from .lexer import Line, tokenize

STATEMENT_WORDS = ["say", "set", "change", "add", "subtract", "remove", "ask", "if",
                   "repeat", "for", "define", "give", "stop", "skip", "use", "try", "write"]

RESERVED = set(STATEMENT_WORDS) | {
    "otherwise", "while", "in", "with", "and", "or", "not", "is", "yes", "no", "nothing",
    "list", "item", "items", "of", "to", "from", "times", "plus", "minus", "divided",
    "mod", "then",
}

MODULES = ["math", "random", "text", "files", "dates"]

# phrase -> built-in function name (the argument follows the phrase)
PREFIXES = [
    (("length", "of"), "length"),
    (("uppercase", "of"), "upper"),
    (("lowercase", "of"), "lower"),
    (("number", "of"), "tonumber"),
    (("text", "of"), "totext"),
    (("square", "root", "of"), "sqrt"),
    (("absolute", "value", "of"), "abs"),
    (("round", "of"), "round"),
    (("floor", "of"), "floor"),
    (("ceiling", "of"), "ceiling"),
    (("read", "file"), "readfile"),
    (("sum", "of"), "sum"),
    (("largest", "of"), "largest"),
    (("smallest", "of"), "smallest"),
    (("sorted", "of"), "sorted"),
    (("reversed", "of"), "reversed"),
    (("trim", "of"), "trim"),
    (("the", "date", "today"), "today"),
    (("the", "time", "now"), "now"),
]

EXAMPLES = {
    "say": 'say "Hello"',
    "set": "set age to 20",
    "change": "change age to 21",
    "add": "add 1 to count",
    "subtract": "subtract 1 from count",
    "remove": 'remove "red" from colors',
    "ask": 'ask "What is your name?" and save it as name',
    "if": "if age is at least 18",
    "repeat": "repeat 3 times",
    "for": "for each color in colors",
    "define": "define add with a and b",
    "give": "give back a + b",
    "use": "use math",
    "write": 'write "hi" to file "out.txt"',
}


class Parser:
    def __init__(self, lines=None):
        self.lines = lines or []
        self.pos = 0
        self.toks, self.i = [], 0
        self.lineno, self.level = 0, 0
        self.example = None
        self.in_function = 0
        self.in_loop = 0
        self.defined = set()  # names made with "define" so far

    # ---- token helpers -------------------------------------------------
    def peek(self, k=0):
        j = self.i + k
        return self.toks[j] if j < len(self.toks) else None

    def word(self, w, k=0):
        t = self.peek(k)
        return t is not None and t.kind == "WORD" and t.value == w

    def words(self, *ws):
        return all(self.word(w, k) for k, w in enumerate(ws))

    def ahead(self, w):
        """Is the word w somewhere later on this line?"""
        return any(t.kind == "WORD" and t.value == w for t in self.toks[self.i + 1:])

    def accept(self, w):
        if self.word(w):
            self.i += 1
            return True
        return False

    def show(self, t):
        if t.kind == "STR":
            return '"' + "".join(p[1] for p in t.value) + '"'
        return str(t.value)

    def fail(self, msg, hint=None):
        if not msg.endswith((".", "?", "!")):
            msg += "."
        if hint is None and self.example:
            hint = f"Example: {self.example}"
        raise HLError(msg, self.lineno, hint)

    def expect(self, w):
        if not self.accept(w):
            t = self.peek()
            if t is None:
                self.fail(f'The line ended too early; I expected "{w}" here')
            self.fail(f'I expected "{w}" here but found "{self.show(t)}"')

    def end(self):
        t = self.peek()
        if t is not None:
            hint = None
            if t.kind == "OP" and t.value == "(" and self.i > 0 and self.toks[self.i - 1].kind == "WORD":
                hint = for_word(self.toks[self.i - 1].value) or ('HL doesn\'t put brackets after a name to use it. To use a function, write: '
                        'name with value.  Brackets are only for calculations like (a + b) * 2.')
            self.fail(f'I didn\'t expect "{self.show(t)}" here', hint)

    def name(self):
        t = self.peek()
        if t is None:
            self.fail("The line ended too early; I expected a name here")
        if t.kind != "WORD":
            self.fail(f'I expected a name here but found "{self.show(t)}"')
        if t.value in RESERVED:
            self.fail(f'"{t.value}" is a word HL already uses, so it can\'t be a name',
                      hint=f'Pick another name, for example "my_{t.value}".')
        self.i += 1
        return t.value

    # ---- blocks and statements -----------------------------------------
    def load(self, ln):
        self.toks, self.i = ln.toks, 0
        self.lineno, self.level = ln.no, ln.indent

    def parse_program(self):
        return self.parse_block(0)

    def parse_block(self, level):
        stmts = []
        while self.pos < len(self.lines):
            ln = self.lines[self.pos]
            if ln.indent < level:
                break
            if ln.indent > level:
                raise HLError("This line is indented more than it should be.", ln.no,
                              hint="Only indent lines that belong under if, repeat, for each, define or try.")
            stmts.append(self.parse_statement())
        return stmts

    def body(self, lvl):
        if self.pos >= len(self.lines) or self.lines[self.pos].indent <= lvl:
            raise HLError("I expected an indented block under this line.", self.lineno,
                          hint="Indent the lines that belong to it by 4 spaces.")
        if self.lines[self.pos].indent != lvl + 1:
            raise HLError("This line is indented too far.", self.lines[self.pos].no,
                          hint="Indent by exactly 4 spaces (one level) under the line above.")
        return self.parse_block(lvl + 1)

    def loop_body(self, lvl):
        self.in_loop += 1
        try:
            return self.body(lvl)
        finally:
            self.in_loop -= 1

    def parse_statement(self):
        ln = self.lines[self.pos]
        self.pos += 1
        self.load(ln)
        self.example = None
        t = self.toks[0]
        if t.kind != "WORD":
            self.fail(f'A line can\'t start with "{self.show(t)}"',
                      hint="Lines start with a word like say, set, if or repeat.")
        w = t.value
        if w == "otherwise":
            self.fail('"otherwise" must come right after an "if" block')
        if w in STATEMENT_WORDS:
            self.i = 1
            self.example = EXAMPLES.get(w)
            return getattr(self, "st_" + w)()
        return self.st_call()

    def st_say(self):
        line = self.lineno
        e = self.expr()
        self.end()
        return ("say", line, e)

    def st_set(self):
        line = self.lineno
        name = self.name()
        self.expect("to")
        e = self.expr()
        self.end()
        return ("set", line, name, e)

    def st_change(self):
        line = self.lineno
        if self.accept("item"):
            idx = self.arith()
            self.expect("of")
            name = self.name()
            self.expect("to")
            e = self.expr()
            self.end()
            return ("changeitem", line, name, idx, e)
        name = self.name()
        self.expect("to")
        e = self.expr()
        self.end()
        return ("change", line, name, e)

    def _value_then(self, kind, word):
        line = self.lineno
        e = self.expr()
        self.expect(word)
        name = self.name()
        self.end()
        return (kind, line, e, name)

    def st_add(self):
        return self._value_then("add", "to")

    def st_subtract(self):
        return self._value_then("subtract", "from")

    def st_remove(self):
        return self._value_then("remove", "from")

    def st_ask(self):
        line = self.lineno
        numeric = self.word("number") and not self.word("and", 1)
        if numeric:
            self.i += 1
        prompt = self.arith()
        for w in ("and", "save", "it", "as"):
            self.expect(w)
        name = self.name()
        self.end()
        return ("ask", line, numeric, prompt, name)

    def cond_header(self):
        c = self.expr()
        self.accept("then")
        self.end()
        return c

    def st_if(self):
        line, lvl = self.lineno, self.level
        branches = [(self.cond_header(), self.body(lvl))]
        else_body = None
        while self.pos < len(self.lines):
            nxt = self.lines[self.pos]
            if nxt.indent != lvl or not (nxt.toks[0].kind == "WORD" and nxt.toks[0].value == "otherwise"):
                break
            self.pos += 1
            self.load(nxt)
            self.i = 1
            self.example = "otherwise if age is at least 13"
            if self.accept("if"):
                cond = self.cond_header()
                branches.append((cond, self.body(lvl)))
            else:
                self.example = "otherwise"
                self.end()
                else_body = self.body(lvl)
                break
        return ("if", line, branches, else_body)

    def st_repeat(self):
        line, lvl = self.lineno, self.level
        if self.accept("while"):
            self.example = "repeat while count is less than 3"
            cond = self.cond_header()
            return ("while", line, cond, self.loop_body(lvl))
        n = self.arith()
        self.expect("times")
        self.end()
        return ("times", line, n, self.loop_body(lvl))

    def st_for(self):
        line, lvl = self.lineno, self.level
        self.expect("each")
        name = self.name()
        self.expect("in")
        seq = self.expr()
        self.end()
        return ("for", line, name, seq, self.loop_body(lvl))

    def st_define(self):
        line, lvl = self.lineno, self.level
        name = self.name()
        params = []
        if self.accept("with"):
            params.append(self.name())
            while self.accept("and"):
                params.append(self.name())
        if len(set(params)) != len(params):
            self.fail("Two inputs of this function have the same name")
        self.end()
        saved = self.in_loop
        self.in_loop = 0
        self.defined.add(name)
        self.in_function += 1
        try:
            body = self.body(lvl)
        finally:
            self.in_function -= 1
            self.in_loop = saved
        return ("define", line, name, params, body)

    def st_give(self):
        line = self.lineno
        if not self.in_function:
            self.fail('"give back" only works inside a "define" block')
        self.expect("back")
        e = None if self.peek() is None else self.expr()
        self.end()
        return ("give", line, e)

    def _loop_word(self, kind):
        line = self.lineno
        if not self.in_loop:
            self.fail(f'"{kind}" only works inside a "repeat" or "for each" loop')
        self.end()
        return (kind, line)

    def st_stop(self):
        return self._loop_word("stop")

    def st_skip(self):
        return self._loop_word("skip")

    def st_use(self):
        line = self.lineno
        t = self.peek()
        if t is None or t.kind != "WORD":
            self.fail("I expected a module name here")
        if t.value not in MODULES:
            self.fail(f'I don\'t know a module called "{t.value}"',
                      hint=suggest(t.value, MODULES) or "Modules: " + ", ".join(MODULES))
        self.i += 1
        self.end()
        return ("use", line, t.value)

    def st_write(self):
        line = self.lineno
        value = self.expr()
        self.expect("to")
        self.expect("file")
        path = self.expr()
        self.end()
        return ("write", line, value, path)

    def st_try(self):
        line, lvl = self.lineno, self.level
        self.end()
        body = self.body(lvl)
        nxt = self.lines[self.pos] if self.pos < len(self.lines) else None
        ok = (nxt is not None and nxt.indent == lvl and
              [t.value for t in nxt.toks] == ["if", "that", "fails"])
        if not ok:
            raise HLError('A "try" block needs an "if that fails" block right after it.', line,
                          hint="Example:\n    try\n        say 10 / 0\n    if that fails\n        say \"Oops\"")
        self.pos += 1
        self.load(nxt)
        fail_body = self.body(lvl)
        return ("try", line, body, fail_body)

    def st_call(self):
        line = self.lineno
        first = self.toks[0].value
        if first not in self.defined and not self.word("with", 1):
            hint = for_word(first)
            if hint:
                self.fail(f'I don\'t understand "{first}" at the start of a line', hint)
        name = self.name()
        if self.peek() is None:
            return ("callstmt", line, ("call", name, []))
        if self.word("with"):
            self.i += 1
            args = self.call_args()
            self.end()
            return ("callstmt", line, ("call", name, args))
        self.fail(f'I don\'t understand "{name}" at the start of a line',
                  hint=for_word(name) or suggest(name, STATEMENT_WORDS) or
                  "Lines start with a word like say, set, change, if, repeat or define.")

    def call_args(self):
        args = [self.arith()]
        while self.accept("and"):
            args.append(self.arith())
        return args

    # ---- expressions -----------------------------------------------------
    def expr(self):
        left = self.and_()
        while self.accept("or"):
            left = ("or", left, self.and_())
        return left

    def and_(self):
        left = self.not_()
        while self.accept("and"):
            left = ("and", left, self.not_())
        return left

    def not_(self):
        if self.accept("not"):
            return ("not", self.not_())
        return self.cmp()

    def cmp(self):
        left = self.arith()
        if self.accept("contains"):
            return ("contains", left, self.arith())
        if not self.accept("is"):
            return left
        negate = self.accept("not")
        if self.words("less", "than"):
            op, self.i = "lt", self.i + 2
        elif self.words("greater", "than"):
            op, self.i = "gt", self.i + 2
        elif self.words("at", "least"):
            op, self.i = "ge", self.i + 2
        elif self.words("at", "most"):
            op, self.i = "le", self.i + 2
        else:
            op = "eq"
        node = ("cmp", op, left, self.arith())
        return ("not", node) if negate else node

    def arith(self):
        left = self.term()
        while True:
            t = self.peek()
            if t is None:
                break
            if (t.kind == "OP" and t.value in "+-") or (t.kind == "WORD" and t.value in ("plus", "minus")):
                op = "+" if t.value in ("+", "plus") else "-"
                self.i += 1
                left = ("bin", op, left, self.term())
            else:
                break
        return left

    def term(self):
        left = self.unary()
        while True:
            t = self.peek()
            if t is None:
                break
            if t.kind == "OP" and t.value in "*/%":
                op = t.value
                self.i += 1
            elif t.kind == "WORD" and t.value == "times" and self.peek(1) is not None:
                op = "*"
                self.i += 1
            elif self.words("divided", "by"):
                op = "/"
                self.i += 2
            elif t.kind == "WORD" and t.value == "mod":
                op = "%"
                self.i += 1
            elif self.words("to", "the", "power", "of"):
                op = "**"
                self.i += 4
            else:
                break
            left = ("bin", op, left, self.unary())
        return left

    def unary(self):
        t = self.peek()
        if t is not None and t.kind == "OP" and t.value == "-":
            self.i += 1
            return ("neg", self.unary())
        return self.factor()

    def factor(self):
        t = self.peek()
        if t is None:
            self.fail("The line ended too early; I expected a value here")
        if t.kind == "NUM":
            self.i += 1
            return ("lit", t.value)
        if t.kind == "STR":
            self.i += 1
            return self.string_node(t)
        if t.kind == "OP":
            if t.value == "(":
                self.i += 1
                e = self.expr()
                n = self.peek()
                if n is None or n.kind != "OP" or n.value != ")":
                    self.fail('I expected ")" to close the bracket')
                self.i += 1
                return e
            self.fail(f'I expected a value here but found "{t.value}"')
        w = t.value
        if w in ("yes", "no"):
            self.i += 1
            return ("lit", w == "yes")
        if w == "nothing":
            self.i += 1
            return ("lit", None)
        if w == "list" and self.word("of", 1):
            self.i += 2
            items = [self.arith()]
            while self.peek() is not None and self.peek().kind == "OP" and self.peek().value == ",":
                self.i += 1
                items.append(self.arith())
            return ("list", items)
        if w == "empty" and self.word("list", 1):
            self.i += 2
            return ("list", [])
        if w == "item":
            self.i += 1
            idx = self.arith()
            self.expect("of")
            return ("item", idx, self.factor())
        if self.words("how", "many", "items", "in"):
            self.i += 4
            return ("fn", "length", [self.factor()])
        if self.words("random", "number", "from"):
            self.i += 3
            a = self.arith()
            self.expect("to")
            return ("fn", "random", [a, self.arith()])
        if self.words("random", "item", "from"):
            self.i += 3
            return ("fn", "pick", [self.factor()])
        for word, joiner in (("split", "by"), ("join", "by")):
            if self.word(word) and self.ahead(joiner):
                self.i += 1
                first = self.arith()
                self.expect(joiner)
                return ("fn", word, [first, self.arith()])
        if self.word("replace") and self.ahead("by") and self.ahead("in"):
            self.i += 1
            old = self.arith()
            self.expect("by")
            new = self.arith()
            self.expect("in")
            return ("fn", "replace", [old, new, self.arith()])
        for phrase, fname in PREFIXES:
            if self.words(*phrase):
                self.i += len(phrase)
                if fname in ("today", "now"):
                    return ("fn", fname, [])
                return ("fn", fname, [self.unary()])
        if w in RESERVED:
            self.fail(f'I expected a value here but found "{w}"')
        if self.word("with", 1):
            self.i += 2
            return ("call", w, self.call_args())
        self.i += 1
        return ("var", w)

    def string_node(self, t):
        parts = []
        for kind, val in t.value:
            if kind == "t":
                parts.append(val)
                continue
            toks = tokenize(val, self.lineno)
            if not toks:
                self.fail("This text has an empty { } in it",
                          hint='Put a name or calculation inside, like "Hello {name}".')
            sub = Parser()
            sub.toks, sub.lineno = toks, self.lineno
            e = sub.expr()
            if sub.peek() is not None:
                self.fail(f'I didn\'t understand "{val}" inside the text',
                          hint='Inside { } write a name or a calculation, like {age + 1}.')
            parts.append(e)
        if all(isinstance(p, str) for p in parts):
            return ("lit", "".join(parts))
        return ("str", parts)


def parse(source_lines):
    return Parser(source_lines).parse_program()


def parse_expression(src):
    p = Parser()
    p.toks = tokenize(src, 0)
    e = p.expr()
    if p.peek() is not None:
        raise HLError("That isn't a complete value.")
    return e

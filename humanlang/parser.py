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
    (("file", "exists"), "fileexists"),
    (("sum", "of"), "sum"),
    (("largest", "of"), "largest"),
    (("smallest", "of"), "smallest"),
    (("sorted", "of"), "sorted"),
    (("keys", "of"), "keys"),
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
    "record": 'set person to record with name "Ann" and age 30',
    "fail": 'fail with "That is not allowed"',
}

VALUE_WORDS = ("yes", "no", "nothing", "list", "item")


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
        self.declared = set()  # every name made with "define", anywhere in the program
        self.warnings = []  # (line, message, hint): things that work but are likely not what was meant

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

    def value_start(self, k=1):
        """Could a value begin at the token k places ahead? (used to recognise phrases by context)"""
        t = self.peek(k)
        if t is None:
            return False
        if t.kind in ("NUM", "STR"):
            return True
        if t.kind == "OP":
            return t.value in ("(", "-")
        return t.kind == "WORD" and (t.value in VALUE_WORDS or t.value not in RESERVED)

    def pair_ahead(self, firsts, second):
        """Is one of the words `firsts` followed by `second` later on this line? Gives back the word."""
        for j in range(self.i + 1, len(self.toks) - 1):
            a, b = self.toks[j], self.toks[j + 1]
            if a.kind == "WORD" and a.value in firsts and b.kind == "WORD" and b.value == second:
                return a.value
        return None

    def field_ahead(self):
        """Is this "field KEY of ..." (KEY a word, or a calculation in brackets)? The word "field" is not reserved."""
        if not self.word("field"):
            return False
        t = self.peek(1)
        if t is None:
            return False
        if t.kind == "WORD":
            return t.value not in ("of", "to", "and") and self.word("of", 2)
        if t.kind == "OP" and t.value == "(":
            depth = 0
            for j in range(self.i + 1, len(self.toks)):
                tj = self.toks[j]
                if tj.kind == "OP" and tj.value == "(":
                    depth += 1
                elif tj.kind == "OP" and tj.value == ")":
                    depth -= 1
                    if depth == 0:
                        nxt = self.toks[j + 1] if j + 1 < len(self.toks) else None
                        return nxt is not None and nxt.kind == "WORD" and nxt.value == "of"
        return False

    def field_key(self):
        """The name of a field: a plain word, or a calculation in brackets, like (column)."""
        t = self.peek()
        if t is not None and t.kind == "WORD":
            self.i += 1
            return ("lit", t.value)
        if t is not None and t.kind == "OP" and t.value == "(":
            self.i += 1
            e = self.expr()
            if not (self.peek() is not None and self.peek().kind == "OP" and self.peek().value == ")"):
                self.fail('I expected ")" to close the bracket')
            self.i += 1
            return e
        self.fail("I expected the name of a field here", hint="Example: field name of person")

    def place(self):
        """A variable, item N of a place, or field KEY of a place (so things inside things can be changed in place)."""
        if self.accept("item"):
            idx = self.arith()
            self.expect("of")
            return ("pitem", idx, self.place())
        if self.field_ahead():
            self.i += 1
            key = self.field_key()
            self.expect("of")
            return ("pfield", key, self.place())
        return self.name()

    def wrapped(self, a, b):
        """Are the tokens from a to b one bracketed group, like (2 + 1)?"""
        t = self.toks
        if not (t[a].kind == "OP" and t[a].value == "("):
            return False
        depth = 0
        for j in range(a, b):
            if t[j].kind == "OP" and t[j].value == "(":
                depth += 1
            elif t[j].kind == "OP" and t[j].value == ")":
                depth -= 1
                if depth == 0:
                    return j == b - 1
        return False

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
        for ln in self.lines:
            t = ln.toks
            if len(t) > 1 and t[0].kind == "WORD" and t[0].value == "define" and t[1].kind == "WORD":
                self.declared.add(t[1].value)
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
        if w == "fail" and "fail" not in self.declared and self.word("with", 1):
            self.i = 1
            self.example = EXAMPLES["fail"]
            return self.st_fail()
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

    def st_fail(self):
        line = self.lineno
        self.expect("with")
        e = self.expr()
        self.end()
        return ("fail", line, e)

    def st_set(self):
        line = self.lineno
        if self.field_ahead():
            self.i += 1
            key = self.field_key()
            self.expect("of")
            target = self.place()
            self.expect("to")
            e = self.expr()
            self.end()
            return ("setfield", line, target, key, e)
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
            name = self.place()
            self.expect("to")
            e = self.expr()
            self.end()
            return ("changeitem", line, name, idx, e)
        if self.field_ahead():
            self.i += 1
            key = self.field_key()
            self.expect("of")
            target = self.place()
            self.expect("to")
            e = self.expr()
            self.end()
            return ("changefield", line, target, key, e)
        name = self.name()
        self.expect("to")
        e = self.expr()
        self.end()
        return ("change", line, name, e)

    def _value_then(self, kind, word):
        line = self.lineno
        e = self.expr()
        self.expect(word)
        if kind == "add" and self.word("file") and self.value_start(1):
            self.i += 1
            path = self.expr()
            self.end()
            return ("append", line, e, path)
        target = self.place()
        self.end()
        if isinstance(target, str):
            return (kind, line, e, target)
        return (kind + "place", line, e, target)

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
        if self.words("the", "program"):
            line = self.lineno
            self.i += 2
            self.end()
            return ("exit", line)
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
            args = self.call_args(name)
            self.end()
            return ("callstmt", line, ("call", name, args))
        self.fail(f'I don\'t understand "{name}" at the start of a line',
                  hint=for_word(name) or suggest(name, STATEMENT_WORDS) or
                  "Lines start with a word like say, set, change, if, repeat or define.")

    def call_args(self, name):
        args = [self.call_arg(name)]
        while self.accept("and"):
            args.append(self.call_arg(name))
        return args

    def call_arg(self, name):
        start = self.i
        node = self.arith()
        if node[0] == "bin" and not self.wrapped(start, self.i):
            text = " ".join(self.show(t) for t in self.toks[start:self.i])
            self.warnings.append((
                self.lineno,
                f'"{name} with {text}" gives the whole calculation "{text}" to {name} as its input.',
                f'Put brackets to show what you mean: "{name} with ({text})". '
                f'If you wanted to calculate after the call, write "({name} with ...) + ...". '
                f"Without brackets this will become an error in a future version."))
        return node

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
        if self.words("has", "field") and self.peek(2) is not None:
            self.i += 2
            return ("hasfield", left, self.field_key())
        if self.accept("contains"):
            return ("contains", left, self.arith())
        if not self.accept("is"):
            return left
        negate = self.accept("not")
        kind = self.peek(1)
        if (self.word("a") and kind is not None and kind.kind == "WORD"
                and kind.value in ("number", "text", "list", "record") and not self.word("of", 2)):
            self.i += 2
            node = ("typeis", kind.value, left)
            return ("not", node) if negate else node
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
        if w == "empty" and self.word("record", 1):
            self.i += 2
            return ("record", [])
        if w == "record" and self.word("with", 1) and "record" not in self.declared:
            return self.record_literal()
        if self.field_ahead():
            self.i += 1
            key = self.field_key()
            self.expect("of")
            return ("field", key, self.factor())
        if w == "item":
            self.i += 1
            idx = self.arith()
            self.expect("of")
            return ("item", idx, self.factor())
        if w in ("first", "last") and self.value_start(1):
            kind = self.pair_ahead(("letters", "items"), "of")
            if kind:
                self.i += 1
                n = self.arith()
                self.expect(kind)
                self.expect("of")
                return ("fn", w, [n, self.unary(), ("lit", kind)])
        if w in ("letters", "items") and self.value_start(1) and self.ahead("to") and self.ahead("of"):
            self.i += 1
            a = self.arith()
            self.expect("to")
            b = self.arith()
            self.expect("of")
            return ("fn", "slice", [a, b, self.unary(), ("lit", w)])
        if w == "find" and self.value_start(1) and self.ahead("in"):
            self.i += 1
            what = self.arith()
            self.expect("in")
            return ("fn", "find", [what, self.unary()])
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
                arg = self.unary()
                if fname == "sorted" and self.words("by", "field"):
                    self.i += 2
                    return ("fn", "sortby", [arg, self.field_key()])
                return ("fn", fname, [arg])
        if w in RESERVED:
            self.fail(f'I expected a value here but found "{w}"')
        if self.word("with", 1):
            self.i += 2
            return ("call", w, self.call_args(w))
        self.i += 1
        return ("var", w)

    def record_literal(self):
        """record with name "Ann" and age 30"""
        self.i += 2
        pairs, seen = [], set()
        while True:
            t = self.peek()
            if t is None or t.kind != "WORD" or t.value == "and":
                self.fail("I expected the name of a field here",
                          hint='Example: record with name "Ann" and age 30')
            if t.value in seen:
                self.fail(f'The field "{t.value}" is written twice in this record')
            seen.add(t.value)
            self.i += 1
            pairs.append((t.value, self.arith()))
            if not self.accept("and"):
                break
        return ("record", pairs)

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
            sub.warnings, sub.defined, sub.declared = self.warnings, self.defined, self.declared
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


def parse_with_warnings(source_lines):
    """Gives back (statements, warnings); a warning is (line, message, hint)."""
    p = Parser(source_lines)
    stmts = p.parse_program()
    return stmts, p.warnings


def parse_expression(src):
    p = Parser()
    p.toks = tokenize(src, 0)
    e = p.expr()
    if p.peek() is not None:
        raise HLError("That isn't a complete value.")
    return e

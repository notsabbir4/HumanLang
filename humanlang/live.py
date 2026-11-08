"""Live pages: a page that reacts when someone clicks a button or types in a box.

    define total as 0
    show a page titled "Adder"
        put an input called amount with hint "A number"
        put a button "Add"
        put a text "Total: {total}"
    when the button "Add" is clicked
        change total to total + the number in amount

How it works: the program runs once and shows the page. After that, each click (or change) runs the matching
"when" block, and then the page's own lines run AGAIN with the new values, so the page always shows the latest.
This file reads the "when" lines (a Parser mixin) and runs them (an Interpreter mixin).
"""
from decimal import Decimal, InvalidOperation

EXAMPLE = 'when the button "Add" is clicked\n    change total to total + the number in amount'


class LiveParser:
    def st_when(self):
        line, lvl = self.lineno, self.level
        self.example = EXAMPLE
        self.expect("the")
        if self.accept("button"):
            kind = "click"
        elif self.accept("input") or self.accept("box"):
            kind = "change"
        else:
            self.fail('After "when the" I expected "button" or "input", like: when the button "Add" is clicked')
        if self.peek() is None:
            self.fail("I expected the button's words in quotes, or the name of the input")
        key = self.arith() if kind == "click" else ("lit", self.name())
        if kind == "click":
            self.expect("is")
            self.expect("clicked")
        else:
            self.expect("changes")
        self.end()
        return ("when", line, kind, key, self.body(lvl))

    def live_factor(self):
        """the text in NAME   |   the number in NAME"""
        if self.word("the") and (self.word("text", 1) or self.word("number", 1)) and self.word("in", 2) \
                and self.peek(1).value not in self.declared:
            which = self.peek(1).value
            self.i += 3
            return ("inputvalue", which, self.name())
        return None


class LiveRun:
    live_page = None  # (the page statement, where it ran): run again after every click
    live_handlers = None
    live_values = None

    def live_init(self):
        self.live_handlers = []
        self.live_values = {}
        self.live_page = None

    def x_when(self, s, env):
        _, line, kind, key, body = s
        k = self.fmt(self.ev(key, env))
        self.live_handlers.append({"kind": kind, "key": k, "body": body, "line": line, "env": env})

    def e_inputvalue(self, n, env):
        _, which, name = n
        if name not in self.design_names and name not in self.live_values:
            raise self.err(f'There is no input called "{name}" on the page.',
                           f'Make it with: put an input called {name}')
        text = str(self.live_values.get(name, ""))
        if which == "text":
            return text
        try:
            v = Decimal(text.strip().replace(",", "."))
            if not v.is_finite():
                raise InvalidOperation
        except InvalidOperation:
            raise self.err(f'The input "{name}" holds "{text}", which is not a number.',
                           'Catch that with: try ... if that fails ...  (or ask for the text and check it first)')
        return self.norm(v) if hasattr(self, "norm") else v

    def live_keys(self):
        """What the page should tell us about: {"click": [button words/names], "change": [input names]}"""
        out = {"click": [], "change": []}
        for h in self.live_handlers:
            out[h["kind"]].append(h["key"])
        return out

    def live_render(self):
        """Run the page's lines again; returns the new page (a dict) or None when the program showed no page."""
        if self.live_page is None:
            return None
        stmt, env = self.live_page
        keep = self.designs[:]
        self.designs = []
        self.design_stack = []
        try:
            self.x_page(stmt, env, remember=False)
            return self.designs[-1]
        finally:
            self.designs = keep[:-1] + self.designs if keep else self.designs

    def live_event(self, kind, name, text, values):
        """Someone clicked a button (kind "click", with its name and words) or changed an input. Run what matches."""
        from .interpreter import Env, StopSignal
        self.live_values = {str(k): str(v) for k, v in (values or {}).items()}
        for h in self.live_handlers:
            if h["kind"] != kind or h["key"] not in (name, text):
                continue
            self.set_time_limit(5)
            self.line = h["line"]
            try:
                self.exec_block(h["body"], Env(h["env"]))
            except StopSignal:
                pass
        return self.live_render()

import glob
import os
import sys
import threading
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

sys.setrecursionlimit(50000)  # the `hl` command does this too, in a big-stack thread


def in_big_stack(fn):
    """Run fn on a thread with a large stack, as the `hl` command does (older Pythons need it for deep recursion)."""
    box = {}

    def target():
        try:
            box["value"] = fn()
        except BaseException as e:  # hand every outcome back to the test
            box["error"] = e

    old_limit = sys.getrecursionlimit()
    t = None
    try:
        for megabytes in (256, 64, 16, 0):  # some systems refuse a huge stack, so step down
            try:
                threading.stack_size(megabytes * 1024 * 1024)
                t = threading.Thread(target=target)
                t.start()
                break
            except (ValueError, RuntimeError):
                t = None
        if t is None:
            target()
        else:
            t.join()
    finally:
        threading.stack_size(0)
        sys.setrecursionlimit(old_limit)
    if "error" in box:
        raise box["error"]
    return box["value"]


def run(src, inputs=()):
    out, answers = [], list(inputs)

    def inp(prompt):
        if not answers:
            raise EOFError
        return answers.pop(0)

    Interpreter(out=out.append, inp=inp).run(src)
    return "".join(out)


def error_of(src):
    try:
        run(src)
    except HLError as e:
        return e.format(src.splitlines())
    raise AssertionError("expected an error")


class Basics(unittest.TestCase):
    def test_say_and_math(self):
        self.assertEqual(run('say "Hello"\nsay 2 plus 3 times 4\nsay (2 + 3) * 4\nsay 10 / 4\nsay 7 mod 3'),
                         "Hello\n14\n20\n2.5\n1\n")

    def test_float_display(self):
        self.assertEqual(run("say 0.1 + 0.2"), "0.3\n")

    def test_interpolation(self):
        self.assertEqual(run('set name to "Sam"\nset age to 20\nsay "Hi {name}, {age + 1}!"'), "Hi Sam, 21!\n")

    def test_booleans_and_nothing(self):
        self.assertEqual(run("say yes\nsay no\nsay nothing"), "yes\nno\nnothing\n")

    def test_comments_and_blank_lines(self):
        self.assertEqual(run("note: hi\n\nsay 1\n"), "1\n")

    def test_escapes(self):
        self.assertEqual(run('say "a\\tb \\"q\\" \\{x\\}"'), 'a\tb "q" {x}\n')


class Control(unittest.TestCase):
    def test_if_chain(self):
        src = ('set age to {}\nif age is at least 18\n    say "Adult"\n'
               'otherwise if age is at least 13\n    say "Teen"\notherwise\n    say "Child"')
        self.assertEqual(run(src.format(20)), "Adult\n")
        self.assertEqual(run(src.format(15)), "Teen\n")
        self.assertEqual(run(src.format(5)), "Child\n")

    def test_comparisons(self):
        self.assertEqual(run("say 3 is 3\nsay 3 is not 4\nsay 3 is at most 3\nsay 2 is greater than 3\n"
                             'say "a" is less than "b"'), "yes\nyes\nyes\nno\nyes\n")

    def test_logic(self):
        self.assertEqual(run("say yes and no\nsay yes or no\nsay not no\nsay 1 is 1 and 2 is 2"),
                         "no\nyes\nyes\nyes\n")

    def test_loops_stop_skip(self):
        src = ("set n to 0\nrepeat 10 times\n    add 1 to n\n    if n is 3\n        skip\n"
               "    if n is 6\n        stop\n    say n")
        self.assertEqual(run(src), "1\n2\n4\n5\n")

    def test_while(self):
        self.assertEqual(run("set c to 0\nrepeat while c is less than 3\n    add 1 to c\nsay c"), "3\n")

    def test_for_each_text(self):
        self.assertEqual(run('for each ch in "ab"\n    say ch'), "a\nb\n")

    def test_try(self):
        self.assertEqual(run('try\n    say 1 / 0\nif that fails\n    say "bad: {problem}"'),
                         "bad: You can't divide by zero.\n")


class Lists(unittest.TestCase):
    def test_list_ops(self):
        src = ('set c to list of "a", "b"\nadd "c" to c\nsay c\nsay item 2 of c\n'
               'say how many items in c\nchange item 1 of c to "z"\nremove "b" from c\nsay c\nsay empty list')
        self.assertEqual(run(src), "list of a, b, c\nb\n3\nlist of z, c\nempty list\n")

    def test_lists_are_copied(self):
        self.assertEqual(run("set a to list of 1\nset b to a\nadd 2 to b\nsay a\nsay b"),
                         "list of 1\nlist of 1, 2\n")

    def test_item_out_of_range(self):
        self.assertIn("only 2 items", error_of("set c to list of 1, 2\nsay item 3 of c"))


class Functions(unittest.TestCase):
    def test_define_and_call(self):
        src = "define add_two with a and b\n    give back a + b\nset t to add_two with 2 and 3\nsay t\nsay add_two with 1 and (add_two with 2 and 3)"
        self.assertEqual(run(src), "5\n6\n")

    def test_recursion(self):
        src = "define fact with n\n    if n is at most 1\n        give back 1\n    give back n * fact with (n - 1)\nsay fact with 10"
        self.assertEqual(run(src), "3628800\n")

    def test_no_params_and_statement_call(self):
        self.assertEqual(run('define hi\n    say "hi"\nhi\nhi'), "hi\nhi\n")

    def test_locals_do_not_leak(self):
        err = error_of("define f\n    set secret to 1\nf\nsay secret")
        self.assertIn('I don\'t know "secret"', err)

    def test_change_outer_variable(self):
        self.assertEqual(run("set t to 0\ndefine bump\n    add 1 to t\nbump\nbump\nsay t"), "2\n")

    def test_runaway_recursion(self):
        err = in_big_stack(lambda: error_of("define f with n\n    give back f with n\nf with 1"))
        self.assertIn("kept calling itself", err)

    def test_wrong_arg_count(self):
        self.assertIn("needs 2 values (a and b), but you gave 1",
                      error_of("define f with a and b\n    give back a\nf with 1"))


class Input(unittest.TestCase):
    def test_ask_text_and_number(self):
        src = 'ask "Name?" and save it as n\nask number "Age?" and save it as a\nsay "{n} {a + 1}"'
        self.assertEqual(run(src, ["Sam", "20"]), "Sam 21\n")

    def test_ask_number_retries(self):
        out = run('ask number "Age?" and save it as a\nsay a', ["abc", "7"])
        self.assertIn("isn't a number", out)
        self.assertTrue(out.endswith("7\n"))

    def test_random_range(self):
        with mock.patch("humanlang.interpreter.random.randint", return_value=7) as r:
            self.assertEqual(run("say random number from 1 to 10"), "7\n")
            r.assert_called_once_with(1, 10)


class Modules(unittest.TestCase):
    def test_math_needs_use(self):
        self.assertIn('use math', error_of("say square root of 9"))
        self.assertEqual(run("use math\nsay square root of 9\nsay round of 2.5\nsay absolute value of -4"),
                         "3\n3\n4\n")

    def test_files(self):
        path = os.path.join(os.path.dirname(__file__), "_tmp.txt")
        try:
            hl_path = path.replace("\\", "/")  # in HL text a backslash starts an escape; / works everywhere
            self.assertEqual(run(f'use files\nwrite "hello" to file "{hl_path}"\nsay read file "{hl_path}"'), "hello\n")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_text_functions(self):
        self.assertEqual(run('say length of "hello"\nsay uppercase of "hi"\nsay number of "5" + 1\nsay text of 5 + "x"'
                             .replace('text of 5 + "x"', '"x" + text of 5')), "5\nHI\n6\nx5\n")


class FriendlyErrors(unittest.TestCase):
    def test_unknown_variable_suggestion(self):
        err = error_of('set name to "Sam"\nsay "Hello {nmae}"')
        self.assertIn('Line 2: I don\'t know "nmae".', err)
        self.assertIn('Did you mean "name"?', err)

    def test_no_suggestion_for_longer_names_that_contain_the_word(self):
        err = error_of("define make_secret\n    set secret to 1\nmake_secret\nsay secret")
        self.assertNotIn("Did you mean", err)
        self.assertIn("set secret to", err)

    def test_change_unknown(self):
        err = error_of("set age to 1\nchange agee to 2")
        self.assertIn('Did you mean "age"?', err)

    def test_text_plus_number(self):
        err = error_of('say "5" + 1')
        self.assertIn("You tried to add a number to text", err)
        self.assertIn('number of "5"', err)

    def test_compare_text_number(self):
        self.assertIn("ask number", error_of('set a to "5"\nif a is less than 3\n    say 1'))

    def test_strict_condition(self):
        self.assertIn("expected yes or no", error_of("if 5\n    say 1"))

    def test_keyword_typo(self):
        self.assertIn('Did you mean "say"?', error_of('sya "hi"'))

    def test_missing_word_shows_example(self):
        err = error_of("set age 5")
        self.assertIn('I expected "to"', err)
        self.assertIn("Example: set age to 20", err)

    def test_reserved_name(self):
        self.assertIn("can't be a name", error_of("set list to 1"))

    def test_tabs(self):
        self.assertIn("Tabs", error_of("if yes\n\tsay 1"))

    def test_bad_indent(self):
        self.assertIn("multiple of 4", error_of("if yes\n  say 1"))

    def test_missing_block(self):
        self.assertIn("indented block", error_of("if yes\nsay 1"))

    def test_unclosed_quote(self):
        self.assertIn("closing quote", error_of('say "hi'))

    def test_equals_sign_hint(self):
        self.assertIn("is greater than", error_of("set a to 1\nif a = 1\n    say 1"))

    def test_stop_outside_loop(self):
        self.assertIn("only works inside", error_of("stop"))

    def test_give_outside_function(self):
        self.assertIn("only works inside", error_of("give back 1"))

    def test_try_needs_fail(self):
        self.assertIn("if that fails", error_of("try\n    say 1\nsay 2"))


class Examples(unittest.TestCase):
    def test_all_examples_parse(self):
        files = glob.glob(os.path.join(os.path.dirname(__file__), "..", "examples", "*.hum"))
        self.assertTrue(files)
        for f in files:
            with open(f, encoding="utf-8") as fh:
                Interpreter().check(fh.read())

    def test_guess_game(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "guess.hum")
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        with mock.patch("humanlang.interpreter.random.randint", return_value=6):
            out = run(src, ["3", "9", "6"])
        self.assertIn("Too low", out)
        self.assertIn("Too high", out)
        self.assertTrue(out.endswith("You got it!\n"))


class EdgeCases(unittest.TestCase):
    def test_empty_and_comment_only(self):
        for src in ("", "note: hi\n", "   \n\n"):
            self.assertEqual(run(src), "")

    def test_unicode_names_and_text(self):
        self.assertEqual(run('set na\u00efve to "h\u00e9llo \u2713"\nsay na\u00efve'), "h\u00e9llo \u2713\n")

    def test_crlf_line_endings(self):
        self.assertEqual(run("say 1\r\nsay 2\r\n"), "1\n2\n")

    def test_big_numbers_do_not_crash(self):
        self.assertEqual(run("say 99999999999999999999 * 99999999999999999999"), "9999999999999999999800000000000000000001\n")
        self.assertEqual(run("set x to 1\nrepeat 400 times\n    set x to x * 10.5\nsay x"), "infinity\n")

    def test_math_edges(self):
        self.assertEqual(run("say -7 mod 3\nsay -0"), "2\n0\n")
        self.assertIn("divide by zero", error_of("say 5 mod 0"))

    def test_bad_list_indexes(self):
        self.assertIn("item 0", error_of("say item 0 of list of 1"))
        self.assertIn("whole number", error_of("say item 1.5 of list of 1, 2"))
        self.assertIn("needs a list or text", error_of("say item 1 of 5"))

    def test_bad_repeat_counts(self):
        for n in ("-1", "1.5", '"a"'):
            self.assertIn("whole number of times", error_of(f"repeat {n} times\n    say 1"))

    def test_strict_types(self):
        self.assertIn("multiply numbers", error_of('say "a" * 3'))
        self.assertIn("can't add nothing", error_of("say nothing + 1"))
        self.assertIn("expected yes or no", error_of("say 1 and 2"))
        self.assertEqual(run("say yes is 1\nsay list of 1, 2 is list of 1, 2"), "no\nyes\n")

    def test_control_flow_through_try(self):
        self.assertEqual(run('repeat 3 times\n    try\n        stop\n    if that fails\n        say 1\nsay "ok"'), "ok\n")
        self.assertEqual(run("define f\n    try\n        give back 5\n    if that fails\n        give back 6\nsay f"), "5\n")

    def test_error_line_inside_function(self):
        self.assertIn("Line 2: I don't know", error_of("define f\n    say nope\nf"))

    def test_parameter_shadowing(self):
        self.assertEqual(run("define f with a\n    set a to 5\n    give back a\nset a to 1\nsay f with 2\nsay a"), "5\n1\n")

    def test_ask_with_no_input(self):
        self.assertIn("no answer to read", error_of('ask "q" and save it as x'))

    def test_deep_nesting(self):
        self.assertEqual(run('if yes\n    if yes\n        if yes\n            say "deep"'), "deep\n")

    def test_dedent_mismatch(self):
        self.assertIn("multiple of 4", error_of("if yes\n    say 1\n  say 2"))

    def test_otherwise_without_if(self):
        self.assertIn("right after an", error_of("otherwise\n    say 1"))
        self.assertIn("right after an", error_of("if no\n    say 1\notherwise\n    say 2\notherwise\n    say 3"))


class LexerParser(unittest.TestCase):
    def test_tokens(self):
        from humanlang.lexer import tokenize
        kinds = [(t.kind, t.value) for t in tokenize('set x to 3.5 + y', 1)]
        self.assertEqual(kinds, [("WORD", "set"), ("WORD", "x"), ("WORD", "to"), ("NUM", 3.5),
                                 ("OP", "+"), ("WORD", "y")])

    def test_string_parts(self):
        from humanlang.lexer import tokenize
        self.assertEqual(tokenize('"a {x} b"', 1)[0].value, [("t", "a "), ("e", "x"), ("t", " b")])

    def test_precedence_tree(self):
        from humanlang.parser import parse_expression
        self.assertEqual(parse_expression("2 + 3 * 4"),
                         ("bin", "+", ("lit", 2), ("bin", "*", ("lit", 3), ("lit", 4))))

    def test_words_equal_symbols(self):
        from humanlang.parser import parse_expression
        self.assertEqual(parse_expression("2 plus 3 times 4"), parse_expression("2 + 3 * 4"))

    def test_repeat_times_is_not_multiplication(self):
        self.assertEqual(run("repeat 2 times\n    say 1\nsay 2 times 3"), "1\n1\n6\n")

    def test_check_does_not_run(self):
        out = []
        Interpreter(out=out.append).check('say "should not print"')
        self.assertEqual(out, [])


HL = [sys.executable, "-m", "humanlang"]
ROOT = os.path.join(os.path.dirname(__file__), "..")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def cli(*args, stdin=""):
    import subprocess
    r = subprocess.run(HL + list(args), input=stdin, capture_output=True, text=True, encoding="utf-8", cwd=ROOT, timeout=60)
    return r.returncode, r.stdout, r.stderr


class GoldenPrograms(unittest.TestCase):
    """tests/programs/NAME.hum + NAME.out (+ optional NAME.in): output must match exactly."""

    def test_programs(self):
        folder = os.path.join(os.path.dirname(__file__), "programs")
        names = sorted(f[:-4] for f in os.listdir(folder) if f.endswith(".hum"))
        self.assertGreaterEqual(len(names), 5)
        for name in names:
            with self.subTest(program=name):
                stdin = read(os.path.join(folder, name + ".in")) if os.path.exists(os.path.join(folder, name + ".in")) else ""
                code, out, err = cli("run", os.path.join("tests", "programs", name + ".hum"), stdin=stdin)
                expected = read(os.path.join(folder, name + ".out"))
                self.assertEqual(out + err, expected)


class CommandLine(unittest.TestCase):
    def test_exit_codes_and_messages(self):
        self.assertEqual(cli("--version")[:2], (0, f"HumanLang {__import__('humanlang').__version__}\n"))
        code, _, err = cli("run", "nope.hum")
        self.assertEqual(code, 1)
        self.assertIn('can\'t find the file "nope.hum"', err)
        self.assertEqual(cli("run", "tests/programs/typo.hum")[0], 1)
        self.assertEqual(cli("run", "examples/hello.hum")[:2], (0, "Hello, world!\n"))

    def test_check_command(self):
        self.assertEqual(cli("check", "examples/hello.hum")[:2], (0, "No mistakes found.\n"))
        # unknown names are only found when the program runs, so `check` accepts this file
        self.assertEqual(cli("check", "tests/programs/typo.hum")[0], 0)
        code, _, err = cli("check", "tests/programs/badsyntax.hum")
        self.assertEqual(code, 1)
        self.assertIn('Did you mean "say"?', err)

    def test_repl(self):
        code, out, _ = cli(stdin='set x to 5\nx + 1\nif x is 5\n    say "five"\n\nsya 1\nexit\n')
        self.assertEqual(code, 0)
        self.assertIn("6", out)
        self.assertIn("five", out)
        self.assertIn('Did you mean "say"?', out)

    def test_deep_recursion_in_cli(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".hum", delete=False) as f:
            f.write("define down with n\n    if n is 0\n        give back 0\n    give back down with (n - 1)\nsay down with 900\n")
        try:
            self.assertEqual(cli("run", f.name)[:2], (0, "0\n"))
        finally:
            os.remove(f.name)


class StandardLibrary(unittest.TestCase):
    def test_list_math(self):
        self.assertEqual(run("use math\nset n to list of 5, 3, 9\nsay sum of n\nsay largest of n\nsay smallest of n"),
                         "17\n9\n3\n")

    def test_sorted_reversed(self):
        self.assertEqual(run('say sorted of list of 3, 1, 2\nsay reversed of "abc"\nsay sorted of list of "b", "a"'),
                         "list of 1, 2, 3\ncba\nlist of a, b\n")
        self.assertIn("not a mix", error_of('say sorted of list of 1, "a"'))

    def test_power(self):
        self.assertEqual(run("say 2 to the power of 10\nsay 2 times 3 to the power of 2\nsay 9 to the power of 0.5"),
                         "1024\n36\n3\n")
        self.assertIn("too big", error_of("say 10 to the power of 99999"))
        self.assertIn("divide by zero", error_of("say 0 to the power of -1"))
        self.assertIn("no real answer", error_of("say -8 to the power of 0.5"))

    def test_text_module(self):
        src = ('use text\nset p to split "a,b,c" by ","\nsay p\nsay join p by "-"\n'
               'say replace "l" by "L" in "hello"\nsay "[{trim of "  hi  "}]"')
        self.assertEqual(run(src), "list of a, b, c\na-b-c\nheLLo\n[hi]\n")
        self.assertIn('use text', error_of('say trim of " x "'))

    def test_split_join_still_usable_as_names(self):
        self.assertEqual(run("set split to 1\nset join to 2\nsay split + join"), "3\n")

    def test_contains(self):
        self.assertEqual(run('say "hello" contains "ell"\nsay list of 1, 2 contains 2\nsay list of 1 contains 5\n'
                             'if not "abc" contains "z"\n    say "no z"'), "yes\nyes\nno\nno z\n")
        self.assertIn('"contains" needs', error_of("say 5 contains 5"))

    def test_random_item_and_dates(self):
        self.assertEqual(run('use random\nsay random item from list of "only"'), "only\n")
        self.assertIn("use random", error_of('say random item from list of "x"'))
        out = run("use dates\nsay length of the date today\nsay length of the time now")
        self.assertEqual(out, "10\n5\n")

    def test_enormous_numbers_do_not_crash(self):
        src = "set big to 1\nrepeat 2000 times\n    set big to big * 7\nsay big / big\nsay length of text of big"
        self.assertEqual(run(src), "1\n1691\n")
        out = run("set big to 1\nrepeat 6000 times\n    set big to big * 10\nsay big")
        self.assertIn("infinity", out)
        self.assertIn("too big", error_of("set a to 10 to the power of 400\nsay a / 0.5"))


class Formatter(unittest.TestCase):
    MESSY = ('\n\nnote: hi\nset   x to   1\nif x is 1\n  say   "keep   this  "   \n\n\n\n  if yes\n      say 2\nsay   3 \t\n')

    def test_tidies_whitespace(self):
        from humanlang.formatter import format_source
        self.assertEqual(format_source(self.MESSY),
                         'note: hi\nset x to 1\nif x is 1\n    say "keep   this  "\n\n    if yes\n        say 2\nsay 3\n')

    def test_idempotent_and_meaning_preserved(self):
        from humanlang.formatter import format_source
        once = format_source(self.MESSY)
        self.assertEqual(format_source(once), once)
        self.assertIn("multiple of 4", error_of(self.MESSY))  # the messy file can't even run...
        self.assertEqual(run(once), "keep   this  \n2\n3\n")  # ...but the tidy one does

    def test_examples_already_tidy_or_equivalent(self):
        from humanlang.formatter import format_source
        for f in glob.glob(os.path.join(ROOT, "examples", "*.hum")):
            src = read(f)
            tidy = format_source(src)
            self.assertEqual(format_source(tidy), tidy, f)
            Interpreter().check(tidy)

    def test_format_command(self):
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".hum", delete=False) as f:
            f.write(self.MESSY)
        try:
            self.assertEqual(cli("format", "--check", f.name)[0], 1)
            self.assertEqual(cli("format", f.name)[0], 0)
            self.assertEqual(cli("format", "--check", f.name)[0], 0)
        finally:
            os.remove(f.name)


class Tooling(unittest.TestCase):
    def test_trace(self):
        code, out, err = cli("run", "--trace", "examples/hello.hum")
        self.assertEqual((code, out), (0, "Hello, world!\n"))
        self.assertIn('[line 1] say "Hello, world!"', err)

    def test_language_server(self):
        import json
        import subprocess
        p = subprocess.Popen(HL + ["lsp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=ROOT)

        def send(o):
            b = json.dumps(o).encode()
            p.stdin.write(b"Content-Length: %d\r\n\r\n" % len(b) + b)
            p.stdin.flush()

        def recv():
            n = 0
            while True:
                h = p.stdout.readline().strip()
                if not h:
                    break
                if h.lower().startswith(b"content-length:"):
                    n = int(h.split(b":")[1])
            return json.loads(p.stdout.read(n))

        try:
            send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            self.assertTrue(recv()["result"]["capabilities"]["documentFormattingProvider"])
            uri = "file:///t.hum"
            send({"jsonrpc": "2.0", "method": "textDocument/didOpen",
                  "params": {"textDocument": {"uri": uri, "text": 'set x to 1\nsya "hi"\n'}}})
            diag = recv()["params"]["diagnostics"]
            self.assertEqual(diag[0]["range"]["start"]["line"], 1)
            self.assertIn('Did you mean "say"?', diag[0]["message"])
            send({"jsonrpc": "2.0", "method": "textDocument/didChange",
                  "params": {"textDocument": {"uri": uri}, "contentChanges": [{"text": 'set  x to 1\nsay "hi"\n'}]}})
            self.assertEqual(recv()["params"]["diagnostics"], [])
            send({"jsonrpc": "2.0", "id": 2, "method": "textDocument/completion", "params": {"textDocument": {"uri": uri}}})
            labels = [i["label"] for i in recv()["result"]]
            self.assertIn("say", labels)
            self.assertIn("x", labels)
            send({"jsonrpc": "2.0", "id": 3, "method": "textDocument/formatting", "params": {"textDocument": {"uri": uri}}})
            self.assertEqual(recv()["result"][0]["newText"], 'set x to 1\nsay "hi"\n')
            send({"jsonrpc": "2.0", "id": 4, "method": "shutdown"})
            recv()
            send({"jsonrpc": "2.0", "method": "exit"})
            self.assertEqual(p.wait(10), 0)
        finally:
            if p.poll() is None:
                p.kill()
            p.stdin.close()
            p.stdout.close()

    def test_vscode_extension_files_are_valid(self):
        import json
        base = os.path.join(ROOT, "editors", "vscode")
        for rel in ("package.json", "language-configuration.json", "snippets/humanlang.json",
                    "syntaxes/humanlang.tmLanguage.json"):
            json.loads(read(os.path.join(base, rel)))


class FastPathsKeepMeaning(unittest.TestCase):
    """The speed-ups for plain numbers must not change what any program means."""

    def test_yes_no_are_not_numbers(self):
        self.assertIn("add", error_of("say yes + 1"))
        self.assertIn("can't compare", error_of("say yes is less than 2"))
        self.assertEqual(run("say yes is 1\nsay 1 is 1.0\nsay 2 is less than 2.5"), "no\nyes\nyes\n")

    def test_huge_plus_float_is_friendly(self):
        self.assertIn("too big", error_of("say 10 to the power of 400 + 1.5"))
        self.assertIn("too big", error_of("say 10 to the power of 400 * 1.5"))

    def test_results_stay_tidy(self):
        self.assertEqual(run("say 0.5 + 0.5\nsay 2.5 * 2\nsay 7 - 0.25\nset a to 1\nadd 0.5 to a\nadd 0.5 to a\nsay a"),
                         "1\n5\n6.75\n2\n")

    def test_lists_still_copied_by_every_path(self):
        src = ("set a to list of 1\ndefine f with x\n    add 9 to x\n    give back x\nset b to f with a\n"
               "say a\nsay b\nfor each row in list of list of 1\n    add 2 to row\n    say row")
        self.assertEqual(run(src), "list of 1\nlist of 1, 9\nlist of 1, 2\n")

    def test_loop_control_and_line_numbers(self):
        self.assertIn("Line 3:", error_of("set n to 0\nrepeat while n is less than 3\n    say missing\n    add 1 to n"))
        self.assertIn("Line 2:", error_of("set n to 1\nrepeat while n\n    add 1 to n"))
        self.assertEqual(run("for each x in list of 1, 2, 3, 4\n    if x is 2\n        skip\n    if x is 4\n        stop\n    say x"), "1\n3\n")


class MigrationHints(unittest.TestCase):
    """People who know other languages get pointed to the HL way."""

    CASES = [
        ('print "hi"', 'Example: say "Hello"'),
        ('print("hi")', "with \"say\""),
        ('Print "hi"', "with \"say\""),
        ("if yes\n    say 1\nelse\n    say 2", '"otherwise"'),
        ("if yes\n    say 1\nelif no\n    say 2", '"otherwise if"'),
        ("define f\n    return 5", '"give back"'),
        ("while yes\n    say 1", '"repeat"'),
        ("repeat 2 times\n    break", '"stop"'),
        ("repeat 2 times\n    continue", '"skip"'),
        ("function foo with a\n    say a", '"define"'),
        ("let x be 5", '"set"'),
        ("say true", '"yes" and "no"'),
        ("say False", '"yes" and "no"'),
        ("set x to null", '"nothing"'),
        ("set x to None", '"nothing"'),
        ("x = 5", "set name to value"),
        ("if 1 == 1\n    say 1", "name is value"),
        ("if 1 < 2\n    say 1", "is less than"),
        ("set a to 1 && 2", '"and", "or" and "not"'),
        ("set c to [1, 2]", "list of"),
        ("say len(list of 1)", "length of"),
        ("set s to str(5)", "text of"),
        ('say "a";', "semicolons"),
        ('say "hi" # comment', "note:"),
        ("say x.length", "dots"),
        ("say 'hi'", "double quotes"),
        ('Say "hi"', "all lowercase"),
        ("import math", '"use"'),
    ]

    def test_each_mistake_gets_its_hint(self):
        for src, expected in self.CASES:
            with self.subTest(src=src):
                self.assertIn(expected, error_of(src))

    def test_your_own_function_may_use_those_names(self):
        self.assertEqual(run('define print with x\n    say x\nprint with "ok"'), "ok\n")
        self.assertEqual(run('define echo\n    say "yo"\necho'), "yo\n")

    def test_variables_may_use_those_words_as_names(self):
        self.assertEqual(run('set input to 1\nset length to 2\nsay input + length'), "3\n")


class BigStackFallback(unittest.TestCase):
    def test_refused_stack_sizes_step_down(self):
        from humanlang import cli
        sizes = []

        def fake_stack_size(n=0):
            sizes.append(n)
            if n >= 64 * 1024 * 1024:
                raise RuntimeError("size not valid")
            return 0

        with mock.patch.object(cli.threading, "stack_size", fake_stack_size):
            self.assertEqual(cli.run_big(lambda: 7), 7)
        self.assertEqual(sizes[:3], [256 * 1024 * 1024, 64 * 1024 * 1024, 16 * 1024 * 1024])

    def test_no_thread_at_all_still_runs(self):
        from humanlang import cli

        def refuse(n=0):
            raise ValueError("no")

        with mock.patch.object(cli.threading, "stack_size", refuse):
            self.assertEqual(cli.run_big(lambda: 9), 9)
        sys.setrecursionlimit(50000)  # run_big lowered it; the rest of the tests expect the high one


class FuzzSmoke(unittest.TestCase):
    def test_fuzzer_finds_no_crashes(self):
        import subprocess
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "fuzz.py"), "1500", "99"],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()

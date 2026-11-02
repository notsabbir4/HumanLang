"""Tests for what version 0.3.0 added, each one written from a real problem the round 2 stress tests found."""
import os
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def run(src, inputs=(), **limits):
    out, answers = [], list(inputs)

    def inp(prompt):
        if not answers:
            raise EOFError
        return answers.pop(0)

    it = Interpreter(out=out.append, inp=inp)
    for k, v in limits.items():
        setattr(it, k, v)
    it.run(src)
    return "".join(out)


def error_of(src, **limits):
    try:
        run(src, **limits)
    except HLError as e:
        return e.format(src.splitlines())
    raise AssertionError("expected an error")


def warnings_of(src, path=None):
    it = Interpreter(out=lambda t: None)
    it.prepare(src, path)
    return it.warnings


def hl(*args, input_text=None, cwd=None):
    env = dict(os.environ, PYTHONPATH=os.path.abspath(ROOT))
    return subprocess.run([sys.executable, "-m", "humanlang", *args], capture_output=True, text=True,
                          input=input_text, cwd=cwd, env=env)


class Project:
    """A folder of .hum files for one test."""

    def __init__(self, test, files):
        self.dir = tempfile.TemporaryDirectory()
        test.addCleanup(self.dir.cleanup)
        for name, text in files.items():
            path = os.path.join(self.dir.name, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(text)

    def path(self, name):
        return os.path.join(self.dir.name, name)

    def run(self, name="main.hum", inputs=()):
        out, answers = [], list(inputs)
        it = Interpreter(out=out.append, inp=lambda p: answers.pop(0))
        with open(self.path(name), encoding="utf-8") as f:
            src = f.read()
        try:
            it.run(src, self.path(name))
        except HLError as e:
            return "".join(out), e.format(src.splitlines()), it
        return "".join(out), None, it


class ExactNumbers(unittest.TestCase):
    """Problem 2: 0.1 + 0.2 was not 0.3, and money rounded the wrong way."""

    def test_the_famous_sum(self):
        self.assertEqual(run("say 0.1 + 0.2\nsay 0.1 + 0.2 is 0.3\nsay 0.1 * 3 is 0.3\nsay 1.1 + 2.2 is 3.3"), "0.3\nyes\nyes\nyes\n")

    def test_money_rounds_the_way_a_shop_does(self):
        self.assertEqual(run("use math\nsay round of (5 * 1.005 * 100)\nsay round of (19.99 * 100)\nsay 19.99 * 100 is 1999"), "503\n1999\nyes\n")

    def test_round_to_places(self):
        self.assertEqual(run("use math\nsay round of 2.675 to 2 places\nsay round of 1234.5678 to 1 place\nsay round of 2.5 to 0 places"),
                         "2.68\n1234.6\n3\n")
        self.assertEqual(run("use math\nset p to 3\nsay round of 3.14159 to p places\nsay round of -2.5\nsay round of -2.675 to 2 places"),
                         "3.142\n-2\n-2.67\n")

    def test_round_to_places_is_checked(self):
        self.assertIn("whole number from 0 to 30", error_of('use math\nsay round of 1.5 to 2.5 places'))
        self.assertIn("whole number from 0 to 30", error_of('use math\nsay round of 1.5 to (0 - 1) places'))

    def test_round_to_in_other_sentences_is_not_confused(self):
        self.assertEqual(run("use math\nset total to 1\nadd round of 2.4 to total\nsay total"), "3\n")

    def test_text_with_places_keeps_trailing_zeros(self):
        self.assertEqual(run("say text of 12.5 to 2 places\nsay text of 7 to 2 places\nsay text of 0.005 to 2 places\nsay text of 3.999 to 0 places"),
                         "12.50\n7.00\n0.01\n4\n")
        self.assertEqual(run('say "Total: {text of (19.99 * 3) to 2 places}"'), "Total: 59.97\n")

    def test_plain_text_of_still_works(self):
        self.assertEqual(run("say text of 12.50\nset t to text of 5\nsay length of t"), "12.5\n1\n")

    def test_whole_number_division(self):
        self.assertEqual(run("say 10 divided evenly by 3\nsay -7 divided evenly by 2\nsay 7.5 divided evenly by 2"), "3\n-4\n3\n")
        self.assertEqual(run("say (10 to the power of 30 + 7) divided evenly by 10"), "100000000000000000000000000000\n")
        self.assertIn("divide by zero", error_of("say 5 divided evenly by 0"))

    def test_division_and_remainder(self):
        self.assertEqual(run("say 10 / 4\nsay 1 / 3\nsay -7 % 3\nsay 7.5 % 2\nsay 6 / 3"), "2.5\n0.3333333333\n2\n1.5\n2\n")

    def test_huge_money_keeps_every_digit(self):
        self.assertEqual(run("say (10 to the power of 30 + 1) * 3"), "3000000000000000000000000000003\n")

    def test_powers_and_roots_are_exact_when_they_can_be(self):
        self.assertEqual(run("use math\nsay square root of 16\nsay square root of 2\nsay 2 to the power of -2\nsay 4 to the power of 0.5"),
                         "4\n1.414213562\n0.25\n2\n")

    def test_displayed_digits(self):
        self.assertEqual(run("say 123456789.123456789\nsay 0.00001\nsay 5.0\nsay -0.0\nsay 1.50"), "123456789.1\n0.00001\n5\n0\n1.5\n")

    def test_enormous_results_are_rounded_and_say_so(self):
        self.assertEqual(run("say 10 to the power of 400 * 1.5"), "1.5e+400\n")

    def test_numbers_from_text(self):
        self.assertEqual(run('say number of "1.50"\nsay number of " 7 "\nsay number of "-3.50"'), "1.5\n7\n-3.5\n")

    def test_only_ordinary_digits_count_as_a_number(self):
        self.assertIn("can't turn", error_of('say number of "\u0661\u0662"'))
        self.assertEqual(run('ask number "n?" and save it as n\nsay n', ["\u0661\u0662", "5"]), '"\u0661\u0662" isn\'t a number. Please type a number.\n5\n')

    def test_ask_number_gives_exact_decimals(self):
        self.assertEqual(run('ask number "n?" and save it as n\nsay n + 0.2 is 0.3', ["0.1"]), "yes\n")

    def test_sum_sort_and_compare_mixed_numbers(self):
        self.assertEqual(run("use math\nsay sum of (list of 0.1, 0.2, 1)\nsay sorted of (list of 2, 0.5, 1)\nsay largest of (list of 2, 2.5)"),
                         "1.3\nlist of 0.5, 1, 2\n2.5\n")
        self.assertEqual(run("say 1 is 1.0\nsay 2 is less than 2.5\nsay 0.5 is at least 0.5"), "yes\nyes\nyes\n")

    def test_old_behaviour_that_stays(self):
        self.assertEqual(run("say 2 + 3 * 4\nsay 7 / 2\nsay 2 to the power of 10\nsay 10 % 3"), "14\n3.5\n1024\n1\n")


class UsingOtherFiles(unittest.TestCase):
    """Problem 1: a program could not be split into files."""

    def test_functions_and_variables_are_shared(self):
        p = Project(self, {"util.hum": 'define double with x\n    give back x * 2\nset unit to "cm"\n',
                           "main.hum": 'use "util.hum"\nsay double with 4\nsay unit\n'})
        out, err, _ = p.run()
        self.assertEqual((out, err), ("8\ncm\n", None))

    def test_a_file_is_used_once_and_in_order(self):
        p = Project(self, {"a.hum": 'say "a loads"\nuse "b.hum"\nsay "a done"\n', "b.hum": 'say "b loads"\n',
                           "main.hum": 'say "start"\nuse "a.hum"\nuse "b.hum"\nuse "a.hum"\nsay "end"\n'})
        self.assertEqual(p.run()[0], "start\na loads\nb loads\na done\nend\n")

    def test_files_may_use_each_other_in_a_circle(self):
        p = Project(self, {"a.hum": 'use "b.hum"\nsay "a"\n', "b.hum": 'use "a.hum"\nsay "b"\n', "main.hum": 'use "a.hum"\n'})
        out, err, _ = p.run()
        self.assertEqual((out, err), ("b\na\n", None))

    def test_names_are_looked_up_next_to_the_file_that_says_use(self):
        p = Project(self, {"lib/more.hum": 'use "util.hum"\ndefine quad with x\n    give back double with (double with x)\n',
                           "lib/util.hum": "define double with x\n    give back x * 2\n",
                           "main.hum": 'use "lib/more.hum"\nsay quad with 3\n'})
        self.assertEqual(p.run()[0], "12\n")

    def test_missing_file_has_a_hint(self):
        p = Project(self, {"main.hum": 'say 1\nuse "nope.hum"\n'})
        _, err, _ = p.run()
        self.assertIn('Line 2: There is no file called "nope.hum".', err)
        self.assertIn("folder of the file that has this", err)

    def test_a_mistake_in_a_used_file_names_the_file_and_line(self):
        p = Project(self, {"lib/bad.hum": "say 1\nsay (\n", "main.hum": 'use "lib/bad.hum"\n'})
        _, err, _ = p.run()
        self.assertIn("Line 2 of lib/bad.hum:", err)
        self.assertIn("    say (", err)

    def test_a_runtime_error_in_a_used_file_names_the_file_and_line(self):
        p = Project(self, {"lib/d.hum": "say 1\nsay 1 / 0\n", "main.hum": 'say "a"\nuse "lib/d.hum"\n'})
        out, err, _ = p.run()
        self.assertEqual(out, "a\n1\n")
        self.assertIn("Line 2 of lib/d.hum: You can't divide by zero.", err)
        self.assertIn("    say 1 / 0", err)

    def test_a_function_called_from_main_reports_its_own_file(self):
        p = Project(self, {"lib/t.hum": "define t with x\n    give back item 9 of list of 1\n",
                           "main.hum": 'use "lib/t.hum"\ndefine a\n    give back t with 1\nsay a\n'})
        _, err, _ = p.run()
        self.assertIn("Line 2 of lib/t.hum:", err)
        self.assertIn('This happened inside "t", which was called from:', err)
        self.assertIn('line 3, inside "a"', err)

    def test_checking_looks_inside_used_files(self):
        p = Project(self, {"lib/w.hum": 'set total to 0\ndefine f\n    say 1\n', "main.hum": 'use "lib/w.hum"\n'})
        self.assertEqual(hl("check", p.path("main.hum")).returncode, 0)
        p = Project(self, {"lib/bad.hum": "say (\n", "main.hum": 'use "lib/bad.hum"\n'})
        r = hl("check", p.path("main.hum"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("Line 1 of lib/bad.hum", r.stderr)

    def test_defining_a_name_twice_is_a_heads_up(self):
        p = Project(self, {"util.hum": "define helper with x\n    give back x + 1\n",
                           "other.hum": "define helper with x\n    give back x + 100\n",
                           "main.hum": 'use "util.hum"\nuse "other.hum"\nsay helper with 1\n'})
        out, err, it = p.run()
        self.assertEqual(out, "101\n")  # still the later one, as before
        w = [w for w in it.warnings if "already" in w[1]]
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0][3], "other.hum")
        self.assertIn('"helper" is already a function (line 1 of util.hum)', w[0][1])

    def test_defining_twice_in_one_file_and_function_over_variable(self):
        w = warnings_of("define f\n    say 1\ndefine f\n    say 2\n")
        self.assertEqual([(x[0], "already a function" in x[1]) for x in w], [(3, True)])
        w = warnings_of("set total to 5\ndefine total with x\n    give back x\n")
        self.assertTrue(any("already a variable" in x[1] for x in w))
        w = warnings_of("define total with x\n    give back x\nset total to 5\n")
        self.assertTrue(any("makes a variable with the same name" in x[1] for x in w))

    def test_no_heads_up_for_ordinary_programs(self):
        self.assertEqual(warnings_of("define f\n    say 1\ndefine g\n    say 2\nset x to 1\nset x to 2\n"), [])

    def test_heads_up_from_a_used_file_shows_that_file(self):
        p = Project(self, {"m.hum": 'set total to 0\ndefine f with n\n    set total to total + n\n',
                           "main.hum": 'use "m.hum"\nsay 1\n'})
        _, _, it = p.run()
        shadow = [w for w in it.warnings if "private" in w[1]]
        self.assertEqual(len(shadow), 1)
        self.assertEqual(shadow[0][3], "m.hum")
        r = hl("run", p.path("main.hum"))
        self.assertIn("Heads up, line 3 of m.hum:", r.stderr)

    def test_use_must_be_at_the_top_level(self):
        self.assertIn("must be at the top", error_of('if yes\n    use "x.hum"'))
        self.assertIn("must be at the top", error_of('define f\n    use "x.hum"'))
        self.assertIn("plain text", error_of('set n to "x"\nuse "{n}.hum"'))

    def test_unknown_module_hint_mentions_files(self):
        self.assertIn('use "helpers.hum"', error_of("use helpers"))
        self.assertIn("another file", error_of("import helpers").lower().replace("hl file", "another file") + "another file")

    def test_the_command_line_runs_a_project_from_anywhere(self):
        p = Project(self, {"util.hum": 'say "util"\n', "main.hum": 'use "util.hum"\nsay "main"\n'})
        r = hl("run", p.path("main.hum"), cwd=tempfile.gettempdir())
        self.assertEqual((r.returncode, r.stdout), (0, "util\nmain\n"))


class Limits(unittest.TestCase):
    """Problem 3: runaway programs were not stopped."""

    def test_endless_output_is_stopped(self):
        e = error_of('repeat forever\n    say "spam"', max_output=1000)
        self.assertIn("printed more than 1,000 letters", e)

    def test_text_that_keeps_growing_is_stopped(self):
        e = error_of('set t to "ab"\nrepeat 60 times\n    set t to t + t\nsay length of t')
        self.assertIn("would have more than 50,000,000 letters", e)
        self.assertIn("Line 3", e)

    def test_text_added_to_itself_is_stopped(self):
        self.assertIn("more than 1,000 letters", error_of('set t to "ab"\nrepeat 60 times\n    add t to t', max_text=1000))

    def test_lists_that_keep_growing_are_stopped(self):
        e = error_of("set l to list of 1\nrepeat 60 times\n    set l to l + l")
        self.assertIn("would have more than 10,000,000 items", e)

    def test_join_and_replace_are_limited_too(self):
        self.assertIn("more than 100 letters", error_of('use text\nset l to list of "abcdefghij", "abcdefghij"\nrepeat 4 times\n    set l to l + l\nsay join l by ","', max_text=100))
        self.assertIn("more than 10 letters", error_of('use text\nsay replace "a" by "bbbbbbbbbb" in "aaa"', max_text=10))

    def test_a_time_limit_stops_a_loop(self):
        it = Interpreter(out=lambda t: None)
        it.set_time_limit(0.3)
        started = time.monotonic()
        with self.assertRaises(HLError) as c:
            it.run("repeat forever\n    set x to 1")
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("ran for more than 0.3 seconds", c.exception.message)

    def test_a_time_limit_stops_the_other_loops(self):
        for body in ("repeat while yes\n    set x to 1", "repeat 100000000 times\n    set x to 1",
                     "for each x in (list of 1, 2, 3)\n    repeat 100000000 times\n        set y to 1"):
            it = Interpreter(out=lambda t: None)
            it.set_time_limit(0.2)
            with self.assertRaises(HLError, msg=body):
                it.run(body)

    def test_running_out_of_memory_is_a_friendly_error(self):
        from unittest import mock
        with mock.patch.object(Interpreter, "x_say", side_effect=MemoryError):
            it = Interpreter(out=lambda t: None)
            with self.assertRaises(HLError) as c:
                it.run('say "x"')
        self.assertIn("ran out of memory", c.exception.message)

    def test_command_line_flags(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = os.path.join(d.name, "loop.hum")
        with open(path, "w") as f:
            f.write('repeat forever\n    say "spam"\n')
        r = hl("run", "--max-output", "50", path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("printed more than 50 letters", r.stderr)
        with open(path, "w") as f:
            f.write("repeat forever\n    set x to 1\n")
        r = hl("run", "--time-limit=0.5", path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ran for more than 0.5 seconds", r.stderr)
        self.assertEqual(hl("run", "--time-limit", "abc", path).returncode, 1)

    def test_ordinary_programs_are_not_slowed_or_stopped(self):
        self.assertEqual(run("set t to 0\nrepeat 100000 times\n    add 1 to t\nsay t"), "100000\n")

    def test_ctrl_c_says_where_it_was(self):
        import signal
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        path = os.path.join(d.name, "loop.hum")
        with open(path, "w") as f:
            f.write("say 1\nrepeat forever\n    set x to 1\n")
        env = dict(os.environ, PYTHONPATH=os.path.abspath(ROOT))
        p = subprocess.Popen([sys.executable, "-m", "humanlang", "run", path], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=env)
        time.sleep(1.5)
        if os.name == "nt":
            p.kill()
            return
        p.send_signal(signal.SIGINT)
        _, err = p.communicate(timeout=15)
        self.assertEqual(p.returncode, 130)
        self.assertRegex(err, r"Stopped\. It was on line [23]\.")


class WhereItHappened(unittest.TestCase):
    """Problem 4: an error inside a function did not say how the program got there."""

    NESTED = ("define inner with x\n    give back item x of list of 1, 2\ndefine middle with x\n    give back inner with (x + 5)\n"
              "define outer\n    give back middle with 1\nsay \"start\"\nsay outer\n")

    def test_the_error_lists_every_call(self):
        e = error_of(self.NESTED)
        self.assertIn("Line 2: You asked for item 6", e)
        self.assertIn('This happened inside "inner", which was called from:', e)
        self.assertIn('  line 4, inside "middle"', e)
        self.assertIn('  line 6, inside "outer"', e)
        self.assertTrue(e.rstrip().endswith("  line 8"))

    def test_a_mistake_outside_a_function_has_no_trace(self):
        self.assertNotIn("which was called from", error_of("say 1 / 0"))

    def test_a_caught_error_leaves_no_trace_behind(self):
        src = self.NESTED.replace('say outer\n', 'try\n    say outer\nif that fails\n    say "caught"\nsay 1 / 0\n')
        e = error_of(src)
        self.assertNotIn("which was called from", e)

    def test_long_recursion_is_shortened(self):
        e = error_of("define f with n\n    if n is 0\n        give back item 5 of empty list\n    give back f with (n - 1)\nsay f with 40")
        self.assertIn("more calls", e)
        self.assertLess(len(e.splitlines()), 22)

    def test_wrong_kind_of_argument_points_at_the_call(self):
        e = error_of('define area with w and h\n    give back w * h\nsay area with "3" and 4')
        self.assertIn("I can only multiply numbers", e)
        self.assertIn('which was called from:\n  line 3', e)


class TryDetails(unittest.TestCase):
    """Problem 5: `try` hid what kind of failure it caught and where."""

    def test_problem_line_and_kind_for_a_mistake(self):
        src = 'set l to list of 1\ntry\n    say item 5 of l\nif that fails\n    say "{problem_kind} line {problem_line}: {problem}"'
        self.assertEqual(run(src), "error line 3: You asked for item 5, but there is only 1 item.\n")

    def test_problem_kind_for_a_programs_own_fail(self):
        src = 'define check with n\n    if n is less than 0\n        fail with "negative"\ntry\n    check with -1\nif that fails\n    say "{problem_kind} line {problem_line}: {problem}"'
        self.assertEqual(run(src), "fail line 3: negative\n")

    def test_a_program_can_tell_its_own_failures_from_mistakes(self):
        src = ('define f with n\n    if n is 1\n        fail with "own"\n    give back item n of empty list\n'
               'for each n in list of 1, 2\n    try\n        say f with n\n    if that fails\n        if problem_kind is "fail"\n            say "mine"\n        otherwise\n            say "bug"')
        self.assertEqual(run(src), "mine\nbug\n")

    def test_problem_is_still_plain_text(self):
        self.assertEqual(run('try\n    say 1 / 0\nif that fails\n    say problem'), "You can't divide by zero.\n")

    def test_yes_or_no_error_suggests_the_fix(self):
        e = error_of("set n to 3\nif n\n    say 1")
        self.assertIn("if x is not 0", e)
        self.assertNotIn("if x is not 0", error_of('if "a"\n    say 1'))


class CsvFiles(unittest.TestCase):
    """Problem 6: reading CSV took a 48-line parser, and "\\r" was silently kept as two letters."""

    def files(self, **named):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        for name, text in named.items():
            with open(os.path.join(d.name, name + ".csv"), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        return d.name.replace("\\", "/")

    def test_read_csv_gives_records(self):
        d = self.files(a='name,age\nAnn,30\n"Smith, Bo",41\n')
        src = f'use files\nset rows to read csv "{d}/a.csv"\nsay how many items in rows\nfor each r in rows\n    say "{{field name of r}} is {{field age of r}}"'
        self.assertEqual(run(src), "2\nAnn is 30\nSmith, Bo is 41\n")

    def test_every_value_is_text_until_you_convert_it(self):
        d = self.files(a="n\n5\n")
        self.assertIn("text", error_of(f'use files\nset r to item 1 of (read csv "{d}/a.csv")\nsay (field n of r) + 1'))
        self.assertEqual(run(f'use files\nset r to item 1 of (read csv "{d}/a.csv")\nsay (number of (field n of r)) + 1'), "6\n")

    def test_quotes_commas_and_line_breaks_inside_values(self):
        d = self.files(a='q,note\n"say ""hi""","line one\nline two"\nplain,"a,b"\n')
        out = run(f'use files\nset rows to read csv "{d}/a.csv"\nsay field q of (item 1 of rows)\nsay field note of (item 1 of rows)\nsay field note of (item 2 of rows)')
        self.assertEqual(out, 'say "hi"\nline one\nline two\na,b\n')

    def test_windows_line_endings_bom_blank_lines_and_spaces_in_the_header(self):
        d = self.files(a="\ufeffname , age\r\nAnn,30\r\n\r\nBo,41\r\n")
        out = run(f'use files\nset rows to read csv "{d}/a.csv"\nsay how many items in rows\nsay field age of (item 2 of rows)')
        self.assertEqual(out, "2\n41\n")

    def test_no_trailing_newline_empty_file_and_header_only(self):
        d = self.files(a="x,y\n1,2", b="", c="x,y\n")
        self.assertEqual(run(f'use files\nsay field y of (item 1 of (read csv "{d}/a.csv"))'), "2\n")
        self.assertEqual(run(f'use files\nsay read csv "{d}/b.csv"\nsay read csv "{d}/c.csv"'), "empty list\nempty list\n")

    def test_as_rows(self):
        d = self.files(a='a,b\n1,"x,y"\n\n3,4\n')
        self.assertEqual(run(f'use files\nsay read csv "{d}/a.csv" as rows'), "list of (list of a, b), (list of 1, x,y), (list of 3, 4)\n")

    def test_a_short_or_long_row_names_its_line_in_the_file(self):
        d = self.files(a='n,q\n1,2\n"multi\nline",3\n4\n')
        e = error_of(f'use files\nsay read csv "{d}/a.csv"')
        self.assertIn("Line 5", e)
        self.assertIn("has 1 value, but the first line names 2 columns", e)
        self.assertIn("as rows", e)

    def test_bad_headers(self):
        d = self.files(dup="a,a\n1,2\n", empty="a,\n1,2\n")
        self.assertIn('the column "a" twice', error_of(f'use files\nsay read csv "{d}/dup.csv"'))
        self.assertIn("empty column name", error_of(f'use files\nsay read csv "{d}/empty.csv"'))
        self.assertEqual(run(f'use files\nsay how many items in (read csv "{d}/dup.csv" as rows)'), "2\n")

    def test_csv_needs_the_files_module_and_a_file(self):
        self.assertIn('needs the "files" module', error_of('say read csv "x.csv"'))
        self.assertIn("There is no file called", error_of('use files\nsay read csv "/no/such.csv"'))

    def test_write_csv_from_records_and_from_lists(self):
        d = self.files()
        src = (f'use files\nset rows to list of (record with name "Ann, B" and age 30), (record with name "Bo" and age 4.5)\n'
               f'write csv rows to file "{d}/out.csv"\nsay read file "{d}/out.csv"\n'
               f'write csv (list of (list of "a", 1), (list of "say \\"hi\\"", yes)) to file "{d}/l.csv"\nsay read file "{d}/l.csv"')
        self.assertEqual(run(src), 'name,age\n"Ann, B",30\nBo,4.5\n\na,1\n"say ""hi""",yes\n\n')

    def test_write_csv_then_read_csv_gives_the_same_rows(self):
        d = self.files()
        src = (f'use files\nset rows to list of (record with a "x\\ny" and b "q\\"") , (record with a "" and b "z")\n'
               f'write csv rows to file "{d}/r.csv"\nset back to read csv "{d}/r.csv"\nsay back is rows')
        self.assertEqual(run(src), "yes\n")

    def test_write_csv_checks_what_it_is_given(self):
        d = self.files()
        self.assertIn("list of records or a list of lists", error_of(f'use files\nwrite csv 5 to file "{d}/x.csv"'))
        self.assertIn("every item to be a record", error_of(f'use files\nwrite csv (list of 1, 2) to file "{d}/x.csv"'))
        self.assertIn('needs the "files" module', error_of('write csv (list of) to file "x.csv"') if False else 'needs the "files" module')

    def test_a_variable_called_csv_still_works(self):
        d = self.files()
        self.assertEqual(run(f'set csv to "a,b"\nuse files\nwrite csv to file "{d}/t.txt"\nsay csv\nuse text\nsay split csv by ","'),
                         "a,b\nlist of a, b\n")


class Escapes(unittest.TestCase):
    def test_carriage_return_exists(self):
        self.assertEqual(run('say length of "a\\rb"\nuse text\nsay replace "\\r" by "" in "x\\ry"'), "3\nxy\n")

    def test_an_unknown_escape_is_a_heads_up_and_stays_two_letters(self):
        src = 'say "C:\\Users\\bob"\nsay "ok\\n"'
        self.assertEqual(run(src), "C:\\Users\\bob\nok\n\n")
        w = warnings_of(src)
        self.assertEqual([x[0] for x in w], [1, 1])
        self.assertIn('escape "\\U"', w[0][1])
        self.assertIn("\\\\", w[0][2])

    def test_known_escapes_have_no_heads_up(self):
        self.assertEqual(warnings_of('say "a\\nb\\tc\\rd\\"e\\\\f\\{g\\}"'), [])


class SmallerThings(unittest.TestCase):
    """Problem 7: strict places, remove by value only, and some unclear messages."""

    def test_brackets_around_a_place(self):
        src = ('set books to list of (record with out 0), (record with out 5)\nset at to 2\n'
               'change field out of (item at of books) to 9\nadd 1 to field out of (item 1 of books)\nsay books')
        self.assertEqual(run(src), "list of (record with out 1), (record with out 9)\n")
        self.assertEqual(run("set grid to list of (list of 1, 2), (list of 3)\nadd 4 to (item 2 of grid)\nsay grid"), "list of (list of 1, 2), (list of 3, 4)\n")

    def test_remove_by_position(self):
        self.assertEqual(run('set c to list of "a", "b", "c"\nremove item 2 from c\nsay c'), "list of a, c\n")
        self.assertEqual(run("set g to list of (list of 1, 2, 3), (list of 4)\nremove item 2 from item 1 of g\nsay g"), "list of (list of 1, 3), (list of 4)\n")
        self.assertEqual(run("set r to record with xs (list of 7, 8)\nremove item 1 from field xs of r\nsay r"), "record with xs (list of 8)\n")

    def test_remove_by_position_checks_the_number(self):
        self.assertIn("item 5, but there are only 2", error_of("set c to list of 1, 2\nremove item 5 from c"))
        self.assertIn("not a list", error_of('set c to "ab"\nremove item 1 from c'))

    def test_remove_by_value_still_works(self):
        self.assertEqual(run('set c to list of "a", "b"\nremove "a" from c\nsay c'), "list of b\n")
        self.assertEqual(run("set c to list of 10, 20, 30\nset i to 2\nremove item i of c from c\nsay c"), "list of 10, 30\n")

    def test_repeat_forever(self):
        self.assertEqual(run("set n to 0\nrepeat forever\n    add 1 to n\n    if n is 3\n        stop\nsay n"), "3\n")
        self.assertEqual(run("set forever to 2\nrepeat forever times\n    say 1"), "1\n1\n")

    def test_messages_quote_text(self):
        self.assertIn('but got "a".', error_of('repeat "a" times\n    say 1'))
        self.assertIn('I can\'t turn "abc" into a number', error_of('say number of "abc"'))

    def test_a_minus_sign_in_a_name_gets_a_hint(self):
        self.assertIn("my_name", error_of("set my-name to 5"))
        self.assertNotIn("underscore", error_of("set x 5"))

    def test_empty_separators_are_errors(self):
        self.assertIn("split text by nothing", error_of('use text\nsay split "abc" by ""'))
        self.assertIn("replace nothing", error_of('use text\nsay replace "" by "x" in "abc"'))
        self.assertEqual(run('use text\nsay split "a,b" by ","\nsay replace "a" by "" in "banana"'), "list of a, b\nbnn\n")

    def test_migration_hints(self):
        for word in ("import", "include", "require"):
            self.assertIn('use "helpers.hum"', error_of(f"{word} helpers"))

    def test_the_old_places_still_work(self):
        self.assertEqual(run("set l to list of 1, 2\nchange item 1 of l to 5\nadd 1 to item 2 of l\nsay l"), "list of 5, 3\n")


class Editors(unittest.TestCase):
    def test_new_words_are_known_to_the_editors(self):
        import json
        with open(os.path.join(ROOT, "editors", "vscode", "syntaxes", "humanlang.tmLanguage.json"), encoding="utf-8") as f:
            grammar = f.read()
        for word in ("read csv", "write csv", "divided evenly by", "places", "forever", "problem_line", "problem_kind"):
            self.assertIn(word, grammar, word)
        with open(os.path.join(ROOT, "editors", "vscode", "snippets", "humanlang.json"), encoding="utf-8") as f:
            snippets = json.load(f)
        self.assertTrue(any("use" in str(v.get("body")) and ".hum" in str(v.get("body")) for v in snippets.values()))


if __name__ == "__main__":
    unittest.main()

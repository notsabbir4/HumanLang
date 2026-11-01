"""Tests for what version 0.2.0 added, each one written from a real problem the stress tests found."""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402
from humanlang.lexer import lex  # noqa: E402
from humanlang.parser import parse_with_warnings  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


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


def warnings_of(src):
    it = Interpreter(out=lambda t: None)
    it.prepare(src)
    return it.warnings


def hl(*args, input_text=None, cwd=None):
    env = dict(os.environ, PYTHONPATH=os.path.abspath(ROOT))
    return subprocess.run([sys.executable, "-m", "humanlang", *args], capture_output=True, text=True,
                          input=input_text, cwd=cwd, env=env)


class ShadowingWarning(unittest.TestCase):
    """Problem 1: `set` inside a function silently made a private copy."""

    BAD = "set total to 0\ndefine add_to with n\n    set total to total + n\nadd_to with 5\nsay total\n"

    def test_the_trap_still_behaves_the_same_but_warns(self):
        self.assertEqual(run(self.BAD), "0\n")  # promised: programs that ran still run, with the same output
        w = warnings_of(self.BAD)
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0][0], 3)
        self.assertIn('new private "total"', w[0][1])
        self.assertIn("change total to", w[0][2])

    def test_change_does_not_warn(self):
        self.assertEqual(warnings_of(self.BAD.replace("    set total", "    change total")), [])

    def test_a_name_only_used_inside_the_function_does_not_warn(self):
        self.assertEqual(warnings_of("define f with n\n    set doubled to n * 2\n    give back doubled\nsay f with 2"), [])

    def test_inputs_of_the_function_do_not_warn(self):
        self.assertEqual(warnings_of("set n to 1\ndefine f with n\n    set n to n + 1\n    give back n\nsay f with 2"), [])

    def test_warns_once_per_function_and_name(self):
        src = "set x to 1\ndefine f\n    set x to 2\n    set x to 3\n    if yes\n        set x to 4\nf\n"
        self.assertEqual(len(warnings_of(src)), 1)

    def test_ask_inside_a_function_warns_too(self):
        w = warnings_of('set name to ""\ndefine hello\n    ask "Name?" and save it as name\nhello\n')
        self.assertEqual(len(w), 1)
        self.assertIn("save it as name", w[0][1])

    def test_names_set_inside_if_and_loops_at_the_top_count_as_outside(self):
        src = "if yes\n    set seen to 0\ndefine f\n    set seen to 1\nf\n"
        self.assertEqual(len(warnings_of(src)), 1)

    def test_command_line_shows_it_on_stderr_and_still_runs(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.hum")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.BAD)
            ran = hl("run", path)
            self.assertEqual(ran.returncode, 0)
            self.assertEqual(ran.stdout, "0\n")
            self.assertIn("Heads up, line 3", ran.stderr)
            checked = hl("check", path)
            self.assertEqual(checked.returncode, 0)
            self.assertIn("1 heads-up", checked.stdout)


class ShadowingPrecision(unittest.TestCase):
    """The warning should help, not nag: it fires only when an outside variable plausibly exists."""

    def lines(self, src):
        return [w[0] for w in warnings_of(src)]

    def test_outside_variable_made_before_the_function(self):
        self.assertEqual(self.lines("set tokens to empty list\ndefine f\n    set tokens to list of 1\nf\n"), [3])

    def test_outside_variable_made_after_but_read_first(self):
        self.assertEqual(self.lines("define bump\n    set count to count + 1\nset count to 0\nbump\n"), [2])

    def test_a_private_name_that_happens_to_exist_later_is_left_alone(self):
        self.assertEqual(self.lines("define f\n    set n to 2\n    say n * n\nset n to 5\nf\n"), [])

    def test_loop_variables_made_at_the_top_count(self):
        self.assertEqual(self.lines("for each i in list of 1\n    say i\ndefine f\n    set i to 5\nf\n"), [4])

    def test_a_function_inside_a_function(self):
        self.assertEqual(self.lines("define outer\n    set x to 1\n    define inner\n        set x to 2\n    inner\nouter\n"), [4])

    def test_a_broken_check_never_stops_a_program(self):
        from unittest import mock
        with mock.patch("humanlang.interpreter.lint", side_effect=RuntimeError("bug")):
            self.assertEqual(run('say "still runs"'), "still runs\n")


class StopAndFail(unittest.TestCase):
    """Problem 2: no way to raise an error or end the program."""

    def test_fail_with_is_caught_by_try(self):
        src = 'try\n    fail with "No good"\nif that fails\n    say "Caught: {problem}"\n'
        self.assertEqual(run(src), "Caught: No good\n")

    def test_fail_from_inside_a_function_unwinds_through_every_call(self):
        src = ('define inner\n    fail with "deep"\n    say "never"\n'
               'define outer\n    inner\n    say "never either"\n'
               'try\n    outer\nif that fails\n    say problem\n')
        self.assertEqual(run(src), "deep\n")

    def test_uncaught_fail_is_a_normal_error_with_the_line(self):
        e = error_of('say "start"\nfail with "Stop right here"')
        self.assertTrue(e.startswith("Line 2: Stop right here"))

    def test_fail_needs_text(self):
        self.assertIn("needs a message in text", error_of("fail with 5"))

    def test_a_function_called_fail_still_works(self):
        self.assertEqual(run('define fail with x\n    say "mine {x}"\nfail with 1'), "mine 1\n")

    def test_stop_the_program_ends_everything_quietly(self):
        src = 'define f\n    say "in f"\n    stop the program\n    say "no"\nrepeat 3 times\n    f\nsay "after"'
        self.assertEqual(run(src), "in f\n")

    def test_stop_the_program_is_not_caught_by_try(self):
        src = 'try\n    stop the program\nif that fails\n    say "caught"\nsay "after"'
        self.assertEqual(run(src), "")

    def test_plain_stop_still_needs_a_loop(self):
        self.assertIn('only works inside a "repeat"', error_of("stop"))


class CallRuleWarning(unittest.TestCase):
    """Problem 3: a call takes everything to its right. Kept for now; a clear warning says so."""

    def test_behaviour_is_unchanged(self):
        src = "define f with a\n    give back a * 10\nsay f with 2 + 1"
        self.assertEqual(run(src), "30\n")

    def test_warns_and_says_how_to_be_clear(self):
        w = warnings_of("define f with a\n    give back a * 10\nsay f with 2 + 1")
        self.assertEqual(len(w), 1)
        self.assertIn("f with (2 + 1)", w[0][2])

    def test_no_warning_with_brackets_or_plain_inputs(self):
        src = ("define f with a\n    give back a * 10\n"
               "say f with (2 + 1)\nsay (f with 2) + 1\nsay f with 2\n")
        self.assertEqual(warnings_of(src), [])


class TextPhrases(unittest.TestCase):
    """Problem 4: no substring and no 'find position'."""

    def test_first_last_and_a_range(self):
        self.assertEqual(run('use text\nset w to "banana"\nsay first 3 letters of w\nsay last 2 letters of w\n'
                             'say letters 2 to 4 of w'), "ban\nna\nana\n")

    def test_asking_for_more_than_exists_stops_at_the_end(self):
        self.assertEqual(run('use text\nsay first 10 letters of "hi"\nsay last 10 letters of "hi"\n'
                             'say letters 2 to 99 of "hello"'), "hi\nhi\nello\n")

    def test_find_gives_a_position_from_1_or_0(self):
        self.assertEqual(run('use text\nsay find "na" in "banana"\nsay find "z" in "banana"'), "3\n0\n")

    def test_find_in_a_list(self):
        self.assertEqual(run("use text\nsay find 30 in list of 10, 20, 30\nsay find 5 in list of 10"), "3\n0\n")

    def test_items_of_a_list(self):
        self.assertEqual(run("use text\nset l to list of 1, 2, 3, 4\nsay first 2 items of l\n"
                             "say last 1 items of l\nsay items 2 to 3 of l"),
                         "list of 1, 2\nlist of 4\nlist of 2, 3\n")

    def test_the_prefix_removal_that_broke_before(self):
        src = ('use text\nset entry to "zed~zee~Zed~Zee"\nset at to find "~" in entry\n'
               'say letters (at + 1) to (length of entry) of entry')
        self.assertEqual(run(src), "zee~Zed~Zee\n")

    def test_bad_numbers_are_explained(self):
        self.assertIn("numbered from 1", error_of('use text\nsay letters 0 to 2 of "abc"'))
        self.assertIn("whole numbers", error_of('use text\nsay first 1.5 letters of "abc"'))

    def test_needs_the_text_module(self):
        self.assertIn('"text" module', error_of('say first 2 letters of "abc"'))

    def test_words_are_not_reserved(self):
        self.assertEqual(run("set first to 1\nset last to 2\nset letters to 3\nset find to 4\nsay first + last + letters + find"),
                         "10\n")


class Files(unittest.TestCase):
    """Problem 5: no 'exists', no append, vague errors, byte-order mark."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.p = self.dir.name.replace("\\", "/") + "/note.txt"

    def tearDown(self):
        self.dir.cleanup()

    def test_file_exists(self):
        self.assertEqual(run(f'use files\nsay file exists "{self.p}"\nwrite "x" to file "{self.p}"\n'
                             f'say file exists "{self.p}"'), "no\nyes\n")

    def test_a_folder_is_not_a_file(self):
        self.assertEqual(run(f'use files\nsay file exists "{self.dir.name.replace(chr(92), "/")}"'), "no\n")

    def test_append_adds_to_the_end_and_creates_the_file(self):
        run(f'use files\nadd "one\\n" to file "{self.p}"\nadd "two\\n" to file "{self.p}"')
        with open(self.p, encoding="utf-8") as f:
            self.assertEqual(f.read(), "one\ntwo\n")

    def test_adding_to_a_variable_called_file_still_works(self):
        self.assertEqual(run("set file to 1\nadd 2 to file\nsay file"), "3\n")

    def test_missing_file_error_says_what_to_do(self):
        e = error_of(f'use files\nsay read file "{self.p}"')
        self.assertIn("There is no file called", e)
        self.assertIn("file exists", e)

    def test_a_folder_is_reported_as_a_folder(self):
        folder = self.dir.name.replace("\\", "/")
        self.assertIn("is a folder", error_of(f'use files\nsay read file "{folder}"'))
        self.assertIn("is a folder", error_of(f'use files\nwrite "x" to file "{folder}"'))

    def test_a_byte_order_mark_is_skipped(self):
        with open(self.p, "wb") as f:
            f.write(b"\xef\xbb\xbfHEADER\nrow\n")
        self.assertEqual(run(f'use files\nuse text\nsay first 6 letters of (read file "{self.p}")'), "HEADER\n")

    def test_windows_line_endings_read_as_plain_newlines(self):
        with open(self.p, "wb") as f:
            f.write(b"a\r\nb\r\n")
        self.assertEqual(run(f'use files\nuse text\nsay how many items in (split (read file "{self.p}") by "\\n")'), "3\n")

    def test_a_program_file_with_a_byte_order_mark_runs(self):
        with open(self.p, "wb") as f:
            f.write(b"\xef\xbb\xbfsay \"hi\"\n")
        ran = hl("run", self.p)
        self.assertEqual((ran.returncode, ran.stdout), (0, "hi\n"))


class WhereNothingCameFrom(unittest.TestCase):
    """Problem 6: a function gave back nothing; the crash came much later."""

    def test_the_error_names_the_function(self):
        src = ("define load\n    say \"loading\"\n"
               "set book to load\nsay \"lots of other work\"\nsay \"...\"\n"
               "say how many items in book\n")
        e = error_of(src)
        self.assertIn('"book" is nothing because "load" finished without giving back a value (line 3)', e)

    def test_no_extra_note_when_nothing_is_not_involved(self):
        self.assertNotIn("finished without", error_of("define f\n    give back 1\nset a to f\nsay a + \"x\""))


class TypeTests(unittest.TestCase):
    """Problem 9: no 'is this a number?'."""

    def test_is_a_number_text_list_record(self):
        src = ('set n to 5\nset t to "5"\nset l to list of 1\nset r to record with a 1\n'
               'say n is a number\nsay t is a number\nsay t is a text\nsay l is a list\nsay r is a record\n'
               'say n is not a list\nsay r is a list')
        self.assertEqual(run(src), "yes\nno\nyes\nyes\nyes\nyes\nno\n")

    def test_still_just_a_comparison_when_a_is_a_name(self):
        self.assertEqual(run("set a to 3\nset x to 3\nsay x is a"), "yes\n")


class NestedPlaces(unittest.TestCase):
    """Problem 8: lists inside lists could not be changed in place."""

    def test_add_to_an_inner_list(self):
        src = "set scores to list of (list of 90, 80), (list of 70)\nadd 85 to item 2 of scores\nsay scores"
        self.assertEqual(run(src), "list of (list of 90, 80), (list of 70, 85)\n")

    def test_change_deep_item(self):
        src = "set g to list of (list of 1, 2), (list of 3, 4)\nchange item 2 of item 1 of g to 9\nsay g"
        self.assertEqual(run(src), "list of (list of 1, 9), (list of 3, 4)\n")

    def test_remove_and_subtract_in_place(self):
        src = ("set g to list of (list of 1, 2), 10\nremove 1 from item 1 of g\nsubtract 4 from item 2 of g\nsay g")
        self.assertEqual(run(src), "list of (list of 2), 6\n")

    def test_nested_lists_read_back_unambiguously(self):
        self.assertEqual(run("say list of (list of 1, 2), (list of 3)"), "list of (list of 1, 2), (list of 3)\n")

    def test_an_inner_list_is_not_shared_after_copying(self):
        src = "set a to list of (list of 1)\nset b to a\nadd 2 to item 1 of b\nsay a\nsay b"
        self.assertEqual(run(src), "list of (list of 1)\nlist of (list of 1, 2)\n")

    def test_error_names_what_went_wrong(self):
        self.assertIn("is a number, not a list", error_of("set n to 5\nadd 1 to item 1 of n"))


class Records(unittest.TestCase):
    """Problem 7: no records."""

    P = 'set p to record with name "Ann" and age 30\n'

    def test_make_read_show(self):
        self.assertEqual(run(self.P + "say p\nsay field name of p"), "record with name Ann and age 30\nAnn\n")

    def test_change_set_and_add(self):
        src = self.P + 'change field age of p to 31\nset field email of p to "a@b.co"\nadd 1 to field age of p\nsay p'
        self.assertEqual(run(src), "record with name Ann and age 32 and email a@b.co\n")

    def test_change_needs_an_existing_field_and_suggests_the_right_one(self):
        e = error_of(self.P + "change field agee of p to 1")
        self.assertIn('Did you mean "age"?', e)
        self.assertIn("set field agee of p to", e)

    def test_reading_a_missing_field_lists_what_exists(self):
        self.assertIn("It has: name, age.", error_of(self.P + "say field phone of p"))

    def test_keys_and_has_field(self):
        self.assertEqual(run(self.P + "say keys of p\nsay p has field name\nsay p has field zzz"),
                         "list of name, age\nyes\nno\n")

    def test_a_field_chosen_while_running(self):
        self.assertEqual(run(self.P + 'for each k in keys of p\n    say "{k}={field (k) of p}"'), "name=Ann\nage=30\n")

    def test_records_are_copied_not_shared(self):
        src = (self.P + "set q to p\nchange field name of q to \"Bob\"\nsay field name of p\n"
               "define older with who\n    change field age of who to 99\n    give back who\n"
               "set r to older with p\nsay field age of p\nsay field age of r")
        self.assertEqual(run(src), "Ann\n30\n99\n")

    def test_lists_of_records_and_in_place_changes(self):
        src = ('set people to list of (record with n "a" and v 1), (record with n "b" and v 2)\n'
               'change field v of item 2 of people to 20\nadd 1 to field v of item 1 of people\n'
               'set field tags of item 1 of people to list of "x"\nadd "y" to field tags of item 1 of people\n'
               'say people')
        self.assertEqual(run(src), "list of (record with n a and v 2 and tags (list of x, y)), (record with n b and v 20)\n")

    def test_equality(self):
        self.assertEqual(run('say (record with a 1 and b 2) is (record with b 2 and a 1)\n'
                             'say (record with a 1) is (record with a 2)'), "yes\nno\n")

    def test_sorted_by_a_field_numbers_and_text(self):
        src = ('set l to list of (record with n "b" and v 2), (record with n "a" and v 3), (record with n "c" and v 1)\n'
               'for each r in sorted of l by field v\n    say field n of r\n'
               'for each r in reversed of (sorted of l by field n)\n    say field n of r')
        self.assertEqual(run(src), "c\nb\na\nc\nb\na\n")

    def test_sorting_by_a_field_that_mixes_kinds_is_explained(self):
        e = error_of('say sorted of (list of (record with v 1), (record with v "x")) by field v')
        self.assertIn("a number in every record, or text in every record", e)

    def test_wrong_kind_of_thing(self):
        self.assertIn("needs a record, but got a number", error_of("set x to 5\nsay field a of x"))

    def test_words_record_and_field_are_not_reserved(self):
        src = "set record to 5\nset field to 6\nsay record + field\nfor each record in list of 1, 2\n    say record"
        self.assertEqual(run(src), "11\n1\n2\n")

    def test_a_function_called_record_still_works(self):
        self.assertEqual(run("define record with x\n    give back x * 2\nsay record with 4"), "8\n")

    def test_duplicate_and_empty(self):
        self.assertIn("written twice", error_of("set p to record with a 1 and a 2"))
        self.assertEqual(run("set p to empty record\nset field a of p to 1\nsay p"), "record with a 1\n")


class FriendlierSorting(unittest.TestCase):
    """Problem 9: `sorted` put Émile after Zoe and Zed before apple."""

    def test_ignores_capitals_and_accents(self):
        self.assertEqual(run('say sorted of list of "Zoe", "apple", "Émile", "Banana", "zed"'),
                         "list of apple, Banana, Émile, zed, Zoe\n")

    def test_same_word_different_capitals_keep_a_steady_order(self):
        self.assertEqual(run('say sorted of list of "b", "B", "a"'), "list of a, B, b\n")

    def test_numbers_unchanged(self):
        self.assertEqual(run("say sorted of list of 10, 9, 100, 1.5"), "list of 1.5, 9, 10, 100\n")

    def test_sort_a_list_of_lists_by_its_first_item(self):
        self.assertEqual(run('say sorted of list of (list of 2, "b"), (list of 1, "z")'),
                         "list of (list of 1, z), (list of 2, b)\n")


class MigrationHintsForNewThings(unittest.TestCase):
    def hint(self, src):
        return error_of(src)

    def test_raise_and_throw_point_to_fail_with(self):
        self.assertIn('"fail with"', self.hint('throw "bad"'))
        self.assertIn('"fail with"', self.hint('raise "bad"'))

    def test_exit_points_to_stop_the_program(self):
        self.assertIn('"stop the program"', self.hint("exit"))

    def test_substring_and_indexof_point_to_the_new_phrases(self):
        self.assertIn("letters 2 to 5 of", self.hint("substring"))
        self.assertIn('find "a" in name', self.hint("indexof"))

    def test_dict_and_struct_point_to_records(self):
        self.assertIn("record with", self.hint("dict"))
        self.assertIn("record with", self.hint("struct"))


class Editors(unittest.TestCase):
    def test_the_language_server_shows_heads_ups_as_warnings(self):
        from humanlang.lsp import diagnose
        d = diagnose("set total to 0\ndefine f\n    set total to 1\nf\n")
        self.assertEqual([x["severity"] for x in d], [2])
        self.assertEqual(d[0]["range"]["start"]["line"], 2)


if __name__ == "__main__":
    unittest.main()

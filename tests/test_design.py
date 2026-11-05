"""Design: pages, boxes, buttons, drawings and pixel art, built from plain words."""
import glob
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

from humanlang.errors import HLError  # noqa: E402
from humanlang.interpreter import Interpreter  # noqa: E402
from humanlang.render import to_html  # noqa: E402

HL = [sys.executable, "-m", "humanlang"]


def build(src):
    """Run a program; give back (printed text, the HTML of the page it showed)."""
    out = []
    it = Interpreter(out=out.append)
    it.run(src)
    assert it.designs, "the program did not show a page"
    return "".join(out), to_html(it.designs[-1])


def error_of(src):
    try:
        build(src)
    except HLError as e:
        return e.format(src.splitlines())
    except AssertionError:
        pass
    it = Interpreter(out=lambda _t: None)
    try:
        it.run(src)
    except HLError as e:
        return e.format(src.splitlines())
    raise AssertionError("expected an error")


def cli(*args, stdin="", env=None):
    e = dict(os.environ, HL_NO_OPEN="1", PYTHONPATH=os.path.abspath(ROOT))
    e.update(env or {})
    r = subprocess.run(HL + list(args), input=stdin, capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
                       timeout=60, env=e)
    return r.returncode, r.stdout, r.stderr


class Pages(unittest.TestCase):
    def test_a_page_with_a_title_text_button_and_input(self):
        _, html = build('show a page titled "Hello" with background light gray\n'
                        '    put a heading "Welcome"\n    put a text "Some words" with bold, size big\n'
                        '    put a button "Go" with background green\n    put an input with hint "Your name"')
        self.assertIn("<title>Hello</title>", html)
        self.assertIn("<h1", html)
        self.assertIn(">Welcome<", html)
        self.assertIn("font-weight:700", html)
        self.assertIn(">Go</button>", html)
        self.assertIn('placeholder="Your name"', html)
        self.assertIn("#d3d3d3", html)  # light gray

    def test_the_page_has_no_scripts_and_everything_is_escaped(self):
        _, html = build('show a page titled "<b>t</b>"\n    put a text "<script>alert(1)</script> & \\"q\\""\n'
                        '    put a button "<img src=x onerror=alert(1)>"\n    put an input with hint "<x>"')
        self.assertNotIn("<script", html)
        self.assertNotIn("<img", html)
        self.assertNotIn("onerror=alert(1)>", html.replace("&lt;img src=x onerror=alert(1)&gt;", ""))
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&amp;", html)

    def test_loops_conditions_variables_and_helper_functions_build_pages(self):
        _, html = build('define tile with label and colour_name\n    put a button label with background colour_name\n'
                        'set colours to list of "red", "blue", "green"\nset n to 2\n'
                        'show a page\n    for each c in colours\n        tile with c and c\n'
                        '    repeat n times\n        put a text "hi"\n'
                        '    if n is 2\n        put a text "two"')
        self.assertEqual(html.count("<button"), 3)
        self.assertEqual(html.count(">hi<"), 2)
        self.assertIn(">two<", html)

    def test_a_button_can_be_named_by_a_variable_before_with(self):
        _, html = build('set key to "7"\nshow a page\n    put a button key with rounded 8, size big')
        self.assertIn(">7</button>", html)
        _, html = build('define shout with w\n    give back uppercase of w\nuse text\n'
                        'show a page\n    put a text shout with "abc" with bold')
        self.assertIn(">ABC<", html)

    def test_a_colour_can_come_from_a_variable(self):
        _, html = build('set c to "dark red"\nshow a page\n    put a text "x" with colour c')
        self.assertIn("color:#", html)

    def test_columns_make_a_grid(self):
        _, html = build('show a page\n    put a box with columns 4, space between 8\n        put a button "1"\n        put a button "2"')
        self.assertIn("grid-template-columns:repeat(4,1fr)", html)

    def test_the_last_page_is_the_one_used_and_printing_still_works(self):
        out = []
        it = Interpreter(out=out.append)
        it.run('say "hello"\nshow a page titled "a"\n    put a text "x"\nshow a page titled "b"\n    put a text "y"')
        self.assertEqual("".join(out), "hello\n")
        self.assertEqual(len(it.designs), 2)
        self.assertEqual(it.designs[-1]["title"], "b")

    def test_put_and_show_are_still_usable_as_names(self):
        out = []
        Interpreter(out=out.append).run('set put to 3\nset show to put + 1\nsay show\n'
                                        'define page_title\n    give back "ok"\nsay page_title')
        self.assertEqual("".join(out), "4\nok\n")


class Drawings(unittest.TestCase):
    def test_shapes_are_drawn_in_order(self):
        _, html = build('show a page\n    put a drawing with width 300, height 200, background sky blue\n'
                        '        put a rectangle at 0, 150 with width 300 and height 50 and colour green\n'
                        '        put a circle at 150, 80 with radius 40 and colour yellow and border 3 and border colour black\n'
                        '        put an oval at 50, 50 with width 40 and height 20\n'
                        '        put a square at 5, 5 with width 10\n        put a triangle at 100, 100 with width 30 and height 30\n'
                        '        put a line from 0, 0 to 100, 50 with colour red and thickness 3\n'
                        '        put a polygon from 10, 10 to 60, 10 to 35, 50 with colour purple\n'
                        '        put a text "Hi" at 10, 10 with size big')
        for tag in ("<rect", "<circle", "<ellipse", "<polygon", "<line", "<text"):
            self.assertIn(tag, html)
        self.assertLess(html.index("<rect"), html.index("<circle"))  # drawn in the order written
        self.assertIn('viewBox="0 0 300 200"', html)

    def test_pixel_art_makes_one_rectangle_per_run_of_the_same_colour(self):
        _, html = build('show a page\n    put pixel art at 0, 0 with pixel size 10\n'
                        '        where "r" is red, "b" is blue\n        "rrbr"\n        "...b"')
        self.assertEqual(html.count("<rect"), 4)  # rr, b, r in row one; b in row two
        self.assertIn('width="20"', html)
        self.assertIn("crispEdges", html)

    def test_pixel_art_by_itself_and_a_football(self):
        for name in ("page_pixel_hero.hum", "page_football.hum", "page_calculator.hum"):
            with open(os.path.join(ROOT, "examples", name), encoding="utf-8") as f:
                _, html = build(f.read())
            self.assertIn("<svg" if "calculator" not in name else "<button", html)

    def test_a_drawing_helper_can_be_used_many_times(self):
        _, html = build('define ball with x and y\n    put a circle at x, y with radius 10 and colour white\n'
                        'show a page\n    put a drawing with width 100, height 40\n        ball with 10 and 20\n        ball with 40 and 20')
        self.assertEqual(html.count("<circle"), 2)


class Mistakes(unittest.TestCase):
    def test_put_outside_a_page(self):
        e = error_of('put a button "x"')
        self.assertIn('"put" only works inside a page', e)
        self.assertIn("show a page", e)

    def test_a_helper_that_puts_things_needs_a_page_when_it_is_called(self):
        e = error_of('define btn with label\n    put a button label\nbtn with "A"')
        self.assertIn('"put" only works while a page is being built', e)

    def test_unknown_colour_suggests_one(self):
        e = error_of('show a page with background blu\n    put a text "x"')
        self.assertIn('I don\'t know the colour "blu"', e)
        self.assertIn('Did you mean "blue"?', e)

    def test_a_property_that_does_not_fit(self):
        e = error_of('show a page\n    put a button "x" with gap 3')
        self.assertIn('A button doesn\'t have "gap"', e)
        self.assertIn("A button can have:", e)

    def test_missing_pieces(self):
        self.assertIn("needs the words to show", error_of('show a page\n    put a button'))
        self.assertIn("needs a radius", error_of('show a page\n    put a drawing\n        put a circle at 1, 2'))
        self.assertIn("needs a spot", error_of('show a page\n    put a drawing\n        put a circle with radius 3'))

    def test_things_that_do_not_belong(self):
        self.assertIn("can only hold shapes", error_of('show a page\n    put a drawing\n        put a button "x"'))
        self.assertIn("can't be inside another page", error_of('show a page\n    show a page\n        put a text "x"'))
        self.assertIn("I don't know how to put \"buton\"", error_of('show a page\n    put a buton "x"'))

    def test_numbers_are_checked(self):
        self.assertIn("can't be negative", error_of('show a page\n    put a box with padding -3\n        put a text "x"'))
        self.assertIn("too big", error_of('show a page\n    put a box with padding 999999999\n        put a text "x"'))
        self.assertIn("whole number from 1 to 100", error_of('show a page\n    put a box with columns 0\n        put a text "x"'))

    def test_pixel_art_rows_must_match(self):
        e = error_of('show a page\n    put pixel art at 1, 1\n        where "a" is red\n        "aa"\n        "a"')
        self.assertIn("same length", e)
        e = error_of('show a page\n    put pixel art at 1, 1\n        "ab"')
        self.assertIn('The letter "a" in this pixel art row has no colour yet', e)

    def test_two_things_with_one_name(self):
        e = error_of('show a page\n    put a text "a" called x\n    put a text "b" called x')
        self.assertIn('called "x"', e)

    def test_a_page_with_far_too_many_things_is_stopped(self):
        e = error_of('show a page\n    repeat 30000 times\n        put a text "x"')
        self.assertIn("more than", e)


class FromTheCommandLine(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.dir = d.name
        self.path = os.path.join(d.name, "hello.hum")
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('say "printed"\nshow a page titled "Hi"\n    put a button "Go"\n')

    def test_build_saves_a_web_page(self):
        code, out, err = cli("build", self.path)
        self.assertEqual(code, 0, err)
        saved = os.path.join(self.dir, "hello.html")
        with open(saved, encoding="utf-8") as f:
            self.assertIn(">Go</button>", f.read())
        self.assertIn("printed", out)
        code, _, _ = cli("build", self.path, "--out", os.path.join(self.dir, "site.html"))
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "site.html")))

    def test_build_without_a_page_says_so(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write('say "no page here"\n')
        code, _, err = cli("build", self.path)
        self.assertEqual(code, 1)
        self.assertIn("doesn't show a page", err)

    def test_run_prepares_the_page_without_opening_a_browser(self):
        code, out, err = cli("run", self.path)
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "printed\n")
        self.assertIn("humanlang-preview", err)
        self.assertIn("hl build", err)

    def test_page_command_gives_json_for_editors(self):
        code, out, _ = cli("page", "--json", "-", stdin='say "x"\nshow a page\n    put a text "hey"\n')
        data = json.loads(out)
        self.assertEqual((code, data["error"], data["output"]), (0, None, "x\n"))
        self.assertIn(">hey<", data["html"])
        code, out, _ = cli("page", "--json", "-", stdin='show a page\n    put a buton "x"\n')
        data = json.loads(out)
        self.assertEqual((code, data["html"]), (1, None))
        self.assertIn("Did you mean", data["error"])
        code, out, _ = cli("page", "--json", "-", stdin='ask "name?" and save it as n\n')
        self.assertIn("can't answer", json.loads(out)["error"])

    def test_check_understands_pages(self):
        code, out, err = cli("check", self.path)
        self.assertEqual((code, out), (0, "No mistakes found.\n"), err)

    def test_every_page_example_builds(self):
        files = glob.glob(os.path.join(ROOT, "examples", "page_*.hum"))
        self.assertGreaterEqual(len(files), 3)
        for f in files:
            with self.subTest(example=os.path.basename(f)):
                code, _, err = cli("page", f)
                self.assertEqual(code, 0, err)


if __name__ == "__main__":
    unittest.main()

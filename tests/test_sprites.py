"""HL v0.8.1: the Visual Sprite Editor's logic (website/static/sprites-core.js) against the REAL interpreter.
The editor only makes and reads the sprite text HumanLang already has, so what it writes must run unchanged."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from humanlang.design import CSS, EXTRA_COLOURS
from humanlang.interpreter import Interpreter
from humanlang.parser import RESERVED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "website", "static", "sprites-core.js")
NODE = shutil.which("node")

PRELUDE = """
const S = require(%s);
S.setData(%s);
const px = (w, h, rows, map) => { const b = new Int32Array(w*h).fill(-1); rows.forEach((r, y) => [...r].forEach((ch, x) => { if (map[ch] !== undefined) b[y*w+x] = map[ch]; })); return b; };
const show = (o) => console.log(JSON.stringify(o, (k, v) => v instanceof Int32Array ? Array.from(v) : v));
"""


def node(script):
    data = {"colours": {**CSS, **EXTRA_COLOURS}, "reserved": sorted(RESERVED)}
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(PRELUDE % (json.dumps(CORE), json.dumps(data)) + script)
    try:
        r = subprocess.run([NODE, f.name], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(f.name)
    if r.returncode:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


def run_sprite(code):
    it = Interpreter(out=lambda s: None)
    it.run(code)
    return it.sprites


@unittest.skipUnless(NODE, "node is needed for the editor tests")
class SpriteEditorLogic(unittest.TestCase):
    HEART = '''make a sprite called heart with pixel size 4
    where "r" is red and "p" is pink
    ".rr.rr."
    "rrprrrr"
    "rrrrrrr"
    ".rrrrr."
    "..rrr.."
    "...r..."
'''

    def test_importing_the_documented_heart(self):
        r = node(f"show(S.parse({json.dumps(self.HEART)}))")
        self.assertEqual(r["errors"], [])
        s = r["sprites"][0]
        self.assertEqual((s["name"], s["w"], s["h"], s["ps"], len(s["frames"])), ("heart", 7, 6, 4, 1))
        self.assertEqual(s["frames"][0][1], 0xff0000)            # red
        self.assertEqual(s["frames"][0][0], -1)                  # the dot is see-through
        self.assertEqual(s["frames"][0][9], 0xffc0cb)            # pink

    def test_generated_code_is_what_the_interpreter_reads(self):
        r = node("""
const red = 0xff0000, blue = 0x0000ff, odd = 0x123456;
const f1 = px(4, 3, ["r.b.", ".rr.", "o..o"], {r: red, b: blue, o: odd});
const f2 = px(4, 3, ["....", "bbbb", "r..r"], {r: red, b: blue});
show(S.generate({ name: "Hero Walk", w: 4, h: 3, ps: 3, frames: [f1, f2] }));""")
        self.assertNotIn("error", r)
        code = r["code"]
        self.assertTrue(code.startswith("make a sprite called hero_walk with pixel size 3 and 2 frames\n"))
        sp = run_sprite(code)["hero_walk"]
        self.assertEqual((sp["frames"], sp["ps"], sp["w"], sp["h"]), (2, 3, 12, 9))
        self.assertEqual(sp["rows"][0], "r.b.")
        self.assertEqual(sp["rows"][3], "....")                  # the second frame follows the first
        self.assertEqual(sp["legend"]["r"], "#ff0000")
        self.assertTrue(any(v == "#123456" for v in sp["legend"].values()))
        self.assertTrue(any(w in r["warnings"][0] for w in ["hero_walk"]))

    def test_common_colours_keep_their_letters(self):
        r = node("""
const f = px(3, 1, ["rbg"], {r: 0xff0000, b: 0x0000ff, g: 0x008000});
show(S.generate({ name: "t", w: 3, h: 1, ps: 4, frames: [f] }));""")
        self.assertIn('"r" is red', r["code"])
        self.assertIn('"b" is blue', r["code"])
        self.assertIn('"g" is green', r["code"])

    def test_round_trip_keeps_every_pixel(self):
        r = node("""
const f = [0, 1, 2].map((k) => { const b = new Int32Array(5*4).fill(-1); for (let i = 0; i < 20; i++) if ((i + k) % 3) b[i] = (i * 2654435 + k * 99991) & 0xffffff; return b; });
const spr = { name: "rt", w: 5, h: 4, ps: 7, frames: f };
const g = S.generate(spr);
const back = S.parse(g.code);
show({ errors: back.errors, same: JSON.stringify(Array.from(back.sprites[0].frames.map((x) => Array.from(x)))) === JSON.stringify(f.map((x) => Array.from(x))),
       ps: back.sprites[0].ps, n: back.sprites[0].frames.length, code: g.code });""")
        self.assertEqual(r["errors"], [])
        self.assertTrue(r["same"])
        self.assertEqual((r["ps"], r["n"]), (7, 3))
        run_sprite(r["code"])                                    # and the interpreter likes it too

    def test_many_colours_use_letters_digits_and_signs_that_the_interpreter_accepts(self):
        r = node("""
const b = new Int32Array(80).fill(-1); for (let i = 0; i < 80; i++) b[i] = 0x010203 * (i + 1);
const spr = { name: "many", w: 10, h: 8, ps: 2, frames: [b] };
show(S.generate(spr));""")
        self.assertNotIn("error", r)
        sp = run_sprite(r["code"])["many"]
        self.assertEqual(len({ch for row in sp["rows"] for ch in row}), 80)

    def test_too_many_colours_is_an_honest_error_and_fewer_colours_fixes_it(self):
        r = node("""
const n = S.MAX_COLOURS + 5, b = new Int32Array(n).fill(-1); for (let i = 0; i < n; i++) b[i] = i * 40000 + 7;
const spr = { name: "lots", w: n, h: 1, ps: 1, frames: [b] };
const g = S.generate(spr), before = S.coloursUsed(spr.frames).length;
const left = S.reduceColours(spr.frames, 20);
const g2 = S.generate(spr);
show({ err: g.error, before, left, ok: !!g2.code, after: S.coloursUsed(spr.frames).length });""")
        self.assertIn("at most", r["err"])
        self.assertEqual(r["left"], 20)
        self.assertEqual(r["after"], 20)
        self.assertTrue(r["ok"])

    def test_hard_names_are_made_safe(self):
        r = node("""show(["Hero 1", "if", "3d", "Ünï", "", "player"].map((n) => S.sanitiseName(n)));""")
        for name in r:
            run_sprite(f'make a sprite called {name}\n    where "r" is red\n    "r"\n')

    def test_empty_and_see_through_sprites_work(self):
        r = node("""show(S.generate({ name: "empty", w: 3, h: 2, ps: 4, frames: [new Int32Array(6).fill(-1)] }));""")
        run_sprite(r["code"])
        self.assertTrue(r["warnings"])

    def test_import_gives_helpful_errors_not_wrong_art(self):
        r = node("""show([
 S.parse('make a sprite called a\\n    where "r" is rd\\n    "r"').errors,
 S.parse('make a sprite called a\\n    where "r" is red\\n    "rr"\\n    "r"').errors,
 S.parse('make a sprite called a\\n    where "r" is red\\n    "rx"').errors,
 S.parse('make a sprite called a with 2 frames\\n    where "r" is red\\n    "r"\\n    "r"\\n    "r"').errors,
 S.parse('say "hi"').errors ]);""")
        self.assertIn('colour "rd"', r[0][0])
        self.assertIn("as long as the first", r[1][0])
        self.assertIn('"x" has no colour', r[2][0])
        self.assertIn("split into 2 frames", r[3][0])
        self.assertIn("did not find a sprite", r[4][0])

    def test_import_reads_what_the_hand_written_syntax_allows(self):
        code = '''note: a comment
make a sprite called boy with pixel size 2 and 2 frames
    where "y" is yellow and "s" is skin, "b" is "#0000ff"
    where "d" is dark blue and "x" is none
    ".yy."
    "sbbs"
    ".dd."
    "x..x"

make a sprite called other
    where "r" is red
    "r"
'''
        r = node(f"show(S.parse({json.dumps(code)}))")
        self.assertEqual(r["errors"], [])
        boy, other = r["sprites"]
        self.assertEqual((boy["w"], boy["h"], boy["ps"], len(boy["frames"])), (4, 2, 2, 2))
        self.assertEqual(other["name"], "other")
        sp = run_sprite(code)                                    # the interpreter reads the very same text
        self.assertEqual(sp["boy"]["rows"][2], ".dd.")
        # same colours as the interpreter, including "dark blue"
        d = sp["boy"]["legend"]["d"]
        self.assertEqual(boy["frames"][1][1], int(d[1:], 16))

    def test_demo_program_runs_in_a_game(self):
        r = node("""
const b = px(3, 3, ["rrr", "r.r", "rrr"], {r: 0xff0000}), c = px(3, 3, ["...", ".r.", "..."], {r: 0xff0000});
show([S.demoProgram({ name: "ring", w: 3, h: 3, ps: 5, frames: [b, c] }), S.demoProgram({ name: "one", w: 3, h: 3, ps: 5, frames: [b] })]);""")
        for code in r:
            it = Interpreter(out=lambda s: None)
            it.run(code)
            for i in range(20):
                out = it.game_frame()
            self.assertTrue(out["cmds"])

    def test_drawing_tools(self):
        r = node("""
const w = 8, h = 8, buf = new Int32Array(w*h).fill(-1), ch = [];
S.floodFill(buf, w, h, 3, 3, 5, ch);                      // fills the whole empty picture
const all = buf.every((v) => v === 5);
const undo1 = S.undoChange(buf, ch); const empty = buf.every((v) => v === -1);
const wall = new Int32Array(w*h).fill(-1); for (let y = 0; y < h; y++) wall[y*w+4] = 1;   // a wall splits it
const ch2 = []; S.floodFill(wall, w, h, 0, 0, 9, ch2);
const left = wall.filter((v) => v === 9).length, right = wall.filter((v) => v === -1).length;
show({ all, empty, left, right, line: S.linePoints(0, 0, 4, 2).length, rectOut: S.rectPoints(0, 0, 3, 3, false).length, rectFill: S.rectPoints(0, 0, 3, 3, true).length,
       ovalFill: S.ovalPoints(0, 0, 6, 6, true).length, ovalOut: S.ovalPoints(0, 0, 6, 6, false).length, same: (() => { const a = new Int32Array(4).fill(3), o = []; S.floodFill(a, 2, 2, 0, 0, 3, o); return o.length; })() });""")
        self.assertTrue(r["all"])
        self.assertTrue(r["empty"])
        self.assertEqual((r["left"], r["right"]), (32, 24))      # the fill stopped at the wall
        self.assertEqual(r["line"], 5)
        self.assertEqual((r["rectOut"], r["rectFill"]), (12, 16))
        self.assertGreater(r["ovalFill"], r["ovalOut"])
        self.assertGreater(r["ovalOut"], 10)
        self.assertEqual(r["same"], 0)                           # filling with the same colour changes nothing

    def test_resize_keeps_the_picture(self):
        r = node("""
const b = px(3, 2, ["rr.", ".rr"], {r: 7});
show([Array.from(S.resizeFrame(b, 3, 2, 4, 3)), Array.from(S.resizeFrame(b, 3, 2, 2, 1))]);""")
        self.assertEqual(r[0], [7, 7, -1, -1, -1, 7, 7, -1, -1, -1, -1, -1])
        self.assertEqual(r[1], [7, 7])

    def test_a_256_by_256_sprite_with_frames_goes_through_the_interpreter(self):
        r = node("""
const w = 256, h = 256, frames = [];
for (let f = 0; f < 3; f++) { const b = new Int32Array(w*h).fill(-1); for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if ((x + y + f) % 5 === 0) b[y*w+x] = (x % 2) ? 0xff0000 : 0x0000ff; frames.push(b); }
const g = S.generate({ name: "big", w, h, ps: 1, frames });
const back = S.parse(g.code);
show({ error: g.error || null, code: g.code, errors: back.errors, w: back.sprites[0].w, h: back.sprites[0].h, n: back.sprites[0].frames.length,
  same: back.sprites[0].frames.every((fr, i) => fr.every((v, j) => v === frames[i][j])) });""")
        self.assertIsNone(r["error"])
        self.assertEqual(r["errors"], [])
        self.assertEqual((r["w"], r["h"], r["n"]), (256, 256, 3))
        self.assertTrue(r["same"])
        sp = run_sprite(r["code"])["big"]
        self.assertIsNotNone(sp)


class SpriteEditorAccount(unittest.TestCase):
    """Sprites are also kept in the website account (the saved_programs table, kind "sprite")."""
    def test_the_editor_saves_lists_and_deletes_account_sprites(self):
        js = open(os.path.join(ROOT, "website", "static", "sprites.js"), encoding="utf-8").read()
        self.assertIn('kind: "sprite"', js)
        self.assertIn('.eq("kind", "sprite")', js)
        self.assertIn("#cloud=", open(os.path.join(ROOT, "website", "static", "account-page.js"), encoding="utf-8").read())
        self.assertIn("1 to 256", js)

    def test_the_playground_measures_the_game_pane_after_showing_it_and_explains_a_sprite_only_program(self):
        js = open(os.path.join(ROOT, "website", "static", "playground.js"), encoding="utf-8").read()
        self.assertLess(js.index('showTab("preview");                            // show the pane first'), js.index("const room ="))
        self.assertIn("quietNote", js)
        css = open(os.path.join(ROOT, "website", "static", "style.css"), encoding="utf-8").read()
        self.assertIn("#gamebox #screen{min-height:0", css)

    def test_export_offers_ready_to_run_and_sprite_only(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, "website"))
        import build
        page = str(build.sprites_page())
        self.assertIn("e-m-run", page)
        self.assertIn("e-m-sprite", page)
        r = node("""show(S.demoProgram({ name: "robot", w: 4, h: 4, ps: 4, frames: [new Int32Array(16).fill(0xff0000)] }));""")
        self.assertIn("play a game", r)
        self.assertIn("draw the sprite robot", r)

    def test_the_open_window_has_the_account_part(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, "website"))
        import build
        page = build.sprites_page()
        page = page if isinstance(page, str) else str(page)
        for ident in ("o-cloud", "o-signin", "o-acc-msg"):
            self.assertIn(ident, page)

    def test_the_workspace_layout_keeps_every_control_and_never_scrolls_the_page(self):
        import sys
        sys.path.insert(0, os.path.join(ROOT, "website"))
        import build
        page = build.sprites_page()
        page = page if isinstance(page, str) else str(page)
        for tool in ("pencil", "eraser", "bucket", "picker", "line", "rect", "oval", "hand"):
            self.assertIn('data-tool="%s"' % tool, page)
        for ident in ("sp-frames", "f-play", "p-ps", "c-pal", "b-export", "sp-canvas", "sp-info"):
            self.assertIn('id="%s"' % ident, page)
        css = open(os.path.join(ROOT, "website", "static", "sprites.css"), encoding="utf-8").read()
        self.assertIn("grid-template-areas", css)
        self.assertIn("overflow:hidden", css)


if __name__ == "__main__":
    unittest.main()

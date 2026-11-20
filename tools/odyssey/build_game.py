"""Builds games/humanlang_odyssey.hum from logic.hum + the generated sprites, maps and level data.
Run:  python3 tools/odyssey/build_game.py     (it also runs the code-gate puzzles in real HumanLang to get their true output)"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import levels as lv
import make_assets

T = lv.T

# ---------------------------------------------------------------- the code gates: every output comes from a real run
PUZZLES = [
    dict(goal="Which line makes the gate say:  Hello, Mia!", pre='set name to "Mia"', show=['set name to "Mia"', "___"],
         opts=['say "Hello, name!"', 'say "Hello, {name}!"', 'say "Hello, Mia"'], answer=2),
    dict(goal="Which number makes the gate count:  1 2 3", pre="", show=["for each n from 1 to ___", "    say n"],
         opts=["2", "3", "4"], answer=2, loop=True),
]


def run_hl(code):
    with tempfile.NamedTemporaryFile("w", suffix=".hum", delete=False, encoding="utf-8") as fh:
        fh.write(code)
        path = fh.name
    r = subprocess.run([sys.executable, "-m", "humanlang", "run", path], capture_output=True, text=True, cwd=ROOT, timeout=30)
    os.unlink(path)
    if r.returncode != 0:
        raise SystemExit("puzzle failed to run:\n" + code + r.stdout + r.stderr)
    return " ".join(r.stdout.split())


def puzzle_outputs():
    outs = []
    for p in PUZZLES:
        row = []
        for o in p["opts"]:
            if p.get("loop"):
                code = f"for each n from 1 to {o}\n    say n\n"
            else:
                code = p["pre"] + "\n" + o + "\n"
            row.append(run_hl(code))
        outs.append(row)
    return outs


def q(s):
    return '"' + s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace('"', '\\"') + '"'


def lst(items):
    return "list of " + ", ".join(str(i) for i in items)


def strlist(items):
    return "list of " + ", ".join(q(i) for i in items)


def data_block():
    outs = puzzle_outputs()
    out = ["note: the code gates (the outputs below were made by really running the code in HumanLang)"]
    out.append("set pz_goal to " + strlist([p["goal"] for p in PUZZLES]))
    out.append("set pz_code_a to " + strlist([p["show"][0] for p in PUZZLES]))
    out.append("set pz_code_b to " + strlist([p["show"][1] for p in PUZZLES]))
    # a list of lists: build it row by row
    out.append("set pz_opts to empty list")
    for p in PUZZLES:
        out.append("add (" + strlist(p["opts"]) + ") to pz_opts")
    out.append("set pz_outs to empty list")
    for o in outs:
        out.append("add (" + strlist(o) + ") to pz_outs")
    out.append("set pz_answer to " + lst([p["answer"] for p in PUZZLES]))
    out.append("")
    out.append("note: what Echo says (two lines on each page)")
    out.append("set echo_a to " + strlist(["Hello! I am Echo, your guide.", "Code is just words a computer can read.", "Two gates block the way. Each one is a puzzle."]))
    out.append("set echo_b to " + strlist(["Welcome to the Motherboard!", "HumanLang writes it almost like English.", "Read the code, pick the right piece, open the gate."]))
    out.append("set echo2_a to " + strlist(["Nice! The first gate is open.", "One more gate, then the exit portal."]))
    out.append("set echo2_b to " + strlist(["Loops repeat things for you.", "Count to three and walk through."]))
    out.append("set scroll_text to " + strlist(["Scroll: say shows words on the screen.", "Scroll: set puts a value in a box with a name.", "Scroll: for each repeats a line again and again."]))
    out.append("set door_x to " + lst(lv.HUB_DOORS))
    return "\n".join(out)


def map_block(name, level, wheres):
    rows = level.text()
    w = " and ".join(f'"{k}" is the sprite {v}' for k, v in wheres)
    s = f"make a map called {name} with tile size {T}\n    where {w}\n"
    return s + "\n".join(f'    "{r}"' for r in rows) + "\n"


def lists(level_name, L):
    d = {}
    d["COIN_X"] = lst([x for x, _ in L.coins])
    d["COIN_Y"] = lst([y for _, y in L.coins])
    d["COIN_GOT"] = lst([0] * len(L.coins))
    d["DECOR_K"] = lst([k for k, _, _ in L.decor])
    d["DECOR_X"] = lst([x for _, x, _ in L.decor])
    d["DECOR_Y"] = lst([y for _, _, y in L.decor])
    return {f"{level_name}_{k}": v for k, v in d.items()}


def main():
    make_assets.build()
    sprites = open(os.path.join(HERE, "build", "sprites.hum"), encoding="utf-8").read()
    h, w1, w5 = lv.hub(), lv.world1(), lv.world5()
    maps = "\n".join([
        map_block("hubmap", h, [("C", "t_circuit"), ("^", "t_spike")]),
        map_block("w1map", w1, [("G", "t_grass"), ("D", "t_dirt"), ("E", "t_deep")]),
        map_block("w5map", w5, [("N", "t_snow"), ("S", "t_stone"), ("^", "t_spike")]),
    ])
    sub = {"SPRITES": sprites, "MAPS": maps, "DATA": data_block(),
           "HUB_W": str(lv.HUB_COLS * T), "W1_W": str(lv.W1_COLS * T), "W5_W": str(lv.W5_COLS * T),
           "GATE1_X": str(lv.W1_GATE1_X), "GATE2_X": str(lv.W1_GATE2_X), "ECHO_X": str(lv.W1_ECHO_X), "PORTAL_X": str(lv.W1_PORTAL_X),
           "W5_GOAL": str(lv.W5_GOAL_X), "HUB_DOOR1": str(lv.HUB_DOORS[0] + 6), "HUB_DOOR5": str(lv.HUB_DOORS[4] + 6)}
    sub.update(lists("W1", w1))
    sub.update(lists("W5", w5))
    sub["W1_SCROLL_X"] = lst([x for x, _ in w1.scrolls])
    sub["W1_SCROLL_Y"] = lst([y for _, y in w1.scrolls])
    sub["W5_BUG_X"] = lst([b[0] for b in w5.bugs])
    sub["W5_BUG_LO"] = lst([b[0] for b in w5.bugs])
    sub["W5_BUG_HI"] = lst([b[1] for b in w5.bugs])
    sub["W5_BUG_Y"] = lst([b[2] for b in w5.bugs])
    sub["W5_BUG_DIR"] = lst([1] * len(w5.bugs))
    sub["W5_BUG_ALIVE"] = lst([1] * len(w5.bugs))
    sub["W5_FLAG_X"] = lst([f[0] for f in w5.flags])
    sub["W5_FLAG_Y"] = lst([f[1] for f in w5.flags])
    sub["W5_FLAG_ON"] = lst([0] * len(w5.flags))
    text = open(os.path.join(HERE, "logic.hum"), encoding="utf-8").read()
    for k, v in sub.items():
        text = text.replace("{{" + k + "}}", v)
    if "{{" in text:
        i = text.index("{{")
        raise SystemExit("unfilled placeholder: " + text[i:i + 40])
    out = os.path.join(ROOT, "games", "humanlang_odyssey.hum")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("wrote", out, len(text) // 1024, "KB")


if __name__ == "__main__":
    main()

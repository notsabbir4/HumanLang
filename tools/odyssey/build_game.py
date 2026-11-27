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
    # World 1: pick the line (each choice is run for real)
    dict(goal="Which line makes the gate say:  Hello, Mia!", pre='set name to "Mia"', show=['set name to "Mia"', "___"],
         opts=['say "Hello, name!"', 'say "Hello, {name}!"', 'say "Hello, Mia"'], answer=2),
    dict(goal="Which number makes the gate count:  1 2 3", pre="", show=["for each n from 1 to ___", "    say n"],
         opts=["2", "3", "4"], answer=2, loop=True),
    # World 2: lists
    dict(goal="Which number makes the gate say:  fig", pre='set fruits to list of "pear", "fig", "plum"', show=['set fruits to list of "pear", "fig", "plum"', "say item ___ of fruits"],
         opts=["1", "2", "3"], answer=2, tpl="say item {o} of fruits"),
    dict(goal="What will the gate print?", predict='say length of list of 5, 6, 7, 8', show=["say length of list of 5, 6, 7, 8", ""],
         opts=["3", "4", "8"], answer=2),
    # World 3: words and numbers
    dict(goal="What will the gate print?", predict='set word to "robot"\nsay first 3 letters of word', show=['set word to "robot"', "say first 3 letters of word"],
         opts=["rob", "bot", "ro"], answer=1),
    dict(goal="What will the gate print?", predict='set a to 6\nsay a * a - 6', show=["set a to 6", "say a * a - 6"],
         opts=["12", "30", "36"], answer=2),
]


PAINT_1 = [  # 4 red, 2 white, 0 nothing: a heart (8 x 8)
    "00000000",
    "04400440",
    "04244440",
    "04444440",
    "00444400",
    "00044000",
    "00000000",
    "00000000",
]
PAINT_2 = [  # 1 blue, 2 white, 3 yellow, 0 nothing: the HL badge (12 x 12)
    "000000000000",
    "011111111110",
    "012121211110",
    "012121211110",
    "012121211110",
    "012221211110",
    "012121211110",
    "012121222110",
    "011111111110",
    "000000000000",
    "033333333330",
    "000000000000",
]
PAINT_T1 = [int(ch) for row in PAINT_1 for ch in row]
PAINT_T2 = [int(ch) for row in PAINT_2 for ch in row]


def run_hl(code):
    code = "use text\nuse math\n" + code
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
            if p.get("predict"):
                code = p["predict"] + "\n"
            elif p.get("tpl"):
                code = p["pre"] + "\n" + p["tpl"].format(o=o) + "\n"
            elif p.get("loop"):
                code = f"for each n from 1 to {o}\n    say n\n"
            else:
                code = p["pre"] + "\n" + o + "\n"
            row.append(run_hl(code))
        outs.append(row)
    return outs


def q(s):
    return '"' + s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace('"', '\\"') + '"'


def lst(items):
    if not items:
        return "empty list"
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
    out.append("note: what Echo says in each world (two lines on each page)")
    pages = {
        "echo_a_all": [["Hello! I am Echo, your guide.", "Code is just words a computer can read.", "Two gates block the way. Each one is a puzzle."],
                       ["This is the factory. Machines use lists.", "Item 1 is the first thing in a list.", "Pits, bugs and gates. Take your time."],
                       ["Welcome to Word and Number Town!", "Text can be cut into pieces.", "Gates, pits and bugs again. You can do it."]],
        "echo_b_all": [["Welcome to the Motherboard!", "HumanLang writes it almost like English.", "Read the code, pick the right piece, open the gate."],
                       ["A list keeps many things in one box.", "Read the code, pick a number, open the gate.", "Jump on the blocks to find the scrolls."],
                       ["Here the code works with text and sums.", "Numbers can be added, taken away or multiplied.", "Predict what the code prints, then answer."]],
        "echo2_a_all": [["Nice! The first gate is open.", "One more gate, then the exit portal."],
                        ["The first gate is open. Well done!", "Lists can be counted too."],
                        ["The first gate is open!", "One more gate, then the portal."]],
        "echo2_b_all": [["Loops repeat things for you.", "Count to three and walk through."],
                        ["Ask a list how long it is: length of.", "Predict what the code prints."],
                        ["Multiply goes before add and take away.", "Work it out, then choose."]],
    }
    for name, rows in pages.items():
        out.append(f"set {name} to empty list")
        for r in rows:
            out.append(f"add ({strlist(r)}) to {name}")
    out.append("set scroll_text to " + strlist([
        "Scroll: say shows words on the screen.", "Scroll: set puts a value in a box with a name.", "Scroll: for each repeats a line again and again.",
        "Scroll: item 1 is the first item of a list.", "Scroll: add puts a new item at the end of a list.", "Scroll: length of tells how many items a list has.",
        "Scroll: first 3 letters of cuts a word short.", "Scroll: * goes before + and -, like in maths.", "Scroll: mod gives what is left after dividing."]))
    out.append("set door_x to " + lst(lv.HUB_DOORS))
    import math as _m
    out.append("set fw_dx to " + lst([round(_m.cos(i * _m.pi / 8), 3) for i in range(16)]))
    out.append("set fw_dy to " + lst([round(_m.sin(i * _m.pi / 8), 3) for i in range(16)]))
    out.append("set fw_col to " + strlist(["#FF5FA8", "#7FE8FF", "#C58CFF", "#FFE680", "#8FF2AE", "#FFFFFF"]))
    out.append("set done_lines to " + strlist(["You said hello to HumanLang!", "You can read lists now!", "Words and numbers are no problem!", "You painted with pixels!",
                                               "You climbed the Platform Peaks!", "The Citadel is free!", "You are a HumanLang builder!"]))
    out.append("set paint_pal to " + strlist(["#2EB2F5", "#F6F8FF", "#FFD95C", "#E43A4C"]))
    out.append("set paint_cols to " + strlist(["#141C3E", "#2EB2F5", "#F6F8FF", "#FFD95C", "#E43A4C"]))
    out.append("set paint_t1 to " + lst(PAINT_T1))
    out.append("set paint_t2 to " + lst(PAINT_T2))
    out.append("set user_letters to " + strlist(["G", "D", "S", "^", "c", "F"]))
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


def gw_loader():
    out = ["define load_gw_data with n"]
    worlds = {1: lv.world1(), 2: lv.world2(), 3: lv.world3()}
    for n, L in worlds.items():
        g = lv.GATE_WORLDS[n]
        out.append(("    if n is 1" if n == 1 else f"    otherwise if n is {n}" if n == 2 else "    otherwise"))
        rows = [
            f"change world_w to {g['cols'] * T}", f"change echo_x to {g['echo']}", f"change g1_x to {g['g1']}", f"change g2_x to {g['g2']}",
            f"change portal_x to {g['portal']}",
            "change coin_x to " + lst([x for x, _ in L.coins]), "change coin_y to " + lst([y for _, y in L.coins]),
            "change coin_got to " + lst([0] * len(L.coins)),
            "change decor_k to " + lst([k for k, _, _ in L.decor]), "change decor_x to " + lst([x for _, x, _ in L.decor]),
            "change decor_y to " + lst([y for _, _, y in L.decor]),
            "change scroll_x to " + lst([x for x, _ in L.scrolls]), "change scroll_y to " + lst([y for _, y in L.scrolls]),
            "change bug_x to " + lst([b[0] for b in L.bugs]), "change bug_lo to " + lst([b[0] for b in L.bugs]),
            "change bug_hi to " + lst([b[1] for b in L.bugs]), "change bug_y to " + lst([b[2] for b in L.bugs]),
            "change bug_dir to " + lst([1] * len(L.bugs)), "change bug_alive to " + lst([1] * len(L.bugs)),
            "change flag_x to " + lst([f[0] for f in L.flags]), "change flag_y to " + lst([f[1] for f in L.flags]),
            "change flag_on to " + lst([0] * len(L.flags)),
        ]
        out += ["        " + r for r in rows]
    return "\n".join(out)


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "patch_logic.py")], check=True, cwd=HERE)
    make_assets.build()
    sprites = open(os.path.join(HERE, "build", "sprites.hum"), encoding="utf-8").read()
    h, w1, w2, w3, w5, w6 = lv.hub(), lv.world1(), lv.world2(), lv.world3(), lv.world5(), lv.arena()
    user = lv.Level(lv.USER_COLS, "w7")
    maps = "\n".join([
        map_block("hubmap", h, [("H", "t_hub"), ("J", "t_hub_alt"), ("h", "t_hub_in"), ("k", "t_hub_in_alt")]),
        map_block("w1map", w1, [("G", "t_grass"), ("D", "t_dirt"), ("E", "t_deep")]),
        map_block("w2map", w2, [("M", "t_metal"), ("m", "t_metal_in"), ("^", "t_spike")]),
        map_block("w3map", w3, [("G", "t_grass"), ("D", "t_dirt"), ("E", "t_deep"), ("^", "t_spike")]),
        map_block("w5map", w5, [("N", "t_snow"), ("S", "t_stone"), ("^", "t_spike")]),
        map_block("w6map", w6, [("C", "t_circuit"), ("S", "t_metal")]),
        "make a map called usermap with tile size 16\n    where \"G\" is the sprite t_grass and \"D\" is the sprite t_dirt and \"S\" is the sprite t_stone and \"^\" is the sprite t_spike and \"c\" is the sprite coin and \"F\" is the sprite star\n"
        + "\n".join(f'    "{r}"' for r in lv.user_start()) + "\n",
    ])
    sub = {"SPRITES": sprites, "MAPS": maps, "DATA": data_block(), "GW_LOADER": gw_loader(),
           "HUB_W": str(lv.HUB_COLS * T), "CHIP_X": str(lv.HUB_DOORS[3] + 25 - 38),
           "HUB_DECOR_K": lst([k for k, _, _ in lv.hub_decor()]), "HUB_DECOR_X": lst([x for _, x, _ in lv.hub_decor()]),
           "HUB_DECOR_Y": lst([y for _, _, y in lv.hub_decor()]), "W5_W": str(lv.W5_COLS * T), "W5_GOAL": str(lv.W5_GOAL_X)}
    sub.update(lists("W5", w5))
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

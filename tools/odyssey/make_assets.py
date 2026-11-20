"""Writes every sprite of HumanLang Odyssey as HumanLang source (pixel size 1) into build/sprites.hum, plus previews."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
import art
import hero
from pixelkit import Sheet, load, trim, main_part, harden, resize, put, palette_of, preview

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "build")
os.makedirs(OUT, exist_ok=True)


def build():
    sh = Sheet()
    prev = {}

    def add(name, frames, colours=24, note=None):
        frames = [f.image() if hasattr(f, "image") else f for f in (frames if isinstance(frames, (list, tuple)) else [frames])]
        sh.sprite(name, frames, colours, note)
        prev[name] = frames

    # ---- the hero: the HL mascot, from the project's own reaction pictures ----
    f = hero.frames()
    names = ["idle", "run1", "run2", "jump", "hurt", "cheer"]
    add("hero", [f[n] for n in names], 34, "The hero: the HL mascot (6 frames: stand, run, run, jump, hurt, cheer). Converted from the mascot pictures, pixel size 1.")
    # ---- the title picture and the logo ----
    thumbs = trim(main_part(harden(load(os.path.join(ROOT, "website", "static", "mascot", "thumbs.png")))))
    th = resize(thumbs, round(thumbs.width * 112 / thumbs.height), 112)
    add("title_hero", [th], 36, "The big mascot on the title screen.")
    logo = trim(load(os.path.join(ROOT, "assets", "logo.png")))
    lw = 232
    lg = resize(logo, lw, round(logo.height * lw / logo.width))
    add("logo", [lg], 22, "The HumanLang wordmark.")

    # ---- characters and things you meet ----
    add("echo", [art.robot_echo(0), art.robot_echo(1)], 30, "Echo, the friendly guide robot (2 frames: normal, happy and waving).")
    add("gate", [art.gate(0), art.gate(1)], 28, "The code gate (frame 1 closed, frame 2 open).")
    add("portal", [art.portal(0), art.portal(1), art.portal(2)], 28, "The exit portal (3 frames).")
    add("goal", [art.goal(0), art.goal(1)], 30, "The Compiler Gate at the end of a world (2 frames).")
    doors = [art.door(c) for c in ("green", "orange", "blue", "pink", "purple", "red", "gold")] + [art.door("x", True)]
    add("door", doors, 40, "The seven doors of the hub (frames 1 to 7 are open, in the colour of their world; frame 8 is locked).")
    add("tower", [art.tower(0), art.tower(1)], 26, "A server tower with blinking lights.")
    add("bug", [art.bug(0), art.bug(1)], 24, "A glitch bug (2 frames).")
    add("flag", [art.flag(0), art.flag(1)], 24, "A checkpoint flag (2 frames).")
    add("coin", [art.coin(i) for i in range(4)], 14, "A spinning coin (4 frames).")
    add("heart", [art.heart(full=True), art.heart(full=False)], 14, "Health: a full and an empty heart.")
    add("scroll", [art.scroll(0), art.scroll(1)], 22, "A scroll of code (2 frames: still, glowing).")
    add("star", [art.star()], 10)
    add("padlock", [art.padlock()], 10)
    add("sign", [art.sign()], 16, "A signpost.")

    # ---- the ground and the scenery ----
    add("t_grass", [art.tile_grass()], 20, "Tiles are 16 x 16.")
    add("t_dirt", [art.tile_dirt()], 14)
    add("t_deep", [art.tile_dirt(3, True)], 14)
    add("t_stone", [art.tile_stone()], 14)
    add("t_snow", [art.tile_stone(snow=True)], 18)
    add("t_spike", [art.tile_spike()], 12)
    add("t_circuit", [art.tile_circuit()], 14)
    add("tree", [art.tree()], 30, "Scenery.")
    add("pine", [art.pine()], 24)
    add("bush", [art.bush()], 20)
    add("flower_a", [art.flower("pink")], 12)
    add("flower_b", [art.flower("orange", seed=12)], 12)
    add("tuft", [art.tuft()], 8)
    add("rock", [art.rock()], 12)
    add("cloud_a", [art.cloud(74, 28, 1)], 12)
    add("cloud_b", [art.cloud(48, 20, 2)], 12)
    add("mtn_far", [art.mountains(224, 110, 14, "stone", True, 3)], 22, "Far mountains (they scroll slowly).")
    add("mtn_near", [art.mountains(224, 92, 3, "rock", True, 4)], 22, "Near mountains.")
    add("hills", [art.hills(224, 58)], 12)
    with open(os.path.join(OUT, "sprites.hum"), "w", encoding="utf-8") as fh:
        fh.write(sh.text())
    sizes = {k: (v[0].size, len(v)) for k, v in prev.items()}
    return prev, sizes


if __name__ == "__main__":
    prev, sizes = build()
    for k, v in sizes.items():
        print(f"{k:10s} {v[0][0]:3d}x{v[0][1]:3d}  frames {v[1]}")
    big = ["hero", "title_hero", "logo", "echo", "gate", "portal", "goal", "door", "tower", "bug", "flag"]
    for n in big:
        preview(prev[n], os.path.join("/tmp/g/od", "p_" + n + ".png"), scale=4)
    print(os.path.getsize(os.path.join(OUT, "sprites.hum")) // 1024, "KB of sprites")

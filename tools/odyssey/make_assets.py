"""Writes every sprite of HumanLang Odyssey as HumanLang source (pixel size 1) into build/sprites.hum, plus previews."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
import art
import hero
import hero2
import bgs
import art2
import hubart
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
    f = hero2.frames()
    add("hero", [f[n] for n in hero2.NAMES], 40, "The hero: the HL mascot, from your sprite sheet (11 frames: 1 stand, 2-6 run, 7 jump up, 8 top of the jump, 9 fall, 10 hurt, 11 cheer). Pixel size 1.")
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
    doors = [hubart.portal_door(i, st) for i in range(1, 8) for st in (0, 1, 2)]
    add("portal_door", doors, 60, "The seven arched doors of the hub, 3 frames each: waiting (2 shimmer frames) and finished (lit). Each shows a peek of its world.")
    add("city_far", [hubart.skyline_far()], 14, "The far city skyline of the hub.")
    add("city_near", [hubart.skyline_near(0), hubart.skyline_near(1), hubart.skyline_near(2)], 40, "The near city of the hub: 3 frames, more windows light up as you finish worlds.")
    add("chip", [hubart.chip_tower(0), hubart.chip_tower(1)], 30, "The chip tower in the middle of the Motherboard.")
    add("t_hub", [hubart.tile_hub(True)], 20, "Hub path tiles.")
    add("t_hub_alt", [hubart.tile_hub(True, alt=True)], 20)
    add("t_hub_in", [hubart.tile_hub(False)], 20)
    add("t_hub_in_alt", [hubart.tile_hub(False, alt=True)], 20)
    add("terminal", [hubart.terminal()], 14, "A little computer with a smile.")
    add("dish", [hubart.dish(0), hubart.dish(1)], 14, "A satellite dish.")
    add("fern", [hubart.fern(0), hubart.fern(1)], 14, "A glowing plant.")
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
    add("bg_meadow", [bgs.meadow()], 56, "World 1 and the title screen: your meadow picture, cut to 600 x 224. It slides slowly behind the level.")
    add("bg_snow", [bgs.snow()], 56, "World 5: your snowy sunset picture, cut to 600 x 224.")
    # ---- worlds 2, 3, 4, 6 and 7 ----
    add("t_metal", [art2.tile_metal(True)], 18, "Factory floor (World 2).")
    add("t_metal_in", [art2.tile_metal(False)], 14)
    add("house_a", [art2.house(0)], 28, "Town houses (World 3).")
    add("house_b", [art2.house(1)], 28)
    add("gear", [art2.gear(0), art2.gear(1)], 12, "A turning gear (2 frames).")
    add("crate", [art2.crate()], 10)
    add("lamp", [art2.lamp()], 12, "A street lamp.")
    add("boss", [art2.boss(0), art2.boss(1)], 26, "The Glitch King, boss of World 6 (2 frames).")
    add("bolt", [art2.bolt(0), art2.bolt(1)], 14, "An error bolt (2 frames).")
    add("warn", [art2.warn()], 10, "The marker that shows where a bolt will land.")
    add("easel", [art2.easel()], 14, "A painter's easel.")
    with open(os.path.join(OUT, "sprites.hum"), "w", encoding="utf-8") as fh:
        fh.write(sh.text())
    sizes = {k: (v[0].size, len(v)) for k, v in prev.items()}
    return prev, sizes


if __name__ == "__main__":
    prev, sizes = build()
    for k, v in sizes.items():
        print(f"{k:10s} {v[0][0]:3d}x{v[0][1]:3d}  frames {v[1]}")
    big = ["hero", "title_hero", "logo", "echo", "gate", "portal", "goal", "portal_door", "tower", "bug", "flag"]
    for n in big:
        preview(prev[n], os.path.join("/tmp/g/od", "p_" + n + ".png"), scale=4)
    print(os.path.getsize(os.path.join(OUT, "sprites.hum")) // 1024, "KB of sprites")

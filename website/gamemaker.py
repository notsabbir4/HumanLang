"""Game Maker as an interactive course: sprites, keys, the game loop, maps, physics, sound and sharing.

Every exercise is CHECKED BY RUNNING IT in HumanLang (tests/test_courses_interactive.py): a game question is answered by really running the
game for some frames with the keys held, a fill-in-the-blank makes a real game, a bug is on the line HL points at.
The shared parts (how an exercise is written, checked and exported) are in website/coursekit.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coursekit import B, C, F, GV, K, O, P, T, W, export_json as _export_json, part, rich_run as run, unit  # noqa: E402,F401

COURSE = {"id": "game-maker", "name": "Game Maker", "key": "hl-game-maker", "exam": 20,
          "lead": "Make your own 2D game in plain words: sprites, keys, maps, physics and sound. You follow real games frame by frame. Tests after each unit, a grade and a certificate."}

SKILLS = {
    "sprite": "Sprites", "game": "The game and its screen", "draw": "Drawing in a game", "keys": "Keys and moving", "var": "Set or change",
    "parts": "The parts of a game", "map": "Maps and tiles", "hit": "Hitting things", "body": "Bodies and physics", "sound": "Sound and music",
    "share": "Sharing a game", "debug": "Finding mistakes",
}

TAGS = {
    "sprite-word": ("sprite", "A sprite is made with: make a sprite called name. Then a where line, then one text per row."),
    "sprite-dot": ("sprite", 'In a sprite, a dot "." means "nothing here" (see-through).'),
    "sprite-rows": ("sprite", "Every row of a sprite must be the same length."),
    "game-word": ("game", 'A game starts with: play a game titled "Name" with size 320 by 240.'),
    "game-size": ("game", "size 320 by 240 means 320 wide and 240 tall, measured in dots."),
    "game-parts": ("game", "The parts of a game are indented under play a game."),
    "draw-spot": ("draw", "draw the sprite ship at x, y puts the sprite at that spot. x is across, y is down from the top."),
    "draw-name": ("draw", "The sprite name must be one you made. HL suggests the nearest name."),
    "y-down": ("keys", "y counts DOWN from the top of the screen, so up means a smaller y."),
    "key-word": ("keys", 'Keys are written in quotes: key "left" is down.'),
    "key-name": ("keys", "The key names are left, right, up, down, space, enter, escape, shift, a to z and 0 to 9."),
    "move-sign": ("keys", "Plus moves right (or down). Minus moves left (or up)."),
    "set-vs-change": ("var", "Inside a game part, set makes a new little variable that is forgotten. Use change to update a variable made before."),
    "var-first": ("var", "Make a variable with set before the game, then change it inside the game."),
    "part-start": ("parts", "when the game starts runs once, before the first picture."),
    "part-frame": ("parts", "every frame runs about 60 times a second, once for each picture."),
    "part-key": ("parts", 'when the key "space" is pressed runs once each time the key goes down. Holding it does not repeat.'),
    "part-seconds": ("parts", "every 2 seconds runs once every 2 seconds (any number)."),
    "part-order": ("parts", "A game part runs again and again. Variables carry the result from one frame to the next."),
    "map-tiles": ("map", "A map is a grid of tiles. Each letter is one tile, and where says what the letter is."),
    "map-spot": ("map", "tile at x, y of level is the letter on the map at that screen spot."),
    "map-change": ("map", 'change tile at x, y of level to "." changes one tile. The new letter must be in the where line (a dot is always allowed).'),
    "map-draw": ("map", "draw the map level puts the map on the screen, every frame."),
    "hit-touch": ("hit", "the sprite a at x, y touches the sprite b at p, q is yes when the two pictures overlap."),
    "hit-stop": ("hit", "stop the game ends the game. The last picture stays."),
    "body-make": ("body", "make a body called hero at x, y with size w by h makes something that can run, jump and fall."),
    "body-update": ("body", "update the body hero on the map level with solid \"#\" moves it one step each frame. Without it nothing moves."),
    "body-jump": ("body", "A body can jump only from the ground. In the air use bounce."),
    "sound-word": ("sound", 'play the sound "coin" plays a short sound. play the music "adventure" plays a tune.'),
    "sound-names": ("sound", "Built-in sounds: jump, coin, hit, shoot, explosion, powerup, win, lose, beep, blip, step."),
    "share-build": ("share", "hl build mygame.hum saves the whole game as one web page you can send to anyone."),
    "share-offline": ("share", "hl build mygame.hum --offline makes a page that works with no internet."),
    "debug-line": ("debug", "The message names the line. Look at that line first."),
    "debug-did-you-mean": ("debug", 'When HL says Did you mean "...", it is nearly always a typing mistake.'),
    "other": ("game", "Follow the game frame by frame, and keep track of every variable."),
}

DOT = 'make a sprite called dot\n    where "d" is white\n    "d"\n'


def G(pre, *body, size="100 by 100"):
    """A tiny game around some parts: pre = lines before it, body = lines inside play a game (4 spaces are added)."""
    return DOT + pre + f'play a game titled "T" with size {size}\n' + "\n".join("    " + b for b in body)


# =====================================================================================================
U1 = unit(1, "Your first game", "Make a sprite and put it on the screen.", [
    part("Sprites", '''
A game is made of a few simple pieces. The first is a **sprite**: a small picture made of squares, like the pixel art in Designer Go.

```hum
make a sprite called ship
    where "g" is lightgreen and "d" is darkgreen
    "....g...."
    "...ggg..."
    ".ggggggg."
    "ggggggggg"
    "gdgdgdgdg"
```

A `where` line says what each letter means. Then comes **one text for each row**. A dot `.` means nothing there. Every row must be the same length.
''',
         F('make a ___ called ship\n    where "g" is green\n    "gg"\n    "gg"', ["sprite"], "sprite", "make a sprite called name makes a picture you can use in the game.",
           wrong=[(r"^(picture|image|shape|pixel|character|player)$", "sprite-word")]),
         C('In a sprite, what does a dot  "."  mean?', "Nothing here (see-through)", [("A black square", "sprite-dot"), ("The end of the row", "sprite-dot"), ("An error", "sprite-dot")], "sprite",
           "A dot is empty: you can see through it."),
         B('make a sprite called s\n    where "a" is red\n    "aa"\n    "a"', 4, "sprite", "Every row must be the same length. The last row has 1 letter but the first has 2.", '    "aa"'),
         W('Write the where line that makes the letter "b" blue', ['where "b" is blue'], "sprite", 'where "b" is blue says what b means.', ctx='make a sprite called s\n    "bb"', indent=1,
           wrong=[(r'^"b" is blue', "sprite-word"), (r"^where b ", "sprite-word")])),
    part("The game and the screen", '''
Now put it in a game. `play a game` says how big the screen is. Inside it, `every frame` runs again and again (about 60 times a second, once for each picture). `draw the sprite` puts a sprite on the screen:

```hum-game
make a sprite called ship
    where "g" is lightgreen and "d" is darkgreen
    "....g...."
    "...ggg..."
    ".ggggggg."
    "ggggggggg"
    "gdgdgdgdg"

play a game titled "Hello" with size 320 by 240 and background black
    every frame
        draw the sprite ship at 140, 200
```

`size 320 by 240` is the width by the height. The spot `140, 200` is **140 across and 200 down** from the top left corner.
''',
         F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a ___ titled "T" with size 100 by 100\n    every frame\n        draw the sprite dot at 5, 5', ["game"], "game", "play a game starts the game.",
           wrong=[(r"^(level|screen|app|window)$", "game-word")]),
         W('Inside every frame, draw the sprite dot at 10, 20', ['draw the sprite dot at 10, 20'], "draw", "draw the sprite name at x, y.", ctx=DOT + 'play a game titled "T" with size 100 by 100\n    every frame',
           indent=2, wrong=[(r"^draw dot", "draw-spot"), (r"^draw the dot", "draw-spot"), (r"at 20, 10", "draw-spot")]),
         B(G("set x to 1\n", "every frame", "    draw the sprite dott at x, 5"), 7, "debug", 'The sprite is called dot. HL says: Did you mean "dot"?', '        draw the sprite dot at x, 5'),
         C("In  size 320 by 240  what is 240?", "How tall the screen is", [("How wide the screen is", "game-size"), ("How fast the game runs", "game-size"), ("How many sprites there are", "game-size")], "game",
           "size is width by height, so 240 is the height."),
         ),
], [
    P(G("set x to 1\n", "every frame", "    draw the sprite dott at x, 5"), 'Line 7: I don\'t know a sprite called "dott".',
      [("Line 5: I don't know a sprite called \"dott\".", "debug-line"), ("Nothing: the game works", "draw-name"), ('Line 7: I don\'t know "x".', "draw-name")], "debug",
      "The sprite dott does not exist. HL points at line 7 and suggests dot.", error=True),
    F('make a sprite called dot\n    ___ "d" is white\n    "d"', ["where"], "sprite", 'where "d" is white says what the letter d means.', wrong=[(r"^(with|is|colour)$", "sprite-word")]),
    F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by ___\n    every frame\n        draw the sprite dot at 5, 5', ["100"], "game", "size is width by height: size 100 by 100.",
      q="Make the screen 100 tall"),
    C("Which line starts a game?", 'play a game titled "Hi" with size 100 by 100', [('make a game called "Hi"', "game-word"), ('start the game "Hi"', "game-word"), ('game "Hi" size 100', "game-word")], "game",
      'It is: play a game titled "..." with size W by H.'),
    C("How often does every frame run?", "About 60 times a second", [("Once", "part-frame"), ("Once a second", "part-frame"), ("Only when a key is pressed", "part-frame")], "game", "Once for each picture: about 60 times a second."),
    C('The spot  at 5, 40  is...', "5 across and 40 down", [("5 down and 40 across", "draw-spot"), ("5 up and 40 across", "draw-spot"), ("In the middle", "draw-spot")], "draw", "x (across) comes first, then y (down)."),
    B('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        draw the sprite dot at', 6, "draw", "draw the sprite needs a spot: at x, y.", '        draw the sprite dot at 5, 5'),
    W('Draw the sprite dot at 50, 50', ['draw the sprite dot at 50, 50'], "draw", "draw the sprite dot at 50, 50.", ctx=DOT + 'play a game titled "T" with size 100 by 100\n    every frame', indent=2,
      wrong=[(r"^draw the sprite dot 50", "draw-spot")]),
])

U2 = unit(2, "Move with the keys", "Make the sprite move when a key is held down.", [
    part("Keys", '''
A game checks the keys again on every frame. If a key is held down, change the position a little. Do this 60 times a second and the sprite slides:

```hum-game
make a sprite called ship
    where "g" is lightgreen
    "..g.."
    ".ggg."
    "ggggg"

set x to 140

play a game titled "Move" with size 320 by 240 and background black
    every frame
        if key "left" is down
            change x to x - 3
        if key "right" is down
            change x to x + 3
        draw the sprite ship at x, 200
```

**Use `change`, not `set`,** to update a number you made before the game. Inside a game part, `set` makes a new little variable that is forgotten when the part ends.
''',
         GV(G("set x to 10\n", "every frame", "    if key \"right\" is down", "        change x to x + 3", "    draw the sprite dot at x, 50"), "x", 10, "40", ["10", "13", "30"], "keys",
            "10 frames, each adds 3 to x: 10 + 30 = 40.", down=["right"], q="Hold the right key for 10 frames. What is inside x then?"),
         GV(G("set x to 50\n", "every frame", "    if key \"left\" is down", "        change x to x - 2", "    draw the sprite dot at x, 50"), "x", 10, "30", ["70", "48", "50"], "keys",
            "10 frames, each takes 2 away from x: 50 - 20 = 30.", down=["left"], q="Hold the left key for 10 frames. What is inside x then?"),
         F('set x to 10\nmake a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        if ___ "left" is down\n            change x to x - 3\n        draw the sprite dot at x, 50', ["key"], "keys",
           'if key "left" is down is the question for a held key.', wrong=[(r"^(button|press|pressed|keys)$", "key-word")]),
         GV(G("set x to 10\n", "every frame", "    if key \"right\" is down", "        set x to x + 3", "    draw the sprite dot at x, 50"), "x", 10, "10", ["40", "13", "30"], "var",
            "set only makes a new little variable that is forgotten. The real x never changes. Use change.", down=["right"], q="Hold the right key for 10 frames. What is inside x then?")),
    part("Up and down", '''
`y` counts **down** from the top of the screen. So to move up, make y **smaller**. The key names are `left`, `right`, `up`, `down`, `space`, `enter`, `escape`, `shift`, `a` to `z` and `0` to `9`.

If a key name is wrong, HL tells you:

```hum-error
make a sprite called dot
    where "d" is white
    "d"
set x to 1
play a game titled "T" with size 100 by 100
    every frame
        if key "lefft" is down
            change x to x + 1
        draw the sprite dot at x, 5
```
''',
         W('Write the line that moves up (make y smaller by 3)', ['change y to y - 3'], "keys", "Up means a smaller y, so take 3 away: change y to y - 3.",
           ctx=DOT + 'set y to 50\nplay a game titled "T" with size 100 by 100\n    every frame\n        if key "up" is down', indent=3, wrong=[(r"^change y to y \+ 3", "y-down"), (r"^set ", "set-vs-change")]),
         B(G("set x to 1\n", "every frame", '    if key "lefft" is down', "        change x to x + 1", "    draw the sprite dot at x, 5"), 7, "debug", 'The key is called left. HL says: Did you mean "left"?',
           '        if key "left" is down'),
         GV(G("set y to 50\n", "every frame", "    if key \"up\" is down", "        change y to y - 3", "    draw the sprite dot at 5, y"), "y", 10, "20", ["80", "47", "50"], "keys",
            "Up makes y smaller: 10 frames of -3 is 50 - 30 = 20.", down=["up"], q="Hold the up key for 10 frames. What is inside y then?"),
         C("To move a sprite DOWN the screen you...", "Make y bigger", [("Make y smaller", "y-down"), ("Make x bigger", "y-down"), ("Make x smaller", "y-down")], "keys", "y counts down from the top, so down means a bigger y.")),
], [
    GV(G("set x to 10\n", "every frame", "    if key \"right\" is down", "        change x to x + 3", "    draw the sprite dot at x, 50"), "x", 10, "10", ["40", "13", "7"], "keys", "No key is held, so x never changes.", q="Touch no keys for 10 frames. What is inside x then?"),
    GV(G("set x to 10\n", "every frame", "    if key \"right\" is down", "        change x to x + 5", "    if key \"left\" is down", "        change x to x - 5", "    draw the sprite dot at x, 50"), "x", 4, "10", ["30", "20", "0"], "keys",
       "Both keys cancel each other: +5 and -5 every frame.", down=["right", "left"], q="Hold the right and left keys for 4 frames. What is inside x then?"),
    GV(G("set x to 80\n", "every frame", "    if key \"right\" is down", "        change x to x + 10", "    if x is greater than 90", "        change x to 90", "    draw the sprite dot at x, 50"), "x", 20, "90", ["280", "100", "80"], "keys",
       "x grows by 10, but when it is more than 90 it is set back to 90. So it stops at 90.", down=["right"], q="Hold the right key for 20 frames. What is inside x then?"),
    F('set x to 10\nmake a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        if key "right" is down\n            ___ x to x + 3\n        draw the sprite dot at x, 50',
      ["change"], "var", "change updates the variable made before the game.", wrong=[(r"^set$", "set-vs-change")]),
    F('set x to 10\nmake a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        if key "left" is down\n            change x to x ___ 3\n        draw the sprite dot at x, 50',
      ["-"], "keys", "Minus moves left: x gets smaller.", q="Make it move LEFT", wrong=[(r"^\+$", "move-sign")]),
    C("A sprite does not move even though the key works. The line says  set x to x + 3 . Why?", "set makes a new little variable, so use change", [("The key is wrong", "set-vs-change"), ("x is too small", "set-vs-change"), ("Sprites cannot move", "set-vs-change")], "var",
      "Inside a game part, set makes a variable that is forgotten at the end of the part. change updates the real x."),
    C('Which key name is NOT right?', '"jump"', [('"space"', "key-name"), ('"up"', "key-name"), ('"enter"', "key-name")], "keys", "There is no key called jump. The jump key is usually space or up."),
    W('Write the line that moves right (make x bigger by 2)', ['change x to x + 2'], "keys", "change x to x + 2.", ctx=DOT + 'set x to 5\nplay a game titled "T" with size 100 by 100\n    every frame\n        if key "right" is down', indent=3,
      wrong=[(r"^set ", "set-vs-change"), (r"x - 2", "move-sign")]),
])

U3 = unit(3, "The parts of a game", "Things that happen at the start, every frame, and on a key press.", [
    part("Start and key press", '''
A game has **parts**. Each part says when its lines run:

| Part | When it runs |
|---|---|
| `when the game starts` | once, before the first picture |
| `every frame` | about 60 times a second |
| `every 2 seconds` | every 2 seconds (any number) |
| `when the key "space" is pressed` | once each time the key goes down |
| `when the mouse is clicked` | each click on the game |

```hum-game
make a sprite called dot
    where "d" is white
    "d"

set score to 0

play a game titled "Parts" with size 200 by 120 and background navy
    when the game starts
        change score to 100
    every frame
        put a text "Score {score}" at 8, 8 with colour white
    every 2 seconds
        add 1 to score
    when the key "space" is pressed
        add 10 to score
        play the sound "coin"
```
''',
         GV(G("set score to 0\n", "when the game starts", "    change score to 100", "every frame", "    draw the sprite dot at 5, 5"), "score", 1, "100", ["0", "1", "60"], "parts",
            "when the game starts runs once, before the first picture, and sets score to 100.", q="Touch no keys and wait for 1 frame. What is inside score then?"),
         GV(G("set score to 0\n", "when the key \"space\" is pressed", "    add 10 to score", "every frame", "    draw the sprite dot at 5, 5"), "score", 5, "10", ["0", "50", "5"], "parts",
            "The key was pressed once, and the part runs once for each press. 10 is added one time.", pressed=["space"], q="Press space once, then wait for 5 frames. What is inside score then?"),
         GV(G("set score to 0\n", "every frame", "    add 1 to score", "    draw the sprite dot at 5, 5"), "score", 30, "30", ["1", "0", "60"], "parts",
            "every frame runs for every picture, and 30 pictures were drawn.", q="Touch no keys and wait for 30 frames. What is inside score then?"),
         C("Which part runs only ONCE, before the first picture?", "when the game starts", [("every frame", "part-start"), ("every 2 seconds", "part-start"), ('when the key "space" is pressed', "part-start")], "parts",
           "when the game starts runs once, at the very beginning.")),
    part("Time and the mouse", '''
`every 2 seconds` runs on a timer. `when the mouse is clicked` runs on each click, and `mouse x` and `mouse y` tell you where the click was:

```hum-game
make a sprite called dot
    where "d" is yellow
    "d"

set cx to 20
set cy to 20

play a game titled "Click me" with size 200 by 120 and background black
    when the mouse is clicked
        change cx to mouse x
        change cy to mouse y
    every frame
        draw the sprite dot at cx, cy
```
''',
         GV(G("set score to 0\n", "when the game starts", "    change score to 100", "every frame", "    add 1 to score", "    draw the sprite dot at 5, 5"), "score", 5, "105", ["100", "5", "106"], "parts",
            "The start part sets 100. After that every frame adds 1, and 5 frames were drawn: 100 + 5.", q="Touch no keys and wait for 5 frames. What is inside score then?"),
         F('make a sprite called dot\n    where "d" is white\n    "d"\nset n to 0\nplay a game titled "T" with size 100 by 100\n    ___ the game starts\n        change n to 5', ["when"], "parts", "when the game starts is a part.',",
           wrong=[(r"^(if|on|at)$", "part-start")]),
         C('How do you run something every 3 seconds?', "every 3 seconds", [("each 3 seconds", "part-seconds"), ("after 3 frames", "part-seconds"), ("every frame 3", "part-seconds")], "parts", "Write every 3 seconds, then the lines inside."),
         C("You hold the space key for a whole second. How many times does  when the key \"space\" is pressed  run?", "Once", [("60 times", "part-key"), ("Never", "part-key"), ("Twice", "part-key")], "parts",
           "It runs once each time the key goes DOWN. Holding it does not repeat. (every frame with if key is down repeats.)")),
], [
    GV(G("set n to 0\n", "every frame", "    add 2 to n", "    draw the sprite dot at 5, 5"), "n", 10, "20", ["2", "10", "12"], "parts", "10 frames, 2 each: 20.", q="Touch no keys and wait for 10 frames. What is inside n then?"),
    GV(G("set n to 5\n", "when the game starts", "    change n to n * 2", "every frame", "    draw the sprite dot at 5, 5"), "n", 3, "10", ["5", "15", "30"], "parts", "The start part runs once: 5 * 2 = 10. The frames do not change n.", q="Touch no keys and wait for 3 frames. What is inside n then?"),
    GV(G("set n to 0\n", "when the key \"a\" is pressed", "    add 1 to n", "every frame", "    draw the sprite dot at 5, 5"), "n", 6, "1", ["0", "6", "5"], "parts", "One press: the part ran once.", pressed=["a"], q="Press a once, then wait for 6 frames. What is inside n then?"),
    GV(G("set n to 0\n", "every frame", "    if key \"a\" is down", "        add 1 to n", "    draw the sprite dot at 5, 5"), "n", 6, "6", ["0", "1", "36"], "parts", "Holding a for 6 frames: the if is true on each of the 6 frames.", down=["a"],
       q="Hold the a key for 6 frames. What is inside n then?"),
    F('make a sprite called dot\n    where "d" is white\n    "d"\nset n to 0\nplay a game titled "T" with size 100 by 100\n    ___ frame\n        add 1 to n', ["every"], "parts", "every frame runs once for each picture.", wrong=[(r"^(each|per|all)$", "part-frame")]),
    F('make a sprite called dot\n    where "d" is white\n    "d"\nset n to 0\nplay a game titled "T" with size 100 by 100\n    when the ___ is clicked\n        add 1 to n', ["mouse"], "parts", "when the mouse is clicked.", wrong=[(r"^(button|screen|game|key)$", "part-key")]),
    C("Where do the parts go?", "Indented under play a game", [("Before play a game", "game-parts"), ("In a separate file", "game-parts"), ("Anywhere", "game-parts")], "game", "The parts are indented under play a game."),
    C("What are mouse x and mouse y?", "Where the last click happened", [("The size of the screen", "part-order"), ("The x and y of the ship", "part-order"), ("The speed of the mouse", "part-order")], "parts", "They tell you where the click was."),
])

U4 = unit(4, "Maps and coins", "Make a level out of tiles and collect coins.", [
    part("Maps", '''
A **map** is a grid of tiles. It works like a sprite, but each letter is one tile, and a tile can be a colour or a sprite you made before. `tile size` says how many dots wide each tile is.

```hum-game
make a sprite called coin
    where "y" is yellow
    "...yy..."
    "..yyyy.."
    ".yyyyyy."
    ".yyyyyy."
    ".yyyyyy."
    ".yyyyyy."
    "..yyyy.."
    "...yy..."

make a map called level with tile size 16
    where "#" is blue and "c" is the sprite coin
    "##########"
    "#c..c..c.#"
    "#........#"
    "##########"

set px to 20
set score to 0

play a game titled "Coins" with size 160 by 64 and background black
    every frame
        if key "right" is down
            change px to px + 2
        if key "left" is down
            change px to px - 2
        draw the map level
        put a circle at px, 24 with radius 6 and colour red
        if tile at px, 24 of level is "c"
            change tile at px, 24 of level to "."
            add 1 to score
        put a text "Coins {score}" at 6, 4 with size small and colour white
```
''',
         F('make a map called level with tile size 16\n    where "#" is blue\n    "###"\n    "#.#"\nplay a game titled "T" with size 100 by 100\n    every frame\n        draw the ___ level', ["map"], "map", "draw the map level puts the whole map on the screen.",
           wrong=[(r"^(sprite|level|tiles|grid)$", "map-draw")]),
         C('A map row is "#c..#". How many tiles is that?', "5", [("4", "map-tiles"), ("1", "map-tiles"), ("2", "map-tiles")], "map", "Each letter is one tile, so five letters are five tiles."),
         GV('make a sprite called dot\n    where "d" is white\n    "d"\nmake a map called level with tile size 16\n    where "#" is blue and "c" is the sprite dot\n    "###"\n    "#c#"\nset n to 0\nplay a game titled "T" with size 100 by 100\n    every frame\n        draw the map level\n        if tile at 24, 24 of level is "c"\n            change tile at 24, 24 of level to "."\n            add 1 to n',
            "n", 3, "1", ["0", "3", "2"], "map", "The first frame the coin is there, so n becomes 1 and the tile is changed to a dot. After that the tile is empty, so n stays 1.", q="Touch no keys and wait for 3 frames. What is inside n then?"),
         B('make a sprite called dot\n    where "d" is white\n    "d"\nmake a map called level with tile size 16\n    where "#" is blue\n    "###"\nplay a game titled "T" with size 100 by 100\n    every frame\n        change tile at 5, 5 of level to "x"', 9, "map",
           'The map has no tile called x. The new letter must be in the where line. Add: where "x" is red (or use a dot).', '        change tile at 5, 5 of level to "."')),
    part("Hitting things", '''
`the sprite ship at x, y touches the sprite alien at a, b` is `yes` when the two pictures overlap. `stop the game` ends the game (the last picture stays).

```hum-game
make a sprite called box
    where "b" is orange
    "bbbb"
    "bbbb"

set x to 10

play a game titled "Touch" with size 160 by 80 and background black
    every frame
        change x to x + 2
        draw the sprite box at x, 30
        draw the sprite box at 100, 30
        if the sprite box at x, 30 touches the sprite box at 100, 30
            stop the game
```
''',
         GV(G("set n to 0\n", "every frame", "    add 1 to n", "    if n is 3", "        stop the game", "    draw the sprite dot at 5, 5"), "n", 10, "3", ["10", "0", "2"], "hit",
            "At the third frame n is 3 and stop the game ends everything. n stays 3.", q="Touch no keys and wait for 10 frames. What is inside n then?"),
         GV(G("set hit to 0\n", "every frame", "    if the sprite dot at 5, 5 touches the sprite dot at 5, 5", "        add 1 to hit"), "hit", 5, "5", ["0", "1", "10"], "hit",
            "The two dots are at the same spot, so they touch on every frame: 5 times.", q="Touch no keys and wait for 5 frames. What is inside hit then?"),
         GV(G("set hit to 0\n", "every frame", "    if the sprite dot at 5, 5 touches the sprite dot at 80, 80", "        add 1 to hit"), "hit", 5, "0", ["5", "1", "80"], "hit",
            "The dots are far apart, so they never touch.", q="Touch no keys and wait for 5 frames. What is inside hit then?"),
         C("What does  stop the game  do?", "Ends the game; the last picture stays", [("Pauses it for one second", "hit-stop"), ("Closes the browser", "hit-stop"), ("Restarts it", "hit-stop")], "hit", "The game is over and the last picture stays on the screen.")),
], [
    GV(G("set n to 0\n", "every frame", "    add 1 to n", "    if n is 5", "        stop the game"), "n", 20, "5", ["20", "0", "4"], "hit", "At 5 the game stops.", q="Touch no keys and wait for 20 frames. What is inside n then?"),
    F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        if the ___ dot at 5, 5 touches the sprite dot at 5, 5\n            stop the game', ["sprite"], "hit", "the sprite dot at 5, 5 touches the sprite dot at 5, 5.",
      wrong=[(r"^(object|picture|image|thing)$", "hit-touch")]),
    F('make a sprite called dot\n    where "d" is white\n    "d"\nmake a map called level with tile size 16\n    where "#" is blue\n    "##"\nplay a game titled "T" with size 100 by 100\n    every frame\n        draw the map ___', ["level"], "map", "draw the map level: the name of the map.",
      wrong=[(r"^(map|tiles|grid)$", "map-draw")]),
    C('What does  tile at 20, 20 of level  give?', "The letter on the map at that spot", [("The size of the map", "map-spot"), ("The colour of the sprite", "map-spot"), ("A number", "map-spot")], "map", "It gives the letter of the tile at that screen spot."),
    C("What is the tile size?", "How many dots wide each tile is", [("How many tiles there are", "map-tiles"), ("The size of the screen", "map-tiles"), ("The size of the sprite", "map-tiles")], "map", "tile size 16 means every tile is 16 dots wide."),
    C('Which letter is always allowed in  change tile ... to  ?', 'A dot "."', [('"x"', "map-change"), ('"#"', "map-change"), ('"0"', "map-change")], "map", "A dot is always allowed. Other letters must be in the where line."),
    B('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    every frame\n        draw the map level', 6, "map", "There is no map called level. Make it first with make a map called level.", '        draw the sprite dot at 5, 5'),
    W('Change the tile at 24, 24 of level to a dot', ['change tile at 24, 24 of level to "."'], "map", 'change tile at x, y of level to ".".',
      ctx='make a map called level with tile size 16\n    where "#" is blue\n    "###"\nplay a game titled "T" with size 100 by 100\n    every frame', indent=2, wrong=[(r"^set tile", "map-change"), (r"to \.$", "map-change")]),
])

U5 = unit(5, "Physics", "A body that runs, jumps and falls for you.", [
    part("Bodies", '''
A **body** runs, jumps and falls for you, and lands on the solid tiles of a map. You only say what the person pressed.

```hum-game
make a sprite called hero
    where "g" is green
    "gggg"
    "gggg"
    "gggg"
    "gggg"

make a map called level with tile size 16
    where "#" is blue
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "..........................."
    "...........###............."
    "..........................."
    "###########################"

make a body called hero at 20, 40 with size 8 by 8

play a game titled "Physics" with size 200 by 144 and background black
    every frame
        make the body hero stop
        if key "left" is down
            make the body hero run left
        if key "right" is down
            make the body hero run right
        if key "up" is down
            make the body hero jump
        update the body hero on the map level with solid "#"
        draw the map level
        draw the sprite hero at the body hero
```

`update the body hero on the map level with solid "#"` moves it one step. Without it, nothing moves.
''',
         F('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a ___ called hero at 5, 5 with size 8 by 8\nplay a game titled "T" with size 100 by 100\n    every frame\n        update the body hero on the map level with solid "#"', ["body"], "body",
           "make a body called hero at x, y with size w by h.", wrong=[(r"^(player|sprite|character|hero|thing)$", "body-make")]),
         GV('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nset px to 0\nplay a game titled "T" with size 100 by 100\n    every frame\n        make the body hero run right\n        update the body hero on the map level with solid "#"\n        change px to the x of the body hero',
            "px", 10, "27", ["5", "10", "0"], "body", "Running right moves the body a little every frame. After 10 frames it has moved to x = 27.", q="Touch no keys and wait for 10 frames. What is inside px then?"),
         GV('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nset px to 0\nplay a game titled "T" with size 100 by 100\n    every frame\n        change px to the x of the body hero',
            "px", 10, "5", ["27", "0", "10"], "body", "Nobody told the body to run and it is never updated, so it stays at x = 5.", q="Touch no keys and wait for 10 frames. What is inside px then?"),
         C("Why does the body not move when you forget  update the body ... ?", "update is what moves the body one step each frame", [("Bodies cannot move", "body-update"), ("The map is too small", "body-update"), ("It needs a sprite first", "body-update")], "body",
           "make the body run right only says what it wants to do. update does the moving.")),
    part("Running, jumping and falling", '''
A body can `run left`, `run right`, `stop`, `jump` (only from the ground) and `bounce` (jump in the air). You can ask `the body hero is on the ground` and `the body hero is falling`.

```text
make the body hero jump
if the body hero is on the ground
    play the sound "step"
```
''',
         C("When can a body jump?", "Only from the ground", [("Any time", "body-jump"), ("Only in the air", "body-jump"), ("Only when a key is held for a second", "body-jump")], "body", "jump works only from the ground. Use bounce to jump in the air."),
         W('Write the line that makes the body hero jump', ['make the body hero jump'], "body", "make the body hero jump.",
           ctx='make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nplay a game titled "T" with size 100 by 100\n    every frame\n        if key "up" is down',
           indent=3, wrong=[(r"^hero jump", "body-make"), (r"^jump", "body-make")]),
         GV('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nset px to 0\nplay a game titled "T" with size 100 by 100\n    every frame\n        make the body hero run left\n        update the body hero on the map level with solid "#"\n        change px to the x of the body hero',
            "px", 3, "0", ["5", "3", "10"], "body", "Running left from x = 5 stops at the edge of the map (x = 0).", q="Touch no keys and wait for 3 frames. What is inside px then?"),
         C('What does  solid "#"  mean in the update line?', "The tiles with # stop the body (floor and walls)", [("The sprite is made of #", "body-update"), ("The map has a # in it", "body-update"), ("The body is made of steel", "body-update")], "body",
           'Tiles written with # are solid: the body lands on them and cannot go through.')),
], [
    C("What does a body need to land on things?", "A map with solid tiles", [("A sprite", "body-update"), ("A sound", "body-update"), ("A score", "body-update")], "body", "update the body ... on the map ... with solid ... lands it on those tiles."),
    F('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nplay a game titled "T" with size 100 by 100\n    every frame\n        make the body hero ___ right\n        update the body hero on the map level with solid "#"',
      ["run"], "body", "make the body hero run right.", wrong=[(r"^(go|move|walk|slide)$", "body-make")]),
    F('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nplay a game titled "T" with size 100 by 100\n    every frame\n        make the body hero stop\n        ___ the body hero on the map level with solid "#"',
      ["update"], "body", "update moves the body one step.", wrong=[(r"^(move|step|run|go)$", "body-update")]),
    GV('make a map called level with tile size 16\n    where "#" is blue\n    "..."\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nset py to 0\nplay a game titled "T" with size 100 by 100\n    every frame\n        change py to the y of the body hero',
       "py", 5, "5", ["0", "8", "16"], "body", "The body is never updated, so y stays at 5.", q="Touch no keys and wait for 5 frames. What is inside py then?"),
    C('What does  make the body hero stop  do?', "Stops it running left or right", [("Deletes the body", "body-make"), ("Ends the game", "body-make"), ("Stops it falling", "body-make")], "body", "It stops the sideways running. Gravity still pulls it down."),
    C("Which line draws the sprite where the body is?", "draw the sprite hero at the body hero", [("draw the body hero", "draw-spot"), ("draw the sprite hero", "draw-spot"), ("put hero on the map", "draw-spot")], "body", "draw the sprite hero at the body hero."),
    B('make a map called level with tile size 16\n    where "#" is blue\n    "###"\nmake a body called hero at 5, 5 with size 8 by 8\nplay a game titled "T" with size 100 by 100\n    every frame\n        update the body hero on the map level with solid "#"\n        make the body hero jumpp', 8, "debug",
      "The action is jump. HL says what it can do.", '        make the body hero jump'),
    C("What can a body do?", "run left, run right, stop, jump, bounce", [("fly, swim, dig", "body-make"), ("Only run", "body-make"), ("Only jump", "body-make")], "body", "run left, run right, stop, jump (from the ground) and bounce."),
])

U6 = unit(6, "Sound, camera and sharing", "Add sound, move the camera and share your game.", [
    part("Sound and the camera", '''
`play the sound "coin"` plays a short sound. The built-in sounds are `jump`, `coin`, `hit`, `shoot`, `explosion`, `powerup`, `win`, `lose`, `beep`, `blip` and `step`. There are also five tunes with no file needed: `play the music "adventure"`, `"chill"`, `"chase"`, and `"boss"` and `"doom"` for boss fights. `stop the music` stops it.

`move the camera to 100, 0` slides the view, so a level can be much wider than the screen. Text stays put, so a score never moves away.

Your own pictures and sounds go in the same folder as your program: `draw the picture "face.png" at 10, 20 with size 32 by 32` and `play the sound "boom.wav"`.
''',
         F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    when the key "space" is pressed\n        play the ___ "coin"', ["sound"], "sound", 'play the sound "coin" plays a short sound.',
           wrong=[(r"^(noise|audio|music|sfx)$", "sound-word")]),
         F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    when the game starts\n        play the ___ "adventure"', ["music"], "sound", 'play the music "adventure" plays a built-in tune.',
           wrong=[(r"^(tune|song|sound|audio)$", "sound-word")]),
         C("Which sound is NOT built in?", '"dragon"', [('"coin"', "sound-names"), ('"jump"', "sound-names"), ('"explosion"', "sound-names")], "sound", "Built in: jump, coin, hit, shoot, explosion, powerup, win, lose, beep, blip, step."),
         C("What does  move the camera to 100, 0  do?", "Slides the view 100 dots to the right", [("Moves the ship", "hit-stop"), ("Zooms in", "hit-stop"), ("Ends the game", "hit-stop")], "game",
           "The camera is the view. A level can be much wider than the screen, and text stays put.")),
    part("Sharing your game", '''
`hl build mygame.hum` saves the whole game as one web page, `mygame.html`. Put it on any website or send it to a friend: it opens in any browser. It needs the internet when it starts.

`hl build mygame.hum --offline` makes a page that works with **no internet at all** (a bigger file).

On a phone or tablet the game shows buttons on the screen for the keys it uses: arrows, A for space, B for enter. You do not have to add anything.
''',
         C("Which command saves a game as one web page?", "hl build mygame.hum", [("hl save mygame.hum", "share-build"), ("hl page mygame", "share-build"), ("hl run --web mygame", "share-build")], "share", "hl build mygame.hum makes mygame.html."),
         C("What does  --offline  add?", "The page works with no internet", [("The game is faster", "share-offline"), ("The game is smaller", "share-offline"), ("The game is secret", "share-offline")], "share", "It packs everything the page needs, so it works with no internet. The file is bigger."),
         C("Do you have to write extra code so the game works on a phone?", "No: touch buttons appear for the keys the game uses", [("Yes, a lot", "share-build"), ("Yes, a touch part", "share-build"), ("It never works on a phone", "share-build")], "share",
           "On a phone the game shows buttons on the screen for its keys."),
         B('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    when the key "space" is pressed\n        play the sond "coin"', 6, "debug", 'The word is sound. HL says: Did you mean "sound"?', '        play the sound "coin"')),
], [
    F('make a sprite called dot\n    where "d" is white\n    "d"\nplay a game titled "T" with size 100 by 100\n    when the key "space" is pressed\n        play the sound "___"', ["coin"], "sound", "coin is a built-in sound.", q='Play the sound "coin"'),
    C("Which command stops the tune?", "stop the music", [("stop the sound", "sound-word"), ("end the music", "sound-word"), ("quiet", "sound-word")], "sound", "stop the music."),
    C("Where do your own picture and sound files go?", "In the same folder as your program", [("Inside the program", "sound-word"), ("On the desktop", "sound-word"), ("In the sprite", "sound-word")], "sound", "Same folder as your program (or the Files tab in the Playground)."),
    C("Which is a built-in tune?", '"chase"', [('"coin"', "sound-names"), ('"jump"', "sound-names"), ('"hit"', "sound-names")], "sound", "The tunes are adventure, chill, chase, boss and doom. coin, jump and hit are short sounds."),
    C("Which text stays on the screen when the camera moves?", "Text, like a score", [("Sprites", "hit-stop"), ("Shapes", "hit-stop"), ("Nothing", "hit-stop")], "game", "Text always stays on the screen. Sprites and shapes move when the camera moves."),
    C("A friend has no internet. Which build do you send?", "hl build mygame.hum --offline", [("hl build mygame.hum", "share-offline"), ("hl share mygame.hum", "share-offline"), ("hl run mygame.hum", "share-offline")], "share", "--offline packs everything the page needs."),
    GV(G("set score to 0\n", "when the key \"space\" is pressed", "    add 5 to score", "    play the sound \"coin\"", "every frame", "    draw the sprite dot at 5, 5"), "score", 4, "5", ["0", "4", "20"], "sound",
       "Pressing space once adds 5 and plays the sound once.", pressed=["space"], q="Press space once, then wait for 4 frames. What is inside score then?"),
    GV(G("set n to 0\n", "every frame", "    add 1 to n", "    if n is 4", "        play the sound \"win\"", "        stop the game"), "n", 10, "4", ["10", "0", "3"], "hit", "At 4 the sound plays and the game stops.", q="Touch no keys and wait for 10 frames. What is inside n then?"),
])

UNITS = [U1, U2, U3, U4, U5, U6]


def export_json(render_markdown, highlight):
    return _export_json(sys.modules[__name__], render_markdown, highlight)

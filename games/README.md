# Games

Games written in HumanLang. They appear on the website's **Games** page, where people play them in the browser.

## Add a game

1. Put the program in this folder, for example `my_game.hum`.
2. Add an entry to `index.json`: `id` (short, no spaces), `title`, `subtitle` (optional), `file`, `tagline` (one line for the card),
   `blurb`, `tags`, `image` (a 16:9 picture in `games/thumbs/`, shown on the card and on the game page).
3. Add `test_runs` (a list of `{"ending": "NAME", "answers": [...]}`) so the test suite plays the game and checks that each
   ending can be reached. A game prints `ENDING: NAME` for each one (or give `"expect": "some text"` when an ending is announced differently). Games without endings can leave `test_runs` out.
4. Run `python -m unittest tests.test_games`. The page itself is built by `python website/build.py`.

Every game needs a `how` list for the **Inspect** button: steps of `{"title", "at", "text"}`. `at` is the start of the first line
of that step in the code (steps must be in the order they appear). Write like you are explaining to a beginner.

Arcade games (`"kind": "arcade"`, plus `"keys": "Left/Right move..."`) are drawn on a canvas and have no `test_runs`; `tests/test_arcade.py` plays them instead.
Make the thumbnail from a real screenshot of the game (16:9).

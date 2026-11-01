# Games

Games written in HumanLang. They appear on the website's **Games** page, where people play them in the browser.

## Add a game

1. Put the program in this folder, for example `my_game.hum`.
2. Add an entry to `index.json`: `id` (short, no spaces), `title`, `subtitle` (optional), `file`, `tagline` (one line for the card),
   `blurb`, `tags`.
3. Add `test_runs` (a list of `{"ending": "NAME", "answers": [...]}`) so the test suite plays the game and checks that each
   ending can be reached. A game prints `ENDING: NAME` for each one. Games without endings can leave `test_runs` out.
4. Run `python -m unittest tests.test_games`. The page itself is built by `python website/build.py`.

Games are play only on the website: there is no editor. People who want to see how one works can open the `.hum` file here.

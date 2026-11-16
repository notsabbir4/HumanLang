"""Designer Go as an interactive course: pages, looks, layout, drawings, pixel art, and pages that react.

Every exercise is CHECKED BY RUNNING IT in HumanLang (tests/test_courses_interactive.py): a fact about a page is true for the page
HL really builds, a fill-in-the-blank makes a real page, a puzzle has exactly one right order, a bug is on the line HL points at.
The shared parts (how an exercise is written, checked and exported) are in website/coursekit.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coursekit import B, C, F, K, O, P, PG, T, W, export_json as _export_json, part, rich_run as run, unit  # noqa: E402,F401

COURSE = {"id": "designer-go", "name": "Designer Go", "key": "hl-designer-go", "exam": 20,
          "lead": "Build real pages, drawings and pixel art in plain words. You see every page you make. Questions, tests after each unit, a grade and a certificate."}

SKILLS = {
    "page": "Starting a page", "put": "Putting things on a page", "indent": "Indenting page lines", "with": "Looks with with",
    "colour": "Colours", "size": "Sizes and styles", "layout": "Boxes, rows and columns", "draw": "Drawings", "shapes": "Shapes and spots",
    "pixel": "Pixel art", "react": "Pages that react", "build": "Loops and functions on pages", "debug": "Finding mistakes",
}

TAGS = {
    "page-word": ("page", 'A page starts with: show a page titled "Name".'),
    "page-title": ("page", "The title is what the browser tab shows. The big words on the page are a heading."),
    "page-empty": ("page", "Everything indented under show a page belongs to the page."),
    "put-word": ("put", 'Each thing is put on the page with: put a heading "..." (or text, button, input).'),
    "put-kind": ("put", "A heading is big text, a text is normal text, a button can be clicked, an input is a box to type in."),
    "quotes-missing": ("put", 'The words to show go inside quotes: put a heading "Hello".'),
    "indent-page": ("indent", "Lines that belong to the page are indented by 4 spaces."),
    "indent-nested": ("indent", "Something inside a box or a row is indented one more step."),
    "order-top": ("page", "The page is built from the top to the bottom, in the order you write the lines."),
    "with-word": ("with", "After a thing, write with and then what it should look like."),
    "with-join": ("with", "Join several looks with commas (or and): with bold, colour red."),
    "with-wrong-thing": ("with", "Each thing has its own looks. HL tells you which ones it can have."),
    "colour-name": ("colour", 'A colour is a name like red or sky blue, or a code like "#ff8800". Put dark, light or pale in front to change it.'),
    "colour-word": ("colour", "The look for colour is written colour (or color). background is for the colour behind."),
    "size-word": ("size", "Sizes are tiny, small, normal, big, huge, or a number of pixels."),
    "style-word": ("size", "Styles are single words: bold, italic, underlined, rounded, shadow."),
    "box-row": ("layout", "A box stacks its things from top to bottom. A row puts them side by side."),
    "columns": ("layout", "columns 3 makes a grid with 3 columns. space between sets the gap."),
    "nest": ("layout", "Put the things you want inside a box or row one step further in."),
    "drawing-first": ("draw", "Shapes go inside a drawing. Say its width and height first."),
    "at-spot": ("shapes", "at 150, 100 means 150 across and 100 down from the top left corner."),
    "shape-props": ("shapes", "Each shape has its own looks: a circle has radius, a rectangle has width and height."),
    "shape-order": ("shapes", "Shapes are drawn in the order you write them, so later ones are on top."),
    "pixel-where": ("pixel", 'Say which letter is which colour first with where "h" is brown. A dot is see-through.'),
    "pixel-rows": ("pixel", "Every row of pixel art must have the same number of letters."),
    "pixel-size": ("pixel", "pixel size makes each little square bigger."),
    "react-input": ("react", "Give a text box a name with called, then read it with the number in amount (or the text in amount)."),
    "react-when": ("react", 'A click is handled with: when the button "Add" is clicked, and the button text must match.'),
    "react-change": ("react", "Inside a when part use change (not set) to update a variable you made earlier."),
    "react-again": ("react", "After every click the page's own lines run again, so the page shows the new values."),
    "build-loop": ("build", "A for each loop inside a page puts one thing on the page for every item."),
    "build-func": ("build", "A function can put things on the page. Write it once, use it many times."),
    "debug-line": ("debug", "The message names the line. Look at that line first."),
    "debug-did-you-mean": ("debug", 'When HL says Did you mean "...", it is nearly always a typing mistake.'),
    "other": ("page", "Look at the page and read the lines again slowly."),
}

PAGE = 'show a page titled "{}"'

# =====================================================================================================
U1 = unit(1, "Your first page", "Show a page with a heading, text and a button.", [
    part("Show a page", '''
Until now HumanLang *said* things. It can also *show* things. A **page** is what you see in a browser.

```hum-page
show a page titled "My first page"
    put a heading "Hello!"
    put a text "This is my page."
    put a button "Click me"
```

`show a page titled "..."` starts the page. Every line **indented under it** goes on the page. Each `put a ...` line puts one thing on it: a `heading` (big words), a `text`, a `button`, an `input` (a box to type in).
''',
         PG('show a page titled "Shop"\n    put a heading "Welcome"\n    put a text "Open today"\n    put a button "Buy"\n    put a button "Sell"',
            "How many buttons are on this page?", ("count", "button"), "2", ["1", "3", "4"], "put",
            "Every put a button line puts one button on the page. There are two of them."),
         PG('show a page titled "Shop"\n    put a heading "Welcome"\n    put a text "Open today"\n    put a button "Buy"',
            "What does the big heading on the page say?", ("text", "h1"), "Welcome", [("Shop", "page-title"), ("Open today", "put-kind"), ("Buy", "put-kind")], "put",
            "The heading is the big text: Welcome. Shop is only the title of the page, shown on the browser tab."),
         F('show a ___ titled "Home"\n    put a heading "Welcome"', ["page"], "page", "A page starts with show a page titled ...", show=True,
           wrong=[(r"^(window|screen|site|web|website)$", "page-word")]),
         W('Add a line (inside the page) that puts a button "Play"', ['put a button "Play"'], "put", 'put a button "words" puts one button on the page.',
           ctx='show a page titled "Game"\n    put a heading "Ready?"', indent=1, show=True,
           wrong=[(r'^(button|add a button|make a button|put button)', "put-word"), (r"^put a button [^\"]", "quotes-missing")])),
    part("Order and indenting", '''
A page is built from the **top to the bottom**, in the order you write the lines. Put the heading first and it is at the top.

The things that belong to the page are **indented by 4 spaces**. If a line is not indented, HL does not know it belongs to the page, and tells you.

```hum-error
show a page titled "Oops"
put a heading "Hi"
```
''',
         O(['show a page titled "Menu"', '    put a heading "Menu"', '    put a button "Start"'], "indent",
           "The page starts first. Then the heading is above the button, because the lines run from the top down.", show=True),
         B('show a page titled "A"\n    put a buton "Go"', 2, "debug", 'The word is button. HL even says: Did you mean "button"?', '    put a button "Go"'),
         B('show a page titled "A"\nput a heading "Hi"', 2, "indent", "The heading is not indented, so it does not belong to the page. Indent it by 4 spaces.", '    put a heading "Hi"'),
         C("Which line starts a page?", 'show a page titled "Hi"', [('put a page "Hi"', "page-word"), ('make a page called "Hi"', "page-word"), ('page "Hi"', "page-word")], "page",
           'A page starts with show a page titled "...".')),
], [
    PG('show a page titled "A"\n    put a heading "One"\n    put a heading "Two"\n    put a text "Three"', "How many headings are on the page?", ("count", "h1"), "2", ["1", "3"], "put",
       "Two put a heading lines make two headings. The text is not a heading."),
    PG('show a page titled "A"\n    put a button "Yes"\n    put a button "No"\n    put a button "Maybe"', "Which buttons are on the page, from top to bottom?", ("texts", "button"),
       "Yes, No, Maybe", ["Maybe, No, Yes", "Yes, No", "No, Yes, Maybe"], "put", "They appear in the order the lines are written."),
    PG('show a page titled "Hi"\n    put a text "Welcome"', "Is there a button on this page?", ("has", "<button"), "no", ["yes"], "put", "Nothing puts a button on it. Only a text."),
    PG('show a page titled "Chat"\n    put a heading "Chat"\n    put an input with hint "Say hi"\n    put a button "Send"', "How many text boxes (inputs) are on the page?", ("count", "input"), "1", ["0", "2"], "put",
       "put an input puts one text box on the page."),
    F('show a page titled "Hi"\n    ___ a heading "Hello"', ["put"], "put", "put puts something on the page.", show=True, wrong=[(r"^(add|make|show|create)$", "put-word")]),
    W('Add a line that puts a text "Open today"', ['put a text "Open today"'], "put", 'put a text "words".', ctx='show a page titled "Shop"\n    put a heading "Welcome"', indent=1, show=True,
      wrong=[(r"^put a text [^\"]", "quotes-missing"), (r"^(text|add)", "put-word")]),
    B('show a page titled "A"\n    put a heading Hello', 2, "put", "Words to show must be in quotes. Without quotes HL thinks Hello is a name.", '    put a heading "Hello"'),
    O(['show a page titled "Todo"', '    put a heading "My list"', '    put a text "Wash up"', '    put a button "Done"'], "indent", "The page first, then the things in the order they should appear.", show=True),
])

U2 = unit(2, "Make it look good", "Colours, sizes and styles with the word with.", [
    part("With", '''
After a thing, write **with** and then what it should look like. Join several looks with commas.

```hum-page
show a page titled "Colours" with background light yellow
    put a heading "Colourful!" with colour dark blue
    put a text "Big and bold" with size big, bold
    put a button "Go" with background green, colour white, rounded, padding 12
```

Colours can be names (`red`, `dark blue`, `sky blue`, `hot pink`) or a code like `"#ff8800"`. Put `dark`, `light` or `pale` in front to change a colour.
''',
         F('show a page titled "Hi"\n    put a heading "Hello" ___ colour red', ["with"], "with", "with starts the looks of a thing.", show=True, wrong=[(r"^(using|has|and|having)$", "with-word")]),
         W('Add a text "Sale!" that is bold and has the colour red', ['put a text "Sale!" with bold, colour red', 'put a text "Sale!" with colour red, bold', 'put a text "Sale!" with bold and colour red',
                                                                    'put a text "Sale!" with colour red and bold', 'put a text "Sale!" with bold, color red', 'put a text "Sale!" with color red, bold',
                                                                    'put a text "Sale!" with bold and color red', 'put a text "Sale!" with color red and bold'],
           "with", "with bold, colour red gives two looks, joined with a comma.", ctx='show a page titled "Shop"\n    put a heading "Today"', indent=1, show=True,
           wrong=[(r'^put a text "Sale!" (bold|colour|color)', "with-word"), (r"with bold colour", "with-join"), (r"red bold", "with-join")]),
         C("Which line makes the button green with white words?", 'put a button "Go" with background green, colour white',
           [('put a button "Go" with colour green, background white', "colour-word"), ('put a button "Go" green white', "with-word"), ('put a button "Go" with green', "with-word")], "colour",
           "background is the colour behind. colour is the colour of the words.", code='show a page titled "A"\n    put a button "Go" with background green, colour white', show=True),
         PG('show a page titled "A"\n    put a text "Hello" with bold, italic\n    put a text "World" with underlined', "How many texts are on this page?", ("count", "p"), "2", ["1", "3"], "with",
            "Looks do not add things. There are still two texts.")),
    part("Colours and sizes", '''
Sizes are `tiny`, `small`, `normal`, `big`, `huge`, or a number of pixels like `size 40`.

If you ask for a colour HL does not know, it suggests the nearest one:

```hum-error
show a page titled "A"
    put a heading "Hi" with colour blurple
```
''',
         P('show a page titled "A"\n    put a heading "Hi" with colour blurple', 'Line 2: I don\'t know the colour "blurple".',
           [("Line 1: I don't know the colour \"blurple\".", "debug-line"), ("Nothing: the heading is shown in blurple", "colour-name"), ('Line 2: A heading doesn\'t have "colour".', "with-wrong-thing")],
           "colour", "blurple is not a colour HL knows. It points at line 2 and suggests purple.", error=True, q="What does HL say?"),
         B('show a page titled "A"\n    put a heading "Hi" with wobble 5', 2, "with", 'A heading cannot "wobble". HL lists what a heading can have.', '    put a heading "Hi" with size big'),
         F('show a page titled "A"\n    put a heading "Hi" with size ___', ["huge"], "size", "huge is the biggest of the size words: tiny, small, normal, big, huge.", show=True,
           q="Make the heading the biggest size word", wrong=[(r"^(large|giant|max|biggest|bigger)$", "size-word")]),
         C("Which of these is NOT a size word?", "middle", [("big", "size-word"), ("tiny", "size-word"), ("huge", "size-word")], "size", "The size words are tiny, small, normal, big and huge.")),
], [
    PG('show a page titled "A" with background light yellow\n    put a heading "Hi"', "Does the page have a heading?", ("has", "<h1"), "yes", ["no"], "with", "Yes: the colour is only the background."),
    P('show a page titled "A"\n    put a text "Hi" with colour red, huge', "Line 2: A text doesn't have \"huge\".", [("Nothing: it works", "size-word"), ("Line 1: I don't know \"huge\".", "debug-line")], "size",
      "huge is a size word, so it needs size: with size huge.", error=True, q="What does HL say?"),
    F('show a page titled "A"\n    put a heading "Hi" with ___ yellow', ["background"], "colour", "background is the colour behind the thing.", show=True, wrong=[(r"^(behind|back|bg)$", "colour-word")], q="Make the BACKGROUND yellow"),
    W('Add a heading "Big news" that is italic', ['put a heading "Big news" with italic'], "with", "with italic makes the words lean.", ctx='show a page titled "News"', indent=1, show=True,
      wrong=[(r'^put a heading "Big news" italic', "with-word"), (r"^put a heading Big", "quotes-missing")]),
    W('Add a button "Go" with a green background', ['put a button "Go" with background green'], "colour", "background green colours the button itself.", ctx='show a page titled "A"', indent=1, show=True,
      wrong=[(r"with colour green", "colour-word"), (r"^put a button Go", "quotes-missing")]),
    B('show a page titled "A"\n    put a text "Hi" with colour', 2, "colour", "colour needs a colour after it, for example colour red.", '    put a text "Hi" with colour red'),
    B('show a page titled "A"\n    put a heading "Hi" with size gigantic', 2, "size", "gigantic is not a size word. Use tiny, small, normal, big, huge or a number.", '    put a heading "Hi" with size huge'),
    C("Which makes a pale blue button?", 'put a button "Go" with background pale blue', [('put a button "Go" with background blue pale', "colour-name"), ('put a button "Go" with pale background blue', "colour-name")], "colour",
      "dark, light or pale go in front of the colour: pale blue."),
])

U3 = unit(3, "Boxes and rows", "Decide where things go: top to bottom, or side by side.", [
    part("Box and row", '''
A **box** holds things and stacks them from top to bottom. A **row** puts them side by side. They can go inside each other.

```hum-page
show a page titled "Layout" with background light gray
    put a box with background white, padding 16, rounded 12, shadow, space between 10
        put a heading "Sign in"
        put an input with hint "Your name"
        put a row with space between 8
            put a button "OK" with background blue, colour white
            put a button "Cancel"
```

Things inside a box or a row are indented **one more step**. `space between` sets the gap.
''',
         F('show a page titled "Pair"\n    put a ___ with space between 8\n        put a button "Yes"\n        put a button "No"', ["row"], "layout", "A row puts things side by side.", show=True,
           wrong=[(r"^(line|side|across|horizontal)$", "box-row"), (r"^box$", "box-row")], q="Put the two buttons side by side"),
         PG('show a page titled "A"\n    put a row\n        put a button "1"\n        put a button "2"', "Are the buttons inside a row?", ("has", "hl-row"), "yes", ["no"], "layout", "put a row makes a row, and the buttons are indented inside it."),
         C("What does a box do with the things inside it?", "Stacks them from top to bottom", [("Puts them side by side", "box-row"), ("Hides them", "box-row"), ("Makes them bigger", "box-row")], "layout",
           "A box stacks. A row sets side by side."),
         B('show a page titled "A"\n    put a rwo with space between 8\n        put a button "1"', 2, "debug", 'The word is row. HL says: Did you mean "row"?', '    put a row with space between 8')),
    part("Columns and loops", '''
`columns 3` makes a grid with 3 columns. Pages are made by a real program, so **loops build pages**. This puts one button on the page for every item in the list:

```hum-page
set keys to list of "1", "2", "3", "4", "5", "6"

show a page titled "Keys"
    put a box with columns 3, space between 8
        for each key in keys
            put a button key with rounded 8
```
''',
         PG('set keys to list of "1", "2", "3", "4"\nshow a page titled "Keys"\n    put a box with columns 2\n        for each key in keys\n            put a button key', "How many buttons does the loop put on the page?", ("count", "button"), "4", ["1", "2", "6"], "build",
            "for each runs the line once for every item. There are 4 items, so 4 buttons."),
         F('show a page titled "Grid"\n    put a box with ___ 3\n        put a text "a"\n        put a text "b"\n        put a text "c"', ["columns"], "layout", "columns 3 makes a grid with 3 columns.", show=True,
           wrong=[(r"^(cols|column|grid|rows)$", "columns")]),
         O(['show a page titled "Stack"', '    put a box with space between 6', '        put a text "Top"', '        put a text "Bottom"'], "layout", "The box first, then the things inside it in order.", show=True),
         PG('show a page titled "A"\n    repeat 3 times\n        put a button "Go"', "How many buttons?", ("count", "button"), "3", ["1", "0"], "build", "repeat 3 times puts the button on the page 3 times.")),
], [
    PG('show a page titled "A"\n    put a row\n        put a text "L"\n        put a text "R"', "How many texts are on the page?", ("count", "p"), "2", ["1", "0"], "layout", "A row only decides where they go. Both texts are there."),
    PG('set names to list of "Ann", "Bo", "Cy"\nshow a page titled "Names"\n    for each n in names\n        put a text n', "Which texts are on the page?", ("texts", "p"), "Ann, Bo, Cy", ["n, n, n", "Names", "Ann"], "build",
       "The loop puts one text on the page for each name."),
    PG('show a page titled "A"\n    put a box\n        put a button "1"\n        put a button "2"', "Which is true: are the buttons inside a row?", ("has", "hl-row"), "no", ["yes"], "layout", "They are inside a box. A box stacks, so they are not in a row."),
    F('show a page titled "A"\n    put a ___ with space between 8\n        put a text "x"\n        put a text "y"', ["box"], "layout", "A box stacks things top to bottom.", show=True, q="Stack the two texts from top to bottom", wrong=[(r"^row$", "box-row")]),
    B('show a page titled "A"\n    put a box\n        put a button "1"\n      put a button "2"', 4, "indent", "Indents must line up. The second button should line up with the first.", '        put a button "2"'),
    W('Add a row (with space between 10)', ['put a row with space between 10'], "layout", "put a row with space between 10.", ctx='show a page titled "A"', indent=1,
      wrong=[(r"^put a line", "box-row"), (r"^row", "put-word")]),
    C("Which makes 4 equal columns?", "put a box with columns 4", [("put a row with columns", "columns"), ("put a box with 4 columns", "columns"), ("put a box with rows 4", "columns")], "layout", "It is: with columns 4."),
    O(['show a page titled "Pair"', '    put a row', '        put a text "A"', '        put a text "B"'], "layout", "Page, then the row, then what is inside the row.", show=True),
])

U4 = unit(4, "Drawings", "Draw circles, rectangles and lines at exact spots.", [
    part("A drawing", '''
Inside a `drawing`, you place shapes at a spot. `at 150, 100` means **150 across and 100 down** from the top left corner.

```hum-page
show a page titled "Football"
    put a drawing with width 300, height 300, background sky blue, rounded 12
        put a rectangle at 0, 220 with width 300 and height 80 and colour green
        put a circle at 150, 130 with radius 70 and colour white and border colour black and border 4
        put a text "GOAL!" at 100, 20 with size big, bold, colour white
```

Shapes: `circle` (with `radius`), `oval`, `rectangle`, `square`, `triangle` (with `width` and `height`), `line` and `polygon`. They are drawn in the order you write them, so **later ones are on top**.
''',
         PG('show a page titled "A"\n    put a drawing with width 200, height 100\n        put a circle at 50, 50 with radius 20\n        put a circle at 120, 50 with radius 20\n        put a rectangle at 0, 80 with width 200 and height 20',
            "How many circles are in the drawing?", ("count", "circle"), "2", ["1", "3"], "draw", "Each put a circle line draws one circle. The rectangle is not a circle."),
         F('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a ___ at 50, 50 with radius 20 and colour red', ["circle"], "shapes", "A circle has a radius.", show=True,
           wrong=[(r"^(round|ball|dot)$", "shape-props")]),
         B('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a triangle at 50, 50 with radius 20', 3, "shapes", "A triangle has width and height. Only a circle has a radius.", '        put a triangle at 50, 50 with width 30 and height 30'),
         C("Where is the spot  at 10, 80  in a drawing?", "10 across and 80 down from the top left", [("10 down and 80 across", "at-spot"), ("10 up from the bottom, 80 across", "at-spot"), ("In the middle", "at-spot")], "shapes",
           "The first number is across (x), the second is down (y), counted from the top left corner.")),
    part("Shapes at spots", '''
`square`, `rectangle`, `oval` and `circle` are placed with `at x, y`. A `line` goes **from** one spot **to** another:

```hum-page
show a page titled "Lines"
    put a drawing with width 120, height 80, background white
        put a line from 0, 0 to 120, 80 with colour red
        put a square at 20, 40 with width 30 and colour blue
```
''',
         PG('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a line from 0, 0 to 100, 100\n        put a line from 0, 100 to 100, 0', "How many lines are drawn?", ("count", "line"), "2", ["1", "4"], "shapes",
            "Each put a line makes one line. Two lines make a cross."),
         W('Add a square at 10, 10 with width 30 and colour blue', ['put a square at 10, 10 with width 30 and colour blue', 'put a square at 10, 10 with width 30 and color blue'], "shapes",
           "put a square at x, y with width 30 and colour blue.", ctx='show a page titled "A"\n    put a drawing with width 100, height 100', indent=2, show=True,
           wrong=[(r"with size", "shape-props"), (r"^put square", "put-word")]),
         O(['show a page titled "Sun"', '    put a drawing with width 100, height 100, background sky blue', '        put a rectangle at 0, 70 with width 100 and height 30 and colour green',
            '        put a circle at 50, 40 with radius 20 and colour yellow'], "draw", "Page, drawing, then the shapes: ground first, sun after, so the sun is drawn on top.", show=True),
         C("Two circles overlap. Which one is drawn on top?", "The one written later", [("The one written first", "shape-order"), ("The bigger one", "shape-order"), ("The one nearer the top", "shape-order")], "shapes",
           "Shapes are drawn in the order of the lines, so later ones cover earlier ones.")),
], [
    PG('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a circle at 30, 30 with radius 10\n        put a rectangle at 50, 50 with width 20 and height 20', "How many rectangles?", ("count", "rect"), "1", ["0", "2"], "draw", "One rectangle line, one rectangle."),
    PG('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a triangle at 10, 10 with width 40 and height 40', "Is there a triangle in the drawing?", ("has", "<polygon"), "yes", ["no"], "shapes", "put a triangle draws one."),
    F('show a page titled "A"\n    put a ___ with width 100, height 100, background green\n        put a circle at 50, 50 with radius 10', ["drawing"], "draw", "A drawing holds the shapes and has a width and a height.", show=True),
    F('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a line ___ 0, 0 to 100, 50', ["from"], "shapes", "put a line from 0, 0 to 100, 50.", show=True, wrong=[(r"^(at|in|on|start)$", "at-spot")]),
    B('show a page titled "A"\n    put a drawing with width 100, height 100\n        put a circel at 50, 50 with radius 20', 3, "debug", 'The word is circle. HL says: Did you mean "circle"?', '        put a circle at 50, 50 with radius 20'),
    W('Add a circle at 40, 40 with radius 15 and colour red', ['put a circle at 40, 40 with radius 15 and colour red', 'put a circle at 40, 40 with radius 15 and color red'], "shapes", "put a circle at x, y with radius 15 and colour red.",
      ctx='show a page titled "A"\n    put a drawing with width 100, height 100', indent=2, show=True, wrong=[(r"^put a circle 40", "at-spot"), (r"with size", "shape-props")]),
    C("Which is a shape you can draw?", "oval", [("button", "put-kind"), ("heading", "put-kind"), ("input", "put-kind")], "draw", "A button, heading and input go on the page. An oval is drawn in a drawing."),
    O(['show a page titled "Dot"', '    put a drawing with width 50, height 50', '        put a circle at 25, 25 with radius 10 and colour red'], "draw", "Page, then the drawing, then the shape inside it.", show=True),
])

U5 = unit(5, "Pixel art", "Draw a picture made of little squares.", [
    part("Pixel art", '''
Pixel art is a picture made of little squares. First say which letter is which colour with `where`. Then draw the picture with **one line of letters for each row**. A `.` is a see-through square.

```hum-page
show a page titled "Pixel hero" with background light blue
    put pixel art at 10, 10 with pixel size 14
        where "h" is brown, "s" is skin, "e" is black, "b" is blue
        "..hhhh.."
        ".hhhhhh."
        "..ssss.."
        "..sese.."
        ".bbbbbb."
```

Every row must be the **same length**, and every letter needs a colour. HL checks both and tells you which line is wrong.
''',
         F('show a page titled "A"\n    put pixel art at 0, 0 with pixel size 12\n        ___ "r" is red\n        "rr"\n        "rr"', ["where"], "pixel", 'where "r" is red says what the letter r means.', show=True,
           wrong=[(r"^(with|is|colour|let)$", "pixel-where")]),
         B('show a page titled "A"\n    put pixel art at 0, 0\n        where "a" is red\n        "aa"\n        "aaa"', 5, "pixel", "Every row must have the same length. The last row has 3 letters, the first has 2.", '        "aa"'),
         B('show a page titled "A"\n    put pixel art at 0, 0\n        where "a" is red\n        "ab"', 4, "pixel", 'The letter b has no colour yet. Add: where "b" is blue.', '        "aa"'),
         PG('show a page titled "A"\n    put pixel art at 0, 0 with pixel size 10\n        where "r" is red, "b" is blue\n        "rb"\n        "br"', "How many coloured squares does it have?", ("count", "rect"), "4", ["2", "3"], "pixel",
            "The picture is 2 by 2: four squares. Each letter is one square.")),
    part("Reading the rows", '''
A `.` (or a space) is a see-through square. The first row is the top of the picture.
`pixel size 14` makes every little square 14 dots wide, so a bigger number gives a bigger picture.
''',
         C("Which row is the TOP of this picture?", '"rw"', [('"wr"', "pixel-rows"), ("The last one", "pixel-rows"), ("It depends on the colours", "pixel-rows")], "pixel",
           "The first row of letters is the top.", code='show a page titled "Flag"\n    put pixel art at 0, 0 with pixel size 20\n        where "r" is red, "w" is white\n        "rw"\n        "wr"', show=True),
         C("Which squares are see-through here?", "The dot in each row", [("The g squares", "pixel-where"), ("None", "pixel-where"), ("The whole picture", "pixel-where")], "pixel",
           "A dot is a see-through square. The g letters are green.", code='show a page titled "A"\n    put pixel art at 0, 0\n        where "g" is green\n        "gg."\n        ".gg"', show=True),
         F('show a page titled "A"\n    put pixel art at 0, 0 with pixel ___ 20\n        where "a" is orange\n        "aa"', ["size"], "pixel", "pixel size 20 makes each square 20 dots wide.", show=True, wrong=[(r"^(width|big|scale|zoom)$", "pixel-size")]),
         C("Why must every row of pixel art have the same length?", "The picture is a rectangle of squares", [("HL likes it tidy", "pixel-rows"), ("So the colours match", "pixel-rows"), ("It does not matter", "pixel-rows")], "pixel",
           "The picture is a rectangle of squares, so all the rows need the same number of squares.")),
], [
    PG('show a page titled "A"\n    put pixel art at 0, 0\n        where "x" is black\n        "x.x"\n        ".x."\n        "x.x"', "How many black squares?", ("count", "rect"), "5", ["9", "4", "3"], "pixel", "The corners and the middle: 5 x letters."),
    C("A row \"xxx\" has how many squares across?", "3", [("1", "pixel-rows"), ("2", "pixel-rows"), ("4", "pixel-rows")], "pixel", "One letter is one square, so xxx is three squares."),
    F('show a page titled "A"\n    put pixel art at 0, 0\n        where "a" is ___\n        "aa"', ["red"], "pixel", "any colour name works", show=True, q='Make the letter a red: where "a" is ___'),
    B('show a page titled "A"\n    put pixel art at 0, 0\n        "aa"\n        "aa"', 3, "pixel", "There is no where line, so HL does not know what a means.", '        where "a" is red'),
    W('Add a line that says "b" is blue (start with where)', ['where "b" is blue'], "pixel", 'where "b" is blue.', ctx='show a page titled "A"\n    put pixel art at 0, 0\n        "bb"', indent=2,
      wrong=[(r'^"b" is blue', "pixel-where"), (r"^where b ", "quotes-missing")]),
    C("In pixel art, what does a dot . mean?", "A see-through square", [("A black square", "pixel-where"), ("The end of a row", "pixel-where"), ("An error", "pixel-where")], "pixel", "A dot (or a space) is see-through."),
    C("Pixel art and a heading are on one page. The heading line comes first. Where does it appear?", "Above the picture", [("Below the picture", "order-top"), ("Inside the picture", "order-top"), ("Nowhere", "order-top")], "page",
      "A page is built from the top to the bottom, in the order of the lines.", code='show a page titled "Pair"\n    put a heading "Art"\n    put pixel art at 0, 0 with pixel size 8\n        where "o" is orange\n        "oo"', show=True),
    C("The first row of letters is which part of the picture?", "The top", [("The bottom", "pixel-rows"), ("The left", "pixel-rows"), ("The middle", "pixel-rows")], "pixel", "Rows go from the top to the bottom."),
])

U6 = unit(6, "Pages that react", "Make buttons and text boxes do something.", [
    part("Buttons and inputs", '''
A page can do things when it is used. Give each text box a name with `called`, then say what happens `when the button "..." is clicked`. Inside, `the number in amount` is what the person typed in the box.

```hum-page
set total to 0

show a page titled "Adder"
    put a heading "Adder"
    put an input called amount with hint "A number"
    put a button "Add"
    put a text "Total: {total}"

when the button "Add" is clicked
    change total to total + the number in amount
```

The program runs once and shows the page. Each click runs the matching `when` part, then the page's own lines run **again** with the new values, so the page always shows the latest.
(On this website the page is only a picture. Press Open in Playground to use the buttons.)
''',
         F('set total to 0\nshow a page titled "Adder"\n    put an input called amount with hint "A number"\n    put a button "Add"\n\nwhen the ___ "Add" is clicked\n    change total to total + the number in amount', ["button"], "react",
           'when the button "Add" is clicked runs when that button is clicked.', wrong=[(r"^(click|key|page|mouse)$", "react-when")]),
         W("Write the line that adds what is typed in the box amount to total", ['change total to total + the number in amount', 'add the number in amount to total'], "react",
           "change total to total + the number in amount.", ctx='set total to 0\nshow a page titled "Adder"\n    put an input called amount with hint "A number"\n    put a button "Add"\n    put a text "Total: {total}"\n\nwhen the button "Add" is clicked',
           indent=1, wrong=[(r"^set total", "react-change"), (r"\+ amount$", "react-input"), (r"^change total to the number", "react-change")]),
         C("The when part says set total to 5, but the page never shows 5. Why?", "set makes a new little variable. Use change.", [("The button is broken", "react-again"), ("The page needs to be reloaded", "react-again"), ("5 is not allowed", "react-change")],
           "react", "Inside a when part, use change to update a variable made earlier. set only makes a new variable that is forgotten at the end of the part."),
         C("What does  put an input called amount  do?", "Makes a text box named amount", [("Makes a button named amount", "react-input"), ("Shows the number amount", "react-input"), ("Makes a variable amount = 0", "react-input")], "react",
           "called gives the text box a name, so you can read what is in it later.")),
    part("Loops and functions on pages", '''
A function can put things on the page. Write it once and use it again and again:

```hum-page
define ball with x and y
    put a circle at x, y with radius 14 and colour white and border 3 and border colour black

show a page titled "Three balls"
    put a drawing with width 240, height 60, background green, rounded 10
        ball with 40 and 30
        ball with 120 and 30
        ball with 200 and 30
```
''',
         PG('define ball with x and y\n    put a circle at x, y with radius 14 and colour white\nshow a page titled "A"\n    put a drawing with width 240, height 60\n        ball with 40 and 30\n        ball with 120 and 30\n        ball with 200 and 30',
            "How many circles are in the drawing?", ("count", "circle"), "3", ["1", "4"], "build", "The function is called three times, and each call draws one circle."),
         F('___ ball with x and y\n    put a circle at x, y with radius 10 and colour red\nshow a page titled "A"\n    put a drawing with width 100, height 100\n        ball with 20 and 20', ["define"], "build",
           "define makes a function.", show=True, wrong=[(r"^(function|make|def|create)$", "build-func")]),
         PG('set names to list of "Ann", "Bo"\nshow a page titled "A"\n    for each n in names\n        put a button n\n        put a text n', "How many things are put on the page in total?", ("count", "p"), "2", ["1", "4"], "build",
            "Two names, so the loop runs twice. Each round puts a button and a text: 2 texts."),
         O(['define dot with x', '    put a circle at x, 20 with radius 5', 'show a page titled "Dots"', '    put a drawing with width 100, height 40', '        dot with 20', '        dot with 60'], "build",
           "Define the function first, then the page that uses it.", show=True)),
], [
    C("Which line starts the handler for a button called Go?", 'when the button "Go" is clicked', [('on click "Go"', "react-when"), ('when "Go" clicks', "react-when"), ("click the button Go", "react-when")], "react", 'It is: when the button "Go" is clicked.'),
    C("What do you write to read a number from the box called age?", "the number in age", [("age.number", "react-input"), ("number age", "react-input"), ("get age", "react-input")], "react", "the number in age (or the text in age for words)."),
    F('set count to 0\nshow a page titled "Click"\n    put a button "Plus"\n    put a text "Count: {count}"\n\nwhen the button "Plus" is clicked\n    ___ count to count + 1', ["change"], "react", "change updates a variable made before.", wrong=[(r"^set$", "react-change")]),
    F('set name to ""\nshow a page titled "Hi"\n    put an input called who\n    put a button "Go"\n    put a text "Hi {name}"\n\nwhen the button "Go" is clicked\n    change name to the ___ in who', ["text"], "react", "The box holds words, so use the text in who.", wrong=[(r"^number$", "react-input")]),
    B('set total to 0\nshow a page titled "A"\n    put a button "Add"\nwhen the button "Add" is clicked\nadd 1 to total', 5, "react", "The lines that belong to a when part are indented by 4 spaces.", '    add 1 to total'),
    C("After a click, what happens to the page?", "Its lines run again with the new values", [("Nothing until you refresh", "react-again"), ("The page closes", "react-again"), ("Only the button changes", "react-again")], "react", "The page's own lines run again, so it shows the latest values."),
    PG('define bar with y\n    put a rectangle at 0, y with width 50 and height 5\nshow a page titled "A"\n    put a drawing with width 100, height 100\n        bar with 10\n        bar with 30\n        bar with 50\n        bar with 70', "How many rectangles?", ("count", "rect"), "4", ["1", "3"], "build", "Four calls, four rectangles."),
    C("Which line must come BEFORE the page so the page can show total?", "set total to 0", [('when the button "Plus" is clicked', "react-when"), ("put a text total", "react-again"), ("Nothing", "react-change")], "react",
      "A variable has to exist before the page uses it, so make it first with set.", code='set total to 0\nshow a page titled "Count"\n    put a text "{total}"', show=True),
])

UNITS = [U1, U2, U3, U4, U5, U6]


def export_json(render_markdown, highlight):
    return _export_json(sys.modules[__name__], render_markdown, highlight)

"""Gentle pointers for people who already know another programming language."""

_SAY = 'In HL you show something with "say". Example: say "Hello"'
_ELSE = 'In HL the other case is called "otherwise". Example: otherwise'
_DEFINE = 'In HL you make a function with "define". Example: define add with a and b'
_SET = 'In HL you make a variable with "set". Example: set age to 20'
_ASK = 'In HL you read what someone types with "ask". Example: ask "Your name?" and save it as name'

WORDS = {
    "print": _SAY, "println": _SAY, "puts": _SAY, "echo": _SAY, "console": _SAY, "printf": _SAY,
    "return": 'In HL a function sends a value back with "give back". Example: give back a + b',
    "else": _ELSE,
    "elif": 'In HL write "otherwise if". Example: otherwise if age is at least 13',
    "elseif": 'In HL write "otherwise if". Example: otherwise if age is at least 13',
    "def": _DEFINE, "function": _DEFINE, "func": _DEFINE, "fn": _DEFINE, "fun": _DEFINE,
    "while": 'In HL a loop that keeps going starts with "repeat". Example: repeat while count is less than 3',
    "var": _SET, "let": _SET, "const": _SET, "my": _SET,
    "input": _ASK, "prompt": _ASK, "scanf": _ASK, "cin": _ASK, "readline": _ASK,
    "import": 'In HL you switch on extras with "use". Example: use math',
    "include": 'In HL you switch on extras with "use". Example: use math',
    "require": 'In HL you switch on extras with "use". Example: use math',
    "break": 'In HL, leave a loop early with "stop".',
    "continue": 'In HL, jump to the next round of a loop with "skip".',
    "switch": 'HL has no "switch". Use "if" and "otherwise if" instead.',
    "case": 'HL has no "switch". Use "if" and "otherwise if" instead.',
    "catch": 'In HL write "if that fails" after a "try" block.',
    "except": 'In HL write "if that fails" after a "try" block.',
    "finally": 'HL has no "finally". Put the code after the "if that fails" block.',
    "throw": 'HL has no "throw". Errors happen by themselves, and "try" catches them.',
    "raise": 'HL has no "raise". Errors happen by themselves, and "try" catches them.',
    "true": 'HL uses "yes" and "no" instead of true and false.',
    "false": 'HL uses "yes" and "no" instead of true and false.',
    "null": 'In HL the empty value is "nothing".',
    "none": 'In HL the empty value is "nothing".',
    "nil": 'In HL the empty value is "nothing".',
    "undefined": 'In HL the empty value is "nothing".',
    "len": 'In HL you count with "length of" or "how many items in". Example: length of name',
    "length": 'In HL write "length of name" (the word "of" is needed).',
    "append": 'In HL you add to a list with "add". Example: add "pink" to colors',
    "push": 'In HL you add to a list with "add". Example: add "pink" to colors',
    "int": 'In HL turn text into a number with "number of". Example: number of "5"',
    "float": 'In HL turn text into a number with "number of". Example: number of "5"',
    "str": 'In HL turn a value into text with "text of". Example: text of 5',
}

CHARACTERS = {
    "&": 'HL uses the words "and", "or" and "not" instead of && || !',
    "|": 'HL uses the words "and", "or" and "not" instead of && || !',
    "{": 'HL has no braces. Indent the lines inside an "if" or "repeat" by 4 spaces. (Braces are only used inside text, like "Hi {name}".)',
    "}": 'HL has no braces. Indent the lines inside an "if" or "repeat" by 4 spaces. (Braces are only used inside text, like "Hi {name}".)',
    ";": "HL doesn't need semicolons. Each line is one instruction.",
    ":": 'HL doesn\'t use colons, except in comments: note: like this',
    "[": 'HL makes lists with words. Example: set colors to list of "red", "green"  and  item 1 of colors',
    "]": 'HL makes lists with words. Example: set colors to list of "red", "green"  and  item 1 of colors',
    ".": 'HL has no dots for calling things. Use phrases like "length of name".',
    "'": 'Use double quotes for text, like "this".',
    "#": 'Comments in HL start with "note:". Example: note: this is a comment',
    "$": 'HL names are plain words. To put a value in text, use braces: "Hi {name}".',
    "@": "HL doesn't use this symbol.",
    "^": 'To raise to a power, write "to the power of". Example: 2 to the power of 10',
    "~": "HL doesn't use this symbol.",
    "?": 'In HL a question is a comparison like "age is at least 18".',
}


def for_word(word):
    """A hint for a word borrowed from another language, or None."""
    low = word.lower()
    if word != low and low in ("say", "set", "change", "add", "subtract", "remove", "ask", "if",
                               "repeat", "for", "define", "give", "stop", "skip", "use", "try", "write"):
        return f'HL\'s words are all lowercase. Write "{low}".'
    return WORDS.get(low)

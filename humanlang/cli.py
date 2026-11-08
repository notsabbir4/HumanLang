"""Command line: `hl run file.hum`, `hl check file.hum`, or just `hl` for the REPL."""
import os
import sys
import tempfile
import threading
import webbrowser

from . import __version__
from .errors import HLError, format_warning
from .formatter import format_source
from .interpreter import Interpreter
from .render import to_html

USAGE = """HumanLang (HL) - code that reads like you talk.

Usage:
  hl                   start the interactive prompt
  hl run FILE.hum      run a program
  hl run --trace FILE  run a program and show each line as it runs
  hl run --time-limit SECONDS FILE   stop a program that runs longer than this
  hl run --max-output LETTERS FILE   stop a program that prints more than this (0 = no limit)
  hl run --no-open FILE              (for a program that shows a page) don't open the browser
  hl build FILE.hum    run a program that shows a page, and save the page as FILE.html for the web
  hl build FILE.hum --out PAGE.html   ...saved under another name
  hl build FILE.hum --offline         ...a page (or game) that works with no internet (a bigger file)
  hl page FILE.hum     run a program that shows a page and print the page's HTML (used by editor previews)
  (a program with 'play a game' opens as a playable game; hl build saves it as one web page)
  hl debug FILE.hum    step through a program one line at a time, and see what each line does
  hl check FILE.hum    check a program for mistakes without running it
  hl format FILE.hum   tidy a program's spacing and indentation (--check to only report)
  hl lsp               start the language server (for editors)
  hl --version         show the version
"""

BLOCK_STARTERS = {"if", "repeat", "for", "define", "try"}
VALUE_FLAGS = ("--time-limit", "--max-output", "--out", "--dir")
NUMBER_FLAGS = ("--time-limit", "--max-output")
RUNNING = {}  # the interpreter that is running now, so Ctrl-C can say where the program was


def run_big(fn):
    """Run fn in a thread with a big stack so deep recursion is safe."""
    result = [1]

    def target():
        result[0] = fn()

    t = None
    # some systems refuse a huge stack, so step down; the recursion limit must match the stack we get
    for megabytes, limit in ((256, 200000), (64, 200000), (16, 20000), (0, 5000)):
        try:
            threading.stack_size(megabytes * 1024 * 1024)
            sys.setrecursionlimit(limit)
            t = threading.Thread(target=target, daemon=True)
            t.start()
            break
        except (ValueError, RuntimeError):
            t = None
    if t is None:  # no helper thread possible: run here, with a limit that is safe for a normal stack
        sys.setrecursionlimit(5000)
        return fn()
    try:
        while t.is_alive():
            t.join(0.1)
    except KeyboardInterrupt:
        interp = RUNNING.get("interp")
        line = interp.line if interp else 0
        where = ""
        if line:
            src = interp.source
            where = f" It was on line {line}" + (f" of {src.name}" if src.name else "") + "."
        print(f"\nStopped.{where}", file=sys.stderr)
        return 130
    return result[0]


def read_program(path):
    try:
        with open(path, encoding="utf-8-sig") as f:  # "-sig": skip the invisible mark some Windows editors add
            return f.read()
    except FileNotFoundError:
        print(f'I can\'t find the file "{path}".\nCheck the spelling and the folder.', file=sys.stderr)
    except OSError as e:
        print(f'I couldn\'t read "{path}": {e.strerror}.', file=sys.stderr)
    return None


def format_file(path, check_only=False):
    source = read_program(path)
    if source is None:
        return 1
    tidy = format_source(source)
    if tidy == source:
        print(f"{path} is already tidy.")
        return 0
    if check_only:
        print(f"{path} would be changed by: hl format {path}")
        return 1
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(tidy)
    print(f"Tidied {path}.")
    return 0


def show_warnings(interp, lines):
    """Heads-ups go to standard error, so a program's own output stays clean."""
    for w in interp.warnings:
        print(format_warning(w, lines), file=sys.stderr)


def write_page(page, where):
    try:
        with open(where, "w", encoding="utf-8", newline="\n") as f:
            f.write(to_html(page))
    except OSError as e:
        print(f'I couldn\'t save the page as "{where}": {e.strerror}.', file=sys.stderr)
        return False
    return True


def preview_page(page, name, open_browser=True):
    """Save the page where the browser can open it, and open it."""
    folder = os.path.join(tempfile.gettempdir(), "humanlang-preview")
    os.makedirs(folder, exist_ok=True)
    where = os.path.join(folder, os.path.splitext(os.path.basename(name))[0] + ".html")
    if not write_page(page, where):
        return
    if open_browser and not os.environ.get("HL_NO_OPEN"):
        try:
            opened = webbrowser.open("file:///" + where.replace(os.sep, "/").lstrip("/"))
        except Exception:
            opened = False
    else:
        opened = None
    if opened:
        print(f"Your page is open in the browser ({where}).", file=sys.stderr)
    else:
        print(f"Your page is ready. Open this file in a browser to see it:\n{where}", file=sys.stderr)
    print("To save it for the web, type:  hl build " + name, file=sys.stderr)


def live_out(interp, source, path, build, open_browser, offline=False):
    """The page has buttons that run code: it needs HumanLang inside the page, so it is built like a game."""
    from .livepage import live_to_html
    try:
        text = live_to_html(interp.designs[-1], interp.live_keys(), source, offline, lambda t: print(t, file=sys.stderr))
    except Exception as e:
        if type(e).__name__ != "OfflineError":
            raise
        print(e, file=sys.stderr)
        return 1
    if build is not None:
        where = build or os.path.splitext(path)[0] + ".html"
    else:
        folder = os.path.join(tempfile.gettempdir(), "humanlang-preview")
        os.makedirs(folder, exist_ok=True)
        where = os.path.join(folder, os.path.splitext(os.path.basename(path))[0] + ".html")
    try:
        with open(where, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    except OSError as e:
        print(f'I couldn\'t save the page as "{where}": {e.strerror}.', file=sys.stderr)
        return 1
    if build is not None:
        print(f"Saved your live page as {where}. " + ("It works without internet." if offline else "(It needs the internet to start.)"))
        return 0
    opened = None
    if open_browser and not os.environ.get("HL_NO_OPEN"):
        try:
            opened = webbrowser.open("file:///" + where.replace(os.sep, "/").lstrip("/"))
        except Exception:
            opened = False
    print(f"Your live page is {'open in the browser' if opened else 'ready. Open this file in a browser'} ({where}).", file=sys.stderr)
    print("To save it for the web, type:  hl build " + path, file=sys.stderr)
    return 0


def game_out(interp, source, path, build, open_browser, offline=False):
    """The program is a game: save it as one web page, and (for `hl run`) open it."""
    from .gamepage import game_to_html
    try:
        page = game_to_html(source, interp.game["title"], offline, lambda t: print(t, file=sys.stderr),
                            os.path.dirname(os.path.abspath(path)))
    except Exception as e:
        if type(e).__name__ != "OfflineError":
            raise
        print(e, file=sys.stderr)
        return 1
    if build is not None:
        where = build or os.path.splitext(path)[0] + ".html"
    else:
        folder = os.path.join(tempfile.gettempdir(), "humanlang-preview")
        os.makedirs(folder, exist_ok=True)
        where = os.path.join(folder, os.path.splitext(os.path.basename(path))[0] + ".html")
    try:
        with open(where, "w", encoding="utf-8", newline="\n") as f:
            f.write(page)
    except OSError as e:
        print(f'I couldn\'t save the game as "{where}": {e.strerror}.', file=sys.stderr)
        return 1
    if build is not None:
        print(f"Saved your game as {where}. Open that file in a browser, or put it on any website. " + ("It works without internet." if offline else "(It needs the internet to start.)"))
        return 0
    opened = None
    if open_browser and not os.environ.get("HL_NO_OPEN"):
        try:
            opened = webbrowser.open("file:///" + where.replace(os.sep, "/").lstrip("/"))
        except Exception:
            opened = False
    if opened:
        print(f"Your game is open in the browser ({where}).", file=sys.stderr)
    else:
        print(f"Your game is ready. Open this file in a browser to play it:\n{where}", file=sys.stderr)
    print("To save it for the web, type:  hl build " + path, file=sys.stderr)
    return 0


def run_file(path, check_only=False, trace=False, time_limit=0, max_output=None, build=None, open_browser=True, offline=False):
    source = read_program(path)
    if source is None:
        return 1
    from .memory import Memory
    memory = Memory(path=os.path.join(os.path.dirname(os.path.abspath(path)), ".hl-memory", os.path.basename(path) + ".json"))
    interp = Interpreter(memory=memory)
    from .assets import scan_folder
    interp.assets = scan_folder(os.path.dirname(os.path.abspath(path)), source)
    RUNNING["interp"] = interp
    if time_limit:
        interp.set_time_limit(time_limit)
    if max_output is not None:
        interp.max_output = max_output
    if trace:
        interp.trace = lambda n, text: print(f"  [line {n}] {text}", file=sys.stderr)
    lines = source.splitlines()
    try:
        if check_only:
            interp.check(source, path)
            show_warnings(interp, lines)
            n = len(interp.warnings)
            print("No mistakes found." if not n else
                  f"No mistakes found, but {n} heads-up{'s' if n != 1 else ''} above (the program still runs).")
        else:
            stmts = interp.prepare(source, path)
            show_warnings(interp, lines)
            if time_limit:
                interp.set_time_limit(time_limit)  # the clock starts when the program does, not while it is being read
            interp.run_statements(stmts, source)
            sys.stdout.flush()
            if interp.game is not None:
                return game_out(interp, source, path, build, open_browser, offline)
            if interp.designs:
                if len(interp.designs) > 1:
                    print(f"Your program showed {len(interp.designs)} pages; I'm using the last one.", file=sys.stderr)
                if interp.live_handlers:
                    return live_out(interp, source, path, build, open_browser, offline)
                if build is not None:
                    where = build or os.path.splitext(path)[0] + ".html"
                    if write_page(interp.designs[-1], where):
                        print(f"Saved your page as {where}. Open that file in a browser, or put it on any website.")
                    else:
                        return 1
                else:
                    preview_page(interp.designs[-1], path, open_browser)
            elif build is not None:
                print("This program doesn't show a page, so there is nothing to build.", file=sys.stderr)
                print('Start a page with:  show a page titled "My page"   then indent what goes on it.', file=sys.stderr)
                return 1
    except HLError as e:
        sys.stdout.flush()
        print(e.format(source.splitlines()), file=sys.stderr)
        return 1
    finally:
        try:
            memory.save()
        except OSError:
            pass
    return 0


def page_command(path, as_json, folder=None):
    """Run a program and give back the page it shows (not opening any browser). `-` reads the program from standard input."""
    import json
    if path == "-":
        source = sys.stdin.buffer.read().decode("utf-8-sig", "replace")
        path = None
    else:
        source = read_program(path)
        if source is None:
            return 1
    out, answers_needed = [], []

    def no_answers(prompt):
        answers_needed.append(prompt)
        raise HLError("This program asks a question, and a preview can't answer it.", getattr(interp, "line", 0) or None,
                      "Add the answer to the program while you design (set name to \"Sam\"), then use ask when you are done.")

    interp = Interpreter(out=out.append, inp=no_answers)
    interp.set_time_limit(10)
    interp.max_output = 200000
    error = None
    try:
        stmts = interp.prepare(source, path)
        interp.set_time_limit(10)
        interp.run_statements(stmts, source)
    except HLError as e:
        error = e.format(source.splitlines())
    except RecursionError:
        error = "This program calls itself too deeply."
    kind = "page"
    page = to_html(interp.designs[-1]) if interp.designs else None
    if not error and interp.game is not None:
        # a game: the editor shows it as a playable page (it brings Python with it, so it needs the internet the first time)
        from .gamepage import game_to_html
        kind = "game"
        page = game_to_html(source, interp.game["title"], folder=folder or (os.path.dirname(os.path.abspath(path)) if path else None))
    elif not error and interp.designs and interp.live_handlers:
        from .livepage import live_to_html
        kind = "live"
        page = live_to_html(interp.designs[-1], interp.live_keys(), source)
    if as_json:
        sys.stdout.write(json.dumps({"html": page, "output": "".join(out), "error": error, "kind": kind}))
    elif page is not None:
        sys.stdout.write(page)
    if error and not as_json:
        print(error, file=sys.stderr)
    elif page is None and not as_json:
        print('This program doesn\'t show a page. Start one with:  show a page titled "My page"', file=sys.stderr)
    return 1 if (error or (page is None and not as_json)) else 0


def repl():
    try:
        import readline  # arrow keys and history, where the system has it
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass
    print(f"HumanLang {__version__}. Type your code, or 'exit' to quit.")
    interp = Interpreter()
    while True:
        try:
            line = input("hl> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            continue
        if line.strip() in ("exit", "quit"):
            return 0
        if not line.strip():
            continue
        buf = [line]
        words = line.split()
        if words[0] in BLOCK_STARTERS or words[:3] in (["make", "a", "sprite"], ["make", "a", "map"], ["play", "a", "game"]) or words[:3] == ["show", "a", "page"] or words[0] == "put":
            try:
                while True:
                    more = input("... ")
                    if not more.strip():
                        break
                    buf.append(more)
            except EOFError:
                pass
        src = "\n".join(buf)
        try:
            before = len(interp.designs)
            interp.run_repl(src)
            if len(interp.designs) > before:
                preview_page(interp.designs[-1], "page")
        except HLError as e:
            print(e.format(src.splitlines()))
        except KeyboardInterrupt:
            print("\nStopped.")


def use_utf8():
    """Make text (including non-English letters) work the same on every system."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    use_utf8()
    if not argv:
        return run_big(repl)
    cmd = argv[0]
    if cmd in ("-v", "--version", "version"):
        print(f"HumanLang {__version__}")
        return 0
    if cmd in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if cmd == "lsp":
        from .lsp import serve
        return serve()
    flags, rest, values, skip = [], [], {}, False
    for k, a in enumerate(argv[1:]):
        if skip:
            skip = False
        elif a.startswith("--"):
            name, eq, value = a.partition("=")
            if name in VALUE_FLAGS:
                if not eq:
                    value = argv[k + 2] if k + 2 < len(argv) else ""
                    skip = True
                values[name] = value
            flags.append(name)
        else:
            rest.append(a)
    if cmd not in ("run", "check", "format", "build", "page", "debug"):
        rest = argv
    numbers = {}
    for name, value in values.items():
        if name not in NUMBER_FLAGS:
            continue
        try:
            numbers[name] = float(value)
            if numbers[name] < 0:
                raise ValueError
        except ValueError:
            print(f'{name} needs a number (0 or more), for example: {name} 10', file=sys.stderr)
            return 1
    if cmd == "format":
        return format_file(rest[0], "--check" in flags) if rest else (print(USAGE) or 1)
    if not rest:
        print(USAGE)
        return 1
    if cmd == "debug":
        source = read_program(rest[0])
        if source is None:
            return 1
        from .debugger import walk
        return run_big(lambda: walk(rest[0], source))
    if cmd == "page":
        return run_big(lambda: page_command(rest[0], "--json" in flags, values.get("--dir") or None))
    max_output = int(numbers["--max-output"]) if "--max-output" in numbers else None
    build = None
    if cmd == "build":
        build = values.get("--out", "")
        if "--out" in flags and not build:
            print("--out needs a file name, for example: --out page.html", file=sys.stderr)
            return 1
    return run_big(lambda: run_file(rest[0], cmd == "check", "--trace" in flags,
                                    numbers.get("--time-limit", 0), max_output, build, "--no-open" not in flags,
                                    "--offline" in flags))


if __name__ == "__main__":
    sys.exit(main())

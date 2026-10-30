"""Command line: `hl run file.hum`, `hl check file.hum`, or just `hl` for the REPL."""
import sys
import threading

from . import __version__
from .errors import HLError
from .formatter import format_source
from .interpreter import Interpreter

USAGE = """HumanLang (HL) - code that reads like you talk.

Usage:
  hl                   start the interactive prompt
  hl run FILE.hum      run a program
  hl run --trace FILE  run a program and show each line as it runs
  hl check FILE.hum    check a program for mistakes without running it
  hl format FILE.hum   tidy a program's spacing and indentation (--check to only report)
  hl lsp               start the language server (for editors)
  hl --version         show the version
"""

BLOCK_STARTERS = {"if", "repeat", "for", "define", "try"}


def run_big(fn):
    """Run fn in a thread with a big stack so deep recursion is safe."""
    sys.setrecursionlimit(200000)
    try:
        threading.stack_size(256 * 1024 * 1024)
    except (ValueError, RuntimeError):
        pass
    result = [1]

    def target():
        result[0] = fn()

    t = threading.Thread(target=target, daemon=True)
    t.start()
    try:
        while t.is_alive():
            t.join(0.1)
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 130
    return result[0]


def read_program(path):
    try:
        with open(path, encoding="utf-8") as f:
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


def run_file(path, check_only=False, trace=False):
    source = read_program(path)
    if source is None:
        return 1
    interp = Interpreter()
    if trace:
        interp.trace = lambda n, text: print(f"  [line {n}] {text}", file=sys.stderr)
    try:
        if check_only:
            interp.check(source)
            print("No mistakes found.")
        else:
            interp.run(source)
            sys.stdout.flush()
    except HLError as e:
        sys.stdout.flush()
        print(e.format(source.splitlines()), file=sys.stderr)
        return 1
    return 0


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
        if line.split()[0] in BLOCK_STARTERS:
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
            interp.run_repl(src)
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
    flags = [a for a in argv[1:] if a.startswith("--")]
    rest = [a for a in argv[1:] if not a.startswith("--")] if cmd in ("run", "check", "format") else argv
    if cmd == "format":
        return format_file(rest[0], "--check" in flags) if rest else (print(USAGE) or 1)
    if not rest:
        print(USAGE)
        return 1
    return run_big(lambda: run_file(rest[0], cmd == "check", "--trace" in flags))


if __name__ == "__main__":
    sys.exit(main())

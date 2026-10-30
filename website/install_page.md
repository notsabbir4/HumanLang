# Install HumanLang

## Easiest: no install

Open the **Playground** and start typing. It runs right in your browser.

## On your computer

Pick whichever is easiest for you.

### A. With Python (any system)

If you have Python 3.9 or newer:

```text
pip install humanlang
hl --version
```

(`pip install humanlang` works once HumanLang has been published to PyPI. Until then, download the
source and run `pip install .` inside the folder.)

If your computer says `hl` is not found, use `python -m humanlang` instead. It does the same thing.

### B. A single program, no Python needed

On the project's **Releases** page, download the file for your system:

| System | File | Then |
|---|---|---|
| Windows | `hl-windows.exe` | rename to `hl.exe`, and put it in a folder that is on your PATH |
| macOS | `hl-macos` | `chmod +x hl-macos`, then `mv hl-macos /usr/local/bin/hl` |
| Linux | `hl-linux` | `chmod +x hl-linux`, then `sudo mv hl-linux /usr/local/bin/hl` |

On macOS you may need to right-click the file and choose Open the first time.

## Check it works

```text
hl --version
```

Make a file called `hello.hum` containing:

```hum-fragment
say "Hello, world!"
```

and run it:

```text
hl run hello.hum
```

## Your editor

- **VS Code:** copy the `editors/vscode` folder from the project into `~/.vscode/extensions/humanlang`
  (on Windows: `%USERPROFILE%\.vscode\extensions\humanlang`), run `npm install` inside it once, and
  restart VS Code. You get colours, snippets, and error messages as you type.
- **Other editors:** run `hl lsp` as a language server for `.hum` files (Neovim, Helix, Zed, Emacs and others support this).

## Something wrong?

| Problem | Fix |
|---|---|
| `hl` is not recognised | use `python -m humanlang`, or add the folder with `hl` to your PATH |
| `I can't find the file` | you are in a different folder; use `cd` to go to where the file is |
| Letters look broken on Windows | use Windows Terminal, or run `chcp 65001` first |

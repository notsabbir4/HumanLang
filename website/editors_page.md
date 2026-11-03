# Use HumanLang in your code editor

A code editor is a program for writing code. HumanLang works in any of them, because a HumanLang program is only a text file ending in `.hum`. This page shows how to get two things:

- **Run:** press a button (or a key) and your program runs.
- **Colours and live help:** words get colours, and mistakes are underlined as you type. This is available in VS Code and in editors that understand "language servers".

Before you start, **install HumanLang** from the [Download page](install.html). Then check that `hl --version` works in a terminal.

## VS Code

VS Code (Visual Studio Code) is a free editor from Microsoft. Download it from <https://code.visualstudio.com> if you do not have it. The steps below also work in **VSCodium**, **Cursor** and **Windsurf**.

### Step 1: Get the HumanLang extension

An *extension* is an add-on for the editor.

1. Download the extension file: <a href="https://github.com/notsabbir4/HumanLang/releases/latest/download/HumanLang-VSCode.vsix">HumanLang-VSCode.vsix</a>. It goes to your **Downloads** folder.
2. Open VS Code.
3. On the left side, click the **Extensions** icon (it looks like four little squares, one of them flying away). You can also press **Ctrl + Shift + X** (on Mac: **Command + Shift + X**).
4. At the top right of the Extensions panel, click the **three dots** (`...`).
5. Click **Install from VSIX...**.
6. Choose `HumanLang-VSCode.vsix` from your Downloads folder and click **Install**.
7. If VS Code shows a **Reload** or **Restart Extensions** button, click it.

You can do steps 2 to 7 with one line instead. In a terminal, go to your Downloads folder and type:

```terminal
code --install-extension HumanLang-VSCode.vsix
```

### Step 2: Write a program

1. Click **File**, then **Open Folder...**, make or choose a folder, and click **Select Folder**.
2. Click the **New File** icon in the Explorer panel and name the file `hello.hum`.
3. Type:

```hum-fragment
say "Hello, world!"
```

You should see the words in colour. The HumanLang icon appears next to the file name in the list on the left.

### Step 3: Run it

Pick any one of these:

- Click the little **triangle (play) button** at the top right of the editor.
- Press **Ctrl + F5** (on Mac: **Command + F5**).
- Press **Ctrl + Shift + P** (Mac: **Command + Shift + P**), type `HumanLang: Run`, and press **Enter**.

A terminal opens at the bottom and shows `Hello, world!`. VS Code saves your file first, so you never run an old copy.

To check a file for mistakes without running it, use the command **HumanLang: Check this file for mistakes** in the same way.

### What you get

- **Colours** for words, text, numbers and notes.
- **Snippets:** type a short word like `if`, `repeat` or `define`, press **Tab**, and a ready-made piece of code appears.
- **Live errors:** a wavy red line appears under a mistake, with the same helpful message HumanLang gives when you run the program. Move the mouse over it.
- **Completion:** as you type, VS Code suggests HumanLang words and your own names.

### If something does not work

| What you see | What to do |
|---|---|
| A yellow box says *I could not start the "hl" program* | HumanLang is not installed, or VS Code started before you installed it. Install it from the [Download page](install.html), then **close VS Code completely** and open it again. |
| The terminal says `hl` is not recognized | Same fix: close VS Code and open it again. If it still fails, open **File > Preferences > Settings**, search for `humanlang`, and in **Humanlang: Command** type the full path to `hl.exe`. On Windows it is usually `C:\Users\YOURNAME\AppData\Local\Programs\HumanLang\hl.exe`. The path must not contain spaces. |
| No colours, and the file shows as *Plain Text* | The file name must end in `.hum`. Click the language name at the bottom right of VS Code, choose **HumanLang**. |
| There is no triangle button | Click inside a `.hum` file first. The button only appears for HumanLang files. |
| *Install from VSIX* does not appear | Your VS Code may be very old. Update it (**Help > Check for Updates**). It needs version 1.75 or newer. |

## Other editors

For every editor below you get **Run**. Colours and live help are explained at the end.

### Notepad++ (Windows)

1. Open your `.hum` file.
2. Press **F5** (or click **Run > Run...**).
3. In the box, type this exactly, and click **Run** to try it:

```config
cmd /k hl run "$(FULL_CURRENT_PATH)"
```

4. To keep it, click **Save...**, name it `Run HumanLang`, and pick a shortcut key. It then appears in the **Run** menu.

### Sublime Text

1. Click **Tools > Build System > New Build System...**
2. Delete what is there and paste this:

```config
{
    "cmd": ["hl", "run", "$file"]
}
```

3. Save it as `HumanLang.sublime-build` (Sublime picks the right folder).
4. Choose **Tools > Build System > HumanLang**, and press **Ctrl + B** (Mac: **Command + B**) to run.

Programs that use `ask` need typing in; Sublime's build window can't take typing, so for those use a terminal and `hl run file.hum`.

### JetBrains editors (IntelliJ IDEA, PyCharm, WebStorm and others)

1. Open **Settings** (Mac: **Preferences**) and go to **Tools > External Tools**.
2. Click the **+** button and fill in:
   - **Name:** `Run HumanLang`
   - **Program:** `hl`
   - **Arguments:** `run $FilePath$`
   - **Working directory:** `$FileDir$`
3. Click **OK**. Run it with **Tools > External Tools > Run HumanLang**, or right-click the file.

### Vim and Neovim

Run the open file from inside the editor:

```config
:!hl run %
```

To set the file type for `.hum` files, add this line to your `vimrc` (Neovim: `init.vim`):

```config
autocmd BufRead,BufNewFile *.hum setfiletype humanlang
```

### Emacs

Press **M-x**, type `compile`, press **Enter**, and then type the command with your file name:

```config
hl run hello.hum
```

### Helix and Zed

Zed has a terminal panel: press **Ctrl + `**, then type `hl run hello.hum`. Helix has none, so keep a terminal window open next to it and type `hl run hello.hum` there.

### Any other editor

Every editor can save a file, and every computer has a terminal. So this always works:

1. Save your file, for example `hello.hum`.
2. Open a terminal in the same folder.
3. Type:

```terminal
hl run hello.hum
```

## Colours and live help in other editors

HumanLang comes with a **language server**. That is a small helper that tells an editor where your mistakes are and what words could come next. Start it with `hl lsp`. Editors that can talk to a language server can use it:

**Neovim (version 0.11 or newer):** put this in your `init.lua`.

```config
vim.filetype.add({ extension = { hum = "humanlang" } })
vim.lsp.config("humanlang", { cmd = { "hl", "lsp" }, filetypes = { "humanlang" } })
vim.lsp.enable("humanlang")
```

**Helix:** add this to your `languages.toml`.

```config
[language-server.humanlang]
command = "hl"
args = ["lsp"]

[[language]]
name = "humanlang"
scope = "source.humanlang"
file-types = ["hum"]
language-servers = ["humanlang"]
comment-token = "note:"
```

**Sublime Text:** install the **LSP** package, then add this under **Preferences > Package Settings > LSP > Settings**.

```config
{
    "clients": {
        "humanlang": {
            "enabled": true,
            "command": ["hl", "lsp"],
            "selector": "source.humanlang"
        }
    }
}
```

**Emacs (eglot):**

```config
(define-derived-mode humanlang-mode prog-mode "HL")
(add-to-list 'auto-mode-alist '("\\.hum\\'" . humanlang-mode))
(add-to-list 'eglot-server-programs '(humanlang-mode . ("hl" "lsp")))
```

These recipes follow each editor's normal rules for adding a language server. The colour themes for these editors are not made yet; the VS Code extension is the only one that ships colours today. If something in this page does not work for your editor, please [tell us](https://github.com/notsabbir4/HumanLang/issues) which editor and what you saw.

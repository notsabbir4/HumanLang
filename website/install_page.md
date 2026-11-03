# Install HumanLang

## Step by step: Windows

You need a Windows computer (Windows 10 or Windows 11). This takes about two minutes.

1. **Download the installer.** Click the big blue **Download for Windows** button at the top of this page. A file called `HumanLang-Setup.exe` goes to your **Downloads** folder.
2. **Open it.** Open the **Downloads** folder and double-click `HumanLang-Setup.exe`.
3. **If Windows shows a blue box that says "Windows protected your PC":** don't worry, nothing is wrong. Windows says this about every new program it has not seen before. Click the small words **More info**. A new button appears. Click **Run anyway**.
4. **Click Next.** The installer asks two questions. Leave both boxes ticked, then keep clicking **Next**, and then **Install**:
   - *Let me type "hl" in a terminal* lets you run HumanLang from a terminal window.
   - *Give .hum files the HumanLang icon* gives your HumanLang files their own little picture, and lets you run them with a double-click.
5. **Click Finish.** HumanLang is installed.

Now go to **Check that it works**, below.

## Step by step: Mac

You need a Mac with an M1 chip or newer (any Mac made since late 2020). This takes about one minute.

1. **Open the Terminal.** Press the **Command** key and the **Space bar** together. A search box appears. Type `Terminal` and press **Enter**. A window with a text prompt opens. This is where you type commands.
2. **Copy this line.** Click the **Copy** button on the box below.

```terminal
curl -fsSL https://notsabbir4.github.io/HumanLang/install.sh | sh
```

3. **Paste it and press Enter.** Click inside the Terminal window, press **Command + V** to paste, then press **Enter**. Words scroll by while it downloads. When it stops, it says `Installed: HumanLang ...`.
4. **Close the Terminal window and open a new one.** This lets the Mac find the new program.

Now go to **Check that it works**, below.

If you prefer to download the file yourself, the **Download for Mac** button at the top gives you `hl-macos`. The line above is easier, because the Mac does not block it.

## Step by step: Linux

This works on the usual kind of Linux computer (Ubuntu, Fedora, Debian, Mint and others on a 64-bit Intel or AMD processor).

1. **Open a terminal.** On most systems you press **Ctrl + Alt + T**.
2. **Copy this line, paste it, and press Enter.** (Paste in a terminal with **Ctrl + Shift + V**.)

```terminal
curl -fsSL https://notsabbir4.github.io/HumanLang/install.sh | sh
```

3. **Close the terminal and open a new one.**

Now go to **Check that it works**, below.

## Check that it works

First, open a terminal window:

- **Windows:** press the **Windows key** (the one with the four squares), type `cmd`, and press **Enter**. A black window opens.
- **Mac:** press **Command + Space**, type `Terminal`, press **Enter**.
- **Linux:** press **Ctrl + Alt + T**.

Type this and press **Enter**:

```terminal
hl --version
```

If it prints something like `HumanLang 0.3.1`, then HumanLang works. If it says `hl is not recognized` or `command not found`, look at **Something wrong?** at the bottom of this page.

## Your first program

A HumanLang program is just a text file whose name ends in `.hum`.

**On Windows**

1. Press the **Windows key**, type `Notepad`, and press **Enter**.
2. Type this one line exactly:

```hum-fragment
say "Hello, world!"
```

3. Click **File**, then **Save as**. Choose the **Desktop** on the left.
4. In the box **Save as type**, choose **All files**. (If you skip this, Windows secretly saves `hello.hum.txt`, which will not work.)
5. In **File name**, type `hello.hum` and click **Save**.
6. On your Desktop, **double-click** `hello.hum`. A black window opens and says `Hello, world!`. It stays open so you can read it. Close it with the **X**.

**On Mac or Linux**

Open a text editor, type the same line, and save the file as `hello.hum` in your home folder. Then, in a terminal, type:

```terminal
hl run hello.hum
```

You should see:

```output
Hello, world!
```

On Windows you can also run it from a terminal. Type `cd Desktop` and press **Enter**, then type `hl run hello.hum` and press **Enter**.

## Where to go next

- Learn HumanLang in about an hour with the [tutorial](tutorial.html). Every example in it really runs.
- Want better colours and a **Run** button while you write? Set up a code editor: [Editors](editors.html).
- Want to try something right now? The [Playground](playground.html) runs in your browser.

## Something wrong?

| What you see | What to do |
|---|---|
| `hl` is not recognized, or `command not found` | Close the terminal window and open a **new** one. Windows and Macs only look for new programs when a terminal starts. If it still fails on Windows, run `HumanLang-Setup.exe` again and keep the box *Let me type "hl" in a terminal* ticked. |
| Windows says **"Windows protected your PC"** | Click **More info**, then **Run anyway**. The installer is safe, but Windows warns about every program from a small team. |
| Your antivirus program blocks the download | Try the download again, or tell your antivirus to allow `HumanLang-Setup.exe`. You can also use the [Playground](playground.html) with nothing to install. |
| The `.hum` file shows no icon on Windows | Windows remembers old pictures. Sign out and sign back in, or restart the computer. |
| `I can't find the file` | The terminal is in a different folder from your file. Use `cd` to go to the folder that holds it, for example `cd Desktop`. |
| Letters look broken on Windows | Open **Windows Terminal** instead, or type `chcp 65001` and press **Enter** first. |
| Mac or Linux says the computer type is not supported | The ready-made program is for 64-bit Intel/AMD Linux and for Macs with an M1 chip or newer. On other computers, use the [Playground](playground.html). |

## How to remove HumanLang

- **Windows:** open **Settings**, then **Apps**, then **Installed apps**, find **HumanLang**, and choose **Uninstall**.
- **Mac or Linux:** in a terminal, type `rm ~/.local/bin/hl`.

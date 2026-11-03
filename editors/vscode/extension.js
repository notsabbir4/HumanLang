// HumanLang for VS Code:
//   - colours and snippets come from the grammar (no code needed)
//   - the language server (`hl lsp`) gives live error messages and completion
//   - "Run" button / Ctrl+F5 runs the open file with `hl run`
const vscode = require("vscode");
const { workspace, window, commands } = vscode;
const { LanguageClient } = require("vscode-languageclient/node");

let client;
let warned = false;

function hlCommand() {
  const parts = workspace.getConfiguration("humanlang").get("command", "hl").trim().split(/\s+/);
  return { command: parts[0], args: parts.slice(1) };
}

function explainMissing() {
  if (warned) return;
  warned = true;
  window
    .showWarningMessage(
      'HumanLang: I could not start the "hl" program. Colours still work, but live errors and the Run button need it. ' +
        "Install HumanLang from https://notsabbir4.github.io/HumanLang/install.html, then restart VS Code.",
      "Open the install page"
    )
    .then((pick) => {
      if (pick) vscode.env.openExternal(vscode.Uri.parse("https://notsabbir4.github.io/HumanLang/install.html"));
    });
}

function startServer() {
  const { command, args } = hlCommand();
  client = new LanguageClient(
    "humanlang",
    "HumanLang",
    { command, args: args.concat(["lsp"]) },
    { documentSelector: [{ scheme: "file", language: "humanlang" }] }
  );
  client.start().catch(explainMissing);
  client.onDidChangeState && client.onDidChangeState((e) => {
    if (e.newState === 1 /* Stopped */) explainMissing();
  });
}

async function currentFile() {
  const editor = window.activeTextEditor;
  if (!editor || editor.document.languageId !== "humanlang") {
    window.showInformationMessage("Open a HumanLang file (ending in .hum) first.");
    return null;
  }
  if (editor.document.isUntitled) {
    window.showInformationMessage("Save the file first (Ctrl+S), and give it a name ending in .hum.");
    return null;
  }
  await editor.document.save();
  return editor.document.fileName;
}

async function runInTerminal(sub) {
  const file = await currentFile();
  if (!file) return;
  const { command, args } = hlCommand();
  let terminal = window.terminals.find((t) => t.name === "HumanLang");
  if (!terminal || terminal.exitStatus) terminal = window.createTerminal("HumanLang");
  terminal.show(true);
  terminal.sendText([command, ...args, sub, `"${file}"`].join(" "));
}

function activate(context) {
  context.subscriptions.push(
    commands.registerCommand("humanlang.run", () => runInTerminal("run")),
    commands.registerCommand("humanlang.check", () => runInTerminal("check"))
  );
  startServer();
}

function deactivate() {
  return client ? client.stop() : undefined;
}

module.exports = { activate, deactivate };

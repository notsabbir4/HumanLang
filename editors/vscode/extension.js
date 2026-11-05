// HumanLang for VS Code:
//   - colours and snippets come from the grammar (no code needed)
//   - the language server (`hl lsp`) gives live error messages and completion
//   - "Run" button / Ctrl+F5 runs the open file with `hl run`
//   - a program that shows a page (design) gets a live preview panel beside the editor
const vscode = require("vscode");
const { workspace, window, commands } = vscode;
const { LanguageClient } = require("vscode-languageclient/node");
const { spawn } = require("child_process");

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

// ---- design preview: a program that says "show a page" is drawn in a panel beside the editor ----
let panel = null;
let lastGoodHtml = null;
let previewDoc = null;
let timer = null;
let output = null;

const showsAPage = (text) => /^[ \t]*show a page\b/m.test(text);
const escapeHtml = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const SAFE = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src data:;">';

// Runs `hl page --json -` with the program on standard input. Resolves to {html, output, error}.
function renderPage(text) {
  return new Promise((resolve) => {
    const { command, args } = hlCommand();
    let out = "", err = "";
    let child;
    try {
      child = spawn(command, [...args, "page", "--json", "-"], { windowsHide: true });
    } catch (e) {
      resolve({ html: null, output: "", error: 'I could not start "hl": ' + e.message });
      return;
    }
    child.stdout.on("data", (d) => (out += d));
    child.stderr.on("data", (d) => (err += d));
    child.on("error", (e) => resolve({ html: null, output: "", error: 'I could not start "hl" (' + e.message + "). Install HumanLang from https://notsabbir4.github.io/HumanLang/install.html and restart VS Code." }));
    child.on("close", () => {
      try { resolve(JSON.parse(out)); }
      catch (e) { resolve({ html: null, output: "", error: err || "The preview gave no answer." }); }
    });
    child.stdin.on("error", () => {});
    child.stdin.end(text);
  });
}

function banner(message) {
  return '<div style="position:sticky;top:0;z-index:9;padding:8px 14px;background:#fff3cd;color:#664d03;font:14px system-ui;white-space:pre-wrap;border-bottom:1px solid #ffe69c">' +
    escapeHtml(message) + "</div>";
}

function withSafety(html, message) {
  let page = html.replace("<head>", "<head>\n" + SAFE);
  if (message) page = page.replace(/<body[^>]*>/, (m) => m + banner(message));
  return page;
}

async function updatePreview() {
  if (!panel || !previewDoc) return;
  const result = await renderPage(previewDoc.getText());
  if (!panel) return;
  if (result.output) {
    output = output || window.createOutputChannel("HumanLang");
    output.clear();
    output.append(result.output);
  }
  if (result.html && !result.error) {
    lastGoodHtml = result.html;
    panel.webview.html = withSafety(result.html);
  } else if (lastGoodHtml) {
    panel.webview.html = withSafety(lastGoodHtml, "Showing your last working page. Fix this:\n" + (result.error || "This program doesn't show a page."));
  } else {
    panel.webview.html = withSafety("<!doctype html><html><head><meta charset=\"utf-8\"></head><body></body></html>",
      result.error || 'This program doesn\'t show a page yet. Start one with:  show a page titled "My page"');
  }
}

function openPreview() {
  const editor = window.activeTextEditor;
  if (!editor || editor.document.languageId !== "humanlang") {
    window.showInformationMessage("Open a HumanLang file (ending in .hum) first.");
    return;
  }
  previewDoc = editor.document;
  if (!panel) {
    panel = window.createWebviewPanel("humanlangPreview", "HumanLang preview", { viewColumn: vscode.ViewColumn.Beside, preserveFocus: true }, { enableScripts: false });
    panel.onDidDispose(() => { panel = null; lastGoodHtml = null; });
  } else {
    panel.reveal(vscode.ViewColumn.Beside, true);
  }
  panel.title = "Preview: " + require("path").basename(previewDoc.fileName || "untitled.hum");
  updatePreview();
}

function onTextChange(event) {
  if (!panel || !previewDoc || event.document !== previewDoc) return;
  clearTimeout(timer);
  timer = setTimeout(updatePreview, 400);  // wait until typing pauses
}

function onEditorChange(editor) {
  if (!panel || !editor || editor.document.languageId !== "humanlang") return;
  if (editor.document !== previewDoc) {
    previewDoc = editor.document;
    lastGoodHtml = null;
    panel.title = "Preview: " + require("path").basename(previewDoc.fileName || "untitled.hum");
    updatePreview();
  }
}

// Run: a program that shows a page opens the preview; any other program runs in the terminal.
function runCommand() {
  const editor = window.activeTextEditor;
  if (editor && editor.document.languageId === "humanlang" && showsAPage(editor.document.getText())) {
    openPreview();
    return;
  }
  return runInTerminal("run");
}

function activate(context) {
  context.subscriptions.push(
    commands.registerCommand("humanlang.run", runCommand),
    commands.registerCommand("humanlang.check", () => runInTerminal("check")),
    commands.registerCommand("humanlang.preview", openPreview),
    workspace.onDidChangeTextDocument(onTextChange),
    window.onDidChangeActiveTextEditor(onEditorChange)
  );
  startServer();
}

function deactivate() {
  return client ? client.stop() : undefined;
}

module.exports = { activate, deactivate };

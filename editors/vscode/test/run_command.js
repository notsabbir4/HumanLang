// Checks the Run / Check commands against a stand-in for VS Code.  node editors/vscode/test/run_command.js
const Module = require("module");
const sent = []; const warnings = [];
let activeEditor = { document: { languageId: "humanlang", isUntitled: false, fileName: "C:\\Users\\me\\hello.hum", getText: () => "say \"hi\"", save: async () => true } };
const terminal = { name: "HumanLang", exitStatus: undefined, show() {}, sendText: (t) => sent.push(t) };
const vscode = {
  workspace: { getConfiguration: () => ({ get: (k, d) => (k === "command" && process.env.HL_TEST_COMMAND) || d }),
    onDidChangeTextDocument: (fn) => { vscode.onChange = fn; return { dispose() {} }; } },
  window: { get activeTextEditor() { return activeEditor; },
    onDidChangeActiveTextEditor: () => ({ dispose() {} }),
    createOutputChannel: () => ({ clear() {}, append: (t) => vscode.printed.push(t) }),
    createWebviewPanel: (id, title, col, opts) => { vscode.panel = { webview: { html: "" }, title, opts, onDidDispose() {}, reveal() {} }; return vscode.panel; }, terminals: [], createTerminal: () => terminal,
    showInformationMessage: (m) => warnings.push(m), showWarningMessage: () => Promise.resolve(undefined) },
  commands: { registerCommand: (id, fn) => { vscode.registered[id] = fn; return { dispose() {} }; } },
  registered: {}, printed: [], env: {}, Uri: {}, ViewColumn: { Beside: 2 },
};
const orig = Module._load;
Module._load = function (req, ...r) {
  if (req === "vscode") return vscode;
  if (req === "vscode-languageclient/node") return { LanguageClient: class { constructor(...a) { this.a = a; } start() { return Promise.reject(new Error("no hl")); } } };
  return orig.call(this, req, ...r);
};
(async () => {
  const ext = require(require("path").join(__dirname, "..", "extension.js"));
  ext.activate({ subscriptions: [] });
  await vscode.registered["humanlang.run"]();
  await vscode.registered["humanlang.check"]();
  activeEditor = { document: { languageId: "plaintext" } };
  await vscode.registered["humanlang.run"]();
  const assert = require("assert");
  // design preview: needs Python and the HumanLang source (HL_TEST_COMMAND="python3 -m humanlang", PYTHONPATH=repo root)
  if (process.env.HL_TEST_COMMAND) {
    const doc = (text) => ({ languageId: "humanlang", isUntitled: false, fileName: "/tmp/x.hum", getText: () => text, save: async () => true });
    activeEditor = { document: doc('say "hello from the program"\nshow a page titled "Hi"\n    put a button "Go"\n') };
    await vscode.registered["humanlang.run"]();   // a program that shows a page opens the preview, not the terminal
    for (let i = 0; i < 100 && !vscode.panel.webview.html; i++) await new Promise((r) => setTimeout(r, 100));
    const html = vscode.panel.webview.html;
    assert.ok(html.includes("<button") && html.includes(">Go<"), "the page is in the preview");
    assert.ok(html.includes("Content-Security-Policy"), "the preview forbids scripts");
    assert.strictEqual(sent.length, 2, "the terminal was not used for a page");
    assert.deepStrictEqual(vscode.printed, ["hello from the program\n"]);
    // a typo keeps the last good page and says what is wrong
    activeEditor.document = doc('show a page titled "Hi"\n    put a buton "Go"\n');
    vscode.onChange({ document: activeEditor.document }); // not the preview's document: ignored
    const same = vscode.panel.webview.html;
    assert.strictEqual(same, html);
    console.log("Design preview: ok");
  }
  const hl = process.env.HL_TEST_COMMAND || "hl";
  assert.deepStrictEqual(sent, [hl + ' run "C:\\Users\\me\\hello.hum"', hl + ' check "C:\\Users\\me\\hello.hum"']);
  assert.deepStrictEqual(warnings, ["Open a HumanLang file (ending in .hum) first."]);
  console.log("Run command: ok");
})();

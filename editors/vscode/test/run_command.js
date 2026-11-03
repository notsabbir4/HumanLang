// Checks the Run / Check commands against a stand-in for VS Code.  node editors/vscode/test/run_command.js
const Module = require("module");
const sent = []; const warnings = [];
let activeEditor = { document: { languageId: "humanlang", isUntitled: false, fileName: "C:\\Users\\me\\hello.hum", save: async () => true } };
const terminal = { name: "HumanLang", exitStatus: undefined, show() {}, sendText: (t) => sent.push(t) };
const vscode = {
  workspace: { getConfiguration: () => ({ get: (k, d) => d }) },
  window: { get activeTextEditor() { return activeEditor; }, terminals: [], createTerminal: () => terminal,
    showInformationMessage: (m) => warnings.push(m), showWarningMessage: () => Promise.resolve(undefined) },
  commands: { registerCommand: (id, fn) => { vscode.registered[id] = fn; return { dispose() {} }; } },
  registered: {}, env: {}, Uri: {},
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
  assert.deepStrictEqual(sent, ['hl run "C:\\Users\\me\\hello.hum"', 'hl check "C:\\Users\\me\\hello.hum"']);
  assert.deepStrictEqual(warnings, ["Open a HumanLang file (ending in .hum) first."]);
  console.log("Run command: ok");
})();

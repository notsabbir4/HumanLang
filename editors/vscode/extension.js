// Starts the HumanLang language server (`hl lsp`) for .hum files.
// Not required for syntax highlighting, which works from the grammar alone.
const { workspace } = require("vscode");
const { LanguageClient } = require("vscode-languageclient/node");

let client;

function activate() {
  const parts = workspace.getConfiguration("humanlang").get("command", "hl").trim().split(/\s+/);
  const command = parts[0];
  const args = parts.slice(1).concat(["lsp"]);
  client = new LanguageClient(
    "humanlang",
    "HumanLang",
    { command, args },
    { documentSelector: [{ scheme: "file", language: "humanlang" }] }
  );
  client.start();
}

function deactivate() {
  return client ? client.stop() : undefined;
}

module.exports = { activate, deactivate };

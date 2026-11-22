// The CardLang extension for VS Code (TL1). Plain JavaScript, no build step.
//
// - Highlighting comes from the TextMate grammars in syntaxes/ (declared in package.json).
// - Diagnostics as you type come from the CardLang language server, tools/lsp/cardlang_lsp.py, a Python program
//   in the CardLang repository, started through uv and spoken to with vscode-languageclient.
// - Build Applet, Check Applet and Run Scenario run tools/clc.py as tasks; build errors also go to the Problems
//   panel through the $cardlang problem matcher.
"use strict";
const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { LanguageClient } = require("vscode-languageclient/node");

let client = null;
let output = null;

/** The CardLang repository: the setting, else a workspace folder (or a parent of one) with tools/clc.py. */
function toolsRoot() {
  const configured = vscode.workspace.getConfiguration("cardlang").get("toolsPath");
  if (configured) return configured;
  for (const folder of vscode.workspace.workspaceFolders || []) {
    let dir = folder.uri.fsPath;
    for (let i = 0; i < 6; i++) {
      if (fs.existsSync(path.join(dir, "tools", "clc.py"))) return dir;
      const up = path.dirname(dir);
      if (up === dir) break;
      dir = up;
    }
  }
  return null;
}

function uv() {
  return vscode.workspace.getConfiguration("cardlang").get("uvPath") || "uv";
}

/** uv arguments that run a Python script of the repository in its environment. */
function pythonArgs(root, script, args) {
  return ["run", "--project", root, "python", "-I", path.join(root, script), ...args];
}

/** The program of the active editor: the directory of its cardlang.json if it lists the file, else the file. */
function programOf(file) {
  const dir = path.dirname(file);
  const project = path.join(dir, "cardlang.json");
  if (fs.existsSync(project)) {
    try {
      const meta = JSON.parse(fs.readFileSync(project, "utf8"));
      if ((meta.files || []).some((f) => path.resolve(dir, f).toLowerCase() === path.resolve(file).toLowerCase())) return dir;
    } catch (e) { /* not a project file we can read: treat the file on its own */ }
  }
  return file;
}

function runTask(root, name, args, matchErrors) {
  const execution = new vscode.ProcessExecution(uv(), pythonArgs(root, path.join("tools", "clc.py"), args), { cwd: root });
  const task = new vscode.Task({ type: "cardlang", command: args[0] }, vscode.TaskScope.Workspace, name, "cardlang",
                               execution, matchErrors ? ["$cardlang"] : []);
  task.presentationOptions = { reveal: vscode.TaskRevealKind.Always, clear: true };
  return vscode.tasks.executeTask(task);
}

function activeFile(languageId) {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.uri.scheme !== "file") return null;
  if (languageId && editor.document.languageId !== languageId) return null;
  return editor.document;
}

async function startClient(context, root) {
  const server = { command: uv(), args: pythonArgs(root, path.join("tools", "lsp", "cardlang_lsp.py"), []), options: { cwd: root } };
  client = new LanguageClient("cardlang", "CardLang", { run: server, debug: server }, {
    documentSelector: [{ scheme: "file", language: "cardlang" }],
    outputChannel: output,
    synchronize: { fileEvents: vscode.workspace.createFileSystemWatcher("**/{*.card,cardlang.json}") },
  });
  await client.start();
}

async function activate(context) {
  // A log channel: vscode-languageclient 11 logs through it (error, onDidChangeLogLevel), and traces into it too.
  output = vscode.window.createOutputChannel("CardLang", { log: true });
  context.subscriptions.push(output);
  const root = toolsRoot();
  if (!root) {
    vscode.window.showWarningMessage("CardLang: set cardlang.toolsPath to the CardLang repository (the folder with tools/clc.py).");
    return;
  }
  output.info(`CardLang tools: ${root}`);
  try { await startClient(context, root); }
  catch (e) {
    output.error(`The language server did not start: ${e && e.stack ? e.stack : e}`);
    vscode.window.showErrorMessage(`CardLang: the language server did not start (${e}). See the CardLang output channel.`);
  }

  const program = async (save) => {
    const doc = activeFile("cardlang");
    if (!doc) { vscode.window.showInformationMessage("CardLang: open a .card file of the applet first."); return null; }
    if (save) await vscode.workspace.saveAll(false);
    return programOf(doc.uri.fsPath);
  };
  context.subscriptions.push(
    vscode.commands.registerCommand("cardlang.build", async () => {
      const p = await program(true);
      if (p) await runTask(root, "build", ["build", p], true);
    }),
    vscode.commands.registerCommand("cardlang.check", async () => {
      const p = await program(true);
      if (p) await runTask(root, "check", ["check", p], true);
    }),
    vscode.commands.registerCommand("cardlang.runScenario", async () => {
      const doc = activeFile("cardlang-scenario");
      if (!doc) { vscode.window.showInformationMessage("CardLang: open a scenario file first."); return; }
      await vscode.workspace.saveAll(false);
      const backend = vscode.workspace.getConfiguration("cardlang").get("scenarioBackend") || "pyvm";
      await runTask(root, "run scenario", ["run", doc.uri.fsPath, "--backend", backend], true);
    }),
    vscode.commands.registerCommand("cardlang.restartServer", async () => {
      if (client) await client.stop();
      await startClient(context, root);
    }),
    // Debugging (TL1 step 6): tools/dap/cardlang_dap.py runs a scenario on the prototype VM.
    vscode.commands.registerCommand("cardlang.debugScenario", async () => {
      const doc = activeFile("cardlang-scenario");
      if (!doc) { vscode.window.showInformationMessage("CardLang: open a scenario file first."); return; }
      await vscode.workspace.saveAll(false);
      await vscode.debug.startDebugging(vscode.workspace.getWorkspaceFolder(doc.uri),
        { type: "cardlang", request: "launch", name: `Debug ${path.basename(doc.uri.fsPath)}`, scenario: doc.uri.fsPath });
    }),
    vscode.debug.registerDebugAdapterDescriptorFactory("cardlang", {
      createDebugAdapterDescriptor: () =>
        new vscode.DebugAdapterExecutable(uv(), pythonArgs(root, path.join("tools", "dap", "cardlang_dap.py"), []), { cwd: root }),
    }),
    vscode.debug.registerDebugConfigurationProvider("cardlang", {
      // F5 without a launch.json: debug the scenario in the editor.
      resolveDebugConfiguration(folder, config) {
        if (!config.type && !config.request && !config.name) {
          const doc = activeFile("cardlang-scenario");
          if (!doc) {
            vscode.window.showInformationMessage("CardLang: open a scenario file to debug, or add a launch configuration.");
            return undefined;
          }
          return { type: "cardlang", request: "launch", name: "Debug scenario", scenario: doc.uri.fsPath };
        }
        if (!config.scenario) {
          vscode.window.showErrorMessage("CardLang: the launch configuration needs a \"scenario\".");
          return undefined;
        }
        return config;
      },
    })
  );
}

async function deactivate() {
  if (client) await client.stop();
}

module.exports = { activate, deactivate };

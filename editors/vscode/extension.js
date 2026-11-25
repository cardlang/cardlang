// The CardLang extension for VS Code. Plain JavaScript, no build step.
//
// - Highlighting comes from the TextMate grammars in syntaxes/ (declared in package.json).
// - Diagnostics as you type come from the CardLang language server, the command cardlang-lsp of the cardlang
//   package in the CardLang repository, started through uv and spoken to with vscode-languageclient.
// - Build Applet, Check Applet and Run Scenario run the command clc as tasks; build errors also go to the Problems
//   panel through the $cardlang problem matcher.
// - Debugging runs the command cardlang-dap.
// Each command runs through uv, in one of two environments:
// - the CardLang repository's, when the workspace is the repository or cardlang.repository names it: uv run --project;
// - else the toolchain bundled in this extension (toolchain/), once the user has agreed to set it up: toolchain.js
//   installs uv and the environment into the extension's storage.
"use strict";
const vscode = require("vscode");
const path = require("path");
const fs = require("fs");
const { spawnSync } = require("child_process");
const { LanguageClient } = require("vscode-languageclient/node");
const toolchain = require("./toolchain.js");

let client = null;
let output = null;
let tools = null;          // how to run a command: { uv, run(command, args) -> { args, env }, cwd }, or null
let settingUp = null;      // the setup in progress, if any
const DECLINED = "cardlang.setupDeclined";

/** Whether dir holds the CardLang repository: a pyproject.toml whose project is named cardlang. */
function isRepository(dir) {
  try { return /^\s*name\s*=\s*"cardlang"\s*$/m.test(fs.readFileSync(path.join(dir, "pyproject.toml"), "utf8")); }
  catch (e) { return false; }
}

/** The CardLang repository: the setting, else a workspace folder (or a parent of one) that is the repository. */
function toolsRoot() {
  const configured = vscode.workspace.getConfiguration("cardlang").get("repository");
  if (configured) return configured;
  for (const folder of vscode.workspace.workspaceFolders || []) {
    let dir = folder.uri.fsPath;
    for (let i = 0; i < 6; i++) {
      if (isRepository(dir)) return dir;
      const up = path.dirname(dir);
      if (up === dir) break;
      dir = up;
    }
  }
  return null;
}

/** The bundled toolchain's facts: where it is, the uv pin, where the extension keeps its own files. */
function bundled(context) {
  const pin = JSON.parse(fs.readFileSync(path.join(context.extensionPath, "uv.json"), "utf8"));
  return { bundle: path.join(context.extensionPath, "toolchain"), storage: context.globalStorageUri.fsPath,
           version: context.extension.packageJSON.version, pin };
}

/** The uv the user configured, or null. */
function configuredUv() {
  return vscode.workspace.getConfiguration("cardlang").get("uvPath") || null;
}

/** How to run the toolchain's commands (clc, cardlang-lsp, cardlang-dap), or null before the setup. */
function findTools(context) {
  const b = bundled(context);
  const own = toolchain.ownUv(b.storage, b.pin);
  const uv = configuredUv() || (fs.existsSync(own) ? own : "uv");
  const root = toolsRoot();
  // A repository with no uv to run it: the setup provides one.
  if (root && uv === "uv" && spawnSync("uv", ["--version"], { stdio: "ignore" }).status !== 0) return null;
  if (root) return { uv, where: root, cwd: root, run: (command, args) => ({ args: ["run", "--project", root, command, ...args], env: {} }) };
  if (fs.existsSync(b.bundle) && toolchain.isReady(b.storage, b.version)) {
    return { uv, where: `the bundled toolchain, ${toolchain.envDir(b.storage, b.version)}`, cwd: b.bundle,
             run: (command, args) => toolchain.bundledRun(b.bundle, b.storage, b.version, command, args) };
  }
  return null;
}

/** Offer the setup; true once the tools are there. asked: the user ran a command, so ask even after a "Not Now". */
async function offerSetUp(context, asked) {
  if (tools) return true;
  if (settingUp) return settingUp;
  const b = bundled(context);
  if (!fs.existsSync(b.bundle)) {
    vscode.window.showWarningMessage("CardLang: set cardlang.repository to the CardLang repository (the folder whose pyproject.toml names cardlang).");
    return false;
  }
  if (!asked && context.globalState.get(DECLINED)) {
    output.info("The toolchain is not set up: run CardLang: Set Up Toolchain, or set cardlang.repository.");
    return false;
  }
  const uvNote = configuredUv() ? `uses your uv (${configuredUv()})` :
    `downloads uv ${b.pin.version} from github.com/astral-sh/uv, checked against a pinned SHA-256,`;
  const choice = await vscode.window.showInformationMessage(
    `CardLang: the compiler, language server and debugger need a one-time setup. It ${uvNote} and through uv installs ` +
    "Python (if needed) and the toolchain into VS Code's storage for this extension. " +
    "Alternatively, set cardlang.repository to a clone of the CardLang repository.",
    "Set Up", "Not Now");
  if (choice !== "Set Up") {
    if (!asked) await context.globalState.update(DECLINED, true);
    return false;
  }
  await context.globalState.update(DECLINED, undefined);
  settingUp = setUp(context).finally(() => { settingUp = null; });
  return settingUp;
}

async function setUp(context) {
  const b = bundled(context);
  output.show(true);
  try {
    await vscode.window.withProgress(
      { location: vscode.ProgressLocation.Notification, title: "CardLang: setting up the toolchain", cancellable: true },
      async (progress, token) => {
        await toolchain.setUp({ ...b, uv: configuredUv(), cancelled: () => token.isCancellationRequested,
          log: (line) => { output.info(line); progress.report({ message: line.length > 80 ? line.slice(0, 77) + "..." : line }); } });
      });
  } catch (e) {
    output.error(`The setup failed: ${e && e.stack ? e.stack : e}`);
    vscode.window.showErrorMessage(`CardLang: the setup failed (${e.message || e}). See the CardLang output channel. ` +
      "You can install uv yourself and set cardlang.uvPath, or use a clone of the CardLang repository.");
    return false;
  }
  return startTools(context);
}

/** Find the tools and start the language server; true if the tools are there. */
async function startTools(context) {
  tools = findTools(context);
  if (!tools) return false;
  output.info(`CardLang tools: ${tools.where}, run by ${tools.uv}`);
  try { await startClient(); }
  catch (e) {
    output.error(`The language server did not start: ${e && e.stack ? e.stack : e}`);
    vscode.window.showErrorMessage(`CardLang: the language server did not start (${e}). See the CardLang output channel.`);
  }
  return true;
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

function runTask(name, args, matchErrors) {
  const run = tools.run("clc", args);
  const execution = new vscode.ProcessExecution(tools.uv, run.args, { cwd: tools.cwd, env: run.env });
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

async function startClient() {
  const run = tools.run("cardlang-lsp", []);
  const server = { command: tools.uv, args: run.args, options: { cwd: tools.cwd, env: { ...process.env, ...run.env } } };
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
  if (!(await startTools(context))) offerSetUp(context, false);     // not awaited: activation must not wait for it

  // Every command needs the tools: before the setup, it offers the setup instead.
  const ready = () => offerSetUp(context, true);
  const program = async (save) => {
    if (!(await ready())) return null;
    const doc = activeFile("cardlang");
    if (!doc) { vscode.window.showInformationMessage("CardLang: open a .card file of the applet first."); return null; }
    if (save) await vscode.workspace.saveAll(false);
    return programOf(doc.uri.fsPath);
  };
  context.subscriptions.push(
    vscode.commands.registerCommand("cardlang.build", async () => {
      const p = await program(true);
      if (p) await runTask("build", ["build", p], true);
    }),
    vscode.commands.registerCommand("cardlang.check", async () => {
      const p = await program(true);
      if (p) await runTask("check", ["check", p], true);
    }),
    vscode.commands.registerCommand("cardlang.runScenario", async () => {
      if (!(await ready())) return;
      const doc = activeFile("cardlang-scenario");
      if (!doc) { vscode.window.showInformationMessage("CardLang: open a scenario file first."); return; }
      await vscode.workspace.saveAll(false);
      const backend = vscode.workspace.getConfiguration("cardlang").get("scenarioBackend") || "pyvm";
      await runTask("run scenario", ["run", doc.uri.fsPath, "--backend", backend], true);
    }),
    vscode.commands.registerCommand("cardlang.restartServer", async () => {
      if (!(await ready())) return;
      if (client) await client.stop();
      await startClient();
    }),
    vscode.commands.registerCommand("cardlang.setUpToolchain", async () => {
      if (settingUp) return settingUp;
      if (!fs.existsSync(bundled(context).bundle)) { await offerSetUp(context, true); return; }
      await context.globalState.update(DECLINED, undefined);
      if (client) { await client.stop(); client = null; }
      tools = null;
      settingUp = setUp(context).finally(() => { settingUp = null; });
      return settingUp;
    }),
    // Debugging: cardlang-dap runs a scenario on the Python VM.
    vscode.commands.registerCommand("cardlang.debugScenario", async () => {
      if (!(await ready())) return;
      const doc = activeFile("cardlang-scenario");
      if (!doc) { vscode.window.showInformationMessage("CardLang: open a scenario file first."); return; }
      await vscode.workspace.saveAll(false);
      await vscode.debug.startDebugging(vscode.workspace.getWorkspaceFolder(doc.uri),
        { type: "cardlang", request: "launch", name: `Debug ${path.basename(doc.uri.fsPath)}`, scenario: doc.uri.fsPath });
    }),
    vscode.debug.registerDebugAdapterDescriptorFactory("cardlang", {
      createDebugAdapterDescriptor: async () => {
        if (!(await ready())) return undefined;
        const run = tools.run("cardlang-dap", []);
        return new vscode.DebugAdapterExecutable(tools.uv, run.args, { cwd: tools.cwd, env: run.env });
      },
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

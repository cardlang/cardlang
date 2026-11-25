// The self-test of the extension's own setup, run outside VS Code: by CI on Windows, macOS and Linux, and by hand.
//
//   node selftest.js <extension> [<storage>]
//
// <extension> is an unpacked extension (the extension/ folder of a .vsix), so the test uses exactly the shipped
// toolchain.js, uv.json and toolchain/. <storage> stands in for VS Code's storage folder (default: a new temporary
// folder). The test runs the setup as the extension does, downloading the pinned uv, and then uses only the bundled
// toolchain, from a folder outside any repository:
//   - clc check, build and run on a small applet and its scenario;
//   - the language server: it starts, reports a mistake in a file, and completes `card.` from the Base Profile;
//   - the debug adapter: it starts and answers initialize.
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawn, spawnSync } = require("child_process");

const extension = path.resolve(process.argv[2] || "");
if (!process.argv[2] || !fs.existsSync(path.join(extension, "toolchain.js"))) {
  console.error("usage: node selftest.js <unpacked extension folder> [<storage folder>]");
  process.exit(2);
}
const toolchain = require(path.join(extension, "toolchain.js"));
const storage = path.resolve(process.argv[3] || fs.mkdtempSync(path.join(os.tmpdir(), "cardlang-storage-")));
const bundle = path.join(extension, "toolchain");
const version = JSON.parse(fs.readFileSync(path.join(extension, "package.json"), "utf8")).version;
const pin = JSON.parse(fs.readFileSync(path.join(extension, "uv.json"), "utf8"));

let failed = 0;
function check(name, passed, detail = "") {
  console.log(`${passed ? "PASS" : "FAIL"} ${name}${detail ? " | " + detail : ""}`);
  if (!passed) failed++;
}

const APPLET = `errors CounterError {
    NoRoom = 1;
    Exhausted = 2;
}

persistent counter: u32;

command process(request: ref u8[], response: inout u8[]) -> u32 {
    require response.length >= 4 else CounterError.NoRoom;
    counter = attempt checked_add(counter, 1) else CounterError.Exhausted;
    response[0..4] = encode_be(counter);
    return Ok(4);
}
`;
const SCENARIO = `install
power_on
command 00
expect ok 00 00 00 01
command 00
expect ok 00 00 00 02
`;

function lspMessage(body) {
  const json = JSON.stringify(body);
  return `Content-Length: ${Buffer.byteLength(json, "utf8")}\r\n\r\n${json}`;
}

/** Start a JSON-RPC server (LSP or DAP framing), send requests, and collect what it sends back until done() says so.
 *  Then send the closing messages and wait for the server to exit, as VS Code does, so it leaves no file in use. */
function converse(uv, command, messages, done, closing, timeoutMs = 60000) {
  return new Promise((resolve) => {
    const run = toolchain.bundledRun(bundle, storage, version, command, []);
    const child = spawn(uv, run.args, { cwd: bundle, env: { ...process.env, ...run.env } });
    const received = [];
    let buffer = Buffer.alloc(0), finished = false;
    child.on("close", () => { clearTimeout(timer); resolve(received); });
    const finish = () => {
      if (finished) return;
      finished = true;
      for (const m of closing) child.stdin.write(lspMessage(m));
      child.stdin.end();
      clearTimeout(timer);
      timer = setTimeout(() => child.kill(), 10000);           // a server that ignores the request to exit
    };
    let timer = setTimeout(finish, timeoutMs);
    child.stdout.on("data", (chunk) => {
      buffer = Buffer.concat([buffer, chunk]);
      for (;;) {
        const end = buffer.indexOf("\r\n\r\n");
        if (end < 0) break;
        const length = Number(/Content-Length: (\d+)/i.exec(buffer.slice(0, end).toString())[1]);
        if (buffer.length < end + 4 + length) break;
        received.push(JSON.parse(buffer.slice(end + 4, end + 4 + length).toString("utf8")));
        buffer = buffer.slice(end + 4 + length);
        if (done(received)) { finish(); return; }
      }
    });
    child.stderr.on("data", () => {});
    for (const m of messages) child.stdin.write(lspMessage(m));
  });
}

async function main() {
  console.log(`extension ${extension} (version ${version}), storage ${storage}, uv ${pin.version} for ${process.platform}-${process.arch}`);
  const uv = await toolchain.setUp({ bundle, storage, version, pin, uv: null, log: (line) => console.log(`  ${line}`) });
  check("the setup installs the pinned uv", uv === toolchain.ownUv(storage, pin) && fs.existsSync(uv), uv);
  check("the environment is marked ready", toolchain.isReady(storage, version));

  const work = fs.mkdtempSync(path.join(os.tmpdir(), "cardlang-applet-"));
  const applet = path.join(work, "counter.card");
  fs.writeFileSync(applet, APPLET);
  fs.writeFileSync(path.join(work, "counter.scenario"), SCENARIO);
  const clc = (args) => {
    const run = toolchain.bundledRun(bundle, storage, version, "clc", args);
    const r = spawnSync(uv, run.args, { cwd: work, env: { ...process.env, ...run.env }, encoding: "utf8" });
    return { code: r.status, out: `${r.stdout}${r.stderr}`.trim() };
  };
  let r = clc(["check", applet]);
  check("clc check", r.code === 0, r.out.split("\n").pop());
  r = clc(["build", applet, "-o", path.join(work, "counter.clvm")]);
  check("clc build", r.code === 0 && fs.existsSync(path.join(work, "counter.clvm")), r.out.split("\n").pop());
  r = clc(["run", path.join(work, "counter.scenario"), "--program", applet]);
  check("clc run", r.code === 0 && /passed/.test(r.out), r.out.split("\n").pop());
  fs.writeFileSync(path.join(work, "broken.card"), APPLET.replace("counter = attempt", "counter = attemp"));
  r = clc(["check", path.join(work, "broken.card")]);
  check("clc check reports a mistake with its code", r.code !== 0 && /CE-[A-Z]+-\d+/.test(r.out), r.out.split("\n")[0]);

  // The language server.
  const uri = "file:///" + applet.replace(/\\/g, "/").replace(/^\//, "");
  const broken = APPLET.replace("checked_add(counter, 1)", "checked_add(counter, true)") + "\nfunction f() {\n    card.\n}\n";
  const lines = broken.split("\n");
  const cardLine = lines.findIndex((l) => l.trim() === "card.");
  const lsp = await converse(uv, "cardlang-lsp", [
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { processId: null, rootUri: null, capabilities: {} } },
    { jsonrpc: "2.0", method: "initialized", params: {} },
    { jsonrpc: "2.0", method: "textDocument/didOpen", params: { textDocument: { uri, languageId: "cardlang", version: 1, text: broken } } },
    { jsonrpc: "2.0", id: 2, method: "textDocument/completion",
      params: { textDocument: { uri }, position: { line: cardLine, character: lines[cardLine].length } } },
  ], (got) => got.some((m) => m.id === 2) && got.some((m) => m.method === "textDocument/publishDiagnostics"),
    [{ jsonrpc: "2.0", id: 3, method: "shutdown", params: null }, { jsonrpc: "2.0", method: "exit", params: null }]);
  check("the language server answers initialize", lsp.some((m) => m.id === 1 && m.result && m.result.capabilities));
  const diagnostics = lsp.filter((m) => m.method === "textDocument/publishDiagnostics").flatMap((m) => m.params.diagnostics);
  check("the language server reports the mistake", diagnostics.length > 0, diagnostics.map((d) => d.code || d.message).join(", "));
  const completion = lsp.find((m) => m.id === 2);
  const items = completion && completion.result ? (completion.result.items || completion.result) : [];
  check("the language server completes card. from the Base Profile", items.some((i) => /random|crypto|key/.test(i.label)),
        `${items.length} items`);

  // The debug adapter.
  const dap = await converse(uv, "cardlang-dap", [
    { seq: 1, type: "request", command: "initialize", arguments: { adapterID: "cardlang", linesStartAt1: true, columnsStartAt1: true } },
  ], (got) => got.some((m) => m.type === "response" && m.command === "initialize"),
    [{ seq: 2, type: "request", command: "disconnect", arguments: {} }]);
  check("the debug adapter answers initialize", dap.some((m) => m.type === "response" && m.command === "initialize" && m.success));

  // A second setup reuses the downloaded uv.
  const again = await toolchain.setUp({ bundle, storage, version, pin, uv: null, log: () => {} });
  check("a second setup reuses the installed uv", again === uv);

  fs.rmSync(work, { recursive: true, force: true });
  console.log(failed ? `FAILED: ${failed}` : "ALL PASS");
  process.exit(failed ? 1 : 0);
}

main().catch((e) => { console.error(e && e.stack ? e.stack : e); process.exit(1); });

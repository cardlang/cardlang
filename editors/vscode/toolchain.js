// Setting up the bundled toolchain, for users without the CardLang repository. Plain Node, with no dependency on
// VS Code, so the self-test (selftest.js) runs exactly the code the extension runs.
//
// The extension carries the toolchain in toolchain/, copied in when it is packaged. The setup
//   1. downloads the uv pinned in uv.json for this platform, checks its SHA-256, and unpacks it into the storage
//      folder, as uv-<version>/ (skipped when the caller already has a uv);
//   2. runs `uv sync` on the bundle, into the storage folder's env-<extension version>/, so nothing is written inside
//      the extension's own folder; uv fetches a Python if the machine has none;
//   3. runs `clc --help` as a smoke test, and only then marks the environment ready.
"use strict";
const fs = require("fs");
const path = require("path");
const https = require("https");
const crypto = require("crypto");
const { spawn } = require("child_process");

const READY = ".cardlang-ready";
const exe = (name) => (process.platform === "win32" ? `${name}.exe` : name);

/** uv.json's entry for this machine, or null when uv publishes no build for it. */
function pinFor(pin) {
  return pin.platforms[`${process.platform}-${process.arch}`] || null;
}

/** Where the extension keeps its own uv. */
function ownUv(storage, pin) {
  return path.join(storage, `uv-${pin.version}`, exe("uv"));
}

/** The environment for this version of the extension. */
function envDir(storage, version) {
  return path.join(storage, `env-${version}`);
}

function isReady(storage, version) {
  return fs.existsSync(path.join(envDir(storage, version), READY));
}

/** The uv arguments that run a command of the bundled package, and the environment that goes with them. */
function bundledRun(bundle, storage, version, command, args) {
  return {
    args: ["run", "--frozen", "--no-dev", "--project", bundle, command, ...args],
    env: { UV_PROJECT_ENVIRONMENT: envDir(storage, version) },
  };
}

function download(url, dest, cancelled, redirects = 5) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { "User-Agent": "cardlang-vscode" } }, (res) => {
      if ([301, 302, 303, 307, 308].includes(res.statusCode) && res.headers.location && redirects > 0) {
        res.resume();
        resolve(download(new URL(res.headers.location, url).toString(), dest, cancelled, redirects - 1));
        return;
      }
      if (res.statusCode !== 200) { res.resume(); reject(new Error(`${url}: HTTP ${res.statusCode}`)); return; }
      const file = fs.createWriteStream(dest);
      res.pipe(file);
      file.on("finish", () => file.close(() => resolve()));
      file.on("error", reject);
      res.on("error", reject);
    });
    req.on("error", reject);
    const timer = setInterval(() => { if (cancelled()) { req.destroy(new Error("cancelled")); } }, 200);
    req.on("close", () => clearInterval(timer));
  });
}

function sha256(file) {
  return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
}

/** Run a program; resolve with its exit code, sending each line of its output to log. */
function run(command, args, options, log) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { ...options, env: { ...process.env, ...(options.env || {}) } });
    const lines = (data) => String(data).split(/\r?\n/).filter((l) => l.trim()).forEach((l) => log(l));
    child.stdout.on("data", lines);
    child.stderr.on("data", lines);
    child.on("error", reject);
    child.on("close", resolve);
  });
}

/** tar unpacks both uv's .tar.gz and, on Windows 10 and later, its .zip: Windows' own tar is bsdtar. */
function tar() {
  if (process.platform === "win32") {
    const own = path.join(process.env.SystemRoot || "C:\\Windows", "System32", "tar.exe");
    if (fs.existsSync(own)) return own;
  }
  return "tar";
}

function findFile(dir, name) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) { const found = findFile(p, name); if (found) return found; }
    else if (entry.name === name) return p;
  }
  return null;
}

/** Download, check and unpack the pinned uv; return its path. */
async function installUv(storage, pin, log, cancelled) {
  const target = ownUv(storage, pin);
  if (fs.existsSync(target)) return target;
  const entry = pinFor(pin);
  if (!entry) throw new Error(`uv publishes no build for ${process.platform}-${process.arch}; install uv yourself and set cardlang.uvPath`);
  const work = fs.mkdtempSync(path.join(storage, "download-"));
  try {
    const archive = path.join(work, path.basename(new URL(entry.url).pathname));
    log(`Downloading uv ${pin.version}: ${entry.url}`);
    await download(entry.url, archive, cancelled);
    const digest = sha256(archive);
    if (digest !== entry.sha256) throw new Error(`the download of ${entry.url} has SHA-256 ${digest}, not the pinned ${entry.sha256}`);
    log(`Checked its SHA-256: ${digest}`);
    const unpacked = path.join(work, "unpacked");
    fs.mkdirSync(unpacked);
    const code = await run(tar(), ["-xf", archive, "-C", unpacked], {}, log);
    if (code !== 0) throw new Error(`could not unpack ${archive} (tar exited with ${code})`);
    const found = findFile(unpacked, exe("uv"));
    if (!found) throw new Error(`${archive} holds no ${exe("uv")}`);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.copyFileSync(found, target);
    if (process.platform !== "win32") fs.chmodSync(target, 0o755);
    log(`Installed uv at ${target}`);
    return target;
  } finally {
    fs.rmSync(work, { recursive: true, force: true });
  }
}

/** The whole setup. uv: a uv to use, or null to install the pinned one. Returns the uv it used. */
async function setUp({ bundle, storage, version, pin, uv, log, cancelled = () => false }) {
  fs.mkdirSync(storage, { recursive: true });
  const env = envDir(storage, version);
  // Never build on a half-finished environment. Windows may hold a file of an exiting process a moment longer.
  fs.rmSync(env, { recursive: true, force: true, maxRetries: 10, retryDelay: 300 });
  const tool = uv || await installUv(storage, pin, log, cancelled);
  if (cancelled()) throw new Error("cancelled");
  log(`Installing the CardLang toolchain into ${env}`);
  const options = { cwd: bundle, env: { UV_PROJECT_ENVIRONMENT: env } };
  let code = await run(tool, ["sync", "--frozen", "--no-dev", "--project", bundle], options, log);
  if (code !== 0) throw new Error(`uv sync exited with ${code}`);
  const smoke = bundledRun(bundle, storage, version, "clc", ["--help"]);
  code = await run(tool, smoke.args, { cwd: bundle, env: smoke.env }, () => {});
  if (code !== 0) throw new Error(`the installed clc does not run (exit ${code})`);
  fs.writeFileSync(path.join(env, READY), `${new Date().toISOString()}\n`);
  for (const entry of fs.readdirSync(storage)) {                // environments of other versions of the extension
    if (entry.startsWith("env-") && path.join(storage, entry) !== env) {
      fs.rmSync(path.join(storage, entry), { recursive: true, force: true, maxRetries: 10, retryDelay: 300 });
    }
  }
  log("The CardLang toolchain is ready.");
  return tool;
}

module.exports = { pinFor, ownUv, envDir, isReady, bundledRun, setUp };

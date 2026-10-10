import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

function harness() {
  const timers = new Map();
  const listeners = new Set();
  const requests = [];
  let nextTimer = 0;
  const document = {
    hidden: false,
    addEventListener: (_, fn) => listeners.add(fn),
    removeEventListener: (_, fn) => listeners.delete(fn),
  };
  const context = vm.createContext({
    document, exports: {},
    setTimeout: (fn, ms) => { const id = ++nextTimer; timers.set(id, { fn, ms }); return id; },
    clearTimeout: id => timers.delete(id),
    require: () => ({ readResource: () => new Promise((resolve, reject) => requests.push({ resolve, reject })) }),
  });
  const source = readFileSync(new URL("../src/lib/poll-resource.ts", import.meta.url), "utf8");
  vm.runInContext(ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return {
    poll: context.exports.pollResource, requests, timers, listeners,
    visibility(hidden) { document.hidden = hidden; for (const fn of listeners) fn(); },
    tick() { for (const [id, { fn }] of [...timers]) { timers.delete(id); fn(); } },
  };
}
const settle = () => new Promise(resolve => setImmediate(resolve));

test("slow requests do not overlap and schedule only after completion", async () => {
  const h = harness();
  const received = [];
  const stop = h.poll("/progress", data => received.push(data));
  h.tick();
  h.visibility(false);
  assert.equal(h.requests.length, 1);
  assert.equal(h.timers.size, 0);
  h.requests[0].resolve({ notes: [] });
  await settle();
  assert.equal(received.length, 1);
  assert.equal([...h.timers.values()][0].ms, 15000);
  h.tick();
  assert.equal(h.requests.length, 2);
  stop();
});

test("hidden tabs pause and resume with a single fresh read", async () => {
  const h = harness();
  h.visibility(true);
  const stop = h.poll("/progress", () => {});
  assert.equal(h.requests.length, 0);
  h.visibility(false);
  assert.equal(h.requests.length, 1);
  h.visibility(true);
  h.requests[0].resolve({});
  await settle();
  assert.equal(h.timers.size, 0);
  h.visibility(false);
  assert.equal(h.requests.length, 2);
  stop();
});

test("unmount removes listeners and suppresses late results", async () => {
  const h = harness();
  let received = 0;
  const stop = h.poll("/progress", () => received++);
  stop();
  h.requests[0].resolve({});
  await settle();
  assert.equal(received, 0);
  assert.equal(h.timers.size, 0);
  assert.equal(h.listeners.size, 0);
});

test("errors notify the caller and retain bounded polling", async () => {
  const h = harness();
  let errors = 0;
  const stop = h.poll("/progress", () => {}, 30000, () => errors++);
  h.requests[0].reject(new Error("unavailable"));
  await settle();
  assert.equal(errors, 1);
  assert.equal([...h.timers.values()][0].ms, 30000);
  stop();
  assert.equal(h.timers.size, 0);
});

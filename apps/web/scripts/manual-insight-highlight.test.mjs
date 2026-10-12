import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

function harness(storage = new Map(), unavailable = false) {
  const context = vm.createContext({exports: {}, localStorage: {
    getItem(key) { if (unavailable) throw Error("denied"); return storage.get(key) ?? null; },
    setItem(key, value) { if (unavailable) throw Error("denied"); storage.set(key, value); },
  }});
  const source = readFileSync(new URL("../src/lib/manual-insight-highlight.ts", import.meta.url), "utf8");
  vm.runInContext(ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText, context);
  return context.exports;
}

test("manual highlights persist until actually acknowledged, across reloads", () => {
  const storage = new Map();
  const a = harness(storage);
  a.queueManualInsight("workspace", 42);
  a.queueManualInsight("workspace", 42);
  const b = harness(storage);
  assert.deepEqual([...b.pendingManualInsights("workspace")], [42]);
  assert.deepEqual([...b.pendingManualInsights("other")], []);
  b.acknowledgeManualInsight("workspace", 42);
  assert.deepEqual([...a.pendingManualInsights("workspace")], []);
});

test("invalid input is ignored; storage denial preserves in-memory queue", () => {
  const a = harness(new Map(), true);
  for (const id of [-1, 0, NaN, 1.2, "12"]) a.queueManualInsight("workspace", id);
  assert.deepEqual([...a.pendingManualInsights("workspace")], []);
  a.queueManualInsight("workspace", 12);
  assert.deepEqual([...a.pendingManualInsights("workspace")], [12]);
  a.acknowledgeManualInsight("workspace", 12);
  assert.deepEqual([...a.pendingManualInsights("workspace")], []);
});

test("pending queue is bounded without duplicating creations", () => {
  const a = harness();
  for (let id = 1; id <= 120; id++) a.queueManualInsight("workspace", id);
  assert.equal(a.pendingManualInsights("workspace").length, 100);
});

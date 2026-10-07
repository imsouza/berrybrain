import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../src/lib/judge-selection.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {} };
vm.runInNewContext(compiled, sandbox);
const { judgeSelectionIssues } = sandbox.exports;
const slots = () => ["glm-5", "kimi-k2.5", "minimax-m2.5"].map((model, i) => ({ slot: `judge-${i+1}`, provider: "opencode-zen", model }));

test("setup shows provider rejection instead of claiming chat is unsupported", () => {
  const setup = readFileSync(new URL("../src/components/required-ai-setup.tsx", import.meta.url), "utf8");
  const parsed = ts.createSourceFile("setup.tsx", setup, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const fn = parsed.statements.find((node) => ts.isFunctionDeclaration(node) && node.name?.text === "readError");
  assert.ok(fn);
  const context = {};
  vm.runInNewContext(ts.transpileModule(fn.getText(parsed), {}).outputText, context);
  for (const reason of ["Invalid API key", "max_tokens parameter rejected", "Rate limit reached"]) {
    const message = context.readError({ detail: { code: "model_capability_mismatch", failures: [{
      slot: "hipporag", model: "nemotron-3-ultra-free", capability: "chat", status: 400, reason,
    }] } });
    assert.match(message, /hipporag: nemotron-3-ultra-free/);
    assert.match(message, /HTTP 400/);
    assert.ok(message.includes(reason));
    assert.ok(!message.includes("does not provide"));
  }
});

test("distinct models on active provider are accepted", () => {
  assert.equal(judgeSelectionIssues(slots(), 3, "opencode-zen", "big-pickle").length, 0);
});
test("duplicates and generator exclusions ignore whitespace and case", () => {
  const selected = slots();
  selected[1].model = " GLM-5 ";
  selected[2].model = " BIG-PICKLE ";
  const issues = judgeSelectionIssues(selected, 3, "opencode-zen", "big-pickle").join(" ");
  assert.match(issues, /Judge 2:.*already selected/);
  assert.match(issues, /Judge 3: the generator/);
});
test("incomplete committee identifies the missing slot", () => {
  assert.match(judgeSelectionIssues(slots().slice(0, 2), 3, "opencode-zen", "main").join(" "), /Judge 3: choose/);
  assert.equal(judgeSelectionIssues(slots().slice(0, 2), 2, "opencode-zen", "main").length, 0);
});
test("stale provider and duplicate slot IDs fail before save", () => {
  const selected = slots();
  selected[1].provider = "old-provider";
  selected[2].slot = selected[0].slot;
  const issues = judgeSelectionIssues(selected, 3, "opencode-zen", "main").join(" ");
  assert.match(issues, /provider changed/);
  assert.match(issues, /duplicate slot/);
});
test("configuration save notifies Home and Settings to refresh", () => {
  for (const file of ["required-ai-setup.tsx", "settings-panel.tsx", "home/home-view.tsx"]) {
    const content = readFileSync(new URL(`../src/components/${file}`, import.meta.url), "utf8");
    assert.match(content, /bb:ai-configuration-changed/);
  }
});

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const source = readFileSync(new URL("../src/lib/pending-drafts.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const sandbox = { exports: {} };
vm.runInNewContext(compiled, sandbox);
const { draftKey, keepDraft, readDraft, acknowledgeDraft, forgetDraft } = sandbox.exports;

test("pending drafts survive remount lookup, but never cross session or note", () => {
  const key = draftKey("", "session-one", "a.md");
  keepDraft(key, { text: "pending", baseContent: "base", baseHash: "h1" });
  assert.equal(readDraft(key).text, "pending");
  assert.equal(readDraft(draftKey("", "session-two", "a.md")), undefined);
  assert.equal(readDraft(draftKey("", "session-one", "b.md")), undefined);
  assert.equal(draftKey("", "", "a.md"), null);
});
test("late saves retain newer edits with the new base version", () => {
  const key = draftKey("", "session", "late.md");
  keepDraft(key, { text: "newer draft", baseContent: "base", baseHash: "h1" });
  acknowledgeDraft(key, "older save", "h2");
  assert.equal(readDraft(key).text, "newer draft");
  assert.equal(readDraft(key).baseHash, "h2");
  acknowledgeDraft(key, "newer draft", "h3");
  assert.equal(readDraft(key), undefined);
});
test("discard and returning to base remove retained text", () => {
  const key = draftKey("", "session", "discard.md");
  keepDraft(key, { text: "pending", baseContent: "base", baseHash: "h1" });
  forgetDraft(key);
  assert.equal(readDraft(key), undefined);
  keepDraft(key, { text: "base", baseContent: "base", baseHash: "h1" });
  assert.equal(readDraft(key), undefined);
});

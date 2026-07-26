#!/usr/bin/env node
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const tracked = execFileSync("git", ["-C", root, "ls-files"], { encoding: "utf8" })
  .split(/\r?\n/)
  .filter(Boolean);

const failures = [];
const checks = {};

function pass(name, value) {
  checks[name] = value;
  if (!value) failures.push(name);
}

const trackedVault = tracked.filter((file) => file.startsWith("vault/") && file !== "vault/.gitkeep");
pass("no_personal_vault_content_tracked", trackedVault.length === 0);

const derivedIndexes = tracked.filter((file) =>
  /(^|\/)(\.?qdrant|\.?chroma|\.?berrybrain|hipporag\.db|.*\.(db|sqlite|sqlite3))$/i.test(file)
);
pass("no_derived_indexes_tracked", derivedIndexes.length === 0);

const secretPatterns = [
  /\bsk-[A-Za-z0-9_-]{20,}\b/g,
  /\bnvapi-[A-Za-z0-9_-]{20,}\b/g,
  /\bgh[pousr]_[A-Za-z0-9_]{20,}\b/g,
  /\bAIza[0-9A-Za-z_-]{20,}\b/g,
  /\bxox[baprs]-[0-9A-Za-z-]{20,}\b/g,
];
const secretHits = [];
for (const file of tracked) {
  if (/^apps\/web\/\.next\//.test(file)) continue;
  if (file === "apps/api/tests/test_security_redaction.py") continue;
  const full = path.join(root, file);
  if (!fs.existsSync(full) || fs.statSync(full).size > 1024 * 1024) continue;
  const text = fs.readFileSync(full, "utf8");
  for (const pattern of secretPatterns) {
    const matches = text.match(pattern);
    if (matches) secretHits.push({ file, count: matches.length });
  }
}
pass("no_hardcoded_secret_tokens", secretHits.length === 0);

const settingsStore = fs.readFileSync(path.join(root, "apps/api/src/berrybrain_api/settings_store.py"), "utf8");
const settingsRouter = fs.readFileSync(path.join(root, "apps/api/src/berrybrain_api/routers/settings.py"), "utf8");
pass("api_keys_encrypted_at_rest", settingsStore.includes("bbenc:v1:") && settingsStore.includes("ENCRYPTED_SETTING_KEYS"));
pass("api_keys_masked_in_settings_api", settingsRouter.includes("SECRET_KEYS") && settingsRouter.includes('data["value"] = ""'));

const backup = fs.readFileSync(path.join(root, "apps/api/src/berrybrain_api/backup.py"), "utf8");
pass("exports_redact_sensitive_settings", backup.includes("omittedSensitiveSettings") && backup.includes("_is_sensitive_setting"));

const graphRouter = fs.readFileSync(path.join(root, "apps/api/src/berrybrain_api/routers/graph.py"), "utf8");
pass("external_research_mode_opt_in", graphRouter.includes("research_mode_enabled") && graphRouter.includes('!= "true"'));

const compose = fs.readFileSync(path.join(root, "docker-compose.yml"), "utf8");
const hippoBlock = compose.match(/\n  hipporag:\n[\s\S]*?(?=\n[a-zA-Z0-9_-]+:|\nvolumes:|$)/)?.[0] || "";
pass("hipporag_sidecar_not_public", Boolean(hippoBlock) && !/\n\s+ports:\n/.test(hippoBlock));

const redaction = fs.existsSync(path.join(root, "apps/api/src/berrybrain_api/redaction.py"));
const redactionTest = fs.existsSync(path.join(root, "apps/api/tests/test_security_redaction.py"));
pass("redaction_has_code_and_tests", redaction && redactionTest);

const report = {
  status: failures.length === 0 ? "pass" : "fail",
  checks,
  failures,
  evidence: {
    trackedVault,
    derivedIndexes,
    secretHits,
  },
};
console.log(JSON.stringify(report, null, 2));
process.exit(failures.length === 0 ? 0 : 1);

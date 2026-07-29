#!/usr/bin/env node
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "../..");
const failures = [];
const checks = {};

function pass(name, value) {
  checks[name] = value;
  if (!value) failures.push(name);
}

function trackedFiles(prefix) {
  return execFileSync("git", ["-C", root, "ls-files", prefix], { encoding: "utf8" })
    .split(/\r?\n/)
    .filter(Boolean)
    .filter((file) => fs.existsSync(path.join(root, file)));
}

for (const layer of ["domain", "application", "infrastructure", "shared", "ui", "config"]) {
  pass(`package_${layer}_has_boundary_doc`, fs.existsSync(path.join(root, "packages", layer, "README.md")));
}

const layerRules = [
  { prefix: "packages/domain", forbidden: [/packages\/infrastructure/, /packages\/ui/, /packages\/application/] },
  { prefix: "packages/application", forbidden: [/packages\/ui/] },
  { prefix: "packages/shared", forbidden: [/packages\/domain/, /packages\/application/, /packages\/infrastructure/, /packages\/ui/] },
];
for (const rule of layerRules) {
  const offenders = [];
  for (const file of trackedFiles(rule.prefix)) {
    if (!/\.(ts|tsx|py|md)$/.test(file)) continue;
    const text = fs.readFileSync(path.join(root, file), "utf8");
    if (rule.forbidden.some((pattern) => pattern.test(text))) offenders.push(file);
  }
  pass(`${rule.prefix.replace("/", "_")}_dependency_direction`, offenders.length === 0);
}

const sourceFiles = trackedFiles("apps")
  .filter((file) => /\/src\/.*\.(py|ts|tsx)$/.test(file))
  .filter((file) => !file.includes("/tests/"));
const hardcodedAbsolute = sourceFiles.filter((file) => {
  const text = fs.readFileSync(path.join(root, file), "utf8");
  return /\/mnt\/HDD_1|\/home\/mtz/.test(text);
});
pass("app_source_has_no_machine_absolute_paths", hardcodedAbsolute.length === 0);

pass(
  "graph_contract_module_exists",
  fs.existsSync(path.join(root, "apps/api/src/berrybrain_api/graph_contracts.py"))
);

const workerMain = fs.readFileSync(path.join(root, "apps/worker/src/berrybrain_worker/main.py"), "utf8");
pass("worker_uses_job_handler_registry", workerMain.includes("JobHandler = Callable") && workerMain.includes("job_handlers()"));

const report = {
  status: failures.length === 0 ? "pass" : "fail",
  checks,
  failures,
  evidence: { hardcodedAbsolute },
};
console.log(JSON.stringify(report, null, 2));
process.exit(failures.length === 0 ? 0 : 1);

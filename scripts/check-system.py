"""Run product checks in separate processes with temporary storage and no network.

Research/benchmark suites are deliberately excluded. No production settings, DB,
vault, provider requests, or historical research evidence are used or updated.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = re.compile(
    r"benchmark|evaluation|maturity|calibration|dataset|paired_statistics|claim_support|"
    r"comparative|compare_generation|generation_profile|official|rerank_policy|confirmatory|"
    r"external_ranking|coverage_regression|documentation_consistency|analysis_report"
)
BOOTSTRAP = r"""
import os, pathlib, socket, sys
root, test_file, sandbox = map(pathlib.Path, sys.argv[1:4])
os.environ.update({
    'BERRYBRAIN_PROJECT_ROOT': str(sandbox),
    'BERRYBRAIN_ENVIRONMENT': 'test',
    'BERRYBRAIN_DATABASE_URL': 'sqlite:///' + str(sandbox / 'test.db'),
    'BERRYBRAIN_VAULT_PATH': str(sandbox / 'vault'),
    'BERRYBRAIN_JOBS_PATH': str(sandbox / 'jobs'),
    'BERRYBRAIN_LOG_PATH': str(sandbox / 'logs'),
    'BERRYBRAIN_BACKUP_PATH': str(sandbox / 'backups'),
    'BERRYBRAIN_SESSION_SECRET': 'product-only-isolated-test-secret-32-bytes',
    'BERRYBRAIN_API_TOKEN': 'product-only-test-token',
    'BERRYBRAIN_VAULT_WATCHER_ENABLED': 'false',
    'BERRYBRAIN_ENABLE_DEFAULT_OWNER': 'false',
    'PYTHONDONTWRITEBYTECODE': '1',
    'HIPPORAG_DATA_DIR': str(sandbox / 'hipporag'),
    'HIPPORAG_LLM_URL': '',
    'HIPPORAG_SERVICE_TOKEN': '',
})
# Prompts/static assets remain available; no .env is copied or read.
for directory in ('prompts', 'docs'):
    (sandbox / directory).symlink_to(root / directory, target_is_directory=True)
original_connect = socket.socket.connect
def blocked_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        raise RuntimeError('Network disabled in isolated product checks')
    return original_connect(self, address)
socket.socket.connect = blocked_connect
sys.path[:0] = [str(root / 'apps' / 'api' / 'src'), str(root / 'apps' / 'worker' / 'src'), str(root / 'apps' / 'api'), str(test_file.parent)]
if test_file.parent.parent.name == 'hipporag':
    sys.path.insert(0, str(test_file.parent.parent))
import pytest
class Results:
    def __init__(self):
        self.result = dict(tests=0, failures=0, errors=0, skipped=0)
    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.result['tests'] += 1
            self.result['failures'] += int(report.failed)
        elif report.failed:
            self.result['errors'] += 1
        if report.skipped:
            self.result['skipped'] += 1
    def pytest_collectreport(self, report):
        self.result['errors'] += int(report.failed)
results = Results()
status = pytest.main([str(test_file), '-q', '--tb=short', '-p', 'no:cacheprovider'], plugins=[results])
print('PRODUCT_RESULT ' + __import__('json').dumps(results.result))
sys.exit(int(status))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        choices=["api", "worker", "hipporag", "regressions", "all"],
        default="all",
    )
    parser.add_argument("--only", default="", help="Comma-separated filename fragments")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument(
        "--report", type=Path, help="Optional machine-readable product-check report"
    )
    args = parser.parse_args()
    selected = []
    for group, directory in [
        ("api", "apps/api/tests"),
        ("worker", "apps/worker/tests"),
        ("regressions", "apps/api/regression_tests"),
        ("hipporag", "apps/hipporag/tests"),
    ]:
        if args.suite not in {"all", group}:
            continue
        for path in sorted((ROOT / directory).glob("test_*.py")):
            if RESEARCH.search(path.name) or "from benchmarks" in path.read_text():
                continue
            if args.only and not any(
                part in path.name for part in args.only.split(",")
            ):
                continue
            selected.append(path)
    results = []
    for path in selected:
        with tempfile.TemporaryDirectory(
            prefix="berrybrain-system-check-"
        ) as temporary:
            environment = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith(("BERRYBRAIN_", "SMTP_"))
            }
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            try:
                run = subprocess.run(
                    [sys.executable, "-c", BOOTSTRAP, str(ROOT), str(path), temporary],
                    cwd=ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                    check=False,
                )
                marker = next(
                    (
                        line.removeprefix("PRODUCT_RESULT ")
                        for line in run.stdout.splitlines()
                        if line.startswith("PRODUCT_RESULT ")
                    ),
                    "{}",
                )
                item = {
                    "file": str(path.relative_to(ROOT)),
                    "exit": run.returncode,
                    **json.loads(marker),
                }
                if run.returncode:
                    item["diagnostic"] = (run.stdout + run.stderr)[-6500:]
            except subprocess.TimeoutExpired:
                item = {"file": str(path.relative_to(ROOT)), "exit": "timeout"}
            results.append(item)
            print(json.dumps(item, ensure_ascii=False), flush=True)
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(
                    json.dumps(results, indent=2, ensure_ascii=False) + "\n"
                )
    print(
        json.dumps(
            {
                "modules": len(results),
                "tests": sum(x.get("tests", 0) for x in results),
                "failedModules": sum(x["exit"] != 0 for x in results),
                "skipped": sum(x.get("skipped", 0) for x in results),
            }
        ),
        flush=True,
    )
    return 1 if not results or any(x["exit"] != 0 for x in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())

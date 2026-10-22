#!/usr/bin/env python3
"""Reject release images whose published version differs from their code."""

from __future__ import annotations

import argparse
import ast
import json
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def source_version(package: str) -> str:
    source = (ROOT / "apps" / package / "src" / f"berrybrain_{package}" / "__init__.py").read_text(
        encoding="utf-8"
    )
    for statement in ast.parse(source).body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            if isinstance(value, str):
                return value
    raise ValueError(f"Missing literal __version__ in {package} source")


def versions() -> dict[str, str]:
    result: dict[str, str] = {}
    for package in ("api", "worker"):
        project = tomllib.loads(
            (ROOT / "apps" / package / "pyproject.toml").read_text(encoding="utf-8")
        )
        result[f"{package} package"] = project["project"]["version"]
        result[f"{package} source"] = source_version(package)
    web = ROOT / "apps" / "web"
    manifest = json.loads((web / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((web / "package-lock.json").read_text(encoding="utf-8"))
    result["web package"] = manifest["version"]
    result["web lock"] = lock["version"]
    result["web lock root"] = lock["packages"][""]["version"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", help="Expected release tag, e.g. v1.5.0")
    args = parser.parse_args()
    found = versions()
    expected = args.expected.removeprefix("v") if args.expected else found["api package"]
    mismatches = {name: value for name, value in found.items() if value != expected}
    if mismatches:
        print(f"Version mismatch; expected {expected}: {mismatches}")
        return 1
    print(f"Version sync OK: {expected} ({len(found)} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

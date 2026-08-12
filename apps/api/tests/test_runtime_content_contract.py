import re
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class RuntimeContentContractTest(unittest.TestCase):
    def test_runtime_contains_no_seeded_demo_or_mock_payloads(self) -> None:
        source_roots = (
            REPOSITORY_ROOT / "apps/api/src",
            REPOSITORY_ROOT / "apps/worker/src",
            REPOSITORY_ROOT / "apps/web/src",
        )
        forbidden = (
            re.compile(r"\b(?:DEMO|MOCK|FAKE)_[A-Z0-9_]+\s*(?::[^=\n]+)?="),
            re.compile(r'["\']local-demo["\']'),
            re.compile(r'["\']demo/[^"\']+\.md["\']'),
        )
        violations: list[str] = []
        for root in source_roots:
            for path in root.rglob("*"):
                if path.suffix not in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                    continue
                text = path.read_text(encoding="utf-8")
                if any(pattern.search(text) for pattern in forbidden):
                    violations.append(str(path.relative_to(REPOSITORY_ROOT)))
        self.assertEqual(violations, [])

    def test_generation_gate_requires_english_and_preserves_user_quotes(self) -> None:
        for relative_path in (
            "apps/api/src/berrybrain_api/ai_gateway.py",
            "apps/worker/src/berrybrain_worker/main.py",
        ):
            text = (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("system-generated label", text)
            self.assertIn("in English", text)
            self.assertIn("verbatim user excerpts", text)

    def test_unspecified_source_language_is_not_invented(self) -> None:
        model_source = (
            REPOSITORY_ROOT / "apps/api/src/berrybrain_api/models.py"
        ).read_text(encoding="utf-8")
        self.assertIn('default="und"', model_source)

    def test_web_exposes_only_the_english_system_locale(self) -> None:
        source = (REPOSITORY_ROOT / "apps/web/src/i18n.ts").read_text(encoding="utf-8")
        self.assertIn('export type LangKind = "en";', source)
        self.assertEqual(source.count('export type LangKind = "en";'), 1)


if __name__ == "__main__":
    unittest.main()

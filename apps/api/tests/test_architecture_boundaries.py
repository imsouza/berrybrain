import ast
import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
API_SOURCE = REPOSITORY_ROOT / "apps" / "api" / "src" / "berrybrain_api"

DOMAIN_FORBIDDEN_PREFIXES = (
    "fastapi",
    "sqlalchemy",
    "httpx",
    "requests",
    "pathlib",
    "subprocess",
    "berrybrain_api.database",
    "berrybrain_api.models",
    "berrybrain_api.routers",
)
APPLICATION_FORBIDDEN_PREFIXES = (
    "fastapi",
    "berrybrain_api.routers",
    "berrybrain_api.database",
)


def _python_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


class ArchitectureBoundaryTest(unittest.TestCase):
    def test_graph_inference_projects_only_through_durable_job_outbox(self) -> None:
        service = (API_SOURCE / "graph_inference_service.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("create_job(", service)
        self.assertIn('"graphUpdate": "queued"', service)
        self.assertNotIn("expand_knowledge_graph", service)

    def test_python_domain_modules_are_framework_free(self) -> None:
        domain_files = sorted(API_SOURCE.glob("modules/**/domain.py"))
        self.assertTrue(domain_files, "At least one domain module must be present")
        violations = []
        for path in domain_files:
            for imported in _python_imports(path):
                if imported.startswith(DOMAIN_FORBIDDEN_PREFIXES):
                    violations.append(
                        f"{path.relative_to(REPOSITORY_ROOT)} -> {imported}"
                    )
        self.assertEqual(violations, [])

    def test_python_application_modules_do_not_depend_on_delivery_or_database(
        self,
    ) -> None:
        application_files = sorted(API_SOURCE.glob("modules/**/application.py"))
        violations = []
        for path in application_files:
            for imported in _python_imports(path):
                if imported.startswith(APPLICATION_FORBIDDEN_PREFIXES):
                    violations.append(
                        f"{path.relative_to(REPOSITORY_ROOT)} -> {imported}"
                    )
        self.assertEqual(violations, [])

    def test_typescript_domain_package_has_no_ui_or_infrastructure_imports(
        self,
    ) -> None:
        domain_root = REPOSITORY_ROOT / "packages" / "domain"
        forbidden = re.compile(
            r"from\s+['\"](?:react|next|@berrybrain/(?:ui|infrastructure))"
        )
        violations = []
        for path in sorted(domain_root.rglob("*.ts")):
            if forbidden.search(path.read_text(encoding="utf-8")):
                violations.append(str(path.relative_to(REPOSITORY_ROOT)))
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

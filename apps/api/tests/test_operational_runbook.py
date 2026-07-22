from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
COMPOSE = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
RUNBOOK = (ROOT / "OPERATIONS.md").read_text(encoding="utf-8")


class OperationalRunbookTest(unittest.TestCase):
    def test_required_services_start_without_an_optional_profile(self) -> None:
        required_section = COMPOSE.split("  searxng:", maxsplit=1)[0]

        for service in ("api", "web", "worker"):
            self.assertIn(f"  {service}:", required_section)
        self.assertNotIn("profiles:", required_section)
        self.assertIn("http://127.0.0.1:8000/health", required_section)
        self.assertIn("/api/v1/worker/status", required_section)

    def test_runbook_covers_release_and_recovery_contract(self) -> None:
        required_fragments = (
            "docker compose config --quiet",
            "create_backup",
            "list_backups",
            "git checkout <reviewed-tag-or-commit>",
            "docker compose up -d api",
            "docker compose up -d worker web",
            "docker compose ps api web worker",
            "restore_backup('BACKUP_ID')",
            "docker compose stop web worker api",
            "python -m benchmarks.maturity_release_gate",
            "2,500 ms",
            "5,000 nodes and 20,000 edges",
            "500 ms",
            "worker heartbeat",
        )

        for fragment in required_fragments:
            self.assertIn(fragment, RUNBOOK)


if __name__ == "__main__":
    unittest.main()

import unittest

from berrybrain_api.routers import hipporag


class HippoRagSecurityTest(unittest.TestCase):
    def test_sync_does_not_return_exception_details(self) -> None:
        result = hipporag._sync_failure("Research/private-note.md")

        self.assertEqual(
            result,
            {
                "path": "Research/private-note.md",
                "code": "sidecar_request_failed",
            },
        )


if __name__ == "__main__":
    unittest.main()

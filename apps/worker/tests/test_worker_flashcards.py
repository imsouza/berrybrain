import unittest

from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.main import process_job


class WorkerFlashcardsTest(unittest.IsolatedAsyncioTestCase):
    async def test_generate_flashcards_job_is_unsupported(self) -> None:
        job = {
            "id": 1,
            "type": "GENERATE_FLASHCARDS",
            "payload": {"note_path": "inbox/a.md"},
        }

        with self.assertRaisesRegex(ValueError, "Unsupported"):
            await process_job(None, WorkerSettings(), job)


if __name__ == "__main__":
    unittest.main()

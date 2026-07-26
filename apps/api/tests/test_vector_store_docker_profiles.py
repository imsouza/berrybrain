import unittest
from pathlib import Path


class VectorStoreDockerProfilesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compose = (
            Path(__file__).resolve().parents[3] / "docker-compose.yml"
        ).read_text(encoding="utf-8")

    def test_qdrant_profile_is_declared(self) -> None:
        self.assertIn("  qdrant:", self.compose)
        self.assertIn("qdrant/qdrant:latest", self.compose)
        self.assertIn("vector-qdrant", self.compose)
        self.assertIn("qdrant_data:/qdrant/storage", self.compose)
        self.assertIn("${BERRYBRAIN_QDRANT_PORT:-6333}:6333", self.compose)

    def test_chroma_profile_is_declared(self) -> None:
        self.assertIn("  chroma:", self.compose)
        self.assertIn("chromadb/chroma:latest", self.compose)
        self.assertIn("vector-chroma", self.compose)
        self.assertIn("chroma_data:/chroma/chroma", self.compose)
        self.assertIn("${BERRYBRAIN_CHROMA_PORT:-8001}:8000", self.compose)


if __name__ == "__main__":
    unittest.main()

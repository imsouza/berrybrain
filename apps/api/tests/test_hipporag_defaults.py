import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.cognitive_layer import cognitive_config as layer_config
from berrybrain_api.cognitive_state import cognitive_config as state_config
from berrybrain_api.database import Base
from berrybrain_api.models import SettingRecord


class HippoRagDefaultsTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_hipporag_is_enabled_by_default(self) -> None:
        self.assertEqual(state_config(self.session)["hipporag_enabled"], "true")
        self.assertEqual(layer_config(self.session)["hipporag_enabled"], "true")

    def test_hipporag_can_be_explicitly_enabled(self) -> None:
        self.session.add(SettingRecord(key="hipporag_enabled", value="true"))
        self.session.commit()

        self.assertEqual(state_config(self.session)["hipporag_enabled"], "true")
        self.assertEqual(layer_config(self.session)["hipporag_enabled"], "true")


if __name__ == "__main__":
    unittest.main()

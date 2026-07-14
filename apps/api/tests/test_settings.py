import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.config import _discover_project_root
from berrybrain_api.settings_store import (
    get_setting,
    list_settings,
    serialize_setting,
    set_setting,
)


class SettingsStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_set_setting_creates_and_updates_value(self) -> None:
        created = set_setting(self.session, "automation.mode", "autopilot")
        updated = set_setting(self.session, "automation.mode", "manual")

        self.assertEqual(created.id, updated.id)
        self.assertEqual(updated.value, "manual")
        self.assertEqual(get_setting(self.session, "automation.mode").value, "manual")

    def test_list_settings_orders_by_key_and_serializes(self) -> None:
        set_setting(self.session, "ui.theme", "light")
        setting = set_setting(self.session, "automation.mode", "autopilot")

        settings = list_settings(self.session)
        serialized = serialize_setting(setting)

        self.assertEqual(
            [item.key for item in settings], ["automation.mode", "ui.theme"]
        )
        self.assertEqual(serialized["key"], "automation.mode")
        self.assertEqual(serialized["value"], "autopilot")

    def test_project_root_can_be_explicit_in_packaged_runtime(self) -> None:
        with (
            tempfile.TemporaryDirectory() as tmp,
            patch.dict(os.environ, {"BERRYBRAIN_PROJECT_ROOT": tmp}),
        ):
            self.assertEqual(_discover_project_root(), Path(tmp).resolve())


if __name__ == "__main__":
    unittest.main()

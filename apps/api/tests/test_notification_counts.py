import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import NotificationRecord
from berrybrain_api.routers.notifications import (
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    notification_summary,
)


class NotificationCountsTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as session:
            session.add_all(
                [
                    NotificationRecord(
                        type="job_failed",
                        title=f"Job {i}",
                        description="Failed",
                        action="Monitor",
                        read_at=None if i < 7 else datetime.now(UTC),
                    )
                    for i in range(9)
                ]
            )
            session.commit()
        self.mock = patch(
            "berrybrain_api.routers.notifications.SessionLocal", self.sessions
        )
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.engine.dispose()

    def test_count_is_not_limited_by_page_or_notification_category(self):
        result = list_notifications(limit=2)
        self.assertEqual(len(result["notifications"]), 2)
        self.assertEqual(result["unreadCount"], 7)
        self.assertEqual(notification_summary(), {"unreadCount": 7})

    def test_read_updates_count_and_keeps_history(self):
        mark_notification_read(1)
        self.assertEqual(notification_summary()["unreadCount"], 6)
        self.assertEqual(mark_all_notifications_read()["count"], 6)
        self.assertEqual(notification_summary()["unreadCount"], 0)
        self.assertEqual(len(list_notifications(limit=20)["notifications"]), 9)


if __name__ == "__main__":
    unittest.main()

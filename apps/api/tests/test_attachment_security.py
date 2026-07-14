import unittest

from berrybrain_api.attachment_security import (
    attachment_category,
    attachment_checksum,
    detect_mime_type,
    validate_attachment_filename,
)


class AttachmentSecurityTest(unittest.TestCase):
    def test_detects_content_signatures_instead_of_filename(self) -> None:
        self.assertEqual(detect_mime_type(b"%PDF-1.7\nfixture"), "application/pdf")
        self.assertEqual(detect_mime_type(b"\x89PNG\r\n\x1a\nfixture"), "image/png")
        self.assertEqual(detect_mime_type(b"plain UTF-8 text"), "text/plain")
        self.assertEqual(attachment_category("image/png"), "image")

    def test_filename_rejects_path_traversal(self) -> None:
        for invalid in ("../secret.txt", "folder/file.txt", "folder\\file.txt", ".."):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_attachment_filename(invalid)
        self.assertEqual(
            validate_attachment_filename("safe report.txt"), "safe report.txt"
        )

    def test_checksum_is_stable_and_content_sensitive(self) -> None:
        self.assertEqual(attachment_checksum(b"same"), attachment_checksum(b"same"))
        self.assertNotEqual(attachment_checksum(b"same"), attachment_checksum(b"other"))


if __name__ == "__main__":
    unittest.main()

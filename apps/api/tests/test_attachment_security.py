import unittest
import io
import zipfile

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
        for invalid in (
            "../secret.txt",
            "folder/file.txt",
            "folder\\file.txt",
            "..",
            ".",
            "",
            "\x00.txt",
            "...",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_attachment_filename(invalid)
        self.assertEqual(
            validate_attachment_filename("safe report.txt"), "safe report.txt"
        )
        self.assertEqual(validate_attachment_filename("safe@name.txt"), "safe-name.txt")
        self.assertEqual(len(validate_attachment_filename("a" * 220 + ".txt")), 180)

    def test_detects_supported_media_and_office_signatures(self) -> None:
        signatures = {
            b"\xff\xd8\xffpayload": "image/jpeg",
            b"GIF87apayload": "image/gif",
            b"GIF89apayload": "image/gif",
            b"RIFFxxxxWEBPpayload": "image/webp",
            b"RIFFxxxxWAVEpayload": "audio/wav",
            b"OggSpayload": "audio/ogg",
            b"fLaCpayload": "audio/flac",
            b"ID3payload": "audio/mpeg",
            b"\xff\xe3payload": "audio/mpeg",
            b"xxxxftypM4A payload": "audio/mp4",
            b"xxxxftypisompayload": "video/mp4",
        }
        for content, expected in signatures.items():
            with self.subTest(expected=expected):
                self.assertEqual(detect_mime_type(content), expected)

        office = io.BytesIO()
        with zipfile.ZipFile(office, "w") as archive:
            archive.writestr("word/document.xml", "<document />")
        self.assertEqual(
            detect_mime_type(office.getvalue()),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        archive_data = io.BytesIO()
        with zipfile.ZipFile(archive_data, "w") as archive:
            archive.writestr("notes/readme.txt", "knowledge")
        self.assertEqual(detect_mime_type(archive_data.getvalue()), "application/zip")
        self.assertEqual(
            detect_mime_type(b"PK\x03\x04broken"), "application/octet-stream"
        )

    def test_unknown_binary_and_categories_fail_closed(self) -> None:
        self.assertEqual(detect_mime_type(b""), "application/octet-stream")
        self.assertEqual(
            detect_mime_type(b"binary\x00payload"), "application/octet-stream"
        )
        self.assertEqual(attachment_category("audio/mpeg"), "audio")
        self.assertEqual(attachment_category("video/mp4"), "video")
        self.assertEqual(attachment_category("text/plain"), "other")
        self.assertEqual(attachment_category("application/pdf"), "other")

    def test_checksum_is_stable_and_content_sensitive(self) -> None:
        self.assertEqual(attachment_checksum(b"same"), attachment_checksum(b"same"))
        self.assertNotEqual(attachment_checksum(b"same"), attachment_checksum(b"other"))


if __name__ == "__main__":
    unittest.main()

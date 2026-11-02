import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock
from urllib.error import HTTPError
from urllib.request import Request

path = Path(__file__).resolve().parents[3] / "examples" / "berrybrain_client.py"
spec = importlib.util.spec_from_file_location("berrybrain_example", path)
client_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client_module)


class ExternalClientTest(unittest.TestCase):
    def setUp(self):
        self.client = client_module.BerryBrainClient(
            "https://example.test/berrybrain", "private-fixture"
        )
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"ok": True}
        ).encode()
        self.client.opener = MagicMock()
        self.client.opener.open.return_value = response

    def test_mount_encoded_note_path_and_authorization(self):
        self.client.read_note("inbox/study #one.md")
        request = self.client.opener.open.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://example.test/berrybrain/api/v1/notes/inbox/study%20%23one.md",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer private-fixture")

    def test_update_sends_hash_and_conflict_is_not_retried(self):
        self.client.opener.open.side_effect = HTTPError(
            "https://example.test",
            409,
            "Conflict",
            {"X-Correlation-ID": "review-fixture"},
            io.BytesIO(b'{"detail":"changed"}'),
        )
        with self.assertRaises(client_module.APIError) as raised:
            self.client.update_note("inbox/note.md", "new", "old-hash")
        self.assertEqual(raised.exception.status, 409)
        self.assertEqual(raised.exception.correlation_id, "review-fixture")
        self.assertEqual(self.client.opener.open.call_count, 1)
        request = self.client.opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data)["base_content_hash"], "old-hash")

    def test_redirect_does_not_forward_workspace_credentials(self):
        request = Request(
            "https://example.test", headers={"Authorization": "Bearer private-fixture"}
        )
        handler = client_module.NoRedirects()
        self.assertIsNone(
            handler.redirect_request(
                request, None, 302, "Redirect", {}, "https://other.test"
            )
        )

    def test_rejects_credential_urls_and_parent_endpoints(self):
        for url in (
            "file:///tmp/notes",
            "https://user:pass@example.test",
            "https://example.test?token=x",
        ):
            with self.assertRaises(ValueError):
                client_module.BerryBrainClient(url, "token")
        with self.assertRaises(ValueError):
            self.client.request("GET", "/../admin")

    def test_v15_vaults_skills_graph_and_ontology_helpers(self):
        self.client.list_vaults()
        req = self.client.opener.open.call_args.args[0]
        self.assertEqual(
            req.full_url, "https://example.test/berrybrain/api/v1/vault/namespaces"
        )

        self.client.list_notes(limit=10, offset=5, vault_id="research")
        req = self.client.opener.open.call_args.args[0]
        self.assertEqual(
            req.full_url,
            "https://example.test/berrybrain/api/v1/notes?limit=10&offset=5&vault_id=research",
        )

        self.client.match_skills("systematic review", task_type="ask")
        req = self.client.opener.open.call_args.args[0]
        self.assertEqual(
            req.full_url,
            "https://example.test/berrybrain/api/v1/ai/skills?query=systematic+review&task_type=ask",
        )

        self.client.graph_nodes(limit=100, cursor="n-10")
        req = self.client.opener.open.call_args.args[0]
        self.assertEqual(
            req.full_url,
            "https://example.test/berrybrain/api/v1/graph/nodes?limit=100&cursor=n-10&includeProvisional=false",
        )

        turtle_response = MagicMock()
        turtle_response.__enter__.return_value.read.return_value = (
            b"@prefix skos: <http://www.w3.org/2004/02/skos/core#> ."
        )
        turtle_response.__enter__.return_value.headers = {"Content-Type": "text/turtle"}
        self.client.opener.open.return_value = turtle_response
        exported = self.client.export_ontology(output_format="turtle")
        self.assertIn("@prefix skos:", exported)

        with self.assertRaises(ValueError):
            self.client.export_ontology(output_format="xml")
        with self.assertRaises(ValueError):
            self.client.inference_feedback(42, "invalid-action")

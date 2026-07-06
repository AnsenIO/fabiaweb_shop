"""fabiaweb_shop Flask backend tests.

Run with:
    python test.py

Requires Flask (already in requirements.txt).
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Make server.py importable from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import app, SERVABLE


class FabiaWebShopTests(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

        # Redirect orders.csv to a temp file so tests don't pollute real data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.orders_csv = Path(self.temp_dir.name) / "orders.csv"

    def tearDown(self):
        self.temp_dir.cleanup()

    def _patch_csv(self):
        return patch("server.ORDERS_CSV", self.orders_csv)

    # ── Static file serving ─────────────────────────────────────────────────

    def test_index_serves_html(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FABIABox Shop", response.data)

    def test_og_image_is_servable(self):
        self.assertIn("og-fabiashop.png", SERVABLE)
        response = self.client.get("/og-fabiashop.png")
        # 200 if file exists, 404 if missing in this checkout — both acceptable
        self.assertIn(response.status_code, (200, 404))

    def test_csv_is_not_servable(self):
        self.assertNotIn("orders.csv", SERVABLE)
        response = self.client.get("/orders.csv")
        self.assertEqual(response.status_code, 404)

    def test_env_file_is_not_servable(self):
        response = self.client.get("/.env")
        self.assertEqual(response.status_code, 404)

    def test_server_py_is_not_servable(self):
        response = self.client.get("/server.py")
        self.assertEqual(response.status_code, 404)

    # ── Health ──────────────────────────────────────────────────────────────

    def test_health_ok(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "ok"})

    # ── Order submission ────────────────────────────────────────────────────

    def _valid_payload(self, **overrides):
        payload = {
            "name": "Ada",
            "email": "ada@example.com",
            "company": "IABAI",
            "country": "France",
            "sku": "FABIABox Edge",
            "quantity": "1",
            "action": "pre-buy",
            "message": "",
            "consent": True,
        }
        payload.update(overrides)
        return payload

    def test_submit_without_consent_fails(self):
        response = self.client.post(
            "/submit",
            json=self._valid_payload(consent=False),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_submit_missing_name_fails(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(name=""),
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_submit_invalid_email_fails(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(email="not-an-email"),
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_submit_missing_country_fails(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(country=""),
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_submit_invalid_action_fails(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(action="hacker"),
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_submit_json_success(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(),
            )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])
        self.assertTrue(self.orders_csv.exists())

        rows = self.orders_csv.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(rows), 2)  # header + 1 order
        self.assertIn("ada@example.com", rows[1])
        self.assertIn("pending", rows[1])

    def test_submit_form_encoded_success(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                data=self._valid_payload(consent="on"),
            )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])
        self.assertTrue(self.orders_csv.exists())

    def test_submit_case_insensitive_consent(self):
        with self._patch_csv():
            response = self.client.post(
                "/submit",
                json=self._valid_payload(consent="YES"),
            )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

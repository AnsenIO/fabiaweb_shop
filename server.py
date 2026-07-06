"""FABIABox Shop web server — Flask, loopback-only, nginx reverse proxy."""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=None)

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
CONTACTS_CSV = DATA_DIR / "contacts.csv"


def _ensure_csv():
    """Create contacts.csv with headers if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    if not CONTACTS_CSV.exists():
        with CONTACTS_CSV.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow(["timestamp", "ip", "name", "email", "company", "product", "message", "source"])


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/")
def index():
    return send_from_directory(str(BASE), "index.html")


@app.route("/submit", methods=["POST"])
def submit_lead():
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    company = (data.get("company") or "").strip()
    product = (data.get("product") or "").strip()
    message = (data.get("message") or "").strip()
    source = (data.get("source") or "product_shop").strip()
    consent = data.get("consent")
    # Accept boolean True or checkbox "on" from form-encoded fallback
    consent_ok = consent is True or (isinstance(consent, str) and consent.lower() in ("on", "true", "yes", "1"))

    if not name or "@" not in email:
        return jsonify(success=False, error="Name and valid email required"), 400

    if not consent_ok:
        return jsonify(success=False, error="Consent required"), 400

    _ensure_csv()
    with CONTACTS_CSV.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([
            datetime.now(timezone.utc).isoformat(),
            _client_ip(),
            name,
            email,
            company,
            product,
            message,
            source,
        ])

    print(f"[LEAD] {name} <{email}> from {source} - product: {product} - {_client_ip()}")
    return jsonify(success=True), 201


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    _ensure_csv()
    port = int(os.environ.get("PORT", "8081"))
    # Bind to loopback only — nginx handles external traffic
    app.run(host="127.0.0.1", port=port, debug=False)

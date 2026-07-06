"""fabiaweb_shop web server — Flask, loopback-only, nginx reverse proxy."""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=None)

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
ORDERS_CSV = DATA_DIR / "orders.csv"

# Files nginx should serve directly from the app
SERVABLE = {
    "index.html",
    "og-fabiashop.png",
}

VALID_SKUS = {
    "FABIABox Entry",
    "FABIABox Edge",
    "FABIABox Pro",
    "FABIABox Enterprise",
    "Agentic Build Plan",
    "Agentic Operate Plan",
}

VALID_ACTIONS = {"pre-buy", "waiting-list"}


def _ensure_csv():
    """Create orders.csv with headers if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    if not ORDERS_CSV.exists():
        with ORDERS_CSV.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([
                "timestamp", "name", "email", "company", "country",
                "sku", "quantity", "action", "message", "status",
            ])


@app.route("/")
def index():
    return send_from_directory(str(BASE), "index.html")


@app.route("/<path:filename>")
def static_file(filename):
    """Only serve explicitly allowed files — nothing else leaks."""
    if filename not in SERVABLE:
        return jsonify(error="not found"), 404
    return send_from_directory(str(BASE), filename)


@app.route("/submit", methods=["POST"])
def submit_order():
    data = request.get_json(silent=True) or request.form.to_dict() or {}

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    company = (data.get("company") or "").strip()
    country = (data.get("country") or "").strip()
    sku = (data.get("sku") or "").strip()
    quantity = (data.get("quantity") or "1").strip()
    action = (data.get("action") or "").strip().lower()
    message = (data.get("message") or "").strip()
    consent = data.get("consent")
    consent_ok = consent is True or (isinstance(consent, str) and consent.lower() in ("on", "true", "yes", "1"))

    if not name or "@" not in email:
        return jsonify(success=False, error="Name and valid email required"), 400

    if not country:
        return jsonify(success=False, error="Country required"), 400

    if not consent_ok:
        return jsonify(success=False, error="Consent required"), 400

    if sku not in VALID_SKUS:
        return jsonify(success=False, error="Invalid product"), 400

    if action not in VALID_ACTIONS:
        return jsonify(success=False, error="Invalid action"), 400

    try:
        quantity_int = int(quantity)
        if quantity_int < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify(success=False, error="Quantity must be a positive integer"), 400

    _ensure_csv()
    with ORDERS_CSV.open("a", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerow([
            datetime.now(timezone.utc).isoformat(),
            name,
            email,
            company,
            country,
            sku,
            quantity_int,
            action,
            message,
            "pending",
        ])

    print(f"[ORDER] {action} {quantity_int}x {sku} by {name} <{email}>")
    return jsonify(success=True), 201


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    _ensure_csv()
    port = int(os.environ.get("PORT", "8080"))
    # Bind to loopback only — nginx handles external traffic
    app.run(host="127.0.0.1", port=port, debug=False)

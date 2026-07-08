"""fabiaweb_shop web server — Flask serves all traffic, nginx proxies everything.

On every HTML page view, an async Meta Pixel PageView event is fired with
forwarder headers (X-Forwarded-For, X-Forwarded-Proto, Referer, User-Agent,
and _fbp/_fbc cookies). The event is fire-and-forget: page serving never blocks.
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from meta_pixel import send_event_async

app = Flask(__name__, static_folder=None)

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
ORDERS_CSV = DATA_DIR / "orders.csv"

# Files that Flask is allowed to serve directly. Everything else is proxied
# through the catch-all route, but nginx blocks sensitive extensions first.
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


def _ensure_csv() -> None:
    """Create orders.csv with headers if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    if not ORDERS_CSV.exists():
        with ORDERS_CSV.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerow([
                "timestamp", "name", "email", "company", "country",
                "sku", "quantity", "action", "message", "status",
            ])


def _client_ip() -> str:
    """Recover the client IP from nginx forwarder headers."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _emit_page_view() -> None:
    """Send async Meta Pixel PageView event before serving HTML."""
    send_event_async(
        event_name="PageView",
        request=request,
        content_name="FABIABox Shop",
        content_category="shop",
    )


def _send_file(filename: str):
    """Read a whitelisted file and return a closed-body response."""
    path = BASE / filename
    with path.open("rb") as fh:
        data = fh.read()
    from flask import make_response
    response = make_response(data)
    # Best-effort MIME type
    if filename.endswith(".html"):
        response.headers["Content-Type"] = "text/html; charset=utf-8"
    elif filename.endswith(".png"):
        response.headers["Content-Type"] = "image/png"
    return response


@app.route("/")
@app.route("/<path:filename>")
def catch_all(filename: str = "index.html"):
    """Serve the SPA index page or whitelisted static assets.

    Any path without a file extension falls back to index.html so the
    single-page shop handles its own routing in the browser. Paths that
    look like files but are not explicitly whitelisted return 404 so we
    never leak source data or config even if nginx regex blocks are absent.
    """
    if filename in SERVABLE:
        if filename == "index.html":
            _emit_page_view()
        return _send_file(filename)

    # SPA route — serve index.html and fire the PageView event.
    if "." not in filename:
        _emit_page_view()
        return _send_file("index.html")

    return jsonify(error="not found"), 404


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

    # Fire a corresponding CAPI event for segmentation/optimization.
    if action == "pre-buy":
        send_event_async(
            event_name="InitiateCheckout",
            request=request,
            email=email,
            first_name=name.split()[0] if name.split() else None,
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else None,
            country=country,
            content_name=sku,
            content_category="fabiabox_hardware",
            content_ids=[sku],
            content_type="product",
            num_items=quantity_int,
        )
    else:
        send_event_async(
            event_name="Lead",
            request=request,
            email=email,
            first_name=name.split()[0] if name.split() else None,
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else None,
            country=country,
            content_name=sku,
            content_category="fabiabox_hardware",
            content_ids=[sku],
            content_type="product",
            status="waiting-list",
            custom_properties={"action": action, "quantity": quantity_int},
        )

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

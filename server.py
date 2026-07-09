"""fabiaweb_shop web server — Flask serves all traffic, nginx proxies everything.

On every HTML page view, an async Meta Pixel PageView event is fired with
forwarder headers (X-Forwarded-For, X-Forwarded-Proto, Referer, User-Agent,
and _fbp/_fbc cookies). The event is fire-and-forget: page serving never blocks.
"""

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

from matomo_tracker import track_event, track_page_view
from meta_pixel import send_event_async

app = Flask(__name__, static_folder=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1, x_host=1, x_prefix=0)


@app.before_request
def _log_request() -> None:
    """Log every request with the recovered client IP for debugging."""
    if request.path == "/health":
        return
    print(
        f"[REQUEST] {request.method} {request.path} "
        f"ip={_client_ip()} host={request.host} "
        f"proto={request.headers.get('X-Forwarded-Proto', '')} "
        f"ua={request.headers.get('User-Agent', '')[:80]}"
    )

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE / "data"
ORDERS_CSV = DATA_DIR / "orders.csv"
VERSION_FILE = BASE / "version.json"


def _load_version() -> dict | None:
    """Return the deployed git version info if available."""
    if not VERSION_FILE.exists():
        return None
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None

# Files that Flask is allowed to serve directly. Everything else is proxied
# through the catch-all route, but nginx blocks sensitive extensions first.
SERVABLE = {
    "favicon.ico",
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


def _uid_from_email(email: str) -> str:
    """Stable pseudonymised Matomo user ID."""
    return hashlib.sha256(email.encode("utf-8")).hexdigest()


def _track_form_error(error: str, action_name: str = "FABIABox Shop") -> None:
    """Track a form validation error so drop-off points are visible in Matomo."""
    if app.testing:
        return
    track_event(
        request,
        category="form",
        action="validation-error",
        name=error,
        action_name=action_name,
    )


def _emit_page_view() -> None:
    """Send async Meta Pixel + Matomo PageView events before serving HTML."""
    send_event_async(
        event_name="PageView",
        request=request,
        content_name="FABIABox Shop",
        content_category="shop",
    )
    if app.testing:
        return
    track_page_view(request, action_name="FABIABox Shop")


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
    elif filename.endswith(".ico"):
        response.headers["Content-Type"] = "image/x-icon"
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
        _track_form_error("missing-name-or-email")
        return jsonify(success=False, error="Name and valid email required"), 400

    if not country:
        _track_form_error("missing-country")
        return jsonify(success=False, error="Country required"), 400

    if not consent_ok:
        _track_form_error("missing-consent")
        return jsonify(success=False, error="Consent required"), 400

    if sku not in VALID_SKUS:
        _track_form_error("invalid-product")
        return jsonify(success=False, error="Invalid product"), 400

    if action not in VALID_ACTIONS:
        _track_form_error("invalid-action")
        return jsonify(success=False, error="Invalid action"), 400

    try:
        quantity_int = int(quantity)
        if quantity_int < 1:
            raise ValueError
    except (ValueError, TypeError):
        _track_form_error("invalid-quantity")
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

    uid = _uid_from_email(email)

    if not app.testing:
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
            track_event(
                request,
                category="conversion",
                action="initiate-checkout",
                name=sku,
                value=float(quantity_int),
                action_name="FABIABox Shop",
                uid=uid,
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
            track_event(
                request,
                category="conversion",
                action="lead",
                name=sku,
                value=float(quantity_int),
                action_name="FABIABox Shop",
                uid=uid,
            )

    return jsonify(success=True), 201


@app.route("/health")
def health():
    return jsonify(status="ok", version=_load_version()), 200


if __name__ == "__main__":
    _ensure_csv()
    port = int(os.environ.get("PORT", "8080"))
    # Bind to loopback only — nginx handles external traffic
    app.run(host="127.0.0.1", port=port, debug=False)

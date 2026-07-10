"""Meta Pixel Conversions API — async server-side events."""

import hashlib
import hmac
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

import requests

API_VERSION = os.environ.get("META_CAPI_VERSION", "v18.0")


def _appsecret_proof(access_token: str) -> Optional[str]:
    """Generate the appsecret_proof required by Meta for server-side API calls."""
    app_secret = os.environ.get("META_APP_SECRET", "")
    if not app_secret or not access_token:
        return None
    return hmac.new(
        app_secret.encode("utf-8"),
        access_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


# Fire-and-forget thread pool so page serving is never blocked.
_executor = ThreadPoolExecutor(max_workers=2)


def _sha256(value: Optional[str]) -> Optional[str]:
    """Hash user data the way Meta expects (lowercase, trimmed, UTF-8)."""
    if not value:
        return None
    return hashlib.sha256(value.lower().strip().encode("utf-8")).hexdigest()


def _client_ip_from_request(request) -> str:
    """Best-guess client IP from nginx forwarder headers."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _build_user_data(
    request,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    external_id: Optional[str] = None,
) -> dict[str, Any]:
    """Build a user_data payload with hashed PII and browser/click IDs."""
    user_data: dict[str, Any] = {
        "client_ip_address": _client_ip_from_request(request),
        "client_user_agent": request.headers.get("User-Agent", ""),
    }

    # Browser / click IDs (from Meta Pixel JS or ads)
    fbp = request.cookies.get("_fbp")
    fbc = request.cookies.get("_fbc")
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc

    # Hashed PII — only send when you have explicit consent (GDPR)
    em_hash = _sha256(email)
    if em_hash:
        user_data["em"] = em_hash
        # Use email hash as a stable external ID when no user ID exists.
        if not external_id:
            user_data["external_id"] = em_hash

    ph_hash = _sha256(phone)
    if ph_hash:
        user_data["ph"] = ph_hash

    fn_hash = _sha256(first_name)
    if fn_hash:
        user_data["fn"] = fn_hash

    ln_hash = _sha256(last_name)
    if ln_hash:
        user_data["ln"] = ln_hash

    if country:
        user_data["country"] = country.lower().strip()

    if city:
        user_data["ct"] = city.lower().strip()

    if external_id:
        user_data["external_id"] = external_id.lower().strip()

    return user_data


def send_event_async(
    event_name: str,
    request,
    value: Optional[float] = None,
    currency: Optional[str] = None,
    content_name: Optional[str] = None,
    content_category: Optional[str] = None,
    content_ids: Optional[list[str]] = None,
    contents: Optional[list[dict[str, Any]]] = None,
    content_type: Optional[str] = None,
    num_items: Optional[int] = None,
    status: Optional[str] = None,
    predicted_ltv: Optional[float] = None,
    custom_properties: Optional[dict[str, Any]] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    country: Optional[str] = None,
    city: Optional[str] = None,
    external_id: Optional[str] = None,
) -> None:
    """Send a Meta Pixel Conversions API event asynchronously.

    Does nothing if META_PIXEL_ID or META_ACCESS_TOKEN is missing.
    Failures are swallowed — page serving must never block or error.
    """
    pixel_id = os.environ.get("META_PIXEL_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")
    if not pixel_id or not access_token:
        return

    custom_data: dict[str, Any] = {}
    if value is not None:
        custom_data["value"] = value
    if currency:
        custom_data["currency"] = currency.upper()
    if content_name:
        custom_data["content_name"] = content_name
    if content_category:
        custom_data["content_category"] = content_category
    if content_ids:
        custom_data["content_ids"] = content_ids
    if contents:
        custom_data["contents"] = contents
    if content_type:
        custom_data["content_type"] = content_type
    if num_items is not None:
        custom_data["num_items"] = num_items
    if status:
        custom_data["status"] = status
    if predicted_ltv is not None:
        custom_data["predicted_ltv"] = predicted_ltv
    if custom_properties:
        custom_data.update(custom_properties)

    payload = {
        "data": [
            {
                "event_name": event_name,
                "event_time": int(time.time()),
                "event_id": str(uuid.uuid4()),
                "action_source": "website",
                "event_source_url": request.url,
                "user_data": _build_user_data(
                    request,
                    email=email,
                    phone=phone,
                    first_name=first_name,
                    last_name=last_name,
                    country=country,
                    city=city,
                    external_id=external_id,
                ),
                "custom_data": custom_data,
            }
        ]
    }

    referrer = request.headers.get("Referer")
    if referrer:
        custom_data["referrer"] = referrer

    endpoint = f"https://graph.facebook.com/{API_VERSION}/{pixel_id}/events"
    params = {"access_token": access_token}
    proof = _appsecret_proof(access_token)
    if proof:
        params["appsecret_proof"] = proof

    _executor.submit(_send_event, endpoint, params, payload)


def send_page_view_async(
    url: str,
    user_agent: str,
    client_ip: str,
    fbp: Optional[str] = None,
    fbc: Optional[str] = None,
    referrer: Optional[str] = None,
    email: Optional[str] = None,
) -> None:
    """Legacy PageView helper kept for backward compatibility.

    Prefer send_event_async for new code.
    """
    pixel_id = os.environ.get("META_PIXEL_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")
    if not pixel_id or not access_token:
        return

    user_data = {
        "client_ip_address": client_ip,
        "client_user_agent": user_agent or "",
    }
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc
    if email:
        user_data["em"] = _sha256(email)
        user_data["external_id"] = _sha256(email)

    payload = {
        "data": [
            {
                "event_name": "PageView",
                "event_time": int(time.time()),
                "event_id": str(uuid.uuid4()),
                "action_source": "website",
                "event_source_url": url,
                "user_data": user_data,
                "custom_data": {},
            }
        ]
    }
    if referrer:
        payload["data"][0]["custom_data"]["referrer"] = referrer

    endpoint = f"https://graph.facebook.com/{API_VERSION}/{pixel_id}/events"
    params = {"access_token": access_token}
    proof = _appsecret_proof(access_token)
    if proof:
        params["appsecret_proof"] = proof

    _executor.submit(_send_event, endpoint, params, payload)


def _send_event(endpoint: str, params: dict, payload: dict) -> None:
    event_name = payload.get("data", [{}])[0].get("event_name", "unknown")
    ip = payload.get("data", [{}])[0].get("user_data", {}).get("client_ip_address", "")
    try:
        print(f"[PIXEL] send event={event_name} ip={ip}")
        response = requests.post(endpoint, params=params, json=payload, timeout=5)
        print(f"[PIXEL] response event={event_name} status={response.status_code}")
        if response.status_code >= 400:
            # Log the error body (never the access token) so we can diagnose 400s.
            body = response.text
            print(f"[PIXEL] response body event={event_name}: {body[:500]}")
        response.raise_for_status()
    except requests.HTTPError:
        # HTTP errors are already logged above with status + body.
        pass
    except Exception as exc:
        print(f"[PIXEL] send failed event={event_name}: {type(exc).__name__}: {exc}")
        # CAPI failures must not break the shop.
        pass

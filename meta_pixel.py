"""Meta Pixel Conversions API — async server-side PageView events."""

import hashlib
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import requests

API_VERSION = os.environ.get("META_CAPI_VERSION", "v18.0")

# Fire-and-forget thread pool so page serving is never blocked.
_executor = ThreadPoolExecutor(max_workers=2)


def _sha256(value: str) -> str:
    """Hash user data the way Meta expects (lowercase, trimmed, UTF-8)."""
    return hashlib.sha256(value.lower().strip().encode("utf-8")).hexdigest()


def _client_ip(headers, remote_addr: Optional[str]) -> str:
    """Best-guess client IP from nginx forwarder headers."""
    xff = headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return remote_addr or ""


def send_page_view_async(
    url: str,
    user_agent: str,
    client_ip: str,
    fbp: Optional[str] = None,
    fbc: Optional[str] = None,
    referrer: Optional[str] = None,
    email: Optional[str] = None,
) -> None:
    """Send a Meta Pixel PageView event asynchronously.

    Does nothing if META_PIXEL_ID or META_ACCESS_TOKEN is missing.
    Failures are swallowed — page serving must never block or error.
    """
    pixel_id = os.environ.get("META_PIXEL_ID")
    access_token = os.environ.get("META_ACCESS_TOKEN")
    if not pixel_id or not access_token:
        return

    user_data = {
        "client_ip_address": _client_ip({}, client_ip),
        "client_user_agent": user_agent or "",
    }
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc
    if email:
        user_data["em"] = _sha256(email)

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

    _executor.submit(_send_event, endpoint, params, payload)


def _send_event(endpoint: str, params: dict, payload: dict) -> None:
    try:
        response = requests.post(endpoint, params=params, json=payload, timeout=5)
        response.raise_for_status()
    except Exception:
        # CAPI failures must not break the shop.
        pass

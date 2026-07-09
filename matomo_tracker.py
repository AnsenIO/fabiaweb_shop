"""Matomo Tracking API — async server-side page views and events.

Tracks page views and conversion events on a self-hosted Matomo instance.
Fires hits in a background thread pool so page serving is never blocked.

Environment variables:
    MATOMO_URL        Matomo root URL or full tracker endpoint.
                      Example: https://platform.iabai.net/
                      A path ending in .php is used as-is; otherwise
                      /matomo.php is appended.
    MATOMO_SITE_ID    Site ID (default: 1).
    MATOMO_TOKEN_AUTH Optional auth token. When present the real visitor
                      IP is forwarded via the cip parameter.
"""

import hashlib
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from urllib.parse import urlencode, urljoin

import requests

_executor = ThreadPoolExecutor(max_workers=2)


def _tracker_url() -> Optional[str]:
    """Resolve the Matomo tracking endpoint from env."""
    url = os.environ.get("MATOMO_URL", "https://platform.iabai.net/").rstrip()
    if not url:
        return None
    if url.endswith(".php"):
        return url
    if not url.endswith("/"):
        url += "/"
    return urljoin(url, "matomo.php")


def _site_id() -> str:
    return os.environ.get("MATOMO_SITE_ID", "1").strip() or "1"


def _token_auth() -> Optional[str]:
    return os.environ.get("MATOMO_TOKEN_AUTH") or None


def _client_ip(request) -> str:
    """Best-guess client IP from nginx forwarder headers."""
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or ""


def _visitor_id(request) -> str:
    """Return a stable 16-character hex visitor ID for Matomo.

    Prefers an existing Matomo first-party cookie. Falls back to a
    deterministic hash of IP + User-Agent.
    """
    for name, value in request.cookies.items():
        if name.startswith("_pk_id") and "." in value:
            candidate = value.split(".")[0]
            if len(candidate) == 16 and all(c in "0123456789abcdefABCDEF" for c in candidate):
                return candidate.lower()

    ip = _client_ip(request)
    ua = request.headers.get("User-Agent", "")
    digest = hashlib.md5(f"{ip}|{ua}".encode("utf-8")).hexdigest()
    return digest[:16]


def _base_params(request, url: Optional[str] = None) -> dict:
    """Build the common query parameters for every Matomo hit."""
    params = {
        "idsite": _site_id(),
        "rec": "1",
        "apiv": "1",
        "send_image": "0",
        "rand": str(int(time.time() * 1000)) + str(random.randint(1000, 9999)),
        "_id": _visitor_id(request),
        "url": url or request.url,
        "ua": request.headers.get("User-Agent", ""),
    }

    referrer = request.headers.get("Referer") or request.headers.get("Referrer")
    if referrer:
        params["urlref"] = referrer

    token = _token_auth()
    if token:
        params["token_auth"] = token
        params["cip"] = _client_ip(request)

    return params


def track_page_view(
    request,
    action_name: Optional[str] = None,
    url: Optional[str] = None,
) -> None:
    """Fire an async Matomo PageView hit. Does nothing if MATOMO_URL is unset."""
    endpoint = _tracker_url()
    if not endpoint:
        return

    params = _base_params(request, url=url)
    if action_name:
        params["action_name"] = action_name

    _executor.submit(_send_hit, endpoint, params)


def track_event(
    request,
    category: str,
    action: str,
    name: Optional[str] = None,
    value: Optional[float] = None,
    url: Optional[str] = None,
    action_name: Optional[str] = None,
) -> None:
    """Fire an async Matomo event hit."""
    endpoint = _tracker_url()
    if not endpoint:
        return

    params = _base_params(request, url=url)
    params["e_c"] = category
    params["e_a"] = action
    if name:
        params["e_n"] = name
    if value is not None:
        params["e_v"] = str(value)
    if action_name:
        params["action_name"] = action_name

    _executor.submit(_send_hit, endpoint, params)


def _send_hit(endpoint: str, params: dict) -> None:
    try:
        requests.get(endpoint, params=params, timeout=5)
    except Exception:
        # Tracking failures must never break the site.
        pass

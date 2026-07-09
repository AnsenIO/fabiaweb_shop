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
import ipaddress
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, urljoin

import requests

_executor = ThreadPoolExecutor(max_workers=2)


def _hashed_uid(email: str) -> str:
    """Return a stable, pseudonymised user ID from an email address."""
    return hashlib.sha256(email.lower().strip().encode("utf-8")).hexdigest()


_DEFAULT_EXCLUDED_NETWORKS = (
    "127.0.0.0/8",
    "10.0.0.0/8",
    "172.16.0.0/12",
    "192.168.0.0/16",
    "::1/128",
    "fc00::/7",
)


def _excluded_networks() -> list:
    """Return IP networks that should not be tracked.

    Defaults to common loopback/private ranges. Add public IPs/CIDRs via
    the MATOMO_EXCLUDE_IPS environment variable (comma-separated).
    """
    networks = [
        ipaddress.ip_network(cidr, strict=False)
        for cidr in _DEFAULT_EXCLUDED_NETWORKS
    ]
    raw = os.environ.get("MATOMO_EXCLUDE_IPS", "")
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            # Ignore malformed entries rather than breaking tracking.
            continue
    return networks


def _is_excluded_ip(ip: str) -> bool:
    """Return True if the given IP is in an excluded network."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _excluded_networks())


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


def _base_params(request, url: Optional[str] = None, uid: Optional[str] = None) -> dict:
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

    if uid:
        params["uid"] = uid

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
    uid: Optional[str] = None,
) -> None:
    """Fire an async Matomo PageView hit. Does nothing if MATOMO_URL is unset."""
    endpoint = _tracker_url()
    if not endpoint or _is_excluded_ip(_client_ip(request)):
        return

    params = _base_params(request, url=url, uid=uid)
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
    uid: Optional[str] = None,
) -> None:
    """Fire an async Matomo event hit."""
    endpoint = _tracker_url()
    if not endpoint or _is_excluded_ip(_client_ip(request)):
        return

    params = _base_params(request, url=url, uid=uid)
    params["e_c"] = category
    params["e_a"] = action
    if name:
        params["e_n"] = name
    if value is not None:
        params["e_v"] = str(value)
    if action_name:
        params["action_name"] = action_name

    _executor.submit(_send_hit, endpoint, params)


def track_download(
    request,
    filename: str,
    url: Optional[str] = None,
    uid: Optional[str] = None,
) -> None:
    """Fire an async Matomo event for a file download."""
    suffix = Path(filename).suffix.lstrip(".").lower() or "file"
    track_event(
        request,
        category="download",
        action=suffix,
        name=filename,
        url=url,
        uid=uid,
    )


def _send_hit(endpoint: str, params: dict) -> None:
    try:
        requests.get(endpoint, params=params, timeout=5)
    except Exception:
        # Tracking failures must never break the site.
        pass

#!/usr/bin/env python3
"""Soft validation of Meta Pixel and Matomo tracking configuration.

Loads the local .env, checks that required variables are present, and makes
small test calls to both endpoints. Never prints secrets.
"""

import hashlib
import hmac
import os
import sys
import time
import uuid
from typing import Any

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _check(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if value:
        # Only reveal length so the user knows it loaded without exposing it.
        return f"present (len={len(value)})"
    return "MISSING"


def _appsecret_proof(access_token: str) -> str:
    secret = os.environ["META_APP_SECRET"]
    return hmac.new(
        secret.encode("utf-8"),
        access_token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def validate_meta() -> dict[str, Any]:
    print("[META] Checking configuration...")
    result: dict[str, Any] = {
        "pixel_id": _check("META_PIXEL_ID"),
        "access_token": _check("META_ACCESS_TOKEN"),
        "app_secret": _check("META_APP_SECRET"),
    }
    for k, v in result.items():
        print(f"[META] {k}: {v}")

    if any(v == "MISSING" for v in result.values()):
        print("[META] SKIP test call — required variables missing.")
        result["test_status"] = "skipped"
        return result

    pixel_id = os.environ["META_PIXEL_ID"]
    access_token = os.environ["META_ACCESS_TOKEN"]
    version = os.environ.get("META_CAPI_VERSION", "v18.0")
    endpoint = f"https://graph.facebook.com/{version}/{pixel_id}/events"

    event_id = f"validate-{uuid.uuid4()}"
    payload = {
        "data": [
            {
                "event_name": "PageView",
                "event_time": int(time.time()),
                "event_id": event_id,
                "action_source": "website",
                "event_source_url": "https://shop.fabiabox.com/validate",
                "user_data": {
                    "client_ip_address": "127.0.0.1",
                    "client_user_agent": "fabia-validate/1.0",
                },
                "custom_data": {},
            }
        ]
    }
    params = {
        "access_token": access_token,
        "appsecret_proof": _appsecret_proof(access_token),
    }

    try:
        resp = requests.post(endpoint, params=params, json=payload, timeout=10)
        result["test_status_code"] = resp.status_code
        try:
            body = resp.json()
            result["test_body"] = body
            print(f"[META] Test call status: {resp.status_code}")
            print(f"[META] Test call body: {body}")
            if resp.status_code == 200 and body.get("events_received") == 1:
                result["test_status"] = "ok"
            else:
                result["test_status"] = "error"
        except Exception:
            result["test_body"] = resp.text[:500]
            print(f"[META] Test call status: {resp.status_code}")
            print(f"[META] Test call body (non-JSON): {resp.text[:500]}")
            result["test_status"] = "error"
    except Exception as exc:
        print(f"[META] Test call failed: {type(exc).__name__}: {exc}")
        result["test_status"] = "exception"
        result["test_error"] = str(exc)

    return result


def validate_matomo() -> dict[str, Any]:
    print("\n[MATOMO] Checking configuration...")
    # Fallback to the known defaults if env vars are not set.
    matomo_url = os.environ.get("MATOMO_URL", "https://platform.iabai.net/").strip()
    site_id_str = os.environ.get("MATOMO_SITE_ID", "1").strip()

    result: dict[str, Any] = {
        "url": _check("MATOMO_URL") if os.environ.get("MATOMO_URL") else f"default ({matomo_url})",
        "site_id": _check("MATOMO_SITE_ID") if os.environ.get("MATOMO_SITE_ID") else f"default ({site_id_str})",
        "token_auth": _check("MATOMO_TOKEN_AUTH"),
    }
    for k, v in result.items():
        print(f"[MATOMO] {k}: {v}")

    if result["token_auth"] == "MISSING":
        print("[MATOMO] SKIP test call — token_auth missing.")
        result["test_status"] = "skipped"
        return result

    base_url = matomo_url.rstrip("/") + "/"
    site_id = int(site_id_str)
    token = os.environ["MATOMO_TOKEN_AUTH"]

    # 1. Tracking API test with a known override IP.
    test_ip = "185.247.137.198"
    test_url = f"https://fabiabox.com/validate-{uuid.uuid4()}"
    tracking_endpoint = f"{base_url}matomo.php"
    tracking_params = {
        "idsite": site_id,
        "rec": 1,
        "url": test_url,
        "action_name": "Validate / Tracking",
        "cip": test_ip,
        "ua": "fabia-validate/1.0",
    }
    try:
        resp = requests.post(
            tracking_endpoint,
            params=tracking_params,
            data={"token_auth": token},
            timeout=10,
        )
        result["tracking_status_code"] = resp.status_code
        print(f"[MATOMO] Tracking test status: {resp.status_code}")
    except Exception as exc:
        print(f"[MATOMO] Tracking test failed: {type(exc).__name__}: {exc}")
        result["test_status"] = "exception"
        result["test_error"] = str(exc)
        return result

    # 2. Reporting API test — confirm the override IP was recorded.
    reporting_endpoint = f"{base_url}index.php"
    reporting_params = {
        "module": "API",
        "method": "Live.getLastVisitsDetails",
        "idSite": site_id,
        "period": "day",
        "date": "today",
        "segment": f"visitIp=={test_ip}",
        "format": "json",
    }
    try:
        resp = requests.post(
            reporting_endpoint,
            params=reporting_params,
            data={"token_auth": token},
            timeout=15,
        )
        result["reporting_status_code"] = resp.status_code
        visits = resp.json() if resp.status_code == 200 else []
        matched = [v for v in visits if v.get("visitIp") == test_ip]
        result["ip_override_working"] = len(matched) > 0
        result["matched_visits"] = len(matched)
        print(f"[MATOMO] Reporting test status: {resp.status_code}")
        print(f"[MATOMO] IP override working: {len(matched) > 0} ({len(matched)} matched visit(s))")
        if resp.status_code == 200 and matched:
            result["test_status"] = "ok"
        elif resp.status_code == 200:
            result["test_status"] = "ip_override_failed"
        else:
            result["test_status"] = "error"
            print(f"[MATOMO] Reporting body: {resp.text[:500]}")
    except Exception as exc:
        print(f"[MATOMO] Reporting test failed: {type(exc).__name__}: {exc}")
        result["test_status"] = "exception"
        result["test_error"] = str(exc)

    return result


def main() -> int:
    print("=" * 60)
    print("Fabia tracking validation")
    print("=" * 60)

    meta = validate_meta()
    matomo = validate_matomo()

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Meta:    {meta.get('test_status', 'unknown')}")
    print(f"Matomo:  {matomo.get('test_status', 'unknown')}")

    if meta.get("test_status") == "ok" and matomo.get("test_status") == "ok":
        print("\nAll good — both endpoints are reachable and accepting data.")
        return 0

    print("\nSome checks failed. See output above for details.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

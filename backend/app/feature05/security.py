import hashlib
import hmac
import os
import secrets
import time


# Set FEATURE05_SECRET in your environment (.env) so links survive restarts.
_SECRET = os.getenv("FEATURE05_SECRET") or secrets.token_hex(32)

SIGNED_URL_TTL_SECONDS = 900  # 15 minutes


def _sign(session_id: str, investigation_id: str, expires: int) -> str:
    message = f"{session_id}|{investigation_id}|{expires}".encode("utf-8")
    return hmac.new(
        _SECRET.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()


def create_signed_params(
    session_id: str,
    investigation_id: str,
    ttl: int = SIGNED_URL_TTL_SECONDS,
) -> dict:
    expires = int(time.time()) + ttl
    return {
        "exp": expires,
        "sig": _sign(session_id, investigation_id, expires),
    }


def verify_signature(
    session_id: str,
    investigation_id: str,
    exp,
    sig,
) -> bool:
    if not sig or exp is None:
        return False

    try:
        exp = int(exp)
    except (TypeError, ValueError):
        return False

    if exp < int(time.time()):
        return False

    expected = _sign(session_id, investigation_id, exp)
    return hmac.compare_digest(expected, str(sig))

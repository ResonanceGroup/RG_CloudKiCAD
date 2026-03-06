import base64
import hashlib
import hmac
import json
import time
from typing import Any, TypedDict

from fastapi import Response

from app.core.config import settings
from app.core.roles import Role

SESSION_COOKIE_NAME = "kicad_prism_session"
SESSION_COOKIE_SAMESITE = "lax"


class SessionPayload(TypedDict):
    email: str
    name: str
    picture: str
    role: Role
    iat: int
    exp: int


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(value: str) -> bytes:
    pad = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + pad).encode("ascii"))


def _sign(message: str) -> str:
    secret = settings.SESSION_SECRET.encode("utf-8")
    digest = hmac.new(secret, message.encode("utf-8"), hashlib.sha256).digest()
    return _b64_encode(digest)


def _serialize_payload(payload: SessionPayload) -> str:
    return _b64_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _deserialize_payload(encoded_payload: str) -> SessionPayload:
    raw = _b64_decode(encoded_payload)
    data: dict[str, Any] = json.loads(raw.decode("utf-8"))
    return SessionPayload(
        email=str(data["email"]).strip().lower(),
        name=str(data.get("name") or ""),
        picture=str(data.get("picture") or ""),
        role=str(data["role"]),  # type: ignore[typeddict-item]
        iat=int(data["iat"]),
        exp=int(data["exp"]),
    )


def create_session_token(email: str, name: str, picture: str, role: Role) -> str:
    now = int(time.time())
    payload: SessionPayload = SessionPayload(
        email=email.strip().lower(),
        name=name,
        picture=picture,
        role=role,
        iat=now,
        exp=now + (settings.SESSION_TTL_HOURS * 3600),
    )
    encoded_payload = _serialize_payload(payload)
    signature = _sign(encoded_payload)
    return f"v1.{encoded_payload}.{signature}"


def decode_session_token(token: str) -> SessionPayload | None:
    if not token:
        return None
    if not settings.SESSION_SECRET:
        return None

    parts = token.split(".")
    if len(parts) != 3 or parts[0] != "v1":
        return None

    _, encoded_payload, signature = parts
    expected_signature = _sign(encoded_payload)
    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        payload = _deserialize_payload(encoded_payload)
    except (ValueError, json.JSONDecodeError, KeyError, TypeError):
        return None

    if payload["exp"] <= int(time.time()):
        return None
    return payload


def set_session_cookie(response: Response, token: str) -> None:
    max_age = settings.SESSION_TTL_HOURS * 3600
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        max_age=max_age,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=SESSION_COOKIE_SAMESITE,
        path="/",
    )

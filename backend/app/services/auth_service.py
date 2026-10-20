"""Accounts and sessions, stored in the app database.

Passwords: salted scrypt (standard library, no extra dependency).
Sessions: random opaque tokens; only their SHA-256 is stored, so the database never
holds a usable login token. Logging out deletes the row, which revokes it instantly.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.services.postgres_service import DatabaseProtocol

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LEN = 32

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


class AuthError(ValueError):
    """Raised with a message that is safe to show the user."""


@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str


# --- passwords -------------------------------------------------------------

def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=_SCRYPT_LEN)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = _scrypt(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P)
    b64 = lambda raw: base64.b64encode(raw).decode("ascii")  # noqa: E731
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${b64(salt)}${b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = _scrypt(password, salt, int(n), int(r), int(p))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Verified against when the email is unknown, so "no such user" and "wrong password"
# cost the same time and can't be told apart by timing.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def validate_credentials(email: str, password: str) -> str:
    """Return the normalised email, or raise AuthError with a user-facing message."""
    email = email.strip().lower()
    if len(email) > 254 or not _EMAIL_RE.match(email):
        raise AuthError("Enter a valid email address.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise AuthError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters.")
    return email


# --- accounts --------------------------------------------------------------

async def create_user(db: DatabaseProtocol, email: str, password: str, name: str = "") -> User:
    email = validate_credentials(email, password)
    name = " ".join(name.split())[:80]
    if await db.fetch_one("SELECT id FROM app_users WHERE email = $1", (email,)):
        raise AuthError("An account with this email already exists.")
    password_hash = await asyncio.to_thread(hash_password, password)
    user_id = str(uuid.uuid4())
    try:
        await db.execute(
            "INSERT INTO app_users (id, email, name, password_hash, created_at) VALUES ($1, $2, $3, $4, $5)",
            (user_id, email, name, password_hash, datetime.now(UTC)),
        )
    except Exception:
        # Lost a race with a concurrent signup for the same email (UNIQUE constraint).
        if await db.fetch_one("SELECT id FROM app_users WHERE email = $1", (email,)):
            raise AuthError("An account with this email already exists.") from None
        raise
    return User(id=user_id, email=email, name=name)


async def authenticate(db: DatabaseProtocol, email: str, password: str) -> User | None:
    email = email.strip().lower()
    row = await db.fetch_one("SELECT * FROM app_users WHERE email = $1", (email,))
    stored = row["password_hash"] if row else _DUMMY_HASH
    ok = await asyncio.to_thread(verify_password, password, stored)
    if not row or not ok:
        return None
    return User(id=row["id"], email=row["email"], name=row.get("name", ""))


# --- sessions --------------------------------------------------------------

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(db: DatabaseProtocol, user_id: str, days: int) -> tuple[str, datetime]:
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires = now + timedelta(days=days)
    await db.execute("DELETE FROM app_sessions WHERE user_id = $1 AND expires_at < $2", (user_id, now))
    await db.execute(
        "INSERT INTO app_sessions (token_hash, user_id, created_at, expires_at) VALUES ($1, $2, $3, $4)",
        (_hash_token(token), user_id, now, expires),
    )
    return token, expires


async def user_for_session(db: DatabaseProtocol, token: str) -> User | None:
    if not token or len(token) > 200:
        return None
    row = await db.fetch_one(
        """
        SELECT u.id, u.email, u.name
        FROM app_sessions s JOIN app_users u ON u.id = s.user_id
        WHERE s.token_hash = $1 AND s.expires_at > $2
        """,
        (_hash_token(token), datetime.now(UTC)),
    )
    return User(id=row["id"], email=row["email"], name=row.get("name", "")) if row else None


async def end_session(db: DatabaseProtocol, token: str) -> None:
    if token:
        await db.execute("DELETE FROM app_sessions WHERE token_hash = $1", (_hash_token(token),))

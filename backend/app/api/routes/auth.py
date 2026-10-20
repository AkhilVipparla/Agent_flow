from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.api.auth_middleware import read_session_token, session_cookie_name
from app.api.dependencies import DbDep
from app.config import settings
from app.services.auth_service import (
    AuthError,
    User,
    authenticate,
    create_session,
    create_user,
    end_session,
)

router = APIRouter(tags=["auth"])

# Failed-login lockout per email, on top of the per-IP rate limit, so a botnet can't
# guess one account's password from many addresses. In memory, per process.
_MAX_FAILURES = 5
_LOCKOUT_SECONDS = 15 * 60
_failures: dict[str, tuple[int, float]] = {}


class SignupRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)
    name: str = Field(default="", max_length=120)


class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=256)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, name=user.name)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        session_cookie_name(),
        token,
        max_age=settings.session_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


def _locked_out(email: str) -> int:
    """Seconds remaining on a lockout, or 0."""
    count, first = _failures.get(email, (0, 0.0))
    if count >= _MAX_FAILURES:
        remaining = _LOCKOUT_SECONDS - (time.monotonic() - first)
        if remaining > 0:
            return int(remaining) + 1
        _failures.pop(email, None)
    return 0


def _record_failure(email: str) -> None:
    if len(_failures) > 10_000:
        _failures.clear()
    count, first = _failures.get(email, (0, time.monotonic()))
    if time.monotonic() - first > _LOCKOUT_SECONDS:
        count, first = 0, time.monotonic()
    _failures[email] = (count + 1, first)


@router.post("/auth/signup", response_model=UserResponse, status_code=201)
async def signup(body: SignupRequest, response: Response, db: DbDep) -> UserResponse:
    try:
        user = await create_user(db, body.email, body.password, body.name)
    except AuthError as exc:
        raise HTTPException(status_code=409 if "already exists" in str(exc) else 400, detail=str(exc)) from None
    token, _ = await create_session(db, user.id, settings.session_days)
    _set_session_cookie(response, token)
    return _user_response(user)


@router.post("/auth/login", response_model=UserResponse)
async def login(body: LoginRequest, response: Response, db: DbDep) -> UserResponse:
    email = body.email.strip().lower()
    wait = _locked_out(email)
    if wait:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {max(1, wait // 60)} minute(s).",
            headers={"Retry-After": str(wait)},
        )
    user = await authenticate(db, email, body.password)
    if user is None:
        _record_failure(email)
        # One message for "no such account" and "wrong password".
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _failures.pop(email, None)
    token, _ = await create_session(db, user.id, settings.session_days)
    _set_session_cookie(response, token)
    return _user_response(user)


@router.post("/auth/logout", status_code=204, response_model=None)
async def logout(request: Request, response: Response, db: DbDep) -> None:
    await end_session(db, read_session_token(request.scope["headers"]))
    response.delete_cookie(session_cookie_name(), path="/")


class SessionResponse(BaseModel):
    user: UserResponse | None


@router.get("/auth/session", response_model=SessionResponse)
async def session(request: Request) -> SessionResponse:
    """Who is signed in, if anyone. Always 200, so the browser's "am I signed in?" check on
    page load doesn't log a failed request when the answer is no."""
    user = request.scope.get("user")
    return SessionResponse(user=_user_response(user) if user else None)


@router.get("/auth/me", response_model=UserResponse)
async def me(request: Request) -> UserResponse:
    # AuthMiddleware has already rejected anonymous callers with a 401.
    return _user_response(request.scope["user"])

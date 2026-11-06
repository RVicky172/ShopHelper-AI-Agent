"""HTTP side of accounts: the login gate, /auth/* and /admin/*.

AccountsGate wraps every request, including /docs, so a new route is protected by default.
With accounts off (AWS) it passes everything through and these routes return 404.
"""

import re
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from shophelper.accounts import auth
from shophelper.api.schemas import LoginRequest, RoleChange, SignupRequest, UserOut
from shophelper.core.config import get_settings
from shophelper.core.identity import Principal, Role

PUBLIC_PATHS = {"/health", "/auth/signup", "/auth/login", "/auth/demo-accounts"}
PUBLIC_READS = re.compile(r"/categories|/products(/[^/]+)?")  # fullmatch: "/products/x/y" isn't one
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def is_public(method: str, path: str) -> bool:
    """The catalogue is open to reads only. Anything else on these paths still needs a session."""
    return path in PUBLIC_PATHS or (method == "GET" and PUBLIC_READS.fullmatch(path) is not None)


class AccountsGate:
    """Plain ASGI middleware, so it doesn't buffer streamed responses."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        settings = get_settings()
        if scope["type"] != "http" or not settings.accounts_enabled:
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        origin = request.headers.get("origin")
        if request.method in UNSAFE_METHODS and origin and origin != settings.web_origin:
            await JSONResponse({"detail": "Cross-site request refused"}, 403)(scope, receive, send)
            return

        token = request.cookies.get(auth.COOKIE_NAME)
        principal = None
        if token:
            principal = await run_in_threadpool(auth.resolve_session, auth.get_user_store(), token)
        if principal is None and not is_public(request.method, request.url.path):
            await JSONResponse({"detail": "Sign in first"}, 401)(scope, receive, send)
            return

        scope.setdefault("state", {})["principal"] = principal
        await self.app(scope, receive, send)


def current_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if principal is None:
        raise HTTPException(status_code=401, detail="Sign in first")
    return principal


def require_role(*roles: Role) -> Callable[[Request], Principal]:
    def check(request: Request) -> Principal:
        principal = current_principal(request)
        if principal.role not in roles:
            raise HTTPException(status_code=403, detail="You don't have access to this")
        return principal

    return check


def accounts_only() -> None:
    if not get_settings().accounts_enabled:
        raise HTTPException(status_code=404)


router = APIRouter(dependencies=[Depends(accounts_only)])


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth.COOKIE_NAME, token,
        max_age=int(auth.SESSION_LIFETIME.total_seconds()),
        httponly=True,  # page scripts can't read it
        samesite="strict",  # the browser won't send it on requests started by other sites
    )


def _user_out(user: auth.Principal | auth.User) -> UserOut:
    return UserOut(id=user.user_id, email=user.email, role=user.role, display_name=user.display_name)


# Plain `def` routes run in a worker thread, so slow password hashing doesn't block streaming.
@router.post("/auth/signup", status_code=201)
def signup(body: SignupRequest, response: Response) -> UserOut:
    store = auth.get_user_store()
    try:
        principal = auth.signup(store, body.email, body.password.get_secret_value(), body.display_name)
    except auth.InvalidSignup as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except auth.EmailTaken as exc:
        raise HTTPException(status_code=409, detail="That email already has an account") from exc
    _set_cookie(response, auth.start_session(store, principal.user_id))
    return _user_out(principal)


@router.post("/auth/login")
def login(body: LoginRequest, response: Response) -> UserOut:
    try:
        principal, token = auth.login(auth.get_user_store(), body.email, body.password.get_secret_value())
    except auth.InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="Wrong email or password") from exc
    except auth.LockedOut as exc:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in 15 minutes.") from exc
    _set_cookie(response, token)
    return _user_out(principal)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    auth.logout(auth.get_user_store(), request.cookies[auth.COOKIE_NAME])
    response.delete_cookie(auth.COOKIE_NAME)


@router.get("/auth/me")
def me(principal: Annotated[Principal, Depends(current_principal)]) -> UserOut:
    return _user_out(principal)


@router.get("/auth/demo-accounts")
def demo_accounts() -> list[dict]:
    return auth.demo_accounts() if get_settings().seed_demo_users else []


@router.get("/admin/users", dependencies=[Depends(require_role("admin"))])
def list_users() -> list[UserOut]:
    return [_user_out(u) for u in auth.get_user_store().list_users()]


@router.patch("/admin/users/{user_id}", dependencies=[Depends(require_role("admin"))])
def change_role(user_id: int, body: RoleChange) -> UserOut:
    try:
        user = auth.get_user_store().set_role(user_id, body.role)
    except auth.LastAdmin as exc:
        raise HTTPException(status_code=409, detail="This is the last admin") from exc
    if not user:
        raise HTTPException(status_code=404, detail="No such user")
    return _user_out(user)

"""Accounts: sign up, log in, cookie sessions and saved preferences under /api/auth.
Passwords are scrypt-hashed; session tokens are stored only as sha256. Existing routes never require a login."""
import hashlib
import hmac
import secrets

import psycopg
from fastapi import APIRouter, HTTPException, Request, Response
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from server import db

router = APIRouter(prefix="/api/auth")
COOKIE, DAYS = "camox_session", 30


class SignupIn(BaseModel):
    email: str = Field(pattern=r"^\S+@\S+$")
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    role: str | None = None
    organisation: str | None = None
    about: str = ""  # what they work on: places, populations, decisions; every agent reads it


class LoginIn(BaseModel):
    email: str
    password: str


class ProfileIn(BaseModel):
    name: str
    role: str | None = None
    organisation: str | None = None
    about: str | None = None


def _hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)


def _token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def current_user(request: Request):
    """The logged-in user (id, email, name, prefs) from the session cookie, or None."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    return db.q("select u.id, u.email, u.name, u.prefs from sessions s join users u on u.id = s.user_id "
                "where s.token_hash = %s and s.expires_at > now()", (_token_hash(token),), one=True)


def _require(request):
    user = current_user(request)
    if not user:
        raise HTTPException(401, "Not logged in.")
    return user


def _start_session(request, response, user_id):
    token = secrets.token_urlsafe(32)
    db.q("insert into sessions(token_hash, user_id, expires_at) values (%s, %s, now() + interval '30 days')",
         (_token_hash(token), user_id))
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    response.set_cookie(COOKIE, token, max_age=DAYS * 86400, httponly=True, samesite="lax", secure=secure, path="/")


def _profiles(user_id):
    return [db._public(r) for r in db.q(f"select {db.PROFILE_COLS}, keys from profiles where user_id = %s order by id",
                                        (user_id,))]


def _account(user):
    return {"user": {k: user[k] for k in ("id", "email", "name")}, "profiles": _profiles(user["id"]),
            "prefs": user["prefs"]}


@router.post("/signup", status_code=201)
def signup(body: SignupIn, request: Request, response: Response):
    salt = secrets.token_bytes(16)
    try:
        user = db.q("insert into users(email, name, pw_salt, pw_hash) values (%s, %s, %s, %s) returning id, email, name",
                    (body.email.strip().lower(), body.name, salt, _hash(body.password, salt)), one=True)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "An account with this email already exists.")
    db.q("insert into profiles(name, role, organisation, about, user_id) values (%s, %s, %s, %s, %s)",
         (body.name, body.role, body.organisation, body.about, user["id"]))
    _start_session(request, response, user["id"])
    return {"user": user, "profiles": _profiles(user["id"])}


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response):
    user = db.q("select id, email, name, prefs, pw_salt, pw_hash from users where email = %s",
                (body.email.strip().lower(),), one=True)
    # Hash even for unknown emails so the response time does not reveal which emails exist.
    digest = _hash(body.password, bytes(user["pw_salt"]) if user else b"0" * 16)
    if not user or not hmac.compare_digest(digest, bytes(user["pw_hash"])):
        raise HTTPException(401, "Wrong email or password.")
    _start_session(request, response, user["id"])
    return _account(user)


@router.post("/logout", status_code=204)
def logout(request: Request):
    token = request.cookies.get(COOKIE)
    if token:
        db.q("delete from sessions where token_hash = %s", (_token_hash(token),))
    response = Response(status_code=204)
    response.delete_cookie(COOKIE, path="/")
    return response


@router.get("/me")
def me(request: Request):
    return _account(_require(request))


@router.put("/prefs")
def set_prefs(prefs: dict, request: Request):
    user = _require(request)
    return db.q("update users set prefs = prefs || %s where id = %s returning prefs", (Jsonb(prefs), user["id"]), one=True)


@router.post("/profiles")
def create_profile(p: ProfileIn, request: Request):
    user = _require(request)
    return db._public(db.q(f"insert into profiles(name, role, organisation, about, user_id) values (%s, %s, %s, %s, %s) "
                           f"returning {db.PROFILE_COLS}, keys", (p.name, p.role, p.organisation, p.about, user["id"]),
                           one=True))


@router.put("/profiles/{profile_id}")
def update_profile(profile_id: int, p: ProfileIn, request: Request):
    user = _require(request)
    row = db.q(f"update profiles set name = %s, role = %s, organisation = %s, about = %s where id = %s and user_id = %s "
               f"returning {db.PROFILE_COLS}, keys", (p.name, p.role, p.organisation, p.about, profile_id, user["id"]), one=True)
    if not row:
        raise HTTPException(404, "No such profile on your account.")
    return db._public(row)


class PasswordIn(BaseModel):
    current: str
    new: str = Field(min_length=8)


@router.put("/password", status_code=204)
def change_password(body: PasswordIn, request: Request):
    user = _require(request)
    row = db.q("select pw_salt, pw_hash from users where id = %s", (user["id"],), one=True)
    if not hmac.compare_digest(_hash(body.current, bytes(row["pw_salt"])), bytes(row["pw_hash"])):
        raise HTTPException(401, "Current password is wrong.")
    salt = secrets.token_bytes(16)
    db.q("update users set pw_salt = %s, pw_hash = %s where id = %s", (salt, _hash(body.new, salt), user["id"]))


@router.delete("/account", status_code=204)
def delete_account(request: Request):
    """Deletes the user, their profiles (with projects and runs) and sessions."""
    user = _require(request)
    db.q("delete from profiles where user_id = %s", (user["id"],))
    db.q("delete from users where id = %s", (user["id"],))
    response = Response(status_code=204)
    response.delete_cookie(COOKIE, path="/")
    return response

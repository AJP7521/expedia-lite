"""Account registration, password comparison, and persistent login sessions."""
import hashlib
import hmac
import secrets
import time
from uuid import uuid4

from ..models import Account, AccountCreate, Credentials, User
from .database import DatabaseController
from .errors import AuthenticationError, ConflictError

SESSION_SECONDS = 86400


def public_account(user: User) -> Account:
    return Account(user_id=user.user_id, username=user.username,
                   display_name=user.display_name, email=user.email)


def _encode_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 200_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def register(body: AccountCreate) -> Account:
    with DatabaseController() as db:
        if db.find_user(body.username):
            raise ConflictError("That username is already taken.")
        user = User(user_id=f"U-{uuid4().hex}", display_name=body.username,
                    username=body.username, password=_encode_password(body.password, secrets.token_hex(16)),
                    email=body.email or None)
        return public_account(db.create(user))


def login(body: Credentials, old_token: str | None = None) -> tuple[Account, str]:
    with DatabaseController() as db:
        user = db.find_user(body.username)
        valid = False
        if user and user.password:
            salt = user.password.split("$")[1]
            valid = hmac.compare_digest(_encode_password(body.password, salt), user.password)
        if not valid:
            raise AuthenticationError("Incorrect username or password.")
        if old_token:
            db.remove_session(old_token)
        token = secrets.token_urlsafe(32)
        db.save_session(token, user.user_id, int(time.time()) + SESSION_SECONDS)
        return public_account(user), token


def current(token: str | None) -> Account:
    with DatabaseController() as db:
        user = db.session_user(token or "", int(time.time()))
        if not user or not user.username:
            raise AuthenticationError("Please log in to continue.")
        return public_account(user)


def logout(token: str | None) -> None:
    with DatabaseController() as db:
        db.remove_session(token or "")

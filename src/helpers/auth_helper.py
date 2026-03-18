from __future__ import annotations

import jwt
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# local imports
from src.config import config


class AuthHelper:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: int = 180) -> str:
        payload = data.copy()
        payload["exp"] = (datetime.now(timezone.utc) + timedelta(days=expires_delta)).timestamp()
        secret = config.JWT_SECRET
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def generate_otp() -> str:
        return f"{secrets.randbelow(10**6):06d}"

    @staticmethod
    def get_otp_expiry() -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=10)

    @staticmethod
    def verify_google_token(id_token_str: str, client_ids: list[str]) -> dict:
        idinfo = id_token.verify_oauth2_token(
            id_token_str, google_requests.Request()
        )
        if idinfo["aud"] not in client_ids:
            raise ValueError("Invalid Google client ID")
        return idinfo

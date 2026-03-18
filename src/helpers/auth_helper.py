from __future__ import annotations

import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

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

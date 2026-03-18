from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

import aiohttp
import bcrypt
import jwt

# local imports
from src.config import config

_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"


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
        payload["exp"] = (datetime.now(UTC) + timedelta(days=expires_delta)).timestamp()
        secret = config.JWT_SECRET
        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def generate_otp() -> str:
        return f"{secrets.randbelow(10**6):06d}"

    @staticmethod
    def get_otp_expiry() -> datetime:
        return datetime.now(UTC) + timedelta(minutes=10)

    @staticmethod
    async def verify_google_token(id_token_str: str, client_ids: list[str]) -> dict:
        """Verify Google ID token using Google's tokeninfo endpoint via aiohttp."""
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                _GOOGLE_CERTS_URL,
                params={"id_token": id_token_str},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp,
        ):
            if resp.status != 200:
                raise ValueError("Invalid Google token")
            import orjson

            idinfo = orjson.loads(await resp.read())

        if idinfo.get("aud") not in client_ids:
            raise ValueError("Invalid Google client ID")
        if idinfo.get("email_verified") not in ("true", True):
            raise ValueError("Google email not verified")
        return idinfo

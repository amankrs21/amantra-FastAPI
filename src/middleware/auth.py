from __future__ import annotations

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import orjson

from src.config import config
from src.database import get_db
from src.helpers.cipher import decrypt

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


async def verify_encryption_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Parse body for key field
    body_bytes = await request.body()
    key: str | None = None
    if body_bytes:
        try:
            body = orjson.loads(body_bytes)
            key = body.get("key") if isinstance(body, dict) else None
        except Exception:
            pass

    # If user has textVerify and key is provided, verify it
    if key:
        db = get_db()
        from bson import ObjectId
        user = await db.usermodels.find_one({"_id": ObjectId(payload["id"])})
        if user and user.get("textVerify"):
            try:
                decrypt(user["textVerify"], key)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid Encryption Key!")

    return payload

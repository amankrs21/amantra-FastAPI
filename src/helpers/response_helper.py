from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from src.models.user import UserResponse


def build_user_response(user: dict) -> UserResponse:
    """Build a standardized UserResponse from a raw MongoDB user document."""
    return UserResponse(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user.get("email", ""),
        dateOfBirth=user.get("dateOfBirth"),
        weatherCity=user.get("weatherCity"),
        avatarUrl=user.get("avatarUrl"),
        textVerify=user.get("textVerify"),
        isVerified=user.get("isVerified", False),
        createdAt=user.get("createdAt"),
    )


def build_user_dict(user: dict) -> dict:
    """Build a sanitized user dict (strips sensitive fields) for raw dict responses."""
    user.pop("password", None)
    user.pop("verificationOTP", None)
    user.pop("otpExpiresAt", None)
    user["id"] = str(user.pop("_id"))
    return user


def serialize_document(item: dict) -> dict:
    """Serialize a MongoDB document for JSON response (ObjectId → str, datetime → ISO)."""
    for key in ("_id", "createdBy"):
        if key in item:
            item[key] = str(item[key])
    for key in ("createdAt", "updatedAt"):
        if key in item and hasattr(item[key], "isoformat"):
            item[key] = item[key].isoformat()
    return item


def extract_domain(url: str) -> str:
    """Extract clean domain name from a URL."""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return "Unknown"


def compute_watchlist_status(parts: list[dict] | None) -> str | None:
    """Auto-derive watchlist status from parts progress."""
    if not parts:
        return None
    watched_count = sum(1 for p in parts if p.get("watched"))
    if watched_count == 0:
        return "to_watch"
    if watched_count == len(parts):
        return "watched"
    return "watching"

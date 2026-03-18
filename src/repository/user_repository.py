from __future__ import annotations

from typing import Optional

# local imports
from src.database import get_db


class UserRepoError(RuntimeError):
    """Custom exception for user repository errors."""


class UserRepository:
    def __init__(self) -> None:
        self._db = get_db()
        self._users = self._db.users

    # Get user by email
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        return self._users.find_one({"email": email})

from __future__ import annotations

from functools import lru_cache

# local imports
from src.services.auth_service import AuthService
from src.repository.user_repository import UserRepository



@lru_cache(maxsize=1)
def _auth_service_singleton() -> AuthService:
    """Provision a singleton instance of AuthService for FastAPI dependency injection."""
    return AuthService(UserRepository())

def get_auth_service() -> AuthService:
    return _auth_service_singleton()

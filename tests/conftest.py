from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Set env vars before any src imports
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017/testdb")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-key-for-testing")
os.environ.setdefault("PASSWORD_KEY", "01234567890123456789012345678901")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("SMTP_EMAIL", "test@test.com")
os.environ.setdefault("SMTP_PASSWORD", "testpass")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily")
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral")
os.environ.setdefault("GOOGLE_CLIENT_IDS", "test-client-id")

from src.helpers.auth_helper import AuthHelper

_helper = AuthHelper()

TEST_USER_ID = "507f1f77bcf86cd799439011"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_NAME = "Test User"
TEST_USER_PASSWORD = "SecurePass123!"
TEST_USER_HASHED_PW = _helper.hash_password(TEST_USER_PASSWORD)


def _make_test_user(**overrides) -> dict:
    from bson import ObjectId

    base = {
        "_id": ObjectId(TEST_USER_ID),
        "email": TEST_USER_EMAIL,
        "name": TEST_USER_NAME,
        "password": TEST_USER_HASHED_PW,
        "isVerified": True,
        "textVerify": None,
        "dateOfBirth": None,
        "weatherCity": None,
        "avatarUrl": None,
        "verificationOTP": None,
        "otpExpiresAt": None,
    }
    base.update(overrides)
    return base


@pytest.fixture
def test_user():
    return _make_test_user()


@pytest.fixture
def auth_token():
    return _helper.create_access_token({"id": TEST_USER_ID, "name": TEST_USER_NAME})


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest_asyncio.fixture
async def client():
    """Create test client with mocked DB (no real MongoDB)."""
    # Patch get_db before importing app to prevent real DB connections
    mock_db = MagicMock()
    # Make db.usermodels.find_one return AsyncMock (used by verify_encryption_key middleware)
    mock_db.usermodels.find_one = AsyncMock(return_value=None)
    with (
        patch("src.database.get_db", return_value=mock_db),
        patch("src.database.connect_db", new_callable=AsyncMock),
        patch("src.database.close_db", new_callable=AsyncMock),
        patch("src.services.email_service.aiosmtplib.send", new_callable=AsyncMock),
    ):
        # Clear lru_cache singletons so dependency_overrides work
        from src.dependencies import (
            _auth_service_singleton,
            _journal_service_singleton,
            _newsletter_service_singleton,
            _pin_service_singleton,
            _user_service_singleton,
            _vault_service_singleton,
            _watchlist_service_singleton,
        )

        for fn in [
            _auth_service_singleton,
            _user_service_singleton,
            _vault_service_singleton,
            _journal_service_singleton,
            _pin_service_singleton,
            _watchlist_service_singleton,
            _newsletter_service_singleton,
        ]:
            fn.cache_clear()

        from src.app import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

        # Clear again after test
        for fn in [
            _auth_service_singleton,
            _user_service_singleton,
            _vault_service_singleton,
            _journal_service_singleton,
            _pin_service_singleton,
            _watchlist_service_singleton,
            _newsletter_service_singleton,
        ]:
            fn.cache_clear()

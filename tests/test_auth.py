from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD, _make_test_user


@pytest.mark.asyncio
async def test_login_success(client):
    user = _make_test_user()
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.post("/api/auth/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD})
    assert resp.status_code == 200
    data = resp.json()
    assert data["token"] is not None
    assert data["message"] == "Login successful"


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    user = _make_test_user()
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.post("/api/auth/login", json={"email": TEST_USER_EMAIL, "password": "wrongpass"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_user_not_found(client):
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=None
    ):
        resp = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "pass"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unverified_email(client):
    user = _make_test_user(isVerified=False)
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.post("/api/auth/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD})
    assert resp.status_code == 401
    assert "verify" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_success(client):
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=None
        ),
        patch("src.repository.user_repository.UserRepository.create_user", new_callable=AsyncMock) as mock_create,
        patch("src.services.email_service.EmailService.send_otp_email", new_callable=AsyncMock),
    ):
        from bson import ObjectId

        mock_create.return_value = {"_id": ObjectId(), "email": "new@example.com"}
        resp = await client.post(
            "/api/auth/register", json={"name": "New User", "email": "new@example.com", "password": "Pass123!"}
        )
    assert resp.status_code == 201
    assert "otp" in resp.json()["message"].lower() or "check" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    user = _make_test_user()
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.post(
            "/api/auth/register", json={"name": "Dup", "email": TEST_USER_EMAIL, "password": "Pass123!"}
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_verify_otp_success(client):
    from datetime import datetime, timedelta

    user = _make_test_user(
        isVerified=False, verificationOTP="123456", otpExpiresAt=datetime.now(UTC) + timedelta(minutes=5)
    )
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
        ),
        patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock),
    ):
        resp = await client.post("/api/auth/verify", json={"email": TEST_USER_EMAIL, "otp": "123456"})
    assert resp.status_code == 200
    assert resp.json()["token"] is not None


@pytest.mark.asyncio
async def test_verify_otp_invalid(client):
    from datetime import datetime, timedelta

    user = _make_test_user(
        isVerified=False, verificationOTP="123456", otpExpiresAt=datetime.now(UTC) + timedelta(minutes=5)
    )
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.post("/api/auth/verify", json={"email": TEST_USER_EMAIL, "otp": "000000"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_success(client):
    user = _make_test_user()
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
        ),
        patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock),
        patch("src.services.email_service.EmailService.send_otp_email", new_callable=AsyncMock),
    ):
        resp = await client.post("/api/auth/forgot-password", json={"email": TEST_USER_EMAIL})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_forgot_password_user_not_found(client):
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=None
    ):
        resp = await client.post("/api/auth/forgot-password", json={"email": "nobody@test.com"})
    assert resp.status_code == 400

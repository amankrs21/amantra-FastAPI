from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import TEST_USER_PASSWORD, _make_test_user


@pytest.mark.asyncio
async def test_fetch_user_success(client, auth_headers):
    user = _make_test_user()
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_id", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.get("/api/user/fetch", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == user["email"]
    assert "password" not in data


@pytest.mark.asyncio
async def test_fetch_user_not_found(client, auth_headers):
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_id", new_callable=AsyncMock, return_value=None
    ):
        resp = await client.get("/api/user/fetch", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_fetch_user_no_auth(client):
    resp = await client.get("/api/user/fetch")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_user_success(client, auth_headers):
    with patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock):
        resp = await client.patch("/api/user/update", headers=auth_headers, json={"name": "Updated"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_user_empty(client, auth_headers):
    resp = await client.patch("/api/user/update", headers=auth_headers, json={})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_change_password_success(client, auth_headers):
    user = _make_test_user()
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_id", new_callable=AsyncMock, return_value=user
        ),
        patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock),
    ):
        resp = await client.patch(
            "/api/user/changePassword",
            headers=auth_headers,
            json={"oldPassword": TEST_USER_PASSWORD, "newPassword": "NewPass456!"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(client, auth_headers):
    user = _make_test_user()
    with patch(
        "src.repository.user_repository.UserRepository.get_user_by_id", new_callable=AsyncMock, return_value=user
    ):
        resp = await client.patch(
            "/api/user/changePassword",
            headers=auth_headers,
            json={"oldPassword": "WrongOld!", "newPassword": "NewPass456!"},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_deactivate_user(client, auth_headers):
    with (
        patch(
            "src.repository.vault_repository.VaultRepository.delete_many_by_user",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "src.repository.journal_repository.JournalRepository.delete_many_by_user",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "src.repository.watchlist_repository.WatchlistRepository.delete_many_by_user",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch("src.repository.newsletter_repository.NewsletterRepository.delete_user_cache", new_callable=AsyncMock),
        patch("src.repository.user_repository.UserRepository.delete_user", new_callable=AsyncMock),
    ):
        resp = await client.delete("/api/user/deactivate", headers=auth_headers)
    assert resp.status_code == 200
    assert "deactivated" in resp.json()["message"].lower()

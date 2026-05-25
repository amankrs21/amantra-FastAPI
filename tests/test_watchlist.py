from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

from tests.conftest import TEST_USER_ID


@pytest.mark.asyncio
async def test_fetch_watchlist(client, auth_headers):
    items = [
        {
            "_id": ObjectId(),
            "title": "Inception",
            "category": "movie",
            "status": "watched",
            "createdBy": ObjectId(TEST_USER_ID),
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }
    ]
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.find_by_user",
        new_callable=AsyncMock,
        return_value=items,
    ):
        resp = await client.get("/api/watchlist/fetch", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_add_watchlist(client, auth_headers):
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.create", new_callable=AsyncMock, return_value="w123"
    ):
        resp = await client.post(
            "/api/watchlist/add", headers=auth_headers, json={"title": "Inception", "category": "movie"}
        )
    assert resp.status_code == 200
    assert resp.json()["_id"] == "w123"


@pytest.mark.asyncio
async def test_update_watchlist_success(client, auth_headers):
    item_id = str(ObjectId())
    existing = {"_id": ObjectId(item_id), "title": "Inception", "createdBy": ObjectId(TEST_USER_ID)}
    with (
        patch(
            "src.repository.watchlist_repository.WatchlistRepository.find_one",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch("src.repository.watchlist_repository.WatchlistRepository.update", new_callable=AsyncMock, return_value=1),
    ):
        resp = await client.put(f"/api/watchlist/update/{item_id}", headers=auth_headers, json={"rating": 9.0})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_watchlist_not_found(client, auth_headers):
    item_id = str(ObjectId())
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.find_one", new_callable=AsyncMock, return_value=None
    ):
        resp = await client.put(f"/api/watchlist/update/{item_id}", headers=auth_headers, json={"rating": 9.0})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_watchlist_success(client, auth_headers):
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.delete", new_callable=AsyncMock, return_value=1
    ):
        resp = await client.delete(f"/api/watchlist/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_watchlist_not_found(client, auth_headers):
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.delete", new_callable=AsyncMock, return_value=0
    ):
        resp = await client.delete(f"/api/watchlist/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_subscribed(client, auth_headers):
    items = [
        {
            "_id": ObjectId(),
            "title": "Breaking Bad",
            "subscribeNews": True,
            "createdBy": ObjectId(TEST_USER_ID),
            "createdAt": datetime.now(UTC),
        }
    ]
    with patch(
        "src.repository.watchlist_repository.WatchlistRepository.get_subscribed_by_user",
        new_callable=AsyncMock,
        return_value=items,
    ):
        resp = await client.get("/api/watchlist/subscribed", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_watchlist_no_auth(client):
    resp = await client.get("/api/watchlist/fetch")
    assert resp.status_code == 401

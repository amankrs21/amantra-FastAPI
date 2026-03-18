from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

from tests.conftest import TEST_USER_ID

MOCK_KEY = base64.b64encode(b"testkey123456789").decode()


@pytest.mark.asyncio
async def test_fetch_journals(client, auth_headers):
    journals = [{"_id": ObjectId(), "title": "Day 1", "content": "enc", "updatedAt": None}]
    with patch(
        "src.repository.journal_repository.JournalRepository.find_by_user",
        new_callable=AsyncMock,
        return_value=journals,
    ):
        resp = await client.get("/api/journal/fetch", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["content"] is None  # content masked


@pytest.mark.asyncio
async def test_add_journal(client, auth_headers):
    with patch(
        "src.repository.journal_repository.JournalRepository.create", new_callable=AsyncMock, return_value="j123"
    ):
        resp = await client.post(
            "/api/journal/add",
            headers=auth_headers,
            json={"title": "Day 1", "content": "Dear diary...", "key": MOCK_KEY},
        )
    assert resp.status_code == 200
    assert resp.json()["_id"] == "j123"


@pytest.mark.asyncio
async def test_update_journal_success(client, auth_headers):
    with patch("src.repository.journal_repository.JournalRepository.update", new_callable=AsyncMock, return_value=1):
        resp = await client.patch(
            "/api/journal/update",
            headers=auth_headers,
            json={"id": str(ObjectId()), "title": "Updated", "content": "new content", "key": MOCK_KEY},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_journal_not_found(client, auth_headers):
    with patch("src.repository.journal_repository.JournalRepository.update", new_callable=AsyncMock, return_value=0):
        resp = await client.patch(
            "/api/journal/update",
            headers=auth_headers,
            json={"id": str(ObjectId()), "title": "X", "content": "X", "key": MOCK_KEY},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_journal_success(client, auth_headers):
    with patch("src.repository.journal_repository.JournalRepository.delete", new_callable=AsyncMock, return_value=1):
        resp = await client.delete(f"/api/journal/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_journal_not_found(client, auth_headers):
    with patch("src.repository.journal_repository.JournalRepository.delete", new_callable=AsyncMock, return_value=0):
        resp = await client.delete(f"/api/journal/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_decrypt_journal_success(client, auth_headers):
    from src.helpers.cipher import encrypt

    encrypted = encrypt("secret diary entry", MOCK_KEY)
    journal = {"_id": ObjectId(), "content": encrypted, "createdBy": ObjectId(TEST_USER_ID)}
    with patch(
        "src.repository.journal_repository.JournalRepository.find_one", new_callable=AsyncMock, return_value=journal
    ):
        resp = await client.post(f"/api/journal/{journal['_id']}", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 200
    assert resp.json()["content"] == "secret diary entry"


@pytest.mark.asyncio
async def test_decrypt_journal_not_found(client, auth_headers):
    with patch(
        "src.repository.journal_repository.JournalRepository.find_one", new_callable=AsyncMock, return_value=None
    ):
        resp = await client.post(f"/api/journal/{ObjectId()}", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 400

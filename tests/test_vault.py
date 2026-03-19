from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch

import pytest
from bson import ObjectId

from tests.conftest import TEST_USER_ID

MOCK_KEY = base64.b64encode(b"testkey123456789").decode()  # Test-only mock encryption key


@pytest.mark.asyncio
async def test_fetch_vaults(client, auth_headers):
    vaults = [{"_id": ObjectId(), "title": "Gmail", "username": "u", "password": "enc", "category": "email", "updatedAt": None}]
    with patch(
        "src.repository.vault_repository.VaultRepository.find_by_user", new_callable=AsyncMock, return_value=vaults
    ):
        resp = await client.post(
            "/api/vault/fetch", headers=auth_headers, json={"pageSize": 10, "offSet": 0, "key": MOCK_KEY}
        )
    assert resp.status_code == 200
    assert resp.json()[0]["password"] is None  # password should be masked
    assert resp.json()[0]["category"] == "email"


@pytest.mark.asyncio
async def test_add_vault(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.create", new_callable=AsyncMock, return_value="abc123"):
        resp = await client.post(
            "/api/vault/add",
            headers=auth_headers,
            json={"title": "Gmail", "username": "user", "password": "pass123", "key": MOCK_KEY, "category": "email"},
        )
    assert resp.status_code == 200
    assert resp.json()["_id"] == "abc123"


@pytest.mark.asyncio
async def test_update_vault_success(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.update", new_callable=AsyncMock, return_value=1):
        resp = await client.patch(
            "/api/vault/update",
            headers=auth_headers,
            json={"id": str(ObjectId()), "title": "Gmail", "username": "user", "password": "newpass", "key": MOCK_KEY, "category": "social"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_vault_not_found(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.update", new_callable=AsyncMock, return_value=0):
        resp = await client.patch(
            "/api/vault/update",
            headers=auth_headers,
            json={"id": str(ObjectId()), "title": "Gmail", "username": "user", "password": "newpass", "key": MOCK_KEY, "category": "social"},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_vault_success(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.delete", new_callable=AsyncMock, return_value=1):
        resp = await client.delete(f"/api/vault/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_vault_not_found(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.delete", new_callable=AsyncMock, return_value=0):
        resp = await client.delete(f"/api/vault/delete/{ObjectId()}", headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_decrypt_vault_success(client, auth_headers):
    from src.helpers.cipher import encrypt

    encrypted = encrypt("mypassword", MOCK_KEY)
    vault = {"_id": ObjectId(), "password": encrypted, "createdBy": ObjectId(TEST_USER_ID)}
    with patch("src.repository.vault_repository.VaultRepository.find_one", new_callable=AsyncMock, return_value=vault):
        resp = await client.post(f"/api/vault/{vault['_id']}", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 200
    assert resp.json()["password"] is not None


@pytest.mark.asyncio
async def test_decrypt_vault_not_found(client, auth_headers):
    with patch("src.repository.vault_repository.VaultRepository.find_one", new_callable=AsyncMock, return_value=None):
        resp = await client.post(f"/api/vault/{ObjectId()}", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 400

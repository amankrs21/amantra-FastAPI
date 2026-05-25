from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch

import pytest

MOCK_KEY = base64.b64encode(b"testkey123456789").decode()


@pytest.mark.asyncio
async def test_verify_pin(client, auth_headers):
    resp = await client.post("/api/pin/verify", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 200
    assert "valid" in resp.json()["message"].lower() or "encryption" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_set_text(client, auth_headers):
    with patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock):
        resp = await client.post("/api/pin/setText", headers=auth_headers, json={"key": MOCK_KEY})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_reset_pin(client, auth_headers):
    with (
        patch("src.repository.user_repository.UserRepository.update_user", new_callable=AsyncMock),
        patch("src.repository.journal_repository.JournalRepository.nullify_content_by_user", new_callable=AsyncMock),
        patch("src.repository.vault_repository.VaultRepository.nullify_passwords_by_user", new_callable=AsyncMock),
    ):
        resp = await client.get("/api/pin/reset", headers=auth_headers)
    assert resp.status_code == 200
    assert "reset" in resp.json()["message"].lower()


@pytest.mark.asyncio
async def test_pin_no_auth(client):
    resp = await client.post("/api/pin/verify", json={"key": MOCK_KEY})
    assert resp.status_code == 401

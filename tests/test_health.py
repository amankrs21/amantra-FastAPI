from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_check_method_not_allowed(client):
    resp = await client.post("/health")
    assert resp.status_code == 405


@pytest.mark.asyncio
async def test_nonexistent_route(client):
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_docs_available(client):
    resp = await client.get("/docs")
    assert resp.status_code == 200

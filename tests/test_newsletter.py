from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import TEST_USER_EMAIL, TEST_USER_ID, _make_test_user

MOCK_FEED = {
    "articles": [{"title": "Test", "url": "https://test.com", "tag": "ai"}],
    "category": "all",
    "fetchedAt": "2026-03-19T12:00:00Z",
}


@pytest.mark.asyncio
async def test_get_newsletter_feed(client, auth_headers):
    user = _make_test_user()
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
        ),
        patch(
            "src.services.newsletter_service.NewsletterService.get_feed",
            new_callable=AsyncMock,
            return_value=MOCK_FEED,
        ),
    ):
        resp = await client.get("/api/newsletter/feed", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["articles"][0]["title"] == "Test"


@pytest.mark.asyncio
async def test_get_newsletter_with_category(client, auth_headers):
    user = _make_test_user()
    feed = {**MOCK_FEED, "category": "ai"}
    with (
        patch(
            "src.repository.user_repository.UserRepository.get_user_by_email", new_callable=AsyncMock, return_value=user
        ),
        patch(
            "src.services.newsletter_service.NewsletterService.get_feed",
            new_callable=AsyncMock,
            return_value=feed,
        ),
    ):
        resp = await client.get("/api/newsletter/feed?category=ai", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["category"] == "ai"


@pytest.mark.asyncio
async def test_newsletter_no_auth(client):
    resp = await client.get("/api/newsletter/feed")
    assert resp.status_code == 401

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.middleware.auth import get_current_user
from src.dependencies import get_newsletter_service
from src.services.newsletter_service import NewsletterService
from src.repository.newsletter_repository import NewsletterRepoError


newsletter_route = APIRouter()


@newsletter_route.get("/feed", status_code=status.HTTP_200_OK)
async def get_newsletter(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    service: NewsletterService = Depends(get_newsletter_service),
) -> dict:
    try:
        return await service.get_feed(current_user["id"], category)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except NewsletterRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

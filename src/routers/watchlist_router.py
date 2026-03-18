from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.dependencies import get_watchlist_service

# local imports
from src.middleware.auth import get_current_user
from src.models.user import MessageResponse
from src.models.watchlist import WatchlistAdd, WatchlistUpdate
from src.repository.watchlist_repository import WatchlistRepoError
from src.services.watchlist_service import WatchlistService

watchlist_route = APIRouter()


@watchlist_route.get("/fetch", status_code=status.HTTP_200_OK)
async def fetch_watchlist(
    current_user: dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[dict]:
    try:
        return await service.fetch_watchlist(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except WatchlistRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@watchlist_route.post("/add", status_code=status.HTTP_200_OK)
async def add_watchlist(
    body: WatchlistAdd,
    current_user: dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> dict:
    try:
        return await service.add_item(current_user["id"], body.model_dump())
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except WatchlistRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@watchlist_route.put("/update/{item_id}", status_code=status.HTTP_200_OK)
async def update_watchlist(
    item_id: str,
    body: WatchlistUpdate,
    current_user: dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> MessageResponse:
    try:
        return await service.update_item(item_id, current_user["id"], body.model_dump())
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except WatchlistRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@watchlist_route.delete("/delete/{item_id}", status_code=status.HTTP_200_OK)
async def delete_watchlist(
    item_id: str,
    current_user: dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> MessageResponse:
    try:
        return await service.delete_item(item_id, current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except WatchlistRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@watchlist_route.get("/subscribed", status_code=status.HTTP_200_OK)
async def get_subscribed(
    current_user: dict = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> list[dict]:
    try:
        return await service.get_subscribed(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except WatchlistRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

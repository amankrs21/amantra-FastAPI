from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

# local imports
from src.dependencies import get_user_service
from src.middleware.auth import get_current_user
from src.models.user import ChangePasswordRequest, MessageResponse, UpdateUserRequest
from src.models.user import DeactivateRequest, DeactivateVerifyRequest
from src.repository.user_repository import UserRepoError
from src.services.user_service import UserService

user_route = APIRouter()


@user_route.get("/fetch", status_code=status.HTTP_200_OK)
async def fetch_user(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict:
    try:
        return await service.fetch_user(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@user_route.get("/overview", status_code=status.HTTP_200_OK)
async def fetch_overview(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> dict:
    try:
        return await service.fetch_overview(current_user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@user_route.patch("/update", status_code=status.HTTP_200_OK)
async def update_user(
    body: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.update_user(current_user["id"], body.model_dump())
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@user_route.patch("/changePassword", status_code=status.HTTP_200_OK)
async def change_password(
    body: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.change_password(current_user["id"], body.oldPassword, body.newPassword)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure)) from ure
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@user_route.post("/deactivate/request", status_code=status.HTTP_200_OK)
async def request_deactivate(
    body: DeactivateRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.request_deactivation_otp(current_user["id"], body.email)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


@user_route.post("/deactivate/confirm", status_code=status.HTTP_200_OK)
async def confirm_deactivate(
    body: DeactivateVerifyRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    try:
        return await service.confirm_deactivation(current_user["id"], body.email, body.otp)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve)) from ve
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

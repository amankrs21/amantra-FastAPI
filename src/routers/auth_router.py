from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, status

# local imports
from src.config import config
from src.dependencies import get_auth_service
from src.services.auth_service import AuthService
from src.models.user import LoginRequest, LoginResponse
from src.repository.user_repository import UserRepoError


auth_route = APIRouter()


@auth_route.post("/login", status_code=status.HTTP_200_OK)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    try:
        response = await service.user_login(request.email, request.password)
        if not response.token:
            raise PermissionError(response.message or "Login failed")
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(pe))
    except UserRepoError as ure:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(ure))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

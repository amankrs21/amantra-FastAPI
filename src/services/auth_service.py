# local imports
from models.user import LoginResponse
from src.helpers.auth_helper import AuthHelper
from repository.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo
        self._helper = AuthHelper()


    # User login method
    async def user_login(self, email: str, password: str) -> LoginResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            return LoginResponse(token=None, message="Email or Password is incorrect")
        if not self._helper.verify_password(password, user.get("password", "")):
            return LoginResponse(token=None, message="Email or Password is incorrect")
        token = self._helper.create_access_token({"email": user["email"]})
        return LoginResponse(token=token, message="Login successful")

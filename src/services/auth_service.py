from __future__ import annotations

import logging
from datetime import UTC, datetime

# local imports
from src.config import config
from src.helpers.auth_helper import AuthHelper
from src.helpers.response_helper import build_user_response
from src.models.user import AuthResponse, MessageResponse
from src.repository.user_repository import UserRepository
from src.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService) -> None:
        self._repo = user_repo
        self._email = email_service
        self._helper = AuthHelper()

    async def _send_otp_safe(self, email: str, otp: str, purpose: str = "verification") -> bool:
        """Send OTP email, return True if sent, False if failed (non-fatal)."""
        try:
            await self._email.send_otp_email(email, otp, purpose=purpose)
            return True
        except Exception as e:
            logger.warning("Failed to send OTP email to %s: %s", email, e)
            return False

    async def user_login(self, email: str, password: str) -> AuthResponse:
        user = await self._repo.get_user_by_email(email)
        if not user or not user.get("password"):
            raise PermissionError("Invalid credentials")
        if not self._helper.verify_password(password, user["password"]):
            raise PermissionError("Invalid credentials")
        if not user.get("isVerified", False):
            raise PermissionError("Please verify your email before logging in")
        token = self._helper.create_access_token({"id": str(user["_id"]), "name": user.get("name")})
        return AuthResponse(
            token=token,
            message="Login successful",
            user=build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

    async def user_register(
        self, name: str, email: str, password: str, dateOfBirth: str | None = None, weatherCity: str | None = None
    ) -> MessageResponse:
        existing = await self._repo.get_user_by_email(email)
        if existing:
            if existing.get("isVerified"):
                raise ValueError("You already have an account. Please login instead.")
            # User exists but not verified — update their info, resend OTP
            otp = self._helper.generate_otp()
            otp_expiry = self._helper.get_otp_expiry()
            hashed = self._helper.hash_password(password)
            await self._repo.update_user(str(existing["_id"]), {
                "name": name,
                "password": hashed,
                "dateOfBirth": dateOfBirth,
                "weatherCity": weatherCity,
                "verificationOTP": otp,
                "otpExpiresAt": otp_expiry,
            })
            sent = await self._send_otp_safe(email, otp, purpose="verification")
            msg = "Registration successful. Please check your email for OTP." if sent else "Registration successful. OTP email could not be sent — please use 'Resend OTP'."
            return MessageResponse(message=msg)

        hashed = self._helper.hash_password(password)
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        avatar_url = f"https://api.dicebear.com/9.x/fun-emoji/svg?seed={email}"
        user_doc = {
            "email": email,
            "password": hashed,
            "name": name,
            "dateOfBirth": dateOfBirth,
            "weatherCity": weatherCity,
            "avatarUrl": avatar_url,
            "textVerify": None,
            "isVerified": False,
            "verificationOTP": otp,
            "otpExpiresAt": otp_expiry,
            "createdAt": datetime.now(UTC),
        }
        await self._repo.create_user(user_doc)
        sent = await self._send_otp_safe(email, otp, purpose="verification")
        msg = "Registration successful. Please check your email for OTP." if sent else "Registration successful. OTP email could not be sent — please use 'Resend OTP'."
        return MessageResponse(message=msg)

    async def verify_otp(self, email: str, otp: str) -> AuthResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.get("isVerified", False):
            raise ValueError("Email already verified")
        stored_otp = user.get("verificationOTP")
        otp_expires = user.get("otpExpiresAt")
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid OTP")
        if otp_expires and datetime.now(UTC) > (
            otp_expires.replace(tzinfo=UTC) if otp_expires.tzinfo is None else otp_expires
        ):
            raise ValueError("OTP has expired")
        await self._repo.update_user(
            str(user["_id"]),
            {
                "isVerified": True,
                "verificationOTP": None,
                "otpExpiresAt": None,
            },
        )
        user["isVerified"] = True
        token = self._helper.create_access_token({"id": str(user["_id"]), "name": user.get("name")})
        return AuthResponse(
            token=token,
            message="Email verified successfully",
            user=build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

    async def resend_otp(self, email: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        if user.get("isVerified", False):
            raise ValueError("Email already verified")
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        await self._repo.update_user(
            str(user["_id"]),
            {
                "verificationOTP": otp,
                "otpExpiresAt": otp_expiry,
            },
        )
        sent = await self._send_otp_safe(email, otp, purpose="verification")
        if not sent:
            raise ValueError("Failed to send OTP email. Please try again later.")
        return MessageResponse(message="OTP resent successfully")

    async def forgot_password(self, email: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        await self._repo.update_user(
            str(user["_id"]),
            {
                "verificationOTP": otp,
                "otpExpiresAt": otp_expiry,
            },
        )
        sent = await self._send_otp_safe(email, otp, purpose="password reset")
        if not sent:
            raise ValueError("Failed to send OTP email. Please try again later.")
        return MessageResponse(message="OTP sent to your email")

    async def reset_password(self, email: str, otp: str, password: str) -> MessageResponse:
        user = await self._repo.get_user_by_email(email)
        if not user:
            raise ValueError("User not found")
        stored_otp = user.get("verificationOTP")
        otp_expires = user.get("otpExpiresAt")
        if not stored_otp or stored_otp != otp:
            raise ValueError("Invalid OTP")
        if otp_expires and datetime.now(UTC) > (
            otp_expires.replace(tzinfo=UTC) if otp_expires.tzinfo is None else otp_expires
        ):
            raise ValueError("OTP has expired")
        hashed = self._helper.hash_password(password)
        await self._repo.update_user(
            str(user["_id"]),
            {
                "password": hashed,
                "verificationOTP": None,
                "otpExpiresAt": None,
            },
        )
        return MessageResponse(message="Password reset successful")

    async def google_auth(self, id_token_str: str) -> AuthResponse:
        idinfo = await self._helper.verify_google_token(id_token_str, config.google_client_ids)
        email = idinfo["email"]
        user = await self._repo.get_user_by_email(email)
        if not user:
            user_doc = {
                "email": email,
                "password": None,
                "name": idinfo.get("name", ""),
                "dateOfBirth": None,
                "weatherCity": None,
                "avatarUrl": idinfo.get("picture"),
                "textVerify": None,
                "isVerified": True,
                "verificationOTP": None,
                "otpExpiresAt": None,
                "createdAt": datetime.now(UTC),
            }
            user = await self._repo.create_user(user_doc)
        token = self._helper.create_access_token(
            {
                "id": str(user["_id"]),
                "name": user.get("name"),
                "email": user.get("email"),
                "avatarUrl": user.get("avatarUrl"),
            }
        )
        return AuthResponse(
            token=token,
            message="Google authentication successful",
            user=build_user_response(user),
            isKeySet=user.get("textVerify") is not None,
        )

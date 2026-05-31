from __future__ import annotations

# local imports
from datetime import UTC, datetime

from src.helpers.auth_helper import AuthHelper
from src.helpers.cipher import encrypt
from src.models.user import MessageResponse
from src.repository.journal_repository import JournalRepository
from src.repository.user_repository import UserRepository
from src.repository.vault_repository import VaultRepository
from src.services.email_service import EmailService


class PinService:
    def __init__(
        self,
        user_repo: UserRepository,
        vault_repo: VaultRepository,
        journal_repo: JournalRepository,
        email_service: EmailService,
    ) -> None:
        self._user_repo = user_repo
        self._vault_repo = vault_repo
        self._journal_repo = journal_repo
        self._email = email_service
        self._helper = AuthHelper()

    async def verify_key(self) -> MessageResponse:
        return MessageResponse(message="Valid Encryption Key!")

    async def set_text(self, user_id: str, key: str) -> MessageResponse:
        encrypted = encrypt("Hey SV, Verify me!", key)
        await self._user_repo.update_user(user_id, {"textVerify": encrypted})
        return MessageResponse(message="Encryption key set")

    async def reset_pin(self, user_id: str) -> MessageResponse:
        await self._user_repo.update_user(user_id, {"textVerify": None})
        await self._journal_repo.nullify_content_by_user(user_id)
        await self._vault_repo.nullify_passwords_by_user(user_id)
        return MessageResponse(message="PIN reset successful")

    async def send_reset_otp(self, user_id: str) -> MessageResponse:
        user = await self._user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not user.get("email"):
            raise ValueError("Email not found")

        otp = self._helper.generate_otp()
        otp_expiry = self._helper.get_otp_expiry()
        await self._user_repo.update_user(
            user_id,
            {
                "pinResetOTP": otp,
                "pinResetOTPExpiresAt": otp_expiry,
            },
        )
        await self._email.send_otp_email(user["email"], otp, purpose="encryption key reset")
        return MessageResponse(message="OTP sent")

    async def verify_reset_otp(self, user_id: str, otp: str) -> MessageResponse:
        user = await self._user_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        stored = user.get("pinResetOTP")
        otp_expires = user.get("pinResetOTPExpiresAt")
        if not stored or stored != otp:
            raise ValueError("Invalid OTP")
        if otp_expires and datetime.now(UTC) > (
            otp_expires.replace(tzinfo=UTC) if otp_expires.tzinfo is None else otp_expires
        ):
            raise ValueError("OTP has expired")

        await self.reset_pin(user_id)
        await self._user_repo.update_user(
            user_id,
            {
                "pinResetOTP": None,
                "pinResetOTPExpiresAt": None,
            },
        )
        return MessageResponse(message="Encryption key reset")

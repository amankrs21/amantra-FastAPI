from __future__ import annotations

from functools import lru_cache

from src.repository.journal_repository import JournalRepository
from src.repository.newsletter_repository import NewsletterRepository
from src.repository.user_repository import UserRepository
from src.repository.vault_repository import VaultRepository
from src.repository.watchlist_repository import WatchlistRepository
from src.services.auth_service import AuthService
from src.services.email_service import EmailService
from src.services.journal_service import JournalService
from src.services.newsletter_service import NewsletterService
from src.services.pin_service import PinService
from src.services.user_service import UserService
from src.services.vault_service import VaultService
from src.services.watchlist_service import WatchlistService


@lru_cache(maxsize=1)
def _auth_service_singleton() -> AuthService:
    return AuthService(UserRepository(), EmailService())


def get_auth_service() -> AuthService:
    return _auth_service_singleton()


@lru_cache(maxsize=1)
def _user_service_singleton() -> UserService:
    return UserService(
        UserRepository(), VaultRepository(), JournalRepository(), WatchlistRepository(), NewsletterRepository()
    )


def get_user_service() -> UserService:
    return _user_service_singleton()


@lru_cache(maxsize=1)
def _vault_service_singleton() -> VaultService:
    return VaultService(VaultRepository())


def get_vault_service() -> VaultService:
    return _vault_service_singleton()


@lru_cache(maxsize=1)
def _journal_service_singleton() -> JournalService:
    return JournalService(JournalRepository())


def get_journal_service() -> JournalService:
    return _journal_service_singleton()


@lru_cache(maxsize=1)
def _pin_service_singleton() -> PinService:
    return PinService(UserRepository(), VaultRepository(), JournalRepository())


def get_pin_service() -> PinService:
    return _pin_service_singleton()


@lru_cache(maxsize=1)
def _watchlist_service_singleton() -> WatchlistService:
    return WatchlistService(WatchlistRepository())


def get_watchlist_service() -> WatchlistService:
    return _watchlist_service_singleton()


@lru_cache(maxsize=1)
def _newsletter_service_singleton() -> NewsletterService:
    return NewsletterService(NewsletterRepository(), WatchlistRepository())


def get_newsletter_service() -> NewsletterService:
    return _newsletter_service_singleton()

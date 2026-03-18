from __future__ import annotations

import base64
from datetime import UTC, datetime

import pytest
from bson import ObjectId

from src.helpers.auth_helper import AuthHelper
from src.helpers.cipher import decrypt, encrypt
from src.helpers.response_helper import (
    build_user_dict,
    build_user_response,
    compute_watchlist_status,
    extract_domain,
    serialize_document,
)

MOCK_KEY = base64.b64encode(b"testkey123456789").decode()


class TestCipher:
    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Hello, World!"
        encrypted = encrypt(plaintext, MOCK_KEY)
        assert encrypted != plaintext
        assert ":" in encrypted
        decrypted = decrypt(encrypted, MOCK_KEY)
        assert decrypted == plaintext

    def test_encrypt_different_each_time(self):
        text = "same text"
        e1 = encrypt(text, MOCK_KEY)
        e2 = encrypt(text, MOCK_KEY)
        assert e1 != e2  # random IV

    def test_decrypt_wrong_key(self):
        encrypted = encrypt("secret", MOCK_KEY)
        wrong_key = base64.b64encode(b"wrongkey12345678").decode()
        with pytest.raises((ValueError, Exception)):
            decrypt(encrypted, wrong_key)

    def test_encrypt_empty_string(self):
        encrypted = encrypt("", MOCK_KEY)
        assert decrypt(encrypted, MOCK_KEY) == ""


class TestAuthHelper:
    def setup_method(self):
        self.helper = AuthHelper()

    def test_hash_and_verify_password(self):
        pw = "MyPassword123!"
        hashed = self.helper.hash_password(pw)
        assert hashed != pw
        assert self.helper.verify_password(pw, hashed)

    def test_verify_wrong_password(self):
        hashed = self.helper.hash_password("correct")
        assert not self.helper.verify_password("wrong", hashed)

    def test_create_and_decode_token(self):
        import os

        import jwt

        data = {"id": "123", "name": "Test"}
        token = self.helper.create_access_token(data)
        decoded = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
        assert decoded["id"] == "123"
        assert decoded["name"] == "Test"
        assert "exp" in decoded

    def test_generate_otp_format(self):
        otp = self.helper.generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()

    def test_otp_expiry_in_future(self):
        expiry = self.helper.get_otp_expiry()
        assert expiry > datetime.now(UTC)


class TestResponseHelper:
    def test_build_user_response(self):
        user = {"_id": ObjectId(), "name": "Test", "email": "t@t.com", "isVerified": True}
        resp = build_user_response(user)
        assert resp.name == "Test"
        assert resp.email == "t@t.com"

    def test_build_user_dict_strips_sensitive(self):
        user = {"_id": ObjectId(), "name": "Test", "email": "t@t.com", "password": "hash", "verificationOTP": "123"}
        result = build_user_dict(user)
        assert "password" not in result
        assert "verificationOTP" not in result
        assert "id" in result

    def test_serialize_document(self):
        doc = {"_id": ObjectId(), "createdBy": ObjectId(), "createdAt": datetime.now(UTC)}
        result = serialize_document(doc)
        assert isinstance(result["_id"], str)
        assert isinstance(result["createdBy"], str)

    def test_extract_domain(self):
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("https://api.github.com") == "api.github.com"

    def test_compute_watchlist_status(self):
        assert compute_watchlist_status(None) is None
        assert compute_watchlist_status([]) is None
        assert compute_watchlist_status([{"watched": False}]) == "to_watch"
        assert compute_watchlist_status([{"watched": True}]) == "watched"
        assert compute_watchlist_status([{"watched": True}, {"watched": False}]) == "watching"

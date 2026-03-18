from __future__ import annotations

import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# local imports
from src.config import config


def _derive_key(user_key_b64: str) -> bytes:
    password_key = config.PASSWORD_KEY
    decoded = base64.b64decode(user_key_b64).decode("latin-1")
    padded = decoded + password_key[len(decoded):]
    return padded.encode("utf-8")[:32]


def encrypt(text: str, user_key_b64: str) -> str:
    key = _derive_key(user_key_b64)
    iv = os.urandom(16)
    aesgcm = AESGCM(key)
    ct_with_tag = aesgcm.encrypt(iv, text.encode("utf-8"), None)
    ct = ct_with_tag[:-16]
    tag = ct_with_tag[-16:]
    return iv.hex() + ":" + ct.hex() + ":" + tag.hex()


def decrypt(encrypted: str, user_key_b64: str) -> str:
    key = _derive_key(user_key_b64)
    parts = encrypted.split(":")
    iv = bytes.fromhex(parts[0])
    ct = bytes.fromhex(parts[1])
    tag = bytes.fromhex(parts[2])
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(iv, ct + tag, None)
    return plaintext.decode("utf-8")

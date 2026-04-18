"""
Keystore — Argon2id + AES-256-GCM encrypted key storage.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Argon2id parameters for key derivation
ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536  # 64 MiB
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32


class Keystore:
    """
    Encrypted keystore using Argon2id + AES-256-GCM.

    Stores encrypted mnemonic/private keys safely on disk.
    """

    @staticmethod
    def encrypt(data: bytes, password: str) -> dict[str, Any]:
        """
        Encrypt data with password.

        Returns: keystore dict[str, Any] (JSON-serializable)
        """
        salt = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)  # AES-GCM nonce

        # Derive encryption key from password using Argon2id
        key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=ARGON2_TIME_COST,
            memory_cost=ARGON2_MEMORY_COST,
            parallelism=ARGON2_PARALLELISM,
            hash_len=ARGON2_HASH_LEN,
            type=Type.ID,
        )

        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        return {
            "version": 1,
            "crypto": {
                "cipher": "aes-256-gcm",
                "ciphertext": ciphertext.hex(),
                "nonce": nonce.hex(),
                "kdf": "argon2id",
                "kdfparams": {
                    "salt": salt.hex(),
                    "time_cost": ARGON2_TIME_COST,
                    "memory_cost": ARGON2_MEMORY_COST,
                    "parallelism": ARGON2_PARALLELISM,
                    "hash_len": ARGON2_HASH_LEN,
                },
            },
        }

    @staticmethod
    def decrypt(keystore: dict[str, Any], password: str) -> bytes:
        """
        Decrypt keystore with password.

        Returns: decrypted data bytes
        """
        crypto = keystore["crypto"]
        kdfparams = crypto["kdfparams"]

        # Re-derive key
        key = hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=bytes.fromhex(kdfparams["salt"]),
            time_cost=kdfparams["time_cost"],
            memory_cost=kdfparams["memory_cost"],
            parallelism=kdfparams["parallelism"],
            hash_len=kdfparams["hash_len"],
            type=Type.ID,
        )

        # Decrypt
        aesgcm = AESGCM(key)
        ciphertext = bytes.fromhex(crypto["ciphertext"])
        nonce = bytes.fromhex(crypto["nonce"])
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def save(keystore: dict[str, Any], path: Path) -> None:
        """Save keystore to file."""
        path.write_text(json.dumps(keystore, indent=2))

    @staticmethod
    def load(path: Path) -> dict[str, Any]:
        """Load keystore from file."""
        return json.loads(path.read_text())

"""
Blake2b-256 and HMAC hashing utilities for Midnight.
"""
import hashlib
import hmac as _hmac


def blake2_256(data: bytes) -> bytes:
    """Blake2b-256 — primary hash function of Midnight (digest_size=32)."""
    return hashlib.blake2b(data, digest_size=32).digest()


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    """HMAC-SHA256."""
    return _hmac.new(key, data, hashlib.sha256).digest()


def hmac_sha512(key: bytes, data: bytes) -> bytes:
    """HMAC-SHA512."""
    return _hmac.new(key, data, hashlib.sha512).digest()

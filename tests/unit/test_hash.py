"""Unit tests for hash utilities."""
from noxipher.crypto.hash import blake2_256, hmac_sha256, hmac_sha512


class TestHashUtils:
    """Test hash functions."""

    def test_blake2_256_length(self) -> None:
        result = blake2_256(b"hello")
        assert len(result) == 32

    def test_blake2_256_deterministic(self) -> None:
        assert blake2_256(b"test") == blake2_256(b"test")

    def test_blake2_256_different_inputs(self) -> None:
        assert blake2_256(b"a") != blake2_256(b"b")

    def test_hmac_sha256_length(self) -> None:
        result = hmac_sha256(b"key", b"data")
        assert len(result) == 32

    def test_hmac_sha512_length(self) -> None:
        result = hmac_sha512(b"key", b"data")
        assert len(result) == 64

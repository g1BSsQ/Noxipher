"""Unit tests for JubJub key derivation."""

import pytest

from noxipher.crypto.jubjub import DustSecretKey, ZswapSecretKeys


class TestZswapSecretKeys:
    """Test ZswapSecretKeys derivation."""

    def test_derive_from_seed(self) -> None:
        keys = ZswapSecretKeys(bytes(32))
        assert len(keys.coin_public_key) == 64  # hex string (32 bytes = 64 hex chars)
        assert len(keys.encryption_public_key) == 64

    def test_deterministic(self) -> None:
        keys1 = ZswapSecretKeys(bytes(32))
        keys2 = ZswapSecretKeys(bytes(32))
        assert keys1.coin_public_key == keys2.coin_public_key
        assert keys1.encryption_public_key == keys2.encryption_public_key

    def test_different_seeds_different_keys(self) -> None:
        keys1 = ZswapSecretKeys(bytes(32))
        keys2 = ZswapSecretKeys(b"\x01" + bytes(31))
        assert keys1.coin_public_key != keys2.coin_public_key

    def test_invalid_seed_length(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            ZswapSecretKeys(bytes(16))


class TestDustSecretKey:
    """Test DustSecretKey derivation."""

    def test_derive_from_seed(self) -> None:
        key = DustSecretKey(bytes(32))
        assert len(key.public_key) == 32
        assert len(key.public_key_hex) == 64

    def test_deterministic(self) -> None:
        key1 = DustSecretKey(bytes(32))
        key2 = DustSecretKey(bytes(32))
        assert key1.public_key == key2.public_key

    def test_invalid_seed_length(self) -> None:
        with pytest.raises(ValueError, match="32 bytes"):
            DustSecretKey(bytes(16))

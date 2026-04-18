"""Unit tests for keystore encryption/decryption."""
import pytest

from noxipher.wallet.keystore import Keystore


class TestKeystore:
    """Test Argon2id + AES-256-GCM keystore."""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Encrypt then decrypt returns original data."""
        data = b"my secret mnemonic words"
        password = "strong_password_123!"

        keystore = Keystore.encrypt(data, password)
        decrypted = Keystore.decrypt(keystore, password)
        assert decrypted == data

    def test_wrong_password_fails(self) -> None:
        """Wrong password raises on decrypt."""
        data = b"secret"
        keystore = Keystore.encrypt(data, "correct_password")
        with pytest.raises(Exception):
            Keystore.decrypt(keystore, "wrong_password")

    def test_keystore_has_version(self) -> None:
        keystore = Keystore.encrypt(b"data", "password")
        assert keystore["version"] == 1

    def test_keystore_uses_argon2id(self) -> None:
        keystore = Keystore.encrypt(b"data", "password")
        assert keystore["crypto"]["kdf"] == "argon2id"

    def test_keystore_uses_aes_gcm(self) -> None:
        keystore = Keystore.encrypt(b"data", "password")
        assert keystore["crypto"]["cipher"] == "aes-256-gcm"

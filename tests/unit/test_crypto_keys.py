"""Unit tests for crypto key derivation."""
import pytest

from noxipher.crypto.keys import (
    MIDNIGHT_COIN_TYPE,
    KeyDerivation,
    Roles,
    SpendingKey,
    Sr25519Signer,
)
from noxipher.core.config import Network
from noxipher.core.exceptions import InvalidMnemonicError


TEST_MNEMONIC = "abandon " * 23 + "art"


class TestKeyDerivation:
    """Test HD key derivation for Midnight."""

    def test_mnemonic_to_seed_length(self) -> None:
        """Seed is 64 bytes (BIP39 standard)."""
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        assert len(seed) == 64

    def test_invalid_mnemonic_raises(self) -> None:
        with pytest.raises(InvalidMnemonicError):
            KeyDerivation.mnemonic_to_seed("invalid mnemonic words here")

    def test_derive_key_returns_32_bytes(self) -> None:
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        key = KeyDerivation.derive_key(seed, account=0, role=0, index=0)
        assert len(key) == 32

    def test_different_roles_different_keys(self) -> None:
        """Each role derives a different key."""
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        keys = KeyDerivation.derive_all_roles(seed)
        night_key = keys[Roles.NIGHT_EXTERNAL]
        zswap_key = keys[Roles.ZSWAP]
        dust_key = keys[Roles.DUST]
        assert night_key != zswap_key
        assert night_key != dust_key
        assert zswap_key != dust_key

    def test_deterministic_derivation(self) -> None:
        """Same mnemonic → same keys every time."""
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        keys1 = KeyDerivation.derive_all_roles(seed)
        keys2 = KeyDerivation.derive_all_roles(seed)
        assert keys1 == keys2

    def test_different_account_different_keys(self) -> None:
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        key_0 = KeyDerivation.derive_key(seed, account=0, role=0, index=0)
        key_1 = KeyDerivation.derive_key(seed, account=1, role=0, index=0)
        assert key_0 != key_1

    def test_midnight_coin_type(self) -> None:
        """BIP-44 coin type for Midnight is 2400."""
        assert MIDNIGHT_COIN_TYPE == 2400


class TestSr25519Signer:
    """Test sr25519 signing/verification."""

    def test_sign_verify(self) -> None:
        seed = KeyDerivation.mnemonic_to_seed(TEST_MNEMONIC)
        key = KeyDerivation.derive_key(seed, role=Roles.NIGHT_EXTERNAL)
        signer = Sr25519Signer(key)

        data = b"Hello Midnight"
        signature = signer.sign(data)
        assert len(signature) == 64
        assert signer.verify(signature, data)

    def test_public_key_length(self) -> None:
        signer = Sr25519Signer(bytes(32))
        assert len(signer.public_key) == 32


class TestSpendingKey:
    """Test SpendingKey facade."""

    def test_from_mnemonic(self) -> None:
        sk = SpendingKey.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        assert len(sk.night_key) == 32
        assert len(sk.zswap_seed) == 32
        assert len(sk.dust_seed) == 32

    def test_signer_works(self) -> None:
        sk = SpendingKey.from_mnemonic(TEST_MNEMONIC, Network.PREPROD)
        sig = sk.signer.sign(b"test")
        assert len(sig) == 64

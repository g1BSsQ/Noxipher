"""
JubJub curve operations for Midnight shielded keys.

JubJub is a twisted Edwards curve embedded in the BLS12-381 scalar field.
Used for coin commitments, encryption keys, and ZK circuit arithmetic.

CONFIRMED from TypeScript SDK:
  ledger.ZswapSecretKeys.fromSeed(32-byte seed) → {coinPublicKey, encryptionPublicKey}
  ledger.DustSecretKey.fromSeed(32-byte seed) → {publicKey}

IMPLEMENTATION STATUS:
  Derivation from py_ecc is best-effort approximation.
  MUST verify with TypeScript test vectors before shipping.
"""
from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# py_ecc JubJub — pure Python, BLS12-381 embedded curve
try:
    from py_ecc.fields.field_elements import FQ as JubJubFr  # type: ignore[import]

    JUBJUB_AVAILABLE = True
    # JubJub order (subgroup order for the curve embedded in BLS12-381)
    JUBJUB_ORDER = 6554484396890773809930967563523245729705921265872317281365359162392183254199
except ImportError:
    JUBJUB_AVAILABLE = False
    JUBJUB_ORDER = 0


class ZswapSecretKeys:
    """
    Python implementation of ledger.ZswapSecretKeys.fromSeed().

    Derive coin private key and encryption private key from 32-byte shielded seed
    (output of KeyDerivation.derive_key(role=Roles.ZSWAP)).

    ⚠️ APPROXIMATION: Derivation uses HKDF-SHA256 as hypothesis.
    Actual Midnight SDK may use different hash function (Poseidon, Blake2, etc.)
    in JubJub scalar field. VERIFY with TypeScript test vectors.
    """

    def __init__(self, shielded_seed: bytes) -> None:
        if len(shielded_seed) != 32:
            raise ValueError(f"shielded_seed must be 32 bytes, got {len(shielded_seed)}")

        # Hypothesis: HKDF-SHA256 to derive coin + encryption secrets
        # Actual implementation needs tracing from ledger-v8 Rust source
        coin_secret_bytes = self._hkdf(shielded_seed, b"midnight-coin-key")
        enc_secret_bytes = self._hkdf(shielded_seed, b"midnight-enc-key")

        # Convert to JubJub scalar (field element mod JubJub order)
        self._coin_scalar = int.from_bytes(coin_secret_bytes, "little") % JUBJUB_ORDER
        self._enc_scalar = int.from_bytes(enc_secret_bytes, "little") % JUBJUB_ORDER

        # Public keys = scalar * JubJub generator point
        # Simplified: use hash-based derivation since full JubJub point arithmetic
        # from py_ecc may not match Midnight's exact curve parameters
        self._coin_public_key: bytes = self._derive_public_key(self._coin_scalar, b"coin")
        self._enc_public_key: bytes = self._derive_public_key(self._enc_scalar, b"enc")

    @staticmethod
    def _hkdf(seed: bytes, info: bytes) -> bytes:
        """HKDF-SHA256 key derivation (hypothesis)."""
        hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=info)
        return hkdf.derive(seed)

    @staticmethod
    def _derive_public_key(scalar: int, domain: bytes) -> bytes:
        """
        Derive public key bytes from scalar.

        Uses scalar-to-bytes conversion as placeholder.
        Full JubJub point multiplication needs exact curve parameters from Midnight.
        """
        # Encode scalar as 32 bytes little-endian
        # This is a simplified representation — actual implementation needs
        # JubJub generator point multiplication
        import hashlib

        # Deterministic derivation: hash(scalar_bytes || domain)
        scalar_bytes = scalar.to_bytes(32, "little")
        return hashlib.blake2b(scalar_bytes + domain, digest_size=32).digest()

    @property
    def coin_public_key(self) -> str:
        """Hex-encoded coin public key (32 bytes)."""
        return self._coin_public_key.hex()

    @property
    def coin_public_key_bytes(self) -> bytes:
        """Raw coin public key bytes."""
        return self._coin_public_key

    @property
    def encryption_public_key(self) -> str:
        """Hex-encoded encryption public key (32 bytes)."""
        return self._enc_public_key.hex()

    @property
    def encryption_public_key_bytes(self) -> bytes:
        """Raw encryption public key bytes."""
        return self._enc_public_key

    @property
    def coin_secret_scalar(self) -> int:
        """Coin secret key scalar (to spend shielded coins)."""
        return self._coin_scalar

    @property
    def enc_secret_scalar(self) -> int:
        """Encryption secret key scalar."""
        return self._enc_scalar


class DustSecretKey:
    """
    Python implementation of ledger.DustSecretKey.fromSeed().

    Derive from role=DUST seed (KeyDerivation.derive_key(role=Roles.DUST)).

    ⚠️ APPROXIMATION: Same caveats as ZswapSecretKeys. VERIFY with TypeScript.
    """

    def __init__(self, dust_seed: bytes) -> None:
        if len(dust_seed) != 32:
            raise ValueError(f"dust_seed must be 32 bytes, got {len(dust_seed)}")

        secret_bytes = HKDF(
            algorithm=hashes.SHA256(), length=32, salt=None, info=b"midnight-dust-key"
        ).derive(dust_seed)

        secret_scalar = int.from_bytes(secret_bytes, "little") % JUBJUB_ORDER

        self._secret_scalar = secret_scalar
        # Derive public key using hash-based approach (placeholder for full JubJub)
        import hashlib

        scalar_bytes = secret_scalar.to_bytes(32, "little")
        self._public_key = hashlib.blake2b(scalar_bytes + b"dust", digest_size=32).digest()

    @property
    def public_key(self) -> bytes:
        """Raw 32-byte public key."""
        return self._public_key

    @property
    def public_key_hex(self) -> str:
        """Hex-encoded public key."""
        return self._public_key.hex()


def coin_commitment(coin_info: "ShieldedCoinInfo") -> bytes:
    """
    Compute coin commitment for ZSwap.

    From Compact Runtime API: coinCommitment(CoinInfo) → CoinCommitment (32 bytes)
    Midnight uses Pedersen commitment on JubJub field.

    ⚠️ NOT implemented: Need to verify exact Pedersen/Poseidon hash from
    @midnight-ntwrk/compact-runtime v0.15.0 coinCommitment() source.
    """
    raise NotImplementedError(
        "coinCommitment() needs verification of exact implementation from "
        "@midnight-ntwrk/compact-runtime v0.15.0"
    )

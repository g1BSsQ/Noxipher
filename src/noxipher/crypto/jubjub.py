"""
JubJub curve operations and key derivation for Midnight shielded keys.

This module implements key derivation for Zswap and Dust ecosystems,
complying with Midnight Protocol v8.1.0-rc.1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .curves import JubJubPoint
from .fields import EmbeddedFr, Fr
from .hash import PersistentHashWriter, sample_bytes
from .poseidon import transient_hash

if TYPE_CHECKING:
    pass

# JubJub subgroup order
JUBJUB_ORDER = 0x0E7DB4EA6533AFA906673B0101343B00A6682093CCC81082D0970E5ED6F72CB7


class ZswapSecretKeys:
    """
    Implementation of midnight-zswap SecretKeys.
    Derived from a 32-byte seed.
    """

    def __init__(self, coin_secret_key: bytes, encryption_secret_key: EmbeddedFr) -> None:
        self._coin_sk = coin_secret_key
        self._enc_sk = encryption_secret_key

    @classmethod
    def from_seed(cls, seed: bytes) -> ZswapSecretKeys:
        """
        Derive Zswap keys from a 32-byte seed using protocol-defined domain separators.
        Matches Seed::derive_coin_secret_key and Seed::derive_encryption_secret_key
        in midnight-zswap/src/keys.rs.
        """
        if len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")

        # Derive Coin Secret Key (CSK)
        # hash(b"midnight:csk" || seed)
        csk_writer = PersistentHashWriter()
        csk_writer.update(b"midnight:csk")
        csk_writer.update(seed)
        coin_sk = csk_writer.finalize()

        # Derive Encryption Secret Key (ESK)
        # sample_bytes(64, b"midnight:esk", seed) -> Fr::from_uniform_bytes
        esk_bytes = sample_bytes(64, b"midnight:esk", seed)
        enc_sk = EmbeddedFr.from_uniform_bytes(esk_bytes)

        return cls(coin_sk, enc_sk)

    @property
    def coin_public_key(self) -> bytes:
        """
        Derive Coin Public Key (CPK).
        Matches SecretKey::public_key in coin-structure/src/coin.rs.
        hash(b"midnight:zswap-pk[v1]" || coin_sk)
        """
        pk_writer = PersistentHashWriter()
        pk_writer.update(b"midnight:zswap-pk[v1]")
        pk_writer.update(self._coin_sk)
        return pk_writer.finalize()

    @property
    def encryption_public_key(self) -> bytes:
        """
        Derive Encryption Public Key (EPK).
        Matches SecretKey::public_key in transient-crypto/src/encryption.rs.
        EPK = generator * enc_sk
        """
        gen = JubJubPoint.generator()
        pk_point = gen * self._enc_sk
        return pk_point.to_bytes()

    @property
    def coin_secret_key(self) -> bytes:
        return self._coin_sk

    @property
    def encryption_secret_key(self) -> EmbeddedFr:
        return self._enc_sk


class DustSecretKey:
    """
    Implementation of DustSecretKey.
    Matches DustSecretKey in ledger/src/dust.rs.
    """

    def __init__(self, secret_key: Fr) -> None:
        self._sk = secret_key

    @classmethod
    def from_seed(cls, seed: bytes) -> DustSecretKey:
        """
        Derive Dust key from seed.
        Matches DustSecretKey::sample_bytes(seed, 64, b"midnight:dsk").
        Uses Fr (BLS12-381 scalar field) as per ledger/src/dust.rs.
        """
        if len(seed) != 32:
            raise ValueError("Seed must be 32 bytes")

        dsk_bytes = sample_bytes(64, b"midnight:dsk", seed)
        sk = Fr.from_uniform_bytes(dsk_bytes)
        return cls(sk)

    @property
    def public_key(self) -> bytes:
        """
        Derive Dust Public Key.
        Matches DustPublicKey derivation: transient_hash([Fr::from_le_bytes("mdn:dust:pk"), sk])
        """
        # "mdn:dust:pk" (11 bytes) as a field element
        domain_f = Fr.from_le_bytes(b"mdn:dust:pk")

        # sk as Fr
        sk_f = self._sk

        pk_f = transient_hash([domain_f, sk_f])
        return pk_f.to_bytes()

    @property
    def secret_key(self) -> Fr:
        return self._sk


def hash_to_field(data: bytes) -> Fr:
    """
    Implementation of transient-crypto/src/hash.rs:hash_to_field.
    Construction: transient_hash([midnight:field_hash, data])
    """
    # Midnight represents [u8] in field as chunks of 31 bytes (FR_BYTES_STORED).
    # For small strings like domain separators, it's just Fr(data_le).

    # preimage = b"midnight:field_hash".field_repr() + data.field_repr()
    preimage = []

    # "midnight:field_hash" (19 bytes)
    preimage.append(Fr.from_le_bytes(b"midnight:field_hash"))

    # data
    # We simplify for data < 31 bytes which is the case for our domains
    if len(data) > 31:
        # Full implementation would chunk it LE
        raise NotImplementedError("hash_to_field for large data not implemented")
    preimage.append(Fr.from_le_bytes(data))

    return transient_hash(preimage)


def coin_commitment(
    nonce: bytes,
    token_type: bytes,
    value: int,
    recipient_is_user: bool,
    recipient_hash: bytes,
) -> bytes:
    """
    Compute Zswap coin commitment.
    Matches Info::commitment in coin-structure/src/coin.rs.
    """
    writer = PersistentHashWriter()
    writer.update(b"midnight:zswap-cc[v1]")
    writer.update(nonce)  # 32 bytes
    writer.update(token_type)  # 32 bytes
    writer.update(value.to_bytes(16, "little"))  # u128 LE

    # Recipient
    writer.update(b"\x01" if recipient_is_user else b"\x00")
    writer.update(recipient_hash)

    return writer.finalize()

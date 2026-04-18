"""
UnshieldedWallet — NIGHT token wallet with sr25519 signing.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from noxipher.core.config import Network

from noxipher.crypto.keys import Sr25519Signer

if TYPE_CHECKING:
    from noxipher.indexer.client import IndexerClient


class UnshieldedWallet:
    """
    NIGHT token wallet — unshielded UTxO model.
    Signing: sr25519 (py-sr25519-bindings).

    Balance is computed from: unshieldedCreatedOutputs - unshieldedSpentOutputs
    (Indexer has no direct balance query — must compute from UTxO set)
    """

    def __init__(self, key_bytes: bytes, network: Network) -> None:
        self._signer = Sr25519Signer(key_bytes)
        self._network = network
        self._address = self._signer.compute_address(network)

    @property
    def address(self) -> str:
        """Bech32m unshielded address."""
        return self._address

    @property
    def public_key(self) -> bytes:
        """32-byte sr25519 public key."""
        return self._signer.public_key

    def sign(self, data: bytes) -> bytes:
        """sr25519 sign — 64-byte signature."""
        return self._signer.sign(data)

    def sign_pre_proof(self, data: bytes) -> bytes:
        """Sign with 'pre-proof' marker — for unproven transactions."""
        return self._signer.sign(data)

    def as_substrate_keypair(self) -> object:
        """Get substrate-interface Keypair."""
        return self._signer.as_substrate_keypair()

    async def get_utxos(self, indexer: IndexerClient) -> list[dict[str, Any]]:

        """
        Get UTxO set from Indexer using optimized query.
        """
        return await indexer.get_utxos(address=self._address)

    async def get_balance(self, indexer: IndexerClient) -> dict[str, int]:
        """
        Returns {token_type_hex: amount_specks}.
        NIGHT native token type = "0000...00" (32 zero bytes).
        """
        utxos = await self.get_utxos(indexer)
        balances: dict[str, int] = {}
        for utxo in utxos:
            tt = utxo.get("token_type", "00" * 32)
            # Handle potential nested structure from GraphQL
            if isinstance(tt, dict):
                tt = tt.get("hex", "00" * 32)

            val = int(utxo.get("value", 0))
            balances[tt] = balances.get(tt, 0) + val
        return balances

    def sign_seg_intent(self, data_to_sign: bytes) -> bytes:
        """
        Signs the serialized SegIntent data for an unshielded offer.
        The data should already include the 'midnight:hash-intent:' prefix.
        """
        return self.sign(data_to_sign)

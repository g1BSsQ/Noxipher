"""
ShieldedWallet — Privacy-preserving shielded wallet using JubJub keys.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from noxipher.core.config import Network
from noxipher.crypto.jubjub import ZswapSecretKeys


if TYPE_CHECKING:
    from noxipher.indexer.client import IndexerClient


class ShieldedWallet:
    """
    Privacy-preserving shielded wallet.
    Keys: JubJub curve via py_ecc (ZswapSecretKeys).

    Shielded address = Bech32m(ShieldedAddress(coinPublicKey, encryptionPublicKey))

    CONFIRMED from Counter CLI (Apr 2026):
      coinPubKey = ShieldedCoinPublicKey.fromHexString(
          state.shielded.coinPublicKey
      )
      encPubKey  = ShieldedEncryptionPublicKey.fromHexString(
          state.shielded.encryptionPublicKey
      )
      shieldedAddress = MidnightBech32m.encode(
          networkId, new ShieldedAddress(coinPubKey, encPubKey)
      )

    """

    def __init__(self, shielded_seed: bytes, network: Network) -> None:
        self._seed = shielded_seed
        self._network = network
        self._keys = ZswapSecretKeys(shielded_seed)
        self._address = self._compute_address()

    def _compute_address(self) -> str:
        """
        Shielded address = Bech32m(coinPublicKey_bytes + encryptionPublicKey_bytes).

        Payload = 64 bytes (32 + 32) with HRP mn_shield-addr_<network>.
        CONFIRMED: ShieldedAddress(coinPubKey, encPubKey) → combined bytes.
        """
        from noxipher.address.bech32m import encode_address

        coin_pk = self._keys.coin_public_key_bytes  # 32 bytes
        enc_pk = self._keys.encryption_public_key_bytes  # 32 bytes
        address_bytes = coin_pk + enc_pk  # 64 bytes total
        return encode_address(address_bytes, "shielded", self._network)

    @property
    def address(self) -> str:
        """Bech32m shielded address."""
        return self._address

    @property
    def viewing_key(self) -> str:
        """
        Viewing key for Indexer connect() mutation.

        CONFIRMED from Counter CLI source:
          state.shielded.coinPublicKey.toHexString() +
          state.shielded.encryptionPublicKey.toHexString()
        = hex-encoded 64 bytes (coinPK 32B + encPK 32B)

        Format: "aabb...cc" (128 hex chars, no separator)
        """
        return self._keys.coin_public_key + self._keys.encryption_public_key

    async def open_session(self, indexer: IndexerClient) -> str:
        """Open shielded session with Indexer to scan shielded transactions."""
        return await indexer.connect_wallet_session(self.viewing_key)

    async def close_session(self, indexer: IndexerClient, session_id: str) -> None:
        """Close shielded session."""
        await indexer.disconnect_wallet_session(session_id)

    async def sync_coins(self, indexer: IndexerClient, session_id: str) -> list[dict[str, Any]]:

        """Stream shielded transactions, collect unspent coins."""
        coins = []
        async for event in indexer.subscribe_shielded_transactions(session_id):
            match event.get("__typename"):
                case "ShieldedTransactionFound":
                    coins.extend(event.get("relevantCoins", []))
                case "ShieldedTransactionProgress":
                    pass  # Progress update — log only
        return coins

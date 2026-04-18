"""
DustWallet — DUST fee token wallet (non-transferable).

⚠️ IMPORTANT: DUST is NON-TRANSFERABLE.
DUST CANNOT be sent to other users — only used to pay fees.
DUST is generated automatically from NIGHT UTxOs (after registering on-chain).
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING, Never


from noxipher.core.config import Network
from noxipher.core.exceptions import WalletError
from noxipher.crypto.jubjub import DustSecretKey

if TYPE_CHECKING:
    from noxipher.indexer.client import IndexerClient
    from noxipher.indexer.models import DustGenerationStatus
    from noxipher.tx.builder import TransactionBuilder
    from noxipher.wallet.unshielded import UnshieldedWallet


class DustWallet:
    """
    DUST fee token wallet.

    DUST mechanics (from official Counter CLI):
      1. User holds NIGHT UTxOs
      2. Register UTxOs: wallet.registerNightUtxosForDustGeneration(utxos, pubkey, signFn)
      3. Wait: DUST balance increases over time
      4. Spend: Automatic when submitting transaction (no manual handling needed)

    DUST cost parameters (from official source):
      additionalFeeOverhead: 300_000_000_000_000 (300T Specks)
      feeBlocksMargin: 5 blocks
    """

    # DUST cost parameters from official Counter CLI source (Apr 2026)
    ADDITIONAL_FEE_OVERHEAD = 300_000_000_000_000  # Specks
    FEE_BLOCKS_MARGIN = 5

    def __init__(self, dust_seed: bytes, network: Network) -> None:
        self._key = DustSecretKey(dust_seed)
        self._network = network

    @property
    def address(self) -> str:
        """
        DUST address = Bech32m with HRP mn_dust_<network>.
        Payload is SCALE compact encoding of the 32-byte BigInt public key.
        Specifically, BigInt > 2^30 uses 32 bytes, encoded with prefix 0x73,
        followed by 32 bytes in little-endian order.
        """
        from noxipher.address.bech32m import encode_address

        # SCALE encoding: 0x73 + little-endian pubkey
        # We assume self._key.public_key is big-endian bytes (typical for TS representations)
        pub_le = bytes(reversed(self._key.public_key))
        scale_payload = b"\x73" + pub_le
        return encode_address(scale_payload, "dust", self._network)

    @property
    def public_key(self) -> bytes:
        """32-byte DUST public key."""
        return self._key.public_key

    def can_transfer(self) -> bool:
        """DUST cannot be transferred. Always returns False."""
        return False

    def transfer(self, *args: object, **kwargs: object) -> Never:
        """DUST is non-transferable. Raises WalletError."""
        raise WalletError(
            "DUST cannot be transferred between wallets. "
            "DUST is only used to pay transaction fees. "
            "See: docs.midnight.network for DUST mechanics."
        )

    async def get_generation_status(
        self, indexer: IndexerClient, cardano_stake_key: str
    ) -> DustGenerationStatus:
        """Query DUST generation status for Cardano stake key."""
        results = await indexer.get_dust_status([cardano_stake_key])
        if not results:
            raise WalletError(f"No DUST status for stake key: {cardano_stake_key}")
        return results[0]

    async def register_night_utxos(
        self,
        utxos: list[dict[str, Any]],

        tx_builder: TransactionBuilder,
        unshielded_wallet: UnshieldedWallet,
    ) -> str:
        """
        Register NIGHT UTxOs for DUST generation.

        Must be called before DUST starts generating.
        Creates an on-chain transaction to register UTxOs.
        """
        raise NotImplementedError(
            "registerNightUtxosForDustGeneration needs implementation "
            "after tx format is verified from Midnight team."
        )

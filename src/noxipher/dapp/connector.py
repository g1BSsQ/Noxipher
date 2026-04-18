"""
DApp Connector — interface with Midnight DApps.

DApp Connector pattern (from Midnight web3 docs):
  1. DApp requests wallet connection
  2. Wallet (Noxipher) provides:
     - getCoinPublicKey(): string
     - getEncryptionPublicKey(): string
     - balanceTx(tx, ttl): BalancedTx
     - submitTx(tx): string → tx hash

TTL default: 30 minutes = 1800 seconds
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from noxipher.core.exceptions import WalletError
from noxipher.wallet.wallet import MidnightWallet

if TYPE_CHECKING:
    from noxipher.core.client import NoxipherClient

DEFAULT_TTL_SECONDS = 1800  # 30 minutes


class DAppConnector:
    """
    DApp Connector interface for Midnight smart contracts.
    Allows DApps to interact with wallet through standard interface.
    """

    def __init__(self, wallet: MidnightWallet, client: "NoxipherClient") -> None:
        self._wallet = wallet
        self._client = client

    def get_coin_public_key(self) -> str:
        """Return hex-encoded coin public key (32 bytes)."""
        return self._wallet.shielded._keys.coin_public_key

    def get_encryption_public_key(self) -> str:
        """Return hex-encoded encryption public key (32 bytes)."""
        return self._wallet.shielded._keys.encryption_public_key

    async def balance_transaction(
        self, unbound_tx: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS
    ) -> dict:
        """
        Balance unbound transaction — add inputs/outputs to cover fees.

        TTL default: 30 minutes (1800 seconds)
        """
        raise NotImplementedError(
            "balance_transaction needs implementation after tx format is verified. "
            "Reference: wallet.balanceTransaction() from wallet-sdk-facade."
        )

    async def submit_transaction(self, finalized_tx: dict) -> str:
        """Submit finalized transaction → tx hash."""
        raw_bytes = self._client.tx._serialize_transaction(
            finalized_tx, self._wallet
        )
        return await self._client.node.submit_extrinsic(raw_bytes)

    def as_provider_dict(self) -> dict:
        """
        Return provider dict compatible with Midnight.js contracts API.

        MidnightProvider interface:
          getCoinPublicKey: () → string
          getEncryptionPublicKey: () → string
          balanceTx: (tx, ttl) → Promise<BalancedTx>
          submitTx: (tx) → Promise<string>
        """
        return {
            "getCoinPublicKey": self.get_coin_public_key,
            "getEncryptionPublicKey": self.get_encryption_public_key,
            "balanceTx": self.balance_transaction,
            "submitTx": self.submit_transaction,
        }

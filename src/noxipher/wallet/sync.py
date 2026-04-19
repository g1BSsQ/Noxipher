"""
WalletSyncer — Sync wallet state from Indexer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from noxipher.core.logger import get_logger

if TYPE_CHECKING:
    from noxipher.indexer.client import IndexerClient
    from noxipher.wallet.wallet import MidnightWallet

log = get_logger(__name__)


class WalletSyncer:
    """
    Sync wallet balances and state from Indexer.

    Handles both unshielded (UTxO scan) and shielded (session-based) sync.
    """

    def __init__(self, wallet: MidnightWallet, indexer: IndexerClient) -> None:
        self._wallet = wallet
        self._indexer = indexer

    async def sync_unshielded(self) -> dict[str, int]:
        """Sync unshielded NIGHT balance from Indexer."""
        log.info("syncing_unshielded", address=self._wallet.unshielded.address)
        balance = await self._wallet.unshielded.get_balance(self._indexer)
        log.info("unshielded_synced", balance=balance)
        return balance

    async def sync_shielded(self) -> list[dict[str, Any]]:
        """Sync shielded coins via Indexer session."""
        log.info("syncing_shielded")
        session_id = await self._wallet.shielded.open_session(self._indexer)
        try:
            coins = await self._wallet.shielded.sync_coins(self._indexer, session_id)
            log.info("shielded_synced", coin_count=len(coins))
            return coins
        finally:
            await self._wallet.shielded.close_session(self._indexer, session_id)

    async def sync_all(self) -> dict[str, Any]:
        """Sync all wallet components."""
        unshielded = await self.sync_unshielded()
        return {
            "unshielded": unshielded,
            "network": str(self._wallet.network),
        }

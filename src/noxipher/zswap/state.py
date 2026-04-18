"""
ZSwap state management — global shielded state.

Midnight maintains a Merkle tree of all coin commitments.
Spending = prove membership in Merkle tree + reveal nullifier.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from noxipher.zswap.notes import ShieldedCoinNote


@dataclass
class ZswapState:
    """
    Local ZSwap state for a wallet.
    Synced from Indexer shielded transaction stream.
    """

    unspent_coins: list[ShieldedCoinNote] = field(default_factory=list)
    spent_nullifiers: set[bytes] = field(default_factory=set)
    last_synced_height: int = 0

    def add_coin(self, note: ShieldedCoinNote) -> None:
        """Add an unspent coin."""
        self.unspent_coins.append(note)

    def mark_spent(self, nullifier: bytes) -> None:
        """Mark a coin as spent by nullifier."""
        self.spent_nullifiers.add(nullifier)
        self.unspent_coins = [
            c for c in self.unspent_coins if c.compute_nullifier_safe() != nullifier
        ]

    def get_balance(self, token_type: bytes | None = None) -> dict[bytes, int]:
        """
        Compute shielded balance from unspent coins.

        Args:
            token_type: Filter by token type. None = all.
        """
        balances: dict[bytes, int] = {}
        for coin in self.unspent_coins:
            if token_type is None or coin.token_type == token_type:
                balances[coin.token_type] = (
                    balances.get(coin.token_type, 0) + coin.value
                )
        return balances


class MerkleTree:
    """
    Simplified Midnight commitment Merkle tree.

    ⚠️ PLACEHOLDER: Full implementation needs ZK circuit integration.
    """

    def __init__(self, depth: int = 32) -> None:
        self._depth = depth
        self._leaves: dict[int, bytes] = {}  # index → commitment

    def insert(self, index: int, commitment: bytes) -> None:
        """Insert a commitment at index."""
        self._leaves[index] = commitment

    def root(self) -> bytes:
        """Compute Merkle root. ⚠️ PLACEHOLDER."""
        raise NotImplementedError("MerkleTree.root() needs implementation from compact-runtime")

    def proof(self, index: int) -> list[bytes]:
        """Generate Merkle proof at index. ⚠️ PLACEHOLDER."""
        raise NotImplementedError("MerkleTree.proof() needs implementation from compact-runtime")

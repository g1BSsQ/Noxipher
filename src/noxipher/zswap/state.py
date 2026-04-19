"""
ZSwap state management — global shielded state.

Midnight maintains a Merkle tree of all coin commitments.
Spending = prove membership in Merkle tree + reveal nullifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from noxipher.crypto.fields import Fr
from noxipher.crypto.poseidon import transient_hash
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
                balances[coin.token_type] = balances.get(coin.token_type, 0) + coin.value
        return balances


class MerkleTree:
    """
    Simplified Midnight commitment Merkle tree.
    Uses Poseidon hash for internal nodes.
    """

    def __init__(self, depth: int = 32) -> None:
        self._depth = depth
        self._leaves: dict[int, bytes] = {}  # index → commitment
        # Precompute zero nodes for each level
        self._zero_nodes = self._precompute_zero_nodes(depth)

    def _precompute_zero_nodes(self, depth: int) -> list[bytes]:
        zeros = [b"\x00" * 32] * (depth + 1)
        for i in range(depth):
            f_val = Fr.from_le_bytes(zeros[i])
            # Internal node = hash(left, right)
            parent = transient_hash([f_val, f_val])
            zeros[i + 1] = parent.to_bytes()
        return zeros

    def insert(self, index: int, commitment: bytes) -> None:
        """Insert a commitment at index."""
        if index >= 2**self._depth:
            raise ValueError(f"Index {index} out of bounds for depth {self._depth}")
        self._leaves[index] = commitment

    def root(self) -> bytes:
        """
        Compute Merkle root using current leaves and precomputed zero nodes.
        """
        if not self._leaves:
            return self._zero_nodes[self._depth]

        # Start with all leaf nodes that exist
        current_nodes = {i: Fr.from_le_bytes(c) for i, c in self._leaves.items()}

        for level in range(self._depth):
            next_nodes = {}
            # Get all unique parent indices for current nodes
            parent_indices = {i // 2 for i in current_nodes.keys()}

            for p_idx in parent_indices:
                left_idx = p_idx * 2
                right_idx = left_idx + 1

                left = current_nodes.get(left_idx, Fr.from_le_bytes(self._zero_nodes[level]))
                right = current_nodes.get(right_idx, Fr.from_le_bytes(self._zero_nodes[level]))

                next_nodes[p_idx] = transient_hash([left, right])

            current_nodes = next_nodes

        return current_nodes[0].to_bytes()

    def proof(self, index: int) -> list[bytes]:
        """
        Generate Merkle proof (path of siblings) for leaf at index.
        """
        if index >= 2**self._depth:
            raise ValueError(f"Index {index} out of bounds")

        proof_path = []

        # We need the nodes at each level to find siblings
        # For simplicity, we recompute necessary parts of the tree
        # In production, we'd cache the tree or use a more efficient data structure

        # Build a temporary tree of necessary nodes
        tree_nodes: dict[int, dict[int, Fr]] = {level: {} for level in range(self._depth + 1)}
        for idx, leaf in self._leaves.items():
            tree_nodes[0][idx] = Fr.from_le_bytes(leaf)

        for level in range(self._depth):
            for idx in list(tree_nodes[level].keys()):
                p_idx = idx // 2
                if p_idx not in tree_nodes[level + 1]:
                    left_idx = p_idx * 2
                    right_idx = left_idx + 1
                    zero_val = Fr.from_le_bytes(self._zero_nodes[level])
                    left = tree_nodes[level].get(left_idx, zero_val)
                    right = tree_nodes[level].get(right_idx, zero_val)
                    tree_nodes[level + 1][p_idx] = transient_hash([left, right])

        # Extract siblings
        curr = index
        for level in range(self._depth):
            sibling_idx = curr + 1 if curr % 2 == 0 else curr - 1
            zero_val = Fr.from_le_bytes(self._zero_nodes[level])
            sibling_val = tree_nodes[level].get(sibling_idx, zero_val)
            proof_path.append(sibling_val.to_bytes())
            curr //= 2

        return proof_path

"""
ZSwap pool — privacy pool operations.
"""
from __future__ import annotations

from noxipher.zswap.state import ZswapState


class ZswapPool:
    """
    ZSwap privacy pool interface.

    Manages shielded coin state and provides methods for
    shield/unshield operations.
    """

    def __init__(self) -> None:
        self._state = ZswapState()

    @property
    def state(self) -> ZswapState:
        """Current ZSwap state."""
        return self._state

    def get_shielded_balance(self, token_type: bytes | None = None) -> dict[bytes, int]:
        """Get shielded balance."""
        return self._state.get_balance(token_type)

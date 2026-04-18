"""Wallet balance models."""
from pydantic import BaseModel


class TokenBalance(BaseModel):
    """Balance for a single token type."""

    token_type: str  # hex-encoded RawTokenType
    balance_specks: int  # Balance in Specks (smallest unit)


class WalletState(BaseModel):
    """Aggregated wallet state."""

    unshielded_balances: list[TokenBalance] = []
    shielded_balances: list[TokenBalance] = []
    dust_available: int = 0  # Specks
    last_synced_height: int = 0
